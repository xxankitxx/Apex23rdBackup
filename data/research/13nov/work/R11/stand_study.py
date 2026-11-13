import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R11: can the forecaster honestly take a 5 / 15-minute "stand"? Walk-forward on the Forecast Lab collect files.
# Discover 19 Oct - 4 Nov, test 5 Nov - 11 Nov (per day), plus rolling (train on every earlier day).
import glob, os, json
import numpy as np
sys.path.insert(0, r"D:\ApexOptions")

OUT = r"D:\ApexOptions\data\research\13nov\work\R11"
files = sorted(glob.glob(r"D:\ApexOptions\data\forecast_lab\collect\*.joblib"))
USE = ["r300", "r600", "r1800", "vwap", "rng", "dhi", "dlo", "kf", "er300", "vr", "hw120", "bank120", "up60", "imb", "ofi120", "tod", "left"]
HS = (300, 900)
import time; T0 = time.time()
days = {}
for f in sorted(glob.glob(os.path.join(OUT, "cache", "*.npz"))):
    c = np.load(f); day = os.path.basename(f)[:-4]
    Z = c["Z"]
    days[day] = dict(Z=Z, y={300: c["y5"], 900: c["y15"]}, t=c["t"], vw=Z[:, USE.index("vwap")],
                     r18=Z[:, USE.index("r1800")], kf=Z[:, USE.index("kf")], r6=Z[:, USE.index("r600")])
print("loaded", round(time.time() - T0, 1), flush=True)
names = sorted(days)
early = [d for d in names if d <= "2026-11-04"]
late = [d for d in names if d >= "2026-11-05"]


def fit(Zs, ys, lam=5.0):
    Z = np.vstack(Zs); yy = np.concatenate(ys)
    ok = np.isfinite(yy) & (yy != 0)
    Z, yy = Z[ok], (yy[ok] > 0).astype(float)
    mu, sd = Z.mean(0), Z.std(0) + 1e-9
    A = np.c_[np.ones(len(Z)), (Z - mu) / sd]
    w = np.zeros(A.shape[1])
    for _ in range(8):
        p = 1 / (1 + np.exp(-A @ w))
        g = A.T @ (p - yy) + lam * np.r_[0, w[1:]]
        H = (A * (p * (1 - p))[:, None]).T @ A + lam * np.diag(np.r_[0, np.ones(len(w) - 1)])
        w -= np.linalg.solve(H, g)
    return mu, sd, w


def prob(m, Z):
    mu, sd, w = m
    return 1 / (1 + np.exp(-(np.c_[np.ones(len(Z)), (Z - mu) / sd] @ w)))


def score(p, y, thr):
    ok = np.isfinite(y) & (y != 0)
    p, y = p[ok], y[ok]
    call = np.abs(p - 0.5) >= thr - 0.5
    if call.sum() == 0:
        return dict(n=0, cov=0.0, hit=None, pts=None)
    right = (p[call] > 0.5) == (y[call] > 0)
    signed = np.where(p[call] > 0.5, y[call], -y[call])
    # 5-s origins overlap: independent checks about n * 5 / h
    return dict(n=int(call.sum()), cov=float(call.mean()), hit=float(right.mean()), pts=float(signed.mean()))


res = dict(variants=[], per_day={})
nvar = 0
for h in HS:
    # A: fixed split, logistic on USE
    m = fit([days[d]["Z"] for d in early], [days[d]["y"][h] for d in early])
    for thr in (0.55, 0.60, 0.65):
        nvar += 1
        rows = []
        for d in late:
            s = score(prob(m, days[d]["Z"]), days[d]["y"][h], thr); s["day"] = d; rows.append(s)
        ins = [score(prob(m, days[d]["Z"]), days[d]["y"][h], thr) for d in early]
        res["variants"].append(dict(model="logit_split", h=h, thr=thr, test=rows,
                                    insample_hit=float(np.nanmean([x["hit"] for x in ins if x["hit"] is not None])) if ins else None))
    # B: rolling (train on all earlier days, min 5)
    for thr in (0.60,):
        nvar += 1
        rows = []
        for i, d in enumerate(names):
            if i < 5:
                continue
            m2 = fit([days[e]["Z"] for e in names[:i]], [days[e]["y"][h] for e in names[:i]])
            s = score(prob(m2, days[d]["Z"]), days[d]["y"][h], thr); s["day"] = d; rows.append(s)
        res["variants"].append(dict(model="logit_rolling", h=h, thr=thr, test=rows))
    # C: descriptive trend stand, no fitting: above VWAP and 30-min momentum up and Kalman slope up -> bullish
    for rule in ("vwap+r1800+kf", "vwap+r600"):
        nvar += 1
        rows = []
        for d in names:
            D = days[d]
            if rule == "vwap+r1800+kf":
                sg = np.where((D["vw"] > 0) & (D["r18"] > 0) & (D["kf"] > 0), 1, np.where((D["vw"] < 0) & (D["r18"] < 0) & (D["kf"] < 0), -1, 0))
            else:
                sg = np.where((D["vw"] > 0) & (D["r6"] > 0), 1, np.where((D["vw"] < 0) & (D["r6"] < 0), -1, 0))
            p = 0.5 + 0.2 * sg
            s = score(p, D["y"][h], 0.6); s["day"] = d; rows.append(s)
        res["variants"].append(dict(model="rule_" + rule, h=h, thr=None, test=rows))

# stand stability: how often a 15-min logistic stand at 0.60 flips (bull <-> bear, ignoring none) per hour, test days
m = fit([days[d]["Z"] for d in early], [days[d]["y"][900] for d in early])
flips = {}
for d in late:
    p = prob(m, days[d]["Z"])
    s = np.where(p >= 0.6, 1, np.where(p <= 0.4, -1, 0))
    nz = s[s != 0]
    raw = int((np.diff(s) != 0).sum())
    flips[d] = dict(changes_per_hour=raw / (len(s) * 5 / 3600), bull_bear_flips=int((np.diff(nz) != 0).sum()), hours=len(s) * 5 / 3600)
res["flips_logit900_060"] = flips
res["n_variants"] = nvar
res["early"], res["late"] = early, late
json.dump(res, open(os.path.join(OUT, "stand_study.json"), "w"), indent=1)

for v in res["variants"]:
    tt = v["test"]
    hits = [x["hit"] for x in tt if x["hit"] is not None]
    lines = " ".join(f"{x['day'][5:]}:{'-' if x['hit'] is None else round(x['hit']*100)}%/{round(x['cov']*100)}c" for x in tt)
    print(v["model"], v["h"], v["thr"], "mean hit", None if not hits else round(np.mean(hits) * 100, 1),
          "days>50", sum(h > 0.5 for h in hits), "/", len(hits), "ins", v.get("insample_hit"))
    print("   ", lines)
print("flips", json.dumps(flips))
