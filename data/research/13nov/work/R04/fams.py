import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R04")
import r04lib as L
m = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R04\cache_meta.json"))
bk = m["strs"]["book"]; dy = m["strs"]["day"]
c = collections.Counter(L.family(b) for b in bk)
t = collections.Counter(L.family(b) for b, d in zip(bk, dy) if d >= "2026-11-05")
nb = collections.defaultdict(set)
for b in bk: nb[L.family(b)].add(b)
for f, n in c.most_common(): print(f, n, t[f], len(nb[f]), sorted(nb[f])[:6])
print(len(m["names"]))
