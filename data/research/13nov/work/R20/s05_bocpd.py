import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time
from mc_lib import *
t0 = time.time()
df = load()
ctx = []
paths = {}
for d, g in df.groupby('day'):
    p = minute_path(g, d)
    paths[d] = p
    x = np.diff(p, prepend=np.nan)
    for H in (60,):
        o = bocpd(x, hazard=1 / H)
    m = ((g.trig - open_epoch(d)) // 60).astype(int).clip(1, 375) - 1      # last COMPLETED minute before the trigger
    o2 = o[m.values]
    pm = p[m.values]
    day_open = p[np.isfinite(p)][0]
    c = pd.DataFrame({'cp_p10': o2[:, 0], 'rl': o2[:, 1], 'seg_mu': o2[:, 2], 'seg_sd': o2[:, 3],
                      'move_open': pm - day_open}, index=g.index)
    ctx.append(c)
    # day summary of change points (MAP run length reset count)
    rl = o[:, 1]
    resets = int(np.nansum(np.diff(rl) < -5))
    print(d, 'resets', resets, 'median rl', np.nanmedian(rl), 'p path ok', np.isfinite(p).mean().round(2))
C = pd.concat(ctx)
df = df.join(C)
df['seg_t'] = df.seg_mu / (df.seg_sd / np.sqrt(df.rl + 1))
df['seg_with'] = np.sign(df.seg_mu) == df.dirn
df['fresh'] = df.rl < 15
df['strong'] = df.seg_t.abs() > 2
df[['cp_p10', 'rl', 'seg_mu', 'seg_sd', 'seg_t', 'seg_with', 'fresh', 'strong', 'move_open']].to_pickle('ctx_bocpd.pkl')
pd.to_pickle(paths, 'paths.pkl')
pool = df[df.fam == 'c20pool'].copy()
pool['early'] = pool.day <= EARLY_END
for col in ('fresh', 'seg_with', 'strong'):
    print(pool.groupby(['early', col]).agg(n=('win', 'size'), strike=('win', 'mean'), mean=('ret_pct', 'mean')).round(3))
pool['ctx'] = pool.fresh.map({True: 'F', False: 'S'}) + pool.seg_with.map({True: 'w', False: 'a'})
print(pool.groupby(['early', 'ctx']).agg(n=('win', 'size'), strike=('win', 'mean'), mean=('ret_pct', 'mean')).round(3))
# per-day sign stability of with-vs-against
g = pool.groupby(['day', 'seg_with']).ret_pct.mean().unstack()
print((g[True] > g[False]).value_counts(), g.round(1))
print(time.time() - t0)
