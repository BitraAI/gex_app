import asyncio
import json
import os
import threading
import time as _time_mod
import pandas as pd
from calculations import calculate_atm_strike

MAX_ROWS = 200

# Minimum seconds between REST option-chain re-fetches for a single ticker
# after an ATM strike crossing.  Prevents a fast-moving tape from spamming
# the Schwab REST endpoint while still keeping put/call walls reasonably
# fresh in the Order Flow grid.
_WALL_REFRESH_MIN_INTERVAL = 30.0

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

        # Timestamp (time.time()) of the last tick processed by _option_handler.
        # Used by the Order Flow watchdog to detect a silently dead feed.
        self._last_tick_time: float = _time_mod.time()

        # Track the last set of skipped (unknown-spot) tickers so the
        # "skipped N ticker(s)" notice is only printed when the set changes,
        # not on every re-subscribe.
        self._last_skipped_no_spot = None
        self._last_sub_ok_set = None

        # Set by _do_subscribe when the WebSocket session is dead (e.g.
        # error 20 "STREAM CONNECTION NOT FOUND").  ensure_atm_streaming
        # checks this and calls register() again to re-establish the feed.
        self._needs_reconnect = False

        # Throttle re-subscribe attempts on a dead connection: only attempt
        # _do_subscribe once per _reconnect_interval seconds to avoid
        # spamming the Schwab API with failed requests every 2-second tick.
        self._last_sub_attempt: float = 0.0
        self._reconnect_interval: float = 5.0

        # Ticker symbols whose front expiration has been explicitly verified
        # via the Schwab option-expiration-chain API.  Used to avoid
        # re-fetching on every grid render.
        self._expiration_verified: set[str] = set()

        # Ticker symbols whose put/call walls have been fetched via a full
        # option-chain REST query.  Used to pace the lazy background fetch
        # in ensure_atm_streaming.
        self._walls_verified: set[str] = set()

        # Wall-refresh throttling: tracks the last time put/call walls were
        # recomputed from the REST option chain for each ticker.  When the
        # streaming spot causes an ATM strike crossing we invalidate
        # _walls_verified so the lazy fetcher picks up the ticker on the
        # next ensure_atm_streaming cycle, but we throttle re-fetches to
        # at most one per _WALL_REFRESH_MIN_INTERVAL seconds per ticker so
        # a fast-moving tape doesn't hammer the Schwab REST endpoint.
        self._wall_refresh_ts: dict[str, float] = {}

        # Per-ticker flow tracking (all tracked tickers including primary)
        # _ticker_flows: display_symbol -> {stream_symbol, spot, atm_strike,
        #   call_sym, put_sym, call_bid, call_ask, put_bid, put_ask,
        #   bullish, bearish, flow_history, trend}
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
            for _key, _t in self._ticker_flows.items():
                if _t.get("stream_symbol") != self._symbol:
                    continue
                # Skip index-symbol entries (e.g. SPX, RUT) — their spot
                # comes from the index's own REST quote, not the ETF proxy
                # streaming price.  Only update the ETF proxy itself.
                _key_norm = _key.upper().lstrip("$")
                if _key_norm != self._symbol:
                    continue
                old_atm = _t.get("atm_strike")
                _t["spot"] = spot
                _t["atm_strike"] = new_strike
                # Invalidate put/call walls on an ATM strike crossing for
                # the primary ticker so the lazy fetcher re-fetches OI.
                self._maybe_invalidate_walls_on_strike_change(
                    _key, old_atm, new_strike,
                )
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
            self._expiration_verified.clear()
            self._walls_verified.clear()
            self._wall_refresh_ts.clear()

            # Reset the watchdog timestamp so it doesn't immediately fire
            # again after this re-registration.  The flow needs time to
            # re-subscribe and start receiving ticks.
            import time as _time_mod
            self._last_tick_time = _time_mod.time()

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
                    "expiration": self._expiration,
                    "call_wall": None,
                    "put_wall": None,
                    "call_sym": None,
                    "put_sym": None,
                    "call_bid": None,
                    "call_ask": None,
                    "put_bid": None,
                    "put_ask": None,
                    "bullish": 0,
                    "bearish": 0,
                    "flow_history": [],
                    "trend": "flat",
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

    def is_feed_stale(self, max_age_seconds: float = 60.0) -> bool:
        """Return True if no option ticks have been received for
        *max_age_seconds*.  Used by the Order Flow watchdog to detect a
        silently dead WebSocket subscription."""
        with self._lock:
            return (_time_mod.time() - self._last_tick_time) > max_age_seconds

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
                "expiration": self._expiration,
                "call_wall": None,
                "put_wall": None,
                "call_sym": None,
                "put_sym": None,
                "call_bid": None,
                "call_ask": None,
                "put_bid": None,
                "put_ask": None,
                "bullish": 0,
                "bearish": 0,
                "flow_history": [],
                "trend": "flat",
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
        available, else the single available side.
        Falls back to the primary ticker's class-level bid/ask when the
        per-ticker values are unavailable (for any ticker that shares the
        primary's stream symbol, e.g. index tickers like SPX using SPY)."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return {}
            result = {}
            cb, ca = ticker.get("call_bid"), ticker.get("call_ask")
            # Fallback to primary's class-level bid/ask if per-ticker is empty
            # and this ticker uses the same stream symbol as the primary
            _stream_sym = _get_stream_symbol(display_symbol)
            if cb is None and ca is None and _stream_sym == self._symbol:
                cb, ca = self._call_bid, self._call_ask
            if cb is not None and ca is not None and ca > 0:
                result["call_price"] = round((cb + ca) / 2, 2)
            elif cb is not None:
                result["call_price"] = round(cb, 2)
            elif ca is not None:
                result["call_price"] = round(ca, 2)
            pb, pa = ticker.get("put_bid"), ticker.get("put_ask")
            if pb is None and pa is None and _stream_sym == self._symbol:
                pb, pa = self._put_bid, self._put_ask
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
        or None if not tracked / no spot known yet.
        Falls back to calculating from the current spot when the stored
        atm_strike is not set, so the column stays in sync with live spot."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return None
            if ticker["atm_strike"] > 0:
                return ticker["atm_strike"]
            if ticker["spot"] > 0:
                return calculate_atm_strike(ticker["spot"])
            return None

    def get_ticker_expiration(self, display_symbol: str) -> str | None:
        """Return the front expiration date for a tracked ticker.
        Tries per-ticker expiration first (which may be set from option
        chain data), then parses the OCC option symbol, then falls back
        to the shared service expiration."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return self._expiration
            exp = ticker.get("expiration")
            if exp:
                return exp
            call_sym = ticker.get("call_sym")
            if call_sym and len(call_sym) >= 12:
                yymmdd = call_sym[6:12]
                return f"20{yymmdd[0:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}"
            return self._expiration

    def set_ticker_expiration(self, display_symbol: str, expiration: str):
        """Set the front expiration for a tracked ticker.
        Used when option chain data is available for that ticker.
        Triggers re-subscription if the expiration changed so the ticker
        subscribes to the correct option contracts."""
        sc = None
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is not None:
                old_exp = ticker.get("expiration")
                ticker["expiration"] = expiration
                self._expiration_verified.add(
                    _normalize_display_symbol(display_symbol)
                )
                # Re-subscribe if expiration changed to correct contracts
                if old_exp != expiration and self._running and self._expiration:
                    sc = self._stream_client
        if sc is not None:
            asyncio.run_coroutine_threadsafe(
                self._do_subscribe(sc), self._loop,
            )

    def _maybe_invalidate_walls_on_strike_change(
        self, display_symbol: str, old_atm: float | None, new_atm: float,
    ) -> None:
        """Invalidate put/call wall verification when a ticker's ATM strike
        changes, throttled to _WALL_REFRESH_MIN_INTERVAL seconds per ticker
        so a fast-moving tape does not spam the Schwab REST endpoint.

        Called from the streaming spot-update paths (update_ticker_spot,
        bulk_update_spots, set_ticker_spot) with the OLD and NEW ATM strike.
        On a true crossing (and after the throttle elapses), the ticker is
        removed from _walls_verified so the lazy fetcher in
        ensure_atm_streaming re-fetches the option chain and recomputes
        the walls on the next cycle."""
        if old_atm is None or new_atm is None or old_atm == new_atm:
            return
        norm = _normalize_display_symbol(display_symbol)
        now = _time_mod.monotonic()
        last = self._wall_refresh_ts.get(norm, 0.0)
        if now - last < _WALL_REFRESH_MIN_INTERVAL:
            return
        # Mark for re-fetch on the next ensure_atm_streaming cycle.
        self._walls_verified.discard(norm)

    def set_ticker_walls(self, display_symbol: str, put_wall: float | None, call_wall: float | None):
        """Store the Put Wall (support) and Call Wall (resistance) for a
        tracked ticker.  These are read from REST option-chain analytics
        and displayed in the Order Flow grid."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is not None:
                # Only update if new values are provided (non-None) to preserve existing walls
                if put_wall is not None:
                    ticker["put_wall"] = put_wall
                if call_wall is not None:
                    ticker["call_wall"] = call_wall
                norm = _normalize_display_symbol(display_symbol)
                self._walls_verified.add(norm)
                # Stamp the refresh time so the throttle in
                # _maybe_invalidate_walls_on_strike_change takes effect.
                self._wall_refresh_ts[norm] = _time_mod.monotonic()

    def set_ticker_option_prices(self, display_symbol: str,
                                  call_price: float | None,
                                  put_price: float | None):
        """Store the ATM mark for Call/Put for a tracked ticker.

        Used to populate the Call Price / Put Price columns in the ATM
        Order Flow grid for tickers that do NOT have a LEVELONE_OPTIONS
        stream of their own — namely index symbols (SPX, RUT, NDX) which
        only stream the ETF proxy (SPY, IWM, QQQ).  Without this setter
        ``get_ticker_option_prices`` would fall back to the ETF's option
        bid/ask mid, which is the wrong underlying price level.

        Values are written into both ``call_bid`` and ``call_ask`` (same
        for puts) so ``get_ticker_option_prices`` returns the supplied
        mark verbatim and does not recompute a mid from stale ticks."""
        if call_price is None and put_price is None:
            return
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return
            if call_price is not None:
                ticker["call_bid"] = float(call_price)
                ticker["call_ask"] = float(call_price)
            if put_price is not None:
                ticker["put_bid"] = float(put_price)
                ticker["put_ask"] = float(put_price)

    def set_ticker_spot(self, display_symbol: str, spot: float):
        """Set the spot price for a tracked ticker and recalculate its ATM
        strike.  Used for index symbols (SPX, RUT, NDX) whose actual spot
        differs from the ETF proxy (SPY, IWM, QQQ) used for streaming.
        Does NOT trigger a re-subscribe — index tickers share the ETF
        proxy's option subscription."""
        if not spot or spot <= 0:
            return
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is not None:
                old = ticker["spot"]
                old_atm = ticker.get("atm_strike")
                ticker["spot"] = spot
                new_atm = calculate_atm_strike(spot)
                ticker["atm_strike"] = new_atm
                # Invalidate put/call walls on an ATM strike crossing so the
                # lazy fetcher re-fetches fresh OI from REST.  Index symbols
                # share the ETF proxy subscription, but their walls are
                # still computed from the index option chain.
                self._maybe_invalidate_walls_on_strike_change(
                    display_symbol, old_atm, new_atm,
                )
                if abs(spot - old) / max(old, 1) > 0.001:
                    self._spot_changed = True

    def get_ticker_put_wall(self, display_symbol: str) -> float | None:
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return None
            return ticker.get("put_wall")

    def get_ticker_call_wall(self, display_symbol: str) -> float | None:
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return None
            return ticker.get("call_wall")

    def update_ticker_spot(self, display_symbol: str, spot: float):
        """Update the spot price for a tracked ticker and trigger re-subscription
        if the ATM strike changes."""
        sc = None
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return
            old_spot = ticker["spot"]
            old_atm = ticker.get("atm_strike")
            ticker["spot"] = spot
            new_atm = calculate_atm_strike(spot)
            ticker["atm_strike"] = new_atm
            # Invalidate put/call walls on an ATM strike crossing so the
            # lazy fetcher re-fetches fresh open interest from REST.
            self._maybe_invalidate_walls_on_strike_change(
                display_symbol, old_atm, new_atm,
            )
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
        all spots are set.

        Only triggers re-subscription if at least one spot actually changed
        by more than 0.1%, so calling this every 2 seconds from
        ensure_atm_streaming does NOT spam the Schwab server with redundant
        subscription requests."""
        sc = None
        _spot_changed = False
        with self._lock:
            for display_symbol, spot in spot_map.items():
                ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
                if ticker is not None:
                    old = ticker["spot"]
                    old_atm = ticker.get("atm_strike")
                    ticker["spot"] = spot
                    new_atm = calculate_atm_strike(spot)
                    ticker["atm_strike"] = new_atm
                    # Invalidate put/call walls on an ATM strike crossing so
                    # the lazy fetcher re-fetches fresh OI from REST.
                    self._maybe_invalidate_walls_on_strike_change(
                        display_symbol, old_atm, new_atm,
                    )
                    # Only trigger re-subscribe for non-index tickers
                    # (index symbols share the ETF proxy subscription).
                    _disp_norm = _normalize_display_symbol(display_symbol)
                    if abs(spot - old) / max(old, 1) > 0.001 and \
                       _get_stream_symbol(_disp_norm) == _disp_norm:
                        _spot_changed = True
            if self._running and self._expiration:
                sc = self._stream_client
        if sc is not None and _spot_changed:
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
            subs_clean = {s.replace(" ", "") for s in subs if s}
            primary_root_clean = (self._symbol or "").ljust(6)[:6].rstrip()
            for c in msg.get("content", []):
                sym = c.get("key", "") or c.get("SYMBOL", "")
                if not sym:
                    continue

                # Normalize: strip spaces for robust matching against
                # _make_option_symbol (which pads root to 6 chars).  The
                # Schwab streaming API may return symbols with or without
                # the OCC-standard space padding.
                sym_raw = sym
                sym = sym.replace(" ", "")

                # Check if this option belongs to a tracked per-ticker flow
                ticker_display = self._sym_to_ticker.get(sym_raw)
                if ticker_display is None:
                    ticker_display = self._sym_to_ticker.get(sym)
                ticker = self._ticker_flows.get(ticker_display) if ticker_display else None

                # Fallback: match by root prefix (the OCC root is the stock
                # symbol leading the option symbol, followed by the date).
                # Handles both padded (e.g. "AAPL  ") and unpadded formats.
                if ticker is None:
                    for _td, _tk in self._ticker_flows.items():
                        stock_sym = _tk.get("stream_symbol") or ""
                        if sym.startswith(stock_sym) or sym.startswith(stock_sym.ljust(6).replace(" ", "")):
                            ticker = _tk
                            ticker_display = _td
                            break

                # Detect primary ticker by root prefix (space-insensitive)
                is_primary = bool(
                    sym_raw in subs
                    or sym in subs_clean
                    or (primary_root_clean and sym.startswith(primary_root_clean))
                )

                if not ticker and not is_primary:
                    continue

                self._ticks_received += 1
                self._last_tick_time = _time_mod.time()

                bid = c.get("BID_PRICE")
                ask = c.get("ASK_PRICE")
                bid_size = c.get("BID_SIZE")
                ask_size = c.get("ASK_SIZE")
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
                        if bid_size is not None:
                            ticker["current_bid_size"] = float(bid_size)
                        if ask_size is not None:
                            ticker["current_ask_size"] = float(ask_size)
                    elif contract_type in ("PUT", "P"):
                        if underlying is not None:
                            ticker["spot"] = float(underlying)
                        if bid is not None:
                            ticker["put_bid"] = float(bid)
                        if ask is not None:
                            ticker["put_ask"] = float(ask)
                        if bid_size is not None:
                            ticker["current_bid_size"] = float(bid_size)
                        if ask_size is not None:
                            ticker["current_ask_size"] = float(ask_size)
                    
                    # Maintain cross-ticker bid/ask consistency for the primary symbol
                    if is_primary:
                        if contract_type in ("CALL", "C"):
                            if bid is not None:
                                self._call_bid = float(bid)
                            if ask is not None:
                                self._call_ask = float(ask)
                        elif contract_type in ("PUT", "P"):
                            if bid is not None:
                                self._put_bid = float(bid)
                            if ask is not None:
                                self._put_ask = float(ask)
                        
                        # Also update primary symbol's per-ticker entry for backwards compatibility
                        if self._symbol:
                            primary_ticker = _find_flow_for_display(self._ticker_flows, self._symbol)
                            if primary_ticker:
                                if contract_type in ("CALL", "C"):
                                    if bid is not None:
                                        primary_ticker["call_bid"] = float(bid)
                                    if ask is not None:
                                        primary_ticker["call_ask"] = float(ask)
                                elif contract_type in ("PUT", "P"):
                                    if bid is not None:
                                        primary_ticker["put_bid"] = float(bid)
                                    if ask is not None:
                                        primary_ticker["put_ask"] = float(ask)

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
                    # Also update the primary ticker's per-ticker entry so
                    # get_ticker_option_prices can serve it without fallback.
                    _pri = _find_flow_for_display(self._ticker_flows, self._symbol)
                    if _pri is not None:
                        if contract_type in ("CALL", "C"):
                            if underlying is not None:
                                _pri["spot"] = float(underlying)
                            if bid is not None:
                                _pri["call_bid"] = float(bid)
                            if ask is not None:
                                _pri["call_ask"] = float(ask)
                        elif contract_type in ("PUT", "P"):
                            if underlying is not None:
                                _pri["spot"] = float(underlying)
                            if bid is not None:
                                _pri["put_bid"] = float(bid)
                            if ask is not None:
                                _pri["put_ask"] = float(ask)

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

        Each ticker uses its own per-ticker expiration (set via
        ``set_ticker_expiration``) so the ``Expiration`` column in the
        Order Flow grid shows the correct date per ticker rather than
        the chart symbol's shared front expiration.

        Note: Tickers without a known spot (spot<=0) are *skipped* rather
        than subscribed at a placeholder strike of 100, because subscribing
        to non-existent option symbols both wastes the message budget and
        causes grief on the next re-subscribe (root prefix match mistakes).
        They will be subscribed when `update_ticker_spot` arrives."""
        with self._lock:
            tickers = dict(self._ticker_flows)
        if not tickers:
            return

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

                # Use per-ticker expiration when available, otherwise fall
                # back to the shared service expiration so newly added
                # tickers still get subscribed before the lazy fetch runs.
                exp = info.get("expiration") or self._expiration
                if not exp:
                    continue
                parts = exp.split("-")
                yymmdd = parts[0][2:] + parts[1] + parts[2]

                atm = calculate_atm_strike(spot)
                call_sym = _make_option_symbol(stream_sym, yymmdd, "C", atm)
                put_sym = _make_option_symbol(stream_sym, yymmdd, "P", atm)
                all_symbols.append(call_sym)
                all_symbols.append(put_sym)
                info["call_sym"] = call_sym
                info["put_sym"] = put_sym
                info["atm_strike"] = atm
                # Preserve per-ticker expiration — do NOT overwrite with
                # the shared self._expiration here.
                # For SPX/RUT/NDX index options the display symbol
                # (e.g. "$SPX") differs from the ETF proxy used as the
                # stream symbol ("SPY"). Map back to the *display* symbol
                # so the per-ticker flow dict can be looked up by it.
                target_sym = display_sym
                self._sym_to_ticker[call_sym] = target_sym
                self._sym_to_ticker[put_sym] = target_sym
                self._sym_to_ticker[call_sym.replace(" ", "")] = target_sym
                self._sym_to_ticker[put_sym.replace(" ", "")] = target_sym

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

        # Throttle: during reconnection, only attempt once per
        # _reconnect_interval seconds to avoid spamming the log.
        _now = _time_mod.time()
        if self._needs_reconnect and _now - self._last_sub_attempt < self._reconnect_interval:
            return
        self._last_sub_attempt = _now

        # Deduplicate: skip the subscription request if the symbol set
        # is identical to the last successful one.
        _new_set = frozenset(all_symbols)
        if _new_set == self._last_sub_ok_set and not self._needs_reconnect:
            with self._lock:
                primary_info = self._ticker_flows.get(self._symbol)
                if primary_info:
                    self._subscribed_call_sym = primary_info.get("call_sym")
                    self._subscribed_put_sym = primary_info.get("put_sym")
            return

        try:
            await sc.level_one_option_subs(all_symbols)
            self._needs_reconnect = False
        except Exception as e:
            if type(e).__name__ == "ConnectionClosedOK":
                return
            _err_str = str(e).lower()
            _is_dead = (
                "connection not found" in _err_str
                or "stream connection" in _err_str
                or type(e).__name__ == "ConnectionClosedError"
                or type(e).__name__ == "ConnectionClosed"
            )
            if _is_dead:
                self._needs_reconnect = True
            # Only log on first failure or when the error message changes
            _err_key = str(e)[:120]
            if _err_key != getattr(self, "_last_sub_err_key", None):
                print(
                    f"[AtmOptionVolumeService] _do_subscribe FAILED: "
                    f"{type(e).__name__}: {e} (symbols={len(all_symbols)})"
                    f"{' — will reconnect' if _is_dead else ''}"
                )
                self._last_sub_err_key = _err_key
            return

        _ok_set = _new_set
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

    def get_ticker_trend(self, display_symbol: str) -> str:
        """Return the Trend direction for a tracked ticker:
        'up', 'down', or 'flat'.
        None if not tracked."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return "flat"
            return ticker.get("trend", "flat")

    def get_ticker_trend_data(self, display_symbol: str) -> dict:
        """Atomically return trend, book_imbalance, and trend_reversal
        for a ticker under a single lock, avoiding race conditions where
        book_imbalance is updated by _snapshot_flow before trend."""
        with self._lock:
            ticker = _find_flow_for_display(self._ticker_flows, display_symbol)
            if ticker is None:
                return {"trend": "flat", "book_imbalance": None, "trend_reversal": None}
            return {
                "trend": ticker.get("trend", "flat"),
                "book_imbalance": ticker.get("book_imbalance"),
                "trend_reversal": ticker.get("trend_reversal"),
            }

    def _calculate_book_imbalance(self, bid_size: float, ask_size: float) -> float:
        """Calculate book imbalance ratio from bid/ask sizes.
        Positive → bullish pressure, Negative → bearish pressure."""
        total = bid_size + ask_size
        if total == 0:
            return 0.0
        return (bid_size - ask_size) / total

    def _snapshot_flow(self, ticker: dict):
        """Enhanced flow snapshot combining OPTIONS_BOOK with flow momentum for trend detection.
        Called with self._lock held."""
        import time as _time
        now = _time.time()
        net = ticker["bullish"] - ticker["bearish"]
        ticker["flow_history"].append((now, net))
        
        # Calculate and store book imbalance for enhanced trend detection
        bid_size = ticker.get("current_bid_size")
        ask_size = ticker.get("current_ask_size")
        if bid_size is not None and ask_size is not None:
            book_imbalance = self._calculate_book_imbalance(bid_size, ask_size)
            ticker["book_imbalance"] = book_imbalance
            ticker["book_imbalance_history"].append((now, book_imbalance))
        
        # Keep last 60 seconds of data
        cutoff = now - 60
        while ticker["flow_history"] and ticker["flow_history"][0][0] < cutoff:
            ticker["flow_history"].pop(0)
        while ticker.get("book_imbalance_history") and ticker["book_imbalance_history"][0][0] < cutoff:
            ticker["book_imbalance_history"].pop(0)

        # Enhanced trend detection using both flow momentum and book imbalance
        history = ticker["flow_history"]
        if len(history) < 2:
            ticker["trend"] = "flat"
            ticker["flow_speed"] = 0
            return

        # Calculate flow momentum (net change in bullish/bearish volume)
        segment_size = len(history) // 2
        older_first = history[0][1]
        newer_first = history[-segment_size][1]
        flow_diff = newer_first - older_first

        # Store flow speed for UI display
        ticker["flow_speed"] = flow_diff

        # Determine base trend from flow momentum
        if flow_diff > 0:
            current_trend = "up"
        elif flow_diff < 0:
            current_trend = "down"
        else:
            current_trend = "flat"
        
        # Enhanced trend detection: apply book imbalance pressure
        # This detects when strong book imbalance can override pure flow signals
        previous_trend = ticker.get("trend", None)
        book_imbalance = ticker.get("book_imbalance", 0.0)
        
        if abs(book_imbalance) > 0.3:  # Strong book imbalance threshold
            # Book imbalance bullish and trend is flat/down - upgrade to bullish
            if book_imbalance > 0.3 and current_trend != "up":
                current_trend = "up"
            # Book imbalance bearish and trend is flat/up - downgrade to bearish
            elif book_imbalance < -0.3 and current_trend != "down":
                current_trend = "down"
        
        # Detect trend reversal
        if previous_trend is None:
            reversal = None
        elif previous_trend != current_trend:
            if previous_trend == "up" and current_trend == "down":
                reversal = "bearish"
            elif previous_trend == "down" and current_trend == "up":
                reversal = "bullish"
            else:
                reversal = None
        else:
            reversal = None
        
        # Apply book imbalance pressure to trend assignment
        if book_imbalance > 0.3 and current_trend != "up":
            current_trend = "up"
        elif book_imbalance < -0.3 and current_trend != "down":
            current_trend = "down"
        
        ticker["trend"] = current_trend
        ticker["trend_reversal"] = reversal

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

        # Snapshot flow every ~10 ticks for trend computation
        total = ticker["bullish"] + ticker["bearish"]
        if total % 10 == 0:
            self._snapshot_flow(ticker)

    def _infer_dir(self, price: float, bid: float | None, ask: float | None) -> str:
        if bid is not None and ask is not None:
            spread = ask - bid
            if spread > 0:
                mid = (ask + bid) / 2
                return "buy" if price >= mid else "sell"
        return ""
