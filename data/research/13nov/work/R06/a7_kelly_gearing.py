"""R06 a7: strike = leverage. With all-in trades the only sizing knob left is the option's gearing (elasticity
Omega = |delta| F / premium). Scale each Conductor trade's return by lambda (lambda < 1 ~ deeper ITM or next weekly,
> 1 ~ nearer the money) and find the growth-optimal lambda (Kelly) on discovery days, then score it on test days."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R06"
m = pd.read_csv(W + r"\conductor_joined.csv", usecols=["day", "c_ret", "dtype", "delta_in", "entry", "fut_in", "rr", "fut_out"])
m["r"] = m.c_ret / 100
m["omega"] = m.delta_in.abs() * m.fut_in / m.entry
m["x"] = (m.fut_out - m.fut_in) / m.fut_in * np.where(m.rr == "CE", 1, -1)
m["late"] = m.day >= "2026-11-05"
lams = np.round(np.arange(0.3, 2.01, 0.05), 2)
def G(r, lam): return np.log1p(np.clip(lam * r, -0.99, None)).sum()
print("median gearing Omega by day type:", m.groupby("dtype").omega.median().round(1).to_dict())
print("effective Omega = ret / underlying return (median, |x|>2e-4):",
      m[m.x.abs() > 2e-4].assign(e=lambda d: d.r / d.x).groupby("dtype").e.median().round(1).to_dict())
for lab, sel in (("all", slice(None)), ("expiry", m.dtype == "expiry"), ("day_before", m.dtype == "day_before"), ("normal", m.dtype == "normal")):
    d = m[sel]
    E, L = d[~d.late], d[d.late]
    le = lams[np.argmax([G(E.r, l) for l in lams])] if len(E) else np.nan
    ll = lams[np.argmax([G(L.r, l) for l in lams])] if len(L) else np.nan
    def rep(D, l):
        dd = D.groupby("day").r.apply(lambda s: np.expm1(G(s, l)))
        return f"comp {100 * np.expm1(G(D.r, l)):8.1f}%  loss days {int((dd < 0).sum())}/{len(dd)}  worst day {100 * dd.min():6.1f}%"
    print(f"\n{lab}: n disc {len(E)}, test {len(L)}; Kelly lambda disc {le}, test {ll}")
    for l in (0.6, 0.8, 1.0, 1.2, le):
        if len(L):
            print(f"   lambda {l:4.2f}  TEST {rep(L, l)}   | DISC {rep(E, l) if len(E) else ''}")
