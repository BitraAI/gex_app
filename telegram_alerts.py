"""Standalone Telegram alerts runner.

Polls every ticker in ``~/.local/share/gex_app/ticker_history.json``, fetches
its option chain via the Schwab API, runs the GEX analytics pipeline, and pushes
Telegram alerts when key GEX events fire:
    - Gamma Flip change
    - Call Wall / Put Wall change
    - Dealer gamma flip (Long ↔ Short)
    - Spot crossing above/below Call Wall or Put Wall

By default the runner only operates during US regular trading hours
(Mon–Fri 09:30–16:00 America/New_York). Use ``--outside-rth`` to poll outside
RTH (e.g. for futures or extended-hours tickers).

Per-symbol previous state is persisted to
``~/.local/share/gex_app/alert_state.json`` so consecutive runs detect true
transitions rather than re-broadcasting the current state on every run.

Usage::

    # Run once (what cron invokes):
    uv run python telegram_alerts.py

    # Loop forever, polling every N seconds (default 300s = 5 min):
    uv run python telegram_alerts.py --loop --interval 300

    # Force a run even outside market hours (testing):
    uv run python telegram_alerts.py --outside-rth

    # Dry-run: compute analytics + diff but do not send Telegram messages
    uv run python telegram_alerts.py --dry-run

Exit codes:
    0  success (or skipped outside RTH)
    1  unrecoverable error (e.g. no tickers, Schwab auth failure)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import config
from analytics import compute_analytics
from calculations import build_greeks_lookup, parse_option_chain
from client import (
    create_client,
    fetch_option_chain,
    get_interest_rate,
    get_yield,
)
from telegram_notifier import diff_alerts, notify_alerts

logger = logging.getLogger("telegram_alerts")

_BASE_DIR = os.path.expanduser("~/.local/share/gex_app")
TICKER_HISTORY_FILE = os.path.join(_BASE_DIR, "ticker_history.json")
ALERT_STATE_FILE = os.path.join(_BASE_DIR, "alert_state.json")
_STRIKE_COUNT = 75
# Index symbols lack Greeks in the Schwab response; mirror app.py's fallback map.
_FALLBACK_SYMBOLS = {
    "SPX": "SPY", "SPXW": "SPY",
    "RUT": "IWM", "RUTW": "IWM",
    "NDX": "QQQ", "NDXP": "QQQ",
}
_NY_TZ = ZoneInfo("America/New_York")


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _load_tickers() -> list[str]:
    try:
        with open(TICKER_HISTORY_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(s) for s in data if s]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def _load_state() -> dict[str, dict[str, Any]]:
    try:
        with open(ALERT_STATE_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def _save_state(state: dict[str, dict[str, Any]]) -> None:
    os.makedirs(_BASE_DIR, exist_ok=True)
    tmp = ALERT_STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, ALERT_STATE_FILE)


# ---------------------------------------------------------------------------
# Market-hours guard
# ---------------------------------------------------------------------------

def within_rth(now: Optional[datetime] = None) -> bool:
    """True iff ``now`` falls within US regular trading hours."""
    now = now or datetime.now(timezone.utc)
    ny = now.astimezone(_NY_TZ)
    # NYSE weekend: weekday() 5=Sat, 6=Sun
    if ny.weekday() >= 5:
        return False
    mins = ny.hour * 60 + ny.minute
    return (9 * 60 + 30) <= mins < (16 * 60)


# ---------------------------------------------------------------------------
# Per-ticker analytics
# ---------------------------------------------------------------------------

async def _compute_for_symbol(client, symbol: str) -> Optional[dict[str, Any]]:
    """Fetch the chain and compute analytics for one symbol."""
    try:
        raw = await fetch_option_chain(
            client, symbol, strike_count=_STRIKE_COUNT, include_quotes=True,
        )
    except Exception as exc:
        logger.error("fetch_option_chain failed for %s: %s", symbol, exc)
        return None

    try:
        r = await get_interest_rate(client)
        q = await get_yield(client, symbol)
    except Exception as exc:
        logger.warning("rate/yield fetch failed for %s (%s); using 0.0", symbol, exc)
        r, q = 0.0, 0.0

    fallback_greeks = None
    fallback_sym = _FALLBACK_SYMBOLS.get(symbol.upper())
    if fallback_sym:
        try:
            fb_raw = await fetch_option_chain(
                client, fallback_sym, strike_count=_STRIKE_COUNT, include_quotes=True,
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
        except Exception as exc:
            logger.warning("fallback greeks fetch failed for %s via %s: %s",
                           symbol, fallback_sym, exc)

    data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
    if not data or spot <= 0:
        logger.warning("no option data for %s (spot=%s)", symbol, spot)
        return None

    analytics = compute_analytics(data, spot, r=r, q=q)
    return {"analytics": analytics, "spot": spot}


async def _run_once(*, dry_run: bool, outside_rth: bool) -> int:
    tickers = _load_tickers()
    if not tickers:
        logger.warning("No tickers in %s — nothing to poll", TICKER_HISTORY_FILE)
        return 1

    if not outside_rth and not within_rth():
        logger.info("Outside US RTH; skipping. Use --outside-rth to force.")
        return 0

    if not (config.TELEGRAM_ENABLED and config.BOT_TOKEN and config.CHAT_ID):
        if not dry_run:
            logger.warning("Telegram disabled or unconfigured; --dry-run implied.")
            dry_run = True

    logger.info("Polling %d ticker(s): %s", len(tickers), ", ".join(tickers))
    try:
        client = create_client()
    except Exception as exc:
        logger.error("Failed to create Schwab client: %s", exc)
        return 1

    state = _load_state()
    new_state: dict[str, dict[str, Any]] = dict(state)

    try:
        for sym in tickers:
            result = await _compute_for_symbol(client, sym)
            if result is None:
                continue
            analytics, spot = result["analytics"], result["spot"]
            prev = state.get(sym)
            new_alerts, next_sym_state = diff_alerts(prev, analytics, spot)
            new_state[sym] = next_sym_state

            if new_alerts:
                logger.info("[%s] %d alert(s): %s", sym, len(new_alerts), new_alerts)
                if not dry_run:
                    notify_alerts(new_alerts, symbol=sym, spot=spot)
            else:
                logger.debug("[%s] no change", sym)
    finally:
        # Persist state regardless of send success so a transient Telegram
        # outage doesn't replay the same alerts forever.
        _save_state(new_state)
        try:
            await client.close()
        except Exception:
            pass

    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--loop", action="store_true",
                   help="Run forever, sleeping --interval seconds between polls")
    p.add_argument("--interval", type=int, default=300,
                   help="Seconds between polls when --loop (default 300)")
    p.add_argument("--outside-rth", action="store_true",
                   help="Run even outside US regular trading hours")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute and log alerts but do not send Telegram messages")
    p.add_argument("--once", action="store_true",
                   help="Run a single poll then exit (default behavior)")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.loop:
        logger.info("Loop mode: interval=%ds outside_rth=%s dry_run=%s",
                    args.interval, args.outside_rth, args.dry_run)
        while True:
            try:
                rc = asyncio.run(_run_once(
                    dry_run=args.dry_run, outside_rth=args.outside_rth,
                ))
            except KeyboardInterrupt:
                return 0
            except Exception as exc:  # never let the loop die
                logger.exception("poll failed: %s", exc)
                rc = 1
            if rc != 0:
                logger.warning("poll returned rc=%d; sleeping", rc)
            time.sleep(max(args.interval, 30))
    else:
        rc = asyncio.run(_run_once(
            dry_run=args.dry_run, outside_rth=args.outside_rth,
        ))
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
