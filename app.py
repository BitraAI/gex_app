import asyncio
import json
import os
import threading
from datetime import datetime, date
from typing import Any, Optional

# Persistent event loop in a background thread (avoids Python 3.12 "Event loop is closed")
_ASYNC_LOOP: asyncio.AbstractEventLoop | None = None
_ASYNC_LOOP_THREAD: threading.Thread | None = None
_ASYNC_LOOP_LOCK = threading.Lock()


def _run_async_loop_forever(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def _ensure_async_loop() -> asyncio.AbstractEventLoop:
    global _ASYNC_LOOP, _ASYNC_LOOP_THREAD
    with _ASYNC_LOOP_LOCK:
        if _ASYNC_LOOP is None or _ASYNC_LOOP.is_closed():
            _ASYNC_LOOP = asyncio.new_event_loop()
            _ASYNC_LOOP_THREAD = threading.Thread(
                target=_run_async_loop_forever, args=(_ASYNC_LOOP,), daemon=True,
            )
            _ASYNC_LOOP_THREAD.start()
    return _ASYNC_LOOP

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
import client as client_mod
from client import create_client, fetch_option_chain, get_yield, get_interest_rate, get_20d_rv, get_next_earnings_date, fetch_candles_smart, load_candle_cache, fetch_price_history_daily, save_candle_cache
from streaming_service import StreamingService
from option_streaming_service import AtmOptionVolumeService
from chart_component import render_chart
from calculations import (
    aggregate_by_strike,
    aggregate_by_expiration,
    compute_totals,
    parse_option_chain,
    build_greeks_lookup,
)
from analytics import compute_analytics
from signals import score_options, generate_recommendations, assess_market_bias
from telegram_notifier import notify_alerts, diff_alerts
from charts import (
    DARK_TEMPLATE,
    LIGHT_TEMPLATE,
    DARK_CSS,
    LIGHT_CSS,
    STYLE,
    INDICATORS,
    _sma,
    _ema,
    _trend,
    create_gex_histogram,
    create_gex_by_expiration,
    create_oi_by_strike,
    create_heatmap,
    create_gamma_surface,
    create_dealer_gamma_curve,
    create_atm_iv_histogram,
    create_vrp_chart,
    create_vol_surface_2d,
    create_vrp_by_strike,
    create_iv_by_strike,
)
from chart_component import render_chart

st.set_page_config(
    page_title="GammaEx - GEX Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(STYLE, unsafe_allow_html=True)

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

_SESSION_DEFAULTS = {
    "theme": "dark",
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
}

TICKER_HISTORY_FILE = os.path.expanduser("~/.local/share/gex_app/ticker_history.json")


def _load_ticker_history() -> list[str]:
    try:
        with open(TICKER_HISTORY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_ticker_history(history: list[str]):
    os.makedirs(os.path.dirname(TICKER_HISTORY_FILE), exist_ok=True)
    with open(TICKER_HISTORY_FILE, "w") as f:
        json.dump(history, f)


for k, v in _SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.ticker_history:
    st.session_state.ticker_history = _load_ticker_history()

st.markdown(DARK_CSS if st.session_state.theme == "dark" else LIGHT_CSS, unsafe_allow_html=True)

# Replace streaming service if it was created with old code (no shared loop)
if st.session_state.get("client") is not None:
    loop = _ensure_async_loop()
    old = st.session_state.get("streaming_service")
    if old is None or getattr(old, '_loop', None) is None:
        if old is not None:
            old.stop()
        st.session_state.streaming_service = StreamingService(st.session_state.client, loop)
    atm_opt = st.session_state.get("atm_option_service")
    if atm_opt is None or getattr(atm_opt, '_loop', None) is None:
        if atm_opt is not None:
            atm_opt.stop()
        st.session_state.atm_option_service = AtmOptionVolumeService(st.session_state.client, loop)


async def _create_client_async():
    return create_client()

def init_client():
    loop = _ensure_async_loop()
    if st.session_state.get("client") is None:
        try:
            fut = asyncio.run_coroutine_threadsafe(
                _create_client_async(), loop,
            )
            st.session_state.client = fut.result(timeout=30)
        except Exception as e:
            st.error(f"Failed to create Schwab client: {e}")
            return False
    old = st.session_state.get("streaming_service")
    if old is None or getattr(old, '_loop', None) is None:
        if old is not None:
            old.stop()
        st.session_state.streaming_service = StreamingService(st.session_state.client, loop)
    atm_opt = st.session_state.get("atm_option_service")
    if atm_opt is None or getattr(atm_opt, '_loop', None) is None:
        if atm_opt is not None:
            atm_opt.stop()
        st.session_state.atm_option_service = AtmOptionVolumeService(st.session_state.client, loop)
    return True


def run_async(coro):
    loop = _ensure_async_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result()


def fetch_data(symbol: str) -> bool:
    if not init_client():
        return False
    try:
        raw = run_async(
            fetch_option_chain(
                st.session_state.client, symbol, strike_count=75, include_quotes=True,
            )
        )
    except Exception as e:
        st.error(f"API Error: {e}")
        return False

    r = run_async(get_interest_rate(st.session_state.client))
    q = run_async(get_yield(st.session_state.client, symbol))

    fallback_greeks = None
    sym_map = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}
    if symbol.upper() in sym_map:
        try:
            fb_raw = run_async(
                fetch_option_chain(
                    st.session_state.client, sym_map[symbol.upper()], strike_count=75, include_quotes=True,
                )
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
        except Exception:
            pass

    data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
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
    if symbol not in st.session_state.ticker_history:
        st.session_state.ticker_history.insert(0, symbol)
        st.session_state.ticker_history = st.session_state.ticker_history[:10]
        _save_ticker_history(st.session_state.ticker_history)
    st.session_state.last_refresh = datetime.now()
    st.session_state.underlying_20d_rv = run_async(get_20d_rv(st.session_state.client, symbol))
    st.session_state.next_earnings_date = run_async(get_next_earnings_date(st.session_state.client, symbol))
    prefetch_daily_candles(symbol)
    apply_filters()
    compute_state()
    st.session_state.iv_rank = compute_iv_rank(
        symbol, atm_iv=st.session_state.analytics.get("atm_iv")
    )
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
    analytics = compute_analytics(data, spot, show_calls, show_puts, data_full=st.session_state.data)

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


def render_metrics(analytics: dict, spot: float, last_refresh: Optional[datetime], rv: float = 0.0, iv_rank: float | None = None):
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(
        f'<div class="gex-metric"><div class="label">Current Price</div>'
        f'<div class="value neutral">${spot:.2f}</div></div>',
        unsafe_allow_html=True,
    )
    net = analytics.get('net_gex', 0)
    net_cls = "positive" if net >= 0 else "negative"
    col2.markdown(
        f'<div class="gex-metric"><div class="label">Net GEX</div>'
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
        f'<div class="gex-metric"><div class="label">Put Wall</div>'
        f'<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    cw = analytics.get('call_wall')
    col2.markdown(
        f'<div class="gex-metric"><div class="label">Call Wall</div>'
        f'<div class="value neutral">${cw:.2f}</div></div>' if cw else
        f'<div class="gex-metric"><div class="label">Call Wall</div>'
        f'<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )
    gf = analytics.get('gamma_flip')
    col3.markdown(
        f'<div class="gex-metric"><div class="label">Gamma Flip</div>'
        f'<div class="value neutral">${gf:.2f}</div></div>' if gf else
        f'<div class="gex-metric"><div class="label">Gamma Flip</div>'
        f'<div class="value neutral">N/A</div></div>',
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
        f'<div class="gex-metric"><div class="label">Max Pain</div>'
        f'<div class="value neutral">N/A</div></div>',
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
            f'<div class="gex-metric"><div class="label">IV Skew (25Δ)</div>'
            f'<div class="value neutral">N/A</div></div>',
            unsafe_allow_html=True,
        )
    col3.markdown(
        f'<div class="gex-metric"><div class="label">RV (20d)</div>'
        f'<div class="value neutral">{rv*100:.2f}%</div></div>' if rv > 0 else
        f'<div class="gex-metric"><div class="label">RV (20d)</div>'
        f'<div class="value neutral">N/A</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    if iv_rank is not None:
        rank_cls = "negative" if iv_rank > 50 else "positive"
        c1.markdown(
            f'<div class="gex-metric"><div class="label">IV Rank</div>'
            f'<div class="value {rank_cls}">{iv_rank:.2f}%</div></div>',
            unsafe_allow_html=True,
        )
    else:
        c1.markdown(
            f'<div class="gex-metric"><div class="label">IV Rank</div>'
            f'<div class="value neutral">N/A</div></div>',
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
            f'<div class="gex-metric"><div class="label">Exp. Move</div>'
            f'<div class="value neutral">N/A</div></div>',
            unsafe_allow_html=True,
        )
    lr = last_refresh.strftime("%H:%M:%S") if last_refresh else "—"
    c3.markdown(
        f'<div style="text-align:right;color:gray;font-size:0.85rem">Last Refresh: {lr}</div>',
        unsafe_allow_html=True,
    )


def check_alerts(analytics: dict, spot: float):
    prev = st.session_state.prev_alerts_state
    new_alerts, next_state = diff_alerts(prev, analytics, spot)
    st.session_state.prev_alerts_state = next_state

    if new_alerts:
        st.session_state.alerts = new_alerts + st.session_state.alerts[:20]
        notify_alerts(
            new_alerts,
            symbol=st.session_state.get("symbol"),
            spot=spot,
        )


CANDLE_TTL_SECS = 600  # 10 minutes


def _candles_need_refresh(symbol: str, tf: str) -> bool:
    last = st.session_state.candle_last_fetch.get(f"{symbol}|{tf}")
    if last is None:
        return True
    from datetime import datetime, timezone
    return (datetime.now(timezone.utc) - last).total_seconds() > CANDLE_TTL_SECS


def refresh_candles(symbol: str, tf: str):
    """Fetch candles via Parquet cache + API, store in session state."""
    from datetime import datetime, timezone
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
    from datetime import datetime, timezone
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


def compute_iv_rank(symbol: str, atm_iv: float | None = None) -> float | None:
    df = load_candle_cache(symbol, "1d")
    if df.empty or len(df) < 2:
        try:
            raw = run_async(fetch_price_history_daily(st.session_state.client, symbol, years=1))
            if raw:
                df = pd.DataFrame(raw)
                save_candle_cache(df, symbol, "1d")
        except Exception:
            return None
    if df.empty or len(df) < 2:
        return None
    df = df.sort_values("datetime")
    closes = df["close"].tolist()

    returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes))]
    rv_values = []
    for i in range(19, len(returns)):
        rv_20d = np.std(returns[i-19:i+1]) * (252 ** 0.5)
        rv_values.append(rv_20d)

    if not rv_values:
        return None

    recent_252 = rv_values[-252:]

    if atm_iv is not None and atm_iv > 0:
        current = atm_iv
    else:
        current = rv_values[-1]

    lo = min(recent_252)
    hi = max(recent_252)
    if hi == lo:
        return 50.0
    return round((current - lo) / (hi - lo) * 100, 2)


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
                    st.rerun()
            symbol = st.session_state.get("symbol", "")
        else:
            symbol = choice

        refresh = st.button("Refresh", type="primary", use_container_width=True)
        if refresh and symbol:
            with st.spinner(f"Loading {symbol} option chain..."):
                fetch_data(symbol)

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

        st.markdown("### Theme")
        apply_filters()
        compute_state()
        theme = st.selectbox(
            "Theme", ["dark", "light"],
            index=0 if st.session_state.theme == "dark" else 1,
            label_visibility="collapsed",
        )
        st.session_state.theme = theme


def render_indicators_panel():
    with st.expander("Indicators", expanded=False):
        st.markdown("## Indicators")
        st.info("Indicator code preserved - available for future enhancements")


TIMEFRAMES = {
    "1m": "1min", "2m": "2min", "5m": "5min", "15m": "15min",
    "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W", "1M": "1ME",
}


def _build_candlestick_df(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample OHLCV DataFrame (ms index) to a target rule and return
    a DataFrame with 'datetime', 'open', 'high', 'low', 'close' columns."""
    idx = pd.to_datetime(df.index, unit="ms", errors="coerce")
    resampled = df.copy()
    resampled.index = idx
    resampled = resampled.resample(rule).agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna()
    return resampled.reset_index().rename(columns={"index": "datetime"})


@st.fragment(run_every=1)
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
            indicator_options = ["SMA 20", "SMA 50", "EMA 20", "EMA 50 Squeeze", "EMA 200", "Volume Profile", "Anchored VWAP", "Trend", "Volume", "ATM_Option_Flow", "Andean Osc", "IV Skew (25Δ)"]
            selected_indicators = st.multiselect("Indicators", indicator_options, default=[], label_visibility="collapsed")
        
        from client import load_candle_cache

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

        # --- Start streaming services if not running ---
        # Map index symbols (SPX, RUT, NDX) to their ETF equivalents
        # because Schwab LEVELONE_EQUITIES does not support index symbols.
        _STREAM_SYMBOL_MAP = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}
        stream_symbol = _STREAM_SYMBOL_MAP.get(symbol.upper(), symbol)
        svc = st.session_state.get("streaming_service")
        if svc:
            if not svc.is_running:
                svc.start(stream_symbol)
            elif svc.symbol != stream_symbol:
                svc.stop()
                svc.start(stream_symbol)

        # Feed spot from equity stream to ATM option service
        svc_spot = st.session_state.get("streaming_service")
        if svc_spot and svc_spot.last_price:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc:
                atm_svc.update_spot(svc_spot.last_price)

        # Start ATM option streaming on the shared equity StreamClient
        if "ATM_Option_Flow" in selected_indicators:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc:
                by_exp_all = s.get("by_exp_all", [])
                if by_exp_all:
                    front_exp = by_exp_all[0]["expiration"]
                else:
                    from datetime import timedelta
                    front_exp = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                if svc_spot and svc_spot.last_price:
                    atm_svc.update_spot(svc_spot.last_price)
                eq_sc = svc_spot.get_stream_client() if svc_spot else None
                if eq_sc is not None and (not atm_svc.is_running or atm_svc.symbol != symbol):
                    atm_svc.register(eq_sc, symbol, front_exp)

        # Normalize chart_df["datetime"] to int64 for merging
        chart_df["datetime"] = chart_df["datetime"].astype("int64")

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
        _merge_streaming = svc and svc.is_running and svc.symbol == stream_symbol and symbol.upper() == stream_symbol
        if _merge_streaming:
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
                            from zoneinfo import ZoneInfo
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
                            from zoneinfo import ZoneInfo
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

        # Merge ATM option volume into chart df when available
        # atm_df index is int64 milliseconds — same unit as chart_df["datetime"].
        # Warnings are shown near the chart (see ATM Option Flow block below);
        # this block only attaches ATM volume columns to chart_df.
        if "ATM_Option_Flow" in selected_indicators:
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
                                from zoneinfo import ZoneInfo
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
                except Exception as e:
                    pass

        # Persist in session state. chart_df["datetime"] stays as int64 ms because
        # chart_component.render_chart converts it to UNIX-seconds time keys for
        # lightweight-charts (with the proper EST offset).
        s.candlestick_data = chart_df
        s.candlestick_label = chart_label

        # --- Render lightweight-charts streaming candlestick ---
        is_dark = getattr(s, 'theme', 'dark') == 'dark'
        df = s.candlestick_data

        # Build the candle list for chart_component.render_chart. Keep datetime as
        # int64 ms so the streaming 1-second bars are uniquely keyed on time.
        candles_payload = []
        for _, row in df.iterrows():
            c = {
                "datetime": int(row["datetime"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
            if "volume" in df.columns:
                vol_val = row.get("volume")
                if pd.notna(vol_val):
                    vol_val = float(vol_val)
                    if vol_val == vol_val:  # NaN guard
                        c["volume"] = vol_val
            if "buy_vol" in df.columns and pd.notna(row.get("buy_vol")):
                c["buy_vol"] = int(row["buy_vol"])
            if "sell_vol" in df.columns and pd.notna(row.get("sell_vol")):
                c["sell_vol"] = int(row["sell_vol"])
            for atm_col in ["call_buy_vol", "call_sell_vol", "put_buy_vol", "put_sell_vol",
                            "total_buy_vol", "total_sell_vol"]:
                if atm_col in df.columns and pd.notna(row.get(atm_col)):
                    c[atm_col] = int(row[atm_col])
            candles_payload.append(c)

        # Use unique chart id for the current ticker to preserve Y-axis state
        chart_id = s.get("symbol", "SPY")

        last_close = float(df["close"].iloc[-1]) if not df.empty else None

        # Call/Put wall horizontal lines (price levels from analytics)
        _analytics = s.get("analytics") or {}
        _cw = _analytics.get("call_wall")
        _pw = _analytics.get("put_wall")

        # Websocket streaming status — overlaid on the candlesticks chart.
        # The equity StreamClient feeds the live candles (and, when
        # ATM_Option_Flow is selected, the option-trade aggregation), so its
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
            if "ATM_Option_Flow" in selected_indicators and _atm_svc is not None:
                if _atm_svc.is_running and _atm_svc.has_data:
                    _n = _atm_svc.ticks_received
                    _msg += f" · { _n } option tick{'s' if _n != 1 else ''}"
                elif _atm_svc.is_running and not _atm_svc.has_data:
                    _msg += f" · waiting for option trades..."
                elif not _atm_svc.is_running:
                    _msg += " · option flow not subscribed"
            _status = {"text": _msg, "level": "success"}
        elif _eq_svc.is_connected and not _eq_svc.has_data:
            _status = {"text": f"Connected · waiting for {stream_symbol} trades...", "level": "info"}
        elif not _eq_svc.is_connected:
            _err = getattr(_eq_svc, "last_error", None)
            _msg = f"WebSocket disconnected"
            if _err:
                _msg += f": {_err}"
            _status = {"text": _msg, "level": "warning"}

        if candles_payload:
            _iv_skew_hist = s.get("iv_skew_history") or []
            if "IV Skew (25Δ)" in selected_indicators and _analytics.get("iv_skew") is not None:
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
            render_chart(
                candles_payload,
                indicators=selected_indicators,
                call_wall=_cw,
                put_wall=_pw,
                is_dark=is_dark,
                last_close=last_close,
                status=_status,
                symbol=symbol,
                iv_skew_history=_iv_skew_hist,
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
    live = None
    svc = s.get("streaming_service")
    if svc:
        live = svc.last_price
    spot = live if (live and live > 0) else s.spot
    metrics_container = st.container()
    with metrics_container:
        render_metrics(s.analytics, spot, s.last_refresh, rv=s.get("underlying_20d_rv", 0.0), iv_rank=s.get("iv_rank"))


@st.fragment(run_every=10)
def render_market_structure_frag():
    s = st.session_state; d = getattr(s, 'theme', 'dark') == "dark"
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
            fig = create_gex_histogram(strikes, s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), gamma_flip=s.analytics.get("gamma_flip"), is_dark=d)
            fig.update_layout(dragmode="zoom"); st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_histogram")
        elif ms_view == "GEX by Expiration":
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="gex_exp_slider")
            fig = create_gex_by_expiration(s.by_exp_all, max_exps=mx, is_dark=d); fig.update_layout(dragmode="zoom")
            st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_by_exp")
        elif ms_view == "Gamma Surface":
            fig = create_gamma_surface(s.filtered_data, is_dark=d); st.plotly_chart(fig, width='stretch', key="gamma_surface")
        else:
            dm = st.radio("Select", ["GEX", "VEX", "CEX"], horizontal=True, label_visibility="collapsed")
            fig = create_dealer_gamma_curve(strikes, s.spot, mode=dm.lower(), gamma_flip=s.analytics.get("gamma_flip"), is_dark=d, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), vex_magnet=s.analytics.get("vex_magnet"), vex_repellent=s.analytics.get("vex_repellent"))
            st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="dealer_curve_chart")


@st.fragment(run_every=30)
def render_positioning_frag():
    s = st.session_state; d = getattr(s, 'theme', 'dark') == "dark"
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
    
    positioning_data = aggregate_by_strike(
        raw_data, s.spot, show_calls=s.show_calls, show_puts=s.show_puts
    )
    if not positioning_data:
        return

    if selected_view_type == "Open Interest":
        with st.container():
            fig = create_oi_by_strike(
                positioning_data, s.spot, mode="oi", is_dark=d
            )
            fig.update_layout(dragmode="zoom")
            st.plotly_chart(
                fig, config={"scrollZoom": True}, width="stretch", key="oi_chart"
            )
    elif selected_view_type == "Volume":
        with st.container():
            fig = create_oi_by_strike(
                positioning_data, s.spot, mode="volume", is_dark=d
            )
            fig.update_layout(dragmode="zoom")
            st.plotly_chart(
                fig, config={"scrollZoom": True}, width="stretch", key="volume_chart"
            )


@st.fragment(run_every=15)
def render_volatility_frag():
    s = st.session_state; d = getattr(s, 'theme', 'dark') == "dark"
    if not s.get("strikes"):
        return

    st.subheader("Volatility")

    volatility_container = st.container()
    with volatility_container:
        vol_view = st.radio(
            "View",
            ["IV by Strike", "IV by Expiration"],
            horizontal=True, label_visibility="collapsed",
            key="vol_view_radio",
        )

        if vol_view == "IV by Strike":
            tm = st.radio("View", ["IV Rank", "VRP", "VRP Ratio"], horizontal=True, label_visibility="collapsed", key="vrp_strike_mode")
        else:
            mo = st.radio("View", ["ATM IV", "VRP", "VRP Ratio"], horizontal=True, label_visibility="collapsed", key="iv_exp_mode")

        _rv = s.get("underlying_20d_rv", 0.0)
        if vol_view == "IV by Strike":
            se = s.get("selected_expiration", []); se = [] if isinstance(se, str) else se
            raw = [e for e in s.data if e["expiration"] in se] if se else list(s.data)
            if not s.get("show_itm", True): raw = [e for e in raw if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
            if not s.get("show_otm", True): raw = [e for e in raw if (e["type"]=="CALL" and e["strike"]<=s.spot) or (e["type"]=="PUT" and e["strike"]>=s.spot)]
            vk = aggregate_by_strike(raw, s.spot, show_calls=s.show_calls, show_puts=s.show_puts)
            if tm == "IV":
                if vk: st.plotly_chart(create_iv_by_strike(vk, s.spot, is_dark=d, rv=_rv).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="iv_by_strike_tab6")
                else: st.info("No strike data")
            elif tm == "IV Rank":
                _iv_rank = s.get("iv_rank")
                if vk and _iv_rank is not None:
                    st.plotly_chart(create_iv_by_strike(vk, s.spot, is_dark=d, rv=_rv, iv_rank=_iv_rank).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="iv_rank_by_strike")
                elif vk:
                    st.info("IV Rank not available yet")
                else:
                    st.info("No strike data")
            elif _rv > 0 and vk:
                st.plotly_chart(create_vrp_by_strike(vk, s.spot, _rv, is_dark=d, mode="vrp" if tm=="VRP" else "vrp_ratio").update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="vrp_by_strike")
            else: st.info("No RV data")
        else:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="iv_exp_slider")
            ivd = s.by_exp_all[:mx]
            if mo == "ATM IV": st.plotly_chart(create_atm_iv_histogram(ivd, is_dark=d, rv=_rv), config={"scrollZoom": True}, width='stretch', key="atm_iv_chart")
            elif _rv > 0: st.plotly_chart(create_vrp_chart(ivd, _rv, is_dark=d, mode="vrp_ratio" if mo=="VRP Ratio" else "vrp"), config={"scrollZoom": True}, width='stretch', key="vrp_chart")
            else: st.info("No RV data")


@st.fragment(run_every=20)
def render_heatmaps_frag():
    s = st.session_state; d = getattr(s, 'theme', 'dark') == "dark"
    if not s.get("strikes"):
        return

    st.subheader("Heatmaps")

    om = st.radio("Select", ["Open Interest", "Volume", "VRP", "VRP Ratio"], horizontal=True, label_visibility="collapsed", key="hm_oi_vol_radio")

    if om == "Open Interest":
        oi_container = st.container()
        with oi_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_oi_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            otm = [e for e in fl if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
            fig = create_heatmap(otm, "open_interest", "Open Interest Heatmap", d, spot=s.spot)
            if fig: st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_oi_chart")

    elif om == "Volume":
        volume_container = st.container()
        with volume_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_v_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            otm = [e for e in fl if (e["type"]=="CALL" and e["strike"]>=s.spot) or (e["type"]=="PUT" and e["strike"]<=s.spot)]
            fig = create_heatmap(otm, "volume", "Volume Heatmap", d, spot=s.spot)
            if fig: st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_v_chart")

    elif om in ("VRP", "VRP Ratio"):
        vrp_container = st.container()
        with vrp_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_vrp_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            vd = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            smi = min(e["strike"] for e in vd) if vd else 0; sma = max(e["strike"] for e in vd) if vd else 0
            _rv = s.get("underlying_20d_rv", 0.0)
            if _rv > 0:
                fig = create_vol_surface_2d(vd, _rv, smi, sma, s.spot, is_dark=d, mode="vrp" if om=="VRP" else "vrp_ratio")
                st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_vrp_chart")
            else:
                st.info("No RV data")


@st.fragment(run_every=10)
def render_trade_signals_frag():
    s = st.session_state; d = getattr(s, 'theme', 'dark') == "dark"

    st.subheader("Trade Signals")

    signals_container = st.container()
    with signals_container:
        _rv = s.get("underlying_20d_rv", 0.0)
        if _rv <= 0:
            st.info("Load data to see strategy signals")
            return
        if not s.get("strikes"):
            return
        aks = sorted(set(e["strike"] for e in s.filtered_data)); atm_k = min(aks, key=lambda k: abs(k-s.spot)) if aks else s.spot
        sd = [e for e in s.filtered_data if e.get("open_interest",0)>0 and (e.get("mark",0) or 0)>0 and ((e["strike"]==atm_k) or (e["type"]=="CALL" and e["strike"]>s.spot) or (e["type"]=="PUT" and e["strike"]<s.spot))]
        with st.expander("How to read these signals", expanded=False):
            st.markdown("Data &mdash; Each row is a single option (Type + Strike + Expiration). Only **OTM + ATM** options with positive OI and price are used.\n\n**VRP** &mdash; `(IV - RV) x 100`. &gt;+2% option expensive. &lt;-2% option cheap.\n\n**IV Skew (25D)** &mdash; `Put IV - Call IV`. Positive -> puts expensive. Negative -> calls expensive.\n\n**IV Rank** &mdash; Where ATM IV sits in the trailing 1Y range of 20d realized vol. &gt;70 high (sell premium), &lt;30 low (buy premium).\n\n**Scoring** &mdash; Sell Premium (>= +1), Buy Premium (<= -1), Neutral.\n\n**Market Bias** &mdash; Auto-detected from gamma flip, net GEX, IV skew, OI wall, IV rank.\n\n**Strategies** &mdash; Long/Short Calls/Puts, Spreads, Iron Condor, Butterfly, Straddle, Strangle, Calendar.")
        _iv_rank = s.get("iv_rank")
        b, br = assess_market_bias(s.analytics, s.spot, iv_rank=_iv_rank)
        e = {"Bullish":"🟢","Bearish":"🔴","Neutral":"🟡"}
        st.markdown(f"**Market Bias:** {e.get(b,'')} {b} &mdash; {br}")
        st.markdown(f"**Next Earnings:** {s.get('next_earnings_date') or 'N/A'}")
        st.markdown(f"**IV Rank:** {_iv_rank:.1f}%" if _iv_rank is not None else "")
        ar = s.get("strikes_atm_range",20)
        if ar>0 and sd and s.spot>0:
            sk = sorted(set(e["strike"] for e in sd)); ak = min(sk, key=lambda k: abs(k-s.spot)); ai = sk.index(ak)
            nb = min(ar,ai); na = min(ar,len(sk)-1-ai); sd2 = [e for e in sd if sk[ai-nb]<=e["strike"]<=sk[ai+na]]
        else: sd2 = sd
        c1,c2 = st.columns([1,2])
        with c1:
            pt = st.radio("Premium Type", ["Buy Premium","Sell Premium"], horizontal=True, key="premium_type")
            stg = st.selectbox("Strategy", ["Long Calls","Long Puts","Call Debit Spread","Put Debit Spread","Long Straddles","Long Strangles","Calendar Spread"] if pt=="Buy Premium" else ["Short Calls","Short Puts","Call Credit Spread","Put Credit Spread","Iron Condor","Butterfly","Broken Wing Butterfly","Jade Lizard"])
        sc = score_options(sd2, s.spot, _rv, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), iv_skew=s.analytics.get("iv_skew"), iv_rank=_iv_rank)
        rc = generate_recommendations(sc, s.spot, strategy=stg, all_data=sd, rv=_rv, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), iv_skew=s.analytics.get("iv_skew"))
        with c2:
            for r in rc: st.markdown(f"- {r}")


@st.fragment(run_every=10)
def render_options_data_frag():
    if not st.session_state.get("data"): return
    render_analytics_panel()
    render_table()


def render_analytics_panel():
    with st.expander("Analytics Panel", expanded=False):
        a = st.session_state.get("analytics", {})
        if not a:
            st.info("Load data to see analytics")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Key Levels")
            st.markdown(f"- **Call Wall:** ${a.get('call_wall', 'N/A')}")
            st.markdown(f"- **Put Wall:** ${a.get('put_wall', 'N/A')}")
            st.markdown(f"- **Gamma Flip:** ${a.get('gamma_flip', 'N/A')}")
            st.markdown(f"- **Max Pain:** ${a.get('expected_pin', 'N/A')}")

        with col2:
            st.markdown("#### Exposure Summary")
            st.markdown(f"- **Max +GEX:** ${a.get('max_positive_gex', 0):,.0f} @ {a.get('max_positive_gex_strike', 'N/A')}")
            st.markdown(f"- **Max -GEX:** ${a.get('max_negative_gex', 0):,.0f} @ {a.get('max_negative_gex_strike', 'N/A')}")
            st.markdown(f"- **Total Call GEX:** ${a.get('total_call_gex', 0):,.0f}")
            st.markdown(f"- **Total Put GEX:** ${a.get('total_put_gex', 0):,.0f}")
            st.markdown(f"- **Net GEX:** ${a.get('net_gex', 0):,.0f}")
            st.markdown(f"- **Dealer Position:** {a.get('dealer_position', 'N/A')}")
            vex_m = a.get('vex_magnet')
            vex_r = a.get('vex_repellent')
            if vex_m:
                st.markdown(f"- **VEX Magnet:** ${vex_m:.2f} ({a.get('vex_magnet_value', 0):,.0f})")
            if vex_r:
                st.markdown(f"- **VEX Repellent:** ${vex_r:.2f} ({a.get('vex_repellent_value', 0):,.0f})")

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
            "Expirations": s["num_expirations"],
            "IV": s.get("call_iv", 0) if s["strike"] >= st.session_state.spot else s.get("put_iv", 0),
        })

    df = pd.DataFrame(rows)
    spot = st.session_state.spot
    atm_strike = min(strikes, key=lambda s: abs(s["strike"] - spot))
    atm_iv = (atm_strike.get("call_iv", 0) + atm_strike.get("put_iv", 0)) / 2
    df["Rel IV"] = df["IV"] / atm_iv if atm_iv > 0 else 0.0

    rv = st.session_state.get("underlying_20d_rv", 0.0)
    if rv > 0:
        df["VRP"] = df["IV"] - rv
        df["VRP Ratio"] = df["IV"] / rv
    else:
        df["VRP"] = 0.0
        df["VRP Ratio"] = 0.0

    max_pin_idx = (df["Call OI"] + df["Put OI"]).idxmax()
    call_wall = st.session_state.analytics.get("call_wall")
    call_wall_idx = df[df["Strike"] == call_wall].index.tolist()
    put_wall = st.session_state.analytics.get("put_wall")
    put_wall_idx = df[df["Strike"] == put_wall].index.tolist()

    is_dark = st.session_state.theme == "dark"
    atm_bg = "#555555" if is_dark else "#e0e0e0"
    max_pain_bg = "#8b1a1a" if is_dark else "#ffcccc"
    call_wall_bg = "#ef553b" if is_dark else "#ffcccc"
    put_wall_bg = "#00cc96" if is_dark else "#ccffcc"

    def highlight_atm(row):
        is_atm = abs(row["Strike"] - spot) == min(
            abs(df["Strike"] - spot)
        )
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
        "VRP Ratio": "{:.2f}",
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
        "Call Price": "${:.2f}",
        "Put Price": "${:.2f}",
        "Rel IV": "{:.2f}",
    })

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Export CSV", width='stretch'):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download", csv,
                f"{st.session_state.symbol}_gex.csv",
                "text/csv",
                width='stretch',
            )

    st.dataframe(styled, width='stretch', height=400)


def main():
    render_sidebar()

    main_section = st.container()
    with main_section:
        st.markdown(
            f"# {st.session_state.symbol} — Gamma Exposure Analysis"
        )

        if st.session_state.get("data"):
            render_metrics_frag()
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Market Structure", "Positioning", "Volatility", "Heatmaps", "Trade Signals", "Candlesticks"])
            with tab1: render_market_structure_frag()
            with tab2: render_positioning_frag()
            with tab3: render_volatility_frag()
            with tab4: render_heatmaps_frag()
            with tab5: render_trade_signals_frag()
            with tab6: render_candlesticks_frag()
            with st.container(): render_options_data_frag()
        else:
            st.info("Enter a stock ticker in the sidebar and click Refresh to begin analysis")
            st.markdown(r"""
            ### Quick Start
            1. Enter a ticker (e.g., SPY, AAPL, TSLA, \$SPX, \$RUT) in the sidebar
            2. Click **Refresh** to load the option chain (works best during regular US market hours)
            3. Explore GEX visualizations and analytics
            """)
            st.markdown("### Note")
            st.caption("Candlestick chart fragment was removed. Indicator code is available in charts.py and can be reused in other chart components.")


if __name__ == "__main__":
    main()
