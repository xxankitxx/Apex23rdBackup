import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, os, re, glob, collections
MISS = re.compile(r"—\s?(pts|away|%|/min)|(is|at|of|by|to) —(?=[\s.,;]|$)|\(—\)|: —(?=[\s.,;]|$)|\[\w[\w.]*: \w+Error\]")
n = m = 0; keys = collections.Counter(); ex = {}
files = glob.glob(r"D:\ApexOptions\data\replay\batch\p44_*\paper\commentary_*.jsonl") + glob.glob(r"D:\ApexOptions\data\paper\commentary_2026-11-1[123].jsonl")
for f in files:
    for l in open(f, encoding="utf-8"):
        r = json.loads(l); t = r.get("text")
        if not t or r.get("kind") == "verdict": continue
        n += 1
        if MISS.search(t):
            m += 1; keys[r.get("key")] += 1; ex.setdefault(r.get("key"), t[:160])
print(f"remarks {n}, with a missing value or a format error {m} ({100*m/n:.1f}%)")
for k, c in keys.most_common(12): print(c, k, "|", ex[k])
