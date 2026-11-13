import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, datetime as dt
for d in ['2026-11-06','2026-11-09']:
    z=np.load(rf"D:\ApexOptions\data\research\ds_v2\{d}.npz")
    t=z['t']; f=z['fut'][:,0]
    ist=[dt.datetime.utcfromtimestamp(x+19800) for x in t[[0,-1]]]
    m=np.isfinite(f)
    tt=np.array([(dt.datetime.utcfromtimestamp(x+19800)) for x in t[::60]])
    # value at ~15:29
    hm=(t+19800)%86400/60
    k=np.where((hm>=15*60+29)&(hm<15*60+30)&m)[0]
    k0=np.where((hm>=9*60+15)&m)[0][:1]
    print(d, ist, 'fut0',f[k0], 'fut1529', f[k[-1]] if len(k) else None, 'max',np.nanmax(f),'min',np.nanmin(f))
