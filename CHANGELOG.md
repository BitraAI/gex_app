# Changelog

## [Unreleased]

### Added
- **Pin Score** column in Order Flow grid - simpler metric than absorption showing volume absorbed per $1 net displacement
- **Wall Strength** metrics in analytics - GEX at wall / total GEX ratio

### Changed
- **Liquidity Flow** threshold now dynamic: `max(25, 3% of avg book depth)` instead of static 25 contracts
- **Absorption** now uses delta-weighted volume (same as Flow Ratio) instead of raw volume
- **Absorption** denominator smoothed: `vol_60 / (spot_path + 0.05)` for smoother transitions
- **GEX Formula**: Fixed to use `(spot/100)^2` instead of `spot^2` for correct scaling
- **Dealer Position**: Now includes strength indicator (Strong/Moderate/Weak)
- Updated conviction score liquidity flow threshold from 2% to 3%

### Improved
- **Call/Put Walls**: 
  - Require minimum GEX threshold (1M or 0.5% of total)
  - Use weighted average of top 3 walls by GEX
  - Check absolute GEX magnitude, not just positive
- **Gamma Flip**: Now uses linear interpolation between strikes for precise flip point
- **Expected Pin**: Now uses GEX-based strength weighting
- Liquidity Flow now shows bid/ask flows separately
- Side-aware warnings: Underlines red when ask liquidity drains on bullish trend (bearish signal)
- Improved color coding for Liquidity Flow magnitude levels

### Removed
- Flow Ratio (Raw) and Flow Vol (raw) columns from Order Flow grid
- `get_ticker_flow_metrics_raw_60s()` method from option streaming service
