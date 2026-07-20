# Trade Signals — GammaEx

The Trade Signals tab in the sidebar (tab 5) provides automated options strategy recommendations derived from the GEX analytics engine. It has three layers: Market Bias, Option Scoring, and Strategy Recommendations.

---

## Market Bias

`assess_market_bias()` in `signals.py:4` computes a directional bias score from five factors.
The IV skew factor **prefers the SSVI-smoothed skew** (`ssvi_skew.iv_skew`) over the raw market `iv_skew` when the surface is available, giving a cleaner, less noisy signal.

The **IV Skew (25Δ)** metric itself is computed for the **selected expiration** (sidebar Expiration selector). It is derived from **OTM strikes only** — OTM puts (`strike < spot`) and OTM calls (`strike > spot`), preferring the quote closest to 25Δ, falling back to the most OTM valid quote when no near-25Δ quote exists. When the market chain lacks usable OTM put/call quotes for the selected expiration (e.g. LEAPS or one-sided weeklies), it falls back to the SSVI-smoothed 25Δ skew at that expiration's tenor, and finally to the front expiration's market skew, so the metric always displays a value when any expiration in the chain carries a valid skew.

| Factor | Bullish contribution | Bearish contribution |
|---|---|---|
| **Gamma Flip** | Spot below flip → dealers long gamma (+1) | Spot above flip → dealers short gamma (-1) |
| **Net GEX** | Positive net gamma (+1) | Negative net gamma (-1) |
| **IV Skew (25Δ)** | Positive skew → calls cheap (+1) | Negative skew → puts cheap (-1) |
| **Wall Proximity** | Put wall closer than call wall (+0.5) | Call wall closer than put wall (-0.5) |
**Wall Proximity detail:** Compares distances from spot to each wall. Call wall closer → -0.5 (resistance near, bearish). Put wall closer → +0.5 (support near, bullish).

**Thresholds:** ≥ +1 → Bullish, ≤ -1 → Bearish, else Neutral.

---

## Option Scoring

`score_options()` in `signals.py:68` assigns each OTM/ATM option a numeric score. The same factors used for bias are applied per option to produce a score and signal.

The VRP is computed as raw market IV minus RV. When an `ssvi_surface` is available, SSVI is used downstream in `generate_recommendations()` for per-strike richness comparison and strike selection (not in scoring itself).

**Pre-filters have been removed.** All filtering is now done inside each strategy's pipeline in `generate_recommendations()`.

| Factor | Contribution |
|---|---|
| **VRP > 5pp** | +1 (option expensive → sell) |
| **VRP < 0** | -1 (option cheap → buy) |
| **Positive net GEX below spot** | -0.5 (dealer support below) |
| **Negative net GEX above spot** | +0.5 (dealer resistance above) |
| **Within 2% of call wall** | +0.5 — Resisting above → sell premium against resistance |
| **Within 2% of put wall** | -0.5 — Supporting below → risky for short puts; lean buy premium |
| **IV Skew skew adjustment** | ±0.5 — see detail below |
**IV Skew adjustment detail** (`iv_skew = put_iv_25d - call_iv_25d`, OTM strikes only):

- IV Skew > 0 (put skew) → calls cheap → **-0.5**
- IV Skew < 0 (call skew) → puts cheap → **+0.5**

**Signal thresholds:**
- **Score ≥ +1** → Sell Premium
- **Score ≤ -1** → Buy Premium
- **Else** → Neutral

---

## Strategy Recommendations

`generate_recommendations()` in `signals.py:157` produces structured trade recommendations from the scored options. The user selects Premium Type ("Buy Premium" or "Sell Premium") and a specific strategy from the dropdown. The single-ticker view restricts scoring to the **selected expiration** so every displayed VRP is the selected expiration's VRP and every strike is from that expiration.

The Trade Signals tab can scan **every ticker in `~/.local/share/gex_app/ticker_history.json`** by ticking "Scan all tickers in ticker_history.json" and pressing **Run scan**. Each ticker's option chain is fetched and run through the same scoring + recommendation pipeline (using the selected Premium Type and strategy), with results shown grouped per ticker. This is independent of the currently loaded symbol and does not alter the main session state.

When an `ssvi_surface` is provided, the IV Skew (25Δ) metric uses a fallback chain: market OTM quotes → SSVI-smoothed skew at the selected expiration's TTE → front expiration market skew.

### Selection logic (Long / Short Calls / Puts)

Each directional strategy follows a multi-step pipeline. Pre-filters are no longer applied — all criteria are checked inside the strategy logic.

| Strategy | GEX Bias | Strike filter | DTE range | VRP selection | IV Skew gate | Delta filter | Strike pick | Display |
|---|---|---|---|---|---|---|---|---|
| **Long Calls** | Bullish | `CALL strike > spot` (OTM) | 30–45 | lowest VRP across expirations | `> 0` | `|Δ| 0.35–0.55` | lowest (IV − SSVI IV) | `Buy Call @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | Bearish | `PUT strike < spot` (OTM) | 30–45 | lowest VRP across expirations | `< 0` | `|Δ| 0.35–0.55` | lowest (IV − SSVI IV) | `Buy Put @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Calls** | Bearish | `CALL strike > spot` (OTM) | 30–45 | highest VRP across expirations | `< 0` | `|Δ| 0.15–0.20` | highest (IV − SSVI IV) | `Sell Call @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | Bullish | `PUT strike < spot` (OTM) | 30–45 | highest VRP across expirations | `> 0` | `|Δ| 0.15–0.20` | highest (IV − SSVI IV) | `Sell Put @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |

**Pipeline (all four):**
1. Check GEX Bias matches the strategy direction (skip with message if mismatch)
2. Filter to candidate options matching the strike filter (`strike` vs `spot`) with DTE 30–45
3. Across those expirations, pick the one with the **lowest VRP** (long) or **highest VRP** (short) — VRP is computed per-option as `(IV − RV) × 100`
4. Check IV Skew gate (skip with message if not satisfied)
5. Within that expiration, filter to the delta range using absolute delta `|Δ|`
6. Pick the strike with the **lowest** (long) or **highest** (short) **SSVI richness pp** (IV − SSVI IV)

### Buy Premium strategies

| Strategy | Logic |
|---|---|
| **Long Calls** | GEX Bullish → OTM calls (`strike > spot`) DTE 30–45 → lowest-VRP expiration → IV skew `> 0` → `|Δ|` 0.35–0.55 → lowest (IV − SSVI IV) → `Buy Call @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | GEX Bearish → OTM puts (`strike < spot`) DTE 30–45 → lowest-VRP expiration → IV skew `< 0` → `|Δ|` 0.35–0.55 → lowest (IV − SSVI IV) → `Buy Put @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Long LEAPS** | Same as Long Calls, but DTE 90–365 (still uses pre-filter in `_build_signals`) |
| **Call Debit Spread** | Buy lowest-strike call (score ≤ -0.5) / Sell highest-strike call, same expiration |
| **Put Debit Spread** | Buy highest-strike put (score ≤ -0.5) / Sell lowest-strike put, same expiration |
| **Long Straddles** | ATM call + put at same strike; buys if avg VRP negative (cheap), sells if avg VRP positive (rich) |
| **Long Strangles** | OTM call + put from the same expiration; buys if avg VRP negative, sells if positive |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest score difference |

### Sell Premium strategies

| Strategy | Logic |
|---|---|
| **Short Calls** | GEX Bearish → OTM calls (`strike > spot`) DTE 30–45 → highest-VRP expiration → IV skew `< 0` → `|Δ|` 0.15–0.20 → highest (IV − SSVI IV) → `Sell Call @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | GEX Bullish → OTM puts (`strike < spot`) DTE 30–45 → highest-VRP expiration → IV skew `> 0` → `|Δ|` 0.15–0.20 → highest (IV − SSVI IV) → `Sell Put @ K (MM-DD) — VRP X.X%, (IV - SSVI IV) +X.XX%, 25Δ Skew +X.XX%` |
| **Call Credit Spread** | Sell lowest OTM call / Buy higher OTM call, same expiration; picks the pair with the highest avg score |
| **Put Credit Spread** | Sell highest OTM put / Buy lower OTM put, same expiration; picks the pair with the highest avg score |
| **Iron Condor** | Two-legged credit spread — sell put/call at the Put Wall and Call Wall strikes, with long protection legs at the highest-scored OTM strikes beyond them. Falls back to symmetric wings if walls unavailable |
| **Butterfly** | Buy one OTM put + one OTM call, sell 2× ATM body |
| **Broken Wing Butterfly (Calls)** | Buy lowest OTM call / Sell 2× middle call / Buy highest OTM call, where the upper wing is wider than the lower |
| **Jade Lizard** | Sell OTM put + Sell OTM call + Buy higher OTM call (protection), same expiration; picks the combo with the highest avg score |

### Data filtering

- Only **OTM + ATM** options with positive open interest and positive mark price are scored.
- The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes).
- All recommendations use same-expiration legs where applicable.
- The IV Skew (25Δ) metric uses **OTM strikes only** (puts `strike < spot`, calls `strike > spot`) and reflects the **selected expiration**.
- **Per-strategy pre-filters** (applied before scoring, removed from `sd2`):
- **Buy Premium:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 60–90 — Long Calls: gate `iv_skew > 0` & selected-exp VRP `< 0`, strike CALL `> spot` (OTM), lowest SSVI richness; Long Puts: gate `iv_skew < 0` & selected-exp VRP `> 0`, strike PUT `< spot` (OTM), lowest SSVI richness
- **Long LEAPS:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 90–365
- **Sell Premium:** delta `|Δ|` 0.15–0.20, VRP > 0.05 (>5pp), IV Richness > 0, DTE 30–45 — Short Calls: gate `iv_skew < 0` & selected-exp VRP `> 0`, strike CALL `> spot` (OTM), highest SSVI richness; Short Puts: gate `iv_skew > 0` & selected-exp VRP `< 0`, strike PUT `< spot` (OTM), highest SSVI richness

---

## Code reference

- `signals.py` — Scoring, bias, and recommendation logic (SSVI-smoothed skew for IV Skew metric, SSVI-based per-strike richness and strike selection in directional strategies, trading-day TTE for CEX/SSVI precision). Directional strategies: Long Calls at `signals.py:225`, Long Puts at `signals.py:264`, Short Calls at `signals.py:303`, Short Puts at `signals.py:342`.
- `analytics.py:167` — `_calculate_iv_skew()` computes the selected-expiration 25Δ skew from OTM strikes, with SSVI and front-expiration fallbacks.
- `app.py:1812` — `render_trade_signals_frag()` renders the UI, applies per-strategy pre-filters and the selected-expiration restriction, and calls `score_options` + `generate_recommendations`.
- `telegram_alerts.py:166` — `_build_strategy_alerts()` replicates the same filtering logic for standalone Telegram alert generation.
- `app.py:542` — `_build_strategy_alerts()` in-app variant triggered by `check_alerts()` on data refresh.
