import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05 analysis 5: the thesis field 'held_net' (books holding the trade's side minus books holding the other side, the
engine's weather5.hold_photo item 126) rebuilt for the c20 trades from the trade table (every book's t_in / t_out / rr),
and the exit-now rule 'at mark m, held_net <= x -> sell at the bid' on the per-second paths of 5, 6, 9 Nov
(paths_pilot.pkl from analysis4; no new ds_v2 reads). Also the same rebuilt field on the non-council trades checked
against the engine's own h<m>_thesis_held_* (validation of the rebuild)."""
import os, pickle, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
df = pd.read_pickle(os.path.join(W, "tr.pkl"))
paths = pickle.load(open(os.path.join(W, "paths_pilot.pkl"), "rb"))
iv = df[["day", "book", "t_in", "t_out", "rr"]].copy()
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
PRI = {b: i for i, b in enumerate(POOL)}


def held(day, T, rr, me):
    g = IV[day]
    on = (g.t_in.values <= T) & (g.t_out.values > T) & (g.book.values != me)
    w = int((on & (g.rr.values == rr)).sum())
    a = int((on & (g.rr.values != rr)).sum())
    return w, a


IV = {d: g for d, g in iv.groupby("day")}
# validation on non-council trades with marks (the engine counts every other book holding a position)
chk = df[df.book.str.startswith(("t28", "spot")) & df.h300_thesis_held_with_n.notna()].sample(400, random_state=1)
dv = []
for _, r in chk.iterrows():
    w, a = held(r.day, r.t_in + 300, r.rr, r.book)
    dv.append((w - float(r.h300_thesis_held_with_n), a - float(r.h300_thesis_held_against_n)))
dv = np.array(dv)
print("rebuild check (rebuilt - engine) with: median", np.median(dv[:, 0]), "mean abs", np.abs(dv[:, 0]).mean(),
      "| against: median", np.median(dv[:, 1]), "mean abs", np.abs(dv[:, 1]).mean(), flush=True)
c20 = df.loc[list(paths), ["day", "book", "t_in", "t_out", "trigger_t", "rr", "entry", "ret_pct", "reason"]].copy()
c20["trig"] = c20.trigger_t.fillna(c20.t_in)
c20["pri"] = c20.book.map(PRI).fillna(99)


def account(tr, ret_col, tout_col):
    cap, hd, out = 100000.0, None, []
    for _, t in tr.sort_values(["trig", "pri"]).iterrows():
        if hd is not None:
            h_trig, h_out, h_book = hd
            if t.trig <= h_trig or t.trig < h_out or (t.trig == h_out and t.book == h_book):
                continue
            hd = None
        lots = int(cap // (t.entry * 65))
        if lots < 1:
            continue
        cap += t.entry * (t[ret_col] / 100.0) * lots * 65
        hd = (t.trig, t[tout_col], t.book)
        out.append((t.book, t[ret_col], cap))
    return out


pool_m = c20.book.isin(PRI).values
rows = []
for m in (60, 120, 300, 600, 900):
    hn, alt, ok = [], [], []
    for idx, r in c20.iterrows():
        tt, b, k1 = paths[idx]
        k = int(np.searchsorted(tt, m))
        if k >= k1 or not np.isfinite(b[k]):
            hn.append(np.nan); alt.append(np.nan); ok.append(False); continue
        w, a = held(r.day, r.t_in + m, r.rr, r.book)
        hn.append(w - a); alt.append(100 * (b[k] / r.entry - 1)); ok.append(True)
    hn, alt, ok = np.array(hn, float), np.array(alt, float), np.array(ok)
    rest = c20.ret_pct.values - alt
    print(f"m{m}: held at mark {ok.sum()}; held_net quartiles {np.nanquantile(hn, [.1, .25, .5, .75, .9]).round(1)}", flush=True)
    for x in (-5, -1, 0, 2, 5):
        f = ok & (hn <= x)
        if f.sum() == 0:
            continue
        r2 = np.where(f, alt, c20.ret_pct.values)
        dl = r2 - c20.ret_pct.values
        g = c20.assign(ret2=r2, tout2=np.where(f, c20.t_in + m, c20.t_out))
        acc = {d: account(gd, "ret2", "tout2") for d, gd in g[pool_m].groupby("day")}
        per = pd.Series(dl).groupby(c20.day.values).mean()
        rows.append(dict(mark=m, rule=f"held_net<={x}", fired=int(f.sum()), rest_fired=round(np.nanmean(rest[f]), 2),
                         rest_notfired=round(np.nanmean(rest[ok & ~f]), 2) if (ok & ~f).any() else np.nan,
                         win=f"{(c20.ret_pct.values > 0).mean():.3f}->{(r2 > 0).mean():.3f}", d_all=round(dl.mean(), 3),
                         d_days=";".join(f"{k_[5:]}:{v:+.2f}" for k_, v in per.items()),
                         cond=";".join(f"{d[5:]}:{100 * (a[-1][2] / 1e5 - 1):+.1f}% {sum(1 for z in a if z[1] > 0)}/{len(a)}" for d, a in acc.items())))
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(R.to_string(index=False))
print("base conductor:", {d: round(100 * (account(gd, "ret_pct", "t_out")[-1][2] / 1e5 - 1), 1) for d, gd in c20[pool_m].groupby("day")})
R.to_pickle(os.path.join(W, "analysis5.pkl"))
print("done", round(time.time() - T0, 1))
