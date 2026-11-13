import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R09: lead-lag, relative strength and spread mean reversion between NIFTY, BANKNIFTY, FINNIFTY (futures and spot)
and VIX on the per-second panels in work/R09/sister. Two-fold: fit on one day, score on the other."""
import glob, json, os
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R09\sister"
OUTJ = r"D:\ApexOptions\data\research\13nov\work\R09\leadlag_results.json"
IST = 19800


def load(day):
    ts, Xs, As = [], [], []
    for p in sorted(glob.glob(os.path.join(D, day + "*.npz"))):
        z = np.load(p); ts.append(z["t"]); Xs.append(z["X"]); As.append(z["A"])
    t = np.concatenate(ts); X = np.concatenate(Xs); A = np.concatenate(As)
    o = np.argsort(t); t, X, A = t[o], X[o], A[o]
    keep = np.r_[True, np.diff(t) > 0]
    t, X, A = t[keep], X[keep], A[keep]
    g = np.arange(t[0], t[-1] + 1)                         # fill gaps between parts with nan
    k = np.searchsorted(t, g); ok = (k < len(t)) & (t[np.minimum(k, len(t) - 1)] == g)
    XX = np.full((len(g), X.shape[1]), np.nan); AA = np.full((len(g), A.shape[1]), 1e9)
    XX[ok] = X[k[ok]]; AA[ok] = A[k[ok]]
    return g, XX, AA


def mid(X, A, b, ai):
    m = (X[:, b + 1] + X[:, b + 2]) / 2
    bad = ~(X[:, b + 2] >= X[:, b + 1]) | (A[:, ai] > 5)
    m[bad] = np.nan
    return m


def series(day):
    t, X, A = load(day)
    s = dict(t=t)
    s["NF"] = mid(X, A, 1, 1); s["BF"] = mid(X, A, 5, 3); s["FF"] = mid(X, A, 9, 5)
    s["N"] = np.where(A[:, 0] <= 5, X[:, 0], np.nan); s["BN"] = np.where(A[:, 2] <= 5, X[:, 4], np.nan)
    s["FN"] = np.where(A[:, 4] <= 5, X[:, 8], np.nan); s["VIX"] = np.where(A[:, 6] <= 30, X[:, 12], np.nan)
    hm = ((t + IST) % 86400) / 60.0
    s["hm"] = hm
    q = dict(rows=int(len(t)))
    for k, ai in (("N", 0), ("NF", 1), ("BN", 2), ("BF", 3), ("FN", 4), ("FF", 5), ("VIX", 6)):
        a = A[:, ai]; a = a[a < 1e8]
        q[k] = dict(age_med=float(np.median(a)) if len(a) else None, age_p90=float(np.percentile(a, 90)) if len(a) else None,
                    valid=float(np.isfinite(s[k]).mean()))
        # how often the value changes from one second to the next
        v = s[k]; q[k]["chg_rate"] = float(np.nanmean(np.diff(v) != 0))
    return s, q


def lr(x, h):
    """log return x[t] / x[t-h] (past), aligned at t."""
    out = np.full(len(x), np.nan)
    out[h:] = np.log(x[h:] / x[:-h])
    return out


def fwd(x, h):
    out = np.full(len(x), np.nan)
    out[:-h] = np.log(x[h:] / x[:-h])
    return out


def xcorr(a, b, lags):
    """corr(a[t], b[t+k]) on 1-s returns; k > 0 means a leads b."""
    ra, rb = lr(a, 1), lr(b, 1)
    res = {}
    for k in lags:
        if k >= 0:
            x, y = ra[:len(ra) - k], rb[k:]
        else:
            x, y = ra[-k:], rb[:len(rb) + k]
        m = np.isfinite(x) & np.isfinite(y) & (x != 0) | (np.isfinite(x) & np.isfinite(y) & (y != 0))
        res[k] = float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 100 else None
    return res


def ic(x, y):
    m = np.isfinite(x) & np.isfinite(y) & (x != 0)
    if m.sum() < 200:
        return None, None, 0
    c = float(np.corrcoef(x[m], y[m])[0, 1])
    yy = y[m]; xx = x[m]; nz = yy != 0
    hit = float(np.mean(np.sign(xx[nz]) == np.sign(yy[nz]))) if nz.sum() else None
    return c, hit, int(m.sum())


def ols(Xs, y):
    m = np.isfinite(y) & np.all(np.isfinite(Xs), 1)
    if m.sum() < 200:
        return None
    Z = np.c_[np.ones(m.sum()), Xs[m]]
    b, *_ = np.linalg.lstsq(Z, y[m], rcond=None)
    return b


def pred(b, Xs):
    return b[0] + Xs @ b[1:]


DAYS = ["2026-10-23", "2026-10-27"]
S, Q = {}, {}
for d in DAYS:
    S[d], Q[d] = series(d)
R = dict(quality=Q)
# A. cross-correlation of 1-s returns
lags = list(range(-10, 11))
R["xcorr"] = {}
for d in DAYS:
    s = S[d]
    R["xcorr"][d] = {f"{a}->{b}": xcorr(s[a], s[b], lags) for a, b in
                     (("BF", "NF"), ("FF", "NF"), ("N", "NF"), ("BN", "NF"), ("BF", "BN"), ("NF", "N"), ("BF", "FF"))}
# B. predictive information: future NF return over h on past returns over L, two-fold (fit on one day, score other)
H = [5, 15, 30, 60, 180, 300]
L = [5, 15, 30, 60, 300]
R["predict"] = []
for h in H:
    for Lb in L:
        row = dict(h=h, L=Lb)
        for name, feats in (("own", ["NF"]), ("BF", ["BF"]), ("FF", ["FF"]), ("own+BF", ["NF", "BF"]), ("own+BF+FF", ["NF", "BF", "FF"]),
                            ("RS_bank", "RS"), ("spotgap", "SG")):
            ics, hits, ns = [], [], []
            for fit, test in ((DAYS[0], DAYS[1]), (DAYS[1], DAYS[0])):
                cols = {}
                for dd in (fit, test):
                    s = S[dd]
                    if feats == "RS":                       # bank relative strength: BF return minus beta * NF return
                        a, n_ = lr(s["BF"], Lb), lr(s["NF"], Lb)
                        mm = np.isfinite(a) & np.isfinite(n_)
                        beta = np.sum(a[mm] * n_[mm]) / np.sum(n_[mm] ** 2) if fit == dd else cols.get("beta", 1.0)
                        if fit == dd:
                            cols["beta"] = beta
                        cols[dd] = np.c_[a - beta * n_]
                    elif feats == "SG":                     # Nifty futures past move minus spot past move (who moved first)
                        cols[dd] = np.c_[lr(s["NF"], Lb) - lr(s["N"], Lb)]
                    else:
                        cols[dd] = np.column_stack([lr(s[f], Lb) for f in feats])
                y_fit = fwd(S[fit]["NF"], h); y_test = fwd(S[test]["NF"], h)
                b = ols(cols[fit], y_fit)
                if b is None:
                    continue
                p = pred(b, cols[test])
                c, hit, n = ic(p - b[0], y_test)
                if c is not None:
                    ics.append(c); hits.append(hit); ns.append(n)
            row[name] = dict(ic=round(float(np.mean(ics)), 4) if ics else None, hit=round(float(np.mean(hits)), 4) if hits else None,
                             ics=[round(x, 4) for x in ics])
        R["predict"].append(row)
# B2. incremental value of sisters over own past, by NF realized-vol regime (15-min rv tertiles, two-fold cut points)
R["regime"] = []
for h, Lb in ((15, 15), (30, 30), (60, 60), (60, 15), (180, 60), (300, 300)):
    for d in DAYS:
        s = S[d]
        r1 = lr(s["NF"], 1)
        rv = np.sqrt(np.convolve(np.nan_to_num(r1 ** 2), np.ones(900), "full")[:len(r1)]) * 1e4
        er = np.abs(lr(s["NF"], 900)) * 1e4 / np.maximum(rv, 1e-9)
        y = fwd(s["NF"], h)
        f_own, f_bf, f_ff = lr(s["NF"], Lb), lr(s["BF"], Lb), lr(s["FF"], Lb)
        for rname, mask in (("rv_low", rv < np.nanpercentile(rv[900:], 33)), ("rv_high", rv > np.nanpercentile(rv[900:], 67)),
                            ("trend", er > 0.5), ("chop", er < 0.25), ("all", np.ones(len(y), bool))):
            m = mask.copy(); m[:900] = False
            out = dict(day=d, h=h, L=Lb, regime=rname, n=int(m.sum()))
            for nm, x in (("own", f_own), ("BF", f_bf), ("FF", f_ff), ("BF_minus_NF", f_bf - f_own), ("FF_minus_NF", f_ff - f_own)):
                c, hit, n = ic(np.where(m, x, np.nan), y)
                out[nm] = (round(c, 4) if c is not None else None, round(hit, 4) if hit is not None else None)
            R["regime"].append(out)
# C. spread mean reversion: e = log BF - beta log NF on 60-s samples, beta from the first hour of each day
R["spread"] = {}
for d in DAYS:
    s = S[d]
    st = np.arange(0, len(s["t"]), 60)
    lb, ln, lf = np.log(s["BF"][st]), np.log(s["NF"][st]), np.log(s["FF"][st])
    res = {}
    for nm, la in (("BF", lb), ("FF", lf)):
        dl = np.diff(la); dn = np.diff(ln); m = np.isfinite(dl) & np.isfinite(dn)
        beta = float(np.sum(dl[m] * dn[m]) / np.sum(dn[m] ** 2))
        e = la - beta * ln
        e = e - np.nanmean(e)
        de = np.diff(e); e0 = e[:-1]; mm = np.isfinite(de) & np.isfinite(e0)
        phi = float(np.sum(de[mm] * e0[mm]) / np.sum(e0[mm] ** 2))
        hl = float(-np.log(2) / np.log(1 + phi)) if -1 < phi < 0 else None
        # rolling 30-min z of e (deviation from its own rolling mean), does it predict NF over the next 5/15/30 min?
        k = 30
        rm = np.array([np.nanmean(e[max(0, i - k):i]) if i >= k else np.nan for i in range(len(e))])
        rs = np.array([np.nanstd(e[max(0, i - k):i]) if i >= k else np.nan for i in range(len(e))])
        z = (e - rm) / rs
        pr = {}
        for hh in (5, 15, 30):
            yN = np.full(len(ln), np.nan); yN[:-hh] = ln[hh:] - ln[:-hh]
            yS = np.full(len(e), np.nan); yS[:-hh] = e[hh:] - e[:-hh]
            pr[f"z->NF{hh}m"] = ic(z, yN)[:2]
            pr[f"z->spread{hh}m"] = ic(z, yS)[:2]
        res[nm] = dict(beta=round(beta, 3), phi_per_min=round(phi, 4), half_life_min=round(hl, 1) if hl else None,
                       e_std_bp=round(float(np.nanstd(e)) * 1e4, 1), pred=pr)
    R["spread"][d] = res
# D. VIX change vs next NF move (VIX is a 15-s ish print)
R["vix"] = {}
for d in DAYS:
    s = S[d]; out = {}
    for Lb, h in ((60, 60), (300, 300), (60, 300)):
        dv = np.full(len(s["VIX"]), np.nan); dv[Lb:] = s["VIX"][Lb:] - s["VIX"][:-Lb]
        out[f"dVIX{Lb}->NF{h}"] = ic(dv, fwd(s["NF"], h))[:2]
        out[f"dVIX{Lb}~NF{Lb}"] = ic(dv, lr(s["NF"], Lb))[:2]
    R["vix"][d] = out
json.dump(R, open(OUTJ, "w"), indent=1, default=float)
print(json.dumps(R["quality"], indent=0)[:3000])
for d in DAYS:
    print(d)
    for k, v in R["xcorr"][d].items():
        print(" ", k, {kk: (round(vv, 3) if vv is not None else None) for kk, vv in v.items() if kk in (-5, -3, -2, -1, 0, 1, 2, 3, 5, 10)})
print("predict (two-fold mean IC, hit)")
for r in R["predict"]:
    print(r["h"], r["L"], {k: (v["ic"], v["hit"]) for k, v in r.items() if isinstance(v, dict)})
print("spread", json.dumps(R["spread"]))
print("vix", json.dumps(R["vix"]))
