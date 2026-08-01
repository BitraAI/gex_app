import asyncio
import threading
import time as _time_mod

import pandas as pd
from schwab.streaming import StreamClient

from _constants import MAX_BAR_ROWS
from option_streaming_service import _get_stream_symbol


class StreamingService:
    """Subscribes to Schwab LEVELONE_EQUITIES plus NASDAQ_BOOK / NYSE_BOOK for
    the chart symbol and every tracked ticker.  Extracts raw tick data
    (LAST_PRICE + TRADE_TIME_MILLIS + LAST_SIZE) plus BID_PRICE/ASK_PRICE to
    infer trade direction, and aggregates into 1-second OHLCV bars with a
    buy/sell volume split for delta.

    The Level 2 order books (keyed per stream symbol) are the single source
    for book_imbalance / flow_speed / flow_acceleration — see
    ``trend_data``.  A book is subscribed for every tracked ticker so the
    per-ticker Order Flow grid and the wall-zone / Telegram alerts all
    consume L2 book pressure rather than option-quote-derived imbalance.
    """

    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop: asyncio.AbstractEventLoop = loop
        self._sc: StreamClient | None = None
        self._symbol: str | None = None
        self._running = False
        self._stream_task: asyncio.Task | None = None

        # Debug state
        self._ticks_received = 0
        self._connected = False
        self._last_error: str | None = None

        # Callbacks invoked after a successful re-login + re-subscribe
        # so other services (ATM option flow) can re-subscribe on the
        # same StreamClient.
        self._on_reconnect_cbs: list = []

        # Aggregated 1-second OHLCV DataFrame — index = bucket start (ms)
        self._df: pd.DataFrame = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume", "buy_vol", "sell_vol"]
        )
        self._df.index.name = "datetime"
        self._lock = threading.Lock()

        # Current (incomplete) 1-second bucket
        self._current_bucket: int | None = None
        self._current_bar: dict | None = None

        # Latest BID_PRICE / ASK_PRICE / LAST_PRICE from level one quotes
        self._bid_price: float | None = None
        self._ask_price: float | None = None
        self._last_price: float | None = None

        # Level 2 order book snapshots, keyed by schwab stream symbol.  One
        # entry per tracked ticker we have asked Schwab to stream a book for.
        self._book_symbols: set[str] = set()        # stream symbols currently subscribed
        self._books_options: dict[str, dict] = {}   # stream_symbol -> latest OPTIONS_BOOK content msg
        # Per-symbol L2 book-imbalance history: stream_symbol -> list[(ts, ratio)],
        # pruned to the last 60s, used to derive flow_speed / flow_acceleration.
        self._book_imb_history: dict[str, list] = {}
        self._prev_trend: dict[str, str] = {}        # stream_symbol -> last trend label (reversal)
        
        # Level 1 options subscription for continuous ATM flow
        self._options_subscribed_symbols: set[str] = set()
        self._options_level_one_data: dict[str, dict] = {}  # store latest L1 options data

    @property
    def symbol(self) -> str | None:
        return self._symbol

    @property
    def last_price(self) -> float | None:
        return self._last_price

    @property
    def ticks_received(self) -> int:
        with self._lock:
            return self._ticks_received

    @property
    def has_data(self) -> bool:
        with self._lock:
            return self._current_bar is not None or not self._df.empty

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def get_candles(self) -> pd.DataFrame:
        """Return snapshot of completed 1s bars plus the live incomplete bar."""
        with self._lock:
            if self._df.empty and self._current_bar is None:
                return pd.DataFrame()

            out = self._df.copy()
            if self._current_bar is not None:
                row = pd.DataFrame(
                    [[
                        self._current_bar["open"],
                        self._current_bar["high"],
                        self._current_bar["low"],
                        self._current_bar["close"],
                        self._current_bar["volume"],
                        self._current_bar["buy_vol"],
                        self._current_bar["sell_vol"],
                    ]],
                    columns=["open", "high", "low", "close", "volume", "buy_vol", "sell_vol"],
                    index=pd.Index([self._current_bucket], name="datetime"),
                )
                out = pd.concat([out, row])
            return out

    def start(self, symbol: str):
        if symbol == self._symbol and self._running:
            return
        self._stop_locked()
        with self._lock:
            self._df = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume", "buy_vol", "sell_vol"]
            )
            self._df.index.name = "datetime"
            self._current_bucket = None
            self._current_bar = None
            self._ticks_received = 0
            self._bid_price = None
            self._ask_price = None
            self._last_price = None
        self._symbol = symbol
        self._running = True
        self._stream_task = asyncio.run_coroutine_threadsafe(
            self._run(), self._loop,
        )

    def stop(self):
        self._stop_locked()

    def _stop_locked(self):
        self._running = False
        self._sc = None
        # Cancel the old streaming task so it doesn't linger on the event loop
        if self._stream_task is not None:
            self._stream_task.cancel()
            self._stream_task = None

    # ------------------------------------------------------------------ #
    # Internal: async websocket session
    # ------------------------------------------------------------------ #

    async def _run(self):
        try:
            await self._stream()
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            with self._lock:
                self._running = False
                self._connected = False

    def _aggregate_tick(self, tick_time_ms: int, price: float, size: int):
        """Merge a raw tick into the 1-second OHLC aggregation.  Called
        with *self._lock* held."""
        direction = self._infer_dir(price)
        bucket = (tick_time_ms // 1000) * 1000

        if bucket != self._current_bucket:
            # Finalise previous bucket
            if self._current_bar is not None:
                row = pd.DataFrame(
                    [[
                        self._current_bar["open"],
                        self._current_bar["high"],
                        self._current_bar["low"],
                        self._current_bar["close"],
                        self._current_bar["volume"],
                        self._current_bar["buy_vol"],
                        self._current_bar["sell_vol"],
                    ]],
                    columns=["open", "high", "low", "close", "volume", "buy_vol", "sell_vol"],
                    index=pd.Index([self._current_bucket], name="datetime"),
                )
                self._df = pd.concat([self._df, row])
                if len(self._df) > MAX_BAR_ROWS:
                    self._df = self._df.iloc[-MAX_BAR_ROWS:]

            # Start new bucket
            self._current_bucket = bucket
            bv = size if direction == "buy" else 0
            sv = size if direction == "sell" else 0
            self._current_bar = {
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": size,
                "buy_vol": bv,
                "sell_vol": sv,
            }
        else:
            # Update existing bucket
            bar = self._current_bar
            if price > bar["high"]:
                bar["high"] = price
            if price < bar["low"]:
                bar["low"] = price
            bar["close"] = price
            bar["volume"] += size
            if direction == "buy":
                bar["buy_vol"] += size
            elif direction == "sell":
                bar["sell_vol"] += size
            else:
                # Unknown direction — split evenly
                bar["buy_vol"] += size // 2
                bar["sell_vol"] += size - (size // 2)

    def _infer_dir(self, price: float) -> str:
        if self._bid_price is not None and self._ask_price is not None:
            spread = self._ask_price - self._bid_price
            if spread > 0:
                mid = (self._ask_price + self._bid_price) / 2
                return "buy" if price >= mid else "sell"
        return ""

    async def _stream(self):
        # Close stale httpx connections that may carry async primitives
        # from a previous event loop.  Access self._client.session._transport
        # (the AsyncHTTPTransport) rather than self._client._transport
        # because the Schwab AsyncClient stores its httpx session at .session,
        # and the transport pool lives on that session.
        try:
            transport = getattr(self._client.session, "_transport", None)
            if transport is not None:
                await transport.aclose()
        except Exception:
            pass

        sc = StreamClient(self._client, enforce_enums=False)
        with self._lock:
            self._sc = sc

        # ---- Level 1 equity handler (trades + quotes) ----------------- #
        def _l1_handler(msg):
            with self._lock:
                for c in msg.get("content", []):
                    self._ticks_received += 1

                    # Capture latest bid/ask for direction inference
                    bid = c.get("BID_PRICE", None)
                    ask = c.get("ASK_PRICE", None)
                    if bid is not None:
                        self._bid_price = float(bid)
                    if ask is not None:
                        self._ask_price = float(ask)

                    t = c.get("TRADE_TIME_MILLIS", 0)
                    price = c.get("LAST_PRICE", None)
                    if price is not None:
                        self._last_price = float(price)
                    if price is None:
                        continue  # not a trade update
                    size = c.get("LAST_SIZE", 0) or 0
                    try:
                        self._aggregate_tick(int(t), float(price), int(size))
                    except Exception:
                        pass

        # ---- Level 1 options handler (trades + quotes) ------------------ #
        def _l1_options_handler(msg):
            with self._lock:
                for c in msg.get("content", []):
                    sym = c.get("key", "") or c.get("SYMBOL", "")
                    if not sym:
                        continue
                    
                    # Normalize symbol for consistency
                    sym_norm = sym.replace(" ", "")
                    
                    # Store latest L1 options data
                    self._options_level_one_data[sym_norm] = {
                        "bid": float(c.get("BID_PRICE", 0)) if c.get("BID_PRICE") else None,
                        "ask": float(c.get("ASK_PRICE", 0)) if c.get("ASK_PRICE") else None,
                        "last": float(c.get("LAST_PRICE", 0)) if c.get("LAST_PRICE") else None,
                        "bid_size": float(c.get("BID_SIZE", 0)) if c.get("BID_SIZE") else None,
                        "ask_size": float(c.get("ASK_SIZE", 0)) if c.get("ASK_SIZE") else None,
                        "time": c.get("TRADE_TIME_MILLIS", 0),
                        "trade_price": float(c.get("LAST_PRICE", 0)) if c.get("LAST_PRICE") else None,
                    }

        # ---- Level 2 book handlers (one message may carry many symbols) - #
        def _options_book_handler(msg):
            with self._lock:
                for content in (msg.get("content") or []):
                    sym = content.get("SYMBOL")
                    if sym is None:
                        continue
                    self._books_options[sym] = content
                    self._update_book_imbalance(sym)

        # Add handlers before subscribing
        sc.add_level_one_equity_handler(_l1_handler)
        sc.add_level_one_option_handler(_l1_options_handler)
        sc.add_options_book_handler(_options_book_handler)

        try:
            await sc.login()
        except Exception as e:
            with self._lock:
                self._last_error = f"Login failed: {e}"
            return

        # Subscribe to all services: Level 1 for the chart symbol + Level 2
        # books for the chart symbol and every tracked ticker + Level 1 options
        # for ATM option flow.
        while self._running and self._symbol:
            try:
                await sc.level_one_equity_subs([self._symbol])
                await self._subscribe_options(sc)
                await self._subscribe_books(sc)
            except Exception as e:
                with self._lock:
                    self._last_error = f"Subs failed: {e}"
                await asyncio.sleep(2)
                continue
            break

        with self._lock:
            self._connected = True

        # Event loop — process incoming messages
        while self._running:
            try:
                await sc.handle_message()
            except Exception as e:
                with self._lock:
                    self._last_error = f"handle_message: {e}"
                await asyncio.sleep(3)
                if self._running and self._symbol:
                    try:
                        await sc.login()
                        # Re-subscribe
                        while self._running and self._symbol:
                            try:
                                await sc.level_one_equity_subs([self._symbol])
                                await self._subscribe_options(sc)
                                await self._subscribe_books(sc)
                            except Exception:
                                await asyncio.sleep(2)
                                continue
                            break
                        with self._lock:
                            self._connected = True
                        # Notify listeners (e.g. ATM option service)
                        for cb in self._on_reconnect_cbs:
                            try:
                                result = cb()
                                if asyncio.iscoroutine(result):
                                    asyncio.ensure_future(result)
                            except Exception:
                                pass
                    except Exception as e2:
                        with self._lock:
                            self._connected = False
                            self._last_error = f"re-login failed: {e2}"

    # Connection state tracking
    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_stream_client(self):
        """Return the shared StreamClient so other services (e.g. ATM option
        flow) can add handlers and subscribe on the same WebSocket connection."""
        with self._lock:
            return self._sc

    def on_reconnect(self, callback):
        """Register a callback (sync or async) to invoke after a successful
        re-login and re-subscription.  Used by AtmOptionVolumeService to
        re-subscribe its LEVELONE_OPTIONS after the equity feed reconnects."""
        self._on_reconnect_cbs.append(callback)

    # ------------------------------------------------------------------ #
    # Level 2 book trend (subscribed per tracked ticker)
    # ------------------------------------------------------------------ #

    @property
    def book_symbols(self) -> set[str]:
        """Stream symbols currently subscribed for Level 2 books."""
        with self._lock:
            return set(self._book_symbols)

    def subscribe_book_symbols(self, stream_symbols: list[str]) -> None:
        """Ensure Level 2 books are subscribed for exactly *stream_symbols*.

        Safe to call frequently (e.g. once per grid refresh): it diffs
        against the current subscription set and only issues SUBS for new
        symbols and UNSUBS for dropped symbols.  The Schwab calls are
        scheduled on the background stream loop and never block the caller;
        a symbol's book will not be populated until the first update lands,
        so ``trend_data`` is None-safe in the meantime.
        """
        want = [s for s in stream_symbols if s]
        with self._lock:
            to_add = [s for s in want if s not in self._book_symbols]
            to_remove = [s for s in self._book_symbols if s not in want]
            for s in to_add:
                self._book_symbols.add(s)
            for s in to_remove:
                self._book_symbols.discard(s)
                self._books_nasdaq.pop(s, None)
                self._books_nyse.pop(s, None)
                self._books_options.pop(s, None)
                self._book_imb_history.pop(s, None)
                self._prev_trend.pop(s, None)
            if not to_add and not to_remove:
                return
            sc = self._sc
            loop = self._loop
        # Fire-and-forget: schedule the async SUBS/UNSUBS on the stream loop.
        if sc is not None and loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._apply_book_subscriptions(to_add, to_remove), loop)

    async def _apply_book_subscriptions(self, to_add, to_remove):
        try:
            sc = self._sc
            if sc is None:
                return
            if to_add:
                await sc.nasdaq_book_subs(to_add)
                await sc.nyse_book_subs(to_add)
                await sc.options_book_subs(to_add)
            if to_remove:
                await sc.nasdaq_book_unsubs(to_remove)
                await sc.nyse_book_unsubs(to_remove)
                await sc.options_book_unsubs(to_remove)
        except Exception:
            import traceback
            traceback.print_exc()

    async def _subscribe_books(self, sc: StreamClient):
        """Subscribe NASDAQ + NYSE + OPTIONS books for the chart symbol and every
        tracked ticker.  Called from ``_stream`` right after login and
        after each re-login so tracked-ticker books survive reconnects."""
        book_syms = [self._symbol] if self._symbol else []
        with self._lock:
            book_syms += [s for s in self._book_symbols if s and s != self._symbol]
        if book_syms:
            await sc.nasdaq_book_subs(book_syms)
            await sc.nyse_book_subs(book_syms)
            await sc.options_book_subs(book_syms)
    
    async def _subscribe_options(self, sc: StreamClient):
        """Subscribe to Level 1 options for the chart symbol and every
        tracked ticker to provide continuous ATM flow.
        Called from ``_stream`` right after login and
        after each re-login so options survive reconnects."""
        option_syms = [self._symbol] if self._symbol else []
        with self._lock:
            option_syms += [s for s in self._book_symbols if s and s != self._symbol]
        if option_syms:
            await sc.level_one_option_subs(option_syms)

    def _book_imbalance_for_symbol(self, symbol: str) -> float | None:
        """Aggregate Level-2 bid/ask volume imbalance for one stream symbol,
        summing across the OPTIONS book only.  Returns a ratio in
        [-1, 1] (positive = bullish pressure) or None when no book yet.

        Assumes *self._lock* is held (called from handlers and trend_data).
        """
        bid_vol = 0.0
        ask_vol = 0.0
        for books in (self._books_options,):
            content = books.get(symbol)
            if not content:
                continue
            for ask in (content.get("ASKS") or []):
                try:
                    ask_vol += float(ask.get("TOTAL_VOLUME") or 0)
                except (TypeError, ValueError):
                    pass
            for bid in (content.get("BIDS") or []):
                try:
                    bid_vol += float(bid.get("TOTAL_VOLUME") or 0)
                except (TypeError, ValueError):
                    pass
        total = bid_vol + ask_vol
        if total <= 0:
            return None
        return (bid_vol - ask_vol) / total

    def _update_book_imbalance(self, symbol: str) -> None:
        """Recompute and record the book-imbalance history for a symbol.

        Assumes *self._lock* is held (called from the book handlers).
        """
        ratio = self._book_imbalance_for_symbol(symbol)
        if ratio is None:
            return
        now = _time_mod.time()
        hist = self._book_imb_history.setdefault(symbol, [])
        hist.append((now, ratio))
        cutoff = now - 60
        while hist and hist[0][0] < cutoff:
            hist.pop(0)

    def _flow_speed_and_accel(self, symbol: str) -> tuple[float, float]:
        """Derive flow_speed / flow_acceleration from the L2 book-imbalance
        series, mirroring the legacy option-flow momentum math so the same
        sign / >0.3 thresholds still apply downstream.

        Assumes *self._lock* is held.
        """
        history = self._book_imb_history.get(symbol)
        if not history or len(history) < 2:
            return 0.0, 0.0
        now = _time_mod.time()
        while history and history[0][0] < now - 60:
            history.pop(0)
        if len(history) < 2:
            return 0.0, 0.0
        segment_size = max(1, len(history) // 2)
        older_first = history[0][1]
        newer_first = history[-segment_size][1]
        flow_speed = newer_first - older_first
        previous_flow = history[segment_size - 1][1] - history[0][1]
        recent_flow = history[-1][1] - history[-segment_size][1]
        flow_acceleration = recent_flow - previous_flow
        return flow_speed, flow_acceleration

    def trend_data(self, stream_symbol: str) -> dict:
        """L2-sourced trend snapshot for a stream symbol, matching the dict
        shape previously produced by
        ``StreamingService.get_ticker_trend_data``:

            {trend, book_imbalance, flow_speed, flow_acceleration,
             trend_reversal, book_imbalance_history, flow_history}

        ``book_imbalance`` is the current NASDAQ+NYSE volume ratio;
        ``flow_speed`` / ``flow_acceleration`` are the first and second
        differences of that ratio over the trailing 60s window.  All trend
        thresholds (>±0.3) match the option-flow derivation, so downstream
        consumers (``flow.classify_trend_signal``, the Telegram formatter,
        and the grid styler) need no changes.
        """
        with self._lock:
            ratio = self._book_imbalance_for_symbol(stream_symbol)
            history = list(self._book_imb_history.get(stream_symbol) or [])
            flow_speed, flow_acceleration = self._flow_speed_and_accel(stream_symbol)

            # trend direction from L2 book pressure (same thresholds as before)
            if ratio is None or len(history) < 2:
                trend = "flat"
            elif ratio > 0.3 and flow_speed > 0 and flow_acceleration > 0:
                trend = "up"
            elif ratio < -0.3 and flow_speed < 0 and flow_acceleration < 0:
                trend = "down"
            elif ratio > 0.3 and flow_speed > 0:
                trend = "up"
            elif ratio < -0.3 and flow_speed < 0:
                trend = "down"
            else:
                trend = "flat"

            prev = self._prev_trend.get(stream_symbol)
            self._prev_trend[stream_symbol] = trend

        reversal: str | None = None
        if prev is not None and prev != trend:
            if prev == "down" and trend == "up":
                reversal = "bullish"
            elif prev == "up" and trend == "down":
                reversal = "bearish"

        now = _time_mod.time()
        book_imbalance_history = [(t, r) for (t, r) in history if t >= now - 60]
        return {
            "trend": trend,
            "book_imbalance": ratio,
            "flow_speed": flow_speed,
            "flow_acceleration": flow_acceleration,
            "trend_reversal": reversal,
            "book_imbalance_history": book_imbalance_history,
            "flow_history": [],
        }


    def get_ticker_trend_data(self, display_symbol: str) -> dict:
        """L2-sourced trend dict for a display symbol.

        Convenience wrapper: maps the display symbol to its stream symbol
        (NASDAQ/NYSE LEVEL2 book key) via ``_get_stream_symbol`` and delegates
        to ``trend_data``.  Returns neutral defaults (trend flat, book_imbalance
        None, flow_speed and flow_acceleration 0) when no book has been
        subscribed, since ``trend_data`` guards the empty-history case.
        """
        return self.trend_data(_get_stream_symbol(display_symbol))
