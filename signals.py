from typing import Any, Optional


def assess_market_bias(
    analytics: dict[str, Any],
    spot: float,
    iv_rank: float | None = None,
) -> tuple[str, str]:
    score = 0.0
    reasons = []

    gamma_flip = analytics.get("gamma_flip")
    if gamma_flip and spot > 0:
        if spot > gamma_flip:
            score -= 1
            reasons.append(f"Spot above gamma flip (${gamma_flip:g}) — dealers short gamma")
        else:
            score += 1
            reasons.append(f"Spot below gamma flip (${gamma_flip:g}) — dealers long gamma")

    net_gex = analytics.get("net_gex", 0)
    if net_gex > 0:
        score += 1
        reasons.append("Net dealer gamma positive (buy dips)")
    elif net_gex < 0:
        score -= 1
        reasons.append("Net dealer gamma negative (sell rips)")

    iv_skew = analytics.get("iv_skew")
    if iv_skew is not None:
        if iv_skew > 0:
            score += 1
            reasons.append(f"IV Skew (25Δ) positive ({iv_skew:+.2%}) — calls cheap (bullish)")
        elif iv_skew < 0:
            score -= 1
            reasons.append(f"IV Skew (25Δ) negative ({iv_skew:+.2%}) — puts cheap (bearish)")

    call_wall = analytics.get("call_wall")
    put_wall = analytics.get("put_wall")
    if call_wall and put_wall and spot > 0:
        dist_above = call_wall - spot
        dist_below = spot - put_wall
        if dist_above < dist_below:
            score -= 0.5
            reasons.append(f"Call wall closer than put wall (${call_wall:g}) — resistance near")
        elif dist_below < dist_above:
            score += 0.5
            reasons.append(f"Put wall closer than call wall (${put_wall:g}) — support near")

    if iv_rank is not None:
        if iv_rank > 70:
            score -= 1
            reasons.append(f"IV Rank high ({iv_rank:.0f}%) — options expensive, favor selling")
        elif iv_rank < 30:
            score += 1
            reasons.append(f"IV Rank low ({iv_rank:.0f}%) — options cheap, favor buying")

    if score >= 1:
        bias = "Bullish"
    elif score <= -1:
        bias = "Bearish"
    else:
        bias = "Neutral"

    return bias, "; ".join(reasons)


def score_options(
    data: list[dict[str, Any]],
    spot: float,
    rv: float,
    call_wall: Optional[float] = None,
    put_wall: Optional[float] = None,
    iv_skew: Optional[float] = None,
    iv_rank: float | None = None,
) -> list[dict[str, Any]]:
    gex_per_strike: dict[float, float] = {}
    for e in data:
        gex_per_strike[e["strike"]] = gex_per_strike.get(e["strike"], 0) + (e.get("gex", 0) or 0)

    scored = []
    for e in data:
        sk = e["strike"]
        opt_type = e["type"]
        iv = e.get("iv", 0) or 0
        if iv > 3:
            iv = iv / 100
        vrp = iv - rv
        net_gex = gex_per_strike.get(sk, 0)

        dist_to_call_wall = (call_wall - sk) if call_wall else None
        dist_to_put_wall = (sk - put_wall) if put_wall else None

        score = 0.0
        reasons = []

        if vrp > 0.02:
            score += 1
            reasons.append("VRP rich → sell")
        elif vrp < -0.02:
            score -= 1
            reasons.append("VRP cheap → buy")

        if net_gex > 0 and sk < spot:
            score -= 0.5
            reasons.append("Dealer support below")
        elif net_gex < 0 and sk > spot:
            score += 0.5
            reasons.append("Dealer resistance above")

        if dist_to_call_wall is not None and 0 < dist_to_call_wall < spot * 0.02:
            score += 0.5
            reasons.append("Near call wall")
        if dist_to_put_wall is not None and 0 < dist_to_put_wall < spot * 0.02:
            score -= 0.5
            reasons.append("Near put wall")

        if iv_skew is not None:
            if iv_skew > 0 and opt_type == "CALL":
                score -= 0.5
                reasons.append(f"25Δ skew +{iv_skew:.1%} → calls cheap")
            elif iv_skew < 0 and opt_type == "PUT":
                score += 0.5
                reasons.append(f"25Δ skew {iv_skew:.1%} → puts cheap")

        if iv_rank is not None:
            if iv_rank > 70:
                score += 0.5
                reasons.append(f"IV Rank high ({iv_rank:.0f}%) → sell premium")
            elif iv_rank < 30:
                score -= 0.5
                reasons.append(f"IV Rank low ({iv_rank:.0f}%) → buy premium")

        if score >= 1:
            signal = "Sell Premium"
        elif score <= -1:
            signal = "Buy Premium"
        else:
            signal = "Neutral"

        ep = e["expiration"]
        scored.append({
            "strike": sk,
            "expiration": f"{ep[-5:]}",
            "type": opt_type,
            "vrp": round(vrp * 100, 1),
            "price": round(e.get("mark", 0) or 0, 2),
            "oi": e.get("open_interest", 0) or 0,
            "net_gex": net_gex,
            "score": round(score, 1),
            "signal": signal,
            "reasons": "; ".join(reasons) if reasons else "",
        })
    return scored


def generate_recommendations(
    scored: list[dict[str, Any]],
    spot: float,
    strategy: str = "All",
    all_data: list[dict[str, Any]] | None = None,
    rv: float = 0.0,
    call_wall: float | None = None,
    put_wall: float | None = None,
    iv_skew: float | None = None,
    ssvi_surface: Any = None,
    ssvi_tte: float | None = None,
) -> list[str]:
    recs = []

    sell_candidates = sorted(
        [s for s in scored if s["score"] >= 1],
        key=lambda s: s["score"], reverse=True,
    )
    buy_candidates = sorted(
        [s for s in scored if s["score"] <= -1],
        key=lambda s: s["score"],
    )

    # Expiration-level VRP — represent each expiration by the VRP of the option
    # closest to spot (ATM-like). Used to favor the cheapest expiration for buy
    # premium and the richest expiration for sell premium.
    exp_vrp: dict[str, float] = {}
    exp_strike: dict[str, float] = {}
    for s in scored:
        ep = s["expiration"]
        if ep not in exp_vrp or abs(s["strike"] - spot) < abs(exp_strike[ep] - spot):
            exp_vrp[ep] = s["vrp"]
            exp_strike[ep] = s["strike"]

    def _exp_vrp(opt: dict[str, Any]) -> float:
        return exp_vrp.get(opt["expiration"], opt["vrp"])

    # Per-strike SSVI IV — used to pick the cheapest (lowest SSVI) strike for
    # buy premium and the richest (highest SSVI) strike for sell premium within
    # the selected expiration.
    def _ssvi_iv(opt: dict[str, Any]) -> float:
        if ssvi_surface is not None and ssvi_tte is not None and ssvi_tte > 0:
            iv = ssvi_surface.iv(float(opt["strike"]), float(ssvi_tte))
            if iv and iv > 0:
                return iv
        return float("inf")

    def _buy_key(opt: dict[str, Any]) -> tuple[float, float]:
        return (_exp_vrp(opt), _ssvi_iv(opt))

    def _sell_key(opt: dict[str, Any]) -> tuple[float, float]:
        return (-_exp_vrp(opt), -_ssvi_iv(opt))

    if strategy in ("Sell Premium", "Call Credit Spread", "Put Credit Spread", "Iron Condor"):
        pass

    if strategy in ("Long Calls",):
        if iv_skew is not None and iv_skew > 0:
            calls = [s for s in scored if s["type"] == "CALL" and s["strike"] >= spot]
            if calls:
                best = min(calls, key=_buy_key)
                recs.append(
                    f"**Buy {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
                    f"25Δ Skew {iv_skew:+.2%} (calls cheap), VRP {best['vrp']:.1f}%."
                )
        elif iv_skew is not None:
            recs.append(f"25Δ Skew {iv_skew:+.2%} — puts cheap; skip Long Calls.")
        else:
            recs.append("No IV skew data available.")

    if strategy in ("Long Puts",):
        if iv_skew is not None and iv_skew < 0:
            puts = [s for s in scored if s["type"] == "PUT" and s["strike"] <= spot]
            if puts:
                best = min(puts, key=_buy_key)
                recs.append(
                    f"**Buy {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
                    f"25Δ Skew {iv_skew:+.2%} (puts cheap), VRP {best['vrp']:.1f}%."
                )
        elif iv_skew is not None:
            recs.append(f"25Δ Skew {iv_skew:+.2%} — puts not cheap; skip Long Puts.")
        else:
            recs.append("No IV skew data available.")

    if strategy in ("Short Calls",):
        if iv_skew is not None and iv_skew < 0:
            calls = [s for s in scored if s["type"] == "CALL" and s["strike"] >= spot]
            if calls:
                best = max(calls, key=_sell_key)
                recs.append(
                    f"**Sell {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
                    f"25Δ Skew {iv_skew:+.2%} (calls rich), VRP {best['vrp']:.1f}%."
                )
        elif iv_skew is not None:
            recs.append(f"25Δ Skew {iv_skew:+.2%} — calls not rich; skip Short Calls.")
        else:
            recs.append("No IV skew data available.")

    if strategy in ("Short Puts",):
        if iv_skew is not None and iv_skew > 0:
            puts = [s for s in scored if s["type"] == "PUT" and s["strike"] <= spot]
            if puts:
                best = max(puts, key=_sell_key)
                recs.append(
                    f"**Sell {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
                    f"25Δ Skew {iv_skew:+.2%} (puts rich), VRP {best['vrp']:.1f}%."
                )
        elif iv_skew is not None:
            recs.append(f"25Δ Skew {iv_skew:+.2%} — puts not rich; skip Short Puts.")
        else:
            recs.append("No IV skew data available.")

    if strategy in ("Call Debit Spread",):
        calls = sorted(
            [s for s in scored if s["type"] == "CALL" and s["strike"] >= spot and s["score"] <= -0.5],
            key=lambda s: s["strike"],
        )
        if len(calls) >= 2:
            long_call = calls[0]
            short_call = calls[-1]
            width = short_call["strike"] - long_call["strike"]
            recs.append(
                f"**Call Debit Spread** — Buy {long_call['strike']:g} / Sell {short_call['strike']:g}"
                f" ({long_call['expiration']}, VRP {long_call['vrp']:.1f}%, ${width:g} wide)"
            )

    if strategy in ("Put Debit Spread",):
        puts = sorted(
            [s for s in scored if s["type"] == "PUT" and s["strike"] <= spot and s["score"] <= -0.5],
            key=lambda s: s["strike"], reverse=True,
        )
        if len(puts) >= 2:
            long_put = puts[0]
            short_put = puts[-1]
            width = long_put["strike"] - short_put["strike"]
            recs.append(
                f"**Put Debit Spread** — Buy {long_put['strike']:g} / Sell {short_put['strike']:g}"
                f" ({long_put['expiration']}, VRP {long_put['vrp']:.1f}%, ${width:g} wide)"
            )

    if strategy in ("Sell Premium",) and sell_candidates:
        otm_sell = [s for s in sell_candidates if
                    (s["type"] == "CALL" and s["strike"] >= spot) or
                    (s["type"] == "PUT" and s["strike"] <= spot)]
        pool = otm_sell if otm_sell else sell_candidates
        best = max(pool, key=_sell_key)
        recs.append(
            f"**Sell {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
            f"VRP {best['vrp']:.1f}%, GEX {best['net_gex']:,.0f}."
        )

    if strategy in ("Buy Premium",) and buy_candidates:
        otm_buy = [s for s in buy_candidates if
                   (s["type"] == "CALL" and s["strike"] >= spot) or
                   (s["type"] == "PUT" and s["strike"] <= spot)]
        pool = otm_buy if otm_buy else buy_candidates
        best = min(pool, key=_buy_key)
        recs.append(
            f"**Buy {best['type']} @ {best['strike']:g}** ({best['expiration']}) — "
            f"VRP {best['vrp']:.1f}% (cheap), GEX {best['net_gex']:,.0f}."
        )

    if strategy in ("Call Credit Spread",):
        calls_by_exp = {}
        for s in scored:
            if s["type"] == "CALL" and s["strike"] >= spot and s["score"] >= 0.5:
                calls_by_exp.setdefault(s["expiration"], []).append(s)
        best = None
        for exp, opts in calls_by_exp.items():
            opts_sorted = sorted(opts, key=lambda s: s["strike"])
            if len(opts_sorted) >= 2:
                short, long_call = opts_sorted[0], opts_sorted[-1]
                width = long_call["strike"] - short["strike"]
                avg_score = (short["score"] + long_call["score"]) / 2
                if best is None or avg_score > best[0]:
                    best = (avg_score, short, long_call, width, exp)
        if best:
            _, short, long_call, width, exp = best
            recs.append(
                f"**Call Credit Spread** — Sell {short['strike']:g} / Buy {long_call['strike']:g}"
                f" ({exp}, VRP +{short['vrp']:.1f}%, ${width:g} wide)"
            )

    if strategy in ("Put Credit Spread",):
        puts_by_exp = {}
        for s in scored:
            if s["type"] == "PUT" and s["strike"] <= spot and s["score"] >= 0.5:
                puts_by_exp.setdefault(s["expiration"], []).append(s)
        best = None
        for exp, opts in puts_by_exp.items():
            opts_sorted = sorted(opts, key=lambda s: s["strike"], reverse=True)
            if len(opts_sorted) >= 2:
                short, long_put = opts_sorted[0], opts_sorted[-1]
                width = short["strike"] - long_put["strike"]
                avg_score = (short["score"] + long_put["score"]) / 2
                if best is None or avg_score > best[0]:
                    best = (avg_score, short, long_put, width, exp)
        if best:
            _, short, long_put, width, exp = best
            recs.append(
                f"**Put Credit Spread** — Sell {short['strike']:g} / Buy {long_put['strike']:g}"
                f" ({exp}, VRP +{short['vrp']:.1f}%, ${width:g} wide)"
            )

    def _vrp(raw: dict[str, Any]) -> float:
        iv = raw.get("iv", 0) or 0
        if iv > 3:
            iv = iv / 100
        return round((iv - rv) * 100, 1)

    if strategy in ("Iron Condor",):
        src = all_data or scored
        exps = sorted(set(s["expiration"] for s in scored))

        def _find_opt(strike: float, typ: str, exp: str) -> dict[str, Any] | None:
            opts = [s for s in src if s["strike"] == strike and s["type"] == typ and s["expiration"] == exp]
            return opts[0] if opts else None

        if call_wall and put_wall and put_wall < call_wall:
            strikes_sorted = sorted(set(s["strike"] for s in scored))
            lower_strikes = [s for s in strikes_sorted if s < put_wall]
            higher_strikes = [s for s in strikes_sorted if s > call_wall]
            long_put_strike = lower_strikes[-1] if lower_strikes else None
            long_call_strike = higher_strikes[0] if higher_strikes else None

            best = None
            for exp in exps:
                sp = _find_opt(put_wall, "PUT", exp)
                sc = _find_opt(call_wall, "CALL", exp)
                lp = _find_opt(long_put_strike, "PUT", exp) if long_put_strike else None
                lc = _find_opt(long_call_strike, "CALL", exp) if long_call_strike else None
                if sp and sc and (lp or lc):
                    total_vrp = sum(s["vrp"] for s in [sp, sc, lp, lc] if s)
                    if best is None or total_vrp > best[0]:
                        best = (total_vrp, exp, sp, sc, lp, lc)

            if best:
                _, exp, sp, sc, lp, lc = best
                recs.append(
                    f"**Iron Condor ({exp})** — Sell {sp['type']} {sp['strike']:g}"
                    f" (VRP {sp['vrp']:.1f}%)"
                    + (f" / Buy {lp['type']} {lp['strike']:g} (VRP {_vrp(lp):.1f}%)" if lp else "")
                    + "  |  "
                    f"Sell {sc['type']} {sc['strike']:g} (VRP {sc['vrp']:.1f}%)"
                    + (f" / Buy {lc['type']} {lc['strike']:g} (VRP {_vrp(lc):.1f}%)" if lc else "")
                )
            else:
                recs.append("No strong signals — VRP near zero, dealer gamma balanced.")
        else:
            puts_otm = sorted(
                [s for s in scored if s["type"] == "PUT" and s["strike"] <= spot
                 and s["score"] >= 0.5 and s["vrp"] > 0],
                key=lambda s: s["strike"],
            )
            calls_otm = sorted(
                [s for s in scored if s["type"] == "CALL" and s["strike"] >= spot
                 and s["score"] >= 0.5 and s["vrp"] > 0],
                key=lambda s: s["strike"],
            )
            if puts_otm and calls_otm:
                short_put = puts_otm[0]
                short_call = calls_otm[-1]
                long_put = None
                long_call = None
                if all_data:
                    lower = short_put["strike"]
                    upper = short_call["strike"]
                    lp = sorted(
                        [e for e in all_data if e["type"] == "PUT" and e["strike"] < lower
                         and e.get("open_interest", 0) > 0 and (e.get("mark", 0) or 0) > 0],
                        key=lambda e: e["strike"], reverse=True,
                    )
                    if lp:
                        long_put = lp[0]
                    lc = sorted(
                        [e for e in all_data if e["type"] == "CALL" and e["strike"] > upper
                         and e.get("open_interest", 0) > 0 and (e.get("mark", 0) or 0) > 0],
                        key=lambda e: e["strike"],
                    )
                    if lc:
                        long_call = lc[0]
                if long_put or long_call:
                    recs.append(
                        f"**Iron Condor** — Sell {short_put['type']} {short_put['strike']:g} ({short_put['expiration']}, "
                        f"VRP {short_put['vrp']:.1f}%)"
                        + (f" / Buy {long_put['type']} {long_put['strike']:g} ({long_put['expiration'][-5:]}, "
                           f"VRP {_vrp(long_put):.1f}%)" if long_put else "")
                        + "  |  "
                        f"Sell {short_call['type']} {short_call['strike']:g} ({short_call['expiration']}, "
                        f"VRP {short_call['vrp']:.1f}%)"
                        + (f" / Buy {long_call['type']} {long_call['strike']:g} ({long_call['expiration'][-5:]}, "
                           f"VRP {_vrp(long_call):.1f}%)" if long_call else "")
                    )
                else:
                    width_put = puts_otm[-1]["strike"] - puts_otm[0]["strike"]
                    width_call = calls_otm[-1]["strike"] - calls_otm[0]["strike"]
                    recs.append(
                        f"**Iron Condor** — Sell {short_put['type']} {short_put['strike']:g} ({short_put['expiration']}, "
                        f"VRP {short_put['vrp']:.1f}%) / "
                        f"Buy {puts_otm[-1]['type']} {puts_otm[-1]['strike']:g} ({puts_otm[-1]['expiration']}, "
                        f"VRP {puts_otm[-1]['vrp']:.1f}%) (${width_put:g})  |  "
                        f"Sell {short_call['type']} {short_call['strike']:g} ({short_call['expiration']}, "
                        f"VRP {short_call['vrp']:.1f}%) / "
                        f"Buy {calls_otm[0]['type']} {calls_otm[0]['strike']:g} ({calls_otm[0]['expiration']}, "
                        f"VRP {calls_otm[0]['vrp']:.1f}%) (${width_call:g})"
                    )

    if strategy in ("Calendar Spread",):
        best = None
        groups = {}
        for s in scored:
            if abs(s["score"]) >= 0.5:
                key = (s["type"], s["strike"])
                groups.setdefault(key, []).append(s)
        for (typ, sk), opts in groups.items():
            opts_sorted = sorted(opts, key=lambda s: s["expiration"])
            if len(opts_sorted) >= 2:
                front, back = opts_sorted[0], opts_sorted[-1]
                if front["expiration"] != back["expiration"]:
                    spread_score = front["score"] - back["score"]
                    if best is None or spread_score > best[0]:
                        best = (spread_score, front, back)
        if best:
            _, front, back = best
            recs.append(
                f"**Calendar Spread** — Sell {front['type']} {front['strike']:g} ({front['expiration']}, "
                f"VRP {front['vrp']:.1f}%) / "
                f"Buy {back['type']} {back['strike']:g} ({back['expiration']}, "
                f"VRP {back['vrp']:.1f}%)"
            )

    if strategy in ("Butterfly",) and len(scored) >= 3:
        calls = sorted(
            [s for s in scored if s["type"] == "CALL" and s["strike"] > spot],
            key=lambda s: s["strike"],
        )
        puts = sorted(
            [s for s in scored if s["type"] == "PUT" and s["strike"] < spot],
            key=lambda s: s["strike"], reverse=True,
        )
        if len(calls) >= 1 and len(puts) >= 1:
            lower = puts[0]
            upper = calls[0]
            body_calls = [s for s in scored if s["type"] == "CALL" and s["strike"] < upper["strike"] and s["strike"] > spot]
            body_puts = [s for s in scored if s["type"] == "PUT" and s["strike"] > lower["strike"] and s["strike"] < spot]
            if body_calls or body_puts:
                body = (body_calls + body_puts)[0]
                spread = upper["strike"] - lower["strike"]
                recs.append(
                f"**Butterfly** — Buy {lower['type']} {lower['strike']:g} ({lower['expiration']}) / "
                f"Sell 2× {body['strike']:g} ({body['expiration']}) / "
                f"Buy {upper['type']} {upper['strike']:g} ({upper['expiration']})  "
                f"(width ${spread:g})"
                )

    if strategy in ("Iron Butterfly",) and len(scored) >= 3:
        atm = sorted(scored, key=lambda s: abs(s["strike"] - spot))
        call_opt = next((s for s in atm if s["type"] == "CALL"), None)
        put_opt = next((s for s in atm if s["type"] == "PUT"), None)
        if call_opt and put_opt and call_opt["strike"] == put_opt["strike"]:
            atm_strike = call_opt["strike"]
            exp = call_opt["expiration"]
            calls_higher = sorted([s for s in scored if s["type"] == "CALL" and s["strike"] > atm_strike], key=lambda s: s["strike"])
            puts_lower = sorted([s for s in scored if s["type"] == "PUT" and s["strike"] < atm_strike], key=lambda s: s["strike"], reverse=True)
            if calls_higher and puts_lower:
                upper = calls_higher[0]
                lower = puts_lower[0]
                spread = upper["strike"] - lower["strike"]
                avg_vrp = (call_opt["vrp"] + put_opt["vrp"]) / 2
                recs.append(
                    f"**Iron Butterfly** @ {atm_strike:g} ({exp}) — "
                    f"Sell {call_opt['strike']:g} Call / Sell {put_opt['strike']:g} Put / "
                    f"Buy {upper['strike']:g} Call / Buy {lower['strike']:g} Put  "
                    f"(width ${spread:g}, avg VRP {avg_vrp:.1f}%)"
                )

    if strategy in ("Long Straddles",):
        atm = sorted(
            [s for s in scored],
            key=lambda s: abs(s["strike"] - spot),
        )
        if len(atm) >= 2:
            call_opt = next((s for s in atm if s["type"] == "CALL"), None)
            put_opt = next((s for s in atm if s["type"] == "PUT"), None)
            if call_opt and put_opt and call_opt["strike"] == put_opt["strike"]:
                avg_vrp = (call_opt["vrp"] + put_opt["vrp"]) / 2
                action = "Sell" if avg_vrp > 0 else "Buy"
                exp = call_opt["expiration"]
                recs.append(
                    f"**{action} Straddle @ {call_opt['strike']:g} ({exp})** — "
                    f"{call_opt['type']} VRP {call_opt['vrp']:.1f}%, {put_opt['type']} VRP {put_opt['vrp']:.1f}% ({action.lower()} vol)"
                )

    if strategy in ("Long Strangles",):
        calls_by_exp = {}
        puts_by_exp = {}
        for s in scored:
            if s["type"] == "CALL" and s["strike"] > spot:
                calls_by_exp.setdefault(s["expiration"], []).append(s)
            elif s["type"] == "PUT" and s["strike"] < spot:
                puts_by_exp.setdefault(s["expiration"], []).append(s)
        best = None
        for exp in calls_by_exp:
            if exp not in puts_by_exp:
                continue
            call = calls_by_exp[exp][0]
            put = puts_by_exp[exp][0]
            avg_vrp = (call["vrp"] + put["vrp"]) / 2
            action = "Sell" if avg_vrp > 0 else "Buy"
            if best is None or abs(avg_vrp) > abs(best[0]):
                best = (avg_vrp, call, put, action)
        if best:
            _, call, put, action = best
            recs.append(
                f"**{action} Strangle** — {call['type']} {call['strike']:g} ({call['expiration']}, "
                f"VRP {call['vrp']:.1f}%) / {put['type']} {put['strike']:g} ({put['expiration']}, "
                f"VRP {put['vrp']:.1f}%) ({action.lower()} vol)"
            )

    if strategy in ("Broken Wing Butterfly",):
        calls_by_exp = {}
        for s in scored:
            if s["type"] == "CALL" and s["strike"] > spot:
                calls_by_exp.setdefault(s["expiration"], []).append(s)
        best = None
        for exp, opts in calls_by_exp.items():
            opts_sorted = sorted(opts, key=lambda s: s["strike"])
            if len(opts_sorted) >= 3:
                lower, body, upper = opts_sorted[0], opts_sorted[1], opts_sorted[-1]
                gap1 = body["strike"] - lower["strike"]
                gap2 = upper["strike"] - body["strike"]
                if gap2 > gap1:
                    avg_score = (lower["score"] + body["score"] + upper["score"]) / 3
                    if best is None or avg_score > best[0]:
                        best = (avg_score, lower, body, upper, gap1, gap2, exp)
        if best:
            _, lower, body, upper, gap1, gap2, exp = best
            recs.append(
                f"**Broken Wing Butterfly (Calls)** — Buy {lower['strike']:g} / "
                f"Sell 2× {body['strike']:g} / Buy {upper['strike']:g}"
                f" ({exp}, lower wing ${gap1:g}, upper wing ${gap2:g})"
            )

    if strategy in ("Jade Lizard",) and len(scored) >= 3:
        calls_otm = sorted([s for s in scored if s["type"] == "CALL" and s["strike"] > spot], key=lambda s: s["strike"])
        puts_otm = sorted([s for s in scored if s["type"] == "PUT" and s["strike"] < spot], key=lambda s: s["strike"], reverse=True)
        best = None
        for call_short in calls_otm:
            call_protect = next((c for c in calls_otm if c["strike"] > call_short["strike"]), None)
            if not call_protect:
                continue
            for put_short in puts_otm:
                if put_short["expiration"] != call_short["expiration"]:
                    continue
                score = (call_short["score"] + put_short["score"]) / 2
                if best is None or score > best[0]:
                    best = (score, call_short, call_protect, put_short)
        if best:
            _, call_short, call_protect, put_short = best
            spread = call_protect["strike"] - call_short["strike"]
            recs.append(
                f"**Jade Lizard** ({call_short['expiration']}) — "
                f"Sell {put_short['strike']:g} Put / Sell {call_short['strike']:g} Call / "
                f"Buy {call_protect['strike']:g} Call "
                f"(call spread width ${spread:g})"
            )

    if not recs:
        recs.append("No strong signals — VRP near zero, dealer gamma balanced.")

    return recs
