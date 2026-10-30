"""Data pipeline extracted verbatim from app.py.

Client/session bootstrap, option-chain fetch + parse, filter and state
computation, alerting, candle-cache helpers and IV-rank lookup.
Nothing here renders UI except error paths (``st.error``); view modules
import from this module.
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from scripts import client as client_mod
from scripts._constants import STREAM_SYMBOL_MAP
from scripts._utils import compute_strike_increment, is_otm_or_atm, is_itm_or_atm
from scripts.client import create_client, fetch_option_chain, get_yield, get_interest_rate, get_20d_rv, get_next_earnings_date, fetch_candles_smart, fetch_price_history_daily, load_candle_cache, save_candle_cache
from scripts.streaming_service import StreamingService
from scripts.option_streaming_service import (AtmOptionVolumeService,
                                              _save_ticker_history,
                                              _normalize_display_symbol)
from scripts.calculations import parse_option_chain, build_greeks_lookup, aggregate_by_strike, aggregate_by_expiration
from scripts.analytics import compute_analytics
from scripts.telegram_notifier import notify_alerts, diff_alerts
from scripts.flow import (_ensure_async_loop, _ticker_analytics_cache,
                          _wall_buffer, _WALL_ZONE_ALERT_COOLDOWN,
                          _strike_inc, run_async)
from scripts.news_service import NewsService
from scripts.index_spot_poller import IndexSpotPoller
from scripts.landing import render_landing
from scripts.persistent_session import restore, flush


def sync_index_poller() -> None:
    """Re-sync the IndexSpotPoller's ticker set with the current ticker_history.

    Called whenever a ticker is added or removed so the poller stops polling
    symbols the user no longer tracks (prevents phantom _ticker_flows entries
    that produce spurious alerts) and starts polling newly-added index symbols.
    """
    poller = st.session_state.get("index_spot_poller")
    if poller:
        poller.update_tickers(list(st.session_state.get("ticker_history", [])))


def init_client():
    loop = _ensure_async_loop()
    loop_changed = st.session_state.get("_async_loop_id") is not None and st.session_state._async_loop_id is not loop
    st.session_state._async_loop_id = loop
    if st.session_state.get("client") is None or loop_changed:
        try:
            st.session_state.client = create_client()
        except Exception as e:
            st.error(f"Failed to create Schwab client: {e}")
            return False
    # NOTE: no proactive REST health check here. The Schwab library refreshes
    # the access token transparently via the saved refresh token, and a
    # blocking get_quotes probe on every fragment tick burned REST quota and
    # caused 429 churn (stream status / wall-value flapping -> chart rebuild
    # flicker). Token expiry is surfaced by client.py logging instead.
    old = st.session_state.get("streaming_service")
    if old is None or getattr(old, '_loop', None) is None or getattr(old, '_loop', None) is not loop:
        if old is not None:
            old.stop()
        st.session_state.streaming_service = StreamingService(st.session_state.client, loop)
    atm_opt = st.session_state.get("atm_option_service")
    if atm_opt is None or getattr(atm_opt, '_loop', None) is None or getattr(atm_opt, '_loop', None) is not loop:
        if atm_opt is not None:
            atm_opt.stop()
        st.session_state.atm_option_service = AtmOptionVolumeService(st.session_state.client, loop)

    poller = st.session_state.get("index_spot_poller")
    if poller is None or getattr(poller, '_loop', None) is not loop:
        if poller is not None:
            poller.stop()
        poller = IndexSpotPoller(st.session_state.client, loop)
        st.session_state.index_spot_poller = poller
    if not poller.is_running and st.session_state.get("atm_option_service"):
        sync_index_poller()
        poller.start(st.session_state.atm_option_service)

    # News service (Yahoo Finance RSS polling)
    news_svc = st.session_state.get("news_service")
    if news_svc is None or getattr(news_svc, '_loop', None) is not loop:
        if news_svc is not None:
            news_svc.stop()
        news_svc = NewsService(loop)
        st.session_state.news_service = news_svc
        news_svc.start()
        # Start the background poll loop (runs on the event-loop thread,
        # does NOT touch st.session_state — tickers are pushed from the
        # main thread via update_tickers).
        async def _news_poll_loop():
            while True:
                if news_svc._tickers:
                    await news_svc.poll(news_svc._tickers)
                await asyncio.sleep(60)
        asyncio.run_coroutine_threadsafe(_news_poll_loop(), loop)

    return True


def _fetch_option_chain_core(
    symbol: str,
    *,
    selected_expirations: list[str] | None = None,
) -> dict[str, Any] | None:
    """Fetch, parse and ETF-fallback the option chain for *symbol*.

    Shared by ``fetch_data`` (main chart refresh) and ``_run_ticker_signals``
    (Trade Signals scan) so the Schwab REST + ETF-fallback pipeline is not
    duplicated.

    Returns ``None`` when the client could not be initialized.  A non-index
    fetch failure is reported via ``fetch_error`` (with empty ``data``) so each
    caller can choose its own error UX — ``fetch_data`` raises ``st.error``;
    ``_run_ticker_signals`` stays silent.  Index symbols never short-circuit
    and fall through to the ETF proxy fallback exactly like the original code.

    When *selected_expirations* is given it filters the raw chain to those
    expirations before parsing (Trade Signals scan only).
    """
    if not init_client():
        return None
    _sym = _normalize_display_symbol(symbol)
    is_index_symbol = _sym in STREAM_SYMBOL_MAP

    raw = None
    fetch_error: Exception | None = None
    try:
        raw = run_async(
            fetch_option_chain(
                st.session_state.client, symbol, strike_count=75, include_quotes=True,
            )
        )
    except Exception as e:
        fetch_error = e
        if not is_index_symbol:
            # Non-index fetch failure: nothing more to try.  Caller decides
            # whether to surface the error to the user.
            return {
                "sym": _sym,
                "is_index_symbol": False,
                "fetch_error": fetch_error,
                "data": [],
                "spot": 0.0,
                "r": 0.0,
                "q": 0.0,
                "etf_data": None,
                "etf_spot": 0.0,
                "etf_analytics": None,
                "fallback_greeks": None,
            }

    r = run_async(get_interest_rate(st.session_state.client))
    q = run_async(get_yield(st.session_state.client, symbol))

    fallback_greeks = None
    etf_analytics = None
    etf_data = None
    etf_spot = 0.0

    # Optionally narrow the raw chain to selected expirations before parsing
    # (Trade Signals scan).  Index symbols whose fetch failed have raw=None
    # here, so the filter is a no-op for them.
    if selected_expirations and raw is not None:
        if isinstance(raw, dict) and "optionChain" in raw:
            raw_filtered = [
                e for e in raw["optionChain"]
                if e.get("expiration") in selected_expirations
            ]
            raw = raw_filtered if raw_filtered else None
        elif isinstance(raw, list):
            raw_filtered = [
                e for e in raw if e.get("expiration") in selected_expirations
            ]
            raw = raw_filtered if raw_filtered else None

    if is_index_symbol:
        try:
            fb_raw = run_async(
                fetch_option_chain(
                    st.session_state.client, STREAM_SYMBOL_MAP[_sym], strike_count=75, include_quotes=True,
                )
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
            etf_data, etf_spot = parse_option_chain(fb_raw, r=r, q=q)
            if etf_data and etf_spot > 0:
                etf_analytics = compute_analytics(etf_data, etf_spot, data_full=etf_data, r=r, q=q)
        except Exception:
            pass

    if raw is not None and not (isinstance(raw, dict) and raw.get("errors")):
        data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
    else:
        data, spot = [], 0.0

    if (not data or spot <= 0) and etf_data and etf_spot > 0:
        data, spot = etf_data, etf_spot

    return {
        "sym": _sym,
        "is_index_symbol": is_index_symbol,
        "fetch_error": None,
        "data": data,
        "spot": spot,
        "r": r,
        "q": q,
        "etf_data": etf_data,
        "etf_spot": etf_spot,
        "etf_analytics": etf_analytics,
        "fallback_greeks": fallback_greeks,
    }


def fetch_data(symbol: str) -> bool:
    core = _fetch_option_chain_core(symbol)
    if core is None:
        return False
    if core["fetch_error"] is not None:
        # Non-index fetch failure (index failures fall through to ETF fallback)
        st.error(f"API Error: {core['fetch_error']}")
        return False

    _sym = core["sym"]
    data, spot = core["data"], core["spot"]
    r, q = core["r"], core["q"]
    etf_analytics = core["etf_analytics"]

    st.session_state.r = r
    st.session_state.q = q
    if not data:
        st.warning(f"No option data found for {symbol}")
        return False

    if symbol != st.session_state.get("symbol"):
        st.session_state.prev_alerts_state = {}
        st.session_state.alerts = []
        st.session_state.iv_skew_history = []
    st.session_state.data = data
    st.session_state.spot = spot
    st.session_state.symbol = symbol
    st.session_state.spot_cache[_normalize_display_symbol(symbol)] = spot
    if symbol not in st.session_state.ticker_history:
        st.session_state.ticker_history.insert(0, symbol)
        st.session_state.ticker_history = st.session_state.ticker_history[:20]
        _save_ticker_history(st.session_state.ticker_history)
        sync_index_poller()
    st.session_state.last_refresh = datetime.now()
    st.session_state.underlying_20d_rv = run_async(get_20d_rv(st.session_state.client, symbol))
    st.session_state.next_earnings_date = run_async(get_next_earnings_date(st.session_state.client, symbol))
    prefetch_daily_candles(symbol)
    apply_filters()
    compute_state()
    # Update ATM service with correct front expiration for this ticker
    if data and spot > 0:
        expirations = sorted(set(e["expiration"] for e in data))
        if expirations:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc:
                atm_svc.set_ticker_expiration(_sym, expirations[0])
                # Second-nearest expiration feeds the rolling Flow Ratio
                # / Net Flow (two ATM pairs per ticker).
                if len(expirations) > 1:
                    atm_svc.set_ticker_expiration2(_sym, expirations[1])
    # Store Put Wall (support) and Call Wall (resistance) for the grid
    atm_svc = st.session_state.get("atm_option_service")
    if atm_svc:
        _ana = st.session_state.get("analytics") or {}
        atm_svc.set_ticker_walls(_sym, _ana.get("put_wall"), _ana.get("call_wall"))
    # Populate the per-ticker strike increment (used by
    # maybe_fire_wall_zone_alerts to size the wall-refresh / big-move
    # thresholds).  Without this, the default 1.0 is used until the first
    # REST wall recompute for a non-primary ticker, which can make the
    # half-strike threshold too large (lazy walls for SPY, NDX etc.) or
    # too small (noisy refreshes for SPX).
    _si = compute_strike_increment(data)
    if _si is not None:
        _strike_inc[_normalize_display_symbol(_sym)] = _si
    st.session_state.etf_analytics = etf_analytics
    if etf_analytics and st.session_state.analytics.get("net_gex", 0) == 0:
        for key in ("net_gex", "total_call_gex", "total_put_gex",
                     "max_positive_gex", "max_negative_gex",
                     "max_positive_gex_strike", "max_negative_gex_strike",
                     "dealer_position"):
            if key in etf_analytics:
                st.session_state.analytics[key] = etf_analytics[key]
    if etf_analytics and st.session_state.analytics.get("ssvi_surface") is None:
        st.session_state.analytics["ssvi_surface"] = etf_analytics.get("ssvi_surface")
    if etf_analytics and st.session_state.analytics.get("atm_iv") is None and etf_analytics.get("atm_iv") is not None:
        st.session_state.analytics["atm_iv"] = etf_analytics["atm_iv"]
    st.session_state.iv_rank = compute_iv_rank(symbol)
    _ticker_analytics_cache[_sym] = {
        "net_gex": st.session_state.analytics.get("net_gex"),
        "atm_iv": st.session_state.analytics.get("atm_iv"),
        "rv": st.session_state.get("underlying_20d_rv", 0.0),
        "iv_rank": st.session_state.iv_rank,
    }
    check_alerts(st.session_state.analytics, spot)
    return True


def apply_filters():
    data = st.session_state.data
    spot = st.session_state.spot
    cfg = st.session_state

    filtered = list(data)

    if cfg.get("min_oi", 0) > 0:
        filtered = [e for e in filtered if e["open_interest"] >= cfg["min_oi"]]
    if cfg.get("min_vol", 0) > 0:
        filtered = [e for e in filtered if e["volume"] >= cfg["min_vol"]]
    if not cfg.get("show_itm", True):
        filtered = [e for e in filtered if is_otm_or_atm(e, spot)]
    if not cfg.get("show_otm", True):
        filtered = [e for e in filtered if is_itm_or_atm(e, spot)]

    active = sorted(set(
        e["expiration"] for e in filtered
        if e.get("open_interest", 0) > 0 or e.get("volume", 0) > 0
    ))[:4]
    filtered = [e for e in filtered if e["expiration"] in active]

    st.session_state.filtered_data = filtered


def compute_state():
    data = st.session_state.filtered_data
    spot = st.session_state.spot
    show_calls = st.session_state.show_calls
    show_puts = st.session_state.show_puts

    atm_range = st.session_state.get("strikes_atm_range", 20)
    if atm_range > 0 and data:
        strikes_sorted = sorted(set(e["strike"] for e in data))
        atm_strike = min(strikes_sorted, key=lambda s: abs(s - spot))
        atm_idx = strikes_sorted.index(atm_strike)
        n_below = min(atm_range, atm_idx)
        n_above = min(atm_range, len(strikes_sorted) - 1 - atm_idx)
        min_strike = strikes_sorted[atm_idx - n_below]
        max_strike = strikes_sorted[atm_idx + n_above]
        data = [e for e in data if min_strike <= e["strike"] <= max_strike]

    strikes = aggregate_by_strike(data, spot, show_calls, show_puts)
    by_exp = [
        e for e in aggregate_by_expiration(data, show_calls, show_puts, spot)
        if e.get("call_oi", 0) + e.get("put_oi", 0) > 0 or e.get("atm_iv", 0) > 0
    ]
    _sel_exp = st.session_state.get("selected_expiration", [])
    if isinstance(_sel_exp, str):
        _sel_exp = [_sel_exp]
    _sel_exp_for_skew = _sel_exp[0] if _sel_exp else None
    analytics = compute_analytics(data, spot, show_calls, show_puts, data_full=st.session_state.data, r=st.session_state.get("r", 0.0), q=st.session_state.get("q", 0.0), expiration=_sel_exp_for_skew)

    st.session_state.strikes = strikes
    st.session_state.by_exp = by_exp
    # Cache by_exp_all: only recompute when data changes (tracked by id).
    # Filter changes (min_oi, show_itm, etc.) should NOT trigger a re-aggregation.
    _data_ver = id(st.session_state.data)
    if st.session_state.get("by_exp_all_version", 0) != _data_ver:
        st.session_state.by_exp_all = [
            e for e in aggregate_by_expiration(st.session_state.data, show_calls, show_puts, spot)
            if e.get("call_oi", 0) + e.get("put_oi", 0) > 0 or e.get("atm_iv", 0) > 0
        ]
        st.session_state.by_exp_all_version = _data_ver
    st.session_state.analytics = analytics
    _iv_skew = analytics.get("iv_skew")
    _put_iv = analytics.get("put_iv_25d")
    _call_iv = analytics.get("call_iv_25d")
    _atm_iv = analytics.get("atm_iv")
    if _iv_skew is not None:
        st.session_state.iv_skew_history.append({
            "datetime": int(pd.Timestamp.now(tz="UTC").value // 1_000_000),
            "iv_skew": _iv_skew,
            "put_iv_25d": _put_iv,
            "call_iv_25d": _call_iv,
            "atm_iv": _atm_iv,
        })
        # Cap the history: rows accumulate while the app runs and would grow
        # unbounded (built into the chart payload on every fragment tick).
        if len(st.session_state.iv_skew_history) > 900:
            st.session_state.iv_skew_history = st.session_state.iv_skew_history[-900:]
    st.session_state.expirations = sorted(set(
        e["expiration"] for e in st.session_state.data
    ))


def check_alerts(analytics: dict, spot: float):
    s = st.session_state
    prev = s.prev_alerts_state
    
    new_alerts, next_state = diff_alerts(prev, analytics, spot)
    s.prev_alerts_state = next_state

    all_alerts = new_alerts

    _last_alert_ts = st.session_state.get("_last_check_alert_ts", 0.0)
    _now = time.time()
    if all_alerts and _now - _last_alert_ts >= _WALL_ZONE_ALERT_COOLDOWN:
        st.session_state._last_check_alert_ts = _now
        st.session_state.alerts = all_alerts + st.session_state.alerts[:20]
        tg_alerts = all_alerts
        if tg_alerts:
            _cw = analytics.get("call_wall")
            _pw = analytics.get("put_wall")
            _wall_zone = None
            if _cw is not None and _cw - _wall_buffer(_cw) <= spot <= _cw + _wall_buffer(_cw):
                _wall_zone = "Resistance"
            elif _pw is not None and _pw - _wall_buffer(_pw) <= spot <= _pw + _wall_buffer(_pw):
                _wall_zone = "Support"
            # Flow ratio for Telegram header: rolling 60 s share.
            _atm_svc = st.session_state.get("atm_option_service")
            _sym_key = st.session_state.get("symbol")
            _flow_ratio = None
            if _atm_svc is not None:
                _flow_ratio = _atm_svc.get_ticker_flow_metrics_60s(_sym_key)[1]
            # Absorption for Telegram header
            _absorption = _atm_svc.get_ticker_absorption(st.session_state.get("symbol")) if _atm_svc else None
            notify_alerts(
                tg_alerts,
                symbol=st.session_state.get("symbol"),
                spot=spot,
                gex=analytics.get("net_gex"),
                wall_zone=_wall_zone, pw=_pw, cw=_cw,
                wall_mark=analytics.get("call_wall_mark") if _wall_zone == "Resistance" else analytics.get("put_wall_mark"),
                flow_ratio=_flow_ratio,
                absorption=_absorption,
            )


CANDLE_TTL_SECS = 600  # 10 minutes


def _candles_need_refresh(symbol: str, tf: str) -> bool:
    last = st.session_state.candle_last_fetch.get(f"{symbol}|{tf}")
    if last is None:
        return True
    return (datetime.now(timezone.utc) - last).total_seconds() > CANDLE_TTL_SECS


def refresh_candles(symbol: str, tf: str):
    """Fetch candles via Parquet cache + API, store in session state."""
    key = f"{symbol}|{tf}"
    with st.spinner(f"Loading {tf} candles for {symbol}..."):
        df = run_async(fetch_candles_smart(st.session_state.client, symbol, tf))
    st.session_state.candle_dataframes[key] = df
    st.session_state.candle_last_fetch[key] = datetime.now(timezone.utc)


def prefetch_daily_candles(symbol: str):
    """Pre-fetch daily OHLCV bars for initial data.

    Always refreshes from the API when the cache is older than CANDLE_TTL_SECS
    so today's bar (and any recently-completed bars since the last load) is
    actually present in the chart. Previously this only fetched from the API
    when the cache was empty, leaving the chart stuck at whatever bars were
    last cached — today's daily bar would then never appear until the user
    cleared the cache manually.
    """
    key = f"{symbol}|1d"
    if not _candles_need_refresh(symbol, "1d") and st.session_state.candle_dataframes.get(key) is not None:
        return
    df = load_candle_cache(symbol, "1d")
    # Refresh from API when the cache is stale OR empty — `_candles_need_refresh`
    # above has already confirmed we need a refresh, so we fetch unconditionally
    # and merge the fresh API bars into whatever the cache already had.
    try:
        raw = run_async(fetch_price_history_daily(st.session_state.client, symbol, years=1))
        if raw:
            api_df = pd.DataFrame(raw)
            if not df.empty:
                merged = pd.concat([df, api_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["datetime"], keep="last")
                merged = merged.sort_values("datetime").reset_index(drop=True)
                df = merged
            else:
                df = api_df
            save_candle_cache(df, symbol, "1d")
    except Exception:
        # Fall back to whatever cache we already loaded — keep going so the
        # caller still gets to render the chart with stale data.
        pass
    if not df.empty:
        st.session_state.candle_dataframes[key] = df
        st.session_state.candle_last_fetch[key] = datetime.now(timezone.utc)


def compute_iv_rank(symbol: str) -> float | None:
    return run_async(client_mod.compute_iv_rank(st.session_state.client, symbol))


