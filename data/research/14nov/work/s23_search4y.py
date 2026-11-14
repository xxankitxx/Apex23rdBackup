"""The four-year search: every entry family on 970+ sessions, model option, champion ladder; found on sessions before
2025, judged on 2025-2026. One position at a time per variant."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import lab1, h4


def variants():
    V = []
    for W in (10, 20, 30, 45):
        for pb in (0.4, 0.5):
            V.append((f"pullback W{W} pb{pb}", "pb", dict(W=W, pb=pb)))
    for W in (10, 20, 45, 90):
        for z in (0.6, 1.0, 1.5):
            V.append((f"breakout W{W} z{z}", "brk", dict(W=W, z=z)))
    for age in (30, 60, 120):
        V.append((f"day high/low break, stood {age}m", "dayx", dict(age=age)))
    for n in (15, 30, 60):
        V.append((f"opening range {n}m break", "orb", dict(n=n)))
        V.append((f"opening range {n}m FADE", "orb", dict(n=n, fade=True)))
    for z in (0.3, 0.6):
        V.append((f"gap {z} sigma: go", "gap", dict(z=z, go=True)))
        V.append((f"gap {z} sigma: fade", "gap", dict(z=z, go=False)))
    for b, lab in ((30, "09:45"), (60, "10:15"), (105, "11:00"), (195, "12:30"), (255, "13:30"), (300, "14:15")):
        V.append((f"with the day's move at {lab}", "trend_at", dict(b=b, z=0.3)))
        V.append((f"against the day's move at {lab}", "trend_at", dict(b=b, z=0.3, fade=True)))
    V.append(("VWAP cross with momentum", "vwap", {}))
    for z in (0.4, 0.7):
        V.append((f"back to VWAP from {z} sigma", "vwap", dict(revert=True, z=z)))
    for q in (0.10, 0.18):
        V.append((f"squeeze {q} sigma, 30m", "squeeze", dict(W=30, q=q)))
    for W, z in ((20, 0.4), (20, 0.6), (60, 0.7), (60, 1.0)):
        V.append((f"fade a {W}m move of {z} sigma", "fade", dict(W=W, z=z)))
    for x in (3.0, 5.0):
        V.append((f"volume burst x{x:.0f}", "volbrk", dict(x=x)))
    V.append(("previous day's high/low taken out", "pdx", {}))
    V.append(("previous day's high/low: FADE", "pdx", dict(fade=True)))
    V.append(("after a narrow day: 30m range break", "nr", {}))
    V.append(("after a wide day: fade the 30m range break", "wide", {}))
    V.append(("after a wide day: go with the 30m range break", "wide", dict(fade=False)))
    V.append(("EMA 9/21 cross with the hour's slope", "ema", {}))
    V.append(("new day extreme after 13:30: go", "lastx", {}))
    V.append(("new day extreme after 13:30: FADE", "lastx", dict(fade=True)))
    V.append(("blind, both sides, six times a day", "blind", dict(bars=(30, 75, 135, 195, 255, 300))))
    return V


def work(chunk):
    ALL = h4.load()
    rows = []
    for name, f, p in chunk:
        for D in ALL:
            if D["dte0"]:
                continue
            try:
                sig = h4.fam(D, f, **p)
            except Exception as e:
                rows.append(dict(variant=name, day=D["day"], err=repr(e))); break
            for t in lab1.run(D, sig, model=True):
                t["variant"] = name
                rows.append(t)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    if not os.path.exists(h4.PKL) or "--rebuild" in sys.argv:
        print("built", h4.build(), "sessions")
    V = variants()
    chunks = [V[i::8] for i in range(8)]
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(work, chunks):
            rows += r
    T = pd.DataFrame(rows)
    if "err" in T and T.err.notna().any():
        print("errors:", T[T.err.notna()].groupby("variant").err.first().to_dict()); T = T[T.err.isna()]
    T.to_parquet(os.path.join(lab1.W, "search4y.parquet"))
    print(len(V), "variants", len(T), "trades", round(time.time() - t0), "s")
    T["win_"] = T.ret > 0
    out = []
    for v, g in T.groupby("variant"):
        r = dict(variant=v)
        for tag, s in (("D", g[g.day < h4.SPLIT]), ("T", g[g.day >= h4.SPLIT])):
            dd = s.groupby("day").ret.sum()
            t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 5 and dd.std(ddof=1) > 0 else np.nan
            r[f"{tag}_n"] = len(s); r[f"{tag}_win"] = round(100 * s.win_.mean(), 1) if len(s) else np.nan; r[f"{tag}_mean"] = round(s.ret.mean(), 2) if len(s) else np.nan
            r[f"{tag}_t"] = round(t, 1); r[f"{tag}_ce"] = round(s[s.side == "CE"].ret.mean(), 2); r[f"{tag}_pe"] = round(s[s.side == "PE"].ret.mean(), 2)
        yy = g.assign(y=g.day.str[:4]).groupby("y").ret.mean()
        r["years_pos"] = f"{int((yy > 0).sum())}/{len(yy)}"
        out.append(r)
    R = pd.DataFrame(out)
    R["score"] = np.minimum(R.D_t.fillna(-9), R.T_t.fillna(-9))
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 48)
    print("D = sessions before 2025 (found on), T = 2025 and 2026 (judged on); mean = % per trade, t = day-clustered")
    print(R.sort_values("score", ascending=False).drop(columns=["score"]).to_string(index=False))
