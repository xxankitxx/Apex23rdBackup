import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections
for day in ["2026-11-12","2026-11-13"]:
    rows=[json.loads(l) for l in open(rf"D:\ApexOptions\data\logs\perf_{day}.jsonl",encoding="utf-8") if l.strip()]
    rows=[r for r in rows if "09:15"<=r.get("mkt","")<="15:30"]
    n=sum(r["n"] for r in rows); tot=sum(r["sum_ms"] for r in rows)
    print(day,"minutes",len(rows),"steps",n,"total_s",round(tot/1000,1),"mean_ms",round(tot/max(n,1),2))
    import statistics
    print(" p50 of minute-p50",statistics.median(r["p50"] for r in rows)," median p95",statistics.median(r["p95"] for r in rows),
          " max p95",max(r["p95"] for r in rows)," over300",sum(r["over300"] for r in rows)," over1000",sum(r["over1000"] for r in rows))
    # phase mean ms per step weighted by n
    acc=collections.Counter(); mx=collections.defaultdict(float); cnt=collections.Counter()
    for r in rows:
        for k,(m,x) in r["ph"].items():
            acc[k]+=m*r["n"]; mx[k]=max(mx[k],x); cnt[k]+=1
    print(" phase, sum_s(weighted mean*n, top40 listed only), minutes listed, max_ms")
    for k,v in acc.most_common(45):
        print(f"   {k:32s} {v/1000:8.1f}s  {cnt[k]:4d}  {mx[k]:8.1f}")
    # by hour
    byh=collections.defaultdict(lambda:[0,0.0,[]])
    for r in rows:
        h=r["mkt"][:2]; byh[h][0]+=r["n"]; byh[h][1]+=r["sum_ms"]; byh[h][2].append(r["p95"])
    for h,(a,b,c) in sorted(byh.items()): print("  hour",h,"steps",a,"mean",round(b/a,1),"medp95",round(statistics.median(c),1))
