"""Trading tools (equity): place buy/sell, cancel, and replace orders.

These are the ONLY non-read-only tools in the server, and every mutating call
is deliberately TWO-STEP: call with ``confirm=False`` (default) to get a
preview of the exact order spec Schwab will receive, then call again with
``confirm=True`` to execute. Nothing is submitted on preview.

Scope (v1, kept simple on purpose):
  - Equity instruments only (no options, no multi-leg).
  - MARKET or LIMIT orders, DAY or GTC durations, NORMAL session.
  - Long-quantity legs only: BUY and SELL (short sells rejected — use the
    Schwab web UI for those).
An order that would spend more than the account's available cash WILL still
round-trip to the API; use the preview output to check notional first.
"""

import hashlib
import json

from schwab_mcp.core import _err, _get_client, _ok, _schwab_sem, server

_SIDE_DOC = "BUY | SELL"
_TYPE_MAP = {"MARKET": "MARKET", "LIMIT": "LIMIT"}
_DURATION_MAP = {"DAY": "DAY", "GTC": "GOOD_TILL_CANCEL"}

_MAX_QUANTITY = 10_000          # sanity cap to make fat-finger calls loud
_NOTIONAL_WARN = 50_000.0       # preview flags any order above this
_OPEN_STATUSES = ("AWAITING_REVIEW", "AWAITING_MANUAL_REVIEW", "PENDING",
                  "PENDING_ACTIVATION", "PENDING_ACKNOWLEDGEMENT",
                  "QUEUED", "WORKING")


async def _resolve_account(c, account_last4: str | None) -> tuple[str, str]:
    """Return (account_hash, masked_account_number)."""
    async with _schwab_sem:
        nums = (await c.get_account_numbers()).json()
    if not nums:
        raise RuntimeError("no linked Schwab accounts returned")
    if account_last4:
        acct = next(
            (a for a in nums
             if str(a.get("accountNumber", ""))[-4:] == str(account_last4)[-4:]),
            None)
        if acct is None:
            have = ["****" + str(a.get("accountNumber", ""))[-4:] for a in nums]
            raise ValueError(
                f"no account ending in {account_last4}; available: {have}")
    else:
        acct = nums[0]
    return acct["hashValue"], "****" + str(acct.get("accountNumber", ""))[-4:]


def _build_equity_spec(side: str, symbol: str, quantity: int,
                       order_type: str, limit_price: float | None,
                       duration: str) -> dict:
    """Equity MARKET/LIMIT order spec via the SDK's builders."""
    from schwab.orders import equities as eq
    from schwab.orders.common import Duration
    symbol = symbol.upper().strip()
    if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
        raise ValueError(f"invalid equity symbol: {symbol!r}")
    qty = int(quantity)
    if qty <= 0 or qty > _MAX_QUANTITY:
        raise ValueError(f"quantity must be 1..{_MAX_QUANTITY}, got {quantity}")
    ot = _TYPE_MAP.get((order_type or "").upper())
    if ot is None:
        raise ValueError(f"order_type must be one of {sorted(_TYPE_MAP)}")
    if ot == "LIMIT":
        if limit_price is None or float(limit_price) <= 0:
            raise ValueError("LIMIT orders require a positive limit_price")
        builder = (eq.equity_buy_limit(symbol, qty, float(limit_price))
                   if side == "BUY" else
                   eq.equity_sell_limit(symbol, qty, float(limit_price)))
    else:
        if limit_price is not None:
            raise ValueError("MARKET orders must not carry a limit_price")
        builder = (eq.equity_buy_market(symbol, qty) if side == "BUY"
                   else eq.equity_sell_market(symbol, qty))
    dur = _DURATION_MAP.get((duration or "").upper())
    if dur is None:
        raise ValueError(f"duration must be one of {sorted(_DURATION_MAP)}")
    builder.set_duration(Duration(dur))
    return builder.build()


def _order_id_from(resp) -> str | None:
    """Schwab returns the created order id in the Location header."""
    loc = (getattr(resp, "headers", None) or {}).get("Location", "") \
        or (getattr(resp, "text", "") or "")
    loc = loc.strip()
    if not loc or loc.startswith("{") or " " in loc:
        return None
    return loc.rstrip("/").rsplit("/", 1)[-1]


async def _order_by_id(c, account_hash: str, order_id: str) -> tuple[int, dict]:
    async with _schwab_sem:
        r = await c.get_order(order_id, account_hash)
    try:
        body = r.json() if r.status_code == 200 else {}
    except Exception:
        body = {}
    return r.status_code, (body or {})


def _order_summary(src: dict) -> dict | None:
    """Summarize an order. Accepts either a securitiesAccount dict (from
    get_account) or a bare order object (get_order returns the order itself
    at the top level)."""
    if not isinstance(src, dict):
        return None
    if "orderStrategies" in src:
        candidates = src.get("orderStrategies") or []
    elif src.get("orderLegCollection") is not None:
        candidates = [src]
    else:
        candidates = []
    for o in candidates:
        legs = []
        for leg in (o.get("orderLegCollection") or []):
            legs.append({
                "instrument": (leg.get("instrument") or {}).get("symbol"),
                "instruction": leg.get("instruction"),
                "quantity": leg.get("quantity"),
            })
        return {
            "orderId": o.get("orderId"),
            "status": o.get("status"),
            "enteredTime": o.get("enteredTime"),
            "orderType": o.get("orderType"),
            "duration": o.get("duration"),
            "price": o.get("price"),
            "quantity": o.get("quantity"),
            "filledQuantity": o.get("filledQuantity"),
            "remainingQuantity": o.get("remainingQuantity"),
            "cancelable": o.get("cancelable"),
            "legs": legs,
        }
    return None


def _order_not_found(order_id: str, status_code: int | None) -> str:
    return _err(f"order {order_id} not found "
                f"(HTTP {status_code}); nothing to cancel")


async def _lookup_order(c, acct_hash: str, order_id: str) -> tuple[dict | None, int | None]:
    status_code, body = await _order_by_id(c, acct_hash, order_id)
    summary = _order_summary(body)
    return summary, (status_code if summary is None else None)


def _notional(spec: dict) -> float:
    leg = (spec.get("orderLegCollection") or [{}])[0]
    return float(spec.get("price") or 0) * float(leg.get("quantity") or 0)


def _spec_code(spec: dict) -> str:
    """Deterministic confirmation code derived from the order spec.

    The preview step returns this; the confirm step refuses to run unless
    the caller passes it back. This makes one-shot confirm calls impossible
    (confirm=true without a prior preview cannot know the code) and catches
    parameter drift between preview and confirm (any change to the spec
    invalidates the code).
    """
    return hashlib.sha256(
        json.dumps(spec, sort_keys=True).encode()).hexdigest()[:8]


def _code_mismatch(kind: str) -> str:
    return _err(
        f"{kind} refused: confirmation_code missing or incorrect. "
        "Call this tool FIRST with confirm=false to get a preview and its "
        "confirmation_code, present BOTH to the user, and only after an "
        "explicit affirmative reply re-call with confirm=true plus that "
        "code. A confirm call without a preview is always rejected.")


def _notes(spec: dict) -> list[str]:
    notes = []
    if not _notional(spec):
        notes.append("MARKET order — fill price unknown until execution")
    elif _notional(spec) >= _NOTIONAL_WARN:
        notes.append(f"NOTE: notional ≈ ${_notional(spec):,.2f}")
    return notes


# shared core for both place tools
async def _place(side: str, symbol: str, quantity: int, order_type: str,
                 limit_price: float | None, duration: str,
                 account_last4: str | None, confirm: bool,
                 confirmation_code: str | None) -> str:
    try:
        c = await _get_client()
        acct_hash, acct_masked = await _resolve_account(c, account_last4)
        spec = _build_equity_spec(side, symbol, quantity, order_type,
                                  limit_price, duration)
        code = _spec_code(spec)
        if not confirm:
            return _ok({
                "action": f"{side}_PREVIEW",
                "account": acct_masked,
                "executed": False,
                "confirmation_code": code,
                "orderSpec": spec,
                "notionalIfLimit": round(_notional(spec), 2) or None,
                "notes": _notes(spec),
                "to_execute": ("present this preview AND the "
                               "confirmation_code to the user for approval; "
                               "then re-call with confirm=true, "
                               "confirmation_code=<code from this preview>"),
            })
        if confirmation_code != code:
            return _code_mismatch(f"place_{side.lower()}_order")
        async with _schwab_sem:
            r = await c.place_order(acct_hash, spec)
        if r.status_code not in (200, 201):
            return _err(f"place_order rejected: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:400]}")
        order_id = _order_id_from(r)
        status_code, acc = (await _order_by_id(c, acct_hash, order_id)
                            if order_id else (None, {}))
        return _ok({
            "action": f"{side}_PLACED",
            "account": acct_masked,
            "order_id": order_id,
            "http_status": r.status_code,
            "order_status": _order_summary(acc),
        })
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"place {side.lower()} failed: {type(e).__name__}: {e}")


@server.tool()
async def place_buy_order(symbol: str, quantity: int, order_type: str = "LIMIT",
                          limit_price: float | None = None,
                          duration: str = "DAY",
                          account_last4: str | None = None,
                          confirm: bool = False,
                          confirmation_code: str | None = None) -> str:
    """Place an equity BUY order (three-step confirmation).

    Step 1 — call with confirm=false (default): returns a PREVIEW of the exact
    order spec plus a confirmation_code, and submits NOTHING.
    Step 2 — present the preview AND confirmation_code to the user and wait
    for their explicit approval.
    Step 3 — only after an affirmative user reply, re-call with confirm=true
    AND confirmation_code=<code from the preview>. Without the correct code
    the order is rejected and nothing reaches Schwab.

    symbol: equity symbol (e.g. "AAPL"). quantity: shares (1..10000).
    order_type: MARKET | LIMIT (LIMIT requires limit_price).
    limit_price: required for LIMIT. duration: DAY | GTC.
    account_last4: optional, defaults to the first linked account.
    """
    return await _place("BUY", symbol, quantity, order_type, limit_price,
                        duration, account_last4, confirm, confirmation_code)


@server.tool()
async def place_sell_order(symbol: str, quantity: int, order_type: str = "LIMIT",
                           limit_price: float | None = None,
                           duration: str = "DAY",
                           account_last4: str | None = None,
                           confirm: bool = False,
                           confirmation_code: str | None = None) -> str:
    """Place an equity SELL order (three-step confirmation).

    Sells existing LONG shares (short-selling is rejected; use the Schwab UI).
    Same three steps as place_buy_order: preview (confirm=false) → user
    approval of preview + confirmation_code → confirm=true with that code.
    """
    return await _place("SELL", symbol, quantity, order_type, limit_price,
                        duration, account_last4, confirm, confirmation_code)


@server.tool()
async def cancel_order(order_id: str, account_last4: str | None = None,
                       confirm: bool = False) -> str:
    """Cancel an open order (READ-ONLY UNTIL confirm=true).

    Two-step safety: with confirm=false (default) this returns the order's
    CURRENT status (nothing is canceled — already-filled/canceled orders are
    flagged). Re-call with confirm=true to actually cancel.

    order_id: the Schwab order id as returned by place_*_order.
    """
    try:
        c = await _get_client()
        acct_hash, acct_masked = await _resolve_account(c, account_last4)
        order_id = str(order_id).strip()
        summary, miss = await _lookup_order(c, acct_hash, order_id)
        if not confirm:
            if summary is None:
                return _order_not_found(order_id, miss)
            warn = None
            if summary.get("status") not in _OPEN_STATUSES:
                warn = (f"order status is {summary.get('status')!r} — cancel "
                        f"will likely be rejected or a no-op")
            return _ok({
                "action": "CANCEL_PREVIEW", "account": acct_masked,
                "executed": False, "order_id": order_id,
                "current_order": summary, "warning": warn,
                "to_execute": "re-call this tool with confirm=true to cancel",
            })
        async with _schwab_sem:
            r = await c.cancel_order(order_id, acct_hash)
        if r.status_code not in (200, 201, 204):
            return _err(f"cancel_order rejected: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:300]}")
        status_code, acc = await _order_by_id(c, acct_hash, order_id)
        return _ok({
            "action": "CANCELED", "account": acct_masked,
            "order_id": order_id, "http_status": r.status_code,
            "order_status_after": _order_summary(acc),
        })
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"cancel_order failed: {type(e).__name__}: {e}")


@server.tool()
async def replace_order(order_id: str, quantity: int | None = None,
                        limit_price: float | None = None,
                        order_type: str | None = None,
                        duration: str | None = None,
                        account_last4: str | None = None,
                        confirm: bool = False,
                        confirmation_code: str | None = None) -> str:
    """Replace (modify) an open equity order (three-step confirmation).

    Step 1 — call with confirm=false (default): previews the new spec versus
    the live order, plus a confirmation_code for the replacement. NOTHING is
    submitted.
    Step 2 — present preview + confirmation_code to the user, wait for
    explicit approval.
    Step 3 — re-call with confirm=true AND confirmation_code=<preview code>.
    The old order is canceled and a new one created (new order id).

    Only the parameters you pass are changed; everything else keeps the live
    order's values. Supports MARKET/LIMIT equity; complex/multi-leg rejected.
    """
    try:
        c = await _get_client()
        acct_hash, acct_masked = await _resolve_account(c, account_last4)
        order_id = str(order_id).strip()
        live, miss = await _lookup_order(c, acct_hash, order_id)
        if live is None:
            return _order_not_found(order_id, miss)
        if live.get("status") not in _OPEN_STATUSES:
            return _err(f"cannot replace order in status {live.get('status')!r}")
        legs = live.get("legs") or []
        if len(legs) != 1 or not (legs[0].get("instrument") or ""):
            return _err("replace_order supports single-leg equity orders only")
        leg = legs[0]
        symbol = (leg.get("instrument") or "").upper()
        side = (leg.get("instruction") or "").split("_")[-1].upper()
        if side not in ("BUY", "SELL") or not symbol:
            return _err(f"cannot derive side/symbol from legs {legs}; "
                        "only simple equity BUY/SELL orders are supported")
        new_qty = int(quantity) if quantity is not None else int(leg.get("quantity") or 0)
        new_type = (order_type or str(live.get("orderType") or "LIMIT")).upper()
        new_type = "MARKET" if "MARKET" in new_type else "LIMIT"
        new_price = (limit_price if limit_price is not None
                     else (float(live.get("price")) if live.get("price") else None))
        new_dur = duration or "DAY"
        if new_type == "LIMIT" and (new_price is None or new_price <= 0):
            return _err("replacement LIMIT order needs a positive limit_price "
                        "(live order has none; pass limit_price explicitly)")
        spec = _build_equity_spec(side, symbol, new_qty, new_type,
                                  new_price, new_dur)
        code = _spec_code(spec)
        if not confirm:
            return _ok({
                "action": f"REPLACE_{side}_PREVIEW", "account": acct_masked,
                "executed": False, "order_id": order_id,
                "confirmation_code": code,
                "current_order": live,
                "new_orderSpec": spec,
                "notionalIfLimit": round(float(new_price or 0) * new_qty, 2) or None,
                "to_execute": ("present this preview AND the "
                               "confirmation_code to the user for approval; "
                               "then re-call with confirm=true, "
                               "confirmation_code=<code from this preview>"),
            })
        if confirmation_code != code:
            return _code_mismatch("replace_order")
        async with _schwab_sem:
            r = await c.replace_order(acct_hash, order_id, spec)
        if r.status_code not in (200, 201, 204):
            return _err(f"replace_order rejected: HTTP {r.status_code}: "
                        f"{(getattr(r, 'text', '') or '')[:400]}")
        new_id = _order_id_from(r)
        status_code, acc_new = (await _order_by_id(c, acct_hash, new_id)
                                if new_id else (None, {}))
        return _ok({
            "action": f"REPLACED_{side}", "account": acct_masked,
            "old_order_id": order_id, "new_order_id": new_id,
            "http_status": r.status_code,
            "order_status_after": _order_summary(acc_new),
        })
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"replace_order failed: {type(e).__name__}: {e}")
