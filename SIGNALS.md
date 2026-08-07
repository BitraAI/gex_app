# Trade Signals — GammaEx

The Trade Signals tab in the sidebar (tab 5) provides automated options strategy recommendations derived from the GEX analytics engine. It has three layers: Market Bias, Option Scoring, and Strategy Recommendations.

---

## Market Bias

`assess_market_bias()` in `signals.py` computes a directional bias score from five factors.
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

`generate_recommendations()` in `signals.py` produces structured trade recommendations from the filtered option chain.

### VRP computation

**Expiration ATM VRP** is the only VRP used throughout trade signals — there is no per-strike VRP. For each expiration, the option closest to spot (ATM) is identified and its VRP computed as `(ATM IV − RV) × 100` in percentage points. The `exp_vrp` dict is built from the **full option chain** (`all_data` if available, otherwise `scored`) so all expirations are represented, even when the directional strategy DTE filter narrows the candidate set. **VRP is shown in strategy recommendation text in the Trade Signals tab UI, but VRP-containing alerts are filtered out of Telegram alerts** (see **Telegram alerts** in the Code reference section).

### Candidate filtering

Options must have positive open interest and positive mark price. The strike range is limited by the sidebar's "Strikes around ATM" setting (default ±20 strikes). All recommendations use same-expiration legs where applicable.

### Spot Zone Filtering

**Critical filtering layer**: Strategy signals are calculated ONLY when spot is in the appropriate wall zone for each strategy type:

- **Long Calls / Short Puts / Call Debit Spreads / Put Credit Spreads**: Calculated **ONLY when spot is IN SUPPORT ZONE**
- **Long Puts / Short Calls / Put Debit Spreads / Call Credit Spreads**: Calculated **ONLY when spot is IN RESISTANCE ZONE**

Tickers whose spot is not in the required zone for a strategy are automatically skipped (no signals generated). This ensures each strategy type trades only when spot is aligned with the market's structural support or resistance.

### Selection logic (Long / Short Calls / Puts)

Each directional strategy follows a multi-step pipeline. All criteria are checked inside the strategy logic.

| Strategy | Strike filter | DTE range | Best expiration | IV Skew gate | Delta filter | Strike pick | Display |
|---|---|---|---|---|---|---|---|
| **Long Calls** | `CALL strike > spot` (OTM) | 1–45 | lowest `exp_vrp` among candidate expirations | `> 0` | `\|Δ\| 0.35–0.55` | lowest SSVI richness (pp) | `Buy Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | `PUT strike < spot` (OTM) | 1–45 | lowest `exp_vrp` among candidate expirations | `< 0` | `\|Δ\| 0.35–0.55` | lowest SSVI richness (pp) | `Buy Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Calls** | `CALL strike > spot` (OTM) | 1–45 | highest `exp_vrp` among candidate expirations | `< 0` | `\|Δ\| 0.15–0.20` | highest SSVI richness (pp) | `Sell Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | `PUT strike < spot` (OTM) | 1–45 | highest `exp_vrp` among candidate expirations | `> 0` | `\|Δ\| 0.15–0.20` | highest SSVI richness (pp) | `Sell Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |

**Pipeline (all four):**
1. Filter to candidate options matching the strike filter (`strike` vs `spot`) with DTE 1–45
2. Collect candidate expirations; pick the one with the **lowest** `exp_vrp` (long) or **highest** `exp_vrp` (short) — always ATM IV − RV, never per-strike. Final VRP gate: long needs `exp_vrp < −5%`, short needs `exp_vrp ≥ 5%` (skip with message otherwise)
3. Check IV Skew gate (skip with message if not satisfied)
4. Within that expiration, filter to the delta range using absolute delta `|Δ|`
5. Pick the strike with the **lowest** (long) or **highest** (short) **SSVI richness pp** (IV − SSVI IV, both as decimals). Final richness gate: long needs richness `< −3pp`, short needs richness `> +8pp` (skip with message otherwise)

### Buy Premium strategies

| Strategy | Logic |
|---|---|
| **Long Calls** | OTM calls (`strike > spot`) DTE 1–45 → lowest-VRP expiration → IV skew `> 0` → `\|Δ\|` 0.35–0.55 → lowest SSVI richness (pp) → `Buy Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long Puts** | OTM puts (`strike < spot`) DTE 1–45 → lowest-VRP expiration → IV skew `< 0` → `\|Δ\|` 0.35–0.55 → lowest SSVI richness (pp) → `Buy Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Long LEAPS** | Same as Long Calls, but DTE 90–365 (DTE filter applied in `_build_signals`) |
| **Call Debit Spread** | Buy lowest-strike call / Sell highest-strike call, same expiration; both legs must have `exp_vrp ≤ 0` |
| **Put Debit Spread** | Buy highest-strike put / Sell lowest-strike put, same expiration; both legs must have `exp_vrp ≤ 0` |
| **Long Straddles** | ATM call + put at same strike; buys if `exp_vrp` negative (cheap), sells if positive (rich) |
| **Long Strangles** | OTM call + put from the same expiration; buys if `exp_vrp` negative, sells if positive |
| **Calendar Spread** | Sell front expiration / Buy back expiration at the same strike; selects the pair with the largest `exp_vrp` difference |

### Sell Premium strategies

| Strategy | Logic |
|---|---|
| **Short Calls** | OTM calls (`strike > spot`) DTE 1–45 → highest-VRP expiration → IV skew `< 0` → `\|Δ\|` 0.15–0.20 → highest SSVI richness (pp) → `Sell Call @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
| **Short Puts** | OTM puts (`strike < spot`) DTE 1–45 → highest-VRP expiration → IV skew `> 0` → `\|Δ\|` 0.15–0.20 → highest SSVI richness (pp) → `Sell Put @ K (MM-DD) — VRP X.X%, IV (pp) +X.XX%, 25Δ Skew +X.XX%` |
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

- `signals.py` — Bias and recommendation logic. `exp_vrp` dict (ATM IV − RV per expiration) built from full chain at function entry. Directional strategies select best expiration from this dict. SSVI-based per-strike richness used for final strike selection within the chosen expiration. Also owns `_tte_from_dtes` and `build_strategy_alerts()` which produces the **Buy/Sell Premium strategy recommendation blocks** (shown in the Trade Signals tab UI; these contain VRP values in their text).
- `analytics.py` — `_calculate_iv_skew()` computes the selected-expiration 25Δ skew from OTM strikes, with SSVI and front-expiration fallbacks.
- `app.py` — `render_trade_signals_frag()` renders the UI, applies the selected-expiration restriction, and calls `generate_recommendations`; `_build_strategy_alerts()` builds the in-app Trade Signals alerts.
- `flow.py` — `_recompute_symbol()` calls `signals.build_strategy_alerts` to generate strategy recommendation blocks, then sends them to Telegram alongside wall-broke alerts and wall-reversal trend alerts. "Wall changed" alerts are permanently filtered out (`"Wall changed" not in a`); strategy recommendation text with VRP values **is** included in Telegram, but front expiration VRP is removed from the Telegram header (not passed to `notify_alerts`). The Trade Signals tab UI also shows strategy recommendations.
