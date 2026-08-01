"""Shared ATM order-flow rendering used by both the main app page and
the dedicated Order Flow tab.

Kept free of any st.set_page_config / global app setup so it can be imported
safely from either entry point without re-running app.py's top-level code.
"""

import asyncio
import time as _time_mod
import pandas as pd
import streamlit as st
from datetime import date, datetime
from zoneinfo import ZoneInfo
from _constants import STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP
from option_streaming_service import _find_flow_for_display, _normalize_display_symbol, _get_stream_symbol
from client import fetch_quotes
from calculations import calculate_atm_strike
import json
import logging
import os
from functools import partial

from analytics import _filter_strikes_near_atm, compute_analytics
from calculations import aggregate_by_expiration, build_greeks_lookup, parse_option_chain
from client import (
    fetch_option_chain,
    fetch_price_history_daily,
    get_20d_rv,
    get_interest_rate,
    get_yield,
    load_candle_cache,
    save_candle_cache,
)
from signals import generate_recommendations, assess_market_bias
from telegram_notifier import diff_alerts, notify_alerts


# Per-ticker analytics cache + event-driven trigger tracking
_ticker_analytics_cache: dict[str, dict] = {}
_last_ref_price: dict[str, float] = {}   # last reference price for trigger
_last_recompute_ts: dict[str, float] = {}  # last wall recompute time (monotonic)
_last_full_recompute_ts: dict[str, float] = {}  # last full recompute time (monotonic)
_strike_inc: dict[str, float] = {}       # known strike increment per ticker
logger = logging.getLogger(__name__)

_FETCH_RETRIES = 3

# Wall recompute cadence (hybrid trigger):
#   - recompute when spot moves >= half a strike, or when MAX interval elapses
#   - but never more often than MIN interval per ticker (API throttle)
_WALL_RECOMPUTE_MIN_INTERVAL = 30.0    # sec — hard floor between wall refreshes
_WALL_RECOMPUTE_MAX_INTERVAL = 180.0   # sec — freshness floor in quiet markets
_WALL_FULL_RECOMPUTE_INTERVAL = 300.0  # sec — full analytics + alerts refresh


async def _fetch_quotes_with_retry(client, symbols, max_retries=None):
    """Fetch quotes with retry for transient HTTP errors (ReadError, timeout, etc.)."""
    if max_retries is None:
        max_retries = _FETCH_RETRIES
    for attempt in range(max_retries):
        try:
            return await fetch_quotes(client, symbols)
        except Exception:
            if attempt < max_retries - 1:
                import random
                await asyncio.sleep(0.5 + random.random() * 1.0)
            else:
                raise


def _ensure_async_loop() -> asyncio.AbstractEventLoop:
    """Get or create the shared asyncio event loop (must match app.py)."""
    _ASYNC_LOOP = getattr(_ensure_async_loop, "_loop", None)
    if _ASYNC_LOOP is None:
        import threading
        _ASYNC_LOOP = asyncio.new_event_loop()
        t = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
        t.start()
        _ensure_async_loop._loop = _ASYNC_LOOP
    return _ASYNC_LOOP


def run_async(coro):
    """Run an async coroutine in the shared background event loop and
    return the result synchronously (blocking)."""
    loop = _ensure_async_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result()


def is_market_open() -> bool:
    """Return True if US regular equity trading hours are currently open
    (09:30-16:00 ET, Mon-Fri, excluding major holidays)."""
    _ny = ZoneInfo("America/New_York")
    now = datetime.now(_ny)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    _open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    _close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if not (_open <= now <= _close):
        return False
    # Major US market holidays (fixed/observed subset).
    _holidays = {
        (1, 1),    # New Year's Day
        (7, 4),    # Independence Day
        (12, 25),  # Christmas Day
    }
    if (now.month, now.day) in _holidays:
        return False
    return True


def ensure_atm_streaming(stream_symbol: str):
    """Start the equity + ATM option streaming services for ``stream_symbol``
    and register the ATM option volume service (subscribing to the front
    expiration).  Idempotent — safe to call on every render.

    Extracted from render_candlesticks so the dedicated ATM Order Flow page
    can start streaming on its own without re-running the whole chart render.
    Shared session state (streaming_service / atm_option_service) is reused.
    """
    s = st.session_state
    stream_symbol = STREAM_SYMBOL_MAP.get(stream_symbol.upper().lstrip("$"), stream_symbol)

    svc = s.get("streaming_service")
    if svc:
        if not svc.is_running:
            svc.start(stream_symbol)
        elif svc.symbol != stream_symbol:
            svc.stop()
            svc.start(stream_symbol)

    atm_svc = s.get("atm_option_service")
    # Register reconnect callback once so ATM options re-subscribe
    # automatically after the equity WebSocket reconnects.
    if svc and atm_svc and not getattr(atm_svc, "_reconnect_registered", False):
        async def _delayed_resubscribe(sc):
            """Wait briefly for the re-logged-in WebSocket to settle, then
            re-subscribe ATM options.  If that fails with a dead-connection
            error the flag will trigger a full re-registration on the next
            ensure_atm_streaming cycle."""
            await asyncio.sleep(2)
            if atm_svc.is_running:
                await atm_svc._do_subscribe(sc)

        def _on_equity_reconnect():
            sc = svc.get_stream_client()
            if sc is not None and atm_svc.is_running:
                asyncio.run_coroutine_threadsafe(
                    _delayed_resubscribe(sc), atm_svc._loop,
                )
        svc.on_reconnect(_on_equity_reconnect)
        atm_svc._reconnect_registered = True
    _sel_exp = s.get("selected_expiration", [])
    if isinstance(_sel_exp, str):
        _sel_exp = [_sel_exp]
    _first_exp = _sel_exp[0] if _sel_exp else None
    # Spec: always track the ATM *front* expiration.  If the user has not
    # manually selected an expiration (or it was cleared), fall back to the
    # nearest expiration in the loaded chain so the service still registers
    # and the bullish/bearish flow keeps updating.
    if _first_exp is None and s.get("expirations"):
        _front_exp = sorted(s["expirations"])[0]
        _first_exp = _front_exp
        s.selected_expiration = [_front_exp]

    _all_tickers = s.get("ticker_history", [])
    _current_sym = _normalize_display_symbol(s.get("symbol", ""))
    if _current_sym and _current_sym not in [_normalize_display_symbol(t) for t in _all_tickers]:
        _all_tickers = list(_all_tickers) + [_current_sym]

    import time as _time_mod

    # Index quotes (SPX, RUT, NDX) refreshed every ~10 s via direct REST
    # API polling — the sole source for index-level spots.
    # No fallback to ETF proxy quotes for index symbols.
    if atm_svc:
        _last_idx_fetch_ts = s.get("_idx_spot_fetch_ts", 0.0)
        if _time_mod.time() - _last_idx_fetch_ts >= 10:
            s["_idx_spot_fetch_ts"] = _time_mod.time()
            _idx_to_fetch = []
            _idx_disp = {}
            for _t in _all_tickers:
                _t_upper = _normalize_display_symbol(_t)
                if _t_upper in INDEX_QUOTE_MAP:
                    _iq = INDEX_QUOTE_MAP[_t_upper]
                    _idx_to_fetch.append(_iq)
                    _idx_disp[_iq] = _t_upper
            if _idx_to_fetch:
                try:
                    idx_resp = run_async(_fetch_quotes_with_retry(s.client, _idx_to_fetch))
                    for _iq, _disp_upper in _idx_disp.items():
                        qd = idx_resp.get(_iq, {}) or {}
                        qd2 = qd.get("quote", {}) or qd.get(_iq, {})
                        last = qd2.get("lastPrice") or qd2.get("mark") or qd2.get("closePrice")
                        if last is not None and float(last) > 0:
                            s.spot_cache[_disp_upper] = float(last)
                            atm_svc.set_ticker_spot(_disp_upper, float(last))
                except Exception as e:
                    print(f"[ensure_atm_streaming] index quote fetch failed: {e}")

    if svc and svc.is_connected and atm_svc and _first_exp:

        # Pre-fetch ETF proxy spots via REST only every ~10 s to avoid
        # blocking the Streamlit thread on every 2-second fragment tick.
        # Between fetches we feed whatever is already in spot_cache.
        # Index symbols are excluded — their spot comes from the
        # index quote ($SPX:X etc.), not the ETF proxy quote.
        _last_fetch_ts = s.get("_spot_fetch_ts", 0.0)
        if _time_mod.time() - _last_fetch_ts >= 10:
            s["_spot_fetch_ts"] = _time_mod.time()
            _stream_symbols = [
                _get_stream_symbol(t)
                for t in _all_tickers
                if _normalize_display_symbol(t) not in INDEX_QUOTE_MAP
            ]
            try:
                quote_resp = run_async(fetch_quotes(s.client, _stream_symbols))
                for disp_sym in _all_tickers:
                    _disp_upper = _normalize_display_symbol(disp_sym)
                    # Skip index symbols — their spot comes from the
                    # index quote, not the ETF proxy quote.
                    if _disp_upper in INDEX_QUOTE_MAP:
                        continue
                    _sym = STREAM_SYMBOL_MAP.get(_disp_upper, _disp_upper)
                    qd = quote_resp.get(_sym, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(_sym, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is not None and float(last) > 0:
                        s.spot_cache[_disp_upper] = float(last)
            except Exception as e:
                print(f"[ensure_atm_streaming] spot pre-fetch failed: {e}")

        _was_reconnect = getattr(atm_svc, "_needs_reconnect", False)
        _need_register = (
            not atm_svc.is_running
            or atm_svc.symbol != stream_symbol
            or getattr(atm_svc, "_expiration", None) != _first_exp
            or _was_reconnect
        )
        if _need_register:
            sc = svc.get_stream_client()
            if sc is not None:
                atm_svc._needs_reconnect = False
                atm_svc.register(sc, stream_symbol, _first_exp)
                atm_svc.start()
            if _was_reconnect:
                return
            # Reset the index quote throttle so the next cycle
            # immediately re-fetches SPX/RUT/NDX spots that
            # register() wiped to 0.
            s["_idx_spot_fetch_ts"] = 0.0

        if svc.last_price and svc.last_price > 0:
            atm_svc.update_spot(svc.last_price)
            s.spot_cache[stream_symbol] = svc.last_price

        # Ensure all tickers from session state have entries in _ticker_flows.
        # When a ticker is added via fetch_data() the file is updated but
        # register() may not be called again (service already running), so
        # _init_all_tickers() never picks it up.  Without an entry in
        # _ticker_flows, get_ticker_spot() returns None.
        # Use _find_flow_for_display to find existing entries regardless of
        # key format.  If a matching entry exists under a different key
        # (e.g. "$SPX" vs "SPX"), remove any stale direct-key entry that
        # would shadow it in _find_flow_for_display's step-1 direct lookup.
        for _t in _all_tickers:
            _t_upper = _normalize_display_symbol(_t)
            with atm_svc._lock:
                # If a direct-key entry exists with spot<=0 but a variant
                # (e.g. "$SPX") carries the real data, remove the stale one
                # so _find_flow_for_display's step-1 direct lookup doesn't
                # shadow the correct entry that step 3 would find.
                _direct = atm_svc._ticker_flows.get(_t_upper)
                if _direct is not None and _direct.get("spot", 0) <= 0:
                    _has_variant = any(
                        k != _t_upper
                        and _normalize_display_symbol(k) == _t_upper
                        for k in atm_svc._ticker_flows
                    )
                    if _has_variant:
                        del atm_svc._ticker_flows[_t_upper]

                if not _find_flow_for_display(atm_svc._ticker_flows, _t_upper):
                    # Skip index symbols — their spot comes from REST API
                    # polling (ensure_atm_streaming or IndexSpotPoller), so
                    # creating a zero-spot entry here just yields a blank
                    # column until the next successful poll.
                    if _t_upper in INDEX_QUOTE_MAP:
                        continue
                    _stream = STREAM_SYMBOL_MAP.get(_t_upper, _t_upper)
                    atm_svc._ticker_flows[_t_upper] = {
                        "stream_symbol": _stream,
                        "spot": 0.0,
                        "atm_strike": 0.0,
                        "last_atm_reference": 0.0,
                        "expiration": atm_svc._expiration,
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

        _spot_map = {}
        for _t in _all_tickers:
            _t_upper = _normalize_display_symbol(_t)
            if _t_upper in INDEX_QUOTE_MAP:
                continue
            if _t_upper in s.spot_cache:
                _spot_map[_t_upper] = s.spot_cache[_t_upper]
        if _spot_map:
            atm_svc.bulk_update_spots(_spot_map)

        # Update the walls for the current symbol from the latest analytics
        current_sym = _normalize_display_symbol(s.get("symbol", ""))
        if current_sym and s.get("analytics"):
            atm_svc = s.get("atm_option_service")
            if atm_svc:
                analytics = s.get("analytics")
                put_wall = analytics.get("put_wall")
                call_wall = analytics.get("call_wall")
                if put_wall is not None or call_wall is not None:
                    if current_sym not in atm_svc.tracked_tickers():
                        stream_sym = STREAM_SYMBOL_MAP.get(current_sym, current_sym)
                        spot = atm_svc.get_ticker_spot(current_sym) or 0.0
                        if spot > 0:
                            with atm_svc._lock:
                                if current_sym not in atm_svc._ticker_flows:
                                    atm_svc._ticker_flows[current_sym] = {
                                        "stream_symbol": stream_sym,
                                        "spot": spot,
                                        "atm_strike": calculate_atm_strike(spot) if spot > 0 else 0.0,
                                        "last_atm_reference": spot,
                                        "expiration": atm_svc._expiration,
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
                    # Now set the walls
                    atm_svc.set_ticker_walls(current_sym, put_wall, call_wall)



def update_flow_cache():
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    if atm_svc is None:
        return
    current_sym = _normalize_display_symbol(s.get("symbol", ""))

    if getattr(atm_svc, "is_running", False) and current_sym:
        if current_sym in atm_svc.tracked_tickers():
            bf, brf = atm_svc.get_ticker_flow(current_sym)
            if bf is not None and brf is not None:
                s.flow_cache[current_sym] = {"bullish": bf, "bearish": brf}

    tracked = atm_svc.tracked_tickers()
    _spot_map = {}
    _need_fetch = []

    # Check all tracked equity tickers for missing spots.
    # Index symbols (SPX, RUT, NDX) are updated exclusively via
    # REST Quote polling (IndexSpotPoller every 2s) — no fallback.
    for t_sym in tracked:
        t_upper = _normalize_display_symbol(t_sym)
        if t_upper in INDEX_QUOTE_MAP:
            continue
        if t_upper in s.spot_cache:
            _spot_map[t_upper] = s.spot_cache[t_upper]
        else:
            svc_spot = atm_svc.get_ticker_spot(t_upper)
            if svc_spot is not None and svc_spot > 0:
                _spot_map[t_upper] = svc_spot
            else:
                _need_fetch.append(t_upper)

    # Also ensure index symbols from ticker_history + current symbol are
    # refreshed via REST Quote polling even if the IndexSpotPoller
    # hasn't created an entry yet, and that missing spots for any
    # tracked symbol (index or equity) are fetched on grid render.
    _all_syms = list(s.get("ticker_history", []))
    if current_sym and current_sym not in [_normalize_display_symbol(x) for x in _all_syms]:
        _all_syms.append(current_sym)
    for _t in _all_syms:
        _t_upper = _normalize_display_symbol(_t)
        svc_spot = atm_svc.get_ticker_spot(_t_upper)
        if svc_spot is None or svc_spot <= 0:
            if _t_upper not in _need_fetch:
                _need_fetch.append(_t_upper)
    # Fetch missing spots via REST
    if _need_fetch and s.get("client"):
        try:
            _idx_need = [sym for sym in _need_fetch if sym in INDEX_QUOTE_MAP]
            _eq_need = [sym for sym in _need_fetch if sym not in INDEX_QUOTE_MAP]
            loop = _ensure_async_loop()
            if _eq_need:
                fut = asyncio.run_coroutine_threadsafe(
                    _fetch_quotes_with_retry(s.client, _eq_need), loop,
                )
                quote_resp = fut.result()
                for disp_sym in _eq_need:
                    qd = quote_resp.get(disp_sym, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(disp_sym, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is not None and float(last) > 0:
                        _spot_map[disp_sym] = float(last)
                        s.spot_cache[disp_sym] = float(last)
            if _idx_need:
                _idx_fetch_syms = [INDEX_QUOTE_MAP[sym] for sym in _idx_need]
                fut = asyncio.run_coroutine_threadsafe(
                    _fetch_quotes_with_retry(s.client, _idx_fetch_syms), loop,
                )
                idx_resp = fut.result()
                for disp_sym, iq in zip(_idx_need, _idx_fetch_syms):
                    qd = idx_resp.get(iq, {}) or {}
                    qd2 = qd.get("quote", {}) or qd.get(iq, {})
                    last = qd2.get("lastPrice") or qd2.get("mark") or qd2.get("closePrice")
                    if last is not None and float(last) > 0:
                        s.spot_cache[disp_sym] = float(last)
                        # Use set_ticker_spot which auto-creates the _ticker_flows
                        # entry if it doesn't exist yet (unlike bulk_update_spots).
                        atm_svc.set_ticker_spot(disp_sym, float(last))
        except Exception:
            pass
    if _spot_map:
        atm_svc.bulk_update_spots(_spot_map)

    for t_sym in tracked:
        bf, brf = atm_svc.get_ticker_flow(t_sym)
        if bf is not None and brf is not None:
            s.flow_cache[t_sym] = {"bullish": bf, "bearish": brf}



# ---------------------------------------------------------------------------
# Streaming-driven wall-zone alerts — uses diff_alerts from telegram_notifier
# ---------------------------------------------------------------------------

_WALL_ZONE_BUFFER = 0.0002  # 0.02 % — must match grid coloring in flow.py
_WALL_ZONE_MIN_BUFFER = 0.05  # absolute buffer floor ($) for low-priced tickers
_WALL_ZONE_ALERT_COOLDOWN = 600.0  # min seconds between consecutive alerts per ticker

# Order-absorption grid colour thresholds (contracts per $1 of spot move).
_ABSORPTION_HIGH = 1000.0  # heavy flow absorbed, price pinned
_ABSORPTION_LOW = 300.0    # price drifting on thin flow

# Min contracts absorbed at a wall before a "wall broke" alert fires.
_WALL_BREAK_MIN_ABSORBED = 100.0


def _wall_buffer(wall: float | None) -> float:
    """Near-wall zone width: 0.02 % of the wall price, floored at 5 cents so
    low-priced tickers still get a meaningful zone."""
    if wall is None:
        return 0.0
    return max(abs(wall) * _WALL_ZONE_BUFFER, _WALL_ZONE_MIN_BUFFER)


def maybe_fire_wall_zone_alerts() -> None:
    """Inspect every tracked ticker's streaming spot vs its walls and push
    diff_alerts (wall zone, gamma flip, wall changes) to Telegram.
    """
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    if atm_svc is None:
        return
    if not is_market_open():
        return
    now = _time_mod.monotonic()
    state = s.setdefault("atm_alert_state", {})

    # Ensure Level 2 books are subscribed for every tracked ticker so the
    # L2-sourced trend below is populated (idempotent; diffs each call).
    _svc = s.get("streaming_service")
    if _svc is not None:
        _svc.subscribe_book_symbols(
            [_get_stream_symbol(t) for t in atm_svc.tracked_tickers()]
        )

    for t in atm_svc.tracked_tickers():
        t_upper = _normalize_display_symbol(t)
        spot = atm_svc.get_ticker_spot(t_upper)
        call_wall = atm_svc.get_ticker_call_wall(t_upper)
        put_wall = atm_svc.get_ticker_put_wall(t_upper)
        if spot is None:
            continue

        # Hybrid trigger for wall refreshes:
        #   - fast path: lightweight wall refresh when price moves >= half a
        #     strike OR the freshness floor (MAX interval) elapses — throttled
        #     to at most once per MIN interval per ticker.
        #   - slow path: full recompute (analytics + IV rank + alerts) at a
        #     fixed slower cadence so alert headers stay fresh too.
        _raw_t = t_upper  # retains :X suffix for index symbols
        _ref = _last_ref_price.get(_raw_t)
        _inc = _strike_inc.get(_raw_t, 1.0)
        _last_re = _last_recompute_ts.get(_raw_t, 0.0)
        _moved = _ref is None or abs(spot - _ref) >= _inc / 2
        _stale = (now - _last_re) >= _WALL_RECOMPUTE_MAX_INTERVAL
        _client = s.get("client")
        _loop = _ensure_async_loop()
        if (_moved or _stale) and (_last_re == 0.0 or (now - _last_re) >= _WALL_RECOMPUTE_MIN_INTERVAL):
            _last_ref_price[_raw_t] = spot
            _last_recompute_ts[_raw_t] = now
            if _client:
                asyncio.run_coroutine_threadsafe(
                    _refresh_walls_for_symbol(_raw_t, _client, atm_svc), _loop,
                )
        if (now - _last_full_recompute_ts.get(_raw_t, 0.0)) >= _WALL_FULL_RECOMPUTE_INTERVAL:
            _last_full_recompute_ts[_raw_t] = now
            if _client:
                asyncio.run_coroutine_threadsafe(
                    _recompute_symbol(_raw_t, _client, _loop, atm_svc), _loop,
                )

        prev = state.get(t_upper)

        # Wall stability check: only alert when walls are stable for
        # 2 consecutive refreshes to avoid false signals from moving walls.
        _prev_cw = (prev or {}).get("_prev_call_wall")
        _prev_pw = (prev or {}).get("_prev_put_wall")
        _wall_stable = (prev or {}).get("_wall_stable_count", 0)
        if _prev_cw == call_wall and _prev_pw == put_wall:
            _wall_stable += 1
        else:
            _wall_stable = 0

        _opt_prices = atm_svc.get_ticker_option_prices(t_upper) or {}
        analytics = {
            "gamma_flip": None,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "dealer_position": None,
            "atm_strike": atm_svc.get_ticker_atm_strike(t_upper),
            "call_wall_mark": put_wall,
            "put_wall_mark": call_wall,
        }
        _cp = _opt_prices.get("call_price")  # ATM call mark (grid Call Price column)
        _pp = _opt_prices.get("put_price")   # ATM put mark  (grid Put Price column)
        if _cp is not None:
            analytics["put_wall_mark"] = _cp  # BUY CALL signal shows the call price
        if _pp is not None:
            analytics["call_wall_mark"] = _pp  # BUY PUT signal shows the put price
        _ssvc = s.get("streaming_service")
        ticker_data = _ssvc.get_ticker_trend_data(t_upper) if _ssvc else {}
        new_alerts, next_state = diff_alerts(prev, analytics, spot)
        wall_zone = None
        if call_wall is not None and spot >= call_wall - _wall_buffer(call_wall):
            wall_zone = "Resistance"
        elif put_wall is not None and spot <= put_wall + _wall_buffer(put_wall):
            wall_zone = "Support"
        # Trend signal sourced directly from StreamingService.trend_data: a
        # reversal (bullish/bearish) takes precedence, otherwise a clean
        # direction (up/down). flat is not surfaced as an alert. This replaces
        # the previous wall-zone buy/sell classifier.
        _trend_reversal = ticker_data.get("trend_reversal")
        _trend_dir = ticker_data.get("trend")
        _trend_signal: str | None = None
        if _trend_reversal in ("bullish", "bearish"):
            _trend_signal = _trend_reversal
        elif _trend_dir in ("up", "down"):
            _trend_signal = _trend_dir

        # ---- Wall absorption (order absorption at the wall) ------------- #
        # Snapshot cumulative ATM volume when spot enters a wall zone; while
        # inside, "absorbed" is the flow consumed since entry.  When spot
        # leaves the zone after absorbing a heavy volume, the wall is treated
        # as BROKEN and a dedicated alert fires (high-conviction move).
        _flow_b, _flow_br = atm_svc.get_ticker_flow(t_upper)
        _flow_vol = (_flow_b or 0) + (_flow_br or 0) if _flow_b is not None else None
        _prev_zone = (prev or {}).get("_wall_zone")
        if _prev_zone != wall_zone:
            if wall_zone is not None:
                next_state["_zone_entry_vol"] = _flow_vol
            else:
                _entry_vol = (prev or {}).get("_zone_entry_vol")
                if _prev_zone in ("Resistance", "Support") and _entry_vol is not None and _flow_vol is not None:
                    _absorbed_at_zone = _flow_vol - _entry_vol
                    if _absorbed_at_zone >= _WALL_BREAK_MIN_ABSORBED:
                        new_alerts = [f"💥 {_prev_zone} wall BROKE after absorbing {_absorbed_at_zone:,.0f} contracts"]
                next_state["_zone_entry_vol"] = None
        else:
            next_state["_zone_entry_vol"] = (prev or {}).get("_zone_entry_vol")
        next_state["_wall_zone"] = wall_zone
        _absorbed_at_wall = None
        if wall_zone is not None and _flow_vol is not None and next_state.get("_zone_entry_vol") is not None:
            _absorbed_at_wall = max(0.0, _flow_vol - next_state["_zone_entry_vol"])

        last_ts = (prev or {}).get("last_alert_ts", 0.0)
        next_state["last_alert_ts"] = last_ts
        next_state["_prev_call_wall"] = call_wall
        next_state["_prev_put_wall"] = put_wall
        next_state["_wall_stable_count"] = _wall_stable
        if (new_alerts or _trend_signal) and _wall_stable >= 2 and now - last_ts >= _WALL_ZONE_ALERT_COOLDOWN:
            next_state["last_alert_ts"] = now
            next_state["_last_alert_texts"] = new_alerts
            state[t_upper] = next_state
            _cache = _ticker_analytics_cache.get(t_upper.split(":")[0])
            _buy_vol, _sell_vol, _net_60 = atm_svc.get_ticker_executed_flow(t_upper)
            if _cache:
                _atm_iv = _cache.get("atm_iv")
                _rv = _cache.get("rv", 0.0)
                _vrp = (_atm_iv - _rv) * 100 if _atm_iv is not None and _rv > 0 else None
                notify_alerts(new_alerts or [""], symbol=t_upper, spot=spot,
                              gex=_cache.get("net_gex"), vrp=_vrp,
                              iv_rank=_cache.get("iv_rank"),
                              wall_zone=wall_zone, pw=put_wall, cw=call_wall,
                              wall_mark=analytics.get("call_wall_mark") if wall_zone == "Resistance" else analytics.get("put_wall_mark"),
                              trend_alert=_trend_signal,
                              book_imbalance=ticker_data.get("book_imbalance"),
                              flow_speed=ticker_data.get("flow_speed"),
                              flow_acceleration=ticker_data.get("flow_acceleration"),
                              liquidity_flow=ticker_data.get("liquidity_flow"),
                              absorption=atm_svc.get_ticker_absorption(t_upper),
                              absorbed_at_wall=_absorbed_at_wall,
                              net_flow=_net_60,
                              disable_notification=False)
            else:
                notify_alerts(new_alerts or [""], symbol=t_upper, spot=spot,
                              wall_zone=wall_zone, pw=put_wall, cw=call_wall,
                              wall_mark=analytics.get("call_wall_mark") if wall_zone == "Resistance" else analytics.get("put_wall_mark"),
                              trend_alert=_trend_signal,
                              book_imbalance=ticker_data.get("book_imbalance"),
                              flow_speed=ticker_data.get("flow_speed"),
                              flow_acceleration=ticker_data.get("flow_acceleration"),
                              liquidity_flow=ticker_data.get("liquidity_flow"),
                              absorption=atm_svc.get_ticker_absorption(t_upper),
                              absorbed_at_wall=_absorbed_at_wall,
                              net_flow=_net_60,
                              disable_notification=False)
        else:
            state[t_upper] = next_state


# ---------------------------------------------------------------------------
# Periodic ticker poller (replaces standalone telegram_alerts.py cron job)
# ---------------------------------------------------------------------------

def _tte_from_dtes(dtes: list[int]) -> float | None:
    from zoneinfo import ZoneInfo
    valid = [d for d in dtes if d > 0]
    if not valid:
        return None
    now = datetime.now(ZoneInfo("America/New_York"))
    secs_since_930 = now.hour * 3600 + now.minute * 60 + now.second - 34200
    secs_since_930 = max(0, min(secs_since_930, 23400))
    secs_left = 23400 - secs_since_930
    return (min(valid) + secs_left / 23400) / 365.0



def _build_by_exp_all(data: list[dict], spot: float = 0.0) -> list[dict]:
    return aggregate_by_expiration(data, spot=spot)


def _build_strategy_alerts(
    data: list[dict], analytics: dict, spot: float, rv: float,
) -> list[str]:
    alerts: list[str] = []
    aks = sorted(set(e["strike"] for e in data))
    atm_k = min(aks, key=lambda k: abs(k - spot)) if aks else spot
    sd = [e for e in data if e.get("open_interest", 0) > 0 and (e.get("mark", 0) or 0) > 0 and ((e["strike"] == atm_k) or (e["type"] == "CALL" and e["strike"] > spot) or (e["type"] == "PUT" and e["strike"] < spot))]
    sd2 = _filter_strikes_near_atm(sd, spot, n=20)

    ssvi_surf = analytics.get("ssvi_surface")
    dtes = [e.get("dte", 0) for e in _build_by_exp_all(data, spot)]
    ir_tte = _tte_from_dtes(dtes) if ssvi_surf else None

    def _iv_dec(opt: dict) -> float:
        raw = opt.get("iv", 0) or 0
        return raw / 100.0 if raw > 3.0 else raw

    buy_sd = [e for e in sd2 if 0.35 <= abs(e.get("delta", 0) or 0) <= 0.55]
    buy_sd = [e for e in buy_sd if _iv_dec(e) - rv < 0]
    buy_sd = [e for e in buy_sd if 30 <= (e.get("days_to_exp", 0) or 0) <= 45]
    if ssvi_surf and ir_tte:
        buy_sd = [e for e in buy_sd if _iv_dec(e) - ssvi_surf.iv(float(e["strike"]), float(ir_tte)) < 0]

    sell_sd = [e for e in sd2 if 0.15 <= abs(e.get("delta", 0) or 0) <= 0.20]
    sell_sd = [e for e in sell_sd if _iv_dec(e) - rv > 0.05]
    sell_sd = [e for e in sell_sd if 30 <= (e.get("days_to_exp", 0) or 0) <= 45]
    if ssvi_surf and ir_tte:
        sell_sd = [e for e in sell_sd if _iv_dec(e) - ssvi_surf.iv(float(e["strike"]), float(ir_tte)) > 0]

    bias, _ = assess_market_bias(analytics, spot, iv_rank=analytics.get("iv_rank"))

    if buy_sd:
        buy_recs = [r for r in generate_recommendations(buy_sd, spot, strategy="Long Calls", all_data=buy_sd, rv=rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew"), ssvi_surface=ssvi_surf, ssvi_tte=ir_tte, bias=bias) if "No strong" not in r and "skip" not in r and "GEX Bias" not in r]
        if buy_recs:
            alerts.append("Buy Premium:")
            for r in buy_recs[:3]:
                alerts.append(f"  \u2022 {r}")

    if sell_sd:
        sell_recs = [r for r in generate_recommendations(sell_sd, spot, strategy="Short Calls", all_data=sell_sd, rv=rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew"), ssvi_surface=ssvi_surf, ssvi_tte=ir_tte, bias=bias) if "No strong" not in r and "skip" not in r and "GEX Bias" not in r]
        if sell_recs:
            alerts.append("Sell Premium:")
            for r in sell_recs[:3]:
                alerts.append(f"  \u2022 {r}")

    return alerts


async def _compute_walls_for_symbol(client, symbol: str) -> dict | None:
    """Lightweight recompute: fetch chain + parse + compute analytics only.

    Used for frequent wall refreshes — skips rate/yield/RV/IV-rank so the
    latest walls can be fetched much more often without hammering the API.
    Returns ``None`` when the chain cannot be loaded.
    """
    raw = None
    for attempt in range(3):
        try:
            raw = await fetch_option_chain(
                client, symbol, strike_count=75, include_quotes=True,
            )
            break
        except Exception:
            if attempt < 2:
                await asyncio.sleep(1.0)
    if raw is None:
        logger.warning("fetch_option_chain failed for %s after 3 retries", symbol)
        return None

    try:
        fallback_greeks = None
        fallback_sym = STREAM_SYMBOL_MAP.get(symbol.upper().lstrip("$"))
        if fallback_sym:
            fb_raw = await fetch_option_chain(
                client, fallback_sym, strike_count=75, include_quotes=True,
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
        data, spot = parse_option_chain(raw, fallback_greeks=fallback_greeks)
    except Exception as exc:
        logger.warning("wall parse failed for %s: %s", symbol, exc)
        return None
    if not data or spot <= 0:
        logger.warning("no option data for %s", symbol)
        return None

    analytics = compute_analytics(data, spot)
    return {"analytics": analytics, "spot": spot, "data": data}


async def _compute_for_symbol(client, symbol: str) -> dict | None:
    """Fetch chain + compute analytics + IV rank for one symbol."""
    raw = None
    for attempt in range(3):
        try:
            raw = await fetch_option_chain(
                client, symbol, strike_count=75, include_quotes=True,
            )
            break
        except Exception:
            if attempt < 2:
                await asyncio.sleep(1.0)
    if raw is None:
        logger.warning("fetch_option_chain failed for %s after 3 retries", symbol)
        return None

    try:
        r = await get_interest_rate(client)
        q = await get_yield(client, symbol)
    except Exception as exc:
        logger.warning("rate/yield failed for %s: %s", symbol, exc)
        r, q = 0.0, 0.0

    fallback_greeks = None
    etf_analytics = None
    fallback_sym = STREAM_SYMBOL_MAP.get(symbol.upper().lstrip("$"))
    if fallback_sym:
        try:
            fb_raw = await fetch_option_chain(
                client, fallback_sym, strike_count=75, include_quotes=True,
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
            etf_data, etf_spot = parse_option_chain(fb_raw, r=r, q=q)
            if etf_data and etf_spot > 0:
                etf_analytics = compute_analytics(etf_data, etf_spot, data_full=etf_data, r=r, q=q)
        except Exception as exc:
            logger.warning("fallback greeks failed for %s: %s", symbol, exc)

    data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
    if not data or spot <= 0:
        logger.warning("no option data for %s", symbol)
        return None

    analytics = compute_analytics(data, spot, r=r, q=q)

    if etf_analytics:
        if analytics.get("net_gex", 0) == 0:
            for key in ("net_gex", "total_call_gex", "total_put_gex",
                         "max_positive_gex", "max_negative_gex",
                         "max_positive_gex_strike", "max_negative_gex_strike",
                         "dealer_position"):
                if key in etf_analytics:
                    analytics[key] = etf_analytics[key]
        if analytics.get("ssvi_surface") is None and etf_analytics.get("ssvi_surface") is not None:
            analytics["ssvi_surface"] = etf_analytics["ssvi_surface"]
            analytics["ssvi_skew"] = etf_analytics["ssvi_skew"]
        if analytics.get("atm_iv") is None and etf_analytics.get("atm_iv") is not None:
            analytics["atm_iv"] = etf_analytics["atm_iv"]

    rv = 0.0
    try:
        rv = await get_20d_rv(client, symbol)
    except Exception as exc:
        logger.warning("failed to fetch 20d RV for %s: %s", symbol, exc)

    iv_rank = None
    try:
        df = load_candle_cache(symbol, "1d")
        if df.empty or len(df) < 2:
            raw_ph = await fetch_price_history_daily(client, symbol, years=1)
            if raw_ph:
                df = pd.DataFrame(raw_ph)
                save_candle_cache(df, symbol, "1d")
        if not df.empty and len(df) >= 2:
            df = df.sort_values("datetime")
            closes = df["close"].tolist()
            returns = [(closes[i] / closes[i - 1] - 1) for i in range(1, len(closes))]
            if len(returns) >= 2:
                recent_252 = returns[-252:]
                current = returns[-1]
                lo = min(recent_252)
                hi = max(recent_252)
                iv_rank = round((current - lo) / (hi - lo) * 100, 2) if hi != lo else 50.0
    except Exception as exc:
        logger.warning("failed to compute IV rank for %s: %s", symbol, exc)

    analytics["iv_rank"] = iv_rank
    return {"analytics": analytics, "spot": spot, "rv": rv, "data": data, "iv_rank": iv_rank}


async def _recompute_symbol(display_key: str, client, loop, atm_svc=None) -> None:
    """Event-driven: fetch chain, recompute analytics, check zones, send alerts."""
    try:
        _cache_key = display_key.split(":")[0]
        if _cache_key in STREAM_SYMBOL_MAP:
            api_symbol = f"${_cache_key}:X"
        else:
            api_symbol = display_key

        result = await _compute_for_symbol(client, api_symbol)
        if result is None:
            return
        analytics, spot = result["analytics"], result["spot"]
        rv, data, iv_rank = result["rv"], result["data"], result["iv_rank"]

        _ticker_analytics_cache[_cache_key] = {
            "net_gex": analytics.get("net_gex"),
            "atm_iv": analytics.get("atm_iv"),
            "rv": rv,
            "iv_rank": iv_rank,
        }

        # Push walls and ATM option prices to the ATM service.
        # Use display_key (retains :X suffix for index symbols) so
        # _find_flow_for_display can match the stored ticker key.
        if atm_svc:
            _pw = analytics.get("put_wall")
            _cw = analytics.get("call_wall")
            if _pw is not None or _cw is not None:
                atm_svc.set_ticker_walls(display_key, _pw, _cw)
                _exps = sorted(set(e["expiration"] for e in data))
                if _exps:
                    atm_svc.set_ticker_expiration(display_key, _exps[0])
            # Call/put marks at the ATM strike (populates Call/Put Price columns)
            _atm_k = analytics.get("atm_strike")
            if _atm_k:
                _atm_exps = sorted({e["expiration"] for e in data if e["strike"] == _atm_k})
                _call_mark = _put_mark = None
                if _atm_exps:
                    _front = _atm_exps[0]
                    for e in data:
                        if e["strike"] == _atm_k and e["expiration"] == _front:
                            if e["type"] == "CALL" and _call_mark is None:
                                _call_mark = e.get("mark")
                            elif e["type"] == "PUT" and _put_mark is None:
                                _put_mark = e.get("mark")
                atm_svc.set_ticker_option_prices(display_key, _call_mark, _put_mark)

        strikes = sorted(set(e["strike"] for e in data))
        if len(strikes) >= 2:
            _strike_inc[display_key] = min(
                strikes[i+1] - strikes[i] for i in range(len(strikes)-1)
            )

        _BASE_DIR = os.path.expanduser("~/.local/share/gex_app")
        _ALERT_STATE_FILE = os.path.join(_BASE_DIR, "alert_state.json")
        state = {}
        try:
            with open(_ALERT_STATE_FILE) as f:
                state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        prev = state.get(api_symbol)
        new_alerts, next_sym_state = diff_alerts(prev, analytics, spot)
        last_ts = (prev or {}).get("last_alert_ts", 0.0)
        next_sym_state["last_alert_ts"] = last_ts
        now_ts = _time_mod.monotonic()

        strat_alerts = _build_strategy_alerts(data, analytics, spot, rv)
        all_alerts = new_alerts + strat_alerts

        if all_alerts and now_ts - last_ts >= _WALL_ZONE_ALERT_COOLDOWN:
            next_sym_state["last_alert_ts"] = now_ts
            atm_iv = analytics.get("atm_iv")
            vrp = (atm_iv - rv) * 100 if atm_iv is not None and rv > 0 else None
            await loop.run_in_executor(
                None, partial(
                    notify_alerts, all_alerts,
                    symbol=api_symbol, spot=spot,
                    gex=analytics.get("net_gex"), vrp=vrp,
                    iv_rank=iv_rank, disable_notification=False,
                ),
            )

        state[api_symbol] = next_sym_state
        try:
            os.makedirs(_BASE_DIR, exist_ok=True)
            tmp = _ALERT_STATE_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f, indent=2)
            os.replace(tmp, _ALERT_STATE_FILE)
        except Exception as exc:
            logger.error("failed to persist alert state: %s", exc)

    except Exception as exc:
        logger.warning("[%s] recompute failed: %s", display_key, exc)


async def _refresh_walls_for_symbol(display_key: str, client, atm_svc=None) -> None:
    """Lightweight wall refresh: fetch chain + recompute walls, then push
    the latest walls / expiration / ATM marks to the ATM service.

    Runs frequently (movement- and time-triggered) so the Order Flow grid
    always shows the freshest support/resistance without a full recompute.
    """
    try:
        _cache_key = display_key.split(":")[0]
        if _cache_key in STREAM_SYMBOL_MAP:
            api_symbol = f"${_cache_key}:X"
        else:
            api_symbol = display_key

        result = await _compute_walls_for_symbol(client, api_symbol)
        if result is None:
            return
        analytics, data = result["analytics"], result["data"]

        if atm_svc:
            _pw = analytics.get("put_wall")
            _cw = analytics.get("call_wall")
            if _pw is not None or _cw is not None:
                atm_svc.set_ticker_walls(display_key, _pw, _cw)
                _exps = sorted(set(e["expiration"] for e in data))
                if _exps:
                    atm_svc.set_ticker_expiration(display_key, _exps[0])
            # Call/put marks at the ATM strike (populates Call/Put Price columns)
            _atm_k = analytics.get("atm_strike")
            if _atm_k:
                _atm_exps = sorted({e["expiration"] for e in data if e["strike"] == _atm_k})
                _call_mark = _put_mark = None
                if _atm_exps:
                    _front = _atm_exps[0]
                    for e in data:
                        if e["strike"] == _atm_k and e["expiration"] == _front:
                            if e["type"] == "CALL" and _call_mark is None:
                                _call_mark = e.get("mark")
                            elif e["type"] == "PUT" and _put_mark is None:
                                _put_mark = e.get("mark")
                atm_svc.set_ticker_option_prices(display_key, _call_mark, _put_mark)

        strikes = sorted(set(e["strike"] for e in data))
        if len(strikes) >= 2:
            _strike_inc[display_key] = min(
                strikes[i+1] - strikes[i] for i in range(len(strikes)-1)
            )
    except Exception as exc:
        logger.warning("[%s] wall refresh failed: %s", display_key, exc)


def render_market_status():
    """Display the market status indicator on the same header row as ATM Order Flow.
    
    This indicator should be displayed every fragment tick (every 2s) so it's
    always visible. The visual markup is lightweight and Streamlit-diffable,
    so it won't cause DOM flicker when re-rendered.

    Called from the Order Flow tab's render_flow_frag() function.
    """
    _open = is_market_open()
    _color = "#00cc96" if _open else "#E69500"
    _label = "Market Open" if _open else "Market Closed"
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:flex-end;'
        f'gap:8px;margin-bottom:12px;">'
        f'<span style="font-size:35px;line-height:35px;color:{_color};">●</span>'
        f'<span style="font-size:22px;font-weight:500;">{_label}</span></div>',
        unsafe_allow_html=True,
    )


def _format_expiration(exp: str | None) -> str:
    """Format expiration date into MM-DD (X days) for display.
    
    Returns empty string for None/invalid input.
    """
    if not exp:
        return ""
    try:
        exp_date = date.fromisoformat(exp)
        dte = (exp_date - date.today()).days
        mmdd = exp[5:10]  # "MM-DD"
        return f"{mmdd} ({dte}d)" if dte >= 0 else f"{mmdd} (0d)"
    except (ValueError, TypeError):
        return exp or ""


def render_flow_legend_and_style():
    """Inject only the CSS styles needed for the Order Flow grid.

    Called once per outer-fragment tick (every ~10 s) instead of every 2 s
    to prevent HTML-DOM flicker caused by re-injecting the same markup.

    Called from render_tabs_frag() in app.py to ensure styles are injected
    only once per session when the Order Flow tab is active.
    """
    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] { overflow-x: auto; max-width: 100%; }
    div[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
    </style>
    """, unsafe_allow_html=True)


def render_atm_order_flow_grid():
    """Render the ATM Order Flow as a Streamlit dataframe (mirrors the style of
    the main app's Options Data table): one row per tracked ticker with
    Bullish / Bearish flow, a coloured Status cell, and formatted numbers.

    Used by the Order Flow tab in the main app (wrapped in a refresh fragment).
    The legend and CSS style are rendered separately via
    ``render_flow_legend_and_style`` so they are not re-injected every tick.

    The styled DataFrame is cached in session state and only rebuilt when the
    underlying data actually changes.  A fixed Styler UUID prevents pandas
    from generating unique CSS class names per instance, which would cause
    Streamlit to see a "change" and re-render the DOM even when the data
    is identical.
    """
    s = st.session_state
    current_sym = _normalize_display_symbol(s.get("symbol", ""))
    atm_svc = s.get("atm_option_service")

    update_flow_cache()

    tickers = s.get("ticker_history", [])
    _svc = s.get("streaming_service")
    if _svc is not None:
        _svc.subscribe_book_symbols([_get_stream_symbol(t) for t in tickers])
    rows = []
    if tickers:
        for t in tickers:
            t_upper = _normalize_display_symbol(t)
            opt_prices = atm_svc.get_ticker_option_prices(t_upper) if atm_svc else {}
            atm_strike = atm_svc.get_ticker_atm_strike(t_upper) if atm_svc else None
            spot = atm_svc.get_ticker_spot(t_upper) if atm_svc else None
            # Get book imbalance and trend from ticker data (L2-sourced via
            # StreamingService.trend_data: trend is up/down/flat, reversal is
            # bullish/bearish when the direction flips down->up / up->down).
            book_imbalance = None
            flow_speed = 0
            flow_acceleration = 0
            trend_display = "flat"
            if _svc is not None:
                ticker_data = _svc.get_ticker_trend_data(t_upper)
                book_imbalance = ticker_data.get("book_imbalance")
                flow_speed = ticker_data.get("flow_speed", 0)
                flow_acceleration = ticker_data.get("flow_acceleration", 0)
                # Reversal (bullish/bearish) takes precedence over the bare
                # direction so the Trend column surfaces the flip the moment
                # it is detected; otherwise show the current direction.
                trend_display = ticker_data.get("trend_reversal") or ticker_data.get("trend") or "flat"
            
            # Support (Put Wall) / Resistance (Call Wall): prefer per-ticker value
            # set by fetch_data, fall back to session-state analytics for the
            # current chart symbol so the columns are never empty without a manual
            # Refresh.
            put_wall_val = atm_svc.get_ticker_put_wall(t_upper) if atm_svc else None
            call_wall_val = atm_svc.get_ticker_call_wall(t_upper) if atm_svc else None
            if put_wall_val is None and t_upper == current_sym:
                put_wall_val = (s.get("analytics") or {}).get("put_wall")
            if call_wall_val is None and t_upper == current_sym:
                call_wall_val = (s.get("analytics") or {}).get("call_wall")

            _buy_vol, _sell_vol, _net_60 = (
                atm_svc.get_ticker_executed_flow(t_upper) if atm_svc else (None, None, None)
            )
            rows.append({
                "Ticker": t_upper,
                "Spot": spot,
                "ATM Strike": atm_strike,
                "Expiration": atm_svc.get_ticker_expiration(t_upper) if atm_svc else None,
                "Support": put_wall_val,
                "Resistance": call_wall_val,
                "Call Price": opt_prices.get("call_price"),
                "Put Price": opt_prices.get("put_price"),
                "Trend": trend_display,
                "Book Imbalance": book_imbalance,
                "Flow Speed": flow_speed,
                "Flow Acceleration": flow_acceleration,
                "Liquidity Flow": ticker_data.get("liquidity_flow") if _svc is not None else None,
                "Absorption": atm_svc.get_ticker_absorption(t_upper) if atm_svc else None,
                "Buy/Sell": (f"{_buy_vol:,.0f} | {_sell_vol:,.0f}"
                             if _buy_vol is not None and _sell_vol is not None else None),
                "Net Flow": _net_60,
            })

    if not rows:
        st.info("No tickers tracked yet. Add tickers on the main GammaEx page first.")
        return

    # Hash the row data to detect whether anything actually changed.
    # Include a 10 s epoch so the ATM Strike column is re-rendered every
    # 10 s even when the cached value is unchanged, keeping the display
    # visibly "alive" for users who watch the grid.
    # Include a 60 s epoch so the Support / Resistance wall columns are
    # re-rendered every 60 s even when their stored values are unchanged.
    _atm_epoch = int(_time_mod.time() // 10)
    _wall_epoch = int(_time_mod.time() // 60)
    data_key = tuple(
        (r["Ticker"], r["Spot"], r["ATM Strike"], r["Expiration"],
         r["Support"], r["Resistance"], r["Trend"],
          r["Call Price"], r["Put Price"], r["Book Imbalance"], r["Flow Speed"], r["Flow Acceleration"], r["Liquidity Flow"], r["Absorption"], r["Buy/Sell"], r["Net Flow"])
        for r in rows
    )
    data_hash = hash((data_key, _atm_epoch, _wall_epoch))

    cached_hash = s.get("_flow_styled_hash")
    cached_styled = s.get("_flow_styled")
    if data_hash == cached_hash and cached_styled is not None:
        st.dataframe(cached_styled, height=700, width="stretch")
        return

    df = pd.DataFrame(rows)

    def _trend_color(val):
        """Color the Trend label (up/down/flat/bullish/bearish) by direction.

        Reversal labels (bullish/bearish) are bolded to surface the flip;
        up/down are green/red; flat is amber.
        """
        if val is None:
            return ""
        val_l = val.lower()
        if val_l in ("bearish", "down"):
            return "color: #ef5350; font-weight: bold;"
        if val_l in ("bullish", "up"):
            return "color: #00cc96; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _book_imbalance_color(val):
        """Color the book imbalance value based on magnitude."""
        if val is None:
            return ""
        if val > 0.3:
            return "color: #00cc96; font-weight: bold;"
        if val < -0.3:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _flow_speed_color(val):
        if val is None:
            return ""
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _flow_acceleration_color(val):
        if val is None:
            return ""
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _absorption_color(val):
        """Color order absorption (contracts per $1): green = heavy flow
        absorbed with little price move, red = price drifting on thin flow."""
        if val is None:
            return ""
        if val >= _ABSORPTION_HIGH:
            return "color: #00cc96; font-weight: bold;"
        if val < _ABSORPTION_LOW:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _net_flow_color(val):
        """Color the 60 s net executed flow (buy - sell) by sign."""
        if val is None:
            return ""
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _liquidity_flow_color(val):
        """Color L2 liquidity flow (net depth change over 60 s): green =
        liquidity being posted (book refilling), red = liquidity draining."""
        if val is None:
            return ""
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _spot_bg(row):
        spot = row["Spot"]
        support = row["Support"]
        resistance = row["Resistance"]
        score = 0
        _near_wall = False
        if spot is not None and support is not None:
            pw_buf = _wall_buffer(support)
            if spot <= support + pw_buf:
                score += 1
                _near_wall = True
        if spot is not None and resistance is not None:
            cw_buf = _wall_buffer(resistance)
            if spot >= resistance - cw_buf:
                score -= 1
                _near_wall = True
        if _near_wall:
            bi = row.get("Book Imbalance")
            if bi is not None:
                if bi > 0.3:
                    score += 1
                elif bi < -0.3:
                    score -= 1
            fs = row.get("Flow Speed")
            if fs is not None:
                if fs > 0:
                    score += 1
                elif fs < 0:
                    score -= 1
            fa = row.get("Flow Acceleration")
            if fa is not None:
                if fa > 0:
                    score += 1
                elif fa < 0:
                    score -= 1
        styles = [""] * len(row)
        col_idx = list(row.index)
        spot_i = col_idx.index("Spot")
        if score >= 2:
            styles[spot_i] = "background-color: #a5d6a7"
        elif score == 1:
            styles[spot_i] = "background-color: #ccffcc"
        elif score <= -2:
            styles[spot_i] = "background-color: #ef9a9a"
        elif score == -1:
            styles[spot_i] = "background-color: #ffcccc"
        return styles

    _styler = df.style.set_uuid("flow_grid")
    _styler = _styler.apply(_spot_bg, axis=1)

    if hasattr(_styler, "map"):
        _styler = _styler.map(_trend_color, subset=["Trend"])
        _styler = _styler.map(_book_imbalance_color, subset=["Book Imbalance"])
        _styler = _styler.map(_flow_speed_color, subset=["Flow Speed"])
        _styler = _styler.map(_flow_acceleration_color, subset=["Flow Acceleration"])
        _styler = _styler.map(_absorption_color, subset=["Absorption"])
        _styler = _styler.map(_net_flow_color, subset=["Net Flow"])
        _styler = _styler.map(_liquidity_flow_color, subset=["Liquidity Flow"])
    else:
        _styler = _styler.apply(_trend_color, subset=["Trend"])
        _styler = _styler.apply(_book_imbalance_color, subset=["Book Imbalance"])
        _styler = _styler.apply(_flow_speed_color, subset=["Flow Speed"])
        _styler = _styler.apply(_flow_acceleration_color, subset=["Flow Acceleration"])
        _styler = _styler.apply(_absorption_color, subset=["Absorption"])
        _styler = _styler.apply(_net_flow_color, subset=["Net Flow"])
        _styler = _styler.apply(_liquidity_flow_color, subset=["Liquidity Flow"])

    styled = _styler.format({
        "Spot": lambda v: f"${v:,.2f}" if v is not None else "",
        "ATM Strike": lambda v: f"${v:,.2f}" if v is not None else "",
        "Expiration": lambda v: _format_expiration(v),
        "Support": lambda v: f"${v:,.2f}" if v is not None else "",
        "Resistance": lambda v: f"${v:,.2f}" if v is not None else "",
        "Trend": lambda v: v,
        "Call Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Put Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Book Imbalance": lambda v: f"{v:+.2f}" if v is not None else "",
        "Flow Speed": lambda v: f"{v:+,.0f}" if v is not None else "",
        "Flow Acceleration": lambda v: f"{v:+,.2f}" if v is not None else "",
        "Absorption": lambda v: f"{v:,.0f}" if v is not None else "",
        "Liquidity Flow": lambda v: f"{v:+,.0f}" if v is not None else "",
        "Buy/Sell": lambda v: v if v is not None else "",
        "Net Flow": lambda v: f"{v:+,.0f}" if v is not None else "",
    })

    s._flow_styled_hash = data_hash
    s._flow_styled = styled
    st.dataframe(styled, height=700, width="stretch")


@st.fragment(run_every=2)
def render_flow_frag():
    """Renders the Order Flow dataframe with fast updates.

    Includes a watchdog: if no option ticks arrive for 60 s while the
    market is open, the feed is assumed dead and a reconnection is forced.
    """
    s = st.session_state
    if not s.get("client"):
        return
    stream_symbol = s.get("symbol", "SPY").upper().lstrip("$")
    mapped = STREAM_SYMBOL_MAP.get(stream_symbol, stream_symbol)

    # Watchdog: detect a silently dead option feed.  If the market is
    # open and no ticks have arrived for 60 s, force re-registration
    # so the next ensure_atm_streaming cycle re-subscribes everything.
    atm_svc = s.get("atm_option_service")
    if atm_svc and is_market_open() and atm_svc.is_running:
        if atm_svc.is_feed_stale(max_age_seconds=60):
            print("[_flow_grid] watchdog: feed stale >60 s, forcing reconnect")
            atm_svc._needs_reconnect = True

    ensure_atm_streaming(mapped)
    st.subheader("Order Flow")
    # Market status indicator at the header row
    render_market_status()
    # CSS styles for the dataframe (only need to inject once)
    if "_flow_css_injected" not in s:
        render_flow_legend_and_style()
        s["_flow_css_injected"] = True
    render_atm_order_flow_grid()
    # Drive wall-zone Telegram alerts from the *streaming* spot the grid
    # displays, so alerts fire in real time when the grid colors a cell.
    maybe_fire_wall_zone_alerts()
