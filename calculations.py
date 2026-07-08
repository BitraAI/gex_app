import numpy as np
from typing import Any, Optional
from datetime import datetime, date

STRIKE_SPACING_MAP: dict[float, float] = {
    0.0: 0.5,
    5.0: 0.5,
    10.0: 0.5,
    25.0: 0.5,
    50.0: 0.5,
    100.0: 1.0,
    200.0: 1.0,
    500.0: 2.5,
    1000.0: 5.0,
}


def get_strike_spacing(price: float) -> float:
    if price <= 5:
        return 0.5
    elif price <= 25:
        return 0.5
    elif price <= 200:
        return 1.0
    elif price <= 500:
        return 2.5
    elif price <= 1000:
        return 5.0
    else:
        return 10.0


def calculate_atm_strike(spot: float) -> float:
    spacing = get_strike_spacing(spot)
    return round(spot / spacing) * spacing


def calculate_gex(
    gamma: float, open_interest: int, spot: float
) -> float:
    return gamma * open_interest * 100 * (spot ** 2) * 0.01


def calculate_cex(
    theta: float, gamma: float, iv: float, strike: float, spot: float,
    days_to_exp: int, open_interest: int, option_type: str,
    r: float = 0.05, q: float = 0.0,
) -> float:
    if open_interest <= 0 or spot <= 0 or days_to_exp <= 0 or iv <= 0:
        return 0.0
    T = days_to_exp / 365.0
    sigma = iv
    d1 = (np.log(spot / strike) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    npd1 = np.exp(-d1 ** 2 / 2) / np.sqrt(2 * np.pi)
    charm_yearly = npd1 * (2 * (r - q) * T - 2 * d1 * sigma * np.sqrt(T) - 1) / (2 * T ** 2)
    charm_daily = charm_yearly / 365.0
    cex = charm_daily * open_interest * 100 * spot * 0.01
    if option_type == "PUT":
        cex = -abs(cex)
    return round(cex, 2)


def parse_option_chain(raw: dict[str, Any], r: float = 0.0, q: float = 0.0,
                       fallback_greeks: dict[tuple[str, float, str], float] | None = None) -> tuple[list[dict[str, Any]], float]:
    results = []
    spot_price = 0.0

    try:
        underlying = raw.get("underlying", {})
        spot_val = underlying.get("mark") or underlying.get("last") or 0
        spot_price = float(spot_val)
    except (ValueError, TypeError):
        pass

    call_exp_map = raw.get("callExpDateMap", {})
    put_exp_map = raw.get("putExpDateMap", {})

    for exp_key, strikes in call_exp_map.items():
        exp_date = _parse_exp_key(exp_key)
        for strike_str, options in strikes.items():
            try:
                strike = float(strike_str)
            except (ValueError, TypeError):
                continue
            for opt in options:
                if opt.get("putCall", "").upper() != "CALL":
                    continue
                fb = None
                if fallback_greeks is not None:
                    fb = fallback_greeks.get((exp_date, strike, "CALL"))
                entry = _extract_option_fields(opt, "CALL", strike, exp_date, spot_price, r, q, fallback_gamma=fb)
                if entry:
                    results.append(entry)

    for exp_key, strikes in put_exp_map.items():
        exp_date = _parse_exp_key(exp_key)
        for strike_str, options in strikes.items():
            try:
                strike = float(strike_str)
            except (ValueError, TypeError):
                continue
            for opt in options:
                if opt.get("putCall", "").upper() != "PUT":
                    continue
                fb = None
                if fallback_greeks is not None:
                    fb = fallback_greeks.get((exp_date, strike, "PUT"))
                entry = _extract_option_fields(opt, "PUT", strike, exp_date, spot_price, r, q, fallback_gamma=fb)
                if entry:
                    results.append(entry)

    return results, spot_price


def build_greeks_lookup(raw: dict[str, Any]) -> dict[tuple[str, float, str], float]:
    """Build {(expiration, strike, type): gamma} lookup from an option chain response."""
    lookup = {}
    for exp_key, strikes in raw.get("callExpDateMap", {}).items():
        exp_date = _parse_exp_key(exp_key)
        for strike_str, options in strikes.items():
            try:
                strike = float(strike_str)
            except (ValueError, TypeError):
                continue
            for opt in options:
                gamma = opt.get("gamma")
                if gamma is not None:
                    lookup[(exp_date, strike, "CALL")] = float(gamma)
    for exp_key, strikes in raw.get("putExpDateMap", {}).items():
        exp_date = _parse_exp_key(exp_key)
        for strike_str, options in strikes.items():
            try:
                strike = float(strike_str)
            except (ValueError, TypeError):
                continue
            for opt in options:
                gamma = opt.get("gamma")
                if gamma is not None:
                    lookup[(exp_date, strike, "PUT")] = float(gamma)
    return lookup


def _parse_exp_key(exp_key: str) -> str:
    parts = exp_key.split(":")
    return parts[0].strip()


def _extract_option_fields(
    opt: dict[str, Any],
    option_type: str,
    strike: float,
    expiration: str,
    spot: float,
    r: float = 0.0,
    q: float = 0.0,
    fallback_gamma: float | None = None,
) -> Optional[dict[str, Any]]:
    try:
        gamma = opt.get("gamma")
        if gamma is None:
            gamma = fallback_gamma
        if gamma is None:
            return None
        gamma = float(gamma)

        oi = opt.get("openInterest", 0)
        if oi is None:
            oi = 0
        oi = int(oi)

        volume = opt.get("totalVolume", 0)
        if volume is None:
            volume = 0
        volume = int(volume)

        delta = opt.get("delta")
        if delta is not None:
            delta = float(delta)

        vega = opt.get("vega")
        if vega is not None:
            vega = float(vega)

        theta = opt.get("theta")
        if theta is not None:
            theta = float(theta)

        iv = opt.get("volatility")
        if iv is not None:
            iv = float(iv)

        mark = opt.get("mark", 0)
        if mark is None:
            mark = 0
        mark = float(mark)

        if not expiration:
            return None

        try:
            exp_dt = datetime.strptime(expiration, "%Y-%m-%d")
            days_to_exp = (exp_dt - datetime.now()).days
        except (ValueError, TypeError):
            days_to_exp = 0

        gex = calculate_gex(gamma, oi, spot) if oi > 0 and spot > 0 else 0.0
        vex = (vega * oi * 100 * spot * 0.01) if oi > 0 and spot > 0 and (vega or 0) > 0 else 0.0
        cex = calculate_cex(theta, gamma, iv, strike, spot, max(days_to_exp, 1), oi, option_type, r, q) if oi > 0 and spot > 0 else 0.0

        if option_type == "PUT":
            gex = -abs(gex)
            vex = -abs(vex)

        return {
            "strike": strike,
            "expiration": expiration,
            "type": option_type,
            "gamma": gamma,
            "delta": delta or 0.0,
            "vega": vega or 0.0,
            "theta": theta or 0.0,
            "iv": iv or 0.0,
            "open_interest": oi,
            "volume": volume,
            "mark": mark,
            "gex": gex,
            "vex": vex,
            "cex": cex,
            "days_to_exp": max(days_to_exp, 0),
            "spot": spot,
        }
    except (ValueError, TypeError, KeyError):
        return None


def aggregate_by_strike(
    data: list[dict[str, Any]],
    spot: float,
    show_calls: bool = True,
    show_puts: bool = True,
    min_oi: int = 0,
    min_vol: int = 0,
) -> list[dict[str, Any]]:
    strikes_map: dict[float, dict] = {}

    for entry in data:
        if entry["open_interest"] < min_oi:
            continue
        if entry["volume"] < min_vol:
            continue

        sk = entry["strike"]
        if sk not in strikes_map:
            strikes_map[sk] = {
                "strike": sk,
                "call_gex": 0.0,
                "put_gex": 0.0,
                "net_gex": 0.0,
                "call_vex": 0.0,
                "put_vex": 0.0,
                "net_vex": 0.0,
                "call_cex": 0.0,
                "put_cex": 0.0,
                "net_cex": 0.0,
                "call_oi": 0,
                "put_oi": 0,
                "call_volume": 0,
                "put_volume": 0,
                "call_gamma": 0.0,
                "put_gamma": 0.0,
                "total_gamma": 0.0,
                "call_front_dte": 9999,
                "call_front_iv": 0.0,
                "put_front_dte": 9999,
                "put_front_iv": 0.0,
                "call_mark": 0.0,
                "put_mark": 0.0,
                "num_calls": 0,
                "num_puts": 0,
                "expirations": set(),
                "itm": spot > sk,
            }

        exp = strikes_map[sk]["expirations"]
        exp.add(entry["expiration"])

        if entry["type"] == "CALL" and show_calls:
            strikes_map[sk]["call_gex"] += entry["gex"]
            strikes_map[sk]["call_vex"] += entry["vex"]
            strikes_map[sk]["call_cex"] += entry["cex"]
            strikes_map[sk]["net_gex"] += entry["gex"]
            strikes_map[sk]["net_vex"] += entry["vex"]
            strikes_map[sk]["net_cex"] += entry["cex"]
            strikes_map[sk]["call_oi"] += entry["open_interest"]
            strikes_map[sk]["call_volume"] += entry["volume"]
            strikes_map[sk]["call_gamma"] += entry["gamma"]
            strikes_map[sk]["total_gamma"] += entry["gamma"]
            if entry["days_to_exp"] < strikes_map[sk]["call_front_dte"]:
                strikes_map[sk]["call_front_dte"] = entry["days_to_exp"]
                strikes_map[sk]["call_front_iv"] = entry["iv"]
                strikes_map[sk]["call_mark"] = entry.get("mark", 0) or 0
            strikes_map[sk]["num_calls"] += 1

        elif entry["type"] == "PUT" and show_puts:
            strikes_map[sk]["put_gex"] += abs(entry["gex"])
            strikes_map[sk]["put_vex"] += abs(entry["vex"])
            strikes_map[sk]["put_cex"] += abs(entry["cex"])
            strikes_map[sk]["net_gex"] += entry["gex"]
            strikes_map[sk]["net_vex"] += entry["vex"]
            strikes_map[sk]["net_cex"] += entry["cex"]
            strikes_map[sk]["put_oi"] += entry["open_interest"]
            strikes_map[sk]["put_volume"] += entry["volume"]
            strikes_map[sk]["put_gamma"] += entry["gamma"]
            strikes_map[sk]["total_gamma"] += entry["gamma"]
            if entry["days_to_exp"] < strikes_map[sk]["put_front_dte"]:
                strikes_map[sk]["put_front_dte"] = entry["days_to_exp"]
                strikes_map[sk]["put_front_iv"] = entry["iv"]
                strikes_map[sk]["put_mark"] = entry.get("mark", 0) or 0
            strikes_map[sk]["num_puts"] += 1

    result = []
    for sk in sorted(strikes_map.keys()):
        item = strikes_map[sk]
        item["num_expirations"] = len(item["expirations"])
        item["expirations"] = sorted(item["expirations"])
        item["call_gex"] = round(item["call_gex"], 2)
        item["put_gex"] = round(item["put_gex"], 2)
        item["net_gex"] = round(item["net_gex"], 2)
        item["call_vex"] = round(item["call_vex"], 2)
        item["put_vex"] = round(item["put_vex"], 2)
        item["net_vex"] = round(item["net_vex"], 2)
        item["call_cex"] = round(item["call_cex"], 2)
        item["put_cex"] = round(item["put_cex"], 2)
        item["net_cex"] = round(item["net_cex"], 2)
        item["call_iv"] = round(item["call_front_iv"] / 100, 4) if item["call_front_dte"] < 9999 else 0.0
        item["put_iv"] = round(item["put_front_iv"] / 100, 4) if item["put_front_dte"] < 9999 else 0.0
        result.append(item)

    return result


def aggregate_by_expiration(
    data: list[dict[str, Any]],
    show_calls: bool = True,
    show_puts: bool = True,
    spot: float = 0.0,
) -> list[dict[str, Any]]:
    exp_map: dict[str, dict] = {}

    for entry in data:
        exp = entry["expiration"]
        if exp not in exp_map:
            exp_map[exp] = {
                "expiration": exp,
                "call_gex": 0.0,
                "put_gex": 0.0,
                "net_gex": 0.0,
                "call_oi": 0,
                "put_oi": 0,
                "num_contracts": 0,
                "num_calls": 0,
                "num_puts": 0,
                "atm_iv": 0.0,
                "dte": 0,
            }

        exp_map[exp]["num_contracts"] += 1
        if entry["type"] == "CALL" and show_calls:
            exp_map[exp]["call_gex"] += entry["gex"]
            exp_map[exp]["net_gex"] += entry["gex"]
            exp_map[exp]["call_oi"] += entry["open_interest"]
            exp_map[exp]["num_calls"] += 1
        elif entry["type"] == "PUT" and show_puts:
            exp_map[exp]["put_gex"] += abs(entry["gex"])
            exp_map[exp]["net_gex"] += entry["gex"]
            exp_map[exp]["put_oi"] += entry["open_interest"]
            exp_map[exp]["num_puts"] += 1

    result = []
    for exp in sorted(exp_map.keys()):
        item = exp_map[exp]
        item["call_gex"] = round(item["call_gex"], 2)
        item["put_gex"] = round(item["put_gex"], 2)
        item["net_gex"] = round(item["net_gex"], 2)

        # Find the ATM entry for this expiration to get atm_iv and dte
        exp_entries = [e for e in data if e["expiration"] == exp]
        if exp_entries and spot > 0:
            atm_entry = min(exp_entries, key=lambda e: abs(e["strike"] - spot))
            raw_iv = atm_entry.get("iv", 0.0) or 0.0
            item["atm_iv"] = round(raw_iv / 100, 4) if raw_iv > 3 else round(raw_iv, 4)
            item["dte"] = atm_entry.get("days_to_exp", 0)
        else:
            item["atm_iv"] = 0.0
            item["dte"] = 0

        result.append(item)

    return result


def compute_totals(
    data: list[dict[str, Any]],
) -> dict[str, float]:
    total_call_gex = sum(e["gex"] for e in data if e["type"] == "CALL" and e["gex"] > 0)
    total_put_gex = sum(abs(e["gex"]) for e in data if e["type"] == "PUT" and e["gex"] < 0)
    net_gex = total_call_gex - total_put_gex
    return {
        "total_call_gex": round(total_call_gex, 2),
        "total_put_gex": round(total_put_gex, 2),
        "net_gex": round(net_gex, 2),
    }


def calculate_call_wall(data: list[dict[str, Any]], spot: float) -> Optional[float]:
    strikes = aggregate_by_strike(data, spot)
    above = [s for s in strikes if s["strike"] >= spot and s["call_gex"] != 0]
    if not above:
        return None
    return max(above, key=lambda s: abs(s["call_gex"]))["strike"]


def calculate_put_wall(data: list[dict[str, Any]], spot: float) -> Optional[float]:
    strikes = aggregate_by_strike(data, spot)
    below = [s for s in strikes if s["strike"] <= spot and s["put_gex"] != 0]
    if not below:
        return None
    return max(below, key=lambda s: abs(s["put_gex"]))["strike"]


def calculate_gamma_flip(data: list[dict[str, Any]], spot: float) -> Optional[float]:
    strikes = aggregate_by_strike(data, spot)
    net_gex_above = sum(s["net_gex"] for s in strikes if s["strike"] > spot)
    net_gex_below = sum(s["net_gex"] for s in strikes if s["strike"] < spot)
    if net_gex_above == 0:
        return None
    return round(net_gex_below / net_gex_above, 4)


def dealer_position(data: list[dict[str, Any]], spot: float) -> str:
    totals = compute_totals(data)
    if totals["net_gex"] > 0:
        return "Long Gamma"
    elif totals["net_gex"] < 0:
        return "Short Gamma"
    return "Neutral"
