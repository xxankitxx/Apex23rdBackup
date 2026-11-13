import json
o = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R04\out_s6_replicate.json"))
for g, v in o["groups"].items(): print(g, v["summary"])
st = [x for x in o["strict"] if (x["dG_disc"] or 0) > 0]
print("strict with dG_disc>0:", len(st), "of", len(o["strict"]))
import collections
print(collections.Counter(x["group"] for x in st))
tot = sum(v["summary"]["n_bh"] for v in o["groups"].values()); print("total BH", tot)
