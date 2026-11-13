import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, guards as G
df=sim.load(); base=sim.sim(df); days=sorted(base)
fam=sim.load(pool_only=False); books=sorted(fam.book.unique()); subs={b:fam[fam.book==b] for b in books}; r0={b:sim.sim(subs[b]) for b in books}
V={'whip15':G.whipsaw(15),'whip30':G.whipsaw(30),'whip60':G.whipsaw(60),'whip999':G.whipsaw(999),'sideban2':G.side_ban(2),'sideban3':G.side_ban(3)}
for k,g in V.items():
    r=sim.sim(df,g)
    e=sum(r[d]['ret_day'] for d in sim.EARLY); l=sum(r[d]['ret_day'] for d in sim.LATE)
    ne=sum(r[d]['n'] for d in sim.EARLY); we=sum(r[d]['w'] for d in sim.EARLY); nl=sum(r[d]['n'] for d in sim.LATE); wl=sum(r[d]['w'] for d in sim.LATE)
    dd={d[5:]:round(r[d]['ret_day']-base[d]['ret_day'],1) for d in days if abs(r[d]['ret_day']-base[d]['ret_day'])>0.05}
    E=L=0; b=w=0
    for bk in books:
        rr=sim.sim(subs[bk],g)
        for d in rr:
            dv=rr[d]['ret_day']-r0[bk][d]['ret_day']
            if d in sim.LATE: L+=dv
            else: E+=dv
            b+=dv>0.05; w+=dv<-0.05
    print(f"{k}: cond early {e:.1f} SR {100*we/ne:.1f} n{ne} | late {l:.1f} SR {100*wl/nl:.1f} n{nl} | changed days {dd} | family delta early {E:.1f} late {L:.1f} book-days better {b} worse {w}")
