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
| **IV Rank** | Low rank (<30) → options cheap, favor buying (+1) | High rank (>70) → options expensive, favor selling (-1) |

**Wall Proximity detail:** Compares distances from spot to each wall. Call wall closer → -0.5 (resistance near, bearish). Put wall closer → +0.5 (support near, bullish).

**Thresholds:** ≥ +1 → Bullish, ≤ -1 → Bearish, else Neutral.

---

## Option Scoring

`score_options()` in `signals.py:68` assigns each OTM/ATM option a numeric score. The same factors used for bias are applied per option to produce a score and signal.

When an `ssvi_surface` is provided, two improvements activate:
- **Smoothed IV**: the SSVI model IV replaces raw market IV for VRP calculation, filtering out price noise
- **SSVI skew**: the SSVI-smoothed 25Δ skew replaces the raw market skew for per-option adjustment

### Per-strategy pre-filters

Before scoring, the data is filtered by strategy type:

- **Buy Premium:** options with `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0 (SSVI IV), DTE 60–90
- **Long LEAPS:** same as Buy Premium but DTE 90–365
- **Sell Premium:** options with `|Δ|` 0.15–0.20, VRP > 5pp, IV Richness > 0 (SSVI IV), DTE 30–45

These filters apply to all strategies within each premium type.

| Factor | Contribution |
|---|---|
| **VRP > 5pp** | +1 (option expensive → sell) |
| **VRP < 0** | -1 (option cheap → buy) |
| **Positive net GEX below spot** | -0.5 (dealer support below) |
| **Negative net GEX above spot** | +0.5 (dealer resistance above) |
| **Within 2% of call wall** | +0.5 | Resisting above → sell premium against resistance |
| **Within 2% of put wall** | -0.5 | Supporting below → risky for short puts; lean buy premium |
| **IV Skew skew adjustment** | ±0.5 — see detail below |
| **IV Rank > 70** | +0.5 (high rank → sell premium) |
| **IV Rank < 30** | -0.5 (low rank → buy premium) |

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

When an `ssvi_surface` is provided, the Iron Condor strategy uses SSVI-smoothed 25Δ put/call strikes (with 10Δ protection) instead of the raw market walls, giving more consistent risk/reward across different volatility regimes.

### Selection logic (Long / Short Calls / Puts)

The four directional strategies gate on the **selected-expiration 25Δ skew** and **selected-expiration VRP**, then pick the strike by **SSVI richness (pp)** = market IV − SSVI IV. Displayed result shows the selected-expiration VRP and the selected-strike SSVI richness (pp).

| Strategy | Gate (skew + selected-exp VRP) | Strike filter | Strike pick (SSVI richness pp) | Display |
|---|---|---|---|---|
| **Long Calls** | `iv_skew > 0` AND selected-exp `VRP < 0` | CALL, `strike > spot` | lowest richness (most cheap, `< 0`) | `25Δ Skew X — Calls cheap; Buy Calls, VRP X%, SSVI Richness X%` |
| **Long Puts** | `iv_skew < 0` AND selected-exp `VRP > 0` | PUT, `strike < spot` | highest richness (most rich, `> 0`) | `25Δ Skew X — Puts cheap; Buy Puts, VRP X%, SSVI Richness X%` |
| **Short Calls** | `iv_skew < 0` AND selected-exp `VRP > 0` | CALL, `strike < spot` | highest richness (`> 0`) | `25Δ Skew X — Calls expensive; Sell Calls, VRP X%, SSVI Richness X%` |
| **Short Puts** | `iv_skew > 0` AND selected-exp `VRP < 0` | PUT, `strike > spot` | lowest richness (`< 0`) | `25Δ Skew X — Puts expensive; Sell Puts, VRP X%, SSVI Richness X%` |

### Buy Premium strategies

| Strategy | Logic | Pre-filters |
|---|---|---|
| **Long Calls** | Gate `iv_skew > 0` & selected-exp `VRP < 0`; strike CALL `> spot`, lowest SSVI richness (pp) `< 0` | delta 0.35–0.55, VRP<0, IR<0, DTE 60–90 |
| **Long Puts** | Gate `iv_skew < 0` & selected-exp `VRP > 0`; strike PUT `< spot`, highest SSVI richness (pp) `> 0` | delta 0.35–0.55, VRP<0, IR<0, DTE 60–90 |
| **Long LEAPS** | Same as Long Calls, but filtered to long-dated expirations (DTE 90–365) | delta 0.35–0.55, VRP<0, IR<0, DTE 90–365 |
| **Call Debit Spread** | Buy lowest-strike call (score ≤ -0.5) / Sell highest-strike call, same expiration | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Put Debit Spread** | Buy highest-strike put (score ≤ -0.5) / Sell lowest-strike put, same expiration | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long Straddles** | ATM call + put at same strike; buys if avg VRP negative (cheap), sells if avg VRP positive (rich) | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long Strangles** | OTM call + put from the same expiration; buys if avg VRP negative, sells if positive | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest score difference | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |

### Sell Premium strategies

| Strategy | Logic | Pre-filters |
|---|---|---|
| **Short Calls** | Gate `iv_skew < 0` & selected-exp `VRP > 0`; strike CALL `< spot`, highest SSVI richness (pp) `> 0` | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Short Puts** | Gate `iv_skew > 0` & selected-exp `VRP < 0`; strike PUT `> spot`, lowest SSVI richness (pp) `< 0` | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Call Credit Spread** | Sell lowest OTM call / Buy higher OTM call, same expiration; picks the pair with the highest avg score | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Put Credit Spread** | Sell highest OTM put / Buy lower OTM put, same expiration; picks the pair with the highest avg score | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Iron Condor** | Two-legged credit spread — sell put/call at the Put Wall and Call Wall strikes (or SSVI 25Δ strikes when surface is available, falling back to highest-scored OTM strikes), with long protection legs beyond them (~10Δ when using SSVI). Falls back to symmetric wings if walls unavailable | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Butterfly** | Buy one OTM put + one OTM call, sell 2× ATM body | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Broken Wing Butterfly (Calls)** | Buy lowest OTM call / Sell 2× middle call / Buy highest OTM call, where the upper wing is wider than the lower | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Jade Lizard** | Sell OTM put + Sell OTM call + Buy higher OTM call (protection), same expiration; picks the combo with the highest avg score | delta 0.15–0.20, VRP>5pp, IR>0, DTE 30–45 |

### Data filtering

- Only **OTM + ATM** options with positive open interest and positive mark price are scored.
- The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes).
- All recommendations use same-expiration legs where applicable.
- The IV Skew (25Δ) metric uses **OTM strikes only** (puts `strike < spot`, calls `strike > spot`) and reflects the **selected expiration**.
- **Per-strategy pre-filters** (applied before scoring, removed from `sd2`):
- **Buy Premium:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 60–90 — Long Calls: gate `iv_skew > 0` & selected-exp VRP `< 0`, strike CALL `> spot`, lowest SSVI richness; Long Puts: gate `iv_skew < 0` & selected-exp VRP `> 0`, strike PUT `< spot`, highest SSVI richness
- **Long LEAPS:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 90–365
- **Sell Premium:** delta `|Δ|` 0.15–0.20, VRP > 0.05 (>5pp), IV Richness > 0, DTE 30–45 — Short Calls: gate `iv_skew < 0` & selected-exp VRP `> 0`, strike CALL `< spot`, highest SSVI richness; Short Puts: gate `iv_skew > 0` & selected-exp VRP `< 0`, strike PUT `> spot`, lowest SSVI richness

---

## Code reference

- `signals.py` — Scoring, bias, and recommendation logic (SSVI-smoothed IV/Skew/Iron Condor strikes when surface is available, trading-day TTE for CEX/SSVI precision). Long/Short Calls/Puts gating and SSVI-richness strike selection at `signals.py:224`+.
- `analytics.py:167` — `_calculate_iv_skew()` computes the selected-expiration 25Δ skew from OTM strikes, with SSVI and front-expiration fallbacks.
- `app.py:1799` — `render_trade_signals_frag()` renders the UI, applies per-strategy pre-filters and the selected-expiration restriction, and calls `score_options` + `generate_recommendations`.
- `telegram_alerts.py:166` — `_build_strategy_alerts()` replicates the same filtering logic for standalone Telegram alert generation.
- `app.py:560` — `_build_strategy_alerts()` in-app variant triggered by `check_alerts()` on data refresh.
