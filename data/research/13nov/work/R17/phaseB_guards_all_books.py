import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R17 phase B (after the close): do the account-level loss guards generalise beyond the c20 family?

Every one of the 107 books is run as its own all-in account (its own trades, its own loss history) with and without
each guard; per window (19 Oct-4 Nov discovery, 5-12 Nov test) it prints strike rate, sum of day %, losing days and
book-days made better / worse. Same walk as apex/conductor/account_sim.py (work/R17/sim.py). Columns loaded: only
what the guards read. Expect about 2 minutes; if it runs longer, pass a book prefix (e.g. c20 t28 edge) to split.

    py -3.13 D:\\ApexOptions\\data\\research\\13nov\\work\\R17\\phaseB_guards_all_books.py [BOOK_PREFIX ...]
"""
import os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim, guards as G  # noqa: E402

COLS = ["day", "book", "rr", "entry", "exit", "t_in", "t_out", "trigger_t", "ret_pct", "fut_in", "fut_out", "iv_in", "iv_out",
        "wx_mins_open", "wx_er_day", "wx_er60", "wx_strad_expanding", "wx_day_move", "wx_quote_age"]
V = {"none": None, "after_loss_10m": G.after_loss(10), "whipsaw_30m": G.whipsaw(30), "whipsaw_60m": G.whipsaw(60),
     "flip_after_loss_10m": G.flip_after_loss(10), "against100_er0.1": G.against_trend(100, 0.1)}


def main(prefixes):
    df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=COLS)
    if prefixes:
        df = df[df.book.str.startswith(tuple(prefixes))]
    df = df[df.entry.notna() & df.exit.notna() & df.t_in.notna() & df.t_out.notna()]
    df["trig"] = df.trigger_t.where(df.trigger_t.notna(), df.t_in).astype(float)
    df["pri"] = 0
    df = df.sort_values(["day", "trig"]).reset_index(drop=True)
    subs = {b: g for b, g in df.groupby("book")}
    r0 = {b: sim.sim(g) for b, g in subs.items()}
    for name, g in V.items():
        acc = {"E": [0.0, 0, 0, 0], "L": [0.0, 0, 0, 0]}
        better = worse = 0
        for b, sub in subs.items():
            r = r0[b] if g is None else sim.sim(sub, g)
            for d, x in r.items():
                k = "L" if d >= "2026-11-05" else "E"
                acc[k][0] += x["ret_day"]; acc[k][1] += x["n"]; acc[k][2] += x["w"]; acc[k][3] += x["ret_day"] < 0
                dv = x["ret_day"] - r0[b][d]["ret_day"]
                better += dv > 0.05; worse += dv < -0.05
        print(f"{name:22s} " + " | ".join(f"{k}: sum day% {v[0]:9.1f} SR {100 * v[2] / max(v[1], 1):4.1f} n {v[1]:5d} losing book-days {v[3]:4d}"
                                         for k, v in acc.items()) + f" | book-days better {better} worse {worse}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
