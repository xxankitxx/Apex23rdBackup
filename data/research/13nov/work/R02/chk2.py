import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd
df = pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R02\all_trades_slim.pkl")
POOL = ['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
p = df[df.book.isin(POOL)]
for m in (60,300,900,1800):
    print(m, "open", (p.hold_s>m+1).sum(), "has mark", p[f"h{m}_gain_pts"].notna().sum(), "hold_s col", p[f"h{m}_hold_s"].describe().to_dict() if p[f"h{m}_hold_s"].notna().any() else None)
print(p.groupby("day")["h60_gain_pts"].apply(lambda s: s.notna().mean()).to_dict())
x = df.assign(has=df.h300_gain_pts.notna(), op=df.hold_s>301).groupby("day")[["has","op"]].sum()
print(x)
print(p[["hold_s","hexit_req_gain_pts","hexit_req_peak_pts","hexit_req_attr_theta_pts","hexit_req_attr_delta_pts","hexit_req_giveback_rate_pts_min","peak_pts","ret_pct"]].head(10))
