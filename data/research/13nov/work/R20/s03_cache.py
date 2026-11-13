import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np, time
t0=time.time()
p=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
cols=['day','book','t_in','t_out','trigger_t','ret_pct','rr','fut_in','fut_out','entry','exit','reason','pnl_rs',
 'wx_er60','wx_er_day','wx_chop30','wx_rv5_vs_norm','wx_range_vs_norm','wx_hmm_state','wx_hmm_p','wx_regime','wx_dte',
 'wx_vwap_ext','wx_mins_open','wx_dir60','wx_mv30','wx_mv300','wx_day_move','wx_expiry_day','wx_day_before_expiry','wx_vix']
df=pd.read_parquet(p,columns=cols)
df.to_pickle('trades_small.pkl'); print(df.shape, time.time()-t0)
print(df.wx_hmm_state.value_counts().head(10)); print(df.wx_regime.value_counts().head(10))
print(df[df.book=='conductor'].groupby('day').ret_pct.apply(lambda r: 100*(np.prod(1+r/100)-1)).round(1).to_string())
