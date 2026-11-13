import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import glob, os, time, numpy as np, joblib
t0=time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R03\paths"
for f in sorted(glob.glob(r"D:\ApexOptions\data\forecast_lab\collect\*.joblib")):
    day=os.path.basename(f)[:10]; o=os.path.join(W, day+".npz")
    if os.path.exists(o): continue
    if time.time()-t0>140: break
    d=joblib.load(f); s=np.asarray(d["S"],float)
    np.savez(o, t=s[:,0], F=s[:,1])
    print(day, s.shape, round(time.time()-t0,1), flush=True)
