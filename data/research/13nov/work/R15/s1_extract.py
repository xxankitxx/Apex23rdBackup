import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time; t0=time.time()
import pandas as pd
cols=["day","book","key","t_in","t_out","trigger_t","entry","exit","ret_pct","pnl_rs","rr","strike","reason","why","hold_s","lots","ep_type","dte_in"]
df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=cols)
df.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R15\trades_small.parquet")
print(df.shape, time.time()-t0)
print(df.dtypes)
