import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 4: the nightly weather search as a PROCEDURE, rolling walk-forward. For every day D from 28 Oct on:
search every single weather line on all days before D only, freeze the best (same constraints as s1/s2), trade D
with it. Conductor level (exact account) and trade level for the groups given.
  py -3.13 -u s4_rolling.py [GROUPS] [FIRST_DAY]"""
import json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L

groups = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] else []
FIRST = sys.argv[2] if len(sys.argv) > 2 else "2026-10-28"
d = L.load()
days = d.days
folds = [i for i, x in enumerate(days) if x >= FIRST]
print("loaded", round(time.time() - t0, 1), "folds", len(folds), flush=True)

# ── Conductor level ──
prio = {b: i for i, b in enumerate(L.POOL)}
R = np.flatnonzero(np.isin(d.book, L.POOL) & np.isfinite(d.entry) & np.isfinite(d.exit) & np.isfinite(d.t_in))
pr = np.array([prio[b] for b in d.book[R]])
R = R[np.lexsort((pr, d.trig[R], d.di[R]))]
nR = len(R)
trig, tout, px, ex = d.trig[R], d.t_out[R], d.entry[R], d.exit[R]
bk = np.array([prio[b] for b in d.book[R]])
rr = (d.rr[R] == "CE").astype(int)
dayi = d.di[R]
XR = d.X[R].astype(np.float64)
F = XR.shape[1]


def sim(K, dlist):
    C = K.shape[0]
    out = np.zeros((C, len(days)))
    T = np.zeros((C, nR), bool)
    for di in dlist:
        cap = np.full(C, L.CAP0)
        h_trig = np.full(C, -np.inf); h_out = np.full(C, -np.inf); h_bk = np.full(C, -1)
        for j in np.flatnonzero(dayi == di):
            busy = (trig[j] <= h_trig) | (trig[j] < h_out) | ((trig[j] == h_out) & (bk[j] == h_bk))
            lots = np.floor(cap / (px[j] * L.LOT))
            tk = ~busy & K[:, j] & (lots >= 1)
            if tk.any():
                cap[tk] += (ex[j] - px[j]) * lots[tk] * L.LOT
                h_trig[tk] = trig[j]; h_out[tk] = tout[j]; h_bk[tk] = bk[j]
                T[tk, j] = True
        out[:, di] = 100.0 * (cap / L.CAP0 - 1.0)
    return out, T


base_ret, base_T = sim(np.ones((1, nR), bool), list(range(len(days))))
cond_rows = []
for fd in folds:
    train = list(range(fd))
    trm = np.isin(dayi, train)
    # lines from the training rows (one per trigger second: the first row)
    first = np.ones(nR, bool)
    first[1:] = (dayi[1:] != dayi[:-1]) | (trig[1:] != trig[:-1])
    sel = first & trm
    cf, cop, cln = [], [], []
    for f in range(F):
        xs = np.sort(XR[sel, f][np.isfinite(XR[sel, f])])
        for ln in L.lines_for(xs, d.kinds[f]):
            cf += [f, f]; cop += [1, 0]; cln += [float(ln), float(ln)]
    cf, cop, cln = np.array(cf), np.array(cop), np.array(cln)
    bt = np.flatnonzero(base_T[0] & trm)
    nbig = max(1, int(round(0.1 * len(bt))))
    big = bt[np.argsort(-d.ret[R[bt]])[:nbig]]
    big = big[d.ret[R[big]] > 0]
    Mb = np.zeros((nR, len(big)), np.float32)
    for i, b in enumerate(big):
        same = (dayi == dayi[b]) & (rr == rr[b])
        Mb[:, i] = (same & ((np.abs(trig - trig[b]) <= 60) | ((trig <= trig[b]) & (trig[b] < tout)))).astype(np.float32)
    base_n = len(bt)
    base_sr = float((d.ret[R[bt]] > 0).mean()) if len(bt) else 0.0
    best = (-np.inf, None)
    for s in range(0, len(cf), 4000):
        idx = np.arange(s, min(s + 4000, len(cf)))
        v = XR[:, cf[idx]].T
        K = np.isfinite(v) & np.where(cop[idx][:, None] == 1, v >= cln[idx][:, None], v < cln[idx][:, None])
        rd, T = sim(K, train)
        obj = np.log1p(rd[:, train] / 100).sum(1)
        n = T[:, trm].sum(1)
        w = (T[:, trm] & (d.ret[R][trm] > 0)[None, :]).sum(1)
        sr = np.divide(w, n, out=np.zeros(len(n)), where=n > 0)
        kb = ((T.astype(np.float32) @ Mb) > 0).sum(1)
        okm = (kb >= np.ceil(2 / 3 * len(big) - 1e-9)) & (sr >= base_sr) & (n >= 0.5 * base_n)
        o = np.where(okm, obj, -np.inf)
        c = int(np.argmax(o))
        if o[c] > best[0]:
            best = (float(o[c]), idx[c])
    c = best[1]
    if c is None:
        cond_rows.append({"day": days[fd], "rule": None})
        continue
    v = XR[:, cf[c]]
    K = (np.isfinite(v) & ((v >= cln[c]) if cop[c] == 1 else (v < cln[c])))[None, :]
    rd, T = sim(K, [fd])
    tk = np.flatnonzero(T[0] & (dayi == fd))
    bk0 = np.flatnonzero(base_T[0] & (dayi == fd))
    row = {"day": days[fd], "rule": [d.names[cf[c]], ">=" if cop[c] == 1 else "<", float(cln[c])],
           "train_obj_gain": round(best[0] - float(np.log1p(base_ret[0, train] / 100).sum()), 4),
           "base_ret": round(float(base_ret[0, fd]), 2), "rule_ret": round(float(rd[0, fd]), 2),
           "base_n": len(bk0), "rule_n": len(tk),
           "base_sr": round(float((d.ret[R[bk0]] > 0).mean()), 3) if len(bk0) else None,
           "rule_sr": round(float((d.ret[R[tk]] > 0).mean()), 3) if len(tk) else None}
    cond_rows.append(row)
    print("COND", row, round(time.time() - t0, 1), flush=True)

# ── trade level ──
CONTROLS = {"random_entry", "futures_only", "premium_momentum", "RAW", "conductor"}
fam = np.array([L.family(b) for b in d.book])
trade_out = {}
for grp in groups:
    ok = np.isfinite(d.ret) & ~np.isin(d.book, list(CONTROLS))
    if grp == "pool_trades":
        ok &= np.isin(d.book, L.POOL)
    elif grp.startswith("fam:"):
        ok &= fam == grp[4:]
    rows = []
    for fd in folds:
        tr = np.flatnonzero(ok & (d.di < fd))
        te = np.flatnonzero(ok & (d.di == fd))
        if len(tr) < 60 or len(te) == 0:
            continue
        S = L.Search(d.X, tr, d.kinds)
        real, res = S.best(d.g[tr], d.win[tr], L.big_mask(d.ret[tr]))
        j = int(np.argmax(real))
        if not np.isfinite(real[j]):
            rows.append({"day": days[fd], "rule": None}); continue
        bv, bst = -np.inf, None
        for s in (0, 1):
            t = int(np.argmax(res[s][0][j]))
            if res[s][0][j, t] > bv:
                bv, bst = res[s][0][j, t], (">=" if s == 1 else "<", float(S.line[j, t]))
        km = L.keep_mask(d.X[te, S.feats[j]].astype(float), *bst)
        k = te[km]
        bt = L.big_mask(d.ret[te])
        rows.append({"day": days[fd], "rule": [d.names[S.feats[j]], bst[0], bst[1]], "n": len(te),
                     "sr": round(float(d.win[te].mean()), 3), "kept": len(k),
                     "kept_sr": round(float(d.win[k].mean()), 3) if len(k) else None,
                     "dG": round(float(d.g[k].sum() - d.g[te].sum()), 4),
                     "mean_g": round(float(d.g[te].mean()), 4), "kept_mean_g": round(float(d.g[k].mean()), 4) if len(k) else None,
                     "big_kept": f"{int(bt[km].sum())}/{int(bt.sum())}"})
        print("TRADE", grp, rows[-1], round(time.time() - t0, 1), flush=True)
    trade_out[grp] = rows
json.dump({"conductor": cond_rows, "trade": trade_out}, open(os.path.join(L.HERE, "out_s4_rolling.json"), "w"), default=float)
print("done", round(time.time() - t0, 1), flush=True)
