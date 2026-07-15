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
import urllib.request
from typing import Any, Iterable, Optional

import config

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"


# Analytics keys that participate in the per-symbol alert diff. Sharing this
# list keeps the Streamlit ``check_alerts`` and the standalone cron runner
# (``telegram_alerts.py``) in lock-step.
ALERT_STATE_FIELDS = ("gamma_flip", "call_wall", "put_wall", "dealer_position", "spot")


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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    result = json.loads(body)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result.get('description', body)}")
    return result.get("result", {})


def send_telegram(text: str, *, disable_notification: bool = False) -> bool:
    """Send a single Markdown message to the configured Telegram chat.

    Returns ``True`` on success, ``False`` if disabled or on failure. Never
    raises — failures are logged so the calling app keeps running.
    """
    if not _enabled():
        return False

    url = f"{_API_BASE}/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": disable_notification,
        "disable_web_page_preview": True,
    }
    try:
        _http_post_json(url, payload)
        return True
    except Exception as exc:  # noqa: BLE001 — never let alerts crash the app
        logger.error("Telegram send failed: %s", exc)
        return False


def _format(alerts: Iterable[str], *, symbol: Optional[str], spot: Optional[float]) -> str:
    """Build a Markdown-formatted message from a list of alert strings."""
    header_lines = []
    if symbol:
        header_lines.append(f"*{symbol}*")
    if spot is not None:
        header_lines.append(f"Spot: `${spot:,.2f}`")
    body = "\n".join(f"• {a}" for a in alerts if a)
    if header_lines:
        return "\n".join(header_lines) + "\n" + body
    return body or "No alerts."


def notify_alerts(
    alerts: Iterable[str],
    *,
    symbol: Optional[str] = None,
    spot: Optional[float] = None,
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
    text = _format(alerts, symbol=symbol, spot=spot)
    return send_telegram(text, disable_notification=disable_notification)


def diff_alerts(
    prev: Optional[dict[str, Any]],
    analytics: dict[str, Any],
    spot: float,
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
    }

    if not prev:
        return [], cur

    new_alerts: list[str] = []

    gf = cur["gamma_flip"]
    prev_gf = prev.get("gamma_flip")
    if gf != prev_gf and prev_gf is not None and gf is not None:
        new_alerts.append(f"Gamma Flip changed: ${prev_gf:.2f} → ${gf:.2f}")

    cw = cur["call_wall"]
    prev_cw = prev.get("call_wall")
    if cw != prev_cw and prev_cw is not None and cw is not None:
        new_alerts.append(f"Call Wall changed: ${prev_cw:.2f} → ${cw:.2f}")

    pw = cur["put_wall"]
    prev_pw = prev.get("put_wall")
    if pw != prev_pw and prev_pw is not None and pw is not None:
        new_alerts.append(f"Put Wall changed: ${prev_pw:.2f} → ${pw:.2f}")

    dp = cur["dealer_position"]
    prev_dp = prev.get("dealer_position")
    if prev_dp == "Long Gamma" and dp == "Short Gamma":
        new_alerts.append("Dealer flipped from Long Gamma to Short Gamma")
    elif prev_dp == "Short Gamma" and dp == "Long Gamma":
        new_alerts.append("Dealer flipped from Short Gamma to Long Gamma")

    prev_spot = prev.get("spot")
    if prev_spot is not None:
        _BUFFER = 0.0002  # 0.02 %
        if cw is not None:
            cw_buf = abs(cw) * _BUFFER
            if prev_spot < cw and spot >= cw - cw_buf:
                new_alerts.append(f"Price approaching Call Wall (${cw:.2f})")
        if pw is not None:
            pw_buf = abs(pw) * _BUFFER
            if prev_spot <= pw + pw_buf and spot > pw:
                new_alerts.append(f"Price approaching Put Wall (${pw:.2f})")

    return new_alerts, cur
