import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 6 (s05 rewritten for speed): each non-pool book added to the Conductor's pool at the LOWEST priority
# (pool c20 books win every tie; the candidate only takes the account when it is flat). Account all-in, 1 lakh a day.
# Walk-forward: discovery 19 Oct - 4 Nov (12 days), test 5 - 12 Nov (5 days). Every book x filter counted.
import time, json
import numpy as np, pandas as pd
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R01"
df = pd.read_pickle(W + r"\trades_small.pkl")
df = df[df.entry.notna() & df.exit.notna() & df.t_in.notna() & df.t_out.notna() & (df.entry > 0)].copy()
df["trig"] = df.trigger_t.fillna(df.t_in)
POOL = {"c20_9y": 12.088, "c20_9s": 11.441, "c20_9v": 9.897, "c20_9x": 9.605, "c20_9t": 4.385}
EXCL = set(POOL) | {"conductor", "RAW"}
CONTROLS = {"random_entry", "futures_only", "premium_momentum"}
DAYS = sorted(df.day.unique()); DISC = [d for d in DAYS if d <= "2026-11-04"]; TEST = [d for d in DAYS if d >= "2026-11-05"]
LOT = 65
def sim(a):
    cap = 1e5; ht = -1; hout = -1; n = w = nf = wf = 0
    for trig, prio, tout, en, ex, isp in a:
        if trig <= ht or trig < hout: continue
        lots = int(cap // (en * LOT))
        if lots < 1: continue
        pnl = (ex - en) * lots * LOT; cap += pnl; ht, hout = trig, tout; n += 1; w += pnl > 0
        if not isp: nf += 1; wf += pnl > 0
    return cap, n, w, nf, wf
def arr(g, prio, isp):
    return np.c_[g.trig.values, prio, g.t_out.values, g.entry.values, g.exit.values, np.full(len(g), isp)]
pool_tr = {d: arr(g, g.book.map(lambda b: -POOL[b]).values, 1.0) for d, g in df[df.book.isin(POOL)].groupby("day")}
def run(day, extra=None):
    a = pool_tr.get(day, np.zeros((0, 6)))
    if extra is not None and len(extra): a = np.r_[a, extra]
    a = a[np.lexsort((a[:, 1], a[:, 0]))]
    return sim(a.tolist())
base = {d: run(d) for d in DAYS}
print("baseline account (compare docs/54):")
for d in DAYS: print(d, f"{100*(base[d][0]/1e5-1):+.1f}%", base[d][1], base[d][2])
print("total rs", round(sum(base[d][0]-1e5 for d in DAYS)), "trades", sum(base[d][1] for d in DAYS), "won", sum(base[d][2] for d in DAYS))
f = lambda c: df[c].astype(float)
FILT = {"all": np.ones(len(df), bool),
        "er60>=.4": (f("wx_er60") >= 0.4).values,
        "range_vs_norm>=1": (f("wx_range_vs_norm") >= 1.0).values,
        "before14:15": (f("wx_mins_open") < 300).values,
        "breadth_with": ((f("wx_breadth_dir") * np.where(df.rr == "CE", 1, -1)) > 0).values,
        "day_move_with>=30": ((f("wx_day_move") * np.where(df.rr == "CE", 1, -1)) >= 30).values}
df["_i"] = np.arange(len(df))
cands = sorted(set(df.book.unique()) - EXCL)
print("n cands", len(cands)); A, B = int(sys.argv[1]), int(sys.argv[2]); cands = cands[A:B]
bydb = {k: g for k, g in df[df.book.isin(cands)].groupby(["book", "day"])}
res = []
for b in cands:
    for fn, m in FILT.items():
        row = {"book": b, "filt": fn, "control": b in CONTROLS}
        for wn, ds in (("D", DISC), ("T", TEST)):
            dl, nf, wf, n, w = [], 0, 0, 0, 0
            for d in ds:
                g = bydb.get((b, d))
                if g is not None: g = g[m[g._i.values]]
                r = run(d, arr(g, np.full(len(g), 1e6), 0.0)) if g is not None and len(g) else base[d]
                dl.append(np.log(r[0] / base[d][0])); nf += r[3]; wf += r[4]; n += r[1]; w += r[2]
            dl = np.array(dl)
            row.update({wn+"_sumlog": round(dl.sum(), 4), wn+"_up": int((dl > 1e-9).sum()), wn+"_dn": int((dl < -1e-9).sum()),
                        wn+"_worst": round(dl.min(), 4), wn+"_nfill": nf, wn+"_fsr": round(wf/nf, 2) if nf else np.nan,
                        wn+"_acct_sr": round(w/n, 3) if n else np.nan, wn+"_days": [round(x, 3) for x in dl]})
        res.append(row)
    if time.time() - t0 > 140: print("time cut after", b, flush=True); break
R = pd.DataFrame(res); R.to_pickle(W + "/fillers_" + str(A) + ".pkl")
bD = sum(base[d][2] for d in DISC)/sum(base[d][1] for d in DISC); bT = sum(base[d][2] for d in TEST)/sum(base[d][1] for d in TEST)
print("baseline acct strike D", round(bD,3), "T", round(bT,3), "| variants", len(R))
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 30)
cols = ["book","filt","D_sumlog","D_up","D_dn","D_worst","D_nfill","D_fsr","D_acct_sr","T_sumlog","T_up","T_dn","T_worst","T_nfill","T_fsr","T_acct_sr","T_days"]
sel = R[(R.D_sumlog > 0) & (R.D_up > R.D_dn) & (R.D_worst > -0.10) & (~R.control)]
print("selected on discovery:", len(sel)); print(sel.sort_values("D_sumlog", ascending=False)[cols].head(40).to_string(index=False))
print("selected positive on test:", int((sel.T_sumlog > 0).sum()), "of", len(sel), "| all variants positive on test:", int((R.T_sumlog > 0).sum()), "of", len(R))
print("controls:"); print(R[R.control][cols].to_string(index=False))
print("done", round(time.time()-t0,1))
