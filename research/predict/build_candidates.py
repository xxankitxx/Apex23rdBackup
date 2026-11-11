"""11 Nov 2026 (docs/44 section 2 and M1): origins_v3, the aligned candidate table.

Two corrections to build_origins_v2.py, both from the review in docs/44, declared before any result:

1. EXECUTABLE TAG. Every 5 s the engine's own contract rule (paper.choose_contract: delta band by days to expiry,
   premium range, quote under 15 s, the expiry-day cut-off, the out-of-band fallback) is reconstructed for each
   side, and the contract it names is sampled and tagged exe=1, whatever its depth. Delta comes from the engine's
   own functions (apex.greeks: parity forward, Black-76 implied volatility on the mid, years_to_expiry).
   APPROXIMATION, stated: the parity forward's fallback reference is the future's mid (the engine uses spot when it
   has it), the price is the mid of bid and ask (the engine falls back to the last price without a two-sided quote,
   the recorded set has no last price), and the engine refreshes Greeks on its own cadence. So the tag is the
   reconstructed selector, not an exact replay of it. Agreement with real engine fills is measured separately
   (selector_agreement.py) and must be quoted with any claim that rests on the tag.

2. NO WHOLE-MOMENT SKIP. v2 dropped a timestamp when the at-the-money strike was fewer than four strikes from
   either edge of the recorded chain. Here each candidate is taken on its own: the at-the-money strike and up to
   four strikes in the money on each side, as many as the chain has. Missing ones are counted per part.

Three populations in one table (column `pop` is a bit mask): 1 = broad (one strike out of the money, at-the-money and four in the money),
2 = executable (the reconstructed engine pick). Champion decision episodes are a separate table (build_episodes.py).
Rows carry depth, delta, premium (mid), days to expiry and the fallback flag.

Output: data/research/predict/origins_v3.npz + origins_v3.manifest.json
Usage: py -3.13 research/predict/build_candidates.py [workers]"""
import glob, hashlib, json, os, sys, time
from datetime import datetime
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))   # no engine is built here
from apex import config, greeks
from apex.predict import features as F, targets as T
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
STEP_S = 5
DEPTH = 4
H = T.HORIZONS
FIRST = {'T': 1, 'A': 2, 'N': 0, 'U': 3}
MCOLS = (['t', 'k', 'rr', 'itm', 'strike', 'st', 'entry'] + [f'first{h}' for h in H] + [f'ret{h}' for h in H]
         + ['t_hit', 'peak', 'trough', 'pop', 'delta', 'mid', 'dte', 'fallback'])


def band_for(day, exp, now):
    """The engine's delta band and whether any entry is allowed, as paper.choose_contract (near week only)."""
    zero = day == exp
    hmn = now.hour * 60 + now.minute
    if zero:
        if hmn >= config.mins(config.ZERO_DTE_NO_ENTRY) or config.ZERO_DTE_USE_NEXTWEEK:
            return None                               # no near-week entry (cut-off, or the next week is used)
        return config.DELTA_BANDS['zero_am']
    dte = (np.datetime64(exp) - np.datetime64(day)).astype(int)
    return config.DELTA_BANDS['ge3'] if dte >= 3 else config.DELTA_BANDS['1to2']


def pick(delta, mid, age, band):
    """Index of the strike the engine would buy on one side, and the fallback flag; (None, 0) when there is none."""
    if band is None:
        return None, 0
    lo, hi = band
    ok = np.isfinite(delta) & np.isfinite(mid) & (mid >= config.MIN_PREMIUM) & (mid <= config.MAX_PREMIUM) & (age < 15)
    ad = np.abs(delta)
    inb = ok & (ad >= lo) & (ad <= hi)
    if inb.any():
        return int(np.where(inb, ad, np.inf).argmin()), 0
    ab = ok & (ad >= lo)
    if ab.any():
        return int(np.where(ab, ad, np.inf).argmin()), 1
    return None, 0


def chain_delta(K, bid_i, ask_i, age_i, fut_bid, fut_ask, exp, now):
    """(delta (n, 2), mid (n, 2)) of the near chain at one second, by the engine's own functions. Used by the
    selector-agreement check; one() carries the same arithmetic inline."""
    n = len(K)
    two = (bid_i > 0) & (ask_i > 0) & (ask_i >= bid_i) & (age_i <= config.IV_LEG_MAX_AGE_S)
    mid = np.where(two, 0.5 * (bid_i + ask_i), np.nan)
    delta = np.full((n, 2), np.nan)
    fm = 0.5 * (fut_bid + fut_ask) if fut_bid > 0 and fut_ask >= fut_bid else np.nan
    if np.isfinite(fm):
        Fw = greeks.synthetic_forward(K, mid[:, 0], mid[:, 1], fm)
        Ty = greeks.years_to_expiry(exp, now)
        if Fw and np.isfinite(Fw):
            Kc = np.r_[K, K]
            is_call = np.r_[np.ones(n, bool), np.zeros(n, bool)]
            m2 = np.r_[mid[:, 0], mid[:, 1]]
            with np.errstate(all='ignore'):
                iv = greeks.implied_vol(m2, np.full(2 * n, float(Fw)), Kc, Ty, is_call)
                dl = np.where(np.isfinite(iv) & np.isfinite(m2), greeks.greeks(np.full(2 * n, float(Fw)), Kc, Ty, iv, is_call)['delta'], np.nan)
            delta[:, 0], delta[:, 1] = dl[:n], dl[n:]
    return delta, mid


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
    stat = dict(origins=0, broad_missing_edge=0, broad_no_quote=0, exe_none=0, exe_rows=0, exe_deeper_than_4=0,
                exe_fallback=0, exe_off_quote=0, exe_depth={})
    Kc = np.r_[K, K]
    is_call = np.r_[np.ones(n, bool), np.zeros(n, bool)]
    for i in range(len(t)):
        fs.update(t[i], fut[i, 0], fut[i, 1], fa[i, 0], hw[i, :nh], hwa[i, :nh], sf[i, :nh, 0], sf[i, :nh, 1], sfa[i, :nh],
                  w[:nh], K, bid[i], ask[i], age[i], dte, dte == 0, F.tod_seconds(t[i]),
                  f_ltp=fut[i, 2], f_vol=fut[i, 3], bq=fut[i, 4], aq=fut[i, 5], d_age=fa[i, 1])
        if int(t[i]) % STEP_S or not fs.ready():
            continue
        k = fs.atm()
        if k is None:
            continue
        stat['origins'] += 1
        now = datetime.fromtimestamp(t[i], config.IST)
        # the engine's Greeks for the whole near chain, from this second's quotes only
        two = (bid[i] > 0) & (ask[i] > 0) & (ask[i] >= bid[i]) & (age[i] <= config.IV_LEG_MAX_AGE_S)
        mid = np.where(two, 0.5 * (bid[i] + ask[i]), np.nan)                    # (n, 2)
        fm = 0.5 * (fut[i, 0] + fut[i, 1]) if fut[i, 0] > 0 and fut[i, 1] >= fut[i, 0] else np.nan
        delta = np.full((n, 2), np.nan)
        if np.isfinite(fm):
            Fw = greeks.synthetic_forward(K, mid[:, 0], mid[:, 1], fm)
            Ty = greeks.years_to_expiry(exp, now)
            if Fw and np.isfinite(Fw):
                m2 = np.r_[mid[:, 0], mid[:, 1]]
                with np.errstate(all='ignore'):
                    iv = greeks.implied_vol(m2, np.full(2 * n, float(Fw)), Kc, Ty, is_call)
                    dl = np.where(np.isfinite(iv) & np.isfinite(m2), greeks.greeks(np.full(2 * n, float(Fw)), Kc, Ty, iv, is_call)['delta'], np.nan)
                delta[:, 0], delta[:, 1] = dl[:n], dl[n:]
        band = band_for(day, exp, now)
        cand = {}                                      # (kk, rr) -> [pop, depth, fallback]
        for rr, sgn in ((0, -1), (1, 1)):
            for j in range(-1, DEPTH + 1):            # -1: the forecaster's "at the money" follows the future, the engine's
                kk = k + sgn * j                      # delta follows the parity forward; the pick is often one strike across
                if 0 <= kk < n:
                    cand[(kk, rr)] = [1, j, 0]
                else:
                    stat['broad_missing_edge'] += 1
            kx, fb = pick(delta[:, rr], mid[:, rr], age[i, :, rr], band)
            if kx is None:
                stat['exe_none'] += 1
                continue
            depth = (k - kx) if rr == 0 else (kx - k)
            c = cand.setdefault((kx, rr), [0, depth, 0])
            c[0] |= 2
            c[2] = fb
            stat['exe_rows'] += 1
            stat['exe_fallback'] += fb
            stat['exe_deeper_than_4'] += depth > DEPTH
            stat['exe_depth'][int(depth)] = stat['exe_depth'].get(int(depth), 0) + 1
        for (kk, rr), (pop, depth, fb) in cand.items():
            x = fs.contract(kk, rr)
            if x is None:
                stat['broad_no_quote'] += bool(pop & 1)
                stat['exe_off_quote'] += bool(pop & 2)
                continue
            L = T.label(t, bid[:, kk, rr], ask[:, kk, rr], ok[:, kk, rr], age[:, kk, rr], i)
            tail = [pop, delta[kk, rr], mid[kk, rr], dte, fb]
            if L['st'] != 'ok':
                M.append([t[i], kk, rr, depth, K[kk], -1, np.nan] + [3] * len(H) + [np.nan] * len(H) + [np.nan, np.nan, np.nan] + tail)
            else:
                M.append([t[i], kk, rr, depth, K[kk], 1, L['entry']] + [FIRST[L['first'][h]] for h in H]
                         + [L['ret'][h] if L['ret'][h] is not None else np.nan for h in H]
                         + [L['t_hit'] if L['t_hit'] is not None else np.nan,
                            L['peak'] if L['peak'] is not None else np.nan, L['trough'] if L['trough'] is not None else np.nan] + tail)
            X.append(x)
    M = np.array(M, float) if M else np.zeros((0, len(MCOLS)))
    return name, day, exp, np.array(X, float).reshape(len(M), len(F.NAMES)), M, stat, fs.gaps


if __name__ == '__main__':
    from multiprocessing import Pool
    parts = sorted(glob.glob(os.path.join(DS, '*.npz')))
    t0 = time.time()
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as p:
        res = p.map(one, parts)
    res = [r for r in res if len(r[4])]
    res.sort(key=lambda r: r[4][0, 0])
    X = np.concatenate([r[3] for r in res]); M = np.concatenate([r[4] for r in res])
    days = sorted({r[1] for r in res})
    D = np.concatenate([np.full(len(r[4]), days.index(r[1])) for r in res])
    P = np.concatenate([np.full(len(r[4]), k) for k, r in enumerate(res)])
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, 'origins_v3.npz')
    np.savez_compressed(dst, X=X.astype(np.float32), M=M, D=D, P=P, days=np.array(days), parts=np.array([r[0] for r in res]),
                        names=np.array(F.NAMES), mcols=np.array(MCOLS))
    tot = {}
    for r in res:
        for k_, v in r[5].items():
            if isinstance(v, dict):
                d = tot.setdefault(k_, {})
                for a, b in v.items():
                    d[a] = d.get(a, 0) + b
            else:
                tot[k_] = tot.get(k_, 0) + int(v)
    pc = {c: i for i, c in enumerate(MCOLS)}
    exe = (M[:, pc['pop']].astype(int) & 2) > 0
    man = dict(built=time.strftime('%Y-%m-%d %H:%M:%S'), rows=int(len(X)), rows_broad=int(((M[:, pc['pop']].astype(int) & 1) > 0).sum()),
               rows_executable=int(exe.sum()), days=days, parts=[r[0] for r in res], feature_schema=F.SCHEMA,
               features=list(F.NAMES), target_spec=T.SPEC, step_s=STEP_S, depth=DEPTH, coverage=tot,
               by_part={r[0]: {k_: v for k_, v in r[5].items()} for r in res},
               executable_delta_quantiles=[float(q) for q in np.nanquantile(np.abs(M[exe, pc['delta']]), [0.05, 0.25, 0.5, 0.75, 0.95])] if exe.any() else None,
               executable_premium_quantiles=[float(q) for q in np.nanquantile(M[exe, pc['mid']], [0.05, 0.25, 0.5, 0.75, 0.95])] if exe.any() else None,
               selector='reconstructed paper.choose_contract (default book): see the approximation in this file\'s header',
               sha256=hashlib.sha256(open(dst, 'rb').read()).hexdigest(), wall_s=round(time.time() - t0, 1))
    json.dump(man, open(os.path.join(OUT, 'origins_v3.manifest.json'), 'w'), indent=1)
    print(json.dumps({k_: man[k_] for k_ in ('rows', 'rows_broad', 'rows_executable', 'days', 'coverage', 'executable_delta_quantiles',
                                             'executable_premium_quantiles', 'wall_s')}, indent=1))
