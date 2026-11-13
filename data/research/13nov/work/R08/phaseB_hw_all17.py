"""PHASE B (run after the 15:30 close only; same rules: py -3.13, lowprio, one run at a time, < 3 min each).
R08 heavyweights: the per-second study on every ds_v2 part, a few parts per run, then a summary.

  py -3.13 phaseB_hw_all17.py 2026-10-19 2026-10-19.p2 2026-10-19.p3 2026-10-19.p5 2026-10-21 2026-10-22
  py -3.13 phaseB_hw_all17.py 2026-10-23 2026-10-23.p2 2026-10-26 2026-10-27.p2 2026-10-27.p3 2026-10-28
  py -3.13 phaseB_hw_all17.py 2026-10-29.p3 2026-10-29.p4 2026-10-29.p5 2026-10-30 2026-11-02 2026-11-03
  py -3.13 phaseB_hw_all17.py 2026-11-04 2026-11-05 2026-11-06 2026-11-09 2026-11-11.p4
  py -3.13 phaseB_hw_all17.py --summary

Per part (no fitting, so no leakage): cross-correlation of the Nifty future's mid against the weighted cash and stock-
futures baskets at 5/10/30/60 s, the per-part OLS coefficients of the 10-s forward move on (own 10-s move, cash gap,
stock-futures gap) to check their stability, the FIXED pressure rule P = 0.1 own10 + 0.27 g10 + 0.1 gs10 at
10/30/60/120/300 s, weighted breadth thrusts, and P at every trade trigger of the trade table (pool books and all)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd, json, os, glob, time
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R08")
from s04_leadlag_lib import load, basket, breadth, dF, fwd
OUT = r"D:\ApexOptions\data\research\13nov\work\R08\phaseB"
os.makedirs(OUT, exist_ok=True)
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
T0 = time.time()


def one(p, T):
    D = load(p); F = D["F"]; w = D["w"]; t0 = D["t0"]; n = D["n"]
    r = {"part": p}
    xc = {}
    for S in (5, 10, 30, 60):
        fF = dF(F, S)[S::S]
        for nm, lp in (("cash", D["lc"]), ("sfut", D["ls"])):
            x = (basket(lp, w, S) * F)[S::S]
            for k in (-1, 0, 1):
                a, b = (fF[k:], x[:len(x) - k]) if k >= 0 else (fF[:len(fF) + k], x[-k:])
                m = np.isfinite(a) & np.isfinite(b)
                xc[f"{nm}_S{S}_k{k}"] = float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 20 else None
    r["xcorr"] = xc
    own10 = dF(F, 10); g10 = basket(D["lc"], w, 10) * F - own10; gs10 = basket(D["ls"], w, 10) * F - own10
    y10 = fwd(F, 10)
    A = np.c_[own10, g10, gs10][120::10]; yy = y10[120::10]
    m = np.isfinite(A).all(1) & np.isfinite(yy)
    if m.sum() > 200:
        r["ols10"] = [float(b) for b in np.linalg.lstsq(np.c_[np.ones(m.sum()), A[m]], yy[m], rcond=None)[0]]
    P = 0.1 * own10 + 0.27 * g10 + 0.1 * gs10
    for h in (10, 30, 60, 120, 300):
        y = fwd(F, h)
        on = np.isfinite(P) & np.isfinite(y) & (np.abs(P) >= 1.0)
        idx = np.where(on)[0][::5]
        s = np.sign(P[idx])
        r[f"P_h{h}"] = dict(cover=float(on.mean()), n=int(len(idx)), hit=float(np.mean(s * y[idx] > 0)) if len(idx) else None,
                            pts=float(np.mean(s * y[idx])) if len(idx) else None)
    b60 = breadth(D["lc"], w, 60)
    th, last = [], -10 ** 9
    f30, f60 = fwd(F, 30), fwd(F, 60)
    for i in range(90, n):
        if np.isfinite(b60[i]) and abs(b60[i]) >= 0.8 and i - last > 120 and np.isfinite(b60[i - 30]) and abs(b60[i - 30]) < 0.3:
            d = np.sign(b60[i]); last = i; th.append((f30[i] * d, f60[i] * d))
    th = np.array(th, float).reshape(-1, 2)
    r["thrust"] = dict(n=int(len(th)), f30=float(np.nanmean(th[:, 0])) if len(th) else None,
                       hit30=float(np.nanmean(th[:, 0] > 0)) if len(th) else None,
                       f60=float(np.nanmean(th[:, 1])) if len(th) else None)
    S = T[T.day == p[:10]].copy()
    i = (S.trigger_t.astype(float) - t0).round()
    ok = (i >= 0) & (i < n)
    ii = i.where(ok, 0).astype(int).values
    S["P_trig"] = np.where(ok, P[ii] * S.d.values, np.nan)
    S["g10_trig"] = np.where(ok, g10[ii] * S.d.values, np.nan)
    S = S[S.P_trig.notna()]
    S[["day", "book", "t_in", "ret_pct", "P_trig", "g10_trig"]].to_parquet(os.path.join(OUT, f"trig_{p}.parquet"))
    json.dump(r, open(os.path.join(OUT, f"part_{p}.json"), "w"), indent=1)
    print(p, "done", round(time.time() - T0, 1), flush=True)


def summary():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "part_*.json")))]
    rows = []
    for r in R:
        row = {"part": r["part"], "ols_own": (r.get("ols10") or [None] * 4)[1], "ols_g": (r.get("ols10") or [None] * 4)[2],
               "ols_gs": (r.get("ols10") or [None] * 4)[3], "lead_cash5": r["xcorr"].get("cash_S5_k1"),
               "lag_cash5": r["xcorr"].get("cash_S5_k-1"), "thrust_n": r["thrust"]["n"], "thrust_hit30": r["thrust"]["hit30"]}
        for h in (10, 30, 60, 120, 300):
            row[f"hit{h}"] = r[f"P_h{h}"]["hit"]; row[f"pts{h}"] = r[f"P_h{h}"]["pts"]
        rows.append(row)
    D = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(D.round(3).to_string())
    print("days with hit30 > 0.55:", int((D.hit30 > 0.55).sum()), "of", len(D))
    Tg = pd.concat([pd.read_parquet(f) for f in glob.glob(os.path.join(OUT, "trig_*.parquet"))])
    Tg["win"] = Tg.ret_pct > 0
    for name, sub in (("pool", Tg[Tg.book.isin(POOL)]), ("all", Tg)):
        for win, sel in (("early", sub.day <= "2026-11-04"), ("late", sub.day >= "2026-11-05")):
            s = sub[sel]
            b = pd.cut(s.P_trig, [-99, -1, -0.3, 0.3, 1, 99])
            print(name, win, s.assign(b=b).groupby("b", observed=True).agg(n=("win", "size"), sr=("win", "mean"),
                  ret=("ret_pct", "mean")).round(3).to_string())


if __name__ == "__main__":
    if sys.argv[1:] == ["--summary"]:
        summary()
    else:
        T = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet",
                            columns=["day", "book", "t_in", "trigger_t", "rr", "ret_pct"])
        T["d"] = np.where(T.rr == "CE", 1, -1)
        for p in sys.argv[1:]:
            one(p, T)
