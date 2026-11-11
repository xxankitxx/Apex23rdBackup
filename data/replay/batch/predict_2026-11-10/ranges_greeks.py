"""10 Nov 2026 (docs/40 sections 3 and 4, docs/41 section 12): premium-return RANGES, and whether translating a
forecast of the underlying through the option's own pricing (Greeks / full repricing) beats forecasting the premium
directly.

Same origins, same walk-forward (each test day from earlier days only, at least 5). Horizons 60 s and 300 s.
The quantity forecast: the quote-aware return bid_h / ask_0 - 1 of the FIXED contract (only origins where the bid at
the horizon was observed). Quantiles 10 %, 50 %, 90 %.

Three forecasters, declared here before any result:
  C  baseline     the training days' unconditional quantiles
  B  direct       location-scale on the premium return: ridge for the mean, ridge for the mean absolute residual,
                  quantiles = mean + scale x the training residuals' standardised quantiles
  A  translator   the same location-scale model, but for the INDEX FUTURE's move over the horizon (market features
                  only). 19 equally likely scenarios of that move are repriced with Black-76 at the origin's implied
                  volatility (held constant: an explicit limit), time reduced by the horizon, and turned into the same
                  quote-aware return with the origin's spread. Also reported: the delta-only and delta-gamma-theta
                  approximations of the median, against full repricing.
Scores: pinball loss per quantile (lower is better), coverage and width of the 10-90 % range.
Output: data/research/predict/ranges_greeks.json"""
import json, math, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M, FW, D = z['X'].astype(float), z['M'], z['FW'].astype(float), z['D']
days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
mc = {n: i for i, n in enumerate(z['mcols'])}
ix = {n: i for i, n in enumerate(names)}
H = T.HORIZONS
QS = (0.1, 0.5, 0.9)
ZG = (np.arange(19) + 0.5) / 19.0
MIN = 5
L2 = 10.0
SQ2 = math.sqrt(2.0)
ncdf = np.vectorize(lambda v: 0.5 * (1.0 + math.erf(v / SQ2)))


def b76(Fw, K, Tt, s, call):
    """Black-76 with zero rate. Arrays. Returns price, delta (dV/dF), gamma, theta per second."""
    Tt = np.maximum(Tt, 1e-9); s = np.maximum(s, 1e-4)
    v = s * np.sqrt(Tt)
    d1 = (np.log(Fw / K) + 0.5 * v * v) / v
    d2 = d1 - v
    c = Fw * ncdf(d1) - K * ncdf(d2)
    p = c - Fw + K
    pdf = np.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    delta = np.where(call, ncdf(d1), ncdf(d1) - 1.0)
    gamma = pdf / (Fw * v)
    theta = -Fw * pdf * s / (2 * np.sqrt(Tt))
    return np.where(call, c, p), delta, gamma, theta


def implied(mid, Fw, K, Tt, call):
    lo, hi = np.full(len(mid), 1e-3), np.full(len(mid), 5.0)
    for _ in range(50):
        m = 0.5 * (lo + hi)
        pr = b76(Fw, K, Tt, m, call)[0]
        up = pr < mid
        lo, hi = np.where(up, m, lo), np.where(up, hi, m)
    iv = 0.5 * (lo + hi)
    intrinsic = np.maximum(np.where(call, Fw - K, K - Fw), 0.0)
    return np.where((mid > intrinsic + 0.05) & (iv < 4.9) & (iv > 2e-3), iv, np.nan)


def ridge(A, y, l2=L2):
    med = np.nanmedian(A, 0); sd = np.nanstd(A, 0); sd = np.where(sd > 0, sd, 1.0)
    Z = np.c_[np.ones(len(A)), np.clip(np.nan_to_num((A - med) / sd), -4, 4)]
    P = l2 * np.eye(Z.shape[1]); P[0, 0] = 0
    w = np.linalg.solve(Z.T @ Z + P, Z.T @ y)
    return lambda B: np.c_[np.ones(len(B)), np.clip(np.nan_to_num((B - med) / sd), -4, 4)] @ w


def loc_scale(Atr, ytr, Ate):
    mu = ridge(Atr, ytr)
    r = ytr - mu(Atr)
    sc = ridge(Atr, np.abs(r))
    s_tr = np.maximum(sc(Atr), 0.25 * np.abs(r).mean())
    zz = r / s_tr
    return mu(Ate), np.maximum(sc(Ate), 0.25 * np.abs(r).mean()), zz


def pinball(q, y, a):
    d = y - q
    return float(np.maximum(a * d, (a - 1) * d).mean())


rr = M[:, mc['rr']].astype(int); call = rr == 0; d = np.where(call, 1.0, -1.0)
K = M[:, mc['strike']]; ask0 = X[:, ix['prem']]; sp = X[:, ix['spread_pct']] / 100.0
mid0 = ask0 / (1.0 + sp / 2.0)
Fw0 = K / (1.0 - d * X[:, ix['mny']] / 100.0)
Tt0 = (X[:, ix['dte']] * 86400.0 + (1.0 - X[:, ix['tod']]) * 22500.0) / (365.0 * 86400.0)
iv0 = implied(mid0, Fw0, K, Tt0, call)
MKT = [ix[n] for n in F.MARKET]
res = dict(days=days, note='discovery material; IV held constant in the translator', horizons={})
print('origins', len(X), 'with a usable implied volatility', int(np.isfinite(iv0).sum()), 'median IV', round(float(np.nanmedian(iv0)), 3), flush=True)
for h in (60, 300):
    c = H.index(h)
    y = M[:, mc[f'ret{h}']]; fw = FW[:, c] * 1.0
    ok = (M[:, mc['st']] == 1) & np.isfinite(y) & np.isfinite(fw) & np.isfinite(iv0) & (Tt0 * 365 * 86400 > h + 60)
    Q = {k: np.full((len(X), 3), np.nan) for k in 'ABC'}
    med_delta = np.full(len(X), np.nan); med_dgt = np.full(len(X), np.nan); med_full = np.full(len(X), np.nan)
    for dd in range(MIN, len(days)):
        tr, te = ok & (D < dd), ok & (D == dd)
        if te.sum() == 0:
            continue
        Q['C'][te] = np.quantile(y[tr], QS)
        mu, s, zz = loc_scale(X[tr], y[tr], X[te])
        Q['B'][te] = mu[:, None] + s[:, None] * np.quantile(zz, QS)[None, :]
        # A: the future's own move (signed by nothing: market features are unsigned on calls; use the signed set times d)
        fs = fw * d                                           # the move "with the trade", so signed features apply
        mu_f, s_f, zf = loc_scale(X[tr][:, MKT], fs[tr], X[te][:, MKT])
        scen = mu_f[:, None] + s_f[:, None] * np.quantile(zf, ZG)[None, :]          # 19 scenarios, with the trade
        dF = scen * d[te][:, None]
        n = te.sum()
        Fh = Fw0[te][:, None] + dF
        Th = np.maximum(Tt0[te] - h / (365.0 * 86400.0), 1e-9)[:, None]
        pr = b76(Fh, K[te][:, None], Th, iv0[te][:, None], call[te][:, None])[0]
        bid_h = pr * (1.0 - sp[te][:, None] / 2.0)
        ret = bid_h / ask0[te][:, None] - 1.0
        Q['A'][te] = np.quantile(ret, QS, axis=1).T
        p0, dl, gm, th = b76(Fw0[te], K[te], Tt0[te], iv0[te], call[te])
        m_dF = np.median(dF, axis=1)
        to_ret = lambda mid: mid * (1.0 - sp[te] / 2.0) / ask0[te] - 1.0
        med_full[te] = np.median(ret, axis=1)
        med_delta[te] = to_ret(p0 + dl * m_dF)
        med_dgt[te] = to_ret(p0 + dl * m_dF + 0.5 * gm * m_dF ** 2 + th * (h / (365.0 * 86400.0)))
    m = ok & np.isfinite(Q['B'][:, 0])
    expd = X[:, ix['expd']] > 0.5
    out = dict(n=int(m.sum()))
    for lab, sub in (('all', m), ('expiry_day', m & expd), ('other_days', m & ~expd)):
        row = {}
        for k, nm in (('C', 'baseline'), ('B', 'direct'), ('A', 'translator')):
            q = Q[k][sub]; yy = y[sub]
            row[nm] = dict(pinball10=round(pinball(q[:, 0], yy, 0.1), 5), pinball50=round(pinball(q[:, 1], yy, 0.5), 5),
                           pinball90=round(pinball(q[:, 2], yy, 0.9), 5),
                           coverage_10_90=round(float(((yy >= q[:, 0]) & (yy <= q[:, 2])).mean()), 4),
                           median_width=round(float(np.median(q[:, 2] - q[:, 0])), 4))
        out[lab] = dict(n=int(sub.sum()), **row)
        print(h, lab, int(sub.sum()), {k: (v['pinball10'], v['pinball50'], v['pinball90'], v['coverage_10_90'], v['median_width']) for k, v in row.items()}, flush=True)
    e = lambda a: round(float(np.mean(np.abs(a[m] - y[m]))), 5)
    out['median_abs_error'] = dict(full_repricing=e(med_full), delta_only=e(med_delta), delta_gamma_theta=e(med_dgt), direct=e(Q['B'][:, 1]),
                                   baseline=e(Q['C'][:, 1]))
    out['approximation_gap_vs_full'] = dict(delta_only=round(float(np.mean(np.abs(med_delta[m] - med_full[m]))), 5),
                                            delta_gamma_theta=round(float(np.mean(np.abs(med_dgt[m] - med_full[m]))), 5))
    print(h, 'median abs error', out['median_abs_error'], 'gap vs full', out['approximation_gap_vs_full'], flush=True)
    res['horizons'][str(h)] = out
json.dump(res, open(os.path.join(OUT, 'ranges_greeks.json'), 'w'), indent=1)
