"""10 Nov 2026 (docs/41 section 4, the owner's first question): does the forecast tell the champion family's good
entries from its bad ones?  This is P01 `forecast_select` off-policy.

For every c20-family entry episode of the 14 replay days (batch v3_*) and the Conductor's 12 live trades of 9 Nov,
the engine's feature class is run over the recorded seconds and read at the trigger second for the traded contract.
The forecast for an episode on day d comes from models fitted on the UNSELECTED origins of days before d only
(origins_v1; at least 5 days), so no champion outcome and no same-day data is ever in the fit.

Read-only. Output: data/research/predict/champ_forecast.json"""
import collections, glob, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T, models as Mo
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')


def episodes():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data/replay/batch/v3_2026-*/paper/2026-*.json'))):
        d = json.load(open(f, encoding='utf-8')); day = os.path.basename(f)[:10]
        for n, b in d.items():
            if n.startswith('c20'):
                rows += [(day, n, t) for t in b['trades']]
    live = os.path.join(ROOT, 'data/paper/2026-11-09.json')
    if os.path.exists(live):
        d = json.load(open(live, encoding='utf-8'))
        rows += [('2026-11-09', 'conductor', t) for t in (d.get('conductor') or {}).get('trades', [])]
    ep = collections.OrderedDict()
    for day, n, t in rows:
        if t.get('trigger_t') is None or t.get('ret_pct') is None:
            continue
        ep.setdefault((day, t['key'], round(t['trigger_t'] / 5)), []).append((n, t))
    E = []
    for (day, key, _), v in ep.items():
        ts = [t for _, t in v]
        _, _, exp, strike, right = key.split('|')
        rets = [t['ret_pct'] for t in ts]
        E.append(dict(day=day, key=key, exp=exp, strike=float(strike), rr=0 if right == 'CE' else 1,
                      t=float(min(t['trigger_t'] for t in ts)), ret=float(np.mean(rets)), best=float(max(rets)), worst=float(min(rets)),
                      peak=float(max(100.0 * t['peak_pts'] / t['entry'] for t in ts)), n=len(ts), books=sorted({n for n, _ in v}),
                      live=(v[0][0] == 'conductor'), time=ts[0].get('trigger_time') or ts[0].get('time_in')))
    return E


def feats_for_part(args):
    path, want = args
    z = np.load(path); name = os.path.basename(path)[:-4]; day, exp = name[:10], str(z['expiry'])
    n = len(z['strikes']); order = np.argsort(z['strikes']); K = z['strikes'][order].astype(float)
    o = z['opt'][:, :n].astype(float)[:, order]; age = z['age'][:, :n].astype(float)[:, order]
    bid, ask = o[..., 0], o[..., 1]
    t = z['t'].astype(float); fut = z['fut'].astype(float); fa = z['fa'].astype(float)
    hw, hwa, sf, sfa, w = z['hw'].astype(float), z['hwa'].astype(float), z['sf'].astype(float), z['sfa'].astype(float), z['w'].astype(float)
    nh = min(hw.shape[1], len(w)); dte = F.dte_days(day, exp)
    by_sec = collections.defaultdict(list)
    for j, e in want:
        by_sec[int(e['t'])].append((j, e))
    last = max(by_sec) if by_sec else -1
    fs = F.Features(); out = {}
    for i in range(len(t)):
        if t[i] > last:
            break
        fs.update(t[i], fut[i, 0], fut[i, 1], fa[i, 0], hw[i, :nh], hwa[i, :nh], sf[i, :nh, 0], sf[i, :nh, 1], sfa[i, :nh],
                  w[:nh], K, bid[i], ask[i], age[i], dte, dte == 0, F.tod_seconds(t[i]),
                  f_ltp=fut[i, 2], f_vol=fut[i, 3], bq=fut[i, 4], aq=fut[i, 5], d_age=fa[i, 1])
        for j, e in by_sec.get(int(t[i]), ()):
            if e['exp'] != exp:
                out[j] = ('other expiry', None); continue
            kk = np.where(K == e['strike'])[0]
            if not len(kk):
                out[j] = ('strike not recorded', None); continue
            x = fs.contract(int(kk[0]), e['rr'])
            out[j] = ('ok', x.tolist()) if x is not None else ('not ready or no fresh quote', None)
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    E = episodes()
    jobs = []
    for path in sorted(glob.glob(os.path.join(DS, '*.npz'))):
        z = np.load(path); t = z['t']
        if not len(t):
            continue
        day = os.path.basename(path)[:10]
        want = [(j, e) for j, e in enumerate(E) if e['day'] == day and t[0] <= int(e['t']) <= t[-1]]
        if want:
            jobs.append((path, want))
    with Pool(4) as p:
        got = {}
        for r in p.map(feats_for_part, jobs):
            got.update(r)
    z = np.load(os.path.join(OUT, 'origins_v1.npz'))
    X, M, D = z['X'].astype(float), z['M'], z['D']; days, names = list(z['days']), list(z['names']); mc = {n: i for i, n in enumerate(z['mcols'])}
    filled = M[:, mc['st']] == 1
    models = {}

    def model(d, tgt):
        if (d, tgt) not in models:
            f = M[:, mc[f'first{tgt[1:]}']]; obs = filled & (f != 3) & (D < d)
            models[(d, tgt)] = Mo.fit_logit(X[obs], (f[obs] == (1 if tgt[0] == 'T' else 2)).astype(float), names, l2=10.0)
        return models[(d, tgt)]
    status = collections.Counter(); R = []
    for j, e in enumerate(E):
        st, x = got.get(j, ('second not recorded', None))
        d = days.index(e['day']) if e['day'] in days else -1
        if st == 'ok' and d < 5:
            st = 'fewer than 5 earlier days'
        status[st] += 1
        if st != 'ok':
            continue
        x = np.array(x)
        p = {tg: float(Mo.predict(model(d, tg), x)[0]) for tg in ('T60', 'T300', 'A60', 'A300')}
        R.append(dict(e, edge=p['T300'] - p['A300'], **p))
    print('episodes', len(E), dict(status))
    ret = np.array([r['ret'] for r in R]); edge = np.array([r['edge'] for r in R]); pT = np.array([r['T300'] for r in R]); pA = np.array([r['A300'] for r in R])
    win = ret > 0
    rng = np.random.default_rng(5)

    def perm(s, y, n=5000):
        a = Mo.auc(s, y); return a, float(np.mean([Mo.auc(s, rng.permutation(y)) >= a for _ in range(n)]))
    out = dict(episodes=len(E), status=dict(status), scored=len(R), win_rate=round(float(win.mean()), 3), sum_ret=round(float(ret.sum()), 1), tests={})
    for nm, s in (('edge = pT300 - pA300', edge), ('pT300', pT), ('minus pA300', -pA), ('pT60', np.array([r['T60'] for r in R]))):
        for tn, y in (('won', win), ('developed: peak 5 % or more', np.array([r['peak'] for r in R]) >= 5),
                      ('runner: best sibling 20 % or more', np.array([r['best'] for r in R]) >= 20)):
            a, pv = perm(s, y)
            out['tests'][f'{nm} -> {tn}'] = dict(auc=round(a, 3), shuffle_p=round(pv, 4), positives=int(y.sum()), n=len(y))
            print(f'{nm:24s} -> {tn:34s} AUC {a:.3f}  shuffle p {pv:.4f}  ({int(y.sum())} of {len(y)})')
    med = np.median(edge)
    for lab, m in (('upper half of edge', edge >= med), ('lower half of edge', edge < med), ('edge above 0', edge > 0), ('edge at or below 0', edge <= 0)):
        if m.sum():
            out['tests'][lab] = dict(n=int(m.sum()), won=int(win[m].sum()), lost=int((~win[m]).sum()), sum_ret=round(float(ret[m].sum()), 1),
                                     mean_ret=round(float(ret[m].mean()), 2), runners_kept=int((np.array([r['best'] for r in R])[m] >= 20).sum()))
            print(lab, out['tests'][lab])
    out['rows'] = [dict(day=r['day'], time=r['time'], key=r['key'], live=r['live'], ret=round(r['ret'], 2), best=round(r['best'], 2), peak=round(r['peak'], 1),
                        edge=round(r['edge'], 4), pT300=round(r['T300'], 3), pA300=round(r['A300'], 3)) for r in R]
    print('9 Nov live trades (Conductor):')
    for r in out['rows']:
        if r['live']:
            print('  ', r)
    json.dump(out, open(os.path.join(OUT, 'champ_forecast.json'), 'w'), indent=1)
