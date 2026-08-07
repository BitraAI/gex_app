"""Shared ATM order-flow rendering used by both the main app page and
the dedicated Order Flow tab.

Kept free of any st.set_page_config / global app setup so it can be imported
safely from either entry point without re-running app.py's top-level code.
"""

import asyncio
import html
import time as _time_mod
import streamlit as st
from datetime import date, datetime
from zoneinfo import ZoneInfo
from _constants import STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP
from option_streaming_service import _find_flow_for_display, _normalize_display_symbol, _get_stream_symbol, _ABSORPTION_MIN_VOL
from client import fetch_quotes
from calculations import calculate_atm_strike
import json
import logging
import os
from functools import partial

from analytics import compute_analytics
from calculations import build_greeks_lookup, parse_option_chain
from client import (
    compute_iv_rank,
    fetch_option_chain,
    get_20d_rv,
    get_interest_rate,
    get_yield,
)
from signals import build_strategy_alerts
from telegram_notifier import diff_alerts, notify_alerts


# Per-ticker analytics cache + event-driven trigger tracking
_ticker_analytics_cache: dict[str, dict] = {}
_last_ref_price: dict[str, float] = {}   # last reference price for trigger
_last_recompute_ts: dict[str, float] = {}  # last wall recompute time (monotonic)
_last_full_recompute_ts: dict[str, float] = {}  # last full recompute time (monotonic)
_strike_inc: dict[str, float] = {}       # known strike increment per ticker
logger = logging.getLogger(__name__)

_FETCH_RETRIES = 3

# Trend cell de-bounce: the displayed direction must persist for this many
# consecutive samples before the Trend cell flips, so noisy streaming
# thresholds (book imbalance / flow speed) can't make the column flicker.
# "flat" (neutral) is shown immediately so a quiet book never sits on stale
# up/down text.
_TREND_CONFIRM_SAMPLES = 3

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


async def _fetch_chain_with_retry(client, symbol: str) -> dict | None:
    """Fetch an option chain with _FETCH_RETRIES attempts / 1 s backoff.
    Returns ``None`` when every attempt fails."""
    raw = None
    for attempt in range(_FETCH_RETRIES):
        try:
            raw = await fetch_option_chain(
                client, symbol, strike_count=75, include_quotes=True,
            )
            break
        except Exception:
            if attempt < _FETCH_RETRIES - 1:
                await asyncio.sleep(1.0)
    if raw is None:
        logger.warning(
            "fetch_option_chain failed for %s after %d retries",
            symbol, _FETCH_RETRIES,
        )
    return raw


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
                print(f"[ensure_atm_streaming] spot pre-fetch failed: {e}")

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
                    print(f"[ensure_atm_streaming] option quote refresh failed: {e}")

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

# Number of consecutive samples spot must stay *past* a broken wall (beyond
# the near-wall margin) before a "wall broke" alert fires.  Confirmation stops
# jitter right at the level from being misreported as a break.
_WALL_BREAK_CONFIRM = 2

# Minimum contracts absorbed for a meaningful wall break (avoids noise from
# insignificant breaks with negligible flow).
_MIN_WALL_BREAK_CONTRACTS = 100

# Conviction gate for Telegram trend alerts: only reversals (bullish/bearish)
# are surfaced as alerts now; the plain up/down direction no longer fires a
# Telegram alert. Reversals need _ALERT_MIN_CONVICTION_REVERSAL metric
# agreements (0-5) before they send.
_ALERT_MIN_CONVICTION_REVERSAL = 2


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
    _dist_cw = abs(spot - call_wall) if call_wall is not None else float("inf")
    _dist_pw = abs(spot - put_wall) if put_wall is not None else float("inf")
    if _dist_cw <= _dist_pw:
        _call_p = wall_prices.get("call_wall_call_price") or opt_prices.get("call_price")
        _put_p = wall_prices.get("call_wall_put_price") or opt_prices.get("put_price")
    else:
        _call_p = wall_prices.get("put_wall_call_price") or opt_prices.get("call_price")
        _put_p = wall_prices.get("put_wall_put_price") or opt_prices.get("put_price")
    return _call_p, _put_p


def _opt_mark_at_wall(
    buy_side: str,
    wall_strike: float | None,
    call_wall: float | None,
    put_wall: float | None,
    wall_prices: dict,
) -> float | None:
    """Return the CALL/PUT option mark at a specific wall strike."""
    if buy_side == "CALL":
        return (
            wall_prices.get("call_wall_call_price")
            if wall_strike == call_wall
            else wall_prices.get("put_wall_call_price")
        )
    return (
        wall_prices.get("call_wall_put_price")
        if wall_strike == call_wall
        else wall_prices.get("put_wall_put_price")
    )


def _front_exp_tag(front_exp: str | None) -> str:
    """Format a 'YYYY-MM-DD' expiration as a ' mm/dd' suffix ('' if missing)."""
    if front_exp and len(front_exp) >= 10 and front_exp[4] == "-":
        return f" {front_exp[5:7]}/{front_exp[8:10]}"
    return ""


def _trade_line(
    buy_side: str,
    wall_strike: float | None,
    call_wall: float | None,
    put_wall: float | None,
    wall_prices: dict,
    front_exp: str | None,
) -> str:
    """Build a '🟢 BUY CALL @ $strike dd/mm $price' trade-suggestion line used
    by both the wall-broke and wall-reversal alerts."""
    _trade_emoji = "🟢" if buy_side == "CALL" else "🔴"
    _strike_tag = f" @ ${wall_strike:,.2f}" if wall_strike is not None else ""
    _opt_price = _opt_mark_at_wall(buy_side, wall_strike, call_wall, put_wall, wall_prices)
    _price_tag = f" ${_opt_price:,.2f}" if _opt_price is not None else ""
    return f"{_trade_emoji} BUY {buy_side}{_strike_tag}{_front_exp_tag(front_exp)}{_price_tag}"


def _conviction_score(
    direction: str | None,
    book_imbalance: float | None,
    flow_speed: float | None,
    flow_acceleration: float | None,
    liquidity_flow: float | None,
    net_flow_60: float | None,
    absorption: float | None,
) -> int:
    """0-5 confidence that a trend signal is real, from metric agreement.

    Each agreeing metric adds one point against the expected direction:
    |book_imbalance| > 0.3, flow_speed and flow_acceleration sharing a sign,
    liquidity_flow refilling the book (up) or draining it (down), a 60s net
    flow matching the direction, and heavy absorption.  Weak/absent metrics
    simply contribute nothing, so the score is a lower bound on agreement.
    """
    _up = direction in ("up", "bullish")
    if direction is None:
        return 0
    score = 0
    if book_imbalance is not None and abs(book_imbalance) > 0.3:
        score += 1
    if flow_speed is not None and flow_acceleration is not None:
        if (flow_speed > 0) == (flow_acceleration > 0) and flow_speed != 0:
            score += 1
    if liquidity_flow is not None:
        if (_up and liquidity_flow > 0) or (not _up and liquidity_flow < 0):
            score += 1
    if net_flow_60 is not None:
        if (_up and net_flow_60 > 0) or (not _up and net_flow_60 < 0):
            score += 1
    if absorption is not None and absorption >= _ABSORPTION_MIN_VOL:
        score += 1
    return score


def _tracked_book_contracts(atm_svc, tickers):
    """Build {stream_symbol: [ATM call OCC, ATM put OCC]} for the given
    tickers from the ATM option service.

    OPTIONS_BOOK subscriptions require full OCC option-contract symbols, not
    underlyings, so this mapping (not the underlying) is what
    ``StreamingService.set_book_contracts`` subscribes for the Level 2 book
    imbalance feed.
    """
    contracts = {}
    if atm_svc is None:
        return contracts
    for t in tickers:
        t_upper = _normalize_display_symbol(t)
        occ = [c for c in (
            atm_svc.get_ticker_call_sym(t_upper),
            atm_svc.get_ticker_put_sym(t_upper),
        ) if c]
        if occ:
            contracts[_get_stream_symbol(t_upper)] = occ
    return contracts


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

    # Ensure Level 2 books are subscribed for every tracked ticker so the
    # L2-sourced trend below is populated (idempotent; diffs each call).
    _svc = s.get("streaming_service")
    if _svc is not None:
        _tickers = atm_svc.tracked_tickers()
        _svc.subscribe_book_symbols([_get_stream_symbol(t) for t in _tickers])
        # OPTIONS_BOOK needs the ATM OCC contract symbols, not underlyings.
        _svc.set_book_contracts(_tracked_book_contracts(atm_svc, _tickers))

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
        _raw_t = t_upper
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

        analytics = {
            "gamma_flip": None,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "dealer_position": None,
            "atm_strike": atm_svc.get_ticker_atm_strike(t_upper),
            "call_wall_mark": call_wall,
            "put_wall_mark": put_wall,
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
        _ssvc = s.get("streaming_service")
        ticker_data = _ssvc.get_ticker_trend_data(t_upper) if _ssvc else {}
        new_alerts, next_state = diff_alerts(prev, analytics, spot)
        wall_zone = None
        if call_wall is not None and call_wall - _wall_buffer(call_wall) <= spot <= call_wall + _wall_buffer(call_wall):
            wall_zone = "Resistance"
        elif put_wall is not None and put_wall + _wall_buffer(put_wall) >= spot >= put_wall - _wall_buffer(put_wall):
            wall_zone = "Support"
        # Trend signal sourced directly from StreamingService.trend_data: only
        # a reversal (bullish/bearish) is surfaced as an alert now — the plain
        # up/down direction no longer triggers a Telegram alert. flat is not
        # surfaced as an alert. This replaces the previous wall-zone buy/sell
        # classifier.
        _trend_reversal = ticker_data.get("trend_reversal")
        _trend_signal = (
            _trend_reversal if _trend_reversal in ("bullish", "bearish") else None
        )

        # Conviction gate: a reversal must be corroborated by enough metrics
        # before it becomes an alert, so weak/flat-ish trends stay quiet.
        # Wall-broke alerts bypass the gate entirely.
        if _trend_signal is not None:
            _net_60 = atm_svc.get_ticker_executed_net60(t_upper)[2]
            _absorption_now = atm_svc.get_ticker_absorption(t_upper)
            _conviction = _conviction_score(
                _trend_signal,
                ticker_data.get("book_imbalance"),
                ticker_data.get("flow_speed"),
                ticker_data.get("flow_acceleration"),
                ticker_data.get("liquidity_flow"),
                _net_60,
                _absorption_now,
            )
            _fire_trend = _conviction >= _ALERT_MIN_CONVICTION_REVERSAL
        else:
            _net_60 = None
            _absorption_now = None
            _conviction = 0
            _fire_trend = False

        # ---- Wall zone entry bookkeeping (for reversal absorption) ------ #
        # Snapshot cumulative ATM volume when spot enters a wall zone; while
        # inside, ``_absorbed_at_wall`` is the flow consumed since entry.  This
        # is reported on reversal/break headers as context only — it no longer
        # *drives* the break trigger (see below), because raw cumulative volume
        # inflates with quiet time spent in the zone and produced wrong signals.
        _flow_b, _flow_br = atm_svc.get_ticker_flow(t_upper)
        _flow_vol = (_flow_b or 0) + (_flow_br or 0) if _flow_b is not None else None
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
        # Wall-broke / reversal alerts are high-confidence (directional pierce
        # confirmed or reversal with conviction), so they fire regardless of
        # wall stability.  Only plain trend alerts are gated behind
        # _wall_stable >= 2 to filter jittery moving walls.
        _break_alert = bool(new_alerts)
        if _break_alert:
            _send_gate = now - last_ts >= _WALL_ZONE_ALERT_COOLDOWN
        else:
            _send_gate = _fire_trend and _wall_stable >= 2 and now - last_ts >= _WALL_ZONE_ALERT_COOLDOWN
        if _send_gate:
            next_state["last_alert_ts"] = now
            next_state["_last_alert_texts"] = new_alerts
            state[t_upper] = next_state
            _cache = _ticker_analytics_cache.get(t_upper.split(":")[0]) or {}
            _rv = _cache.get("rv", 0.0)
            notify_alerts(new_alerts or [""], symbol=t_upper, spot=spot,
                          gex=_cache.get("net_gex"), rv=_rv if _rv > 0 else None,
                          iv_rank=_cache.get("iv_rank"),
                          wall_zone=wall_zone, pw=put_wall, cw=call_wall,
                          wall_mark=analytics.get("call_wall_mark") if wall_zone == "Resistance" else analytics.get("put_wall_mark"),
                          trend_alert=_trend_signal,
                          absorption=_absorption_now,
                          absorbed_at_wall=_absorbed_at_wall,
                          net_flow=_net_60,
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
    raw = await _fetch_chain_with_retry(client, symbol)
    if raw is None:
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
    raw = await _fetch_chain_with_retry(client, symbol)
    if raw is None:
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
        iv_rank = await compute_iv_rank(client, symbol)
    except Exception as exc:
        logger.warning("failed to compute IV rank for %s: %s", symbol, exc)

    analytics["iv_rank"] = iv_rank
    return {"analytics": analytics, "spot": spot, "rv": rv, "data": data, "iv_rank": iv_rank}


def _atm_deltas_for_symbol(data: list, atm_strike: float | None):
    """Return the front-month ATM Call delta (>0) and Put delta (<0) from a
    chain ``data`` list, or (None, None) if unavailable."""
    if not data or not atm_strike:
        return None, None
    atm_exps = sorted({
        e["expiration"] for e in data if abs(e["strike"] - atm_strike) < 1e-9
    })
    if not atm_exps:
        return None, None
    front = atm_exps[0]
    call_delta = put_delta = None
    for e in data:
        if abs(e["strike"] - atm_strike) < 1e-9 and e["expiration"] == front:
            if e["type"] == "CALL" and call_delta is None:
                call_delta = e.get("delta")
            elif e["type"] == "PUT" and put_delta is None:
                put_delta = e.get("delta")
    return call_delta, put_delta


async def _recompute_symbol(display_key: str, client, loop, atm_svc=None) -> None:
    """Event-driven: fetch chain, recompute analytics, check zones, send alerts."""
    try:
        _cache_key = display_key.split(":")[0]
        if _cache_key in STREAM_SYMBOL_MAP:
            api_symbol = f"${_cache_key}"
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
        # Use the normalized display key so _find_flow_for_display can
        # match the stored ticker key.
        if atm_svc:
            _pw = analytics.get("put_wall")
            _cw = analytics.get("call_wall")
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
            # Front ATM Call/Put deltas (weight trades -> Net Flow column).
            _atm_d = _atm_deltas_for_symbol(data, _atm_k)
            atm_svc.set_ticker_atm_deltas(display_key, _atm_d[0], _atm_d[1])
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
        # Filter out "Wall changed" and all wall-broke/absorbed alerts permanently
        # — only wall-reversal and strategy recommendation alerts are sent to Telegram.
        tg_alerts = [a for a in all_alerts if not (
            "Wall changed" in a or
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
                iv_rank=iv_rank, wall_zone=_wall_zone, pw=_pw, cw=_cw,
                    disable_notification=False,
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
            # Front ATM Call/Put deltas (weight trades -> Net Flow column).
            _atm_d2 = _atm_deltas_for_symbol(data, _atm_k)
            atm_svc.set_ticker_atm_deltas(display_key, _atm_d2[0], _atm_d2[1])
            # Option marks at the key wall strikes (Call/Put Price columns).
            atm_svc.set_ticker_wall_prices(
                display_key,
                analytics.get("put_wall_call_price"),
                analytics.get("call_wall_put_price"),
                analytics.get("call_wall_mark"),
                analytics.get("put_wall_mark"),
            )

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
    headers keep all 14 columns visible.

    The rendered HTML is cached in session state and only rebuilt when the
    underlying data actually changes.
    """
    s = st.session_state
    current_sym = _normalize_display_symbol(s.get("symbol", ""))
    atm_svc = s.get("atm_option_service")

    update_flow_cache()

    tickers = s.get("ticker_history", [])
    _svc = s.get("streaming_service")
    if _svc is not None:
        _svc.subscribe_book_symbols([_get_stream_symbol(t) for t in tickers])
        # OPTIONS_BOOK needs the ATM OCC contract symbols, not underlyings.
        _svc.set_book_contracts(_tracked_book_contracts(atm_svc, tickers))
    rows = []
    if tickers:
        for t in tickers:
            t_upper = _normalize_display_symbol(t)
            opt_prices = atm_svc.get_ticker_option_prices(t_upper) if atm_svc else {}
            wall_prices = atm_svc.get_ticker_wall_prices(t_upper) if atm_svc else {}
            spot = atm_svc.get_ticker_spot(t_upper) if atm_svc else None
            # Get book imbalance and trend from ticker data (L2-sourced via
            # StreamingService.trend_data: trend is up/down/flat, reversal is
            # Support (Put Wall) / Resistance (Call Wall): prefer preserved ticker
            # walls from ATM option service, which retain last valid values.
            put_wall_val = atm_svc.get_ticker_put_wall(t_upper) if atm_svc else None
            call_wall_val = atm_svc.get_ticker_call_wall(t_upper) if atm_svc else None

            _net_60 = (
                atm_svc.get_ticker_executed_net60(t_upper)[2] if atm_svc else None
            )
            _call_p, _put_p = _wall_price_marks(opt_prices, wall_prices, call_wall_val, put_wall_val, spot)
            
            # Trend from streaming (bullish/bearish reversal or bare direction)
            if _svc is not None:
                ticker_data = _svc.get_ticker_trend_data(t_upper)
                book_imbalance = ticker_data.get("book_imbalance")
                flow_speed = ticker_data.get("flow_speed", 0)
                flow_acceleration = ticker_data.get("flow_acceleration", 0)
                # Reversal (bullish/bearish) takes precedence over the bare
                # direction so the Trend column surfaces the flip the moment
                # it is detected; otherwise show the current direction.
                _candidate = ticker_data.get("trend_reversal") or ticker_data.get("trend") or "flat"
            else:
                ticker_data = {}
                book_imbalance = None
                flow_speed = 0
                flow_acceleration = 0
                _candidate = "flat"

            # De-bounce / stickiness: the raw streaming direction oscillates
            # around its thresholds, so a naive pass-through flickers.  Treat
            # up/down as needing confirmation over several consecutive samples
            # before the cell flips, and reset the streak on any change so the
            # old display persists instead of flapping.
            #
            # Genuine reversals (bullish/bearish) are meaningful, rare flips and
            # surface immediately (not debounced); "flat" (neutral) also applies
            # right away so a quiet book never sits on stale up/down.
            _trend_state = s.setdefault("_flow_trend_state", {})
            if _candidate in ("bullish", "bearish"):
                trend_display = _candidate
                _trend_state[t_upper] = {"candidate": _candidate, "streak": 0, "display": _candidate}
            elif _candidate == "flat" or not _candidate:
                trend_display = "flat"
                _trend_state[t_upper] = {"candidate": _candidate or "flat", "streak": 0, "display": "flat"}
            else:
                _prev = _trend_state.get(t_upper)
                if _prev is None or _prev.get("candidate") != _candidate or _prev.get("streak", 0) == 0:
                    _streak = 1
                    _display = "flat"
                else:
                    _streak = _prev.get("streak", 0) + 1
                    _display = _prev.get("display", "flat")
                if _streak >= _TREND_CONFIRM_SAMPLES:
                    _display = _candidate
                _trend_state[t_upper] = {"candidate": _candidate, "streak": _streak, "display": _display}
                trend_display = _display

            rows.append({
                "Ticker": t_upper,
                "Spot": spot,
                "Expiration": atm_svc.get_ticker_expiration(t_upper) if atm_svc else None,
                "Support": put_wall_val,
                "Resistance": call_wall_val,
                "Call Price": _call_p,
                "Put Price": _put_p,
                "Trend": trend_display,
                "Book Imbalance": book_imbalance,
                "Flow Speed": flow_speed,
                "Flow Acceleration": flow_acceleration,
                "Net Flow": _net_60,
                "Liquidity Flow": ticker_data.get("liquidity_flow") if _svc is not None else None,
                "Absorption": atm_svc.get_ticker_absorption(t_upper) if atm_svc else None,
            })

    if not rows:
        st.info("No tickers tracked yet. Add tickers on the main GammaEx page first.")
        return

    # Hash the row data to detect whether anything actually changed.
    # Include a 10 s epoch so the Spot column is re-rendered every
    # 10 s even when the cached value is unchanged, keeping the display
    # visibly "alive" for users who watch the grid.
    # Include a 60 s epoch so the Support / Resistance wall columns are
    # re-rendered every 60 s even when their stored values are unchanged.
    _atm_epoch = int(_time_mod.time() // 10)
    _wall_epoch = int(_time_mod.time() // 60)
    data_key = tuple(
        (r["Ticker"], r["Spot"], r["Expiration"],
         r["Support"], r["Resistance"], r["Trend"],
          r["Call Price"], r["Put Price"], r["Book Imbalance"], r["Flow Speed"], r["Flow Acceleration"], r["Net Flow"], r["Liquidity Flow"], r["Absorption"])
        for r in rows
    )
    data_hash = hash((data_key, _atm_epoch, _wall_epoch))

    cached_hash = s.get("_flow_styled_hash")
    cached_styled = s.get("_flow_styled")
    if data_hash == cached_hash and cached_styled is not None:
        st.markdown(cached_styled, unsafe_allow_html=True)
        return

    # ---- HTML table rendering ------------------------------------------ #
    # Streamlit's dataframe draws its column headers on a canvas, so CSS
    # cannot wrap them to fit all 14 columns.  Render the grid as a plain
    # HTML table instead: `table-layout: fixed` distributes the tab width
    # evenly across the columns and the headers wrap onto multiple lines
    # (see render_flow_legend_and_style for the `.flow-grid` CSS).
    def _trend_color(row):
        """Color the Trend label (up/down/bullish/bearish) by direction.

        Reversal labels (bullish/bearish) are bolded to surface the flip;
        up/down are green/red; flat is amber.

        When spot leaves the support zone (upwards), trend shows UP in GREEN.
        Within support zone, trend shows BULLISH.
        When spot leaves the resistance zone (downwards), trend shows DOWN in RED.
        Within resistance zone, trend shows BEARISH.
        """
        val = row["Trend"]
        spot = row["Spot"]
        support = row["Support"]
        resistance = row["Resistance"]
        
        if val is None:
            return ""
        
        # When spot leaves support zone (moves away from support wall), show UP in GREEN
        # This indicates bullish sentiment as spot moves away from support
        if spot is not None and support is not None:
            if spot > support + _wall_buffer(support):  # Spot has left support zone upwards
                return "color: #00cc96; font-weight: bold;"
        
        # Within support zone, show BULLISH
        if spot is not None and support is not None:
            if support - _wall_buffer(support) <= spot <= support + _wall_buffer(support):
                return "color: #00cc96; font-weight: bold;"
        
        # When spot leaves resistance zone (moves away from resistance wall), show DOWN in RED
        # This indicates bearish sentiment as spot moves away from resistance
        if spot is not None and resistance is not None:
            if spot < resistance - _wall_buffer(resistance):  # Spot has left resistance zone downwards
                return "color: #ef5350; font-weight: bold;"
        
        # Within resistance zone, show BEARISH
        if spot is not None and resistance is not None:
            if resistance - _wall_buffer(resistance) <= spot <= resistance + _wall_buffer(resistance):
                return "color: #ef5350; font-weight: bold;"
        
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
        """Background color for the Spot cell based on wall break/reversal alerts and zone membership."""
        s = st.session_state
        spot = row["Spot"]
        support = row["Support"]
        resistance = row["Resistance"]
        
        # GREEN if spot is in support zone (between support - buffer and support + buffer)
        if support is not None and spot is not None:
            if support - _wall_buffer(support) <= spot <= support + _wall_buffer(support):
                return "background-color: #ccffcc; font-weight: bold;"  # GREEN for support zone
        
        # RED if spot is in resistance zone (between resistance - buffer and resistance + buffer)
        if resistance is not None and spot is not None:
            if resistance - _wall_buffer(resistance) <= spot <= resistance + _wall_buffer(resistance):
                return "background-color: #ffcccc; font-weight: bold;"  # RED for resistance zone
        
        # Check for wall break alerts (overrides zone-based colors)
        if hasattr(s, "_wall_break_alerts") and row["Ticker"] in s._wall_break_alerts:
            alert = s._wall_break_alerts[row["Ticker"]]
            if alert.get("zone") == "Support":
                return "background-color: #b71c1c; color: #ffffff; font-weight: bold;"  # DARK RED for Support wall broke
            if alert.get("zone") == "Resistance":
                return "background-color: #1b5e20; color: #ffffff; font-weight: bold;"  # DARK GREEN for Resistance wall broke
        
        # Check for wall reversal alerts (lower priority)
        if hasattr(s, "_wall_reversal_alerts") and row["Ticker"] in s._wall_reversal_alerts:
            alert = s._wall_reversal_alerts[row["Ticker"]]
            if alert.get("zone") == "Support":
                return "background-color: #ccffcc;"  # GREEN for Support wall reversal
            if alert.get("zone") == "Resistance":
                return "background-color: #ffcccc;"  # RED for Resistance wall reversal
        
        return ""

    def _support_bg(row):
        """Background for the Support cell: RED when Support wall broke, GREEN when Support wall reversal occurred."""
        spot = row["Spot"]
        support = row["Support"]
        # RED if Support wall broke in this ticker
        if spot is not None and support is not None:
            if spot <= support + _wall_buffer(support):
                # Check if this is a wall break event
                s = st.session_state
                if hasattr(s, "_wall_break_alerts") and row["Ticker"] in s._wall_break_alerts:
                    alert = s._wall_break_alerts[row["Ticker"]]
                    if alert.get("zone") == "Support":
                        return "background-color: #ffcccc;"  # RED for Support wall broke
                # GREEN if this is a reversal event
                if hasattr(s, "_wall_reversal_alerts") and row["Ticker"] in s._wall_reversal_alerts:
                    alert = s._wall_reversal_alerts[row["Ticker"]]
                    if alert.get("zone") == "Support":
                        return "background-color: #ccffcc;"  # GREEN for Support wall reversal
        return ""

    def _resistance_bg(row):
        """Background for the Resistance cell: GREEN when Resistance wall broke, RED when Resistance wall reversal occurred."""
        spot = row["Spot"]
        resistance = row["Resistance"]
        # GREEN if Resistance wall broke, RED if Resistance wall reversal in this ticker
        if spot is not None and resistance is not None:
            if spot >= resistance - _wall_buffer(resistance):
                s = st.session_state
                # Check for Resistance wall break event
                if hasattr(s, "_wall_break_alerts") and row["Ticker"] in s._wall_break_alerts:
                    alert = s._wall_break_alerts[row["Ticker"]]
                    if alert.get("zone") == "Resistance":
                        return "background-color: #ccffcc;"  # GREEN for Resistance wall broke
                # Check for Resistance wall reversal event
                if hasattr(s, "_wall_reversal_alerts") and row["Ticker"] in s._wall_reversal_alerts:
                    alert = s._wall_reversal_alerts[row["Ticker"]]
                    if alert.get("zone") == "Resistance":
                        return "background-color: #ffcccc;"  # RED for Resistance wall reversal
        return ""

    def _call_price_bg(row):
        """Background for the Call Price cell: GREEN for Resistance wall broke
        or reversal at Support wall."""
        s = st.session_state
        if hasattr(s, "_wall_break_alerts") and row["Ticker"] in s._wall_break_alerts:
            if s._wall_break_alerts[row["Ticker"]].get("zone") == "Resistance":
                return "background-color: #ccffcc;"
        if hasattr(s, "_wall_reversal_alerts") and row["Ticker"] in s._wall_reversal_alerts:
            if s._wall_reversal_alerts[row["Ticker"]].get("zone") == "Support":
                return "background-color: #ccffcc;"
        return ""

    def _put_price_bg(row):
        """Background for the Put Price cell: GREEN for Support wall broke
        or reversal at Resistance wall."""
        s = st.session_state
        if hasattr(s, "_wall_break_alerts") and row["Ticker"] in s._wall_break_alerts:
            if s._wall_break_alerts[row["Ticker"]].get("zone") == "Support":
                return "background-color: #ccffcc;"
        if hasattr(s, "_wall_reversal_alerts") and row["Ticker"] in s._wall_reversal_alerts:
            if s._wall_reversal_alerts[row["Ticker"]].get("zone") == "Resistance":
                return "background-color: #ccffcc;"
        return ""

    def _fmt_money(v):
        return f"${v:,.2f}" if v is not None else ""

    def _fmt_signed(v, dec):
        return f"{v:+,.{dec}f}" if v is not None else ""

    def _fmt_commas(v):
        return f"{v:,.0f}" if v is not None else ""

    def _trend_color(row):
        """Color the Trend label (up/down/flat/bullish/bearish/EMA 50 UP/DOWN) by direction.

        Reversal labels (bullish/bearish) are bolded to surface the flip;
        up/down are green/red; flat is amber.
        EMA 50 UP/DOWN use the same colors as up/down.

        When spot leaves the support zone (upwards), trend shows UP in GREEN.
        """
        val = row["Trend"]
        spot = row["Spot"]
        support = row["Support"]
        
        if val is None:
            return ""
        
        # When spot leaves support zone (moves away from support wall), show UP in GREEN
        # This indicates bullish sentiment as spot moves away from support
        if spot is not None and support is not None:
            if spot > support + _wall_buffer(support):  # Spot has left support zone upwards
                return "color: #00cc96; font-weight: bold;"
        
        val_l = val.lower()
        if val_l in ("bearish", "down"):
            return "color: #ef5350; font-weight: bold;"
        if val_l in ("bullish", "up", "ema 50 up"):
            return "color: #00cc96; font-weight: bold;"
        if val_l == "ema 50 down":
            return "color: #ef5350; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"

    def _mk_color(col_name, color_fn):
        def _c(row):
            return color_fn(row[col_name])
        return _c

    cols = [
        ("Ticker", "left", lambda v: html.escape(str(v)) if v is not None else "", None),
        ("Spot", "center", _fmt_money, _spot_bg),
        ("Expiration", "center", lambda v: html.escape(_format_expiration(v)), None),
        ("Support", "right", _fmt_money, _support_bg),
        ("Resistance", "right", _fmt_money, _resistance_bg),
        ("Call Price", "right", _fmt_money, _call_price_bg),
        ("Put Price", "right", _fmt_money, _put_price_bg),
        ("Trend", "center", lambda v: html.escape(str(v)) if v is not None else "", _trend_color),
        ("Book Imbalance", "right", lambda v: _fmt_signed(v, 2), _mk_color("Book Imbalance", _book_imbalance_color)),
        ("Flow Speed", "right", lambda v: _fmt_signed(v, 0), _mk_color("Flow Speed", _flow_speed_color)),
        ("Flow Acceleration", "right", lambda v: _fmt_signed(v, 2), _mk_color("Flow Acceleration", _flow_acceleration_color)),
        ("Liquidity Flow", "right", lambda v: _fmt_signed(v, 0), _mk_color("Liquidity Flow", _liquidity_flow_color)),
        ("Net Flow", "right", lambda v: _fmt_signed(v, 0), _mk_color("Net Flow", _net_flow_color)),
        ("Absorption", "right", _fmt_commas, _mk_color("Absorption", _absorption_color)),
    ]

    thead = "".join(f"<th>{name}</th>" for name, *_rest in cols)
    tbody = []
    for r in rows:
        cells = []
        for name, align, fmt, colorer in cols:
            text = fmt(r[name])
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
        if atm_svc.is_feed_stale(max_age_seconds=60):
            print("[_flow_grid] watchdog: feed stale >60 s, forcing reconnect")
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
