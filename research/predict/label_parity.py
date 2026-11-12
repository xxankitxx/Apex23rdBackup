"""11 Nov 2026 (docs/44 M0 "label parity"): do the outcomes the LIVE engine wrote today equal the labels the offline
function gives for the same forecast on the same day's recorded tape?

Live: data/paper/forecasts_<day>.jsonl (role "sample": instrument "strike|side", issued_t) and outcomes_<day>.jsonl
(kind "outcome": status, first per horizon, t_hit). Offline: apex.predict.targets.label on data/research/ds_v2/<day>*.
Compared per forecast: filled or lapsed; the first event at each horizon. Differences are counted by kind, and the
first few are printed, so each can be explained. Usage: py -3.13 research/predict/label_parity.py 2026-11-11"""
import glob, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex.predict import features as F, targets as T
day = sys.argv[1]
PAPER = os.path.join(ROOT, 'data', 'paper')
fc = {}
for line in open(os.path.join(PAPER, f'forecasts_{day}.jsonl'), encoding='utf-8'):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if r.get('role') == 'sample':
        fc[r['forecast_id']] = r
out = {}
for line in open(os.path.join(PAPER, f'outcomes_{day}.jsonl'), encoding='utf-8'):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if r.get('kind') == 'outcome' and r['forecast_id'] in fc:
        out[r['forecast_id']] = r
parts = []
for p in sorted(glob.glob(os.path.join(ROOT, 'data', 'research', 'ds_v2', f'{day}*.npz'))):
    z = np.load(p)
    if z['t'].ndim != 1 or not len(z['t']):
        continue
    n = len(z['strikes']); order = np.argsort(z['strikes'])
    o = z['opt'][:, :n].astype(float)[:, order]
    age = z['age'][:, :n].astype(float)[:, order]
    parts.append(dict(t=z['t'].astype(float), K=z['strikes'][order].astype(float), bid=o[..., 0], ask=o[..., 1], age=age))
res = dict(day=day, live_samples=len(fc), with_outcome=len(out), compared=0, not_on_tape=0, fill_same=0, fill_diff=0,
           by_h={h: dict(same=0, diff=0, pairs={}) for h in T.HORIZONS})
examples = []
for fid, f in fc.items():
    lv = out.get(fid)
    if lv is None or lv.get('status') in ('restart', 'censored_capacity'):
        continue
    k, side = f['instrument'].split('|')
    rr = 0 if side == 'CE' else 1
    ts = int(f['issued_t'])
    P = next((q for q in parts if q['t'][0] <= ts <= q['t'][-1]), None)
    if P is None:
        res['not_on_tape'] += 1
        continue
    j = np.where(P['K'] == float(k))[0]
    i = int(np.searchsorted(P['t'], ts))
    if not len(j) or i >= len(P['t']) or P['t'][i] != ts:
        res['not_on_tape'] += 1
        continue
    j = int(j[0])
    bid, ask, age = P['bid'][:, j, rr], P['ask'][:, j, rr], P['age'][:, j, rr]
    ok = (bid > 0) & (ask > bid) & (age <= F.Q_FRESH_S)
    L = T.label(P['t'], bid, ask, ok, age, i)
    res['compared'] += 1
    live_ok = lv.get('status') == 'ok'
    if live_ok != (L['st'] == 'ok'):
        res['fill_diff'] += 1
        if len(examples) < 6:
            examples.append(dict(kind='fill', t=ts, inst=f['instrument'], live=lv.get('status'), offline=L['st']))
        continue
    res['fill_same'] += 1
    if not live_ok:
        continue
    for h in T.HORIZONS:
        a = (lv.get('first') or {}).get(str(h))
        b = L['first'][h]
        d = res['by_h'][h]
        if a is None:                                   # the live queue closed at the first event: later horizons unset
            a = lv['first'].get(str(max(T.HORIZONS))) if False else None
        if a is None:
            d['pairs']['live_unset'] = d['pairs'].get('live_unset', 0) + 1
            continue
        if a == b:
            d['same'] += 1
        else:
            d['diff'] += 1
            d['pairs'][f'{a}->{b}'] = d['pairs'].get(f'{a}->{b}', 0) + 1
            if len(examples) < 12:
                examples.append(dict(kind=f'first{h}', t=ts, inst=f['instrument'], live=a, offline=b, live_t_hit=lv.get('t_hit'), off_t_hit=L['t_hit']))
json.dump(dict(res, examples=examples), open(os.path.join(ROOT, 'data', 'research', 'predict', f'label_parity_{day}.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'by_h'}))
for h, d in res['by_h'].items():
    n = d['same'] + d['diff']
    print(f"  horizon {h:3d} s: same {d['same']}, different {d['diff']} ({100 * d['diff'] / max(n, 1):.2f} %), kinds {d['pairs']}")
for e in examples:
    print('  ', e)
