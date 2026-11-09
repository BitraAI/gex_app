# Changelog

## [Unreleased]

### Added
- **Pin Score** column in Order Flow grid - simpler metric than absorption showing volume absorbed per $1 net displacement

### Changed
- **Liquidity Flow** threshold now dynamic: `max(25, 3% of avg book depth)` instead of static 25 contracts
- **Absorption** now uses delta-weighted volume (same as Flow Ratio) instead of raw volume
- **Absorption** denominator smoothed: `vol_60 / (spot_path + 0.05)` for smoother transitions
- Updated conviction score liquidity flow threshold from 2% to 3%

### Improved
- Liquidity Flow now shows bid/ask flows separately
- Side-aware warnings: Underlines red when ask liquidity drains on bullish trend (bearish signal)
- Improved color coding for Liquidity Flow magnitude levels

### Removed
- Flow Ratio (Raw) and Flow Vol (raw) columns from Order Flow grid
- `get_ticker_flow_metrics_raw_60s()` method from option streaming service
