# ATM Order Flow

Live bullish / bearish order-flow dashboard for the ATM (at-the-money) front
expiration of every ticker in `~/.local/share/gex_app/ticker_history.json`.

## What it shows

A Streamlit dataframe (`flow.render_atm_order_flow_grid`) with one row per
    tracked ticker:

| Column | Meaning |
| --- | --- |
| **Ticker** | Display symbol (index symbols like `SPX` kept as-is; streamed via ETF proxy `SPY`/`IWM`/`QQQ`). |
| **Spot** | Latest spot price (REST pre-fetch or live equity stream). |
| **ATM Strike** | Nearest strike to spot, computed by `calculate_atm_strike` (strike spacing by price band). |
| **Trend** | Direction of net flow momentum over the last 60 seconds (see below). Enhanced indicators: **↑↑** (strong bullish with OPTIONS_BOOK), **↓↓** (strong bearish with OPTIONS_BOOK), **→→** (building bullish momentum), **←←** (building bearish momentum), **↑** (normal bullish), **↓** (normal bearish), **→** (balanced/flat). |
| **Call Price** | Mid price of the ATM call option. |
| **Put Price** | Mid price of the ATM put option. |
| **Bullish Flow** | Cumulative option volume classified as bullish. |
| **Bearish Flow** | Cumulative option volume classified as bearish. |
| **Net Flow** | `Bullish − Bearish`. Green when positive, red when negative, grey when zero. |
| **Status** | `Live` / `Closed` / `Cached` / `No Data` (see below). Amber (`Closed`) doubles as the "market open but no ticks yet" warning colour. |

Refresh cadence: the grid is wrapped in `@st.fragment(run_every=2)` (the
module-level `_flow_grid` in `app.py`), so it updates every 2 seconds. The
parent `render_tabs_frag` runs every 10 s and renders the legend / CSS
once per outer tick via `flow.render_flow_legend_and_style()` so the
static HTML is not re-injected on every 2-second data tick (avoids DOM
flicker). `_flow_grid` is defined at module scope (not nested inside
`render_flow_frag`) so Streamlit does not destroy and recreate it every
10 s.

### Status legend

| Status | Meaning | Colour |
| --- | --- | --- |
| **Live** | Ticker is subscribed and US regular trading hours are open (09:30–16:00 ET, Mon–Fri, excluding New Year's / Independence / Christmas). | Green |
| **Closed** | Ticker is subscribed but the market is currently closed (after hours, weekend, or holiday). Flow values are frozen from the last session. Also briefly visible while the market is open but no ticks have arrived yet (watchdog grace window). | Amber |
| **Cached** | Ticker is known but not currently subscribed/streaming. | Blue |
| **No Data** | No flow received yet for this ticker. | Grey |

Market-hours detection lives in `flow.is_market_open()`.

### Trend

Trend reflects the **direction of net-flow momentum** over the last 60 seconds,
not the absolute level. It is computed in `AtmOptionVolumeService._snapshot_flow`
(option_streaming_service.py:803-863) and exposed via `get_ticker_trend`.

How it works:

1. Every ~10 trades (line 883 in option_streaming_service.py), a snapshot of
   `(timestamp, net_flow)` is appended to a per-ticker `flow_history` list.
2. Snapshots older than 60 seconds are pruned (line 811-816 in option_streaming_service.py).
3. If fewer than 2 snapshots exist the trend is **flat** (line 820-826 in option_streaming_service.py). The `len(history) < 2` guard also resets `flow_speed` to 0.
4. The history is split in half. The first points from each segment are extracted:
   - `older_first = history[0][1]` (first point from entire history)
   - `newer_first = history[-segment_size][1]` (first point from newer half)
   - The difference `diff = newer_first - older_first` determines the trend
   - `diff > 0` → **up** (green arrow)
   - `diff < 0` → **down** (red arrow)
   - `diff == 0` → **flat** (grey arrow)
5. **Enhanced trend detection via book imbalance and trend reversal**:
   - Compares `previous_trend` with `current_trend`
   - If trend changed from **up → down**, sets `trend_reversal = "bearish"`
   - If trend changed from **down → up**, sets `trend_reversal = "bullish"`
   - Otherwise no reversal (`trend_reversal = None`)
   - If `book_imbalance > 0.3` (strong bullish pressure), trend becomes **up**
   - If `book_imbalance < -0.3` (strong bearish pressure), trend becomes **down**
   - Strong book imbalance overrides the flow-diff trend determination

**Enhanced trend indicators** in the Trend column (flow.py:218-238):

| Condition | Display |
|-----------|---------|
| **up** trend (bullish) | `↑` |
| **down** trend (bearish) | `↓` |
| **flat** trend (balanced) | `→` |
| **bullish reversal** | `↑↑` (strong bullish with OPTIONS_BOOK) |
| **bearish reversal** | `↓↓` (strong bearish with OPTIONS_BOOK) |
| **building bullish momentum** | `→→` (momentum building) |
| **building bearish momentum** | `←←` (momentum building) |

The enhanced trend indicators incorporate OPTIONS_BOOK liquidity pressure:
- **Strong bullish**: `↑↑` when book imbalance > 0.3
- **Strong bearish**: `↓↓` when book imbalance < -0.3
- **Neutral trends**: `↑`, `↓`, `→` for standard trend cases


## Data pipeline

```
Schwab WebSocket (LEVELONE_OPTIONS)
        │
        ▼
AtmOptionVolumeService (option_streaming_service.py)
  • subscribes to front-expiration ATM call/put for EVERY ticker in
    ticker_history.json, in a single Level-One Options subscription
  • maintains per-ticker flow in _ticker_flows[display_symbol]
        │
        ▼  Lee-Ready direction inference (_infer_dir: price vs bid/ask mid)
   CALL buy  -> Bullish     CALL sell -> Bearish
   PUT  sell -> Bullish     PUT  buy  -> Bearish
   (unknown spread -> split evenly)
        │
        ▼  cumulative per-ticker totals (thread-safe, self._lock)
   flow[symbol] = { bullish, bearish }
        │
        ▼
flow_cache (st.session_state)  — updated by update_flow_cache()
        │
        ▼
ATM Order Flow dataframe (Streamlit, styled like Options Data table)
```

Key points:

- **ATM strike** is computed per ticker from its live spot via
  `calculate_atm_strike` (strike spacing by price band).
- **Front expiration** is auto-selected (nearest expiration in the loaded
  chain) so the service always registers — `ensure_atm_streaming` in `app.py`
  falls back to `sorted(expirations)[0]` when no expiration is manually chosen.
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
| `flow.py` | Shared rendering: `render_atm_order_flow_grid`, `render_flow_legend_and_style`, `update_flow_cache`, `ensure_session_defaults`, `is_market_open`. |
| `option_streaming_service.py` | `AtmOptionVolumeService` — WebSocket handling, Lee-Ready classification, per-ticker flow. |
| `app.py` | Main app; owns streaming (`ensure_atm_streaming` via ticker Refresh), `render_flow_frag`, Order Flow tab. |
| `client.py` | `fetch_quotes` — REST spot pre-fetch for all tickers. |

## Architecture: streaming & spot feeding

### Shared StreamClient

Both the equity stream (`StreamingService`) and ATM option flow
(`AtmOptionVolumeService`) share a single `schwab.streaming.StreamClient`
and therefore a single WebSocket connection. The equity service owns the
connection and runs the `handle_message()` loop; the ATM service registers
its handler via `add_level_one_option_handler` and subscribes via
`level_one_option_subs`.

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

### Registration & subscription order

`ensure_atm_streaming` runs **inside** the `@st.fragment(run_every=2)`
body (not outside it), because code outside a fragment does not re-run on
fragment timer ticks. The flow on each cycle:

1. Pre-fetch spots via `fetch_quotes` → `spot_cache`
2. If `_need_register` is True (first run, symbol change, or expiration
   change): call `register()` which clears `_ticker_flows`, re-initializes
   all tickers with spot=0, and registers the handler. **Critically,
   `register()` does NOT call `_do_subscribe`** — the caller does.
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
- Lee-Ready uses the option bid/ask mid as the trade-direction threshold. If
  bid/ask has not yet arrived for an option, the trade is split evenly between
  bullish and bearish.
- The service uses a single shared front expiration for all tickers in the
  subscription (the primary symbol's front expiration).
- `ensure_session_defaults` reuses `app._SESSION_DEFAULTS` so the page and main
  app never drift apart.
- The REST pre-fetch (`fetch_quotes`) runs every ~10 s (gated by
  `s["_spot_fetch_ts"]`), even though the fragment ticks every 2 s. This is
  a lightweight call but does hit the Schwab API; rate limiting is not
  expected for a single user session. Between fetches, cached spots from
  `s.spot_cache` (fed by the equity stream and prior REST calls) are used.
