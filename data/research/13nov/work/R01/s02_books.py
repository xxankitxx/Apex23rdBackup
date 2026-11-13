import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
df = pd.read_parquet(P, columns=["day","book","rr","ret_pct","t_in","t_out","time_in","time_out","ep_type","why","reason","hold_s"])
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
g = df.groupby("book").agg(n=("ret_pct","size"), win=("ret_pct", lambda x: (x>0).mean()), mean=("ret_pct","mean"),
   med_hold=("hold_s","median"), ep=("ep_type", lambda x: x.value_counts().index[0] if x.notna().any() else None))
print(g.sort_values("n").to_string())
print(df.day.unique())
