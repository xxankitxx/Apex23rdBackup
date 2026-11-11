"""11 Nov 2026 (docs/42 finding A/4, docs/43 section 4): origins_v2. The same builder as build_origins.py with ONE
change, declared before any result: the contracts sampled are the at-the-money strike and the first FOUR strikes in
the money on each side (10 contracts), not the at-the-money and the first one. The owner's rule buys delta 0.52 to
0.85 depending on days to expiry, which is up to three or four strikes in the money; origins_v2 never contained
those contracts, so model_v1/v2 extrapolate to them. Column `itm` is now the depth 0..4. Output origins_v2.npz.

Original text: 10 Nov 2026 (docs/41 M2/M3): forecast origins from the recorded seconds (ds_v2), through the engine's own feature
class (apex.predict.features.Features) and the fixed-contract targets (apex.predict.targets). Read-only on ds_v2.

Sampling policy (declared here, before any result): every STEP_S = 5 seconds, four contracts of the near week: the
at-the-money call and put and the first in-the-money call and put. An origin exists whether or not anything traded:
this is the unselected population, not the champion's trades.

Output: data/research/predict/origins_v2.npz + origins_v2.manifest.json
Usage: py -3.13 build_origins.py [workers]"""
import glob, hashlib, json, os, sys, time
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex.predict import features as F, targets as T
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
STEP_S = 5
DEPTH = 4                    # strikes in the money sampled on each side, besides the at-the-money strike
H = T.HORIZONS
FIRST = {'T': 1, 'A': 2, 'N': 0, 'U': 3}


def one(path):
    z = np.load(path)
    name = os.path.basename(path)[:-4]
    day, exp = name[:10], str(z['expiry'])
    n = len(z['strikes'])
    order = np.argsort(z['strikes'])
    K = z['strikes'][order].astype(float)
    o = z['opt'][:, :n].astype(float)[:, order]
    age = z['age'][:, :n].astype(float)[:, order]
    bid, ask = o[..., 0], o[..., 1]
    ok = (bid > 0) & (ask > bid) & (age <= F.Q_FRESH_S)
    t = z['t'].astype(float); fut = z['fut'].astype(float); fa = z['fa'].astype(float)
    hw, hwa, sf, sfa, w = z['hw'].astype(float), z['hwa'].astype(float), z['sf'].astype(float), z['sfa'].astype(float), z['w'].astype(float)
    nh = min(hw.shape[1], len(w))
    dte = F.dte_days(day, exp)
    fs = F.Features()
    X, M = [], []
    for i in range(len(t)):
        fs.update(t[i], fut[i, 0], fut[i, 1], fa[i, 0], hw[i, :nh], hwa[i, :nh], sf[i, :nh, 0], sf[i, :nh, 1], sfa[i, :nh],
                  w[:nh], K, bid[i], ask[i], age[i], dte, dte == 0, F.tod_seconds(t[i]),
                  f_ltp=fut[i, 2], f_vol=fut[i, 3], bq=fut[i, 4], aq=fut[i, 5], d_age=fa[i, 1])
        if int(t[i]) % STEP_S or not fs.ready():
            continue
        k = fs.atm()
        if k is None or k < DEPTH or k > n - 1 - DEPTH:
            continue
        for kk, rr, itm in [(k - j, 0, j) for j in range(DEPTH + 1)] + [(k + j, 1, j) for j in range(DEPTH + 1)]:
            x = fs.contract(kk, rr)
            if x is None:
                continue
            L = T.label(t, bid[:, kk, rr], ask[:, kk, rr], ok[:, kk, rr], age[:, kk, rr], i)
            if L['st'] != 'ok':
                M.append([t[i], kk, rr, itm, K[kk], -1, np.nan] + [3] * len(H) + [np.nan] * len(H) + [np.nan, np.nan, np.nan])
            else:
                M.append([t[i], kk, rr, itm, K[kk], 1, L['entry']] + [FIRST[L['first'][h]] for h in H]
                         + [L['ret'][h] if L['ret'][h] is not None else np.nan for h in H]
                         + [L['t_hit'] if L['t_hit'] is not None else np.nan,
                            L['peak'] if L['peak'] is not None else np.nan, L['trough'] if L['trough'] is not None else np.nan])
            X.append(x)
        # the underlying's own later move (mid), for the direction forecast: stored once per origin on the ATM call row
    fm = 0.5 * (fut[:, 0] + fut[:, 1])
    idx = {float(a): j for j, a in enumerate(t)}
    M = np.array(M, float) if M else np.zeros((0, 10 + 2 * len(H)))
    fwd = np.full((len(M), len(H)), np.nan)
    for r in range(len(M)):
        i0 = idx[M[r, 0]]
        for c, h in enumerate(H):
            j = idx.get(M[r, 0] + 1 + h); j0 = idx.get(M[r, 0] + 1)
            if j is not None and j0 is not None and fa[j, 0] <= 3 and fa[j0, 0] <= 3:
                fwd[r, c] = fm[j] - fm[j0]
    return name, day, exp, np.array(X, float).reshape(len(M), len(F.NAMES)), M, fwd, fs.gaps


if __name__ == '__main__':
    from multiprocessing import Pool
    parts = sorted(glob.glob(os.path.join(DS, '*.npz')))
    t0 = time.time()
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as p:
        res = p.map(one, parts)
    res = [r for r in res if len(r[4])]
    res.sort(key=lambda r: r[4][0, 0])
    X = np.concatenate([r[3] for r in res]); M = np.concatenate([r[4] for r in res]); FW = np.concatenate([r[5] for r in res])
    days = sorted({r[1] for r in res})
    D = np.concatenate([np.full(len(r[4]), days.index(r[1])) for r in res])
    P = np.concatenate([np.full(len(r[4]), k) for k, r in enumerate(res)])
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, 'origins_v2.npz')
    np.savez_compressed(dst, X=X.astype(np.float32), M=M, FW=FW.astype(np.float32), D=D, P=P, days=np.array(days),
                        parts=np.array([r[0] for r in res]), names=np.array(F.NAMES),
                        mcols=np.array(['t', 'k', 'rr', 'itm', 'strike', 'st', 'entry'] + [f'first{h}' for h in H]
                                       + [f'ret{h}' for h in H] + ['t_hit', 'peak', 'trough']))
    man = dict(built=time.strftime('%Y-%m-%d %H:%M:%S'), rows=int(len(X)), days=days, parts=[r[0] for r in res],
               rows_by_part={r[0]: int(len(r[4])) for r in res}, gaps_by_part={r[0]: int(r[6]) for r in res},
               feature_schema=F.SCHEMA, features=list(F.NAMES), target_spec=T.SPEC, step_s=STEP_S,
               sampling='every 5 s: ATM and the first four ITM strikes, calls and puts, near week',
               sha256=hashlib.sha256(open(dst, 'rb').read()).hexdigest(), wall_s=round(time.time() - t0, 1))
    json.dump(man, open(os.path.join(OUT, 'origins_v2.manifest.json'), 'w'), indent=1)
    print(json.dumps({k: man[k] for k in ('rows', 'days', 'feature_schema', 'wall_s', 'gaps_by_part')}))
