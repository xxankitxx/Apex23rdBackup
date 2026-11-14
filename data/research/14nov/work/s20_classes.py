"""Run the ENGINE strategy classes (thr_sis, thr_hw, st15, c20_9y) second by second on recorded sessions through a
LiveDay filled from fastlab, and compare with what fastlab predicted. Also times one on_second call."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
from apex.engine.council import LiveDay, N_ROWS
import importlib
import fam
BOOKS = {"c20_9y": "c20_9y", "st15_c20_9y": "c20_9y_st15", "thr_sis": "thr_sis", "thr_hw": "thr_hw"}


def live_day(D):
    """a LiveDay with every row filled (the strategies only ever read rows <= i)."""
    L = LiveDay(D["day"], D["expiry"])
    K = D["K"]
    n = len(K)
    L.fwd[:] = D["fwd"]
    L.spot[:] = D["sis"][:, 2]
    L.fut[:] = D["fmid"]
    cols = []
    for j, k in enumerate(K):
        for c, rr in ((0, "CE"), (1, "PE")):
            L.col[(int(k), rr)] = len(cols)
            cols.append((j, c, float(k), rr))
    L.K = np.array([x[2] for x in cols]); L.rr = np.array([x[3] for x in cols])
    T = D["T"]
    for q, (j, c, k, rr) in enumerate(cols):
        bid = D["opt"][:, j, c, 0].astype(float); ask = D["opt"][:, j, c, 1].astype(float)
        L.bid[:, q] = FL._ffill0(bid); L.ask[:, q] = FL._ffill0(ask)
        mid = 0.5 * (bid + ask)
        L.mid[:, q] = FL._ffill0(mid); L.ltp[:, q] = L.mid[:, q]
        L.age[:, q] = np.where(np.isfinite(bid), 0.5, 9e9)
        call = c == 0
        with np.errstate(all="ignore"):
            iv = FL.iv_of(D["fwd"], k, T, mid, call)
            iv = FL._ffill0(iv)
            dl, gm, th = FL.greeks(D["fwd"], k, T, np.where(np.isfinite(iv), iv, 0.15), call)
        L.iv[:, q] = 100.0 * iv; L.delta[:, q] = dl; L.gamma[:, q] = gm; L.theta[:, q] = th
    L.bnf[:] = FL._ffill0(D["sis"][:, 0].astype(float)); L.fin[:] = FL._ffill0(D["sis"][:, 1].astype(float))
    with np.errstate(all="ignore"):
        L.hwl = np.log(FL._ffill0(D["hw"].astype(float))).astype(np.float32)
    L.hww = D["w"].astype(float)
    return L


def play(D, L, modname):
    """the adapter's loop in miniature: BUY fills at the ask of the next row, SELL at the bid of the next row."""
    s = importlib.import_module(f"apex.engine.council.{modname}").Strategy()
    pos = None; trades = []; pend = None; dt = []
    flat = (15 * 60) if L.dte0 else (15 * 60 + 20)
    for i in range(N_ROWS - 2):
        L.i = i
        if pend is not None:                                # the fill row: the strategy is not stepped (as the adapter)
            kind, a = pend; pend = None
            if kind == "BUY":
                k, rr, why = a
                j = L.col.get((int(k), rr))
                ask = L.ask[i, j] if j is not None else np.nan
                if np.isfinite(ask) and ask > 0:
                    pos = {"rr": rr, "strike": float(k), "j": j, "i_in": i, "entry": float(ask), "qty": 65, "peak_bid": float(L.bid[i, j]) if np.isfinite(L.bid[i, j]) else float(ask), "st": {}, "why": why}
            else:
                bid = L.bid[i, pos["j"]]
                trades.append(dict(day=D["day"], i_in=pos["i_in"], i_out=i, side=pos["rr"], K=pos["strike"], e=pos["entry"], ret=100 * (float(bid) / pos["entry"] - 1), why=a, tag=pos["why"]))
                pos = None
            continue
        if pos is not None:
            b = L.bid[i, pos["j"]]
            if np.isfinite(b):
                pos["peak_bid"] = max(pos["peak_bid"], float(b))
            if L.hm[i] >= flat:
                pend = ("SELL", "TIME (forced flat)"); continue
        t0 = time.perf_counter()
        act = s.on_second(i, L, pos)
        dt.append(time.perf_counter() - t0)
        if not act:
            continue
        if act[0] == "BUY" and pos is None:
            j = L.col.get((int(act[1]), act[2]))
            if j is not None and abs(L.delta[i, j]) >= 0.5:
                pend = ("BUY", (act[1], act[2], act[3] if len(act) > 3 else ""))
        elif act[0] == "SELL" and pos is not None:
            pend = ("SELL", act[1] if len(act) > 1 else "")
    return trades, float(np.mean(dt) * 1e6), float(np.quantile(dt, 0.99) * 1e6)


def one(day):
    D = FL.load_day(day)
    L = live_day(D)
    X = FL.features(D)
    out = {}
    for b, m in BOOKS.items():
        tr, mean_us, p99_us = play(D, L, m)
        out[b] = (tr, mean_us, p99_us)
    # fastlab's own prediction for the thrust books on this day
    pred = {}
    for nm, sig in (("thr_sis", fam.sig_sis(D, X, L=60, pts=8.0)), ("thr_hw", fam.sig_hw(D, X, L=60, pts=8.0, brd=0.5))):
        pred[nm] = FL.run(D, [s for s in sig if not X["gap"][s[0]]])
    return day, D["dte0"], out, pred


if __name__ == "__main__":
    days = sys.argv[1:] or ["2026-10-26", "2026-11-02", "2026-11-06", "2026-11-12", "2026-11-13", "2026-11-05", "2026-10-27"]
    t0 = time.time()
    rows = []; tim = []
    with ProcessPoolExecutor(max_workers=7) as ex:
        for day, dte0, out, pred in ex.map(one, days):
            for b, (tr, mu, p99) in out.items():
                comp = 100 * (np.prod([1 + t["ret"] / 100 for t in tr]) - 1) if tr else 0.0
                r = dict(day=day, expiry=dte0, book=b, trades=len(tr), wins=sum(t["ret"] > 0 for t in tr), day_pct=round(comp, 1), exits=" ".join(sorted({t["why"] for t in tr}))[:60])
                if b in pred:
                    p = pred[b]
                    r["fastlab_trades"] = len(p); r["fastlab_day_pct"] = round(100 * (np.prod([1 + t["ret"] / 100 for t in p]) - 1) if p else 0.0, 1)
                    r["same_entries"] = len({t["i_in"] for t in tr} & {t["i_in"] + 0 for t in p}) + len({t["i_in"] for t in tr} & {t["i_in"] + 1 for t in p}) + len({t["i_in"] for t in tr} & {t["i_in"] - 1 for t in p})
                rows.append(r); tim.append((b, mu, p99))
    pd.set_option("display.width", 300)
    print(pd.DataFrame(rows).to_string(index=False))
    Tm = pd.DataFrame(tim, columns=["book", "mean_us", "p99_us"]).groupby("book").mean().round(0)
    print("\none on_second call, microseconds:\n", Tm.to_string())
    print(round(time.time() - t0), "s")
