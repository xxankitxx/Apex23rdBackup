"""Shared helper for R12's Phase B scripts: the c20 trigger as a never-holding observer on ds_v2 per-second data.
Normal days: c20_08 NORM pullback machine + c20_8x pbg (impulse 40 pts / 20 min, pullback 50-75 %, 5-pt resumption,
arm life 900 s) and c20_9s's stale-impulse flag (arm older than 660 s). Expiry days: c20_08 EXP breakout (smoothed
forward beyond its 10-min high/low with >= 20 pts in 150 s). Parity forward = K + mid(CE) - mid(PE) at the strike
nearest the futures mid; 5-s EMA. Validated on 4-6 Nov: 10 of 10 Conductor triggers within 3 s of an observer fire.
Phases: 1 IDLE, 2 ARMED (pullback < 50 %), 3 ZONE (pullback 50-75 %, waiting for resumption), 4 IMPULSE printing, 5 FIRE."""
import json, os, glob
from collections import deque
from datetime import datetime, timezone, timedelta
import numpy as np
IST = timezone(timedelta(hours=5, minutes=30))
DS = r"D:\ApexOptions\data\research\ds_v2"
NORM = dict(tau=5.0, W=1200, L=1200, vmin=40.0, pb=0.5, rs=5.0, PB_DMAX=0.75, PB_AMAX=900, AGE=660, t1=900)
EXP = dict(tau=5.0, W=600, L=150, vmin=20.0, t1=880)
N = 6 * 3600 + 15 * 60 + 1


def parts_of(day):
    out = []
    for m in sorted(glob.glob(os.path.join(DS, day + "*.manifest.json"))):
        j = json.load(open(m))
        if j.get("rows"):
            out.append((m.replace(".manifest.json", ".npz"), j))
    return out


def forward_grid(day):
    y, m, d = map(int, day.split("-"))
    t_open = datetime(y, m, d, 9, 15, tzinfo=IST).timestamp()
    g = np.full(N, np.nan)
    exp = None
    for path, man in parts_of(day):
        exp = man.get("expiry")
        z = np.load(path)
        T, OPT, K, FUT = z["t"], z["opt"], np.array(z["strikes"], float), z["fut"]
        fm = 0.5 * (FUT[:, 0] + FUT[:, 1])
        mid = 0.5 * (OPT[:, :len(K), :, 0] + OPT[:, :len(K), :, 1])
        ok = np.isfinite(fm)
        j = np.argmin(np.abs(K[None, :] - np.where(ok, fm, 0)[:, None]), axis=1)
        r = np.arange(len(T))
        F = K[j] + mid[r, j, 0] - mid[r, j, 1]
        F[~ok] = np.nan
        idx = (T - t_open).astype(int)
        sel = (idx >= 0) & (idx < N) & np.isfinite(F)
        g[idx[sel]] = F[sel]
        del z, OPT, mid
    for i in range(1, N):
        if not np.isfinite(g[i]):
            g[i] = g[i - 1]
    return t_open, g, (exp == day)


def observe(day):
    t_open, g, dte0 = forward_grid(day)
    P = EXP if dte0 else NORM
    fs = np.full(N, np.nan)
    a = 1 / P["tau"]
    qmax, qmin = deque(), deque()
    arm = None
    ph = np.zeros(N, np.int8)
    prog = np.full(N, np.nan)
    fires = []
    for i in range(N):
        f = g[i]
        if not np.isfinite(f):
            continue
        prev = fs[i - 1] if i else np.nan
        fs[i] = f if not np.isfinite(prev) else prev + a * (f - prev)
        if np.isfinite(prev):
            while qmax and qmax[-1][1] <= prev:
                qmax.pop()
            qmax.append((i - 1, prev))
            while qmin and qmin[-1][1] >= prev:
                qmin.pop()
            qmin.append((i - 1, prev))
        while qmax and qmax[0][0] < i - P["W"]:
            qmax.popleft()
        while qmin and qmin[0][0] < i - P["W"]:
            qmin.popleft()
        hm = 555 + i / 60
        if hm < 556 or hm >= P["t1"] or i < P["W"] + 2 or not np.isfinite(fs[i - P["W"]]) or not qmax:
            continue
        hi, lo = qmax[0][1], qmin[0][1]
        v = fs[i] - fs[i - P["L"]]
        side = "CE" if (fs[i] > hi and v >= P["vmin"]) else "PE" if (fs[i] < lo and -v >= P["vmin"]) else None
        if dte0:      # expiry: breakout entry; progress = the weaker of the two legs (velocity, range edge)
            if side:
                fires.append((i, side, False))
                ph[i] = 5
                continue
            pu = min(max(v, 0) / P["vmin"], 1.0) * (1.0 if fs[i] > hi else max(0.0, 1 - (hi - fs[i]) / P["vmin"]))
            pd = min(max(-v, 0) / P["vmin"], 1.0) * (1.0 if fs[i] < lo else max(0.0, 1 - (fs[i] - lo) / P["vmin"]))
            ph[i] = 1
            prog[i] = max(pu, pd)
            continue
        if side is not None:
            if arm is None or arm[0] != side:
                arm = [side, fs[i - P["L"]], fs[i], fs[i], i]
            else:
                arm[2] = max(arm[2], fs[i]) if side == "CE" else min(arm[2], fs[i])
                arm[3] = arm[2]
            ph[i] = 4
            prog[i] = 1.0
            continue
        if arm is None:
            ph[i] = 1
            prog[i] = min(abs(v) / P["vmin"], 1.0)
            continue
        if i - arm[4] > min(P["W"], P["PB_AMAX"]):
            arm = None
            ph[i] = 1
            continue
        sd, base = arm[0], arm[1]
        up = sd == "CE"
        arm[2] = max(arm[2], fs[i]) if up else min(arm[2], fs[i])
        arm[3] = min(arm[3], fs[i]) if up else max(arm[3], fs[i])
        imp = abs(arm[2] - base)
        ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
        if imp <= 0 or ret < P["pb"] * imp:
            ph[i] = 2
            prog[i] = ret / imp / P["pb"] if imp > 0 else 0
            continue
        if ret > P["PB_DMAX"] * imp:
            arm = None
            ph[i] = 1
            continue
        res = (fs[i] - arm[3]) if up else (arm[3] - fs[i])
        if res >= P["rs"]:
            fires.append((i, sd, i - arm[4] > P["AGE"]))
            arm = None
            ph[i] = 5
            continue
        ph[i] = 3
        prog[i] = max(res, 0) / P["rs"]
    return dict(day=day, t_open=t_open, dte0=dte0, fs=fs, ph=ph, prog=prog, fires=fires)
