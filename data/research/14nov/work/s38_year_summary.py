"""The year at per-second resolution: the real strategy classes on 229 broker sessions (model chain, normal days) plus
the recorded window. By book: the year before the window in two halves and by quarter; the fade pair as one account."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import hist1s
T = pd.read_parquet(os.path.join(hist1s.OUT, "classes_run.parquet"))
M = T[T.src == "model chain"].copy()
comp = lambda r: 100 * (np.prod(1 + np.asarray(r) / 100) - 1)


def one_account(g):
    """trades of several books taken by one account: in time order, skip a trade that starts before the last ended."""
    out = []
    for day, d in g.sort_values(["day", "i_in"]).groupby("day"):
        free = -1
        for r in d.itertuples():
            if r.i_in > free:
                out.append(r._asdict()); free = r.i_out + 60
    return pd.DataFrame(out)


books = {b: M[M.book == b] for b in M.book.unique()}
books["fade20 + fade60 (one account)"] = one_account(M[M.book.isin(["fade20", "fade60"])])
books["three fades (one account)"] = one_account(M[M.book.isin(["fade20", "fade60", "orbfade"])])
hist_days = sorted(d for d in M.day.unique() if d < "2026-10-19")
mid = hist_days[len(hist_days) // 2]
pd.set_option("display.width", 250)
print(f"year before the recorded window: {hist_days[0]} to {hist_days[-1]} ({len(hist_days)} normal sessions with a trade in some book); halves split at {mid}")
out = []
for b, g in books.items():
    for tag, s in (("older half", g[g.day < mid]), ("newer half", g[(g.day >= mid) & (g.day < "2026-10-19")]), ("whole year before", g[g.day < "2026-10-19"]), ("recorded window", g[g.day >= "2026-10-19"])):
        if not len(s):
            continue
        dd = s.groupby("day").ret.apply(comp); ds = s.groupby("day").ret.sum()
        qq = s.assign(q=s.day.str[:7]).groupby("q").ret.sum()
        out.append(dict(book=b, period=tag, sessions=s.day.nunique(), trades=len(s), winners=round(100 * (s.ret > 0).mean()), per_trade=round(s.ret.mean(), 2),
                        t=round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1) if len(ds) > 3 else None, days_up=f"{int((dd > 0).sum())}/{len(dd)}", median_day=round(dd.median(), 1),
                        worst_day=round(dd.min()), best_day=round(dd.max()), months_up=f"{int((qq > 0).sum())}/{len(qq)}", total=round(s.ret.sum())))
print(pd.DataFrame(out).to_string(index=False))
print("\nmonthly totals (% points, sum of trade results):")
P = pd.concat([g.assign(b=b) for b, g in books.items()])
print(P.assign(m=P.day.str[:7]).pivot_table(index="b", columns="m", values="ret", aggfunc="sum").round(0).fillna(0).astype(int).to_string())
g = books["c20_9x"]; g = g[g.day < "2026-10-19"]
print("\nc20_9x, year before the window: by side", {s: (len(x), round(100 * (x.ret > 0).mean()), round(x.ret.mean(), 2)) for s, x in g.groupby("side")}, "| top 5 trades' share of the total:",
      round(100 * g.ret.nlargest(5).sum() / g.ret.sum()) if g.ret.sum() > 0 else "total not positive")
