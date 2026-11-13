import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq
s=pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
n=[c for c in s.names]
import re
keys=['mins','phase','gap','dte','expiry','event','or15','or30','pdh','pdl','time','open','last','drive','ib','orb','day']
print([c for c in n if not c.startswith('wx_') and not re.match(r'h\d+_',c)])
print([c for c in n if c.startswith('wx_') and any(k in c for k in keys)])
