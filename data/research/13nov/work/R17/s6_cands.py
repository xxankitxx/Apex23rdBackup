import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, guards as G, numpy as np, pandas as pd
C={'C1 any entry <10 min after a loss':G.any_after_loss(10),
   'C2 other side <10 min after a loss':G.flip_after_loss(10),
   'C3 er60 in [0.10,0.25)':G.band('wx_er60',0.10,0.25),
   'C4 ATM IV 5-min chg in (-0.1,0]':G.band('wx_atm_iv_chg5',-0.1,0.0001),
   'C5 no entry from 14:15':G.late('14:15'),
   'C6 >=100 pts against an efficient day':G.against_trend(100,0.1),
   'C7 option quote older than 0.8 s':G.quote_age(0.8),
   'C1+C3':G.OR(G.any_after_loss(10),G.band('wx_er60',0.10,0.25)),
   'C1+C5':G.OR(G.any_after_loss(10),G.late('14:15')),
   'C2+C5':G.OR(G.flip_after_loss(10),G.late('14:15')),
}
df=sim.load(); base=sim.sim(df)
days=sorted(base)
out=[]
print('BASE per day', {d[5:]:round(base[d]['ret_day'],1) for d in days})
for name,g in C.items():
    r=sim.sim(df,g)
    dd={d[5:]:round(r[d]['ret_day']-base[d]['ret_day'],1) for d in days}
    better=sum(v>0.05 for v in dd.values()); worse=sum(v<-0.05 for v in dd.values())
    late={d:dd[d[5:]] for d in sim.LATE}
    print(f'\n{name}: days better {better}, worse {worse}; late-window deltas {list(late.values())}')
    print('  per day delta', dd)
    print('  late per day: ', [(d[5:], r[d]['n'], r[d]['w'], round(r[d]['ret_day'],1)) for d in sim.LATE])
# family robustness: each c20 book as its own all-in account with its own history
fam=sim.load(pool_only=False)
books=sorted(fam.book.unique())
subs={bk:fam[fam.book==bk] for bk in books}
r0s={bk:sim.sim(subs[bk]) for bk in books}
print('\nFAMILY (10 c20 books, each own account): sum of day % early | late ; book-days better/worse')
for name,g in [('none',None)]+list(C.items()):
    E=L=0.0; b=w=0; srE=[];srL=[]
    for bk in books:
        sub=subs[bk]; r0=r0s[bk]; r=sim.sim(sub,g) if g else r0
        for d in r:
            v=r[d]['ret_day']; dv=v-r0[d]['ret_day']
            if d in sim.LATE: L+=v
            else: E+=v
            b+=dv>0.05; w+=dv<-0.05
            for x in r[d]['taken']: (srL if d in sim.LATE else srE).append(x['ret']>0)
    print(f'{name:40s} early {E:8.1f} (SR {100*np.mean(srE):.1f}, n {len(srE)}) | late {L:7.1f} (SR {100*np.mean(srL):.1f}, n {len(srL)}) | better {b} worse {w}')
