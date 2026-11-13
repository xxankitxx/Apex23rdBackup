import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections, re
GROUPS = {
 "display/observer (no book reads it)": ["publish","quant view","ideas","pred","commentary","forecast panel","gen2","gen3","episode log","decision tape","ideas view","health"],
 "persistence": ["save exit state","save books (trade)","warm save","strike levels save"],
 "photo inputs (weather)": ["weather base","weather feed v3","weather feed","weather tick v5","option history","edge snapshot","strike levels","forward history"],
}
for day in ["2026-11-11","2026-11-12","2026-11-13"]:
    rows=[json.loads(l) for l in open(rf"D:\ApexOptions\data\logs\perf_{day}.jsonl",encoding="utf-8") if l.strip()]
    rows=[r for r in rows if "09:15"<=r.get("mkt","")<="15:30"]
    tot=sum(r["sum_ms"] for r in rows)/1000; n=sum(r["n"] for r in rows)
    acc=collections.Counter()
    for r in rows:
        for k,(m,x) in r["ph"].items(): acc[k]+=m*r["n"]/1000
    print(f"== {day}: steps {n}, engine step time {tot:.0f} s, mean {1000*tot/n:.1f} ms/step, over300 {sum(r['over300'] for r in rows)}, over1000 {sum(r['over1000'] for r in rows)}")
    for g,ks in GROUPS.items():
        s=sum(acc[k] for k in ks); print(f"   {g:40s} {s:7.0f} s  {100*s/tot:5.1f} %")
    rb=sum(v for k,v in acc.items() if re.match(r"book:.*_r00\d", k))
    allb=sum(v for k,v in acc.items() if k.startswith("book:"))
    print(f"   restricted books (book:*_r00N, >2ms steps only) {rb:7.0f} s  {100*rb/tot:5.1f} %   all book:* {allb:.0f} s")
    top=[(k,v) for k,v in acc.items() if k.startswith("book:")]; top.sort(key=lambda x:-x[1])
    print("   top books:", ", ".join(f"{k[5:]} {v:.0f}s" for k,v in top[:10]))
    # minutes with high p95 and the save lag
    hi=[r for r in rows if r["p95"]>300]
    print(f"   minutes with p95>300ms: {len(hi)}; of them with save lag>0 at minute end: {sum(1 for r in hi if (r.get('save') or {}).get('lag',0)>0)}")
    lm=[ (r.get('save') or {}).get('last_ms') for r in rows if (r.get('save') or {}).get('last_ms')]
    if lm: 
        lm.sort(); print(f"   books write last_ms median {lm[len(lm)//2]:.0f} p90 {lm[int(len(lm)*.9)]:.0f} max {lm[-1]:.0f}; commits {rows[-1].get('save',{}).get('commits')}")
