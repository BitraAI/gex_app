"""get_positions — account balances and open positions (read-only)."""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server


@server.tool()
async def get_positions() -> str:
    """Open positions and balances for the linked Schwab account (READ-ONLY).

    Returns per-position symbol, side (LONG/SHORT), quantity, average price,
    market value and day change, plus key account balances. Account number is
    truncated to the last 4 digits.
    """
    try:
        from schwab.client import AsyncClient
        c = await _get_client()
        async with _schwab_sem:
            nums = (await c.get_account_numbers()).json()
        accounts = []
        for acct in nums:
            h = acct["hashValue"]
            async with _schwab_sem:
                acc = (await c.get_account(h, fields=AsyncClient.Account.Fields.POSITIONS)).json()
            sa = acc.get("securitiesAccount", {})
            positions = sa.get("positions") or []
            plist = []
            for p in positions:
                inv = p.get("instrument", {})
                lq = float(p.get("longQuantity") or 0)
                sq = float(p.get("shortQuantity") or 0)
                qty = lq - sq
                plist.append({
                    "symbol": inv.get("symbol"),
                    "description": inv.get("description"),
                    "side": "LONG" if qty > 0 else ("SHORT" if qty < 0 else "FLAT"),
                    "quantity": qty,
                    "averagePrice": p.get("averagePrice"),
                    "marketValue": p.get("marketValue"),
                    "dayChange": p.get("currentDayProfitLoss"),
                    "type": inv.get("assetType"),
                })
            bal = sa.get("currentBalances") or {}
            init = sa.get("initialBalances") or {}
            accounts.append({
                "account": "****" + acct.get("accountNumber", "")[-4:],
                "type": sa.get("type"),
                "positions": plist,
                "balances": {
                    "cash": bal.get("cashBalance"),
                    "longMarketValue": bal.get("longMarketValue") or init.get("longStockValue"),
                    "shortMarketValue": bal.get("shortMarketValue"),
                    "equity": init.get("equity"),
                    "moneyMarketFund": bal.get("moneyMarketFund"),
                    "buyingPower": init.get("buyingPower"),
                },
            })
        return _ok({"accounts": accounts})
    except Exception as e:
        return _err(f"get_positions failed: {type(e).__name__}: {e}")
