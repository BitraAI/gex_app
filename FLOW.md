# Order Flow

Live bullish / bearish order-flow dashboard for the ATM (at-the-money) front
expiration of every ticker in `~/.local/share/gex_app/ticker_history.json`.

## What it shows

A Streamlit dataframe (`flow.render_atm_order_flow_grid`) with one row per
    tracked ticker:

| Column | Meaning |
| --- | --- |
| **Ticker** | Display symbol (index symbols like `SPX` kept as-is; streamed via ETF proxy `SPY`/`IWM`/`QQQ`). |
| **Spot** | Latest spot price (REST pre-fetch or live equity stream). |
| **Trend** | Direction of L2 book-imbalance pressure over the last 60 s, sourced from `StreamingService.trend_data()`. Labels: **up** / **down** (plain direction), **UP** / **DOWN** (strong: `|book_imbalance| > 0.3` **and** matching sign on `flow_speed` **and** `flow_acceleration`), **bullish** / **bearish** (reversal: previous tick was `down→up` or `up→down` — the reversal label takes precedence and is always bolded in the grid), or **flat** (cold-start or no strong signal). |
| **Call Price** | CALL option mark at the **put-wall (support) strike** — what the call is worth at the support level. Falls back to the ATM call mark until the wall prices are computed. For index symbols (SPX/RUT/NDX) only REST chain marks are used (the streamed bid/ask belong to the ETF proxy's options). |
| **Put Price** | PUT option mark at the **call-wall (resistance) strike** — what the put is worth at the resistance level. Falls back to the ATM put mark until the wall prices are computed. Same index-symbol rule as Call Price. |
| **Support** | Put wall value (support level from Options data). |
| **Resistance** | Call wall value (resistance level from Options data). |
| **Book Imbalance** | Live Level-2 order-book pressure (OPTIONS): Positive → bullish, Negative → bearish. Ratio `(sum bid TOTAL_VOLUME − sum ask TOTAL_VOLUME) / sum` over the best book levels, range [-1, 1], refreshed on every book update. |
| **Flow Speed** | First difference of the L2 book-imbalance series over the trailing 60 s: `flow_speed = history[-1][1] − history[0][1]` (last ratio minus first ratio in the window). Displayed as a signed integer. Green > 0, red < 0, orange otherwise. |
| **Flow Acceleration** | Second difference of the L2 book-imbalance series: `flow_acceleration = recent_flow − previous_flow` (where `recent_flow = history[-1][1] − history[mid][1]`, `previous_flow = history[mid-1][1] − history[0][1]`, `mid = max(1, len(history) // 2)`). Displayed with 2 decimals. Green > 0, red < 0, orange otherwise. |
| **Absorption** | Order absorption (contracts per $1): cumulative ATM option volume over the trailing 60 s divided by the spot displacement over the same window. High = heavy flow absorbed, price pinned (level holding); low = price drifting on thin flow. Computed by `AtmOptionVolumeService.get_ticker_absorption`. Green ≥ 1000, red < 300, orange otherwise. |
| **Net Flow** | Net executed flow over the trailing 60 s: `buy_vol − sell_vol` (rolling window, delta-adjusted). Green > 0, red < 0, orange otherwise. |
| **Liquidity Flow** | Net change in L2 OPTIONS-book resting depth at the best levels over the trailing 60 s: `liquidity_flow = depth_now − depth_60s_ago` (from `StreamingService.trend_data`). Positive = liquidity being posted (book refilling); negative = liquidity being drained (break risk). Green > 0, red < 0, orange otherwise. |

Refresh cadence: the grid is wrapped in `@st.fragment(run_every=2)` (the
module-level `_flow_grid` in `app.py`), so it updates every 2 seconds. The
parent `render_tabs_frag` runs every 10 s and renders the legend / CSS
once per outer tick via `flow.render_flow_legend_and_style()` so the
static HTML is not re-injected on every 2-second data tick (avoids DOM
flicker). `_flow_grid` is defined at module scope (not nested inside
`render_flow_frag`) so Streamlit does not destroy and recreate it every
10 s.

### Market status indicator

The grid displays a market status indicator in the header area:

| Status | Meaning | Colour |
| --- | --- | --- |
| **Market Open** | US regular trading hours are open (09:30–16:00 ET, Mon–Fri, excluding New Year's / Independence / Christmas). | Green `●` |
| **Market Closed** | Market is currently closed (after hours, weekend, or holiday). Flow values are frozen from the last session. | Amber `●` |

Market-hours detection lives in `flow.is_market_open()`.

### Trend

Trend reflects the **rate of change of L2 book-imbalance pressure** over the
last 60 seconds, not the absolute level. It is computed on demand by
`StreamingService.trend_data()` from the OPTIONS LEVEL2 books and read
by the grid and the Telegram trend alerts via
`StreamingService.get_ticker_trend_data(display_symbol)`.

How it works:

1. **Book snapshots** - on every Level 2 options book update the aggregate
   `book_imbalance = (sum bid TOTAL_VOLUME - sum ask TOTAL_VOLUME) / sum`
   across the best options book price levels is appended as
   `(timestamp, ratio)` to a per-symbol 60s history.
2. **Cold-start guard** - if fewer than 2 samples exist the trend is
   **flat** and `flow_speed` / `flow_acceleration` are 0.
3. **Book-pressure momentum** - the window is split at the exact midpoint
   (`mid = max(1, len(history) // 2)`) so every sample is used:
   - `flow_speed = history[-1][1] - history[0][1]` (first difference over the
     whole 60 s window)
   - `previous_flow = history[mid-1][1] - history[0][1]` (change in older half)
   - `recent_flow = history[-1][1] - history[mid][1]` (change in recent half)
   - `flow_acceleration = recent_flow - previous_flow`
4. **Trend cascade** - the label is set by a single prioritized ladder
   (no separate "override" step): strong `UP` / `DOWN` require
   `|book_imbalance| > 0.3` **and** matching sign on `flow_speed`
   **and** `flow_acceleration`; plain `up` / `down` require
   `|book_imbalance| > 0.3` **and** matching sign on `flow_speed`; else
   `flat`. See the full cascade table below.
5. **Reversal detection** - compared against the previous tick's stored trend
   (`_prev_trend`); only the exact plain-direction transitions fire a
   reversal (transitions to/from `UP` / `DOWN` / `flat` do **not**):
   - previous `down` and current `up` => `trend_reversal = "bullish"`
   - previous `up` and current `down` => `trend_reversal = "bearish"`
   - otherwise => `trend_reversal = None`

The final `trend` (and `book_imbalance`, `flow_speed`, `flow_acceleration`) is
    returned by `StreamingService.trend_data` and consumed unchanged by the grid
(via `flow.render_atm_order_flow_grid`) and the Telegram alerts.

The trend label is classified inside `trend_data` (one source of truth — there is
no separate `classify_trend_signal` helper), using the L2 book-imbalance ratio
and its first / second differences:

| Label | Condition |
|-------|-----------|
| **UP** (strong up)   | `book_imbalance > 0.3` **and** `flow_speed > 0` **and** `flow_acceleration > 0` |
| **DOWN** (strong down) | `book_imbalance < −0.3` **and** `flow_speed < 0` **and** `flow_acceleration < 0` |
| **up**               | `book_imbalance > 0.3` **and** `flow_speed > 0` |
| **down**             | `book_imbalance < −0.3` **and** `flow_speed < 0` |
| **flat**             | none of the above (or cold start: fewer than 2 history samples) |

Where:
- `book_imbalance = (Σ bid TOTAL_VOLUME − Σ ask TOTAL_VOLUME) / Σ` over the best
  L2 options-book price levels, range `[−1, 1]`.
- `flow_speed = history[-1][1] − history[0][1]` over the trailing 60 s history
  (first difference over the whole window).
- `flow_acceleration = recent_flow − previous_flow`, where
  `previous_flow = history[mid-1][1] − history[0][1]` and
  `recent_flow = history[-1][1] − history[mid][1]`, with
  `mid = max(1, len(history) // 2)`.

A **reversal** is derived by comparing the current trend to the previous tick's
stored trend (`_prev_trend`):

| Reversal label | Condition |
|----------------|-----------|
| `bullish` | previous trend was `down` **and** current trend is `up` |
| `bearish` | previous trend was `up` **and** current trend is `down` |
| `None`    | otherwise |

The grid's **Trend column** shows `trend_reversal` if present (`bullish` /
`bearish`), otherwise the bare `trend` (`up` / `down` / `UP` / `DOWN` /
`flat`). The cell is colored green for `bullish` / `up`, red for `bearish` /
`down`, amber for `flat`, and the label is always bolded. The Spot-cell
background shading uses the same components (wall proximity, book imbalance,
flow speed, flow acceleration), but the book-imbalance / flow-speed /
flow-acceleration scores are only counted when the spot is **near a wall**
(`spot ≤ put_wall + pw_buf` or `spot ≥ call_wall − cw_buf`, with
`pw_buf = _wall_buffer(put_wall)`, `cw_buf = _wall_buffer(call_wall)`:
`max(0.02 % × wall price, 5 cents)` so low-priced tickers still get a
meaningful zone). Outside the buffer those scores contribute nothing.


## Data pipeline

```
Schwab WebSocket (LEVEL1_EQUITIES + LEVEL1_OPTIONS + OPTIONS_BOOK)
        |
        |----------------------------------|
        v                                  v
   LEVEL1 trades                      LEVEL2 options books
   bid, ask, last,                     per-symbol book messages
   volume (ATM service)                (BIDS / ASKS level TOTAL_VOLUME)
   (_process_trade_ticker)             (StreamingService book handlers)
   -> buy/sell                         -> book_imbalance ratio [-1, 1]
   -> GEX totals                       -> appended to per-symbol 60s rolling history
         |                              -> flow_speed / flow_acceleration
         |                                  (first / second difference)
        |                                  -> trend (up/down/UP/DOWN/flat)
        |                                  -> reversal (bullish/bearish)
        v                                  (StreamingService.trend_data)
   Cumulative per-ticker GEX totals
   { Put Wall, Call Wall }
        |
        v
flow_cache (st.session_state)  -- updated by update_flow_cache()
        |
        v
ATM Order Flow dataframe (Streamlit, styled like Options Data table)
```

Key points:

- **ATM strike** is computed per ticker from its live spot via
  `calculate_atm_strike` (strike spacing by price band).
- **Front expiration** is managed per-ticker. The front (earliest) expiration
  is read from the ticker's option-chain data (`expirations[0]`) and pushed
  via `set_ticker_expiration()`, which triggers a re-subscription when it
  changes so the ticker subscribes to the correct option
  contracts. This ensures non-primary tickers (AAPL, TSLA, etc.) don't
  inherit the primary's expiration and subscribe to non-existent contracts.
- The service runs on the **same shared StreamClient** as the equity stream
  (no second WebSocket). Bid/ask for direction inference comes from the option
  quotes on that stream.
- `_ticker_flows` is keyed by the user's original display symbol, with ETF-proxy
  remapping (`SPX→SPY`, `RUT→IWM`, `NDX→QQQ`) handled for the subscription
  symbol only.

## How to open it

Open the **Order Flow** tab on the main page
(`app.py` → `render_tabs_frag`, tab7 → `render_flow_frag`).
The tab renders the ATM Order Flow grid directly and starts streaming
automatically via `ensure_atm_streaming`.

## Files

| File | Role |
| --- | --- |
| `flow.py` | Shared rendering: `render_atm_order_flow_grid`, `render_flow_legend_and_style`, `update_flow_cache`, `ensure_session_defaults`, `is_market_open`. Wall refresh: `maybe_fire_wall_zone_alerts`, `_refresh_walls_for_symbol`, `_recompute_symbol`, `_compute_walls_for_symbol`. Near-wall buffer: `_wall_buffer`, `_WALL_ZONE_BUFFER`. Trend coloring: `_trend_color` (in `render_atm_order_flow_grid`); the trend *classification* itself lives in `StreamingService.trend_data` (not `flow.py`). |
| `option_streaming_service.py` | `AtmOptionVolumeService` — WebSocket handling, classification, per-ticker flow. |
| `app.py` | Main app; owns streaming (`ensure_atm_streaming` via ticker Refresh), `render_flow_frag`, Order Flow tab. |
| `client.py` | `fetch_quotes` — REST spot pre-fetch for all tickers. |

## Architecture: streaming & spot feeding

### Index Symbol Spot Handling

The updated ATM streaming service includes enhanced spot price handling for index symbols:

- The `set_ticker_spot()` method now **triggers a re-subscription** when a ticker has no option subscriptions yet (`call_sym`/`put_sym` are `None`) and the service is running
- This ensures index tickers like `$SPX`, `$RUT`, and `$NDX` gain their option symbols after `register()` wipes `_ticker_flows` or when the IndexSpotPoller delivers a fresh spot
- For index symbols, actual spot prices are stored in the **display symbol** (`$SPX`, etc.) rather than the ETF proxy (`SPY`, `IWM`, `QQQ`) that is used for WebSocket streaming
- The flow tracking uses the **original display symbol** as the key, with ETF-proxy remapping (`SPX→SPY`, `RUT→IWM`, `NDX→QQQ`) handled internally for the WebSocket subscription only
- Index spots are fetched via REST with the plain OAuth quote symbol (`$SPX`, `$RUT`, …) — the `$SPX:X` suffix is rejected by Schwab as `errors.invalidSymbols`. The ATM Call/Put prices shown for index tickers are the REST chain marks (stored separately in `call_mark`/`put_mark`); the streamed ETF-proxy option quotes only drive buy/sell direction inference and never overwrite the index marks.

### Shared StreamClient

Both the equity stream (`StreamingService`) and ATM option flow
(`AtmOptionVolumeService`) share a single `schwab.streaming.StreamClient`
and therefore a single WebSocket connection. The equity service owns the
connection and runs the `handle_message()` loop; the ATM service registers
its handler via `add_level_one_option_handler` and subscribes via
`level_one_option_subs`. The streaming service also subscribes to LEVEL1_OPTIONS
for continuous ATM flow and OPTIONS_BOOK for Level 2 options data.

### Spot price feeding

Non-primary tickers (IWM, QQQ, NVDA, etc.) need spot prices to calculate
their ATM strikes, but they don't have their own equity stream. Spot prices
are fed via a two-step process:

1. **REST pre-fetch (throttled)**: `ensure_atm_streaming` calls `fetch_quotes` (from
   `client.py`) for all tickers, but only every ~10 seconds — the fragment
   itself ticks every 2 s, but the REST call is gated by
   `s["_spot_fetch_ts"]` so the Streamlit thread isn't blocked on every
   cycle. The `fetch_quotes` function returns `client.get_quotes()` parsed
   as JSON — note that the Schwab `AsyncClient.get_quotes()` returns a raw
   `Response` object, so `.json()` must be called on it. Between REST
   fetches, spots already cached in `s.spot_cache` are fed to the service.
2. **Bulk feed**: After pre-fetch, `bulk_update_spots(spot_map)` sets all
   spots in `_ticker_flows` in a single lock acquisition, then triggers one
   `_do_subscribe` to re-subscribe with correct ATM strikes.

### Wall (support/resistance) refresh cadence

The Support / Resistance columns come from the put/call walls computed by
`compute_analytics` on a REST option chain. Walls are refreshed with a
**hybrid trigger** in `flow.maybe_fire_wall_zone_alerts` (checked every 2 s
fragment tick), with two tiers:

| Tier | Trigger | Cost |
| --- | --- | --- |
| **Fast wall refresh** | spot moved ≥ half a strike **or** ≥ 180 s elapsed (`_WALL_RECOMPUTE_MAX_INTERVAL`) | Lightweight — `fetch_option_chain` + `parse_option_chain` + `compute_analytics` only (`_refresh_walls_for_symbol`), then pushes walls / expiration / ATM marks to the ATM service. Skips rate, yield, RV, and IV-rank. |
| **Full recompute** | ≥ 300 s elapsed (`_WALL_FULL_RECOMPUTE_INTERVAL`) | Full pipeline (`_recompute_symbol`) — adds IV rank, RV, diff/strategy alerts, and the `_ticker_analytics_cache` used for Telegram alert headers. |

Both are throttled so a single ticker never triggers a wall refresh more
often than every 30 s (`_WALL_RECOMPUTE_MIN_INTERVAL`), which caps Schwab
API load in fast markets while the 180 s freshness floor keeps walls current
in quiet ones. Walls are also recomputed on a manual Refresh on the main
page (`fetch_data`) and by the Trade Signals tab scan.

### Trend alerts (Telegram)

In addition to the diff-based wall-zone / gamma-flip / wall-change alerts,
`maybe_fire_wall_zone_alerts` pushes a **trend alert** to Telegram whenever
the streaming spot is near a wall **and** the L2 trend produces a directional
signal. The alert text is the literal `trend_reversal` (`bullish` /
`bearish`) if a reversal just occurred, otherwise the bare `trend`
(`up` / `down`). Telegram maps the direction to a trade suggestion:

| Trend alert body | Direction | Suggestion |
| --- | --- | --- |
| `🟢 BULLISH` / `🟢 UP`   | buy  | `BUY CALL $<wall_mark>` |
| `🔴 BEARISH` / `🔴 DOWN` | sell | `BUY PUT $<wall_mark>` |

Sourced straight from `StreamingService.trend_data()` (no separate
`classify_trend_signal` helper), so the grid and the alerts share the same
label set.

**Conviction gate.** A trend label alone is not enough — before it fires,
`maybe_fire_wall_zone_alerts` computes a 0–5 conviction score
(`_conviction_score` in `flow.py`) from how many independent metrics agree
with the signal direction:

| +1 point when | Meaning |
| --- | --- |
| \|book_imbalance\| > 0.3 | price pressure is strong |
| flow_speed & flow_acceleration share a sign | momentum is accelerating |
| liquidity_flow > 0 (up) / < 0 (down) | book refills in an up move, drains in a down move |
| net_flow(60 s) > 0 (up) / < 0 (down) | delta-adjusted executed flow matches direction |
| absorption ≥ 20 vol/$1 (`_ABSORPTION_MIN_VOL`) | heavy flow is being absorbed |

Plain `up` / `down` alerts require score ≥ 3; reversals
(`bullish` / `bearish`) already represent a flip and clear with score ≥ 2.
Weak / flat-ish trends that don't corroborate stay quiet, and the dedicated
💥 wall-broke alert bypasses the gate entirely. Thresholds are the tunable
`_ALERT_MIN_CONVICTION_PLAIN` / `_ALERT_MIN_CONVICTION_REVERSAL` constants
in `flow.py`.

**Compact signal line.** When a trend alert fires, `notify_alerts(..., trend_alert=...)`
renders a single dense signal line instead of repeating the flow-metric
header rows, folding in the corroborating metrics:

    🟢 BULLISH - BUY CALL $8.25 · Imb +0.42 · Net +1,200 · Liq -800 · Abs 9,500

(`Imb` = book imbalance, `Net` = 60 s net flow, `Liq` = liquidity flow,
`Abs` = absorption.) GEX / VRP / IV rank / wall zone and
`Wall absorbed` remain separate header lines for context. Non-trend alerts
keep the full per-metric header layout.

`flat` and strong `UP` / `DOWN` are **not** surfaced as Telegram alerts —
only `up`, `down`, and the reversal labels can fire a send. Like all wall-zone
alerts, trend alerts require the walls to be stable for 2 consecutive
refreshes and respect the 600 s per-ticker cooldown.

### Order absorption (Telegram + grid)

**Price-impact absorption** (`AtmOptionVolumeService.get_ticker_absorption`,
surfaced as the grid **Absorption** column and the Telegram
`Absorption: <n> vol/$1` header line — folded into the compact trend signal
line as `Abs`) measures how much aggressive ATM option flow the book consumed
without moving the price:

    absorption = Δ(cumulative ATM volume over 60 s) / max(|Δspot| over 60 s, 0.05)

High absorption (≥ 1000 vol/$1) means heavy flow is being soaked up at a level
(price pinned — support/resistance holding); low absorption (< 300) means the
price is drifting on thin flow.

**Executed flow** (`AtmOptionVolumeService.get_ticker_executed_flow`, the grid
**Net Flow** column and the Telegram
`Net Flow (60s): <n>` header line — folded into the compact trend signal
line as `Net`) is the **delta-adjusted** aggressor split: every trade
print is classified buyer- vs seller-initiated (`_infer_dir` against the
bid/ask mid), then folded by option side so `buy_vol` counts **buying calls
and selling puts** (bullish pressure) while `sell_vol` counts selling calls
and buying puts (bearish pressure):

    buy_vol   = call_buy_vol  + put_sell_vol
    sell_vol  = call_sell_vol + put_buy_vol

A rolling 60 s net (`buy_vol − sell_vol`) gives current pressure, so the
`Net` line is the delta-adjusted net flow (equivalent to `bullish − bearish`).
The per-contract raw sides (`call_buy_vol` / `call_sell_vol` /
`put_buy_vol` / `put_sell_vol`) are still kept in the 1-second OHLCV bars, so
both views remain computable.

**Wall absorption** in `flow.maybe_fire_wall_zone_alerts` snapshots the
cumulative ATM volume when spot enters a wall zone and reports how many
contracts were absorbed while spot stayed inside (Telegram
`Wall absorbed: <n> contracts`). When spot then leaves the zone after
absorbing ≥ 100 contracts, the wall is treated as **broken** and a dedicated
💥 `Resistance/Support wall BROKE after absorbing <n> contracts` alert fires —
heavy absorption followed by a break is a high-conviction move.

### Liquidity flow (L2 book)

**Liquidity flow** (`StreamingService._liquidity_flow`, exposed via
`trend_data` as the grid **Liquidity Flow** column and the Telegram
`Liquidity Flow: <n>` header line — folded into the compact trend signal
line as `Liq`) measures whether resting liquidity at the best L2 OPTIONS-book
levels is being added or drained over the trailing 60 s:

    depth = Σ bid TOTAL_VOLUME + Σ ask TOTAL_VOLUME (best levels)
    liquidity_flow = depth_now − depth_60s_ago   (contracts)

Positive = liquidity is being posted (the book is refilling — strong
support/resistance); negative = liquidity is being consumed (the book is
draining — elevated break risk).  Unlike `flow_speed` (which is the
dimensionless rate of change of the book-imbalance *ratio*), liquidity flow
is measured in actual contracts of resting volume.

### Registration & subscription order

`ensure_atm_streaming` runs **inside** the `@st.fragment(run_every=2)`
body (not outside it), because code outside a fragment does not re-run on
fragment timer ticks. The flow on each cycle:

1. Pre-fetch spots via `fetch_quotes` → `spot_cache`
2. If `_need_register` is True (first run, symbol change, or expiration
   change): call `register()` which clears `_ticker_flows`, re-initializes
   all tickers with spot=0, and registers the handler. **Critically,
   `register()` does NOT call `_do_subscribe`** — the caller does.
   - **Exception**: When re-registering due to a reconnect (`_needs_reconnect`
     flag), the function returns early to avoid feeding spots before the
     WebSocket connection is fully established.
3. Feed live spot from equity stream for the primary ticker.
4. `bulk_update_spots(spot_map)` sets spots from `spot_cache` and triggers
   `_do_subscribe`.

The reason `register()` does not subscribe is a threading race: if it queued
`_do_subscribe` on the event loop, the event-loop thread could pick it up
**before** `bulk_update_spots` on the main thread has set the spots — so
all non-primary tickers would see spot=0 and be skipped.

`_need_register` is also tripped when the watchdog sets
`atm_svc._needs_reconnect = True` (see "Watchdog / stale-feed detection"
below). On the next cycle `ensure_atm_streaming` clears the flag and calls
`register()` to re-establish the WebSocket handler with a fresh
`_last_tick_time`.

### Watchdog / stale-feed detection

`AtmOptionVolumeService.is_feed_stale(max_age_seconds=60)` (in
`option_streaming_service.py`) returns True when no option ticks have been
received for `max_age_seconds`. The `_flow_grid` fragment in `app.py`
checks this every 2 s while the market is open; if stale, it sets
`atm_svc._needs_reconnect = True` so the next `ensure_atm_streaming` cycle
fully re-registers the handler (see "Registration & subscription order").

`_last_tick_time` is updated on every received option message by
`_option_handler` and reset to "now" inside `register()` so the watchdog
does not immediately re-fire after a re-registration.

### Schwab SDK field mapping

The Schwab streaming SDK's `_Handler.label_message()` renames certain fields.
For LEVELONE_OPTIONS messages, the option symbol is in the **`key`** field,
not `SYMBOL`. The handler uses `c.get("key", "") or c.get("SYMBOL", "")` to
handle both formats.

### Reconnection

There are two cooperative mechanisms:

1. **Equity-stream reconnect callback**: when the equity WebSocket
   disconnects and reconnects (driven by `StreamingService._run` calling
   every callback registered via `StreamingService.on_reconnect`), the ATM
   service re-subscribes its option chain after the equity feed is back
   online. The callback is registered once in `ensure_atm_streaming`
   (`app.py`) as `_on_equity_reconnect` and schedules
   `_delayed_resubscribe(sc)` on the ATM service's event loop, which
   awaits `asyncio.sleep(2)` for the re-logged-in WebSocket to settle
   before calling `atm_svc._do_subscribe(sc)`.

2. **Subscription-time dead connection**: when `_do_subscribe` raises a
   `ConnectionClosedError`, `ConnectionClosed`, or a Schwab
   "connection not found / stream connection" error, the service sets
   `self._needs_reconnect = True`. `ensure_atm_streaming` includes this
   flag in its `_need_register` condition, so the next cycle calls
   `register()` (clearing it) to recreate the handler and re-subscribe.

Either path ends with the same `_do_subscribe` building all per-ticker
ATM option symbols and re-issuing `level_one_option_subs`. Subscription
requests are deduplicated against `_last_sub_ok_set` so identical symbol
sets are not re-sent — re-sending identical subscription requests every
2 s causes the Schwab server to rate-limit and silently drop the feed.

## Notes / limitations

- Flow totals are **cumulative** for the session, not a rolling window.
- Uses the option bid/ask mid as the trade-direction threshold. If
  bid/ask has not yet arrived for an option, the trade is split evenly between
  bullish and bearish.
- Each ticker uses its own per-ticker expiration (the earliest date in its
  option chain, `expirations[0]`, set via `set_ticker_expiration()`), so
  non-primary tickers subscribe to the correct option contracts rather than
  inheriting the primary's expiration.
- `ensure_session_defaults` reuses `app._SESSION_DEFAULTS` so the page and main
  app never drift apart.
- The REST pre-fetch (`fetch_quotes`) runs every ~10 s (gated by
  `s["_spot_fetch_ts"]`), even though the fragment ticks every 2 s. This is
  a lightweight call but does hit the Schwab API; rate limiting is not
  expected for a single user session. Between fetches, cached spots from
  `s.spot_cache` (fed by the equity stream and prior REST calls) are used.
