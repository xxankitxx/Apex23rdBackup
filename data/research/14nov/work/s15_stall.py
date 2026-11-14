"""The owner's hold question as a rule: sell a trade that has gone nowhere. Tested on the champion books' REAL entries
(c20_9y and c20_9x, every recorded day), exits walked per second on real quotes."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import fam
T = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "strike", "rr", "t_in", "ret_pct"])
T = T[T.book.isin(["c20_9y", "c20_9x", "c20_9s", "c20_9v", "c20_9t"])]
RULES = {"base (no added rule)": None}
for after in (600, 900, 1200):
    for pk, band in ((0.08, 0.04), (0.05, 0.03), (0.10, 0.05)):
        RULES[f"stall: after {after // 60} min, peak < {int(pk * 100)} %, within +-{int(band * 100)} %"] = fam.stall(after, pk, band)
for m, tmin, bar in ((30.0, 300, -1.5), (30.0, 600, -2.0), (45.0, 300, -2.0)):
    RULES[f"drift test: {m:.0f} pts/15 min, from {tmin // 60} min, bar {bar}"] = fam.sprt(m, tmin, bar)
rows = []
for day in FL.days():
    D = FL.load_day(day)
    for r in T[T.day == day].itertuples():
        i = int(round(r.t_in - D["t_open"])) - 1
        j = np.flatnonzero(D["K"] == int(r.strike))
        if not len(j) or i < 1:
            continue
        for name, ex in RULES.items():
            x = FL.exit_ladder(D, i, r.rr, int(j[0]), extra=ex)
            if x:
                rows.append(dict(rule=name, day=day, book=r.book, dte0=D["dte0"], i=i, ret=x["ret"], hold=x["hold_s"], why=x["why"]))
R = pd.DataFrame(rows)
B = R[R.rule == "base (no added rule)"].set_index(["day", "book", "i"])
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 70)
for nm, d0 in (("NORMAL days", False), ("EXPIRY days", True)):
    out = []
    for rule, g in R[R.dte0 == d0].groupby("rule", sort=False):
        g = g.set_index(["day", "book", "i"])
        b = B.loc[g.index]
        fired = g.why.isin(["STALL", "SPRT"])
        out.append(dict(rule=rule, trades=len(g), fired=int(fired.sum()), win=round(100 * (g.ret > 0).mean(), 1), mean=round(g.ret.mean(), 2), sum=round(g.ret.sum()),
                        on_fired_new=round(g.ret[fired].mean(), 2) if fired.any() else np.nan, on_fired_old=round(b.ret[fired.values].mean(), 2) if fired.any() else np.nan,
                        old_won_pct=round(100 * (b.ret[fired.values] > 0).mean()) if fired.any() else np.nan,
                        minutes_freed=round((b.hold[fired.values] - g.hold[fired]).sum() / 60) if fired.any() else 0,
                        days_better=int((g.ret.groupby(level=0).sum() > b.ret.groupby(level=0).sum() + 0.5).sum()), days_worse=int((g.ret.groupby(level=0).sum() < b.ret.groupby(level=0).sum() - 0.5).sum())))
    print(f"\n{nm}: the five pool books' real entries")
    print(pd.DataFrame(out).to_string(index=False))
