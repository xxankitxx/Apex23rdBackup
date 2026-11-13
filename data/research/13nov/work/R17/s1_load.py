import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, json, numpy as np
P=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
base=['day','book','key','strike','rr','entry','exit','t_in','t_out','trigger_t','time_in','time_out','ret_pct','pnl_rs','reason','why','ep_type','regime','iv_in','iv_out','dte_in','fut_in','fut_out','delta_in','peak_pts','worst_pts','entry_bid','entry_ask','fill_delay_s','exit_quote_age']
import pyarrow.parquet as pq
names=pq.read_schema(P).names
wx=[n for n in names if n.startswith('wx_')]
hcols=[n for n in names if n.startswith('h') and n not in base and n.split('_')[0] in ('h60','h300','h900','h1800','hexit')]
df=pd.read_parquet(P,columns=base+wx+hcols, filters=[('book','in',['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t','c20_8x','c20_9e','c20_9h','c20_9x_r002','c20_9x_r004'])])
print(df.shape, df.memory_usage(deep=True).sum()/1e6)
df.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R17\c20.pkl")
print(df.book.value_counts())
