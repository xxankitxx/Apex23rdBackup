import json, numpy as np
o = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R04\out_s2_conductor.json"))
pf = o["per_feature"]
print("features with a valid line at the account:", len(pf))
t = np.array([x["test_dObj"] for x in pf]); dd = np.array([x["dObj"] for x in pf])
print("disc dObj>0:", int((dd > 0).sum()), "test dObj>0:", int((t > 0).sum()), "test<0:", int((t < 0).sum()), "test=0:", int((t == 0).sum()))
top = sorted(pf, key=lambda x: -x["dObj"])
print("top 20 by discovery, test dObj:", [ (x["f"], x["dObj"], x["test_dObj"]) for x in top[:20]])
k = [i for i, x in enumerate(top) if x["f"] == "sign_none_share300"]
print("sign_none_share300 rank", k, top[k[0]] if k else None)
print("spearman disc vs test:", np.corrcoef(np.argsort(np.argsort(dd)), np.argsort(np.argsort(t)))[0, 1])
for q in (10, 25, 50, 100):
    print("top", q, "mean test dObj", round(float(np.mean([x["test_dObj"] for x in top[:q]])), 3), "share>0", round(float(np.mean([x["test_dObj"] > 0 for x in top[:q]])), 2))
print("null", o["null"])
s6 = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R04\out_s6_replicate.json"))
for g in ("pool_events", "pool_trades", "fam:c20", "all"):
    for x in s6["groups"][g]["rows"]:
        if x["f"].startswith("sign_none") or x["f"] in ("atm_iv_day_pos",):
            print(g, x["f"], x["op"], round(x["line"], 4), "dGd", x["dG_disc"], "p", x["p"], "bh", x["bh"], "dGt", x["dG_test"], "sr", x["sr_test"], x["base_sr_test"], x["days_pos"], x["days_neg"])
