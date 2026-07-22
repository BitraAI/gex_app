"""Shared ATM order-flow rendering used by both the main app page and
the dedicated Order Flow tab.

Kept free of any st.set_page_config / global app setup so it can be imported
safely from either entry point without re-running app.py's top-level code.
"""

import asyncio
import pandas as pd
import streamlit as st
from datetime import date, datetime
from zoneinfo import ZoneInfo
from option_streaming_service import _find_flow_for_display


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
            _stream_map = {"SPX": "SPY", "SPXW": "SPY", "RUT": "IWM", "RUTW": "IWM", "NDX": "QQQ", "NDXP": "QQQ"}
            _fetch_syms = [_stream_map.get(sym, sym) for sym in _need_fetch]
            loop = _ensure_async_loop()
            fut = asyncio.run_coroutine_threadsafe(fetch_quotes(s.client, _fetch_syms), loop)
            quote_resp = fut.result()
            for disp_sym, _sym in zip(_need_fetch, _fetch_syms):
                qd = quote_resp.get(_sym, {}) or {}
                quote = qd.get("quote", {}) or qd.get(_sym, {})
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
            if t_sym not in s.flow_cache or s.flow_cache[t_sym]["bullish"] is not None:
                s.flow_cache[t_sym] = {"bullish": bf, "bearish": brf}


def _format_expiration(exp: str | None) -> str:
    if not exp:
        return ""
    try:
        exp_date = date.fromisoformat(exp)
        dte = (exp_date - date.today()).days
        mmdd = exp[5:10]  # "MM-DD"
        return f"{mmdd} ({dte}d)" if dte >= 0 else f"{mmdd} (0d)"
    except (ValueError, TypeError):
        return exp or ""


_STATUS_COLORS = {
    "Live": "#00cc96",
    "Closed": "#E69500",
    "Cached": "#1E90FF",
    "No Data": "#808080",
}


def render_flow_legend_and_style():
    """Render the static legend and dataframe style block for the Order Flow grid.

    Called once per outer-fragment tick (every ~10 s) instead of every 2 s
    to prevent HTML-DOM flicker caused by re-injecting the same markup.
    """
    _items = list(_STATUS_COLORS.items())
    _legend_html = "".join(
        f'<span style="display:inline-flex;align-items:center;'
        f'margin-left:16px;">'
        f'<span style="font-size:35px;line-height:35px;'
        f'color:{c};margin-right:6px;">•</span>{name}</span>'
        for name, c in _items
    )
    st.markdown(
        f'<div style="margin-bottom:8px;font-size:0.9rem;display:flex;'
        f'justify-content:flex-end;">{_legend_html}</div>',
        unsafe_allow_html=True,
    )
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
        
        rows.append({
            "Ticker": t_upper,
            "Spot": spot,
            "ATM Strike": atm_strike,
            "Expiration": atm_svc.get_ticker_expiration(t_upper) if atm_svc else None,
            "Call Price": opt_prices.get("call_price"),
            "Put Price": opt_prices.get("put_price"),
            "Bullish Flow": bullish if has_data else 0,
            "Bearish Flow": bearish if has_data else 0,
            "Net Flow": net if has_data else 0,
            "Trend": trend_display,
            "Status": status,
        })

    if not rows:
        st.info("No tickers tracked yet. Add tickers on the main GammaEx page first.")
        return

    # Hash the row data to detect whether anything actually changed.
    data_key = tuple(
        (r["Ticker"], r["Spot"], r["ATM Strike"], r["Expiration"], r["Trend"],
         r["Call Price"], r["Put Price"], r["Bullish Flow"],
         r["Bearish Flow"], r["Net Flow"], r["Status"])
        for r in rows
    )
    data_hash = hash(data_key)

    cached_hash = s.get("_flow_styled_hash")
    cached_styled = s.get("_flow_styled")
    if data_hash == cached_hash and cached_styled is not None:
        st.dataframe(cached_styled, height=700, width="stretch")
        return

    df = pd.DataFrame(rows)

    def _status_color(val):
        color = _STATUS_COLORS.get(val, "#808080")
        return f"color: {color}; font-size: 35px; line-height: 35px; text-align: center;"

    def _net_flow_color(val):
        if val > 0:
            return "color: #00cc96; font-weight: bold;"
        if val < 0:
            return "color: #ef5350; font-weight: bold;"
        return "color: #808080;"

    def _trend_color(val):
        """Color the trend text (up/down/flat) based on trend direction."""
        return {
            "up": "color: #00cc96; font-weight: bold;",
            "down": "color: #ef5350; font-weight: bold;",
        }.get(val, "color: #808080;")

    _styler = df.style.set_uuid("flow_grid")
    if hasattr(_styler, "map"):
        _styler = _styler.map(_status_color, subset=["Status"])
        _styler = _styler.map(_net_flow_color, subset=["Net Flow"])
        _styler = _styler.map(_trend_color, subset=["Trend"])
    else:
        _styler = _styler.apply(_status_color, subset=["Status"])
        _styler = _styler.apply(_net_flow_color, subset=["Net Flow"])
        _styler = _styler.apply(_trend_color, subset=["Trend"])

    styled = _styler.format({
        "Spot": lambda v: f"${v:,.2f}" if v is not None else "",
        "ATM Strike": lambda v: f"${v:,.2f}" if v is not None else "",
        "Expiration": lambda v: _format_expiration(v),
        "Trend": lambda v: v,
        "Call Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Put Price": lambda v: f"${v:,.2f}" if v is not None else "",
        "Bullish Flow": "{:,.0f}",
        "Bearish Flow": "{:,.0f}",
        "Net Flow": "{:,.0f}",
        "Status": lambda v: "●",
    })

    s._flow_styled_hash = data_hash
    s._flow_styled = styled
    st.dataframe(styled, height=700, width="stretch")
