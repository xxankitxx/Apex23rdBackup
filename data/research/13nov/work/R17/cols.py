import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = s.names
print(len(names))
base=[n for n in names if not n.startswith('wx_') and not n.startswith('h')]
print(base)
hs=[n for n in names if n.startswith('h') and n not in base]
print(sorted(set(n.split('_')[0] for n in hs)), sorted(set('_'.join(n.split('_')[1:]) for n in hs)))
wx=[n for n in names if n.startswith('wx_')]
print(' '.join(wx))
