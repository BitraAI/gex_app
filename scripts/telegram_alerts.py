"""Telegram alerts for GEX Wall-based BUY signals.

Generates alerts ONLY for two specific BUY conditions:

1. BUY CALL: Spot price is inside the stable GEX Put Wall range.
   Condition: Put_Wall < Spot_Price < Put_Wall + (Strike_Spacing / 4)
   - Put Wall must be confirmed STABLE based on GEX wall stability metrics.

2. BUY PUT: Spot price is inside the stable GEX Call Wall range.
   Condition: Call_Wall > Spot_Price > Call_Wall - (Strike_Spacing / 4)
   - Call Wall must be confirmed STABLE based on GEX wall stability metrics.

 STRICT RULES:
 - Alert ONLY when the respective wall is STABLE and the exact price condition is satisfied.
 - Ignore unstable walls, price outside the specified ranges, and incomplete data.
 - Do NOT generate SELL, HOLD, WAIT, neutral, or speculative alerts.
 - Avoid duplicate alerts for the same stock and signal while the condition remains active.
 - Re-alert only after the condition becomes inactive and triggers again.
 - Monitor all symbols independently.
 - Use real-time spot prices and the latest available GEX data.
 - Do not assume a wall is stable without sufficient confirmation.

OUTPUT FORMAT:
Only output qualifying alerts, with a maximum of 5 lines per update.

Example:
AAPL | Spot: 250.25 | BUY CALL @ 45.25 | Put Wall: 250.00 | Exp: 2024-12-20
TSLA | Spot: 345.50 | BUY PUT @ 345.50 | Call Wall: 346.00 | Exp: 2024-12-20

If no qualifying signals exist, output NOTHING. Do not provide explanations,
summaries, market commentary, or additional text.
"""

import logging
import time

import streamlit as st

from scripts import config
from scripts.option_streaming_service import _normalize_display_symbol
from scripts.calculations import get_strike_spacing

logger = logging.getLogger("gex.telegram_alerts")

# Telegram configuration check
TELEGRAM_CONFIGURED = bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)

def _wall_is_stable(display_key: str, side: str) -> bool:
    """Check if a GEX wall is confirmed STABLE.

    Delegates to the single source of truth in flow.py, which tracks
    stability per ticker in its module-level _wall_stability dict
    (an unchanged wall surviving _WALL_STABLE_REFRESHES refreshes).
    """
    from scripts import flow

    return flow._wall_is_stable(display_key, side)

# Per-ticker alert state tracking - use session state to persist
# Format: {symbol: {"call": last_alert_ts, "put": last_alert_ts}}


def _get_alert_state() -> dict:
    """Get or create the alert state from session state."""
    s = st.session_state
    if "_alert_state" not in s:
        s["_alert_state"] = {}
    return s["_alert_state"]


def _is_alert_needed(symbol: str, signal_type: str) -> bool:
    """True when this ticker+signal has no live alert yet.

    Dedup is per (ticker, signal type).  The caller clears the timestamp
    whenever the full condition goes inactive, so once the condition
    re-triggers the signal alerts again.

    Signal types: "call" (BUY CALL), "put" (BUY PUT)
    """
    state = _get_alert_state()
    state_symbol = state.setdefault(symbol, {"call": None, "put": None})
    needed = state_symbol[signal_type] is None
    logger.debug(f"[{symbol}] {signal_type.upper()}: alert needed = {needed}")
    return needed


def _update_alert_timestamp(symbol: str, signal_type: str) -> None:
    """Update the last alert timestamp for a signal."""
    state = _get_alert_state()
    state_symbol = state.setdefault(symbol, {"call": None, "put": None})
    state_symbol[signal_type] = time.time()


def _clear_alert_timestamp(symbol: str, signal_type: str) -> None:
    """Clear the dedup timestamp so the signal can alert again after the
    condition goes inactive (re-alert on reactivation)."""
    state = _get_alert_state()
    state_symbol = state.setdefault(symbol, {"call": None, "put": None})
    state_symbol[signal_type] = None


# --- 1-minute VWAP gate ----------------------------------------------------
# BUY CALL requires spot > VWAP; BUY PUT requires spot < VWAP.
# Index tickers ($SPX, $RUT, $NDX) have zero volume → fall back to their
# proxy ETF (SPY, IWM, QQQ) VWAP instead of using a uniform-price average.
_VWAP_CACHE_TTL = 60.0                       # seconds between VWAP recomputes
_vwap_cache: dict[str, tuple[float, float | None]] = {}
_INDEX_CANDLE_SYMBOLS = {"SPX", "SPXW", "RUT", "RUTW", "NDX", "NDXP"}

# Mapping from index to its proxy ETF for VWAP fallback.
_INDEX_VWAP_PROXY = {
    "SPX": "SPY",
    "SPXW": "SPY",
    "RUT": "IWM",
    "RUTW": "IWM",
    "NDX": "QQQ",
    "NDXP": "QQQ",
}


def _candle_lookup_symbol(ticker: str) -> str:
    """Candle cache/API symbol: index tickers keep the leading '$'."""
    raw = (ticker or "").strip().upper()
    if raw and not raw.startswith("$") and raw in _INDEX_CANDLE_SYMBOLS:
        return "$" + raw
    return raw


def _vwap_1m(ticker: str) -> float | None:
    """Session VWAP from the 1-min Parquet cache.

    Cumulative typical-price * volume / cumulative volume within the current
    RTH session.  Memoized for _VWAP_CACHE_TTL seconds per ticker.
    """
    key = _normalize_display_symbol(ticker) or ticker
    now = time.monotonic()
    cached = _vwap_cache.get(key)
    if cached is not None and (now - cached[0]) < _VWAP_CACHE_TTL:
        return cached[1]

    sym = _candle_lookup_symbol(ticker)
    try:
        from scripts.client import load_candle_cache, fetch_candles_smart
    except Exception as exc:  # pragma: no cover - import guard
        logger.warning(f"VWAP unavailable (import failed): {exc}")
        return None

    df = load_candle_cache(sym, "1m")
    need_refresh = df is None or df.empty or len(df) < 2
    if not need_refresh and "datetime" in df.columns:
        try:
            last_ms = int(df["datetime"].iloc[-1])
            if (time.time() * 1000 - last_ms) > 5 * 60 * 1000:
                need_refresh = True
        except Exception:
            pass

    if need_refresh:
        client = st.session_state.get("client")
        if client is not None:
            try:
                from scripts.flow import run_async
                df = run_async(fetch_candles_smart(client, sym, "1m"))
            except Exception as exc:
                logger.warning(f"VWAP refresh failed for {sym}: {exc}")

    if df is None or df.empty:
        # No data loaded (missing parquet / refresh failed). For index
        # tickers without a parquet file, fall back to the proxy ETF VWAP.
        proxy = _INDEX_VWAP_PROXY.get(key)
        if proxy:
            logger.debug(f"[{key}] VWAP: no parquet, falling back to {proxy}")
            proxy_vwap = _vwap_1m(proxy)
            _vwap_cache[key] = (now, proxy_vwap)
            return proxy_vwap
        _vwap_cache[key] = (now, None)
        return None

    try:
        if "datetime" in df.columns:
            df = df.sort_values("datetime")
        closes = df["close"].astype(float)
        highs = df["high"].astype(float)
        lows = df["low"].astype(float)
        volumes = df["volume"].astype(float)
    except Exception:
        _vwap_cache[key] = (now, None)
        return None

    # Compute session-anchored VWAP (same RTH logic as charts.py).
    if "datetime" in df.columns:
        try:
            # Column is in ms; convert to unix seconds and adjust to ET.
            from datetime import timezone
            import pytz
            et = pytz.timezone("America/New_York")
            unix_secs = (df["datetime"] / 1000).astype(int)
            et_offset = et.utcoffset(et.localize(datetime.now())).total_seconds()
            et_day = (unix_secs + int(et_offset)) // 86400
            et_sod = ((unix_secs + int(et_offset)) % 86400).astype(int)
        except Exception:
            et_day = None
            et_sod = None
    else:
        et_day = None
        et_sod = None

    rth_open_sod = 9 * 3600 + 30 * 60  # 09:30 ET = 34200s
    cum_pv = 0.0
    cum_v = 0.0
    cur_day: int | None = None
    have_session = False

    for i in range(len(df)):
        if et_day is not None:
            d = int(et_day.iloc[i])
            s = int(et_sod.iloc[i])
            new_session = False
            if not have_session:
                new_session = True
            elif s >= rth_open_sod and d != cur_day:
                new_session = True
            if new_session:
                cur_day = d
                have_session = True
                cum_pv = 0.0
                cum_v = 0.0
        else:
            if i == 0:
                have_session = True
            elif i > 0 and cum_v == 0:
                have_session = True

        v = float(volumes.iloc[i])
        if v > 0:
            typical = (float(highs.iloc[i]) + float(lows.iloc[i]) + float(closes.iloc[i])) / 3.0
            cum_pv += typical * v
            cum_v += v

    if cum_v <= 0:
        # Index ticker with zero volume — fall back to proxy ETF VWAP.
        # E.g. $SPX → SPY, $RUT → IWM, $NDX → QQQ.
        proxy = _INDEX_VWAP_PROXY.get(key)
        if proxy:
            logger.debug(f"[{key}] VWAP: zero volume, falling back to {proxy}")
            proxy_vwap = _vwap_1m(proxy)
            _vwap_cache[key] = (now, proxy_vwap)
            return proxy_vwap
        _vwap_cache[key] = (now, None)
        return None

    vwap = cum_pv / cum_v
    logger.debug(f"[{key}] VWAP 1m: {vwap:.4f}")
    _vwap_cache[key] = (now, vwap)
    return vwap


def generate_telegram_alerts() -> list[str]:
    """Generate Telegram alerts for qualifying BUY signals.
    
    Returns a list of alert strings (max 5) for symbols that meet the criteria.
    """
    alerts: list[str] = []
    s = st.session_state
    
    # Get the current symbol and all tracked tickers
    current_sym = _normalize_display_symbol(s.get("symbol", ""))
    tickers = list(s.get("ticker_history", []))
    
    # If current symbol is not in ticker history, add it
    if current_sym and current_sym not in tickers:
        tickers = [current_sym] + tickers
    
    for ticker in tickers:
        if len(alerts) >= 5:
            break
            
        t_upper = _normalize_display_symbol(ticker)
        
        # Get current data
        atm_svc = s.get("atm_option_service")
        if not atm_svc:
            logger.debug(f"[{t_upper}] no atm_option_service -> skip")
            continue
            
        snap = atm_svc.get_ticker_snapshot(t_upper)
        if not snap:
            logger.debug(f"[{t_upper}] no snapshot -> skip")
            continue
            
        spot = snap.get("spot", 0.0)
        put_wall = snap.get("put_wall")
        call_wall = snap.get("call_wall")
        opt_prices = snap.get("opt_prices", {})
        wall_prices = snap.get("wall_prices", {})
        net_gex = snap.get("net_gex")
        # The snapshot has no expiration field; ask the service directly.
        expiration = atm_svc.get_ticker_expiration(t_upper)
        
        # Skip if missing critical data
        if spot <= 0:
            logger.debug(f"[{t_upper}] spot <= 0 ({spot}) -> skip")
            continue
        
        logger.debug(
            f"[{t_upper}] spot={spot:.2f} put_wall={put_wall} call_wall={call_wall} "
            f"stable_put={_wall_is_stable(t_upper, 'put')} stable_call={_wall_is_stable(t_upper, 'call')}"
        )
        
        # Format expiration date for display
        exp_date = ""
        if expiration:
            # expiration is typically in format "YYYY-MM-DD" or similar
            exp_date = expiration
            
        spacing = get_strike_spacing(spot) if spot > 0 else 1.0
        zone = spacing * 0.25
        
        # Format NET GEX as plain text. Telegram's HTML parse_mode does NOT
        # support <span> or inline color styles — sending them makes the API
        # reject the whole message with HTTP 400 ("can't parse entities: Tag
        # span ..."). Use a colored emoji + explicit sign to convey direction.
        if net_gex is not None:
            if net_gex > 0:
                _gex_emoji = "🟢"
            elif net_gex < 0:
                _gex_emoji = "🔴"
            else:
                _gex_emoji = "⚪"
            gex_str = f"{_gex_emoji} GEX: {net_gex:+,.0f}"
        else:
            gex_str = "GEX: N/A"
        
        # BUY CALL requires ALL of:
        #   - Put_Wall < Spot < Put_Wall + (Strike_Spacing / 4)
        #   - Put Wall STABLE
        #   - net GEX > 0
        #   - Spot > VWAP
        _vwap = _vwap_1m(ticker)
        _call_ok = (
            put_wall is not None
            and put_wall < spot < put_wall + zone
            and _wall_is_stable(t_upper, "put")
            and net_gex is not None and net_gex > 0
            and _vwap is not None and spot > _vwap
        )
        if _call_ok:
            if _is_alert_needed(t_upper, "call"):
                # CALL mark at the put-wall (support) strike
                call_price = wall_prices.get("put_wall_call_price") or opt_prices.get("call")
                call_str = f"{float(call_price):.2f}" if call_price is not None else "N/A"

                alert = f"{gex_str} | {t_upper} | {spot:.2f} | BUY CALL {put_wall:.2f} @ {call_str} | Exp: {exp_date}"
                alerts.append(alert)
                _update_alert_timestamp(t_upper, "call")
                logger.info(f"TELEGRAM ALERT generated: {alert}")
                if len(alerts) >= 5:
                    break
        else:
            # Condition inactive -> clear dedup so a later re-trigger re-alerts.
            _clear_alert_timestamp(t_upper, "call")

        # BUY PUT requires ALL of:
        #   - Call_Wall > Spot > Call_Wall - (Strike_Spacing / 4)
        #   - Call Wall STABLE
        #   - net GEX < 0
        #   - Spot < VWAP
        _put_ok = (
            call_wall is not None
            and call_wall > spot > call_wall - zone
            and _wall_is_stable(t_upper, "call")
            and net_gex is not None and net_gex < 0
            and _vwap is not None and spot < _vwap
        )
        if _put_ok:
            if _is_alert_needed(t_upper, "put"):
                # PUT mark at the call-wall (resistance) strike
                put_price = wall_prices.get("call_wall_put_price") or opt_prices.get("put")
                put_str = f"{float(put_price):.2f}" if put_price is not None else "N/A"

                alert = f"{gex_str} | {t_upper} | {spot:.2f} | BUY PUT {call_wall:.2f} @ {put_str} | Exp: {exp_date}"
                alerts.append(alert)
                _update_alert_timestamp(t_upper, "put")
                logger.info(f"TELEGRAM ALERT generated: {alert}")
                if len(alerts) >= 5:
                    break
        else:
            # Condition inactive -> clear dedup so a later re-trigger re-alerts.
            _clear_alert_timestamp(t_upper, "put")
    
    return alerts


def send_telegram_alerts(alerts: list[str]) -> bool:
    """Send alerts to Telegram if configured.
    
    Returns True if alerts were sent successfully, False otherwise.
    If Telegram is not configured, returns False without sending.
    """
    if not TELEGRAM_CONFIGURED:
        logger.debug("Telegram not configured - alerts not sent")
        return False
    
    if not alerts:
        logger.debug("No alerts to send")
        return False
    
    import urllib.request
    import urllib.error
    import json
    
    text = "\n".join(alerts[:5])
    message = f"<b>GEX Alerts</b>\n\n{text}"
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info(f"Telegram alerts sent: {len(alerts)} alert(s)")
                return True
            else:
                logger.error(f"Telegram API returned status {response.status}")
                return False
    except urllib.error.HTTPError as e:
        # HTTPError is a URLError subclass; read the response body so the
        # Telegram description (e.g. bad markup) is visible in the log.
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        logger.error(f"Failed to send Telegram alert: {e} {body}".strip())
        return False
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
