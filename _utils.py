"""Shared utility functions deduplicated across the GEX app codebase."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd


def to_json(resp: Any) -> Any:
    """Convert a Schwab response object to a dict if possible."""
    if hasattr(resp, "json"):
        return resp.json()
    return resp


def nested_get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts: nested_get(d, 'a', 'b', 'c', default=0)
    returns d['a']['b']['c'] or default if any key is missing."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default) or default
    return d


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


def floor_ts_to_tf(
    ts_ms: int, timeframe: str, tf_minutes: int | None = None
) -> int:
    """Floor a timestamp (ms since epoch, UTC) to a timeframe boundary.

    For intraday timeframes (*tf_minutes* is set), simply floors to the
    nearest *tf_minutes* interval.

    For daily/weekly/monthly (when *tf_minutes* is None), floors to the
    start of the US/Eastern trading day so it aligns with TDA's daily
    cache bars (which use midnight ET, not midnight UTC).
    """
    if tf_minutes is None:
        tf_ms = 24 * 60 * 60 * 1000
        try:
            ny_tz = ZoneInfo("America/New_York")
            now_ny = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("UTC")).astimezone(ny_tz)
            day_start_ny = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)
            return int(day_start_ny.astimezone(ZoneInfo("UTC")).timestamp() * 1000)
        except Exception:
            return (ts_ms // tf_ms) * tf_ms
    else:
        tf_ms = tf_minutes * 60 * 1000
        return (ts_ms // tf_ms) * tf_ms


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
            tf_ms = 24 * 60 * 60 * 1000
            return (now_utc_ms // tf_ms) * tf_ms
    else:
        tf_ms = tf_minutes * 60 * 1000
        return (now_utc_ms // tf_ms) * tf_ms


def extract_last_price(quote: dict) -> float | None:
    """Extract the best available price from a Schwab quote dict."""
    last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
    if last is not None:
        try:
            v = float(last)
            if v > 0:
                return v
        except (ValueError, TypeError):
            pass
    return None
