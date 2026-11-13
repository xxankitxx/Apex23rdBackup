"""R20: the declared side-loss lock (from the dir1 gate family) and its Thompson-sampling twin, scored per day."""
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
PRIO = {b: i for i, b in enumerate(POOL)}
G = {d: g for d, g in df.groupby('day')}
static = {d: sim_day(G[d], books=POOL, prio=PRIO) for d in DAYS}
FSET = {'c20pool', 'c20ext'}


def tapes(g):
    g = g[g.fam.isin(FSET)].sort_values('t_out')
    return g.t_out.to_numpy(float), g.rr.to_numpy(object).tolist(), g.win.to_numpy(int).tolist()


def run(rule, N=12, nmin=3, seed=None):
    rng = np.random.default_rng(seed)
    tk, refused = {}, []
    for d in DAYS:
        tt, rr, ww = tapes(G[d])
        st = {'k': 0, 'CE': [], 'PE': []}

        def acc(r, st=st, tt=tt, rr=rr, ww=ww, d=d):
            while st['k'] < len(tt) and tt[st['k']] < r.trig:
                st[rr[st['k']]].append(ww[st['k']]); st['k'] += 1
            w = st[r.rr][-N:]
            n, k = len(w), sum(w)
            if rule == 'none' or n < nmin:
                ok = True
            elif rule == 'lose_gt_win':
                ok = not (n - k > k)
            elif rule == 'lose_ge_win':
                ok = not (n - k >= k)
            elif rule == 'ts':                       # Thompson: sample p ~ Beta(1+k, 1+n-k), trade if p >= 0.5
                ok = rng.beta(1 + k, 1 + n - k) >= 0.5
            if not ok:
                refused.append((d, r.Index, r.book, r.rr, r.ret_pct, n, k))
            return ok
        tk[d] = sim_day(G[d], acc, books=POOL, prio=PRIO)
    return tk, refused


def full(tk, label):
    sc = score(df, tk, label)
    sc['kept'], sc['top'] = top_kept(df, tk, static)
    t = df.loc[[i for v in tk.values() for i in v]]
    # without the single best trade: remove it from its day and recompound
    bi = t.ret_pct.idxmax()
    tk2 = {d: [i for i in v if i != bi] for d, v in tk.items()}
    sc['woBT'] = score(df, tk2)['all_sum']
    e = t.day <= EARLY_END
    sc['late_woBT'] = score(df, {d: v for d, v in tk2.items() if d > EARLY_END})['all_sum']
    return sc


rows = []
for rule in ('none', 'lose_gt_win', 'lose_ge_win'):
    for N in (6, 12, 999):
        if rule == 'none' and N != 12:
            continue
        tk, ref = run(rule, N)
        sc = full(tk, f'{rule} N{N}')
        rows.append(sc)
        if rule == 'lose_gt_win' and N == 12:
            REF = pd.DataFrame(ref, columns=['day', 'ix', 'book', 'rr', 'ret', 'n', 'k'])
            PD = sc['_perday']
            TK = tk
ts = []
for s in range(12):
    tk, _ = run('ts', 12, seed=s)
    ts.append(full(tk, f'ts seed{s}'))
TS = pd.DataFrame(ts)
R = pd.DataFrame(rows)
pd.set_option('display.width', 250)
cols = ['label', 'all_strike', 'all_n', 'all_sum', 'all_lose', 'all_worst', 'all_woBD', 'woBT', 'early_strike', 'early_sum',
        'late_strike', 'late_n', 'late_sum', 'late_lose', 'late_worst', 'late_woBT', 'kept']
print(R[cols].round(1).to_string())
print('Thompson (12 seeds) median / min / max:')
print(TS[cols[1:]].describe().loc[['50%', 'min', 'max']].round(1).to_string())
base = R.iloc[0]['_perday']
print(pd.DataFrame({'static': base, 'sidelock': PD}).assign(diff=lambda x: x.sidelock - x.static).to_string())
print('refused triggers (own result of the refused trade):', len(REF), 'strike', round(100 * (REF.ret > 0).mean(), 1),
      'mean', round(REF.ret.mean(), 2))
REF['early'] = REF.day <= EARLY_END
print(REF.groupby('early').ret.agg(['size', lambda x: (x > 0).mean(), 'mean']).round(2))
print(REF.groupby('day').ret.agg(['size', 'mean']).round(1).to_string())
t = df.loc[[i for v in TK.values() for i in v]]
t.to_pickle('sidelock_trades.pkl')
R.to_pickle('sidelock_results.pkl')
print('time', time.time() - t0)
