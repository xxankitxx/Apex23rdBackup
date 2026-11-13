import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = s.names
print(len(names))
nonwx = [n for n in names if not n.startswith("wx_")]
print(nonwx)
