import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (run after 15:30, alone; about 3 minutes on a quiet machine). How many seconds of the forecaster's 1-3 minute
direction skill survive a delay? For lags 0, 5, 10, 15, 20, 30, 45, 60 s: walk-forward ridge (all 46 inputs, earlier
days only) of the move from t+lag to t+lag+h, h = 60, 120, 180 s. Prints mean IC, top-fifth hit and days with IC > 0.
Reads data/forecast_lab/collect/<day>.joblib one at a time; writes work/R10/phaseB_lag_decay.json."""
import os, glob, json, time
import numpy as np, joblib
T0 = time.time()
COL = r"D:\ApexOptions\data\forecast_lab\collect"
OUT = r"D:\ApexOptions\data\research\13nov\work\R10"
LAGS = (0, 5, 10, 15, 20, 30, 45, 60); H = (60, 120, 180)
days = []
for f in sorted(glob.glob(os.path.join(COL, "*.joblib"))):
    d = joblib.load(f); X, S = d["X"], d["S"]
    st = S[:, 0].astype(np.int64); base = int(st[0]); arr = np.full(int(st[-1]) - base + 2000, np.nan); arr[st - base] = S[:, 1]
    t = X[:, 0]

    def at(tt):
        k = np.round(tt).astype(np.int64) - base; ok = (k >= 0) & (k < len(arr)); o = np.full(len(tt), np.nan); o[ok] = arr[k[ok]]; return o
    y = {(lag, h): (at(t + lag + h) - (X[:, 1] if lag == 0 else at(t + lag))) / np.sqrt(X[:, 2] * h) for lag in LAGS for h in H}
    days.append(dict(day=d["day"], X=X[:, 3:].astype(float), y=y))
    del d
X0 = np.vstack([d["X"] for d in days[:5]]); med = np.nanmedian(X0, 0); sd = np.nanstd(X0, 0); sd = np.where(sd > 1e-9, sd, 1)
for d in days:
    d["Z"] = np.c_[np.ones(len(d["X"])), np.clip(np.nan_to_num((d["X"] - med) / sd), -6, 6)]
    d["G"] = {}
    for k, y in d["y"].items():
        ok = np.isfinite(y); d["G"][k] = (d["Z"][ok].T @ d["Z"][ok], d["Z"][ok].T @ np.clip(y[ok], -4, 4))
out = {}
for k in days[0]["y"]:
    ics, tops = [], []
    for i in range(5, len(days)):
        A = sum(d["G"][k][0] for d in days[:i]).copy(); A[1:, 1:] += 3000 * np.eye(A.shape[0] - 1)
        w = np.linalg.solve(A, sum(d["G"][k][1] for d in days[:i]))
        s = days[i]["Z"] @ w; y = days[i]["y"][k]; ok = np.isfinite(y) & (y != 0)
        ics.append(float(np.corrcoef(s[ok], y[ok])[0, 1]))
        top = ok & (np.abs(s) >= np.quantile(np.abs(s[ok]), 0.8)); tops.append(float((np.sign(s[top]) == np.sign(y[top])).mean()))
    out[f"{k[0]}_{k[1]}"] = dict(ic=float(np.mean(ics)), top=float(np.mean(tops)), pos=int(sum(x > 0 for x in ics)), n=len(ics))
    print(f"lag {k[0]:2d} s  h {k[1] // 60} min: IC {np.mean(ics):+.3f}  top-fifth hit {np.mean(tops):.3f}  IC>0 on {sum(x > 0 for x in ics)}/{len(ics)}", flush=True)
json.dump(out, open(os.path.join(OUT, "phaseB_lag_decay.json"), "w"), indent=1)
print("done", round(time.time() - T0, 1), "s")
