# Candidate bit-identical implied_vol variants (same elementwise operations, fewer numpy calls).
def _prep(price, F, K, T, is_call):
    price = np.asarray(price, dtype=float); K = np.asarray(K, dtype=float); is_call = np.asarray(is_call, dtype=bool)
    F = np.broadcast_to(np.asarray(F, dtype=float), price.shape)
    intrinsic = np.where(is_call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    valid = (price > intrinsic + 0.05) & (price > 0) & np.isfinite(price)
    out = np.full(price.shape, np.nan)
    if not valid.any(): return None, out, valid
    Tv = np.broadcast_to(np.asarray(T, dtype=float), price.shape)[valid]
    return (price[valid], F[valid], K[valid], is_call[valid], np.sqrt(np.maximum(Tv, 1e-8))), out, valid
def iv_stacked(price, F, K, T, is_call, iters=40):
    pr, out, valid = _prep(price, F, K, T, is_call)
    if pr is None: return out
    pv, Fv, Kv, cv, sqrtT = pr
    lnFK = np.log(Fv / Kv); n = pv.shape[0]
    lo = np.full(pv.shape, 0.005); hi = np.full(pv.shape, 5.0)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        sT = np.maximum(mid, 1e-4) * sqrtT
        d1 = (lnFK + 0.5 * sT * sT) / sT
        x = np.concatenate((d1, d1 - sT)) / SQRT2
        e = np.sign(x) * _erf_pos(np.abs(x))
        nn = 0.5 * (1.0 + e); mm = 0.5 * (1.0 - e)
        below = np.where(cv, Fv * nn[:n] - Kv * nn[n:], Kv * mm[n:] - Fv * mm[:n]) < pv
        lo = np.where(below, mid, lo); hi = np.where(below, hi, mid)
    out[valid] = 0.5 * (lo + hi)
    return out
def iv_inplace(price, F, K, T, is_call, iters=40):
    pr, out, valid = _prep(price, F, K, T, is_call)
    if pr is None: return out
    pv, Fv, Kv, cv, sqrtT = pr
    lnFK = np.log(Fv / Kv); n = pv.shape[0]
    FK = np.concatenate((Fv, Kv)); KF = np.concatenate((Kv, Fv))
    lo = np.full(n, 0.005); hi = np.full(n, 5.0)
    mid = np.empty(n); sT = np.empty(n); d = np.empty(2 * n); t = np.empty(2 * n); e = np.empty(2 * n); s = np.empty(2 * n)
    for _ in range(iters):
        np.add(lo, hi, out=mid); np.multiply(0.5, mid, out=mid)
        np.maximum(mid, 1e-4, out=sT); np.multiply(sT, sqrtT, out=sT)
        # d1 = (lnFK + 0.5 * sT * sT) / sT ; same order of operations
        np.multiply(0.5, sT, out=d[:n]); np.multiply(d[:n], sT, out=d[:n]); np.add(lnFK, d[:n], out=d[:n]); np.divide(d[:n], sT, out=d[:n])
        np.subtract(d[:n], sT, out=d[n:])
        np.divide(d, SQRT2, out=d)
        np.sign(d, out=s); np.abs(d, out=d)
        # _erf_pos(a): 1.0 - (((((1.061405429*t - 1.453152027)*t) + 1.421413741)*t - 0.284496736)*t + 0.254829592)*t*exp(-a*a), t = 1/(1+0.3275911 a)
        np.multiply(0.3275911, d, out=t); np.add(1.0, t, out=t); np.divide(1.0, t, out=t)
        np.multiply(1.061405429, t, out=e); np.subtract(e, 1.453152027, out=e); np.multiply(e, t, out=e)
        np.add(e, 1.421413741, out=e); np.multiply(e, t, out=e); np.subtract(e, 0.284496736, out=e); np.multiply(e, t, out=e)
        np.add(e, 0.254829592, out=e); np.multiply(e, t, out=e)
        np.negative(d, out=t); np.multiply(t, d, out=t); np.exp(t, out=t); np.multiply(e, t, out=e); np.subtract(1.0, e, out=e)
        np.multiply(s, e, out=e)
        # n = 0.5*(1+e), m = 0.5*(1-e)
        np.add(1.0, e, out=t); np.multiply(0.5, t, out=t)      # t = ncdf(d1), ncdf(d2)
        np.subtract(1.0, e, out=s); np.multiply(0.5, s, out=s)  # s = ncdf(-d1), ncdf(-d2)
        callv = Fv * t[:n] - Kv * t[n:]
        putv = Kv * s[n:] - Fv * s[:n]
        below = np.where(cv, callv, putv) < pv
        lo = np.where(below, mid, lo); hi = np.where(below, hi, mid)
    out[valid] = 0.5 * (lo + hi)
    return out
