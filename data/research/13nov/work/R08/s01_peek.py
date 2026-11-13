import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np
z = np.load(r"D:\ApexOptions\data\research\ds_v2\2026-11-05.npz", allow_pickle=True)
for k in z.files:
    a = z[k]; print(k, a.shape, a.dtype)
print(z['sym'], z['w'], z['g'])
print(z['fut'][1000], z['hw'][1000], z['sf'][1000], z['hwa'][1000])
print(np.isnan(z['hw']).mean(0))
print(np.median(z['hwa'],0))
