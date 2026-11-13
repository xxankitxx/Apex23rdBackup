import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Calibration by conviction bucket and the hysteresis study on the fused stand probabilities (study2.py)."""
import os, glob, json, itertools
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); LAGS = (0, 30)
R = np.load(os.path.join(D, "stand_rows.npz"))
cache = {os.path.basename(f)[:10]: np.load(f) for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz")))}
tdays = sorted({k.split("|")[1] for k in R.files})
EARLY = [d for d in tdays if d <= "2026-11-04"]; LATE = [d for d in tdays if d >= "2026-11-05"]
BK = [0.5, 0.55, 0.6, 0.65, 0.7, 1.01]
out = {}


def y_of(day, lag, h):
    return cache[day]["dF"][LAGS.index(lag), H.index(h)].astype(float)


print("== calibration by conviction bucket (conviction = max(p, 1-p)); hit = sign right, zero moves dropped")
for key in ("lag0_H120", "lag0_H180", "lag0_H300", "lag30_H180", "lag30_H300"):
    lag = int(key.split("_")[0][3:]); Hs = int(key.split("H")[1])
    for win, dl in (("early", EARLY), ("late", LATE)):
        P = np.concatenate([R[f"{key}|{d}"] for d in dl]); Y = np.concatenate([y_of(d, lag, Hs) for d in dl])
        ok = np.isfinite(Y) & (Y != 0)
        P, Y = P[ok], Y[ok]
        c = np.maximum(P, 1 - P); hit = (np.sign(P - 0.5) == np.sign(Y))
        row = []
        for a, b in zip(BK[:-1], BK[1:]):
            m = (c >= a) & (c < b)
            if m.sum():
                row.append(f"[{a:.2f}-{min(b,1):.2f}) n={m.sum():5d} (~{m.sum()*5/Hs:4.0f} indep) said {c[m].mean():.3f} got {hit[m].mean():.3f}")
        print(key, win, "overall hit", round(hit.mean(), 3), "share>=0.60", round((c >= 0.6).mean(), 3))
        for r_ in row:
            print("   ", r_)
        out[f"{key}|{win}"] = dict(hit=float(hit.mean()), rows=row)
    # per test day: hit of conviction >= 0.60 and of all
    pd_ = []
    for d in tdays:
        P = R[f"{key}|{d}"]; Y = y_of(d, lag, Hs); ok = np.isfinite(Y) & (Y != 0)
        c = np.maximum(P, 1 - P); hit = np.sign(P - 0.5) == np.sign(Y)
        m = ok & (c >= 0.6)
        pd_.append((d, round(float(hit[ok].mean()), 3), int(m.sum()), round(float(hit[m].mean()), 3) if m.sum() else None))
    print("  per day (day, hit all, n conv>=0.60, hit conv>=0.60):", pd_)
    out[f"{key}|perday"] = pd_


def stand_series(p, a_hl, th_in, th_out, dwell_rows):
    """EWMA (half-life a_hl rows) then Schmitt trigger with a minimum dwell. +1 BULLISH, -1 BEARISH, 0 NEUTRAL."""
    al = 1 - 0.5 ** (1.0 / a_hl) if a_hl > 0 else 1.0
    s = np.empty(len(p)); st = np.zeros(len(p), int)
    cur, since, e = 0, 0, 0.5
    for i, x in enumerate(p):
        e = e + al * (x - e) if i else x
        s[i] = e
        want = cur
        if cur == 0:
            if e >= th_in: want = 1
            elif e <= 1 - th_in: want = -1
        elif cur == 1 and e < th_out:
            want = -1 if e <= 1 - th_in else 0
        elif cur == -1 and e > 1 - th_out:
            want = 1 if e >= th_in else 0
        if want != cur and (i - since) >= dwell_rows:
            cur, since = want, i
        st[i] = cur
    return s, st


def eval_h(key, dl, lag, Hs, prm):
    hits = n = flips = rows = 0; lean_h = lean_n = 0; per = []
    for d in dl:
        p = R[f"{key}|{d}"].astype(float); Y = y_of(d, lag, Hs)
        s, st = stand_series(p, *prm)
        ok = np.isfinite(Y) & (Y != 0)
        m = ok & (st != 0)
        hh = (np.sign(st[m]) == np.sign(Y[m])).sum()
        hits += hh; n += m.sum()
        fl = int((np.diff(st) != 0).sum()); flips += fl; rows += len(st)
        mn = ok & (st == 0)
        lean_h += (np.sign(s[mn] - 0.5) == np.sign(Y[mn])).sum(); lean_n += mn.sum()
        per.append((d, round(hh / max(m.sum(), 1), 3), round(m.sum() / max(ok.sum(), 1), 2), fl))
    hrs = rows * 5 / 3600
    return dict(hit=hits / max(n, 1), cover=n / max(1, sum(np.isfinite(y_of(d, lag, Hs)).sum() for d in dl)),
                flips_h=flips / hrs, lean_hit=lean_h / max(lean_n, 1), per=per)


print("\n== hysteresis grid, chosen on EARLY test days, then frozen on LATE")
grid = list(itertools.product((0, 4), (0.56, 0.58, 0.60, 0.62), (0.52, 0.54), (0, 12)))
for key in ("lag0_H180", "lag30_H180"):
    lag = int(key.split("_")[0][3:]); Hs = 180
    best = None
    for prm in grid:
        e = eval_h(key, EARLY, lag, Hs, prm)
        if e["cover"] >= 0.25 and (best is None or e["hit"] > best[1]["hit"]):
            best = (prm, e)
    prm = best[0]
    lt = eval_h(key, LATE, lag, Hs, prm)
    print(key, "variants", len(grid), "chosen (half-life rows, in, out, dwell rows)", prm)
    print("   early hit %.3f cover %.2f flips/h %.1f lean-hit %.3f" % (best[1]["hit"], best[1]["cover"], best[1]["flips_h"], best[1]["lean_hit"]))
    print("   late  hit %.3f cover %.2f flips/h %.1f lean-hit %.3f" % (lt["hit"], lt["cover"], lt["flips_h"], lt["lean_hit"]))
    print("   late per day (day, hit, cover, flips):", lt["per"])
    raw = eval_h(key, LATE, lag, Hs, (0, 0.56, 0.56, 0))
    print("   no hysteresis (in=out=0.56): late hit %.3f cover %.2f flips/h %.1f" % (raw["hit"], raw["cover"], raw["flips_h"]))
    out[f"hyst|{key}"] = dict(prm=prm, early=best[1], late=lt, raw=raw)

# the current verdict rule analogue: 2-min ridge z with thresholds 0.15 / 0.35 (word changes per hour)
fl = rows = 0
for d in tdays:
    z = R[f"z120|{d}"].astype(float)
    w = np.where(z >= 0.35, 2, np.where(z >= 0.15, 1, np.where(z <= -0.35, -2, np.where(z <= -0.15, -1, 0))))
    fl += int((np.diff(w) != 0).sum()); rows += len(w)
print("\ncurrent-rule analogue (2-min ridge z, words at 0.15 / 0.35): word changes per hour %.1f" % (fl / (rows * 5 / 3600)))
json.dump(out, open(os.path.join(D, "sum2.json"), "w"), indent=1, default=str)
