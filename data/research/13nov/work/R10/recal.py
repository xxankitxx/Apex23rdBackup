import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""(1) Honest odds: Platt recalibration of the fused stand fitted on EARLIER walk-forward days' out-of-sample rows.
(2) Hysteresis chosen under a stability cap (at most 12 changes an hour) on early test days, frozen on late.
(3) Today's persistence: does the last 5-minute move continue? Sign learned within the day from matured checks only."""
import os, glob, json, itertools
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); LAGS = (0, 30)
R = np.load(os.path.join(D, "stand_rows.npz"))
cache = {os.path.basename(f)[:10]: np.load(f) for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz")))}
tdays = sorted({k.split("|")[1] for k in R.files})
out = {}
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
y_of = lambda d, lag, h: cache[d]["dF"][LAGS.index(lag), H.index(h)].astype(float)


def platt(x, y, iters=30):
    w = np.zeros(2)
    Xc = np.c_[np.ones(len(x)), x]
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Xc @ w, -30, 30)))
        st = np.linalg.solve((Xc * (p * (1 - p))[:, None]).T @ Xc + 1e-6 * np.eye(2), Xc.T @ (p - y))
        w -= st
        if np.abs(st).max() < 1e-8:
            break
    return w


print("== (1) recalibrated conviction, lag 0, stand horizon 3 min (Platt on earlier test days' OOS rows)")
BK = [0.5, 0.53, 0.56, 0.60, 0.65, 1.01]
for key, lag, Hs in (("lag0_H180", 0, 180), ("lag0_H120", 0, 120), ("lag30_H180", 30, 180)):
    pooled = {"early": [], "late": []}
    coefs = []
    for k in range(2, len(tdays)):
        prev = tdays[:k]
        x = np.concatenate([lg(R[f"{key}|{d}"].astype(float)) for d in prev])
        y = np.concatenate([y_of(d, lag, Hs) for d in prev])
        ok = np.isfinite(y) & (y != 0)
        w = platt(x[ok], (y[ok] > 0).astype(float))
        coefs.append((tdays[k], round(float(w[0]), 3), round(float(w[1]), 3)))
        d = tdays[k]
        p2 = 1 / (1 + np.exp(-(w[0] + w[1] * lg(R[f"{key}|{d}"].astype(float)))))
        yy = y_of(d, lag, Hs)
        pooled["early" if d <= "2026-11-04" else "late"].append((p2, yy, d))
    print(key, "Platt (day, a, b):", coefs)
    for win in ("early", "late"):
        P = np.concatenate([a for a, _, _ in pooled[win]]); Y = np.concatenate([b for _, b, _ in pooled[win]])
        ok = np.isfinite(Y) & (Y != 0); P, Y = P[ok], Y[ok]
        c = np.maximum(P, 1 - P); hit = np.sign(P - 0.5) == np.sign(Y)
        ece = 0.0
        print(f"  {win}: rows {len(P)}, hit {hit.mean():.3f}")
        for a, b in zip(BK[:-1], BK[1:]):
            m = (c >= a) & (c < b)
            if m.sum():
                ece += m.mean() * abs(c[m].mean() - hit[m].mean())
                print(f"    [{a:.2f}-{min(b, 1):.2f}) share {m.mean():5.1%} n={m.sum():5d} (~{m.sum() * 5 / Hs:4.0f} indep) said {c[m].mean():.3f} got {hit[m].mean():.3f}")
        print(f"    calibration error (ECE) {ece:.3f}")
        # per day hit for conviction >= 0.56
        pdl = []
        for p2, yy, d in pooled[win]:
            okd = np.isfinite(yy) & (yy != 0); cc = np.maximum(p2, 1 - p2); m = okd & (cc >= 0.56)
            pdl.append((d[5:], round(float((np.sign(p2[m] - 0.5) == np.sign(yy[m])).mean()), 3) if m.sum() else None, int(m.sum())))
        print("    per day hit at conviction >= 56 %:", pdl)
        out[f"recal|{key}|{win}"] = dict(hit=float(hit.mean()), ece=ece, perday=pdl)


def stand_series(p, a_hl, th_in, th_out, dwell):
    al = 1 - 0.5 ** (1.0 / a_hl) if a_hl > 0 else 1.0
    st = np.zeros(len(p), int); sm = np.empty(len(p)); cur, since, e = 0, -10 ** 6, p[0]
    for i, x in enumerate(p):
        e = e + al * (x - e)
        sm[i] = e
        want = cur
        if cur == 0:
            want = 1 if e >= th_in else -1 if e <= 1 - th_in else 0
        elif cur == 1 and e < th_out:
            want = -1 if e <= 1 - th_in else 0
        elif cur == -1 and e > 1 - th_out:
            want = 1 if e >= th_in else 0
        if want != cur and (i - since) >= dwell:
            cur, since = want, i
        st[i] = cur
    return sm, st


def ev(key, dl, lag, Hs, prm):
    hh = nn = fl = rows = tot = 0; per = []
    for d in dl:
        p = R[f"{key}|{d}"].astype(float); y = y_of(d, lag, Hs)
        sm, st = stand_series(p, *prm)
        ok = np.isfinite(y) & (y != 0); m = ok & (st != 0)
        h_ = int((np.sign(st[m]) == np.sign(y[m])).sum())
        hh += h_; nn += int(m.sum()); tot += int(ok.sum())
        f_ = int((np.diff(st) != 0).sum()); fl += f_; rows += len(st)
        per.append((d[5:], round(h_ / max(m.sum(), 1), 3), round(m.sum() / max(ok.sum(), 1), 2), round(f_ / (len(st) * 5 / 3600), 1)))
    return dict(hit=hh / max(nn, 1), cover=nn / max(tot, 1), flips_h=fl / (rows * 5 / 3600), n=nn, per=per)


print("\n== (2) hysteresis under a stability cap (<= 12 changes an hour), chosen on early test days, frozen on late")
EARLY = [d for d in tdays if d <= "2026-11-04"]; LATE = [d for d in tdays if d >= "2026-11-05"]
grid = list(itertools.product((6, 12, 24), (0.56, 0.58, 0.60), (0.50, 0.53), (12, 24)))
for key, lag, Hs in (("lag0_H180", 0, 180), ("lag0_H300", 0, 300)):
    best = None
    for prm in grid:
        e = ev(key, EARLY, lag, Hs, prm)
        if e["flips_h"] <= 12 and e["cover"] >= 0.2 and (best is None or e["hit"] > best[1]["hit"]):
            best = (prm, e)
    if best is None:
        print(key, "no setting met the cap"); continue
    lt = ev(key, LATE, lag, Hs, best[0])
    print(key, f"variants {len(grid)}; chosen (EWMA half-life rows, enter, leave, min dwell rows) {best[0]}")
    print(f"   early: hit {best[1]['hit']:.3f} cover {best[1]['cover']:.2f} changes/h {best[1]['flips_h']:.1f}")
    print(f"   late : hit {lt['hit']:.3f} cover {lt['cover']:.2f} changes/h {lt['flips_h']:.1f}; per day {lt['per']}")
    out[f"hyst|{key}"] = dict(prm=best[0], early=best[1], late=lt)

print("\n== (3) today's persistence: follow (or fade) the last 5-min move by today's matured record; no cross-day fit")
for lag in (0, 30):
    for h in (180, 300, 600, 900):
        res = {"early": [0, 0], "late": [0, 0]}; per = []
        for d in sorted(cache):
            z = cache[d]; X = z["X"]; r300 = X[:, 5].astype(float); y = y_of(d, lag, h)
            s0 = np.sign(r300) * (np.abs(r300) >= 0.7)
            agree = np.where(np.isfinite(y) & (y != 0) & (s0 != 0), s0 * np.sign(y), 0.0)
            k = (h + lag) // 5                                   # rows until a check matures
            cs = np.r_[0.0, np.cumsum(agree)]; cn = np.r_[0, np.cumsum(agree != 0)]
            idx = np.arange(len(y)) - k
            A = np.where(idx >= 0, cs[np.clip(idx + 1, 0, len(cs) - 1)], 0.0)
            N = np.where(idx >= 0, cn[np.clip(idx + 1, 0, len(cn) - 1)], 0)
            neff = N * 5.0 / h
            rate = np.where(N > 0, A / np.maximum(N, 1), 0.0)
            act = (neff >= 6) & (np.abs(rate) * np.sqrt(np.maximum(neff, 1)) >= 1.0) & (s0 != 0) & np.isfinite(y) & (y != 0)
            pred = s0 * np.sign(rate)
            hit = int((pred[act] == np.sign(y[act])).sum()); n = int(act.sum())
            w = "early" if d <= "2026-11-04" else "late"
            res[w][0] += hit; res[w][1] += n
            per.append((d[5:], round(hit / max(n, 1), 3), round(n * 5 / h)))
        print(f"  lag {lag:2d} s, horizon {h // 60:2d} min: early hit {res['early'][0] / max(res['early'][1], 1):.3f} "
              f"(~{res['early'][1] * 5 / h:.0f} indep), late hit {res['late'][0] / max(res['late'][1], 1):.3f} (~{res['late'][1] * 5 / h:.0f} indep)")
        print("     per day (day, hit, ~indep):", per)
        out[f"persist|lag{lag}|{h}"] = dict(res=res, per=per)
json.dump(out, open(os.path.join(D, "recal.json"), "w"), indent=1, default=str)
