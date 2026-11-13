import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, pyarrow.parquet as pq
s = pq.read_schema(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet")
names = s.names
for k in ["peak","best","bank_z","basket_gap","vwap_side","dte","gap_filled","gap_pts","or30","hmm"]:
    print(k, [n for n in names if k in n][:12])
print([n for n in names if not n.startswith(("wx_","h"))][:80])
j = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))
print(type(j), list(j.keys())[:10] if isinstance(j,dict) else len(j))
d = j.get("days", j) if isinstance(j, dict) else j
if isinstance(d, dict):
    k0 = list(d.keys())[0]; print(k0, str(d[k0])[:800])
elif isinstance(d, list): print(str(d[0])[:800])
