import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
f = pq.ParquetFile(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = f.schema.names
print(len(names))
print([n for n in names if not n.startswith("wx_") and not n.startswith("h")])
print([n for n in names if n.startswith("h")][:40])
import pandas as pd
df = pd.read_parquet(f.reader if False else r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day","book","t_in","t_out","trigger_t","entry","exit","ret_pct","pnl_rs"])
print(df.head()); print(df.day.value_counts().sort_index()); print(df.book.nunique())
print(df.trigger_t.isna().sum(), (df.trigger_t>df.t_in).sum())
print(sorted(df.book.unique()))
