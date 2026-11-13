import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
t=pd.read_parquet('t_small.parquet'); c=pd.read_parquet('cond.parquet')
t['sgn']=np.where(t.rr=='CE',1,-1)
t['gap_raw']=t.wx_gap_pts*t.sgn
print(t.groupby('day').gap_raw.agg(['min','max','count']))
t['pdh_raw']=t.wx_to_pdh; 
m=c.merge(t.drop(columns=['time_in','rr','ret_pct','pnl_rs','reason','why','trigger_t','entry','t_out']),left_on=['day','src','t_in'],right_on=['day','book','t_in'],how='left')
print('matched',m.wx_mins_open.notna().sum(),'of',len(m))
m.to_parquet('cond_wx.parquet')
