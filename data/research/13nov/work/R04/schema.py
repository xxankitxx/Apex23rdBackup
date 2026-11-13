import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
f = pq.ParquetFile(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
s = f.schema_arrow
print(f.metadata.num_rows, len(s))
names = [(n, str(s.field(n).type)) for n in s.names]
wx = [x for x in names if x[0].startswith("wx_")]
h = [x for x in names if x[0].startswith("h") and "_" in x[0] and x[0][1].isdigit()]
other = [x for x in names if x not in wx and x not in h]
print("WX", len(wx), "H", len(h), "OTHER", len(other))
print("OTHER:", other)
import collections
print("WX types", collections.Counter(t for _, t in wx))
with open("wx_cols.txt", "w") as fo:
    for n, t in wx: fo.write(f"{n}\t{t}\n")
print("H sample", h[:40])
