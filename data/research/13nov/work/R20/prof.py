import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time
t0=time.time()
from mc_lib import *
df=load(); print('load',time.time()-t0)
cx=pd.read_pickle('ctx_bocpd.pkl'); df=df.join(cx); print('join',time.time()-t0)
G={d:g for d,g in df.groupby('day')}
PRIO={b:i for i,b in enumerate(POOL)}
st={d:sim_day(G[d],books=POOL,prio=PRIO) for d in G}; print('static',time.time()-t0)
for c in ['fresh']:
    for k,x in df[df.fam.notna()].groupby(['day','fam',c]).win: pass
print('grp',time.time()-t0)
sc=score(df,st); print('score',time.time()-t0)
print(top_kept(df,st,st)); print('kept',time.time()-t0)
import cProfile, pstats
exec(open('s06_policies.py',encoding='utf-8').read().split("if SEC == 'gate'")[0].split("SEC = sys.argv[1]")[1].replace("df = load()","df = df"), globals())
print('setup2',time.time()-t0)
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
cProfile.run('run()','pr.out'); pstats.Stats('pr.out').sort_stats('cumtime').print_stats(8)
print('one',time.time()-t0)
