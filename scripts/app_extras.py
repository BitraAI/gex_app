"""Unusual-trades scanner + Live News tab extracted verbatim from app.py."""
import asyncio

import pandas as pd
import streamlit as st

from scripts.flow import _ensure_async_loop
from scripts._utils import format_expiration
from scripts.app_data import _fetch_option_chain_core
from scripts.app_tables import _render_styled_dataframe


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


def _infer_uw_side(bid: float, ask: float, mark: float) -> str:
    """Infer the aggressor side (ASK/BID/MID) from the mark's position
    within the bid-ask spread.

    Trading at/near the ask means a buyer lifted the offer (demand);
    at/near the bid means a seller hit the bid (supply); a mark sitting
    on the midpoint (or a missing bid/ask) is uninformative -> MID.
    """
    if bid <= 0 or ask <= 0 or ask <= bid:
        return "MID"
    mid = (bid + ask) / 2
    half = (ask - bid) / 2
    frac = (mark - mid) / half if half > 0 else 0.0
    if frac >= 0.3:
        return "ASK"
    if frac <= -0.3:
        return "BID"
    return "MID"


def render_unusual_trades():
    """Unusual Trades scanner tab.

    Scans every tracked ticker (or just the current one) for "unusual"
    options blocks: outsized volume relative to open interest (fresh
    positioning rather than churn) or extreme traded premium.  Uses the
    same self-contained per-ticker fetch as the Trade Signals scan so it
    never disturbs the main session state.
    """
    s = st.session_state

    st.subheader("Unusual Trades Scanner")

    with st.expander("How to read this scanner", expanded=False):
        st.markdown(
            "Each row is a single option contract flagged by the scanner. "
            "**Vol/OI** is today's volume divided by open interest &mdash; a "
            "ratio above 1.0 means more contracts traded today than are open, "
            "a classic sign of fresh position building (unusual flow) rather "
            "than churn of existing contracts. **Premium** is "
            "`mark x volume x 100`, the estimated money traded at the last mark."
        )

    scope = st.radio(
        "Scope",
        ["All tracked tickers", "Current ticker only"],
        horizontal=True,
        key="uw_scope",
    )
    if scope == "All tracked tickers":
        tickers = list(s.get("ticker_history", []))
    else:
        tickers = [s.get("symbol", "")] if s.get("symbol") else []
    if not tickers:
        st.info("No tickers to scan — add tickers on the main page first.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        min_vol = st.number_input("Min Volume", min_value=1, value=1000, step=100, key="uw_min_vol")
    with c2:
        min_ratio = st.number_input("Min Vol/OI", min_value=0.1, value=1.0, step=0.1, key="uw_min_ratio")
    with c3:
        min_premium = st.number_input("Min Premium ($)", min_value=0, value=100000, step=10000, key="uw_min_premium")
    with c4:
        max_dte = st.number_input("Max DTE", min_value=1, value=3, step=1, key="uw_max_dte")

    otm_only = st.checkbox(
        "Show OTM only (strikes beyond spot)",
        value=True,
        key="uw_otm_only",
    )

    run = st.button("Run scan", type="primary", key="run_uw_scan")

    if run:
        rows = []
        with st.spinner(f"Scanning {len(tickers)} ticker(s)..."):
            for sym in tickers:
                core = _fetch_option_chain_core(sym)
                if core is None or core["fetch_error"] is not None:
                    continue
                data, spot = core["data"], core["spot"]
                if not data or spot <= 0:
                    continue
                for opt in data:
                    volume = int(opt.get("volume", 0) or 0)
                    if volume < min_vol:
                        continue
                    dte = int(opt.get("days_to_exp", 0) or 0)
                    if dte <= 0 or dte > max_dte:
                        continue
                    oi = int(opt.get("open_interest", 0) or 0)
                    ratio = volume / oi if oi > 0 else float("inf")
                    if oi > 0 and ratio < min_ratio:
                        continue
                    mark = float(opt.get("mark", 0) or 0)
                    premium = mark * volume * 100
                    if premium < min_premium:
                        continue
                    if otm_only:
                        if opt["type"] == "CALL" and opt["strike"] <= spot:
                            continue
                        if opt["type"] == "PUT" and opt["strike"] >= spot:
                            continue
                    rows.append({
                        "Ticker": core["sym"],
                        "Type": opt["type"],
                        "Side": _infer_uw_side(
                            float(opt.get("bid", 0) or 0),
                            float(opt.get("ask", 0) or 0),
                            float(opt.get("mark", 0) or 0),
                        ),
                        "Strike": opt["strike"],
                        "Expiration": opt["expiration"],
                        "DTE": dte,
                        "Volume": volume,
                        "OI": oi,
                        "Vol/OI": ratio if oi > 0 else None,
                        "Mark": mark,
                        "Premium": premium,
                        "IV": opt.get("iv", 0) or 0,
                        "Delta": opt.get("delta", 0) or 0,
                        "Spot": spot,
                    })
        if rows:
            df = pd.DataFrame(rows).sort_values("Premium", ascending=False)
            st.session_state.uw_results = df.reset_index(drop=True)
        else:
            st.session_state.uw_results = pd.DataFrame()

    results_df = s.get("uw_results")
    if results_df is None or results_df.empty:
        st.info("Set your filters and click **Run scan** to surface unusual options activity.")
        return

    _total_premium = float(results_df["Premium"].sum())
    _calls = int((results_df["Type"] == "CALL").sum())
    _puts = int((results_df["Type"] == "PUT").sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Flagged contracts", len(results_df))
    m2.metric("Total premium", f"${_total_premium:,.0f}")
    m3.metric("Tickers", results_df["Ticker"].nunique())
    m4.metric("Calls / Puts", f"{_calls} / {_puts}")

    df = results_df.head(3000).copy()
    df["Expiration"] = df["Expiration"].map(format_expiration)

    def _row_style(row):
        is_call = row["Type"] == "CALL"
        bg = "#e6f7f1" if is_call else "#fdecec"
        side = row["Side"]
        if side == "ASK":
            side_style = "color: #00cc96; font-weight: 600;"
        elif side == "BID":
            side_style = "color: #ef5350; font-weight: 600;"
        else:
            side_style = "color: #ff9800;"
        return [
            side_style if col == "Side" else f"background-color: {bg};"
            for col in row.index
        ]

    styled = (
        df.style
        .apply(_row_style, axis=1)
        .format({
            "Strike": "${:,.2f}",
            "Volume": "{:,.0f}",
            "OI": "{:,.0f}",
            "Vol/OI": lambda v: "—" if pd.isna(v) else f"{v:.2f}x",
            "Mark": "${:,.2f}",
            "Premium": "${:,.0f}",
            "IV": lambda v: "—" if pd.isna(v) or v == 0 else f"{(v / 100 if v > 3 else v):.0%}",
            "Delta": "{:.2f}",
            "Spot": "${:,.2f}",
        })
        .set_properties(**{"text-align": "right"})
    )

    _render_styled_dataframe(
        styled,
        height=460,
        column_config={
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Side": st.column_config.TextColumn("Side", width="small"),
        },
    )

