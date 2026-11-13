import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Conductor entries vs the fused 2-minute stand (walk-forward probabilities from study2.py) at the entry second."""
import os, glob, json
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
B = r"D:\ApexOptions\data\replay\batch"
R = np.load(os.path.join(D, "stand_rows.npz"))
cache = {os.path.basename(f)[:10]: np.load(f)["t"] for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz")))}
A = json.load(open(os.path.join(B, "p44_sim", "conductor_sim.json")))["days"]
Rr = json.load(open(os.path.join(B, "p44_simr", "conductor_sim.json")))["days"]
rows = []
for day in sorted(cache):
    if f"lag0_H120|{day}" not in R.files:
        continue
    src = Rr if day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03") else A
    dd = src.get(day)
    if not dd:
        continue
    t = cache[day]; p = R[f"lag0_H120|{day}"].astype(float)
    for tr in dd["trades"]:
        k = np.searchsorted(t, tr["t_in"], side="right") - 1
        if k < 0 or tr["t_in"] - t[k] > 10:
            continue
        pu = p[k] if tr["rr"] == "CE" else 1 - p[k]               # probability the stand gives the trade's direction
        cls = "with" if pu >= 0.56 else "against" if pu <= 0.44 else "neutral"
        rows.append((day, cls, tr["ret_pct"], pu))
print("trades matched", len(rows))
for win, sel in (("early 27 Oct-4 Nov", lambda d: d <= "2026-11-04"), ("late 5-11 Nov", lambda d: d >= "2026-11-05"), ("all", lambda d: True)):
    print(win)
    for c in ("with", "neutral", "against"):
        r = [x[2] for x in rows if sel(x[0]) and x[1] == c]
        if r:
            g = np.prod([1 + v / 100 for v in r]) - 1
            print(f"   {c:8s} n={len(r):3d} won {np.mean([v > 0 for v in r]):.0%} mean {np.mean(r):+.1f} % compounded {g * 100:+.0f} %")
by = {}
for d, c, r, _ in rows:
    by.setdefault(d, {}).setdefault(c, []).append(r)
print("per day mean ret (with / neutral / against):")
for d in sorted(by):
    print("  ", d[5:], " / ".join(f"{np.mean(by[d][c]):+.1f} ({len(by[d][c])})" if c in by[d] else "-" for c in ("with", "neutral", "against")))

print("\nskip-when-with rule (keep neutral + against), per window: trades, won, compounded, without best trade, worst day")
for win, sel in (("early", lambda d: d <= "2026-11-04"), ("late", lambda d: d >= "2026-11-05")):
    for name, keep in (("all trades", lambda c: True), ("skip 'with'", lambda c: c != "with")):
        r = [(d, x) for d, c, x, _ in rows if sel(d) and keep(c)]
        v = [x for _, x in r]
        g = np.prod([1 + x / 100 for x in v]) - 1
        vb = sorted(v)[:-1]
        gb = np.prod([1 + x / 100 for x in vb]) - 1
        dd = {}
        for d, x in r:
            dd[d] = dd.get(d, 1.0) * (1 + x / 100)
        print(f"  {win} {name:12s} n={len(v):3d} won {np.mean([x > 0 for x in v]):.0%} comp {g * 100:+.0f} % without best {gb * 100:+.0f} % "
              f"worst day {(min(dd.values()) - 1) * 100:+.1f} % losing days {sum(x < 1 for x in dd.values())}/{len(dd)}")
