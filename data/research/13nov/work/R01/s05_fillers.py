import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 5: complementary entry families as LOW-PRIORITY pool members of the Conductor (the account_sim logic, from the
# trade table): pool c20 books first, the candidate only when the account is flat. Walk-forward: discovery days
# 19 Oct - 4 Nov, test days 5 - 12 Nov. Every candidate and every filter is counted (multiple testing).
import json, time
import numpy as np
import pandas as pd
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R01"
df = pd.read_pickle(W + r"\trades_small.pkl")
df = df[df.entry.notna() & df.exit.notna() & df.t_in.notna() & df.t_out.notna()].copy()
df["trig"] = df.trigger_t.fillna(df.t_in)
POOL = {"c20_9y": 12.088, "c20_9s": 11.441, "c20_9v": 9.897, "c20_9x": 9.605, "c20_9t": 4.385}
EXCL = set(POOL) | {"conductor", "RAW", "c20_8x", "c20_9e", "c20_9h", "fx_c20_9y", "fr_c20_9y", "rx_c20_9y"}
CONTROLS = {"random_entry", "futures_only", "premium_momentum"}
DISC = [d for d in sorted(df.day.unique()) if d <= "2026-11-04"]
TEST = [d for d in sorted(df.day.unique()) if d >= "2026-11-05"]
LOT = 65


def sim(tr):
    """tr: array rows (trig, prio, t_out, entry, exit, is_pool). Returns (cap_end, n, wins, n_pool, n_fill, wins_fill)."""
    cap = 100000.0
    held = None
    n = w = npool = nf = wf = 0
    for trig, prio, tout, en, ex, ispool in tr:
        if held is not None:
            if trig <= held[0] or trig < held[1]:
                continue
            held = None
        lots = int(cap // (en * LOT))
        if lots < 1:
            continue
        pnl = (ex - en) * lots * LOT
        cap += pnl
        held = (trig, tout)
        n += 1; w += pnl > 0
        if ispool:
            npool += 1
        else:
            nf += 1; wf += pnl > 0
    return cap, n, w, npool, nf, wf


pool_tr = {}
for day, g in df[df.book.isin(POOL)].groupby("day"):
    pr = g.book.map(lambda b: -POOL[b]).values
    pool_tr[day] = np.c_[g.trig.values, pr, g.t_out.values, g.entry.values, g.exit.values, np.ones(len(g))]


def run(day, extra):
    a = pool_tr.get(day, np.zeros((0, 6)))
    if extra is not None and len(extra):
        a = np.r_[a, extra]
    a = a[np.lexsort((a[:, 1], a[:, 0]))]
    return sim(a)


base = {d: run(d, None) for d in sorted(df.day.unique())}
print("baseline (should be the p44 Conductor):")
tot = 0
for d, r in base.items():
    tot += r[0] - 1e5
    print(d, f"{100 * (r[0] / 1e5 - 1):+.1f}%", "trades", r[1], "won", r[2])
print("total rs", round(tot))
# filters on the trigger photograph (pre-specified, motivated by the silent-stretch shapes; all counted)
FILT = {
    "all": lambda g: np.ones(len(g), bool),
    "trend_with": lambda g: (g.wx_er60.astype(float) >= 0.4) & (g.wx_dir60.astype(float) == 1),
    "day_with": lambda g: g.wx_day_move.astype(float) >= 30,
    "breadth60": lambda g: g.wx_breadth_dir.astype(float) >= 0.6,
    "before1415": lambda g: g.wx_mins_open.astype(float) < 300,
    "active": lambda g: g.wx_range_vs_norm.astype(float) >= 1.0,
}
cands = sorted(set(df.book.unique()) - EXCL)
res = []
for b in cands:
    gb = df[df.book == b]
    for fn, f in FILT.items():
        m = f(gb).fillna(False).values if hasattr(f(gb), "fillna") else f(gb)
        g = gb[m]
        out = {"book": b, "filt": fn, "control": b in CONTROLS}
        for wname, ds in (("D", DISC), ("T", TEST)):
            diffs, nf, wf, nfill_raw, wfill_raw, ntr, wtr = [], 0, 0, 0, 0, 0, 0
            for d in ds:
                gd = g[g.day == d]
                ex = np.c_[gd.trig.values, np.full(len(gd), 1e6), gd.t_out.values, gd.entry.values, gd.exit.values, np.zeros(len(gd))]
                r = run(d, ex)
                diffs.append(np.log(r[0] / 1e5) - np.log(base[d][0] / 1e5))
                nf += r[4]; wf += r[5]; ntr += r[1]; wtr += r[2]
                nfill_raw += len(gd); wfill_raw += int((gd.exit > gd.entry).sum())
            diffs = np.array(diffs)
            out.update({f"{wname}_sumlog": round(float(diffs.sum()), 4), f"{wname}_up": int((diffs > 1e-9).sum()),
                        f"{wname}_dn": int((diffs < -1e-9).sum()), f"{wname}_worst": round(float(diffs.min()), 4),
                        f"{wname}_nfill": nf, f"{wname}_fill_sr": round(wf / nf, 3) if nf else None,
                        f"{wname}_acct_sr": round(wtr / ntr, 3) if ntr else None, f"{wname}_raw_n": nfill_raw,
                        f"{wname}_raw_sr": round(wfill_raw / nfill_raw, 3) if nfill_raw else None,
                        f"{wname}_days": [round(float(x), 4) for x in diffs]})
        res.append(out)
R = pd.DataFrame(res)
R.to_pickle(W + r"\fillers.pkl")
bsr_D = sum(base[d][2] for d in DISC) / sum(base[d][1] for d in DISC)
bsr_T = sum(base[d][2] for d in TEST) / sum(base[d][1] for d in TEST)
print("baseline strike rate D", round(bsr_D, 3), "T", round(bsr_T, 3))
sel = R[(R.D_sumlog > 0) & (R.D_up > R.D_dn) & (R.D_worst > -0.10) & (~R.control)]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 600); pd.set_option("display.max_columns", 40)
cols = ["book", "filt", "D_sumlog", "D_up", "D_dn", "D_worst", "D_nfill", "D_fill_sr", "D_acct_sr", "T_sumlog", "T_up", "T_dn",
        "T_worst", "T_nfill", "T_fill_sr", "T_acct_sr"]
print("\nvariants tried:", len(R), "(", R.book.nunique(), "books x", len(FILT), "filters )")
print("selected on discovery (sumlog>0, up>dn, worst>-10%):", len(sel))
print(sel.sort_values("D_sumlog", ascending=False)[cols].to_string(index=False))
print("\nof the selected, positive on test:", int((sel.T_sumlog > 0).sum()), "of", len(sel))
print("all variants positive on test:", int((R.T_sumlog > 0).sum()), "of", len(R))
print("\nTOP 25 BY TEST (for reference, NOT a selection):")
print(R.sort_values("T_sumlog", ascending=False)[cols].head(25).to_string(index=False))
print("done", round(time.time() - t0, 1))
