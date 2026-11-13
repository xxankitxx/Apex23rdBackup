import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R01 Phase B (after 15:30 only; one process, every normal day in ds_v2 one at a time):

 1. ARM CENSUS: every c20 normal-day arm (replica, phaseB_c20_complements.run_day logic) with how it ended and its
    deepest retrace; for each arm that AGED OUT (no 50 % pullback in 15 min) the smoothed futures move over the next
    900 s and 1800 s in the arm's direction (does an aged-out arm mean a trend the account is missing?).
 2. AGE-OUT ENTRY ("AGE"): buy the arm's side at the age-out second when its deepest retrace was < AGE_RET of the
    impulse, c20_9x normal-day exits (Kit). One position.
 3. PULLBACK-DEPTH SWEEP: the replica with pb in {0.25, 0.33, 0.40, 0.50} x arm age {600, 900, 1200} s (12 variants,
    all counted). Discovery = days <= 2026-11-04, test = days >= 2026-11-05. Report per day: trades, won, compounded %.
    Pick on discovery by (strike rate, then sum of log returns), report the pick's test days next to pb 0.50/900
    (the live c20 setting).
Writes work/R01/phaseB_pb_sweep.json.   Run:  py -3.13 phaseB_pb_sweep.py
"""
import glob, json, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phaseB_c20_complements as B

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phaseB_pb_sweep.json")
AGE_RET = 0.35


def replica(D, fs, hi, lo, pb, amax, census=False):
    P = B.P
    N = len(fs)
    t0, t1, flat = 60, 345 * 60, 365 * 60
    k20, kage = B.Kit(D, fs), B.Kit(D, fs)
    arm = None
    arms = []
    for i in range(N):
        k20.step(i, flat); kage.step(i, flat)
        f = fs[i]
        if not np.isfinite(f) or i < P["W"] + 2 or not np.isfinite(fs[i - P["L"]]):
            continue
        v = f - fs[i - P["L"]]
        side = "CE" if (np.isfinite(hi[i]) and f > hi[i] and v >= P["vmin"]) else \
               "PE" if (np.isfinite(lo[i]) and f < lo[i] and -v >= P["vmin"]) else None
        inwin = t0 <= i < t1
        if not (inwin and k20.pos is None and i - k20.last_exit >= P["cool"]):
            continue
        if side is not None:
            if arm is None or arm[0] != side:
                if arm is not None:
                    arms.append(dict(i=arm[4], end_i=i, side=arm[0], maxret=arm[5], end="other"))
                arm = [side, fs[i - P["L"]], f, f, i, 0.0]
            else:
                arm[2] = max(arm[2], f) if side == "CE" else min(arm[2], f)
                arm[3] = arm[2]
            continue
        if arm is None:
            continue
        if i - arm[4] > amax:
            a = dict(i=arm[4], end_i=i, side=arm[0], maxret=arm[5], end="aged")
            if census:
                sg = 1 if arm[0] == "CE" else -1
                for h in (900, 1800):
                    a[f"cont{h}"] = float(sg * (fs[min(i + h, N - 1)] - f))
                if arm[5] < AGE_RET:
                    kage.buy(i, arm[0], "age-out")
            arms.append(a)
            arm = None
            continue
        up = arm[0] == "CE"
        arm[2] = max(arm[2], f) if up else min(arm[2], f)
        arm[3] = min(arm[3], f) if up else max(arm[3], f)
        imp = abs(arm[2] - arm[1])
        ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
        arm[5] = max(arm[5], ret / imp if imp > 0 else 0.0)
        if imp > 0 and ret >= pb * imp:
            if ret > P["dmax"] * imp:
                arms.append(dict(i=arm[4], end_i=i, side=arm[0], maxret=arm[5], end="reversal"))
                arm = None
            elif ((f - arm[3]) if up else (arm[3] - f)) >= P["rs"]:
                arms.append(dict(i=arm[4], end_i=i, side=arm[0], maxret=arm[5], end="fired"))
                k20.buy(i, arm[0], f"pb{pb}")
                arm = None
    return k20.trades, kage.trades, arms


def summ(tr):
    r = [x["ret"] for x in tr]
    return dict(n=len(r), won=sum(1 for x in r if x > 0), comp=round(100 * (np.prod([1 + x / 100 for x in r]) - 1), 2) if r else 0.0,
                sumlog=round(float(np.sum(np.log1p(np.array(r) / 100))), 4) if r else 0.0)


def main():
    days = sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(B.DS, "*.npz"))})
    grid = [(pb, am) for pb in (0.25, 0.33, 0.40, 0.50) for am in (600, 900, 1200)]
    res = {"days": {}, "grid": [list(g) for g in grid]}
    t0 = time.time()
    for day in days:
        D = B.load_day(day)
        if D is None or D["expiry"] == day:
            continue
        fs = B.ema(D["fut"], B.P["tau"])
        hi, lo = B.roll_max_min(fs, B.P["W"])
        r = {"census": None, "age": None, "sweep": {}}
        for pb, am in grid:
            tr, tage, arms = replica(D, fs, hi, lo, pb, am, census=(pb == 0.5 and am == 900))
            r["sweep"][f"{pb}/{am}"] = summ(tr)
            if pb == 0.5 and am == 900:
                r["census"] = arms
                r["age"] = dict(summ(tage), trades=tage)
        res["days"][day] = r
        print(day, "done", round(time.time() - t0), "s", r["sweep"]["0.5/900"], "AGE", {k: r["age"][k] for k in ("n", "won", "comp")}, flush=True)
        del D
    # walk-forward pick
    DISC = [d for d in res["days"] if d <= "2026-11-04"]; TEST = [d for d in res["days"] if d >= "2026-11-05"]
    def agg(key, ds):
        s = [res["days"][d]["sweep"][key] for d in ds]
        n = sum(x["n"] for x in s); w = sum(x["won"] for x in s)
        return dict(sr=round(w / n, 3) if n else None, n=n, sumlog=round(sum(x["sumlog"] for x in s), 4),
                    losing_days=sum(1 for x in s if x["sumlog"] < 0), per_day=[x["comp"] for x in s])
    table = {f"{pb}/{am}": dict(D=agg(f"{pb}/{am}", DISC), T=agg(f"{pb}/{am}", TEST)) for pb, am in grid}
    pick = max(table, key=lambda k: ((table[k]["D"]["sr"] or 0), table[k]["D"]["sumlog"]))
    res["table"], res["pick"] = table, pick
    print("\nvariant  D(sr, n, sumlog, losing days)  T(sr, n, sumlog, losing days)")
    for k, v in table.items():
        print(f"{k:9s} {v['D']['sr']} {v['D']['n']} {v['D']['sumlog']} {v['D']['losing_days']} | {v['T']['sr']} {v['T']['n']} {v['T']['sumlog']} {v['T']['losing_days']} {v['T']['per_day']}")
    print("pick on discovery:", pick, "(live c20 = 0.5/900); 12 variants tried")
    aged = [a for d in res["days"].values() for a in (d["census"] or []) if a["end"] == "aged"]
    for h in (900, 1800):
        c = np.array([a[f"cont{h}"] for a in aged if f"cont{h}" in a])
        shallow = np.array([a[f"cont{h}"] for a in aged if a["maxret"] < AGE_RET])
        print(f"aged-out arms: {len(c)}; futures move {h}s after, in the arm's direction: median {np.median(c):+.1f}, "
              f"share > 0 {np.mean(c > 0):.2f}; shallow (< {AGE_RET}) n {len(shallow)} median {np.median(shallow) if len(shallow) else float('nan'):+.1f}")
    ag = [x for d in res["days"].values() for x in d["age"]["trades"]]
    print("AGE entries:", summ(ag))
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
