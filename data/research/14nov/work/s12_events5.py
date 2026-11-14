"""How Nifty moves after each kind of event: 71 days of 5-minute bars, index points, no option model.
For every event: the move in the event's direction 15 / 30 / 60 minutes later, day-clustered t, both halves."""
import sys; sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab5
NB = lab5.NB
DD = lab5.load()
half = {d["day"]: (0 if k < len(DD) / 2 else 1) for k, d in enumerate(DD)}


def dedupe(ev, gap=6):
    out = []; last = {1: -99, -1: -99}
    for b, s, tag in sorted(ev):
        if b - last[s] >= gap:
            out.append((b, s, tag)); last[s] = b
    return out


def events(D, X):
    c, h, l, o = D["c"], D["h"], D["l"], D["o"]
    E = {}
    def add(name, up, dn, gap=6, lo=3, hi=66):
        ev = [(int(b), 1, name) for b in np.flatnonzero(up) if lo <= b <= hi] + [(int(b), -1, name) for b in np.flatnonzero(dn) if lo <= b <= hi]
        E[name] = dedupe(ev, gap)
    em = X["em20"]
    with np.errstate(invalid="ignore"):
        add("BRK20 40pts", (c > X["hi4"]) & (X["m4"] >= 40), (c < X["lo4"]) & (X["m4"] <= -40))
        add("BRK20 1.0 implied", (c > X["hi4"]) & (X["m4"] >= em), (c < X["lo4"]) & (X["m4"] <= -em))
        add("BRK20 1.5 implied", (c > X["hi4"]) & (X["m4"] >= 1.5 * em), (c < X["lo4"]) & (X["m4"] <= -1.5 * em))
        add("BRK60 1.0 implied", (c > X["hi12"]) & (X["m12"] >= 1.73 * em), (c < X["lo12"]) & (X["m12"] <= -1.73 * em))
        add("BRK120", (c > X["hi24"]) & (X["m24"] >= 2.45 * em), (c < X["lo24"]) & (X["m24"] <= -2.45 * em))
        # day extreme after it stood 30 / 60 minutes
        for age in (6, 12):
            up = np.zeros(NB, bool); dn = np.zeros(NB, bool)
            thi = tlo = 0; hi_ = h[0]; lo_ = l[0]
            for b in range(1, NB):
                if c[b] > hi_ and b - thi >= age: up[b] = True
                if c[b] < lo_ and b - tlo >= age: dn[b] = True
                if h[b] > hi_: hi_ = h[b]; thi = b
                if l[b] < lo_: lo_ = l[b]; tlo = b
            add(f"DAY HIGH/LOW break, stood {age * 5} min", up, dn, lo=6)
        add("FADE 20-min move >= 1.5 implied", X["m4"] <= -1.5 * em, X["m4"] >= 1.5 * em)
        add("FADE 60-min move >= 1.5 implied", X["m12"] <= -1.5 * 1.73 * em, X["m12"] >= 1.5 * 1.73 * em)
        add("HEAVYWEIGHT thrust 5 min (12 pts, breadth 0.6)", (X["hw1"] >= 12) & (X["brd1"] >= 0.6), (X["hw1"] <= -12) & (X["brd1"] <= -0.6))
        add("HEAVYWEIGHT thrust 15 min (25 pts, breadth 0.6)", (X["hw3"] >= 25) & (X["brd3"] >= 0.6), (X["hw3"] <= -25) & (X["brd3"] <= -0.6))
        add("HEAVYWEIGHTS ahead of Nifty 15 min (>= 10 pts)", (X["hw3"] - X["m3"] >= 10), (X["hw3"] - X["m3"] <= -10))
        add("HEAVYWEIGHTS ahead of Nifty 30 min (>= 15 pts)", (X["hw6"] - X["m6"] >= 15), (X["hw6"] - X["m6"] <= -15))
        add("NIFTY ahead of heavyweights 15 min (fade)", (X["hw3"] - X["m3"] >= 10) & (X["m3"] < 0), (X["hw3"] - X["m3"] <= -10) & (X["m3"] > 0))
        add("BREADTH 60 min all one way (0.8)", X["brd12"] >= 0.8, X["brd12"] <= -0.8)
        add("BANKNIFTY ahead of Nifty 15 min (>= 15 pts)", (X["bn3"] - X["m3"] >= 15), (X["bn3"] - X["m3"] <= -15))
        add("BANKNIFTY ahead of Nifty 30 min (>= 25 pts)", (X["bn6"] - X["m6"] >= 25), (X["bn6"] - X["m6"] <= -25))
        add("BOTH SISTERS ahead 15 min (>= 10 pts each)", (X["bn3"] - X["m3"] >= 10) & (X["fn3"] - X["m3"] >= 10), (X["bn3"] - X["m3"] <= -10) & (X["fn3"] - X["m3"] <= -10))
        add("SISTERS + HEAVYWEIGHTS + NIFTY all up 15 min (15 pts)", (X["bn3"] >= 15) & (X["fn3"] >= 15) & (X["hw3"] >= 15) & (X["m3"] >= 15),
            (X["bn3"] <= -15) & (X["fn3"] <= -15) & (X["hw3"] <= -15) & (X["m3"] <= -15))
        vw = c - X["vwap"]; pv = np.r_[np.nan, vw[:-1]]
        add("VWAP cross with the 15-min move", (vw > 0) & (pv <= 0) & (X["m3"] > 5), (vw < 0) & (pv >= 0) & (X["m3"] < -5), lo=6)
        add("VIX falling + up / VIX rising + down (15 min)", (X["vix3"] <= -0.15) & (X["m3"] >= 10), (X["vix3"] >= 0.15) & (X["m3"] <= -10))
        add("SQUEEZE break (20-min range <= 0.6 implied)", ((X["hi4"] - X["lo4"]) <= 0.6 * em) & (c > X["hi4"] + 2), ((X["hi4"] - X["lo4"]) <= 0.6 * em) & (c < X["lo4"] - 2))
        # the pullback pattern on bars: impulse >= 40 in 20 min at a new high, 50-75 % pullback inside 15 min, a close 5 pts off the low
        up = np.zeros(NB, bool); dn = np.zeros(NB, bool); arm = None
        for b in range(4, NB):
            v = c[b] - c[b - 4]
            sd = 1 if (c[b] > X["hi4"][b] and v >= 40) else (-1 if (c[b] < X["lo4"][b] and v <= -40) else 0)
            if sd:
                if arm is None or arm[0] != sd:
                    arm = [sd, c[b - 4], c[b], c[b], b]
                else:
                    arm[2] = max(arm[2], h[b]) if sd > 0 else min(arm[2], l[b]); arm[3] = arm[2]
            elif arm is not None:
                if b - arm[4] > 4:
                    arm = None; continue
                u = arm[0] > 0
                arm[3] = min(arm[3], l[b]) if u else max(arm[3], h[b])
                imp = abs(arm[2] - arm[1]); ret = abs(arm[2] - arm[3])
                if imp > 0 and ret >= 0.5 * imp:
                    if ret > 0.75 * imp:
                        arm = None
                    elif (c[b] - arm[3] if u else arm[3] - c[b]) >= 5:
                        (up if u else dn)[b] = True; arm = None
        add("PULLBACK pattern on bars (the champion's idea)", up, dn)
    # openings
    E["ORB 15 min"] = []; E["ORB 30 min"] = []
    for n, nm in ((3, "ORB 15 min"), (6, "ORB 30 min")):
        hi_, lo_ = h[:n].max(), l[:n].min()
        for b in range(n, 40):
            if c[b] > hi_: E[nm].append((b, 1, nm)); break
            if c[b] < lo_: E[nm].append((b, -1, nm)); break
    if D["prev"]:
        g = o[0] - D["prev"]["c"]
        if abs(g) >= 40:
            E["GAP >= 40 pts: go with it at 09:20"] = [(0, 1 if g > 0 else -1, "gapgo")]
        f30 = c[5] - o[0]
        if abs(f30) >= 20:
            E["FIRST 30 MIN direction, held from 09:45"] = [(5, 1 if f30 > 0 else -1, "f30")]
        f60 = c[11] - o[0]
        if abs(f60) >= 30:
            E["FIRST HOUR direction, held from 10:15"] = [(11, 1 if f60 > 0 else -1, "f60")]
        E["MORNING direction (to 12:30), held from 12:30"] = [(39, 1 if c[39] > o[0] else -1, "am")]
        E["DAY direction at 14:00, last hour"] = [(57, 1 if c[57] > o[0] else -1, "pm")]
    return E


rows = []
for D in DD:
    X = lab5.feats(D)
    c, h, l = D["c"], D["h"], D["l"]
    for name, ev in events(D, X).items():
        for b, s, _ in ev:
            r = dict(fam=name, day=D["day"], b=b, s=s, h=half[D["day"]], dte=D["dte"])
            for k, nm in ((3, "f15"), (6, "f30"), (12, "f60")):
                r[nm] = s * (c[min(b + k, 73)] - c[b]) if b + 1 <= 73 else np.nan
            r["fclose"] = s * (c[73] - c[b])
            # first passage: +30 before -30 within 60 minutes (a tie inside one bar counts as a loss)
            w = None
            for i in range(b + 1, min(b + 13, 74)):
                adv = s * ((l[i] if s > 0 else h[i]) - c[b]); fav = s * ((h[i] if s > 0 else l[i]) - c[b])
                if adv <= -30: w = 0; break
                if fav >= 30: w = 1; break
            r["fp30"] = w
            rows.append(r)
T = pd.DataFrame(rows)
out = []
for fam, g in T.groupby("fam"):
    def tstat(col):
        dm = g.groupby("day")[col].mean().dropna()
        return dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm))) if len(dm) > 5 and dm.std(ddof=1) > 0 else np.nan
    a, b_ = g[g.h == 0], g[g.h == 1]
    fp = g.fp30.dropna()
    out.append(dict(event=fam, n=len(g), days=g.day.nunique(), f15=round(g.f15.mean(), 1), f30=round(g.f30.mean(), 1), f60=round(g.f60.mean(), 1), to_close=round(g.fclose.mean(), 1),
                    hit30=round(100 * (g.f30 > 0).mean()), t30=round(tstat("f30"), 1), t60=round(tstat("f60"), 1),
                    f60_h1=round(a.f60.mean(), 1), f60_h2=round(b_.f60.mean(), 1), up_n=int((g.s > 0).sum()), up_f60=round(g[g.s > 0].f60.mean(), 1), dn_f60=round(g[g.s < 0].f60.mean(), 1),
                    resolved=len(fp), plus30_first=round(100 * fp.mean()) if len(fp) else np.nan))
R = pd.DataFrame(out).sort_values("t60", ascending=False)
pd.set_option("display.width", 330); pd.set_option("display.max_colwidth", 60)
print(f"{len(DD)} days {DD[0]['day']} .. {DD[-1]['day']}; Nifty change over the period {DD[-1]['c'][-1] - DD[0]['o'][0]:+.0f} pts; moves in points in the event's direction")
print(R.to_string(index=False))
T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\events5.parquet")
