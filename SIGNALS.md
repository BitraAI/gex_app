# Trade Signals — GammaEx

The Trade Signals tab in the sidebar (tab 5) provides automated options strategy recommendations derived from the GEX analytics engine. It has three layers: Market Bias, Option Scoring, and Strategy Recommendations.

---

## Market Bias

`assess_market_bias()` in `signals.py:4` computes a directional bias score from five factors.
The IV skew factor **prefers the SSVI-smoothed skew** (`ssvi_skew.iv_skew`) over the raw market `iv_skew` when the surface is available, giving a cleaner, less noisy signal.

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
- **SSVI skew**: the front-month SSVI-smoothed 25Δ skew replaces the raw market skew for per-option adjustment

### Per-strategy pre-filters

Before scoring, the data is filtered by strategy type:

- **Buy Premium:** options with `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0 (SSVI IV), DTE 20–45
- **Long LEAPS:** same as Buy Premium but DTE 90–365
- **Sell Premium:** options with `|Δ|` 0.10–0.20, VRP > 5pp, IV Richness > 0 (SSVI IV), DTE 30–45

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

**IV Skew adjustment detail** (`iv_skew = put_iv_25d - call_iv_25d`):

- IV Skew > 0 (put skew) → calls cheap → **-0.5**
- IV Skew < 0 (call skew) → puts cheap → **+0.5**

**Signal thresholds:**
- **Score ≥ +1** → Sell Premium
- **Score ≤ -1** → Buy Premium
- **Else** → Neutral

---

## Strategy Recommendations

`generate_recommendations()` in `signals.py:157` produces structured trade recommendations from the scored options. The user selects Premium Type ("Buy Premium" or "Sell Premium") and a specific strategy from the dropdown.

When an `ssvi_surface` is provided, the Iron Condor strategy uses SSVI-smoothed 25Δ put/call strikes (with 10Δ protection) instead of the raw market walls, giving more consistent risk/reward across different volatility regimes.

### Buy Premium strategies

| Strategy | Logic | Pre-filters |
|---|---|---|
| **Long Calls** | Best call above spot when 25Δ skew positive (calls cheap); picks the expiration with the lowest VRP, then the lowest SSVI IV strike | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long Puts** | Best put below spot when 25Δ skew negative (puts cheap); picks the expiration with the highest VRP, then the highest SSVI IV strike | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long LEAPS** | Same as Long Calls, but filtered to long-dated expirations | delta 0.35–0.55, VRP<0, IR<0, DTE 90–365 |
| **Call Debit Spread** | Buy lowest-strike call (score ≤ -0.5) / Sell highest-strike call, same expiration | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Put Debit Spread** | Buy highest-strike put (score ≤ -0.5) / Sell lowest-strike put, same expiration | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long Straddles** | ATM call + put at same strike; buys if avg VRP negative (cheap), sells if avg VRP positive (rich) | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Long Strangles** | OTM call + put from the same expiration; buys if avg VRP negative, sells if positive | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest score difference | delta 0.35–0.55, VRP<0, IR<0, DTE 20–45 |

### Sell Premium strategies

| Strategy | Logic | Pre-filters |
|---|---|---|
| **Short Calls** | Best call above spot when 25Δ skew negative (calls rich); picks the expiration with the highest VRP, then the highest SSVI IV strike | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Short Puts** | Best put below spot when 25Δ skew positive (puts rich); picks the expiration with the lowest VRP, then the lowest SSVI IV strike | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Call Credit Spread** | Sell lowest OTM call / Buy higher OTM call, same expiration; picks the pair with the highest avg score | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Put Credit Spread** | Sell highest OTM put / Buy lower OTM put, same expiration; picks the pair with the highest avg score | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Iron Condor** | Two-legged credit spread — sell put/call at the Put Wall and Call Wall strikes (or SSVI 25Δ strikes when surface is available, falling back to highest-scored OTM strikes), with long protection legs beyond them (~10Δ when using SSVI). Falls back to symmetric wings if walls unavailable | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Butterfly** | Buy one OTM put + one OTM call, sell 2× ATM body | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Broken Wing Butterfly (Calls)** | Buy lowest OTM call / Sell 2× middle call / Buy highest OTM call, where the upper wing is wider than the lower | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |
| **Jade Lizard** | Sell OTM put + Sell OTM call + Buy higher OTM call (protection), same expiration; picks the combo with the highest avg score | delta 0.10–0.20, VRP>5pp, IR>0, DTE 30–45 |

### Data filtering

- Only **OTM + ATM** options with positive open interest and positive mark price are scored.
- The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes).
- All recommendations use same-expiration legs where applicable.
- **Per-strategy pre-filters** (applied before scoring, removed from `sd2`):
- **Buy Premium:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 20–45 — Long Calls: expiration with lowest VRP, then lowest SSVI IV strike; Long Puts: expiration with highest VRP, then highest SSVI IV strike
- **Long LEAPS:** delta `|Δ|` 0.35–0.55, VRP < 0, IV Richness < 0, DTE 90–365
- **Sell Premium:** delta `|Δ|` 0.10–0.20, VRP > 0.05 (>5pp), IV Richness > 0, DTE 30–45 — Short Calls: expiration with highest VRP, then highest SSVI IV strike; Short Puts: expiration with lowest VRP, then lowest SSVI IV strike

---

## Code reference

- `signals.py` — Scoring, bias, and recommendation logic (SSVI-smoothed IV/Skew/Iron Condor strikes when surface is available, trading-day TTE for CEX/SSVI precision)
- `app.py:1430` — `render_trade_signals_frag()` renders the UI, applies per-strategy pre-filters (delta/VRP/IV Richness/DTE), and calls `score_options` + `generate_recommendations`
- `telegram_alerts.py:148` — `_build_strategy_alerts()` replicates the same filtering logic for standalone Telegram alert generation
- `app.py:483` — `_build_strategy_alerts()` in-app variant triggered by `check_alerts()` on data refresh
