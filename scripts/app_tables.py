"""Options-data table views extracted verbatim from app.py.

Styled dataframe helper + the Options Data tab + the wall-filter helper
shared with the Trade Signals scan.
"""
import pandas as pd
import streamlit as st

from scripts.calculations import aggregate_by_strike
from scripts.analytics import _filter_strikes_near_atm
from scripts.signals import _tte_from_dtes


_STYLED_DF_CSS = """
<style>
div[data-testid="stDataFrame"] { overflow-x: auto; max-width: 100%; }
div[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
</style>
"""


def _render_styled_dataframe(styled, height=400, column_config=None):
    """Render a styled Streamlit dataframe with horizontal-scroll CSS."""
    st.markdown(_STYLED_DF_CSS, unsafe_allow_html=True)
    st.dataframe(styled, height=height, column_config=column_config)


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

    _render_styled_dataframe(styled, height=400)

