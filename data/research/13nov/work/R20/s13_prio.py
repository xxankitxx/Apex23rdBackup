import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
from mc_lib import *
df = load(); e = df[df.day <= EARLY_END]
for f in ('lvl', 't28'):
    s = e[e.fam == f].groupby('book').ret_pct.agg(['size', 'mean', lambda x: (x > 0).mean()]).sort_values('mean', ascending=False)
    print(f); print(s.round(2).to_string())
tk = pd.read_pickle('tk_lvl_ownlosing.pkl')
t = df.loc[[i for v in tk.values() for i in v]]
print(t.groupby('fam').agg(n=('ret_pct','size'), strike=('win','mean'), mean=('ret_pct','mean')).round(2))
print(t.groupby(['fam', t.day > EARLY_END]).agg(n=('ret_pct','size'), strike=('win','mean'), mean=('ret_pct','mean')).round(2))
tk = pd.read_pickle('tk_t28_both.pkl')
t = df.loc[[i for v in tk.values() for i in v]]
print(t.groupby(['fam', t.day > EARLY_END]).agg(n=('ret_pct','size'), strike=('win','mean'), mean=('ret_pct','mean')).round(2))
