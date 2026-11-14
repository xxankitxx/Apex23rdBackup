"""Run every entry-family variant on every day (parallel by day), champion exits, one position per variant."""
import os, sys, time, json
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam
W = r"D:\ApexOptions\data\research\14nov\work"


def variants():
    V = {}
    for Wn, vm in ((300, 15.0), (600, 28.0), (1200, 40.0)):
        for pb in (0.33, 0.5):
            V[f"pb W{Wn} v{vm:.0f} pb{pb}"] = (fam.sig_pb, dict(W=Wn, vmin=vm, pb=pb, amax=max(300, int(0.75 * Wn)), rs=5.0 if Wn >= 600 else 3.0))
            for vz in (0.7, 1.0, 1.4):
                V[f"pb W{Wn} z{vz} pb{pb}"] = (fam.sig_pb, dict(W=Wn, vz=vz, pb=pb, amax=max(300, int(0.75 * Wn)), rs=5.0 if Wn >= 600 else 3.0))
    for Wn, vm in ((300, 15.0), (600, 28.0)):
        for e in (0.2, 0.35):
            V[f"pbT W{Wn} v{vm:.0f} trend3600>{e}"] = (fam.sig_pb, dict(W=Wn, vmin=vm, pb=0.5, amax=max(300, int(0.75 * Wn)), rs=3.0, trend=(3600, e)))
    for Wn, vm in ((600, 28.0), (1200, 40.0)):
        for e in (0.3, 0.45):
            V[f"flag W{Wn} v{vm:.0f} er{e}"] = (fam.sig_flag, dict(W=Wn, vmin=vm, er=e, amax=max(300, int(0.75 * Wn))))
        V[f"flag W{Wn} z1.0 er0.3"] = (fam.sig_flag, dict(W=Wn, vz=1.0, er=0.3, amax=max(300, int(0.75 * Wn))))
    for Wn, vm in ((600, 28.0), (1200, 40.0), (3600, 60.0)):
        for c in ("", "hw", "hw+sis", "nohw"):
            V[f"brk W{Wn} v{vm:.0f} {c or 'plain'}"] = (fam.sig_brk, dict(W=Wn, vmin=vm, confirm=c))
        for vz in (1.0, 1.4):
            for c in ("", "hw+sis"):
                V[f"brk W{Wn} z{vz} {c or 'plain'}"] = (fam.sig_brk, dict(W=Wn, vz=vz, confirm=c))
    for age in (0, 900, 1800, 3600):
        for buf in (0.0, 5.0):
            V[f"dayx age{age // 60} buf{buf:.0f}"] = (fam.sig_dayx, dict(age=age, buf=buf))
    for Wn in (1200, 3600):
        for tg in (0.8, 1.2):
            for buf in (2.0, 5.0):
                V[f"sqz W{Wn} tight{tg} buf{buf:.0f}"] = (fam.sig_sqz, dict(W=Wn, tight=tg, buf=buf))
    for L, ps in ((60, (8.0, 12.0, 18.0)), (300, (20.0, 30.0))):
        for p in ps:
            for b in (0.5, 0.8):
                V[f"hw L{L} {p:.0f}pts brd{b}"] = (fam.sig_hw, dict(L=L, pts=p, brd=b))
            V[f"hw L{L} {p:.0f}pts lead0.5"] = (fam.sig_hw, dict(L=L, pts=p, brd=0.5, lead=0.5))
    for L, ps in ((60, (8.0, 12.0, 18.0)), (300, (20.0, 30.0))):
        for p in ps:
            V[f"sis L{L} {p:.0f}pts"] = (fam.sig_sis, dict(L=L, pts=p))
            V[f"sis L{L} {p:.0f}pts lead0.5"] = (fam.sig_sis, dict(L=L, pts=p, lead=0.5))
    for L, ps in ((60, (6.0, 10.0)), (300, (15.0, 25.0))):
        for p in ps:
            V[f"all3 L{L} {p:.0f}pts"] = (fam.sig_all3, dict(L=L, pts=p))
    for buf in (2.0, 5.0):
        for m in (5.0, 15.0):
            V[f"vwap buf{buf:.0f} m{m:.0f}"] = (fam.sig_vwap, dict(buf=buf, m=m))
    for g in (10.0, 20.0):
        V[f"catch g{g:.0f} L300"] = (fam.sig_catch, dict(g=g, L=300))
    return V


def one(day):
    D = FL.load_day(day)
    X = FL.features(D)
    rows = []
    for name, (fn, kw) in variants().items():
        try:
            sig = fn(D, X, **kw)
        except Exception as e:
            rows.append(dict(variant=name, day=day, err=repr(e)))
            continue
        sig = [s for s in sig if not X["gap"][s[0]]]
        for t in FL.run(D, sig):
            t["variant"] = name
            rows.append(t)
    return rows


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "normal"
    t0 = time.time()
    ds = []
    for d in FL.days():
        z = np.load(os.path.join(FL.CACHE, d + ".npz"))
        if bool(z["dte0"]) == (which == "expiry"):
            ds.append(d)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, ds):
            rows += r
    T = pd.DataFrame(rows)
    if "err" in T:
        print("errors:", T[T.err.notna()].groupby("variant").err.first().to_dict() if T.err.notna().any() else "none")
        T = T[T.get("err").isna()] if "err" in T else T
    T.to_parquet(W + rf"\fam_{which}.parquet")
    print(which, "days", len(ds), "variants", T.variant.nunique(), "trades", len(T), "in", round(time.time() - t0, 1), "s")
