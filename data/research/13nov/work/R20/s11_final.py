"""R20: side-loss lock for c20 plus hand-off of the locked side to the pullback families (t28, lvl), whose own
losing side tends to turn (s09). One account, all-in, walk-forward scoring (rules declared from s09 early days)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import functools
import time
from mc_lib import *

print = functools.partial(print, flush=True)
t0 = time.time()
df = load()
df = df[['day', 'book', 'fam', 'trig', 't_in', 't_out', 'ret_pct', 'rr', 'win']].copy()
for c in ('day', 'book', 'fam', 'rr'):
    df[c] = df[c].astype(object)
DAYS = sorted(df.day.unique())
PRIO0 = {b: i for i, b in enumerate(POOL)}
G = {d: g for d, g in df.groupby('day')}
static = {d: sim_day(G[d], books=POOL, prio=PRIO0) for d in DAYS}
early = df[df.day <= EARLY_END]
C20 = {'c20pool', 'c20ext'}


def run(helpers, mode, N=12):
    hb = sorted(df[df.fam.isin(helpers)].book.unique())
    er = early[early.book.isin(hb)].groupby('book').ret_pct.mean()          # early-days rank only
    hb = [b for b in er.sort_values(ascending=False).index if er[b] > 0]
    prio = dict(PRIO0); prio.update({b: 10 + i for i, b in enumerate(hb)})
    books = POOL + hb
    tk = {}
    for d in DAYS:
        g = G[d]
        tp = g[g.fam.notna()].sort_values('t_out')
        tt = tp.t_out.to_numpy(float); ff = tp.fam.tolist(); rr = tp.rr.tolist(); ww = tp.win.tolist()
        st = {'k': 0}

        def side(key, r):
            w = st.get(key, [])[-N:]
            return len(w) >= 3 and (len(w) - sum(w)) > sum(w)        # True = this side is losing today

        def acc(r, st=st, tt=tt, ff=ff, rr=rr, ww=ww):
            while st['k'] < len(tt) and tt[st['k']] < r.trig:
                k = st['k']
                fk = 'c20' if ff[k] in C20 else ff[k]
                st.setdefault((fk, rr[k]), []).append(ww[k]); st['k'] += 1
            c20_lock = side(('c20', r.rr), r)
            if r.fam == 'c20pool':
                return not c20_lock
            if mode == 'c20locked':           # helper may trade a side only while c20 is locked on it
                return c20_lock
            if mode == 'ownlosing':           # helper may trade a side only while its own family is losing on it
                return side((r.fam, r.rr), r)
            if mode == 'both':
                return c20_lock and side((r.fam, r.rr), r)
            return True
        tk[d] = sim_day(g, acc, books=books, prio=prio)
    return tk



def woBT(tk):
    t = df.loc[[i for v in tk.values() for i in v]]
    bi = t.ret_pct.idxmax()
    return {d: [i for i in v if i != bi] for d, v in tk.items()}
rows = []
cands = [(['t28'], 'both'), (['lvl'], 'ownlosing'), (['t28', 'lvl'], 'both')]
for helpers, mode in cands:
    for N in (6, 12, 999):
        tk = run(helpers, mode, N)
        sc = score(df, tk, f"lock+{'+'.join(helpers)} {mode} N{N}")
        sc['kept'], _ = top_kept(df, tk, static)
        s2 = score(df, woBT(tk))
        sc['woBT'] = s2['all_sum']; sc['late_woBT'] = s2['late_sum']; sc['late_woBD'] = sc['late_woBD']
        rows.append(sc)
        if N == 12:
            t = df.loc[[i for v in tk.values() for i in v]]
            t = t[t.day > EARLY_END]
            print(sc['label'], 'late per day (n, strike, ret):')
            print(t.groupby('day').agg(n=('ret_pct', 'size'), strike=('win', 'mean'), ret=('ret_pct', day_ret)).round(2).to_string())
            pd.to_pickle(tk, f"tk_{'_'.join(helpers)}_{mode}.pkl")
sc = score(df, static, 'static'); sc['kept'] = 12
s2 = score(df, woBT(static)); sc['woBT'] = s2['all_sum']; sc['late_woBT'] = s2['late_sum']
rows.append(sc)
t = df.loc[[i for v in static.values() for i in v]]; t = t[t.day > EARLY_END]
print('static late per day'); print(t.groupby('day').agg(n=('ret_pct', 'size'), strike=('win', 'mean'), ret=('ret_pct', day_ret)).round(2).to_string())
R = pd.DataFrame(rows)
pd.set_option('display.width', 260)
cols = ['label', 'all_strike', 'all_n', 'all_sum', 'all_lose', 'all_worst', 'all_woBD', 'woBT', 'early_strike', 'early_sum',
        'late_strike', 'late_n', 'late_sum', 'late_lose', 'late_worst', 'late_woBD', 'late_woBT', 'kept']
print(R[cols].round(1).to_string())
R.to_pickle('final_candidates.pkl')
