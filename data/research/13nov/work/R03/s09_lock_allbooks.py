import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 part 5: the declared trend lock L1 (dec detector) applied to every book standalone (each book trades alone, all-in,
its own trades minus the vetoed ones; no re-entry modelling, so this is a lower bound on what a live lock would add)."""
import os, time, warnings
warnings.filterwarnings("ignore")
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
base = pd.read_pickle(os.path.join(W, "base.pkl"))
BD = pd.read_csv(os.path.join(W, "book_day.csv")); fam = BD.groupby("book")["fam"].first()
FE = pd.read_csv(os.path.join(W, "cp_features.csv")); FE["cp"] = FE["cp"].astype(int).map(lambda x: f"{x:04d}")
base = base.dropna(subset=["ret_pct"]).copy()
base["trig"] = base["trigger_t"].fillna(base["t_in"])
base["hm"] = ((base.trig + 19800.0) % 86400.0) / 60.0
base["d"] = np.where(base.rr == "CE", 1, -1)
base["lr"] = np.log1p(base.ret_pct / 100.0)
out = []
for cp, cm in (("1015", 615), ("1100", 660)):
    S = FE[FE.cp == cp].set_index("day")
    dec = (S.er >= 0.30) & (S.Dc.abs() >= 0.60)
    sgn = np.sign(S.mv_pct)
    v = base.day.map(dec).fillna(False).astype(bool) & (base.hm >= cm) & (base.d != base.day.map(sgn))
    a = base.groupby(["book", "day"]).lr.sum()
    b = base[~v].groupby(["book", "day"]).lr.sum().reindex(a.index).fillna(0.0)
    vv = base[v].groupby(["book", "day"]).ret_pct.agg(["size", lambda s: (s > 0).mean()]).reindex(a.index)
    t = pd.DataFrame({"base": np.expm1(a) * 100, "lock": np.expm1(b) * 100}).reset_index()
    t["fam"] = t.book.map(fam); t["dec"] = t.day.map(dec)
    t = t[t.dec]
    g = t.groupby("fam").agg(books=("book", "nunique"), bookdays=("book", "size"), base_mean=("base", "mean"), lock_mean=("lock", "mean"),
                             better=("lock", lambda s: 0), )
    g["better"] = t.assign(b=t.lock > t.base + 1e-9).groupby("fam").b.sum()
    g["worse"] = t.assign(b=t.lock < t.base - 1e-9).groupby("fam").b.sum()
    g["vetoed_trades"] = base[v].assign(fam=base[v].book.map(fam)).groupby("fam").size()
    g["vetoed_strike"] = base[v].assign(fam=base[v].book.map(fam)).groupby("fam").ret_pct.apply(lambda s: round(100 * (s > 0).mean(), 0))
    g["cp"] = cp
    out.append(g.round(1))
    print(f"\nL1 dec {cp}: dec days {list(dec[dec].index)}; book-days on those days, mean book-day % without and with the lock\n", g.round(1).to_string())
pd.concat(out).to_csv(os.path.join(W, "lock_allbooks.csv"))
print(round(time.time() - t00, 1))
