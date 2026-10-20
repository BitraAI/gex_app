# GammaEx — Gamma Exposure Analytics Platform

A professional-grade options analytics dashboard that calculates and visualizes **Gamma Exposure (GEX)** for any stock using real Schwab market data.

Built with Streamlit, Plotly, NumPy, and the Schwab API.

## Features

- **Real-time Option Chain Data** — Fetches live options data via the Schwab API. For index symbols (`$SPX`, `$RUT`, `$NDX`), the ETF proxy chain (`SPY`, `IWM`, `QQQ`) is automatically fetched as a fallback: when the index chain returns zero gamma or open interest (common with Schwab's index data), delta-matched values from the ETF chain backfill the missing fields so GEX calculations remain meaningful. Per-ticker expirations are managed independently, so non-primary tickers subscribe to the correct option contracts.
- **Candlestick Charts** — Interactive OHLCV charts with SMA/EMA overlays, Trend, Volume (buy/sell pressure with streaming delta), Volume Profile (VPVR — client-side per-bar volume binned at each visible price level with buy/sell split, POC highlighted, recomputes on every pan/zoom), Anchored VWAP (session-reset line, anchored at each 09:30 ET boundary), Andean Oscillator, and EMA 50 indicators. Live ticks from the equity WebSocket are merged into the current bar every second (see `CANDLESTICS.md`). The **Order Flow** tab shows the real-time ATM option flow with per-ticker expirations, delta-weighted Net Flow, L2 Liquidity Flow, and Absorption metrics.
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
    - IV by Expiration (bar chart, toggle ATM IV / VRP — ATM IV colored by IV magnitude with RV horizontal line; VRP colored by ±10pp buckets with a Buy Premium → Sell Premium legend)
    - IV by Strike (bar chart, toggle IV / IV Richness (pp) — IV with SSVI fitted smile overlay and Spot/ATM marker; IV Richness (pp) colored by ±5pp buckets with a Cheap → Expensive legend)
  - Heatmaps + Vol Surface (strike × expiration grid, toggle OI/Volume/VRP, expandable via slider, x-axis locked)
  - Strategy Signals (automated trade recommendations from the option chain)
- **Analytics Panel:**
  - Call Wall (highest call GEX above spot), Put Wall (highest put GEX below spot)
  - Gamma Flip (cumulative net GEX zero-crossing with 1% threshold), Max Pain
  - Max +GEX, Max -GEX
  - Dealer Position (Long/Short Gamma)
   - IV Skew (25-delta, both market and SSVI-smoothed), Expected Move, Next Earnings Date, VEX Magnet, VEX Repellent
   - IV Rank — Where the latest daily return sits in the trailing 52-week range of daily returns. >70 = high vol regime (sell premium), <30 = low vol regime (buy premium)
    - **Order Flow** — Real-time ATM option flow for every tracked ticker, shown in the **Order Flow** tab. Subscribes to front expiration ATM call and put contracts for every ticker in `ticker_history.json` via LEVELONE_OPTIONS streaming (with L2 options book support). Index symbols (`$SPX`/`$RUT`/`$NDX`) stream their ETF proxy's options (`SPY`/`IWM`/`QQQ`) at the proxy's ATM strike, so Book Imbalance works for indices too. Each ticker uses its own per-ticker expiration (fetched lazily), so non-primary tickers subscribe to the correct option contracts. The grid shows per-ticker **Spot** (live equity stream or REST pre-fetch; index spots fetched separately via REST, stored as normalized uppercase display symbol), **Trend** (`up`/`down`/`UP`/`DOWN`/`bullish`/`bearish`/`flat` — from L2 book-imbalance momentum over 60 s), **Call Price** / **Put Price** (REST option marks at the put-wall / call-wall strikes, refreshed every ~2 s — index symbols quote their own index-option root), **Support** (Put Wall: strike below spot with highest put GEX) and **Resistance** (Call Wall: strike above spot with highest call GEX), **Book Imbalance** (L2 pressure, `[-1, 1]`), **Flow Speed** (first difference of book-imbalance over 60 s), **Flow Acceleration** (second difference, split at time midpoint), **Absorption** (ATM option volume per $1 of spot move — heavy absorption = price pinned, thin flow = price drifting), **Liquidity Flow** (net change in L2 resting depth over 60 s — positive = book refilling, negative = liquidity draining / break risk), **Net Flow** (60 s delta-weighted executed flow: `delta_buy − delta_sell`; each trade print routes to every tracked ticker whose stream symbol matches the option root), **Buy/Sell** (session-cumulative executed flow split by aggressor side), and **Flow Ratio** (red background `#ef5350` when > 0.8, green background `#00cc96` when < 0.2, bold text). Ticker flow tracking uses normalized display symbols (uppercase, no "$") as keys in `_ticker_flows` so lookups stay consistent. Spot cell background turns green/red on support/resistance wall breaks or reversals. Spot price updates always apply regardless of service running state. Streaming starts when you Refresh a ticker on the main page.
- **Strategy Signals:**
  - Per-option scoring (VRP + Dealer Gamma + Wall Proximity + IV Rank + IV Richness)
  - Market Bias (Bullish/Bearish/Neutral from gamma flip, net GEX, IV skew, wall distance, IV Rank)
  - Strategy recommendations: Sell/Buy Premium, Call/Put Credit Spreads, Iron Condor, Butterfly, Broken Wing Butterfly, Straddle, Strangle, Calendar Spread
  - All strategies use same-expiration legs where applicable
  - Iron Condor uses ATM range boundaries for short legs with protection legs from full data
  - Sell Premium includes Calendar Spread, Butterfly, Broken Wing Butterfly, Jade Lizard
  - Buy Premium includes Calendar Spread, Long LEAPS
  - **Multi-ticker scan** — Tick the "Scan all tickers in ticker_history.json" box to run the same signal pipeline (Buy/Sell Premium with the selected strategy) across every ticker listed in `~/.local/share/gex_app/ticker_history.json`; results are shown grouped per ticker.
    - **Per-strategy filters** (applied before scoring):
      - **Buy Premium:** delta 0.35–0.55, VRP < −5, IV Richness < −3pp, DTE 1–45
        - **Long Calls:** gate `iv_skew > 0` & selected-expiration VRP `< −5`; strike CALL `> spot`, lowest SSVI richness (pp) `< −3`
        - **Long Puts:** gate `iv_skew < 0` & selected-expiration VRP `< −5`; strike PUT `< spot`, highest SSVI richness (pp) `< −3`
      - **Long LEAPS:** delta 0.35–0.55, VRP < −5, IV Richness < −3pp, DTE 90–365
      - **Sell Premium:** delta 0.15–0.20, VRP ≥ 5% (0.05), IV Richness > +8pp, DTE 1–45
        - **Short Calls:** gate `iv_skew < 0` & selected-expiration VRP `> 0`; strike CALL `> spot`, highest SSVI richness (pp) `> 8`
        - **Short Puts:** gate `iv_skew > 0` & selected-expiration VRP `> 0`; strike PUT `< spot`, lowest SSVI richness (pp) `> 8`
      - Single-ticker view restricts scoring to the **selected expiration** so displayed VRP is the selected expiration's VRP and the strike is from that expiration.
- **Automatic Data Filtering:**
  - **±20 strikes around ATM** applied across all heatmaps (OI, Volume, IV Richness, VRP), positioning charts (OI, Volume), dealer curve (GEX, VEX, CEX), and volatility charts (IV, IV Richness, VRP)
  - **Nearest 4 active expirations** with non-zero OI/volume
  - Charts have sliders to control expiration count and are unaffected by sidebar expiration selection
- **Options Data** — Sortable grid filtered by sidebar expiration selection, with highlighted cells and CSV export (columns: Strike, Call/Put GEX, Net GEX, Call/Put OI, Call/Put Vol, Call/Put Gamma, Call/Put Price, Call/Put Delta, Call/Put IV, SSVI IV, IV (pp), Expirations):
  - **Gray row** — ATM strike (closest to spot)
  - **Red OI cells** — Max Pain strike OI columns
  - **Orange Call GEX cell** — Call Wall strike Call GEX
  - **Green Put GEX cell** — Put Wall strike Put GEX
  - **SSVI IV** — Model IV from the SSVI volatility surface at the front-month TTE
  - **IV (pp)** — IV Richness in percentage points = IV - SSVI IV
  - **Call/Put Delta** — Option delta at the front expiration (used for the Trade Signals delta filters)
- **Light Theme** — Clean light-themed UI
  - **Telegram Alerts** — Pushes an alert to a Telegram chat when key events fire:
   - GEX events: gamma flip, call wall / put wall changes, dealer gamma flips (Long↔Short), and spot crossings of the walls
   - **Trend alerts:** Wall-reversal alerts with a **conviction gate** (0–5 score from `book_imbalance`, `flow_speed`, `flow_acceleration`, `liquidity_flow`, `net_flow`, and `absorption`). Reversals (`bullish`/`bearish`) at walls fire with score ≥ 2. Directional signals sent with a trade suggestion (`BUY CALL` / `BUY PUT`)
   - **Wall-broke alerts:** 💥 "wall BROKE after absorbing N contracts" when a wall finally breaks
   - **Strategy signals:** Buy Premium and Sell Premium recommendations (same filters as the Trade Signals tab; "No strong signals" and "No OTM ..." informational messages are suppressed; wall change alerts are also suppressed from Telegram sends but still shown in the UI)
   Two delivery paths:
   - **In-app (single-ticker):** fires inline when the Streamlit dashboard refreshes its visible symbol (uses session state as the per-symbol baseline).
   - **In-app (multi-ticker):** `flow.maybe_fire_wall_zone_alerts()` runs on every Order Flow grid refresh and diffs every tracked ticker in `ticker_history.json` against the persisted per-symbol baseline — no cron / standalone runner required.
   All alerts are Markdown-formatted with the symbol header and current spot. Reads `BOT_TOKEN` / `CHAT_ID` from the `[telegram]` section of `config.toml` (overridable via `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` env vars). Set `enabled = false` to mute alerts without removing secrets. Alerts are delivered silently by default so they don't buzz the recipient's device on every refresh.

## Setup

### Prerequisites

- Python 3.12+
- A Schwab API developer application (client ID + secret)
- Schwab authentication token

### Installation

```bash
$ git clone https://github.com/BitraAI/gex_app.git
$ cd gex_app
$ python3 -m venv .venv
$ source .venv/bin/activate
(gex_venv) $ python -m pip install -U pip
(gex_venv) $ python -m pip install -U uv
(gex_venv) $ uv pip install -r requirements.txt

# Optional: exposes scripts/email_service.py for `from email_service import ...`
# with a bare interpreter (also enables pytest config below)
(gex_venv) $ python -m pip install --no-build-isolation -e .
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
max_token_age_days = 7
```

Environment variables `SCHWAB_CLIENT_ID` and `SCHWAB_CLIENT_SECRET` override `config.toml`.

#### Telegram Alerts (optional)

See **TELEGRAM.md** for full setup, alert types, message format, and suppression rules.

Quick start: add a `[telegram]` section to `config.toml`:

```toml
[telegram]
enabled = true                     # set false to mute alerts without removing secrets
BOT_TOKEN = "YOUR_BOT_TOKEN"       # from @BotFather
CHAT_ID = "YOUR_CHAT_ID"           # from @userinfobot (or a negative group id, or @channelname)
```

Environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` override `config.toml`.

### Schwab Authentication

Run the auth script to perform the OAuth browser flow and save a token:

```bash
(gex_venv) $ uv run scripts/schwab_auth.py
```

This opens a browser for Schwab login. The token is automatically refreshed by the client library.

### Schwab Authentication on Remote Host

1. Open VS Code Settings, uncheck **Remote.SSH: Use Exec Server**
2. Add new SSH Host and login to the remote host
3. Update `client_id` and `client_secret` in `gex_app/config.toml`
4. Run `uv run scripts/schwab_auth.py`
5. A browser will open to log in to Schwab. Once complete, a message will be displayed:

   ```
   schwab-py callback received! You may now close this window/tab.
   ```

   The token will be saved to `~/.local/share/gex_app/schwab-token.json`

### Running

```bash
(gex_venv) $ ./run.sh
```

Or directly:

```bash
(gex_venv) $ uv run streamlit run app.py
```

The app will be available at `http://localhost:8501`.

When running on a remote host via VS Code, the editor automatically detects the listening TCP port and offers to forward it to your local machine — no need to open ports on the remote host. A notification will appear:

> Your application running on port 8501 is available.

You can then open the app in your local browser.

## Configure Local User Service

Systemd user service for GammaEx GEX Analytics Streamlit App in ~/.config/systemd/user/gex-app.service

## Service File

```
[Unit]
Description=GammaEx GEX Analytics Streamlit App
After=network-online.target

[Service]
WorkingDirectory=/path/to/home/gex_app
ExecStart=/path/to/gex_venv/bin/streamlit run app.py --server.port 8501
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### Start the service
```bash
systemctl --user start gex-app.service
```

### Stop the service
```bash
systemctl --user stop gex-app.service
```

### Restart the service
```bash
systemctl --user restart gex-app.service
```

### Enable service to start on login
```bash
systemctl --user enable gex-app.service
```

### Disable service from starting on login
```bash
systemctl --user disable gex-app.service
```

### Check service status
```bash
systemctl --user status gex-app.service
```

### View logs (journalctl)
```bash
journalctl --user -u gex-app.service
```

### Follow logs in real-time
```bash
journalctl --user -u gex-app.service -f
```

## Usage

1. Enter a ticker symbol (e.g., SPY, AAPL, TSLA, $SPX) in the sidebar
2. Click **Refresh** to load the option chain (the app works best during regular US market trading hours)
3. Explore the visualization tabs (Market Structure, Positioning, Volatility, Heatmaps, Trade Signals, Candlesticks, Order Flow) with GEX analytics. The **Candlesticks** tab is where live WebSocket streaming starts when you Refresh a ticker; open the **Order Flow** tab for real-time ATM option flow.
4. Use the sidebar expiration selector to filter the Options Data table (charts use sliders to control expiration count)
5. Light theme indicator in the sidebar
6. Use sliders in GEX by Expiration, IV by Strike, IV by Expiration, Heatmaps, and Gamma Surface tabs to control expiration count
7. In the **Candlesticks** tab:
   - Click and **drag in the chart body** to pan both axes (vertical drag pans the price range; horizontal drag pans time).
   - **Drag the price-scale labels** (right edge) to zoom the Y-axis, or the **time-scale labels** (bottom) to zoom the X-axis.
   - **Scroll the mouse wheel** to zoom the X-axis (bar spacing).
   - The Y zoom persists across the live 1-second streaming updates — drag it to where you want and the chart stays there.
 8. **Order Flow** — open the **Order Flow** tab to see the real-time ATM order-flow grid for every ticker in `ticker_history.json`. Columns: **Ticker**, **Spot** (live equity stream or REST pre-fetch), **ATM Strike**, **Expiration**, **Support** (Put Wall: strike below spot with highest put GEX), **Resistance** (Call Wall: strike above spot with highest call GEX), **Call Price** / **Put Price** (REST marks at wall strikes, ~2 s refresh; index symbols quote their own index-option root), **Trend** (`up`/`down`/`UP`/`DOWN`/`bullish`/`bearish`/`flat` — from L2 book-imbalance momentum over 60 s), **Book Imbalance** (L2 pressure, `[-1, 1]`), **Flow Speed** (first difference of book imbalance over 60 s), **Flow Acceleration** (second difference, split at time midpoint), **Absorption** (ATM vol per $1 spot move — heavy = price pinned), **Liquidity Flow** (net L2 depth change over 60 s), **Net Flow** (60 s delta-weighted executed flow), and **Buy/Sell**. Flow Ratio background turns red (`#ef5350`) when > 0.8 and green (`#00cc96`) when < 0.2, both in bold. Spot cell background turns green/red on wall breaks or reversals. Index symbols (`$SPX`/`$RUT`/`$NDX`) stream via their ETF proxy at proxy strikes. Ticker flows use normalized display symbols (uppercase, no "$") as keys so lookups stay consistent. Streaming starts when you Refresh a ticker on the main page.

## Architecture

```
gex_app/
├── app.py                              # Main Streamlit application
├── scripts/                            # Application modules (imported by app.py as scripts.*)
│   ├── flow.py                         # Shared ATM Order Flow rendering (grid, market status indicator, wall-zone alerts, conviction scoring, session defaults, market-hours check)
│   ├── analytics.py                    # Analytical calculations (walls, flip, skew, etc.)
│   ├── calculations.py                 # GEX/VEX/CEX calculation engine, data aggregation, delta-based ETF fallback for index symbols
│   ├── charts.py                       # Plotly chart generators
│   ├── chart_component.py             # Lightweight Charts HTML/JS component (custom indicators, dual-axis pan/zoom, VPVR overlay, Y-range persistence across streaming re-renders)
│   ├── client.py                       # Schwab API client wrapper (auth, quotes, chains, candles, rate-limit retries)
│   ├── auth_db.py                       # SQLite account store for the landing page (users table, salted scrypt password hashing)
│   ├── landing.py                       # Robinhood-style landing page with Log in / Sign up (gates the app before sign-in)
│   ├── mailer.py                        # Password-reset email via SMTP ([email] config, one retry on transient drops)
│   ├── email_service.py                 # Alternate config-driven SMTP sender (send_email + send_password_reset_email, 3-attempt retry)
│   ├── config.py                       # Application configuration (single-parse of config.toml at repo root)
│   ├── schwab_auth.py                  # OAuth authentication script (run as python3 scripts/schwab_auth.py)
│   ├── _constants.py                   # Static symbol maps (STREAM_SYMBOL_MAP, INDEX_QUOTE_MAP, INDEX_SYMBOLS, MAX_BAR_ROWS, flow/stream/polling constants, chart layout)
│   ├── _utils.py                       # Shared utilities (JSON I/O, nested dict access, timestamp flooring, strike increment computation)
│   ├── index_spot_poller.py           # Background poller for index symbol REST quotes ($SPX/$RUT/$NDX → proxy ETF spots)
│   ├── news_service.py                # RSS news fetching + sentiment tagging
│   ├── option_streaming_service.py    # Schwab WebSocket options streaming (LEVELONE_OPTIONS for ATM call/put, per-ticker expiration, 1s aggregation with buy/sell split and delta-weighted Net Flow — shares the equity StreamClient)
│   ├── streaming_service.py           # Schwab WebSocket streaming (Level 1 + Level 2 options books, O(1) list-based bar accumulator converted to DataFrame on demand)
│   ├── signals.py                      # Strategy signals engine (scoring, recommendations, bias)
│   ├── svi.py                          # SSVI volatility surface (Raw SVI + SSVI surface calibration)
│   └── telegram_notifier.py            # Telegram Bot API alert sender + diff_alerts rule (config-driven, fail-safe)
├── config.toml                         # Schwab credentials and settings (NOT committed — see .gitignore)
├── requirements.txt                   # Python dependencies
├── pyproject.toml                       # Exposes scripts/email_service.py as top-level `email_service` on `pip install -e .` + pytest config (pythonpath=., testpaths=tests)
├── assets/                            # Screenshots of charts and dashboard panels
├── tests/                             # Unit tests (pytest config placeholders — no test files yet)
├── CANDLESTICS.md                     # Candlestick chart internals (indicators, dual-axis pan/zoom, Y-range persistence)
├── FLOW.md                            # ATM order-flow architecture (streaming, absorption, liquidity, net flow, conviction-gated alerts)
├── SIGNALS.md                         # Strategy-signal logic (scoring, filters, market bias)
├── LICENSE                            # License file
└── README.md                          # This file
```

### Landing Page & Accounts

The app opens on a Robinhood-style landing page (promo bar, sticky nav, hero with a live ticker tape, feature cards built from the screenshots in `assets/`, a dark flow band, trust cards, and a legal footer). Nobody reaches the dashboard until they sign in or create an account on the page:

- **Accounts live in SQLite** at `~/.local/share/gex_app/app.db` (WAL mode; override the path with the `GEX_APP_DB` env var). One `users` table keyed by **email only**: unique case-insensitive address + salted **scrypt** password hash (stdlib `hashlib`), `created_at` / `last_login` stamps. Ledger databases created with the earlier username+email schema are migrated automatically on first use.
- **The signed-in user** is kept in `st.session_state["gex_user"]`; **Log out** (top of the sidebar) clears it and returns to the landing page.
- **Forgot password**: the auth card offers a "Forgot password?" view that emails a single-use reset link (30-minute expiry) after asking for the account email. SMTP settings live under `[email]` in `config.toml` (`smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `from_addr`, `use_ssl`, `link_base`), with `GEX_SMTP_USER` / `GEX_SMTP_PASSWORD` env overrides; without `smtp_host` the link is written to the app log instead. **Gmail requires a 16-character App Password** (Google accounts reject plain account passwords for SMTP — `myaccount.google.com` → Security → 2-Step Verification → App passwords). Transient server disconnects (Gmail briefly jails IPs after bursts of failed auths) are retried automatically. Tokens are stored only as SHA-256 hashes in a `password_resets` table; a new request invalidates any pending link, and the emailed `…/?reset=<token>` URL opens the app in reset mode. Delivery is handled by `scripts/mailer.py` (app flow); `scripts/email_service.py` (`send_email()` / `send_password_reset_email()`) is the same config-driven sender with its own API — import it as `scripts.email_service`, or as top-level `email_service` after `pip install -e .`.
- The landing screenshots are copied at render time from `assets/` into `static/landing/` (git-ignored) and served by Streamlit's static handler.

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

**Realized Volatility (RV):** - RV measures the underlying's realized price volatility over the trailing 20 days, annualized.
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

**Key Metrics:**
- **Call Wall** — Strike above spot with highest call GEX
- **Put Wall** — Strike below spot with highest put GEX
- **Gamma Flip** — Strike where cumulative net GEX crosses zero gamma level. Requires cumulative magnitude > 1% of total absolute GEX before registering a cross, filtering out noise from small near-zero fluctuations. 
    Above this line: Dealer flows stabilize the market (lower volatility).
    Below this line: Dealer flows destabilize the market (amplifying volatility).
- **Max +GEX** — Highest call GEX above spot 
- **Max -GEX** — Highest put GEX below spot 
- **Dealer Position** — Long Gamma (net positive) or Short Gamma (net negative)
- **VEX Magnet** — Strike with highest positive net VEX (most positive vanna exposure). As IV rises, dealer hedging creates buying pressure that attracts price toward this level.
- **VEX Repellent** — Strike with most negative net VEX. As IV rises, dealer hedging creates selling pressure that pushes price away from this level.
- **Max Pain** — Strike that minimizes total dollar payout to option holders at expiration. For each strike K in the dataset, not a user-configured range: Total Pain(P) = Σ(S - K) × call_oi (if S > K) + Σ(K - S) × put_oi (if S < K), across all ITM strikes in the full chain.
- **Expected Move** — Expected price range based on ATM straddle cost
  - `Expected Move = (ATM Call Price + ATM Put Price) × 0.85`
  - Finds the ATM strike (closest to spot), sums the call and put mark prices, multiplies by 0.85 (TastyTrade convention, approximating one standard deviation)
- **IV Skew (25Δ)** — For the **selected expiration**, OTM put IV minus OTM call IV at 25 delta (OTM strikes only: puts `strike < spot`, calls `strike > spot`). Positive value = puts more expensive (downside skew), negative = calls more expensive (upside skew). Steep put skew combined with short gamma creates explosive downside risk — dealers who are short gamma must sell more into a falling market, and expensive puts amplify the hedging pressure. When the chain lacks usable OTM put/call quotes for the selected expiration it falls back to the SSVI-smoothed 25Δ skew at that tenor, then to the front expiration's market skew, so the metric always displays a value when any expiration carries a valid skew.
- **Volatility** — The market's implied annualized future volatility for that specific strike and expiration.
- **VRP (Volatility Risk Premium)** — Computed as `VRP = ATM IV - RV` for each expiration. Measures the spread between implied volatility (option price) and realized volatility. Positive VRP → Options are expensive relative to recent realized movement. Negative VRP → Options are cheap relative to recent realized movement.
- **SSVI Volatility Surface** — A parametric implied volatility surface fit using the Surface Stochastic Volatility Inspired (SSVI) framework. Two-stage calibration:
  1. **Raw SVI**: Per-expiration fit of total variance as a function of log-moneyness: `w(k) = a + b(ρ(k - m) + √((k - m)² + σ²))`. TTE uses the trading-day-aware formula `(DTE + secsLeft/23400)/365`.
  2. **SSVI surface**: Across-expiration fit of ATM total variance `θ(t) = w(0, t)`, then surface-wide `ρ` (average skew), `η` (skew-smile decay), and `γ` (power-law exponent) parameters, giving a fully arbitrage-free surface.
  - **Curvature (γ)**: Controls how steeply IV rises away from ATM along the smile.
    - **High Curvature (γ is large)**: OTM strikes are heavily penalized (expensive) compared to ATM options.
    - **Low Curvature (γ is small)**: The smile is flatter. OTM options are relatively cheap.
  - **Skew (ρ)**: Controls the left/right asymmetry of the smile.
    - **Negative Skew (ρ ≪ 0)**: Common in equity indexes like SPY, where puts are expensive. Use the SSVI surface to locate the specific put strike where the skew slope begins to decay, creating an optimal entry for Put Ratio Spreads.
  - **Skew-smile decay (η)**: Controls how quickly the skew term fades as time-to-expiration grows. Higher `η` means the skew-smile shape decays faster across expirations.
- **SSVI IV / Skew** — Once calibrated, the surface provides cleaner `iv(strike, tte)` queries and a model-based 25Δ skew via root-finding on Black-Scholes delta. Stored as `ssvi_surface` and `ssvi_skew` in analytics.
- **IV Rank** — Where the latest daily return (not annualized) sits in the trailing 52-week range of daily returns. For each trading day, the daily simple return is `r_i = close_i / close_{i-1} - 1`. The most recent 252 daily returns form the trailing range. The latest daily return is ranked against this range. Formula: `IV Rank = round((current_return - min_return_252d) / (max_return_252d - min_return_252d) × 100, 2)`. Values >70 indicate the underlying is at the high end of its yearly return range (high vol regime, favor selling premium), values <30 indicate it's at the low end (low vol regime, favor buying premium). The IV by Strike chart's IV Rank view overlays the SSVI fitted surface (green line+markers) on the same strikes at the front-month tenor.
- **Bullish Flow** — `call_buy_vol + put_sell_vol` from ATM option streaming. Both buying calls and selling puts express bullish conviction. Subscribes to the front expiration ATM call and put contracts via LEVELONE_OPTIONS WebSocket streaming (with Level 2 options book support). Trade direction is inferred by comparing the trade price to the bid-ask midpoint: trades at or above mid are classified as buys, trades below mid as sells. When bid/ask data is unavailable, volume is split evenly between buy and sell. Totals accumulate over the streaming session (up to 200 seconds of 1-second aggregated bars) and display in a dedicated fragment refreshing every 1 second. Card turns green when bullish flow exceeds bearish flow.
- **Bearish Flow** — `call_sell_vol + put_buy_vol` from ATM option streaming. Both selling calls and buying puts express bearish conviction. Uses the same front expiration ATM contracts and direction inference as Bullish Flow. Totals accumulate over the streaming session and display in the metrics panel with 1-second refresh. Card turns red when bearish flow exceeds bullish flow. Note: bearish flow can increase during a price rally — this often reflects traders selling calls into strength or buying protective puts to hedge long positions.

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

Uses the [Schwab API](https://developer.schwab.com/) via the `schwab-py` Python client library, which provides real-time options chain data including gamma, open interest, volume, IV, and Greeks. For index symbols (`$SPX`, `$RUT`, `$NDX`), the ETF chain is automatically fetched as a fallback source for gamma, open interest, and volume when the index chain returns zeros — matched by delta (not strike) so it works across different price scales. Index symbols stream their ETF proxy's options (`SPY`/`IWM`/`QQQ`) at proxy-level strikes, with index-level spot quotes fetched separately via REST.

Streaming uses a single WebSocket connection per session. The equity `StreamingService` owns the connection; the `AtmOptionVolumeService` piggybacks on the same `StreamClient` to subscribe to ATM option L1 quotes without opening a second connection. Each ticker uses its own per-ticker expiration (derived from the earliest option-chain date, `expirations[0]`, via `set_ticker_expiration()`), so non-primary tickers subscribe to the correct option contracts rather than inheriting the primary's expiration. The streaming service also subscribes to Level 1 options for continuous ATM flow and Level 2 options books for order flow analysis. L1 option ticks are routed to every tracked ticker whose stream symbol matches the option root, so tracking both `$SPX` and `SPY` updates both rows from the same proxy ticks.

## Disclaimer

This software is for **educational and informational purposes only**. It does not constitute financial advice, investment advice, or a recommendation to buy or sell any securities. Options trading involves substantial risk and is not suitable for all investors. Past performance is not indicative of future results. The authors and contributors are not responsible for any financial losses or damages resulting from the use of this software. Always consult a qualified financial professional before making investment decisions.

## License

See the [LICENSE](LICENSE) file for details. Commercial use is not permitted without prior written approval.
