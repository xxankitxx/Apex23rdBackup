import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import joblib, numpy as np
d = joblib.load(r"D:\ApexOptions\data\forecast_lab\collect\2026-10-27.joblib")
print(d['S'].dtype, d['X'].dtype, d['IVT'].dtype)
X=d['X']; t=X[:,0]; print(np.diff(t)[:10], (t.min()+19800)%86400/3600, (t.max()+19800)%86400/3600, X[:3,:3])
S=d['S']; print(np.unique(np.diff(S[:,0].astype(float)))[:10])
