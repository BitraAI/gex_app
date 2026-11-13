"""Shared ATM order-flow rendering used by both the main app page and
the dedicated Order Flow tab.

Kept free of any st.set_page_config / global app setup so it can be imported
safely from either entry point without re-running app.py's top-level code.
"""

import asyncio
import html
import json
import logging
import os
import random
import threading
import time as _time_mod
import streamlit as st
from collections import deque
from functools import partial
from scripts._constants import (STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP, TICKER_RETRY_COUNT,
                        FLOW_WATCHDOG_STALE_SECONDS,
                        ATM_SUBSCRIBE_BACKOFF_BASE, ATM_SUBSCRIBE_BACKOFF_RANGE)
from scripts._utils import compute_strike_increment, format_expiration, is_market_open
from scripts.option_streaming_service import _find_flow_for_display, _normalize_display_symbol, _get_stream_symbol
from scripts.client import fetch_quotes
from scripts.calculations import calculate_atm_strike
from scripts.signals import build_strategy_alerts
from scripts.telegram_notifier import diff_alerts, notify_alerts


# Per-ticker analytics cache + event-driven trigger tracking
_ticker_analytics_cache: dict[str, dict] = {}
_last_ref_price: dict[str, float] = {}   # last reference price for trigger
_last_recompute_ts: dict[str, float] = {}  # last wall recompute time (monotonic)
_last_full_recompute_ts: dict[str, float] = {}  # last full recompute time (monotonic)
_strike_inc: dict[str, float] = {}       # known strike increment per ticker
logger = logging.getLogger(__name__)

_FETCH_RETRIES = TICKER_RETRY_COUNT

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
                await asyncio.sleep(ATM_SUBSCRIBE_BACKOFF_BASE + random.random() * ATM_SUBSCRIBE_BACKOFF_RANGE)
            else:
                raise


def _ensure_async_loop() -> asyncio.AbstractEventLoop:
    """Get or create the shared asyncio event loop (must match app.py)."""
    _ASYNC_LOOP = getattr(_ensure_async_loop, "_loop", None)
    if _ASYNC_LOOP is None:
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
                    logger.warning("[ensure_atm_streaming] index quote fetch failed: %s", e)

    if svc and svc.is_connected and atm_svc and _first_exp:

        # Pre-fetch ETF proxy spots via REST only every ~10 s to avoid
        # blocking the Streamlit thread on every 2-second fragment tick.
        # Between fetches we feed whatever is already in spot_cache.
        # Equity tickers get their spot from this proxy quote; index
        # symbols (SPX/RUT/NDX) keep their index-level spot (fed by the
        # index quote above) but ALSO get the ETF-proxy price pushed via
        # set_ticker_proxy_spot so their Level-1 / OPTIONS_BOOK
        # subscriptions use real proxy strikes (SPY ~570) instead of
        # non-existent index-level strikes (SPX ~5700).
        _last_fetch_ts = s.get("_spot_fetch_ts", 0.0)
        if _time_mod.time() - _last_fetch_ts >= 10:
            s["_spot_fetch_ts"] = _time_mod.time()
            _stream_symbols = list(dict.fromkeys(
                _get_stream_symbol(t) for t in _all_tickers
            ))
            try:
                quote_resp = run_async(fetch_quotes(s.client, _stream_symbols))
                for disp_sym in _all_tickers:
                    _disp_upper = _normalize_display_symbol(disp_sym)
                    _sym = STREAM_SYMBOL_MAP.get(_disp_upper, _disp_upper)
                    qd = quote_resp.get(_sym, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(_sym, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is None or float(last) <= 0:
                        continue
                    if _disp_upper in INDEX_QUOTE_MAP:
                        atm_svc.set_ticker_proxy_spot(_disp_upper, float(last))
                    else:
                        s.spot_cache[_disp_upper] = float(last)
            except Exception as e:
                logger.warning("[ensure_atm_streaming] spot pre-fetch failed: %s", e)

        # Refresh the Call/Put Price marks for every tracked ticker every
        # ~2 s.  The streamed L1 bids only cover ATM strikes, and the wall
        # / ATM marks are otherwise pushed only by the throttled analytics
        # recompute (30-180 s), which makes the columns look frozen.  Quote
        # the ATM and wall-strike OCC symbols in one batched REST call.
        _last_opt_ts = s.get("_opt_price_fetch_ts", 0.0)
        if _time_mod.time() - _last_opt_ts >= 2:
            s["_opt_price_fetch_ts"] = _time_mod.time()
            _quote_map = {}
            for _t in _all_tickers:
                _t_upper = _normalize_display_symbol(_t)
                for _label, _occ in atm_svc.get_ticker_quote_symbols(_t_upper).items():
                    _quote_map.setdefault(_occ, (_t_upper, _label))
            if _quote_map:
                try:
                    _resp = run_async(fetch_quotes(s.client, list(_quote_map.keys())))
                    _per_ticker = {}
                    for _occ, (_tk, _label) in _quote_map.items():
                        _occ_clean = _occ.replace(" ", "")
                        qd = _resp.get(_occ) or _resp.get(_occ_clean) or {}
                        qq = (
                            qd.get("quote")
                            or qd.get(_occ)
                            or qd.get(_occ_clean)
                            or qd
                        )
                        if not isinstance(qq, dict):
                            continue
                        mark = qq.get("mark") or qq.get("lastPrice") or qq.get("closePrice")
                        if mark is None or float(mark) <= 0:
                            continue
                        _per_ticker.setdefault(_tk, {})[_label] = float(mark)
                    for _tk, _marks in _per_ticker.items():
                        _pwc = _marks.get("put_wall_call")
                        _cwp = _marks.get("call_wall_put")
                        _cwc = _marks.get("call_wall_call")
                        _pwp = _marks.get("put_wall_put")
                        if _pwc is not None or _cwp is not None or _cwc is not None or _pwp is not None:
                            atm_svc.set_ticker_wall_prices(_tk, _pwc, _cwp, _cwc, _pwp)
                        _acall = _marks.get("call_atm")
                        _aput = _marks.get("put_atm")
                        if _acall is not None or _aput is not None:
                            atm_svc.set_ticker_option_prices(_tk, _acall, _aput)
                except Exception as e:
                    logger.warning("[ensure_atm_streaming] option quote refresh failed: %s", e)

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
                        "expiration2": None,
                        "print_history": deque(),
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
                                    }
                    # Now set the walls
                    atm_svc.set_ticker_walls(current_sym, put_wall, call_wall)
        
        # Force wall recomputes for all tracked non-index tickers if needed
        if atm_svc:
            tracked = atm_svc.tracked_tickers()
            now = _time_mod.monotonic()
            _client = atm_svc._client
            _loop = atm_svc._loop
            
            # First, check if any ticker needs a wall refresh
            for t_sym in tracked:
                t_upper = _normalize_display_symbol(t_sym)
                # Skip index symbols - their walls come from proxy options
                if t_upper in INDEX_QUOTE_MAP:
                    continue
                
                # Get spot for this ticker
                spot = atm_svc.get_ticker_spot(t_upper)
                if spot is None:
                    continue
                
                # Check if we need to schedule a wall refresh
                _ref = _last_ref_price.get(t_upper)
                _inc = _strike_inc.get(t_upper, 1.0)
                _last_re = _last_recompute_ts.get(t_upper, 0.0)
                _moved = _ref is None or abs(spot - _ref) >= _inc / 2
                _stale = (now - _last_re) >= _WALL_RECOMPUTE_MAX_INTERVAL
                
                # Force refresh if the ticker has no walls set yet, or if the interval has passed
                _current_ticker = _find_flow_for_display(atm_svc._ticker_flows, t_upper)
                has_walls = _current_ticker and (_current_ticker.get("put_wall") is not None or _current_ticker.get("call_wall") is not None)
                
                should_refresh = (
                    not has_walls or  # No walls set yet - force refresh
                    _moved or  # Spot moved enough
                    _stale  # Max interval elapsed
                ) and (now - _last_re >= _WALL_RECOMPUTE_MIN_INTERVAL)  # But respect min interval
                
                if should_refresh:
                    # Schedule a wall refresh for this ticker
                    _last_ref_price[t_upper] = spot
                    _last_recompute_ts[t_upper] = now
                    _last_full_recompute_ts[t_upper] = now  # Also trigger full recompute
                    if _client:
                        asyncio.run_coroutine_threadsafe(
                            _recompute_symbol(t_upper, _client, _loop, atm_svc), _loop,
                        )



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


def _wall_buffer(wall: float | None) -> float:
    """Near-wall zone width: 0.02 % of the wall price, floored at 5 cents so
    low-priced tickers still get a meaningful zone."""
    if wall is None:
        return 0.0
    return max(abs(wall) * _WALL_ZONE_BUFFER, _WALL_ZONE_MIN_BUFFER)


def _wall_price_marks(
    opt_prices: dict,
    wall_prices: dict,
    call_wall: float | None,
    put_wall: float | None,
    spot: float | None,
) -> tuple[float | None, float | None]:
    """Return (CALL, PUT) marks at whichever wall (resistance/support) is
    nearest to spot, falling back to the ATM prices when a wall-level mark is
    unavailable.  Used by both the alert path and the grid columns so the
    wall-pricing logic exists in one place."""
    _dist_cw = abs(spot - call_wall) if call_wall is not None and spot is not None else float("inf")
    _dist_pw = abs(spot - put_wall) if put_wall is not None and spot is not None else float("inf")
    if _dist_cw <= _dist_pw:
        _call_p = wall_prices.get("call_wall_call_price") or opt_prices.get("call_price")
        _put_p = wall_prices.get("call_wall_put_price") or opt_prices.get("put_price")
    else:
        _call_p = wall_prices.get("put_wall_call_price") or opt_prices.get("call_price")
        _put_p = wall_prices.get("put_wall_put_price") or opt_prices.get("put_price")
    return _call_p, _put_p


def _maybe_schedule_wall_refresh(t_upper: str, spot: float, now: float,
                                 include_full: bool = False, atm_svc=None) -> None:
    """Hybrid wall-refresh trigger for ONE ticker.

      - fast path: lightweight wall refresh when price moves >= half a
        strike OR the freshness floor (MAX interval) elapses — throttled
        to at most once per MIN interval per ticker.
      - slow path (include_full=True): full recompute (analytics + IV rank
        + alerts context) at a fixed slower cadence so alert headers stay
        fresh too.

    Writes the module-level throttle dicts (_last_ref_price,
    _last_recompute_ts, _last_full_recompute_ts, _strike_inc), so callers
    on different tabs (the Order Flow alerts loop AND the Candlesticks
    fragment) share one cadence and never double-schedule a REST refresh
    for the same ticker.
    """
    _client = st.session_state.get("client")
    _loop = _ensure_async_loop()
    _ref = _last_ref_price.get(t_upper)
    _inc = _strike_inc.get(t_upper, 1.0)
    _last_re = _last_recompute_ts.get(t_upper, 0.0)
    _moved = _ref is None or abs(spot - _ref) >= _inc / 2
    _stale = (now - _last_re) >= _WALL_RECOMPUTE_MAX_INTERVAL
    if (_moved or _stale) and (_last_re == 0.0 or (now - _last_re) >= _WALL_RECOMPUTE_MIN_INTERVAL):
        _last_ref_price[t_upper] = spot
        _last_recompute_ts[t_upper] = now
        if _client:
            asyncio.run_coroutine_threadsafe(
                _refresh_walls_for_symbol(t_upper, _client, atm_svc), _loop,
            )
    if include_full and (now - _last_full_recompute_ts.get(t_upper, 0.0)) >= _WALL_FULL_RECOMPUTE_INTERVAL:
        _last_full_recompute_ts[t_upper] = now
        if _client:
            asyncio.run_coroutine_threadsafe(
                _recompute_symbol(t_upper, _client, _loop, atm_svc), _loop,
            )


def maybe_refresh_ticker_walls(display_symbol: str) -> None:
    """Public: schedule the lightweight wall refresh for one ticker.

    Called every Candlesticks-tab tick so the Resistance/Support lines on
    the candlestick chart track moving walls even while the Order Flow
    tab (whose alerts loop normally drives wall refreshes) is not open.
    The throttle state is SHARED with maybe_fire_wall_zone_alerts, so the
    total REST cadence stays capped at the MIN/MAX intervals per ticker.

    No-op when the ATM service, client, or a streaming spot is missing
    (the refresh needs a spot to compare against the last reference).
    """
    atm_svc = st.session_state.get("atm_option_service")
    if atm_svc is None or st.session_state.get("client") is None:
        return
    t_upper = _normalize_display_symbol(display_symbol)
    if not t_upper:
        return
    spot = atm_svc.get_ticker_spot(t_upper)
    if spot is None:
        return
    _maybe_schedule_wall_refresh(t_upper, spot, _time_mod.monotonic(),
                                 include_full=False, atm_svc=atm_svc)


def maybe_fire_wall_zone_alerts() -> None:
    """Inspect every tracked ticker's streaming spot vs its walls and push
    diff_alerts (wall zone, gamma flip, wall changes) to Telegram.
    """
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    if atm_svc is None:
        return
    now = _time_mod.monotonic()
    state = s.setdefault("atm_alert_state", {})

    for t in atm_svc.tracked_tickers():
        t_upper = _normalize_display_symbol(t)
        spot = atm_svc.get_ticker_spot(t_upper)
        call_wall = atm_svc.get_ticker_call_wall(t_upper)
        put_wall = atm_svc.get_ticker_put_wall(t_upper)
        if spot is None:
            continue

        # Hybrid trigger for wall refreshes (fast + slow path; see
        # _maybe_schedule_wall_refresh for the cadence rules).
        _maybe_schedule_wall_refresh(t_upper, spot, now, include_full=True, atm_svc=atm_svc)

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

        _ticker_ana = _ticker_analytics_cache.get(t_upper.split(":")[0]) or {}
        analytics = {
            "gamma_flip": None,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "dealer_position": None,
            "atm_strike": atm_svc.get_ticker_atm_strike(t_upper),
            "call_wall_mark": call_wall,
            "put_wall_mark": put_wall,
            "oi_support": _ticker_ana.get("oi_support"),
            "oi_resistance": _ticker_ana.get("oi_resistance"),
            "volume_support": _ticker_ana.get("volume_support"),
            "volume_resistance": _ticker_ana.get("volume_resistance"),
        }
        _opt_prices = atm_svc.get_ticker_option_prices(t_upper) or {}
        _wall_prices = atm_svc.get_ticker_wall_prices(t_upper) or {}
        _call_p, _put_p = _wall_price_marks(_opt_prices, _wall_prices, call_wall, put_wall, spot)
        analytics["call_wall_mark"] = call_wall
        analytics["put_wall_mark"] = put_wall
        if _call_p is not None:
            analytics["call_wall_mark"] = _call_p
        if _put_p is not None:
            analytics["put_wall_mark"] = _put_p
        new_alerts, next_state = diff_alerts(prev, analytics, spot)
        wall_zone = None
        if call_wall is not None and call_wall - _wall_buffer(call_wall) <= spot <= call_wall + _wall_buffer(call_wall):
            wall_zone = "Resistance"
        elif put_wall is not None and put_wall + _wall_buffer(put_wall) >= spot >= put_wall - _wall_buffer(put_wall):
            wall_zone = "Support"

        # ---- Wall zone entry bookkeeping (for break absorption) --------- #
        # Snapshot cumulative ATM volume when spot enters a wall zone; while
        # inside, ``_absorbed_at_wall`` is the flow consumed since entry.
        # This is reported on break headers as context only — it no longer
        # *drives* the break trigger, because raw cumulative volume
        # inflates with quiet time spent in the zone and produced wrong signals.
        _flow_b, _flow_br = atm_svc.get_ticker_flow(t_upper)
        _flow_vol = None if _flow_b is None and _flow_br is None else (_flow_b or 0) + (_flow_br or 0)
        _prev_zone = (prev or {}).get("_wall_zone")
        if _prev_zone != wall_zone:
            next_state["_zone_entry_vol"] = _flow_vol if wall_zone is not None else None
        else:
            next_state["_zone_entry_vol"] = (prev or {}).get("_zone_entry_vol")
        next_state["_wall_zone"] = wall_zone
        _absorbed_at_wall = None
        if wall_zone is not None and _flow_vol is not None and next_state.get("_zone_entry_vol") is not None:
            _absorbed_at_wall = max(0.0, _flow_vol - next_state["_zone_entry_vol"])

        pass

        last_ts = (prev or {}).get("last_alert_ts", 0.0)
        next_state["last_alert_ts"] = last_ts
        next_state["_prev_call_wall"] = call_wall
        next_state["_prev_put_wall"] = put_wall
        next_state["_wall_stable_count"] = _wall_stable
        # Wall-broke alerts are high-confidence (directional pierce confirmed),
        # so they fire regardless of wall stability.
        _cache = _ticker_analytics_cache.get(t_upper.split(":")[0]) or {}
        if new_alerts and now - last_ts >= _WALL_ZONE_ALERT_COOLDOWN:
            next_state["last_alert_ts"] = now
            next_state["_last_alert_texts"] = new_alerts
            state[t_upper] = next_state
            notify_alerts(new_alerts or [""], symbol=t_upper, spot=spot,
                          gex=_cache.get("net_gex"),
                          wall_zone=wall_zone, pw=put_wall, cw=call_wall,
                          wall_mark=analytics.get("call_wall_mark") if wall_zone == "Resistance" else analytics.get("put_wall_mark"),
                          absorbed_at_wall=_absorbed_at_wall,
                          oi_support=analytics.get("oi_support"),
                          oi_resistance=analytics.get("oi_resistance"),
                          volume_support=analytics.get("volume_support"),
                          volume_resistance=analytics.get("volume_resistance"),
                           disable_notification=False)
        else:
            state[t_upper] = next_state


# ---------------------------------------------------------------------------
# Periodic ticker poller (replaces standalone telegram_alerts.py cron job)
# ---------------------------------------------------------------------------

async def _compute_walls_for_symbol(client, symbol: str) -> dict | None:
    """Lightweight recompute: fetch chain + parse + compute analytics only.

    Used for frequent wall refreshes — skips rate/yield/RV/IV-rank so the
    latest walls can be fetched much more often without hammering the API.
    Returns ``None`` when the chain cannot be loaded.
    """
    from scripts.chain_parser import fetch_and_parse_chain
    
    _sym = symbol.upper().lstrip("$")
    is_index = _sym in STREAM_SYMBOL_MAP
    
    result = await fetch_and_parse_chain(
        client, symbol, include_quotes=True, is_index_symbol=is_index
    )
    
    if not result["data"] or result["spot"] <= 0:
        logger.warning("no option data for %s", symbol)
        return None
    
    return {
        "analytics": result["analytics"],
        "spot": result["spot"],
        "data": result["data"]
    }





async def _recompute_symbol(display_key: str, client, loop, atm_svc=None) -> None:
    """Event-driven: fetch chain, recompute analytics, check zones, send alerts."""
    try:
        from scripts.chain_parser import compute_analytics_for_symbol
        
        _cache_key = display_key.split(":")[0]
        if _cache_key in STREAM_SYMBOL_MAP:
            api_symbol = f"${_cache_key}"
        else:
            api_symbol = display_key

        result = await compute_analytics_for_symbol(client, api_symbol)
        if result is None:
            return
        analytics, spot = result["analytics"], result["spot"]
        rv, data, iv_rank = result.get("rv", 0.0), result["data"], result.get("iv_rank")

        _ticker_analytics_cache[_cache_key] = {
            "net_gex": analytics.get("net_gex"),
            "atm_iv": analytics.get("atm_iv"),
            "rv": rv,
            "iv_rank": iv_rank,
            "oi_support": analytics.get("oi_support"),
            "oi_resistance": analytics.get("oi_resistance"),
            "volume_support": analytics.get("volume_support"),
            "volume_resistance": analytics.get("volume_resistance"),
        }

        # Push walls and ATM option prices to the ATM service.
        # Use the normalized display key so _find_flow_for_display can
        # match the stored ticker key.
        if atm_svc:
            _pw = analytics.get("put_wall")
            _cw = analytics.get("call_wall")
            atm_svc.set_ticker_walls(display_key, _pw, _cw)
            _exps = sorted(set(e["expiration"] for e in data))
            if _exps:
                atm_svc.set_ticker_expiration(display_key, _exps[0])
                # Second-nearest expiration: a second ATM pair so the trade
                # stream spans both closest expiries.
                if len(_exps) > 1:
                    atm_svc.set_ticker_expiration2(display_key, _exps[1])
            # Call/put marks at the ATM strike (populates Call/Put Price columns)
            _atm_k = analytics.get("atm_strike")
            _call_delta = None
            _put_delta = None
            if _atm_k:
                _atm_exps = sorted({e["expiration"] for e in data if e["strike"] == _atm_k})
                _call_mark = _put_mark = None
                if _atm_exps:
                    _front = _atm_exps[0]
                    for e in data:
                        if e["strike"] == _atm_k and e["expiration"] == _front:
                            if e["type"] == "CALL" and _call_mark is None:
                                _call_mark = e.get("mark")
                                _call_delta = e.get("delta")
                            elif e["type"] == "PUT" and _put_mark is None:
                                _put_mark = e.get("mark")
                                _put_delta = e.get("delta")
                atm_svc.set_ticker_option_prices(display_key, _call_mark, _put_mark)
                # Set delta values for index tickers ($SPX, $RUT, etc.) to use in Net Flow calculation
                if _call_delta is not None or _put_delta is not None:
                    atm_svc.set_ticker_atm_deltas(display_key, _call_delta, _put_delta)
            # Option marks at the key wall strikes: CALL at the put wall
            # (support), PUT at the call wall (resistance), CALL at the
            # call wall (resistance), and PUT at the put wall (support).
            # These populate the grid's Call/Put Price columns.
            atm_svc.set_ticker_wall_prices(
                display_key,
                analytics.get("put_wall_call_price"),
                analytics.get("call_wall_put_price"),
                analytics.get("call_wall_mark"),
                analytics.get("put_wall_mark"),
            )

        _si = compute_strike_increment(data)
        if _si is not None:
            _strike_inc[display_key] = _si

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

        # Resolve the wall zone up-front so the Support-zone strategy scan
        # below can re-use it (matches the zone classifier used at notify time).
        _cw = analytics.get("call_wall")
        _pw = analytics.get("put_wall")
        _wall_zone = None
        if _cw is not None and _cw - _wall_buffer(_cw) <= spot <= _cw + _wall_buffer(_cw):
            _wall_zone = "Resistance"
        elif _pw is not None and _pw - _wall_buffer(_pw) <= spot <= _pw + _wall_buffer(_pw):
            _wall_zone = "Support"

        # Wall-zone-biased strategy alerts.  When spot is sitting at a wall,
        # the directional bias is set by the wall's role and we only surface
        # the matching-direction premium recommendations instead of the full
        # strategy set — this avoids signalling against the dealer bias (e.g.
        # Long Puts / Short Calls at a put-wall support that's likely to
        # bounce).  This is the same ``generate_recommendations`` pipeline
        # used by the Trade Signals tab (signals.py), gated with the default
        # DTE 1-45 (generate_recommendations' default args) and the per-
        # strategy enable flags on ``build_strategy_alerts``.
        if _wall_zone == "Support":
            # Bullish bias (bounce off support) -> Long Calls / Short Puts.
            strat_alerts = build_strategy_alerts(
                data, analytics, spot, rv,
                enable_long_calls=True,
                enable_long_puts=False,
                enable_short_calls=False,
                enable_short_puts=True,
            )
        elif _wall_zone == "Resistance":
            # Bearish bias (rejection at resistance) -> Long Puts / Short Calls.
            strat_alerts = build_strategy_alerts(
                data, analytics, spot, rv,
                enable_long_calls=False,
                enable_long_puts=True,
                enable_short_calls=True,
                enable_short_puts=False,
            )
        else:
            strat_alerts = build_strategy_alerts(data, analytics, spot, rv)
        all_alerts = new_alerts + strat_alerts
        # Diagnostic: trace why strategy recommendation blocks may be empty for
        # a given symbol (equities often lack SSVI/iv_skew enrichment from the
        # ETF fallback path that index symbols get).
        if not strat_alerts:
            logger.info(
                "[%s] empty strat_alerts — iv_skew=%s ssvi_surface=%s atm_iv=%s "
                "near_atm_pool=%d spot=%s wall_zone=%s",
                display_key,
                analytics.get("iv_skew"),
                "yes" if analytics.get("ssvi_surface") is not None else "no",
                analytics.get("atm_iv"),
                len(data),
                spot,
                _wall_zone,
            )
            # Additional debug for strategy build failures
            if analytics.get("ssvi_surface") is None and analytics.get("iv_skew") is None:
                logger.info(
                    "[%s] SSVI surface and iv_skew both missing - strategy signals may be unavailable",
                    display_key
                )
        # Filter out wall-broke and wall-reversal alerts from the periodic
        # poller path — those are surfaced by the streaming
        # ``maybe_fire_wall_zone_alerts`` path with full L2 context instead.
        # "Wall changed" alerts are intentionally passed through.
        tg_alerts = [a for a in all_alerts if not (
            "wall BROKE" in a or
            "wall REVERSAL" in a
        )]

        if tg_alerts and now_ts - last_ts >= _WALL_ZONE_ALERT_COOLDOWN:
            next_sym_state["last_alert_ts"] = now_ts
            await loop.run_in_executor(
                None, partial(
                notify_alerts, tg_alerts,
                symbol=api_symbol, spot=spot,
                gex=analytics.get("net_gex"),
                wall_zone=_wall_zone, pw=_pw, cw=_cw,
                    disable_notification=False,
                ),
            )

        state[api_symbol] = next_sym_state
        try:
            os.makedirs(_BASE_DIR, exist_ok=True)
            tmp = _ALERT_STATE_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f)
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
            api_symbol = f"${_cache_key}"
        else:
            api_symbol = display_key

        result = await _compute_walls_for_symbol(client, api_symbol)
        if result is None:
            return
        analytics, data = result["analytics"], result["data"]

        if atm_svc:
            _pw = analytics.get("put_wall")
            _cw = analytics.get("call_wall")
            atm_svc.set_ticker_walls(display_key, _pw, _cw)
            _exps = sorted(set(e["expiration"] for e in data))
            if _exps:
                atm_svc.set_ticker_expiration(display_key, _exps[0])
                # Second-nearest expiration: a second ATM pair so the trade
                # stream spans both closest expiries.
                if len(_exps) > 1:
                    atm_svc.set_ticker_expiration2(display_key, _exps[1])
            # Call/put marks at the ATM strike (populates Call/Put Price columns)
            _atm_k = analytics.get("atm_strike")
            _call_delta = None
            _put_delta = None
            if _atm_k:
                _atm_exps = sorted({e["expiration"] for e in data if e["strike"] == _atm_k})
                _call_mark = _put_mark = None
                if _atm_exps:
                    _front = _atm_exps[0]
                    for e in data:
                        if e["strike"] == _atm_k and e["expiration"] == _front:
                            if e["type"] == "CALL" and _call_mark is None:
                                _call_mark = e.get("mark")
                                _call_delta = e.get("delta")
                            elif e["type"] == "PUT" and _put_mark is None:
                                _put_mark = e.get("mark")
                                _put_delta = e.get("delta")
                atm_svc.set_ticker_option_prices(display_key, _call_mark, _put_mark)
                # Set delta values for index tickers ($SPX, $RUT, etc.) to use in Net Flow calculation
                if _call_delta is not None or _put_delta is not None:
                    atm_svc.set_ticker_atm_deltas(display_key, _call_delta, _put_delta)
            # Option marks at the key wall strikes (Call/Put Price columns).
            atm_svc.set_ticker_wall_prices(
                display_key,
                analytics.get("put_wall_call_price"),
                analytics.get("call_wall_put_price"),
                analytics.get("call_wall_mark"),
                analytics.get("put_wall_mark"),
            )

        _si = compute_strike_increment(data)
        if _si is not None:
            _strike_inc[display_key] = _si
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


def render_flow_legend_and_style():
    """Inject only the CSS styles needed for the Order Flow grid.

    Called once per outer-fragment tick (every ~10 s) instead of every 2 s
    to prevent HTML-DOM flicker caused by re-injecting the same markup.

    Called from render_tabs_frag() in app.py to ensure styles are injected
    only once per session when the Order Flow tab is active.
    """
    st.markdown("""
    <style>
    div.flow-grid-wrap { width: 100%; overflow-x: auto; }
    table.flow-grid {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 12px;
        font-family: var(--font, "Source Sans Pro", sans-serif);
    }
    table.flow-grid thead th {
        padding: 6px 4px;
        text-align: center;
        vertical-align: bottom;
        white-space: normal;
        overflow-wrap: break-word;
        word-break: break-word;
        line-height: 1.15;
        font-weight: 600;
        color: var(--text-color, #31333f);
        background-color: var(--secondary-background-color, #f0f2f6);
        border-bottom: 1px solid var(--border-color, #e0e2e6);
        cursor: help;
    }
    table.flow-grid thead th[data-tooltip]::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: -35px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s;
        z-index: 1000;
    }
    table.flow-grid thead th[data-tooltip]:hover::after {
        opacity: 1;
    }
    table.flow-grid tbody td {
        padding: 4px 5px;
        color: var(--text-color, #31333f);
        white-space: nowrap;
        border-bottom: 1px solid var(--border-color, #e0e2e6);
    }
    table.flow-grid tbody td:first-child {
        text-align: left !important;
        font-weight: 600;
        white-space: normal;
    }
    table.flow-grid tbody tr:hover td {
        background-color: var(--secondary-background-color, #f7f8fa);
    }
    </style>
    """, unsafe_allow_html=True)


def render_atm_order_flow_grid():
    """Render the ATM Order Flow as an HTML table (mirrors the style of the
    main app's Options Data table): one row per tracked ticker with
    Bullish / Bearish flow, a coloured Status cell, and formatted numbers.

    Used by the Order Flow tab in the main app (wrapped in a refresh fragment).
    The legend and CSS style are rendered separately via
    ``render_flow_legend_and_style`` so they are not re-injected every tick.

    A plain HTML table (via ``st.markdown``) is used instead of
    ``st.dataframe`` because Streamlit's dataframe draws its headers on a
    canvas, which cannot wrap them; ``table-layout: fixed`` + wrapping
    headers keep all columns visible.

    The rendered HTML is cached in session state and only rebuilt when the
    underlying data actually changes.
    """
    s = st.session_state
    atm_svc = s.get("atm_option_service")

    update_flow_cache()

    tickers = s.get("ticker_history", [])
    rows = []
    if tickers:
        for t in tickers:
            t_upper = _normalize_display_symbol(t)
            if atm_svc:
                snap = atm_svc.get_ticker_snapshot(t_upper)
                if not snap:
                    continue
                opt_prices = snap["opt_prices"]
                wall_prices = snap["wall_prices"]
                spot = snap["spot"]
                put_wall_val = snap["put_wall"]
                call_wall_val = snap["call_wall"]
                expiration = atm_svc.get_ticker_expiration(t_upper)
            else:
                opt_prices = wall_prices = {}
                spot = put_wall_val = call_wall_val = expiration = None
            support_cell = (f'<span style="white-space: nowrap">$'
                            f"{put_wall_val:,.2f}</span>"
                            ) if put_wall_val is not None else ""
            resistance_cell = (f'<span style="white-space: nowrap">$'
                               f"{call_wall_val:,.2f}</span>"
                               ) if call_wall_val is not None else ""

            # Grid pricing: Call Price column shows the support price (PUT
            # mark at the put-wall). Put Price column shows the resistance
            # price (CALL mark at the call-wall). Falls back to ATM marks
            # when a wall-level mark is unavailable.
            _call_p = wall_prices.get("put_wall_put_price") or opt_prices.get("put_price")
            _put_p = wall_prices.get("call_wall_call_price") or opt_prices.get("call_price")

            rows.append({
                "Ticker": t_upper,
                "Spot": spot,
                "Expiration": expiration,
                "Support": support_cell,
                "Resistance": resistance_cell,
                "Call Price": _call_p,
                "Put Price": _put_p,
            })
            
            # Add Net Flow and Flow Ratio (from 4 most active expirations)
            if atm_svc:
                net_flow, flow_ratio, rolling_bullish, rolling_bearish, has_institutional = atm_svc.get_ticker_net_flow(t_upper)
            else:
                net_flow, flow_ratio, rolling_bullish, rolling_bearish, has_institutional = 0.0, 0.0, 0.0, 0.0, False
            rows[-1]["Net Flow"] = net_flow
            rows[-1]["Flow Ratio"] = flow_ratio
            rows[-1]["Has Institutional"] = has_institutional
            
            # Add OI Support, OI Resistance, Volume Support, Volume Resistance
            # from the per-ticker analytics cache (each row shows its own
            # ticker's values, not the primary symbol's).
            _ticker_ana = _ticker_analytics_cache.get(t_upper.split(":")[0]) or {}
            rows[-1]["OI Support"] = _ticker_ana.get("oi_support")
            rows[-1]["OI Resistance"] = _ticker_ana.get("oi_resistance")
            rows[-1]["Volume Support"] = _ticker_ana.get("volume_support")
            rows[-1]["Volume Resistance"] = _ticker_ana.get("volume_resistance")

    if not rows:
        st.info("No tickers tracked yet. Add tickers on the main GammaEx page first.")
        return

    # Hash the row data to detect whether anything actually changed.
    # Only meaningful data changes trigger re-render — this prevents flicker
    # caused by the table being re-drawn on every 2-second fragment tick.
    data_key = tuple(
        (r["Ticker"],
         r["Expiration"],
         r["Support"], r["Resistance"],
         r["Call Price"], r["Put Price"],
         r.get("Net Flow"), r.get("Flow Ratio"),
         r.get("OI Support"), r.get("OI Resistance"),
         r.get("Volume Support"), r.get("Volume Resistance"),
         r.get("Has Institutional"))
        for r in rows
    )
    data_hash = hash(data_key)

    cached_hash = s.get("_flow_styled_hash")
    cached_styled = s.get("_flow_styled")
    if data_hash == cached_hash and cached_styled is not None:
        st.markdown(cached_styled, unsafe_allow_html=True)
        return

    # ---- HTML table rendering ------------------------------------------ #
    # Streamlit's dataframe draws its column headers on a canvas, so CSS
    # cannot wrap them to fit all columns.  Render the grid as a plain
    # HTML table instead: `table-layout: fixed` distributes the tab width
    # evenly across the columns and the headers wrap onto multiple lines
    # (see render_flow_legend_and_style for the `.flow-grid` CSS).
    def _fmt_money(v):
        return f"${v:,.2f}" if v is not None else ""

    def _spot_cell_colorer(r):
        spot = r.get("Spot", 0.0)
        support = r.get("Support", None)
        resistance = r.get("Resistance", None)
        
        if spot is None or spot == 0:
            return ""
        
        # Convert support/resistance to float if they are strings
        try:
            support = float(support) if support is not None else None
            resistance = float(resistance) if resistance is not None else None
        except (TypeError, ValueError):
            return ""
        
        # Green when spot is within 2% of support level (support zone)
        if support is not None:
            zone_pct = 0.02
            support_zone_upper = support * (1 + zone_pct)
            if spot >= support and spot <= support_zone_upper:
                return "background-color:#90EE90;"
        
        # Red when spot is within 2% of resistance level (resistance zone)
        if resistance is not None:
            zone_pct = 0.02
            resistance_zone_lower = resistance * (1 - zone_pct)
            if spot >= resistance_zone_lower and spot <= resistance:
                return "background-color:#FFB6C1;"
        
        return ""

    cols = [
        ("Ticker", "left", None, None),
        ("Spot", "right", _fmt_money, _spot_cell_colorer),
        ("Expiration", "center", lambda v: html.escape(format_expiration(v)) if v else "", None),
        ("Support", "right", None, None),
        ("Resistance", "right", None, None),
        ("Put Price", "right", _fmt_money, None),
        ("Call Price", "right", _fmt_money, None),
        ("Net Flow", "right", None, None),
        ("Flow Ratio", "right", lambda v: f"<span style='color:{'green' if v > 0.70 else ('red' if v < 0.30 else 'inherit')}'>{v:.2f}</span>" if v != 0 else "", None),
        ("OI Support", "right", lambda v: f"${v:,.2f}" if v is not None else "", None),
        ("OI Resistance", "right", lambda v: f"${v:,.2f}" if v is not None else "", None),
        ("Volume Support", "right", lambda v: f"${v:,.2f}" if v is not None else "", None),
        ("Volume Resistance", "right", lambda v: f"${v:,.2f}" if v is not None else "", None),
    ]

    thead = ""
    for col in cols:
        name = col[0]
        tooltip = col[5] if len(col) > 5 else None
        tooltip_attr = f' data-tooltip="{html.escape(tooltip)}"' if tooltip else ""
        thead += f"<th{tooltip_attr}>{name}</th>"
    
    tbody = []
    for r in rows:
        cells = []
        for col in cols:
            name = col[0]
            align = col[1]
            fmt = col[2]
            colorer = col[3] if len(col) > 3 else None
            if name == "Net Flow":
                v = r[name]
                has_inst = r.get("Has Institutional", False)
                text = f"<span style='color:{'green' if v > 0 else ('red' if v < 0 else 'inherit')}'>{v:,.0f}{'*' if has_inst else ''}</span>" if v != 0 else ""
            elif fmt:
                text = fmt(r[name])
            else:
                text = str(r[name]) if r[name] is not None else ""
            style = colorer(r) if colorer else ""
            if align == "right":
                style += " text-align:right;"
            elif align == "center":
                style += " text-align:center;"
            cells.append(f'<td style="{style}">{text}</td>')
        tbody.append("<tr>" + "".join(cells) + "</tr>")
    table_html = (
        '<div class="flow-grid-wrap">'
        '<table class="flow-grid">'
        # Explicit column widths: wall columns (Support/Resistance) carry
        # money, so they need a few extra percentage points over an even
        # split across the 12 columns.
        '<colgroup>'
        '<col style="width:7%"><col style="width:6%"><col style="width:7%">'
        '<col style="width:8%"><col style="width:8%">'
        '<col style="width:7%"><col style="width:7%">'
        '<col style="width:7%"><col style="width:7%">'
        '<col style="width:7%"><col style="width:8%">'
        '<col style="width:8%">'
        '</colgroup>'
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(tbody)}</tbody>"
        "</table></div>"
    )

    s._flow_styled_hash = data_hash
    s._flow_styled = table_html
    st.markdown(table_html, unsafe_allow_html=True)


@st.fragment(run_every=2)
def render_flow_frag():
    """Renders the Order Flow grid with fast updates.

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
        if atm_svc.is_feed_stale(max_age_seconds=FLOW_WATCHDOG_STALE_SECONDS):
            logger.warning("[_flow_grid] watchdog: feed stale >60 s, forcing reconnect")
            atm_svc._needs_reconnect = True

    ensure_atm_streaming(mapped)
    st.subheader("Order Flow")
    # Market status indicator at the header row
    render_market_status()
    # CSS styles for the grid (only need to inject once)
    if "_flow_css_injected" not in s:
        render_flow_legend_and_style()
        s["_flow_css_injected"] = True
    render_atm_order_flow_grid()
    # Drive wall-zone Telegram alerts from the *streaming* spot the grid
    # displays, so alerts fire in real time when the grid colors a cell.
    maybe_fire_wall_zone_alerts()
