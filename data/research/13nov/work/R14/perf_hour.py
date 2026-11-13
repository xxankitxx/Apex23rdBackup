import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections
PH = ["step:market","step:greeks","step:guard-domino-regime","publish","step:ctx","forward view","weather base","strike levels","edge snapshot","step:books","save exit state","ideas","quant view"]
for day in ["2026-11-11","2026-11-12","2026-11-13"]:
    rows=[json.loads(l) for l in open(rf"D:\ApexOptions\data\logs\perf_{day}.jsonl",encoding="utf-8") if l.strip()]
    rows=[r for r in rows if "09:15"<=r.get("mkt","")<="15:30"]
    by=collections.defaultdict(lambda: collections.Counter()); nn=collections.Counter()
    for r in rows:
        h=r["mkt"][:2]; nn[h]+=r["n"]
        for k in PH:
            if k in r["ph"]: by[h][k]+=r["ph"][k][0]*r["n"]
    print("==",day, "mean ms per step by hour")
    print("hour  " + " ".join(f"{k.replace('step:','')[:10]:>10s}" for k in PH))
    for h in sorted(nn):
        print(h, "  ", " ".join(f"{by[h][k]/nn[h]:10.2f}" for k in PH))
