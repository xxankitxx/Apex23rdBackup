import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 part 4: day-direction lock. Declared rules, nothing fitted, so they are scored on all 17 days and per window.
L1(det, cp): from the checkpoint on, on a day the detector calls 'one-way', the pool may only buy in the direction of the
             move so far (sign of futures minus open at the checkpoint).
L2(cp):      every day, from the checkpoint on, only buy with the move so far at the checkpoint.
L3:          every trade, only buy with the day's move at the trigger (wx_day_move > 0, signed by the trade).
L4:          only buy on the VWAP side (wx_vwap_ext > 0, signed by the trade)."""
import os, time, warnings
warnings.filterwarnings("ignore")
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 60)
base = pd.read_pickle(os.path.join(W, "base.pkl"))
wx = pd.read_pickle(os.path.join(W, "wx.pkl"))[["wx_day_move", "wx_vwap_ext"]]
FE = pd.read_csv(os.path.join(W, "cp_features.csv")); FE["cp"] = FE["cp"].astype(int).map(lambda x: f"{x:04d}")
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
P0 = {b: i for i, b in enumerate(POOL)}
df = pd.concat([base, wx], axis=1)
df["trig"] = df["trigger_t"].fillna(df["t_in"])
df = df[df.book.isin(POOL)].dropna(subset=["entry", "exit", "t_out", "trig"]).reset_index(drop=True)
df["hm"] = ((df.trig + 19800.0) % 86400.0) / 60.0
df["d"] = np.where(df.rr == "CE", 1, -1)
df["_p"] = df.book.map(P0)
DAYS = sorted(df.day.unique())
ARRS = {}
for d, g in df.groupby("day"):
    g = g.sort_values(["trig", "_p"], kind="stable")
    ARRS[d] = (g.index.values, g.trig.values, g.t_out.values, g._p.values, g.entry.values, g.exit.values, g.ret_pct.values, g.book.values)


def sim(d, veto=None):
    ix, tg, to, pb, en, ex, rp, bk = ARRS[d]
    keep = np.ones(len(ix), bool) if veto is None else ~veto[ix]
    cap = 1e5; held = None; out = []
    for k in np.nonzero(keep)[0]:
        t = tg[k]
        if held is not None:
            if t <= held[0] or t < held[1] or (t == held[1] and pb[k] == held[2]):
                continue
            held = None
        lots = int(cap // (en[k] * 65))
        if lots < 1:
            continue
        pnl = (ex[k] - en[k]) * lots * 65; cap += pnl
        held = (t, to[k], pb[k]); out.append((bk[k], t, rp[k], pnl))
    return out, (cap / 1e5 - 1) * 100


cond = {d: sim(d) for d in DAYS}
print("Conductor sum", round(sum(v[1] for v in cond.values()), 1))
allc = [(d, x) for d in DAYS for x in cond[d][0]]
thr = np.percentile([x[2] for _, x in allc], 90)
TOP = {(d, x[0], x[1]) for d, x in allc if x[2] >= thr}
CPM = {"0945": 585, "1015": 615, "1100": 660}
F = {cp: FE[FE.cp == cp].set_index("day") for cp in CPM}


def det(name, cp, d):
    S = F[cp].loc[d]
    if name == "dec":
        return S.er >= 0.30 and abs(S.Dc) >= 0.60
    if name == "oneway":
        return (S.pos >= 0.85 and S.mv_pct > 0) or (S.pos <= 0.15 and S.mv_pct < 0)
    if name == "gapgo":
        return abs(S.gap_pct) >= 0.30 and np.sign(S.mv_pct) == np.sign(S.gap_pct)
    if name == "all":
        return True


def score(tag, veto):
    out = {d: sim(d, veto) for d in DAYS}
    r = np.array([out[d][1] for d in DAYS]); c = np.array([cond[d][1] for d in DAYS]); e = np.array([d < "2026-11-05" for d in DAYS])
    n = sum(len(out[d][0]) for d in DAYS); w = sum(sum(1 for x in out[d][0] if x[3] > 0) for d in DAYS)
    nL = sum(len(out[d][0]) for d in DAYS if d >= "2026-11-05"); wL = sum(sum(1 for x in out[d][0] if x[3] > 0) for d in DAYS if d >= "2026-11-05")
    took = {(d, x[0], x[1]) for d in DAYS for x in out[d][0]}
    allr = sorted([x[2] for d in DAYS for x in out[d][0]])
    return dict(rule=tag, vetoed=int(veto.sum()), strike=round(100 * w / n, 1), n=n, sum=round(r.sum(), 1), diff=round(r.sum() - c.sum(), 1),
                early_diff=round(r[e].sum() - c[e].sum(), 1), late_diff=round(r[~e].sum() - c[~e].sum(), 1),
                late_strike=round(100 * wL / max(nL, 1), 1), late_n=nL,
                lose=int((r < 0).sum()), worst=round(r.min(), 1), ex_best_day=round(r.sum() - r.max(), 1),
                ex_best_trade_note=round(allr[-1], 1) if allr else 0, top_kept=f"{len(TOP & took)}/{len(TOP)}",
                better=int((r > c + 1e-9).sum()), worse=int((r < c - 1e-9).sum()),
                per_day=" ".join(f"{x:.0f}" for x in r)), out


rows = []; OUT = {}
c = np.array([cond[d][1] for d in DAYS])
rows.append(dict(rule="Conductor", vetoed=0, strike=round(100 * sum(sum(1 for x in cond[d][0] if x[3] > 0) for d in DAYS) / sum(len(cond[d][0]) for d in DAYS), 1),
                 n=sum(len(cond[d][0]) for d in DAYS), sum=round(c.sum(), 1), lose=int((c < 0).sum()), worst=round(c.min(), 1),
                 ex_best_day=round(c.sum() - c.max(), 1), top_kept=f"{len(TOP)}/{len(TOP)}", per_day=" ".join(f"{x:.0f}" for x in c),
                 late_strike=round(100 * sum(sum(1 for x in cond[d][0] if x[3] > 0) for d in DAYS if d >= "2026-11-05") / sum(len(cond[d][0]) for d in DAYS if d >= "2026-11-05"), 1)))
for dn in ("dec", "oneway", "gapgo", "all"):
    for cp, cm in CPM.items():
        veto = np.zeros(len(df), bool)
        for d in DAYS:
            if not det(dn, cp, d):
                continue
            sgn = np.sign(F[cp].loc[d].mv_pct)
            m = (df.day == d) & (df.hm >= cm) & (df.d != sgn)
            veto |= m.values
        s, o = score(f"L{'2' if dn == 'all' else '1'} {dn} {cp}", veto); rows.append(s); OUT[s["rule"]] = o
s, o = score("L3 with day move", (df.wx_day_move < 0).values); rows.append(s); OUT[s["rule"]] = o
s, o = score("L4 VWAP side", (df.wx_vwap_ext < 0).values); rows.append(s); OUT[s["rule"]] = o
R = pd.DataFrame(rows)
R.to_csv(os.path.join(W, "trend_lock.csv"), index=False)
print("days:", " ".join(d[5:] for d in DAYS))
print(R.to_string())
print("variants:", len(R) - 1, round(time.time() - t00, 1))
