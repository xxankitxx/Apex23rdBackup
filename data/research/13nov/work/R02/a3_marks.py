"""Mark-based exit rules (exit at a hold mark when a yes/no condition holds), walk-forward:
choose on 19 Oct - 4 Nov, score once on 5 - 12 Nov. Marks are LTP based: an exit at a mark is priced at
LTP - half the entry spread (a bid proxy). A rule can only exit EARLIER than the book did (at 60/300/900/1800 s)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, itertools
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
J = pd.read_pickle(W + r"\conductor_joined.pkl")
POOL = ['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
SPLIT = "2026-11-05"
def prep(d):
    d = d.copy()
    d["ret"] = d["ret_pct"] / 100.0
    d["exp"] = (d["day"] == d["expiry"])
    d["half"] = 0.5 * (d["entry_ask"] - d["entry_bid"]).clip(lower=0).fillna(0)
    return d
NOMARK = {"RAW","conductor"} | {b for b in df.book.unique() if "c20_" in b}
pool = prep(df[~df.book.isin(NOMARK)])        # the 92 engine books that record hold marks (council books do not)
cond = prep(df[df.book.isin(["t28_fwd","t28_core","t28_d46","t28_all","t28_fill","t28_core_fill","t28_d46_fill"])])   # forward-trigger t28 family
MARKS = (60, 300, 900, 1800)
def feat(d, m):
    f = {}
    g = f"h{m}_"
    op = (d["hold_s"] > m + 1) & d[g + "gain_pts"].notna()
    f["open"] = op
    f["g"] = (d[g + "gain_pts"] - d["half"]) / d["entry"]
    f["pk"] = d[g + "peak_pts"] / d["entry"]
    f["gbs"] = d[g + "giveback_share"]
    f["th"] = -d[g + "attr_theta_pts"]           # decay paid so far (pts, >0)
    f["de"] = d[g + "attr_delta_pts"]            # delta-explained pts
    f["iv"] = d[g + "attr_iv_chg"]
    f["ff"] = d[g + "fut_fav_pts"]
    f["fg"] = d[g + "fut_giveback_pts"]
    f["pa"] = d[g + "peak_age_s"]
    return f
RULES = []
for m in (300, 900, 1800):
    for x in (-0.08, -0.05, -0.02, 0.0, 0.02):
        RULES.append((f"m{m} gain<{x:+.2f}", m, lambda f, x=x: f["g"] < x))
    for x in (0.03, 0.05, 0.08, 0.10):
        RULES.append((f"m{m} peak<{x:.2f}", m, lambda f, x=x: f["pk"] < x))
    RULES.append((f"m{m} theta>delta", m, lambda f: f["th"] > f["de"].clip(lower=0)))
    RULES.append((f"m{m} theta>delta&gain<0", m, lambda f: (f["th"] > f["de"].clip(lower=0)) & (f["g"] < 0)))
    for y in (0, 10, 20):
        RULES.append((f"m{m} futfav<{y}", m, lambda f, y=y: f["ff"] < y))
    for s, p in itertools.product((0.5, 0.8), (0.05, 0.10)):
        RULES.append((f"m{m} gbshare>{s}&peak>{p}", m, lambda f, s=s, p=p: (f["gbs"] > s) & (f["pk"] > p)))
    for z in (0.5, 1.0, 2.0):
        RULES.append((f"m{m} ivchg<-{z}", m, lambda f, z=z: f["iv"] < -z))
    for x in (0.10, 0.20, 0.30):
        RULES.append((f"m{m} TP gain>{x}", m, lambda f, x=x: f["g"] > x))
    for a in (120, 300):
        RULES.append((f"m{m} peakage>{a}&gain<pk/2", m, lambda f, a=a: (f["pa"] > a) & (f["g"] < 0.5 * f["pk"])))
for x in (-0.05, -0.02):
    RULES.append((f"m60 gain<{x:+.2f}", 60, lambda f, x=x: f["g"] < x))
print("rules tried:", len(RULES))
def apply(d, rule):
    name, m, fn = rule
    f = feat(d, m)
    hit = f["open"] & fn(f).fillna(False)
    r = np.where(hit, f["g"], d["ret"])
    return pd.Series(r, index=d.index), hit
def score(d, r):
    out = {}
    lr = np.log1p(r.clip(lower=-0.99))
    out["n"] = len(r); out["win"] = 100 * float((r > 0).mean()) if len(r) else np.nan
    out["mean"] = 100 * float(r.mean()) if len(r) else np.nan
    out["logsum"] = 100 * float(lr.sum())
    # book-day compounding: each book's trades in time order, all-in
    dd = np.expm1(pd.Series(lr.values, index=d.index).groupby([d["book"], d["day"]]).sum())
    out["bookdays"] = len(dd); out["losing_bookdays"] = int((dd < 0).sum())
    out["mean_bookday"] = 100 * float(dd.mean()) if len(dd) else np.nan
    return out
res = []
for name, d in (("marked", pool), ("t28fwd", cond)):
    disc, test = d[d.day < SPLIT], d[d.day >= SPLIT]
    b_disc, b_test = score(disc, disc["ret"]), score(test, test["ret"])
    for rule in RULES:
        rd, hd = apply(disc, rule); rt, ht = apply(test, rule)
        sd, st = score(disc, rd), score(test, rt)
        res.append(dict(set=name, rule=rule[0], fired_disc=int(hd.sum()), fired_test=int(ht.sum()),
                        d_logsum=sd["logsum"] - b_disc["logsum"], d_win=sd["win"] - b_disc["win"],
                        t_logsum=st["logsum"] - b_test["logsum"], t_win=st["win"] - b_test["win"],
                        t_mean_bookday=st["mean_bookday"] - b_test["mean_bookday"], t_losing_bookdays=st["losing_bookdays"] - b_test["losing_bookdays"]))
    print(f"\n== {name}: baseline disc {b_disc} | test {b_test}")
R = pd.DataFrame(res)
pd.set_option("display.width", 250)
for name in ("marked", "t28fwd"):
    x = R[R.set == name].sort_values("d_logsum", ascending=False)
    print(f"\n== {name}: top 15 by discovery (sum of log returns, pct pts) and their test change")
    print(x.head(15).round(2).to_string(index=False))
    print(f"-- {name}: rules better in discovery: {(x.d_logsum > 0).sum()} of {len(x)}; better in test: {(x.t_logsum > 0).sum()}; both: {((x.d_logsum > 0) & (x.t_logsum > 0)).sum()}")
    print(x[(x.d_logsum > 0) & (x.t_logsum > 0)].round(2).to_string(index=False))
R.to_csv(W + r"\a3_marks.csv", index=False)
# which mark features predict the REMAINING return (hold from mark to the book's own exit)? Spearman, disc vs test
rows = []
for m in (300, 900, 1800):
    for nm, d in (("marked", pool),):
        f = feat(d, m); op = f["open"]
        rem = (d["ret"] - f["g"])[op]
        for k in ("g", "pk", "gbs", "th", "de", "iv", "ff", "fg", "pa"):
            for per, msk in (("disc", d.day < SPLIT), ("test", d.day >= SPLIT)):
                mm = op & msk & f[k].notna()
                if mm.sum() > 20:
                    rho = f[k][mm].rank().corr((d["ret"] - f["g"])[mm].rank())
                    rows.append(dict(mark=m, feat=k, per=per, n=int(mm.sum()), rho=round(float(rho), 3)))
F = pd.DataFrame(rows).pivot_table(index=["mark", "feat"], columns="per", values=["rho", "n"]).round(3)
print("\n== Spearman of mark feature vs the return still to come (book exit minus exit-now), pool5")
print(F.to_string())
