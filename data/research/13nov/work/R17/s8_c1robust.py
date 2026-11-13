import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, guards as G, numpy as np, pandas as pd
df=sim.load(); base=sim.sim(df); days=sorted(base)
def score(r,ds): 
    n=sum(r[d]['n'] for d in ds); w=sum(r[d]['w'] for d in ds)
    return sum(r[d]['ret_day'] for d in ds), 100*w/max(n,1), n
print('base', score(base,sim.EARLY), score(base,sim.LATE))
res={}
for lt in (0.0,-3.0,-5.0,-10.0):
    for M in range(2,31,2):
        r=sim.sim(df,G.after_loss(M,lt)); res[(lt,M)]=r
        e=score(r,sim.EARLY); l=score(r,sim.LATE)
        dd=[round(r[d]['ret_day']-base[d]['ret_day'],1) for d in days]
        print(f'lt {lt:5} M {M:2d}: early {e[0]:7.1f} SR {e[1]:4.1f} n {e[2]:3d} | late {l[0]:6.1f} SR {l[1]:4.1f} n {l[2]:2d} | better {sum(x>0.05 for x in dd)} worse {sum(x<-0.05 for x in dd)} worst day {min(r[d]["ret_day"] for d in days):.1f}')
# diff-book only (what the per-book seq veto cannot see)
for M in (6,10,14):
    r=sim.sim(df,G.after_loss(M,0.0,diff_book=True)); e=score(r,sim.EARLY); l=score(r,sim.LATE)
    print('diffbook',M,round(e[0],1),round(e[1],1),e[2],'|',round(l[0],1),round(l[1],1),l[2])
# rolling: on each day from 23 Oct, choose (lt,M) by best sum of day % on all earlier days, apply to that day
cfg=list(res)
roll=[];baseroll=[]
for k,d in enumerate(days):
    if k<3: continue
    prior=days[:k]
    best=max(cfg,key=lambda c:(sum(res[c][x]['ret_day'] for x in prior), -c[1]))
    roll.append((d[5:],best,round(res[best][d]['ret_day'],1),round(base[d]['ret_day'],1)))
print('rolling choice per day (day, chosen (lt,M), guarded day %, base day %)')
for x in roll: print(x)
print('rolling total', round(sum(x[2] for x in roll),1),'base', round(sum(x[3] for x in roll),1), 'days better', sum(x[2]>x[3]+0.05 for x in roll), 'worse', sum(x[2]<x[3]-0.05 for x in roll))
