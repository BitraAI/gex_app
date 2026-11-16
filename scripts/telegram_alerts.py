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
from typing import Optional

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
    """Check if an alert should be sent for this signal.
    
    Returns True if:
    - Never alerted before for this signal type, OR
    - Alerted before but condition is no longer active (need reactivation)
    
    Signal types: "call" (BUY CALL), "put" (BUY PUT)
    """
    state = _get_alert_state()
    state_symbol = state.setdefault(symbol, {"call": None, "put": None})
    
    # If never alerted, we need to alert
    if state_symbol[signal_type] is None:
        return True
    
    # Check if condition is still active
    # For this, we need to check current state via session state
    s = st.session_state
    current_sym = _normalize_display_symbol(symbol)
    
    if current_sym in s.get("ticker_history", []):
        # Get current spot and walls from ATM service
        atm_svc = s.get("atm_option_service")
        if atm_svc:
            snap = atm_svc.get_ticker_snapshot(current_sym)
            if snap:
                spot = snap.get("spot", 0.0)
                put_wall = snap.get("put_wall")
                call_wall = snap.get("call_wall")
                
                if signal_type == "call" and put_wall is not None:
                    # Check if BUY CALL condition is still active
                    spacing = get_strike_spacing(spot) if spot > 0 else 1.0
                    zone = spacing * 0.25
                    if not (put_wall < spot < put_wall + zone and _wall_is_stable(current_sym, "put")):
                        # Condition is no longer active - allow re-alert
                        return True
                elif signal_type == "put" and call_wall is not None:
                    # Check if BUY PUT condition is still active
                    spacing = get_strike_spacing(spot) if spot > 0 else 1.0
                    zone = spacing * 0.25
                    if not (call_wall > spot > call_wall - zone and _wall_is_stable(current_sym, "call")):
                        # Condition is no longer active - allow re-alert
                        return True
    
    # Condition still active, don't re-alert
    return False


def _update_alert_timestamp(symbol: str, signal_type: str) -> None:
    """Update the last alert timestamp for a signal."""
    state = _get_alert_state()
    state_symbol = state.setdefault(symbol, {"call": None, "put": None})
    state_symbol[signal_type] = time.time()


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
            continue
            
        snap = atm_svc.get_ticker_snapshot(t_upper)
        if not snap:
            continue
            
        spot = snap.get("spot", 0.0)
        put_wall = snap.get("put_wall")
        call_wall = snap.get("call_wall")
        opt_prices = snap.get("opt_prices", {})
        wall_prices = snap.get("wall_prices", {})
        # The snapshot has no expiration field; ask the service directly.
        expiration = atm_svc.get_ticker_expiration(t_upper)
        
        # Skip if missing critical data
        if spot <= 0:
            continue
        
        # Format expiration date for display
        exp_date = ""
        if expiration:
            # expiration is typically in format "YYYY-MM-DD" or similar
            exp_date = expiration
            
        spacing = get_strike_spacing(spot) if spot > 0 else 1.0
        zone = spacing * 0.25
        
        # Check BUY CALL condition:
        # Put_Wall < Spot_Price < Put_Wall + (Strike_Spacing / 4)
        # Put Wall must be STABLE
        if put_wall is not None:
            if (put_wall < spot < put_wall + zone and 
                _wall_is_stable(t_upper, "put") and
                _is_alert_needed(t_upper, "call")):
                
                # CALL mark at the put-wall (support) strike
                call_price = wall_prices.get("put_wall_call_price") or opt_prices.get("call") or "N/A"
                
                alert = f"{t_upper} | {spot:.2f} | BUY CALL {put_wall:.2f} @ {call_price} | Exp: {exp_date}"
                alerts.append(alert)
                _update_alert_timestamp(t_upper, "call")
                continue
        
        # Check BUY PUT condition:
        # Call_Wall > Spot_Price > Call_Wall - (Strike_Spacing / 4)
        # Call Wall must be STABLE
        if call_wall is not None:
            if (call_wall > spot > call_wall - zone and 
                _wall_is_stable(t_upper, "call") and
                _is_alert_needed(t_upper, "put")):
                
                # PUT mark at the call-wall (resistance) strike
                put_price = wall_prices.get("call_wall_put_price") or opt_prices.get("put") or "N/A"
                
                alert = f"{t_upper} | {spot:.2f} | BUY PUT {call_wall:.2f} @ {put_price} | Exp: {exp_date}"
                alerts.append(alert)
                _update_alert_timestamp(t_upper, "put")
                continue
    
    return alerts


def format_alerts_for_output(alerts: list[str]) -> str:
    """Format alerts for output - maximum 5 lines."""
    if not alerts:
        return ""
    return "\n".join(alerts[:5])


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
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
