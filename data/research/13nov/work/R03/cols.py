import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
f = pq.ParquetFile(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = f.schema.names
print(len(names))
nonwx = [n for n in names if not n.startswith("wx_") and not (n.startswith("h") and "_" in n and n[1:n.index("_")].isdigit())]
print(nonwx)
wx = [n for n in names if n.startswith("wx_")]
print(len(wx))
print(" ".join(wx))
hm = sorted(set(n.split("_")[0] for n in names if n.startswith("h") and "_" in n and n[1:n.index("_")].isdigit()))
print(hm)
print(sorted(set(n.split("_",1)[1] for n in names if n.startswith("h60_"))))
