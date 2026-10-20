"""Shared utility functions deduplicated across the GEX app codebase."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

import pandas as pd


def to_json(resp: Any) -> Any:
    """Convert a Schwab response object to a dict if possible."""
    if hasattr(resp, "json"):
        return resp.json()
    return resp


def ensure_dir(path: str) -> None:
    """Ensure the parent directory of *path* exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_json(path: str, default: Any = None) -> Any:
    """Load JSON from *path*, returning *default* on error."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: str, data: Any, secure: bool = False) -> None:
    """Save *data* as JSON to *path*.  If *secure* is True, use 0o600 perms."""
    ensure_dir(path)
    if secure:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
    else:
        with open(path, "w") as f:
            json.dump(data, f)


def compute_strike_increment(options_data: list[dict]) -> float | None:
    """Compute the minimum strike spacing from a list of option dicts.

    Returns None if fewer than 2 unique strikes.
    """
    strikes = sorted(set(e["strike"] for e in options_data))
    if len(strikes) >= 2:
        return min(strikes[i + 1] - strikes[i] for i in range(len(strikes) - 1))
    return None


_NY_TZ = ZoneInfo("America/New_York")
_secs_since_930_cache: tuple[tuple[int, int], float] | None = None  # ((hh, mm), secs)


def secs_since_market_open() -> float:
    """Seconds elapsed since 09:30 ET today, clamped to the 09:30-16:00
    session (0..23400).  Cached per minute — recomputed for thousands of
    options per chain parse, and minute granularity is sufficient."""
    global _secs_since_930_cache
    now = datetime.now(_NY_TZ)
    key = (now.hour, now.minute)
    if _secs_since_930_cache is not None and _secs_since_930_cache[0] == key:
        return _secs_since_930_cache[1]
    secs = max(0, min(now.hour * 3600 + now.minute * 60 + now.second - 34200, 23400))
    _secs_since_930_cache = (key, secs)
    return secs


def is_otm_or_atm(e: dict, spot: float) -> bool:
    """True for OTM-or-ATM options relative to ``spot`` (shared moneyness filter)."""
    return (e["type"] == "CALL" and e["strike"] >= spot) or (e["type"] == "PUT" and e["strike"] <= spot)


def is_itm_or_atm(e: dict, spot: float) -> bool:
    """True for ITM-or-ATM options relative to ``spot`` (shared moneyness filter)."""
    return (e["type"] == "CALL" and e["strike"] <= spot) or (e["type"] == "PUT" and e["strike"] >= spot)


def flow_metrics(call_buy, call_sell, put_buy, put_sell) -> tuple[int, int, float | None]:
    """(net_flow, total_flow, flow_ratio) from the streamed per-side volumes.

    ``None`` inputs count as 0; ``flow_ratio`` is None when there is no flow
    at all yet (Telegram headers omit it, the Order Flow grid maps it to 0)."""
    cb = call_buy or 0
    cs = call_sell or 0
    pb = put_buy or 0
    ps = put_sell or 0
    total = cb + ps + pb + cs
    ratio = round((cb + ps) / total, 2) if total > 0 else None
    net = cb + ps - pb - cs
    return net, total, ratio


def format_expiration(exp: str | None) -> str:
    """Format expiration date into MM-DD (X days) for display.

    Returns empty string for None/invalid input.
    """
    if not exp:
        return ""
    try:
        exp_date = date.fromisoformat(exp)
        dte = (exp_date - date.today()).days
        mmdd = exp[5:10]  # "MM-DD"
        return f"{mmdd} ({dte}d)" if dte >= 0 else f"{mmdd} (0d)"
    except (ValueError, TypeError):
        return exp or ""


def floor_dataframe_timestamps(
    df: pd.DataFrame,
    col: str = "datetime",
    timeframe: str = "1d",
    tf_minutes: int | None = None,
) -> pd.DataFrame:
    """Floor a DataFrame's timestamp column to the chart's timeframe boundary.

    For daily/weekly/monthly (tf_minutes is None), uses US/Eastern day
    boundary so live bars align with TDA's daily cache (midnight ET).

    For intraday (tf_minutes is set), simply floors to the interval.
    """
    if tf_minutes is None:
        tf_ms = 24 * 60 * 60 * 1000
        try:
            ny_tz = ZoneInfo("America/New_York")
            tick_dt = pd.to_datetime(df[col], unit="ms", utc=True).dt.tz_convert(ny_tz)
            day_start_ny = tick_dt.dt.normalize()
            df[col] = day_start_ny.dt.tz_convert("UTC").astype("int64")
        except Exception:
            logger.debug("Timezone fallback for floor_dataframe_timestamps", exc_info=True)
            df[col] = (df[col] // tf_ms) * tf_ms
    else:
        tf_ms = tf_minutes * 60 * 1000
        df[col] = (df[col] // tf_ms) * tf_ms
    return df


def compute_current_bucket(timeframe: str, tf_minutes: int | None = None) -> int:
    """Compute the current timeframe-aligned bucket timestamp (ms UTC).

    For daily/weekly/monthly (tf_minutes is None), uses US/Eastern day
    boundary.  For intraday, floors to the nearest interval.
    """
    now_utc_ms = int(pd.Timestamp.now(tz="UTC").value // 1_000_000)
    if tf_minutes is None:
        try:
            ny_tz = ZoneInfo("America/New_York")
            return int(
                pd.Timestamp.now(tz=ny_tz)
                .normalize()
                .tz_convert("UTC")
                .value // 1_000_000
            )
        except Exception:
            logger.debug("Timezone fallback for compute_current_bucket", exc_info=True)
            tf_ms = 24 * 60 * 60 * 1000
            return (now_utc_ms // tf_ms) * tf_ms
    else:
        tf_ms = tf_minutes * 60 * 1000
        return (now_utc_ms // tf_ms) * tf_ms
