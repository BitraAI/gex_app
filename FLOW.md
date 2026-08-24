# Order Flow

Live bullish / bearish order-flow dashboard for the ATM (at-the-money) front
expiration of every ticker in `~/.local/share/gex_app/ticker_history.json`.

## What it shows

A Streamlit dataframe (`flow.render_atm_order_flow_grid`) with one row per
    tracked ticker:

| Column | Source | Meaning |
| --- | --- | --- |
| **Ticker** | — | Display symbol (index symbols like `SPX` kept as-is; streamed via ETF proxy `SPY`/`IWM`/`QQQ`). |
| **Spot** | **Level 1** (equity stream) or REST pre-fetch | Latest spot price. |
| **Trend** | **Level 2** (OPTIONS_BOOK) | Direction of L2 book-imbalance pressure over the last 60 s, sourced from `StreamingService.trend_data()`. Labels: **up** / **down** (plain direction), **UP** / **DOWN** (strong: `|book_imbalance| > 0.3` **and** matching sign on `flow_speed` **and** `flow_acceleration`), **bullish** / **bearish** (reversal: previous tick was `down→up` or `up→down` — the reversal label takes precedence and is always bolded in the grid), or **flat** (cold-start or no strong signal). |
| **Call Price** | REST option marks (~2 s) | CALL mark at the **put-wall (support) strike** — what the call is worth at the support level. Falls back to the ATM call mark until the wall prices are computed. Refreshed every ~2 s by a batched `fetch_quotes` of the ATM / wall-strike OCC symbols (see **Call/Put Price refresh**), so the column stays live instead of only moving on the throttled analytics recompute (30–180 s). Index symbols (SPX/RUT/NDX) quote their **own index-option root** (`SPX`/`SPXW`, `RUT`/`RUTW`, `NDX`/`NDXP`), so the marks are index-level, not the ETF-proxy (SPY/IWM/QQQ) strikes. |
| **Put Price** | REST option marks (~2 s) | PUT mark at the **call-wall (resistance) strike** — what the put is worth at the resistance level. Falls back to the ATM put mark until the wall prices are computed. Same ~2 s refresh and index-option-root rule as Call Price. |
| **Support** | REST option chain (GEX) | Put wall value — the strike below spot with the highest `put_gex` (dealer gamma exposure, OI × gamma; not raw OI). See **Wall (support/resistance) refresh cadence**. |
| **Resistance** | REST option chain (GEX) | Call wall value — the strike above spot with the highest `call_gex` (dealer gamma exposure, OI × gamma; not raw OI). See **Wall (support/resistance) refresh cadence**. |
| **Book Imbalance** | **Level 2** (OPTIONS_BOOK) | Live Level-2 order-book pressure (OPTIONS): Positive → bullish, Negative → bearish. Ratio `(Σ bid TOTAL_VOLUME − Σ ask TOTAL_VOLUME) / (Σ bid TOTAL_VOLUME + Σ ask TOTAL_VOLUME)`, range [-1, 1], refreshed on every book update. See **Book pressure (L2 OPTIONS book)** below. |
| **Flow Speed** | **Level 2** (OPTIONS_BOOK, derived) | First difference of the L2 book-imbalance series over the trailing 60 s: `flow_speed = history[-1][1] − history[0][1]` (last ratio minus first ratio in the window). Displayed as a signed integer. Green > 0, red < 0, orange otherwise. See **Book pressure (L2 OPTIONS book)** below. |
| **Flow Acceleration** | **Level 2** (OPTIONS_BOOK, derived) | Second difference of the L2 book-imbalance series: `flow_acceleration = recent_flow − previous_flow` (where `recent_flow = history[-1][1] − history[mid][1]`, `previous_flow = history[mid-1][1] − history[0][1]`, and `mid` is the first sample at/after the window's **time** midpoint `mid_ts`). Displayed with 2 decimals. Green > 0, red < 0, orange otherwise. See **Book pressure (L2 OPTIONS book)** below. |
| **Absorption** | **Level 1** (ATM option volume + spot displacement) | Order absorption (contracts per $1): cumulative ATM option volume over the trailing 60 s divided by the spot displacement over the same window. High = heavy flow absorbed, price pinned (level holding); low = price drifting on thin flow. Computed by `AtmOptionVolumeService.get_ticker_absorption`. Green ≥ 1000, red < 300, orange otherwise. |
| **Net Flow** | **Level 1** (ATM option trades, delta-weighted by REST chain deltas) | Net executed **delta-weighted** flow over the trailing 60 s: `net_60 = exec_history[-1][1] − exec_history[0][1]`, i.e. the change in `delta_buy − delta_sell` over the trailing 60 s window, from the ATM call/put only. Each ATM trade is weighted by the front-month ATM option delta (call Δ > 0, put Δ < 0, plumbed from the REST chain via `set_ticker_atm_deltas`; defaults to ±0.5 before the first chain refresh), so the column reports `net_delta = delta_buy − delta_sell` rather than raw contracts. Each trade print is routed to **every** tracked flow whose stream symbol matches the option's root, so tracking both `$SPX` and `SPY` (or `$RUT`+`IWM`) updates both rows from the same proxy ticks. Green > 0, red < 0, orange otherwise. See **Order absorption (Telegram + grid)**. |
| **Liquidity Flow** | **Level 2** (OPTIONS_BOOK) | Net change in L2 OPTIONS-book resting depth at the best levels over the trailing 60 s: `liquidity_flow = depth_now − depth_60s_ago` (from `StreamingService.trend_data`). Positive = liquidity being posted (book refilling); negative = liquidity being drained (break risk). Green > 0, red < 0, orange otherwise. |

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
3. **Book-pressure momentum** - the window is split at its **time** midpoint
   (`mid_ts = history[0][0] + (history[-1][0] − history[0][0]) / 2`; `mid` is
   the first sample at/after `mid_ts`, clamped so both halves stay non-empty):
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
`down`, amber for `flat`, and the label is always bolded.

**Spot cell background coloring** is driven by wall events stored in session
state by `maybe_fire_wall_zone_alerts` (`s._wall_break_alerts` /
`s._wall_reversal_alerts`):

| Spot cell color | Condition |
| --- | --- |
| 🔴 red `#ffcccc` | Support wall **broke** (spot exited a Support zone after absorbing ≥ 100 contracts) |
| 🟢 green `#ccffcc` | Resistance wall **broke** (spot exited a Resistance zone after absorbing ≥ 100 contracts) |
| 🟢 green `#ccffcc` | Support wall **reversal** (L2 trend flipped while spot was inside a Support zone) |
| 🔴 red `#ffcccc` | Resistance wall **reversal** (L2 trend flipped while spot was inside a Resistance zone) |

When no wall event is active for a ticker, the Spot cell has no special
background. The same wall-break / wall-reversal state also drives the
background of the **Support**, **Resistance**, **Call Price** and **Put
Price** cells — each colored green or red according to whether its associated
wall broke (high-conviction move) or reversed at the wall. See `flow.py`
`_spot_bg`, `_support_bg`, `_resistance_bg`, `_call_price_bg`,
`_put_price_bg` for the full per-cell mapping.


## Data pipeline

```
Schwab WebSocket (LEVEL1_EQUITIES + LEVEL1_OPTIONS + OPTIONS_BOOK)
        |
        |---------------------------------------------|
        v                                             v
   LEVEL 1 (trades + quotes)                   LEVEL 2 (OPTIONS_BOOK)
   ATM option trades (bid/ask/last/vol)        per-symbol book messages
   (_process_trade_ticker)                     (BIDS / ASKS level TOTAL_VOLUME)
   -> buy/sell (direction vs bid/ask mid)      -> book_imbalance ratio [-1, 1]     [Level 2]
   -> buy_vol / sell_vol (delta-adjusted)      -> appended to per-symbol 60s history [Level 2]
   -> GEX totals                               -> flow_speed / flow_acceleration  [Level 2]
   -> Net Flow 60s  (exec_history Δ, delta-weighted)  -> trend / reversal (trend_data)   [Level 2]
   -> Absorption  (vol / spot displacement)    -> Liquidity Flow (depth Δ)        [Level 2]
         |                                             |
         |  Spot [Level 1 equity] / walls, option marks, index proxy spots [REST] |
         v                                             v
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
- **Index proxy strikes**: index symbols (SPX/RUT/NDX) stream their ETF
  proxy's options, so `_do_subscribe` builds their OCC call/put symbols at
  the **proxy** ATM strike (SPY ~570), never the index level (~5700) — the
  index-level strikes don't exist on the proxy's chain. The proxy last price
  is pushed via `set_ticker_proxy_spot` (REST, ~10 s) and drives only the
  subscription symbols; the displayed Spot / ATM Strike stay at the index
  level.
- **Multi-flow tick routing**: every L1 option tick is routed to **each**
  tracked flow whose stream symbol matches the option's root (padded or
  unpadded), so tracking both `$SPX` and `SPY` updates both rows from the
  same SPY ticks. The `_is_idx` guard keeps index entries' spots at their
  index level while only the ETF entry's spot follows `UNDERLYING_PRICE`.
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
| `client.py` | `fetch_quotes` — REST spot pre-fetch for all tickers + ~2 s option-mark refresh (Call/Put Price columns). |

## Architecture: streaming & spot feeding

### Index Symbol Spot Handling

The updated ATM streaming service includes enhanced spot price handling for index symbols:

- The `set_ticker_spot()` method now **triggers a re-subscription** when a ticker has no option subscriptions yet (`call_sym`/`put_sym` are `None`) and the service is running
- This ensures index tickers like `$SPX`, `$RUT`, and `$NDX` gain their option symbols after `register()` wipes `_ticker_flows` or when the IndexSpotPoller delivers a fresh spot
- For index symbols, actual spot prices are stored in the **display symbol** (`$SPX`, etc.) rather than the ETF proxy (`SPY`, `IWM`, `QQQ`) that is used for WebSocket streaming
- The flow tracking uses the **original display symbol** as the key, with ETF-proxy remapping (`SPX→SPY`, `RUT→IWM`, `NDX→QQQ`) handled internally for the WebSocket subscription only
- Index spots are fetched via REST with the plain OAuth quote symbol (`$SPX`, `$RUT`, …) — the `$SPX:X` suffix is rejected by Schwab as `errors.invalidSymbols`. The ATM Call/Put prices shown for index tickers are the REST marks on the index-option root (refreshed every ~2 s — see **Call/Put Price refresh**), stored separately in `call_mark`/`put_mark`; the streamed ETF-proxy option quotes only drive buy/sell direction inference and never overwrite the index marks.
- **Proxy-strike subscriptions**: index tickers stream their ETF proxy's
  options, so their OCC call/put symbols must be struck at the *proxy* price.
  `set_ticker_proxy_spot` stores the ETF-proxy last price in `proxy_spot`
  (leaving the index-level `spot` untouched), and `_do_subscribe` builds the
  symbols at `calculate_atm_strike(proxy_spot)` (SPY ~570) instead of the
  index level (~5700). An index ticker is **skipped** until a proxy spot
  arrives, and `set_ticker_proxy_spot` re-subscribes when the proxy ATM
  strike moves so the ticker always streams real proxy contracts.
- **Index-option root for quotes**: `get_ticker_quote_symbols` uses
  `_index_option_root` to map index expirations to the correct OCC root —
  standard (third-Friday) expirations use `SPX`/`RUT`/`NDX`, every other
  listed expiration uses the weekly/EOM roots `SPXW`/`RUTW`/`NDXP` — so the
  Call/Put Price marks are index-level, not the ETF proxy's.

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

### Call/Put Price refresh (REST option marks)

The Call Price / Put Price columns previously moved only when the throttled
analytics recompute (30–180 s) pushed fresh marks, so they looked frozen.
They are now refreshed every ~2 s from `ensure_atm_streaming` (gated by
`s["_opt_price_fetch_ts"]`, matching the grid cadence):

1. `atm_svc.get_ticker_quote_symbols(display)` returns the four OCC symbols
   that drive the columns for a ticker: `call_wall` (CALL at the put-wall
   strike), `put_wall` (PUT at the call-wall strike), and `call_atm` /
   `put_atm` (the ATM strikes).
2. All tickers' symbols are fetched in a **single batched** `fetch_quotes`
   call (`client.py`) — one REST request per ~2 s, not one per column.
3. The marks are pushed back via `atm_svc.set_ticker_wall_prices` /
   `set_ticker_option_prices`.

For index symbols (SPX/RUT/NDX) the quote symbols use their **own
index-option root** via `_index_option_root` — standard (third-Friday)
expirations map to `SPX`/`RUT`/`NDX`, every other listed expiration to
`SPXW`/`RUTW`/`NDXP` — so the Call/Put Price columns show index-level marks
rather than the ETF proxy's strikes.

### Wall (support/resistance) refresh cadence

The Support / Resistance columns come from the put/call walls computed by
`compute_analytics` on a REST option chain. They are **GEX-derived** (not raw
OI): `_find_put_wall` picks the strike below spot with the highest `put_gex`,
and `_find_call_wall` picks the strike above spot with the highest `call_gex`
(dealer gamma exposure = OI × gamma). Walls are refreshed with a
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

The `maybe_fire_wall_zone_alerts` function sends **wall-reversal trend alerts**,
**wall-broke alerts**, **wall-change diff alerts** (Call/Put Wall / Gamma Flip /
Dealer flip changed, plus wall price-crossings), and **strategy recommendation
blocks** to Telegram. Front expiration VRP is no longer passed as a header
parameter to `notify_alerts`; it is excluded from the Telegram header but
remains in the underlying strategy recommendation text.

When the trend reversal fires inside a wall zone, it is emitted as a dedicated
wall-reversal alert:

    💥 {Resistance/Support} wall {BULLISH/BEARISH} REVERSAL after absorbing <n> contracts @ $<strike>

The alert text is the literal `trend_reversal` (`bullish` / `bearish`). Telegram maps the direction to a trade suggestion:

| Trend alert body | Direction | Suggestion |
| --- | --- | --- |
| `🟢 BULLISH` | buy  | `BUY CALL $<wall_mark>` |
| `🔴 BEARISH` | sell | `BUY PUT $<wall_mark>` |

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
| net_flow(60 s) > 0 (up) / < 0 (down) | delta-weighted executed flow matches direction |
| absorption ≥ 20 vol/$1 (`_ABSORPTION_MIN_VOL`) | heavy flow is being absorbed |

Reversals (`bullish` / `bearish`) clear with score ≥ 2. Weak / flat-ish
trends that don't corroborate stay quiet. Thresholds are the tunable
`_ALERT_MIN_CONVICTION_REVERSAL` constant in `flow.py`.

**Wall-reversal alerts.** When a trend reversal fires **inside** a wall zone
(`wall_zone is not None` — spot trading within a wall buffer of a
resistance/support level), `maybe_fire_wall_zone_alerts` sends a dedicated
wall-reversal alert to Telegram:

    💥 {Resistance/Support} wall {BULLISH/BEARISH} REVERSAL after absorbing <n> contracts @ $<strike>

This replaces the previous behavior where trend alerts were *filtered*
(suppressed) when spot was **away** from a wall. Now:

- High-conviction reversals **at walls** fire a wall-reversal alert (spot
  inside the wall buffer).
- Low-value reversals **in open space** (spot away from walls) are suppressed
  — the conviction gate and the wall-zone check ensure only meaningful L2
  signals at key levels surface.

All diff-based alerts (wall zone, gamma flip, wall change, wall-broke)
except wall-broke alerts, wall-reversal trend alerts, and strategy
recommendation blocks are sent to Telegram. "Wall changed" alerts are
passed through unchanged. Front expiration VRP is removed from the
Telegram header (not passed to `notify_alerts`) but remains in strategy
recommendation text.

**Compact signal line.** When a wall-reversal alert fires, `notify_alerts(..., trend_alert=...)`
renders a single dense signal line instead of repeating the flow-metric
header rows, folding in the corroborating metrics:

    🟢 BULLISH - BUY CALL $8.25 · Net +1,200 · Abs 9,500

(`Net` = 60 s net flow, `Abs` = absorption.) IV rank / RV / GEX / wall zone and
`Wall absorbed` remain separate header lines for context. VRP, Book Imbalance,
Flow Speed, Flow Acceleration, and Liquidity Flow are no longer included in
Telegram alert headers; VRP values remain within strategy recommendation text
but are not surfaced as header lines. Wall-reversal trend alerts, wall-broke
alerts, and strategy recommendations are sent to Telegram.

`flat` and strong `UP` / `DOWN` are **not** surfaced as Telegram alerts —
only wall-reversal trend alerts (`bullish` / `bearish` REVERSAL) can fire a
send. Wall-broke alerts and strategy recommendations are also sent to
Telegram. Wall-reversal alerts require the walls to be stable for 2
consecutive refreshes and respect the 600 s per-ticker cooldown.

### Order absorption (Telegram + grid)

**Price-impact absorption** (`AtmOptionVolumeService.get_ticker_absorption`,
surfaced as the grid **Absorption** column and the Telegram
`Absorption: <n> vol/$1` header line — folded into the compact trend signal
line as `Abs`) measures how much aggressive ATM option flow the book consumed
without moving the price. **Level 1** data: ATM option trade volume (from
`LEVEL1_OPTIONS`) over the spot displacement (from the `LEVEL1_EQUITIES`
stream):

    absorption = Δ(cumulative ATM volume over 60 s) / max(|Δspot| over 60 s, 0.05)

High absorption (≥ 1000 vol/$1) means heavy flow is being soaked up at a level
(price pinned — support/resistance holding); low absorption (< 300) means the
price is drifting on thin flow.

**Executed flow** (`AtmOptionVolumeService.get_ticker_executed_flow`, the grid
**Net Flow** column and the Telegram
`Net Flow (60s): <n>` header line — folded into the compact trend signal
line as `Net`) is the **delta-weighted** aggressor split, sourced from
**Level 1** ATM option trade prints (`LEVEL1_OPTIONS`) weighted by the
**front-month ATM option delta** from the REST chain: every trade print is
classified buyer- vs seller-initiated (`_infer_dir` against the bid/ask mid),
then folded by option side so `buy_vol` counts **buying calls and selling
puts** (bullish pressure) while `sell_vol` counts selling calls and buying
puts (bearish pressure) — equivalently:

     buy ↔ call_buy  + put_sell
    sell ↔ call_sell + put_buy

`buy_vol` / `sell_vol` are session-cumulative **raw contract** buckets (pure
aggressor-direction counts incremented directly by size in
`_process_trade_ticker`, not prices × contracts). They are computed and
returned by `get_ticker_executed_flow`, but the grid itself exposes no
Buy/Sell columns — only **Net Flow** (the delta-weighted `net_60`) is
displayed, so the raw buckets are not rendered independently. The
right-hand sides simply mirror the same identity in the per-1-second bar
counters (`call_buy_vol` / `call_sell_vol` / `put_buy_vol` / `put_sell_vol`)
rather than being a literal assignment into the ticker totals. Separately,
each trade is weighted by its option delta — call Δ > 0,
put Δ < 0 — into `delta_buy` (bullish pressure) and `delta_sell` (bearish
pressure), so the Net Flow column reports **net_delta** rather than raw
contracts:

    delta_buy   = Σ size × aggressor × Δ_opt   (positive contributions only)
    delta_sell  = Σ |size × aggressor × Δ_opt| (negative contributions only)
    net_delta   = delta_buy − delta_sell

The deltas come from the front-month ATM strike of the REST chain
(`set_ticker_atm_deltas`, pushed on every wall refresh); before the first
refresh populates them, a static **call +0.5 / put −0.5** fallback is used so
the column is live even at cold start. On every trade a `(timestamp,
delta_buy − delta_sell)` sample is appended to a per-symbol `exec_history`
pruned to the trailing 60 s. The grid's **Net Flow** cell is the change over
that window:

    net_60 = exec_history[-1][1] − exec_history[0][1]   (Δ net_delta over trailing 60 s)

The per-contract raw sides (`call_buy_vol` / `call_sell_vol` /
`put_buy_vol` / `put_sell_vol`) are still kept in the 1-second OHLCV bars, so
both views remain computable. Only the ATM call and ATM put at the per-ticker
front expiration are subscribed, so Net Flow is strictly ATM flow.

**Multi-flow routing.** Each trade print is folded into **every** tracked flow
whose stream symbol matches the option's root (`_option_handler` prefix-matches
the OCC symbol against `stream_symbol`, padded or unpadded). Because index
tickers stream their ETF proxy's options, one SPY tick updates both the `$SPX`
flow and the `SPY` flow when both are tracked (same for `$RUT`+`IWM` and
`$NDX`+`QQQ`); the `_is_idx` guard keeps index entries' spots at their index
level while the ETF entry's spot follows `UNDERLYING_PRICE`.

**Wall absorption** in `flow.maybe_fire_wall_zone_alerts` snapshots the
cumulative ATM volume when spot enters a wall zone and reports how many
contracts were absorbed while spot stayed inside (Telegram
`Wall absorbed: <n> contracts`). This is reported as *context* only — it does
**not** drive the broken-wall trigger.

**Wall broke** is triggered by a **directional pierce**, not by leaving the
zone: Resistance breaks when spot settles **above** the call wall, Support
breaks when spot settles **below** the put wall. Each must persist past the
wall by the near-wall buffer margin for `_WALL_BREAK_CONFIRM` consecutive
samples (filters jitter at the level), and the ticker must have been observed
holding the wall first (never after a session starts already past the wall),
so a 💥 `Resistance/Support wall BROKE after absorbing <n> contracts` alert plus a
`BUY CALL`/`BUY PUT` trade line only fires on a real, direction-correct break.

### Book pressure (L2 OPTIONS book)

The **Book Imbalance**, **Flow Speed**, and **Flow Acceleration** columns are
all derived from the same per-symbol **Level 2** OPTIONS-book data by
`StreamingService`, fed by the `OPTIONS_BOOK` messages on the shared WebSocket
(the Level 2 depth feed, distinct from the Level 1 trade/quotes stream).
Because `OPTIONS_BOOK` subscriptions require full OCC option-contract symbols
(not underlyings), `StreamingService` subscribes each tracked ticker's **ATM
call and put contracts** (`set_book_contracts`) and aggregates their resting
volume per underlying.  The contract set comes from `flow._tracked_book_contracts`,
which pulls each ticker's subscribed ATM call/put OCC symbols from the ATM
service — for index tickers those are built at the **ETF-proxy** ATM strike
(SPY ~570) by `_do_subscribe`, so the Level 2 book is aggregated for the
proxy's options, keyed by the underlying stream symbol (`SPY`). Since the key
is the stream symbol, one OPTIONS_BOOK feed serves both the `$SPX` and `SPY`
flows when both are tracked.  On every book update the resting volume on each
BIDS / ASKS level (`TOTAL_VOLUME`) is summed across those contracts
(`_book_volume_for_symbol`) and a `(timestamp, ratio)` sample is appended to
a per-symbol **60 s rolling history** (`_update_book_imbalance`).

**Book Imbalance** (`_book_imbalance_for_symbol`) — the current bid/ask
pressure ratio over the subscribed ATM contracts:

    bid_vol          = Σ BIDS.TOTAL_VOLUME
    ask_vol          = Σ ASKS.TOTAL_VOLUME
    book_imbalance   = (bid_vol − ask_vol) / (bid_vol + ask_vol)   ∈ [−1, 1]

Positive = more resting bid volume (bullish pressure); negative = more resting
ask volume (bearish). Returns `None` when there is no book yet or total ≤ 0.

**Flow Speed** — the first difference of the imbalance ratio over the trailing
60 s window (`_flow_speed_and_accel`):

    flow_speed = history[-1][1] − history[0][1]

the last ratio minus the first ratio in the window — the window's net change
in book pressure (dimensionless, in ratio units).

**Flow Acceleration** — the second difference of the ratio, i.e. the change in
book-pressure momentum. The window is split at its **time** midpoint (`mid_ts`,
halfway between the first and last sample timestamps) so the older and recent
halves cover equal wall-clock spans even when book updates arrive unevenly;
`mid` is the first sample at/after `mid_ts`. The older half's change is
subtracted from the recent half's change:

    mid_ts            = history[0][0] + (history[-1][0] − history[0][0]) / 2
    previous_flow     = history[mid-1][1] − history[0][1]
    recent_flow       = history[-1][1]    − history[mid][1]
    flow_acceleration = recent_flow − previous_flow

Cold-start guard: with fewer than 2 history samples both `flow_speed` and
`flow_acceleration` are 0 (and the trend is `flat`). Agreement between
`flow_speed` / `flow_acceleration` signs and `|book_imbalance| > 0.3`
drives the strong **UP** / **DOWN** trend labels (see the Trend section).

### Liquidity flow (L2 book)

**Liquidity flow** (`StreamingService._liquidity_flow`, exposed via
`trend_data` as the grid **Liquidity Flow** column) measures whether resting liquidity at the best **Level 2**
OPTIONS-book levels is being added or drained over the trailing 60 s:

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
- The Call/Put Price columns are kept live by a second REST call
  (`get_ticker_quote_symbols` + `fetch_quotes`) gated by
  `s["_opt_price_fetch_ts"]` (~2 s), in addition to the ~10 s spot pre-fetch.
  Both are lightweight single-user calls; rate limiting is not expected.
- Index symbols (SPX/RUT/NDX) subscribe their Level-1 / OPTIONS_BOOK
  contracts at the **ETF-proxy** ATM strike (SPY ~570) and quote their
  Call/Put Price marks on the **index-option root** (`SPX`/`SPXW` etc.), so
  Book Imbalance and the price columns work for indices even though the index
  level (~5700) has no proxy contracts.
- The REST pre-fetch (`fetch_quotes`) runs every ~10 s (gated by
  `s["_spot_fetch_ts"]`), even though the fragment ticks every 2 s. This is
  a lightweight call but does hit the Schwab API; rate limiting is not
  expected for a single user session. Between fetches, cached spots from
  `s.spot_cache` (fed by the equity stream and prior REST calls) are used.
