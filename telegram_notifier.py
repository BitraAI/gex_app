"""Telegram notifier for GEX signal/alert events.

Reads BOT_TOKEN and CHAT_ID from ``config`` (populated from the ``[telegram]``
section of ``config.toml`` or the ``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID``
environment variables) and pushes formatted messages via the Telegram Bot API
over plain HTTPS.

We use stdlib ``urllib`` instead of ``python-telegram-bot`` because the latter
is fully async (v20+) and we need to fire alerts synchronously from Streamlit
scripts and background threads without an event loop. A send needs no special
auth flow, so a single POST to ``/sendMessage`` is sufficient.

All public functions are safe to call even when Telegram is disabled or
mis-configured: they simply become no-ops and return ``False`` so alert
delivery never crashes the host app.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Iterable, Optional

import config

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"



def _enabled() -> bool:
    """Return True only when Telegram alerts are enabled AND configured."""
    return bool(
        config.TELEGRAM_ENABLED
        and config.BOT_TOKEN
        and config.CHAT_ID
    )


def _http_post_json(url: str, payload: dict, *, timeout: float = 10.0) -> dict:
    """POST JSON to ``url`` and return the parsed JSON response.

    Raises ``RuntimeError`` on transport or API error responses.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        result = json.loads(body)
        raise RuntimeError(
            f"Telegram API error (HTTP {exc.code}): "
            f"{result.get('description', body)}"
        ) from exc
    result = json.loads(body)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result.get('description', body)}")
    return result.get("result", {})


def send_telegram(text: str, *, disable_notification: bool = False) -> bool:
    """Send a single HTML message to the configured Telegram chat.

    Returns ``True`` on success, ``False`` if disabled or on failure. Never
    raises — failures are logged so the calling app keeps running.
    """
    if not _enabled():
        return False

    url = f"{_API_BASE}/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": disable_notification,
        "disable_web_page_preview": True,
    }
    try:
        _http_post_json(url, payload)
        return True
    except Exception as exc:  # noqa: BLE001 — never let alerts crash the app
        logger.error("Telegram send failed: %s", exc)
        return False


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def notify_alerts(
    alerts: Iterable[str],
    *,
    symbol: Optional[str] = None,
    spot: Optional[float] = None,
    gex: Optional[float] = None,
    iv_rank: Optional[float] = None,
    wall_zone: Optional[str] = None,
    pw: Optional[float] = None,
    cw: Optional[float] = None,
    wall_mark: Optional[float] = None,
    trend_alert: Optional[str] = None,
    absorption: Optional[float] = None,
    absorbed_at_wall: Optional[float] = None,
    net_flow: Optional[float] = None,
    rv: Optional[float] = None,
    disable_notification: bool = True,
) -> bool:
    """Push a batch of alert strings to Telegram as one message.

    ``disable_notification=True`` (default) delivers the message silently,
    which is appropriate for routine GEX updates — flip ``False`` for
    urgent alerts so the recipient gets a sound.
    """
    alerts = list(alerts)
    if not alerts:
        return False
    text = _format(alerts, symbol=symbol, spot=spot, gex=gex, iv_rank=iv_rank,
                   wall_zone=wall_zone, pw=pw, cw=cw, wall_mark=wall_mark, trend_alert=trend_alert,
                   absorption=absorption, absorbed_at_wall=absorbed_at_wall,
                   net_flow=net_flow, rv=rv)
    return send_telegram(text, disable_notification=disable_notification)


def diff_alerts(
    prev: Optional[dict[str, Any]],
    analytics: dict[str, Any],
    spot: float,
) -> tuple[list[str], dict[str, Any]]:
    """Track per-symbol alert state across polls.

    Returns ``(new_alerts, next_state)``. The caller stores *next_state* as
    the new baseline; *new_alerts* is always empty — live alert generation is
    handled by ``maybe_fire_wall_zone_alerts``.
    """
    cur = {
        "gamma_flip": analytics.get("gamma_flip"),
        "call_wall": analytics.get("call_wall"),
        "put_wall": analytics.get("put_wall"),
        "dealer_position": analytics.get("dealer_position"),
        "spot": spot,
        "wall_zone": None,
        "atm_strike": analytics.get("atm_strike"),
    }

    return [], cur


def _format(alerts: Iterable[str], *, symbol: Optional[str], spot: Optional[float], gex: Optional[float] = None, iv_rank: Optional[float] = None, wall_zone: Optional[str] = None, pw: Optional[float] = None, cw: Optional[float] = None, wall_mark: Optional[float] = None, trend_alert: Optional[str] = None, absorption: Optional[float] = None, absorbed_at_wall: Optional[float] = None, net_flow: Optional[float] = None, rv: Optional[float] = None) -> str:
    """Build an HTML-formatted message from a list of alert strings."""
    # Trend alerts carry the flow-metric signal line, so those metrics are
    # folded into it instead of duplicated as separate header rows.
    _compact = trend_alert is not None
    header_lines = []
    if symbol:
        header_lines.append(f"<b>{_escape_html(symbol)}</b>")
    if spot is not None:
        header_lines.append(f"Price: <code>{spot:,.2f}</code>")
    if iv_rank is not None:
        emoji = "🟢" if iv_rank < 40 else "🔴" if iv_rank > 50 else "🟡"
        header_lines.append(f"{emoji} IV Rank: <code>{iv_rank:.1f}%</code>")
    if rv is not None and rv > 0:
        header_lines.append(f"RV: <code>{rv * 100:.1f}%</code>")
    if gex is not None:
        emoji = "🟢" if gex > 0 else "🔴"
        header_lines.append(f"{emoji} GEX: <code>{gex:,.0f}</code>")
    if wall_zone:
        emoji = "🟢" if wall_zone == "Support" else "🔴"
        wall_val = pw if wall_zone == "Support" else cw
        wall_tag = f"${wall_val:,.2f}" if wall_val is not None else "pw" if wall_zone == "Support" else "cw"
        header_lines.append(f"{emoji} Near {wall_zone} {wall_tag}")
    if absorption is not None and not _compact:
        emoji = "🟢" if absorption >= 1000 else "🔴" if absorption < 300 else "🟡"
        header_lines.append(f"{emoji} Absorption: <code>{absorption:,.0f}</code> vol/$1")
    if absorbed_at_wall is not None:
        header_lines.append(f"🟡 Wall absorbed: <code>{absorbed_at_wall:,.0f}</code> contracts")
    if net_flow is not None and not _compact:
        emoji = "🟢" if net_flow > 0 else "🔴" if net_flow < 0 else "🟡"
        header_lines.append(f"{emoji} Net Flow (60s): <code>{net_flow:+,.0f}</code>")
    body_lines = []
    if trend_alert:
        _buy = trend_alert in ("bullish", "up")
        emoji = "🟢" if _buy else "🔴"
        suggestion = "BUY CALL" if _buy else "BUY PUT"
        _segs = [f"{emoji} <b>{trend_alert.upper()}</b> - {suggestion}"]
        if wall_mark is not None:
            _segs[0] += f" ${wall_mark:,.2f}"
        if net_flow is not None:
            _segs.append(f"Net {net_flow:+,.0f}")
        if absorption is not None:
            _segs.append(f"Abs {absorption:,.0f}")
        body_lines.append(" · ".join(_segs))
    body_lines.extend(f"{_escape_html(a)}" for a in alerts if a)
    body = "\n".join(body_lines)
    if header_lines:
        return "\n".join(header_lines) + "\n" + body
    return body or "No alerts."
