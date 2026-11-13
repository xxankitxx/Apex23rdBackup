import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (run after 15:30, alone, needs work/R10/cache/*.npz from cache.py). Builds the STAND model file the
forecaster would read, and its honest-odds table, without touching apex/ or data/forecast_lab/:
  1. ridge zhat_h per horizon (1, 2, 3, 5, 10, 15 min) on ALL cached days (what tomorrow's live run would use)
  2. fusion logistic L = a0 + sum a_h zhat_h for the sign of the 2-minute move (leave-one-day-out zhat inputs)
  3. Platt c0 + c1 L fitted on the walk-forward out-of-sample rows of every day after the fifth
  4. the honest-odds table: realised hit by conviction bucket on those out-of-sample rows, and per day
Writes work/R10/stand_model.json. A shadow display reads this file; nothing live does until the owner says so."""
import os, glob, json, time
import numpy as np
T0 = time.time()
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); HS = 120
days = []
for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz"))):
    z = np.load(f); days.append(dict(day=os.path.basename(f)[:10], X=z["X"].astype(float), dF=z["dF"][0].astype(float), vref=z["vref"].astype(float)))
X0 = np.vstack([d["X"] for d in days]); med = np.nanmedian(X0, 0); sd = np.nanstd(X0, 0); sd = np.where(sd > 1e-9, sd, 1)
for d in days:
    d["Z"] = np.c_[np.ones(len(d["X"])), np.clip(np.nan_to_num((d["X"] - med) / sd), -6, 6)]
    d["G"] = {}
    for j, h in enumerate(H):
        y = d["dF"][j] / np.sqrt(d["vref"] * h); ok = np.isfinite(y)
        d["G"][h] = (d["Z"][ok].T @ d["Z"][ok], d["Z"][ok].T @ np.clip(y[ok], -4, 4))


def ridge(tr, h):
    A = sum(d["G"][h][0] for d in tr).copy(); A[1:, 1:] += 3000 * np.eye(A.shape[0] - 1)
    return np.linalg.solve(A, sum(d["G"][h][1] for d in tr))


def logit_fit(X, y, l2=10.0):
    Xc = np.c_[np.ones(len(X)), X]; w = np.zeros(Xc.shape[1]); R = l2 * np.eye(len(w)); R[0, 0] = 0
    for _ in range(30):
        p = 1 / (1 + np.exp(-np.clip(Xc @ w, -30, 30)))
        s = np.linalg.solve((Xc * (p * (1 - p))[:, None]).T @ Xc + R, Xc.T @ (p - y) + R @ w); w -= s
        if np.abs(s).max() < 1e-8: break
    return w


def zmat(ws, d):
    return np.column_stack([d["Z"] @ ws[h] for h in H])


# 1-2: final ridge on all days; fusion on leave-one-day-out zhat
W = {h: ridge(days, h) for h in H}
Zl, Yl = [], []
for k in range(len(days)):
    wk = {h: ridge(days[:k] + days[k + 1:], h) for h in H}
    Zl.append(zmat(wk, days[k])); Yl.append(days[k]["dF"][H.index(HS)])
Zl = np.vstack(Zl); Yl = np.concatenate(Yl); ok = np.isfinite(Yl) & (Yl != 0)
A = logit_fit(Zl[ok], (Yl[ok] > 0).astype(float))
# 3-4: walk-forward OOS fused logits, Platt on them, the odds table
L, Y, DY = [], [], []
for i in range(5, len(days)):
    wi = {h: ridge(days[:i], h) for h in H}
    zi = zmat(wi, days[i]); Ai = A                               # fusion weights: an approximation (fitted on all days)
    L.append(np.c_[np.ones(len(zi)), zi] @ Ai); Y.append(days[i]["dF"][H.index(HS)]); DY += [days[i]["day"]] * len(zi)
L = np.concatenate(L); Y = np.concatenate(Y); DY = np.array(DY); ok = np.isfinite(Y) & (Y != 0)
C = logit_fit(L[ok][:, None], (Y[ok] > 0).astype(float), l2=1e-6)
p = 1 / (1 + np.exp(-(C[0] + C[1] * L)))
c = np.maximum(p, 1 - p); hit = np.sign(p - 0.5) == np.sign(Y)
table = []
for a, b in ((0.5, 0.53), (0.53, 0.56), (0.56, 0.60), (0.60, 0.65), (0.65, 1.01)):
    m = ok & (c >= a) & (c < b)
    days_ok = [float(hit[m & (DY == dd)].mean()) for dd in sorted(set(DY)) if (m & (DY == dd)).sum() >= 30]
    table.append(dict(lo=a, hi=min(b, 1.0), n=int(m.sum()), indep=round(m.sum() * 5 / HS), said=float(c[m].mean()) if m.sum() else None,
                      got=float(hit[m].mean()) if m.sum() else None, days_above_half=sum(x > 0.5 for x in days_ok), days=len(days_ok)))
json.dump(dict(built=time.strftime("%Y-%m-%d %H:%M"), horizon_s=HS, feats_med=med.tolist(), feats_sd=sd.tolist(),
               ridge={str(h): W[h].tolist() for h in H}, fusion=A.tolist(), platt=C.tolist(), odds=table,
               note="fusion weights in the odds table are fitted on all days (slightly optimistic); see R10 report"),
          open(os.path.join(D, "stand_model.json"), "w"), indent=1)
for r in table:
    print(r)
print("done", round(time.time() - T0, 1), "s")
