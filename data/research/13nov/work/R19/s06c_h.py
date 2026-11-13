import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H
df=H.load(["hexit_req_gain_pct","hexit_gain_pct","h300_gain_pct"])
c=df[df.book.str.startswith("c20")]; print(c.hexit_req_gain_pct.notna().sum(), c.hexit_gain_pct.notna().sum(), len(c))
s=df[df.book=="t28_gap"]; print(len(s), s.h300_gain_pct.notna().sum(), (s.hold_s>300).sum())
print(df[df.h300_gain_pct.notna()].book.value_counts().head(8))
