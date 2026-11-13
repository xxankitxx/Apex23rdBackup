import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
M = pd.read_parquet(OUT + r"\conductor_hw.parquet")
pd.set_option("display.width", 220)


def comp(r):
    return (np.prod(1 + np.asarray(r) / 100) - 1) * 100


def summary(sub, label):
    g = sub.groupby("day")["cret"].apply(comp)
    allg = M.groupby("day")["cret"].apply(lambda r: 0.0)
    g = g.reindex(allg.index, fill_value=0.0)
    best_day = g.idxmax()
    no_best_day = g.drop(best_day).sum()
    bt = sub.cret.max() if len(sub) else 0
    no_best_trade = (sub.cret.sum() - bt)
    return dict(label=label, n=len(sub), sr=round((sub.cret > 0).mean(), 3), sum_daily_pct=round(g.sum(), 1),
                lose_days=int((g < 0).sum()), worst_day=round(g.min(), 1), ex_best_day=round(no_best_day, 1),
                ex_best_trade_simple=round(no_best_trade, 1))


for win, sel in (("early", M.day <= "2026-11-04"), ("late", M.day >= "2026-11-05")):
    S = M[sel]
    rows = [summary(S, "base")]
    for th in (0.5, 1.0, 1.589, 2.0, 3.0):
        rows.append(summary(S[~(S.basket_gap > th)], f"veto gap>{th}"))
    print(win); print(pd.DataFrame(rows).to_string())
# per test day
L = M[M.day >= "2026-11-05"]
for th in (1.589,):
    for d, s in L.groupby("day"):
        k = s[~(s.basket_gap > th)]
        v = s[s.basket_gap > th]
        print(d, "base n", len(s), "sr", round((s.cret > 0).mean(), 2), "ret", round(comp(s.cret), 1),
              "| kept n", len(k), "sr", round((k.cret > 0).mean(), 2) if len(k) else None, "ret", round(comp(k.cret), 1),
              "| vetoed", list(v.cret.round(1)))
# top trades kept?
top = M.sort_values("cret", ascending=False).head(12)
print(top[["day", "book", "cret", "basket_gap", "div10"]].to_string())
# the pool books (all their trades, not only the Conductor's)
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
df = pd.read_parquet(P, columns=["day", "book", "ret_pct", "wx_basket_gap"])
pool = df[df.book.isin(["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"])]
for win, sel in (("early", pool.day <= "2026-11-04"), ("late", pool.day >= "2026-11-05")):
    s = pool[sel]
    b = pd.cut(s.wx_basket_gap, [-99, -2, 0, 1.6, 3, 99])
    print(win, s.assign(b=b, w=s.ret_pct > 0).groupby("b", observed=True).agg(n=("w", "size"), sr=("w", "mean"), mean=("ret_pct", "mean")).round(3).to_string())
allb = df
for win, sel in (("early", allb.day <= "2026-11-04"), ("late", allb.day >= "2026-11-05")):
    s = allb[sel]
    b = pd.cut(s.wx_basket_gap, [-99, -2, 0, 1.6, 3, 99])
    print("ALL BOOKS", win, s.assign(b=b, w=s.ret_pct > 0).groupby("b", observed=True).agg(n=("w", "size"), sr=("w", "mean"), mean=("ret_pct", "mean")).round(3).to_string())
# per book in late: does the veto help most books?
bk = []
for book, s in df.groupby("book"):
    for win, sel in (("e", s.day <= "2026-11-04"), ("l", s.day >= "2026-11-05")):
        x = s[sel]
        if len(x) < 15:
            continue
        hi = x.wx_basket_gap > 1.6
        if hi.sum() < 5:
            continue
        bk.append(dict(book=book, win=win, sr_hi=(x[hi].ret_pct > 0).mean(), sr_rest=(x[~hi].ret_pct > 0).mean()))
B = pd.DataFrame(bk)
for win in ("e", "l"):
    b = B[B.win == win]
    print("books", win, len(b), "share of books where gap>1.6 trades win less:", round(float((b.sr_hi < b.sr_rest).mean()), 3))
