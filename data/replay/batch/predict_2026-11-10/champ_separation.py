"""10 Nov 2026 (docs/40 section 2, docs/41): can the entry photograph tell the champion family's winning episodes from
its losing ones? Walk-forward by day: every model is fitted on EARLIER days only. Discovery material, 14 replay days
(v3 photograph, batch v3_*). Episode = one family entry (same contract, trigger within 5 s); siblings are one row.
Read-only. Output: data/research/predict/champ_separation.json"""
import json, glob, os, collections, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, 'data/replay/batch/v3_2026-*/paper/2026-*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    day = os.path.basename(f)[:10]
    for n, b in d.items():
        if n.startswith('c20'):
            for t in b['trades']:
                rows.append((day, n, t))
ep = collections.OrderedDict()
for day, n, t in rows:
    ep.setdefault((day, t['key'], round(t['trigger_t'] / 5)), []).append((n, t))
E = []
for (day, key, _), v in ep.items():
    ts = [t for _, t in v]
    w = ts[0].get('weather_trig') or {}
    rets = [t['ret_pct'] for t in ts]
    peak = max(100.0 * t['peak_pts'] / t['entry'] for t in ts)
    y9 = [t['ret_pct'] for n, t in v if n == 'c20_9y']
    E.append(dict(day=day, w=w, ret=float(np.mean(rets)), best=max(rets), worst=min(rets), peak=peak,
                  r9y=(y9[0] if y9 else None), n=len(ts), expd=bool(w.get('expiry_day'))))
days = sorted({e['day'] for e in E})
num = sorted({k for e in E for k, x in e['w'].items() if isinstance(x, (int, float)) and not isinstance(x, bool)})
X = np.array([[(e['w'].get(k) if isinstance(e['w'].get(k), (int, float)) and not isinstance(e['w'].get(k), bool)
                else np.nan) for k in num] for e in E], float)
D = np.array([days.index(e['day']) for e in E])
ret = np.array([e['ret'] for e in E]); peak = np.array([e['peak'] for e in E])
cls = np.where(peak < 5, 0, np.where(ret <= 0, 1, 2))   # 0 never developed, 1 gained 5 %+ then lost, 2 won
print('episodes', len(E), 'days', len(days), 'features', len(num))
print('class counts: never developed', int((cls == 0).sum()), 'gave back', int((cls == 1).sum()), 'won', int((cls == 2).sum()))
print('win rate', round(float((ret > 0).mean()), 3), 'mean ret %', round(float(ret.mean()), 2), 'sum', round(float(ret.sum()), 1))


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, bool)
    if y.all() or (~y).all():
        return np.nan
    r = s.argsort().argsort() + 1.0
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def fit_logit(A, y, l2):
    w = np.zeros(A.shape[1] + 1)
    A1 = np.c_[np.ones(len(A)), A]
    for _ in range(25):
        p = 1 / (1 + np.exp(-A1 @ w))
        g = A1.T @ (p - y) + l2 * np.r_[0, w[1:]]
        H = (A1 * (p * (1 - p))[:, None]).T @ A1 + l2 * np.eye(len(w))
        w -= np.linalg.solve(H + 1e-9 * np.eye(len(w)), g)
    return w


def walk(y, k, l2, rng=None):
    """Predict each day from earlier days (at least 5). Top-k features by in-train |rank correlation|."""
    P = np.full(len(y), np.nan); B = np.full(len(y), np.nan)
    yy = y.copy()
    for d in range(5, len(days)):
        tr, te = D < d, D == d
        if te.sum() == 0:
            continue
        ytr = yy[tr].copy()
        if rng is not None:
            ytr = rng.permutation(ytr)
        Xt = X[tr]; ok = (np.isfinite(Xt).mean(0) > 0.9) & (np.nanstd(Xt, 0) > 0)
        med = np.nanmedian(Xt[:, ok], 0); sd = np.nanstd(Xt[:, ok], 0)
        Z = lambda M: np.clip(np.nan_to_num((M[:, ok] - med) / sd), -4, 4)
        Zt = Z(X[tr]); R = Zt.argsort(0).argsort(0).astype(float); R -= R.mean(0); yc = ytr - ytr.mean()
        c = np.abs(R.T @ yc) / (np.sqrt((R ** 2).sum(0)) * np.sqrt((yc ** 2).sum()) + 1e-12)
        top = np.argsort(-np.nan_to_num(c))[:k]
        w = fit_logit(Zt[:, top], ytr.astype(float), l2)
        P[te] = 1 / (1 + np.exp(-(np.c_[np.ones(te.sum()), Z(X[te])[:, top]] @ w)))
        B[te] = ytr.mean()
    m = np.isfinite(P)
    return dict(n=int(m.sum()), auc=auc(P[m], y[m]), brier=float(((P[m] - y[m]) ** 2).mean()),
                brier_base=float(((B[m] - y[m]) ** 2).mean()), P=P, m=m)


out = dict(episodes=len(E), days=len(days), features=len(num), tried=[])
rng = np.random.default_rng(11)
for name, y in (('won (mean family return above 0)', ret > 0), ('developed (peak 5 % or more)', peak >= 5),
                ('runner (best sibling 20 % or more)', np.array([e['best'] for e in E]) >= 20)):
    for k in (3, 8):
        for l2 in (1.0, 10.0):
            r = walk(y.astype(float), k, l2)
            sh = [walk(y.astype(float), k, l2, rng)['auc'] for _ in range(100)]
            p = float((np.array(sh) >= r['auc']).mean())
            m = r['m']; top = m & (r['P'] >= np.nanmedian(r['P'][m])); bot = m & ~top
            row = dict(target=name, k=k, l2=l2, n=r['n'], base=round(float(y[m].mean()), 3), auc=round(r['auc'], 3),
                       shuffle_p=round(p, 3), brier=round(r['brier'], 4), brier_base=round(r['brier_base'], 4),
                       top_half_n=int(top.sum()), top_half_win=round(float((ret[top] > 0).mean()), 3),
                       top_half_ret=round(float(ret[top].sum()), 1), bottom_half_win=round(float((ret[bot] > 0).mean()), 3),
                       bottom_half_ret=round(float(ret[bot].sum()), 1))
            out['tried'].append(row); print(row, flush=True)
os.makedirs(os.path.join(ROOT, 'data/research/predict'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'data/research/predict/champ_separation.json'), 'w'), indent=1)
