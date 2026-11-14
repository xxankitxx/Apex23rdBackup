"""Fit the IV factor on the recorded days and check lab5 against the champion's real trades."""
import sys; sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab5
DD = lab5.load()
by = {d["day"]: d for d in DD}
print("days", len(DD), DD[0]["day"], "..", DD[-1]["day"], "| expiry days:", [d["day"][5:] for d in DD if d["dte0"]])
print("dte by day (last 20):", [(d["day"][5:], d["dte"]) for d in DD[-20:]])
# IV factor: recorded ATM IV at 11:00 and 14:00 against VIX
rows = []
for day in FL.days():
    D = FL.load_day(day); X = FL.features(D)
    if day not in by:
        continue
    for hhmm in ("10:00", "11:30", "13:00", "14:30"):
        i = FL.row_of(hhmm)
        v = X["vix"][i] if np.isfinite(X["vix"][i]) else by[day]["vix"][i // 300]
        rows.append((day, by[day]["dte"], hhmm, X["iv"][i], v, X["iv"][i] / v))
R = pd.DataFrame(rows, columns=["day", "dte", "t", "iv", "vix", "k"])
print("ATM IV / VIX by trading days to expiry:\n", R.groupby("dte").k.agg(["median", "min", "max", "count"]).round(2).to_string())
print("expiry day by time:\n", R[R.dte == 0].groupby("t").k.median().round(2).to_string())
# check against real c20_9x / c20_9y trades: same time and side, lab5's result against the recorded one
T = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "rr", "t_in", "ret_pct", "entry"])
T = T[T.book.isin(["c20_9x", "c20_9y"])]
out = []
for r in T.itertuples():
    if r.day not in by:
        continue
    D = by[r.day]
    t0 = FL.load_day(r.day)["t_open"]
    b = int((r.t_in - t0) // 300) - 1                 # the bar that closed before the entry
    x = lab5.ladder(D, b, r.rr)
    if x:
        out.append((r.day, D["dte0"], r.ret_pct, x["ret"], r.entry, x["e"]))
O = pd.DataFrame(out, columns=["day", "dte0", "rec", "sim", "e_rec", "e_sim"])
for d, g in O.groupby("dte0"):
    print("expiry" if d else "normal", "n", len(g), "ret corr", round(np.corrcoef(g.rec, g.sim)[0, 1], 2), "mean rec", round(g.rec.mean(), 1), "sim", round(g.sim.mean(), 1),
          "win rec", round(100 * (g.rec > 0).mean()), "sim", round(100 * (g.sim > 0).mean()), "| premium ratio sim/rec median", round((g.e_sim / g.e_rec).median(), 2))
