import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (after phaseB_sister_extract_all.py): walk-forward test of the sister-index lead on all 17 days.
  1. Lead model: NF futures mid return over the next h s on the past L-s returns of NF, BF mid, FF mid, FN spot, BN spot.
     Fit (least squares) on 19 Oct - 4 Nov pooled; score IC and sign hit-rate on EACH day 5 - 12 Nov.
     Grid h in (5, 15, 30, 60, 180), L in (5, 15, 30, 60). 20 cells x 4 feature sets = 80 variants: say so in the report.
  2. Clean sister measures at the Conductor's entries (BF mid 15 s, FN spot 60 s, sis15 = mean of BF and FF 15 s,
     rsb15 = BF15 - 0.75 NF15, all signed by the trade's direction): cut chosen on the discovery days (quantiles 0.2 / 0.33 / 0.5
     and 0, keep above or below), scored per test day (strike first, compounded %, losing days, worst day, without best day).
Writes work/R09/phaseB_wf_results.json. One process, numpy only, about 1 GB peak."""
import glob, json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sister_io import load, mid  # noqa: E402
SD = os.path.join(HERE, "sister")
days = sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(SD, "2026-*.npz"))})
E = [d for d in days if d <= "2026-11-04"]; L_ = [d for d in days if d > "2026-11-04"]
IST = 19800


def panel(d):
    t, X, A = load(d)
    return dict(t=t, NF=mid(X, A, 1, 1), BF=mid(X, A, 5, 3), FF=mid(X, A, 9, 5),
                FN=np.where(A[:, 4] <= 5, X[:, 8], np.nan), BN=np.where(A[:, 2] <= 5, X[:, 4], np.nan))


def past(x, L):
    o = np.full(len(x), np.nan); o[L:] = np.log(x[L:] / x[:-L]); return o


def fut(x, h):
    o = np.full(len(x), np.nan); o[:-h] = np.log(x[h:] / x[:-h]); return o


SETS = {"own": ["NF"], "own+BF+FF": ["NF", "BF", "FF"], "own+FN+BN": ["NF", "FN", "BN"], "all": ["NF", "BF", "FF", "FN", "BN"]}
res = dict(days=days, lead=[])
P = {d: panel(d) for d in days}
for h in (5, 15, 30, 60, 180):
    for L in (5, 15, 30, 60):
        for nm, fs in SETS.items():
            Xf = np.vstack([np.column_stack([past(P[d][f], L) for f in fs]) for d in E])
            yf = np.concatenate([fut(P[d]["NF"], h) for d in E])
            m = np.isfinite(yf) & np.all(np.isfinite(Xf), 1)
            Z = np.c_[np.ones(m.sum()), Xf[m]]; b = np.linalg.lstsq(Z, yf[m], rcond=None)[0]
            per = {}
            for d in L_:
                Xt = np.column_stack([past(P[d][f], L) for f in fs]); yt = fut(P[d]["NF"], h)
                mm = np.isfinite(yt) & np.all(np.isfinite(Xt), 1)
                p = Xt[mm] @ b[1:]; y = yt[mm]; nz = y != 0
                per[d] = dict(ic=round(float(np.corrcoef(p, y)[0, 1]), 4), hit=round(float(np.mean(np.sign(p[nz]) == np.sign(y[nz]))), 4))
            res["lead"].append(dict(h=h, L=L, set=nm, coef=[float(x) for x in b], test=per))
# 2. Conductor entries
ct = []
for run in ("p44_sim", "p44_simr"):
    dd = json.load(open(rf"D:\ApexOptions\data\replay\batch\{run}\conductor_sim.json"))
    for day, v in dd["days"].items():
        if (run == "p44_sim") == (day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")):
            continue
        for t in v["trades"]:
            ct.append(dict(day=day, book=t["src"], t_in=float(t["t_in"]), ret=float(t["ret_pct"]), rr=t["rr"]))
ct = pd.DataFrame(ct); ct = ct[ct.day.isin(days)]
feat = {k: [] for k in ("bf15", "fn60", "sis15", "rsb15")}
for r in ct.itertuples():
    p = P[r.day]; i = int(r.t_in) - int(p["t"][0]); sg = 1.0 if r.rr == "CE" else -1.0
    ok = 60 <= i < len(p["t"])

    def g(x, L):
        return sg * 1e4 * np.log(x[i] / x[i - L]) if ok and x[i] > 0 and x[i - L] > 0 else np.nan
    bf, ff, nf = g(p["BF"], 15), g(p["FF"], 15), g(p["NF"], 15)
    feat["bf15"].append(bf); feat["fn60"].append(g(p["FN"], 60)); feat["sis15"].append((bf + ff) / 2); feat["rsb15"].append(bf - 0.75 * nf)
for k, v in feat.items():
    ct[k] = v


def score(s, ds):
    dr = np.array([np.prod(1 + s.loc[s.day == d, "ret"].values / 100) - 1 for d in ds]) * 100
    lg = np.log1p(dr / 100)
    return dict(n=len(s), strike=round(float((s.ret > 0).mean()) * 100, 1) if len(s) else None, comp=round(float(np.expm1(lg.sum())) * 100, 1),
                losing_days=int((dr < 0).sum()), worst=round(float(dr.min()), 1), wo_best_day=round(float(np.expm1(lg.sum() - lg.max())) * 100, 1),
                per_day=[round(float(x), 1) for x in dr])


e, l = ct[ct.day.isin(E)], ct[ct.day.isin(L_)]
res["conductor"] = dict(base_disc=score(e, E), base_test=score(l, L_), rows=[])
for k in feat:
    cuts = sorted({float(e[k].quantile(q)) for q in (0.2, 0.33, 0.5)} | {0.0})
    for side in ("above", "below"):
        for c in cuts:
            keep = lambda s: s[(s[k] > c) | s[k].isna()] if side == "above" else s[(s[k] < c) | s[k].isna()]
            res["conductor"]["rows"].append(dict(f=k, side=side, cut=round(c, 3), disc=score(keep(e), E), test=score(keep(l), L_)))
res["conductor"]["variants"] = len(res["conductor"]["rows"])
json.dump(res, open(os.path.join(HERE, "phaseB_wf_results.json"), "w"), indent=1)
print("done", len(res["lead"]), "lead cells,", res["conductor"]["variants"], "conductor variants")
