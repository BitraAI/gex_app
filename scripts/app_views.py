"""View components extracted verbatim from app.py.

Metric cards, the 10 s metrics fragment, the four analytics tab views
(Market Structure / Positioning / Volatility / Heatmaps) and the sidebar.
Chart-heavy views keep their lazy ``from scripts.charts import ...`` calls
inside the function bodies, exactly as before.
"""
import streamlit as st

from datetime import datetime
from typing import Optional

from scripts import persistent_session
from scripts._constants import INDEX_SYMBOLS
from scripts._utils import is_otm_or_atm, is_itm_or_atm
from scripts.calculations import aggregate_by_strike
from scripts.analytics import _filter_strikes_near_atm
from scripts.signals import _tte_from_dtes
from scripts.option_streaming_service import (_normalize_display_symbol,
                                              _save_ticker_history)
from scripts.app_data import sync_index_poller, fetch_data


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
            from scripts.charts import create_gex_histogram
            fig = create_gex_histogram(strikes, s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"), gamma_flip=s.analytics.get("gamma_flip"), )
            fig.update_layout(dragmode="zoom"); st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_histogram")
        elif ms_view == "GEX by Expiration":
            from scripts.charts import create_gex_by_expiration
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="gex_exp_slider")
            fig = create_gex_by_expiration(s.by_exp_all, max_exps=mx, ); fig.update_layout(dragmode="zoom")
            st.plotly_chart(fig, config={"scrollZoom": True}, width='stretch', key="gex_by_exp")
        elif ms_view == "Gamma Surface":
            from scripts.charts import create_gamma_surface
            fig = create_gamma_surface(s.filtered_data, ); st.plotly_chart(fig, width='stretch', key="gamma_surface")
        else:
            from scripts.charts import create_dealer_gamma_curve
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
        raw_data = [e for e in raw_data if is_otm_or_atm(e, s.spot)]
    if not s.get("show_otm", True):
        raw_data = [e for e in raw_data if is_itm_or_atm(e, s.spot)]
    
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

    # Schwab's option-chain REST API zeroes totalVolume after the close
    # (open interest persists; thinkorswim shows leftover volume from its own
    # streaming session). Defuse the "empty chart" and hint at OI instead.
    if selected_view_type == "Volume":
        if not any(e["call_volume"] or e["put_volume"] for e in positioning_data):
            st.caption("Volume is 0: Schwab's chain API reports 0 for every contract after the close "
                       "(thinkorswim keeps its own streaming counter). This view fills while the market session is live.")

    if selected_view_type == "Open Interest":
        from scripts.charts import create_oi_by_strike
        with st.container():
            fig = create_oi_by_strike(
                positioning_data, s.spot, mode="oi",
            )
            fig.update_layout(dragmode="zoom")
            st.plotly_chart(
                fig, config={"scrollZoom": True}, width="stretch", key="oi_chart"
            )
    elif selected_view_type == "Volume":
        from scripts.charts import create_oi_by_strike
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

    from scripts.charts import create_iv_by_strike, create_iv_richness_by_strike

    _rv = s.get("underlying_20d_rv", 0.0)
    _ssvi_surf = s.analytics.get("ssvi_surface") if s.get("analytics") else None

    vol_view = st.radio(
        "View",
        ["IV by Expiration", "IV by Strike"],
        horizontal=True, label_visibility="collapsed",
        key="vol_view_radio",
    )

    if vol_view == "IV by Expiration":
        from scripts.charts import create_atm_iv_histogram, create_vrp_chart
        mo = st.radio("View", ["ATM IV", "VRP"], horizontal=True, label_visibility="collapsed", key="iv_exp_mode")
        mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="iv_exp_slider")
        ivd = s.by_exp_all[:mx]
        if mo == "ATM IV": st.plotly_chart(create_atm_iv_histogram(ivd, rv=_rv).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="atm_iv_chart")
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
        if not s.get("show_itm", True): raw = [e for e in raw if is_otm_or_atm(e, s.spot)]
        if not s.get("show_otm", True): raw = [e for e in raw if is_itm_or_atm(e, s.spot)]
        raw = _filter_strikes_near_atm(raw, s.spot, n=20)
        vk = aggregate_by_strike(raw, s.spot, show_calls=s.show_calls, show_puts=s.show_puts)
        _ssvi_tte = _tte_from_dtes([e.get("dte", 0) for e in s.by_exp_all]) if _ssvi_surf is not None and s.get("by_exp_all") else None
        if tm == "IV":
            if vk:
                st.plotly_chart(create_iv_by_strike(vk, s.spot, ssvi_surface=_ssvi_surf, ssvi_tte=_ssvi_tte).update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="iv_by_strike")
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

    from scripts.charts import create_heatmap, create_vol_surface_2d

    om = st.radio("Select", ["Open Interest", "Volume", "IV Richness (pp)", "VRP"], horizontal=True, label_visibility="collapsed", key="hm_oi_vol_radio")

    if om == "Open Interest":
        oi_container = st.container()
        with oi_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_oi_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            fl = _filter_strikes_near_atm(fl, s.spot, n=20)
            otm = [e for e in fl if is_otm_or_atm(e, s.spot)]
            fig = create_heatmap(otm, "open_interest", "Open Interest Heatmap", spot=s.spot, call_wall=s.analytics.get("call_wall"), put_wall=s.analytics.get("put_wall"))
            if fig: st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_oi_chart")

    elif om == "Volume":
        volume_container = st.container()
        with volume_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_v_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            fl = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            fl = _filter_strikes_near_atm(fl, s.spot, n=20)
            otm = [e for e in fl if is_otm_or_atm(e, s.spot)]
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

    elif om == "VRP":
        vrp_container = st.container()
        with vrp_container:
            mx = st.slider("Expirations", min_value=2, max_value=max(2, len(s.by_exp_all)), value=min(4, len(s.by_exp_all)), key="hm_vrp_slider")
            ae = set(e["expiration"] for e in s.by_exp_all[:mx]) if mx else set()
            vd = [e for e in s.data if e.get("expiration") in ae] if ae else s.filtered_data
            vd = _filter_strikes_near_atm(vd, s.spot, n=20)
            smi = min(e["strike"] for e in vd) if vd else 0; sma = max(e["strike"] for e in vd) if vd else 0
            _rvv = s.get("underlying_20d_rv", 0.0)
            if not vd:
                st.info("No strike data")
            elif _rvv <= 0:
                st.info("No RV data")
            else:
                fig = create_vol_surface_2d(vd, _rvv, smi, sma, s.spot, mode="vrp")
                st.plotly_chart(fig.update_layout(dragmode="zoom"), config={"scrollZoom": True}, width='stretch', key="heatmap_vrp_chart")

def render_sidebar():
    with st.sidebar:
        st.markdown("## GammaEx")

        st.markdown("&nbsp;")

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

        # Blank row so the Expiration section doesn't crowd the Refresh button
        st.markdown("&nbsp;")

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

        # Blank rows so sections don't crowd each other
        st.markdown("&nbsp;")

        st.markdown("### Alerts")
        if st.session_state.alerts:
            for alert in st.session_state.alerts[:10]:
                st.info(alert, icon="ℹ")
            if st.button("Clear Alerts", width='stretch'):
                st.session_state.alerts = []
        else:
            st.caption("No alerts yet")

        st.markdown("&nbsp;")

        st.markdown("### Display")
        st.session_state.show_calls = st.checkbox("Show Calls", value=True)
        st.session_state.show_puts = st.checkbox("Show Puts", value=True)
        st.session_state.show_itm = st.checkbox("Show ITM", True)
        st.session_state.show_otm = st.checkbox("Show OTM", True)

        _user = st.session_state.get("gex_user")
        if _user:
            st.markdown("&nbsp;")
            st.markdown("---")
            st.caption(f"Signed in as **{_user['email']}**")
            if st.button("Log out", width="stretch"):
                # Revoke the persistent session (and clear its cookie) too,
                # otherwise the browser would sign straight back in.
                persistent_session.end()
                st.session_state.pop("gex_user", None)
                st.rerun()

