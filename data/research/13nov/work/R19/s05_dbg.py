import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H, numpy as np
df=H.load(["time_in"],books=H.POOL)
keep,_=H.apply_filter(df,"time_in < '12:00:00'",H.POOL)
w2=[d for d in sorted(df.day.unique()) if d>="2026-11-05"]
p,s=H.mask_shuffle_p(df,keep.to_numpy().copy(),H.POOL,H.POOL,w2,44.7,100)
print(p, np.percentile(s,[0,5,25,50,75,95,100]).round(1))
c=H.conductor(df[keep],days=w2); print({d:round(v[0],1) for d,v in c.items()})
