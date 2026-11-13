import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, time
t0=time.time()
P=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
c=["day","book","trigger_t","t_in","t_out","time_in","entry","exit","ret_pct","pnl_rs","rr","dir","why","reason","fut_in","fut_out","spot_in","ep_type","regime"]
df=pd.read_parquet(P,columns=c)
df.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R03\base.pkl")
print(df.shape, time.time()-t0)
g=df.groupby("book").agg(n=("ret_pct","size"),days=("day","nunique"),win=("ret_pct",lambda s:(s>0).mean()),mret=("ret_pct","mean"))
pd.set_option("display.width",250); pd.set_option("display.max_rows",300)
print(g.sort_index().to_string())
print(df.groupby("day").size().to_string())
print(df[["dir","rr"]].value_counts())
