"""PHASE B (after 15:30). While the Conductor holds, does a FRESH observer trigger tell the voice anything?
Same-side fire during a hold = "the pattern fired again my way"; opposite-side fire = "the pattern now points the
other way". For each Conductor trade (p44 sims), the first observer fire inside (t_in + 5 s, t_out): the held
contract's bid change from the fire second to the actual exit, and the alternative "exit at that fire" return.
Walk-forward: early (19 Oct - 4 Nov) and late (5 - 11 Nov) reported separately, strike rate first, compounded %.
Variants: 2 (same-side keep, opposite-side exit). Untested until run.
    py -3.13 phaseB_retrigger_hold.py"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R12")
import json
import numpy as np
from r12_observer import observe, parts_of

DAYS = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
        "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11"]
SIMR = ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")
sim = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
simr = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"))["days"]
res = []
for day in DAYS:
    o = observe(day)
    bids = []
    for path, man in parts_of(day):
        z = np.load(path)
        bids.append((z["t"], z["opt"][:, :, :, 0], list(z["strikes"]), z["opt2"][:, :, :, 0], list(z["strikes2"]), man))

    def bid(t, k, rr, exp):
        for T, O, K, O2, K2, man in bids:
            i = int(np.searchsorted(T, t))
            if i < len(T) and abs(T[i] - t) <= 2:
                if exp == man["expiry"] and k in K:
                    v = O[i, K.index(k), 0 if rr == "CE" else 1]
                elif exp == man.get("expiry2") and k in K2:
                    v = O2[i, K2.index(k), 0 if rr == "CE" else 1]
                else:
                    return None
                return float(v) if np.isfinite(v) and v > 0 else None
        return None

    src = simr if day in SIMR else sim
    for t in (src.get(day) or {}).get("trades", []):
        exp = t["key"].split("|")[2]
        for (i, side, _st) in o["fires"]:
            ts = o["t_open"] + i
            if not (t["t_in"] + 5 < ts < t["t_out"]):
                continue
            b0 = bid(ts + 1, int(t["strike"]), t["rr"], exp)
            if b0 is None:
                continue
            res.append(dict(day=day, time_in=t["time_in"], same=side == t["rr"], after_fire_to_exit=100 * (t["exit"] / b0 - 1),
                            actual=t["ret_pct"], exit_at_fire=100 * (b0 / t["entry"] - 1)))
            break
    print(day, "done", flush=True)


def comp(xs):
    r = 1.0
    for x in xs:
        r *= 1 + x / 100
    return 100 * (r - 1)


for lab, lo, hi in (("early", "2026-10-19", "2026-11-04"), ("late", "2026-11-05", "2026-11-12")):
    for same in (True, False):
        s = [r for r in res if lo <= r["day"] <= hi and r["same"] == same]
        if not s:
            continue
        print(f"{lab} {'same-side' if same else 'opposite'} n={len(s)}: bid change fire->exit mean "
              f"{np.mean([r['after_fire_to_exit'] for r in s]):+.2f}% | actual won {sum(r['actual'] > 0 for r in s)}/{len(s)} "
              f"comp {comp([r['actual'] for r in s]):+.1f}% | exit-at-fire won {sum(r['exit_at_fire'] > 0 for r in s)}/{len(s)} "
              f"comp {comp([r['exit_at_fire'] for r in s]):+.1f}%")
json.dump(res, open(r"D:\ApexOptions\data\research\13nov\work\R12\phaseB_retrigger_hold.json", "w"), indent=1)
