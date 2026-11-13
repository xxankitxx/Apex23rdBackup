import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, json
df=sim.load(); res=sim.sim(df)
ref={}
for f in [r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"]:
    d=json.load(open(f,encoding='utf-8'))['days']
    for k,v in d.items():
        if 'simr' in f or k not in ('2026-10-28','2026-10-30','2026-11-02','2026-11-03'): ref[k]=v
tot=0
for d in sorted(res):
    r=res[d]; x=ref.get(d,{})
    print(d, r['n'], r['w'], round(r['ret_day'],1), '| ref', x.get('n'), x.get('wins'), x.get('ret_day_pct'))
    tot+=r['ret_day']
print(tot, sim.summary(res), sim.summary(res,sim.EARLY), sim.summary(res,sim.LATE))
