import json, collections, numpy as np
H = r"D:\ApexOptions\data\research\13nov\work\R04"
s5 = {x["f"]: x for x in json.load(open(H + r"\out_s5_summary.json"))}
s6 = json.load(open(H + r"\out_s6_replicate.json"))["groups"]
s1 = {}
import glob
for fn in glob.glob(H + r"\out_s1_*.json"):
    r = json.load(open(fn)); s1[r["group"]] = {x["f"]: x for x in r["rows"]}
F = collections.defaultdict(lambda: {"acted": 0, "helped": 0, "hurt": 0, "rho_agree": 0, "rho_n": 0, "rt": []})
for g, v in s6.items():
    for x in v["rows"]:
        f = F[x["f"]]
        if x["dG_test"] != 0:
            f["acted"] += 1
            if x["dG_test"] > 0 and x["sr_test"] > x["base_sr_test"]: f["helped"] += 1
            if x["dG_test"] < 0: f["hurt"] += 1
for g, rows in s1.items():
    for nm, x in rows.items():
        a, b = x.get("rho_disc"), x.get("rho_test")
        if a is not None and b is not None:
            F[nm]["rho_n"] += 1; F[nm]["rho_agree"] += int(a * b > 0 and abs(b) >= 0.05); F[nm]["rt"].append(abs(b))
items = collections.defaultdict(list)
for nm, f in F.items():
    it = s5.get(nm, {}); items[(it.get("item"), it.get("label"))].append((nm, f))
tot_acted = sum(f["acted"] for f in F.values()); tot_help = sum(f["helped"] for f in F.values())
print("overall help rate when a line acts on test:", round(tot_help / tot_acted, 3), tot_help, tot_acted)
rows = []
for (n, lab), fs in items.items():
    acted = sum(f["acted"] for _, f in fs); helped = sum(f["helped"] for _, f in fs); hurt = sum(f["hurt"] for _, f in fs)
    ra = sum(f["rho_agree"] for _, f in fs); rn = sum(f["rho_n"] for _, f in fs)
    mrt = max([max(f["rt"]) if f["rt"] else 0 for _, f in fs])
    rows.append((n, lab, len(fs), acted, helped, hurt, ra, rn, round(mrt, 3)))
rows.sort(key=lambda r: (r[4] / max(1, r[3])))
print("item | label | fields | lines acting on test | helped | hurt | rank-sign kept (|rho|>=.05) / groups | max |rho_test|")
for r in rows: print(r)
nodata = sorted(nm for nm, x in s5.items() if x["class"].startswith("no data"))
print("NO DATA", nodata)
json.dump(rows, open(H + r"\out_s10_items.json", "w"), default=str)
