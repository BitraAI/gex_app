"""get_option_chain — per-contract marks, greeks, volume, open interest."""

from datetime import date, timedelta

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server


@server.tool()
async def get_option_chain(
    symbol: str,
    strike_count: int = 50,
    max_dte: int = 60,
    expiration: str | None = None,
) -> str:
    """Option chain with greeks and open interest per contract.

    symbol: underlying (e.g. SPY, NVDA, SPX).
    strike_count: strikes each side of the money (Schwab API param, max ~50).
    max_dte: only return contracts expiring within this many days (0 = today+1).
    expiration: optional 'YYYY-MM-DD' filter for a single expiry.
    Returns rows: symbol, strike, type (CALL/PUT), dte, mark, bid, ask,
    lastPrice, volume, openInterest, delta, gamma, theta, vega.
    """
    try:
        from scripts.client import fetch_option_chain
        from_date = date.today().isoformat()
        to_date = (date.today() + timedelta(days=420)).isoformat()
        async with _schwab_sem:
            raw = await fetch_option_chain(
                await _get_client(), symbol,
            strike_count=strike_count, from_date=from_date, to_date=to_date,
        )
        if isinstance(raw, dict) and raw.get("errors"):
            return _err(f"chain API error: {raw['errors']}")
        rows = []
        def _scan(node: dict) -> None:
            for exp_key, strikes in node.items():
                for strike_str, opts in strikes.items():
                    for opt in opts:
                        pc = (opt.get("putCall") or "").upper()
                        if pc not in ("CALL", "PUT"):
                            continue
                        g = opt.get("greeks") or {}
                        rows.append({
                            "symbol": opt.get("symbol"),
                            "expiration": opt.get("expirationDate") or exp_key.split(":")[0],
                            "strike": float(strike_str),
                            "type": pc,
                            "mark": opt.get("mark"),
                            "bid": opt.get("bid"),
                            "ask": opt.get("ask"),
                            "lastPrice": opt.get("last"),
                            "volume": opt.get("totalVolume") or 0,
                            "openInterest": opt.get("openInterest") or 0,
                            "daysToExpiration": opt.get("daysToExpiration"),
                            "delta": g.get("delta"),
                            "gamma": g.get("gamma"),
                            "theta": g.get("theta"),
                            "vega": g.get("vega"),
                        })
        chain = raw.get("optionChain") if isinstance(raw, dict) else None
        if isinstance(chain, list):
            for entry in chain:
                _scan(entry.get("callExpDateMap") or {})
                _scan(entry.get("putExpDateMap") or {})
        elif isinstance(raw, dict):
            _scan(raw.get("callExpDateMap") or {})
            _scan(raw.get("putExpDateMap") or {})
        if expiration:
            rows = [r_ for r_ in rows if str(r_["expiration"]).startswith(expiration)]
        if max_dte is not None and max_dte >= 0:
            rows = [r_ for r_ in rows if isinstance(r_["daysToExpiration"], int)
                    and r_["daysToExpiration"] <= max_dte]
        if not rows:
            return _err("no contracts matched the filters")
        spot = None
        und = raw.get("underlying") if isinstance(raw, dict) else None
        if und:
            spot = und.get("mark") or und.get("last")
        return _ok({"symbol": symbol, "spot": spot, "contracts": len(rows), "rows": rows})
    except Exception as e:
        return _err(f"get_option_chain failed: {type(e).__name__}: {e}")
