import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, json, numpy as np
P=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
cols=['day','book','t_in','t_out','time_in','rr','ret_pct','pnl_rs','hold_s','reason','why','trigger_t','dte_in','entry',
'wx_mins_open','wx_phase_bucket','wx_gap_pts','wx_gap_filled','wx_dte','wx_expiry_day','wx_day_before_expiry','wx_event',
'wx_or15_pos','wx_or30_pos','wx_to_pdh','wx_to_pdl','wx_weekday','wx_hrs_to_expiry','wx_mins_to_flat','wx_day_move','wx_er_day','wx_ret_today','wx_n_today','wx_vix_chg_open','wx_after_break','wx_to_pdc','wx_dist_hi','wx_dist_lo','wx_pos_dir','wx_er30','wx_mv300','wx_open_side_min']
import pyarrow.parquet as pq
names=set(pq.read_schema(P).names); cols=[c for c in cols if c in names]
df=pd.read_parquet(P,columns=cols)
df.to_parquet('t_small.parquet')
print(df.shape); print(df.day.value_counts().sort_index())
print(df.groupby('day')[['wx_dte','wx_gap_pts','wx_event','wx_day_before_expiry','wx_weekday']].agg(lambda s: s.dropna().iloc[0] if s.notna().any() else None))
# conductor
tr=[]
a=json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))['days']
b=json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"))['days']
r4=['2026-10-28','2026-10-30','2026-11-02','2026-11-03']
for d,v in a.items():
    if d in r4: continue
    for t in v['trades']: t['day']=d; tr.append(t)
for d,v in b.items():
    if d not in r4: continue
    for t in v['trades']: t['day']=d; tr.append(t)
c=pd.DataFrame(tr); print(c.shape, c.day.nunique()); print(c.groupby('day').ret_pct.agg(['count','sum']))
c.to_parquet('cond.parquet')
