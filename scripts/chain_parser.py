"""Shared option chain parsing and analytics computation logic.

This module centralizes the duplicate chain parsing logic that was previously
duplicated across app.py, flow.py, and other modules.
"""

import logging
from typing import Any

from scripts._constants import STREAM_SYMBOL_MAP
from scripts.calculations import build_greeks_lookup, parse_option_chain
from scripts.analytics import compute_analytics
from scripts.client import (
    fetch_option_chain,
    get_interest_rate,
    get_yield,
)

logger = logging.getLogger(__name__)


async def fetch_and_parse_chain(
    client,
    symbol: str,
    *,
    include_quotes: bool = True,
    is_index_symbol: bool = False,
) -> dict[str, Any]:
    """Fetch and parse an option chain with ETF fallback support.
    
    This is a centralized version of the chain parsing logic that was
    previously duplicated across app.py, flow.py, and other modules.
    
    Args:
        client: Schwab async client
        symbol: Ticker symbol to fetch
        include_quotes: Whether to include quotes in the chain
        is_index_symbol: Whether this is an index symbol (SPX, RUT, NDX)
        
    Returns:
        dict with keys:
            - data: Parsed option chain data
            - spot: Underlying spot price
            - r: Risk-free rate
            - q: Dividend yield
            - etf_data: ETF proxy data (if applicable)
            - etf_spot: ETF proxy spot (if applicable)
            - etf_analytics: ETF proxy analytics (if applicable)
            - fallback_greeks: Fallback greeks lookup
    """
    # Normalize symbol for streaming
    _sym = symbol.upper().lstrip("$")
    
    # Fetch chain
    raw = await fetch_option_chain(
        client, symbol, strike_count=75, include_quotes=include_quotes,
    )
    
    # Get rates
    r = await get_interest_rate(client)
    q = await get_yield(client, symbol)
    
    # Setup fallback greeks for index symbols
    fallback_greeks = None
    etf_analytics = None
    etf_data = None
    etf_spot = 0.0
    
    if is_index_symbol:
        try:
            fallback_sym = STREAM_SYMBOL_MAP.get(_sym)
            if fallback_sym:
                fb_raw = await fetch_option_chain(
                    client, fallback_sym, strike_count=75, include_quotes=include_quotes,
                )
                fallback_greeks = build_greeks_lookup(fb_raw)
                etf_data, etf_spot = parse_option_chain(fb_raw, r=r, q=q)
                if etf_data and etf_spot > 0:
                    etf_analytics = compute_analytics(etf_data, etf_spot, data_full=etf_data, r=r, q=q)
        except Exception as exc:
            logger.warning("ETF fallback failed for %s: %s", symbol, exc)
    
    # Parse the main chain
    data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
    
    # ETF fallback for index symbols that failed
    if (not data or spot <= 0) and etf_data and etf_spot > 0:
        data, spot = etf_data, etf_spot
    
    return {
        "data": data,
        "spot": spot,
        "r": r,
        "q": q,
        "etf_data": etf_data,
        "etf_spot": etf_spot,
        "etf_analytics": etf_analytics,
        "fallback_greeks": fallback_greeks,
        "sym": _sym,
        "is_index_symbol": is_index_symbol,
    }


async def compute_analytics_for_symbol(
    client,
    symbol: str,
    *,
    include_quotes: bool = True,
) -> dict[str, Any] | None:
    """Compute full analytics for a symbol.
    
    This is a higher-level function that fetches, parses, and computes
    analytics for a symbol in a single call.
    
    Args:
        client: Schwab async client
        symbol: Ticker symbol to analyze
        include_quotes: Whether to include quotes in the chain
        
    Returns:
        dict with keys:
            - analytics: Full analytics dictionary
            - spot: Underlying spot price
            - data: Parsed option chain data
            - r: Risk-free rate
            - q: Dividend yield
            - iv_rank: Implied volatility rank (if available)
            - rv: Realized volatility (if available)
            - etf_analytics: ETF proxy analytics (if applicable)
    """
    # Normalize symbol
    _sym = symbol.upper().lstrip("$")
    is_index = _sym in STREAM_SYMBOL_MAP
    
    # Fetch and parse chain
    result = await fetch_and_parse_chain(
        client, symbol, include_quotes=include_quotes, is_index_symbol=is_index
    )
    
    if not result["data"] or result["spot"] <= 0:
        logger.warning("No option data for %s", symbol)
        return None
    
    # Compute analytics
    data = result["data"]
    spot = result["spot"]
    r = result["r"]
    q = result["q"]
    
    analytics = compute_analytics(data, spot, r=r, q=q)
    
    # Merge ETF analytics if available
    if result["etf_analytics"]:
        if analytics.get("net_gex", 0) == 0:
            for key in ("net_gex", "total_call_gex", "total_put_gex",
                        "max_positive_gex", "max_negative_gex",
                        "max_positive_gex_strike", "max_negative_gex_strike",
                        "dealer_position"):
                if key in result["etf_analytics"]:
                    analytics[key] = result["etf_analytics"][key]
        if analytics.get("ssvi_surface") is None and result["etf_analytics"].get("ssvi_surface") is not None:
            analytics["ssvi_surface"] = result["etf_analytics"]["ssvi_surface"]
        if analytics.get("atm_iv") is None and result["etf_analytics"].get("atm_iv") is not None:
            analytics["atm_iv"] = result["etf_analytics"]["atm_iv"]
    
    # Compute additional metrics
    rv = 0.0
    try:
        from scripts.client import get_20d_rv
        rv = await get_20d_rv(client, symbol)
    except Exception as exc:
        logger.warning("Failed to fetch 20d RV for %s: %s", symbol, exc)
    
    iv_rank = None
    try:
        from scripts.client import compute_iv_rank
        iv_rank = await compute_iv_rank(client, symbol)
    except Exception as exc:
        logger.warning("Failed to compute IV rank for %s: %s", symbol, exc)
    
    analytics["iv_rank"] = iv_rank
    analytics["rv"] = rv
    
    return {
        "analytics": analytics,
        "spot": spot,
        "data": data,
        "r": r,
        "q": q,
        "iv_rank": iv_rank,
        "rv": rv,
        "sym": _sym,
        "is_index_symbol": is_index,
    }


async def compute_analytics_light(
    client,
    symbol: str,
) -> dict[str, Any] | None:
    """Compute light analytics (no IV rank/RV) for frequent wall refreshes.
    
    This is optimized for the "lightweight recompute" path used by
    _compute_walls_for_symbol in flow.py.
    
    Args:
        client: Schwab async client
        symbol: Ticker symbol to analyze
        
    Returns:
        dict with keys:
            - analytics: Analytics dictionary (without iv_rank/rv)
            - spot: Underlying spot price
            - data: Parsed option chain data
    """
    # Normalize symbol
    _sym = symbol.upper().lstrip("$")
    is_index = _sym in STREAM_SYMBOL_MAP
    
    # Fetch and parse chain
    result = await fetch_and_parse_chain(
        client, symbol, include_quotes=True, is_index_symbol=is_index
    )
    
    if not result["data"] or result["spot"] <= 0:
        logger.warning("No option data for %s", symbol)
        return None
    
    # Compute analytics
    data = result["data"]
    spot = result["spot"]
    r = result["r"]
    q = result["q"]
    
    analytics = compute_analytics(data, spot, r=r, q=q)
    
    # Merge ETF analytics if available
    if result["etf_analytics"]:
        if analytics.get("net_gex", 0) == 0:
            for key in ("net_gex", "total_call_gex", "total_put_gex",
                        "max_positive_gex", "max_negative_gex",
                        "max_positive_gex_strike", "max_negative_gex_strike",
                        "dealer_position"):
                if key in result["etf_analytics"]:
                    analytics[key] = result["etf_analytics"][key]
        if analytics.get("ssvi_surface") is None and result["etf_analytics"].get("ssvi_surface") is not None:
            analytics["ssvi_surface"] = result["etf_analytics"]["ssvi_surface"]
        if analytics.get("atm_iv") is None and result["etf_analytics"].get("atm_iv") is not None:
            analytics["atm_iv"] = result["etf_analytics"]["atm_iv"]
    
    return {
        "analytics": analytics,
        "spot": spot,
        "data": data,
        "sym": _sym,
    }
