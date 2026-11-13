import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq, pandas as pd
p = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
s = pq.read_schema(p)
names = s.names
nw = [n for n in names if not n.startswith("wx_") and not (n.startswith("h") and "_" in n and n[1:n.index("_")].isdigit())]
print(len(names)); print(nw)
hm = sorted({n.split("_")[0] for n in names if n.startswith("h") and "_" in n and n[1:n.index("_")].isdigit()})
print(hm)
print([n for n in names if n.startswith("h60_")])
df = pd.read_parquet(p, columns=["day","book","t_in","trigger_t","ret_pct","pnl_rs","entry","exit","rr","time_in"])
print(df.day.value_counts().sort_index())
print(df.book.nunique()); print(df.head())
for b in ["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t"]:
    x=df[df.book==b]; print(b,len(x),(x.ret_pct>0).mean().round(3),x.ret_pct.mean().round(2))
