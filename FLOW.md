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

Two entry points, both sharing `st.session_state` (so streaming started on one
is visible on the other):

1. **Order Flow tab** on the main page
   (`app.py` → `render_tabs_frag`, tab7 → `_render_flow_link`). The link is
   rendered as an `st.iframe` with an inline `target="_blank"` anchor, so it
   opens **`http://localhost:8501/atm_order_flow` in a new browser tab**
   (Streamlit strips `target="_blank"` from `st.markdown`, hence the iframe).

2. **Dedicated page** `pages/atm_order_flow.py` at
   `http://localhost:8501/atm_order_flow`. It does **not** start streaming
   itself — streaming is owned by the main app (the ticker Refresh button calls
   `fetch_data` → `render_candlesticks` → `ensure_atm_streaming`, which starts
   the WebSocket feed). On open the page:
   - calls `ensure_session_defaults()` (initialises `spot_cache`,
     `flow_cache`, `ticker_history`, etc., since pages run as a separate script;
     `ticker_history` is loaded from `ticker_history.json` so the grid always
     has its row list),
   - if the ATM option service is not yet running, shows a hint to open the main
     page and click **Refresh**,
   - renders the grid via `render_atm_order_flow_grid`, reading the shared
     `flow_cache` that the main app's stream populates.

You must start streaming from the main GammaEx page (Refresh a ticker) first;
the ATM Order Flow page then displays that live data.

## Files

| File | Role |
| --- | --- |
| `pages/atm_order_flow.py` | Dedicated page; reads shared session state and renders the grid. |
| `flow_page.py` | Shared rendering: `render_atm_order_flow_grid`, `update_flow_cache`, `ensure_session_defaults`, `is_market_open`. |
| `option_streaming_service.py` | `AtmOptionVolumeService` — WebSocket handling, Lee-Ready classification, per-ticker flow. |
| `app.py` | Main app; owns streaming (`ensure_atm_streaming` via ticker Refresh), `_render_flow_link`, Order Flow tab. |

## Notes / limitations

- Flow totals are **cumulative** for the session, not a rolling window.
- Lee-Ready uses the option bid/ask mid as the trade-direction threshold. If
  bid/ask has not yet arrived for an option, the trade is split evenly between
  bullish and bearish.
- The service uses a single shared front expiration for all tickers in the
  subscription (the primary symbol's front expiration).
- `ensure_session_defaults` reuses `app._SESSION_DEFAULTS` so the page and main
  app never drift apart.
