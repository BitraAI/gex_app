"""Trade-signals tab extracted verbatim from app.py.

Self-contained per-ticker signal pipeline (``_run_ticker_signals``) plus the
``render_trade_signals`` view and its helpers.  Charitable reads of the
per-box scan state (``ticker_scan_*``) originate in the main session state.
"""
from typing import Any

import streamlit as st

from scripts.client import get_20d_rv, get_next_earnings_date
from scripts.calculations import aggregate_by_expiration
from scripts.analytics import compute_analytics
from scripts.signals import generate_recommendations, assess_market_bias, _tte_from_dtes
from scripts.option_streaming_service import _normalize_display_symbol
from scripts.flow import run_async
from scripts.app_data import _fetch_option_chain_core
from scripts.app_tables import _get_filtered_data_for_walls


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
                # Second-nearest expiration feeds the rolling Flow Ratio
                # / Net Flow (two ATM pairs per ticker).
                if len(expirations) > 1:
                    atm_svc.set_ticker_expiration2(_sym, expirations[1])
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

