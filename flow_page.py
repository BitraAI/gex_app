"""Shared ATM order-flow rendering used by both the main app page and the
dedicated Order Flow tab.

Kept free of any st.set_page_config / global app setup so it can be imported
safely from either entry point without re-running app.py's top-level code.
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo


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


def ensure_session_defaults():
    """Initialize the shared st.session_state defaults.

    The main app.py applies _SESSION_DEFAULTS at import time, but Streamlit
    *pages* run as a separate script and would otherwise start with an empty
    session state (causing AttributeError on st.session_state.spot_cache,
    st.session_state.show_calls, etc. when the page drives fetch_data /
    streaming directly).  Call this from any page before touching session state.

    Reuses the exact _SESSION_DEFAULTS dict from app.py so the two never drift.
    """
    from app import _SESSION_DEFAULTS
    for k, v in _SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.ticker_history:
        try:
            from option_streaming_service import _load_ticker_history
            st.session_state.ticker_history = _load_ticker_history()
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
    for t_sym in tracked:
        t_upper = t_sym.upper().lstrip("$")
        if t_upper in s.spot_cache:
            _spot_map[t_upper] = s.spot_cache[t_upper]
    if _spot_map:
        atm_svc.bulk_update_spots(_spot_map)

    for t_sym in tracked:
        bf, brf = atm_svc.get_ticker_flow(t_sym)
        if bf is not None and brf is not None:
            if t_sym not in s.flow_cache or s.flow_cache[t_sym]["bullish"] is not None:
                s.flow_cache[t_sym] = {"bullish": bf, "bearish": brf}


def render_atm_order_flow_grid():
    """Render the ATM Order Flow as a Streamlit dataframe (mirrors the style of
    the main app's Options Data table): one row per tracked ticker with
    Bullish / Bearish flow, a coloured Status cell, and formatted numbers.

    Used by the Order Flow tab in the main app (wrapped in a refresh fragment).
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
        if not has_data:
            status = "No Data"
        elif is_tracked and is_market_open():
            status = "Live"
        elif is_tracked:
            status = "Closed"
        else:
            status = "Cached"
        net = (bullish - bearish) if has_data else None
        opt_prices = atm_svc.get_ticker_option_prices(t_upper) if atm_svc else {}
        atm_strike = atm_svc.get_ticker_atm_strike(t_upper) if atm_svc else None
        spot = atm_svc.get_ticker_spot(t_upper) if atm_svc else None
        rows.append({
            "Ticker": t_upper,
            "Spot": spot,
            "ATM Strike": atm_strike,
            "Call Price": opt_prices.get("call_price"),
            "Put Price": opt_prices.get("put_price"),
            "Bullish Flow": bullish if has_data else 0,
            "Bearish Flow": bearish if has_data else 0,
            "Net Flow": net if has_data else 0,
            "Status": status,
        })

    if not rows:
        st.info("No tickers tracked yet. Add tickers on the main GammaEx page first.")
        return

    df = pd.DataFrame(rows)

    # Static colour key for the Status column (non-interactive legend).
    _status_colors = {
        "Live": "#00cc96",
        "Closed": "#E69500",
        "Cached": "#1E90FF",
        "No Data": "#808080",
    }
    _items = list(_status_colors.items())
    _legend_html = "".join(
        f'<span style="display:inline-flex;align-items:center;'
        f'margin-left:16px;">'
        f'<span style="font-size:25px;line-height:25px;'
        f'color:{c};margin-right:6px;">\u25cf</span>{name}</span>'
        for name, c in _items
    )
    st.markdown(
        f'<div style="margin-bottom:8px;font-size:0.9rem;display:flex;'
        f'justify-content:flex-end;">{_legend_html}</div>',
        unsafe_allow_html=True,
    )

    # Status column shows the colour-key only (no background fill, no text).
    # The cell background is white/transparent and holds a centered coloured
    # dot; the text is hidden so only the colour conveys status (see legend).
    def _status_color(val):
        color = _status_colors.get(val, "#808080")
        return f"color: {color}; font-size: 25px; text-align: center;"

    # Net Flow colouring: green when net bullish, red when net bearish,
    # neutral grey when zero.  Colour the text so the row stays readable.
    def _net_flow_color(val):
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #808080;"

    _styler = df.style
    # pandas >= 2.1 renamed Styler.applymap -> Styler.map; support both.
    if hasattr(_styler, "map"):
        _styler = _styler.map(_status_color, subset=["Status"])
        _styler = _styler.map(_net_flow_color, subset=["Net Flow"])
    else:
        _styler = _styler.applymap(_status_color, subset=["Status"])
        _styler = _styler.applymap(_net_flow_color, subset=["Net Flow"])
    styled = _styler.format({
        "Spot": lambda v: f"${v:,.2f}" if v is not None else "",
        "ATM Strike": lambda v: f"${v:,.2f}" if v is not None else "",
        "Call Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Put Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Bullish Flow": "{:,.0f}",
        "Bearish Flow": "{:,.0f}",
        "Net Flow": "{:,.0f}",
        "Status": lambda v: "\u25cf",
    })

    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] { overflow-x: auto; max-width: 100%; }
    div[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
    </style>
    """, unsafe_allow_html=True)
    st.dataframe(styled, height=700, width="stretch")
