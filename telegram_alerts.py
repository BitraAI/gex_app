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
    get_20d_rv,
    get_interest_rate,
    get_yield,
)
from signals import generate_recommendations, score_options
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

def _tte_from_dtes(dtes: list[int]) -> float | None:
    valid = [d for d in dtes if d > 0]
    if not valid:
        return None
    now = datetime.now(_NY_TZ)
    secs_since_930 = now.hour * 3600 + now.minute * 60 + now.second - 34200
    secs_since_930 = max(0, min(secs_since_930, 23400))
    secs_left = 23400 - secs_since_930
    return (min(valid) + secs_left / 23400) / 365.0


def _filter_strikes_near_atm(data: list[dict], spot: float, n: int = 20) -> list[dict]:
    strikes = sorted(set(e["strike"] for e in data))
    atm = min(strikes, key=lambda k: abs(k - spot)) if strikes else 0
    ai = strikes.index(atm) if atm in strikes else 0
    kr = set(strikes[max(0, ai - n):ai + n + 1])
    return [e for e in data if e["strike"] in kr]


def _build_strategy_alerts(
    data: list[dict], analytics: dict, spot: float, rv: float,
) -> list[str]:
    alerts: list[str] = []

    aks = sorted(set(e["strike"] for e in data))
    atm_k = min(aks, key=lambda k: abs(k - spot)) if aks else spot
    sd = [e for e in data if e.get("open_interest", 0) > 0 and (e.get("mark", 0) or 0) > 0 and ((e["strike"] == atm_k) or (e["type"] == "CALL" and e["strike"] > spot) or (e["type"] == "PUT" and e["strike"] < spot))]

    sd2 = _filter_strikes_near_atm(sd, spot)

    ssvi_surf = analytics.get("ssvi_surface")
    dtes = [e.get("dte", 0) for e in _build_by_exp_all(data, spot)]
    ir_tte = _tte_from_dtes(dtes) if ssvi_surf else None

    buy_sd = [e for e in sd2 if 0.35 <= abs(e.get("delta", 0) or 0) <= 0.55]
    buy_sd = [e for e in buy_sd if (e.get("iv", 0) or 0) - rv < 0]
    buy_sd = [e for e in buy_sd if 20 <= (e.get("days_to_exp", 0) or 0) <= 45]
    if ssvi_surf and ir_tte:
        buy_sd = [e for e in buy_sd if (e.get("iv", 0) or 0) - ssvi_surf.iv(float(e["strike"]), float(ir_tte)) < 0]

    sell_sd = [e for e in sd2 if 0.10 <= abs(e.get("delta", 0) or 0) <= 0.20]
    sell_sd = [e for e in sell_sd if (e.get("iv", 0) or 0) - rv > 0.05]
    sell_sd = [e for e in sell_sd if 30 <= (e.get("days_to_exp", 0) or 0) <= 45]
    if ssvi_surf and ir_tte:
        sell_sd = [e for e in sell_sd if (e.get("iv", 0) or 0) - ssvi_surf.iv(float(e["strike"]), float(ir_tte)) > 0]

    if buy_sd:
        sc = score_options(buy_sd, spot, rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew"))
        buy_recs = [r for r in generate_recommendations(sc, spot, strategy="Long Calls", all_data=buy_sd, rv=rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew")) if "No strong" not in r]
        if buy_recs:
            alerts.append("Buy Premium:")
            for r in buy_recs[:3]:
                alerts.append(f"  • {r}")

    if sell_sd:
        sc = score_options(sell_sd, spot, rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew"))
        sell_recs = [r for r in generate_recommendations(sc, spot, strategy="Short Calls", all_data=sell_sd, rv=rv, call_wall=analytics.get("call_wall"), put_wall=analytics.get("put_wall"), iv_skew=analytics.get("iv_skew")) if "No strong" not in r]
        if sell_recs:
            alerts.append("Sell Premium:")
            for r in sell_recs[:3]:
                alerts.append(f"  • {r}")

    return alerts


def _build_by_exp_all(data: list[dict], spot: float = 0.0) -> list[dict]:
    from calculations import aggregate_by_expiration
    return aggregate_by_expiration(data, spot=spot)


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
    etf_analytics = None
    fallback_sym = _FALLBACK_SYMBOLS.get(symbol.upper().lstrip("$"))
    if fallback_sym:
        try:
            fb_raw = await fetch_option_chain(
                client, fallback_sym, strike_count=_STRIKE_COUNT, include_quotes=True,
            )
            fallback_greeks = build_greeks_lookup(fb_raw)
            etf_data, etf_spot = parse_option_chain(fb_raw, r=r, q=q)
            if etf_data and etf_spot > 0:
                etf_analytics = compute_analytics(etf_data, etf_spot, data_full=etf_data, r=r, q=q)
        except Exception as exc:
            logger.warning("fallback greeks fetch failed for %s via %s: %s",
                           symbol, fallback_sym, exc)

    data, spot = parse_option_chain(raw, r=r, q=q, fallback_greeks=fallback_greeks)
    if not data or spot <= 0:
        logger.warning("no option data for %s (spot=%s)", symbol, spot)
        return None

    analytics = compute_analytics(data, spot, r=r, q=q)

    if etf_analytics:
        if analytics.get("net_gex", 0) == 0:
            for key in ("net_gex", "total_call_gex", "total_put_gex",
                         "max_positive_gex", "max_negative_gex",
                         "max_positive_gex_strike", "max_negative_gex_strike",
                         "dealer_position"):
                if key in etf_analytics:
                    analytics[key] = etf_analytics[key]
        if analytics.get("ssvi_surface") is None and etf_analytics.get("ssvi_surface") is not None:
            analytics["ssvi_surface"] = etf_analytics["ssvi_surface"]
            analytics["ssvi_skew"] = etf_analytics["ssvi_skew"]
            if analytics.get("atm_iv") is None and etf_analytics.get("atm_iv") is not None:
                analytics["atm_iv"] = etf_analytics["atm_iv"]

    rv = 0.0
    try:
        rv = await get_20d_rv(client, symbol)
    except Exception as exc:
        logger.warning("failed to fetch 20d RV for %s: %s", symbol, exc)

    strat_alerts = _build_strategy_alerts(data, analytics, spot, rv)
    return {"analytics": analytics, "spot": spot, "strategy_alerts": strat_alerts}


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

            strat_alerts = result.get("strategy_alerts", [])
            new_alerts = [a for a in new_alerts if "Wall changed" not in a]
            all_alerts = new_alerts + strat_alerts

            if all_alerts:
                logger.info("[%s] %d alert(s): %s", sym, len(all_alerts), all_alerts)
                if not dry_run:
                    notify_alerts(all_alerts, symbol=sym, spot=spot)
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
