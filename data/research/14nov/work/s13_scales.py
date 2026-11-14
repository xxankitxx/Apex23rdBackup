"""The pullback structure at other time-scales: is there a plateau, on both sides, in both halves, on the untouched days?"""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam
W_ = r"D:\ApexOptions\data\research\14nov\work"
HOLD = ("2026-11-12", "2026-11-13")


def variants():
    V = {}
    for Wn in (300, 450, 600, 750, 900, 1200, 1800):
        vm = round(40.0 * np.sqrt(Wn / 1200.0), 1)
        for pb in (0.4, 0.5, 0.6):
            for am in (0.75,):
                V[f"W{Wn} v{vm} pb{pb}"] = dict(W=Wn, vmin=vm, pb=pb, amax=max(300, int(am * Wn)), rs=5.0)
        V[f"W{Wn} v{round(vm * 0.75, 1)} pb0.5"] = dict(W=Wn, vmin=round(vm * 0.75, 1), pb=0.5, amax=max(300, int(0.75 * Wn)), rs=5.0)
        V[f"W{Wn} v{round(vm * 1.3, 1)} pb0.5"] = dict(W=Wn, vmin=round(vm * 1.3, 1), pb=0.5, amax=max(300, int(0.75 * Wn)), rs=5.0)
    return V


def one(day):
    D = FL.load_day(day)
    if D["dte0"]:
        return []
    X = FL.features(D)
    rows = []
    for name, kw in variants().items():
        sig = [s for s in fam.sig_pb(D, X, **kw) if not X["gap"][s[0]]]
        for t in FL.run(D, sig):
            t["variant"] = name
            rows.append(t)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, FL.days()):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(W_ + r"\scales.parquet")
    days = sorted(d for d in T.day.unique() if d not in HOLD)
    half = {d: (0 if k < len(days) / 2 else 1) for k, d in enumerate(days)}
    out = []
    for v, g0 in T.groupby("variant"):
        g = g0[~g0.day.isin(HOLD)]; hd = g0[g0.day.isin(HOLD)]
        a, b = g[g.day.map(half) == 0], g[g.day.map(half) == 1]
        dd = g.groupby("day").ret.sum().reindex(days).fillna(0)
        ce, pe = g[g.side == "CE"], g[g.side == "PE"]
        rs = np.random.default_rng(0)
        bs = [g.ret.sample(len(g), replace=True, random_state=int(rs.integers(1 << 30))).mean() for _ in range(400)]
        out.append(dict(variant=v, W=int(v.split()[0][1:]), n=len(g), win=round(100 * (g.ret > 0).mean()), mean=round(g.ret.mean(), 1), lo90=round(np.quantile(bs, 0.05), 1),
                        sum=round(g.ret.sum()), mean1=round(a.ret.mean(), 1), mean2=round(b.ret.mean(), 1), days_pos=int((dd > 0).sum()), days_neg=int((dd < 0).sum()),
                        worst=round(dd.min()), ce=round(ce.ret.mean(), 1), pe=round(pe.ret.mean(), 1), pe_n=len(pe), top3_share=round(100 * g.ret.nlargest(3).sum() / max(g.ret.sum(), 1e-9)),
                        hold_n=len(hd), hold_win=int((hd.ret > 0).sum()), hold_sum=round(hd.ret.sum(), 1)))
    R = pd.DataFrame(out).sort_values(["W", "variant"])
    pd.set_option("display.width", 300)
    print(f"normal days {len(days)} (12 and 13 Nov held out), {round(time.time() - t0)} s")
    print(R.drop(columns=["W"]).to_string(index=False))
