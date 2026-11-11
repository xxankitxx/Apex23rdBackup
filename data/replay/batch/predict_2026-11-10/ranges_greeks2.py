"""10 Nov 2026, evening (docs/41 section 12.3 follow-up): the translator with a VOLATILITY scenario.

ranges_greeks.py held implied volatility constant and its 10-90 % range covered 74-75 % where 80 % is right.
Here the translator draws JOINT scenarios of (the future's move, the change in the contract's implied volatility):

  - the implied volatility at the horizon is backed out of the observed bid at the horizon (same spread as at the
    origin, the future's observed move, time reduced by the horizon); dv = log(iv_h / iv_0), clipped to +-1
  - a location-scale model for dv on all features, like the one for the future's move
  - 99 training rows drawn once with a fixed seed give 99 PAIRS of standardised residuals (future, volatility), so
    whatever relation the two had on the training days is kept
  - each pair is repriced with Black-76: future = F0 + move, volatility = iv_0 * exp(dv), time reduced

Declared before any result: a forecaster is fit for the live record when its 10-90 % coverage is between 78 % and 82 %
at BOTH horizons; among those, the lower summed tail pinball loss wins; if none qualifies, the direct model stays the
candidate. Same origins, same walk-forward (each test day from earlier days only, at least 5).
Output: data/research/predict/ranges_greeks2.json"""
import json, math, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M, FW, D = z['X'].astype(float), z['M'], z['FW'].astype(float), z['D']
days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
mc = {n: i for i, n in enumerate(z['mcols'])}
ix = {n: i for i, n in enumerate(names)}
H = T.HORIZONS
QS = (0.1, 0.5, 0.9)
NS = 99
MIN = 5
L2 = 10.0
try:
    from scipy.special import ndtr as ncdf
except Exception:
    _erf = np.vectorize(math.erf)
    ncdf = lambda v: 0.5 * (1.0 + _erf(np.asarray(v) / math.sqrt(2.0)))


def b76(Fw, K, Tt, s, call):
    Tt = np.maximum(Tt, 1e-9); s = np.maximum(s, 1e-4)
    v = s * np.sqrt(Tt)
    d1 = (np.log(Fw / K) + 0.5 * v * v) / v
    c = Fw * ncdf(d1) - K * ncdf(d1 - v)
    return np.where(call, c, c - Fw + K)


def implied(mid, Fw, K, Tt, call):
    lo, hi = np.full(len(mid), 1e-3), np.full(len(mid), 5.0)
    for _ in range(50):
        m = 0.5 * (lo + hi)
        up = b76(Fw, K, Tt, m, call) < mid
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
    floor = 0.25 * np.abs(r).mean()
    return mu(Ate), np.maximum(sc(Ate), floor), r / np.maximum(sc(Atr), floor)


def pinball(q, y, a):
    d = y - q
    return float(np.maximum(a * d, (a - 1) * d).mean())


rr = M[:, mc['rr']].astype(int); call = rr == 0; d = np.where(call, 1.0, -1.0)
K = M[:, mc['strike']]; ask0 = X[:, ix['prem']]; sp = X[:, ix['spread_pct']] / 100.0
mid0 = ask0 / (1.0 + sp / 2.0)
Fw0 = K / (1.0 - d * X[:, ix['mny']] / 100.0)
YEAR = 365.0 * 86400.0
Tt0 = (X[:, ix['dte']] * 86400.0 + (1.0 - X[:, ix['tod']]) * 22500.0) / YEAR
iv0 = implied(mid0, Fw0, K, Tt0, call)
MKT = [ix[n] for n in F.MARKET]
expd = X[:, ix['expd']] > 0.5
res = dict(days=days, scenarios=NS, note='discovery material', horizons={})
print('origins', len(X), 'usable implied volatility', int(np.isfinite(iv0).sum()), flush=True)
rng = np.random.default_rng(20261110)
for h in (60, 300):
    c = H.index(h)
    y = M[:, mc[f'ret{h}']]; fw = FW[:, c] * 1.0
    ok = (M[:, mc['st']] == 1) & np.isfinite(y) & np.isfinite(fw) & np.isfinite(iv0) & (Tt0 * YEAR > h + 60)
    Th_all = np.maximum(Tt0 - h / YEAR, 1e-9)
    mid_h = (1.0 + y) * ask0 / (1.0 - sp / 2.0)
    with np.errstate(all='ignore'):
        iv_h = implied(np.nan_to_num(mid_h, nan=-1.0), Fw0 + np.nan_to_num(fw), K, Th_all, call)
        dv = np.clip(np.log(iv_h / iv0), -1.0, 1.0)
    okv = ok & np.isfinite(dv)
    print(h, 'origins', int(ok.sum()), 'with an implied volatility at the horizon', int(okv.sum()),
          'median |dv|', round(float(np.nanmedian(np.abs(dv[okv]))), 4), flush=True)
    Q = {k: np.full((len(X), 3), np.nan) for k in ('C', 'B', 'A', 'V')}
    for dd in range(MIN, len(days)):
        tr, te, trv = ok & (D < dd), ok & (D == dd), okv & (D < dd)
        if te.sum() == 0:
            continue
        Q['C'][te] = np.quantile(y[tr], QS)
        mu, s, zz = loc_scale(X[tr], y[tr], X[te])
        Q['B'][te] = mu[:, None] + s[:, None] * np.quantile(zz, QS)[None, :]
        fs = fw * d
        # joint residual pairs come from the rows where both are known
        mu_f, s_f, zf = loc_scale(X[trv][:, MKT], fs[trv], X[te][:, MKT])
        mu_v, s_v, zv = loc_scale(X[trv], dv[trv], X[te])
        pick = rng.choice(len(zf), NS, replace=False)
        Kt, ct, Tt = K[te][:, None], call[te][:, None], Th_all[te][:, None]
        to_ret = lambda pr: pr * (1.0 - sp[te][:, None] / 2.0) / ask0[te][:, None] - 1.0
        Fh = Fw0[te][:, None] + (mu_f[:, None] + s_f[:, None] * zf[pick][None, :]) * d[te][:, None]
        # constant volatility, same scenarios of the future: the old translator on the new draw
        Q['A'][te] = np.quantile(to_ret(b76(Fh, Kt, Tt, iv0[te][:, None], ct)), QS, axis=1).T
        ivs = iv0[te][:, None] * np.exp(np.clip(mu_v[:, None] + s_v[:, None] * zv[pick][None, :], -1.0, 1.0))
        Q['V'][te] = np.quantile(to_ret(b76(Fh, Kt, Tt, ivs, ct)), QS, axis=1).T
    m = ok & np.isfinite(Q['B'][:, 0])
    out = dict(n=int(m.sum()))
    for lab, sub in (('all', m), ('expiry_day', m & expd), ('other_days', m & ~expd)):
        row = {}
        for k, nm in (('C', 'baseline'), ('B', 'direct'), ('A', 'translator'), ('V', 'translator_vol')):
            q = Q[k][sub]; yy = y[sub]
            row[nm] = dict(pinball10=round(pinball(q[:, 0], yy, 0.1), 5), pinball50=round(pinball(q[:, 1], yy, 0.5), 5),
                           pinball90=round(pinball(q[:, 2], yy, 0.9), 5),
                           coverage_10_90=round(float(((yy >= q[:, 0]) & (yy <= q[:, 2])).mean()), 4),
                           median_width=round(float(np.median(q[:, 2] - q[:, 0])), 4))
        out[lab] = dict(n=int(sub.sum()), **row)
        print(h, lab, int(sub.sum()), flush=True)
        for nm, v in row.items():
            print('   ', f'{nm:15s}', v['pinball10'], v['pinball50'], v['pinball90'], 'cover', v['coverage_10_90'], 'width', v['median_width'], flush=True)
    res['horizons'][str(h)] = out
fit = {}
for nm in ('baseline', 'direct', 'translator', 'translator_vol'):
    cov = [res['horizons'][str(h)]['all'][nm]['coverage_10_90'] for h in (60, 300)]
    tail = sum(res['horizons'][str(h)]['all'][nm][k] for h in (60, 300) for k in ('pinball10', 'pinball90'))
    fit[nm] = dict(coverage=cov, tail_loss=round(tail, 5), qualifies=all(0.78 <= c <= 0.82 for c in cov))
q = [k for k, v in fit.items() if v['qualifies'] and k != 'baseline']
res['selection'] = dict(rule='coverage 78-82 % at both horizons, then lowest summed tail pinball; else direct', table=fit,
                        chosen=(min(q, key=lambda k: fit[k]['tail_loss']) if q else 'direct'))
print('selection', json.dumps(res['selection'], indent=1), flush=True)
json.dump(res, open(os.path.join(OUT, 'ranges_greeks2.json'), 'w'), indent=1)
