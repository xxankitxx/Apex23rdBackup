"""Does the commentary VERDICT carry information? For every Conductor trade on the given ds_v2 parts:
   (a) obey the first EXIT-SOON (exit at the bid one second later) vs the actual exit;
   (b) forward premium move (bid) over the next 300 s (capped at the trade's own exit) after each verdict change, by level.
Usage: py -3.13 s2_verdict_obey.py 2026-11-05 2026-11-06 2026-11-09   (each arg = a ds_v2 part name)"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, csv, os, collections
import numpy as np
B = r"D:\ApexOptions\data\replay\batch"; DS = r"D:\ApexOptions\data\research\ds_v2"
RUN = {"2026-10-19":"g1","2026-10-21":"g1","2026-10-22":"g2","2026-10-23":"g2","2026-10-26":"g3","2026-10-27":"g3",
       "2026-10-28":"r1","2026-10-29":"g4","2026-10-30":"r2","2026-11-02":"r3","2026-11-03":"r4","2026-11-04":"g6",
       "2026-11-05":"g7","2026-11-06":"g7","2026-11-09":"g8","2026-11-11":"g8","2026-11-12":"g9"}
res, fwd = [], collections.defaultdict(list)
for part in sys.argv[1:]:
    day = part[:10]
    man = json.load(open(os.path.join(DS, part + ".manifest.json")))
    if not man.get("rows"): continue
    z = np.load(os.path.join(DS, part + ".npz"))
    T, OPT, K = z["t"], z["opt"], list(z["strikes"]); OPT2, K2 = z["opt2"], list(z["strikes2"])
    pdir = os.path.join(B, "p44_" + RUN[day], "paper")
    rows = [json.loads(l) for l in open(os.path.join(pdir, f"commentary_{day}.jsonl"), encoding="utf-8")]
    trades = list(csv.DictReader(open(os.path.join(pdir, f"trades_{day}.csv"), encoding="utf-8")))
    by = collections.defaultdict(list)
    for r in rows: by[r.get("trade_id")].append(r)
    def bid_at(t, k, rr, exp):
        i = int(np.searchsorted(T, t))
        if i >= len(T) or abs(T[i] - t) > 2: return None
        if exp == man["expiry"] and k in K: a, kk = OPT, K.index(k)
        elif exp == man.get("expiry2") and k in K2: a, kk = OPT2, K2.index(k)
        else: return None
        v = float(a[i, kk, 0 if rr == "CE" else 1, 0])
        return v if np.isfinite(v) and v > 0 else None
    for t in trades:
        cand = [k for k, v in by.items() if k and v and sorted(v, key=lambda x: x["t"])[0].get("time") == t["time_in"]]
        if not cand: continue
        rs = sorted(by[cand[0]], key=lambda x: x["t"]); t0 = rs[0]["t"]; t1 = t0 + float(t["hold_s"])
        if not (T[0] <= t0 <= T[-1]): continue
        k, rr, exp, e = int(float(t["strike"])), t["rr"], t["expiry"], float(t["entry"])
        ver = [x for x in rs if x.get("kind") == "verdict" and x["t"] <= t1]
        fe = next((x for x in ver if x["level"] == "EXIT-SOON"), None)
        fe2 = next((x for x in ver if x["level"] == "EXIT-SOON" and x["t"] - t0 >= 120), None)
        def obey(x):
            if x is None: return float(t["ret_pct"])
            b = bid_at(x["t"] + 1, k, rr, exp)
            return None if b is None else 100 * (b / e - 1)
        res.append(dict(day=day, time_in=t["time_in"], actual=float(t["ret_pct"]), obey1=obey(fe), obey120=obey(fe2),
                        first_exit_s=None if fe is None else round(fe["t"] - t0), reason1=None if fe is None else fe["reason"][:60]))
        for x in ver:
            b0 = bid_at(x["t"], k, rr, exp); b1 = bid_at(min(x["t"] + 300, t1), k, rr, exp)
            if b0 and b1: fwd[x["level"]].append(100 * (b1 / b0 - 1))
for r in res: print(r)
def comp(xs):
    r = 1.0
    for x in xs: r *= 1 + x / 100
    return 100 * (r - 1)
ok = [r for r in res if r["obey1"] is not None and r["obey120"] is not None]
for key in ("actual", "obey1", "obey120"):
    v = [r[key] for r in ok]
    print(f"{key:8s} n={len(v)} won {sum(1 for x in v if x > 0)}/{len(v)} mean {np.mean(v):+.2f}% compounded {comp(v):+.1f}%")
for lv, v in fwd.items():
    print(f"after {lv:9s}: n={len(v)} next-300s bid change mean {np.mean(v):+.2f}% median {np.median(v):+.2f}% share up {np.mean(np.array(v) > 0):.2f}")
json.dump({"trades": res, "fwd": {k: v for k, v in fwd.items()}}, open(r"D:\ApexOptions\data\research\13nov\work\R12\s2_" + "_".join(a[5:] for a in sys.argv[1:]) + ".json", "w"))
