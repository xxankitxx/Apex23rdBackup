import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H
import numpy as np
df = H.load(books=H.POOL)
c = H.conductor(df)
tot=0; n=0; w=0
for d,(r,tk) in c.items():
    pnl = sum((df.at[i,"exit"]-df.at[i,"entry"])*0 for i in tk)
    n+=len(tk); w+=int(df.loc[tk,"win"].sum()); tot+=r*1000
    print(d, len(tk), int(df.loc[tk,"win"].sum()), round(r*1000), round(r,1))
print("total", n, w, round(tot))
