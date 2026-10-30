"""Candlesticks tab extracted verbatim from app.py.

``TIMEFRAMES`` (UI timeframe selectbox schema) and the 2 s
``render_candlesticks_frag`` fragment.  Render order inside the fragment is
load-bearing (title row -> controls -> constant chart host -> payload ->
caption); do not reorder.
"""
import time

import pandas as pd
import streamlit as st

from scripts import client as client_mod
from scripts._constants import (STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP, INDEX_SYMBOLS,
                                FLOW_RATIO_GREEN_THRESHOLD, FLOW_RATIO_RED_THRESHOLD)
from scripts._utils import floor_dataframe_timestamps, compute_current_bucket
from scripts.client import load_candle_cache
from scripts.chart_component import render_chart, render_chart_host
from scripts.flow import ensure_atm_streaming, run_async
from scripts.option_streaming_service import (_normalize_display_symbol,
                                              _get_stream_symbol)
from scripts.app_data import _candles_need_refresh, refresh_candles


TIMEFRAMES = {
    "1m": "1min", "2m": "2min", "5m": "5min", "15m": "15min",
    "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W", "1M": "1ME",
}


@st.fragment(run_every=2)
def render_candlesticks_frag():
    s = st.session_state
    if not s.get("client"):
        st.info("Initialize authentication to load data")
        return

    # Title row: tab title on the left, live ATM flow chips (rolling
    # 60 s) right-aligned on the same line. Rendered at the TOP of the
    # fragment, far from the constant chart host (whose DOM persists at
    # its originally mounted position), so the row holds its place
    # identically on refresh and tab switches. Net Flow Δ is the
    # DELTA-WEIGHTED executed net (`get_ticker_executed_net60` —
    # trailing-60 s change in delta_buy − delta_sell, each print
    # weighted by ITS OWN contract's delta; same source as the Telegram
    # header and the conviction gate). Flow Ratio is the delta-weighted
    # bullish share (`get_ticker_flow_metrics_60s` — trailing-60 s
    # change in the same delta_buy / delta_sell counters). None until
    # the option stream produces flow in the window (em dash). Colors
    # follow the grid /
    # Telegram thresholds: Net Flow green > 0, red < 0, orange at 0;
    # Flow Ratio green above FLOW_RATIO_GREEN_THRESHOLD (0.8), red
    # below FLOW_RATIO_RED_THRESHOLD (0.2), amber between.
    _title_svc = st.session_state.get("atm_option_service")
    _tnf, _tfr = (None, None)
    if _title_svc is not None:
        try:
            _tfr = _title_svc.get_ticker_flow_metrics_60s(
                _normalize_display_symbol(s.get("symbol", "SPY")))[1]
            _tnf = _title_svc.get_ticker_executed_net60(
                _normalize_display_symbol(s.get("symbol", "SPY")))[2]
        except Exception:
            _tnf, _tfr = (None, None)
    if _tnf is not None:
        _tnf_txt = f"{_tnf:+,.0f}"
        _tnf_col = "#00cc96" if _tnf > 0 else "#ef5350" if _tnf < 0 else "#ff9800"
    else:
        _tnf_txt, _tnf_col = "—", "#ff9800"
    if _tfr is not None:
        _tfr_txt = f"{_tfr:.2f}"
        _tfr_col = ("#00cc96" if _tfr > FLOW_RATIO_GREEN_THRESHOLD
                    else "#ef5350" if _tfr < FLOW_RATIO_RED_THRESHOLD else "#ff9800")
    else:
        _tfr_txt, _tfr_col = "—", "#ff9800"
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'gap:12px;margin:0 0 10px 0;">'
        '<h2 style="margin:0;font-size:1.5rem;">Candlesticks</h2>'
        '<div style="display:flex;align-items:center;gap:18px;">'
        f'<span style="color:{_tfr_col};font-weight:bold;">Flow Ratio: {_tfr_txt}</span>'
        f'<span style="color:{_tnf_col};font-weight:bold;">Net Flow Δ (60s): {_tnf_txt}</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Main content container for controls and chart
    candles_container = st.container()
    with candles_container:
        # Only show historical data, no live streaming controls
        symbol = s.get("symbol", "SPY")
        
        # Create row layout for controls - timeframe and indicators on same row
        row1, row2 = st.columns([1, 3])
        
        with row1:
            timeframe = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=0, label_visibility="collapsed", width=100)
        
        with row2:
            indicator_options = ["SMA 20", "SMA 50", "EMA 20", "EMA 50", "EMA 200", "Volume Profile", "VWAP", "Half Trend", "Volume", "Andean Squeeze"]
            selected_indicators = st.multiselect("Indicators", indicator_options, default=["Andean Squeeze", "EMA 50", "EMA 200", "Half Trend", "VWAP"], label_visibility="collapsed")
        
        # Refresh the cache from the API when the existing on-disk bars are
        # stale relative to the user's chosen timeframe. The chart fragment
        # renders every 1s, so we need a gate that doesn't hammer the TDA REST
        # endpoint on every render. We use the parquet's own last-bar
        # timestamp as the freshness indicator: for intraday charts, refresh
        # when the last bar is older than ~2 timeframe buckets (so a 1m
        # chart refreshes when the cache is ~2 min old — never more than a
        # couple bars behind); for D/W/M, refresh when the last bar is more
        # than 10 minutes old.
        try:
            _probe = client_mod.load_last_cached_timestamp(symbol, timeframe)
        except Exception:
            _probe = pd.DataFrame()
        forced_refresh = False
        if not _probe.empty:
            last_bar_dt = pd.Timestamp(int(_probe["datetime"].iloc[-1]), unit="ms", tz="UTC")
            now_dt = pd.Timestamp.now(tz="UTC")
            tf_minutes = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
            if tf_minutes is None:
                stale_threshold_secs = 600  # 10 minutes for D/W/M
            else:
                # 2 TF-buckets, with a 60-second floor so we don't slam the
                # API more than once per minute for very small TFs.
                stale_threshold_secs = max(60, tf_minutes * 60 * 2)
            age_secs = (now_dt - last_bar_dt).total_seconds()
            forced_refresh = age_secs > stale_threshold_secs

        # If the sidebar Refresh button was just clicked for the current
        # symbol, force a fresh candle pull regardless of cache staleness.
        _force_refresh_symbol = s.get("_force_candle_refresh")
        if _force_refresh_symbol == symbol:
            s["_force_candle_refresh"] = None
            forced_refresh = True

        # Also short-circuit if the client isn't ready — refresh can't help.
        client_ok = s.get("client") is not None
        if client_ok and (forced_refresh or _candles_need_refresh(symbol, timeframe)):
            try:
                refresh_candles(symbol, timeframe)
            except Exception:
                # Refresh is best-effort: fall through to whatever cache load
                # returns below so the chart still renders with stale data.
                pass

        historical_df = load_candle_cache(symbol, timeframe)

        # --- Build chart DataFrame ---
        chart_df = pd.DataFrame()
        chart_label = ""

        if not historical_df.empty:
            recent = historical_df.tail(500).dropna(subset=["open", "high", "low", "close"])
            chart_df = recent[["datetime", "open", "high", "low", "close", "volume"]].copy()
            # Remove duplicate datetime entries from historical data
            chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
            chart_label = f"Historical {timeframe}"
        else:
            historical_df = load_candle_cache(symbol, "1d")
            if not historical_df.empty:
                recent = historical_df.tail(500).dropna(subset=["open", "high", "low", "close"])
                chart_df = recent[["datetime", "open", "high", "low", "close", "volume"]].copy()
                # Remove duplicate datetime entries from historical data
                chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
                chart_label = f"No {timeframe} cache — daily"
            else:
                st.info("Load data to see historical data")
                return

        if chart_df.empty:
            st.info("No data available")
            return

        # --- Start streaming services (equity + ATM option) ---
        stream_symbol = STREAM_SYMBOL_MAP.get(symbol.upper().lstrip("$"), symbol)
        ensure_atm_streaming(stream_symbol)

        # Periodically refresh spots for all tickers (every 2s)
        atm_svc = st.session_state.get("atm_option_service")
        _first_exp = st.session_state.get("selected_expiration")
        _first_exp = _first_exp[0] if isinstance(_first_exp, list) and _first_exp else (_first_exp if isinstance(_first_exp, str) else None)
        if atm_svc and atm_svc.is_running and _first_exp:
            _now = time.time()
            _last_spot_refresh = s.get("_last_spot_refresh", 0)
            if _now - _last_spot_refresh >= 2:
                s._last_spot_refresh = _now
                _all_tickers = s.get("ticker_history", [])
                _stream_symbols = [_get_stream_symbol(t) for t in _all_tickers]
                try:
                    from scripts.client import fetch_quotes
                    quote_resp = run_async(fetch_quotes(s.client, _stream_symbols))
                    for disp_sym, stream_sym in zip(_all_tickers, _stream_symbols):
                        _disp_upper = _normalize_display_symbol(disp_sym)
                        qd = quote_resp.get(stream_sym, {}) or {}
                        quote = qd.get("quote", {}) or qd.get(stream_sym, {})
                        last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                        if last is not None and float(last) > 0:
                            spot = float(last)
                            if _disp_upper in INDEX_QUOTE_MAP:
                                # The ETF-proxy price (SPY) drives the index
                                # ticker's OCC subscription strikes, not its
                                # displayed index-level spot.
                                atm_svc.set_ticker_proxy_spot(_disp_upper, spot)
                                continue
                            s.spot_cache[_disp_upper] = spot
                            # Also update ATM service
                            atm_svc.set_ticker_spot(_disp_upper, spot)

                    # Fetch actual index quotes for SPX, RUT, NDX
                    _idx_fetch = []
                    _idx_disp_map = {}
                    for _t in _all_tickers:
                        _t_upper = _normalize_display_symbol(_t)
                        if _t_upper in INDEX_QUOTE_MAP:
                            _iq = INDEX_QUOTE_MAP[_t_upper]
                            _idx_fetch.append(_iq)
                            _idx_disp_map[_iq] = _t_upper
                    if _idx_fetch:
                        try:
                            idx_resp = run_async(fetch_quotes(s.client, _idx_fetch))
                            for _iq, _disp_upper in _idx_disp_map.items():
                                qd = idx_resp.get(_iq, {}) or {}
                                quote = qd.get("quote", {}) or qd.get(_iq, {})
                                last = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
                                if last is not None and float(last) > 0:
                                    spot = float(last)
                                    s.spot_cache[_disp_upper] = spot
                                    atm_svc.set_ticker_spot(_disp_upper, spot)
                        except Exception as e:
                            print(f"[chart] index quote fetch failed: {e}")
                except Exception:
                    pass

        # Feed spot from equity stream to ATM option service
        # Normalize chart_df["datetime"] to int64 for merging
        chart_df["datetime"] = chart_df["datetime"].astype("int64")

        svc = s.get("streaming_service")

        # Merge streaming OHLC + buy_vol/sell_vol into chart df when available.
        # Streaming aggregates ticks into 1-second buckets keyed on ms timestamps.
        # We floor each streaming bucket to the selected timeframe's boundary, so
        # ticks accumulate inside the user's chosen bar (e.g., 5m chart: all ticks
        # between 10:30 and 10:35 belong to the 10:30 bar). Only the *last* bar
        # of the chart gets live-updated on every 1-second fragment tick — every
        # historical bar before it keeps its original OHLC unchanged.
        # Only merge streaming data when the streamed symbol matches the chart
        # symbol exactly (no proxy remapping). Index symbols (SPX, RUT, NDX)
        # are streamed via their ETF equivalents (SPY, IWM, QQQ), but those
        # have completely different price scales — merging them would produce
        # nonsensical candlesticks, so skip the merge for proxy streams.
        _sym_norm_chart = _normalize_display_symbol(symbol)
        _merge_streaming = svc and svc.is_running and svc.symbol == stream_symbol and _sym_norm_chart == stream_symbol
        if _merge_streaming:
            try:
                stream_df = svc.get_candles()
                if not stream_df.empty and not chart_df.empty:
                    stream_df = stream_df.reset_index()
                    stream_df["datetime"] = stream_df["datetime"].astype("int64")
                    # Floor streaming 1s bars to the user's timeframe boundary so
                    # live ticks update the current historical bar.
                    tf_minutes = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                    stream_df = floor_dataframe_timestamps(stream_df, "datetime", timeframe, tf_minutes)
                    # Aggregate streaming bars per (timeframe-aligned) timestamp
                    stream_agg = stream_df.groupby("datetime").agg({
                        "open": "first", "high": "max", "low": "min", "close": "last",
                        "volume": "sum",
                        "buy_vol": "sum", "sell_vol": "sum",
                    }).reset_index()

                    chart_df = chart_df.drop_duplicates(subset=["datetime"], keep="last")
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    # Rightmost historical timestamp — every historical bar at or
                    # before this point stays untouched; only the live/last bar of
                    # the chart is updated with streaming ticks each fragment tick.
                    last_hist_time = int(chart_df["datetime"].iloc[-1])
                    # Current (rightmost) timeframe bucket aligned to the user's
                    # TF. Use the SAME flooring logic applied to live ticks above
                    # so the live-last-bucket timestamp matches what
                    # stream_agg["datetime"] uses (US/Eastern day boundary for
                    # daily/weekly/monthly; intraday-aligned bucket otherwise).
                    current_bucket = compute_current_bucket(timeframe, tf_minutes)
                    # The "live last bar" is whichever bucket is furthest right:
                    # the current timeframe bucket, or the most recent historical
                    # bar (when the cache is ahead of the wall clock for any
                    # reason). Live ticks floored to this bucket merge into the
                    # existing bar; newer buckets append as brand-new bars.
                    live_last_time = max(last_hist_time, current_bucket)

                    # Split live aggregates into cohorts:
                    #   (a) buckets <= last_hist_time AND != live_last_time —
                    #       these match existing historical bars. Per spec ("before
                    #       last bar maintain historical values") we DISCARD their
                    #       live aggregates and keep the historical OHLC intact.
                    #   (b) buckets strictly newer than last_hist_time but earlier
                    #       than live_last_time — closed streaming bars that the
                    #       historical cache hasn't picked up yet. There's no
                    #       historical row to merge with, so they're added as new
                    #       standalone bars between the historical bars and the
                    #       live/last bar.
                    #   (c) the bucket at live_last_time — gets merged with any
                    #       historical row at this timestamp to form the updated
                    #       last bar.
                    #   (d) buckets strictly newer than live_last_time — appended
                    #       as brand-new bars past the right edge.
                    last_bucket_agg = stream_agg[stream_agg["datetime"] == live_last_time]
                    new_bars_agg = stream_agg[stream_agg["datetime"] > live_last_time]
                    closed_between = stream_agg[
                        (stream_agg["datetime"] > last_hist_time) &
                        (stream_agg["datetime"] < live_last_time)
                    ]

                    # Capture the historical row at live_last_time BEFORE removing
                    # it, so we can merge live OHLC into its snapshot.
                    hist_last_row = chart_df[chart_df["datetime"] == live_last_time]
                    hist_last_snapshot = (
                        hist_last_row.iloc[0].to_dict() if not hist_last_row.empty else None
                    )
                    # Remove only the matching historical row (if any) at the live
                    # last-bucket timestamp; every earlier historical bar stays.
                    chart_df = chart_df[chart_df["datetime"] != live_last_time]

                    # Build the updated last bar:
                    #   - If a historical row exists at live_last_time AND we have
                    #     live ticks: merge them (preserves historical open, takes
                    #     max(high)/min(low), live close replaces close, volume
                    #     sums).
                    #   - If only live ticks exist (e.g., current bucket is newer
                    #     than any historical bar): the live aggregate alone is the
                    #     new last bar.
                    #   - If only a historical row exists (no live ticks landing in
                    #     this bucket yet): keep the historical row as-is.
                    last_bar = pd.DataFrame()
                    if not last_bucket_agg.empty:
                        live_row = last_bucket_agg.iloc[0]
                        if hist_last_snapshot is not None:
                            merged_open = hist_last_snapshot["open"]
                            merged_high = max(hist_last_snapshot["high"], live_row["high"])
                            merged_low = min(hist_last_snapshot["low"], live_row["low"])
                            merged_close = live_row["close"]
                            hv = hist_last_snapshot.get("volume", 0)
                            lv = live_row.get("volume", 0)
                            hv = 0 if (hv is None or hv != hv) else hv
                            lv = 0 if (lv is None or lv != lv) else lv
                            merged_volume = float(hv) + float(lv)
                        else:
                            merged_open = live_row["open"]
                            merged_high = live_row["high"]
                            merged_low = live_row["low"]
                            merged_close = live_row["close"]
                            lv = live_row.get("volume", 0)
                            merged_volume = float(0 if (lv is None or lv != lv) else lv)
                        last_bar = pd.DataFrame([{
                            "datetime": live_last_time,
                            "open": float(merged_open),
                            "high": float(merged_high),
                            "low": float(merged_low),
                            "close": float(merged_close),
                            "volume": float(merged_volume),
                            "buy_vol": int(live_row.get("buy_vol", 0) or 0),
                            "sell_vol": int(live_row.get("sell_vol", 0) or 0),
                        }])
                    elif hist_last_snapshot is not None:
                        # No live ticks in this bucket yet — fall back to the
                        # untouched historical last bar.
                        last_bar = pd.DataFrame([hist_last_snapshot])

                    # Assemble final chart_df in chronological order: historical
                    # bars (unchanged) + closed streaming bars that landed between
                    # the cache and the live bucket (new bars formed during this
                    # streaming session but not yet refreshed into cache) + the
                    # merged/updated last bar + any newer streaming bars that
                    # arrived past the current bucket boundary.
                    parts = [chart_df]
                    if not closed_between.empty:
                        parts.append(closed_between)
                    if not last_bar.empty:
                        parts.append(last_bar)
                    if not new_bars_agg.empty:
                        parts.append(new_bars_agg)
                    chart_df = pd.concat(parts, ignore_index=True)
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    # Scale trailing cap to the timeframe so today + recent days
                    # remain visible at intraday granularities.
                    max_bars = 1500 if tf_minutes else 500
                    if len(chart_df) > max_bars:
                        chart_df = chart_df.tail(max_bars).reset_index(drop=True)
            except Exception:
                pass

        # ---- Index symbols (SPX, RUT, NDX): build a live bar from the real
        # index spot poll (s.spot_cache, updated every ~2s by the $SPX etc.
        # fetch above) and merge it into the chart so $SPX/$RUT/$NDX
        # candlesticks update like equities.  Index symbols cannot be streamed
        # via the equity WebSocket (Schwab only supports LEVELONE_EQUITIES for
        # real equities, not indices), so we fall back to REST polling ---- #
        _sym_norm_idx = _normalize_display_symbol(symbol)
        if _sym_norm_idx in INDEX_SYMBOLS and not chart_df.empty:
            try:
                _atm_svc = s.get("atm_option_service")
                _idx_spot = _atm_svc.get_ticker_spot(_sym_norm_idx) if _atm_svc else None
                if _idx_spot is None:
                    _idx_spot = s.spot_cache.get(_sym_norm_idx)
                if _idx_spot is not None and float(_idx_spot) > 0:
                    _idx_spot = float(_idx_spot)
                    _tf_min_idx = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                    _live_bucket_idx = compute_current_bucket(timeframe, _tf_min_idx)
                    chart_df = chart_df.sort_values("datetime").reset_index(drop=True)
                    _last_hist_time_idx = int(chart_df["datetime"].iloc[-1])
                    _live_last_time_idx = max(_last_hist_time_idx, _live_bucket_idx)
                    _hist_at_live_idx = chart_df[chart_df["datetime"] == _live_last_time_idx]
                    _hist_snapshot_idx = _hist_at_live_idx.iloc[0].to_dict() if not _hist_at_live_idx.empty else None
                    chart_df = chart_df[chart_df["datetime"] != _live_last_time_idx]
                    if _hist_snapshot_idx is not None:
                        _o_idx = _hist_snapshot_idx["open"]
                        _h_idx = max(_hist_snapshot_idx["high"], _idx_spot)
                        _l_idx = min(_hist_snapshot_idx["low"], _idx_spot)
                        _vol_idx = _hist_snapshot_idx.get("volume", 0) or 0
                    else:
                        _o_idx = _h_idx = _l_idx = _idx_spot
                        _vol_idx = 0
                    _live_bar_idx = pd.DataFrame([{
                        "datetime": _live_last_time_idx,
                        "open": float(_o_idx),
                        "high": float(_h_idx),
                        "low": float(_l_idx),
                        "close": float(_idx_spot),
                        "volume": float(_vol_idx),
                    }])
                    chart_df = pd.concat([chart_df, _live_bar_idx], ignore_index=True).sort_values("datetime").reset_index(drop=True)
                    _max_bars_idx = 1500 if _tf_min_idx else 500
                    if len(chart_df) > _max_bars_idx:
                        chart_df = chart_df.tail(_max_bars_idx).reset_index(drop=True)
            except Exception:
                pass

        # Merge ATM option volume into chart df when available
        # atm_df index is int64 milliseconds — same unit as chart_df["datetime"].
        # Warnings are shown near the chart (see Option_Volume_Profile block below);
        # this block only attaches ATM volume columns to chart_df.
        if "Option_Volume_Profile" in selected_indicators:
            atm_svc = st.session_state.get("atm_option_service")
            if atm_svc and atm_svc.is_running:
                try:
                    atm_df = atm_svc.get_candles()
                    if not atm_df.empty:
                        atm_df = atm_df.reset_index()
                        atm_df["datetime"] = atm_df["datetime"].astype("int64")
                        # Floor ATM 1-second bucket timestamps to the chart's
                        # timeframe boundary so they match chart_df["datetime"].
                        _tf_min_atm = (client_mod.TIMEFRAMES.get(timeframe) or {}).get("minutes")
                        atm_df = floor_dataframe_timestamps(atm_df, "datetime", timeframe, _tf_min_atm)
                        atm_agg = atm_df.groupby("datetime").agg({
                            "call_buy_vol": "sum", "call_sell_vol": "sum",
                            "put_buy_vol": "sum", "put_sell_vol": "sum",
                            "total_buy_vol": "sum", "total_sell_vol": "sum",
                        }).reset_index()
                        chart_df = chart_df.merge(atm_agg, on="datetime", how="left")
                        for col in ["call_buy_vol", "call_sell_vol", "put_buy_vol", "put_sell_vol", "total_buy_vol", "total_sell_vol"]:
                            if col in chart_df.columns:
                                chart_df[col] = chart_df[col].fillna(0).astype(int)
                except Exception:
                    pass

        # Persist in session state. chart_df["datetime"] stays as int64 ms because
        # chart_component.render_chart converts it to UNIX-seconds time keys for
        # lightweight-charts (with the proper EST offset).
        s.candlestick_data = chart_df
        s.candlestick_label = chart_label

        # --- Render lightweight-charts streaming candlestick ---
        df = s.candlestick_data

        # Build the candle list for chart_component.render_chart. Keep datetime as
        # int64 ms so the streaming 1-second bars are uniquely keyed on time.
        _extra_cols = [c for c in ["buy_vol", "sell_vol",
                                   "call_buy_vol", "call_sell_vol",
                                   "put_buy_vol", "put_sell_vol",
                                   "total_buy_vol", "total_sell_vol"]
                       if c in df.columns]
        base_cols = ["datetime", "open", "high", "low", "close"]
        if "volume" in df.columns:
            base_cols.append("volume")
        candles_payload = df[base_cols + _extra_cols].to_dict("records")
        for c in candles_payload:
            c["datetime"] = int(c["datetime"])
            c["open"] = float(c["open"])
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["close"] = float(c["close"])
            if "volume" in c:
                v = c["volume"]
                c["volume"] = float(v) if pd.notna(v) and v == v else 0.0
            for ac in _extra_cols:
                if ac in c:
                    v = c[ac]
                    try:
                        c[ac] = int(v)
                    except (TypeError, ValueError, OverflowError):
                        c.pop(ac, None)
                else:
                    c.pop(ac, None)

        last_close = float(df["close"].iloc[-1]) if not df.empty else None

        # Call/Put wall horizontal lines (price levels from analytics)
        _analytics = s.get("analytics") or {}
        _cw = _analytics.get("call_wall")
        _pw = _analytics.get("put_wall")

        # Websocket streaming status — overlaid on the candlesticks chart.
        # The equity StreamClient feeds the live candles (and, when
        # Option_Volume_Profile is selected, the option-trade aggregation), so its
        # status is shown regardless of which indicators are selected.  We
        # resolve a single status string + level here and hand it to
        # render_chart() via the `status` parameter; an absolute-positioned
        # badge inside the chart container draws it on top of the canvas.
        _eq_svc = st.session_state.get("streaming_service")
        _atm_svc = st.session_state.get("atm_option_service")
        _status = None
        if _eq_svc is None:
            _status = {"text": "Stream not initialized", "level": "warning"}
        elif not _eq_svc.is_running:
            _status = {"text": f"Starting {stream_symbol} stream...", "level": "info"}
        elif _eq_svc.is_connected and _eq_svc.has_data:
            _msg = f"Receiving {stream_symbol} ticks · {_eq_svc.ticks_received}"
            if "Option_Volume_Profile" in selected_indicators and _atm_svc is not None:
                if _atm_svc.is_running and _atm_svc.has_data:
                    _n = _atm_svc.ticks_received
                    _msg += f" · { _n } option tick{'s' if _n != 1 else ''}"
                elif _atm_svc.is_running and not _atm_svc.has_data:
                    _msg += " · waiting for option trades..."
                elif not _atm_svc.is_running:
                    _msg += " · option flow not subscribed"
            _status = {"text": _msg, "level": "success"}
        elif _eq_svc.is_connected and not _eq_svc.has_data:
            _status = {"text": f"Connected · waiting for {stream_symbol} trades...", "level": "info"}
        elif not _eq_svc.is_connected:
            _err = getattr(_eq_svc, "last_error", None)
            _msg = "WebSocket disconnected"
            if _err:
                _msg += f": {_err}"
            _status = {"text": _msg, "level": "warning"}

        # Persistent chart host (constant element): keeps the chart DOM alive
        # even on ticks without candle data, so it never "disappears".
        render_chart_host()

        # Chart payload (data) is rendered inside candles_container
        # This updates the chart data every tick without recreating the chart DOM
        if candles_payload:
            iv_skew_indicator_enabled = any(ind in selected_indicators for ind in ["IV Skew (25Δ)"])
            _iv_skew_hist = s.get("iv_skew_history") or []
            if iv_skew_indicator_enabled and _analytics.get("iv_skew") is not None:
                # Second-resolution timestamp (kept in ms). Storing ms would
                # collapse to duplicate seconds client-side, shrinking the
                # series every other tick and forcing full setData repaints.
                _now_ms = (int(pd.Timestamp.now(tz="UTC").value // 1_000_000)) * 1000
                if not _iv_skew_hist or _iv_skew_hist[-1].get("datetime") != _now_ms:
                    _iv_skew_hist = list(_iv_skew_hist)
                    _iv_skew_hist.append({
                        "datetime": _now_ms,
                        "iv_skew": _analytics["iv_skew"],
                        "put_iv_25d": _analytics.get("put_iv_25d"),
                        "call_iv_25d": _analytics.get("call_iv_25d"),
                        "atm_iv": _analytics.get("atm_iv"),
                    })
            s["iv_skew_history"] = _iv_skew_hist[-900:] if len(_iv_skew_hist) > 900 else _iv_skew_hist
            render_chart(
                candles_payload,
                indicators=selected_indicators,
                call_wall=_cw,
                put_wall=_pw,
                last_close=last_close,
                status=_status,
                symbol=symbol,
                iv_skew_history=_iv_skew_hist if iv_skew_indicator_enabled else [],
            )
        st.caption(f"{s.candlestick_label} bars ({len(s.candlestick_data)})")

