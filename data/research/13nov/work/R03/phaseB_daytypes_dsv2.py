import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (run after the 15:30 close; one process, under 3 min, well under 1.5 GB).
R03: rebuild the day labels and the 09:45 / 10:15 / 11:00 checkpoint features from EVERY ds_v2 part (all parts of a
multi-part day are joined), add heavyweight-breadth features weighted by Nifty weight, then re-run the leave-one-day-out
day-type classifier and the declared trend lock (L1 dec) with the new labels.
Inputs: data/research/ds_v2/<part>.npz (t, fut, hw, w, sym, g); work/R03/base.pkl (trades).
Outputs: work/R03/phaseB_day_types_dsv2.csv, phaseB_cp_features_dsv2.csv, phaseB_classifier_dsv2.csv (and stdout).
Validated on 13 Nov: ds_v2 (fut[:,0]+fut[:,1])/2 equals the forecast-lab futures mid used in s03 (4 Nov, 4 marks)."""
import os, glob, json, time
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
DS = r"D:\ApexOptions\data\research\ds_v2"
OPEN_M, END_M = 555, 925
CPS = {"0945": 585, "1015": 615, "1100": 660}
parts = {}
for f in sorted(glob.glob(os.path.join(DS, "*.npz"))):
    man = f[:-4] + ".manifest.json"
    try:
        if json.load(open(man)).get("rows", 0) <= 0:
            continue
    except Exception:
        continue
    parts.setdefault(os.path.basename(f)[:10], []).append(f)
TEST = os.environ.get("R03_TEST") == "1"            # smoke test during market hours: two single-part days only
if TEST:
    parts = {k: parts[k] for k in ("2026-11-04", "2026-11-05")}
SUF = "_test" if TEST else ""
rows, feats = [], []
LV = json.load(open(r"D:\ApexOptions\data\learning\day_levels.json", encoding="utf-8"))
for day, fs in sorted(parts.items()):
    T, F, H = [], [], []
    w = None
    for f in fs:
        z = np.load(f, allow_pickle=True)
        t = z["t"].astype(float); fu = z["fut"]
        mid = np.where(np.isfinite(fu[:, 0]) & np.isfinite(fu[:, 1]), (fu[:, 0] + fu[:, 1]) / 2, fu[:, 2])
        T.append(t); F.append(mid); H.append(z["hw"].astype(float))
        if w is None:
            w = np.asarray(z["w"], float)
        del z
    t = np.concatenate(T); Fm = np.concatenate(F); hw = np.concatenate(H)
    o = np.argsort(t, kind="stable"); t, Fm, hw = t[o], Fm[o], hw[o]
    hm = ((t + 19800.0) % 86400.0) / 60.0
    s = (hm >= OPEN_M) & (hm <= END_M + 0.99) & np.isfinite(Fm)
    t, Fm, hw, hm = t[s], Fm[s], hw[s], hm[s]
    if len(t) < 600:
        continue
    marks = np.arange(OPEN_M, END_M + 1)
    idx = np.clip(np.searchsorted(hm, marks + 1.0 / 60, side="right") - 1, 0, len(t) - 1)
    m = Fm[idx]; mi = np.clip(np.floor(hm - OPEN_M).astype(int), 0, len(marks) - 1)
    hi = np.full(len(marks), np.nan); lo = np.full(len(marks), np.nan)
    np.fmax.at(hi, mi, Fm); np.fmin.at(lo, mi, Fm)
    O, C, Hh, Ll = Fm[0], m[-1], np.nanmax(hi), np.nanmin(lo)
    R = Hh - Ll; path = np.nansum(np.abs(np.diff(m)))
    D = (C - O) / R; cpos = (C - Ll) / R
    tH, tL = int(np.nanargmax(hi)), int(np.nanargmin(lo))
    prev = sorted(k for k in LV if k < day)
    gap = O - LV[prev[-1]]["close"] if prev else np.nan            # futures open minus previous SPOT close (basis ~ +50 to +150)
    if D >= 0.55 and cpos >= 0.75:
        shape = "trend_up"
    elif D <= -0.55 and cpos <= 0.25:
        shape = "trend_down"
    elif tL < tH and (O - Ll) >= 0.35 * R and (C - Ll) >= 0.65 * R:
        shape = "V_up"
    elif tH < tL and (Hh - O) >= 0.35 * R and (Hh - C) >= 0.65 * R:
        shape = "V_down"
    else:
        shape = "range"
    rows.append(dict(day=day, parts=len(fs), O=O, H=Hh, L=Ll, C=C, R=R, D=D, cpos=cpos, er=abs(C - O) / path if path else np.nan,
                     shape=shape, gap_raw=gap, tH=tH, tL=tL))
    # heavyweights: open price of each stock = first valid print after 09:15
    hw = np.where(hw > 0, hw, np.nan)
    h0 = np.array([hw[np.isfinite(hw[:, j]), j][0] if np.isfinite(hw[:, j]).any() else np.nan for j in range(hw.shape[1])])
    for cn, cm in CPS.items():
        k = cm - OPEN_M
        i = idx[k]
        seg = m[:k + 1]
        rng = np.nanmax(hi[:k]) - np.nanmin(lo[:k]); Fc = seg[-1]
        pth = np.nansum(np.abs(np.diff(seg)))
        r_stk = hw[i] / h0 - 1.0
        ok = np.isfinite(r_stk) & np.isfinite(w)
        sg = np.sign(Fc - O)
        wb = float(np.sum(w[ok] * (np.sign(r_stk[ok]) == sg)) / np.sum(w[ok])) if ok.any() and sg != 0 else np.nan
        wret = float(np.sum(w[ok] * r_stk[ok]) / np.sum(w[ok]) * 100) if ok.any() else np.nan
        contrib = w[ok] * r_stk[ok]
        top3 = float(np.sum(np.sort(np.abs(contrib))[-3:]) / np.sum(np.abs(contrib))) if ok.sum() >= 3 and np.sum(np.abs(contrib)) > 0 else np.nan
        disp = float(np.nanstd(r_stk[ok]) * 100) if ok.sum() >= 3 else np.nan
        rest = m[k:]; rhi, rlo = np.nanmax(hi[k:]), np.nanmin(lo[k:])
        feats.append(dict(day=day, cp=cn, mv_pct=100 * (Fc - O) / O, rng_pct=100 * rng / O, er=abs(Fc - O) / pth if pth else np.nan,
                          pos=(Fc - np.nanmin(lo[:k])) / rng if rng else np.nan, Dc=(Fc - O) / rng if rng else np.nan,
                          chop=pth / rng if rng else np.nan, hw_breadth_w=wb, hw_wret_pct=wret, hw_top3_share=top3, hw_disp_pct=disp,
                          hw_lead_pct=wret - 100 * (Fc - O) / O if np.isfinite(wret) else np.nan,
                          rest_net_pct=100 * (C - Fc) / O, rest_D=(C - Fc) / (rhi - rlo) if rhi > rlo else np.nan))
    print(day, len(fs), shape, round(time.time() - t00, 1), flush=True)
DT = pd.DataFrame(rows).set_index("day"); FE = pd.DataFrame(feats)
DT.to_csv(os.path.join(W, "phaseB_day_types_dsv2" + SUF + ".csv")); FE.to_csv(os.path.join(W, "phaseB_cp_features_dsv2" + SUF + ".csv"), index=False)
old = pd.read_csv(os.path.join(W, "day_types.csv")).set_index("day")
cmp_ = DT[["shape"]].join(old[["shape"]], rsuffix="_s03")
print("\nlabel agreement with s03 (collect path):", int((cmp_["shape"] == cmp_["shape_s03"]).sum()), "/", len(cmp_))
print(cmp_.to_string())
if TEST:
    print(FE.round(3).to_string()); sys.exit(0)
# ---- LODO classifier on the new features: target = rest-of-day one-way (|rest_D| >= 0.5) and continuation
FE["absD"] = FE.Dc.abs(); FE["ext"] = (FE.pos - 0.5).abs(); FE["y_rest"] = (FE.rest_D.abs() >= 0.5).astype(int)
FE["y_cont"] = (np.sign(FE.rest_net_pct) == np.sign(FE.mv_pct)).astype(int)
X = ["er", "absD", "ext", "chop", "rng_pct", "hw_breadth_w", "hw_top3_share", "hw_disp_pct", "hw_lead_pct"]
out = []
for cn in CPS:
    S = FE[FE.cp == cn].set_index("day").sort_index()
    days = list(S.index)
    for tgt in ("y_rest", "y_cont"):
        y = S[tgt].values; ps = []
        for i in range(len(days)):
            tr = [j for j in range(len(days)) if j != i]
            best = None
            for f in X:
                v = S[f].values.astype(float)
                u = np.unique(v[tr][np.isfinite(v[tr])])
                for th in (u[1:] + u[:-1]) / 2:
                    for sgn in (1, -1):
                        p = (sgn * (v[tr] - th) > 0).astype(int)
                        acc = (p == y[tr]).mean()
                        if best is None or acc > best[0]:
                            best = (acc, f, th, sgn)
            v = S[best[1]].values[i]
            ps.append(int(best[3] * (v - best[2]) > 0) if np.isfinite(v) else 0)
        ps = np.array(ps)
        out.append(dict(cp=cn, target=tgt, days=len(days), base=round(y.mean(), 2), majority=round(max(y.mean(), 1 - y.mean()), 2),
                        lodo_stump=round((ps == y).mean(), 2)))
R = pd.DataFrame(out); R.to_csv(os.path.join(W, "phaseB_classifier_dsv2" + SUF + ".csv"), index=False)
print("\nLODO stump on ds_v2 features (incl. weighted heavyweight breadth)\n", R.to_string())
print("done", round(time.time() - t00, 1))
