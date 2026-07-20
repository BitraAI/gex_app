import asyncio
import threading

import pandas as pd
from schwab.streaming import StreamClient

MAX_ROWS = 200


class StreamingService:
    """Subscribes to Schwab LEVELONE_EQUITIES, NASDAQ_BOOK, NYSE_BOOK.
    Extracts raw tick data (LAST_PRICE + TRADE_TIME_MILLIS + LAST_SIZE)
    plus BID_PRICE/ASK_PRICE to infer trade direction, and aggregates
    into 1-second OHLCV bars with buy/sell volume split for delta.
    Level 2 order book depth is stored separately."""

    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop: asyncio.AbstractEventLoop = loop
        self._sc: StreamClient | None = None
        self._symbol: str | None = None
        self._running = False
        self._stream_task: asyncio.Task | None = None

        # Debug state
        self._ticks_received = 0
        self._handler_errors = 0
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

        # Level 2 order book snapshots
        self._nasdaq_book: dict | None = None
        self._nyse_book: dict | None = None

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

    def load_historical(self, candles: list[dict]):
        pass  # No historical preload — live ticks only

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

    def get_level2_snapshot(self) -> dict:
        """Return latest Level 2 order book data."""
        with self._lock:
            return {
                "nasdaq": self._nasdaq_book,
                "nyse": self._nyse_book,
                "bid": self._bid_price,
                "ask": self._ask_price,
            }

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
            self._handler_errors = 0
            self._bid_price = None
            self._ask_price = None
            self._last_price = None
            self._nasdaq_book = None
            self._nyse_book = None
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
                if len(self._df) > MAX_ROWS:
                    self._df = self._df.iloc[-MAX_ROWS:]

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
                        self._handler_errors += 1

        # ---- NASDAQ book handler (Level 2) ---------------------------- #
        def _nasdaq_handler(msg):
            with self._lock:
                for c in msg.get("content", []):
                    self._nasdaq_book = c

        # ---- NYSE book handler (Level 2) ------------------------------ #
        def _nyse_handler(msg):
            with self._lock:
                for c in msg.get("content", []):
                    self._nyse_book = c

        # Add handlers before subscribing
        sc.add_level_one_equity_handler(_l1_handler)
        sc.add_nasdaq_book_handler(_nasdaq_handler)
        sc.add_nyse_book_handler(_nyse_handler)

        try:
            await sc.login()
        except Exception as e:
            with self._lock:
                self._last_error = f"Login failed: {e}"
            return

        # Subscribe to all three services
        while self._running and self._symbol:
            try:
                await sc.level_one_equity_subs([self._symbol])
                await sc.nasdaq_book_subs([self._symbol])
                await sc.nyse_book_subs([self._symbol])
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
                                await sc.nasdaq_book_subs([self._symbol])
                                await sc.nyse_book_subs([self._symbol])
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

    def get_stats(self) -> dict:
        """Return current streaming stats for monitoring."""
        return {
            "ticks_received": self._ticks_received,
            "handler_errors": self._handler_errors,
            "connected": self._connected,
            "running": self._running,
            "symbol": self._symbol,
            "df_rows": len(self._df) if not self._df.empty else 0,
            "has_current_bar": self._current_bar is not None,
            "has_nasdaq_book": self._nasdaq_book is not None,
            "has_nyse_book": self._nyse_book is not None,
        }
