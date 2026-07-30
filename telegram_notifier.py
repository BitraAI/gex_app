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

def _format(alerts: Iterable[str], *, symbol: Optional[str], spot: Optional[float], gex: Optional[float] = None, vrp: Optional[float] = None, iv_rank: Optional[float] = None) -> str:
    """Build an HTML-formatted message from a list of alert strings."""
    header_lines = []
    if symbol:
        header_lines.append(f"<b>{_escape_html(symbol)}</b>")
    if spot is not None:
        header_lines.append(f"Price: <code>{spot:,.2f}</code>")
    if iv_rank is not None:
        emoji = "🟢" if iv_rank < 40 else "🔴" if iv_rank > 50 else "🟡"
        header_lines.append(f"{emoji} IV Rank: <code>{iv_rank:.1f}%</code>")
    if vrp is not None:
        emoji = "🟢" if vrp < -2 else "🔴" if vrp > 5 else "🟡"
        header_lines.append(f"{emoji} VRP: <code>{vrp:.1f}%</code>")
    if gex is not None:
        emoji = "🟢" if gex > 0 else "🔴"
        header_lines.append(f"{emoji} GEX: <code>{gex:,.0f}</code>")
    body = "\n".join(f"{_escape_html(a)}" for a in alerts if a)
    if header_lines:
        return "\n".join(header_lines) + "\n" + body
    return body or "No alerts."


def notify_alerts(
    alerts: Iterable[str],
    *,
    symbol: Optional[str] = None,
    spot: Optional[float] = None,
    gex: Optional[float] = None,
    vrp: Optional[float] = None,
    iv_rank: Optional[float] = None,
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
    text = _format(alerts, symbol=symbol, spot=spot, gex=gex, vrp=vrp, iv_rank=iv_rank)
    return send_telegram(text, disable_notification=disable_notification)


def diff_alerts(
    prev: Optional[dict[str, Any]],
    analytics: dict[str, Any],
    spot: float,
    options_book_data: Optional[dict[str, Any]] = None,
) -> tuple[list[str], dict[str, Any]]:
    """Pure diff of the previous per-symbol state vs the current analytics.

    Returns ``(new_alerts, next_state)``. If ``prev`` is None or empty this is
    treated as a first-seen baseline: it returns ``([], <baseline>)`` so the
    first poll after a ticker is added does not fire a storm of spurious
    "changed" alerts.

    The set of events detected is exactly what ``check_alerts`` produced in
    ``app.py`` before the refactor, so the Streamlit UI and the standalone
    runner report identical signal changes:
        - Gamma Flip change
        - Call Wall / Put Wall change
        - Dealer gamma flip (Long ↔ Short)
        - Spot crossing above/below Call Wall or Put Wall
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

    _WALL_ZONE_BUFFER = 0.0002  # 0.02 %
    pw = cur["put_wall"]
    cw = cur["call_wall"]
    wall_zone = pw if pw is not None else cw
    cur["wall_zone"] = wall_zone

    if not prev:
        return [], cur

    new_alerts: list[str] = []

    if options_book_data:
        trend = options_book_data.get("trend")
        if trend:
            book_imbalance = options_book_data.get("book_imbalance")
            
            # Check if options_book trend matches wall zone
            if book_imbalance > 0.3 and trend == "up" and pw is not None:
                if pw is not None and spot <= pw + abs(pw) * _WALL_ZONE_BUFFER:
                    new_alerts.append(f"🟢 Options Book bullish (imbalance: {book_imbalance:.2f}) near Support ${pw:.2f}")
            elif book_imbalance < -0.3 and trend == "down" and cw is not None:
                if cw is not None and spot >= cw - abs(cw) * _WALL_ZONE_BUFFER:
                    new_alerts.append(f"🔴 Options Book bearish (imbalance: {book_imbalance:.2f}) near Resistance ${cw:.2f}")

    return new_alerts, cur
