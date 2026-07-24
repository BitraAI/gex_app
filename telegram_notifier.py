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
from datetime import datetime
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

import config

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"

_NY_TZ = ZoneInfo("America/New_York")


def _enabled() -> bool:
    """Return True only when Telegram alerts are enabled AND configured."""
    return bool(
        config.TELEGRAM_ENABLED
        and config.BOT_TOKEN
        and config.CHAT_ID
    )


def _is_market_open() -> bool:
    """Return True iff US regular equity trading hours are currently open
    (09:30–16:00 America/New_York, Mon–Fri, excluding a fixed subset of
    major holidays).

    Kept here in isolation (rather than importing ``flow.is_market_open``)
    so ``telegram_notifier`` stays leaf-of-dependency and can be called
    safely from any module without risking a circular import.  The
    semantics intentionally mirror ``flow.is_market_open`` so the in-app
    UI and every alert path see the same market-hours verdict.
    """
    now = datetime.now(_NY_TZ)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    _open  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    _close = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    if not (_open <= now <= _close):
        return False
    # Major US market holidays (fixed/observed subset).
    if (now.month, now.day) in {(1, 1), (7, 4), (12, 25)}:
        return False
    return True


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


def _format(alerts: Iterable[str], *, symbol: Optional[str],
            spot: Optional[float], gex: Optional[float],
            front_vrp: Optional[float] = None) -> str:
    """Build a Markdown-formatted message from a list of alert strings."""
    header_lines = []
    if symbol:
        header_lines.append(f"*{symbol}*")
    if spot is not None:
        header_lines.append(f"Price: `${spot:,.2f}`")
    if gex is not None:
        # Show Net GEX as billions for readability (analytics["net_gex"] is
        # already in raw gamma × OI × spot² units, which scale to ~billions
        # for major underlyings).  Use a compact format with a sign so the
        # polarity (Long vs Short gamma) is visible at a glance.
        _sign = "+" if gex >= 0 else ""
        _emoji = "🟢" if gex >= 0 else "🔴"
        header_lines.append(f"{_emoji} GEX: `{_sign}{gex / 1e9:.2f}B`")
    if front_vrp is not None:
        # Front-expiration VRP (IV − RV, in percentage points): > +2 means
        # the front options are expensive (rich), < -2 means cheap.  Use a
        # sign so premium/cheap side is visible at a glance.
        _vsign = "+" if front_vrp >= 0 else ""
        header_lines.append(f"VRP: `{_vsign}{front_vrp:.2f}%`")
    body = "\n".join(f"• {a}" for a in alerts if a)
    if header_lines:
        return "\n".join(header_lines) + "\n" + body
    return body or "No alerts."


def notify_alerts(
    alerts: Iterable[str],
    *,
    symbol: Optional[str] = None,
    spot: Optional[float] = None,
    gex: Optional[float] = None,
    front_vrp: Optional[float] = None,
    disable_notification: bool = True,
) -> bool:
    """Push a batch of alert strings to Telegram as one message.

    ``disable_notification=True`` (default) delivers the message silently,
    which is appropriate for routine GEX updates — flip ``False`` for
    urgent alerts so the recipient gets a sound.

    ``gex`` is the Net GEX (positive = dealer Long Gamma) of the symbol
    the alert concerns; it is rendered as a header line for context and
    is *not* itself an alert (i.e. transitions in GEX still come through
    ``diff_alerts`` as their own alert strings).

    ``front_vrp`` is the front-expiration Volatility Risk Premium
    (IV − RV in percentage points); for tracked tickers it's passed in
    by the caller.  Rendered as a header line right under GEX.
    """
    alerts = list(alerts)
    if not alerts:
        return False
    if not _is_market_open():
        # Don't push alerts outside US RTH — even when the dashboard is
        # left running on a remote host, the bot stays silent on nights,
        # weekends and holidays. ``diff_alerts`` already persists the
        # new per-symbol state in ``st.session_state`` so the first
        # in-hours tick won't replay a flood of "X changed" alerts.
        logger.debug("suppressing %d alert(s) — outside US RTH", len(alerts))
        return False
    text = _format(alerts, symbol=symbol, spot=spot, gex=gex, front_vrp=front_vrp)
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
        "wall_zone": None,
    }

    _BUFFER = 0.0005  # 0.05 %
    pw = cur["put_wall"]
    cw = cur["call_wall"]
    if pw is not None and spot <= pw + abs(pw) * _BUFFER:
        cur["wall_zone"] = "support"
    elif cw is not None and spot >= cw - abs(cw) * _BUFFER:
        cur["wall_zone"] = "resistance"

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

    prev_zone = prev.get("wall_zone")
    cur_zone = cur["wall_zone"]
    if cur_zone != prev_zone and (cur_zone in {"support", "resistance"}):
        if cur_zone == "support":
            zone_line = "🟢 Near Support"
            pw_str = f"${pw:.2f}" if pw is not None else "N/A"
            signal_line = f"Signal: BUY CALL {pw_str}"
        else:
            zone_line = "🔴 Near Resistance"
            cw_str = f"${cw:.2f}" if cw is not None else "N/A"
            signal_line = f"Signal: BUY PUT {cw_str}"
        new_alerts.append(zone_line)
        new_alerts.append(signal_line)

    return new_alerts, cur
