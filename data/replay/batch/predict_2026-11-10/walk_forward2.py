"""10 Nov 2026 (docs/41 M3, second run). What the first run (walk_forward.py, kept with its output) could not say:

1. WHICH SIDE: among origins where one barrier was reached within 300 s, does the forecast edge (pT300 - pA300) tell
   the target-first ones from the adverse-first ones, inside each day? The pooled AUC of run 1 was mostly the
   difference between expiry days and other days (base rate of T30: 20-33 % on expiry days, 1-5 % on others).
2. Is a non-linear model better? sklearn HistGradientBoosting (research only: the engine's artefact stays the logit).
3. The policy check day by day, with the first run's A30 numerical fault fixed (damped Newton in models.fit_logit).

Same origins, same targets, same walk-forward (earlier days only, at least 5). Specifications tried here, all
reported: logit l2=10; HGB depth 3, 200 trees, rate 0.05, l2 1.0; thresholds at the training fold's 95th and 99th
percentile of the edge. Output: data/research/predict/walk_forward_v2.json"""
import collections, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M, D, P = z['X'].astype(float), z['M'], z['D'], z['P']
days, parts, names = list(z['days']), list(z['parts']), list(z['names'])
mc = {n: i for i, n in enumerate(z['mcols'])}
filled = M[:, mc['st']] == 1
expd = X[:, names.index('expd')] > 0.5
f300 = M[:, mc['first300']]
obs = filled & (f300 != 3)
yT, yA = (f300 == 1).astype(float), (f300 == 2).astype(float)
MIN = 5
WIN = X[:, names.index('tod')] <= 21600.0 / 22500.0          # the engine takes no entry after 15:15
PREM20 = X[:, names.index('prem')] >= 20.0
res = dict(days=days, models={}, tried=['logit l2=10', 'HGB depth 3, 200 trees, rate 0.05, l2 1.0', 'edge thresholds: training 95th and 99th percentile'])
DSC = {}


def ds(part):
    if part not in DSC:
        q = np.load(os.path.join(ROOT, 'data', 'research', 'ds_v2', part + '.npz'))
        n = len(q['strikes']); order = np.argsort(q['strikes'])
        o = q['opt'][:, :n].astype(float)[:, order]; a = q['age'][:, :n].astype(float)[:, order]
        DSC.clear()
        DSC[part] = dict(t=q['t'].astype(float), bid=o[..., 0], ok=(o[..., 0] > 0) & (o[..., 1] > o[..., 0]) & (a <= F.Q_FRESH_S),
                         idx={float(v): i for i, v in enumerate(q['t'])})
    return DSC[part]


def policy(edge, thr, label, mask=None):
    tr = []
    for pi, part in enumerate(parts):
        rows = np.where((P == pi) & filled & np.isfinite(edge))[0]
        if not len(rows) or int(D[rows[0]]) < MIN:
            continue
        d = int(D[rows[0]]); q = ds(part); free = -1.0
        for r in rows[np.argsort(M[rows, 0], kind='stable')]:
            if M[r, 0] < free or edge[r] < thr[d] or (mask is not None and not mask[r]):
                continue
            k, rr = int(M[r, mc['k']]), int(M[r, mc['rr']])
            a = q['idx'][M[r, 0]] + T.DELAY_S
            x = T.policy_exit(q['t'], q['bid'][:, k, rr], q['ok'][:, k, rr], a, M[r, mc['entry']])
            if x is None:
                continue
            tr.append((days[d], bool(expd[r]), x[0], x[1], x[2], int(rr))); free = q['t'][a] + x[1]
    if not tr:
        return dict(label=label, n=0)
    r = np.array([t[2] for t in tr])
    by = collections.OrderedDict()
    for t in tr:
        b = by.setdefault(t[0], [0, 0, 0.0]); b[0] += 1; b[1] += t[2] > 0; b[2] += 100 * t[2]
    se = float(r.std() / np.sqrt(len(r)))
    day_sum = np.array([v[2] for v in by.values()])
    return dict(label=label, n=len(tr), won=int((r > 0).sum()), lost=int((r <= 0).sum()), sum_pct=round(100 * float(r.sum()), 1),
                mean_pct=round(100 * float(r.mean()), 3), se_pct=round(100 * se, 3),
                days_positive=f"{int((day_sum > 0).sum())} of {len(day_sum)}", worst_day_pct=round(float(day_sum.min()), 1),
                calls=int(sum(1 for t in tr if t[5] == 0)), puts=int(sum(1 for t in tr if t[5] == 1)),
                per_day={k: (v[0], int(v[1]), round(v[2], 1)) for k, v in by.items()})


def fit_predict(kind):
    pT = np.full(len(X), np.nan); pA = np.full(len(X), np.nan); thr = {}
    for d in range(MIN, len(days)):
        tr, te = obs & (D < d), filled & (D == d)
        if kind == 'logit':
            mT = Mo.fit_logit(X[tr], yT[tr], names, l2=10.0); mA = Mo.fit_logit(X[tr], yA[tr], names, l2=10.0)
            f = lambda m, A: Mo.predict(m, A)
        else:
            mk = lambda: HGB(max_depth=3, max_iter=200, learning_rate=0.05, l2_regularization=1.0, random_state=7)
            mT = mk().fit(X[tr], yT[tr]); mA = mk().fit(X[tr], yA[tr])
            f = lambda m, A: m.predict_proba(A)[:, 1]
        pT[te], pA[te] = f(mT, X[te]), f(mA, X[te])
        s = f(mT, X[tr]) - f(mA, X[tr])
        thr[d] = (float(np.quantile(s, 0.95)), float(np.quantile(s, 0.99)))
    return pT, pA, thr


for kind in (('logit',) if os.environ.get('WF2_LOGIT_ONLY') else ('logit', 'hgb')):
    pT, pA, thr = fit_predict(kind)
    edge = pT - pA
    m = obs & np.isfinite(edge)
    ev = m & ((f300 == 1) | (f300 == 2))
    side = []
    for d in range(MIN, len(days)):
        k = ev & (D == d)
        if k.sum() > 100:
            side.append((days[d], int(k.sum()), round(float(yT[k].mean()), 3), round(Mo.auc(edge[k], yT[k]), 4),
                         round(Mo.auc(pT[m & (D == d)], yT[m & (D == d)]), 4)))
    out = dict(T300=dict(auc=round(Mo.auc(pT[m], yT[m]), 4), brier=round(Mo.brier(pT[m], yT[m]), 5)),
               A300=dict(auc=round(Mo.auc(pA[m], yA[m]), 4), brier=round(Mo.brier(pA[m], yA[m]), 5)),
               side_auc_by_day=side, side_auc_mean=round(float(np.mean([s[3] for s in side])), 4),
               side_days_above_half=f"{sum(1 for s in side if s[3] > 0.5)} of {len(side)}",
               within_day_T300_auc_mean=round(float(np.mean([s[4] for s in side])), 4),
               side_reliability=Mo.reliability(edge[ev], yT[ev], bins=10),
               policy_top5=policy(edge, {d: t[0] for d, t in thr.items()}, f'{kind} edge top 5 %'),
               policy_top1=policy(edge, {d: t[1] for d, t in thr.items()}, f'{kind} edge top 1 %'),
               # added after run 1's day table (27 Oct: the losses sit in the expiry afternoon): diagnostics, not a new rule
               policy_top5_engine_window=policy(edge, {d: t[0] for d, t in thr.items()}, f'{kind} edge top 5 %, entries before 15:15', WIN),
               policy_top5_window_prem20=policy(edge, {d: t[0] for d, t in thr.items()}, f'{kind} edge top 5 %, before 15:15, premium 20 or more', WIN & PREM20),
               policy_top1_engine_window=policy(edge, {d: t[1] for d, t in thr.items()}, f'{kind} edge top 1 %, entries before 15:15', WIN),
               policy_all_engine_window=policy(np.where(np.isfinite(edge), 0.0, np.nan), {d: 0.0 for d in thr}, 'every origin before 15:15', WIN))
    res['models'][kind] = out
    print(kind, 'T300', out['T300'], 'A300', out['A300'], flush=True)
    print(' side AUC mean', out['side_auc_mean'], out['side_days_above_half'], 'within-day T300 AUC mean', out['within_day_T300_auc_mean'])
    for s in side:
        print('  ', s)
    for k in ('policy_top5', 'policy_top1', 'policy_top5_engine_window', 'policy_top1_engine_window', 'policy_top5_window_prem20', 'policy_all_engine_window'):
        print(' ', out[k], flush=True)
json.dump(res, open(os.path.join(OUT, 'walk_forward_v2_logit.json' if os.environ.get('WF2_LOGIT_ONLY') else 'walk_forward_v2.json'), 'w'), indent=1)
