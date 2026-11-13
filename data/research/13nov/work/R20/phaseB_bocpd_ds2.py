"""PHASE B (after 15:30; one ds_v2 part at a time, about 5-10 minutes in all): rebuild the BOCPD regime inputs from the
per-second futures (ds_v2 fut[:,2] = last traded price; checked on 6 Nov against the trade-table path: median error 3 pts)
instead of the trade-table futures prints, with three hazards (1/30, 1/60, 1/120 per minute), and re-score
(a) the pool trades by settled/fresh x with/against the segment drift, early vs late, and
(b) the side-loss lock with an extra BOCPD condition: the lock is lifted when a fresh change point (run < 15 min)
    points the other way (the side may have turned).
12 Nov has no ds_v2 part; it falls back to the trade-table path (mc_lib.minute_path).
    py -3.13 phaseB_bocpd_ds2.py"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import functools
import glob
import json
import os
from mc_lib import *

print = functools.partial(print, flush=True)
DS = r"D:\ApexOptions\data\research\ds_v2"
df = load()
DAYS = sorted(df.day.unique())
out = []
for d in DAYS:
    parts = sorted(glob.glob(os.path.join(DS, f"{d}*.npz")))
    s = None
    if parts:
        t0 = open_epoch(d)
        acc = []
        for p in parts:
            man = p.replace('.npz', '.manifest.json')
            try:
                if json.load(open(man)).get('rows', 0) <= 0:
                    continue
            except Exception:
                pass
            z = np.load(p)
            t, f = z['t'], z['fut'][:, 2]
            acc.append(pd.Series(f, index=((t - t0) // 60).astype(int)))
            del z
        if acc:
            ser = pd.concat(acc)
            s = ser.where(ser > 1000).groupby(level=0).last().reindex(np.arange(376)).ffill().values
    if s is None:
        s = minute_path(df[df.day == d], d)
    g = df[df.day == d]
    m = ((g.trig - open_epoch(d)) // 60).astype(int).clip(1, 375) - 1
    for H in (30, 60, 120):
        o = bocpd(np.diff(s, prepend=np.nan), hazard=1 / H)[m.values]
        out.append(pd.DataFrame({'H': H, 'rl': o[:, 1], 'seg_mu': o[:, 2]}, index=g.index))
    print(d, 'done')
C = pd.concat(out)
C.to_pickle('phaseB_bocpd_ds2.pkl')
pool = df[df.fam == 'c20pool']
for H, c in C.groupby('H'):
    j = pool.join(c, how='inner')
    j['early'] = j.day <= EARLY_END
    j['ctx'] = np.where(j.rl < 15, 'F', 'S') + np.where(np.sign(j.seg_mu) == j.dirn, 'w', 'a')
    print('hazard 1/', H)
    print(j.groupby(['early', 'ctx']).agg(n=('win', 'size'), strike=('win', 'mean'), mean=('ret_pct', 'mean')).round(3))
