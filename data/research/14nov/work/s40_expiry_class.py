"""Expiry days with the REAL champion class: stepped per second on a model chain (for the picker's greeks and its
vetoes), but every contract it buys is repriced on that contract's own 1-second broker history for its 15-minute life
(one call a trade), so the fill and every exit decision use real traded prices.

    py -3.13 s40_expiry_class.py check        the 4 recorded expiry days against the same class on tape quotes
    py -3.13 s40_expiry_class.py run [cap]    every downloaded expiry session
"""
import os, sys, glob, importlib
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1s, hist1s
from s32_real_classes import model_live, levels_file
N = FL.N
HALF = 0.0011


def play_real(D, L, council="c20_9x"):
    from apex.engine.council import c20_8x
    c20_8x.LEVELS_PATH = levels_file()
    s = importlib.import_module(f"apex.engine.council.{council}").Strategy()
    pos = None; pend = None; trades = []
    flat = 15 * 60
    for i in range(N - 2):
        L.i = i
        if pend is not None:
            kind, a = pend; pend = None
            if kind == "BUY":
                k, rr, why = a
                j = L.col.get((int(k), rr))
                if j is not None:
                    px = hist1s.fetch_window(D["day"], D["expiry"], "call" if rr == "CE" else "put", int(k), int(i - 1), int(min(i - 1 + 899, N - 1)))
                    if px is None:
                        raise RuntimeError("budget")
                    w = np.isfinite(px)
                    if w[i:i + 30].any():
                        if not w[i]:                                   # no trade in the fill second: the first print after it
                            nx = i + int(np.flatnonzero(w[i:i + 30])[0]); px[i:nx] = px[nx]; w = np.isfinite(px)
                        L.bid[w, j] = (px[w] * (1 - HALF)).astype(np.float32); L.ask[w, j] = (px[w] * (1 + HALF)).astype(np.float32)
                        last = int(np.flatnonzero(w)[-1])
                        if last + 1 < N:                               # after the fetched window: carry its last price
                            L.bid[last + 1:, j] = L.bid[last, j]; L.ask[last + 1:, j] = L.ask[last, j]
                        pos = {"rr": rr, "strike": float(k), "j": j, "i_in": i, "entry": float(L.ask[i, j]), "qty": 65, "peak_bid": float(L.bid[i, j]), "st": {}, "why": why}
            else:
                bid = float(L.bid[i, pos["j"]])
                trades.append(dict(day=D["day"], i_in=pos["i_in"], i_out=i, side=pos["rr"], K=pos["strike"], e=pos["entry"], ret=100.0 * (bid / pos["entry"] - 1.0), why=a, tag=pos["why"]))
                pos = None
            continue
        if pos is not None:
            b = L.bid[i, pos["j"]]
            if np.isfinite(b):
                pos["peak_bid"] = max(pos["peak_bid"], float(b))
            if L.hm[i] >= flat:
                pend = ("SELL", "TIME (forced flat)"); continue
        act = s.on_second(i, L, pos)
        if not act:
            continue
        if act[0] == "BUY" and pos is None:
            j = L.col.get((int(act[1]), act[2]))
            if j is not None and abs(L.delta[i, j]) >= 0.5:
                pend = ("BUY", (act[1], act[2], act[3] if len(act) > 3 else ""))
        elif act[0] == "SELL" and pos is not None:
            pend = ("SELL", act[1] if len(act) > 1 else "")
    return trades


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    comp = lambda tr: 100 * (np.prod([1 + t["ret"] / 100 for t in tr]) - 1) if tr else 0.0
    if mode == "check":
        rows = []
        for day in FL.days():
            F = FL.load_day(day)
            if not F["dte0"]:
                continue
            tape = FL.play(F, FL.live_day(F), "c20_9x")
            D = lab1s.session(day, fwd=F["fwd"].copy())
            real = play_real(D, model_live(D))
            rows.append(dict(day=day, tape_n=len(tape), tape_win=sum(t["ret"] > 0 for t in tape), tape_mean=np.mean([t["ret"] for t in tape]) if tape else np.nan, tape_day=comp(tape),
                             hybrid_n=len(real), hybrid_win=sum(t["ret"] > 0 for t in real), hybrid_mean=np.mean([t["ret"] for t in real]) if real else np.nan, hybrid_day=comp(real)))
            print(pd.DataFrame(rows[-1:]).round(1).to_string(index=False, header=len(rows) == 1), flush=True)
        R = pd.DataFrame(rows)
        print(f"class on tape quotes: {int(R.tape_n.sum())} trades, {100 * R.tape_win.sum() / R.tape_n.sum():.0f} % winners | class on model chain + real option seconds: {int(R.hybrid_n.sum())} trades, "
              f"{100 * R.hybrid_win.sum() / R.hybrid_n.sum():.0f} % winners | day-result correlation {np.corrcoef(R.tape_day, R.hybrid_day)[0, 1]:.2f}; calls {hist1s.CALLS['n']}")
    else:
        cap = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
        have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
        rows = []
        for day in have:
            D = lab1s.session(day)
            if D is None or not D["dte0"]:
                continue
            if hist1s.CALLS["n"] >= cap:
                print("call cap reached"); break
            try:
                tr = play_real(D, model_live(D))
            except RuntimeError as e:
                print("stopped:", e); break
            rows += tr
            print(day, "trades", len(tr), "winners", sum(t["ret"] > 0 for t in tr), "day %", round(comp(tr), 1), "calls", hist1s.CALLS["n"], flush=True)
        T = pd.DataFrame(rows)
        if len(T):
            T.to_parquet(os.path.join(hist1s.OUT, "expiry_class.parquet"))
            dd = T.groupby("day").apply(lambda d: comp(d.to_dict("records")))
            print(f"expiry sessions {T.day.nunique()}: trades {len(T)}, winners {100 * (T.ret > 0).mean():.0f} %, per trade {T.ret.mean():+.2f} %, days up {int((dd > 0).sum())}/{len(dd)}, median day {dd.median():+.1f} %, worst {dd.min():+.0f} %, best {dd.max():+.0f} %")
