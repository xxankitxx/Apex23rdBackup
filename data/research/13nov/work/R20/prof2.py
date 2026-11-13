import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time, cProfile, pstats
t0=time.time()
sys.argv=['x','none']
src=open('s06_policies.py',encoding='utf-8').read().split("if SEC == 'gate'")[0]
exec(src)
print('setup',time.time()-t0)
fams={'c20pool'}; sname='pool'; dm=False; N=6; th=0.45
def run():
    tk={}
    for d in DAYS:
        L=Live(G[d],'c_none'); L.sets={sname:fams}
        def acc(r,L=L):
            L.adv(r.trig); w=L.tape.get((sname,None),[])[-N:]
            return len(w)<3 or (1+sum(w))/(2+len(w))>=th
        tk[d]=sim_day(G[d],acc,books=POOL,prio=PRIO)
    return tk
cProfile.run('run()','pr.out'); pstats.Stats('pr.out').sort_stats('cumtime').print_stats(10)
print('one',time.time()-t0)
