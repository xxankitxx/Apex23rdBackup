import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R11 Phase B (run after the 15:30 close; same rules: one script, under 3 minutes after the close, under 1.5 GB).
# What would the proposed "What I would do now" card have said on each recorded day, and how honest is it?
# Rebuilds the c20 NORM pullback state machine (apex/engine/council/c20_08.py _pullback with the c20_8x "pbg" geometry:
# arm on a 20-min breakout with >= 40 pts of 20-min velocity, enter after a 50-75 % retrace and a 5-pt resumption,
# disarm beyond 75 % or after 900 s) on the futures mid of data/forecast_lab/collect/<day>.joblib (S: t, F per second).
# Approximation: the engine runs it on the parity forward, not the futures mid; vetoes of c20_9y (IV, spread) and the
# Conductor's priority are not modelled. Output per day: seconds the card shows WAIT / GET READY, arms, fires,
# fire rate after arming, arm-to-fire seconds, and for each fire the forward 15-min futures move in its direction.
# Then joins fires to the Conductor's p44 account trades (same day, side, within 120 s) for the card's quoted record.
import glob, os, json
import numpy as np, joblib

OUT = r"D:\ApexOptions\data\research\13nov\work\R11"
P = dict(W=1200, L=1200, vmin=40.0, pb=0.5, dmax=0.75, amax=900, rs=5.0, t0=556.0, t1=900.0)   # minutes since 00:00 / 60 -> see hm


def run_day(t, F):
    n = len(F)
    hm = ((t.astype(np.int64) + 19800) % 86400) / 60.0            # minutes of the day IST
    W = P["W"]
    arm, state = None, np.zeros(n, np.int8)                         # 0 wait, 1 armed (GET READY)
    arms, fires = [], []
    from collections import deque
    qmax, qmin = deque(), deque()
    for i in range(n):
        x = F[i - 1] if i else F[0]
        while qmax and qmax[-1][1] <= x: qmax.pop()
        qmax.append((i - 1, x))
        while qmin and qmin[-1][1] >= x: qmin.pop()
        qmin.append((i - 1, x))
        while qmax and qmax[0][0] < i - W: qmax.popleft()
        while qmin and qmin[0][0] < i - W: qmin.popleft()
        if i < W + 2 or hm[i] < P["t0"] or hm[i] >= P["t1"]:
            continue
        fs, hi, lo = F[i], qmax[0][1], qmin[0][1]
        v = fs - F[i - P["L"]]
        side = "CE" if (fs > hi and v >= P["vmin"]) else "PE" if (fs < lo and -v >= P["vmin"]) else None
        if side is not None:
            if arm is None or arm[0] != side:
                arm = [side, F[i - P["L"]], fs, fs, i]
                arms.append(dict(i=i, side=side, t=float(t[i])))
            else:
                arm[2] = max(arm[2], fs) if side == "CE" else min(arm[2], fs)
                arm[3] = arm[2]
            state[i] = 1
            continue
        if arm is None:
            continue
        if i - arm[4] > min(W, P["amax"]):
            arm = None; continue
        up = arm[0] == "CE"
        arm[2] = max(arm[2], fs) if up else min(arm[2], fs)
        arm[3] = min(arm[3], fs) if up else max(arm[3], fs)
        imp = abs(arm[2] - arm[1]); ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
        state[i] = 1
        if imp <= 0 or ret < P["pb"] * imp:
            continue
        if ret > P["dmax"] * imp:
            arm = None; continue
        res = (fs - arm[3]) if up else (arm[3] - fs)
        if res >= P["rs"]:
            j = np.searchsorted(t, t[i] + 900)
            fwd = (F[min(j, n - 1)] - fs) * (1 if up else -1)
            fires.append(dict(i=i, side=arm[0], t=float(t[i]), arm_t=float(t[arm[4]]), wait_s=float(t[i] - t[arm[4]]), fwd15=float(fwd)))
            arm = None
    return state, arms, fires


def conductor_trades():
    rows = []
    for f in (r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print("not read", f, e); continue
        if isinstance(d, dict) and isinstance(d.get("days"), dict):     # 13 Nov fix: trades sit under days[day]
            tr = [x for dd in d["days"].values() for x in (dd.get("trades") or [])]
        else:
            tr = d.get("trades") if isinstance(d, dict) else d
        for x in tr or []:
            rows.append(x)
    return rows


res = {}
for f in sorted(glob.glob(r"D:\ApexOptions\data\forecast_lab\collect\*.joblib")):
    d = joblib.load(f)
    S = d["S"]; t, F = S[:, 0], S[:, 1]
    st, arms, fires = run_day(t, F)
    live = ((((t.astype(np.int64) + 19800) % 86400) / 60.0) >= P["t0"]) & ((((t.astype(np.int64) + 19800) % 86400) / 60.0) < P["t1"])
    res[d["day"]] = dict(seconds=int(live.sum()), ready_share=float(st[live].mean()) if live.any() else None,
                         arms=len(arms), fires=len(fires), fire_rate=(len(fires) / len(arms)) if arms else None,
                         wait_s_median=float(np.median([x["wait_s"] for x in fires])) if fires else None,
                         fwd15_right=float(np.mean([x["fwd15"] > 0 for x in fires])) if fires else None, fire_list=fires)
    print(d["day"], {k: v for k, v in res[d["day"]].items() if k != "fire_list"}, flush=True)

ct = conductor_trades()
print("conductor trades read:", len(ct), "keys:", sorted(ct[0].keys())[:20] if ct else None)
json.dump(res, open(os.path.join(OUT, "phaseB_armed_card.json"), "w"), indent=1)
# Report in the R11 file: per day the share of the window the card would say GET READY, arms, fires, fire rate,
# and the 15-min move after a fire (early 19 Oct - 4 Nov vs late 5 - 11 Nov). These are the numbers the card quotes
# as "of N setups I armed, X fired; of fires, Y % went my way over 15 minutes".
