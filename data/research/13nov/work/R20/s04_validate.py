import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time
from mc_lib import *
t0 = time.time()
df = load()
prio = {b: i for i, b in enumerate(POOL)}
tk = {d: sim_day(g, books=POOL, prio=prio) for d, g in df.groupby('day')}
sc = score(df, tk, label='static')
print(fmt(sc))
cd = df[df.book == 'conductor']
for d, g in df.groupby('day'):
    a = df.loc[tk[d]]; b = cd[cd.day == d]
    print(d, len(a), len(b), round(day_ret(a.ret_pct), 1), round(day_ret(b.ret_pct), 1))
print(df.groupby('fam').size())
print(time.time() - t0)
