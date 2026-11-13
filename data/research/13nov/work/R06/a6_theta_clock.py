"""R06 a6: which theta clock does the market use intraday? If premiums decay on the kit clock (year theta / 365 / 375,
3.84 x calendar), an IV backed out with CALENDAR time must fall while the trade is held, by about
    d sigma / dt  =  - sigma * (K - 1) / (2 * T)      (ATM, premium ~ sigma sqrt T; K = 1440/375, T calendar hours)
Compare that prediction with the measured slope of (iv_out - iv_in) on hold minutes (all books, by day type),
with each trade's own sigma and T. Then restate the break-even with the clock that fits each day type."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R06"
a = pd.read_parquet(W + r"\t_small.parquet")
a["dtype"] = np.where(a["wx_expiry_day"] == True, "expiry", np.where(a["wx_day_before_expiry"] == True, "day_before", "normal"))
a["ivchg"] = a["iv_out"] - a["iv_in"]
a["hold_h"] = a["hold_s"] / 3600
a["dF"] = (a["fut_out"] - a["fut_in"]) * np.where(a["rr"] == "CE", 1, -1)
K = 1440 / 375
print("dtype  rr   n   T_hrs  sigma  measured_slope/hr (se)   kit-clock prediction/hr   implied clock multiple of calendar")
for dt in ("normal", "day_before", "expiry"):
    for rr in ("CE", "PE"):
        g = a[(a.dtype == dt) & (a.rr == rr)].dropna(subset=["ivchg", "hold_h", "dF", "wx_hrs_to_expiry"])
        g = g[(g.hold_s > 60) & (g.ivchg.abs() < 20)]
        X = np.c_[np.ones(len(g)), g.hold_h, g.dF]
        b, *_ = np.linalg.lstsq(X, g.ivchg, rcond=None)
        res = g.ivchg - X @ b
        se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * res.var())
        T, s = g.wx_hrs_to_expiry.median(), g.iv_in.median()
        pred = -s * (K - 1) / (2 * T)
        # solve for the clock multiple k that matches the slope: slope = -s (k-1) / (2T)
        k = 1 - 2 * T * b[1] / s
        print(f"{dt:10s} {rr} {len(g):5d} {T:6.1f} {s:6.2f}  {b[1]:+.3f} ({se[1]:.3f})            {pred:+.3f}                 {k:.2f}")
