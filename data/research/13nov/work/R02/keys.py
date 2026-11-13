import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np
z = np.load(r"D:\ApexOptions\data\research\ds_v2\2026-11-06.npz")
for k in z.files: print(k, z[k].shape, z[k].dtype)
print(z["expiry"], z["strikes"][:5])
