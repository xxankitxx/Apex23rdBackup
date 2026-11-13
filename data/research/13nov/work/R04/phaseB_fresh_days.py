import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 phase B: judge the FROZEN candidates (frozen_candidates.json) on days the search never saw.
Input: a trade table with the same columns as trades_all_books.parquet (day, book, t_in, t_out, trigger_t, entry,
exit, ret_pct, rr and wx_<factor>) holding NEW days (13 Nov onwards), e.g. from a p44-style replay run after the close.
    py -3.13 phaseB_fresh_days.py PATH_TO_NEW_TABLE.parquet
Prints, per new day: the unfiltered Conductor account vs each candidate gate (return %, trades, strike rate)."""
import json, os
import numpy as np
import pandas as pd
here = os.path.dirname(os.path.abspath(__file__))
POOL = ("c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"); LOT, CAP0 = 65, 100_000.0
fz = json.load(open(os.path.join(here, "frozen_candidates.json")))["candidates"]
cols = ["day", "book", "t_in", "t_out", "trigger_t", "entry", "exit", "ret_pct"] + sorted({"wx_" + c["factor"] for c in fz})
df = pd.read_parquet(sys.argv[1], columns=cols)
df = df[df.book.isin(POOL) & df.entry.notna() & df.exit.notna() & df.t_in.notna()].copy()
df = df[df.day > "2026-11-12"]
df["trig"] = df.trigger_t.where(df.trigger_t.notna(), df.t_in)
df["pr"] = df.book.map({b: i for i, b in enumerate(POOL)})


def account(g, keep):
    g = g.sort_values(["trig", "pr"]); cap = CAP0; held = None; n = w = 0
    for r, k in zip(g.itertuples(), keep.loc[g.sort_values(["trig", "pr"]).index]):
        if held is not None:
            if r.trig <= held[0] or r.trig < held[1] or (r.trig == held[1] and r.book == held[2]):
                continue
            held = None
        if not k:
            continue
        lots = int(cap // (r.entry * LOT))
        if lots < 1:
            continue
        cap += (r.exit - r.entry) * lots * LOT; held = (r.trig, r.t_out, r.book); n += 1; w += int(r.ret_pct > 0)
    return round(100 * (cap / CAP0 - 1), 2), n, w


for day, g in df.groupby("day"):
    line = [f"{day} none={account(g, pd.Series(True, index=g.index))}"]
    for c in fz:
        x = g["wx_" + c["factor"]].astype(float)
        k = x.notna() & ((x >= c["line"]) if c["op"] == ">=" else (x < c["line"]))
        line.append(f"{c['id']}={account(g, k)}")
    print(" | ".join(line))
