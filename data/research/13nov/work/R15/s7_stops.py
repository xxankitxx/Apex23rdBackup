import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import json, itertools
import numpy as np, pandas as pd
from simlib import *
W = r"D:\ApexOptions\data\research\13nov\work\R15"
C = json.load(open(W + r"\conf_days.json"))["POOL"]
def run(rule):
    out = {}
    for d in DAYS:
        cap = 1.0; streak = 0; n = 0; w = 0
        for t in C[d]["trades"]:
            if rule(cap, streak, n):
                break
            r = t[6] / 100; cap *= 1 + r; n += 1; w += r > 0
            streak = streak + 1 if r <= 0 else 0
        out[d] = (100 * (cap - 1), n, w)
    return out
rules = {"none": lambda c, s, n: False}
for k in (1, 2, 3, 4): rules[f"stop_after_{k}_losses_in_row"] = lambda c, s, n, k=k: s >= k
for x in (5, 10, 15, 20, 30): rules[f"stop_dd_{x}"] = lambda c, s, n, x=x: c <= 1 - x / 100
for y in (20, 50, 100): rules[f"stop_up_{y}"] = lambda c, s, n, y=y: c >= 1 + y / 100
for m in (3, 5, 8): rules[f"max_{m}_trades"] = lambda c, s, n, m=m: n >= m
rows = []
for k, f in rules.items():
    o = run(f)
    for wn, dd in (("EARLY", EARLY), ("LATE", LATE)):
        r = [o[d][0] for d in dd]; n = sum(o[d][1] for d in dd); w = sum(o[d][2] for d in dd)
        rows.append({"rule": k, "win": wn, "n": n, "sr": 100 * w / max(1, n), "sum": sum(r), "lose": sum(x < 0 for x in r),
                     "worst": min(r), "wo_best_day": sum(r) - max(r), "days": " ".join(f"{x:+.0f}" for x in r) if wn == "LATE" else ""})
T = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(T.pivot(index="rule", columns="win", values=["sum", "sr", "lose", "worst"]).round(1).to_string())
print(T[T.win == "LATE"][["rule", "days"]].to_string(index=False))
print("variants", len(rules) - 1)
