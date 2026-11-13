import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, guards as G, numpy as np
df=sim.load(); base=sim.sim(df); days=sorted(base)
exec(open('s4_grid.py').read().split("GR={}")[0].split("base=sim.sim(df)")[1])  # stats()
res={}
for M in (20,30,40,45,50,60,75,90,120):
    r=sim.sim(df,G.whipsaw(M)); res[M]=r
    print(M,'E',stats(r,sim.EARLY,base)); print(M,'L',stats(r,sim.LATE,base))
print('BASE E',stats(base,sim.EARLY,base)); print('BASE L',stats(base,sim.LATE,base))
r=res[60]
print('whip60 per day (day, n, won, day %, base day %, blocked trigger count)')
for d in days: print(d[5:], r[d]['n'], r[d]['w'], round(r[d]['ret_day'],1), round(base[d]['ret_day'],1), len(r[d]['blocked']))
# what it blocked: base trades not taken
for d in days:
    ridx={x['idx'] for x in r[d]['taken']}
    lost=[(df.loc[x['idx'],'book'][-2:], df.loc[x['idx'],'rr'], round(x['ret'],1)) for x in base[d]['taken'] if x['idx'] not in ridx]
    new=[(df.loc[x['idx'],'book'][-2:], df.loc[x['idx'],'rr'], round(x['ret'],1)) for x in r[d]['taken'] if x['idx'] not in {y['idx'] for y in base[d]['taken']}]
    if lost or new: print(d[5:],'dropped',lost,'added',new)
# rolling choice of M on prior days
roll=[]
for k,d in enumerate(days):
    if k<3: continue
    pr=days[:k]; best=max(res,key=lambda M:(sum(res[M][x]['ret_day'] for x in pr),-M))
    roll.append((d[5:],best,round(res[best][d]['ret_day'],1),round(base[d]['ret_day'],1)))
print(roll); print('rolling',round(sum(x[2] for x in roll),1),'base',round(sum(x[3] for x in roll),1),'better',sum(x[2]>x[3]+.05 for x in roll),'worse',sum(x[2]<x[3]-.05 for x in roll))
