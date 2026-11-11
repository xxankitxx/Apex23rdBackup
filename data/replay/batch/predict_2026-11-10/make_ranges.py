"""10 Nov 2026, evening (docs/41 section 12.3): the frozen premium-RANGE artefact for the live forecast record.

The direct location-scale model of ranges_greeks.py / ranges_greeks2.py (chosen by the rule declared in
ranges_greeks2.py), fitted on ALL 15 recorded sessions, horizons 60 s and 300 s:
  quantile q of the quote-aware return of the fixed contract = mean(x) + scale(x) * zq[q]
  mean and scale are ridge models on the standardised, clipped features; scale has a floor.
Those sessions are discovery material for it: its first honest test is a day after 9 Nov.
A SEPARATE file from model_v1.json, so the probability model and its hash are untouched.
Output: data/research/predict/ranges_v1.json (the engine's copy apex/predict/ranges_v1.json is written with --install)."""
import hashlib, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M = z['X'].astype(float), z['M']
days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
mc = {n: i for i, n in enumerate(z['mcols'])}
QS = (0.1, 0.5, 0.9)
L2 = 10.0
CLIP = 4.0


def ridge(A, y):
    med = np.nanmedian(A, 0); sd = np.nanstd(A, 0); sd = np.where(sd > 0, sd, 1.0)
    Z = np.c_[np.ones(len(A)), np.clip(np.nan_to_num((A - med) / sd), -CLIP, CLIP)]
    P = L2 * np.eye(Z.shape[1]); P[0, 0] = 0
    w = np.linalg.solve(Z.T @ Z + P, Z.T @ y)
    return med, sd, w, Z @ w


art = dict(version=1, kind='premium return range, direct location-scale', feature_schema=F.SCHEMA, target_spec=T.SPEC,
           training_cutoff=days[-1], training_days=days, l2=L2, clip=CLIP, quantiles=list(QS), horizons={})
for h in (60, 300):
    y = M[:, mc[f'ret{h}']]
    ok = (M[:, mc['st']] == 1) & np.isfinite(y)
    med, sd, w_mu, fit = ridge(X[ok], y[ok])
    r = y[ok] - fit
    _, _, w_sc, sfit = ridge(X[ok], np.abs(r))
    floor = 0.25 * float(np.abs(r).mean())
    s = np.maximum(sfit, floor)
    zq = [float(v) for v in np.quantile(r / s, QS)]
    q = fit[:, None] + s[:, None] * np.array(zq)[None, :]
    cover = float(((y[ok] >= q[:, 0]) & (y[ok] <= q[:, 2])).mean())
    art['horizons'][str(h)] = dict(n=int(ok.sum()), med=[float(v) for v in med], sd=[float(v) for v in sd],
                                   w_mu=[float(v) for v in w_mu], w_sc=[float(v) for v in w_sc], floor=floor, zq=zq,
                                   in_sample_coverage=round(cover, 4), in_sample_median_width=round(float(np.median(q[:, 2] - q[:, 0])), 4))
    print(h, 'n', int(ok.sum()), 'zq', [round(v, 3) for v in zq], 'floor', round(floor, 5), 'in-sample coverage', round(cover, 4),
          'median width', art['horizons'][str(h)]['in_sample_median_width'])
art['hash'] = hashlib.sha256(json.dumps(art, sort_keys=True).encode()).hexdigest()[:12]
json.dump(art, open(os.path.join(OUT, 'ranges_v1.json'), 'w'))
print('hash', art['hash'])
if '--install' in sys.argv:
    json.dump(art, open(os.path.join(ROOT, 'apex', 'predict', 'ranges_v1.json'), 'w'))
    print('installed for the engine')
