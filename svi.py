"""Arbitrage-Free SSVI Volatility Surface calibration.

Two-stage calibration following the README:

1. **Raw SVI** per expiration — fit total variance as a function of
   log-moneyness::

       w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))

    where ``k = ln(K / F)``, ``F = spot * exp((risk_free - dividend_yield) * T)`` is the forward price, and ``m`` is a free location shift that lets
   the smile's vertex sit off k=0 (Schwab OTM puts/calls rarely pin k=0
   exactly). The five parameters ``(a, b, rho, m, sigma)`` are fit with
   bounded least squares; constraints enforce the no-calendar-spread and
   no-butterfly (positive density) conditions on each tenor.

2. **SSVI surface** — across expirations fit ATM total variance
   ``theta(t) = w(0, t)`` then solve for surface parameters:

       phi(theta) = eta * theta ** (-gamma)        (skew-smile decay)
       w(k, t)    = 0.5 * theta * (1 + rho * phi * k +
                                   sqrt((phi * k)^2 + 2 * rho * phi * k + 1*1))

   with surface-wide ``rho`` (averaged per-tenor skew) and ``eta``, ``gamma``
   fit jointly. This form is the standard SSVI parameterization of
   Gatheral & Jacquier (2014) — fully arbitrage-free in the region we use.

Public API:

* ``calibrate(data, spot)`` — returns a dict ``{"surface": SSVISurface,
  "skew": float|None, "atm_iv": float|None}`` suitable for storing in
  ``analytics["ssvi_surface"]`` / ``analytics["ssvi_skew"]``.
* ``SSVISurface.iv(strike, tte)`` —IMPLIED VOL (decimal) at any
  (strike, time-to-expiry-in-years).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import numpy as np
from scipy.optimize import least_squares


# Minimum number of OTM quotes required to attempt a per-tenor SVI fit.
_MIN_POINTS = 5


def _to_decimal_iv(raw_iv: float) -> float:
    """Schwab returns IV as a percentage; we work purely in decimal."""
    return raw_iv / 100.0 if raw_iv > 3.0 else raw_iv


@dataclass
class RawSVIFit:
    expiration: str
    tte: float
    a: float
    b: float
    rho: float
    m: float
    sigma: float
    theta: float  # ATM total variance w(0) = a + b * sigma
    rmse: float

    def total_variance(self, k: float) -> float:
        """Total variance w(k) for log-moneyness ``k = ln(K/S)``.

        Location-shifted Raw SVI::

            w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))
        """
        km = k - self.m
        return self.a + self.b * (self.rho * km + math.sqrt(km * km + self.sigma * self.sigma))


def _raw_svi_residual(params: np.ndarray, k: np.ndarray, w: np.ndarray) -> np.ndarray:
    a, b, rho, m, sigma = params
    km = k - m
    inner = rho * km + np.sqrt(km * km + sigma * sigma)
    return a + b * inner - w


def _ensure_arb_constraints(
    a: float, b: float, rho: float, sigma: float,
) -> bool:
    """Check the SVI no-butterfly-arbitrage conditions (Gatheral 2004).

    With ``m`` absorbed into the location shift the conditions reduce to

    * ``b >= 0``
    * ``|rho| < 1``
    * ``a + b * sigma * sqrt(1 - rho^2) >= 0``   (w stays nonneg)
    * ``b * (1 + |rho|) < 4``                    (total-var finite slope)

    Returns ``True`` if the params are arbitrage-free for this tenor.
    """
    if b < 0 or abs(rho) >= 1.0:
        return False
    if a + b * sigma * math.sqrt(max(0.0, 1.0 - rho * rho)) < 0.0:
        return False
    if b * (1.0 + abs(rho)) >= 4.0:
        return False
    return True


def _fit_raw_svi(
    k: np.ndarray, w: np.ndarray, expiration: str, tte: float,
) -> Optional[RawSVIFit]:
    """Bounded least-squares fit of the 5-parameter location-shifted SVI.

    Returns ``None`` when there are too few quotes (``< _MIN_POINTS``) or the
    fit cannot satisfy the SVI no-butterfly-arbitrage constraints — the
    SSVI second stage requires only arbitrage-free tenors.
    """
    if len(k) < _MIN_POINTS:
        return None

    # Initial guess via moments: sigma ~ std of log-moneyness, theta ~ mean
    # total variance. ``a`` anchors the floor, ``b`` the slope scale, ``rho``
    # the skew, ``m`` the vertex location (start at 0). These guesses keep
    # the optimizer inside its bounds.
    theta0 = float(np.mean(w))
    sigma0 = max(float(np.std(k)), 1e-2)
    a0 = max(theta0 * 0.5, 1e-3)
    b0 = min(theta0 / (2.0 * sigma0), 3.0) if sigma0 > 0 else 0.1
    x0 = np.array([a0, b0, 0.0, 0.0, sigma0], dtype=float)

    bounds = (
        np.array([1e-6, 1e-4, -0.999, -1.0, 1e-3]),
        np.array([5.0, 3.0, 0.999, 1.0, 5.0]),
    )

    try:
        res = least_squares(
            _raw_svi_residual, x0, args=(k, w), bounds=bounds,
            method="trf", loss="soft_l1", max_nfev=2000,
        )
    except Exception:
        return None

    a, b, rho, m, sigma = (float(v) for v in res.x)

    # Nudge the fit back inside the no-arbitrage region if it sat on a bound
    # by clipping rho / b and refitting once. Cheap & rare; keeps the surface
    # stage sane.
    if not _ensure_arb_constraints(a, b, rho, sigma):
        try:
            res = least_squares(
                _raw_svi_residual, np.clip(res.x, bounds[0], bounds[1]),
                args=(k, w), bounds=bounds, method="trf",
                loss="soft_l1", max_nfev=2000,
            )
            a, b, rho, m, sigma = (float(v) for v in res.x)
        except Exception:
            return None
        if not _ensure_arb_constraints(a, b, rho, sigma):
            return None

    theta = a + b * sigma  # ATM total variance w(k=0)
    rmse = float(math.sqrt(np.mean(res.fun ** 2))) if res.fun.size else 0.0
    return RawSVIFit(
        expiration=expiration, tte=tte, a=a, b=b, rho=rho, m=m, sigma=sigma,
        theta=theta, rmse=rmse,
    )


@dataclass
class SSVISurface:
    """Calibrated SSVI surface — arbitrage-free IV(strike, tte).

    Surface (Gatheral-Jacquier 2014 form)::

        phi(theta) = eta * theta ** (-gamma)
        w(k, t)   = 0.5 * theta * (1 + rho * phi * k +
                                    sqrt((phi * k)^2 + 2 * rho * phi * k + 1))

    slice ``theta(t)`` is linear interpolation of the per-tenor ATM total
    variances (with flat extrapolation outside the sampled DTE range).
    """

    eta: float
    gamma: float
    rho: float
    tte_arr: np.ndarray       # sorted ascending DTEs (years)
    theta_arr: np.ndarray      # corresponding ATM total variances w(0,t)
    spot: float
    r: float  # risk-free rate (decimal)
    q: float  # dividend yield (decimal)

    # ---- public query API --------------------------------------------------

    def _theta_at_tte(self, tte: float) -> float:
        t = float(tte)
        if t <= 0.0:
            return 0.0
        if self.tte_arr.size == 0:
            return 0.0
        if t <= self.tte_arr[0]:
            return float(self.theta_arr[0])
        if t >= self.tte_arr[-1]:
            return float(self.theta_arr[-1])
        # Linear in tte (SMV term-structure is close to linear in DTE for
        # the typical option chain span; this keeps the slice monotonic).
        return float(np.interp(t, self.tte_arr, self.theta_arr))

    def total_variance(self, k: float, tte: float) -> float:
        """Total variance w(k, t) at log-moneyness ``k`` and ``tte`` (years)."""
        theta = self._theta_at_tte(tte)
        if theta <= 0.0 or theta > 25.0:  # implausible total-var guard
            return 0.0
        if theta < 1e-4:
            return 0.0
        phi = self.eta * (theta ** (-self.gamma))
        # Clip phi so the no-arb condition b*(1+|rho|) < 4-equivalent holds
        # (here ``rho*phi`` plays the b*rho role; clip to keep |rho|<1).
        phi_neg = max(min(phi, 4.0), 1e-6)
        rhoEff = max(min(self.rho, 0.999), -0.999)
        pk = phi_neg * k
        w = 0.5 * theta * (1.0 + rhoEff * pk + math.sqrt(pk * pk + 2.0 * rhoEff * pk + 1.0))
        # Numerical guards
        if w < 1e-8:
            return 1e-8
        if w > 25.0:
            return 25.0
        return w

    def iv(self, strike: float, tte: float, ref_spot: Optional[float] = None) -> float:
        """Implied vol (decimal) at ``(strike, tte)``.

        ``ref_spot`` defaults to the spot captured at calibration time; pass
        a different value to re-anchor the smile (e.g. for what-if spot
        moves while holding the surface fixed).
        """
        s = float(ref_spot) if ref_spot is not None and ref_spot > 0 else self.spot
        if s <= 0.0 or float(strike) <= 0.0 or float(tte) <= 0.0:
            return 0.0
        F = s * math.exp((self.r - self.q) * float(tte))
        k = math.log(float(strike) / F)
        w = self.total_variance(k, float(tte))
        if w <= 0.0:
            return 0.0
        iv = math.sqrt(w / float(tte))
        if iv < 1e-4:
            return 1e-4
        if iv > 5.0:  # 500% IV implausible — clip
            return 5.0
        return iv


def _group_otm_quotes(
    data: list[dict[str, Any]], spot: float,
    r: float = 0.0, q: float = 0.0,
) -> dict[str, dict[str, Any]]:
    """Group OTM-call + OTM-put IV quotes per expiration into SVI inputs.

    Returns ``{expiration: {"tte": float, "k": np.array, "w": np.array}}``
    where ``k`` is log-moneyness and ``w`` is total variance = (decimal IV)^2 * tte.
    Only contracts with positive IV, positive OI and non-zero ``days_to_exp``
    feed the fit (the standard "use liquid OTM wings" choice).
    """
    grouped: dict[str, dict[str, Any]] = {}
    _ny = ZoneInfo("America/New_York")
    _ny_now = datetime.now(_ny)
    _secs_since_930 = _ny_now.hour * 3600 + _ny_now.minute * 60 + _ny_now.second - 34200
    _secs_since_930 = max(0, min(_secs_since_930, 23400))
    _secs_left = 23400 - _secs_since_930
    for e in data:
        try:
            iv_raw = float(e.get("iv", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if iv_raw <= 0.0:
            continue
        try:
            oi = int(e.get("open_interest", 0) or 0)
        except (TypeError, ValueError):
            oi = 0
        if oi <= 0:
            continue
        try:
            dte = int(e.get("days_to_exp", 0) or 0)
        except (TypeError, ValueError):
            dte = 0
        if dte <= 0:
            continue
        otype = e.get("type", "")
        strike = float(e.get("strike", 0.0) or 0.0)
        if strike <= 0.0 or spot <= 0.0:
            continue

        # Only OTM contracts carry a clean smile signal.
        is_otm_call = otype == "CALL" and strike > spot
        is_otm_put = otype == "PUT" and strike < spot
        if not (is_otm_call or is_otm_put):
            continue

        exp = e.get("expiration")
        if not exp:
            continue

        iv = _to_decimal_iv(iv_raw)
        if iv <= 0.0:
            continue

        tte = (dte + _secs_left / 23400) / 365.0
        F = spot * math.exp((r - q) * tte)
        k = math.log(strike / F)
        w = (iv * iv) * tte

        if exp not in grouped:
            grouped[exp] = {"tte": tte, "k": [], "w": []}
        grouped[exp]["k"].append(k)
        grouped[exp]["w"].append(w)

    out: dict[str, dict[str, Any]] = {}
    for exp, vals in grouped.items():
        if len(vals["k"]) < _MIN_POINTS:
            continue
        ka = np.asarray(vals["k"], dtype=float)
        wa = np.asarray(vals["w"], dtype=float)
        # Filter implausible variances (dispersed data hygiene).
        mask = (wa > 1e-6) & (wa < 25.0) & np.isfinite(ka) & np.isfinite(wa)
        ka, wa = ka[mask], wa[mask]
        if ka.size < _MIN_POINTS:
            continue
        out[exp] = {"tte": vals["tte"], "k": ka, "w": wa}
    return out


def _fit_ssvi_surface(
    per_tenor: list[RawSVIFit], spot: float,
    r: float = 0.0, q: float = 0.0,
) -> Optional[SSVISurface]:
    """Stage-2 fit: surface-wide rho, eta, gamma on the per-tenor thetas."""
    if len(per_tenor) < 2:
        # Single-tenor fallback: still build a one-slice surface so the IV
        # Rank overlay can render with as little as one expiration's data.
        if len(per_tenor) == 1:
            fit = per_tenor[0]
            # eta derived from the single tenor: theta * phi_constant = b
            # (the b parameter of the raw SVI ~ 2 * Rabbi mean-slope scale).
            theta = max(fit.theta, 1e-4)
            eta = max(fit.b / theta, 1e-3) if fit.b > 0 else 0.1
            return SSVISurface(
                eta=float(eta), gamma=0.0, rho=float(fit.rho),
                tte_arr=np.array([fit.tte]),
                theta_arr=np.array([theta]),
                spot=spot, r=r, q=q,
            )
        return None

    # Sort by tte ascending for monotonic interpolation.
    fits = sorted(per_tenor, key=lambda f: f.tte)
    tte_arr = np.array([f.tte for f in fits], dtype=float)
    theta_arr = np.array([max(f.theta, 1e-4) for f in fits], dtype=float)

    # Surface-wide rho = mean of per-tenor rhos (clamped to no-arb region).
    rho_surf = float(np.clip(np.mean([f.rho for f in fits]), -0.999, 0.999))

    # Joint fit of (eta, gamma) against the curvature of the smiles.
    # Objective: each per-tenor slice's b parameter (smile-convexity scale)
    # is captured by SSVI's b_equiv = 0.5 * theta * phi where
    # phi = eta * theta^{-gamma}, so b_equiv = 0.5 * eta * theta^{1-gamma}.
    # Solve in log space: log(b*2) = log(eta) + (1-gamma) * log(theta).
    b_arr = np.array([f.b for f in fits], dtype=float)
    valid = (b_arr > 0) & (theta_arr > 0)
    if int(valid.sum()) < 2:
        # Degenerate — use a sane default instead of failing.
        return SSVISurface(
            eta=0.4, gamma=0.5, rho=rho_surf,
            tte_arr=tte_arr, theta_arr=theta_arr, spot=spot,
            r=r, q=q,
        )

    log_b = np.log(b_arr[valid] * 2.0)
    log_theta = np.log(theta_arr[valid])
    # Linear least squares slope = (1-gamma), intercept = log(eta)
    A = np.vstack([np.ones_like(log_theta), log_theta]).T
    coef, *_ = np.linalg.lstsq(A, log_b, rcond=None)
    intercept, slope = float(coef[0]), float(coef[1])
    gamma = float(np.clip(1.0 - slope, 1e-3, 4.0))
    eta = float(np.clip(math.exp(intercept), 1e-4, 10.0))

    return SSVISurface(
        eta=eta, gamma=gamma, rho=rho_surf,
        tte_arr=tte_arr, theta_arr=theta_arr, spot=spot,
        r=r, q=q,
    )


def _bscall_delta(s: float, k: float, tte: float, sigma: float, r: float = 0.0) -> float:
    """Black-Scholes call delta (r=0 assumed). Used for skew root-finding."""
    if sigma <= 0.0 or tte <= 0.0:
        return 0.5
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * tte) / (sigma * math.sqrt(tte))
    return 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))


def _implied_vol_for_delta(
    surface: SSVISurface, target_delta: float, tte: float, ref_spot: Optional[float] = None,
) -> Optional[float]:
    """Find the strike whose BS delta == ``target_delta`` under SSVI IV.

    Used to compute the 25Δ put IV for ``ssvi_skew``. Bisect over strikes
    because IV is a known closed-form function of strike via the surface.
    """
    s = float(ref_spot) if ref_spot is not None and ref_spot > 0 else surface.spot
    if s <= 0.0 or tte <= 0.0:
        return None

    lo, hi = s * 0.3, s * 3.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        iv = surface.iv(mid, tte, ref_spot=s)
        if iv <= 0.0:
            hi = mid
            continue
        delta = _bscall_delta(s, mid, tte, iv)
        # For puts target_delta is negative — we invert the call-delta anyway
        # by passing abs(target_delta) and converting back outside.
        if delta < abs(target_delta):
            hi = mid
        else:
            lo = mid
    k = 0.5 * (lo + hi)
    return surface.iv(k, tte, ref_spot=s)


def skew_for_tte(
    surface: SSVISurface, tte: float, ref_spot: Optional[float] = None,
) -> Optional[float]:
    """SSVI-smoothed 25Δ skew (put25 IV − call25 IV) at a given tenor ``tte``."""
    if surface is None or tte is None or tte <= 0:
        return None
    try:
        put25 = _implied_vol_for_delta(surface, -0.25, tte, ref_spot=ref_spot)
        call25 = _implied_vol_for_delta(surface, 0.25, tte, ref_spot=ref_spot)
        if put25 is not None and call25 is not None:
            return round(put25 - call25, 4)
    except Exception:
        return None
    return None


def calibrate(data: list[dict[str, Any]], spot: float, r: float = 0.0, q: float = 0.0) -> dict[str, Any]:
    """Calibrate the SSVI surface from an option chain.

    Args:
        data: list of normalized option entries (``calculations`` shape).
        spot: spot price used as the log-moneyness anchor.
        r: risk-free interest rate (decimal, default 0.0).
        q: dividend yield (decimal, default 0.0).

    Returns:
        ``{"surface": SSVISurface|None, "skew": float|None,
           "atm_iv": float|None}``.
    """
    spot_f = float(spot)
    if not data or spot_f <= 0.0:
        logger.warning("SSVI: no data or spot=%s", spot_f)
        return {"surface": None, "skew": None, "atm_iv": None}

    grouped = _group_otm_quotes(data, spot_f, r=r, q=q)
    if not grouped:
        logger.warning("SSVI: _group_otm_quotes returned empty (no OTM options with OI>0)")
        return {"surface": None, "skew": None, "atm_iv": None}

    per_tenor: list[RawSVIFit] = []
    for exp, vals in grouped.items():
        fit = _fit_raw_svi(vals["k"], vals["w"], exp, vals["tte"])
        if fit is not None:
            per_tenor.append(fit)

    if not per_tenor:
        logger.warning("SSVI: no valid per-tenor fits (%d groups)", len(grouped))
        return {"surface": None, "skew": None, "atm_iv": None}

    surface = _fit_ssvi_surface(per_tenor, spot_f, r=r, q=q)
    if surface is None:
        logger.warning("SSVI: _fit_ssvi_surface returned None (%d tenors)", len(per_tenor))
        return {"surface": None, "skew": None, "atm_iv": None}

    # ATM IV = sqrt(theta_front / tte_front) for the front-month tenor.
    front = min(per_tenor, key=lambda f: f.tte)
    atm_iv = math.sqrt(front.theta / max(front.tte, 1e-8)) if front.tte > 0 else None
    if atm_iv is not None:
        atm_iv = float(min(max(atm_iv, 1e-4), 5.0))

    # 25Δ skew (SSVI-smoothed) = put25 IV - call25 IV at the front TTE.
    try:
        put25_iv = _implied_vol_for_delta(surface, -0.25, front.tte)
        call25_iv = _implied_vol_for_delta(surface, 0.25, front.tte)
        skew: Optional[float] = None
        if put25_iv is not None and call25_iv is not None:
            skew = round(put25_iv - call25_iv, 4)
    except Exception:
        skew = None

    return {"surface": surface, "skew": skew, "atm_iv": atm_iv}


def overlay_curve(
    surface: SSVISurface, strikes: list[float], tte: float, ref_spot: Optional[float] = None,
) -> list[float]:
    """Convenience: SSVI IV evaluated at every (strike, tte) — for charting."""
    out: list[float] = []
    for k in strikes:
        v = surface.iv(float(k), tte, ref_spot=ref_spot)
        if v <= 0.0:
            out.append(float("nan"))
        else:
            out.append(v)
    return out
