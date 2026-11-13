import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time; t0=time.time()
import pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
df = pd.read_parquet(P, columns=["day","book","ret_pct","pnl_rs","why","ep_type","t_in","trigger_t"])
print("load", round(time.time()-t0,1))
print(df.groupby("day").size().to_string())
g = df.groupby("book").agg(n=("ret_pct","size"), win=("ret_pct", lambda x: (x>0).mean()), mean=("ret_pct","mean"))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print(g.sort_values("n", ascending=False).to_string())
print(df["ep_type"].value_counts().head(30).to_string())
print(df["why"].str.slice(0,25).value_counts().head(40).to_string())
