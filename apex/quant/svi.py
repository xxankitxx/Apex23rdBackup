"""Raw-SVI smile per snapshot (Gatheral):  w(k) = a + b ( rho (k - m) + sqrt((k - m)^2 + s^2) ),
w = total implied variance iv^2 T, k = ln(K / F).

Calibration: the quasi-explicit method (Zeliade, 2009). For fixed (m, s) write y = (k - m) / s; then
w = a + d y + c sqrt(y^2 + 1) with c = b s, d = rho b s, which is LINEAR in (a, d, c). A coarse-to-fine grid over
(m, s) solves every linear least-squares problem at once (batched 3x3 normal equations), keeps the admissible
solutions (c >= 0, |d| <= c, a + c sqrt(1 - (d/c)^2) >= 0 so w >= 0) and returns the best. No iterative optimiser,
about a millisecond per smile, deterministic.

`residual` = market IV minus fitted IV, in vol points: a strike well above its smile is rich, well below is cheap.
"""
import numpy as np


def svi_w(p, k):
    a, b, rho, m, s = p
    d = k - m
    return a + b * (rho * d + np.sqrt(d * d + s * s))


def _solve(k, w, M, S):
    """Batched quasi-explicit step: for each grid pair (M[g], S[g]) the LS (a, d, c); returns params and SSE."""
    y = (k[None, :] - M[:, None]) / S[:, None]                    # (G, n)
    z = np.sqrt(y * y + 1.0)
    X = np.stack([np.ones_like(y), y, z], axis=2)                 # (G, n, 3)
    A = np.einsum("gni,gnj->gij", X, X) + 1e-12 * np.eye(3)[None]
    rhs = np.einsum("gni,n->gi", X, w)
    sol = np.linalg.solve(A, rhs[..., None])[..., 0]              # (G, 3): a, d, c
    a, d, c = sol[:, 0], sol[:, 1], sol[:, 2]
    sse = np.sum((np.einsum("gni,gi->gn", X, sol) - w[None, :]) ** 2, axis=1)
    ok = (c > 1e-12) & (np.abs(d) <= c) & (a + c * np.sqrt(np.maximum(1 - (d / np.maximum(c, 1e-12)) ** 2, 0)) >= 0)
    sse = np.where(ok, sse, np.inf)
    return a, d, c, sse


def fit(strikes, iv, F, T, prev=None):
    """strikes, iv (decimal) arrays; returns params (a, b, rho, m, s) or None with fewer than 5 good quotes.
    `prev` is accepted for API compatibility (the grid search needs no starting point)."""
    K = np.asarray(strikes, float)
    v = np.asarray(iv, float)
    ok = np.isfinite(K) & np.isfinite(v) & (v > 0.01) & (v < 3.0)
    if ok.sum() < 5 or not (F > 0 and T > 0):
        return None
    k = np.log(K[ok] / F)
    w = v[ok] ** 2 * T
    span = max(float(np.ptp(k)), 1e-4)
    mc, sc = 0.0, span / 2
    best = None
    for zoom in (1.0, 0.25, 0.06):                                # coarse-to-fine around the best (m, s)
        Mg = mc + zoom * span * np.linspace(-1.0, 1.0, 15)
        Sg = np.clip(sc * np.exp(zoom * 2.0 * np.linspace(-1.5, 1.5, 15)), 1e-4, 1.0)
        M, S = (x.ravel() for x in np.meshgrid(Mg, Sg))
        a, d, c, sse = _solve(k, w, M, S)
        g = int(np.argmin(sse))
        if not np.isfinite(sse[g]):
            continue
        if best is None or sse[g] <= best[0]:
            best = (float(sse[g]), float(a[g]), float(d[g]), float(c[g]), float(M[g]), float(S[g]))
        mc, sc = best[4], best[5]
    if best is None:
        return None
    _, a, d, c, m, s = best
    b = c / s
    return np.array([a, b, d / c, m, s])


def iv_at(p, strikes, F, T):
    k = np.log(np.asarray(strikes, float) / F)
    return np.sqrt(np.maximum(svi_w(p, k), 0.0) / T)


def residual(p, strikes, iv, F, T):
    """Market IV minus smile IV, vol points (x100)."""
    return 100.0 * (np.asarray(iv, float) - iv_at(p, strikes, F, T))
