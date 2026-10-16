# Telegram Alerts

Optional Telegram Bot integration that pushes GEX signal/alert events from the
Streamlit dashboard to a configured Telegram chat. Alerts are sent synchronously
over HTTPS via the Telegram Bot API (`/sendMessage`). Failed sends are logged
but never crash or interrupt the host app.

---

## Setup

Add a `[telegram]` section to `config.toml`:

```toml
[telegram]
enabled = true                     # set false to mute without removing secrets
BOT_TOKEN = "YOUR_BOT_TOKEN"       # from @BotFather
CHAT_ID = "YOUR_CHAT_ID"           # channel @userinfobot, negative group id, or @channelname
```

### Getting credentials

1. **BOT_TOKEN** — message [@BotFather](https://t.me/BotFather), `/newbot`, follow the prompts.
2. **CHAT_ID** — create a private channel, add the bot as admin (enable Post Messages),
   then fetch `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` to read the
   chat id (a `-100…` channel id, negative group id, or `@channelname`).
3. Environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` override
   `config.toml`.

---

## How alerts work

### Multi-ticker alerts (inside Streamlit)

There is **no cron job or standalone runner**. Alerts run inside the Streamlit
app on every Order Flow grid refresh (~2 s).

`flow.maybe_fire_wall_zone_alerts()` iterates every ticker in
`~/.local/share/gex_app/ticker_history.json`, diffs each symbol's current state
against its previous baseline (`telegram_notifier.diff_alerts`), and pushes
Telegram alerts on detected transitions.

Per-symbol previous state is persisted to
`~/.local/share/gex_app/alert_state.json` so consecutive refreshes detect true
transitions rather than re-broadcasting on every poll.

Because alerts piggyback on the dashboard's existing L1/L2 option stream, each
tracked ticker sees its own streaming spot, walls, and trend data drive the
diff rules. Keeping the dashboard open during market hours is all that's
required for hands-free multi-ticker alerts.

### Single-ticker in-app alerts

`app.check_alerts()` runs the same `diff_alerts()` pipeline for the currently
selected symbol when the main page refreshes analytics.

---

## Alert types detected

`telegram_notifier.diff_alerts(prev, analytics, spot)` detects:

| Event | Description |
|-------|-------------|
| **Gamma Flip change** | Gamma flip strike value changed |
| **Dealer gamma flip** | Dealer position flipped Long Gamma ↔ Short Gamma |
| **Call Wall moved** | Call wall strike value changed (e.g. `$495.00 → $500.00`) |
| **Put Wall moved** | Put wall strike value changed (e.g. `$485.00 → $480.00`) |
| **Price crossed above/below Resistance** | Spot pierced the Call Wall level |
| **Price crossed above/below Support** | Spot pierced the Put Wall level |

Wall-change alerts fire regardless of wall stability. Plain trend/reversal
alerts additionally require `_wall_stable >= 2` consecutive refreshes to filter
jittery moving walls.

---

## Alert suppression

- **Outside market hours**: Alerts are suppressed when US regular trading is
  closed (Mon–Fri 09:30–16:00 ET, excluding major holidays) via
  `flow.is_market_open()`.
- **Cooldown**: `_WALL_ZONE_ALERT_COOLDOWN` throttles repeat sends per symbol.
- **First-seen baseline**: When a ticker is first added, `diff_alerts` returns
  an empty alert list so the initial poll does not fire spurious "changed"
  alerts.

---

## Telegram message format

Every alert renders as one HTML message with this standard header, followed by
the alert body lines:

```
<b>SYMBOL</b>
Price: <code>$XXX.XX</code>
🟢 GEX: <code>X</code>
🟢 Near Support $XXX.XX
🟢 Absorption: <code>X</code> vol/$1
🟡 Wall absorbed: <code>X</code> contracts
🟢 Net Flow (60s): <code>+X</code>
🟢 Flow Ratio: <code>XX</code>

<alert body lines>
```

### Header fields (when data available)

| Field | Format | Source |
|-------|--------|--------|
| Symbol | `<b>SYMBOL</b>` | ticker |
| Price | `Price: <code>$XXX.XX</code>` | spot |
| GEX | `🟢/🔴 GEX: <code>X</code>` | net GEX |
| Wall zone | `🟢 Near Support $XX` / `🔴 Near Resistance $XX` | `wall_zone`, `pw`/`cw` |
| Absorption | `🟢/🔴/🟡 Absorption: <code>X</code> vol/$1` | absorption |
| Wall absorbed | `🟡 Wall absorbed: <code>X</code> contracts` | absorbed_at_wall |
| Net Flow | `🟢/🔴/🟡 Net Flow (60s): <code>+X</code>` | net_flow |
| Flow Ratio | `🟢/🔴/🟡 Flow Ratio: <code>XX</code>` | flow_ratio |

### Flow Ratio thresholds

- `flow_ratio > FLOW_RATIO_GREEN_THRESHOLD` → 🟢 (bullish bias)
- `flow_ratio < FLOW_RATIO_RED_THRESHOLD` → 🔴 (bearish bias)
- otherwise → 🟡 (neutral)

### Trend alerts (compact body)

When a trend reversal fires (`bullish`/`bearish`), the header is compact —
absorption and net flow appear in the signal line instead of as separate header
rows:

```
🟢 <b>BULLISH</b> - BUY CALL $X · Net +X · Abs X
```

### Delivery flag

All Telegram sends use `disable_notification=False` so urgent alerts produce a
sound on the recipient's device.

---

## Three call sites

All three paths call `telegram_notifier.notify_alerts()` with consistent
parameters:

| Path | Function | Context |
|------|----------|---------|
| Streaming multi-ticker | `flow.maybe_fire_wall_zone_alerts()` | `flow.py` — full L2 context, includes `absorbed_at_wall`, `trend_alert`, `net_flow` |
| Periodic recompute | `flow._recompute_symbol()` | `flow.py` — full recompute cadence, includes `absorption` |
| Single-ticker in-app | `app.check_alerts()` | `app.py` — current symbol, includes `absorption` |

All pass `symbol`, `spot`, `gex`, `iv_rank`, `wall_zone`, `pw`, `cw`,
`wall_mark`, `flow_ratio`, `absorption`. `absorbed_at_wall`, `trend_alert`, and
`net_flow` are supplied only where zone tracking is active.

---

## Files

| File | Role |
|------|------|
| `telegram_notifier.py` | `notify_alerts()`, `diff_alerts()`, `_format()`, `send_telegram()` |
| `flow.py` | `maybe_fire_wall_zone_alerts()`, `_recompute_symbol()` |
| `app.py` | `check_alerts()` |
| `config.toml` | `[telegram]` section for credentials |
