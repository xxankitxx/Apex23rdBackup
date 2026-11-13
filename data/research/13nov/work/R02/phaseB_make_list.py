"""PHASE B helper: list the (part, chunk) runs needed so every pool trade inside a built part is covered."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, glob, os, math
W = r"D:\ApexOptions\data\research\13nov\work\R02"
DS = r"D:\ApexOptions\data\research\ds_v2"
T = json.load(open(W + r"\pool_trades.json", encoding="utf-8"))
lines = []
for m in sorted(glob.glob(DS + r"\*.manifest.json")):
    man = json.load(open(m, encoding="utf-8"))
    if not man.get("rows"):
        continue
    part = os.path.basename(m).replace(".manifest.json", "")
    day = part[:10]
    n = sum(1 for x in T if x["day"] == day and man["first"] <= x["t_in"] <= man["last"])
    for k in range(math.ceil(n / 20)):
        lines.append(f"py -3.13 -W ignore phaseB_paths.py {part} {k}")
open(W + r"\phaseB_list.txt", "w").write("\n".join(lines) + "\n")
print(len(lines), "runs")
