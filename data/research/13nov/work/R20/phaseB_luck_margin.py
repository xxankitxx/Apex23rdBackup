"""PHASE B (run after 15:30 only; about 10-20 minutes): luck margin for the side-loss lock.
Null: lock the same NUMBER of pool triggers per day as the real side lock refused, but chosen at random among the
triggers that reached the flat account. 500 draws. Reports where the real lock's strike rate, sum of daily % and worst
day fall in the null distribution (the promotion standard's "beats by the luck margin", docs/28 section 2).
    py -3.13 phaseB_luck_margin.py"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import functools
from mc_lib import *

print = functools.partial(print, flush=True)
df = load()
df = df[['day', 'book', 'fam', 'trig', 't_in', 't_out', 'ret_pct', 'rr', 'win']].copy()
for c in ('day', 'book', 'fam', 'rr'):
    df[c] = df[c].astype(object)
DAYS = sorted(df.day.unique())
PRIO = {b: i for i, b in enumerate(POOL)}
G = {d: g for d, g in df.groupby('day')}
C20 = {'c20pool', 'c20ext'}


def real(N=12):
    tk, nref = {}, {}
    for d in DAYS:
        tp = G[d][G[d].fam.isin(C20)].sort_values('t_out')
        tt, rr, ww = tp.t_out.to_numpy(float), tp.rr.tolist(), tp.win.tolist()
        st = {'k': 0, 'CE': [], 'PE': [], 'ref': 0}

        def acc(r, st=st, tt=tt, rr=rr, ww=ww):
            while st['k'] < len(tt) and tt[st['k']] < r.trig:
                st[rr[st['k']]].append(ww[st['k']]); st['k'] += 1
            w = st[r.rr][-N:]
            ok = not (len(w) >= 3 and len(w) - sum(w) > sum(w))
            st['ref'] += (not ok)
            return ok
        tk[d] = sim_day(G[d], acc, books=POOL, prio=PRIO)
        nref[d] = st['ref']
    return tk, nref


def rand(nref, rng):
    tk = {}
    for d in DAYS:
        n_trig = len(G[d][G[d].book.isin(POOL)])
        p = min(1.0, nref[d] / max(n_trig, 1) * 2.0)    # refusal probability matched roughly to the real count
        tk[d] = sim_day(G[d], lambda r: rng.random() >= p, books=POOL, prio=PRIO)
    return tk


tk, nref = real()
R = score(df, tk, 'real')
rng = np.random.default_rng(7)
null = [score(df, rand(nref, rng)) for _ in range(500)]
Nl = pd.DataFrame(null)
for k in ('all_strike', 'all_sum', 'all_worst', 'late_strike', 'late_sum'):
    print(k, 'real', round(R[k], 2), 'null p50', round(Nl[k].median(), 2), 'share of null >= real', round((Nl[k] >= R[k]).mean(), 3))
Nl.drop(columns=['_perday']).to_csv('phaseB_luck_null.csv', index=False)
