import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, pyarrow.parquet as pq, re, collections
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
names = pq.read_schema(P).names
h = [n for n in names if re.match(r"h[^_]+_", n) and not n.startswith("hw")]
marks = collections.OrderedDict()
for n in h:
    m, f = n.split("_",1); marks.setdefault(m, []).append(f)
for m,f in marks.items(): print(m, len(f), f if m==list(marks)[0] else "")
df = pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R02\all_trades_slim.pkl")
print([c for c in df.columns if c.startswith("h")][:40])
for c in [c for c in df.columns if c.startswith("h") and c.endswith("gain_pts")]:
    print(c, df[c].notna().mean())
