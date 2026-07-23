import logging
from typing import Any, Optional
import numpy as np
from calculations import (
    aggregate_by_strike,
    aggregate_by_expiration,
    compute_totals,
)
from svi import calibrate as calibrate_ssvi
from svi import skew_for_tte as ssvi_skew_for_tte

logger = logging.getLogger(__name__)


def _filter_strikes_near_atm(data: list[dict[str, Any]], spot: float, n: int = 20) -> list[dict[str, Any]]:
    """Filter strikes to n strikes below, ATM strike, and n strikes above (price-based)."""
    strikes = sorted(set(e["strike"] for e in data))
    
    if not strikes:
        return []
    
    # Find ATM strike (closest to spot)
    atm_strike = min(strikes, key=lambda k: abs(k - spot))
    
    # Get strikes below ATM, sorted by absolute distance (closest first)
    below_strikes = sorted([s for s in strikes if s < atm_strike], key=lambda x: abs(x - atm_strike))[:n]
    
    # Get strikes above ATM, sorted by absolute distance (closest first)
    above_strikes = sorted([s for s in strikes if s > atm_strike], key=lambda x: abs(x - atm_strike))[:n]
    
    # Combine: up to n below + ATM + up to n above
    selected_strikes = below_strikes + [atm_strike] + above_strikes
    
    return [e for e in data if e["strike"] in selected_strikes]
def get_filtered_strikes_for_analysis(
    data: list[dict[str, Any]], spot: float, n: int = 20
) -> list[tuple[float, float, float, float, float, float, float, float, str, str | None]]:
    """Get filtered strikes for order flow support and resistance calculation.
    
    Returns:
        A list of strikes in the order: 20 strikes below ATM, ATM strike, 20 strikes above ATM.
        Each strike is returned as a tuple containing:
        (strike, call_gex, put_gex, call_oi, put_oi, call_iv, put_iv, net_gex, expiration, dte)
        
    Args:
        data: List of option data dictionaries
        spot: Current spot price
        n: Number of strikes to include below and above ATM (default: 20)
    """
    if not data:
        return []
    
    strikes = sorted(set(e["strike"] for e in data))
    
    if not strikes:
        return []
    
    atm_strike = min(strikes, key=lambda k: abs(k - spot))
    
    strike_map: dict[float, dict[str, Any]] = {}
    for e in data:
        strike_map[e["strike"]] = e

    below_strikes = [s for s in strikes if s < atm_strike]
    below_strikes.sort(key=lambda x: (abs(x - atm_strike), x))
    
    above_strikes = [s for s in strikes if s > atm_strike]
    above_strikes.sort(key=lambda x: (abs(x - atm_strike), x))
    
    selected_below = below_strikes[:n]
    selected_above = above_strikes[:n]

    def _row(strike: float) -> tuple:
        d = strike_map.get(strike, {})
        return (
            strike,
            d.get("call_gex", 0),
            d.get("put_gex", 0),
            d.get("call_oi", 0),
            d.get("put_oi", 0),
            d.get("call_iv", d.get("iv", 0)),
            d.get("put_iv", d.get("iv", 0)),
            d.get("net_gex", 0),
            d.get("expiration"),
            d.get("days_to_exp") or d.get("dte"),
        )

    return [_row(s) for s in selected_below] + [_row(atm_strike)] + [_row(s) for s in selected_above]


def compute_analytics(
    data: list[dict[str, Any]],
    spot: float,
    show_calls: bool = True,
    show_puts: bool = True,
    data_full: list[dict[str, Any]] | None = None,
    r: float = 0.0,
    q: float = 0.0,
    expiration: str | None = None,
    filter_strikes_to_chart_range: bool = False,
) -> dict[str, Any]:
    # For wall calculations in ATM Order Flow, use the same 41 strikes as charts
    if filter_strikes_to_chart_range:
        data = _filter_strikes_near_atm(data, spot)

    strikes = aggregate_by_strike(data, spot, show_calls=show_calls, show_puts=show_puts)
    by_exp = aggregate_by_expiration(data, show_calls=show_calls, show_puts=show_puts, spot=spot)
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

    # SSVI arbitrage-free volatility surface (Raw SVI per tenor -> SSVI).
    # Calibrated on the unfiltered chain (``data_full``) when available,
    # so the surface sees as many OTM quotes as possible across expirations.
    try:
        ssvi_res = calibrate_ssvi(data_full if data_full else data, spot, r=r, q=q)
        analytics["ssvi_surface"] = ssvi_res["surface"]
        analytics["ssvi_skew"] = ssvi_res["skew"]
        if analytics.get("atm_iv") is None and ssvi_res["atm_iv"] is not None:
            analytics["atm_iv"] = round(ssvi_res["atm_iv"], 4)
    except Exception as exc:
        logger.warning("SSVI calibration failed: %s", exc, exc_info=True)
        analytics["ssvi_surface"] = None
        analytics["ssvi_skew"] = None

    # Compute the skew on the full (untruncated) chain so every strike for the
    # selected expiration is available — ``data`` may be ATM-range limited.
    _skew_src = data_full if data_full else data
    iv_skew_result = _calculate_iv_skew(_skew_src, spot, expiration=expiration)
    if isinstance(iv_skew_result, dict):
        analytics["iv_skew"] = iv_skew_result["iv_skew"]
        analytics["put_iv_25d"] = iv_skew_result["put_iv_25d"]
        analytics["call_iv_25d"] = iv_skew_result["call_iv_25d"]
        analytics["atm_iv"] = iv_skew_result["atm_iv"]
    else:
        analytics["iv_skew"] = None
        analytics["put_iv_25d"] = None
        analytics["call_iv_25d"] = None
        analytics["atm_iv"] = None

    # Fall back to the SSVI-smoothed 25Δ skew for the selected expiration when
    # the market chain lacks usable OTM put/call quotes (e.g. LEAPS or weekly
    # expirations with strikes only on one side of spot, or no 25Δ quote).
    if analytics.get("iv_skew") is None and expiration:
        _exp_rows = [e for e in _skew_src if e.get("expiration") == expiration]
        _tte = None
        for e in _exp_rows:
            dte = e.get("days_to_exp") or e.get("dte")
            if dte:
                _tte = max(dte, 0) / 365.0
                break
        if _tte:
            _fb = ssvi_skew_for_tte(analytics.get("ssvi_surface"), _tte, ref_spot=spot)
            if _fb is not None:
                analytics["iv_skew"] = _fb

    # Last-resort fallback: if the selected expiration has no usable quotes and
    # SSVI is unavailable, use the front expiration's market skew so the metric
    # never shows N/A when any expiration in the chain carries a valid skew.
    if analytics.get("iv_skew") is None:
        _front = _calculate_iv_skew(_skew_src, spot)
        if isinstance(_front, dict) and _front.get("iv_skew") is not None:
            analytics["iv_skew"] = _front["iv_skew"]

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
    above = [s for s in strikes if s["strike"] > spot and s["call_gex"] != 0]
    if not above:
        return None
    return max(above, key=lambda s: s["call_gex"])["strike"]


def _find_put_wall(strikes: list[dict[str, Any]], spot: float) -> Optional[float]:
    below = [s for s in strikes if s["strike"] < spot and s["put_gex"] != 0]
    if not below:
        return None
    return max(below, key=lambda s: s["put_gex"])["strike"]


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
    full_sorted = sorted(full, key=lambda s: s["strike"])
    full_strikes = np.array([s["strike"] for s in full_sorted], dtype=float)
    call_oi = np.array([s.get("call_oi", 0) for s in full_sorted], dtype=float)
    put_oi = np.array([s.get("put_oi", 0) for s in full_sorted], dtype=float)

    n_full = len(full_strikes)
    cum_call_oi = np.cumsum(call_oi)
    cum_put_oi = np.cumsum(put_oi)
    cum_call_k = np.cumsum(call_oi * full_strikes)
    cum_put_k = np.cumsum(put_oi * full_strikes)
    total_call_oi = cum_call_oi[-1] if n_full else 0.0
    total_put_oi = cum_put_oi[-1] if n_full else 0.0
    total_call_k = cum_call_k[-1] if n_full else 0.0
    total_put_k = cum_put_k[-1] if n_full else 0.0

    best_strike = None
    best_pain = float("inf")
    for p in strike_prices:
        idx = np.searchsorted(full_strikes, p, side="right") - 1
        if idx >= 0:
            left_call_oi = cum_call_oi[idx]
            left_call_k = cum_call_k[idx]
        else:
            left_call_oi = 0.0
            left_call_k = 0.0
        if idx >= 0:
            right_put_oi = total_put_oi - cum_put_oi[idx]
            right_put_k = total_put_k - cum_put_k[idx]
        else:
            right_put_oi = total_put_oi
            right_put_k = total_put_k

        total = p * left_call_oi - left_call_k + right_put_k - p * right_put_oi
        if total < best_pain:
            best_pain = total
            best_strike = p
    return best_strike


def _calculate_iv_skew(data: list[dict[str, Any]], spot: float, expiration: str | None = None) -> Optional[dict[str, float]]:
    if expiration:
        front_exp = expiration
    else:
        front = min((e for e in data if e["days_to_exp"] > 0), key=lambda e: e["days_to_exp"], default=None)
        if not front:
            return None
        front_exp = front["expiration"]
    exp_data = [e for e in data if e["expiration"] == front_exp]
    if not exp_data:
        return None

    otm_puts = [e for e in exp_data if e["type"] == "PUT" and e["strike"] < spot and e["delta"] < 0 and e["iv"] > 0]
    otm_calls = [e for e in exp_data if e["type"] == "CALL" and e["strike"] > spot and e["delta"] > 0 and e["iv"] > 0]

    if not otm_puts or not otm_calls:
        return None

    # Prefer the quote closest to 25Δ; fall back to the most OTM valid quote
    # (largest |delta|) when no near-25Δ quote exists for this expiration.
    def _closest(items, target):
        with_delta = [e for e in items if e.get("delta")]
        if with_delta:
            return min(with_delta, key=lambda e: abs(abs(e["delta"]) - target))
        return max(items, key=lambda e: abs(e.get("strike", 0) - spot))

    put = _closest(otm_puts, 0.25)
    call = _closest(otm_calls, 0.25)

    atm = min(exp_data, key=lambda e: abs(e["strike"] - spot), default=None)
    atm_iv = (atm["iv"] / 100 if atm and atm["iv"] > 3 else atm["iv"] if atm else None)

    put_iv_raw = put["iv"]
    call_iv_raw = call["iv"]
    if put_iv_raw <= 0 or call_iv_raw <= 0:
        return None
    put_iv = put_iv_raw / 100 if put_iv_raw > 3 else put_iv_raw
    call_iv = call_iv_raw / 100 if call_iv_raw > 3 else call_iv_raw

    return {
        "iv_skew": round(put_iv - call_iv, 4),
        "put_iv_25d": round(put_iv, 4),
        "call_iv_25d": round(call_iv, 4),
        "atm_iv": round(atm_iv, 4) if atm_iv is not None else None,
    }


def _calculate_expected_move(data: list[dict[str, Any]], spot: float) -> Optional[dict[str, float]]:
    valid = [e for e in data if (e.get("mark", 0) or 0) > 0]
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
