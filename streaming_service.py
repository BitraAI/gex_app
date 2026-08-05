import asyncio
import threading
import time as _time_mod

import pandas as pd
from schwab.streaming import StreamClient
from websockets.exceptions import ConnectionClosed

from _constants import MAX_BAR_ROWS
from option_streaming_service import _get_stream_symbol


class StreamingService:
    """Subscribes to Schwab LEVELONE_EQUITIES plus OPTIONS_BOOK for the chart
    symbol and every tracked ticker.  Extracts raw tick data
    (LAST_PRICE + TRADE_TIME_MILLIS + LAST_SIZE) plus BID_PRICE/ASK_PRICE to
    infer trade direction, and aggregates into 1-second OHLCV bars with a
    buy/sell volume split for delta.

    The Level 2 OPTIONS books (keyed per underlying stream symbol) are the
    single source for book_imbalance / flow_speed / flow_acceleration — see
    ``trend_data``.  OPTIONS_BOOK requires full OCC option-contract symbols
    (not underlyings), so the ATM call/put contracts for every tracked
    ticker are subscribed (see ``set_book_contracts``) and their resting
    volume is aggregated per underlying so the per-ticker Order Flow grid
    and the wall-zone / Telegram alerts all consume L2 book pressure rather
    than option-quote-derived imbalance.
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

        # Level 2 order book snapshots.  OPTIONS_BOOK messages are keyed by
        # OCC option-contract symbol (e.g. "AAPL  260905C00195000"); the
        # per-underlying subscription/aggregation maps are kept alongside.
        self._book_symbols: set[str] = set()        # underlying stream symbols to keep books for
        self._books_options: dict[str, dict] = {}   # OCC contract symbol -> latest OPTIONS_BOOK content msg
        # underlying stream symbol -> [OCC contract symbols] to subscribe, and
        # the reverse lookup (both padded and space-stripped OCC forms) used to
        # route incoming book messages back to their underlying for aggregation.
        self._book_contracts: dict[str, list[str]] = {}
        self._contract_to_underlying: dict[str, str] = {}
        self._subscribed_contracts: set[str] = set()  # contracts currently subscribed via OPTIONS_BOOK
        # Per-symbol L2 book-imbalance history: stream_symbol -> list[(ts, ratio)],
        # pruned to the last 60s, used to derive flow_speed / flow_acceleration.
        self._book_imb_history: dict[str, list] = {}
        # Per-symbol L2 resting-depth history: stream_symbol -> list[(ts, bid_vol
        # + ask_vol at the best levels)], pruned to 60s, used to derive
        # liquidity_flow (net liquidity added/drained over the window).
        self._book_depth_history: dict[str, list] = {}
        self._prev_trend: dict[str, str] = {}        # stream_symbol -> last trend label (reversal)

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

        # ---- Level 2 book handlers (one message may carry many symbols) - #
        def _options_book_handler(msg):
            with self._lock:
                for content in (msg.get("content") or []):
                    # Schwab book content carries the symbol either as the
                    # numeric SYMBOL field (0) or as the non-numeric "key"
                    # member; some feeds omit one or the other.
                    sym = content.get("SYMBOL") or content.get("key")
                    if sym is None:
                        continue
                    # Store per OCC contract; also index by the stripped form
                    # in case the root padding is dropped in some messages.
                    self._books_options[sym] = content
                    self._books_options[sym.replace(" ", "")] = content
                    # Route back to the underlying so the aggregated
                    # book-imbalance history for the ticker advances.
                    und = self._contract_to_underlying.get(sym)
                    if und is None:
                        und = self._contract_to_underlying.get(sym.replace(" ", ""))
                    if und is not None:
                        self._update_book_imbalance(und)

        # Add handlers before subscribing
        sc.add_level_one_equity_handler(_l1_handler)
        sc.add_options_book_handler(_options_book_handler)

        try:
            await sc.login()
        except Exception as e:
            with self._lock:
                self._last_error = f"Login failed: {e}"
            return

        # Subscribe to all services: Level 1 for the chart symbol + Level 2
        # books for the chart symbol and every tracked ticker.
        while self._running and self._symbol:
            try:
                await sc.level_one_equity_subs([self._symbol])
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

    def subscribe_book_symbols(self, stream_symbols: list[str]) -> None:
        """Declare the set of underlying stream symbols we want to keep
        Level 2 books for.

        Safe to call frequently (e.g. once per grid refresh): it diffs
        against the current key set and drops book state (histories and
        snapshots) for symbols that are no longer tracked.  The actual
        OPTIONS_BOOK subscription symbols are the ATM contracts registered
        via ``set_book_contracts`` — callers should update both together.
        """
        want = [s.upper().lstrip("$") for s in stream_symbols if s]
        with self._lock:
            to_add = [s for s in want if s not in self._book_symbols]
            to_remove = [s for s in self._book_symbols if s not in want]
            for s in to_add:
                self._book_symbols.add(s)
            for s in to_remove:
                self._book_symbols.discard(s)
                self._book_imb_history.pop(s, None)
                self._book_depth_history.pop(s, None)
                self._prev_trend.pop(s, None)
                for c in self._book_contracts.get(s, []):
                    self._books_options.pop(c, None)
                    self._books_options.pop(c.replace(" ", ""), None)

    def set_book_contracts(self, contracts: dict[str, list[str]]) -> None:
        """Register the OCC option-contract symbols to stream via
        OPTIONS_BOOK, keyed by underlying stream symbol, e.g.::

            {"SPY": ["SPY  260905C00550000", "SPY  260905P00550000"]}

        OPTIONS_BOOK subscriptions require full OCC option-contract symbols,
        not underlyings, so this mapping is what makes the book feed arrive.
        Safe to call on every grid refresh: when the registered set changes
        it issues a full ``OPTIONS_BOOK`` SUBS (Schwab's SUBS replaces the
        feed, so dropped contracts are torn down server-side) plus UNSUBS for
        any contracts that moved.  Books and history stay keyed by the
        *underlying* stream symbol, so ``trend_data`` and the Order Flow grid
        are unchanged.
        """
        want = {}
        for und, occ in (contracts or {}).items():
            und = und.upper().lstrip("$")
            occ = [c for c in occ if c]
            if und and occ:
                want[und] = occ
        with self._lock:
            if want == self._book_contracts:
                return
            self._book_contracts = want
            self._contract_to_underlying = {
                c: und for und, occ in want.items() for c in occ
            }
            # Also route space-stripped OCC symbols (some book messages drop
            # the root padding) back to the same underlying.
            self._contract_to_underlying.update({
                c.replace(" ", ""): und
                for und, occ in want.items() for c in occ
            })
            canonical = {c for occ in want.values() for c in occ}
            to_unsub = [c for c in self._subscribed_contracts if c not in canonical]
            for c in to_unsub:
                # Drop stale snapshots for contracts that changed strike/expiry.
                self._books_options.pop(c, None)
                self._books_options.pop(c.replace(" ", ""), None)
            self._subscribed_contracts = canonical
            # Full authoritative set: SUBS replaces the feed, so always send
            # the complete current set to self-heal any dropped subscription.
            to_sub = [c for occ in want.values() for c in occ]
            sc = self._sc
            loop = self._loop
        if sc is not None and loop is not None and (to_sub or to_unsub):
            asyncio.run_coroutine_threadsafe(
                self._apply_book_subscriptions(to_sub, to_unsub), loop)

    async def _apply_book_subscriptions(self, subscribe, unsubscribe):
        sc = self._sc
        if sc is None:
            return
        # Socket not open yet (initial login or re-login in progress): skip.
        # All subscribed OCC contracts are re-subscribed after the next login
        # via _subscribe_books, so nothing is lost by dropping this send.
        if getattr(sc, "_socket", None) is None:
            return
        try:
            if subscribe:
                await sc.options_book_subs(subscribe)
            if unsubscribe:
                await sc.options_book_unsubs(unsubscribe)
        except ConnectionClosed:
            # Expected race: the websocket was torn down (e.g. re-login or a
            # normal server-side close) between scheduling this send and it
            # running — "received 1000 (OK); then sent 1000 (OK)".  The
            # stream loop re-subscribes all contracts after the next login
            # via _subscribe_books, so nothing is lost.
            pass
        except Exception as e:
            # Don't wedge silently: if a SUBS is rejected (bad symbol, budget,
            # socket race) the next refresh's full SUBS retries it.  Surface
            # it so the failure is visible instead of invisible.
            print(f"[StreamingService] OPTIONS_BOOK subscribe error: {e}")

    async def _subscribe_books(self, sc: StreamClient):
        """Subscribe OPTIONS_BOOK for the ATM OCC contracts of the chart
        symbol and every tracked ticker.  Called from ``_stream`` right
        after login and after each re-login so tracked-ticker books survive
        reconnects."""
        with self._lock:
            underlyings = set(self._book_symbols)
            if self._symbol:
                underlyings.add(self._symbol)
            contracts = []
            seen = set()
            for und in underlyings:
                for c in self._book_contracts.get(und, []):
                    if c not in seen:
                        seen.add(c)
                        contracts.append(c)
        if contracts:
            await sc.options_book_subs(contracts)

    def _book_volume_for_symbol(self, symbol: str) -> tuple[float, float] | None:
        """Sum Level-2 OPTIONS-book resting volume for one underlying stream
        symbol, aggregated across the ATM call/put OCC contracts registered
        for it: TOTAL_VOLUME across the best bid levels and best ask levels.
        Returns ``(bid_vol, ask_vol)`` or None when no contract book has
        arrived yet.

        Assumes *self._lock* is held (called from handlers and trend_data).
        """
        contracts = self._book_contracts.get(symbol)
        if not contracts:
            return None
        bid_vol = 0.0
        ask_vol = 0.0
        found = False
        for c in contracts:
            content = self._books_options.get(c)
            if content is None:
                content = self._books_options.get(c.replace(" ", ""))
            if not content:
                continue
            found = True
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
        if not found:
            return None
        return bid_vol, ask_vol

    def _book_imbalance_for_symbol(self, symbol: str) -> float | None:
        """Aggregate Level-2 bid/ask volume imbalance for one stream symbol,
        summing across the OPTIONS book only.  Returns a ratio in
        [-1, 1] (positive = bullish pressure) or None when no book yet.

        Assumes *self._lock* is held (called from handlers and trend_data).
        """
        vols = self._book_volume_for_symbol(symbol)
        if vols is None:
            return None
        bid_vol, ask_vol = vols
        total = bid_vol + ask_vol
        if total <= 0:
            return None
        return (bid_vol - ask_vol) / total

    def _update_book_imbalance(self, symbol: str) -> None:
        """Recompute and record the book-imbalance and resting-depth history
        for a symbol.

        Assumes *self._lock* is held (called from the book handlers).
        """
        vols = self._book_volume_for_symbol(symbol)
        if vols is None:
            return
        bid_vol, ask_vol = vols
        total = bid_vol + ask_vol
        if total <= 0:
            return
        now = _time_mod.time()
        hist = self._book_imb_history.setdefault(symbol, [])
        hist.append((now, (bid_vol - ask_vol) / total))
        cutoff = now - 60
        while hist and hist[0][0] < cutoff:
            hist.pop(0)
        depth = self._book_depth_history.setdefault(symbol, [])
        depth.append((now, total))
        while depth and depth[0][0] < cutoff:
            depth.pop(0)

    def _flow_speed_and_accel(self, symbol: str) -> tuple[float, float]:
        """Derive flow_speed / flow_acceleration from the L2 book-imbalance
        series.

        ``flow_speed`` is the first difference of the ratio over the trailing
        60 s window (``history[-1] - history[0]``).  ``flow_acceleration`` is
        the second difference: the change over the recent half of the window
        minus the change over the older half.  The halves are split at the
        exact **time** midpoint of the window (``mid_ts``), so older/recent
        cover equal wall-clock spans even when book updates arrive in bursts
        rather than uniformly.  Sign semantics match the legacy option-flow
        momentum math so the same >0.3 thresholds apply downstream.

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
        # first difference of the ratio over the trailing 60 s window
        flow_speed = history[-1][1] - history[0][1]
        # second difference: (change over recent half) - (change over older
        # half).  Split at the window's midpoint by timestamp so the halves
        # are time-balanced regardless of sampling cadence.  `mid` is the
        # first sample at/after mid_ts, clamped to keep both halves non-empty.
        mid_ts = history[0][0] + (history[-1][0] - history[0][0]) / 2.0
        mid = len(history) - 1
        for i in range(1, len(history)):
            if history[i][0] >= mid_ts:
                mid = i
                break
        mid = max(1, min(len(history) - 1, mid))
        previous_flow = history[mid - 1][1] - history[0][1]
        recent_flow = history[-1][1] - history[mid][1]
        flow_acceleration = recent_flow - previous_flow
        return flow_speed, flow_acceleration

    def _liquidity_flow(self, symbol: str) -> float | None:
        """Net L2 liquidity change over the trailing 60 s: resting depth at
        the best levels now minus the depth at the window start (contracts
        of liquidity added [+]/drained [-]).  Returns None when fewer than
        2 depth samples exist.

        Positive = liquidity is being posted (book refilling); negative =
        liquidity is being consumed (book draining — a break risk).

        Assumes *self._lock* is held.
        """
        depth = self._book_depth_history.get(symbol)
        if not depth or len(depth) < 2:
            return None
        now = _time_mod.time()
        while depth and depth[0][0] < now - 60:
            depth.pop(0)
        if len(depth) < 2:
            return None
        return depth[-1][1] - depth[0][1]

    def trend_data(self, stream_symbol: str) -> dict:
        """L2-sourced trend snapshot for a stream symbol, matching the dict
        shape previously produced by
        ``StreamingService.get_ticker_trend_data``:

             {trend, book_imbalance, flow_speed, flow_acceleration,
              liquidity_flow, trend_reversal, book_imbalance_history,
              flow_history}

        ``book_imbalance`` is the current L2 OPTIONS-book bid/ask volume
        ratio, aggregated across the ATM call/put OCC contracts subscribed
        for the symbol (``_books_options`` — see
        ``_book_imbalance_for_symbol``); ``flow_speed`` /
        ``flow_acceleration`` are the first and second differences of that
        ratio over the trailing 60s window; ``liquidity_flow`` is the net
        change in resting depth at the best levels over the same window
        (contracts added/drained).  All trend thresholds (>±0.3)
        match the option-flow derivation, so downstream consumers
        (``flow.maybe_fire_wall_zone_alerts`` and the grid Trend column,
        plus the Telegram formatter) consume the trend and trend_reversal
        fields directly.
        """
        with self._lock:
            ratio = self._book_imbalance_for_symbol(stream_symbol)
            history = list(self._book_imb_history.get(stream_symbol) or [])
            flow_speed, flow_acceleration = self._flow_speed_and_accel(stream_symbol)
            liquidity_flow = self._liquidity_flow(stream_symbol)

            # trend direction from L2 book pressure (same thresholds as before)
            if ratio is None or len(history) < 2:
                trend = "flat"
            elif ratio > 0.3 and flow_speed > 0 and flow_acceleration > 0:
                trend = "UP"
            elif ratio < -0.3 and flow_speed < 0 and flow_acceleration < 0:
                trend = "DOWN"
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
            "liquidity_flow": liquidity_flow,
            "trend_reversal": reversal,
            "book_imbalance_history": book_imbalance_history,
            "flow_history": [],
        }


    def get_ticker_trend_data(self, display_symbol: str) -> dict:
        """L2-sourced trend dict for a display symbol.

        Convenience wrapper: maps the display symbol to its stream symbol
        (the L2 OPTIONS-book key) via ``_get_stream_symbol`` and delegates
        to ``trend_data``.  Returns neutral defaults (trend flat, book_imbalance
        None, flow_speed and flow_acceleration 0) when no book has been
        subscribed, since ``trend_data`` guards the empty-history case.
        """
        return self.trend_data(_get_stream_symbol(display_symbol))
