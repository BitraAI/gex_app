import bisect
import numpy as np
from typing import Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts._utils import secs_since_market_open as _secs_since_market_open


def get_strike_spacing(price: float) -> float:
    if price <= 25:
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


# Pre-parsed expiration dates ("YYYY-MM-DD" -> datetime); parse is per-option
# work otherwise and there are only a handful of distinct dates per chain.
_exp_dt_cache: dict[str, datetime] = {}


def calculate_cex(
    iv: float, strike: float, spot: float,
    days_to_exp: int, open_interest: int, option_type: str,
    r: float = 0.05, q: float = 0.0,
) -> float:
    if open_interest <= 0 or spot <= 0 or days_to_exp <= 0 or iv <= 0:
        return 0.0
    _secs_since_930 = _secs_since_market_open()
    _secs_left = 23400 - _secs_since_930
    T = (days_to_exp + _secs_left / 23400) / 365.0
    sigma = iv
    d1 = (np.log(spot / strike) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    npd1 = np.exp(-d1 ** 2 / 2) / np.sqrt(2 * np.pi)
    charm_yearly = npd1 * (2 * (r - q) * T - 2 * d1 * sigma * np.sqrt(T) - 1) / (2 * T ** 2)
    charm_daily = charm_yearly / 365.0
    cex = charm_daily * open_interest * 100 * spot * 0.01
    if option_type == "PUT":
        cex = -abs(cex)
    return round(cex, 2)


def compute_totals(data: list[dict[str, Any]]) -> dict[str, float]:
    total_call_gex = sum(e["gex"] for e in data if e["type"] == "CALL" and e["gex"] > 0)
    total_put_gex = sum(abs(e["gex"]) for e in data if e["type"] == "PUT" and e["gex"] < 0)
    net_gex = total_call_gex - total_put_gex
    return {
        "total_call_gex": round(total_call_gex, 2),
        "total_put_gex": round(total_put_gex, 2),
        "net_gex": round(net_gex, 2),
    }


def parse_option_chain(raw: dict[str, Any], r: float = 0.0, q: float = 0.0,
                       fallback_greeks: dict[tuple[str, float, str], dict[str, float]] | None = None) -> tuple[list[dict[str, Any]], float]:
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
    _now = datetime.now()
    _fb_index = _build_fallback_index(fallback_greeks)

    for exp_map, option_type in ((call_exp_map, "CALL"), (put_exp_map, "PUT")):
        for exp_key, strikes in exp_map.items():
            exp_date = _parse_exp_key(exp_key)
            for strike_str, options in strikes.items():
                try:
                    strike = float(strike_str)
                except (ValueError, TypeError):
                    continue
                for opt in options:
                    if opt.get("putCall", "").upper() != option_type:
                        continue
                    fb = _find_fallback(_fb_index, exp_date, float(opt.get("delta", 0) or 0), option_type)
                    entry = _extract_option_fields(opt, option_type, strike, exp_date, spot_price, r, q, fallback=fb, _now=_now)
                    if entry:
                        results.append(entry)

    return results, spot_price


def build_greeks_lookup(raw: dict[str, Any]) -> dict[tuple[str, float, str], float]:
    """Build {(expiration, rounded_delta, type): {gamma, oi, volume}} lookup
    from an option chain response.  Delta-based so it works across underlyings
    with different price scales (e.g. SPX vs SPY)."""
    lookup: dict[tuple[str, float, str], dict[str, float]] = {}
    for exp_map, option_type in ((raw.get("callExpDateMap", {}), "CALL"),
                                 (raw.get("putExpDateMap", {}), "PUT")):
        for exp_key, strikes in exp_map.items():
            exp_date = _parse_exp_key(exp_key)
            for strike_str, options in strikes.items():
                for opt in options:
                    gamma = opt.get("gamma")
                    delta = opt.get("delta")
                    oi = opt.get("openInterest", 0) or 0
                    vol = opt.get("totalVolume") or opt.get("volume") or 0
                    if gamma is None or delta is None:
                        continue
                    d_rounded = round(float(delta), 2)
                    lookup[(exp_date, d_rounded, option_type)] = {
                        "gamma": float(gamma), "oi": int(oi), "volume": int(vol),
                    }
    return lookup


def _build_fallback_index(
    fallback: dict[tuple[str, float, str], dict[str, float]] | None,
) -> dict[tuple[str, str], tuple[list[float], list[dict[str, float]]]]:
    """Group fallback greeks by (expiration, type), delta-sorted, so the
    nearest-delta lookups in _find_fallback below are O(log n) via bisect
    instead of a linear scan of the whole lookup for every option."""
    index: dict[tuple[str, str], list[tuple[float, dict[str, float]]]] = {}
    for (exp, d, t), v in (fallback or {}).items():
        index.setdefault((exp, t), []).append((float(d), v))
    out: dict[tuple[str, str], tuple[list[float], list[dict[str, float]]]] = {}
    for key, items in index.items():
        if len(items) > 1:
            items.sort(key=lambda iv: iv[0])
        out[key] = ([d for d, _ in items], [v for _, v in items])
    return out


def _find_fallback(
    index: dict[tuple[str, str], tuple[list[float], list[dict[str, float]]]] | None,
    expiration: str, delta: float, option_type: str,
) -> dict[str, float] | None:
    """Find the closest-delta fallback entry for an option using a
    delta-sorted index from _build_fallback_index."""
    if not index:
        return None
    group = index.get((expiration, option_type))
    if group is None:
        return None
    deltas, vals = group
    # The closest delta is adjacent to the bisect position.
    pos = bisect.bisect_left(deltas, delta)
    best: dict[str, float] | None = None
    best_dist = 999.0
    for i in (pos, pos - 1):
        if 0 <= i < len(deltas):
            dist = abs(deltas[i] - delta)
            if dist < best_dist:
                best_dist = dist
                best = vals[i]
    if best is not None and best_dist < 0.15:
        return best
    return None


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
    fallback: dict[str, float] | None = None,
    _now: datetime | None = None,
) -> Optional[dict[str, Any]]:
    try:
        gamma = opt.get("gamma")
        if (gamma is None or gamma == 0) and fallback is not None:
            gamma = fallback.get("gamma")
        if gamma is None:
            gamma = 0.0
        gamma = float(gamma)

        oi = opt.get("openInterest", 0)
        if oi is None:
            oi = 0
        oi = int(oi)
        if oi <= 0 and fallback is not None:
            oi = int(fallback.get("oi", 0) or 0)

        # Schwab chains carry per-option volume as "totalVolume" (legacy TDA
        # field) or "volume"; accept either so the Volume views work with
        # whichever naming the live API returns.
        volume = opt.get("totalVolume") or opt.get("volume") or 0
        if volume is None:
            volume = 0
        volume = int(volume)
        if volume <= 0 and fallback is not None:
            volume = int(fallback.get("volume", 0) or 0)

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
        if iv is not None and iv < 0:
            iv = 0.0

        mark = opt.get("mark", 0)
        if mark is None:
            mark = 0
        mark = float(mark)

        bid = opt.get("bid", 0)
        if bid is None:
            bid = 0
        bid = float(bid)

        ask = opt.get("ask", 0)
        if ask is None:
            ask = 0
        ask = float(ask)

        if not expiration:
            return None

        try:
            exp_dt = _exp_dt_cache[expiration]
        except KeyError:
            exp_dt = datetime.strptime(expiration, "%Y-%m-%d")
            _exp_dt_cache[expiration] = exp_dt
        days_to_exp = (exp_dt - (_now or datetime.now())).days

        gex = calculate_gex(gamma, oi, spot) if oi > 0 and spot > 0 else 0.0
        vex = (vega * oi * 100 * spot * 0.01) if oi > 0 and spot > 0 and (vega or 0) > 0 else 0.0
        cex = calculate_cex(iv, strike, spot, max(days_to_exp, 1), oi, option_type, r, q) if oi > 0 and spot > 0 else 0.0

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
            "bid": bid,
            "ask": ask,
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
                "call_front_delta": 0.0,
                "put_front_dte": 9999,
                "put_front_iv": 0.0,
                "put_front_delta": 0.0,
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
                strikes_map[sk]["call_front_delta"] = entry.get("delta", 0) or 0
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
                strikes_map[sk]["put_front_delta"] = entry.get("delta", 0) or 0
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
        item["call_delta"] = round(item["call_front_delta"], 4) if item["call_front_dte"] < 9999 else 0.0
        item["put_delta"] = round(item["put_front_delta"], 4) if item["put_front_dte"] < 9999 else 0.0
        result.append(item)

    return result


def aggregate_by_expiration(
    data: list[dict[str, Any]],
    show_calls: bool = True,
    show_puts: bool = True,
    spot: float = 0.0,
) -> list[dict[str, Any]]:
    exp_map: dict[str, dict] = {}
    exp_entries: dict[str, list] = {}

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
            exp_entries[exp] = []

        exp_entries[exp].append(entry)
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

        entries = exp_entries[exp]
        if entries and spot > 0:
            atm_entry = min(entries, key=lambda e: abs(e["strike"] - spot))
            raw_iv = atm_entry.get("iv", 0.0) or 0.0
            if raw_iv <= 0:
                item["atm_iv"] = 0.0
            else:
                item["atm_iv"] = round(raw_iv / 100, 4) if raw_iv > 3 else round(raw_iv, 4)
            item["dte"] = atm_entry.get("days_to_exp", 0)
        else:
            item["atm_iv"] = 0.0
            item["dte"] = 0

        result.append(item)

    return result
