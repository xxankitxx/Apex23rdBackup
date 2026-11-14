"""Is the seconds-scale lead of the heavyweights / sisters / order book TRADEABLE in the option, after the spread?
For every second: buy the at-the-money option at the ASK one second later, sell at the BID h seconds after that."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
N = FL.N
HZ = (5, 10, 20, 30, 60, 120, 300)
W = r"D:\ApexOptions\data\research\14nov\work"


def one(day):
    D = FL.load_day(day)
    X = FL.features(D)
    K = D["K"].astype(float); fw = D["fwd"]
    r = np.arange(N)
    ok = np.isfinite(fw)
    f0 = np.where(ok, fw, K[len(K) // 2])
    jc = np.clip(np.searchsorted(K, f0 - 3.0, side="right") - 1, 0, len(K) - 1)      # call: the strike just below the forward
    jp = np.clip(np.searchsorted(K, f0 + 3.0, side="left"), 0, len(K) - 1)           # put: the strike just above
    out = dict(day=np.full(N, day), i=r, dte0=np.full(N, D["dte0"]))
    for nm in ("nf10", "hw_gap10", "sf_gap10", "sis_gap10", "hw10", "bn10", "fin10", "sfb10", "imb10", "imb60", "nf60", "hw_gap60", "sis_gap60", "mom300", "rv300", "em15", "gap", "iv"):
        out[nm] = X[nm]
    for c, j, tag in ((0, jc, "c"), (1, jp, "p")):
        ask = np.full(N, np.nan); ask[:-1] = D["opt"][r[1:], j[:-1], c, 1]
        bid0 = np.full(N, np.nan); bid0[:-1] = D["opt"][r[1:], j[:-1], c, 0]
        out[f"ask_{tag}"] = ask
        out[f"spr_{tag}"] = 100 * (ask - bid0) / ask
        for h in HZ:
            b = np.full(N, np.nan)
            b[:-(h + 1)] = D["opt"][r[h + 1:], j[:-(h + 1)], c, 0]
            out[f"r{h}_{tag}"] = 100 * (b / ask - 1)
    df = pd.DataFrame(out)
    df = df[(df.i >= 300) & (df.i <= 360 * 60) & (df.gap == 0) & ok]
    return df


if __name__ == "__main__":
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=8) as ex:
        M = pd.concat(list(ex.map(one, FL.days())), ignore_index=True)
    M.to_parquet(W + r"\micro.parquet")
    print("rows", len(M), "in", round(time.time() - t0, 1), "s; median spread % call", round(M.spr_c.median(), 3), "put", round(M.spr_p.median(), 3))
    # R08's fixed pressure rule and variants, in Nifty points
    M["P_hw"] = 0.1 * M.nf10 + 0.27 * M.hw_gap10 + 0.1 * M.sf_gap10
    M["P_sis"] = M.sis_gap10
    M["P_all"] = 0.1 * M.nf10 + 0.27 * M.hw_gap10 + 0.1 * M.sf_gap10 + 0.2 * M.sis_gap10
    M["P_sf"] = M.sf_gap10
    M["P_own"] = M.nf10
    M["P_imb"] = M.imb10
    print("no signal at all (cost of crossing the spread): " + "  ".join(f"{h}s {0.5 * (M[f'r{h}_c'].mean() + M[f'r{h}_p'].mean()):+.2f}%" for h in HZ))
    for sig in ("P_hw", "P_sis", "P_all", "P_sf", "P_own", "P_imb"):
        s = M[sig]
        print(f"\n== {sig} ==")
        for q in (0.95, 0.98, 0.995):
            th = s.abs().quantile(q)
            up = M[s >= th]; dn = M[s <= -th]
            line = f"  top {100 * (1 - q):.1f}% (|x| >= {th:.2f}), {len(up) + len(dn)} seconds, {(len(up) + len(dn)) / M.day.nunique() / 60:.0f} min/day:"
            for h in HZ:
                rr = np.r_[up[f"r{h}_c"].to_numpy(), dn[f"r{h}_p"].to_numpy()]
                rr = rr[np.isfinite(rr)]
                line += f"  {h}s {rr.mean():+.2f}% ({100 * (rr > 0).mean():.0f}%)"
            print(line)
            # per-day stability at 30 s and 60 s
            dd = []
            for d, g in M[(s.abs() >= th)].groupby("day"):
                rr = np.where(g[sig] > 0, g["r60_c"], g["r60_p"])
                dd.append(np.nanmean(rr))
            print(f"      60 s result by day: positive on {int((np.array(dd) > 0).sum())} of {len(dd)} days; worst day {min(dd):+.2f}%, best {max(dd):+.2f}%")
