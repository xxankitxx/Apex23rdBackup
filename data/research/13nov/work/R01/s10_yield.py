import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 10: a low-priority filler that YIELDS. Variants: hold cap at a hold mark (exit at that mark's bid gain) and
# PRE-EMPTION (when a pool c20 book fires while the filler holds, the filler leaves at its latest hold mark at or before
# that second, approximate, and the pool trade is taken). Walk-forward D = 19 Oct - 4 Nov, T = 5 - 12 Nov.
import time, numpy as np, pandas as pd
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R01"
df = pd.read_pickle(W + r"\trades_small.pkl")
df = df[df.entry.notna() & df.exit.notna() & df.t_in.notna() & df.t_out.notna() & (df.entry > 0)].copy()
df["trig"] = df.trigger_t.fillna(df.t_in)
POOL = {"c20_9y": 12.088, "c20_9s": 11.441, "c20_9v": 9.897, "c20_9x": 9.605, "c20_9t": 4.385}
DAYS = sorted(df.day.unique()); DISC = [d for d in DAYS if d <= "2026-11-04"]; TEST = [d for d in DAYS if d >= "2026-11-05"]
LOT = 65; MK = (60, 300, 900, 1800)
fams = [b for b in df.book.unique() if b.startswith(("t28", "lvl_trail", "spot_pb45", "spot_orb45", "edge_gate", "spot_dual")) or b in ("c20_8x", "c20_9h", "c20_9e", "apex_edge")]
def mk_rows(g, cap):
    """per trade: trig, t_out, entry, exit, marks gains (nan = gone)"""
    out = []
    for r in g.itertuples():
        gains = [getattr(r, f"h{m}_gain_pct") for m in MK]
        ex, tout = r.exit, r.t_out
        if cap and r.hold_s > cap and np.isfinite(gains[MK.index(cap)]):
            ex, tout = r.entry * (1 + gains[MK.index(cap)] / 100), r.t_in + cap
        out.append((r.trig, tout, r.entry, ex, r.t_in, gains))
    return out
pool = {d: sorted([(r.trig, -POOL[r.book], r.t_out, r.entry, r.exit) for r in g.itertuples()]) for d, g in df[df.book.isin(POOL)].groupby("day")}
def sim(day, fill, pre):
    ev = [(p[0], 0, p[1], p) for p in pool.get(day, [])] + [(f[0], 1, 0, f) for f in fill]
    ev.sort(key=lambda e: (e[0], e[1], e[2]))
    cap = 1e5; held = None; n = w = nf = wf = npre = 0
    for t, isf, _, x in ev:
        if held is not None:
            ht, hout, hf = held
            if t <= ht: continue
            if t < hout:
                if pre and not isf and hf is not None:          # pool trigger while the filler holds: pre-empt
                    f, lots = hf
                    el = t - f[4]; g = 0.0
                    for m, gm in zip(MK, f[5]):
                        if m <= el and np.isfinite(gm): g = gm
                    # undo the filler's booked pnl and book the pre-empted one
                    cap -= (f[3] - f[2]) * lots * LOT; pnl = f[2] * g / 100 * lots * LOT; cap += pnl
                    wf -= (f[3] > f[2]); wf += pnl > 0; w -= (f[3] > f[2]); w += pnl > 0; npre += 1
                    held = None
                else:
                    continue
        en, ex, tout = (x[3], x[4], x[2]) if not isf else (x[2], x[3], x[1])
        lots = int(cap // (en * LOT))
        if lots < 1: continue
        pnl = (ex - en) * lots * LOT; cap += pnl; n += 1; w += pnl > 0
        if isf: nf += 1; wf += pnl > 0; held = (t, tout, (x, lots))
        else: held = (t, tout, None)
    return cap, n, w, nf, wf, npre
base = {d: sim(d, [], False) for d in DAYS}
assert abs(sum(base[d][0] - 1e5 for d in DAYS) - 1092458) < 5, sum(base[d][0] - 1e5 for d in DAYS)
res = []
for b in sorted(fams):
    gb = df[df.book == b]
    for cap in (0, 300, 900):
        rows = {d: mk_rows(g, cap) for d, g in gb.groupby("day")}
        for pre in (False, True):
            r0 = {"book": b, "cap": cap, "pre": pre}
            for wn, ds in (("D", DISC), ("T", TEST)):
                dl, n, w, nf, wf, npr = [], 0, 0, 0, 0, 0
                for d in ds:
                    r = sim(d, rows.get(d, []), pre)
                    dl.append(np.log(r[0] / base[d][0])); n += r[1]; w += r[2]; nf += r[3]; wf += r[4]; npr += r[5]
                dl = np.array(dl)
                r0.update({wn + "_sl": round(dl.sum(), 3), wn + "_up": int((dl > 1e-9).sum()), wn + "_dn": int((dl < -1e-9).sum()), wn + "_worst": round(dl.min(), 3),
                           wn + "_nf": nf, wn + "_pre": npr, wn + "_acct_sr": round(w / max(n, 1), 3), wn + "_fsr": round(wf / max(nf, 1), 2), wn + "_days": [round(x, 3) for x in dl]})
            res.append(r0)
    if time.time() - t0 > 150: print("time cut after", b); break
R = pd.DataFrame(res); R.to_pickle(W + r"\yield.pkl")
pd.set_option("display.width", 280); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 30)
bD = sum(base[d][2] for d in DISC) / sum(base[d][1] for d in DISC); bT = sum(base[d][2] for d in TEST) / sum(base[d][1] for d in TEST)
print("variants", len(R), "| baseline acct strike D", round(bD, 3), "T", round(bT, 3))
print(R.groupby(["cap", "pre"]).agg(D_med=("D_sl", "median"), T_med=("T_sl", "median"), D_pos=("D_sl", lambda x: (x > 0).mean()), T_pos=("T_sl", lambda x: (x > 0).mean()), Tup=("T_up", "mean"), Tdn=("T_dn", "mean")).round(3).to_string())
sel = R[(R.D_sl > 0) & (R.D_up > R.D_dn) & (R.D_worst > -0.10)]
print("selected on D:", len(sel), "positive on T:", int((sel.T_sl > 0).sum()), "T up>dn:", int((sel.T_up > sel.T_dn).sum()))
print(sel.sort_values("D_sl", ascending=False).to_string(index=False))
print("done", round(time.time() - t0, 1))
