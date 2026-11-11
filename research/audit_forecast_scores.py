"""Compare fitted raw scores with the deployed cumulative projection; no fitting."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apex.predict import models as Mo
from apex.predict.ledger import Forecaster

art = json.loads((ROOT/'apex/predict/model_v1.json').read_text())
z = np.load(ROOT/'data/research/predict/origins_v1.npz')
mc = {str(n): i for i, n in enumerate(z['mcols'])}
mask = (z['M'][:, mc['st']] == 1) & (z['M'][:, mc['first300']] != 3)
X = z['X'][mask].astype(float)
raw = {k: Mo.predict(m, X) for k, m in art['models'].items()}
lt, la = np.zeros(len(X)), np.zeros(len(X))
for h in (30,60,180,300):
    dt, da = np.maximum(raw[f'T{h}']-lt,0), np.maximum(raw[f'A{h}']-la,0)
    room = 1-lt-la
    scale = np.minimum(1, room/np.maximum(dt+da,1e-30))
    lt, la = lt+dt*scale, la+da*scale
actual = lt-la
base = raw['T300']-raw['A300']
fc = Forecaster(artefact=art)
for i in np.linspace(0,len(X)-1,31,dtype=int):
    assert abs(fc.forecast(X[i])['edge']-actual[i]) < 1e-10
result = dict(n=len(X), changed=int((np.abs(actual-base)>1e-10).sum()),
              max_abs_difference=float(np.max(np.abs(actual-base))), thresholds={})
for q,v in art['edge_quantiles'].items():
    result['thresholds'][q] = dict(line=v, raw_above=int((base>=v).sum()),
        deployed_above=int((actual>=v).sum()), decisions_changed=int(((base>=v)!=(actual>=v)).sum()))
out = ROOT/'data/research/codex_forecast_audit_2026-11-11'
out.mkdir(parents=True,exist_ok=True)
(out/'score_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
