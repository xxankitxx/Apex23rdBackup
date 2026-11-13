import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
"""Greedy one-position account over the five pool books' own trades (earliest t_in while flat, ties by book order).
An approximation of the Conductor (which ranks books by standing); used only to compare veto against no veto
on the SAME approximation, so a vetoed trigger lets the next pool trigger in, as it would live."""
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
df = pd.read_parquet(P, columns=["day", "book", "t_in", "t_out", "ret_pct", "wx_basket_gap"])
df = df[df.book.isin(POOL)].copy()
df["o"] = df.book.map({b: i for i, b in enumerate(POOL)})
df = df.sort_values(["day", "t_in", "o"])


def run(veto):
    out = []
    for day, s in df.groupby("day"):
        free = -1
        for r in s.itertuples():
            if r.t_in < free:
                continue
            if veto is not None and veto(r):
                continue
            out.append((day, r.book, r.ret_pct))
            free = r.t_out + 1
    return pd.DataFrame(out, columns=["day", "book", "ret"])


def rep(T, label):
    days = sorted(df.day.unique())
    g = T.groupby("day")["ret"].apply(lambda r: (np.prod(1 + r.values / 100) - 1) * 100).reindex(days, fill_value=0.0)
    res = {}
    for win, sel in (("early", [d for d in days if d <= "2026-11-04"]), ("late", [d for d in days if d >= "2026-11-05"])):
        t = T[T.day.isin(sel)]; gg = g[sel]
        res[win] = dict(n=len(t), sr=round(float((t.ret > 0).mean()), 3), sum_pct=round(float(gg.sum()), 1),
                        lose=int((gg < 0).sum()), worst=round(float(gg.min()), 1),
                        ex_best_day=round(float(gg.sum() - gg.max()), 1))
    print(label, res)
    return g


base = rep(run(None), "greedy base")
for th in (1.0, 1.6, 2.0, 3.0):
    g = rep(run(lambda r, th=th: r.wx_basket_gap > th), f"veto gap>{th}")
    if th == 1.6:
        print(pd.DataFrame({"base": base.round(1), "veto1.6": g.round(1)}).T.to_string())
