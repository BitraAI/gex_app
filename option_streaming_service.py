import asyncio
import json
import os
import threading
import pandas as pd
from calculations import calculate_atm_strike

MAX_ROWS = 200

TICKER_HISTORY_FILE = os.path.expanduser("~/.local/share/gex_app/ticker_history.json")
_STREAM_SYMBOL_MAP = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}


def _load_ticker_history() -> list[str]:
    try:
        with open(TICKER_HISTORY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _make_option_symbol(root: str, yymmdd: str, call_put: str, strike: float) -> str:
    root = root.ljust(6)[:6]
    cp = "C" if call_put.upper() == "C" else "P"
    strike_int = int(round(strike * 1000))
    return f"{root}{yymmdd}{cp}{strike_int:08d}"


def _get_stream_symbol(display_symbol: str) -> str:
    sym = display_symbol.upper().lstrip("$")
    return _STREAM_SYMBOL_MAP.get(sym, sym)


def _normalize_display_symbol(symbol: str) -> str:
    """Canonical display-key form used everywhere a per-ticker flow is
    looked up: strip leading '$' and uppercase.  Index symbols that map
    to an ETF proxy for streaming (SPX->SPY, RUT->IWM, NDX->QQQ) are
    kept AS-IS ('SPX'), because _ticker_flows is keyed by the user's
    original display symbol, NOT the stream symbol."""
    return (symbol or "").upper().lstrip("$")


def _find_flow_for_display(spots: dict, display_symbol: str) -> dict | None:
    """Return the matching _ticker_flows entry for a (possibly un-stripped,
    possibly ETF-proxy) display symbol, or None."""
    if display_symbol is None:
        return None
    # 1. Direct
    tk = spots.get(display_symbol)
    if tk is not None:
        return tk
    # 2. Normalized
    norm = _normalize_display_symbol(display_symbol)
    tk = spots.get(norm)
    if tk is not None:
        return tk
    for key in spots:
        if _normalize_display_symbol(key) == norm:
            return spots[key]
    # 3. ETF proxy (SPX asked -> SPY tracked) and reverse
    proxy = _STREAM_SYMBOL_MAP.get(norm)
    if proxy is not None:
        tk = spots.get(proxy)
        if tk is not None:
            return tk
        for key in spots:
            if _normalize_display_symbol(key) == proxy:
                return spots[key]
    for src, p in _STREAM_SYMBOL_MAP.items():
        if norm == p:
            if src in spots:
                return spots[src]
            for key in spots:
                if _normalize_display_symbol(key) == src:
                    return spots[key]
            break
    return None


class AtmOptionVolumeService:
    """Aggregates LEVELONE_OPTIONS trade ticks into 1-second bars with
    buy/sell volume split.  Uses a shared StreamClient (from the equity
    streaming service) instead of opening its own WebSocket connection.

    Subscribes to front-expiration ATM call/put for ALL tickers in
    ticker_history.json in a SINGLE Level-One Options subscription.
    Maintains per-ticker bullish/bearish flow in _ticker_flows dict.
    """

    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop: asyncio.AbstractEventLoop = loop
        self._symbol: str | None = None
        self._expiration: str | None = None  # "YYYY-MM-DD"
        self._running = False

        # Spot & ATM strike state (for primary/chart symbol)
        self._spot: float = 0.0
        self._atm_strike: float = 0.0
        self._subscribed_call_sym: str | None = None
        self._subscribed_put_sym: str | None = None

        # Option bid/ask for direction inference (primary symbol)
        self._call_bid: float | None = None
        self._call_ask: float | None = None
        self._put_bid: float | None = None
        self._put_ask: float | None = None

        # Aggregated 1-second bars (primary symbol for chart merge)
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

        # Track the last set of skipped (unknown-spot) tickers so the
        # "skipped N ticker(s)" notice is only printed when the set changes,
        # not on every re-subscribe.
        self._last_skipped_no_spot = None
        self._last_sub_ok_set = None

        # Per-ticker flow tracking (all tracked tickers including primary)
        # _ticker_flows: display_symbol -> {stream_symbol, spot, atm_strike,
        #   call_sym, put_sym, call_bid, call_ask, put_bid, put_ask,
        #   bullish, bearish}
        self._ticker_flows: dict[str, dict] = {}
        # Reverse lookup: option_symbol -> display_symbol
        self._sym_to_ticker: dict[str, str] = {}

        # Load ticker history upfront for initialization
        self._all_tickers: list[str] = _load_ticker_history()
        
        # Initialize tracking flows from the loaded tickers
        self._init_all_tickers("")

    def tracked_tickers(self) -> list[str]:
        """Return list of tracked display symbols (normalized: uppercase,
        no leading '$').  Index symbols such as 'SPX' are kept as 'SPX'
        (the ETF proxy 'SPY' is only used internally for the WebSocket
        subscription symbol, not for the flow-key)."""
        with self._lock:
            return [_normalize_display_symbol(sym) for sym in self._ticker_flows.keys()]

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
            return self._ticks_received > 0

    def start(self):
        """Start the service - called after register to begin streaming."""
        if not self._running and self._symbol and self._stream_client:
            self._running = True

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
        """Register on a shared StreamClient and subscribe to ATM options for
        ALL tickers in ticker_history.json in a SINGLE Level-One Options
        subscription."""
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
            self._ticker_flows.clear()
            self._sym_to_ticker.clear()
            self._last_sub_ok_set = None

        self._symbol = symbol
        self._expiration = expiration
        self._stream_client = stream_client

        # Re-initialize _ticker_flows here since register() might be called
        # after __init__ (when service is created once and updated for new symbols)
        self._init_all_tickers(symbol)

        # Register handler on the shared StreamClient
        stream_client.add_level_one_option_handler(self._make_handler())

        # NOTE: We do NOT call _do_subscribe here.  The caller
        # (ensure_atm_streaming) will call bulk_update_spots() which sets
        # spot prices for all tickers and then triggers _do_subscribe.
        # If we subscribed here, _do_subscribe would run on the event-loop
        # thread before bulk_update_spots() has set any spots on the main
        # thread, so all tickers would be skipped with "unknown spot".

        self._running = True

    def _init_all_tickers(self, primary_symbol: str):
        """Initialize _ticker_flows for all tickers in history + primary."""
        # Reload from file to pick up any new tickers added via UI
        self._all_tickers = _load_ticker_history()
        all_symbols = list(dict.fromkeys([primary_symbol] + self._all_tickers))
        with self._lock:
            for sym in all_symbols:
                if sym in self._ticker_flows:
                    continue
                stream_sym = _get_stream_symbol(sym)
                self._ticker_flows[sym] = {
                    "stream_symbol": stream_sym,
                    "spot": 0.0,
                    "atm_strike": 0.0,
                    "call_sym": None,
                    "put_sym": None,
                    "call_bid": None,
                    "call_ask": None,
                    "put_bid": None,
                    "put_ask": None,
                    "bullish": 0,
                    "bearish": 0,
                }

    def _get_stream_client(self):
        with self._lock:
            return self._stream_client

    def stop(self):
        self._stop_locked()
        with self._lock:
            self._ticker_flows.clear()
            self._sym_to_ticker.clear()

    def _stop_locked(self):
        self._running = False
        self._subscribed_call_sym = None
        self._subscribed_put_sym = None
        self._stream_client = None

    # ------------------------------------------------------------------ #
    # Per-ticker flow tracking API
    # ------------------------------------------------------------------ #

    def add_ticker(self, display_symbol: str, stream_symbol: str, spot: float):
        """Add a ticker to tracking (does NOT subscribe individually - all
        tickers are subscribed in a single call via _do_subscribe)."""
        with self._lock:
            if display_symbol in self._ticker_flows:
                return
            self._ticker_flows[display_symbol] = {
                "stream_symbol": stream_symbol,
                "spot": spot,
                "atm_strike": 0.0,
                "call_sym": None,
                "put_sym": None,
                "call_bid": None,
                "call_ask": None,
                "put_bid": None,
                "put_ask": None,
                "bullish": 0,
                "bearish": 0,
            }
        # Trigger a full re-subscription to include the new ticker
        if self._running and self._expiration:
            sc = self._get_stream_client()
            if sc is not None:
                asyncio.run_coroutine_threadsafe(
                    self._do_subscribe(sc), self._loop,
                )

    def remove_ticker(self, display_symbol: str):
        """Stop tracking flow for a ticker."""
        with self._lock:
            ticker = self._ticker_flows.pop(display_symbol, None)
            if ticker:
                if ticker["call_sym"]:
                    self._sym_to_ticker.pop(ticker["call_sym"], None)
                if ticker["put_sym"]:
                    self._sym_to_ticker.pop(ticker["put_sym"], None)
        # Trigger re-subscription to remove the unsubscribed symbols
        if self._running and self._expiration:
            sc = self._get_stream_client()
            if sc is not None:
                asyncio.run_coroutine_threadsafe(
                    self._do_subscribe(sc), self._loop,
                )

    def get_ticker_flow(self, display_symbol: str) -> tuple:
        """Return (bullish_vol, bearish_vol) for a tracked ticker,
        or (None, None) if not tracked / no data yet.  Lookup tolerates
        leading '$', case variation, and index/ETF proxy remapping
        (SPX<->SPY, RUT<->IWM, NDX<->QQQ)."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return None, None
            return ticker["bullish"], ticker["bearish"]

    def get_ticker_option_prices(self, display_symbol: str) -> dict:
        """Return {call_price, put_price} mid-market for a tracked ticker,
        or {} if not tracked.  Returns bid/ask mid if both sides are
        available, else the single available side."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return {}
            result = {}
            cb, ca = ticker.get("call_bid"), ticker.get("call_ask")
            if cb is not None and ca is not None and ca > 0:
                result["call_price"] = round((cb + ca) / 2, 2)
            elif cb is not None:
                result["call_price"] = round(cb, 2)
            elif ca is not None:
                result["call_price"] = round(ca, 2)
            pb, pa = ticker.get("put_bid"), ticker.get("put_ask")
            if pb is not None and pa is not None and pa > 0:
                result["put_price"] = round((pb + pa) / 2, 2)
            elif pb is not None:
                result["put_price"] = round(pb, 2)
            elif pa is not None:
                result["put_price"] = round(pa, 2)
            return result

    def get_ticker_spot(self, display_symbol: str) -> float | None:
        """Return the live spot price for a tracked ticker,
        or None if not tracked / no spot known yet."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None or ticker["spot"] <= 0:
                return None
            return ticker["spot"]

    def get_ticker_atm_strike(self, display_symbol: str) -> float | None:
        """Return the front-expiration ATM strike for a tracked ticker,
        or None if not tracked / no spot known yet."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None or ticker["atm_strike"] <= 0:
                return None
            return ticker["atm_strike"]

    def update_ticker_spot(self, display_symbol: str, spot: float):
        """Update the spot price for a tracked ticker and trigger re-subscription
        if the ATM strike changes."""
        sc = None
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return
            old_spot = ticker["spot"]
            ticker["spot"] = spot
            if ticker["call_sym"] is None or ticker["put_sym"] is None or \
               abs(spot - old_spot) / max(old_spot, 1) > 0.001:
                if self._running and self._expiration:
                    sc = self._stream_client
        if sc is not None:
            asyncio.run_coroutine_threadsafe(
                self._do_subscribe(sc), self._loop,
            )

    def bulk_update_spots(self, spot_map: dict[str, float]):
        """Set spot prices for multiple tickers at once and trigger a single
        re-subscription.  Avoids the race where per-ticker update_ticker_spot
        calls each schedule separate _do_subscribe coroutines that run before
        all spots are set."""
        sc = None
        with self._lock:
            for display_symbol, spot in spot_map.items():
                ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
                if ticker is not None:
                    ticker["spot"] = spot
            if self._running and self._expiration:
                sc = self._stream_client
        if sc is not None:
            asyncio.run_coroutine_threadsafe(
                self._do_subscribe(sc), self._loop,
            )

    # ------------------------------------------------------------------ #
    # Internal: handler & subscription
    # ------------------------------------------------------------------ #

    def _option_handler(self, msg):
        with self._lock:
            if self._subscribed_call_sym is None and self._subscribed_put_sym is None \
               and not self._sym_to_ticker:
                return
            subs = {self._subscribed_call_sym, self._subscribed_put_sym}
            primary_root = (self._symbol or "").ljust(6)[:6]
            for c in msg.get("content", []):
                sym = c.get("key", "") or c.get("SYMBOL", "")
                if not sym:
                    continue

                # Check if this option belongs to a tracked per-ticker flow
                ticker_display = self._sym_to_ticker.get(sym)
                ticker = self._ticker_flows.get(ticker_display) if ticker_display else None

                # Detect primary ticker by exact match OR by root symbol prefix
                is_primary = bool(
                    sym in subs
                    or (primary_root and sym[:6] == primary_root)
                )

                if not ticker and not is_primary:
                    continue

                self._ticks_received += 1

                bid = c.get("BID_PRICE")
                ask = c.get("ASK_PRICE")
                contract_type = c.get("CONTRACT_TYPE", "").upper()
                underlying = c.get("UNDERLYING_PRICE")

                # Update the relevant ticker's bid/ask/spot
                if ticker:
                    if contract_type in ("CALL", "C"):
                        if underlying is not None:
                            ticker["spot"] = float(underlying)
                        if bid is not None:
                            ticker["call_bid"] = float(bid)
                        if ask is not None:
                            ticker["call_ask"] = float(ask)
                    elif contract_type in ("PUT", "P"):
                        if underlying is not None:
                            ticker["spot"] = float(underlying)
                        if bid is not None:
                            ticker["put_bid"] = float(bid)
                        if ask is not None:
                            ticker["put_ask"] = float(ask)

                # Also update primary service bid/ask/spot for chart merge
                if is_primary:
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
                    opt_type = "CALL" if ct in ("CALL", "C") else "PUT"
                    self._process_trade_ticker(ticker, price, size, opt_type)
                    if is_primary:
                        self._aggregate_tick(
                            int(t), float(price), int(size), opt_type,
                        )
                except Exception:
                    pass

    def _make_handler(self):
        return self._option_handler

    async def _do_subscribe(self, sc):
        """Build ATM option symbols for ALL tracked tickers and subscribe
        via the shared StreamClient *sc* in a SINGLE call.

        Note: Tickers without a known spot (spot<=0) are *skipped* rather
        than subscribed at a placeholder strike of 100, because subscribing
        to non-existent option symbols both wastes the message budget and
        causes grief on the next re-subscribe (root prefix match mistakes).
        They will be subscribed when `update_ticker_spot` arrives."""
        with self._lock:
            expiration = self._expiration
            tickers = dict(self._ticker_flows)
        if not expiration or not tickers:
            return

        # Parse expiration to YYMMDD
        parts = expiration.split("-")
        yymmdd = parts[0][2:] + parts[1] + parts[2]

        # Build all call/put symbols for all tickers
        all_symbols = []
        skipped_no_spot = []
        with self._lock:
            for display_sym, info in tickers.items():
                spot = info["spot"]
                stream_sym = info["stream_symbol"]
                if spot <= 0:
                    # Skip placeholders - subscribing to wrong strikes
                    # pollutes the feed. Re-subscribe triggered by update_ticker_spot.
                    info["call_sym"] = None
                    info["put_sym"] = None
                    skipped_no_spot.append(display_sym)
                    continue
                atm = calculate_atm_strike(spot)
                call_sym = _make_option_symbol(stream_sym, yymmdd, "C", atm)
                put_sym = _make_option_symbol(stream_sym, yymmdd, "P", atm)
                all_symbols.append(call_sym)
                all_symbols.append(put_sym)
                info["call_sym"] = call_sym
                info["put_sym"] = put_sym
                info["atm_strike"] = atm
                # For SPX/RUT/NDX index options the display symbol
                # (e.g. "$SPX") differs from the ETF proxy used as the
                # stream symbol ("SPY"). Map back to the *display* symbol
                # so the per-ticker flow dict can be looked up by it.
                target_sym = display_sym
                self._sym_to_ticker[call_sym] = target_sym
                self._sym_to_ticker[put_sym] = target_sym

        if skipped_no_spot:
            # Only log when the set of skipped tickers actually changes, so we
            # don't repeat the same notice on every re-subscribe.
            _skipped_set = frozenset(skipped_no_spot)
            if _skipped_set != self._last_skipped_no_spot:
                print(
                    f"[AtmOptionVolumeService] _do_subscribe: skipped "
                    f"{len(skipped_no_spot)} ticker(s) with unknown spot: "
                    f"{skipped_no_spot} (will subscribe when spot arrives)"
                )
                self._last_skipped_no_spot = _skipped_set

        if not all_symbols:
            return

        try:
            await sc.level_one_option_subs(all_symbols)
        except Exception as e:
            # ConnectionClosedOK (1000) is a normal WebSocket close during
            # reconnect — the next _do_subscribe cycle will retry automatically.
            if type(e).__name__ == "ConnectionClosedOK":
                return
            # Surface subscription failures instead of swallowing them
            # silently. A silent failure leaves _sym_to_ticker populated
            # but the feed is dead, so ticks never arrive.
            print(
                f"[AtmOptionVolumeService] _do_subscribe FAILED: "
                f"{type(e).__name__}: {e} (symbols={len(all_symbols)})"
            )
            return

        _ok_set = frozenset(all_symbols)
        if _ok_set != self._last_sub_ok_set:
            print(
                f"[AtmOptionVolumeService] _do_subscribe OK: "
                f"subscribed {len(all_symbols)} option symbols "
                f"({len(tickers) - len(skipped_no_spot)} ticker(s))"
            )
            self._last_sub_ok_set = _ok_set

        # Update primary subscribed symbols for backward compatibility
        with self._lock:
            primary_info = self._ticker_flows.get(self._symbol)
            if primary_info:
                self._subscribed_call_sym = primary_info.get("call_sym")
                self._subscribed_put_sym = primary_info.get("put_sym")

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

    def _process_trade_ticker(self, ticker: dict | None, price: float, size: int, opt_type: str):
        """Accumulate a trade into a per-ticker flow total (cumulative,
        not a rolling window).  Called with self._lock held."""
        if ticker is None:
            return
        if opt_type == "CALL":
            direction = self._infer_dir(price, ticker["call_bid"], ticker["call_ask"])
        else:
            direction = self._infer_dir(price, ticker["put_bid"], ticker["put_ask"])

        if direction == "buy":
            if opt_type == "CALL":
                ticker["bullish"] += size
            else:
                ticker["bearish"] += size
        elif direction == "sell":
            if opt_type == "CALL":
                ticker["bearish"] += size
            else:
                ticker["bullish"] += size
        else:
            # Unknown — split evenly
            half = size // 2
            ticker["bullish"] += half
            ticker["bearish"] += size - half

    def _infer_dir(self, price: float, bid: float | None, ask: float | None) -> str:
        if bid is not None and ask is not None:
            spread = ask - bid
            if spread > 0:
                mid = (ask + bid) / 2
                return "buy" if price >= mid else "sell"
        return ""
