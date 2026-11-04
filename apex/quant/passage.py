"""Premium outcome model: will this option reach its TARGET before its STOP, and how soon?

The reviews' central question ("which option has the highest probability of a meaningful, immediate premium gain
before an unacceptable adverse move") as one closed-form calculation:

1. Full Black-76 repricing (greeks_hi) turns the premium target P0 (1 + up) and stop P0 (1 - dn) into forward
   levels F_up and F_dn: gamma convexity is exact, not a Taylor guess.
2. In the trade's favourable direction the forward is modelled as Brownian motion with drift mu (pts/s, e.g. a
   Kalman velocity) and noise s (pts/sqrt(s), e.g. jump-robust bipower vol). Time decay is folded into the drift:
   the premium loses |theta| per second, which the forward must make up at |delta|, so the effective drift is
   mu - |theta_s| / |delta|.
3. Two absorbing barriers, a = |F_up - F| above and b = |F - F_dn| below: the exit-time densities by the method of
   images (driftless series) times the Girsanov factor for the drift, integrated over [0, h] for every horizon.

Outputs (all probabilities): up_by[h] = target first within h seconds, dn_by[h] = stop first within h,
up_ever = target before stop eventually (scale function), and the barrier distances themselves.
"""
import math

import numpy as np

from . import greeks_hi as G

_K = np.arange(-4, 5)                     # image terms (t < L^2/s^2): the k-th is ~exp(-2 k^2), k=4 -> 1e-14
_SQ2PI = math.sqrt(2.0 * math.pi)


def up_first_ever(a, b, mu, s):
    """P(hit +a before -b) for X = mu t + s W, X0 = 0 (scale function)."""
    if a <= 0:
        return 1.0
    if b <= 0:
        return 0.0
    th = 2.0 * mu / (s * s)
    if abs(th) * max(a, b) < 1e-9:
        return b / (a + b)
    # (1 - e^{th b}) / (e^{-th a} - e^{th b}), written stably for either sign of th
    if th > 0:
        num = -math.expm1(-th * b)                # (1 - e^{-th b}) after multiplying through by e^{-th b}
        den = math.exp(-th * (a + b)) * -1.0 + 1.0
        return num / den
    if -th * a > 700.0:                           # overwhelming headwind: the target is never reached first
        return 0.0
    num = -math.expm1(th * b)
    den = math.exp(-th * a) - math.exp(th * b)
    return num / den


_N = np.arange(1, 9)                      # eigen-terms (t >= L^2/s^2): the n-th is ~exp(-n^2 pi^2 / 2), n=8 -> 1e-137


def _exit_density(c, L, mu, s, t, sign):
    """Density at times t of exiting through the barrier at distance c (in direction `sign`) before the other one,
    interval width L, for X = mu t + s W. Driftless density times the Girsanov factor
    exp(sign mu c / s^2 - mu^2 t / (2 s^2)). The driftless density uses the method of images for short times
    (t < L^2 / s^2, where the image series converges in a few terms) and the eigenfunction (Fourier sine) series for
    long times (where the image series converges too slowly and the eigen-series in a few terms)."""
    f = np.empty_like(t)
    short = t < L * L / (s * s)
    if short.any():
        tt = t[short][:, None]
        x = c + 2.0 * _K[None, :] * L
        f[short] = ((x / (s * _SQ2PI * tt ** 1.5)) * np.exp(-(x * x) / (2.0 * s * s * tt))).sum(axis=1)
    if (~short).any():
        tt = t[~short][:, None]
        x0 = L - c                                    # start, measured from the other barrier
        lam = (_N * math.pi / L) ** 2 * s * s / 2.0
        coef = (math.pi * s * s / (L * L)) * _N * np.where(_N % 2 == 1, 1.0, -1.0) * np.sin(_N * math.pi * x0 / L)
        f[~short] = (coef[None, :] * np.exp(-lam[None, :] * tt)).sum(axis=1)
    return f * np.exp(np.clip(sign * mu * c / (s * s) - mu * mu * t / (2.0 * s * s), -700.0, 700.0))


def two_barrier(a, b, mu, s, horizons):
    """Competing-risk profile. Returns (up_by, dn_by) arrays aligned with `horizons` (seconds) and up_ever."""
    horizons = np.asarray(horizons, dtype=float)
    H = float(horizons.max())
    if a <= 0:
        return np.ones_like(horizons), np.zeros_like(horizons), 1.0
    if b <= 0:
        return np.zeros_like(horizons), np.ones_like(horizons), 0.0
    L = a + b
    lt = np.linspace(math.log(min(H, L * L / (s * s)) * 1e-4), math.log(H), 240)
    t = np.exp(lt)
    fu = _exit_density(a, L, mu, s, t, +1.0) * t          # d/d(log t) form
    fd = _exit_density(b, L, mu, s, t, -1.0) * t
    cu = np.concatenate([[0.0], np.cumsum(0.5 * (fu[1:] + fu[:-1]) * np.diff(lt))])
    cd = np.concatenate([[0.0], np.cumsum(0.5 * (fd[1:] + fd[:-1]) * np.diff(lt))])
    up_by = np.clip(np.interp(np.log(horizons), lt, cu), 0.0, 1.0)
    dn_by = np.clip(np.interp(np.log(horizons), lt, cd), 0.0, 1.0)
    return up_by, dn_by, up_first_ever(a, b, mu, s)


HORIZONS = (60.0, 180.0, 300.0, 600.0, 900.0)


def premium_outcome(F, K, T, sig, is_call, P0, up, dn, mu, s, horizons=HORIZONS, dsig=0.0):
    """The full premium outcome for buying this option at P0 now.

    F forward, K strike, T years left, sig IV (decimal), P0 premium paid, up / dn target and stop as fractions
    (e.g. 0.10 and 0.10), mu forward drift in pts/s (positive = up), s forward noise in pts/sqrt(s), dsig an IV
    scenario applied to the barrier repricing. Returns a dict or None when the barriers cannot be priced."""
    if not (np.isfinite(F) and np.isfinite(sig) and P0 > 0 and s > 0 and T > 0):
        return None
    g = G.all_greeks(F, K, T, sig + dsig, is_call)
    d = float(abs(g["delta"]))
    if d < 1e-3:
        return None
    lo, hi = F * 0.8, F * 1.2
    s_up = G.forward_for_premium(P0 * (1.0 + up), K, T, sig + dsig, is_call, lo, hi)
    s_dn = G.forward_for_premium(P0 * (1.0 - dn), K, T, sig + dsig, is_call, lo, hi)
    if not (np.isfinite(s_up) and np.isfinite(s_dn)):
        return None
    sgn = 1.0 if is_call else -1.0
    a = sgn * (s_up - F)                                  # favourable distance to the target
    b = sgn * (F - s_dn)                                  # adverse distance to the stop
    theta_s = float(g["theta"]) / G.YEAR_S                # premium per second (negative)
    mu_eff = sgn * mu + theta_s / d                       # decay is a headwind the forward must outrun
    up_by, dn_by, up_ever = two_barrier(max(a, 0.0), max(b, 0.0), mu_eff, s, horizons)
    return {"a": a, "b": b, "mu_eff": mu_eff, "up_by": up_by, "dn_by": dn_by, "up_ever": up_ever,
            "horizons": np.asarray(horizons, float), "delta": float(g["delta"]), "theta_s": theta_s}
