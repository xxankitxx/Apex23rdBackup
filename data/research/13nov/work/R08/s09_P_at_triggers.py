import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd, os
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R08")
from s04_leadlag_lib import load, basket, breadth, dF, fwd
PARTS = sys.argv[1:] or ["2026-10-26", "2026-11-05", "2026-11-09"]
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
T = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet",
                    columns=["day", "book", "t_in", "trigger_t", "dir", "rr", "ret_pct", "wx_basket_gap"])
T["d"] = np.where(T.rr == "CE", 1, -1)
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
rows = []
for p in PARTS:
    day = p[:10]
    D = load(p); F = D["F"]; w = D["w"]; t0 = D["t0"]; n = D["n"]
    own10 = dF(F, 10); g10 = basket(D["lc"], w, 10) * F - own10; gs10 = basket(D["ls"], w, 10) * F - own10
    P = 0.1 * own10 + 0.27 * g10 + 0.1 * gs10
    f10, f60, f300 = fwd(F, 10), fwd(F, 60), fwd(F, 300)
    S = T[T.day == day].copy()
    for col in ("trigger_t", "t_in"):
        i = (S[col].astype(float) - t0).round().astype("Int64")
        ok = (i >= 0) & (i < n)
        ii = i.where(ok, 0).astype(int).values
        S[col[:2] + "_P"] = np.where(ok, P[ii] * S.d.values, np.nan)
        S[col[:2] + "_g10"] = np.where(ok, g10[ii] * S.d.values, np.nan)
        S[col[:2] + "_f10"] = np.where(ok, f10[ii] * S.d.values, np.nan)
        S[col[:2] + "_f60"] = np.where(ok, f60[ii] * S.d.values, np.nan)
        S[col[:2] + "_f300"] = np.where(ok, f300[ii] * S.d.values, np.nan)
    rows.append(S)
A = pd.concat(rows)
A["win"] = A.ret_pct > 0
A.to_parquet(os.path.join(OUT, "s09_P_trades.parquet"))
pd.set_option("display.width", 220)
for name, sub in (("pool", A[A.book.isin(POOL)]), ("all", A)):
    sub = sub[sub.tr_P.notna()]
    b = pd.cut(sub.tr_P, [-99, -1, -0.3, 0.3, 1, 99])
    print(name, "n", len(sub))
    print(sub.assign(b=b).groupby("b", observed=True).agg(n=("win", "size"), sr=("win", "mean"), ret=("ret_pct", "mean"),
          f10=("tr_f10", "mean"), f60=("tr_f60", "mean"), f300=("tr_f300", "mean")).round(3).to_string())
    print(" corr gap15(photo) vs g10 at trigger:", round(float(sub[["wx_basket_gap", "tr_g10"]].corr().iloc[0, 1]), 3))
    print(" mean fwd move after trigger (with trade): f10", round(sub.tr_f10.mean(), 2), "f60", round(sub.tr_f60.mean(), 2),
          "f300", round(sub.tr_f300.mean(), 2))
