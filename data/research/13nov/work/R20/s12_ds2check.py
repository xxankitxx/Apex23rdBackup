import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
from mc_lib import *
paths = pd.read_pickle('paths.pkl')
for part in ('2026-11-06', '2026-10-27'):
    z = np.load(rf"D:\ApexOptions\data\research\ds_v2\{part}.npz")
    t = z['t']; f = z['fut']
    print(part, f.shape, np.nanmedian(f[:, :4], axis=0))
    t0 = open_epoch(part)
    m = ((t - t0) // 60).astype(int)
    for col in (0, 1, 2):
        s = pd.Series(f[:, col]).where(lambda x: x > 1000).groupby(m).last().reindex(np.arange(376)).ffill().values
        p = paths[part]
        ok = np.isfinite(s) & np.isfinite(p)
        e = np.abs(s[ok] - p[ok])
        print(' col', col, 'median abs err', round(np.median(e), 2), 'p90', round(np.percentile(e, 90), 2))
    sd = pd.Series(f[:, 2]).where(lambda x: x > 1000).groupby(m).last().reindex(np.arange(376)).ffill().values
    o1 = bocpd(np.diff(sd, prepend=np.nan)); o2 = bocpd(np.diff(paths[part], prepend=np.nan))
    ok = np.isfinite(o1[:, 1]) & np.isfinite(o2[:, 1])
    print(' BOCPD fresh(rl<15) agreement', round(((o1[ok, 1] < 15) == (o2[ok, 1] < 15)).mean(), 3),
          'segment-sign agreement', round((np.sign(o1[ok, 2]) == np.sign(o2[ok, 2])).mean(), 3))
