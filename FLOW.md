# ATM Order Flow

Live bullish / bearish order-flow dashboard for the ATM (at-the-money) front
expiration of every ticker in `~/.local/share/gex_app/ticker_history.json`.

## What it shows

A Streamlit dataframe (`flow_page.render_atm_order_flow_grid`) with one row per
tracked ticker:

| Column | Meaning |
| --- | --- |
| **Ticker** | Display symbol (index symbols like `SPX` kept as-is; streamed via ETF proxy `SPY`/`IWM`/`QQQ`). |
| **Bullish Flow** | Cumulative option volume classified as bullish. |
| **Bearish Flow** | Cumulative option volume classified as bearish. |
| **Net Flow** | `Bullish − Bearish`. Green when positive, red when negative, grey when zero. |
| **Status** | `Live` / `Closed` / `Cached` / `No Data` (see below). |

Refresh cadence: the grid is wrapped in `@st.fragment(run_every=2)`, so it
updates every 2 seconds.

### Status legend

| Status | Meaning | Colour |
| --- | --- | --- |
| **Live** | Ticker is subscribed and US regular trading hours are open (09:30–16:00 ET, Mon–Fri, excluding New Year's / Independence / Christmas). | Green |
| **Closed** | Ticker is subscribed but the market is currently closed (after hours, weekend, or holiday). Flow values are frozen from the last session. | Grey |
| **Cached** | Ticker is known but not currently subscribed/streaming. | Blue |
| **No Data** | No flow received yet for this ticker. | Grey |

Market-hours detection lives in `flow_page.is_market_open()`.

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
| `flow_page.py` | Shared rendering: `render_atm_order_flow_grid`, `update_flow_cache`, `ensure_session_defaults`, `is_market_open`. |
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

1. **REST pre-fetch**: `ensure_atm_streaming` calls `fetch_quotes` (from
   `client.py`) for all tickers every 2 seconds. The `fetch_quotes` function
   returns `client.get_quotes()` parsed as JSON — note that the Schwab
   `AsyncClient.get_quotes()` returns a raw `Response` object, so `.json()`
   must be called on it.
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

### Schwab SDK field mapping

The Schwab streaming SDK's `_Handler.label_message()` renames certain fields.
For LEVELONE_OPTIONS messages, the option symbol is in the **`key`** field,
not `SYMBOL`. The handler uses `c.get("key", "") or c.get("SYMBOL", "")` to
handle both formats.

### Reconnection

When the equity WebSocket disconnects and reconnects (handled by
`StreamingService._run`), the ATM service is notified via
`StreamingService.on_reconnect()` callbacks. The ATM service re-subscribes
its option chain after the equity feed is back online.

## Notes / limitations

- Flow totals are **cumulative** for the session, not a rolling window.
- Lee-Ready uses the option bid/ask mid as the trade-direction threshold. If
  bid/ask has not yet arrived for an option, the trade is split evenly between
  bullish and bearish.
- The service uses a single shared front expiration for all tickers in the
  subscription (the primary symbol's front expiration).
- `ensure_session_defaults` reuses `app._SESSION_DEFAULTS` so the page and main
  app never drift apart.
- The REST pre-fetch (`fetch_quotes`) runs every fragment tick (2 s). This is
  a lightweight call but does hit the Schwab API. Rate limiting is not expected
  for a single user session.
