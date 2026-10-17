"""get_movers — Schwab movers screen (top movers by market volume share).

NOTE: the response schema is FLAT — the JSON body is ``{"screeners": [mover,
mover, ...]}`` where the screeners LIST is the mover list itself (no nested
``movers`` key), and ``netPercentChange`` is a FRACTION (−0.0634 == −6.34%).
This tool normalizes both quirks into a plain list of rows.
"""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server

_VALID_INDEXES = {
    "$DJI", "$SPX", "$COMPX", "$SPX:XO", "OTCBB", "NASDAQ", "NYSE",
    "INDEX_ALL", "EQUITY_ALL", "OPTION_ALL", "OPTION_PUT", "OPTION_CALL",
}
_ALIAS_MAP = {
    "DJI": "$DJI", "DOW": "$DJI", "SPX": "$SPX", "$S&PX": "$SPX",
    "COMPX": "$COMPX", "NASDAQ": "NASDAQ", "NYSE": "NYSE", "OTCBB": "OTCBB",
}
_RENAME = {
    "description": "name", "lastPrice": "last", "netChange": "net_change",
    "netPercentChange": "pct_change", "totalVolume": "market_volume",
    "marketShare": "share_of_market_volume", "trades": "trades",
}


def _resolve_index(index: str) -> str:
    idx = (index or "").upper().strip()
    idx = _ALIAS_MAP.get(idx, idx)
    if not idx.startswith("$") and idx not in _VALID_INDEXES:
        cand = f"${idx}"
        if cand in _VALID_INDEXES:
            return cand
    return idx


@server.tool()
async def get_movers(index: str = "$SPX") -> str:
    """Top movers list from Schwab's movers screen (READ-ONLY).

    index: '$SPX' | '$DJI' | '$COMPX' | NASDAQ | NYSE | OTCBB |
    INDEX_ALL | EQUITY_ALL | OPTION_ALL | OPTION_PUT | OPTION_CALL.
    Lists only populate during REGULAR market hours (data may be empty or
    stale after the close). Rows: symbol, name, last, net_change,
    pct_change (percent), volume, market_volume, share_of_volume, trades,
    direction. Note the screen weights market volume SHARE, not raw % move.
    """
    try:
        idx = _resolve_index(index)
        c = await _get_client()
        async with _schwab_sem:
            r = await c.get_movers(idx)
        if r.status_code != 200:
            return _err(f"get_movers failed: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:300]} "
                        f"(valid: {sorted(_VALID_INDEXES)})")
        rows = []
        for m in (r.json().get("screeners") or []):
            rows.append({
                _RENAME.get(k, k): v
                for k, v in m.items()
                if k not in ("totalVolume", "marketShare")
            } | {
                "market_volume": m.get("totalVolume"),
                "share_of_market_volume": m.get("marketShare"),
                "pct_change": round((m.get("netPercentChange") or 0) * 100, 4),
            })
        if not rows:
            return _ok({"index": idx, "count": 0, "movers": rows,
                        "note": "empty — movers populate during regular hours"})
        return _ok({"index": idx, "count": len(rows), "movers": rows})
    except Exception as e:
        return _err(f"get_movers failed: {type(e).__name__}: {e}")
