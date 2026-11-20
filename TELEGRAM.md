# Telegram Alerts — GammaEx

The app pushes push-notification-style alerts to a Telegram chat for two strictly-defined GEX Wall BUY conditions. Configuration, generation, and sending are handled by `scripts/telegram_alerts.py`; the send hook is invoked from the Order Flow fragment every refresh.

> Nothing is sent unless `[telegram]` is configured. Without it the feature is silently disabled — no errors, no logs.

---

## Setup

### 1. Create a bot and get the chat ID

- **Bot token**: message [@BotFather](https://t.me/BotsFather) on Telegram → `/newbot` → Choose a username (must end in `bot`) → copy the token (format `123456789:ABC-...`).
- **Chat ID**: send any message to the bot (or add it to a group and post once), then read the ID:

  ```
  curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
  ```

  and read `"chat":{"id": ...}` from the JSON. A group ID looks like `-100xxxxxxxxxx`.

- **Groups**: the bot must be a member of the target group. Privacy mode does not block the bot's own `sendMessage` calls, only reading others' messages, but the bot still needs to be added.

### 2. Configure

Add to `.streamlit/config.toml`:

```toml
# Telegram alerts for GEX Wall-based BUY signals.
# Set bot_token and chat_id to enable.
# See https://core.telegram.org/bots for how to create a bot and get your token.
[telegram]
bot_token = "123456:ABC-YOUR-TOKEN"
chat_id   = "-1001234567890"
```

Environment overrides (take precedence over config.toml, useful for service deployments):

| Variable | Purpose |
|---|---|
| `GEX_TELEGRAM_BOT_TOKEN` | Bot token override |
| `GEX_TELEGRAM_CHAT_ID` | Chat ID override |

Both values are loaded in `scripts/config.py` into `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

### 3. Restart

Restart the Streamlit app — config is read once at import time.

### 4. Verify

Send a test alert:

```
.venv/bin/python -c "
from scripts import telegram_alerts
print(telegram_alerts.send_telegram_alerts(['TEST | pipeline check']))
"
```

`True` means the Telegram API accepted the message (HTTP 200) — check the chat. `False` with `Telegram not configured` in the log means the config isn't loading; `Failed to send` means a network or API problem (e.g. wrong token, bot not in the chat).

---

## Alert conditions

Only two BUY signals are alerted. `generate_telegram_alerts()` evaluates them for every ticker in `ticker_history` (the current symbol is included even if not yet in history), using real-time spot and walls from the ATM option streaming service snapshots.

### BUY CALL

All of the following must be true:

```
Put_Wall < Spot_Price < Put_Wall + (Strike_Spacing / 4)
Spot_Price > VWAP
NET_GEX > 0
```

Spot is inside the upper edge of the **Put Wall** support zone, above the session VWAP, and net Gamma Exposure is positive (demand-side bullish). Requires the Put Wall to be **STABLE**.

### BUY PUT

All of the following must be true:

```
Call_Wall > Spot_Price > Call_Wall - (Strike_Spacing / 4)
Spot_Price < VWAP
NET_GEX < 0
```

Spot is inside the lower edge of the **Call Wall** resistance zone, below the session VWAP, and net Gamma Exposure is negative (demand-side bearish). Requires the Call Wall to be **STABLE**.

### Stability gate

A wall counts as STABLE only after surviving `_WALL_STABLE_REFRESHES = 2` consecutive unchanged refreshes, checked via `_wall_is_stable()` against the `_wall_stability` session-state tracker (same threshold as the UI). Unstable walls never alert, even if the price condition is met.

### Deduplication

- One alert per ticker + signal type while the condition remains **active** — tracked in `_alert_state` session state (`{symbol: {"call": last_ts, "put": last_ts}}`).
- Re-alert only after the condition becomes inactive and triggers again (`_is_alert_needed()` re-checks the live price/wall condition each refresh).
- At most **5 alerts** per refresh cycle.

### Never sent

- SELL, HOLD, WAIT, neutral, or speculative signals
- Alerts for unstable walls or incomplete data (missing spot/walls/snapshot)
- Any commentary — if no signal qualifies, nothing is output

---

## VWAP computation

The VWAP used in the alert gates is a session-anchored 1-minute VWAP computed from the Parquet candle cache, with automatic fallback for index tickers:

| Ticker | Volume | VWAP source |
|---|---|---|
| **SPY, IWM, QQQ, AAPL, …** (equities) | Real volume in parquet | Own volume-weighted VWAP (`Σ typical_price × volume / Σ volume`) |
| **$SPX, SPX** | Zero (index) | **SPY** VWAP (volume-weighted) |
| **$RUT, RUT** | Zero (index) | **IWM** VWAP (volume-weighted) |
| **$NDX, NDX** | Zero (index) | **QQQ** VWAP (volume-weighted) |

- VWAP is session-anchored: resets at the first bar at/after 9:30 ET of a new ET date (same RTH logic as the charts).
- Index tickers without parquet data or with all-zero volume transparently delegate to their proxy ETF and cache the result.
- Results are memoized per ticker for **60 seconds** to avoid redundant disk reads.
- If the cache is older than 5 minutes, a fresh fetch from the Schwab API is attempted (when a live client is available).

---

## Message format

```
<emoji> GEX: +123,456,789 | SYMBOL | 250.25 | BUY CALL 250.00 @ 45.25 | Exp: 2024-12-20
```

- One line per alert, joined with `\n`, maximum 5 lines.
- Sent as HTML (`parse_mode: HTML`) so the header renders bold.
- The GEX field leads the line with a direction emoji:
  - 🟢 — positive net GEX (BUY CALL condition)
  - 🔴 — negative net GEX (BUY PUT condition)
  - ⚪ — zero net GEX (edge case, neutral)
  - N/A — missing data
- The option price (`@ ...`) comes from the wall snapshot prices, falling back to the snapshot's ATM option price, then `N/A`.

---

## Runtime integration

`render_flow_frag()` (`scripts/flow.py`, runs every 2 s while the Order Flow tab is open) calls `_maybe_send_telegram_alerts()` at the end of each refresh:

1. Skip silently if `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is empty.
2. Call `generate_telegram_alerts()` → list of alert strings.
3. If non-empty, `send_telegram_alerts()` POSTs to `https://api.telegram.org/bot<token>/sendMessage` (10 s timeout, `urllib`, no external dependency).

Alerts only generate while the app is running with a logged-in client and the Order Flow fragment is refreshing — they are not triggered by a scheduler or background worker.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| No alerts, no log output | Telegram not configured (missing/empty `[telegram]` values) — the pre-send check returns silently. Verify with the config-load check below. |
| Test send returns `False` | Token wrong (Telegram returns 401) or bot not in the target chat (403). Read the app log for `Failed to send Telegram alert: ...`. |
| Config edits have no effect | App not restarted — `config.py` reads the TOML once at import. |
| Configured but never alerts live | Normal if no qualifying setup: price must be inside a *stable* wall zone, spot must be on the correct side of VWAP, GEX must match direction, and the signal must be *fresh* (not active-when-last-alerted). Silence ≠ broken. |
| Duplicate-looking alerts | A condition that deactivates and re-triggers intentionally re-alerts; dedup is per condition, not per day. |

Config-load check (prints booleans, not the secret values):

```
.venv/bin/python -c "
from scripts import config
print(bool(config.TELEGRAM_BOT_TOKEN), bool(config.TELEGRAM_CHAT_ID))
"
```

---

## Files

| File | Role |
|---|---|
| `scripts/telegram_alerts.py` | Condition evaluation, VWAP gate, dedup state, Telegram send |
| `scripts/flow.py` | `_maybe_send_telegram_alerts()` hook in `render_flow_frag()` |
| `scripts/config.py` | Loads `[telegram]` bot_token/chat_id + env overrides |
| `.streamlit/config.toml` | User configuration (`[telegram]` section) |
| `.streamlit/config.toml.example` | Documented template for the section |
