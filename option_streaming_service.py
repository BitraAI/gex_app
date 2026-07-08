import asyncio
import threading
import pandas as pd
from calculations import calculate_atm_strike

MAX_ROWS = 200


def _make_option_symbol(root: str, yymmdd: str, call_put: str, strike: float) -> str:
    root = root.ljust(6)[:6]
    cp = "C" if call_put.upper() == "C" else "P"
    strike_int = int(round(strike * 1000))
    return f"{root}{yymmdd}{cp}{strike_int:08d}"


class AtmOptionVolumeService:
    """Aggregates LEVELONE_OPTIONS trade ticks into 1-second bars with
    buy/sell volume split.  Uses a shared StreamClient (from the equity
    streaming service) instead of opening its own WebSocket connection."""

    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop: asyncio.AbstractEventLoop = loop
        self._symbol: str | None = None
        self._expiration: str | None = None  # "YYYY-MM-DD"
        self._running = False

        # Spot & ATM strike state
        self._spot: float = 0.0
        self._atm_strike: float = 0.0
        self._subscribed_call_sym: str | None = None
        self._subscribed_put_sym: str | None = None

        # Option bid/ask for direction inference
        self._call_bid: float | None = None
        self._call_ask: float | None = None
        self._put_bid: float | None = None
        self._put_ask: float | None = None

        # Aggregated 1-second bars
        self._df: pd.DataFrame = pd.DataFrame(
            columns=[
                "call_buy_vol", "call_sell_vol",
                "put_buy_vol", "put_sell_vol",
                "total_buy_vol", "total_sell_vol",
            ]
        )
        self._df.index.name = "datetime"
        self._lock = threading.Lock()

        # Current (incomplete) 1-second bucket
        self._current_bucket: int | None = None
        self._current_bar: dict | None = None

        # Streaming stats
        self._ticks_received = 0
        self._resubscribes = 0
        self._stream_client = None  # shared StreamClient reference

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def symbol(self) -> str | None:
        return self._symbol

    @property
    def atm_strike(self) -> float:
        with self._lock:
            return self._atm_strike

    @property
    def ticks_received(self) -> int:
        with self._lock:
            return self._ticks_received

    @property
    def has_data(self) -> bool:
        with self._lock:
            return self._current_bar is not None or not self._df.empty

    def update_spot(self, spot: float):
        """Called when the underlying spot price changes (e.g. from equity
        streaming).  If the ATM strike changes, triggers a re-subscription."""
        sc = None
        with self._lock:
            self._spot = spot
            new_strike = calculate_atm_strike(spot)
            if abs(new_strike - self._atm_strike) > 0.001:
                self._atm_strike = new_strike
                if self._running and self._expiration:
                    self._resubscribes += 1
                    sc = self._stream_client
            elif self._running and self._expiration and self._subscribed_call_sym is None:
                self._resubscribes += 1
                sc = self._stream_client
        if sc is not None:
            asyncio.run_coroutine_threadsafe(
                self._do_subscribe(sc), self._loop,
            )

    def get_candles(self) -> pd.DataFrame:
        """Return snapshot of completed 1s bars plus the live incomplete bar."""
        with self._lock:
            if self._df.empty and self._current_bar is None:
                return pd.DataFrame()

            out = self._df.copy()
            if self._current_bar is not None:
                row = pd.DataFrame(
                    [[
                        self._current_bar["call_buy_vol"],
                        self._current_bar["call_sell_vol"],
                        self._current_bar["put_buy_vol"],
                        self._current_bar["put_sell_vol"],
                        self._current_bar["total_buy_vol"],
                        self._current_bar["total_sell_vol"],
                    ]],
                    columns=[
                        "call_buy_vol", "call_sell_vol",
                        "put_buy_vol", "put_sell_vol",
                        "total_buy_vol", "total_sell_vol",
                    ],
                    index=pd.Index([self._current_bucket], name="datetime"),
                )
                out = pd.concat([out, row])
            return out

    def register(self, stream_client, symbol: str, expiration: str):
        """Register on a shared StreamClient (from the equity streaming
        service) and subscribe to ATM option symbols.

        This replaces the old ``start()`` method — no separate WebSocket
        connection is created.  The handler is added to the existing
        StreamClient and the subscription request is sent over the already-
        open connection.
        """
        self._stop_locked()
        with self._lock:
            self._df = pd.DataFrame(
                columns=[
                    "call_buy_vol", "call_sell_vol",
                    "put_buy_vol", "put_sell_vol",
                    "total_buy_vol", "total_sell_vol",
                ]
            )
            self._df.index.name = "datetime"
            self._current_bucket = None
            self._current_bar = None
            self._ticks_received = 0
            self._resubscribes = 0
            self._call_bid = None
            self._call_ask = None
            self._put_bid = None
            self._put_ask = None
            self._subscribed_call_sym = None
            self._subscribed_put_sym = None

        self._symbol = symbol
        self._expiration = expiration
        self._stream_client = stream_client

        # Register handler on the shared StreamClient
        stream_client.add_level_one_option_handler(self._make_handler())

        # Subscribe on the already-open connection
        asyncio.run_coroutine_threadsafe(
            self._do_subscribe(stream_client), self._loop,
        )

        self._running = True

    def _get_stream_client(self):
        with self._lock:
            return self._stream_client

    def stop(self):
        self._stop_locked()

    def _stop_locked(self):
        self._running = False
        self._subscribed_call_sym = None
        self._subscribed_put_sym = None
        self._stream_client = None

    # ------------------------------------------------------------------ #
    # Internal: handler & subscription
    # ------------------------------------------------------------------ #

    def _option_handler(self, msg):
        with self._lock:
            for c in msg.get("content", []):
                self._ticks_received += 1

                # Update bid/ask for direction inference
                bid = c.get("BID_PRICE")
                ask = c.get("ASK_PRICE")
                contract_type = c.get("CONTRACT_TYPE", "").upper()
                underlying = c.get("UNDERLYING_PRICE")

                if contract_type in ("CALL", "C"):
                    if underlying is not None:
                        self._spot = float(underlying)
                    if bid is not None:
                        self._call_bid = float(bid)
                    if ask is not None:
                        self._call_ask = float(ask)
                elif contract_type in ("PUT", "P"):
                    if underlying is not None:
                        self._spot = float(underlying)
                    if bid is not None:
                        self._put_bid = float(bid)
                    if ask is not None:
                        self._put_ask = float(ask)

                # Process trade
                price = c.get("LAST_PRICE")
                if price is None:
                    continue
                size = c.get("LAST_SIZE", 0) or 0
                t = c.get("TRADE_TIME_MILLIS", 0)
                try:
                    ct = c.get("CONTRACT_TYPE", "").upper()
                    self._aggregate_tick(
                        int(t), float(price), int(size),
                        "CALL" if ct in ("CALL", "C") else "PUT",
                    )
                except Exception:
                    pass

    def _make_handler(self):
        return self._option_handler

    async def _do_subscribe(self, sc):
        """Build current ATM option symbols and subscribe via the shared
        StreamClient *sc*."""
        with self._lock:
            spot = self._spot
            symbol = self._symbol
            expiration = self._expiration
            old_call = self._subscribed_call_sym
            old_put = self._subscribed_put_sym
        if not symbol or not expiration or spot <= 0:
            return

        # Parse expiration to YYMMDD
        parts = expiration.split("-")
        yymmdd = parts[0][2:] + parts[1] + parts[2]

        atm = calculate_atm_strike(spot)
        call_sym = _make_option_symbol(symbol, yymmdd, "C", atm)
        put_sym = _make_option_symbol(symbol, yymmdd, "P", atm)

        # Unsubscribe old symbols if different
        to_unsub = []
        if old_call and old_call != call_sym:
            to_unsub.append(old_call)
        if old_put and old_put != put_sym:
            to_unsub.append(old_put)
        if to_unsub:
            try:
                await sc.level_one_option_unsubs(to_unsub)
            except Exception:
                pass

        # Subscribe to new symbols
        new_syms = []
        if not old_call or old_call != call_sym:
            new_syms.append(call_sym)
        if not old_put or old_put != put_sym:
            new_syms.append(put_sym)

        if new_syms:
            try:
                await sc.level_one_option_subs(new_syms)
            except Exception:
                pass

        with self._lock:
            self._subscribed_call_sym = call_sym
            self._subscribed_put_sym = put_sym

    async def _do_resubscribe(self):
        pass  # re-subscription is triggered by update_spot, but since we no
              # longer own the StreamClient, re-subscribing needs the shared
              # client — handled via app.py feeding update_spot + re-register

    def _aggregate_tick(self, tick_time_ms: int, price: float, size: int, opt_type: str):
        """Merge a raw option tick into the 1-second OHLCV aggregation.
        opt_type: 'CALL' or 'PUT'.
        Called with self._lock held."""
        if opt_type == "CALL":
            direction = self._infer_dir(price, self._call_bid, self._call_ask)
        else:
            direction = self._infer_dir(price, self._put_bid, self._put_ask)

        bucket = (tick_time_ms // 1000) * 1000

        if bucket != self._current_bucket:
            if self._current_bar is not None:
                row = pd.DataFrame(
                    [[
                        self._current_bar["call_buy_vol"],
                        self._current_bar["call_sell_vol"],
                        self._current_bar["put_buy_vol"],
                        self._current_bar["put_sell_vol"],
                        self._current_bar["total_buy_vol"],
                        self._current_bar["total_sell_vol"],
                    ]],
                    columns=[
                        "call_buy_vol", "call_sell_vol",
                        "put_buy_vol", "put_sell_vol",
                        "total_buy_vol", "total_sell_vol",
                    ],
                    index=pd.Index([self._current_bucket], name="datetime"),
                )
                self._df = pd.concat([self._df, row])
                if len(self._df) > MAX_ROWS:
                    self._df = self._df.iloc[-MAX_ROWS:]

            # Start new bucket
            cbv = size if (opt_type == "CALL" and direction == "buy") else 0
            csv = size if (opt_type == "CALL" and direction == "sell") else 0
            pbv = size if (opt_type == "PUT" and direction == "buy") else 0
            psv = size if (opt_type == "PUT" and direction == "sell") else 0

            self._current_bucket = bucket
            self._current_bar = {
                "call_buy_vol": cbv,
                "call_sell_vol": csv,
                "put_buy_vol": pbv,
                "put_sell_vol": psv,
                "total_buy_vol": cbv + pbv,
                "total_sell_vol": csv + psv,
            }
        else:
            bar = self._current_bar
            if direction == "buy":
                bar["total_buy_vol"] += size
                if opt_type == "CALL":
                    bar["call_buy_vol"] += size
                else:
                    bar["put_buy_vol"] += size
            elif direction == "sell":
                bar["total_sell_vol"] += size
                if opt_type == "CALL":
                    bar["call_sell_vol"] += size
                else:
                    bar["put_sell_vol"] += size
            else:
                # Unknown — split evenly
                half = size // 2
                rem = size - half
                bar["total_buy_vol"] += half
                bar["total_sell_vol"] += rem
                if opt_type == "CALL":
                    bar["call_buy_vol"] += half
                    bar["call_sell_vol"] += rem
                else:
                    bar["put_buy_vol"] += half
                    bar["put_sell_vol"] += rem

    def _infer_dir(self, price: float, bid: float | None, ask: float | None) -> str:
        if bid is not None and ask is not None:
            spread = ask - bid
            if spread > 0:
                mid = (ask + bid) / 2
                return "buy" if price >= mid else "sell"
        return ""
