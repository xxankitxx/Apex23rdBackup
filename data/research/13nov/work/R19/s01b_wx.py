import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq, re
names = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet").names
wx=[n for n in names if n.startswith("wx_")]
for pat in ["range","er_|er60|eff","vix","gap","dte|expiry","agree","day_hi|day_lo|high|low","vwap","trend","orb|open"]:
    print(pat, [n for n in wx if re.search(pat,n)][:25])
