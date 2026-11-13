import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, time
t0=time.time()
z=np.load(r"D:\ApexOptions\data\research\ds_v2\2026-11-04.npz")
t=z["t"]; f=z["fut"]
print(f.shape, [np.nanmedian(f[:,i]) for i in range(f.shape[1])])
q=np.load(r"D:\ApexOptions\data\research\13nov\work\R03\paths\2026-11-04.npz")
for mk in (9*60+20, 10*60+15, 12*60, 15*60+20):
    e = t[0] - ((t[0]+19800)%86400) + mk*60 - 0   # epoch of that IST minute on the day
    i=np.searchsorted(t,e); j=np.searchsorted(q["t"],e)
    print(mk, f[i,:4], q["F"][j])
hm=((t+19800)%86400)/60; s=(hm>=555)&(hm<=925)
print("ds_v2 col0 hi/lo/open/close", np.nanmax(f[s,0]), np.nanmin(f[s,0]), f[s,0][0], f[s,0][-1], round(time.time()-t0,1))
