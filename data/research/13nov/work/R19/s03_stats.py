import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio  # noqa
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19")
import itertools, json, math
import numpy as np, pandas as pd
from scipy import stats
import harness as H

OUT = r"D:\ApexOptions\data\research\13nov\work\R19\s03_out.json"
res = {}
df_all = H.load()                                    # all 107 books, base columns
days = sorted(df_all["day"].unique()); D = len(days)
KIT = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28"]
POST9X = [d for d in days if d >= "2026-10-30"]       # c20_9x frozen 30 Oct pre-open
LIVE = ["2026-11-09", "2026-11-11", "2026-11-12"]

# ── A. Conductor accounting ─────────────────────────────────────────────────────────────────────────────────────
pool_df = df_all[df_all.book.isin(H.POOL)]
c = H.conductor(pool_df)
cd = pd.Series({d: c[d][0] for d in days})
res["cond_day"] = cd.round(2).to_dict()
grp = {"kit days (c20 parameters fitted) 19-28 Oct": KIT, "29 Oct (looked at before 9x freeze)": ["2026-10-29"],
       "30 Oct - 6 Nov (after 9x freeze, inside pool selection)": [d for d in days if "2026-10-30" <= d <= "2026-11-06"],
       "9-12 Nov (live forward)": LIVE}
tot = cd.sum()
res["groups"] = {k: {"days": len(v), "sum_pct": round(cd[v].sum(), 1), "share": round(cd[v].sum() / tot, 3),
                     "mean_day": round(cd[v].mean(), 1), "median_day": round(cd[v].median(), 1),
                     "losing": int((cd[v] < 0).sum())} for k, v in grp.items()}
srt = cd.sort_values(ascending=False)
res["top_day_share"] = {"top1": round(srt.iloc[0] / tot, 3), "top2": round(srt.iloc[:2].sum() / tot, 3),
                        "top3": round(srt.iloc[:3].sum() / tot, 3)}
# source of Conductor trades, overlap with c20_9x
taken = [i for d in days for i in c[d][1]]
tk = pool_df.loc[taken]
res["cond_src"] = tk.book.value_counts().to_dict()
x9 = pool_df[pool_df.book == "c20_9x"]
same = 0
for i in taken:
    r = pool_df.loc[i]
    m = x9[(x9.day == r.day) & (x9.rr == r.rr) & ((x9.t_in - r.t_in).abs() <= 5) & (x9.strike == r.strike)]
    same += len(m) > 0
res["cond_same_as_9x"] = [same, len(taken)]

# ── B. every book alone (one-book all-in), day matrix ───────────────────────────────────────────────────────────
import os, time
_t0 = time.time()
MP = OUT.replace(".json", "_daymatrix.csv")
books = sorted(df_all.book.unique())
if os.path.exists(MP):
    M = pd.read_csv(MP, index_col=0)
else:
    M = pd.DataFrame(0.0, index=days, columns=books)
    for b in books:
        cb = H.conductor(df_all[df_all.book == b], [b], days=days)
        for d in days:
            M.at[d, b] = cb[d][0]
    M["CONDUCTOR"] = cd
    M.round(4).to_csv(MP)
print("matrix", round(time.time() - _t0, 1), flush=True)
res["book_summary"] = {}
for b in H.POOL + ["CONDUCTOR"]:
    s = M[b]
    res["book_summary"][b] = {"sum_all": round(s.sum(), 1), "mean_all": round(s.mean(), 1),
                              "sum_post9x": round(s[POST9X].sum(), 1), "mean_post9x": round(s[POST9X].mean(), 1),
                              "losing_post9x": int((s[POST9X] < 0).sum()), "sum_live": round(s[LIVE].sum(), 1),
                              "median_all": round(s.median(), 1)}

# ── C. bootstrap of forward expectancy per day ──────────────────────────────────────────────────────────────────
rng = np.random.default_rng(20261113)
def mbb(x, L, n=20000):
    x = np.asarray(x, float); T = len(x)
    nb = math.ceil(T / L)
    starts = rng.integers(0, T, size=(n, nb))                    # circular moving blocks
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]) % T
    s = x[idx.reshape(n, -1)[:, :T]]
    return s
boot = {}
for lab, sel in [("all 17 days", days), ("post-9x-freeze 9 days", POST9X), ("all but 26-27 Oct", [d for d in days if d not in ("2026-10-26", "2026-10-27")]),
                 ("live 3 days", LIVE)]:
    x = cd[sel].to_numpy()
    for L in ([1, 2, 3] if len(x) > 5 else [1]):
        s = mbb(x, L)
        mean = s.mean(1); med = np.median(s, 1); geo = 100 * (np.exp(np.log1p(s / 100).mean(1)) - 1)
        boot[f"{lab} | block {L}"] = {"n_days": len(x), "mean": round(x.mean(), 1),
                                      "mean_ci90": [round(np.percentile(mean, 5), 1), round(np.percentile(mean, 95), 1)],
                                      "median": round(np.median(x), 1),
                                      "median_ci90": [round(np.percentile(med, 5), 1), round(np.percentile(med, 95), 1)],
                                      "geo": round(100 * (np.exp(np.log1p(x / 100).mean()) - 1), 1),
                                      "geo_ci90": [round(np.percentile(geo, 5), 1), round(np.percentile(geo, 95), 1)],
                                      "p_mean_le0": round(float((mean <= 0).mean()), 3),
                                      "p_geo_le0": round(float((geo <= 0).mean()), 3)}
res["bootstrap"] = boot; print("boot", round(time.time() - _t0, 1), flush=True)

# ── D. deflated Sharpe ratio (Bailey and Lopez de Prado 2014) ───────────────────────────────────────────────────
def sr(x):
    x = np.asarray(x, float); s = x.std(ddof=1)
    return x.mean() / s if s > 0 else 0.0
def psr(x, sr0):
    x = np.asarray(x, float); T = len(x); s = sr(x)
    g3 = stats.skew(x); g4 = stats.kurtosis(x, fisher=False)
    den = math.sqrt(max(1e-12, 1 - g3 * s + (g4 - 1) / 4 * s * s))
    return float(stats.norm.cdf((s - sr0) * math.sqrt(T - 1) / den))
active = [b for b in books if (M[b] != 0).sum() >= 8]
srs = np.array([sr(M[b]) for b in active])
V = srs.var(ddof=1)
corr = M[active].corr().to_numpy(); rho = np.nanmean(corr[np.triu_indices_from(corr, 1)])
emc = 0.5772156649
def sr0(N):
    if N <= 1:
        return 0.0
    return math.sqrt(V) * ((1 - emc) * stats.norm.ppf(1 - 1 / N) + emc * stats.norm.ppf(1 - 1 / (N * math.e)))
dsr = {"V_sr_cross_books": round(V, 4), "n_active_books": len(active), "mean_pair_corr": round(rho, 3), "rows": {}}
for b in H.POOL + ["CONDUCTOR"]:
    for lab, sel in [("all", days), ("post9x", POST9X)]:
        x = M.loc[sel, b].to_numpy()
        row = {"SR_daily": round(sr(x), 3), "skew": round(float(stats.skew(x)), 2),
               "kurt": round(float(stats.kurtosis(x, fisher=False)), 2), "T": len(x), "PSR0": round(psr(x, 0.0), 3)}
        for N in (5, 20, 107, 978, 3000):
            Ne = rho + (1 - rho) * N
            row[f"DSR_N{N}"] = round(psr(x, sr0(Ne)), 3)
        dsr["rows"][f"{b} {lab}"] = row
dsr["SR0_by_N"] = {N: round(sr0(rho + (1 - rho) * N), 3) for N in (5, 20, 107, 978, 3000)}
res["dsr"] = dsr

# ── E. PBO by combinatorially symmetric cross-validation (Bailey et al. 2015) ───────────────────────────────────
def pbo(mat, S=8, metric="mean"):
    T = mat.shape[0]
    blocks = np.array_split(np.arange(T), S)
    lam = []
    for comb in itertools.combinations(range(S), S // 2):
        ins = np.concatenate([blocks[i] for i in comb]); oos = np.concatenate([blocks[i] for i in range(S) if i not in comb])
        if metric == "mean":
            a, o = mat[ins].mean(0), mat[oos].mean(0)
        else:
            a = mat[ins].mean(0) / (mat[ins].std(0, ddof=1) + 1e-9); o = mat[oos].mean(0) / (mat[oos].std(0, ddof=1) + 1e-9)
        best = int(np.argmax(a))
        rank = stats.rankdata(o)[best] / (len(o) + 1)
        lam.append(math.log(rank / (1 - rank)))
    lam = np.array(lam)
    return round(float((lam <= 0).mean()), 3), len(lam)
mat_all = M[active].to_numpy()
c20 = [b for b in active if b.startswith("c20")]
res["pbo"] = {"all active books mean": pbo(mat_all), "all active books sharpe": pbo(mat_all, metric="sharpe"),
              "c20 family mean": pbo(M[c20].to_numpy()), "c20 family sharpe": pbo(M[c20].to_numpy(), metric="sharpe"),
              "n_active": len(active), "n_c20": len(c20), "c20_books": c20}
# rank persistence: W1 (to 4 Nov) vs W2 (5-12 Nov)
w1 = [d for d in days if d < "2026-11-05"]; w2 = [d for d in days if d >= "2026-11-05"]
r1 = M.loc[w1, active].mean(); r2 = M.loc[w2, active].mean()
rs = stats.spearmanr(r1, r2)
top10 = r1.sort_values(ascending=False).index[:10]
res["persistence"] = {"spearman_W1_W2": round(float(rs.statistic), 3), "p": round(float(rs.pvalue), 3),
                      "top10_W1_mean_W2": round(float(r2[top10].mean()), 1), "all_mean_W2": round(float(r2.mean()), 1),
                      "top10_W1_rankpct_W2": [round(float(stats.percentileofscore(r2, r2[b])), 0) for b in top10],
                      "top10_W1": list(top10)}
# pool books' W1 and W2 rank
res["pool_rank"] = {b: {"W1_rank": int((r1 > r1[b]).sum() + 1), "W2_rank": int((r2 > r2[b]).sum() + 1)} for b in H.POOL}
r1p = M.loc[[d for d in days if d < "2026-10-30"], active].mean(); r2p = M.loc[POST9X, active].mean()
rsp = stats.spearmanr(r1p, r2p)
res["persistence_9xsplit"] = {"spearman": round(float(rsp.statistic), 3), "p": round(float(rsp.pvalue), 3)}

# ── F. Romano-Wolf style max-statistic bootstrap (studentized mean, stationary blocks) ──────────────────────────
def rw(mat, names, L=2, n=4000):
    T, K = mat.shape
    mu = mat.mean(0); sd = mat.std(0, ddof=1) + 1e-9
    tobs = mu / sd * math.sqrt(T)
    maxs = np.empty(n)
    for j in range(n):
        nb = math.ceil(T / L); st = rng.integers(0, T, nb)
        idx = ((st[:, None] + np.arange(L)[None, :]) % T).ravel()[:T]
        b = mat[idx]
        tb = (b.mean(0) - mu) / (b.std(0, ddof=1) + 1e-9) * math.sqrt(T)
        maxs[j] = tb.max()
    return {nm: round(float((maxs >= tobs[k]).mean()), 3) for k, nm in enumerate(names)}, \
        {nm: round(float(tobs[k]), 2) for k, nm in enumerate(names)}
print("pbo", round(time.time() - _t0, 1), flush=True); pv, tv = rw(mat_all, active)
res["rw_maxT_all17"] = {b: {"t": tv[b], "p_adj_all_books": pv[b]} for b in H.POOL}
best = max(tv, key=tv.get); res["rw_best"] = {"book": best, "t": tv[best], "p": pv[best]}
mat_post = M.loc[POST9X, active].to_numpy()
pv2, tv2 = rw(mat_post, active)
res["rw_maxT_post9x"] = {b: {"t": tv2[b], "p_adj_all_books": pv2[b]} for b in H.POOL}

# ── G. luck per pool book (unadjusted) ─────────────────────────────────────────────────────────────────────────
luck = {}
for b in H.POOL + ["CONDUCTOR"]:
    row = {}
    for lab, sel in [("all17", days), ("post9x", POST9X), ("test5", w2)]:
        x = M.loc[sel, b].to_numpy()
        row[f"p_signflip_{lab}"] = round(H.sign_flip_p(x, rng=rng), 3)
        s = mbb(x, 1, 10000).mean(1)
        row[f"p_boot_mean_le0_{lab}"] = round(float((s <= 0).mean()), 3)
    luck[b] = row
res["luck"] = luck
# trade-level clustering: intraclass correlation by day of pool trades' ret_pct
def icc(frame):
    g = frame.groupby("day")["ret_pct"]
    k = g.size(); n = k.sum(); a = len(k)
    msb = (k * (g.mean() - frame.ret_pct.mean()) ** 2).sum() / (a - 1)
    msw = ((frame.ret_pct - g.transform("mean")) ** 2).sum() / (n - a)
    k0 = (n - (k ** 2).sum() / n) / (a - 1)
    rho = (msb - msw) / (msb + (k0 - 1) * msw)
    return rho, k.mean()
res["icc"] = {}
for b in H.POOL:
    rho_, m_ = icc(pool_df[pool_df.book == b])
    nb = (pool_df.book == b).sum()
    res["icc"][b] = {"icc": round(float(rho_), 3), "trades": int(nb), "per_day": round(float(m_), 1),
                     "n_eff": round(float(nb / (1 + (m_ - 1) * max(rho_, 0))), 1)}
rho_, m_ = icc(tk)
res["icc"]["CONDUCTOR"] = {"icc": round(float(rho_), 3), "trades": len(tk), "per_day": round(float(m_), 1),
                           "n_eff": round(float(len(tk) / (1 + (m_ - 1) * max(rho_, 0))), 1)}
# pool redundancy
res["pool_corr"] = M[H.POOL].corr().round(2).to_dict()
json.dump(res, open(OUT, "w"), indent=1, default=str)

print(json.dumps(res, indent=1, default=str)[:20000])

