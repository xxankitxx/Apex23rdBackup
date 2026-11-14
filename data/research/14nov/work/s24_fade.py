"""The fade family in detail: a grid of window x stretch (plateau or spike?), by year, by sessions to expiry, by time
of day; real option bars against the model on the sessions that have them."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import lab1, h4
GRID = [(W, z) for W in (10, 15, 20, 30, 45, 60) for z in (0.3, 0.4, 0.5, 0.6, 0.8, 1.0)]


def attach_real(ALL):
    opt = lab1._tab("opt")
    OG = {d: g for d, g in opt.groupby("day")}
    grid_t = pd.date_range("2000-01-01 09:15:00", periods=lab1.NB, freq="1min").strftime("%H:%M:%S")
    for D in ALL:
        if D["day"] in OG:
            q = OG[D["day"]]; q = q[q.expiry == q.expiry.min()]
            o = {}
            for (k, r), x in q.groupby(["strike", "right"]):
                x = x.drop_duplicates("ts"); x = x.set_index(x.ts.str[11:]).reindex(grid_t)
                o[(float(k), "CE" if r == "call" else "PE")] = np.stack([x.o.to_numpy(float), x.h.to_numpy(float), x.l.to_numpy(float), x.c.ffill().to_numpy(float)], 1)
            D["opt"] = o


def work(chunk):
    ALL = h4.load()
    real = chunk and chunk[0][0] in ((20, 0.6), (20, 0.4), (60, 0.8), (30, 0.6))
    attach_real(ALL)
    rows = []
    for W, z in chunk:
        for D in ALL:
            if D["dte0"]:
                continue
            sig = h4.fam(D, "fade", W=W, z=z)
            for t in lab1.run(D, sig, model=True):
                t.update(W=W, z=z, real=False); rows.append(t)
            if D["opt"] and (W, z) in ((20, 0.6), (20, 0.4), (60, 0.8), (30, 0.6), (20, 0.5), (45, 0.6)):
                for t in lab1.run(D, sig, model=False):
                    t.update(W=W, z=z, real=True); rows.append(t)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(work, [GRID[i::8] for i in range(8)]):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(lab1.W, "fade.parquet"))
    M = T[~T.real]
    pd.set_option("display.width", 250)
    print(len(T), "trades", round(time.time() - t0), "s")
    for tag, G in (("FOUND ON (before 2025)", M[M.day < h4.SPLIT]), ("JUDGED ON (2025-2026)", M[M.day >= h4.SPLIT])):
        print(f"\n{tag}: mean % per trade (rows: window in minutes, columns: stretch in day-sigmas)")
        print(G.pivot_table(index="W", columns="z", values="ret", aggfunc="mean").round(2).to_string())
        print("trades:"); print(G.pivot_table(index="W", columns="z", values="ret", aggfunc="size").to_string())
        print("winners %:"); print((G.assign(w=G.ret > 0).pivot_table(index="W", columns="z", values="w", aggfunc="mean") * 100).round(0).to_string())
    g = M[(M.W == 20) & (M.z == 0.6)]
    def tab(G, by):
        out = []
        for k, s in G.groupby(by):
            dd = s.groupby("day").ret.sum()
            out.append(dict(key=k, sessions=len(dd), trades=len(s), win=round(100 * (s.ret > 0).mean()), mean=round(s.ret.mean(), 2), ce=round(s[s.side == "CE"].ret.mean(), 2), pe=round(s[s.side == "PE"].ret.mean(), 2),
                            t=round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))), 1) if len(dd) > 3 else None, worst_day=round(dd.min()), best_day=round(dd.max())))
        return pd.DataFrame(out).to_string(index=False)
    print("\nfade 20m 0.6 sigma by year:\n" + tab(g.assign(y=g.day.str[:4]), "y"))
    print("\nby sessions to expiry:\n" + tab(g.assign(d=np.where(g.dte == 1, "1", np.where(g.dte == 2, "2", "3+"))), "d"))
    print("\nby entry time:\n" + tab(g.assign(tb=pd.cut(g.b_in, [0, 45, 105, 195, 285, 400], labels=["09:15-10:00", "10:00-11:00", "11:00-12:30", "12:30-14:00", "14:00-15:00"])), "tb"))
    print("\nby exit reason:\n" + g.groupby("why").ret.agg(["size", "mean"]).round(2).to_string())
    print("\nhold minutes: median", (g.b_out - g.b_in).median(), "| winners", (g[g.ret > 0].b_out - g[g.ret > 0].b_in).median(), "| losers", (g[g.ret <= 0].b_out - g[g.ret <= 0].b_in).median())
    print("\nREAL option bars against the model, same sessions (Nov 2024 to Jun 2025):")
    R = T[T.real]
    for (W, z), a in R.groupby(["W", "z"]):
        b = M[(M.W == W) & (M.z == z) & M.day.isin(a.day.unique())]
        da = a.groupby("day").ret.sum(); db = b.groupby("day").ret.sum().reindex(da.index).fillna(0)
        print(f"  fade {W}m {z}: real {len(a)} trades win {100 * (a.ret > 0).mean():.0f} % mean {a.ret.mean():+.2f} (CE {a[a.side == 'CE'].ret.mean():+.2f}, PE {a[a.side == 'PE'].ret.mean():+.2f}) | model {len(b)} trades win {100 * (b.ret > 0).mean():.0f} % mean {b.ret.mean():+.2f} | day corr {np.corrcoef(da, db)[0, 1]:.2f}")
