import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 6: is the forward-minus-future gap a real lead (the future catches up to the forward) or noise in the
future's mid? Correlate the gap deviation with the NEXT move of the future AND of the forward itself, and split the
gap into (a) the forward's own last-5-s move and (b) the future's own last-5-s move.
Also: does the spread state matter (wide futures spread -> noisier mid)?"""
import os
import numpy as np

W = r"D:\ApexOptions\data\research\13nov\work\R07"
HZ = [5, 10, 30, 60, 120, 300]


def rank(a):
    o = np.argsort(a, kind="stable"); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r


def spear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return np.nan
    return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1])


def at_time(t, y, tq):
    j = np.searchsorted(t, tq, side="right") - 1
    return np.where(j >= 0, y[np.clip(j, 0, None)], np.nan), j


def ema_gap(t, x, tau=300.0):
    out = np.full(len(t), np.nan); prev = np.nan; tp = None
    for i in range(len(t)):
        v = x[i]
        if np.isfinite(v):
            if not np.isfinite(prev):
                prev = v
            else:
                a = 1 - np.exp(-(t[i] - tp) / tau)
                prev = prev + a * (v - prev)
            tp = t[i]
        out[i] = prev
    return out


for p in sys.argv[1:]:
    f = np.load(os.path.join(W, f"feat_{p}.npz"))
    t = f["t"]; fm = f["fm"].astype(float); fwd = f["fwd"].astype(float)
    names = list(f["names"]); X = f["X"].astype(float)
    spr = X[:, names.index("spr")]
    gap = fwd - fm
    gdev = gap - ema_gap(t, gap)           # causal: the gap against its own 5-min EMA
    sel = np.arange(0, len(t), 5)          # every 5th second, as the Lab samples
    f5, _ = at_time(t, fwd, t - 5); m5, _ = at_time(t, fm, t - 5)
    dfw5, dfm5 = fwd - f5, fm - m5
    print(f"\n{p}  rows {len(sel)}; IC with the NEXT h-second move   (h = {HZ})")
    for nm, x in (("gap_dev", gdev), ("fwd_own5", dfw5), ("fut_own5", dfm5)):
        for tgt, s in (("future", fm), ("forward", fwd)):
            ics = []
            for h in HZ:
                y, jh = at_time(t, s, t + h)
                gp = (t + h) - t[np.clip(jh, 0, len(t) - 1)]
                y = np.where(gp > 3, np.nan, y - s)
                ics.append(spear(x[sel], y[sel]))
            print(f"  {nm:9s} -> {tgt:8s}", " ".join(f"{v:+.3f}" for v in ics))
    # by spread state: gap_dev -> future 30 s
    y30, jh = at_time(t, fm, t + 30); y30 = y30 - fm
    w30, _ = at_time(t, fwd, t + 30); w30 = w30 - fwd
    q = np.nanpercentile(spr, [33, 67])
    for lo, hi, nm in ((-1, q[0], "narrow"), (q[0], q[1], "middle"), (q[1], 1e9, "wide")):
        m = (spr > lo) & (spr <= hi)
        mm = np.zeros(len(t), bool); mm[sel] = True; m &= mm
        print(f"  spread {nm:6s} ({lo:.1f},{hi:.1f}] n {int(m.sum())}: gap_dev->fut30 {spear(gdev[m], y30[m]):+.3f}  gap_dev->fwd30 {spear(gdev[m], w30[m]):+.3f}")
    # how big is it: mean future move over 60 s by gap_dev decile
    y60, _ = at_time(t, fm, t + 60); y60 = y60 - fm
    w60, _ = at_time(t, fwd, t + 60); w60 = w60 - fwd
    g = gdev[sel]; yy = y60[sel]; ww = w60[sel]
    ok = np.isfinite(g) & np.isfinite(yy) & np.isfinite(ww)
    qs = np.percentile(g[ok], np.arange(10, 100, 10))
    b = np.digitize(g[ok], qs)
    print("  gap_dev decile edges", np.round(qs, 1).tolist())
    print("  mean future 60-s move by decile ", [round(float(np.mean(yy[ok][b == i])), 2) for i in range(10)])
    print("  mean forward 60-s move by decile", [round(float(np.mean(ww[ok][b == i])), 2) for i in range(10)])
