"""get_gex_analytics — full gex_app analytics pipeline for one symbol."""

from schwab_mcp.core import _err, _get_client, _ok, _r_and_q, _schwab_sem, server


@server.tool()
async def get_gex_analytics(symbol: str = "SPY") -> str:
    """Full gex_app analytics for one symbol — same pipeline as the Streamlit app.

    Returns: total/net GEX, call wall, put wall, gamma flip, ATM strike,
    dealer position, max positive/negative GEX strikes, largest OI strike,
    largest gamma strike, expected pin, IV skew (25-delta), ATM IV,
    SSVI surface, and per-strike aggregates (net GEX + OI by strike).
    Index symbols (SPX/RUT/NDX...) fall back to their ETF proxy chain
    when the index chain is unavailable, exactly as the app does.
    """
    try:
        from analytics import compute_analytics
        from calculations import parse_option_chain
        from client import fetch_option_chain
        from _constants import INDEX_SYMBOLS

        sym = symbol.upper()
        client = await _get_client()
        r, q = await _r_and_q(sym)
        cc_sym = f"${sym}" if sym in ("SPX", "RUT", "NDX", "VIX") else sym
        async with _schwab_sem:
            raw = await fetch_option_chain(client, cc_sym, strike_count=75, include_quotes=True)
        data, spot = parse_option_chain(raw, r=r, q=q)
        if (not data or spot <= 0) and sym in INDEX_SYMBOLS:
            from _constants import STREAM_SYMBOL_MAP
            etf = STREAM_SYMBOL_MAP.get(sym, sym)
            async with _schwab_sem:
                fb_raw = await fetch_option_chain(client, etf, strike_count=75, include_quotes=True)
            data, spot = parse_option_chain(fb_raw, r=r, q=q)
        if not data or spot <= 0:
            return _err(f"could not parse chain for {symbol}")
        analytics = compute_analytics(data, spot, data_full=data, r=r, q=q)
        # Compact per-strike aggregates for the walls band (±5 strikes of ATM)
        near = [{
            "strike": e.get("strike"), "type": e.get("type"),
            "net_gex": round(e.get("gex") or 0.0, 2),
            "open_interest": e.get("oi") if e.get("oi") is not None else e.get("open_interest"),
            "volume": e.get("volume"),
        } for e in data if abs((e.get("strike") or 0) - spot) <= 5]
        return _ok({
            "symbol": symbol, "spot": spot, "r": r, "q": q,
            "analytics": {k: v for k, v in analytics.items() if k != "by_strike"},
            "atm_strikes_context": near[:40],
        })
    except Exception as e:
        return _err(f"get_gex_analytics failed: {type(e).__name__}: {e}")
