from typing import Any, Optional
from calculations import (
    aggregate_by_strike,
    aggregate_by_expiration,
    compute_totals,
)
from svi import calibrate as calibrate_ssvi


def compute_analytics(data: list[dict[str, Any]], spot: float, show_calls: bool = True, show_puts: bool = True, data_full: list[dict[str, Any]] | None = None, r: float = 0.0, q: float = 0.0) -> dict[str, Any]:
    strikes = aggregate_by_strike(data, spot, show_calls=show_calls, show_puts=show_puts)
    by_exp = aggregate_by_expiration(data, show_calls=show_calls, show_puts=show_puts)
    totals = compute_totals(data)

    analytics = {}

    analytics["total_call_gex"] = totals["total_call_gex"]
    analytics["total_put_gex"] = totals["total_put_gex"]
    analytics["net_gex"] = totals["net_gex"]

    call_wall = _find_call_wall(strikes, spot)
    put_wall = _find_put_wall(strikes, spot)
    analytics["call_wall"] = call_wall
    analytics["put_wall"] = put_wall

    gamma_flip = _find_gamma_flip(strikes)
    analytics["gamma_flip"] = gamma_flip

    analytics["dealer_position"] = "Long Gamma" if totals["net_gex"] > 0 else "Short Gamma"

    max_pos = max((s for s in strikes if s["strike"] > spot and s["call_gex"] > 0), key=lambda s: s["call_gex"], default=None)
    max_neg = max((s for s in strikes if s["strike"] < spot and s["put_gex"] > 0), key=lambda s: s["put_gex"], default=None)
    analytics["max_positive_gex_strike"] = max_pos["strike"] if max_pos else None
    analytics["max_positive_gex"] = round(max_pos["call_gex"], 2) if max_pos else 0
    analytics["max_negative_gex_strike"] = max_neg["strike"] if max_neg else None
    analytics["max_negative_gex"] = round(max_neg["put_gex"], 2) if max_neg else 0

    largest_oi = max(strikes, key=lambda s: s["call_oi"] + s["put_oi"], default=None)
    analytics["largest_oi_strike"] = largest_oi["strike"] if largest_oi else None

    largest_gamma = max(strikes, key=lambda s: s["total_gamma"], default=None)
    analytics["largest_gamma_strike"] = largest_gamma["strike"] if largest_gamma else None

    expected_pin = _find_expected_pin(strikes, spot, data_full)
    analytics["expected_pin"] = expected_pin

    iv_skew_result = _calculate_iv_skew(data, spot)
    if isinstance(iv_skew_result, dict):
        analytics["iv_skew"] = iv_skew_result["iv_skew"]
        analytics["put_iv_25d"] = iv_skew_result["put_iv_25d"]
        analytics["call_iv_25d"] = iv_skew_result["call_iv_25d"]
        analytics["atm_iv"] = iv_skew_result["atm_iv"]
    else:
        analytics["iv_skew"] = iv_skew_result
        analytics["put_iv_25d"] = None
        analytics["call_iv_25d"] = None
        analytics["atm_iv"] = None

    # SSVI arbitrage-free volatility surface (Raw SVI per tenor -> SSVI).
    # Calibrated on the unfiltered chain (``data_full``) when available,
    # so the surface sees as many OTM quotes as possible across expirations.
    try:
        ssvi_res = calibrate_ssvi(data_full if data_full else data, spot, r=r, q=q)
        analytics["ssvi_surface"] = ssvi_res["surface"]
        analytics["ssvi_skew"] = ssvi_res["skew"]
        if analytics.get("atm_iv") is None and ssvi_res["atm_iv"] is not None:
            analytics["atm_iv"] = round(ssvi_res["atm_iv"], 4)
    except Exception:
        analytics["ssvi_surface"] = None
        analytics["ssvi_skew"] = None

    analytics["expected_move"] = _calculate_expected_move(data, spot)
    analytics["num_strikes"] = len(strikes)
    analytics["num_expirations"] = len(by_exp)

    vex_magnet = max((s for s in strikes if s["net_vex"] > 0), key=lambda s: s["net_vex"], default=None)
    vex_repellent = min((s for s in strikes if s["net_vex"] < 0), key=lambda s: s["net_vex"], default=None)
    analytics["vex_magnet"] = vex_magnet["strike"] if vex_magnet else None
    analytics["vex_magnet_value"] = round(vex_magnet["net_vex"], 2) if vex_magnet else 0
    analytics["vex_repellent"] = vex_repellent["strike"] if vex_repellent else None
    analytics["vex_repellent_value"] = round(vex_repellent["net_vex"], 2) if vex_repellent else 0

    return analytics


def _find_call_wall(strikes: list[dict[str, Any]], spot: float) -> Optional[float]:
    above = [s for s in strikes if s["strike"] >= spot and s["call_gex"] != 0]
    if not above:
        return None
    return max(above, key=lambda s: abs(s["call_gex"]))["strike"]


def _find_put_wall(strikes: list[dict[str, Any]], spot: float) -> Optional[float]:
    below = [s for s in strikes if s["strike"] <= spot and s["put_gex"] != 0]
    if not below:
        return None
    return max(below, key=lambda s: abs(s["put_gex"]))["strike"]


def _find_gamma_flip(strikes: list[dict[str, Any]]) -> Optional[float]:
    sorted_strikes = sorted(strikes, key=lambda s: s["strike"])
    total_abs_gex = sum(abs(s["net_gex"]) for s in sorted_strikes)
    threshold = total_abs_gex * 0.01 if total_abs_gex > 0 else 0.0
    cumulative = 0.0
    for s in sorted_strikes:
        prev = cumulative
        cumulative += s["net_gex"]
        if prev > threshold and cumulative <= 0:
            return s["strike"]
        if prev < -threshold and cumulative >= 0:
            return s["strike"]
    return None


def _find_expected_pin(strikes: list[dict[str, Any]], spot: float, data_full: list[dict[str, Any]] | None = None) -> Optional[float]:
    if not strikes:
        return None
    full = aggregate_by_strike(data_full, spot) if data_full else strikes
    strike_prices = [s["strike"] for s in strikes]
    best_strike = None
    best_pain = float("inf")
    for p in strike_prices:
        total = 0.0
        for s in full:
            k = s["strike"]
            if p > k:
                total += (p - k) * s["call_oi"]
            if p < k:
                total += (k - p) * s["put_oi"]
        if total < best_pain:
            best_pain = total
            best_strike = p
    return best_strike


def _calculate_iv_skew(data: list[dict[str, Any]], spot: float) -> Optional[dict[str, float]]:
    front = min((e for e in data if e["days_to_exp"] > 0), key=lambda e: e["days_to_exp"], default=None)
    if not front:
        return None

    front_exp = front["expiration"]
    exp_data = [e for e in data if e["expiration"] == front_exp]

    otm_puts = [e for e in exp_data if e["type"] == "PUT" and e["strike"] < spot and e["delta"] < 0 and e["iv"] > 0]
    otm_calls = [e for e in exp_data if e["type"] == "CALL" and e["strike"] > spot and e["delta"] > 0 and e["iv"] > 0]

    if not otm_puts or not otm_calls:
        return None

    put = min(otm_puts, key=lambda e: abs(abs(e["delta"]) - 0.25))
    call = min(otm_calls, key=lambda e: abs(e["delta"] - 0.25))

    atm = min(exp_data, key=lambda e: abs(e["strike"] - spot), default=None)
    atm_iv = (atm["iv"] / 100 if atm and atm["iv"] > 3 else atm["iv"] if atm else None)

    put_iv_raw = put["iv"]
    call_iv_raw = call["iv"]
    put_iv = put_iv_raw / 100 if put_iv_raw > 3 else put_iv_raw
    call_iv = call_iv_raw / 100 if call_iv_raw > 3 else call_iv_raw

    return {
        "iv_skew": round(put_iv - call_iv, 4),
        "put_iv_25d": round(put_iv, 4),
        "call_iv_25d": round(call_iv, 4),
        "atm_iv": round(atm_iv, 4) if atm_iv is not None else None,
    }


def _calculate_expected_move(data: list[dict[str, Any]], spot: float) -> Optional[dict[str, float]]:
    valid = [e for e in data if e.get("mark", 0) or 0 > 0]
    if not valid or spot <= 0:
        return None

    exps: dict[str, dict[str, list]] = {}
    for e in valid:
        exps.setdefault(e["expiration"], {"CALL": [], "PUT": []})
        exps[e["expiration"]][e["type"]].append(e)

    result = {}
    for exp, groups in sorted(exps.items()):
        if not groups["CALL"] or not groups["PUT"]:
            continue
        atm_strike = min(
            set(e["strike"] for e in groups["CALL"] + groups["PUT"]),
            key=lambda s: abs(s - spot),
        )
        call = next((e for e in groups["CALL"] if e["strike"] == atm_strike), None)
        put = next((e for e in groups["PUT"] if e["strike"] == atm_strike), None)
        if call and put:
            straddle = (call["mark"] + put["mark"]) * 0.85
            result[exp] = round(straddle, 2)
    return result or None
