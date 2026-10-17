"""get_market_hours — market session windows from the Schwab market-hours API."""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server

_MARKETS = {"EQUITY", "OPTION", "BOND", "FOREX"}   # no INDEX member in schwab-py


@server.tool()
async def get_market_hours(market: str = "EQUITY", date: str | None = None) -> str:
    """Trading-day session windows for one market (READ-ONLY).

    market: EQUITY | OPTION | BOND | FOREX (no INDEX market in the SDK).
    date: optional 'YYYY-MM-DD' (up to one year out); defaults to today.
    Returns each product's sessions (preMarket / regularMarket / postMarket
    and equivalents) with ET start/end times, or isOpen:false for holidays.
    """
    try:
        from datetime import date as _date, datetime as _datetime
        mk = (market or "").upper().strip()
        if mk not in _MARKETS:
            return _err(f"market must be one of {sorted(_MARKETS)}")
        d = _date.today()
        if date:
            try:
                d = _datetime.strptime(str(date).strip(), "%Y-%m-%d").date()
            except ValueError:
                return _err("date must be 'YYYY-MM-DD'")
        from schwab.client import AsyncClient
        marker = getattr(AsyncClient.MarketHours.Market, mk)
        c = await _get_client()
        async with _schwab_sem:
            r = await c.get_market_hours([marker], date=d)
        if r.status_code != 200:
            return _err(f"get_market_hours failed: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:300]}")
        return _ok({
            "market": mk, "date": d.isoformat(),
            "hours": r.json(),
        })
    except Exception as e:
        return _err(f"get_market_hours failed: {type(e).__name__}: {e}")
