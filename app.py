import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
import streamlit as st
import client as client_mod
from _constants import STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP, INDEX_SYMBOLS
from client import create_client, fetch_option_chain, get_yield, get_interest_rate, get_20d_rv, get_next_earnings_date, fetch_candles_smart, load_candle_cache, fetch_price_history_daily, save_candle_cache
from streaming_service import StreamingService
from option_streaming_service import (AtmOptionVolumeService, _load_ticker_history, _save_ticker_history, _normalize_display_symbol, _get_stream_symbol)
from chart_component import render_chart
from flow import (
    _ensure_async_loop,
    _ticker_analytics_cache,
    _WALL_ZONE_ALERT_COOLDOWN,
    _strike_inc,
    ensure_atm_streaming,
    render_flow_frag,
    run_async,
)
from news_service import NewsService
from index_spot_poller import IndexSpotPoller
from calculations import (
    aggregate_by_strike,
    aggregate_by_expiration,
    parse_option_chain,
    build_greeks_lookup,
)
from analytics import _filter_strikes_near_atm, compute_analytics
from signals import generate_recommendations, assess_market_bias, _tte_from_dtes
from telegram_notifier import notify_alerts, diff_alerts
from charts import _get_style, _get_css
from config import validate_config


from zoneinfo import ZoneInfo

# Fail fast with a clear, actionable message if config.toml / env vars are
# missing required credentials — otherwise the user hits a cryptic traceback
# only after clicking Refresh.  Done at module scope (before main) so the
# banner always renders.
_CONFIG_ERRORS = validate_config()

# NOTE: st.set_page_config / theme markdown must NOT run when this module is
# imported by another module — calling it twice raises StreamlitAPIException.
# Guard it so the module is safely importable for its helper functions
# (fetch_data, compute_iv_rank, etc.).
try:
    st.set_page_config(
        page_title="GammaEx - GEX Analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_get_style(), unsafe_allow_html=True)

    st.markdown("""
    <style>
    input[value="Sell Premium"]:checked + div {
        background-color: #00cc96 !important;
        border-color: #00cc96 !important;
    }
    input[value="Sell Premium"]:checked + div > div {
        background-color: #00cc96 !important;
    }
    </style>
    """, unsafe_allow_html=True)
except Exception:
    pass

_SESSION_DEFAULTS = {
    "data": [],
    "spot": 0.0,
    "analytics": {},
    "strikes": [],
    "by_exp": [],
    "by_exp_all": [],
    "underlying_20d_rv": 0.0,
    "alerts": [],
    "prev_alerts_state": {},
    "ticker_history": [],
    "streaming_service": None,
    "atm_option_service": None,
    "candles_initialized": {},
    "candle_cache": {},
    "candle_dataframes": {},
    "candle_last_fetch": {},
    "expirations": [],
    "last_refresh": None,
    "symbol": "SPY",
    "selected_expiration": [],
    "filtered_data": [],
    "client": None,
    "show_calls": True,
    "show_puts": True,
    "show_net_gex": True,
    "min_oi": 0,
    "min_vol": 0,
    "show_itm": True,
    "show_otm": True,
    "strikes_atm_range": 20,
    "next_earnings_date": None,
    "iv_rank": None,
    "candlestick_data": pd.DataFrame(),
    "candlestick_label": "",
    "iv_skew_history": [],
    "prev_flow_state": None,
    "flow_cache": {},
    "spot_cache": {},
    "news_service": None,
    "index_spot_poller": None,
}


for k, v in _SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.ticker_history:
    st.session_state.ticker_history = _load_ticker_history()

st.markdown(_get_css(), unsafe_allow_html=True)


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
    _strikes = sorted(set(e["strike"] for e in data))
    if len(_strikes) >= 2:
        _strike_inc[_normalize_display_symbol(_sym)] = min(
            _strikes[i + 1] - _strikes[i] for i in range(len(_strikes) - 1)
        )
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
        st.session_state.analytics["ssvi_skew"] = etf_analytics.get("ssvi_skew")
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
        filtered = [
            e for e in filtered
            if (e["type"] == "CALL" and e["strike"] >= spot)
            or (e["type"] == "PUT" and e["strike"] <= spot)
        ]
    if not cfg.get("show_otm", True):
        filtered = [
            e for e in filtered
            if (e["type"] == "CALL" and e["strike"] <= spot)
            or (e["type"] == "PUT" and e["strike"] >= spot)
        ]

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
    st.session_state.by_exp_all = [
        e for e in aggregate_by_expiration(st.session_state.data, show_calls, show_puts, spot)
        if e.get("call_oi", 0) + e.get("put_oi", 0) > 0 or e.get("atm_iv", 0) > 0
    ]
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
    st.session_state.expirations = sorted(set(
        e["expiration"] for e in st.session_state.data
    ))



def render_metrics(analytics: dict, spot: float, last_refresh: Optional[datetime], rv: float = 0.0, iv_rank: float | None = None, iv_skew: float | None = None):
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(
        f'<div class="gex-metric"><div class="label">Current Price</div>'
        f'<div class="value neutral">${spot:.2f}</div></div>',
        unsafe_allow_html=True,
    )
    net = analytics.get('net_gex', 0)
    net_label = "Net GEX" + (" (via ETF)" if st.session_state.get("etf_analytics") else "")
    net_cls = "positive" if net >= 0 else "negative"
    col2.markdown(
        f'<div class="gex-metric"><div class="label">{net_label}</div>'
        f'<div class="value {net_cls}">${net:,.0f}</div></div>',
        unsafe_allow_html=True,
    )
    tc = analytics.get('total_call_gex', 0)
    col3.markdown(
        f'<div class="gex-metric"><div class="label">Call GEX</div>'
        f'<div class="value positive">${tc:,.0f}</div></div>',
        unsafe_allow_html=True,
    )
    tp = analytics.get('total_put_gex', 0)
    col4.markdown(
        f'<div class="gex-metric"><div class="label">Put GEX</div>'
        f'<div class="value negative">${tp:,.0f}</div></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    pw = analytics.get('put_wall')
    col1.markdown(
        f'<div class="gex-metric"><div class="label">Put Wall</div>'
        f'<div class="value neutral">${pw:.2f}</div></div>' if pw else
        '<div class="gex-metric"><div class="label">Put Wall</div>'
        '<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    cw = analytics.get('call_wall')
    col2.markdown(
        f'<div class="gex-metric"><div class="label">Call Wall</div>'
        f'<div class="value neutral">${cw:.2f}</div></div>' if cw else
        '<div class="gex-metric"><div class="label">Call Wall</div>'
        '<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    gf = analytics.get('gamma_flip')
    col3.markdown(
        f'<div class="gex-metric"><div class="label">Gamma Flip</div>'
        f'<div class="value neutral">${gf:.2f}</div></div>' if gf else
        '<div class="gex-metric"><div class="label">Gamma Flip</div>'
        '<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    dp = analytics.get('dealer_position', 'N/A')
    dp_cls = "positive" if dp == "Long Gamma" else "negative"
    col4.markdown(
        f'<div class="gex-metric"><div class="label">Dealer Position</div>'
        f'<div class="value {dp_cls}">{dp}</div></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    pin = analytics.get('expected_pin')
    col1.markdown(
        f'<div class="gex-metric"><div class="label">Max Pain</div>'
        f'<div class="value neutral">${pin:.2f}</div></div>' if pin else
        '<div class="gex-metric"><div class="label">Max Pain</div>'
        '<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    iv_skew = analytics.get('iv_skew')
    if iv_skew is not None:
        skew_cls = "positive" if iv_skew >= 0 else "negative"
        col2.markdown(
            f'<div class="gex-metric"><div class="label">IV Skew (25Δ)</div>'
            f'<div class="value {skew_cls}">{iv_skew:+.2%}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        col2.markdown(
            '<div class="gex-metric"><div class="label">IV Skew (25Δ)</div>'
            '<div class="value neutral">N/A</div></div>',
            unsafe_allow_html=True,
        )
    col3.markdown(
        f'<div class="gex-metric"><div class="label">RV (20d)</div>'
        f'<div class="value neutral">{rv*100:.2f}%</div></div>' if rv > 0 else
        '<div class="gex-metric"><div class="label">RV (20d)</div>'
        '<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    if iv_rank is not None:
        rank_cls = "negative" if iv_rank > 60 else "positive" if iv_rank < 40 else "warning"
        c1.markdown(
            f'<div class="gex-metric"><div class="label">IV Rank</div>'
            f'<div class="value {rank_cls}">{iv_rank:.2f}%</div></div>',
            unsafe_allow_html=True,
        )
    else:
        c1.markdown(
            '<div class="gex-metric"><div class="label">IV Rank</div>'
            '<div class="value neutral">N/A</div></div>',
            unsafe_allow_html=True,
        )
    em = analytics.get('expected_move')
    if em:
        labels = []
        for exp, val in list(em.items())[:4]:
            d = exp[-5:].replace("-", "/")
            labels.append(f"{d} ±${val}")
        c2.markdown(
            f'<div class="gex-metric"><div class="label">Exp. Move</div>'
            f'<div class="value neutral">{", ".join(labels)}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        c2.markdown(
            '<div class="gex-metric"><div class="label">Exp. Move</div>'
            '<div class="value neutral">N/A</div></div>',
            unsafe_allow_html=True,
        )
    lr = last_refresh.strftime("%H:%M:%S") if last_refresh else "—"
    c3.markdown(
        f'<div style="text-align:right;color:gray;font-size:0.85rem">Last Refresh: {lr}</div>',
        unsafe_allow_html=True,
    )



def check_alerts(analytics: dict, spot: float):
    s = st.session_state
    prev = s.prev_alerts_state
    
    new_alerts, next_state = diff_alerts(prev, analytics, spot)
    s.prev_alerts_state = next_state

    rv = s.get("underlying_20d_rv", 0.0)

    all_alerts = new_alerts

    _last_alert_ts = st.session_state.get("_last_check_alert_ts", 0.0)
    _now = time.time()
    if all_alerts and _now - _last_alert_ts >= _WALL_ZONE_ALERT_COOLDOWN:
        st.session_state._last_check_alert_ts = _now
        st.session_state.alerts = all_alerts + st.session_state.alerts[:20]
        tg_alerts = [a for a in all_alerts if "Wall changed" not in a]
        if tg_alerts:
            _cw = analytics.get("call_wall")
            _pw = analytics.get("put_wall")
            _wall_zone = None
            if _cw is not None and spot >= _cw - abs(_cw) * 0.0002:
                _wall_zone = "Resistance"
            elif _pw is not None and spot <= _pw + abs(_pw) * 0.0002:
                _wall_zone = "Support"
            notify_alerts(
                tg_alerts,
                symbol=st.session_state.get("symbol"),
                spot=spot,
                gex=analytics.get("net_gex"),
                rv=rv if rv > 0 else None,
                iv_rank=st.session_state.get("iv_rank"),
                wall_zone=_wall_zone, pw=_pw, cw=_cw,
                wall_mark=analytics.get("call_wall_mark") if _wall_zone == "Resistance" else analytics.get("put_wall_mark"),
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


def render_sidebar():
    with st.sidebar:
        st.markdown("## GammaEx")

        st.markdown("---")

        ticker_history = st.session_state.get("ticker_history", [])
        current = st.session_state.get("symbol", "")
        options = list(ticker_history) if ticker_history else []
        if current and current not in options:
            options.insert(0, current)
        options.append("Add Ticker...")
        options.append("Remove Ticker...")
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        choice = st.selectbox("Ticker", options, index=idx, label_visibility="collapsed")

        dup_key = "add_ticker_dup"
        if dup_key not in st.session_state:
            st.session_state[dup_key] = ""
        prev_key = "add_ticker_prev"
        if st.session_state.get(prev_key) != choice:
            st.session_state[dup_key] = ""
        st.session_state[prev_key] = choice

        if choice == "Add Ticker...":
            if st.session_state[dup_key]:
                st.info(f"{st.session_state[dup_key]} already exists")
                symbol = st.session_state.get("symbol", "")
            else:
                symbol = st.text_input("Enter ticker", key="add_ticker_input", label_visibility="collapsed").upper()
                if symbol and symbol in ticker_history:
                    st.session_state[dup_key] = symbol
                    st.rerun()
        elif choice == "Remove Ticker...":
            if ticker_history:
                to_remove = st.selectbox("Select ticker to remove", ticker_history, label_visibility="collapsed")
                if st.button("Remove", width='stretch'):
                    ticker_history.remove(to_remove)
                    st.session_state.ticker_history = ticker_history
                    _save_ticker_history(ticker_history)
                    sync_index_poller()
                    st.rerun()
            symbol = st.session_state.get("symbol", "")
        else:
            symbol = choice

        refresh = st.button("Refresh", type="primary", width="stretch")
        if refresh and symbol:
            with st.spinner(f"Loading {symbol} option chain..."):
                fetch_data(symbol)
            # Signal render_candlesticks_frag to force a refresh on next tick
            st.session_state["_force_candle_refresh"] = symbol

        st.markdown("### Expiration")
        all_exps = st.session_state.expirations
        active_exps = sorted(set(
            e["expiration"] for e in st.session_state.data
            if e.get("open_interest", 0) > 0 or e.get("volume", 0) > 0
        ))
        exps = [e for e in all_exps if e in active_exps] or all_exps
        if exps:
            cur = st.session_state.get("selected_expiration", [])
            if isinstance(cur, str):
                cur = []
            cur = [e for e in cur if e in exps]
            if not cur:
                cur = [exps[0]]
            sel = st.multiselect(
                "Expiration", exps,
                default=cur,
                label_visibility="collapsed",
                placeholder="Select expirations...",
            )
            st.session_state.selected_expiration = sel

        st.markdown("### Alerts")
        if st.session_state.alerts:
            for alert in st.session_state.alerts[:10]:
                st.info(alert, icon="ℹ")
            if st.button("Clear Alerts", width='stretch'):
                st.session_state.alerts = []
        else:
            st.caption("No alerts yet")

        st.markdown("### Display")
        st.session_state.show_calls = st.checkbox("Show Calls", value=True)
        st.session_state.show_puts = st.checkbox("Show Puts", value=True)
        st.session_state.show_itm = st.checkbox("Show ITM", True)
        st.session_state.show_otm = st.checkbox("Show OTM", True)


TIMEFRAMES = {
    "1m": "1min", "2m": "2min", "5m": "5min", "15m": "15min",
    "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W", "1M": "1ME",
}


@st.fragment(run_every=2)
def render_candlesticks_frag():
    s = st.session_state
    if not s.get("client"):
        st.info("Initialize authentication to load data")
        return

    candles_container = st.container()
    with candles_container:
        st.subheader("Candlesticks")


        # Only show historical data, no live streaming controls
        symbol = s.get("symbol", "SPY")
        
        # Create row layout for controls - timeframe and indicators on same row
        row1, row2 = st.columns([1, 3])
        
        with row1:
            timeframe = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=0, label_visibility="collapsed", width=100)
        
        with row2:
            indicator_options = ["SMA 20", "SMA 50", "EMA 20", "EMA 50 Squeeze", "EMA 200", "Volume Profile", "Anchored VWAP", "Trend", "Volume", "Andean Osc"]
            selected_indicators = st.multiselect("Indicators", indicator_options, default=["Andean Osc", "EMA 50 Squeeze", "Trend"], label_visibility="collapsed")
        
        # Refresh the cache from the API when the existing on-disk bars are
        # stale relative to the user's chosen timeframe. The chart fragment
        # renders every 1s, so we need a gate that doesn't hammer the TDA REST
        # endpoint on every render. We use the parquet's own last-bar
        # timestamp as the freshness indicator: for intraday charts, refresh
        # when the last bar is older than ~2 timeframe buckets (so a 1m
        # chart refreshes when the cache is ~2 min old — never more than a
        # couple bars behind); for D/W/M, refresh when the last bar is more
        # than 10 minutes old.
        try:
            _probe = load_candle_cache(symbol, timeframe)
        except Exception:
            _probe = pd.DataFrame()
        forced_refresh = False
        if not _probe.empty:
            last_bar_dt = pd.Timestamp(int(_probe["datetime"].iloc[-1]), unit="ms", tz="UTC")
            now_dt = pd.Timestamp.now(tz="UTC")
            tf_minutes = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
            if tf_minutes is None:
                stale_threshold_secs = 600  # 10 minutes for D/W/M
            else:
                # 2 TF-buckets, with a 60-second floor so we don't slam the
                # API more than once per minute for very small TFs.
                stale_threshold_secs = max(60, tf_minutes * 60 * 2)
            age_secs = (now_dt - last_bar_dt).total_seconds()
            forced_refresh = age_secs > stale_threshold_secs

        # If the sidebar Refresh button was just clicked for the current
        # symbol, force a fresh candle pull regardless of cache staleness.
        _force_refresh_symbol = s.get("_force_candle_refresh")
        if _force_refresh_symbol == symbol:
            s["_force_candle_refresh"] = None
            forced_refresh = True

        # Also short-circuit if the client isn't ready — refresh can't help.
        client_ok = s.get("client") is not None
        if client_ok and (forced_refresh or _candles_need_refresh(symbol, timeframe)):
            try:
                refresh_candles(symbol, timeframe)
            except Exception:
                # Refresh is best-effort: fall through to whatever cache load
                # returns below so the chart still renders with stale data.
                pass

        historical_df = load_candle_cache(symbol, timeframe)

        # --- Build chart DataFrame ---
        chart_df = pd.DataFrame()
        chart_label = ""

        if not historical_df.empty:
            recent = historical_df.tail(500).dropna(subset=["open", "high", "low", "close"])
            chart_df = recent[["datetime", "open", "high", "low", "close", "volume"]].copy()
            # Remove duplicate datetime entries from historical data
            chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
            chart_label = f"Historical {timeframe}"
        else:
            historical_df = load_candle_cache(symbol, "1d")
            if not historical_df.empty:
                recent = historical_df.tail(500).dropna(subset=["open", "high", "low", "close"])
                chart_df = recent[["datetime", "open", "high", "low", "close", "volume"]].copy()
                # Remove duplicate datetime entries from historical data
                chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
                chart_label = f"No {timeframe} cache — daily"
            else:
                st.info("Load data to see historical data")
                return

        if chart_df.empty:
            st.info("No data available")
            return

        # --- Start streaming services (equity + ATM option) ---
        stream_symbol = STREAM_SYMBOL_MAP.get(symbol.upper().lstrip("$"), symbol)
        ensure_atm_streaming(stream_symbol)

        # Periodically refresh spots for all tickers (every 2s)
        atm_svc = st.session_state.get("atm_option_service")
        _first_exp = st.session_state.get("selected_expiration")
        _first_exp = _first_exp[0] if isinstance(_first_exp, list) and _first_exp else (_first_exp if isinstance(_first_exp, str) else None)
        if atm_svc and atm_svc.is_running and _first_exp:
            import time as _time_mod
            _now = _time_mod.time()
            _last_spot_refresh = s.get("_last_spot_refresh", 0)
            if _now - _last_spot_refresh >= 2:
                s._last_spot_refresh = _now
                _all_tickers = s.get("ticker_history", [])
                _stream_symbols = [_get_stream_symbol(t) for t in _all_tickers]
                try:
                    from client import fetch_quotes
                    quote_resp = run_async(fetch_quotes(s.client, _stream_symbols))
                    for disp_sym, stream_sym in zip(_all_tickers, _stream_symbols):
                        _disp_upper = _normalize_display_symbol(disp_sym)
                        qd = quote_resp.get(stream_sym, {}) or {}
                        quote = qd.get("quote", {}) or qd.get(stream_sym, {})
                        last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                        if last is not None and float(last) > 0:
                            spot = float(last)
                            if _disp_upper in INDEX_QUOTE_MAP:
                                # The ETF-proxy price (SPY) drives the index
                                # ticker's OCC subscription strikes, not its
                                # displayed index-level spot.
                                atm_svc.set_ticker_proxy_spot(_disp_upper, spot)
                                continue
                            s.spot_cache[_disp_upper] = spot
                            # Also update ATM service
                            atm_svc.set_ticker_spot(_disp_upper, spot)

                    # Fetch actual index quotes for SPX, RUT, NDX
                    _idx_fetch = []
                    _idx_disp_map = {}
                    for _t in _all_tickers:
                        _t_upper = _normalize_display_symbol(_t)
                        if _t_upper in INDEX_QUOTE_MAP:
                            _iq = INDEX_QUOTE_MAP[_t_upper]
                            _idx_fetch.append(_iq)
                            _idx_disp_map[_iq] = _t_upper
                    if _idx_fetch:
                        try:
                            idx_resp = run_async(fetch_quotes(s.client, _idx_fetch))
                            for _iq, _disp_upper in _idx_disp_map.items():
                                qd = idx_resp.get(_iq, {}) or {}
                                quote = qd.get("quote", {}) or qd.get(_iq, {})
                                last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                                if last is not None and float(last) > 0:
                                    spot = float(last)
                                    s.spot_cache[_disp_upper] = spot
                                    atm_svc.set_ticker_spot(_disp_upper, spot)
                        except Exception as e:
                            print(f"[chart] index quote fetch failed: {e}")
                except Exception:
                    pass

        # Feed spot from equity stream to ATM option service
        # Normalize chart_df["datetime"] to int64 for merging
        chart_df["datetime"] = chart_df["datetime"].astype("int64")

        svc = s.get("streaming_service")

        # Merge streaming OHLC + buy_vol/sell_vol into chart df when available.
        # Streaming aggregates ticks into 1-second buckets keyed on ms timestamps.
        # We floor each streaming bucket to the selected timeframe's boundary, so
        # ticks accumulate inside the user's chosen bar (e.g., 5m chart: all ticks
        # between 10:30 and 10:35 belong to the 10:30 bar). Only the *last* bar
        # of the chart gets live-updated on every 1-second fragment tick — every
        # historical bar before it keeps its original OHLC unchanged.
        # Only merge streaming data when the streamed symbol matches the chart
        # symbol exactly (no proxy remapping). Index symbols (SPX, RUT, NDX)
        # are streamed via their ETF equivalents (SPY, IWM, QQQ), but those
        # have completely different price scales — merging them would produce
        # nonsensical candlesticks, so skip the merge for proxy streams.
        _sym_norm_chart = _normalize_display_symbol(symbol)
        _merge_streaming = svc and svc.is_running and svc.symbol == stream_symbol and _sym_norm_chart == stream_symbol
        if _merge_streaming:
            # Flag to trigger chart re-render when streaming data updates
            # This ensures the chart updates every time new streaming data arrives
            s["_trigger_candlestick_refresh"] = True
            try:
                stream_df = svc.get_candles()
                if not stream_df.empty and not chart_df.empty:
                    stream_df = stream_df.reset_index()
                    stream_df["datetime"] = stream_df["datetime"].astype("int64")
                    # Floor streaming 1s bars to the user's timeframe boundary so
                    # live ticks update the current historical bar.
                    tf_minutes = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                    if tf_minutes is None:
                        # Daily/weekly/monthly timeframes have no "minutes" key.
                        # The historical cache for these is timestamped at
                        # midnight US/Eastern (TDA convention — 05:00 UTC during
                        # EDT, 06:00 UTC during EST), NOT midnight UTC. So we
                        # floor live ticks to the America/New_York day boundary
                        # (their local midnight interpreted as UTC ms) so today's
                        # daily cache bar keeps updating with new ticks. Otherwise
                        # the live ticks would floor to UTC midnight and never
                        # match the historical EDT-midnight bar — today's bar
                        # wouldn't appear/get updated.
                        tf_ms = 24 * 60 * 60 * 1000
                        try:
                            _ny_tz = ZoneInfo("America/New_York")
                            # Convert each tick ms -> NY-local date, take that
                            # date's start-of-day in NY, convert back to UTC ms.
                            # NOTE: pandas datetime64[ms] casts to int64 directly in
                            # milliseconds — do NOT divide by 1_000_000.
                            tick_dt = pd.to_datetime(stream_df["datetime"], unit="ms", utc=True).dt.tz_convert(_ny_tz)
                            day_start_ny = tick_dt.dt.normalize()
                            stream_df["datetime"] = day_start_ny.dt.tz_convert("UTC").astype("int64")
                        except Exception:
                            # Fallback: floor to UTC day boundary (less correct
                            # for daily/weekly/monthly cache alignment but never
                            # raises).
                            stream_df["datetime"] = (stream_df["datetime"] // tf_ms) * tf_ms
                    else:
                        tf_ms = tf_minutes * 60 * 1000
                        stream_df["datetime"] = (stream_df["datetime"] // tf_ms) * tf_ms
                    # Aggregate streaming bars per (timeframe-aligned) timestamp
                    stream_agg = stream_df.groupby("datetime").agg({
                        "open": "first", "high": "max", "low": "min", "close": "last",
                        "volume": "sum",
                        "buy_vol": "sum", "sell_vol": "sum",
                    }).reset_index()

                    chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    # Rightmost historical timestamp — every historical bar at or
                    # before this point stays untouched; only the live/last bar of
                    # the chart is updated with streaming ticks each fragment tick.
                    last_hist_time = int(chart_df["datetime"].iloc[-1])
                    # Current (rightmost) timeframe bucket aligned to the user's
                    # TF. Use the SAME flooring logic applied to live ticks above
                    # so the live-last-bucket timestamp matches what
                    # stream_agg["datetime"] uses (US/Eastern day boundary for
                    # daily/weekly/monthly; intraday-aligned bucket otherwise).
                    now_utc_ms = int(pd.Timestamp.now(tz="UTC").value // 1_000_000)
                    if tf_minutes is None:
                        try:
                            _ny_tz = ZoneInfo("America/New_York")
                            current_bucket = int(
                                pd.Timestamp.now(tz=_ny_tz)
                                .normalize()
                                .tz_convert("UTC")
                                .value // 1_000_000
                            )
                        except Exception:
                            current_bucket = (now_utc_ms // tf_ms) * tf_ms
                    else:
                        current_bucket = (now_utc_ms // tf_ms) * tf_ms
                    # The "live last bar" is whichever bucket is furthest right:
                    # the current timeframe bucket, or the most recent historical
                    # bar (when the cache is ahead of the wall clock for any
                    # reason). Live ticks floored to this bucket merge into the
                    # existing bar; newer buckets append as brand-new bars.
                    live_last_time = max(last_hist_time, current_bucket)

                    # Split live aggregates into cohorts:
                    #   (a) buckets <= last_hist_time AND != live_last_time —
                    #       these match existing historical bars. Per spec ("before
                    #       last bar maintain historical values") we DISCARD their
                    #       live aggregates and keep the historical OHLC intact.
                    #   (b) buckets strictly newer than last_hist_time but earlier
                    #       than live_last_time — closed streaming bars that the
                    #       historical cache hasn't picked up yet. There's no
                    #       historical row to merge with, so they're added as new
                    #       standalone bars between the historical bars and the
                    #       live/last bar.
                    #   (c) the bucket at live_last_time — gets merged with any
                    #       historical row at this timestamp to form the updated
                    #       last bar.
                    #   (d) buckets strictly newer than live_last_time — appended
                    #       as brand-new bars past the right edge.
                    last_bucket_agg = stream_agg[stream_agg["datetime"] == live_last_time]
                    new_bars_agg = stream_agg[stream_agg["datetime"] > live_last_time]
                    closed_between = stream_agg[
                        (stream_agg["datetime"] > last_hist_time) &
                        (stream_agg["datetime"] < live_last_time)
                    ]

                    # Capture the historical row at live_last_time BEFORE removing
                    # it, so we can merge live OHLC into its snapshot.
                    hist_last_row = chart_df[chart_df["datetime"] == live_last_time]
                    hist_last_snapshot = (
                        hist_last_row.iloc[0].to_dict() if not hist_last_row.empty else None
                    )
                    # Remove only the matching historical row (if any) at the live
                    # last-bucket timestamp; every earlier historical bar stays.
                    chart_df = chart_df[chart_df["datetime"] != live_last_time]

                    # Build the updated last bar:
                    #   - If a historical row exists at live_last_time AND we have
                    #     live ticks: merge them (preserves historical open, takes
                    #     max(high)/min(low), live close replaces close, volume
                    #     sums).
                    #   - If only live ticks exist (e.g., current bucket is newer
                    #     than any historical bar): the live aggregate alone is the
                    #     new last bar.
                    #   - If only a historical row exists (no live ticks landing in
                    #     this bucket yet): keep the historical row as-is.
                    last_bar = pd.DataFrame()
                    if not last_bucket_agg.empty:
                        live_row = last_bucket_agg.iloc[0]
                        if hist_last_snapshot is not None:
                            merged_open = hist_last_snapshot["open"]
                            merged_high = max(hist_last_snapshot["high"], live_row["high"])
                            merged_low = min(hist_last_snapshot["low"], live_row["low"])
                            merged_close = live_row["close"]
                            hv = hist_last_snapshot.get("volume", 0)
                            lv = live_row.get("volume", 0)
                            hv = 0 if (hv is None or hv != hv) else hv
                            lv = 0 if (lv is None or lv != lv) else lv
                            merged_volume = float(hv) + float(lv)
                        else:
                            merged_open = live_row["open"]
                            merged_high = live_row["high"]
                            merged_low = live_row["low"]
                            merged_close = live_row["close"]
                            lv = live_row.get("volume", 0)
                            merged_volume = float(0 if (lv is None or lv != lv) else lv)
                        last_bar = pd.DataFrame([{
                            "datetime": live_last_time,
                            "open": float(merged_open),
                            "high": float(merged_high),
                            "low": float(merged_low),
                            "close": float(merged_close),
                            "volume": float(merged_volume),
                            "buy_vol": int(live_row.get("buy_vol", 0) or 0),
                            "sell_vol": int(live_row.get("sell_vol", 0) or 0),
                        }])
                    elif hist_last_snapshot is not None:
                        # No live ticks in this bucket yet — fall back to the
                        # untouched historical last bar.
                        last_bar = pd.DataFrame([hist_last_snapshot])

                    # Assemble final chart_df in chronological order: historical
                    # bars (unchanged) + closed streaming bars that landed between
                    # the cache and the live bucket (new bars formed during this
                    # streaming session but not yet refreshed into cache) + the
                    # merged/updated last bar + any newer streaming bars that
                    # arrived past the current bucket boundary.
                    parts = [chart_df]
                    if not closed_between.empty:
                        parts.append(closed_between)
                    if not last_bar.empty:
                        parts.append(last_bar)
                    if not new_bars_agg.empty:
                        parts.append(new_bars_agg)
                    chart_df = pd.concat(parts, ignore_index=True)
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    # Scale trailing cap to the timeframe so today + recent days
                    # remain visible at intraday granularities.
                    max_bars = 1500 if tf_minutes else 500
                    if len(chart_df) > max_bars:
                        chart_df = chart_df.tail(max_bars).reset_index(drop=True)
            except Exception:
                pass

        # ---- Index symbols (SPX, RUT, NDX): build a live bar from the real
        # index spot poll (s.spot_cache, updated every ~2s by the $SPX etc.
        # fetch above) and merge it into the chart so $SPX/$RUT/$NDX
        # candlesticks update like equities.  Index symbols cannot be streamed
        # via the equity WebSocket (Schwab only supports LEVELONE_EQUITIES for
        # real equities, not indices), so we fall back to REST polling ---- #
        _sym_norm_idx = _normalize_display_symbol(symbol)
        if _sym_norm_idx in INDEX_SYMBOLS and not chart_df.empty:
            try:
                _atm_svc = s.get("atm_option_service")
                _idx_spot = _atm_svc.get_ticker_spot(_sym_norm_idx) if _atm_svc else None
                if _idx_spot is None:
                    _idx_spot = s.spot_cache.get(_sym_norm_idx)
                if _idx_spot is not None and float(_idx_spot) > 0:
                    _idx_spot = float(_idx_spot)
                    _tf_min_idx = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                    if _tf_min_idx is None:
                        _tf_ms_idx = 24 * 60 * 60 * 1000
                        try:
                            _ny_tz_idx = ZoneInfo("America/New_York")
                            _live_bucket_idx = int(
                                pd.Timestamp.now(tz=_ny_tz_idx).normalize().tz_convert("UTC").value // 1_000_000
                            )
                        except Exception:
                            _live_bucket_idx = (int(pd.Timestamp.now(tz="UTC").value // 1_000_000) // _tf_ms_idx) * _tf_ms_idx
                    else:
                        _tf_ms_idx = _tf_min_idx * 60 * 1000
                        _live_bucket_idx = (int(pd.Timestamp.now(tz="UTC").value // 1_000_000) // _tf_ms_idx) * _tf_ms_idx
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    _last_hist_time_idx = int(chart_df["datetime"].iloc[-1])
                    _live_last_time_idx = max(_last_hist_time_idx, _live_bucket_idx)
                    _hist_at_live_idx = chart_df[chart_df["datetime"] == _live_last_time_idx]
                    _hist_snapshot_idx = _hist_at_live_idx.iloc[0].to_dict() if not _hist_at_live_idx.empty else None
                    chart_df = chart_df[chart_df["datetime"] != _live_last_time_idx]
                    if _hist_snapshot_idx is not None:
                        _o_idx = _hist_snapshot_idx["open"]
                        _h_idx = max(_hist_snapshot_idx["high"], _idx_spot)
                        _l_idx = min(_hist_snapshot_idx["low"], _idx_spot)
                        _vol_idx = _hist_snapshot_idx.get("volume", 0) or 0
                    else:
                        _o_idx = _h_idx = _l_idx = _idx_spot
                        _vol_idx = 0
                    _live_bar_idx = pd.DataFrame([{
                        "datetime": _live_last_time_idx,
                        "open": float(_o_idx),
                        "high": float(_h_idx),
                        "low": float(_l_idx),
                        "close": float(_idx_spot),
                        "volume": float(_vol_idx),
                    }])
                    chart_df = pd.concat([chart_df, _live_bar_idx], ignore_index=True).sort_values("datetime").reset_index(drop=True)
                    _max_bars_idx = 1500 if _tf_min_idx else 500
                    if len(chart_df) > _max_bars_idx:
                        chart_df = chart_df.tail(_max_bars_idx).reset_index(drop=True)
            except Exception:
                pass

        # Merge ATM option volume into chart df when available
        # atm_df index is int64 milliseconds — same unit as chart_df["datetime"].
        # Warnings are shown near the chart (see Option_Volume_Profile block below);
        # this block only attaches ATM volume columns to chart_df.
        if "Option_Volume_Profile" in selected_indicators:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc and atm_svc.is_running:
                try:
                    atm_df = atm_svc.get_candles()
                    if not atm_df.empty:
                        atm_df = atm_df.reset_index()
                        atm_df["datetime"] = atm_df["datetime"].astype("int64")
                        # Floor ATM 1-second bucket timestamps to the chart's
                        # timeframe boundary so they match chart_df["datetime"].
                        _tf_min = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                        if _tf_min is None:
                            _tf_ms = 24 * 60 * 60 * 1000
                            try:
                                _ny_tz = ZoneInfo("America/New_York")
                                tick_dt = pd.to_datetime(atm_df["datetime"], unit="ms", utc=True).dt.tz_convert(_ny_tz)
                                day_start_ny = tick_dt.dt.normalize()
                                atm_df["datetime"] = day_start_ny.dt.tz_convert("UTC").astype("int64")
                            except Exception:
                                atm_df["datetime"] = (atm_df["datetime"] // _tf_ms) * _tf_ms
                        else:
                            _tf_ms = _tf_min * 60 * 1000
                            atm_df["datetime"] = (atm_df["datetime"] // _tf_ms) * _tf_ms
                        atm_agg = atm_df.groupby("datetime").agg({
                            "call_buy_vol": "sum", "call_sell_vol": "sum",
                            "put_buy_vol": "sum", "put_sell_vol": "sum",
                            "total_buy_vol": "sum", "total_sell_vol": "sum",
                        }).reset_index()
                        chart_df = chart_df.merge(atm_agg, on="datetime", how="left")
                        for col in ["call_buy_vol", "call_sell_vol", "put_buy_vol", "put_sell_vol", "total_buy_vol", "total_sell_vol"]:
                            if col in chart_df.columns:
                                chart_df[col] = chart_df[col].fillna(0).astype(int)
                except Exception:
                    pass

        # Persist in session state. chart_df["datetime"] stays as int64 ms because
        # chart_component.render_chart converts it to UNIX-seconds time keys for
        # lightweight-charts (with the proper EST offset).
        s.candlestick_data = chart_df
        s.candlestick_label = chart_label

        # --- Render lightweight-charts streaming candlestick ---
        df = s.candlestick_data

        # Build the candle list for chart_component.render_chart. Keep datetime as
        # int64 ms so the streaming 1-second bars are uniquely keyed on time.
        _extra_cols = [c for c in ["buy_vol", "sell_vol",
                                   "call_buy_vol", "call_sell_vol",
                                   "put_buy_vol", "put_sell_vol",
                                   "total_buy_vol", "total_sell_vol"]
                       if c in df.columns]
        base_cols = ["datetime", "open", "high", "low", "close"]
        if "volume" in df.columns:
            base_cols.append("volume")
        candles_payload = df[base_cols + _extra_cols].to_dict("records")
        for c in candles_payload:
            c["datetime"] = int(c["datetime"])
            c["open"] = float(c["open"])
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["close"] = float(c["close"])
            if "volume" in c:
                v = c["volume"]
                c["volume"] = float(v) if pd.notna(v) and v == v else 0.0
            for ac in _extra_cols:
                if ac in c:
                    v = c[ac]
                    try:
                        c[ac] = int(v)
                    except (TypeError, ValueError, OverflowError):
                        c.pop(ac, None)
                else:
                    c.pop(ac, None)

        last_close = float(df["close"].iloc[-1]) if not df.empty else None

        # Call/Put wall horizontal lines (price levels from analytics)
        _analytics = s.get("analytics") or {}
        _cw = _analytics.get("call_wall")
        _pw = _analytics.get("put_wall")

        # Websocket streaming status — overlaid on the candlesticks chart.
        # The equity StreamClient feeds the live candles (and, when
        # Option_Volume_Profile is selected, the option-trade aggregation), so its
        # status is shown regardless of which indicators are selected.  We
        # resolve a single status string + level here and hand it to
        # render_chart() via the `status` parameter; an absolute-positioned
        # badge inside the chart container draws it on top of the canvas.
        _eq_svc = st.session_state.get("streaming_service")
        _atm_svc = st.session_state.get("atm_option_service")
        _status = None
        if _eq_svc is None:
            _status = {"text": "Stream not initialized", "level": "warning"}
        elif not _eq_svc.is_running:
            _status = {"text": f"Starting {stream_symbol} stream...", "level": "info"}
        elif _eq_svc.is_connected and _eq_svc.has_data:
            _msg = f"Receiving {stream_symbol} ticks · {_eq_svc.ticks_received} received"
            if "Option_Volume_Profile" in selected_indicators and _atm_svc is not None:
                if _atm_svc.is_running and _atm_svc.has_data:
                    _n = _atm_svc.ticks_received
                    _msg += f" · { _n } option tick{'s' if _n != 1 else ''}"
                elif _atm_svc.is_running and not _atm_svc.has_data:
                    _msg += " · waiting for option trades..."
                elif not _atm_svc.is_running:
                    _msg += " · option flow not subscribed"
            _status = {"text": _msg, "level": "success"}
        elif _eq_svc.is_connected and not _eq_svc.has_data:
            _status = {"text": f"Connected · waiting for {stream_symbol} trades...", "level": "info"}
        elif not _eq_svc.is_connected:
            _err = getattr(_eq_svc, "last_error", None)
            _msg = "WebSocket disconnected"
            if _err:
                _msg += f": {_err}"
            _status = {"text": _msg, "level": "warning"}

        if candles_payload:
            iv_skew_indicator_enabled = any(ind in selected_indicators for ind in ["IV Skew (25Δ)"])
            _iv_skew_hist = s.get("iv_skew_history") or []
            if iv_skew_indicator_enabled and _analytics.get("iv_skew") is not None:
                _now_ms = int(pd.Timestamp.now(tz="UTC").value // 1_000_000)
                if not _iv_skew_hist or _iv_skew_hist[-1].get("datetime") != _now_ms:
                    _iv_skew_hist = list(_iv_skew_hist)
                    _iv_skew_hist.append({
                        "datetime": _now_ms,
                        "iv_skew": _analytics["iv_skew"],
                        "put_iv_25d": _analytics.get("put_iv_25d"),
                        "call_iv_25d": _analytics.get("call_iv_25d"),
                        "atm_iv": _analytics.get("atm_iv"),
                    })
            _chart_key = f"lwc_candlestick_{symbol}"
            st.markdown(
                f'<div id="{_chart_key}" style="position:relative;width:100%;"></div>',
                unsafe_allow_html=True,
            )
            render_chart(
                candles_payload,
                indicators=selected_indicators,
                call_wall=_cw,
                put_wall=_pw,
                last_close=last_close,
                status=_status,
                symbol=symbol,
                iv_skew_history=_iv_skew_hist if iv_skew_indicator_enabled else [],
            )
        st.caption(f"{s.candlestick_label} bars ({len(s.candlestick_data)})")


@st.fragment(run_every=10)
def render_metrics_frag():
    s = st.session_state
    if not s.get("data"):
        return
    # Prefer the live L1 last price when the equity stream is active, so
    # the "Current Price" card updates at the fragment cadence rather
    # than the slower option-chain poll cadence. The analytics shown in
    # the neighbouring columns still run off the polled s.spot.
    #
    # For index symbols (SPX, RUT, NDX) the stream subscribes to the
    # ETF proxy (SPY, IWM, QQQ) which has a completely different price
    # scale — never use the ETF's live price as the index spot.
    _sym = _normalize_display_symbol(s.get("symbol", ""))
    live = None
    if _sym not in INDEX_SYMBOLS:
        svc = s.get("streaming_service")
        if svc:
            live = svc.last_price
    spot = live if (live and live > 0) else s.spot
    metrics_container = st.container()
    with metrics_container:
        iv_rank = s.get("iv_rank")
        iv_skew = s.analytics.get('iv_skew')
        render_metrics(s.analytics, spot, s.last_refresh, rv=s.get("underlying_20d_rv", 0.0), iv_rank=iv_rank, iv_skew=iv_skew)


def render_market_structure():
    s = st.session_state
    if not s.get("strikes"):
        return

    strikes = s.get("strikes")

    st.subheader("Market Structure")

    ms_view = st.radio(
        "View",
        ["GEX by Strike", "GEX by Expiration", "Gamma Surface", "Dealer Curve"],
        horizontal=True, label_visibility="collapsed",
    )

    gex_container = st.container()
    with gex_container:
        if ms_view == "GEX by Strike":
            from charts import create_gex_histogram
            fig = create_gex_histogram(strikes, s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), gamma_flip=s.analytics.get("gamma_flip"), )
            fig.update_layout(dragmode="zoom"); st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_histogram")
        elif ms_view == "GEX by Expiration":
            from charts import create_gex_by_expiration
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="gex_exp_slider")
            fig = create_gex_by_expiration(s.by_exp_all, max_exps=mx, ); fig.update_layout(dragmode="zoom")
            st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_by_exp")
        elif ms_view == "Gamma Surface":
            from charts import create_gamma_surface
            fig = create_gamma_surface(s.filtered_data, ); st.plotly_chart(fig, width='stretch', key="gamma_surface")
        else:
            from charts import create_dealer_gamma_curve
            dm = st.radio("Select", ["GEX", "VEX", "CEX"], horizontal=True, label_visibility="collapsed")
            _dc_strikes = _filter_strikes_near_atm(strikes, s.spot, n=20)
            fig = create_dealer_gamma_curve(_dc_strikes, s.spot, mode=dm.lower(), gamma_flip=s.analytics.get("gamma_flip"), call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), vex_magnet=s.analytics.get("vex_magnet"), vex_repellent=s.analytics.get("vex_repellent"))
            st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="dealer_curve_chart")


def render_positioning():
    s = st.session_state
    if not s.get("strikes"):
        return

    st.subheader("Positioning")

    selected_view_type = st.radio(
        "Select", ["Open Interest", "Volume"], horizontal=True, label_visibility="collapsed",
        key="pos_oi_vol_radio"
    )
    selected_expirations = s.get("selected_expiration", [])
    if isinstance(selected_expirations, str):
        selected_expirations = []
    
    raw_data = [e for e in s.data if e["expiration"] in selected_expirations] if selected_expirations else list(s.data)
    if not s.get("show_itm", True):
        raw_data = [e for e in raw_data if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
    if not s.get("show_otm", True):
        raw_data = [e for e in raw_data if (e["type"]=="CALL" and e["strike"]<=s.spot) or (e["type"]=="PUT" and e["strike"]>=s.spot)]
    
    if not raw_data:
        st.info("No positioning data available")
        return
    raw_data = _filter_strikes_near_atm(raw_data, s.spot, n=20)
    positioning_data = aggregate_by_strike(
        raw_data, s.spot, show_calls=s.show_calls, show_puts=s.show_puts
    )

    if not positioning_data:
        st.info("No positioning data available")
        return

    if selected_view_type == "Open Interest":
        from charts import create_oi_by_strike
        with st.container():
            fig = create_oi_by_strike(
                positioning_data, s.spot, mode="oi", 
            )
            fig.update_layout(dragmode="zoom")
            st.plotly_chart(
                fig, config={"scrollZoom": True}, width="stretch", key="oi_chart"
            )
    elif selected_view_type == "Volume":
        from charts import create_oi_by_strike
        with st.container():
            fig = create_oi_by_strike(
                positioning_data, s.spot, mode="volume", 
            )
            fig.update_layout(dragmode="zoom")
            st.plotly_chart(
                fig, config={"scrollZoom": True}, width="stretch", key="volume_chart"
            )


def render_volatility():
    s = st.session_state
    if not s.get("strikes"):
        return

    st.subheader("Volatility")

    from charts import create_iv_by_strike, create_iv_richness_by_strike

    _rv = s.get("underlying_20d_rv", 0.0)
    _ssvi_surf = s.analytics.get("ssvi_surface") if s.get("analytics") else None

    vol_view = st.radio(
        "View",
        ["IV by Expiration", "IV by Strike"],
        horizontal=True, label_visibility="collapsed",
        key="vol_view_radio",
    )

    if vol_view == "IV by Expiration":
        from charts import create_atm_iv_histogram, create_vrp_chart
        mo = st.radio("View", ["ATM IV", "VRP"], horizontal=True, label_visibility="collapsed", key="iv_exp_mode")
        mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="iv_exp_slider")
        ivd = s.by_exp_all[:mx]
        if mo == "ATM IV": st.plotly_chart(create_atm_iv_histogram(ivd, rv=_rv, ssvi_surface=_ssvi_surf, spot=s.spot).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="atm_iv_chart")
        elif _rv > 0:
            legend_items = [
                ("#27AE60", "≤ -10"),
                ("#2ECC71", "-10 to -5"),
                ("#BDC3C7", "-5 to 0"),
                ("#F4D03F", "0 to +5 Fair"),
                ("#F39C12", "+5 to +10"),
                ("#E74C3C", "≥ +10"),
            ]
            cols = st.columns(len(legend_items) + 2)
            cols[0].markdown(
                '<div style="display:flex;align-items:center;justify-content:center;height:100%;">'
                '<span style="font-size:0.75rem;white-space:nowrap;font-weight:600;">Buy Premium</span></div>',
                unsafe_allow_html=True,
            )
            for ci, (color, label) in zip(cols[1:-1], legend_items):
                ci.markdown(
                    f'<div style="display:flex;align-items:center;gap:4px;justify-content:center;">'
                    f'<span style="display:inline-block;width:14px;height:14px;border-radius:2px;background:{color};border:1px solid #555;"></span>'
                    f'<span style="font-size:0.75rem;white-space:nowrap;">{label}</span></div>',
                    unsafe_allow_html=True,
                )
            cols[-1].markdown(
                '<div style="display:flex;align-items:center;justify-content:center;height:100%;">'
                '<span style="font-size:0.75rem;white-space:nowrap;font-weight:600;">Sell Premium</span></div>',
                unsafe_allow_html=True,
            )
            # VRP chart: ATM IV - RV per expiration
            st.plotly_chart(create_vrp_chart(ivd, _rv).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="vrp_exp_chart")
        else: st.info("No RV data")
    else:
        tm = st.radio("View", ["IV", "IV Richness (pp)"], horizontal=True, label_visibility="collapsed", key="vrp_strike_mode")

        se = s.get("selected_expiration", []); se = [] if isinstance(se, str) else se
        raw = [e for e in s.data if e["expiration"] in se] if se else list(s.data)
        if not s.get("show_itm", True): raw = [e for e in raw if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
        if not s.get("show_otm", True): raw = [e for e in raw if (e["type"]=="CALL" and e["strike"]<=s.spot) or (e["type"]=="PUT" and e["strike"]>=s.spot)]
        raw = _filter_strikes_near_atm(raw, s.spot, n=20)
        vk = aggregate_by_strike(raw, s.spot, show_calls=s.show_calls, show_puts=s.show_puts)
        _ssvi_tte = _tte_from_dtes([e.get("dte", 0) for e in s.by_exp_all]) if _ssvi_surf is not None and s.get("by_exp_all") else None
        if tm == "IV":
            if vk:
                st.plotly_chart(create_iv_by_strike(vk, s.spot, rv=_rv, iv_rank=s.get("iv_rank"), ssvi_surface=_ssvi_surf, ssvi_tte=_ssvi_tte).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="iv_by_strike")
            else:
                st.info("No strike data")
        elif tm == "IV Richness (pp)":
            if vk and _ssvi_surf is not None and _ssvi_tte is not None:
                legend_items = [
                    ("#27AE60", "≤ -3"),
                    ("#2ECC71", "-3 to -1"),
                    ("#BDC3C7", "-1 to +1"),
                    ("#F39C12", "+1 to +3"),
                    ("#E74C3C", "≥ +3"),
                ]
                cols = st.columns(len(legend_items) + 2)
                cols[0].markdown(
                    '<div style="display:flex;align-items:center;justify-content:center;height:100%;">'
                    '<span style="font-size:0.75rem;white-space:nowrap;font-weight:600;">Buy Premium</span></div>',
                    unsafe_allow_html=True,
                )
                for ci, (color, label) in zip(cols[1:-1], legend_items):
                    ci.markdown(
                        f'<div style="display:flex;align-items:center;gap:4px;justify-content:center;">'
                        f'<span style="display:inline-block;width:14px;height:14px;border-radius:2px;background:{color};border:1px solid #555;"></span>'
                        f'<span style="font-size:0.75rem;white-space:nowrap;">{label}</span></div>',
                        unsafe_allow_html=True,
                    )
                cols[-1].markdown(
                    '<div style="display:flex;align-items:center;justify-content:center;height:100%;">'
                    '<span style="font-size:0.75rem;white-space:nowrap;font-weight:600;">Sell Premium</span></div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(create_iv_richness_by_strike(vk, s.spot, _ssvi_surf, _ssvi_tte).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="iv_richness_by_strike")
            elif not vk:
                st.info("No strike data")
            else:
                st.info("SSVI surface not calibrated yet")


def render_heatmaps():
    s = st.session_state
    if not s.get("strikes"):
        return

    st.subheader("Heatmaps")

    from charts import create_heatmap, create_vol_surface_2d

    om = st.radio("Select", ["Open Interest", "Volume", "IV Richness (pp)"], horizontal=True, label_visibility="collapsed", key="hm_oi_vol_radio")

    if om == "Open Interest":
        oi_container = st.container()
        with oi_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_oi_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            fl = _filter_strikes_near_atm(fl, s.spot, n=20)
            otm = [e for e in fl if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
            fig = create_heatmap(otm, "open_interest", "Open Interest Heatmap", spot=s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"))
            if fig: st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_oi_chart")

    elif om == "Volume":
        volume_container = st.container()
        with volume_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_v_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            fl = _filter_strikes_near_atm(fl, s.spot, n=20)
            otm = [e for e in fl if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
            fig = create_heatmap(otm, "volume", "Volume Heatmap", spot=s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"))
            if fig: st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_v_chart")

    elif om == "IV Richness (pp)":
        ir_container = st.container()
        with ir_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_ir_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            vd = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            vd = _filter_strikes_near_atm(vd, s.spot, n=20)
            smi = min(e["strike"] for e in vd) if vd else 0; sma = max(e["strike"] for e in vd) if vd else 0
            _ssvi = None
            try:
                _ssvi = s.analytics.get("ssvi_surface")
            except Exception:
                pass
            _ssvi_tte = _tte_from_dtes([e.get("dte", 0) for e in s.by_exp_all]) if _ssvi is not None and s.get("by_exp_all") else None
            if _ssvi is not None and _ssvi_tte is not None:
                fig = create_vol_surface_2d(vd, 0, smi, sma, s.spot, mode="iv_richness", ssvi_surface=_ssvi, ssvi_tte=_ssvi_tte)
                st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_ir_chart")
            else:
                st.info("SSVI surface not calibrated yet")


def _run_ticker_signals(symbol: str) -> dict[str, Any] | None:
    """Self-contained trade-signal analysis for a single ticker.

    Mirrors the pipeline in ``fetch_data`` + ``compute_state`` but keeps all
    state local so the Trade Signals tab can scan every ticker in
    ``ticker_history.json`` without disturbing the main session state.
    Returns ``None`` if data cannot be loaded.
    """
    # Pre-filter the raw chain to selected expirations (Trade Signals scan).
    sel_exp = (
        st.session_state.selected_expirations
        if hasattr(st.session_state, "selected_expirations")
        and st.session_state.selected_expirations
        else None
    )
    core = _fetch_option_chain_core(symbol, selected_expirations=sel_exp)
    if core is None:
        return None
    if core["fetch_error"] is not None:
        # Silent failure (no st.error) — matches the original scan behavior.
        return None

    _sym = core["sym"]
    is_index_symbol = core["is_index_symbol"]
    data, spot = core["data"], core["spot"]
    r, q = core["r"], core["q"]
    etf_analytics = core["etf_analytics"]

    if not data or spot <= 0:
        return None

    # Use filtered data for wall calculations (same 41 strikes as charts)
    # This ensures Support (Put Wall) and Resistance (Call Wall) match between Chart and ATM Order Flow
    selected_expirations = st.session_state.get("selected_expiration", [])
    if isinstance(selected_expirations, str):
        selected_expirations = []
    filtered_data = _get_filtered_data_for_walls(data, selected_expirations)
    analytics = compute_analytics(filtered_data, spot, r=r, q=q, data_full=data)

    # Set filtered data for order flow display with exact 20 strikes below, ATM, 20 above
    # This enables accurate wall calculations and displays correct support/resistance in the ATM order flow grid
    from analytics import get_filtered_strikes_for_analysis
    filtered_flow_data = get_filtered_strikes_for_analysis(filtered_data, spot, n=20)
    analytics["filtered_flow_data"] = filtered_flow_data

    # Update ATM service with walls so the Order Flow grid displays them
    atm_svc = st.session_state.get("atm_option_service")
    if atm_svc:
        atm_svc.set_ticker_walls(_sym, analytics.get("put_wall"), analytics.get("call_wall"))

    if etf_analytics:
        if analytics.get("net_gex", 0) == 0:
            for key in ("net_gex", "total_call_gex", "total_put_gex",
                         "max_positive_gex", "max_negative_gex",
                         "max_positive_gex_strike", "max_negative_gex_strike",
                         "dealer_position"):
                if key in etf_analytics:
                    analytics[key] = etf_analytics[key]
        if analytics.get("ssvi_surface") is None:
            analytics["ssvi_surface"] = etf_analytics.get("ssvi_surface")
            analytics["iv_skew"] = etf_analytics.get("iv_skew")

    rv = run_async(get_20d_rv(st.session_state.client, symbol))
    if rv is None:
        rv = 0.0

    earnings_date = run_async(get_next_earnings_date(st.session_state.client, symbol))

    # Update ATM service with correct expiration for this ticker
    if data and spot > 0:
        expirations = sorted(set(e["expiration"] for e in data))
        if expirations:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc:
                atm_svc.set_ticker_expiration(_sym, expirations[0])
    # Store Put Wall (support) and Call Wall (resistance) for the grid
    atm_svc = st.session_state.get("atm_option_service")
    if atm_svc:
        _put_wall = analytics.get("put_wall")
        _call_wall = analytics.get("call_wall")
        if _put_wall is not None or _call_wall is not None:
            atm_svc.set_ticker_walls(_sym, _put_wall, _call_wall)
        # For index symbols (SPX, RUT, NDX) set the correct spot via
        # the REST option chain parse — the streaming feed only gives
        # us the ETF proxy (SPY, IWM, QQQ) price.
        if is_index_symbol and spot > 0:
            atm_svc.set_ticker_spot(_sym, spot)
            st.session_state.spot_cache[_sym] = spot
        # Populate Call Price / Put Price columns from the REST
        # option-chain ATM marks so the ATM Order Flow grid updates
        # in real time alongside the periodic wall refresh.  This
        # applies to ALL tracked tickers — index symbols need it
        # (they have no own LEVELONE_OPTIONS stream) and equity
        # tickers benefit too as a fallback before WebSocket ticks arrive.
        if atm_svc:
            _atm_k = min(
                (e["strike"] for e in filtered_data),
                key=lambda k: abs(k - spot),
                default=None,
            )
            _call_mark = None
            _put_mark = None
            if _atm_k is not None:
                _atm_exps = sorted(
                    {e["expiration"] for e in filtered_data
                     if e["strike"] == _atm_k}
                )
                if _atm_exps:
                    _front = _atm_exps[0]
                    for e in filtered_data:
                        if e["strike"] == _atm_k and e["expiration"] == _front:
                            if e["type"] == "CALL" and _call_mark is None:
                                _call_mark = e.get("mark")
                            elif e["type"] == "PUT" and _put_mark is None:
                                _put_mark = e.get("mark")
            atm_svc.set_ticker_option_prices(_sym, _call_mark, _put_mark)

    return {"data": data, "spot": spot, "analytics": analytics, "rv": rv, "symbol": _sym, "earnings_date": earnings_date}


_BIAS_EMOJI = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}


def _by_exp_all_from(chain: list[dict], spot: float) -> list[dict]:
    """Aggregate option chain by expiration, keeping only expirations with a
    positive ATM IV.  Shared by the single-ticker view and multi-ticker scan
    so both paths build ``by_exp_all`` identically."""
    return [e for e in aggregate_by_expiration(chain, spot=spot)
            if e.get("atm_iv", 0) > 0]

def _build_signals(
    data: list[dict], spot: float, analytics: dict, rv: float,
    pt: str, stg: str, atm_range: int = 20, by_exp_all: list | None = None,
    selected_expirations: list[str] | None = None,
    dte_min: int = 30, dte_max: int = 45,
    compute_bias: bool = True,
) -> list[str]:
    """Build trade-signal recommendations for a single ticker's option data.

    Shared by the single-ticker Trade Signals view and the multi-ticker scan.
    ``compute_bias`` only controls whether ``assess_market_bias`` is called
    here (the result is passed to ``generate_recommendations``, which
    currently ignores it); the multi-ticker scan computes its own per-ticker
    bias for display separately, so it passes ``False`` to avoid the wasted
    call.
    """
    # Calculate wall zones
    call_wall = analytics.get("call_wall")
    put_wall = analytics.get("put_wall")
    
    # Early return if no wall data
    if not call_wall and not put_wall:
        return []

    # Filter data based on strategy type (single-side strategies only share the
    # same CALL/PUT rule, so collapse the two equivalent branches).
    if stg in ("Long Calls", "Long Puts", "Short Calls", "Short Puts",
               "Call Debit Spread", "Put Debit Spread",
               "Call Credit Spread", "Put Credit Spread"):
        sd2 = [e for e in data if e["type"] == ("CALL" if "Call" in stg else "PUT")]
    else:
        sd2 = data

    # Continue with the rest of the original function
    aks = sorted(set(e["strike"] for e in sd2))
    atm_k = min(aks, key=lambda k: abs(k - spot)) if aks else spot
    sd = [e for e in sd2 if e.get("open_interest", 0) > 0 and (e.get("mark", 0) or 0) > 0 and (e.get("iv", 0) or 0) > 0 and ((e["strike"] == atm_k) or (e["type"] == "CALL" and e["strike"] > spot) or (e["type"] == "PUT" and e["strike"] < spot))]
    
    if atm_range > 0 and sd and spot > 0:
        sk = sorted(set(e["strike"] for e in sd)); ak = min(sk, key=lambda k: abs(k - spot)); ai = sk.index(ak)
        nb = min(atm_range, ai); na = min(atm_range, len(sk) - 1 - ai)
        sd2 = [e for e in sd if sk[ai - nb] <= e["strike"] <= sk[ai + na]]
    else:
        sd2 = sd

    if selected_expirations:
        sd2 = [e for e in sd2 if e["expiration"] in selected_expirations]

    _rec_stg = stg
    if stg == "Long LEAPS":
        _rec_stg = "Long Calls"
    sd2 = [e for e in sd2 if dte_min <= (e.get("days_to_exp", 0) or 0) <= dte_max]

    _ssvi_surf = analytics.get("ssvi_surface")
    if _ssvi_surf is not None and by_exp_all:
        _ir_tte = _tte_from_dtes([e.get("dte", 0) for e in by_exp_all])
    else:
        _ir_tte = None

    bias = assess_market_bias(analytics, spot, iv_rank=st.session_state.get("iv_rank"))[0] if compute_bias else None
    rc = generate_recommendations(sd2, spot, strategy=_rec_stg, all_data=sd2, rv=rv, call_wall=call_wall, put_wall=put_wall, iv_skew=analytics.get("iv_skew"), ssvi_surface=_ssvi_surf, ssvi_tte=_ir_tte, bias=bias, dte_min=dte_min, dte_max=dte_max)
    return rc


def _strategy_side(stg: str) -> str | None:
    """Return the option side a strategy acts on: 'call', 'put', or None (both/neutral)."""
    name = stg.lower()
    if "call" in name:
        return "call"
    if "put" in name:
        return "put"
    return None


def _skew_blocks_strategy(pt: str, stg: str, iv_skew: float | None) -> bool:
    """Whether the IV-skew/strategy-side prefilter should drop a ticker.

    A single-side strategy is skipped when the skew sign disagrees with the
    premium direction (e.g. long calls need positive skew, long puts need
    negative skew).  Returns True when the ticker should be skipped.
    """
    if iv_skew is None:
        return False
    side = _strategy_side(stg)
    if side is None:
        return False
    if pt == "Buy Premium":
        return (side == "call" and iv_skew <= 0) or (side == "put" and iv_skew >= 0)
    return (side == "call" and iv_skew >= 0) or (side == "put" and iv_skew <= 0)


def render_trade_signals():
    s = st.session_state

    st.subheader("Trade Signals")

    signals_container = st.container()
    with signals_container:
        _rv = s.get("underlying_20d_rv", 0.0)
        if _rv <= 0:
            st.info("Load data to see strategy signals")
            return
        if not s.get("strikes"):
            return
        with st.expander("How to read these signals", expanded=False):
            st.markdown("Data &mdash; Each row is a single option (Type + Strike + Expiration). Only **OTM + ATM** options with positive OI and price are used.\n\n**VRP** &mdash; `(IV - RV) x 100`. &gt;+5% option expensive (sell premium). &lt;-2% option cheap (buy premium).\n\n**IV Skew (25D)** &mdash; `Put IV - Call IV`. Positive -> puts expensive. Negative -> calls expensive.\n\n**IV Rank** &mdash; Where the latest daily return ranks in the trailing 52-week range of daily returns. &gt;70 high (sell premium), &lt;30 low (buy premium).\n\n**Market Bias** &mdash; Auto-detected from gamma flip, net GEX, IV skew, OI wall, IV rank.\n\n**Strategies** &mdash; Long/Short Calls/Puts, Spreads, Iron Condor, Butterfly, Straddle, Strangle, Calendar.")

        scan_all = st.checkbox("Scan all tickers in ticker_history.json", value=False, key="scan_all_tickers")

        c1, c2 = st.columns([1, 2])
        with c1:
            pt = st.radio("Premium Type", ["Buy Premium", "Sell Premium"], horizontal=True, key="premium_type")
            stg = st.selectbox("Strategy", ["Long Calls", "Long Puts", "Call Debit Spread", "Put Debit Spread", "Long LEAPS", "Long Straddles", "Long Strangles", "Calendar Spread"] if pt == "Buy Premium" else ["Short Calls", "Short Puts", "Call Credit Spread", "Put Credit Spread", "Iron Condor", "Butterfly", "Broken Wing Butterfly", "Jade Lizard"])
            _dte_col1, _dte_col2 = st.columns(2)
            _leaps = stg == "Long LEAPS"
            with _dte_col1:
                dte_min = st.number_input("DTE Min", min_value=1, max_value=365, value=90 if _leaps else 1, step=1, key="dte_min")
            with _dte_col2:
                dte_max = st.number_input("DTE Max", min_value=1, max_value=365, value=365 if _leaps else 45, step=1, key="dte_max")
            run = st.button("Run scan", key="run_ticker_scan")

        with c2:
            if not scan_all:
                b, br = assess_market_bias(s.analytics, s.spot, iv_rank=s.get("iv_rank"))
                st.markdown(f"**Market Bias:** {_BIAS_EMOJI.get(b, '')} {b} - {br}")
                # Lazily fetch earnings date if not already in session state
                _sym_earn = _normalize_display_symbol(s.get("symbol", ""))
                _ed = s.get("next_earnings_date")
                if _ed is None and _sym_earn and s.get("client"):
                    try:
                        _ed = run_async(get_next_earnings_date(s.client, _sym_earn))
                        st.session_state.next_earnings_date = _ed
                    except Exception:
                        pass
                st.markdown(f"**Next Earnings:** {_ed or 'N/A'}")
                if run:
                    # Full raw chain with all expirations — matches the multi-ticker scan input
                    full_chain = s.get("data") or []
                    rc = _build_signals(
                        full_chain, s.spot, s.analytics, _rv, pt, stg,
                        atm_range=s.get("strikes_atm_range", 20),
                        by_exp_all=_by_exp_all_from(full_chain, s.spot) or s.get("by_exp_all"),
                        selected_expirations=None,
                        dte_min=dte_min, dte_max=dte_max,
                    )
                    st.session_state.single_ticker_signals = rc
                rc = st.session_state.get("single_ticker_signals")
                if rc:
                    for r in rc:
                        st.markdown(f"- {r}")
                else:
                    st.info("Click 'Run scan' to see strategy signals")
            else:
                tickers = list(s.get("ticker_history", []))
                if not tickers:
                    st.info("No tickers in ticker_history.json")
                else:
                    if run:
                        st.session_state.ticker_scan_empty = False
                        results = {}
                        scan_analytics = {}
                        for sym in tickers:
                            with st.spinner(f"Analyzing {sym}..."):
                                res = _run_ticker_signals(sym)
                            if res is None:
                                continue
                            scan_analytics[sym] = res
                            if _skew_blocks_strategy(pt, stg, res["analytics"].get("iv_skew")):
                                continue
                            rc = _build_signals(
                                res["data"], res["spot"], res["analytics"], res["rv"], pt, stg,
                                atm_range=s.get("strikes_atm_range", 20),
                                by_exp_all=_by_exp_all_from(res["data"], res["spot"]),
                                dte_min=dte_min, dte_max=dte_max,
                                compute_bias=False,
                            )
                            _no_sig = "No strong signals" in " ".join(rc)
                            if rc and not _no_sig:
                                results[sym] = rc
                            # Store earnings date for display
                            _scan_earnings = st.session_state.get("_scan_earnings", {})
                            if res.get("earnings_date"):
                                _scan_earnings[sym] = res["earnings_date"]
                            st.session_state._scan_earnings = _scan_earnings
                        st.session_state.ticker_scan_results = results
                        st.session_state.ticker_scan_pt = pt
                        st.session_state.ticker_scan_stg = stg
                        st.session_state.ticker_scan_empty = (len(results) == 0)
                        st.session_state.ticker_scan_analytics = scan_analytics

                    # Display per-ticker Market Bias for the latest multi-ticker scan
                    _scan_analytics = st.session_state.get("ticker_scan_analytics")
                    if _scan_analytics:
                        _bias_lines = []
                        for _sym, _res in _scan_analytics.items():
                            _b, _ = assess_market_bias(_res["analytics"], _res["spot"], iv_rank=_res["analytics"].get("iv_rank"))
                            _bias_lines.append(f"{_sym}: {_BIAS_EMOJI.get(_b, '')} {_b}")
                        if _bias_lines:
                            st.markdown("**Market Bias:** " + " | ".join(_bias_lines))
                            st.markdown("")

                    results = st.session_state.get("ticker_scan_results")
                    if results:
                        shown_pt = st.session_state.get("ticker_scan_pt")
                        shown_stg = st.session_state.get("ticker_scan_stg")
                        st.markdown(f"**Scan results — {shown_pt} / {shown_stg}**")
                        for sym, recs in results.items():
                            _ed = st.session_state.get("_scan_earnings", {}).get(sym, "")
                            _ed_str = f" — Earnings: {_ed}" if _ed else ""
                            st.markdown(f"**{sym}{_ed_str}**")
                            for r in recs:
                                st.markdown(f"- {r}")
                    elif st.session_state.get("ticker_scan_empty"):
                        st.info("No signals found across tickers")


def render_options_data():
    """Renders the Options Data table.
    
    This is a plain function (not a fragment) because it is called from
    inside ``render_tabs_frag`` which is already a fragment.  Nesting a
    ``run_every`` fragment inside another ``run_every`` fragment causes
    the inner fragment to be destroyed / recreated on every parent
    re-run, preventing its content from appearing.
    """
    
    if st.session_state.get("data"):
        try:
            render_table()
        except Exception as e:
            st.error(f"Error loading options table: {e}")


def _get_filtered_data_for_walls(data: list[dict], selected_expirations: list[str] | None) -> list[dict]:
    """Get filtered data for wall calculations, matching charts behavior.
    
    Includes strikes at and around ATM (nearly 4 expirations, 41 strikes total),
    which is what the walls use.
    """
    # Step 1: Filter to expirations with non-zero volume (like charts.py:464)
    active_exps = set(e["expiration"] for e in data if e.get("open_interest", 0) > 0)
    
    # Step 2: Use UI-selected expirations if available, otherwise use up to 4 high volume expirations
    if selected_expirations:
        target_exps = [e for e in selected_expirations if e in active_exps]
    else:
        target_exps = sorted(active_exps)[:4]  # Max 4 expirations like charts
    
    # Step 3: Filter data to target expirations with non-zero volume
    filtered = [e for e in data if e["expiration"] in target_exps]
    
    if not filtered:
        return data
    
    # Step 4: Filter to strikes near ATM (±20 strikes, including ATM)
    # like get_filtered_strikes_for_analysis with n=20 (40 strikes total)
    strike_set = sorted(set(e["strike"] for e in filtered))
    if not strike_set:
        return data
    
    # Get spot from filtered data (floor to nearest available strike)
    spot = sorted(strike_set)[len(strike_set) // 2]
    
    # Apply the _filter_strikes_near_atm filter to get all required strikes
    return _filter_strikes_near_atm(filtered, spot, n=20)


def render_table():
    st.markdown("#### Options Data")
    sel_exp = st.session_state.get("selected_expiration", [])
    if isinstance(sel_exp, str):
        sel_exp = []
    raw_data = st.session_state.get("data", [])
    if sel_exp:
        raw_data = [e for e in raw_data if e["expiration"] in sel_exp]
    strikes = aggregate_by_strike(raw_data, st.session_state.spot)
    if not strikes:
        st.info("No data to display")
        return

    rows = []
    for s in strikes:
        rows.append({
            "Strike": s["strike"],
            "Call GEX": s["call_gex"],
            "Put GEX": s["put_gex"],
            "Net GEX": s["net_gex"],
            "Call Gamma": s["call_gamma"],
            "Put Gamma": s["put_gamma"],
            "Call OI": s["call_oi"],
            "Put OI": s["put_oi"],
            "Call Vol": s["call_volume"],
            "Put Vol": s["put_volume"],
            "Call Price": s.get("call_mark", 0),
            "Put Price": s.get("put_mark", 0),
            "Call Delta": s.get("call_delta", 0),
            "Put Delta": s.get("put_delta", 0),
            "Expirations": s["num_expirations"],
            "IV": s.get("call_iv", 0) if s["strike"] >= st.session_state.spot else s.get("put_iv", 0),
        })

    df = pd.DataFrame(rows)
    spot = st.session_state.spot

    ssvi_surf = None
    try:
        ssvi_surf = st.session_state.analytics.get("ssvi_surface")
    except Exception:
        pass
    tte = None
    if ssvi_surf is not None and st.session_state.get("by_exp_all"):
        dtes = [e.get("dte", 0) for e in st.session_state.by_exp_all if e.get("dte", 0) > 0]
        tte = _tte_from_dtes(dtes)
    if ssvi_surf is not None and tte is not None:
        df["SSVI IV"] = [ssvi_surf.iv(float(k), float(tte)) for k in df["Strike"]]
        df["IV (pp)"] = df["IV"] - df["SSVI IV"]
    else:
        df["SSVI IV"] = 0.0
        df["IV (pp)"] = 0.0

    df = df[["Strike","Call GEX","Put GEX","Net GEX","Call Gamma","Put Gamma","Call OI","Put OI","Call Vol","Put Vol","Call Price","Put Price","Call Delta","Put Delta","Expirations","IV","SSVI IV","IV (pp)"]]

    max_pin_idx = (df["Call OI"] + df["Put OI"]).idxmax()
    call_wall = st.session_state.analytics.get("call_wall")
    call_wall_idx = df[df["Strike"] == call_wall].index.tolist()
    put_wall = st.session_state.analytics.get("put_wall")
    put_wall_idx = df[df["Strike"] == put_wall].index.tolist()

    atm_bg = "#e0e0e0"
    max_pain_bg = "#ffcccc"
    call_wall_bg = "#ffcccc"
    put_wall_bg = "#ccffcc"
    atm_strike = df.iloc[(df["Strike"] - spot).abs().argsort()[:1]]["Strike"].values[0]

    def highlight_atm(row):
        is_atm = row["Strike"] == atm_strike
        styles = [f"background-color: {atm_bg}"] * len(row) if is_atm else [""] * len(row)
        if row.name == max_pin_idx:
            col_idx = list(row.index)
            if "Call OI" in col_idx:
                styles[col_idx.index("Call OI")] = f"background-color: {max_pain_bg}"
            if "Put OI" in col_idx:
                styles[col_idx.index("Put OI")] = f"background-color: {max_pain_bg}"
        if row.name in call_wall_idx:
            col_idx = list(row.index)
            if "Call GEX" in col_idx:
                styles[col_idx.index("Call GEX")] = f"background-color: {call_wall_bg}"
        if row.name in put_wall_idx:
            col_idx = list(row.index)
            if "Put GEX" in col_idx:
                styles[col_idx.index("Put GEX")] = f"background-color: {put_wall_bg}"
        return styles

    styled = df.style.apply(highlight_atm, axis=1).format({
        "Strike": "${:.2f}",
        "VRP": "{:.2%}",
        "Call GEX": "${:,.0f}",
        "Put GEX": "${:,.0f}",
        "Net GEX": "${:,.0f}",
        "Call OI": "{:,.0f}",
        "Put OI": "{:,.0f}",
        "Call Vol": "{:,.0f}",
        "Put Vol": "{:,.0f}",
        "Call Gamma": "{:.4f}",
        "Put Gamma": "{:.4f}",
        "IV": "{:.2%}",
        "SSVI IV": "{:.2%}",
        "IV (pp)": "{:.2%}",
        "Call Price": "${:.2f}",
        "Put Price": "${:.2f}",
        "Call Delta": "{:.4f}",
        "Put Delta": "{:.4f}",
    })

    st.markdown("""
<style>
div[data-testid="stDataFrame"] { overflow-x: auto; max-width: 100%; }
div[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
</style>
""", unsafe_allow_html=True)
    st.dataframe(styled, height=400)






@st.fragment(run_every=60)
def render_news_frag():
    """Render the Live News tab — headlines from Yahoo Finance RSS for
    all tracked tickers.  The fragment auto-refreshes every 60 s to pick
    up newly polled articles."""
    s = st.session_state
    news_svc = s.get("news_service")
    if news_svc is None or not news_svc.is_running:
        st.info("News service not initialized.")
        return

    tickers = s.get("ticker_history", [])
    if not tickers:
        st.info("No tickers tracked yet.")
        return

    # Force a poll on first render so there is something to show
    if s.get("_news_first_poll", True):
        s["_news_first_poll"] = False
        loop = _ensure_async_loop()
        asyncio.run_coroutine_threadsafe(news_svc.poll(tickers), loop)

    news = news_svc.get_all_news()

    if not news:
        st.caption("No news headlines yet — next poll in ~5 min.")
        return

    st.markdown(
        f"<div style='margin-bottom:8px;color:gray;font-size:0.85rem'>"
        f"{len(news)} recent headlines"
        f"</div>",
        unsafe_allow_html=True,
    )

    for item in news:
        title = item.get("title", "")
        link = item.get("link", "")
        published = item.get("published", "")
        st.markdown(
            f"[{title}]({link})  "
            f"<span style='color:gray;font-size:0.8rem'>{published}</span>",
            unsafe_allow_html=True,
        )


def render_tabs_frag():
    # Create the tabs with updated order
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "Market Structure", "Positioning", "Volatility", "Heatmaps",
        "Options Data", "Candlesticks", "Trade Signals", "Order Flow", "Live News"
    ])
    
    # Render each tab
    with tab1:
        render_market_structure()
    
    with tab2:
        render_positioning()
    
    with tab3:
        render_volatility()
    
    with tab4:
        render_heatmaps()
    
    with tab5:
        render_options_data()
    
    with tab6:
        render_candlesticks_frag()
    
    with tab7:
        render_trade_signals()
    
    with tab8:
        render_flow_frag()
    
    with tab9:
        render_news_frag()


def main():
    if _CONFIG_ERRORS:
        st.error("## Configuration Required")
        for _err in _CONFIG_ERRORS:
            st.markdown(f"- {_err}")
        st.markdown("")
        st.markdown(
            "Copy `config.toml.example` to `config.toml` (or set the environment "
            "variables) and re-run. See the **Setup** section of the README."
        )
        return

    render_sidebar()

    main_section = st.container()
    with main_section:
        st.markdown(
            f"# {st.session_state.symbol} — Gamma Exposure Analysis"
        )

        if st.session_state.get("data"):
            render_metrics_frag()
            render_tabs_frag()
        else:
            st.info("Enter a stock ticker in the sidebar and click Refresh to begin analysis")
            st.markdown(r"""
            ### Quick Start
            1. Enter a ticker (e.g., SPY, AAPL, TSLA, \$SPX, \$RUT) in the sidebar
            2. Click **Refresh** to load the option chain (works best during regular US market hours)
            3. Explore GEX visualizations and analytics
            """)
            st.markdown("### Note")
            st.caption("The Candlesticks tab renders interactive OHLCV charts with streaming live ticks — it activates once you Refresh a ticker on the main page (see charts.py and chart_component.py for the indicator implementations).")


if __name__ == "__main__":
    main()
