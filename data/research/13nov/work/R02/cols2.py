import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
wx = [n[3:] for n in s.names if n.startswith("wx_")]
print(" ".join(wx))
