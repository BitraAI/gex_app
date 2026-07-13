# Trade Signals — GammaEx

The Trade Signals tab in the sidebar (tab 5) provides automated options strategy recommendations derived from the GEX analytics engine. It has three layers: Market Bias, Option Scoring, and Strategy Recommendations.

---

## Market Bias

`assess_market_bias()` in `signals.py:4` computes a directional bias score from five factors:

| Factor | Bullish contribution | Bearish contribution |
|---|---|---|
| **Gamma Flip** | Spot below flip → dealers long gamma (+1) | Spot above flip → dealers short gamma (-1) |
| **Net GEX** | Positive net gamma (+1) | Negative net gamma (-1) |
| **IV Skew (25Δ)** | Positive skew → calls cheap (+1) | Negative skew → puts cheap (-1) |
| **Wall Proximity** | Put wall closer than call wall (+0.5) | Call wall closer than put wall (-0.5) |
| **IV Rank** | Low rank (<30) → options cheap, favor buying (+1) | High rank (>70) → options expensive, favor selling (-1) |

**Thresholds:** ≥ +1 → Bullish, ≤ -1 → Bearish, else Neutral.

---

## Option Scoring

`score_options()` in `signals.py:59` assigns each OTM/ATM option a numeric score. The same factors used for bias are applied per option to produce a score and signal:

| Factor | Contribution |
|---|---|
| **VRP > +2%** | +1 (option expensive → sell) |
| **VRP < -2%** | -1 (option cheap → buy) |
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

`generate_recommendations()` in `signals.py:145` produces structured trade recommendations from the scored options. The user selects Premium Type ("Buy Premium" or "Sell Premium") and a specific strategy from the dropdown.

### Buy Premium strategies

| Strategy | Logic |
|---|---|
| **Long Calls** | Best call (lowest VRP) above spot when 25Δ skew positive (calls cheap) |
| **Long Puts** | Best put (lowest VRP) below spot when 25Δ skew negative (puts cheap) |
| **Call Debit Spread** | Buy lowest-strike call (score ≤ -0.5) / Sell highest-strike call, same expiration |
| **Put Debit Spread** | Buy highest-strike put (score ≤ -0.5) / Sell lowest-strike put, same expiration |
| **Long Straddles** | ATM call + put at same strike; buys if avg VRP negative (cheap), sells if avg VRP positive (rich) |
| **Long Strangles** | OTM call + put from the same expiration; buys if avg VRP negative, sells if positive |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest score difference |

### Sell Premium strategies

| Strategy | Logic |
|---|---|
| **Short Calls** | Best call (highest VRP) above spot when 25Δ skew negative (calls rich) |
| **Short Puts** | Best put (highest VRP) below spot when 25Δ skew positive (puts rich) |
| **Call Credit Spread** | Sell lowest OTM call / Buy higher OTM call, same expiration; picks the pair with the highest avg score |
| **Put Credit Spread** | Sell highest OTM put / Buy lower OTM put, same expiration; picks the pair with the highest avg score |
| **Iron Condor** | Two-legged credit spread — sell put/call at the Put Wall and Call Wall strikes (or highest-scored OTM strikes), with long protection legs beyond them. Falls back to symmetric wings if walls unavailable |
| **Butterfly** | Buy one OTM put + one OTM call, sell 2× ATM body |
| **Broken Wing Butterfly (Calls)** | Buy lowest OTM call / Sell 2× middle call / Buy highest OTM call, where the upper wing is wider than the lower |
| **Jade Lizard** | Sell OTM put + Sell OTM call + Buy higher OTM call (protection), same expiration; picks the combo with the highest avg score |

### Data filtering

- Only **OTM + ATM** options with positive open interest and positive mark price are scored.
- The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes).
- All recommendations use same-expiration legs where applicable.

---

## Code reference

- `signals.py` — Scoring, bias, and recommendation logic
- `app.py:1339` — `render_trade_signals_frag()` renders the UI
- `app.py:1354` — In-app "How to read these signals" expander
