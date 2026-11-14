"""Account parity with the live Conductor (correcting s38/s42): no account-level pause after an exit, same-second ties
taken in pool order (the champion first, then fade20, fade60, orbfade, as conductor_fd), and the owner's account
convention: Rs 1,00,000 fresh EVERY day, all-in within the day. Continuous compounding is shown beside it."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import hist1s
K = pd.read_parquet(os.path.join(hist1s.OUT, "classes_run.parquet")); K = K[K.src == "model chain"]
E = pd.read_parquet(os.path.join(hist1s.OUT, "expiry_class.parquet"))
PRI = {"c20_9x": 0, "fade20": 1, "fade60": 2, "orbfade": 3}


def account(g, pause=0):
    out = []
    for day, d in g.assign(p=g.book.map(PRI)).sort_values(["day", "i_in", "p"]).groupby("day"):
        free = -1
        for r in d.itertuples():
            if r.i_in > free:
                out.append(dict(day=day, i_in=r.i_in, ret=r.ret, book=r.book)); free = r.i_out + pause
    return pd.DataFrame(out)


def stats(name, T, days):
    T = T[T.day.isin(days)]
    dd = T.groupby("day").ret.apply(lambda r: 100 * (np.prod(1 + r.to_numpy() / 100) - 1)).reindex(days).fillna(0)
    cont = 100 * np.prod(1 + T.sort_values(["day", "i_in"]).ret.to_numpy() / 100)
    return dict(account=name, trades=len(T), winners=round(100 * (T.ret > 0).mean()), per_trade=round(T.ret.mean(), 2),
                daily_reset_sum_pct=round(dd.sum()), daily_reset_mean_day=round(dd.mean(), 2), days_up=f"{int((dd > 0).sum())}/{int((dd != 0).sum())}",
                worst_day=round(dd.min()), t=round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))), 1), continuous_100_becomes=round(cont, 1))


norm_days = sorted(d for d in K.day.unique() if d < "2026-10-19")
exp_days = sorted(d for d in E.day.unique() if d < "2026-10-19")
rows = []
for nm, bs in (("champion alone", ["c20_9x"]), ("champion + fade60", ["c20_9x", "fade60"]), ("champion + orbfade", ["c20_9x", "orbfade"]),
               ("champion + fade60 + orbfade", ["c20_9x", "fade60", "orbfade"]), ("champion + three fades", ["c20_9x", "fade20", "fade60", "orbfade"]),
               ("three fades, no champion", ["fade20", "fade60", "orbfade"]), ("fade60 + orbfade, no champion", ["fade60", "orbfade"])):
    g = K[K.book.isin(bs)]
    rows.append(stats(nm + " (no pause, as live)", account(g, 0), norm_days))
    if nm == "champion + three fades":
        rows.append(stats(nm + " (with the 60-s pause of s38)", account(g, 60), norm_days))
rows.append(stats("expiry days: champion class, real option seconds", E.assign(i_in=E.i_in), exp_days))
alld = sorted(set(norm_days) | set(exp_days))
both = pd.concat([account(K[K.book == "c20_9x"], 0), E[["day", "i_in", "ret"]].assign(book="c20_9x")])
rows.append(stats("champion on every day (normal + expiry), as live", both, alld))
pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 60)
print("Year before the recorded window (14 Nov 2025 to 16 Oct 2026); normal days on a model option, expiry days on real option seconds")
print(pd.DataFrame(rows).to_string(index=False))
