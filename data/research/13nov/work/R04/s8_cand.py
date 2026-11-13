import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 8: the few lines that passed every trade-level bar, judged at the EXACT Conductor account, all 17 days.
Also the rolling procedure (s4) totals."""
import json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L
d = L.load(); C = L.Conductor(d)
ni = {n: i for i, n in enumerate(d.names)}
cands = {"none": None,
         "sign_none_share300 >= 0.0212 (pool line)": ("sign_none_share300", ">=", 0.0212),
         "sign_none_share300 >= 0.0197 (c20 line)": ("sign_none_share300", ">=", 0.0197),
         "atm_iv_day_pos < 0.874 (Conductor single #4)": ("atm_iv_day_pos", "<", 0.874),
         "agree_same >= 7 (best disc single)": ("agree_same", ">=", 7.0),
         "range_vs_pd < 1.0142 (Conductor single #2)": ("range_vs_pd", "<", 1.0142),
         "with_vol_share300 < 0.636": ("with_vol_share300", "<", 0.636)}
R = np.flatnonzero(np.isin(d.book, L.POOL))
out = {}
for nm, c in cands.items():
    keep = None
    if c:
        x = d.X[:, ni[c[0]]].astype(float); keep = L.keep_mask(x, c[1], c[2])
    res = C.run(d.days, keep)
    rows = L.summarize_account(res, d)
    def blk(days):
        rr = [r for r in rows if r["day"] in days]
        n = sum(r["n"] for r in rr); w = sum(r["won"] for r in rr)
        lg = sum(np.log1p(r["ret_pct"] / 100) for r in rr)
        return {"n": n, "sr": round(w / n, 3) if n else None, "sum_log": round(lg, 3), "lose_days": sum(r["ret_pct"] < 0 for r in rr),
                "mean_day_pct": round(float(np.mean([r["ret_pct"] for r in rr])), 1),
                "worst_day": round(min(r["ret_pct"] for r in rr), 1)}
    disc = [x for x in d.days if x < L.TEST0]; test = [x for x in d.days if x >= L.TEST0]
    cov = None
    if c:
        cov = round(float(np.isfinite(d.X[R, ni[c[0]]]).mean()), 3)
    out[nm] = {"cov_pool": cov, "disc": blk(disc), "test": blk(test), "days": {r["day"]: (r["ret_pct"], r["n"], r["won"]) for r in rows}}
    print(nm, "cov", cov, "| DISC", out[nm]["disc"], "| TEST", out[nm]["test"])
    print("    test days", {k[5:]: v for k, v in out[nm]["days"].items() if k >= L.TEST0})
# sign_none_share300 value distribution on pool rows by day
x = d.X[R, ni["sign_none_share300"]].astype(float)
for dy in d.days:
    m = d.day[R] == dy
    xx = x[m]; xx = xx[np.isfinite(xx)]
    print(dy, len(xx), np.round(np.quantile(xx, [0.1, 0.5, 0.9]), 4) if len(xx) else None, "share<0.02:", round(float((xx < 0.0205).mean()), 2) if len(xx) else None)
s4 = json.load(open(os.path.join(L.HERE, "out_s4_rolling.json")))
b = r = 0.0
for row in s4["conductor"]:
    b += np.log1p(row["base_ret"] / 100); r += np.log1p(row["rule_ret"] / 100)
print("rolling conductor folds", len(s4["conductor"]), "sum log base", round(b, 3), "rule", round(r, 3),
      "better", sum(x["rule_ret"] > x["base_ret"] for x in s4["conductor"]), "worse", sum(x["rule_ret"] < x["base_ret"] for x in s4["conductor"]))
for g, rows in s4["trade"].items():
    print("rolling", g, "sum dG", round(sum(x["dG"] for x in rows if x.get("rule")), 3), "days +", sum(x["dG"] > 0 for x in rows if x.get("rule")),
          "-", sum(x["dG"] < 0 for x in rows if x.get("rule")), "0", sum(x["dG"] == 0 for x in rows if x.get("rule")))
json.dump(out, open(os.path.join(L.HERE, "out_s8_cand.json"), "w"), default=float)
