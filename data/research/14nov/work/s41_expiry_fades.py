"""Expiry days: do the FADES work where the breakout does not? Replica fade entries per second on the future, each
trade priced on its contract's real 1-second history (expiry ladder: 15-minute clock, one call a trade)."""
import os, sys, glob
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1s, hist1s
from s31_expiry_real import trade_real
from s39_fade_grid_1s import sig_orb
V = {"fade 20m 0.6": lambda D: lab1s.sig_fade(D, 20, 0.6), "fade 60m 0.7": lambda D: lab1s.sig_fade(D, 60, 0.7), "fade 20m 0.4": lambda D: lab1s.sig_fade(D, 20, 0.4),
     "fade 10m 0.3": lambda D: lab1s.sig_fade(D, 10, 0.3), "orb fade 15m": lambda D: sig_orb(D, 15, 150), "orb fade 60m": lambda D: sig_orb(D, 60, 255)}
have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
rows = []
cap = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
stop = False
for day in have:
    D = lab1s.session(day)
    if D is None or not D["dte0"] or stop:
        continue
    P = D["P"]
    for name, fn in V.items():
        free = P["t0"]
        for i, side, _ in sorted(fn(D)):
            if i < free or i > P["t1"]:
                continue
            if hist1s.CALLS["n"] >= cap:
                stop = True; break
            try:
                t = trade_real(D, i, side)
            except RuntimeError:
                stop = True; break
            if t is None:
                continue
            t.update(day=day, variant=name); rows.append(t)
            free = t["i_out"] + P["cool"]
    print(day, "calls", hist1s.CALLS["n"], flush=True)
T = pd.DataFrame(rows)
T.to_parquet(os.path.join(hist1s.OUT, "expiry_fades.parquet"))
comp = lambda r: 100 * (np.prod(1 + np.asarray(r) / 100) - 1)
out = []
h = sorted(T.day.unique()); mid = h[len(h) // 2]
for v, g in T.groupby("variant"):
    dd = g.groupby("day").ret.apply(comp); ds = g.groupby("day").ret.sum()
    a, b = g[g.day < mid], g[g.day >= mid]
    out.append(dict(variant=v, sessions=g.day.nunique(), trades=len(g), winners=round(100 * (g.ret > 0).mean()), per_trade=round(g.ret.mean(), 2), t=round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1),
                    days_up=f"{int((dd > 0).sum())}/{len(dd)}", median_day=round(dd.median(), 1), worst=round(dd.min()), best=round(dd.max()), older_half=round(a.ret.mean(), 2), newer_half=round(b.ret.mean(), 2),
                    ce=round(g[g.side == "CE"].ret.mean(), 2), pe=round(g[g.side == "PE"].ret.mean(), 2)))
pd.set_option("display.width", 230)
print(pd.DataFrame(out).to_string(index=False))
