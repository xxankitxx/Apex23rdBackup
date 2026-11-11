"""11 Nov 2026 (docs/42 findings B and F, docs/43 section 7.3 step 2): chronological artefacts on origins_v2.

For every session d with at least MIN_TRAIN earlier sessions: fit the eight models on the sessions BEFORE d only,
take the lines from the deployed score (Forecaster.score) on those same earlier sessions, and score session d, which
the artefact has never seen. One artefact per session, plus a last one fitted through the newest session for the
days after it. Nothing here was tuned on a result: l2, the features, the horizons and the percentiles are those of
model_v1.

Writes  apex/predict/artefacts/model_c_<trained_through>.json   one per training cut-off
        apex/predict/registry.json                               [{file, hash, trained_through, effective_from, ...}]
        data/research/predict/chrono_eval.json                   out-of-sample evidence by session and by depth
Usage: py -3.13 fit_chrono.py [--install]     (without --install nothing is written under apex/)"""
import json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
from apex.predict.ledger import Forecaster
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
ART = os.path.join(ROOT, 'apex', 'predict', 'artefacts')
MIN_TRAIN = 5
QS = ('0.5', '0.9', '0.95', '0.99')
z = np.load(os.path.join(OUT, 'origins_v2.npz'))
X, M, D = z['X'].astype(float), z['M'], z['D'].astype(int)
days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
mc = {str(n): i for i, n in enumerate(z['mcols'])}
sha = json.load(open(os.path.join(OUT, 'origins_v2.manifest.json')))['sha256']
filled = M[:, mc['st']] == 1
f300 = M[:, mc['first300']]
obs300 = filled & (f300 != 3)


def fit(train):
    """An artefact from the rows in `train` (a boolean mask). Lines from the deployed score on the same rows."""
    art = dict(version=3, feature_schema=F.SCHEMA, target_spec=T.SPEC, l2=10.0, origins='origins_v2', origins_sha256=sha,
               score_pipeline='project_v1', models={},
               population='every 5 s: at-the-money and the first four in-the-money strikes, calls and puts, near week')
    for kind, code in (('T', 1), ('A', 2)):
        for h in T.HORIZONS:
            f = M[:, mc[f'first{h}']]
            o = train & filled & (f != 3)
            art['models'][f'{kind}{h}'] = Mo.fit_logit(X[o], (f[o] == code).astype(float), names, l2=10.0, meta=dict(target=f'{kind}{h}'))
    o = train & obs300
    fc = Forecaster(artefact=dict(art, hash='tmp'))
    s = fc.edges(X[o])
    art['edge_quantiles'] = {q: float(np.quantile(s, float(q))) for q in QS}
    art['mom30_q95'] = float(np.nanquantile(np.abs(X[o][:, names.index('mom30')]), 0.95))
    art['line_rows'] = int(o.sum())
    return art


def evaluate(art, test):
    fc = Forecaster(artefact=art)
    o = test & obs300
    pT, pA = fc.score(X[o])
    e = pT[:, -1] - pA[:, -1]
    yT, yA = (f300[o] == 1).astype(float), (f300[o] == 2).astype(float)
    r = M[o, mc['ret300']]
    out = dict(rows=int(o.sum()), base_T=float(yT.mean()), base_A=float(yA.mean()),
               auc_T=float(Mo.auc(pT[:, -1], yT)), auc_A=float(Mo.auc(pA[:, -1], yA)),
               brier_T=float(Mo.brier(pT[:, -1], yT)), brier_T_base=float(Mo.brier(np.full(len(yT), yT.mean()), yT)))
    hit = (yT + yA) > 0                                # direction given that a barrier was hit
    out['auc_side_given_hit'] = float(Mo.auc(e[hit], yT[hit])) if hit.sum() > 50 and 0 < yT[hit].mean() < 1 else None
    for q in ('0.95', '0.99'):
        m = e >= art['edge_quantiles'][q]
        out['above_' + q] = dict(n=int(m.sum()), share=float(m.mean()), T=float(yT[m].mean()) if m.any() else None,
                                 A=float(yA[m].mean()) if m.any() else None,
                                 mean_ret300=float(np.nanmean(r[m])) if m.any() else None)
    itm = M[o, mc['itm']].astype(int)
    out['by_depth'] = {int(j): dict(rows=int((itm == j).sum()), auc_T=float(Mo.auc(pT[itm == j, -1], yT[itm == j])),
                                    auc_A=float(Mo.auc(pA[itm == j, -1], yA[itm == j])),
                                    above_095=int((e[itm == j] >= art['edge_quantiles']['0.95']).sum()))
                       for j in sorted(set(itm)) if (itm == j).sum() > 200 and 0 < yT[itm == j].mean() < 1}
    return out


reg, ev = [], {}
for d in range(MIN_TRAIN, len(days) + 1):
    art = fit(D < d)
    art.update(training_days=days[:d], training_cutoff=days[d - 1], trained_through=days[d - 1],
               effective_from=days[d] if d < len(days) else None)     # None: every session after the cut-off
    art['hash'] = Mo.model_hash(art)
    name = f"model_c_{days[d - 1]}.json"
    reg.append(dict(file='artefacts/' + name, hash=art['hash'], trained_through=days[d - 1], effective_from=art['effective_from'],
                    training_sessions=d, feature_schema=F.SCHEMA, origins_sha256=sha, lines=art['edge_quantiles']))
    if d < len(days):
        ev[days[d]] = dict(artefact=art['hash'], trained_through=days[d - 1], **evaluate(art, D == d))
        e = ev[days[d]]
        print(days[d], 'trained through', days[d - 1], 'rows', e['rows'], 'AUC T', round(e['auc_T'], 3), 'A', round(e['auc_A'], 3),
              'side|hit', None if e['auc_side_given_hit'] is None else round(e['auc_side_given_hit'], 3),
              'above 95 %:', e['above_0.95']['n'], 'T', e['above_0.95']['T'] and round(e['above_0.95']['T'], 3),
              'A', e['above_0.95']['A'] and round(e['above_0.95']['A'], 3),
              'ret300', e['above_0.95']['mean_ret300'] and round(100 * e['above_0.95']['mean_ret300'], 3), flush=True)
    if '--install' in sys.argv:
        os.makedirs(ART, exist_ok=True)
        json.dump(art, open(os.path.join(ART, name), 'w'))
json.dump(dict(min_train=MIN_TRAIN, days=days, by_day=ev), open(os.path.join(OUT, 'chrono_eval.json'), 'w'), indent=1)
if '--install' in sys.argv:
    json.dump(dict(note='chronological artefacts: an artefact is used only on sessions from effective_from on, and only '
                        'until the next one takes over; the last has no end', min_train=MIN_TRAIN, artefacts=reg),
              open(os.path.join(ROOT, 'apex', 'predict', 'registry.json'), 'w'), indent=1)
    print('installed', len(reg), 'artefacts and apex/predict/registry.json')
n = sum(v['above_0.95']['n'] for v in ev.values())
print('out-of-sample sessions', len(ev), '| origins above each artefact\'s own 95 % line', n,
      '| pooled T', round(sum(v['above_0.95']['n'] * (v['above_0.95']['T'] or 0) for v in ev.values()) / max(n, 1), 3),
      'A', round(sum(v['above_0.95']['n'] * (v['above_0.95']['A'] or 0) for v in ev.values()) / max(n, 1), 3),
      'mean ret300 %', round(100 * sum(v['above_0.95']['n'] * (v['above_0.95']['mean_ret300'] or 0) for v in ev.values()) / max(n, 1), 3))
