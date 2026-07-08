import logging
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from schwab import auth
from schwab.client import AsyncClient

from config import (
    APP_NAME,
    BASE_URL,
    CALLBACK_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    MAX_TOKEN_AGE,
    TOKEN_PATH,
)

CANDLE_CACHE_DIR = Path.home() / ".local" / "share" / "gex_app" / "candles"

logger = logging.getLogger(__name__)


def _token_loader() -> dict[str, Any]:
    import json
    with open(TOKEN_PATH) as f:
        return json.load(f)


def _token_writer(token: dict[str, Any], *args: Any, **kwargs: Any) -> None:
    import json
    import os
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    fd = os.open(TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        json.dump(token, f)


def create_client() -> AsyncClient:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    client: AsyncClient = auth.client_from_access_functions(
        client_id,
        client_secret,
        _token_loader,
        _token_writer,
        asyncio=True,
        enforce_enums=False,
        base_url=BASE_URL,
    )
    return client


async def fetch_option_chain(
    client: AsyncClient,
    symbol: str,
    strike_count: int = 50,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    contract_type: Optional[str] = None,
    include_quotes: bool = True,
) -> dict[str, Any]:
    from datetime import date, timedelta
    today = date.today()
    if from_date is None:
        from_date = today.isoformat()
    if to_date is None:
        to_date = (today + timedelta(days=90)).isoformat()

    try:
        ct = None
        if contract_type:
            ct = client.Options.ContractType[contract_type.upper()]

        resp = await client.get_option_chain(
            symbol,
            contract_type=ct,
            strike_count=strike_count,
            include_underlying_quote=include_quotes,
            from_date=date.fromisoformat(from_date),
            to_date=date.fromisoformat(to_date),
        )
        if hasattr(resp, "json"):
            return resp.json()
        return resp
    except Exception as e:
        logger.exception(f"Failed to fetch option chain for {symbol}")
        raise


async def fetch_quotes(
    client: AsyncClient, symbols: list[str]
) -> dict[str, Any]:
    try:
        result = await client.get_quotes(symbols)
        return result
    except Exception as e:
        logger.exception(f"Failed to fetch quotes for {symbols}")
        raise


async def _extract_from_quote(
    client: AsyncClient, symbol: str, field: str
) -> float:
    try:
        resp = await client.get_quotes([symbol])
        if hasattr(resp, "json"):
            resp = resp.json()
        if not isinstance(resp, dict):
            return 0.0
        qd = resp.get(symbol, {}) or {}
        fund = qd.get("fundamental", {}) or {}
        val = fund.get(field, 0)
        if val is None:
            return 0.0
        return float(val)
    except Exception:
        return 0.0


async def get_yield(client: AsyncClient, symbol: str) -> float:
    """Get dividend yield for a symbol from Schwab API."""
    return await _extract_from_quote(client, symbol, "dividendYield")


async def get_interest_rate(client: AsyncClient) -> float:
    """Get risk-free interest rate proxy from Schwab."""
    for sym in ("SGOV", "BIL", "SHV"):
        try:
            resp = await client.get_quotes([sym])
            if hasattr(resp, "json"):
                resp = resp.json()
            if not isinstance(resp, dict):
                continue
            qd = resp.get(sym, {}) or {}
            fund = qd.get("fundamental", {}) or {}
            y = fund.get("yield") or fund.get("netYield") or fund.get("dividendYield") or 0
            if y:
                return float(y)
        except Exception:
            continue
    return 0.05


async def get_next_earnings_date(client: AsyncClient, symbol: str) -> Optional[str]:
    from datetime import datetime, timezone
    try:
        resp = await client.get_quotes([symbol])
        if hasattr(resp, "json"):
            resp = resp.json()
        if not isinstance(resp, dict):
            return None
        qd = resp.get(symbol, {}) or {}
        fund = qd.get("fundamental", {}) or {}
        ts = fund.get("nextEarningsDate")
        if ts and int(ts) > 0:
            return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        return None
    except Exception:
        return None


def historical_volatility(prices: list[float], length: int = 20) -> float:
    """Compute annualized historical volatility from a list of close prices.
       HV = stdev(log(close_i / close_{i-1}), length) * sqrt(252)
       using rolling sample standard deviation (ddof=1).
    """
    import math, statistics
    if len(prices) < length + 1:
        return 0.0
    log_returns = [
        math.log(prices[i] / prices[i - 1])
        for i in range(1, len(prices))
    ]
    rolling_stdevs = [
        statistics.pstdev(log_returns[i - length:i])
        for i in range(length, len(log_returns) + 1)
    ]
    return rolling_stdevs[-1] * math.sqrt(252 * length / (length - 1))


TIMEFRAMES = {
    "1m":  {"label": "1m",  "minutes": 1,    "freq": "EVERY_MINUTE",       "ftype": "MINUTE", "ptype": "DAY",  "period": 3},
    "2m":  {"label": "2m",  "minutes": 2,    "freq": "EVERY_MINUTE",       "ftype": "MINUTE", "ptype": "DAY",  "period": 3},
    "5m":  {"label": "5m",  "minutes": 5,    "freq": "EVERY_FIVE_MINUTES",  "ftype": "MINUTE", "ptype": "DAY",  "period": 10},
    "15m": {"label": "15m", "minutes": 15,   "freq": "EVERY_FIFTEEN_MINUTES","ftype": "MINUTE", "ptype": "DAY",  "period": 10},
    "30m": {"label": "30m", "minutes": 30,   "freq": "EVERY_THIRTY_MINUTES","ftype": "MINUTE", "ptype": "DAY",  "period": 10},
    "1h":  {"label": "1h",  "minutes": 60,   "freq": "EVERY_FIFTEEN_MINUTES","ftype": "MINUTE", "ptype": "DAY",  "period": 10},
    "4h":  {"label": "4h",  "minutes": 240,  "freq": "EVERY_THIRTY_MINUTES","ftype": "MINUTE", "ptype": "DAY",  "period": 10},
    "1d":  {"label": "1d",  "minutes": None, "freq": None,                  "ftype": "DAILY",  "ptype": "YEAR", "period": 1},
    "1w":  {"label": "1w",  "minutes": None, "freq": None,                  "ftype": "WEEKLY", "ptype": "YEAR", "period": 5},
    "1month": {"label": "1M", "minutes": None, "freq": None,                "ftype": "MONTHLY","ptype": "YEAR", "period": 10},
}


def _api_freq(client: AsyncClient, tf: str):
    """Return (period_type, period, frequency_type, frequency) for a given timeframe key."""
    cfg = TIMEFRAMES[tf]
    pt_map = {"DAY": client.PriceHistory.PeriodType.DAY,
              "YEAR": client.PriceHistory.PeriodType.YEAR,
              "MONTH": client.PriceHistory.PeriodType.MONTH}
    per_map_day = {1: client.PriceHistory.Period.ONE_DAY,
                   2: client.PriceHistory.Period.TWO_DAYS,
                   3: client.PriceHistory.Period.THREE_DAYS,
                   4: client.PriceHistory.Period.FOUR_DAYS,
                   5: client.PriceHistory.Period.FIVE_DAYS,
                   10: client.PriceHistory.Period.TEN_DAYS}
    per_map_year = {1: client.PriceHistory.Period.ONE_YEAR,
                    5: client.PriceHistory.Period.FIVE_YEARS,
                    10: client.PriceHistory.Period.TEN_YEARS,
                    15: client.PriceHistory.Period.FIFTEEN_YEARS,
                    20: client.PriceHistory.Period.TWENTY_YEARS}
    ft_map = {"MINUTE": client.PriceHistory.FrequencyType.MINUTE,
              "DAILY": client.PriceHistory.FrequencyType.DAILY,
              "WEEKLY": client.PriceHistory.FrequencyType.WEEKLY,
              "MONTHLY": client.PriceHistory.FrequencyType.MONTHLY}
    f_map = {"EVERY_MINUTE": client.PriceHistory.Frequency.EVERY_MINUTE,
             "EVERY_FIVE_MINUTES": client.PriceHistory.Frequency.EVERY_FIVE_MINUTES,
             "EVERY_TEN_MINUTES": client.PriceHistory.Frequency.EVERY_TEN_MINUTES,
             "EVERY_FIFTEEN_MINUTES": client.PriceHistory.Frequency.EVERY_FIFTEEN_MINUTES,
             "EVERY_THIRTY_MINUTES": client.PriceHistory.Frequency.EVERY_THIRTY_MINUTES,
             None: None}
    pt = pt_map.get(cfg["ptype"])
    per = (per_map_day if cfg["ptype"] == "DAY" else per_map_year).get(cfg["period"])
    return pt, per, ft_map.get(cfg["ftype"]), f_map.get(cfg["freq"])


def aggregate_candles(candles: list[dict], target_minutes: int) -> list[dict]:
    """Aggregate 1-min candles into target_minutes bars."""
    if not candles or target_minutes <= 1:
        return list(candles)
    sorted_c = sorted(candles, key=lambda c: c["datetime"])
    result: list[dict] = []
    period_start: int | None = None
    agg: dict | None = None
    for c in sorted_c:
        t = c["datetime"]
        period = (t // (target_minutes * 60_000)) * (target_minutes * 60_000)
        if period != period_start:
            if agg is not None:
                result.append(agg)
            period_start = period
            agg = {
                "open": c["open"],
                "high": c["high"],
                "low": c["low"],
                "close": c["close"],
                "volume": c.get("volume", 0),
                "datetime": period,
                "symbol": c.get("symbol", ""),
            }
        else:
            agg["high"] = max(agg["high"], c["high"])
            agg["low"] = min(agg["low"], c["low"])
            agg["close"] = c["close"]
            agg["volume"] = (agg.get("volume", 0) or 0) + (c.get("volume", 0) or 0)
    if agg is not None:
        result.append(agg)
    return result


async def fetch_price_history_intraday(
    client: AsyncClient, symbol: str, timeframe: str = "1m",
) -> list[dict]:
    """Fetch OHLCV candles via REST API for the given timeframe.
    For intraday (MINUTE) frequencies uses explicit datetimes so that
    today's partial trading day is always included."""
    from datetime import datetime, timedelta, timezone
    try:
        pt, per, ft, f = _api_freq(client, timeframe)
        now = datetime.now(timezone.utc)

        if ft == client.PriceHistory.FrequencyType.MINUTE:
            days_back = (TIMEFRAMES.get(timeframe) or {}).get("period", 3)
            resp = await client.get_price_history(
                symbol,
                frequency_type=ft,
                frequency=f,
                start_datetime=now - timedelta(days=days_back),
                end_datetime=now,
                need_extended_hours_data=False,
            )
        else:
            resp = await client.get_price_history(
                symbol,
                period_type=pt, period=per,
                frequency_type=ft, frequency=f,
                need_extended_hours_data=False,
            )

        if hasattr(resp, "json"):
            resp = resp.json()
        candles = resp.get("candles", []) if isinstance(resp, dict) else []
        result = []
        for c in candles:
            result.append({
                "open": float(c.get("open", 0)),
                "high": float(c.get("high", 0)),
                "low": float(c.get("low", 0)),
                "close": float(c.get("close", 0)),
                "volume": int(c.get("volume", 0)),
                "datetime": int(c.get("datetime", 0)),
                "symbol": symbol,
            })
        return result
    except Exception:
        return []


def _cache_path(symbol: str, timeframe: str) -> Path:
    return CANDLE_CACHE_DIR / f"{symbol.upper()}_{timeframe}.parquet"


def load_candle_cache(symbol: str, timeframe: str) -> pd.DataFrame:
    """Load cached candles from Parquet, return empty DataFrame if missing."""
    p = _cache_path(symbol, timeframe)
    if p.exists():
        try:
            return pd.read_parquet(p)
        except Exception:
            pass
    return pd.DataFrame()


def save_candle_cache(df: pd.DataFrame, symbol: str, timeframe: str):
    """Save candles DataFrame to Parquet (append merge on datetime)."""
    CANDLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(symbol, timeframe)
    existing = load_candle_cache(symbol, timeframe)
    if not existing.empty:
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["datetime"], keep="last")
        df = df.sort_values("datetime").reset_index(drop=True)
    df.to_parquet(p, index=False)


async def fetch_price_history_daily(
    client: AsyncClient, symbol: str, years: int = 1,
) -> list[dict]:
    """Fetch daily OHLCV candles via REST API.

    TDA's daily frequency API only returns BARS THAT HAVE CLOSED — during a
    live trading session, today's daily bar is NOT yet in the response (the
    API returns bars through the previous day's close). To make today's
    partial session visible on the daily chart, this function also pulls
    today's intraday 1-minute bars and aggregates them into a synthetic
    "today" daily bar (open=first 1m open, high=max high, low=min low,
    close=last 1m close, volume=sum), then merges it into the daily series
    so the chart's rightmost bar reflects current session data.
    """
    try:
        pt_map = {
            1: client.PriceHistory.Period.ONE_YEAR,
            5: client.PriceHistory.Period.FIVE_YEARS,
            10: client.PriceHistory.Period.TEN_YEARS,
            15: client.PriceHistory.Period.FIFTEEN_YEARS,
            20: client.PriceHistory.Period.TWENTY_YEARS,
        }
        period = pt_map.get(years, client.PriceHistory.Period.ONE_YEAR)
        resp = await client.get_price_history(
            symbol,
            period_type=client.PriceHistory.PeriodType.YEAR,
            period=period,
            frequency_type=client.PriceHistory.FrequencyType.DAILY,
            frequency=1,
            need_extended_hours_data=False,
        )
        if hasattr(resp, "json"):
            resp = resp.json()
        candles = resp.get("candles", []) if isinstance(resp, dict) else []
        result = []
        for c in candles:
            result.append({
                "open": float(c.get("open", 0)),
                "high": float(c.get("high", 0)),
                "low": float(c.get("low", 0)),
                "close": float(c.get("close", 0)),
                "volume": int(c.get("volume", 0)),
                "datetime": int(c.get("datetime", 0)),
                "symbol": symbol,
            })

        # Synthesize today's daily bar from intraday 1-minute data so the
        # chart's daily timeframe shows the current in-progress session
        # rather than stopping at yesterday's closed bar. The 1m API uses
        # `start_datetime=now - N days` so it inherently includes today.
        try:
            intraday = await fetch_price_history_intraday(client, symbol, "1m")
            if intraday:
                from datetime import datetime, timezone
                from zoneinfo import ZoneInfo
                _ny = ZoneInfo("America/New_York")
                today_ny = datetime.now(_ny).date()
                # Filter 1m bars to today's NY-local date so we don't pull in
                # any bars from yesterday after-hours that crossed midnight UTC.
                todays_1m = []
                for bar in intraday:
                    bdt = datetime.fromtimestamp(bar["datetime"] / 1000, tz=timezone.utc).astimezone(_ny)
                    if bdt.date() == today_ny:
                        todays_1m.append(bar)
                if todays_1m:
                    # Aggregate 1m bars → daily bar anchored at NY midnight (UTC ms).
                    day_open = todays_1m[0]["open"]
                    day_high = max(b["high"] for b in todays_1m)
                    day_low = min(b["low"] for b in todays_1m)
                    day_close = todays_1m[-1]["close"]
                    day_volume = sum(int(b.get("volume", 0) or 0) for b in todays_1m)
                    # NY midnight as UTC ms — matches the convention the daily
                    # API uses for storing daily bars (midnight US/Eastern).
                    from datetime import datetime as _dt
                    ny_now = _dt.now(tz=_ny)
                    ny_midnight = ny_now.replace(hour=0, minute=0, second=0, microsecond=0)
                    day_bucket_ms = int(ny_midnight.astimezone(timezone.utc).timestamp() * 1000)
                    # Drop any existing API-result bar at the same timestamp
                    # (TDA shouldn't include today, but just in case) and add
                    # our synthesized partial-day bar.
                    result = [b for b in result if b["datetime"] != day_bucket_ms]
                    result.append({
                        "open": float(day_open),
                        "high": float(day_high),
                        "low": float(day_low),
                        "close": float(day_close),
                        "volume": int(day_volume),
                        "datetime": int(day_bucket_ms),
                        "symbol": symbol,
                    })
                    result.sort(key=lambda b: b["datetime"])
        except Exception:
            # Intraday enrichment is best-effort — if it fails we still
            # return the closed daily bars from the API above.
            pass

        return result
    except Exception:
        return []


def _is_intraday(timeframe: str) -> bool:
    """True if the timeframe key represents an intraday period (< 1 day)."""
    return (TIMEFRAMES.get(timeframe) or {}).get("minutes") is not None


async def fetch_candles_smart(
    client: AsyncClient, symbol: str, timeframe: str = "1m",
) -> pd.DataFrame:
    """Load from Parquet cache, fetch from API, merge, save back.
    Falls back to daily data when intraday API returns nothing."""
    cached = load_candle_cache(symbol, timeframe)
    raw = await fetch_price_history_intraday(client, symbol, timeframe)

    if raw:
        api_df = pd.DataFrame(raw)
        if not cached.empty:
            result = pd.concat([cached, api_df], ignore_index=True)
        else:
            result = api_df
        result = result.drop_duplicates(subset=["datetime"], keep="last")
        result = result.sort_values("datetime").reset_index(drop=True)
        save_candle_cache(result, symbol, timeframe)
        return result

    # API returned nothing for intraday timeframe — try daily fallback
    if _is_intraday(timeframe):
        logger.info("fetch_candles_smart: intraday API empty for %s %s, trying daily fallback", symbol, timeframe)
        daily_raw = await fetch_price_history_daily(client, symbol, years=1)
        if daily_raw:
            api_df = pd.DataFrame(daily_raw)
            if not cached.empty:
                result = pd.concat([cached, api_df], ignore_index=True)
            else:
                result = api_df
            result = result.drop_duplicates(subset=["datetime"], keep="last")
            result = result.sort_values("datetime").reset_index(drop=True)
            save_candle_cache(result, symbol, timeframe)
            logger.info("fetch_candles_smart: daily fallback returned %d candles for %s %s", len(result), symbol, timeframe)
            return result

    # Nothing worked — warn and return cache (stale or empty)
    logger.warning("fetch_candles_smart: API returned no data for %s %s, using cached", symbol, timeframe)
    return cached


async def get_20d_rv(client: AsyncClient, symbol: str, length: int = 20) -> float:
    """Realized volatility using historical_volatility on daily close prices."""
    try:
        resp = await client.get_price_history(
            symbol,
            period_type=client.PriceHistory.PeriodType.YEAR,
            period=client.PriceHistory.Period.ONE_YEAR,
            frequency_type=client.PriceHistory.FrequencyType.DAILY,
            frequency=client.PriceHistory.Frequency.DAILY,
            need_extended_hours_data=False,
        )
        if hasattr(resp, "json"):
            resp = resp.json()
        candles = resp.get("candles", []) if isinstance(resp, dict) else []
        if len(candles) < length + 1:
            return 0.0
        closes = [c["close"] for c in candles]
        return historical_volatility(closes, length)
    except Exception:
        return 0.0
