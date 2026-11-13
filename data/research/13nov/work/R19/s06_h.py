import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H
df=H.load(["h300_gain_pct","h60_gain_pct","h900_gain_pct"],books=H.POOL)
x=df[df.hold_s>300]; print(len(df),len(x), x.h300_gain_pct.notna().sum()); print(x.h300_gain_pct.describe()); print(df.reason.value_counts().head(8))
print((x.h300_gain_pct< -4).sum(), (x.h300_gain_pct<-6).sum())
