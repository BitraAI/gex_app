import logging

import pandas as pd
import streamlit as st
from scripts import landing, persistent_session
from scripts.option_streaming_service import _load_ticker_history
from scripts.flow import render_flow_frag
from scripts.charts import _get_style, _get_css
from scripts.config import validate_config
# Dashboard views (split out of this entrypoint; see scripts/app_*.py -- a
# good way to keep app.py load-and-parse work on the hot path small).
from scripts.app_views import render_sidebar, render_metrics_frag, render_market_structure, render_positioning, render_volatility, render_heatmaps
from scripts.app_candlesticks import render_candlesticks_frag
from scripts.app_tables import render_options_data
from scripts.app_signals import render_trade_signals
from scripts.app_extras import render_unusual_trades, render_news_frag


# Fail fast with a clear, actionable message if config.toml / env vars are
# missing required credentials — otherwise the user hits a cryptic traceback
# only after clicking Refresh.  Done at module scope (before main) so the
# banner always renders.
_CONFIG_ERRORS = validate_config()

# Setup logger for client reconnection
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    "by_exp_all_version": 0,
    "underlying_20d_rv": 0.0,
    "alerts": [],
    "prev_alerts_state": {},
    "ticker_history": [],
    "streaming_service": None,
    "atm_option_service": None,
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

# Sidebar (left panel): pull the whole stack up so all items fit in view.
# stSidebarHeader is a fixed 3.75rem row (+1rem margin) that reserves space
# for the app logo even when none is set (2rem stLogoSpacer), so collapse it;
# stSidebarUserContent adds 6rem of bottom scroll padding; widget stacks use
# ~1rem flex gaps — all tightened here.
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"],
    [data-testid="stSidebarHeader"] {
        height: auto !important;
        min-height: 0 !important;
        margin-bottom: 0.25rem !important;
    }
    [data-testid="stLogoSpacer"] {
        height: 0.25rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"],
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        gap: 0.25rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {
        margin: 0.15rem 0 0.35rem 0 !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        margin: 0 0 0.2rem 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stHorizontalRule"],
    [data-testid="stSidebar"] hr {
        margin: 0.25rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main (right-side) panel shown after the landing/login page: pull the
# dashboard content up to the top of the viewport. Modern Streamlit renders
# the content block as stMainBlockContainer (the legacy ".main
# .block-container" wrapper class no longer exists), so both are tightened
# here. Streamlit 1.6x overlays a 3.75rem stHeader (Deploy / Get help / ...)
# on an absolute 0.25rem top gap, so 4rem clears the toolbar while saving
# 2rem versus the 6rem default. The landing page re-supplies its own
# later-in-DOM rules for the same selectors, so its hero layout is untouched.
st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"] {
        padding-top: 4rem !important;
        padding-bottom: 1rem !important;
    }
    .main .block-container {
        padding-top: 4rem !important;
        padding-bottom: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Landing / auth gate
#
# While nobody is signed in, show the Robinhood-style landing page (hero,
# feature cards, trust band) with the Log in / Sign up card on it. The landing
# module calls st.stop(), so the main dashboard below never renders until a
# session is established. Signing out clears the key and reruns back to here.
#
# st.session_state dies with the websocket (refresh, reconnect, restart), so
# before landing on that page we try to sign the user back in from their
# long-lived browser cookie (persistent sessions; see persistent_session.py).
if not st.session_state.get("gex_user"):
    persistent_session.restore()
if not st.session_state.get("gex_user"):
    landing.render_landing()

# A magic-link login queues a fresh token in session state; write the cookie
# now that the dashboard is actually rendering (writes issued during the
# landing run would be discarded by its st.rerun()).
persistent_session.flush()
def render_tabs_frag():
    # Create the tabs with updated order
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "Market Structure", "Positioning", "Volatility", "Heatmaps",
        "Options Data", "Candlesticks", "Order Flow", "Trade Signals", "Unusual Trades",
        "Live News"
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
        render_flow_frag()
    
    with tab8:
        render_trade_signals()
    
    with tab9:
        render_unusual_trades()
    
    with tab10:
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
