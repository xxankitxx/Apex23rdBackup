import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R18"); import sim
t=pd.read_parquet('t_b.parquet'); c=pd.read_parquet('cond_b.parquet')
pool=t[t.book.isin(sim.PRIO)].copy()
pool['trigger_t']=pool.trigger_t.fillna(pool.t_in)
tk=sim.run(pool)
alld=sorted(t.day.unique())
a=sim.days(tk,alld); b=sim.days(c,alld)
print(pd.concat([a.add_prefix('sim_'),b.add_prefix('cond_')],axis=1).round(1))
print('sim',sim.summ(tk,alld)); print('cond',sim.summ(c,alld))
