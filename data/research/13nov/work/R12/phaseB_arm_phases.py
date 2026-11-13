"""PHASE B (run after 15:30 only; one process; about 16 days x 20 s). Walk-forward calibration of the voice's
"how close is my trigger" base rates. Learn P(fire within 5/10/15 min | phase, progress bucket) on 19 Oct - 4 Nov,
check it on 5 - 11 Nov (12 Nov has no ds_v2 part): per test day, Brier score of the table vs a constant base rate.
Also: share of window seconds in each phase per day, and how many Conductor triggers the observer reproduces.
    py -3.13 phaseB_arm_phases.py"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R12")
import json
import numpy as np
from r12_observer import observe

DAYS = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
        "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11"]
SIMR = ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")
sim = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
simr = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"))["days"]
BK = ((0, .5), (.5, .8), (.8, 1.01))
rows, summ = [], []
for day in DAYS:
    o = observe(day)
    fi = np.array([f[0] for f in o["fires"]], float)
    src = simr if day in SIMR else sim
    trig = [t["trigger_t"] - o["t_open"] for t in (src.get(day) or {}).get("trades", [])]
    match = sum(1 for t in trig if len(fi) and np.min(np.abs(fi - t)) <= 30)
    ph, pr = o["ph"], o["prog"]
    act = ph >= 1
    summ.append(dict(day=day, expiry=bool(o["dte0"]), fires=len(fi), cond_trig=len(trig), matched=match,
                     **{f"share_{n}": round(float(np.mean(ph[act] == k)), 3) if act.any() else None
                        for k, n in ((1, "idle"), (2, "armed"), (3, "zone"), (4, "impulse"))}))
    for i in np.nonzero((ph >= 1) & (ph <= 3))[0][::5]:          # every 5th second (outcomes overlap anyway)
        nx = fi[fi > i]
        w = (nx[0] - i) if len(nx) else 1e9
        x = pr[i] if np.isfinite(pr[i]) else 0.0
        b = next((j for j, (lo, hi) in enumerate(BK) if lo <= x < hi), 0)
        rows.append((DAYS.index(day), int(o["dte0"]), int(ph[i]), b, w))
    print(summ[-1], flush=True)
R = np.array(rows, float)
early = R[:, 0] <= DAYS.index("2026-11-04")
late = ~early
out = {"summary": summ, "table": {}, "test": []}
for H in (300, 600, 900):
    for e in (0, 1):
        for k in (1, 2, 3):
            for b in range(3):
                m = (R[:, 1] == e) & (R[:, 2] == k) & (R[:, 3] == b)
                tr, te = R[m & early], R[m & late]
                if len(tr) < 30:
                    continue
                key = f"{'exp' if e else 'norm'}|ph{k}|b{b}|{H}s"
                out["table"][key] = dict(p_train=round(float(np.mean(tr[:, 4] <= H)), 3), n_train=int(len(tr)),
                                         p_test=round(float(np.mean(te[:, 4] <= H)), 3) if len(te) else None, n_test=int(len(te)))
    base = float(np.mean(R[early, 4] <= H))
    for di in sorted(set(R[late, 0].astype(int))):
        sel = R[R[:, 0] == di]
        y = (sel[:, 4] <= H).astype(float)
        ptab = np.array([out["table"].get(f"{'exp' if r[1] else 'norm'}|ph{int(r[2])}|b{int(r[3])}|{H}s", {}).get("p_train", np.nan) for r in sel])
        okm = np.isfinite(ptab)
        out["test"].append(dict(day=DAYS[di], H=H, n=int(okm.sum()), brier_table=round(float(np.mean((ptab[okm] - y[okm]) ** 2)), 4),
                                brier_const=round(float(np.mean((base - y[okm]) ** 2)), 4)))
for k, v in out["table"].items():
    print(k, v)
for t in out["test"]:
    print(t)
json.dump(out, open(r"D:\ApexOptions\data\research\13nov\work\R12\phaseB_arm_phases.json", "w"), indent=1, default=str)
