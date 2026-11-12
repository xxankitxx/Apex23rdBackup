"""Forecast Lab v2 trainer (11 Nov 2026, docs/50). Fits the brain (apex/forecast_lab/brain.py) on collected sessions
(data/forecast_lab/collect/<day>.joblib, written by `py -3.13 -m apex.forecast_lab.tape collect <day>`).

  py -3.13 research/forecast_lab/train.py walk      for every session with at least MIN_TRAIN earlier ones: fit on the
                                                    earlier sessions only, save brains/brain_<trained through>.joblib,
                                                    score the unseen session; writes walk_forward.json and a table
  py -3.13 research/forecast_lab/train.py final     fit on ALL collected sessions -> data/forecast_lab/brain.joblib
                                                    (what the live runner loads; it has seen every recorded session)
Nightly: collect the new day, then `final`. Nothing here is tuned on a result: one ridge strength per model family,
fixed tree settings.

Models per horizon h in (1, 2, 3, 5, 10, 15, 30 min):
  vol    ridge on standardised features -> log( realised variance over h / (reference variance x h) )
  lin    ridge -> the move divided by the predicted sd
  gbm    gradient-boosted trees (80 trees of depth 3, fixed) -> the same target
  qz     empirical 10/25/50/75/90 % points of move / predicted sd on the training sessions
  volvol half the sd of the log-variance error (the paths' volatility mixture)
  iv     at-the-money IV drift per second by (days-to-expiry bucket, 15-minute bucket), shrunk; the residual noise;
         the skew slide d(strike IV)/d(forward) by moneyness bucket"""
import glob, hashlib, json, os, sys, time
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from apex.forecast_lab import brain as B
LAB = os.path.join(ROOT, 'data', 'forecast_lab')
COL = os.path.join(LAB, 'collect')
H = B.H
MIN_TRAIN = 5
A_VOL, A_LIN = 30.0, 3000.0
QS = (10, 25, 50, 75, 90)


def load(day):
    d = joblib.load(os.path.join(COL, f'{day}.joblib'))
    X = d['X']
    S = d['S']
    t, F, vref, feats = X[:, 0], X[:, 1], X[:, 2], X[:, 3:]
    # targets from the 1-second series
    st, sf = S[:, 0], S[:, 1]
    idx = {int(a): i for i, a in enumerate(st)}
    nH = len(H)
    dF = np.full((len(t), nH), np.nan)
    RV = np.full((len(t), nH), np.nan)
    t5 = np.arange(int(st[0]) - int(st[0]) % 5, int(st[-1]) + 1, 5)
    f5 = np.array([sf[idx[a]] if a in idx else np.nan for a in t5])
    d2 = np.diff(f5) ** 2
    ok2 = np.isfinite(d2)
    c2 = np.r_[0.0, np.cumsum(np.where(ok2, d2, 0.0))]
    cn = np.r_[0, np.cumsum(ok2)]
    pos = {int(a): i for i, a in enumerate(t5)}
    for i, a in enumerate(t):
        a = int(a)
        if a not in pos:
            continue
        p0 = pos[a]
        for j, h in enumerate(H):
            p1 = p0 + h // 5
            if p1 >= len(t5):
                continue
            n = cn[p1] - cn[p0]
            if n >= 0.9 * (h // 5):
                RV[i, j] = (c2[p1] - c2[p0]) * (h / 5) / n
            b = idx.get(a + h)
            if b is not None:
                dF[i, j] = sf[b] - F[i]
    out = dict(day=day, t=t, F=F, vref=vref, X=feats, dF=dF, RV=RV, IVT=d['IVT'], IVM=d['IVM'])
    out['ivs'] = iv_stats(out)
    return out


def iv_stats(d):
    """One session's sums for the IV tables (computed once per session, combined per fold)."""
    nb = len(B.MNY_EDGES) + 1
    st = dict(dsum=np.zeros((3, B.N_TOD)), dn=np.zeros((3, B.N_TOD)), sxx=np.zeros((3, nb)), sxy=np.zeros((3, nb)),
              axx=np.zeros(3), axy=np.zeros(3), rows=[])
    T = d['IVT']
    if len(T) < 30:
        return st
    tt = T[:, 0]
    pos = {int(a): i for i, a in enumerate(tt)}
    for i in range(len(tt)):
        j = pos.get(int(tt[i]) + 60)
        if j is None:
            continue
        k = 0 if T[i, 3] * 365 < 1 else (1 if T[i, 3] * 365 < 3 else 2)
        div, dFs = T[j, 2] - T[i, 2], T[j, 1] - T[i, 1]
        if not np.isfinite(div) or abs(div) > 0.05:
            continue
        b = B.tod_bucket(tt[i])
        st['dsum'][k, b] += div / 60.0; st['dn'][k, b] += 1
        st['axx'][k] += dFs * dFs; st['axy'][k] += dFs * div
        st['rows'].append((k, b, div, dFs))
        Ki, ivi = d['IVM'][i]
        Kj, ivj = d['IVM'][j]
        if len(Ki) == len(Kj) and np.array_equal(Ki, Kj):
            dk = ivj - ivi
            okk = np.isfinite(dk) & (np.abs(dk) < 0.08)
            bb = np.searchsorted(B.MNY_EDGES, np.log(Ki / T[i, 1]))
            cnt = np.bincount(bb[okk], minlength=nb)
            st['sxx'][k] += dFs * dFs * cnt
            st['sxy'][k] += dFs * np.bincount(bb[okk], weights=dk[okk], minlength=nb)
    st['rows'] = np.array(st['rows'], float) if st['rows'] else np.zeros((0, 4))
    return st


def iv_tables(days):
    """IV drift per second by (dte bucket, time-of-day bucket), residual noise, and the skew slide by moneyness."""
    nb = len(B.MNY_EDGES) + 1
    S = [d['ivs'] for d in days]
    dsum, dn = sum(x['dsum'] for x in S), sum(x['dn'] for x in S)
    sxx, sxy = sum(x['sxx'] for x in S), sum(x['sxy'] for x in S)
    axx, axy = sum(x['axx'] for x in S), sum(x['axy'] for x in S)
    rows = np.vstack([x['rows'] for x in S]) if S else np.zeros((0, 4))
    drift = np.zeros((3, B.N_TOD))
    beta = np.zeros((3, nb))
    res = np.full(3, 2e-5)
    b_atm = np.where(axx > 0, axy / np.maximum(axx, 1e-9), -4e-5)
    for k in range(3):
        tot = dn[k].sum()
        mean_k = dsum[k].sum() / tot if tot else 0.0
        drift[k] = (dsum[k] + 40.0 * mean_k) / (dn[k] + 40.0)             # shrink each bucket to the day-type mean
        beta[k] = np.clip((sxy[k] + 2e5 * b_atm[k]) / (sxx[k] + 2e5), -4e-4, 2e-4)
    if len(rows):
        kk, bb = rows[:, 0].astype(int), rows[:, 1].astype(int)
        e = rows[:, 2] - drift[kk, bb] * 60.0 - b_atm[kk] * rows[:, 3]
        for k in range(3):
            m = kk == k
            if m.sum() > 50:
                res[k] = float(np.sqrt(np.mean(e[m] ** 2) / 60.0))
            else:
                res[k] = float(np.sqrt(np.mean(e ** 2) / 60.0))
    for k in range(3):                                                     # a day type never seen: borrow the pooled table
        if dn[k].sum() < 200:
            tot = dn.sum(0)
            drift[k] = np.where(tot > 0, dsum.sum(0) / np.maximum(tot, 1), 0.0) * 0.5
            beta[k] = np.clip(np.where(sxx.sum(0) > 0, sxy.sum(0) / np.maximum(sxx.sum(0), 1e-9), -4e-5), -4e-4, 2e-4)
    return dict(drift=drift.tolist(), beta=beta.tolist(), res=res.tolist())


def fit(days, gbm=True):
    X = np.vstack([d['X'] for d in days])
    dF = np.vstack([d['dF'] for d in days]); RV = np.vstack([d['RV'] for d in days])
    vref = np.concatenate([d['vref'] for d in days])
    last = np.concatenate([np.full(len(d['X']), i == len(days) - 1) for i, d in enumerate(days)])
    med = np.nanmedian(X, 0)
    sd = np.nanstd(X, 0); sd = np.where(sd > 1e-9, sd, 1.0)
    Z = np.clip(np.nan_to_num((X - med) / sd), -6, 6)
    out = dict(feats=B.FEATS, H=H, med=med.tolist(), sd=sd.tolist(), vol=[], lin=[], gbm=[], qz=[], volvol=[])
    for j, h in enumerate(H):
        yv = np.log(np.maximum(RV[:, j], 1e-9) / np.maximum(vref * h, 1e-12))
        ok = np.isfinite(yv) & np.isfinite(RV[:, j])
        m = Ridge(alpha=A_VOL).fit(Z[ok], np.clip(yv[ok], -3, 3))
        out['vol'].append([float(m.intercept_)] + m.coef_.tolist())
        pv = np.clip(m.intercept_ + Z @ m.coef_, -3, 3)
        out['volvol'].append(float(0.5 * np.std((yv - pv)[ok])))
        sdh = np.sqrt(vref * h * np.exp(pv))
        z = dF[:, j] / sdh
        okd = np.isfinite(z)
        zc = np.clip(z, -4, 4)
        ml = Ridge(alpha=A_LIN).fit(Z[okd], zc[okd])
        out['lin'].append([float(ml.intercept_)] + ml.coef_.tolist())
        out['qz'].append([float(q) for q in np.percentile(z[okd], QS)])
        if gbm:                                              # fixed settings, no tuning: small, slow-learning trees
            g = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=80, min_samples_leaf=300,
                                              l2_regularization=5.0, random_state=0).fit(X[okd], zc[okd])
            out['gbm'].append(g)
        else:
            out['gbm'].append(None)
    out['iv'] = iv_tables(days)
    out['meta'] = dict(trained_through=days[-1]['day'], sessions=len(days), days=[d['day'] for d in days],
                       built=time.strftime('%Y-%m-%d %H:%M:%S'), rows=int(len(X)))
    out['meta']['hash'] = hashlib.sha256(json.dumps([out['vol'], out['lin'], out['qz'], out['iv']], sort_keys=True).encode()).hexdigest()[:12]
    return out


def auc(s, y):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
    n1 = y.sum(); n0 = len(y) - n1
    return float((r[y > 0].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else np.nan


def evaluate(obj, d):
    """Unseen-session scores of one brain, straight from the arrays (no online learning: the trained part alone)."""
    br = B.Brain(obj=obj)
    X, dF, RV, vref = d['X'], d['dF'], d['RV'], d['vref']
    out = {}
    Z = br.z(X)
    for j, h in enumerate(H):
        w = np.asarray(obj['vol'][j])
        pv = np.clip(w[0] + Z @ w[1:], -3, 3)
        var_m = vref * h * np.exp(pv)
        var_b = vref * h                                           # baseline: the 10-minute clock, scaled by time
        ok = np.isfinite(RV[:, j]) & (RV[:, j] > 0)
        ql = lambda v: float(np.mean(RV[ok, j] / v[ok] - np.log(RV[ok, j] / v[ok]) - 1.0))      # QLIKE, lower better
        z = dF[:, j] / np.sqrt(var_m)
        zb = dF[:, j] / np.sqrt(var_b)
        okd = np.isfinite(z)
        q = np.asarray(obj['qz'][j])
        wl = np.asarray(obj['lin'][j])
        pl = np.clip(wl[0] + Z @ wl[1:], -0.6, 0.6)
        pg = np.clip(obj['gbm'][j].predict(X), -0.6, 0.6) if obj['gbm'][j] is not None else np.zeros(len(X))
        r = dict(n=int(okd.sum()), qlike=ql(var_m), qlike_base=ql(var_b),
                 cover80=float(np.mean((z[okd] >= q[0]) & (z[okd] <= q[4]))),
                 cover80_base=float(np.mean(np.abs(zb[okd]) <= 1.2816)), kurt=float(np.mean(z[okd] ** 4) / np.mean(z[okd] ** 2) ** 2))
        for nm, p in (('lin', pl), ('gbm', pg), ('avg', 0.5 * (pl + pg))):
            ic = float(np.corrcoef(p[okd], z[okd])[0, 1]) if np.std(p[okd]) > 0 else 0.0
            mse0, mse1 = float(np.mean(z[okd] ** 2)), float(np.mean((z[okd] - p[okd]) ** 2))
            big = okd & (np.abs(p) >= np.quantile(np.abs(p[okd]), 0.8)) & (np.abs(z) > 0.25)
            r[nm] = dict(ic=ic, r2=1.0 - mse1 / mse0, top_dir=float(np.mean(np.sign(p[big]) == np.sign(z[big]))) if big.sum() > 20 else None,
                         top_n=int(big.sum()), auc=auc(p[okd], (z[okd] > 0).astype(float)))
        out[h] = r
    return out


def main():
    mode = sys.argv[1]
    days = sorted(os.path.basename(p)[:10] for p in glob.glob(os.path.join(COL, '*.joblib')))
    data = [load(d) for d in days]
    print('sessions', len(days), 'origins', sum(len(d['X']) for d in data), flush=True)
    if mode == 'final':
        obj = fit(data)
        joblib.dump(obj, os.path.join(LAB, 'brain.joblib'), compress=3)
        json.dump(obj['meta'], open(os.path.join(LAB, 'brain.meta.json'), 'w'), indent=1)
        print('saved brain.joblib', obj['meta'])
        return
    os.makedirs(os.path.join(LAB, 'brains'), exist_ok=True)
    res = {}
    for i in range(MIN_TRAIN, len(days)):
        t0 = time.time()
        obj = fit(data[:i])
        joblib.dump(obj, os.path.join(LAB, 'brains', f"brain_{days[i - 1]}.joblib"), compress=3)
        res[days[i]] = evaluate(obj, data[i])
        r5 = res[days[i]][300]
        print(days[i], f"trained on {i} sessions | 5 min: QLIKE {r5['qlike']:.3f} vs {r5['qlike_base']:.3f} | cover {r5['cover80']:.2f} vs {r5['cover80_base']:.2f}"
              f" | IC lin {r5['lin']['ic']:+.3f} gbm {r5['gbm']['ic']:+.3f} avg {r5['avg']['ic']:+.3f} | top-20% direction {r5['avg']['top_dir']} | {time.time() - t0:.0f} s", flush=True)
    json.dump(res, open(os.path.join(LAB, 'walk_forward.json'), 'w'), indent=1)
    print('\nUNSEEN-SESSION AVERAGES over', len(res), 'sessions (trained part alone, no online learning)')
    print('horizon | QLIKE model / 10-min clock (sessions better) | 80% cover model / gaussian | IC ridge / trees / avg (sessions avg>0) | top-20% direction avg')
    for h in H:
        R = [res[d][h] for d in res]
        m = lambda f: float(np.mean([f(r) for r in R]))
        td = [r['avg']['top_dir'] for r in R if r['avg']['top_dir'] is not None]
        print(f"{h // 60:3d} min | {m(lambda r: r['qlike']):.3f} / {m(lambda r: r['qlike_base']):.3f} ({sum(r['qlike'] < r['qlike_base'] for r in R)}/{len(R)})"
              f" | {m(lambda r: r['cover80']):.3f} / {m(lambda r: r['cover80_base']):.3f}"
              f" | {m(lambda r: r['lin']['ic']):+.3f} / {m(lambda r: r['gbm']['ic']):+.3f} / {m(lambda r: r['avg']['ic']):+.3f} ({sum(r['avg']['ic'] > 0 for r in R)}/{len(R)})"
              f" | {np.mean(td):.3f}" if td else '')


if __name__ == '__main__':
    main()
