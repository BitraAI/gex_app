"""get_transactions — account transaction history (read-only)."""

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server

_MAX_DAYS = 60   # Schwab API hard limit for the transactions window


def _mask_acct(acct_number) -> str:
    return "****" + str(acct_number or "")[-4:]


@server.tool()
async def get_transactions(days: int = 30, account_last4: str | None = None) -> str:
    """Transaction history for the linked account, last N days (READ-ONLY).

    days: lookback window, 1..60 (Schwab API hard limit is 60 days).
    account_last4: optional account selector; defaults to the first one.
    Returns one row per transaction: date, time, type (e.g.
    DIVIDEND_OR_INTEREST, TRADE, CASH...), description, net_amount
    (positive = credit), sub_account, and instrument legs when present.
    """
    try:
        from datetime import date, timedelta
        n = int(days)
        if n < 1:
            return _err("days must be >= 1")
        if n > _MAX_DAYS:
            return _err(f"days capped at {_MAX_DAYS} (Schwab API limit)")
        c = await _get_client()
        async with _schwab_sem:
            nums = (await c.get_account_numbers()).json()
        if not nums:
            return _err("no linked Schwab accounts returned")
        acct = next(
            (a for a in nums
             if account_last4
             and str(a.get("accountNumber", ""))[-4:] == str(account_last4)[-4:]),
            nums[0])
        e = acct["hashValue"]
        masked = _mask_acct(acct.get("accountNumber"))
        end = date.today()
        start = end - timedelta(days=n)
        async with _schwab_sem:
            r = await c.get_transactions(e, start_date=start, end_date=end)
        if r.status_code != 200:
            return _err(f"get_transactions failed: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:300]}")
        txs = r.json() or []
        rows = []
        for t in txs:
            legs = []
            for item in (t.get("transferItems") or []):
                instr = item.get("instrument") or {}
                legs.append({
                    "symbol": instr.get("symbol"),
                    "assetType": instr.get("assetType"),
                    "amount": item.get("amount"),
                })
            rows.append({
                "date": (t.get("tradeDate") or "")[:10],
                "time": t.get("time"),
                "type": t.get("type"),
                "description": t.get("description"),
                "net_amount": t.get("netAmount"),
                "sub_account": t.get("subAccount"),
                "status": t.get("status"),
                "settlementDate": (t.get("settlementDate") or "")[:10] or None,
                "legs": legs,
            })
        rows.sort(key=lambda x: x.get("date") or "", reverse=True)
        total = sum((x.get("net_amount") or 0) for x in rows)
        return _ok({
            "account": masked,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "count": len(rows),
            "net_cash_change": round(total, 2),
            "transactions": rows,
        })
    except Exception as e:
        return _err(f"get_transactions failed: {type(e).__name__}: {e}")
