import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
pd.set_option('display.width',250)
R=pd.read_pickle('policy_gate.pkl')
b=R[R.label=='static'].iloc[0]
R['d']=R.label.str.contains('dir1')
cols=['label','all_strike','all_n','all_sum','all_lose','all_worst','all_woBD','early_strike','early_sum','early_worst','late_strike','late_sum','late_lose','late_worst','kept']
print(R.sort_values(['d','label'])[cols].round(1).to_string())
for dm,g in R[R.label!='static'].groupby('d'):
    print('dir',dm,len(g),'strike both windows up',int(((g.early_strike>b.early_strike)&(g.late_strike>b.late_strike)).sum()),
      'worst all better',int((g.all_worst>b.all_worst).sum()),'sum all better',int((g.all_sum>b.all_sum).sum()),'woBD better',int((g.all_woBD>b.all_woBD).sum()))
pdd=pd.DataFrame({r.label:r._perday for r in R.itertuples()})
print(pdd[['static','gate pool N999 th0.45 dir1','gate c20all N999 th0.45 dir1','gate pool N6 th0.55 dir1','gate c20all N12 th0.45 dir1','gate pool N12 th0.45 dir1']].to_string())
