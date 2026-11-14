"""Expiry days with REAL option seconds from the broker: the champion's expiry breakout fired per second on the
future, each trade priced on that contract's own 1-second history (one call a trade: 15 minutes is its whole clock).

    py -3.13 s31_expiry_real.py check            the 4 recorded expiry days: tape quotes against broker seconds
    py -3.13 s31_expiry_real.py run [max_calls]  every downloaded expiry session
"""
import os, sys, glob
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1s, hist1s
N = FL.N
HALF = 0.0011


def strike_for(F, side):
    """one strike in the money, a second one when the first is under 25 points in (the champion wants delta 0.65)."""
    if side == "CE":
        k = np.floor((F - 3.0) / 50.0) * 50.0
        return k - 50.0 if F - k < 25.0 else k
    k = np.ceil((F + 3.0) / 50.0) * 50.0
    return k + 50.0 if k - F < 25.0 else k


def trade_real(D, i, side):
    F = D["fwd"][i]
    if not np.isfinite(F):
        return None
    K = float(strike_for(F, side))
    px = hist1s.fetch_window(D["day"], D["expiry"], "call" if side == "CE" else "put", K, int(i), int(min(i + 899, N - 1)))
    if px is None:
        raise RuntimeError("budget")
    if not np.isfinite(px[i + 1:i + 30]).any():
        return None
    c = 0 if side == "CE" else 1
    opt = np.full((N, 1, 2, 2), np.nan, np.float32)
    opt[:, 0, c, 0] = px * (1 - HALF); opt[:, 0, c, 1] = px * (1 + HALF)
    a = i + 1
    if not np.isfinite(opt[a, 0, c, 1]):                           # no trade that second yet: the first print after it
        nx = np.flatnonzero(np.isfinite(px[a:a + 30]))
        if not len(nx):
            return None
        opt[a:a + nx[0], 0, c, :] = opt[a + nx[0], 0, c, :]
    Dm = FL.Day(dict(D)); Dm["opt"] = opt; Dm["K"] = np.array([K])
    return FL.exit_ladder(Dm, i, side, 0)


def play_real(D):
    X = lab1s.feats(D)
    P = D["P"]; out = []; free = P["t0"]
    for i, side, _ in sorted(lab1s.sig_exp(D, X)):
        if i < free or i < P["t0"] or i > P["t1"]:
            continue
        t = trade_real(D, i, side)
        if t is None:
            continue
        t["day"] = D["day"]; out.append(t)
        free = t["i_out"] + P["cool"]
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    comp = lambda tr: 100 * (np.prod([1 + t["ret"] / 100 for t in tr]) - 1) if tr else 0.0
    if mode == "check":
        rows = []
        for day in FL.days():
            F = FL.load_day(day)
            if not F["dte0"]:
                continue
            D = lab1s.session(day, fwd=F["fwd"].copy())
            X = lab1s.feats(D)
            tape = FL.run(F, lab1s.sig_exp(D, X))
            real = play_real(D)
            rows.append(dict(day=day, tape_n=len(tape), tape_win=sum(t["ret"] > 0 for t in tape), tape_mean=np.mean([t["ret"] for t in tape]), tape_day=comp(tape),
                             broker_n=len(real), broker_win=sum(t["ret"] > 0 for t in real), broker_mean=np.mean([t["ret"] for t in real]) if real else np.nan, broker_day=comp(real)))
            print(pd.DataFrame(rows[-1:]).round(1).to_string(index=False, header=len(rows) == 1), flush=True)
        R = pd.DataFrame(rows)
        print(f"tape quotes: {int(R.tape_n.sum())} trades, {100 * R.tape_win.sum() / R.tape_n.sum():.0f} % winners | broker seconds: {int(R.broker_n.sum())} trades, {100 * R.broker_win.sum() / R.broker_n.sum():.0f} % winners"
              f" | day-result correlation {np.corrcoef(R.tape_day, R.broker_day)[0, 1]:.2f}; calls {hist1s.CALLS['n']}")
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
                tr = play_real(D)
            except RuntimeError as e:
                print("stopped:", e); break
            rows += tr
            print(day, "trades", len(tr), "winners", sum(t["ret"] > 0 for t in tr), "day %", round(comp(tr), 1), "calls", hist1s.CALLS["n"], flush=True)
        T = pd.DataFrame(rows)
        if len(T):
            T.to_parquet(os.path.join(hist1s.OUT, "expiry_real.parquet"))
            dd = T.groupby("day").apply(lambda d: comp(d.to_dict("records")))
            print(f"expiry sessions {T.day.nunique()}: trades {len(T)}, winners {100 * (T.ret > 0).mean():.0f} %, per trade {T.ret.mean():+.2f} %, days up {int((dd > 0).sum())}/{len(dd)}, median day {dd.median():+.1f} %, worst {dd.min():+.0f} %, best {dd.max():+.0f} %")
