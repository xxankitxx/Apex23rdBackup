"""Real option prices, per second: every entry family on the recorded normal days, split by trading days to expiry."""
import sys; sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\14nov\work"
DTE = {"2026-10-21": 4, "2026-10-22": 3, "2026-10-23": 2, "2026-10-26": 1, "2026-10-28": 4, "2026-10-29": 3, "2026-10-30": 2, "2026-11-02": 1, "2026-11-04": 3, "2026-11-05": 2,
       "2026-11-06": 1, "2026-11-11": 2, "2026-11-12": 1, "2026-11-13": 2}
T = pd.read_parquet(W + r"\fam_normal.parquet")
T["dte"] = T.day.map(DTE)
T["grp"] = np.where(T.dte == 1, "1 day to expiry", "2+ days")
T["fam"] = T.variant.str.split().str[0]
pd.set_option("display.width", 300)
print("days:", {k: sorted(d[5:] for d in T[T.grp == k].day.unique()) for k in ("1 day to expiry", "2+ days")})
print("\n== by family (all its variants pooled) ==")
out = []
for (fam, grp), g in T.groupby(["fam", "grp"]):
    dd = g.groupby(["variant", "day"]).ret.sum().groupby("day").mean()
    out.append(dict(family=fam, group=grp, trades=len(g), win=round(100 * (g.ret > 0).mean(), 1), mean=round(g.ret.mean(), 2), ce=round(g[g.side == "CE"].ret.mean(), 1), pe=round(g[g.side == "PE"].ret.mean(), 1),
                    day_sums=" ".join(f"{d[5:]}:{v:+.0f}" for d, v in dd.items())))
print(pd.DataFrame(out).sort_values(["family", "group"]).to_string(index=False))
print("\n== single variants on the 1-day-to-expiry days against the other days ==")
rows = []
for v, g in T.groupby("variant"):
    a, b = g[g.dte == 1], g[g.dte != 1]
    if len(a) < 8:
        continue
    da = a.groupby("day").ret.sum()
    rows.append(dict(variant=v, n1=len(a), win1=round(100 * (a.ret > 0).mean()), mean1=round(a.ret.mean(), 1), pe1=round(a[a.side == "PE"].ret.mean(), 1) if (a.side == "PE").any() else np.nan,
                     days1=" ".join(f"{d[5:]}:{x:+.0f}" for d, x in da.items()), n2=len(b), win2=round(100 * (b.ret > 0).mean()), mean2=round(b.ret.mean(), 1)))
R = pd.DataFrame(rows).sort_values("mean1", ascending=False)
print(R.head(30).to_string(index=False))
print("...")
print(R.tail(6).to_string(index=False))
