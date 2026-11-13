import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import gzip, time, zlib, re
t=time.time(); n=0
with gzip.open(r"D:\ApexOptions\data\ticks\2026-10-19.p2.jsonl.gz","rb") as f:
    while True:
        b=f.read(1<<23)
        if not b: break
        n+=len(b)
t1=time.time()
d=zlib.decompressobj(31); n2=0
with open(r"D:\ApexOptions\data\ticks\2026-10-19.p2.jsonl.gz","rb") as f:
    while True:
        b=f.read(1<<22)
        if not b: break
        n2+=len(d.decompress(b))
t2=time.time()
print(n/1e6, round(t1-t,2), n2/1e6, round(t2-t1,2))
