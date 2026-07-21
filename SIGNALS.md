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

## Strategy Recommendations

`generate_recommendations()` in `signals.py:63` produces structured trade recommendations from the filtered option chain.

### VRP computation

**Expiration ATM VRP** is the only VRP used throughout trade signals — there is no per-strike VRP. For each expiration, the option closest to spot (ATM) is identified and its VRP computed as `(ATM IV − RV) × 100` in percentage points. The `exp_vrp` dict is built from the **full option chain** (`all_data` if available, otherwise `scored`) so all expirations are represented, even when the directional strategy DTE filter narrows the candidate set.

### Candidate filtering

Options must have positive open interest and positive mark price. The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes). All recommendations use same-expiration legs where applicable.

### Selection logic (Long / Short Calls / Puts)

Each directional strategy follows a multi-step pipeline. All criteria are checked inside the strategy logic.

| Strategy | GEX Bias | Strike filter | DTE range | Best expiration | IV Skew gate | Delta filter | Strike pick | Display |
|---|---|---|---|---|---|---|---|---|
| **Long Calls** | Bullish | `CALL strike > spot` (OTM) | 30–45 | lowest `exp_vrp` among candidate expirations | `> 0` | `\|Δ\| 0.35–0.55` | lowest SSVI richness (pp) | `Buy Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | Bearish | `PUT strike < spot` (OTM) | 30–45 | lowest `exp_vrp` among candidate expirations | `< 0` | `\|Δ\| 0.35–0.55` | lowest SSVI richness (pp) | `Buy Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Calls** | Bearish | `CALL strike > spot` (OTM) | 30–45 | highest `exp_vrp` among candidate expirations | `< 0` | `\|Δ\| 0.15–0.20` | highest SSVI richness (pp) | `Sell Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | Bullish | `PUT strike < spot` (OTM) | 30–45 | highest `exp_vrp` among candidate expirations | `> 0` | `\|Δ\| 0.15–0.20` | highest SSVI richness (pp) | `Sell Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |

**Pipeline (all four):**
1. Check GEX Bias matches the strategy direction (skip with message if mismatch)
2. Filter to candidate options matching the strike filter (`strike` vs `spot`) with DTE 30–45
3. Collect candidate expirations; pick the one with the **lowest** `exp_vrp` (long) or **highest** `exp_vrp` (short) — always ATM IV − RV, never per-strike
4. Check IV Skew gate (skip with message if not satisfied)
5. Within that expiration, filter to the delta range using absolute delta `|Δ|`
6. Pick the strike with the **lowest** (long) or **highest** (short) **SSVI richness pp** (IV − SSVI IV, both as decimals)

### Buy Premium strategies

| Strategy | Logic |
|---|---|
| **Long Calls** | GEX Bullish → OTM calls (`strike > spot`) DTE 30–45 → lowest-VRP expiration → IV skew `> 0` → `\|Δ\|` 0.35–0.55 → lowest SSVI richness (pp) → `Buy Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | GEX Bearish → OTM puts (`strike < spot`) DTE 30–45 → lowest-VRP expiration → IV skew `< 0` → `\|Δ\|` 0.35–0.55 → lowest SSVI richness (pp) → `Buy Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long LEAPS** | Same as Long Calls, but DTE 90–365 (DTE filter applied in `_build_signals`) |
| **Call Debit Spread** | Buy lowest-strike call / Sell highest-strike call, same expiration; both legs must have `exp_vrp ≤ 0` |
| **Put Debit Spread** | Buy highest-strike put / Sell lowest-strike put, same expiration; both legs must have `exp_vrp ≤ 0` |
| **Long Straddles** | ATM call + put at same strike; buys if `exp_vrp` negative (cheap), sells if positive (rich) |
| **Long Strangles** | OTM call + put from the same expiration; buys if `exp_vrp` negative, sells if positive |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest `exp_vrp` difference |

### Sell Premium strategies

| Strategy | Logic |
|---|---|
| **Short Calls** | GEX Bearish → OTM calls (`strike > spot`) DTE 30–45 → highest-VRP expiration → IV skew `< 0` → `\|Δ\|` 0.15–0.20 → highest SSVI richness (pp) → `Sell Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | GEX Bullish → OTM puts (`strike < spot`) DTE 30–45 → highest-VRP expiration → IV skew `> 0` → `\|Δ\|` 0.15–0.20 → highest SSVI richness (pp) → `Sell Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Call Credit Spread** | Sell lowest OTM call / Buy higher OTM call, same expiration; picks the pair where the expiration has the highest `exp_vrp` |
| **Put Credit Spread** | Sell highest OTM put / Buy lower OTM put, same expiration; picks the pair where the expiration has the highest `exp_vrp` |
| **Iron Condor** | Two-legged credit spread — sell put/call at the Put Wall and Call Wall strikes, with long protection legs at the richest OTM strikes beyond them. Falls back to symmetric wings if walls unavailable. Display shows expiration ATM VRP for each leg |
| **Iron Butterfly** | Sell ATM call + sell ATM put, buy OTM call above and OTM put below. Displays `exp_vrp` for the expiration |
| **Butterfly** | Buy one OTM put + one OTM call, sell 2× ATM body |
| **Broken Wing Butterfly (Calls)** | Buy lowest OTM call / Sell 2× middle call / Buy highest OTM call, where the upper wing is wider than the lower |
| **Long Strangles** | OTM call + put from the same expiration; buys if `exp_vrp` negative, sells if positive |
| **Jade Lizard** | Sell OTM put + Sell OTM call + Buy higher OTM call (protection), same expiration; picks the combo where the expiration has the highest `exp_vrp` |

---

## Code reference

- `signals.py` — Bias and recommendation logic. `exp_vrp` dict (ATM IV − RV per expiration) built from full chain at function entry. Directional strategies select best expiration from this dict. SSVI-based per-strike richness used for final strike selection within the chosen expiration.
- `analytics.py:167` — `_calculate_iv_skew()` computes the selected-expiration 25Δ skew from OTM strikes, with SSVI and front-expiration fallbacks.
- `app.py` — `render_trade_signals_frag()` renders the UI, applies the selected-expiration restriction, and calls `generate_recommendations`.
- `telegram_alerts.py` — `_build_strategy_alerts()` replicates the same filtering logic for standalone Telegram alert generation.
