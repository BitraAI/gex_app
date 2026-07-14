# GammaEx — Gamma Exposure Analytics Platform

A professional-grade options analytics dashboard that calculates and visualizes **Gamma Exposure (GEX)** for any stock using real Schwab market data.

Built with Streamlit, Plotly, NumPy, and the Schwab API.

## Features

- **Real-time Option Chain Data** — Fetches live options data via the Schwab API
- **Candlestick Charts** — Interactive OHLCV charts with SMA/EMA overlays, Trend, Volume (buy/sell pressure with streaming delta), ATM_Option_Flow (real-time ATM option trade flow via LEVELONE_OPTIONS streaming — computes `(call_buy + put_sell) - (call_sell + put_buy)` per 1s bar with Bullish/Bearish Flow label over last 20 bars), Volume Profile (VPVR — client-side per-bar volume binned at each visible price level with buy/sell split, POC highlighted, recomputes on every pan/zoom), Anchored VWAP (session-reset line, anchored at each 09:30 ET boundary), Andean Oscillator, and EMA 50 Squeeze indicators
- **Candlestick Chart Interactions** — TradingView-style dual-axis pan and zoom:
  - **Drag in the chart body** pans BOTH the time (X) and price (Y) axes together vertically and horizontally (custom body-drag handler pans Y; LWC handles X natively).
  - **Drag the price-scale labels** (right edge) or **drag the time-scale labels** (bottom) zooms each respective axis natively.
  - **Mouse wheel** zooms the X-axis (bar spacing) anywhere over the chart; a crosshair tracks the cursor.
  - The Y range is **persistent across the 1-second streaming fragment re-renders**: user-set Y-zoom (via body drag, axis-label drag, or autoscaleInfoProvider pin) is saved losslessly on gesture end and restored on each re-render, so streaming ticks do not snap the chart back to the auto-fit range and the Y range doesn't drift over time. X-axis range persistence works the same way.
  - Each pane (main candlesticks / Volume / ATM / Andean Osc) pans its own Y range independently when dragged in its own vertical band.
- **3 Calculations** — GEX (Gamma), VEX (Vanna), CEX (Charm) Exposure
- **Arbitrage-Free SSVI Volatility Surface** — Fits a parametric (Raw SVI per-tenor → SSVI surface) smoothed IV surface for cleaner skew / IV estimates. Used for the SSVI model overlay on IV-by-Strike and ATM IV-by-Expiration charts, and `ssvi_skew` analytics.
- **10 Interactive Charts:**
  - GEX by Strike (bar chart with Call/Put Wall, Gamma Flip overlays)
  - GEX by Expiration (stacked bar by expiration cycle, expandable via slider)
  - 3D Gamma Surface (strike × expiration × GEX, expandable via slider)
  - Dealer Curve (cumulative GEX/VEX/CEX across strikes, with Spot/Call Wall/Put Wall/Gamma Flip markers in GEX mode, VEX Magnet/Repellent markers in VEX mode)
  - OI/Vol by Strike (grouped bars, toggle OI or Volume)
   - IV by Strike (bar chart, toggle IV Rank/VRP/VRP Ratio, with Spot/RV/SSVI model overlay lines — SSVI fitted surface drawn in IV Rank and IV modes, expandable via slider)
   - IV by Expiration (bar chart, toggle ATM IV/VRP/VRP Ratio, with RV/SSVI model overlay lines, expandable via slider)
  - Heatmaps + Vol Surface (strike × expiration grid, toggle OI/Volume/VRP/VRP Ratio, expandable via slider, x-axis locked)
  - Strategy Signals (scored options with automated trade recommendations)
- **Analytics Panel:**
  - Call Wall (highest call GEX above spot), Put Wall (highest put GEX below spot)
  - Gamma Flip (cumulative net GEX zero-crossing with 1% threshold), Max Pain
  - Max +GEX, Max -GEX
  - Dealer Position (Long/Short Gamma)
   - IV Skew (25-delta, both market and SSVI-smoothed), Expected Move, Next Earnings Date, VEX Magnet, VEX Repellent
  - IV Rank — Where current ATM implied volatility sits in the trailing 1-year range of 20-day realized volatilities. >70 = high vol regime (sell premium), <30 = low vol regime (buy premium)
- **Strategy Signals:**
  - Per-option scoring (VRP + Dealer Gamma + Wall Proximity + IV Rank)
  - Market Bias (Bullish/Bearish/Neutral from gamma flip, net GEX, IV skew, wall distance, IV Rank)
  - Strategy recommendations: Sell/Buy Premium, Call/Put Credit Spreads, Iron Condor, Butterfly, Broken Wing Butterfly, Straddle, Strangle, Calendar Spread
  - All strategies use same-expiration legs where applicable
  - Iron Condor uses ATM range boundaries for short legs with protection legs from full data
  - Sell Premium includes Calendar Spread, Butterfly, Broken Wing Butterfly, Jade Lizard
  - Buy Premium includes Calendar Spread
- **Automatic Data Filtering:**
  - **20 strikes above/below ATM** inclusive
  - **Nearest 4 active expirations** (excludes expirations with zero OI/volume)
  - Charts have sliders to control expiration count and are unaffected by sidebar expiration selection
- **Options Data** — Sortable grid filtered by sidebar expiration selection, with highlighted cells and CSV export (columns: Strike, Call/Put GEX, Net GEX, Call/Put OI, Call/Put Vol, Call/Put Gamma, Call/Put IV, VRP, VRP Ratio, Call/Put Price, Rel IV, Expirations):
  - **Gray row** — ATM strike (closest to spot)
  - **Red OI cells** — Max Pain strike OI columns
  - **Orange Call GEX cell** — Call Wall strike Call GEX
  - **Green Put GEX cell** — Put Wall strike Put GEX
  - **Rel IV** — Strike IV divided by ATM IV, highlighting elevated IV
  - **RV** — 20-day annualized realized volatility of the underlying (population std of log returns, × √(252 × n/(n−1)))
  - **VRP** — Volatility Risk Premium = IV - RV
  - **VRP Ratio** — Volatility Risk Premium Ratio = IV / RV
- **Light Theme** — Clean light-themed UI
- **Telegram Alerts** — Pushes an alert to a Telegram chat when key GEX events fire: gamma flip / call wall / put wall changes, dealer gamma flips (Long↔Short), and spot price crossings of the walls. Two delivery paths:
  - **In-app:** fires inline when the Streamlit dashboard refreshes its visible symbol (uses session state as the per-symbol baseline).
  - **Automatic multi-ticker:** `telegram_alerts.py` polls every symbol in the saved ticker history list once per run and sends alerts on detected transitions — schedule it on cron for hands-off monitoring during market hours.
  All alerts are Markdown-formatted with the symbol header and current spot. Reads `BOT_TOKEN` / `CHAT_ID` from the `[telegram]` section of `config.toml` (overridable via `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` env vars). Set `enabled = false` to mute alerts without removing secrets. Alerts are delivered silently by default so they don't buzz the recipient's device on every refresh.

## Setup

### Prerequisites

- Python 3.12+
- A Schwab API developer application (client ID + secret)
- Schwab authentication token

### Installation

```bash
$ python3 -m venv gex_env
$ source gex_env/bin/activate
(gex_env) $ python -m pip install -U pip
(gex_env) $ python -m pip install -U uv
(gex_env) $ git clone https://github.com/BitraAI/gex_app.git
(gex_env) $ cd gex_app
(gex_env) $ uv pip install -r requirements.txt
```

### Create a Schwab Developer Portal Account

Register at https://developer.schwab.com/products/trader-api--individual

The developer account is distinct from your brokerage login and is linked later during OAuth authorization.

1. Click **Create App**
2. Enter:
   - **Application Name** (e.g., `gex_app`)
   - **Description**
3. Select the API products you need, such as:
   - Market Data Production
   - Accounts and Trading Production
4. **Order Limit:** 120
5. Enter a **Callback URL(s):** `https://127.0.0.1:8182/`
6. Await approval for your API application

Only after it reaches **Ready for Use** can you obtain OAuth tokens and call the APIs.

### Configuration

Create `config.toml` in the project directory:

```toml
[schwab]
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
callback_url = "https://127.0.0.1:8182/"
token_file = "~/.local/share/gex_app/schwab_token.json"
base_url = "https://api.schwabapi.com"
max_token_age_days = 7
```

Environment variables `SCHWAB_CLIENT_ID` and `SCHWAB_CLIENT_SECRET` override `config.toml`.

#### Telegram Alerts (optional)

To receive alerts when GEX events fire (gamma flip / wall changes, dealer gamma flips, price crossings), add a `[telegram]` section to `config.toml`:

```toml
[telegram]
enabled = true                     # set false to mute alerts without removing secrets
BOT_TOKEN = "YOUR_BOT_TOKEN"       # from @BotFather
CHAT_ID = "YOUR_CHAT_ID"           # from @userinfobot (or a negative group id, or @channelname)
```

- Get a `BOT_TOKEN` from [@BotFather](https://t.me/BotFather) after creating a bot.
- Get your `CHAT_ID` from [@userinfobot](https://t.me/userinfobot), or use a negative group id / `@channelname`.
- Environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` override `config.toml`.
- Alerts are sent synchronously over HTTPS via the Telegram Bot API (no extra async runtime needed) and never raise into the Streamlit app — failed sends are logged but do not interrupt the dashboard.

#### Automatic Multi-Ticker Alerts (cron)

`telegram_alerts.py` is a standalone runner that polls every ticker in `~/.local/share/gex_app/ticker_history.json` (the same list the dashboard maintains as you flip through symbols), computes GEX analytics via the Schwab API, and pushes Telegram alerts on detected transitions. Per-symbol previous state is persisted to `~/.local/share/gex_app/alert_state.json` so consecutive runs detect true transitions rather than re-broadcasting the current state on every poll.

By default it only operates during US regular trading hours (Mon–Fri 09:30–16:00 America/New_York) and silently returns 0 outside RTH — safe to schedule on a 5-minute cron without polluting Schwab's quota or your inbox on weekends/evenings.

```bash
# Single poll (what cron invokes):
uv run python telegram_alerts.py

# Loop forever (foreground), polling every 5 min:
uv run python telegram_alerts.py --loop --interval 300

# Force a run outside market hours (testing):
uv run python telegram_alerts.py --outside-rth

# Dry-run: compute analytics + diff but only log (no Telegram sends):
uv run python telegram_alerts.py --dry-run
```

Flags:
- `--loop` — run forever, sleeping `--interval` seconds between polls.
- `--interval N` — polling period in seconds (default `300`). Clamped to a minimum of 30s in loop mode.
- `--outside-rth` — poll even outside US regular trading hours.
- `--dry-run` — compute and log alerts but do not send Telegram messages (also implied when Telegram is disabled in config).

Example `crontab -e` entry — every 5 minutes during RTH (the script self-guards off-hours):

```cron
30/5 9-16 * * * cd ~/gex_app && /path/to/python telegram_alerts.py >> /tmp/gex_alerts.log 2>&1
```

The alert types fired are identical to the in-app `check_alerts` flow — both paths share the same pure `diff_alerts(analytics, spot)` implementation in `telegram_notifier.py`.

### Schwab Authentication

Run the auth script to perform the OAuth browser flow and save a token:

```bash
(gex_env) $ uv run schwab_auth.py
```

This opens a browser for Schwab login. The token is automatically refreshed by the client library.

### Schwab Authentication on Remote Host

1. Open VS Code Settings, uncheck **Remote.SSH: Use Exec Server**
2. Add new SSH Host and login to the remote host
3. Update `client_id` and `client_secret` in `gex_app/config.toml`
4. Run `uv run schwab_auth.py`
5. A browser will open to log in to Schwab. Once complete, a message will be displayed:

   ```
   schwab-py callback received! You may now close this window/tab.
   ```

   The token will be saved to `~/.local/share/gex_app/schwab-token.json`

### Running

```bash
(gex_env) $ ./run.sh
```

Or directly:

```bash
(gex_env) $ uv run streamlit run app.py
```

The app will be available at `http://localhost:8501`.

When running on a remote host via VS Code, the editor automatically detects the listening TCP port and offers to forward it to your local machine — no need to open ports on the remote host. A notification will appear:

> Your application running on port 8501 is available.

You can then open the app in your local browser.

## Usage

1. Enter a ticker symbol (e.g., SPY, AAPL, TSLA) in the sidebar
2. Click **Refresh** to load the option chain (the app works best during regular US market trading hours)
3. Explore 10 chart tabs with GEX visualizations and analytics
4. Use the sidebar expiration selector to filter the Options Data table (charts use sliders to control expiration count)
5. Light theme indicator in the sidebar
6. Use sliders in GEX by Expiration, IV by Strike, IV by Expiration, Heatmaps, and Gamma Surface tabs to control expiration count
7. In the **Candlesticks** tab:
   - Click and **drag in the chart body** to pan both axes (vertical drag pans the price range; horizontal drag pans time).
   - **Drag the price-scale labels** (right edge) to zoom the Y-axis, or the **time-scale labels** (bottom) to zoom the X-axis.
   - **Scroll the mouse wheel** to zoom the X-axis (bar spacing).
   - The Y zoom persists across the live 1-second streaming updates — drag it to where you want and the chart stays there.

## Architecture

```
gex_app/
├── app.py                 # Main Streamlit application
├── analytics.py           # Analytical calculations (walls, flip, skew, etc.)
├── calculations.py        # GEX/VEX/CEX calculation engine and data aggregation
├── charts.py              # Plotly chart generators
├── chart_component.py     # Lightweight Charts HTML/JS component (custom indicators, dual-axis pan/zoom, VPVR overlay, Y-range persistence across streaming re-renders)
├── client.py              # Schwab API client wrapper
├── option_streaming_service.py  # Schwab WebSocket options streaming (LEVELONE_OPTIONS for ATM call/put, 1s aggregation with buy/sell split)
├── streaming_service.py   # Schwab WebSocket streaming (Level 1 + NASDAQ/NYSE Level 2 order books, 1s OHLCV aggregation with tick-direction buy/sell volume split)
├── config.py              # Application configuration
├── config.toml            # Schwab credentials and settings
├── config.toml.example    # Example configuration template
├── schwab_auth.py         # OAuth authentication script
├── signals.py             # Strategy signals engine (scoring, recommendations, bias)
├── telegram_notifier.py   # Telegram Bot API alert sender + diff_alerts rule (config-driven, fail-safe)
├── telegram_alerts.py     # Standalone cron runner — multi-ticker alerts from ticker_history.json (RTH-guarded)
├── svi.py                 # SSVI volatility surface (Raw SVI + SSVI surface calibration)
├── schwab_data.py         # Standalone Schwab price history fetcher
├── test_calculations.py   # Unit tests for calculations
├── test_streaming.py      # Unit tests for streaming service
├── requirements.txt       # Python dependencies
├── run.sh                 # Convenience run script
├── assets/                # Screenshots of charts and dashboard panels
├── LICENSE                # License file
└── README.md              # This file
```

### Calculation Details

**GEX Formula (Gamma Exposure):**
```
GEX = Gamma × Open Interest × 100 × S² × 0.01
```

Where:
- **Gamma** — Option gamma from the Schwab API
- **Open Interest** — Number of open contracts
- **100** — Contract multiplier (100 shares per contract)
- **S** — Current spot price of the underlying
- **0.01** — 1% scaling factor (GEX represents delta change per 1% spot move)
- GEX measures gamma exposure — how dealer delta changes as the underlying price moves

**VEX Formula (Vanna Exposure):**
```
VEX = Vega × Open Interest × 100 × S × 0.01
```

Where:
- **Vega** — Option vega from the Schwab API
- **Open Interest** — Number of open contracts
- **100** — Contract multiplier
- **S** — Current spot price
- **0.01** — 1% IV scaling factor (VEX represents delta change per 1% IV move)
- VEX measures vanna exposure — how dealer delta changes as implied volatility moves

**CEX Formula (Charm Exposure):**
```
CEX = (N'(d₁) × (2(r-q)T - 2·d₁·σ√T - 1) / (2T² × 365)) × Open Interest × 100 × S × 0.01
```

Where:
- **N'(d₁)** — Standard normal PDF evaluated at d₁
- **d₁ = (ln(S/K) + (r - q + σ²/2)T) / (σ√T)** — Black-Scholes d₁
- **r** — Risk-free rate (5% assumed)
- **q** — Dividend yield (0% assumed)
- **T** — Time to expiration in years: `T = (DTE + secondsLeft / 23400) / 365` where `secondsLeft = 23400 - max(0, min(now_ET_seconds_since_0930, 23400))`. Uses the remaining fraction of the 6.5-hour US equity trading day (09:30–16:00 ET) for greater precision than whole-day DTE
- **σ** — Implied volatility from the Schwab API
- **K** — Option strike price
- CEX measures delta decay — how dealer delta changes as time passes

**Sign Convention:**
- Call options → Positive GEX (dealers buy hedging)
- Put options → Negative GEX (dealers sell hedging)
- VEX and CEX follow the same sign convention (negative for puts)

**Realized Volatility (RV):**
```
r_i = ln(close_i / close_{i-1})
σ = √( Σ(r_i - r̄)² / n )
RV = σ × √(252 × n / (n - 1))
```

Where:
- **r_i** — Daily log return
- **close_i** — Daily closing price of the underlying
- **n** — Number of daily returns in the window (20 calendar days)
- **r̄** — Mean of daily log returns
- **σ** — Population standard deviation of daily log returns (divides by n)
- **252** — Trading days per year
- **n / (n - 1)** — Degrees-of-freedom correction inside the square root
- RV measures the underlying's realized price volatility over the trailing 20 days, annualized

**Key Metrics:**
- **Call Wall** — Strike above spot with highest call GEX
- **Put Wall** — Strike below spot with highest put GEX
- **Gamma Flip** — Strike where cumulative net GEX crosses zero gamma level. Requires cumulative magnitude > 1% of total absolute GEX before registering a cross, filtering out noise from small near-zero fluctuations. 
    Above this line: Dealer flows stabilize the market (lower volatility).
    Below this line: Dealer flows destabilize the market (amplifying volatility).
- **Max +GEX** — Highest call GEX above spot 
- **Max -GEX** — Highest put GEX below spot 
- **Dealer Position** — Long Gamma (net positive) or Short Gamma (net negative)
- **Max Pain** — Strike that minimizes total dollar payout to option holders at expiration. For each strike K in the dataset, not a user-configured range: Total Pain(P) = Σ(S - K) × call_oi (if S > K) + Σ(K - S) × put_oi (if S < K), across all ITM strikes in the full chain.
- **Expected Move** — Expected price range based on ATM straddle cost
  - `Expected Move = (ATM Call Price + ATM Put Price) × 0.85`
  - Finds the ATM strike (closest to spot), sums the call and put mark prices, multiplies by 0.85 (TastyTrade convention, approximating one standard deviation)
- **IV Skew (25Δ)** — Front-expiration OTM put IV minus OTM call IV at 25 delta. Positive value = puts more expensive (downside skew), negative = calls more expensive (upside skew). Steep put skew combined with short gamma creates explosive downside risk — dealers who are short gamma must sell more into a falling market, and expensive puts amplify the hedging pressure.
- **IV (Implied Volatility)** — Per strike: uses call IV for strikes ≥ spot and put IV for strikes < spot. Represents the market's expectation of future price volatility over the option's remaining life, derived from option market prices via the Black-Scholes model.
- **Rel IV** — Per strike: `Rel IV = Strike IV / ATM IV`. Highlights which strikes have elevated implied volatility relative to the at-the-money level. Values above 1.0 indicate OTM/ITM skew — higher relative IV means the market is pricing greater expected moves at that strike. 
- **VRP (Volatility Risk Premium)** — Per strike: `VRP = IV - RV`. Computed as `VRP = ATM IV - RV` for each expiration. Measures the spread between implied volatility (option price) and realized volatility. Positive VRP means options are pricing in more volatility than has actually realized — the premium option sellers earn over time.
- **VRP Ratio** — Per strike: `VRP Ratio = IV / RV`. The ratio form of VRP, where values above 1 indicate options price more volatility than realized (expensive) and below 1 indicates the opposite (cheap).
- **VEX Magnet** — Strike with highest positive net VEX (most positive vanna exposure). As IV rises, dealer hedging creates buying pressure that attracts price toward this level.
- **VEX Repellent** — Strike with most negative net VEX. As IV rises, dealer hedging creates selling pressure that pushes price away from this level.
- **SSVI Volatility Surface** — A parametric implied volatility surface fit using the Surface Stochastic Volatility Inspired (SSVI) framework. Two-stage calibration:
  1. **Raw SVI**: Per-expiration fit of total variance as a function of log-moneyness: `w(k) = a + b(ρ(k - m) + √((k - m)² + σ²))`. TTE uses the trading-day-aware formula `(DTE + secsLeft/23400)/365`.
  2. **SSVI surface**: Across-expiration fit of ATM total variance `θ(t) = w(0, t)`, then surface-wide `ρ` (average skew), `η` (skew-smile decay), and `γ` (power-law exponent) parameters, giving a fully arbitrage-free surface.
- **SSVI IV / Skew** — Once calibrated, the surface provides cleaner `iv(strike, tte)` queries and a model-based 25Δ skew via root-finding on Black-Scholes delta. Stored as `ssvi_surface` and `ssvi_skew` in analytics.
- **IV Rank** — Where current ATM implied volatility sits in the trailing 1-year range of 20-day realized volatilities. The 20-day RV for each trailing day is computed as `σ × √252` where `σ` is the population standard deviation of the 20 most recent daily log returns. The current ATM IV (from the front-month option chain) is then ranked against the 252 trailing RV values. If ATM IV is unavailable, the latest 20-day RV is used as a fallback. Formula: `round((current - min_rv_252d) / (max_rv_252d - min_rv_252d) × 100, 2)`. Values >70 indicate options are expensive relative to history (favor selling premium), values <30 indicate options are cheap (favor buying premium). The IV by Strike chart's IV Rank view overlays the SSVI fitted surface (green line+markers) on the same strikes at the front-month tenor.

**Dealer Curve:**
Plots cumulative net GEX, VEX, or CEX across a continuum of hypothetical spot prices (toggleable). At each price level:
```
Cumulative Net = Σ net_gex / net_vex / net_cex of all strikes ≥ hypothetical spot price
```
A downward-sloping curve means dealers are short gamma (rising spot reduces net GEX); upward-sloping means long gamma. Use the radio toggle to switch between GEX, VEX, and CEX modes. Dashed vertical lines mark the current Spot price, Gamma Flip (purple longdash), Call Wall (red dot), and Put Wall (green dot) in GEX mode. In VEX mode, dashed lines mark the VEX Magnet (orange dot) and VEX Repellent (red dot) strikes. CEX (Charm Exposure) measures delta decay — how dealer delta changes as time passes.

**Aggregation:**
- **By Strike** — All option contracts are summed per strike across every expiration (GEX, OI, volume, gamma)
- **By Expiration** — All option contracts are summed per expiration across every strike (GEX, OI)

## Data Source

Uses the [Schwab API](https://developer.schwab.com/) via the `schwab-py` Python client library, which provides real-time options chain data including gamma, open interest, volume, IV, and Greeks.

## Disclaimer

This software is for **educational and informational purposes only**. It does not constitute financial advice, investment advice, or a recommendation to buy or sell any securities. Options trading involves substantial risk and is not suitable for all investors. Past performance is not indicative of future results. The authors and contributors are not responsible for any financial losses or damages resulting from the use of this software. Always consult a qualified financial professional before making investment decisions.

## License

See the [LICENSE](LICENSE) file for details. Commercial use is not permitted without prior written approval.
