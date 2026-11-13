import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R10 stand study on the compact cache (cache.py). Walk-forward, expanding window, models fitted on earlier days only.
Writes study2.json (per-day metrics, ablations) and stand_rows.npz (per-row fused probabilities for the hysteresis study)."""
import os, glob, json, time
T0 = time.time()
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
FEATS = ("r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800", "lv30", "lv120", "lv600", "lv1800", "lviv",
         "lv120_600", "lv600_iv", "jump120", "absr5", "vr", "er300", "slope120", "kf", "imb", "micro", "ofi30", "ofi120",
         "spr", "vwap", "rng", "dhi", "dlo", "div60", "div300", "skew", "dskew300", "dstr60", "dbasis", "hw30", "hw120",
         "hwlead30", "bank120", "up60", "tod", "tod2", "left", "dte", "exp")
H = (60, 120, 180, 300, 600, 900)
LAGS = (0, 30)
G = dict(hw=["hw30", "hw120", "hwlead30", "bank120", "up60"], flow=["imb", "micro", "ofi30", "ofi120", "spr"],
         opt=["div60", "div300", "skew", "dskew300", "dstr60", "dbasis"], lead=["hwlead30", "dbasis", "div60", "dstr60", "hw30"])
fi = {f: i for i, f in enumerate(FEATS)}
VAR = {"all": list(range(len(FEATS)))}
for g in ("hw", "flow", "opt", "lead"):
    VAR["no_" + g] = [i for i, f in enumerate(FEATS) if f not in G[g]]
VAR["price_only"] = [i for i, f in enumerate(FEATS) if f not in G["hw"] + G["flow"] + G["opt"]]
VAR["hw_flow_only"] = [fi[f] for f in G["hw"] + G["flow"]]

days = []
for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz"))):
    z = np.load(f)
    days.append(dict(day=os.path.basename(f)[:10], **{k: z[k] for k in z.files}))
names = [d["day"] for d in days]
X0 = np.vstack([d["X"] for d in days[:5]]).astype(float)
med = np.nanmedian(X0, 0); sd = np.nanstd(X0, 0); sd = np.where(sd > 1e-9, sd, 1.0)
for d in days:
    Z = np.clip(np.nan_to_num((d["X"].astype(float) - med) / sd), -6, 6)
    d["Zc"] = np.c_[np.ones(len(Z)), Z]
    d["y"] = {}
    for i, lag in enumerate(LAGS):
        for j, h in enumerate(H):
            d["y"][(lag, h)] = d["dF"][i, j].astype(float) / np.sqrt(np.maximum(d["vref"], 1e-9) * h)
    d["G"], d["b"] = {}, {}
    for k, y in d["y"].items():
        ok = np.isfinite(y)
        Zk = d["Zc"][ok]
        d["G"][k] = Zk.T @ Zk
        d["b"][k] = Zk.T @ np.clip(y[ok], -4, 4)
print("prepared", round(time.time() - T0, 1), flush=True)


def solve(tr, k, cols, alpha=3000.0):
    c = [0] + [i + 1 for i in cols]
    A = sum(d["G"][k] for d in tr)[np.ix_(c, c)].copy()
    A[1:, 1:] += alpha * np.eye(len(c) - 1)
    b = sum(d["b"][k] for d in tr)[c]
    return c, np.linalg.solve(A, b)


def logit_fit(Xs, y, l2=10.0, iters=25):
    Xc = np.c_[np.ones(len(Xs)), Xs]
    w = np.zeros(Xc.shape[1]); R = l2 * np.eye(Xc.shape[1]); R[0, 0] = 0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Xc @ w, -30, 30)))
        st = np.linalg.solve((Xc * (p * (1 - p))[:, None]).T @ Xc + R, Xc.T @ (p - y) + R @ w)
        w -= st
        if np.abs(st).max() < 1e-7:
            break
    return w


def lp(w, Xs):
    return 1 / (1 + np.exp(-np.clip(np.c_[np.ones(len(Xs)), Xs] @ w, -30, 30)))


res = dict(days=names, abl={}, stand={}, fus_w={})
# 1. ablations: IC and top-fifth hit per horizon, lag 0 and lag 30
for vn, cols in VAR.items():
    for lag in LAGS:
        per = {}
        for i in range(5, len(days)):
            tr, te = days[:i], days[i]
            rec = {}
            for h in H:
                c, w = solve(tr, (lag, h), cols)
                s = te["Zc"][:, c] @ w
                y = te["dF"][LAGS.index(lag), H.index(h)].astype(float)
                ok = np.isfinite(y) & (y != 0)
                q = np.quantile(np.abs(s[ok]), 0.8)
                top = ok & (np.abs(s) >= q)
                rec[f"ic{h}"] = float(np.corrcoef(s[ok], y[ok])[0, 1])
                rec[f"top{h}"] = float((np.sign(s[top]) == np.sign(y[top])).mean())
                rec[f"all{h}"] = float((np.sign(s[ok]) == np.sign(y[ok])).mean())
            per[te["day"]] = rec
        res["abl"][f"{vn}|lag{lag}"] = per
    print("abl", vn, round(time.time() - T0, 1), flush=True)

# 2. the fused stand: zhat at all horizons -> logistic for the sign of the move over Hs; fitted on training days only
rows = {}
for lag in LAGS:
    for Hs in (120, 180, 300):
        key = f"lag{lag}_H{Hs}"
        for i in range(5, len(days)):
            tr, te = days[:i], days[i]
            ws = {h: solve(tr, (lag, h), VAR["all"]) for h in H}
            Ztr = np.vstack([np.column_stack([d["Zc"] @ ws[h][1] for h in H]) for d in tr])
            ytr = np.concatenate([d["dF"][LAGS.index(lag), H.index(Hs)].astype(float) for d in tr])
            ok = np.isfinite(ytr) & (ytr != 0)
            w = logit_fit(Ztr[ok], (ytr[ok] > 0).astype(float))
            Zte = np.column_stack([te["Zc"] @ ws[h][1] for h in H])
            p = lp(w, Zte)
            rows.setdefault(key, {})[te["day"]] = p.astype(np.float32)
            res["fus_w"].setdefault(key, {})[te["day"]] = [round(float(v), 3) for v in w]
            if lag == 0 and Hs == 120:
                rows.setdefault("z120", {})[te["day"]] = Zte[:, 1].astype(np.float32)
        print("stand", key, round(time.time() - T0, 1), flush=True)
np.savez_compressed(os.path.join(D, "stand_rows.npz"),
                    **{f"{k}|{dd}": v for k, m in rows.items() for dd, v in m.items()})
json.dump(res, open(os.path.join(D, "study2.json"), "w"), indent=1)
print("done", round(time.time() - T0, 1))
