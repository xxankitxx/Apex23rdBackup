"""The c20 normal-day trigger as a never-holding observer ("the twin that only watches"), on ds_v2 per-second data.
Phases each second: IDLE (no arm), ARMED (impulse done, pullback < 50 %), ZONE (pullback 50-75 %, waiting for the 5-pt
resumption), FIRE. Measures how often each phase leads to a fire within 5 / 10 / 15 min, so the voice can say
"armed, pullback 38 % of the 50 % it needs" with an honest base rate. Parity forward = K + mid(CE) - mid(PE) at the
strike nearest the futures mid, then the core's 5-s EMA (c20_08 tau=5). Parameters: c20_08 NORM + c20_8x pbg.
Usage: py -3.13 s4_arm_phases.py 2026-11-04 2026-11-05 2026-11-06"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, os, collections
from collections import deque
import numpy as np
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
DS = r"D:\ApexOptions\data\research\ds_v2"
P = dict(tau=5.0, W=1200, L=1200, vmin=40.0, pb=0.5, rs=5.0, PB_DMAX=0.75, PB_AMAX=900, AGE=660)
sim = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
allph = []
for part in sys.argv[1:]:
    day = part[:10]
    z = np.load(os.path.join(DS, part + ".npz"))
    T, OPT, K, FUT = z["t"], z["opt"], np.array(z["strikes"], float), z["fut"]
    n = len(T)
    fm = 0.5 * (FUT[:, 0] + FUT[:, 1])
    mid = 0.5 * (OPT[:, :len(K), :, 0] + OPT[:, :len(K), :, 1])
    F = np.full(n, np.nan)
    for i in range(n):
        if not np.isfinite(fm[i]): continue
        j = int(np.argmin(np.abs(K - fm[i])))
        c, p = mid[i, j, 0], mid[i, j, 1]
        if np.isfinite(c) and np.isfinite(p): F[i] = K[j] + c - p
    # per-second grid from 09:15
    y, m, d = map(int, day.split("-"))
    t_open = datetime(y, m, d, 9, 15, tzinfo=IST).timestamp()
    N = 6 * 3600 + 15 * 60 + 1
    g = np.full(N, np.nan); idx = (T - t_open).astype(int); ok = (idx >= 0) & (idx < N)
    g[idx[ok]] = F[ok]
    for i in range(1, N):                                  # carry forward over gaps (the engine's LiveDay does)
        if not np.isfinite(g[i]): g[i] = g[i - 1]
    fs = np.full(N, np.nan); a = 1 / P["tau"]
    qmax, qmin = deque(), deque(); arm = None
    ph = np.zeros(N, np.int8); prog = np.full(N, np.nan); fires = []
    for i in range(N):
        f = g[i]
        if not np.isfinite(f): continue
        prev = fs[i - 1] if i else np.nan
        fs[i] = f if not np.isfinite(prev) else prev + a * (f - prev)
        if np.isfinite(prev):
            while qmax and qmax[-1][1] <= prev: qmax.pop()
            qmax.append((i - 1, prev))
            while qmin and qmin[-1][1] >= prev: qmin.pop()
            qmin.append((i - 1, prev))
        while qmax and qmax[0][0] < i - P["W"]: qmax.popleft()
        while qmin and qmin[0][0] < i - P["W"]: qmin.popleft()
        hm = 555 + i / 60
        if hm < 556 or hm >= 900 or i < P["W"] + 2 or not np.isfinite(fs[i - P["W"]]) or not qmax: continue
        hi, lo = qmax[0][1], qmin[0][1]; v = fs[i] - fs[i - P["L"]]
        side = "CE" if (fs[i] > hi and v >= P["vmin"]) else "PE" if (fs[i] < lo and -v >= P["vmin"]) else None
        if side is not None:
            if arm is None or arm[0] != side: arm = [side, fs[i - P["L"]], fs[i], fs[i], i]
            else: arm[2] = max(arm[2], fs[i]) if side == "CE" else min(arm[2], fs[i]); arm[3] = arm[2]
            ph[i] = 4; prog[i] = 1.0; continue                # 4 = impulse printing (breaking out now)
        if arm is None:
            ph[i] = 1; prog[i] = min(abs(v) / P["vmin"], 1.0); continue    # IDLE: progress = 20-min move / 40
        if i - arm[4] > min(P["W"], P["PB_AMAX"]): arm = None; ph[i] = 1; continue
        sd, base = arm[0], arm[1]; up = sd == "CE"
        arm[2] = max(arm[2], fs[i]) if up else min(arm[2], fs[i]); arm[3] = min(arm[3], fs[i]) if up else max(arm[3], fs[i])
        imp = abs(arm[2] - base); ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
        if imp <= 0 or ret < P["pb"] * imp:
            ph[i] = 2; prog[i] = ret / imp / P["pb"] if imp > 0 else 0; continue      # ARMED
        if ret > P["PB_DMAX"] * imp: arm = None; ph[i] = 1; continue
        res = (fs[i] - arm[3]) if up else (arm[3] - fs[i])
        if res >= P["rs"]:
            fires.append((i, sd, i - arm[4] > P["AGE"])); arm = None; ph[i] = 5; continue
        ph[i] = 3; prog[i] = max(res, 0) / P["rs"]                                  # ZONE
    fi = np.array([f[0] for f in fires]) if fires else np.zeros(0, int)
    trig = [t["trigger_t"] - t_open for t in (sim.get(day) or {}).get("trades", [])]
    print(day, "observer fires:", [(datetime.fromtimestamp(t_open + f[0], IST).strftime("%H:%M:%S"), f[1], "stale" if f[2] else "") for f in fires])
    print("   Conductor triggers:", [datetime.fromtimestamp(t_open + t, IST).strftime("%H:%M:%S") for t in trig])
    match = sum(1 for t in trig if len(fi) and np.min(np.abs(fi - t)) <= 30)
    print(f"   Conductor triggers within 30 s of an observer fire: {match}/{len(trig)}")
    for i in range(N):
        if ph[i] in (1, 2, 3):
            nxt = fi[fi > i]; w = (nxt[0] - i) if len(nxt) else 1e9
            allph.append((day, int(ph[i]), float(prog[i]) if np.isfinite(prog[i]) else -1, w))
    ent = (ph >= 1)
    print("   share of window seconds: IDLE %.2f ARMED %.2f ZONE %.2f IMPULSE %.2f" % tuple(np.mean(ph[ent] == k) for k in (1, 2, 3, 4)))
A = np.array([(x[1], x[2], x[3]) for x in allph])
names = {1: "IDLE", 2: "ARMED", 3: "ZONE"}
print("\nP(observer fires within N min | phase, progress bucket)  [pooled over the parts given]")
for k in (1, 2, 3):
    s = A[A[:, 0] == k]
    for lo, hi in ((0, .5), (.5, .8), (.8, 1.01)):
        b = s[(s[:, 1] >= lo) & (s[:, 1] < hi)]
        if len(b) < 60: continue
        print(f"  {names[k]:5s} progress {lo:.1f}-{hi:.1f}: n_sec={len(b):6d}  5 min {np.mean(b[:,2]<=300):.2f}  10 min {np.mean(b[:,2]<=600):.2f}  15 min {np.mean(b[:,2]<=900):.2f}")
