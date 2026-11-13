import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H
df=H.load(["h60_gain_pct","h300_gain_pct"])
g=df.assign(has=df.h60_gain_pct.notna(), long=df.hold_s>60).groupby(df.book.str[:4]).agg(n=("has","size"),has60=("has","sum"),long=("long","sum"))
print(g.sort_values("n",ascending=False).head(25))
