"""get_spot — live quotes for one or more symbols."""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server


@server.tool()
async def get_spot(symbols: list[str]) -> str:
    """Live quotes for one or more symbols: last price, mark, bid/ask, net change.

    symbols: list like ["SPY", "QQQ"]. Index symbols use their ETF proxy mapping
    where the OAuth API requires it (SPX -> $SPX is handled internally).
    """
    try:
        from client import fetch_quotes
        async with _schwab_sem:
            quotes = await fetch_quotes(await _get_client(), symbols)
        out = {}
        for sym, q in (quotes or {}).items():
            if not isinstance(q, dict):
                continue
            # schwab-py 2.x nests the live quote fields; older responses have
            # them at the top level.
            fields = q.get("quote") if isinstance(q.get("quote"), dict) else q
            out[sym] = {
                "lastPrice": fields.get("lastPrice"),
                "mark": fields.get("mark"),
                "closePrice": fields.get("closePrice"),
                "netChange": fields.get("netChange"),
                "netPercentChange": fields.get("netPercentChange"),
                "totalVolume": fields.get("totalVolume"),
                "bid": fields.get("bidPrice"),
                "ask": fields.get("askPrice"),
                "quoteTime": fields.get("quoteTimeInLong") or fields.get("quoteTime"),
                "regularMarketLastPrice": (q.get("regular") or {}).get("lastPrice"),
                "extendedLastPrice": (q.get("extended") or {}).get("lastPrice"),
            }
        return _ok(out) if out else _err("no quotes returned")
    except Exception as e:
        return _err(f"get_spot failed: {type(e).__name__}: {e}")
