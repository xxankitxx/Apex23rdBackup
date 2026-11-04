"""Black-76 (r = 0, undiscounted forward) price and Greeks to third order, exact normal CDF (scipy.special.ndtr).

Sign/unit conventions (all per unit of the variable, T in YEARS, sigma as a decimal):
    delta  dV/dF          gamma  d2V/dF2         vega   dV/dsigma
    theta  dV/dt          (calendar time passing, i.e. -dV/dT; negative for a long option)
    vanna  d2V/dF dsigma  vomma  d2V/dsigma2     charm  d(delta)/dt   (time passing)
    speed  d3V/dF3        color  d(gamma)/dt     zomma  d(gamma)/dsigma
    ultima d3V/dsigma3

`real_years` is the true time left (no floor). apex/greeks.py keeps its 600-s solver floor for the IV bisection;
the floor is a numerical guard, not the contract clock, and these functions only floor at 1 s.
"""
import math
from datetime import datetime

import numpy as np
from scipy.special import ndtr

from .. import config

YEAR_S = 365.0 * 86400.0
_SQ2PI = math.sqrt(2.0 * math.pi)
_SQ2 = math.sqrt(2.0)
T_MIN = 1.0 / YEAR_S                 # one second


def real_years(expiry_iso: str, now: datetime) -> float:
    """Calendar years to 15:30 IST on the expiry date, floored at one second (the contract clock)."""
    exp = datetime.fromisoformat(expiry_iso).replace(hour=15, minute=30, tzinfo=config.IST)
    return max((exp - now).total_seconds(), 1.0) / YEAR_S


def _d(F, K, T, sig):
    F, K, T, sig = (np.asarray(v, dtype=float) for v in (F, K, T, sig))
    T = np.maximum(T, T_MIN)
    sig = np.maximum(sig, 1e-4)
    sT = sig * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    return F, K, T, sig, sT, d1, d1 - sT


def price(F, K, T, sig, is_call):
    F, K, T, sig, sT, d1, d2 = _d(F, K, T, sig)
    call = F * ndtr(d1) - K * ndtr(d2)
    put = call - (F - K)                                  # parity, r = 0
    return np.where(np.asarray(is_call, bool), call, put)


def all_greeks(F, K, T, sig, is_call):
    """Dict of arrays: price and every Greek above (see module docstring for units)."""
    is_call = np.asarray(is_call, bool)
    F, K, T, sig, sT, d1, d2 = _d(F, K, T, sig)
    sqT = np.sqrt(T)
    phi = np.exp(-0.5 * d1 * d1) / _SQ2PI
    Nd1 = ndtr(d1)
    call = F * Nd1 - K * ndtr(d2)
    gamma = phi / (F * sT)
    vega = F * phi * sqT
    out = {
        "price": np.where(is_call, call, call - (F - K)),
        "delta": np.where(is_call, Nd1, Nd1 - 1.0),
        "gamma": gamma,
        "vega": vega,
        "theta": -F * phi * sig / (2.0 * sqT),
        "vanna": -phi * d2 / sig,
        "vomma": vega * d1 * d2 / sig,
        "charm": phi * d2 / (2.0 * T),
        "speed": -gamma / F * (1.0 + d1 / sT),
        "color": gamma * (1.0 - d1 * d2) / (2.0 * T),
        "zomma": gamma * (d1 * d2 - 1.0) / sig,
        "ultima": -vega / (sig * sig) * (d1 * d2 * (1.0 - d1 * d2) + d1 * d1 + d2 * d2),
    }
    return out


def taylor(g, dF, dsig, dt_years):
    """Second-order cross expansion of the premium change (the reviews' 'next level' beyond delta-gamma):
    dV ~ delta dF + 1/2 gamma dF^2 + vega dsig + theta dt + vanna dF dsig + 1/2 vomma dsig^2 + charm dF dt."""
    return (g["delta"] * dF + 0.5 * g["gamma"] * dF * dF + g["vega"] * dsig + g["theta"] * dt_years
            + g["vanna"] * dF * dsig + 0.5 * g["vomma"] * dsig * dsig + g["charm"] * dF * dt_years)


def price_s(F, K, T, sig, is_call):
    """Scalar Black-76 price (math.erfc; for hot loops)."""
    T = max(T, T_MIN)
    sig = max(sig, 1e-4)
    sT = sig * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * sT * sT) / sT
    call = F * 0.5 * math.erfc(-d1 / _SQ2) - K * 0.5 * math.erfc(-(d1 - sT) / _SQ2)
    return call if is_call else call - (F - K)


def delta_s(F, K, T, sig, is_call):
    T = max(T, T_MIN)
    sig = max(sig, 1e-4)
    sT = sig * math.sqrt(T)
    n = 0.5 * math.erfc(-((math.log(F / K) + 0.5 * sT * sT) / sT) / _SQ2)
    return n if is_call else n - 1.0


def forward_for_premium(target, K, T, sig, is_call, F_lo, F_hi, iters=60):
    """Forward level at which the option is worth `target` (full repricing; the premium is monotone in F).
    Newton on delta inside the bracket [F_lo, F_hi], bisection whenever a Newton step leaves it.
    Returns NaN when the target is outside [price(F_lo), price(F_hi)]. Scalar inputs."""
    lo, hi = float(F_lo), float(F_hi)
    p_lo, p_hi = price_s(lo, K, T, sig, is_call), price_s(hi, K, T, sig, is_call)
    if not (min(p_lo, p_hi) <= target <= max(p_lo, p_hi)):
        return float("nan")
    x = 0.5 * (lo + hi)
    for _ in range(iters):
        px = price_s(x, K, T, sig, is_call)
        err = px - target
        if abs(err) < 1e-7:
            return x
        if (err < 0) == bool(is_call):                    # price below target on a call -> x too low
            lo = x
        else:
            hi = x
        d = delta_s(x, K, T, sig, is_call)
        nx = x - err / d if abs(d) > 1e-9 else 0.5 * (lo + hi)
        x = nx if lo < nx < hi else 0.5 * (lo + hi)
        if hi - lo < 1e-6:
            return x
    return x
