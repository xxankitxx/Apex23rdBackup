import sys, time; sys.path.insert(0, r"D:\ApexOptions")
import numpy as np, pandas as pd
from apex import fastlab as FL
t0 = time.time()
T = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet",
                    columns=["day", "book", "strike", "rr", "t_in", "t_out", "entry", "exit", "ret_pct", "reason", "hold_s"])
T = T[T.book.isin(["c20_9x", "c20_9y"])]
rows = []
for day in FL.days():
    D = FL.load_day(day)
    for r in T[T.day == day].itertuples():
        i = int(round(r.t_in - D["t_open"])) - 1
        j = np.flatnonzero(D["K"] == int(r.strike))
        if not len(j) or i < 1:
            continue
        x = FL.exit_ladder(D, i, r.rr, int(j[0]))
        pj = FL.pick(D, i - 1, r.rr)
        if x is None:
            continue
        rows.append(dict(day=day, book=r.book, dte0=D["dte0"], rec=r.ret_pct, sim=x["ret"], e_rec=r.entry, e_sim=x["e"], why_rec=r.reason, why=x["why"],
                         hold_rec=r.hold_s, hold=x["hold_s"], same_strike=(pj is not None and D["K"][pj] == int(r.strike))))
R = pd.DataFrame(rows)
for (b, d), g in R.groupby(["book", "dte0"]):
    print(b, "expiry" if d else "normal", "n", len(g), "entry price same within 1%:", round((abs(g.e_sim / g.e_rec - 1) < 0.01).mean(), 2),
          "| ret corr", round(np.corrcoef(g.rec, g.sim)[0, 1], 3), "| mean rec", round(g.rec.mean(), 2), "sim", round(g.sim.mean(), 2),
          "| sr rec", round((g.rec > 0).mean(), 3), "sim", round((g.sim > 0).mean(), 3), "| within 3 pts:", round((abs(g.rec - g.sim) < 3).mean(), 2),
          "| my strike pick same:", round(g.same_strike.mean(), 2))
print(round(time.time() - t0, 1), "s")
