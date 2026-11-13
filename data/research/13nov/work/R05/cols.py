import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
pf = pq.ParquetFile(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = pf.schema_arrow.names
print(len(names))
non = [n for n in names if not n.startswith("wx_") and not (n.startswith("h") and "_" in n and n.split("_")[0][1:].isdigit())]
print("NON wx/h:", non)
hm = sorted(set(n.split("_")[0] for n in names if n.startswith("h") and n.split("_")[0][1:].isdigit()), key=lambda s:int(s[1:]))
print("marks:", hm)
h60 = [n for n in names if n.startswith("h60_")]
print("h60 fields:", h60)
wx = [n for n in names if n.startswith("wx_")]
print(len(wx))
print(wx)
