"""Dedicated ATM Order Flow page.

Served by Streamlit at http://localhost:8501/atm_order_flow as part of the
multi-page app.  It shares st.session_state with the main app.py entry page.

Streaming is owned by the main app: refreshing a ticker there starts the
WebSocket feed (equity + ATM option volume) via ensure_atm_streaming.  This
page only reads the shared session state (atm_option_service / flow_cache) and
renders the grid — it does not start streaming itself.
"""

import streamlit as st

from flow_page import render_atm_order_flow_grid, ensure_session_defaults

st.set_page_config(
    page_title="ATM Order Flow — GammaEx",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("# ATM Order Flow")

st.caption(
    "Live bullish / bearish order flow from the ATM front-expiration "
    "call/put via the Lee-Ready algorithm (call buy + put sell = bullish, "
    "call sell + put buy = bearish)."
)

# Reuse the same styling as the main app so the grid looks consistent.
try:
    from charts import set_dark, _get_style
    _dark = st.session_state.get("theme", "light") == "dark"
    set_dark(_dark)
    st.markdown(_get_style(_dark), unsafe_allow_html=True)
except Exception:
    pass

# Initialize shared session defaults (spot_cache, ticker_history, services,
# etc.) — the page runs as a separate script and wouldn't have them otherwise.
# ticker_history is loaded from ticker_history.json here so the grid always
# has its row list even before any streaming has started.
ensure_session_defaults()

# Streaming is started by the main app's ticker Refresh (ensure_atm_streaming).
# If it hasn't been started yet, show a hint instead of dead "No Data" rows.
atm_svc = st.session_state.get("atm_option_service")
if not (atm_svc and getattr(atm_svc, "is_running", False)):
    st.info(
        "Streaming is not running yet. Open the main GammaEx page, enter a "
        "ticker, and click **Refresh** to start the WebSocket feed."
    )


@st.fragment(run_every=2)
def _flow_grid():
    render_atm_order_flow_grid()


_flow_grid()

