"""11 Nov 2026 (docs/42 finding B): model_v2 = the SAME fitted weights as model_v1, with the entry / exit lines taken
from the deployed score (Forecaster.score: fitted probabilities, then the horizon projection) and not from the raw
T300 - A300. One scoring function for the lines and the engine. model_v1.json is left as it is.

Still discovery: the weights and the lines come from all 15 sessions (training_cutoff). Usage: py -3.13 make_artefact_v2.py [--install]"""
import json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import models as Mo
from apex.predict.ledger import Forecaster
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
art = json.load(open(os.path.join(ROOT, 'apex', 'predict', 'model_v1.json')))
z = np.load(os.path.join(OUT, 'origins_v1.npz'))
X, M = z['X'].astype(float), z['M']
mc = {str(n): i for i, n in enumerate(z['mcols'])}
obs = (M[:, mc['st']] == 1) & (M[:, mc['first300']] != 3)
fc = Forecaster(artefact=art)
assert fc.ok, fc.why
s = fc.edges(X[obs])
raw = Mo.predict(art['models']['T300'], X[obs]) - Mo.predict(art['models']['A300'], X[obs])
old = dict(art['edge_quantiles'])
art = dict(art, version=2, parent=art['hash'], score_pipeline='project_v1',
           edge_quantiles={q: float(np.quantile(s, float(q))) for q in ('0.5', '0.9', '0.95', '0.99')})
art['hash'] = Mo.model_hash(art)
print('rows', int(obs.sum()), 'old lines', old)
print('new lines', art['edge_quantiles'], 'hash', art['hash'])
for q in ('0.5', '0.95', '0.99'):
    print(q, 'above the old line, raw score', int((raw >= old[q]).sum()), '| above the old line, deployed score', int((s >= old[q]).sum()),
          '| above the new line, deployed score', int((s >= art['edge_quantiles'][q]).sum()))
json.dump(art, open(os.path.join(OUT, 'model_v2.json'), 'w'))
if '--install' in sys.argv:
    json.dump(art, open(os.path.join(ROOT, 'apex', 'predict', 'model_v2.json'), 'w'))
    print('installed apex/predict/model_v2.json')
