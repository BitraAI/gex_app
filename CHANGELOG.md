# Changelog

## [Unreleased]

### Added
- **Pin Score** column in Order Flow grid - simpler metric than absorption showing volume absorbed per $1 net displacement
- **Wall Strength** metrics in analytics - GEX at wall / total GEX ratio
- **VEX and CEX Wall Detection** - Individual VEX and CEX-specific wall functions (`_find_call_wall_vex()`, `_find_put_wall_vex()`, `_find_call_wall_cex()`, `_find_put_wall_cex()`)
- **Wall Strength Metrics** - VEX and CEX-based wall strength (`call_wall_strength_vex`, `put_wall_strength_vex`, `call_wall_strength_cex`, `put_wall_strength_cex`)
- **Combined GEX+VEX+CEX Walls** - Wall detection now uses combined GEX+VEX+CEX metrics for more robust identification

### Changed
- **Liquidity Flow** threshold now dynamic: `max(25, 3% of avg book depth)` instead of static 25 contracts
- **Absorption** now uses delta-weighted volume (same as Flow Ratio) instead of raw volume
- **Absorption** denominator smoothed: `vol_60 / (spot_path + 0.05)` for smoother transitions
- **GEX Formula**: Fixed to use `(spot/100)^2` instead of `spot^2` for correct scaling
- **VEX Formula**: Fixed to use `(spot/100)^2` for spot normalization (consistent with GEX)
- **CEX Formula**: Fixed sign convention - CALL positive, PUT negative (matches GEX/VEX)
- **Dealer Position**: Now includes strength indicator (Strong/Moderate/Weak)
- Updated conviction score liquidity flow threshold from 2% to 3%

### Improved
- **Call/Put Walls**: 
  - Require minimum combined GEX+VEX+CEX threshold (1M or 0.5% of total)
  - Use weighted average of top 3 walls by combined magnitude
  - Check absolute combined magnitude, not just positive
  - VEX and CEX-specific walls provide additional IV sensitivity and time decay analysis
- **Gamma Flip**: Now uses linear interpolation between strikes for precise flip point
- **Expected Pin**: Now uses GEX-based strength weighting
- Liquidity Flow now shows bid/ask flows separately
- Side-aware warnings: Underlines red when ask liquidity drains on bullish trend (bearish signal)
- Improved color coding for Liquidity Flow magnitude levels

### Removed
- Flow Ratio (Raw) and Flow Vol (raw) columns from Order Flow grid (per user preference for delta-weighted metrics only)
- `get_ticker_flow_metrics_raw_60s()` raw flow column display from Order Flow grid (metrics still available via `get_ticker_flow_metrics_raw_60s()` method)

### Fixed
- **Critical**: `compute_totals` in `calculations.py:72-74` - now handles empty data and missing fields with safe defaults
- **Critical**: `calculate_cex` market close time in `calculations.py:58` - now accounts for after-hours/early closes via `is_market_open()`
- **Critical**: Wall threshold in `analytics.py:100-102` - uses safe `get()` accessors for GEX fields
- **High**: Unknown direction handling in `option_streaming_service.py:1789-1816` - improved comments for even split logic
- **High**: Strategy alert diagnostics in `flow.py:1088-1118` - enhanced logging for SSVI/iv_skew fallback
- **High**: Liquidity flow robustness in `streaming_service.py:195-241` - handles empty depth and invalid data gracefully

### Cleaned
- Removed duplicate `_compute_for_symbol` from `flow.py` (now uses `chain_parser.compute_analytics_for_symbol`)
- Removed unused imports in `flow.py`, `app_extras.py`, `app_data.py`, `app_signals.py`
- Reduced `iv_skew_history` cache from 900 to 300 entries in `app_candlesticks.py` and `app_data.py`
- Centralized chain parsing via `chain_parser.fetch_and_parse_chain` in `flow.py`
- Removed duplicate ETF fallback logic in `flow.py` and `app_data.py`
- Removed ETF fallback from `flow._compute_walls_for_symbol` (now uses `chain_parser`)
- Removed `fetch_option_chain` and `compute_analytics` imports from `flow.py` (now uses `chain_parser` versions)
- Removed `get_next_earnings_date` import from `app_extras.py` and `app_signals.py` (imported locally where needed)
- Removed `fetch_candles_smart`, `fetch_price_history_daily`, `save_candle_cache` imports from `app_data.py` (imported locally where needed)
- Added `INDEX_QUOTE_MAP` import back to `flow.py` (required for streaming initialization)
- Added `is_market_open()` wrapper to `_utils.py` (fixes after-hours market close time handling)
- Removed global `get_next_earnings_date` import from `app_extras.py` and `app_signals.py`, added local imports where needed
- Removed global imports for `fetch_candles_smart`, `fetch_price_history_daily`, `save_candle_cache` from `app_data.py`, added local imports where needed
- Fixed ETF fallback logic in `app_data.py` to use `etf_analytics` when fallback chain is used
