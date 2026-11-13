import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = s.names
print(len(names))
base = [n for n in names if not n.startswith("wx_") and not n.startswith("h")]
print("BASE:", base)
hs = sorted(set(n.split("_",1)[0] for n in names if n.startswith("h") and "_" in n and n[1:2].isdigit()))
print("MARKS:", hs)
hf = sorted(set(n.split("_",1)[1] for n in names if n.startswith("h60_")))
print("HFIELDS:", hf)
wx = [n[3:] for n in names if n.startswith("wx_")]
print("WX:", wx)
