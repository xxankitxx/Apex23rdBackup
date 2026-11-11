"""10 Nov 2026 (docs/41 section 5): the frozen forecast artefact the engine loads (data/research/predict/model_v1.json
and a copy the engine reads: config.PREDICT_MODEL). Fitted on ALL 15 recorded sessions' unselected origins, so those
sessions are discovery material for it: its first honest test is the next live day or a tape recorded after 9 Nov.

Eight logistic models (target first / adverse first at 30, 60, 180, 300 s), the entry line (95th percentile of the
in-sample edge), the exit line (its median), and the momentum control's line (95th percentile of |mom30|).
Replaces the file walk_forward.py wrote before the damped-Newton fix (its A30 model had diverged)."""
import json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M = z['X'].astype(float), z['M']; days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
mc = {n: i for i, n in enumerate(z['mcols'])}
filled = M[:, mc['st']] == 1
art = dict(version=1, feature_schema=F.SCHEMA, target_spec=T.SPEC, training_cutoff=days[-1], training_days=days, l2=10.0,
           origins_sha256=json.load(open(os.path.join(OUT, 'origins_v1.manifest.json')))['sha256'], models={})
for kind, code in (('T', 1), ('A', 2)):
    for h in T.HORIZONS:
        f = M[:, mc[f'first{h}']]; obs = filled & (f != 3)
        m = Mo.fit_logit(X[obs], (f[obs] == code).astype(float), names, l2=10.0, meta=dict(target=f'{kind}{h}'))
        art['models'][f'{kind}{h}'] = m
        p = Mo.predict(m, X[obs])
        print(f'{kind}{h}', 'n', m['n'], 'base', round(m['base'], 4), 'in-sample auc', round(Mo.auc(p, f[obs] == code), 4))
f = M[:, mc['first300']]; obs = filled & (f != 3)
s = Mo.predict(art['models']['T300'], X[obs]) - Mo.predict(art['models']['A300'], X[obs])
art['edge_quantiles'] = {q: float(np.quantile(s, float(q))) for q in ('0.5', '0.9', '0.95', '0.99')}
art['mom30_q95'] = float(np.nanquantile(np.abs(X[obs][:, names.index('mom30')]), 0.95))
art['hash'] = Mo.model_hash(art)
json.dump(art, open(os.path.join(OUT, 'model_v1.json'), 'w'))
json.dump(art, open(os.path.join(ROOT, 'apex', 'predict', 'model_v1.json'), 'w'))      # the copy the engine loads (config.PREDICT_MODEL)
print('hash', art['hash'], 'edge quantiles', art['edge_quantiles'], 'mom30 line', art['mom30_q95'])
print('largest T300 weights', sorted(zip(names, np.round(art['models']['T300']['w'][1:], 3)), key=lambda kv: -abs(kv[1]))[:8])
print('largest A300 weights', sorted(zip(names, np.round(art['models']['A300']['w'][1:], 3)), key=lambda kv: -abs(kv[1]))[:8])
