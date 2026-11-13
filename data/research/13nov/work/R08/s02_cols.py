import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pyarrow.parquet as pq, re
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = s.names
print(len(names))
print([n for n in names if not n.startswith(('wx_','h'))])
print([n for n in names if n.startswith('wx_') and re.search(r'wmove|breadth|hw|bank|bn|fn|sync|dom|lead|ep_|basket|nifty60|mv|fmv', n)])
print(sorted({re.match(r'h(\d+)_',n).group(1) for n in names if re.match(r'h\d+_',n)}, key=int))
print([n for n in names if n.startswith('h60_')])
