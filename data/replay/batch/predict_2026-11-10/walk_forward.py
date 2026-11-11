"""10 Nov 2026 (docs/41 M3): walk-forward scoring of the baseline forecasts on the unselected origins.

Every test day is predicted by models fitted on EARLIER days only (at least 5). 15 sessions, so 10 test days.
Discovery material: the feature list and the target spec were fixed before this ran, nothing else was.

Targets, per horizon h in 30/60/180/300 s after the fill (fixed contract, ask in, bid marks):
  T_h  the bid reached +5 % of the entry premium before -5 %, within h
  A_h  the bid reached -5 % first, within h
  UP60 the index future's mid rose more than 5 points in the 60 s after the fill second (calls rows only, unsigned)
Controls on the same rows: the training base rate, a one-feature model on futures momentum (mom30), a one-feature
model on the option's own momentum (om30).
Policy check (P02 off-policy): one position at a time per recorded part, enter when pT300 - pA300 is at or above the
training fold's 95th / 99th percentile of that score, exit by apex.predict.targets.policy_exit. Controls: the same
with mom30 as the score, and every origin taken (no selection).
Stage C: a calibrator updated ONLY from labels whose horizon has fully passed, against the same frozen model.

Output: data/research/predict/walk_forward_v1.json, model_v1.json (fitted on all 15 days, for the engine: discovery)."""
import glob, json, os, sys, collections
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M, FW, D, P = z['X'].astype(float), z['M'], z['FW'].astype(float), z['D'], z['P']
days, parts, names = list(z['days']), list(z['parts']), list(z['names'])
mc = {n: i for i, n in enumerate(z['mcols'])}
H = T.HORIZONS
filled = M[:, mc['st']] == 1
expd = X[:, names.index('expd')] > 0.5
L2 = 10.0
MIN_TRAIN_DAYS = 5
res = dict(rows=int(len(X)), filled=int(filled.sum()), days=days, l2=L2, targets={}, policy={}, stage_c={}, tried=[])


def y_of(kind, h):
    f = M[:, mc[f'first{h}']]
    obs = filled & (f != 3)
    return obs, (f == (1 if kind == 'T' else 2)).astype(float)


def walk(obs, y, cols):
    p = np.full(len(y), np.nan); b = np.full(len(y), np.nan)
    for d in range(MIN_TRAIN_DAYS, len(days)):
        tr, te = obs & (D < d), obs & (D == d)
        if te.sum() == 0 or tr.sum() < 1000:
            continue
        m = Mo.fit_logit(X[tr][:, cols], y[tr], [names[c] for c in cols], l2=L2)
        p[te] = Mo.predict(m, X[te][:, cols]); b[te] = y[tr].mean()
    return p, b


def score(p, b, y, m):
    m = m & np.isfinite(p)
    if m.sum() < 50:
        return None
    br, bb = Mo.brier(p[m], y[m]), Mo.brier(b[m], y[m])
    return dict(n=int(m.sum()), base=round(float(y[m].mean()), 4), auc=round(Mo.auc(p[m], y[m]), 4), brier=round(br, 5),
                brier_base=round(bb, 5), skill=round(1 - br / bb, 4) if bb > 0 else None)


ALL = list(range(len(names)))
PRED = {}
for kind in ('T', 'A'):
    for h in H:
        obs, y = y_of(kind, h)
        p, b = walk(obs, y, ALL)
        PRED[(kind, h)] = (p, b, y, obs)
        pm, _ = walk(obs, y, [names.index('mom30')])
        po, _ = walk(obs, y, [names.index('om30')])
        row = dict(all=score(p, b, y, obs), expiry_day=score(p, b, y, obs & expd), other_days=score(p, b, y, obs & ~expd),
                   ctl_mom30=score(pm, b, y, obs), ctl_om30=score(po, b, y, obs))
        m = obs & np.isfinite(p)
        per_day = []
        for d in range(MIN_TRAIN_DAYS, len(days)):
            s = score(p, b, y, obs & (D == d))
            if s:
                per_day.append((days[d], s['n'], s['auc'], s['skill']))
        row['per_day'] = per_day
        row['days_auc_above_half'] = int(sum(1 for r in per_day if r[2] > 0.5)); row['days_skill_positive'] = int(sum(1 for r in per_day if r[3] > 0))
        if h == 300:
            row['reliability'] = Mo.reliability(p[m], y[m])
        res['targets'][f'{kind}{h}'] = row
        print(kind, h, row['all'], '| mom30', row['ctl_mom30'] and row['ctl_mom30']['auc'], '| om30', row['ctl_om30'] and row['ctl_om30']['auc'],
              '| days auc>0.5', row['days_auc_above_half'], 'skill>0', row['days_skill_positive'], 'of', len(per_day), flush=True)

# speed: among origins that DID reach the target within 300 s, does a higher pT30 mean a faster arrival?
pT30, pT300 = PRED[('T', 30)][0], PRED[('T', 300)][0]
hit = filled & (M[:, mc['first300']] == 1) & np.isfinite(pT30) & np.isfinite(M[:, mc['t_hit']])
ratio = pT30[hit] / np.maximum(pT300[hit], 1e-6)
th = M[hit, mc['t_hit']]
rk = lambda a: np.argsort(np.argsort(a))
res['speed'] = dict(n=int(hit.sum()), median_t_hit_s=float(np.median(th)),
                    rank_corr_pT30_share_vs_time=round(float(np.corrcoef(rk(ratio), rk(th))[0, 1]), 4),
                    median_t_hit_top_quarter=float(np.median(th[ratio >= np.quantile(ratio, 0.75)])),
                    median_t_hit_bottom_quarter=float(np.median(th[ratio <= np.quantile(ratio, 0.25)])))
print('speed', res['speed'], flush=True)

# direction of the underlying (calls rows only: features are unsigned there)
ce = M[:, mc['rr']] == 0
fw60 = FW[:, H.index(60)]
obs = ce & np.isfinite(fw60) & (M[:, mc['itm']] == 0)
for nm, y in (('UP60 (more than +5 points)', (fw60 > 5).astype(float)), ('DOWN60 (more than -5 points)', (fw60 < -5).astype(float))):
    mk = [names.index(n) for n in F.MARKET]
    p, b = walk(obs, y, mk)
    pm, _ = walk(obs, y, [names.index('mom30')])
    res['targets'][nm] = dict(all=score(p, b, y, obs), ctl_mom30=score(pm, b, y, obs))
    print(nm, res['targets'][nm], flush=True)

# -- policy check ---------------------------------------------------------------------------------------------------
DSC = {}


def ds(part):
    if part not in DSC:
        q = np.load(os.path.join(ROOT, 'data', 'research', 'ds_v2', part + '.npz'))
        n = len(q['strikes']); order = np.argsort(q['strikes'])
        o = q['opt'][:, :n].astype(float)[:, order]; a = q['age'][:, :n].astype(float)[:, order]
        DSC.clear()
        DSC[part] = dict(t=q['t'].astype(float), bid=o[..., 0], ask=o[..., 1], ok=(o[..., 0] > 0) & (o[..., 1] > o[..., 0]) & (a <= F.Q_FRESH_S),
                         idx={float(v): i for i, v in enumerate(q['t'])})
    return DSC[part]


def run_policy(scr, thr_of, label):
    """One position at a time per part. scr: score per row (NaN = no forecast). thr_of(d) -> threshold for day d."""
    tr = []
    for pi, part in enumerate(parts):
        rows = np.where((P == pi) & filled & np.isfinite(scr))[0]
        if not len(rows):
            continue
        d = int(D[rows[0]])
        if d < MIN_TRAIN_DAYS:
            continue
        thr = thr_of(d)
        q = ds(part); free = -1.0
        for r in rows[np.argsort(M[rows, 0], kind='stable')]:
            t0 = M[r, 0]
            if t0 < free or scr[r] < thr:
                continue
            k, rr = int(M[r, mc['k']]), int(M[r, mc['rr']])
            a = q['idx'][t0] + T.DELAY_S
            e = M[r, mc['entry']]
            x = T.policy_exit(q['t'], q['bid'][:, k, rr], q['ok'][:, k, rr], a, e)
            if x is None:
                continue
            tr.append((days[d], bool(expd[r]), x[0], x[1], x[2])); free = q['t'][a] + x[1]
    if not tr:
        return dict(label=label, n=0)
    r = np.array([t[2] for t in tr]); byday = collections.defaultdict(float)
    for t in tr:
        byday[t[0]] += t[2]
    ne = np.array([not t[1] for t in tr])
    return dict(label=label, n=len(tr), won=int((r > 0).sum()), lost=int((r <= 0).sum()), sum_pct=round(100 * float(r.sum()), 1),
                mean_pct=round(100 * float(r.mean()), 3), days_positive=f"{sum(1 for v in byday.values() if v > 0)} of {len(byday)}",
                non_expiry=dict(n=int(ne.sum()), won=int((r[ne] > 0).sum()), sum_pct=round(100 * float(r[ne].sum()), 1)),
                exits=dict(collections.Counter(t[4] for t in tr)), mean_hold_s=round(float(np.mean([t[3] for t in tr])), 1))


edge = PRED[('T', 300)][0] - PRED[('A', 300)][0]
# the threshold of day d comes from in-sample scores of a model fitted on days < d: refit to get them
thr_cache = {}
for d in range(MIN_TRAIN_DAYS, len(days)):
    oT, yT = y_of('T', 300); oA, yA = y_of('A', 300)
    tr = oT & (D < d)
    mT = Mo.fit_logit(X[tr], yT[tr], names, l2=L2); mA = Mo.fit_logit(X[tr], yA[tr], names, l2=L2)
    s = Mo.predict(mT, X[tr]) - Mo.predict(mA, X[tr])
    mo = X[tr][:, names.index('mom30')]
    thr_cache[d] = dict(e95=float(np.quantile(s, 0.95)), e99=float(np.quantile(s, 0.99)),
                        m95=float(np.nanquantile(mo, 0.95)), m99=float(np.nanquantile(mo, 0.99)))
mom = np.where(np.isfinite(edge), X[:, names.index('mom30')], np.nan)
for lab, scr, key in (('forecast edge, top 5 %', edge, 'e95'), ('forecast edge, top 1 %', edge, 'e99'),
                      ('control: mom30, top 5 %', mom, 'm95'), ('control: mom30, top 1 %', mom, 'm99')):
    res['policy'][lab] = run_policy(scr, lambda d, k=key: thr_cache[d][k], lab); print(res['policy'][lab], flush=True)
res['policy']['control: every origin, no selection'] = run_policy(np.where(np.isfinite(edge), 0.0, np.nan), lambda d: 0.0, 'every origin')
print(res['policy']['control: every origin, no selection'], flush=True)

# -- stage C: matured-only calibration against the frozen forecast --------------------------------------------------
p, b, y, obs = PRED[('T', 300)]
m = obs & np.isfinite(p)
order = np.where(m)[0][np.argsort(M[m, 0], kind='stable')]
cal = Mo.Calibrator(prior=200.0); adj = np.full(len(p), np.nan); queue = collections.deque(); cur_day = None
for r in order:
    if D[r] != cur_day:                       # a new day: yesterday's open labels have all matured overnight
        for q_ in queue:
            cal.update(p[q_], y[q_])
        queue.clear(); cur_day = D[r]
    while queue and M[queue[0], 0] + T.DELAY_S + 300 + T.MAX_GAP_S < M[r, 0]:
        q_ = queue.popleft(); cal.update(p[q_], y[q_])
    adj[r] = cal(p[r])[0]; queue.append(r)
res['stage_c'] = dict(n=int(len(order)), brier_frozen=round(Mo.brier(p[order], y[order]), 5), brier_adaptive=round(Mo.brier(adj[order], y[order]), 5),
                      brier_base=round(Mo.brier(b[order], y[order]), 5), auc_frozen=round(Mo.auc(p[order], y[order]), 4),
                      auc_adaptive=round(Mo.auc(adj[order], y[order]), 4), calibrator_updates=cal.updates,
                      rule='a label enters the calibrator only after fill + 300 s + 10 s have passed')
print('stage C', res['stage_c'], flush=True)

# -- the artefact for the engine: fitted on all 15 days (discovery; no held-out day left) ----------------------------
art = dict(version=1, feature_schema=F.SCHEMA, target_spec=T.SPEC, training_cutoff=days[-1], training_days=days, l2=L2, models={})
for kind in ('T', 'A'):
    for h in H:
        obs, y = y_of(kind, h)
        art['models'][f'{kind}{h}'] = Mo.fit_logit(X[obs], y[obs], names, l2=L2, meta=dict(target=f'{kind}{h}', days=len(days)))
oT, yT = y_of('T', 300); oA, yA = y_of('A', 300)
s = Mo.predict(art['models']['T300'], X[oT]) - Mo.predict(art['models']['A300'], X[oT])
art['edge_quantiles'] = {q: float(np.quantile(s, float(q))) for q in ('0.5', '0.9', '0.95', '0.99')}
art['hash'] = Mo.model_hash(art)
# the engine's artefact is written by make_artefact.py (10 Nov, after the damped-Newton fix), not here
res['artefact'] = dict(hash=art['hash'], edge_quantiles=art['edge_quantiles'])
top = sorted(zip(names, art['models']['T300']['w'][1:]), key=lambda kv: -abs(kv[1]))[:10]
res['T300_largest_weights'] = [(k, round(v, 3)) for k, v in top]
print('artefact', res['artefact'], res['T300_largest_weights'])
json.dump(res, open(os.path.join(OUT, 'walk_forward_v1.json'), 'w'), indent=1)
