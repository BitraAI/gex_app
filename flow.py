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
from option_streaming_service import _find_flow_for_display, _normalize_display_symbol
from client import fetch_quotes
from calculations import calculate_atm_strike

# Symbol mapping used by ensure_atm_streaming and render_flow_frag.
_STREAM_SYMBOL_MAP = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}


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
    stream_symbol = _STREAM_SYMBOL_MAP.get(stream_symbol.upper().lstrip("$"), stream_symbol)

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

    if svc and svc.is_connected and atm_svc and _first_exp:
        _all_tickers = s.get("ticker_history", [])
        _current_sym = s.get("symbol", "").upper().lstrip("$")
        if _current_sym and _current_sym not in [t.upper().lstrip("$") for t in _all_tickers]:
            _all_tickers = list(_all_tickers) + [_current_sym]

        _INDEX_QUOTE_MAP = {"SPX": "$SPX:X", "SPXW": "$SPX:X",
                            "RUT": "$RUT:X", "RUTW": "$RUT:X",
                            "NDX": "$NDX:X", "NDXP": "$NDX:X"}

        # Pre-fetch ETF proxy spots via REST only every ~10 s to avoid
        # blocking the Streamlit thread on every 2-second fragment tick.
        # Between fetches we feed whatever is already in spot_cache.
        import time as _time
        _last_fetch_ts = s.get("_spot_fetch_ts", 0.0)
        if _time.time() - _last_fetch_ts >= 10:
            s["_spot_fetch_ts"] = _time.time()
            _stream_symbols = [
                _STREAM_SYMBOL_MAP.get(t.upper().lstrip("$"), t.upper().lstrip("$"))
                for t in _all_tickers
            ]
            try:
                quote_resp = run_async(fetch_quotes(s.client, _stream_symbols))
                for disp_sym, _sym in zip(_all_tickers, _stream_symbols):
                    _disp_upper = disp_sym.upper().lstrip("$")
                    # Skip index symbols — their spot comes from the
                    # index quote, not the ETF proxy quote.
                    if _disp_upper in _INDEX_QUOTE_MAP:
                        continue
                    qd = quote_resp.get(_sym, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(_sym, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is not None and float(last) > 0:
                        s.spot_cache[_disp_upper] = float(last)
            except Exception as e:
                print(f"[ensure_atm_streaming] spot pre-fetch failed: {e}")

        # Index quotes (SPX, RUT, NDX) refreshed every ~2 s (every fragment
        # tick) so the Order Flow grid shows a live spot for index symbols
        # instead of relying only on the 10-second ETF-proxy refresh above.
        _last_idx_fetch_ts = s.get("_idx_spot_fetch_ts", 0.0)
        if _time.time() - _last_idx_fetch_ts >= 2:
            s["_idx_spot_fetch_ts"] = _time.time()
            _index_syms_to_fetch = []
            _index_to_disp = {}
            for _t in _all_tickers:
                _t_upper = _t.upper().lstrip("$")
                if _t_upper in _INDEX_QUOTE_MAP:
                    _iq = _INDEX_QUOTE_MAP[_t_upper]
                    _index_syms_to_fetch.append(_iq)
                    _index_to_disp[_iq] = _t_upper
            if _index_syms_to_fetch:
                try:
                    idx_resp = run_async(fetch_quotes(s.client, _index_syms_to_fetch))
                    for _iq, _disp_upper in _index_to_disp.items():
                        qd = idx_resp.get(_iq, {}) or {}
                        quote = qd.get("quote", {}) or qd.get(_iq, {})
                        last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                        if last is not None and float(last) > 0:
                            s.spot_cache[_disp_upper] = float(last)
                except Exception as e:
                    print(f"[ensure_atm_streaming] index quote fetch failed: {e}")

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
            _t_upper = _t.upper().lstrip("$")
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
                    _stream = _STREAM_SYMBOL_MAP.get(_t_upper, _t_upper)
                    atm_svc._ticker_flows[_t_upper] = {
                        "stream_symbol": _stream,
                        "spot": 0.0,
                        "atm_strike": 0.0,
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
            _t_upper = _t.upper().lstrip("$")
            if _t_upper in s.spot_cache:
                _spot_map[_t_upper] = s.spot_cache[_t_upper]
        if _spot_map:
            atm_svc.bulk_update_spots(_spot_map)

        # Update the walls for the current symbol from the latest analytics
        current_sym = s.get("symbol", "").upper().lstrip("$")
        if current_sym and s.get("analytics"):
            atm_svc = s.get("atm_option_service")
            if atm_svc:
                analytics = s.get("analytics")
                put_wall = analytics.get("put_wall")
                call_wall = analytics.get("call_wall")
                if put_wall is not None or call_wall is not None:
                    if current_sym not in atm_svc.tracked_tickers():
                        stream_sym = _STREAM_SYMBOL_MAP.get(current_sym, current_sym)
                        spot = atm_svc.get_ticker_spot(current_sym) or 0.0
                        if spot > 0:
                            with atm_svc._lock:
                                if current_sym not in atm_svc._ticker_flows:
                                    atm_svc._ticker_flows[current_sym] = {
                                        "stream_symbol": stream_sym,
                                        "spot": spot,
                                        "atm_strike": calculate_atm_strike(spot) if spot > 0 else 0.0,
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


def _refresh_ticker_walls_incrementally():
    """Fetch option-chain data for one tracked ticker per call and update its
    Support (Put Wall) / Resistance (Call Wall) on the ATM service.

    Cycles through all tracked tickers one at a time so the load is spread
    across multiple ``update_flow_cache`` invocations (~2 s apart) instead of
    hammering the API with all tickers at once.

    Handles index symbols (SPX, RUT, NDX) by falling back to their ETF
    proxy (SPY, IWM, QQQ) if the direct option-chain fetch fails, mirroring
    the logic in ``fetch_data`` / ``_run_ticker_signals``.
    """
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    client = s.get("client")
    if not atm_svc or not client:
        return

    # Use raw keys from _ticker_flows to preserve the original symbol
    # format (e.g. "$SPX" vs "SPX") that the Schwab API expects.
    with atm_svc._lock:
        ticker_keys = list(atm_svc._ticker_flows.keys())
    if not ticker_keys:
        return

    # Pick the next ticker to refresh (round-robin)
    idx = s.setdefault("_wall_refresh_idx", 0) % len(ticker_keys)
    t = ticker_keys[idx]
    s["_wall_refresh_idx"] = idx + 1
    t_upper = t.upper().lstrip("$")

    # Skip tickers that already have walls set and are <300 s old
    pw = atm_svc.get_ticker_put_wall(t_upper)
    cw = atm_svc.get_ticker_call_wall(t_upper)
    _last_ts = s.setdefault("_wall_ts_per_ticker", {}).get(t_upper, 0.0)
    if pw is not None and cw is not None and _time_mod.time() - _last_ts < 300:
        return

    try:
        from client import fetch_option_chain, get_interest_rate, get_yield
        from calculations import parse_option_chain, build_greeks_lookup
        from analytics import compute_analytics

        _sym_map = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}
        is_index = t_upper in _sym_map

        r = run_async(get_interest_rate(client))
        q = run_async(get_yield(client, t_upper))

        # Try fetching option chain with the original ticker format.
        # Index symbols may require the $ prefix (e.g. $SPX), so pass the
        # raw tracked value rather than the stripped t_upper.
        raw = None
        try:
            raw = run_async(fetch_option_chain(client, t, strike_count=75, include_quotes=True))
        except Exception:
            if not is_index:
                return

        # Build fallback greeks from the ETF proxy for index symbols
        fallback_greeks = None
        etf_data = None
        etf_spot = 0.0
        if is_index:
            try:
                fb_raw = run_async(fetch_option_chain(client, _sym_map[t_upper], strike_count=75, include_quotes=True))
                fallback_greeks = build_greeks_lookup(fb_raw)
                etf_data, etf_spot = parse_option_chain(fb_raw, r=r, q=q)
            except Exception:
                pass

        if raw is not None:
            data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
        else:
            data, spot = [], 0.0

        # Fall back to ETF data if the index chain gave nothing
        if (not data or spot <= 0) and etf_data and etf_spot > 0:
            data, spot = etf_data, etf_spot

        if not data or spot <= 0:
            return

        # For index symbols that fetched their OWN chain (not ETF fallback),
        # set the correct spot and ATM strike directly on the ticker entry
        # so the grid shows the index level (SPX ~5500) not the ETF proxy
        # (SPY ~500).  Skip triggering _do_subscribe — index symbols would
        # subscribe to non-existent ETF-proxy OCC symbols anyway.
        if is_index and raw is not None:
            _new_atm = calculate_atm_strike(spot)
            with atm_svc._lock:
                _idx_ticker = atm_svc._ticker_flows.get(t)
                if _idx_ticker is not None:
                    old_atm = _idx_ticker.get("atm_strike")
                    _idx_ticker["spot"] = spot
                    _idx_ticker["atm_strike"] = _new_atm
                    if abs((old_atm or 0) - _new_atm) > 0.001:
                        atm_svc._maybe_invalidate_walls_on_strike_change(
                            t, old_atm, _new_atm,
                        )

        analytics = compute_analytics(data, spot, r=r, q=q)

        put_wall = analytics.get("put_wall")
        call_wall = analytics.get("call_wall")
        if put_wall is not None or call_wall is not None:
            atm_svc.set_ticker_walls(t_upper, put_wall, call_wall)
            s.setdefault("_wall_ts_per_ticker", {})[t_upper] = _time_mod.time()

        # Also set Call Price / Put Price from the REST chain so they
        # populate for index symbols (RUT/SPX/NDX) whose streaming proxy
        # bid/ask fallback only works when the ATM service's primary
        # symbol matches their ETF proxy.
        _atm_k = min(
            (e["strike"] for e in data),
            key=lambda k: abs(k - spot),
            default=None,
        )
        _call_mark = None
        _put_mark = None
        if _atm_k is not None:
            _atm_exps = sorted(
                {e["expiration"] for e in data if e["strike"] == _atm_k}
            )
            if _atm_exps:
                _front = _atm_exps[0]
                for e in data:
                    if e["strike"] == _atm_k and e["expiration"] == _front:
                        if e["type"] == "CALL" and _call_mark is None:
                            _call_mark = e.get("mark")
                        elif e["type"] == "PUT" and _put_mark is None:
                            _put_mark = e.get("mark")
        atm_svc.set_ticker_option_prices(t_upper, _call_mark, _put_mark)

        # Update front expiration for this ticker so the grid column
        # shows the correct value rather than a stale fallback to the
        # primary service expiration.
        _expirations = sorted(set(e["expiration"] for e in data))
        if _expirations:
            atm_svc.set_ticker_expiration(t_upper, _expirations[0])
    except Exception:
        pass


def update_flow_cache():
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    if atm_svc is None:
        return
    current_sym = s.get("symbol", "").upper().lstrip("$")

    if getattr(atm_svc, "is_running", False) and current_sym:
        if current_sym in atm_svc.tracked_tickers():
            bf, brf = atm_svc.get_ticker_flow(current_sym)
            if bf is not None and brf is not None:
                s.flow_cache[current_sym] = {"bullish": bf, "bearish": brf}

    tracked = atm_svc.tracked_tickers()
    _spot_map = {}
    _need_fetch = []
    for t_sym in tracked:
        t_upper = t_sym.upper().lstrip("$")
        if t_upper in s.spot_cache:
            _spot_map[t_upper] = s.spot_cache[t_upper]
        else:
            svc_spot = atm_svc.get_ticker_spot(t_upper)
            if svc_spot is not None and svc_spot > 0:
                _spot_map[t_upper] = svc_spot
            else:
                _need_fetch.append(t_upper)
    # Fetch missing spots via REST
    if _need_fetch and s.get("client"):
        try:
            from client import fetch_quotes
            _INDEX_QUOTE_MAP_FETCH = {"SPX": "$SPX:X", "SPXW": "$SPX:X",
                                      "RUT": "$RUT:X", "RUTW": "$RUT:X",
                                      "NDX": "$NDX:X", "NDXP": "$NDX:X"}
            _idx_need = [sym for sym in _need_fetch if sym in _INDEX_QUOTE_MAP_FETCH]
            _eq_need = [sym for sym in _need_fetch if sym not in _INDEX_QUOTE_MAP_FETCH]
            loop = _ensure_async_loop()
            if _eq_need:
                _fetch_syms = _eq_need
                fut = asyncio.run_coroutine_threadsafe(fetch_quotes(s.client, _fetch_syms), loop)
                quote_resp = fut.result()
                for disp_sym in _eq_need:
                    qd = quote_resp.get(disp_sym, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(disp_sym, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is not None and float(last) > 0:
                        _spot_map[disp_sym] = float(last)
                        s.spot_cache[disp_sym] = float(last)
            if _idx_need:
                _idx_fetch_syms = [_INDEX_QUOTE_MAP_FETCH[sym] for sym in _idx_need]
                fut = asyncio.run_coroutine_threadsafe(fetch_quotes(s.client, _idx_fetch_syms), loop)
                idx_resp = fut.result()
                for disp_sym, iq in zip(_idx_need, _idx_fetch_syms):
                    qd = idx_resp.get(iq, {}) or {}
                    quote = qd.get("quote", {}) or qd.get(iq, {})
                    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                    if last is not None and float(last) > 0:
                        _spot_map[disp_sym] = float(last)
                        s.spot_cache[disp_sym] = float(last)
        except Exception:
            pass
    if _spot_map:
        atm_svc.bulk_update_spots(_spot_map)

    for t_sym in tracked:
        bf, brf = atm_svc.get_ticker_flow(t_sym)
        if bf is not None and brf is not None:
            s.flow_cache[t_sym] = {"bullish": bf, "bearish": brf}

    # Incrementally refresh walls for tracked tickers (one per cycle)
    _refresh_ticker_walls_incrementally()


# ---------------------------------------------------------------------------
# Streaming-driven wall-zone alerts
# ---------------------------------------------------------------------------
#
# The standalone ``telegram_alerts.py`` cron job pulls REST option-chain
# spot every ~5 min, which can miss brief wall-zone touches the live ATM
# Order Flow grid displays or only sample the spot when it has already
# exited the zone.  To close that gap we re-evaluate wall zones here every
# fragment tick using the streaming spot stored on the ATM service and
# **re-broadcast** the alert on a per-ticker cooldown while spot remains
# in the zone — so the user keeps getting notified the entire time spot
# sits at a wall, not only at the moment of entry.

_WALL_ZONE_BUFFER = 0.0002  # 0.02 % — must match grid coloring in flow.py
_WALL_ZONE_ALERT_COOLDOWN = 300.0  # min seconds between consecutive zone alerts per ticker

def _compute_wall_zone(spot: float | None, put_wall: float | None,
                       call_wall: float | None) -> str | None:
    if spot is None or spot <= 0:
        return None
    if put_wall is not None and spot <= put_wall + abs(put_wall) * _WALL_ZONE_BUFFER:
        return "support"
    if call_wall is not None and spot >= call_wall - abs(call_wall) * _WALL_ZONE_BUFFER:
        return "resistance"
    return None


def maybe_fire_wall_zone_alerts() -> None:
    """Inspect every tracked ticker's streaming spot vs its walls and push
    a Telegram alert while spot *sits* in a wall zone (support or
    resistance).

    Runs on every ATM Order Flow fragment tick (~2 s).  Fires on the first
    tick a ticker enters a zone and then re-fires every
    ``_WALL_ZONE_ALERT_COOLDOWN`` seconds while the ticker remains in the
    zone so a fast-moving tape that briefly exits and re-enters does not
    reset the cooldown prematurely.  When spot leaves the zone the stored
    cooldown is reset so the next entry fires immediately.  Safe to call
    when Telegram is disabled; ``notify_alerts`` is a no-op then.
    """
    s = st.session_state
    atm_svc = s.get("atm_option_service")
    if atm_svc is None:
        return
    if not is_market_open():
        return
    now = _time_mod.monotonic()
    state = s.setdefault("atm_alert_state", {})
    for t in atm_svc.tracked_tickers():
        t_upper = t.upper().lstrip("$")
        spot = atm_svc.get_ticker_spot(t_upper)
        put_wall = atm_svc.get_ticker_put_wall(t_upper)
        call_wall = atm_svc.get_ticker_call_wall(t_upper)
        cur_zone = _compute_wall_zone(spot, put_wall, call_wall)

        prev = state.get(t_upper, {})
        prev_zone = prev.get("wall_zone")
        last_alert_ts = prev.get("last_alert_ts", 0.0)

        # Spot left the zone → reset the cooldown so the next entry fires
        # immediately rather than being suppressed by the prior cooldown.
        if cur_zone is None:
            state[t_upper] = {"wall_zone": None, "last_alert_ts": 0.0}
            continue

        # While still in the zone, throttle re-broadcasts to the cooldown.
        # On the first entry ``prev_zone != cur_zone`` forces the immediate
        # fire below, regardless of last_alert_ts.
        fire = (prev_zone != cur_zone) or (now - last_alert_ts >= _WALL_ZONE_ALERT_COOLDOWN)
        state[t_upper] = {"wall_zone": cur_zone, "last_alert_ts": last_alert_ts}
        if not fire:
            continue

        if cur_zone == "support" and put_wall is not None:
            label = "support"
            wall = put_wall
        elif cur_zone == "resistance" and call_wall is not None:
            label = "resistance"
            wall = call_wall
        else:
            continue
        already = prev_zone == label
        msg = (
            f"Price approaching {'Put' if label == 'support' else 'Call'} Wall (${wall:.2f})"
            + ("" if not already else " (still in zone)")
        )

        state[t_upper]["last_alert_ts"] = now
        from telegram_notifier import notify_alerts
        notify_alerts([msg], symbol=t_upper, spot=spot, disable_notification=False)


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
    current_sym = s.get("symbol", "").upper().lstrip("$")
    atm_svc = s.get("atm_option_service")

    update_flow_cache()

    tickers = s.get("ticker_history", [])
    if not tickers:
        tickers = [current_sym] if current_sym else []

    tracked = set(atm_svc.tracked_tickers()) if atm_svc else set()

    rows = []
    for t in tickers:
        t_upper = t.upper().lstrip("$")
        cached = s.flow_cache.get(t_upper)
        bullish = cached.get("bullish") if cached is not None else None
        bearish = cached.get("bearish") if cached is not None else None
        has_data = bullish is not None and bearish is not None
        is_tracked = (t_upper == current_sym) or (t_upper in tracked)
        net = (bullish - bearish) / (bullish + bearish) if has_data and (bullish + bearish) != 0 else 0 if has_data else None
        opt_prices = atm_svc.get_ticker_option_prices(t_upper) if atm_svc else {}
        atm_strike = atm_svc.get_ticker_atm_strike(t_upper) if atm_svc else None
        spot = atm_svc.get_ticker_spot(t_upper) if atm_svc else None
        trend = atm_svc.get_ticker_trend(t_upper) if atm_svc else "flat"
        
        # Get book imbalance and trend reversal from ticker data
        book_imbalance = None
        trend_reversal = None
        if atm_svc:
            ticker_data = _find_flow_for_display(atm_svc._ticker_flows, t_upper)
            if ticker_data:
                book_imbalance = ticker_data.get("book_imbalance")
                trend_reversal = ticker_data.get("trend_reversal")
        
        # Format Trend column - enhanced with liquidity pressure indicators
        # Keep visual indicators without emojis
        if book_imbalance is not None:
            if book_imbalance > 0.3:
                # Strong bullish pressure
                if trend_reversal == "bullish":
                    trend_display = "↑↑"  # Double bullish
                elif trend == "up":
                    trend_display = "↑"   # Normal bullish
                else:
                    trend_display = "→→" # Building bullish momentum
            elif book_imbalance < -0.3:
                # Strong bearish pressure
                if trend_reversal == "bearish":
                    trend_display = "↓↓"  # Double bearish
                elif trend == "down":
                    trend_display = "↓"   # Normal bearish
                else:
                    trend_display = "←←" # Building bearish momentum
            else:
                # Normal pressure
                trend_display = {"up": "↑", "down": "↓", "flat": "→"}.get(trend, "→")
        else:
            # Standard trend display
            if trend_reversal == "bullish":
                trend_display = "↑"
            elif trend_reversal == "bearish":
                trend_display = "↓"
            else:
                trend_display = {"up": "↑", "down": "↓", "flat": "→"}.get(trend, "→")
        
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

        rows.append({
            "Ticker": t_upper,
            "Spot": spot,
            "ATM Strike": atm_strike,
            "Expiration": atm_svc.get_ticker_expiration(t_upper) if atm_svc else None,
            "Support": put_wall_val,
            "Resistance": call_wall_val,
            "Call Price": opt_prices.get("call_price"),
            "Put Price": opt_prices.get("put_price"),
            "Bullish Flow": bullish if has_data else 0,
            "Bearish Flow": bearish if has_data else 0,
            "Flow Momentum": net if has_data else 0,
            "Trend": trend_display,
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
         r["Call Price"], r["Put Price"], r["Bullish Flow"],
         r["Bearish Flow"], r["Flow Momentum"])
        for r in rows
    )
    data_hash = hash((data_key, _atm_epoch, _wall_epoch))

    cached_hash = s.get("_flow_styled_hash")
    cached_styled = s.get("_flow_styled")
    if data_hash == cached_hash and cached_styled is not None:
        st.dataframe(cached_styled, height=700, width="stretch")
        return

    df = pd.DataFrame(rows)

    def _net_flow_color(val):
        if val > 0.20:
            return "color: #00cc96; font-weight: bold;"
        if val < -0.20:
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _trend_color(val):
        """Color the trend text (up/down/flat) based on trend direction."""
        return {
            "up": "color: #00cc96; font-weight: bold;",
            "down": "color: #ef5350; font-weight: bold;",
        }.get(val, "color: #808080;")

    def _spot_wall_bg(row):
        spot = row["Spot"]
        support = row["Support"]
        resistance = row["Resistance"]
        styles = [""] * len(row)
        col_idx = list(row.index)
        spot_i = col_idx.index("Spot")
        _BUFFER = 0.0002  # 0.02 %
        if spot is not None and support is not None:
            pw_buf = abs(support) * _BUFFER
            if spot <= support + pw_buf:
                styles[spot_i] = "background-color: #ccffcc"
        if spot is not None and resistance is not None:
            cw_buf = abs(resistance) * _BUFFER
            if spot >= resistance - cw_buf:
                styles[spot_i] = "background-color: #ffcccc"
        return styles

    _styler = df.style.set_uuid("flow_grid")
    _styler = _styler.apply(_spot_wall_bg, axis=1)
    if hasattr(_styler, "map"):
        _styler = _styler.map(_net_flow_color, subset=["Flow Momentum"])
        _styler = _styler.map(_trend_color, subset=["Trend"])
    else:
        _styler = _styler.apply(_net_flow_color, subset=["Flow Momentum"])
        _styler = _styler.apply(_trend_color, subset=["Trend"])

    styled = _styler.format({
        "Spot": lambda v: f"${v:,.2f}" if v is not None else "",
        "ATM Strike": lambda v: f"${v:,.2f}" if v is not None else "",
        "Expiration": lambda v: _format_expiration(v),
        "Support": lambda v: f"${v:,.2f}" if v is not None else "",
        "Resistance": lambda v: f"${v:,.2f}" if v is not None else "",
        "Trend": lambda v: v,
        "Call Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Put Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Bullish Flow": "{:,.0f}",
        "Bearish Flow": "{:,.0f}",
        "Flow Momentum": "{:+.2f}",
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
    mapped = _STREAM_SYMBOL_MAP.get(stream_symbol, stream_symbol)

    # Watchdog: detect a silently dead option feed.  If the market is
    # open and no ticks have arrived for 60 s, force re-registration
    # so the next ensure_atm_streaming cycle re-subscribes everything.
    atm_svc = s.get("atm_option_service")
    if atm_svc and is_market_open() and atm_svc.is_running:
        if atm_svc.is_feed_stale(max_age_seconds=60):
            print("[_flow_grid] watchdog: feed stale >60 s, forcing reconnect")
            atm_svc._needs_reconnect = True

    ensure_atm_streaming(mapped)
    st.subheader("ATM Order Flow")
    # Market status indicator at the header row
    render_market_status()
    # CSS styles for the dataframe (only need to inject once)
    if "_flow_css_injected" not in s:
        render_flow_legend_and_style()
        s["_flow_css_injected"] = True
    render_atm_order_flow_grid()
    # Drive wall-zone Telegram alerts from the *streaming* spot the grid
    # displays, so alerts fire in real time when the grid colors a cell
    # even if the standalone cron job's REST fetch hasn't sampled again.
    maybe_fire_wall_zone_alerts()
