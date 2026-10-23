"""
Black-76 pricing on the forward, vectorised implied vol and Greeks (G4 §5.3).

* Forward = synthetic, from ATM put-call parity (F = K + C - P), with the
  futures price as fallback. Pricing on the forward removes spot/basis bias.
* IV by bisection on the premium (robust near expiry); invalid when the premium
  is at/below forward intrinsic (deep ITM) — delta then defaults to ±0.99.
* Time = calendar years to 15:30 IST on expiry; floor 600 s on expiry day.
  Theta is reported per TRADING minute (the session holds all intraday decay
  from the market's point of view: day theta / 375).
No scipy: the normal CDF uses an erf approximation (|error| < 1.5e-7).
"""
import math
from datetime import datetime

import numpy as np

from . import config

SQRT2 = math.sqrt(2.0)
INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def _erf(x):
    x = np.asarray(x, dtype=float)
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
               + 0.254829592) * t * np.exp(-a * a)
    return s * y


def ncdf(x):
    return 0.5 * (1.0 + _erf(np.asarray(x, dtype=float) / SQRT2))


def npdf(x):
    x = np.asarray(x, dtype=float)
    return INV_SQRT_2PI * np.exp(-0.5 * x * x)


def years_to_expiry(expiry_iso: str, now: datetime) -> float:
    exp = datetime.fromisoformat(expiry_iso).replace(hour=15, minute=30, tzinfo=config.IST)
    secs = (exp - now).total_seconds()
    floor = 600.0 if now.date().isoformat() == expiry_iso else 60.0
    return max(secs, floor) / (365.0 * 86400.0)


def b76_price(F, K, T, sig, is_call):
    F, K, sig = (np.asarray(v, dtype=float) for v in (F, K, sig))
    sig = np.maximum(sig, 1e-4)
    sT = sig * math.sqrt(max(T, 1e-8))
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    d2 = d1 - sT
    call = F * ncdf(d1) - K * ncdf(d2)
    put = K * ncdf(-d2) - F * ncdf(-d1)
    return np.where(is_call, call, put)


def _erf_pos(a):
    """_erf for a >= 0 (the polynomial part; the caller applies the sign). Same arithmetic as _erf."""
    t = 1.0 / (1.0 + 0.3275911 * a)
    return 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
                  + 0.254829592) * t * np.exp(-a * a)


def implied_vol(price, F, K, T, is_call, iters=40):
    """Bisection on the Black-76 premium, 40 iterations (unchanged). T may be a scalar or a per-row
    array (so two expiries can be solved in one call). Bit-identical to the original: the same
    elementwise operations in the same order; log(F/K) and sqrt(T) are hoisted out of the loop (they do
    not depend on the iterate), ncdf(-x) is formed from erf(x) by the sign symmetry the erf approximation
    already has (sign(x) * y), and rows whose premium cannot give an IV are left out of the loop (their
    result is NaN either way)."""
    price = np.asarray(price, dtype=float)
    K = np.asarray(K, dtype=float)
    is_call = np.asarray(is_call, dtype=bool)
    F = np.broadcast_to(np.asarray(F, dtype=float), price.shape)
    intrinsic = np.where(is_call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    valid = (price > intrinsic + 0.05) & (price > 0) & np.isfinite(price)
    out = np.full(price.shape, np.nan)
    if not valid.any():
        return out
    Tv = np.broadcast_to(np.asarray(T, dtype=float), price.shape)[valid]
    pv, Fv, Kv, cv = price[valid], F[valid], K[valid], is_call[valid]
    sqrtT = np.sqrt(np.maximum(Tv, 1e-8))          # math.sqrt(max(T, 1e-8)) per row, correctly rounded
    lnFK = np.log(Fv / Kv)
    lo = np.full(pv.shape, 0.005)
    hi = np.full(pv.shape, 5.0)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        sig = np.maximum(mid, 1e-4)
        sT = sig * sqrtT
        d1 = (lnFK + 0.5 * sT * sT) / sT
        d2 = d1 - sT
        x1, x2 = d1 / SQRT2, d2 / SQRT2
        e1 = np.sign(x1) * _erf_pos(np.abs(x1))
        e2 = np.sign(x2) * _erf_pos(np.abs(x2))
        n1, n2 = 0.5 * (1.0 + e1), 0.5 * (1.0 + e2)          # ncdf(d1), ncdf(d2)
        m1, m2 = 0.5 * (1.0 - e1), 0.5 * (1.0 - e2)          # ncdf(-d1), ncdf(-d2): 1.0 + (-e) == 1.0 - e
        call = Fv * n1 - Kv * n2
        put = Kv * m2 - Fv * m1
        below = np.where(cv, call, put) < pv
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    out[valid] = 0.5 * (lo + hi)
    return out


def greeks(F, K, T, sig, is_call):
    """Returns dict of arrays: delta, gamma, theta_min (premium pts per trading
    minute, negative), vega (pts per vol point)."""
    K = np.asarray(K, dtype=float)
    is_call = np.asarray(is_call, dtype=bool)
    bad = ~np.isfinite(sig)
    s = np.where(bad, 0.15, sig)
    T = np.asarray(T, dtype=float)
    sqT = np.sqrt(np.maximum(T, 1e-8))         # math.sqrt(max(T, 1e-8)), per row when T is an array
    d1 = (np.log(F / K) + 0.5 * s * s * T) / (s * sqT)
    pdf = npdf(d1)
    delta = np.where(is_call, ncdf(d1), ncdf(d1) - 1.0)
    gamma = pdf / (F * s * sqT)
    theta_year = -(F * pdf * s) / (2 * sqT)
    theta_min = theta_year / 365.0 / 375.0
    vega = F * pdf * sqT / 100.0
    itm = np.where(is_call, F > K, K > F)
    delta = np.where(bad & itm, np.where(is_call, 0.99, -0.99), np.where(bad, np.nan, delta))
    for arr in (gamma, theta_min, vega):
        arr[bad] = np.where(itm[bad], 0.0, np.nan)
    return {"delta": delta, "gamma": gamma, "theta_min": theta_min, "vega": vega}


def synthetic_forward(strikes, ce, pe, fallback):
    """F from put-call parity at the strikes nearest the fallback where both legs quote."""
    strikes = np.asarray(strikes, float)
    ce = np.asarray(ce, float)
    pe = np.asarray(pe, float)
    ok = np.isfinite(ce) & np.isfinite(pe) & (ce > 0) & (pe > 0)
    if not ok.any() or not fallback or fallback != fallback:
        return fallback
    idx = np.nonzero(ok)[0]
    near = idx[np.argsort(np.abs(strikes[idx] - fallback))[:2]]
    F = float(np.mean(strikes[near] + ce[near] - pe[near]))
    if fallback and abs(F - fallback) > 150:      # parity broken by stale quotes
        return fallback
    return F
