import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq, pandas as pd
p=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
sch=pq.read_schema(p); names=sch.names
print(len(names)); print([n for n in names if not n.startswith(('wx_','h'))])
print([n for n in names if n.startswith('wx_')][:400])
hs=[n for n in names if n.startswith('h') and '_' in n and n[1].isdigit()]
print(hs[:60])
df=pd.read_parquet(p,columns=['day','book','t_in','t_out','ret_pct','trigger_time'])
print(df.day.value_counts().sort_index())
print(df.book.nunique()); print(df.groupby('book').size().sort_values().to_string())
