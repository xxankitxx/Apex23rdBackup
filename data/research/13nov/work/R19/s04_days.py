import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio  # noqa
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19")
import json
import numpy as np, pandas as pd
from scipy import stats
import harness as H

M = pd.read_csv(r"D:\ApexOptions\data\research\13nov\work\R19\s03_out_daymatrix.csv", index_col=0)
days = list(M.index)
active = [b for b in M.columns if (M[b] != 0).sum() >= 8 and b != "CONDUCTOR"]
med = M[active].median(1); mean_b = M[active].mean(1)
out = {"median_book_day": med.round(1).to_dict(), "mean_book_day": mean_b.round(1).to_dict()}
POST = [d for d in days if d >= "2026-10-30"]
W2 = [d for d in days if d >= "2026-11-05"]
ex = {}
for b in H.POOL + ["CONDUCTOR"]:
    e = M[b] - med
    ex[b] = {"excess_all_mean": round(e.mean(), 1), "excess_post_mean": round(e[POST].mean(), 1),
             "days_beat_median_post": int((e[POST] > 0).sum()), "p_flip_post": round(H.sign_flip_p(e[POST].to_numpy()), 3),
             "p_flip_all": round(H.sign_flip_p(e.to_numpy()), 3), "p_flip_W2": round(H.sign_flip_p(e[W2].to_numpy()), 3)}
out["excess_over_median_book"] = ex

cols = ["wx_range_now", "wx_er_day", "wx_vix", "wx_gap_pts", "wx_expiry_day", "wx_pd_range", "wx_mins_open", "wx_er60"]
df = H.load(cols)
df = df.sort_values("trig")
g = df.groupby("day")
feat = pd.DataFrame({"range_max": g["wx_range_now"].max(), "er_day_last": g["wx_er_day"].last(),
                     "er_day_med": g["wx_er_day"].median(), "vix_first": g["wx_vix"].first(),
                     "gap": g["wx_gap_pts"].first(), "expiry": g["wx_expiry_day"].max(),
                     "pd_range": g["wx_pd_range"].first(), "er60_med": g["wx_er60"].median()})
pool = df[df.book.isin(H.POOL)]
c = H.conductor(pool, days=days)
feat["cond_pct"] = M["CONDUCTOR"]
feat["cond_n"] = [len(c[d][1]) for d in days]
feat["cond_wins"] = [int(pool.loc[c[d][1], "win"].sum()) for d in days]
feat["cond_first_in"] = [pool.loc[c[d][1], "time_in"].min() if c[d][1] else None for d in days]
feat["best_trade"] = [round(pool.loc[c[d][1], "ret_pct"].max(), 1) if c[d][1] else None for d in days]
feat["median_book"] = med
x9 = pool[pool.book == "c20_9x"].groupby("day")
feat["x9_n"] = x9.size()
feat["x9_win"] = x9["win"].mean().round(2)
feat["x9_mean_ret"] = x9["ret_pct"].mean().round(1)
out["day_table"] = feat.round(3).reset_index().to_dict(orient="records")
rho = {}
for f in ["range_max", "er_day_last", "er_day_med", "vix_first", "gap", "pd_range", "er60_med", "median_book"]:
    s = stats.spearmanr(feat[f], feat["cond_pct"], nan_policy="omit")
    rho[f] = [round(float(s.statistic), 2), round(float(s.pvalue), 3)]
out["spearman_vs_cond_pct"] = rho
# trade-level: c20_9x trade return vs time of day buckets and expiry
x = pool[pool.book == "c20_9y"].copy()
x["hour"] = x["time_in"].str[:2]
out["9y_by_hour"] = x.groupby("hour").agg(n=("ret_pct", "size"), win=("win", "mean"), mean=("ret_pct", "mean")).round(2).reset_index().to_dict(orient="records")
x["exp"] = x["wx_expiry_day"]
out["9y_by_expiry"] = x.groupby("exp").agg(n=("ret_pct", "size"), win=("win", "mean"), mean=("ret_pct", "mean"), med=("ret_pct", "median")).round(2).reset_index().to_dict(orient="records")
x["W"] = np.where(x.day >= "2026-10-30", "post", "pre")
out["9y_ret_dist"] = x.groupby("W")["ret_pct"].describe(percentiles=[.1, .25, .5, .75, .9]).round(1).reset_index().to_dict(orient="records")
pd.set_option("display.width", 250)
print(feat.round(2).to_string())
print(json.dumps({k: v for k, v in out.items() if k not in ("day_table",)}, indent=1, default=str))
json.dump(out, open(r"D:\ApexOptions\data\research\13nov\work\R19\s04_out.json", "w"), indent=1, default=str)
