# Candlesticks Chart

Live OHLCV candlestick chart for the current symbol, with optional technical
indicators and a real-time WebSocket stream merged into the latest bar.

## Access

The chart lives in the **Candlesticks** tab of the main app (`app.py` →
`render_candlesticks`), which is one of the tabs in the main tab row (alongside
Market Structure, Positioning, Volatility, Heatmaps, Trade Signals, and the
Order Flow tab). It is shown after a ticker is loaded (Refresh on the main
page).

Refreshing a ticker here is also what **starts the WebSocket streaming** for
the whole app — equity `StreamingService` and the ATM option
`AtmOptionVolumeService` are both kicked off inside `render_candlesticks` via
`ensure_atm_streaming`.

## Controls

- **Timeframe** (`st.selectbox`): `1m, 2m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M`.
- **Indicators** (`st.multiselect`, default `Andean Osc`, `EMA 50 Squeeze`,
  `Trend`): `SMA 20`, `SMA 50`, `EMA 20`, `EMA 50 Squeeze`, `EMA 200`,
  `Volume Profile`, `Anchored VWAP`, `Trend`, `Volume`, `Andean Osc`.

The chart itself is rendered by `chart_component.render_chart` (Lightweight
Charts HTML/JS). See `README.md` for the interactive pan/zoom and Y-range
persistence behavior across streaming re-renders.

## Data pipeline

```
Schwab REST (candle history)            Schwab WebSocket (StreamingService)
        │                                      │
        ▼                                      ▼
fetch_candles_smart / refresh_candles   LEVELONE_EQUITY (trades + quotes)
        │                              + NASDAQ/NYSE Level 2 books
        ▼                                      │
load_candle_cache (parquet)                    ▼
 historical_df  ──tail(500)──► chart_df   StreamingService._aggregate_tick
 (datetime, OHLCV)                         1-second OHLCV bars w/ buy_vol/sell_vol
        │                                      │
        │                                      ▼
        │                              streaming_service.get_candles()
        │                                      │  (floored to TF bucket)
        │                                      ▼
        └────────── merge ──────────► chart_df (last bar live-updated)
                                              │
                                              ▼
                                   chart_component.render_chart(...)
```

### Historical candles

- Loaded from an on-disk parquet cache via `load_candle_cache(symbol,
  timeframe)`; refreshed through `refresh_candles` only when stale (intraday:
  when the last cached bar is older than ~2 timeframe buckets, floored at 60s;
  daily/weekly/monthly: older than 10 minutes). This keeps the 1-second chart
  fragment from hammering the REST API.
- Chart uses the last 500 bars (`tail(500)`), de-duplicated by `datetime`.
- If the chosen timeframe has no cache, it falls back to the `1d` cache so the
  chart still renders.

### Live streaming merge

- `ensure_atm_streaming(stream_symbol)` starts the equity WebSocket and
  registers the ATM option service. Index symbols are remapped to their ETF
  proxy (`SPX→SPY`, `RUT→IWM`, `NDX→QQQ`) for the equity subscription.
- The equity `StreamingService` aggregates ticks into 1-second OHLCV bars
  (with `buy_vol`/`sell_vol` split by trade direction). `get_candles()` returns
  those bars.
- Each 1-second streaming bucket is **floored to the selected timeframe
  boundary** (e.g. on a 5m chart, all ticks between 10:30 and 10:35 land in the
  10:30 bar). The streaming bars are grouped/summed to that boundary and merged
  into `chart_df`.
- **Only the rightmost (current) bar is live-updated** on every fragment tick.
  All historical bars keep their original OHLC. Daily/weekly/monthly charts
  floor live ticks to the America/New_York day boundary so today's bar keeps
  updating.
- Streaming is merged **only when the streamed symbol matches the chart symbol
  exactly** (no proxy remapping), to avoid mixing the different price scales of
  an index and its ETF proxy.

### Spot / ATM option service

- Every 10s, `render_candlesticks` refreshes spots for all `ticker_history`
  tickers via `fetch_quotes` and pushes them to `atm_svc.update_ticker_spot`,
  which keeps the ATM option subscription (Lee-Ready flow) aligned to the live
  underlying.
- The same `StreamClient` connection is shared between the equity stream and
  the ATM option `AtmOptionVolumeService` (no second WebSocket).

## Files

| File | Role |
| --- | --- |
| `app.py` | `render_candlesticks`, `ensure_atm_streaming`, `TIMEFRAMES`, candle merge logic. |
| `chart_component.py` | `render_chart` — Lightweight Charts HTML/JS component + indicators. |
| `streaming_service.py` | `StreamingService` — equity WebSocket, 1s OHLCV aggregation, buy/sell split. |
| `option_streaming_service.py` | `AtmOptionVolumeService` — ATM option flow (shares the StreamClient). |
| `client.py` | `fetch_candles_smart`, `load_candle_cache`, `refresh_candles`, `TIMEFRAMES`, `fetch_quotes`. |

## Notes / limitations

- The chart tab renders inside a 1-second fragment, so live ticks update the
  current bar without a full rerun.
- Streaming requires the ticker to have been Refreshed on the main page; if the
  service isn't running, the chart falls back to the historical cache only.
- `buy_vol`/`sell_vol` from the equity stream are merged alongside OHLCV; the
  ATM option flow (separate pipeline) is surfaced on the **Order Flow** tab /
  `/atm_order_flow` page.
