import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05: the hold marks the engine never photographs for the council books (engine_main._council skips
paper.check_exit, the only caller of weather5.hold_tick), rebuilt from the 1-Hz quotes of ds_v2.

For every c20-family trade (all c20* books, the five pool books among them) on the chosen days:
  at marks S after the fill, while still held: bid, ask, mid of the held contract, peak bid / peak mid so far and when,
  the future's favourable move since entry and its best so far;
  after the book's exit: the bid at fixed delays and the best / worst bid inside each delay (for "hold longer" rules).
Read-only on ds_v2 and work/R05/tr.pkl. One part loaded at a time.

Usage: py -3.13 phaseB_c20_paths.py TAG [part ...]      (no part = every ds_v2 part; TAG names the output file)
       pilot (13 Nov, market hours, 3 parts): TAG=pilot 2026-11-05 2026-11-06 2026-11-09"""
import glob, json, os, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
DS = r"D:\ApexOptions\data\research\ds_v2"
S = [30, 60, 120, 180, 300, 450, 600, 900, 1200, 1800, 2700, 3600, 5400]
POST = [30, 60, 120, 300, 600, 900, 1800]
CLOSE = 15 * 3600 + 20 * 60          # council forced flat on a normal day (15:00 on expiry, handled by the clip below)
tag = sys.argv[1] if len(sys.argv) > 1 else "all"
parts = sys.argv[2:] or sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DS, "*.npz")))
df = pd.read_pickle(os.path.join(W, "tr.pkl"))
cols = ["day", "book", "t_in", "t_out", "strike", "rr", "entry", "exit", "ret_pct", "hold_s", "expiry", "reason",
        "dte_in", "fut_in", "key"]
c = df[df.book.str.startswith("c20")][[x for x in cols if x in df]].copy()
del df
rows = []


def sod(t):
    return (int(t) + 19800) % 86400


for part in parts:
    day = part[:10]
    tr = c[c.day == day]
    if not len(tr):
        continue
    man = os.path.join(DS, part + ".manifest.json")
    try:
        if json.load(open(man)).get("rows", 0) <= 0:
            continue
    except Exception:
        pass
    z = np.load(os.path.join(DS, part + ".npz"))
    t = z["t"].astype(float)
    if not len(t):
        continue
    K = z["strikes"].astype(float)
    n = len(K)
    opt = z["opt"][:, :n]                      # (rows, strikes, CE/PE, bid/ask)
    age = z["age"][:, :n]
    fut = z["fut"].astype(float)
    fm = np.where((fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]), 0.5 * (fut[:, 0] + fut[:, 1]), fut[:, 2])
    exp = str(z["expiry"])
    flat = (15 * 3600) if exp == day else CLOSE
    for _, r in tr.iterrows():
        if str(r.get("expiry") or exp) != exp or not (t[0] <= r.t_in <= t[-1]):
            continue
        jj = np.where(K == float(r.strike))[0]
        if not len(jj):
            continue
        j, s_ = int(jj[0]), (0 if r.rr == "CE" else 1)
        d = 1 if s_ == 0 else -1
        bid = opt[:, j, s_, 0].astype(float)
        ask = opt[:, j, s_, 1].astype(float)
        ag = age[:, j, s_].astype(float)
        ok = (bid > 0) & (ask >= bid) & (ag <= 15)
        i0 = int(np.searchsorted(t, r.t_in))
        i1 = int(np.searchsorted(t, r.t_out))
        iE = int(np.searchsorted(t, min(r.t_out + max(POST), r.t_out - sod(r.t_out) + flat), side="right"))
        if i1 <= i0 or i0 >= len(t):
            continue
        f0 = fm[i0] if np.isfinite(fm[i0]) else np.nan
        out = dict(day=day, book=r.book, t_in=r.t_in, t_out=r.t_out, entry=r.entry, exit=r.exit, ret_pct=r.ret_pct,
                   hold_s=r.hold_s, reason=r.reason, rr=r.rr, strike=r.strike, dte0=int(exp == day), part=part)
        # held path
        hb = np.where(ok[i0:i1 + 1], bid[i0:i1 + 1], np.nan)
        hm = np.where(ok[i0:i1 + 1], 0.5 * (bid[i0:i1 + 1] + ask[i0:i1 + 1]), np.nan)
        ht = t[i0:i1 + 1]
        hf = (fm[i0:i1 + 1] - f0) * d
        pkb = np.fmax.accumulate(np.where(np.isfinite(hb), hb, -np.inf))
        pkm = np.fmax.accumulate(np.where(np.isfinite(hm), hm, -np.inf))
        pkf = np.fmax.accumulate(np.where(np.isfinite(hf), hf, -np.inf))
        out["bid_in"] = hb[0] if np.isfinite(hb[0]) else np.nan
        out["ask_in"] = ask[i0] if ok[i0] else np.nan
        out["bid_out"] = hb[-1] if np.isfinite(hb[-1]) else np.nan
        out["peak_bid"] = float(np.nanmax(hb)) if np.isfinite(hb).any() else np.nan
        out["peak_mid"] = float(np.nanmax(hm)) if np.isfinite(hm).any() else np.nan
        for s in S:
            k = int(np.searchsorted(ht, r.t_in + s))
            if k >= len(ht) - 1:                     # not held at this mark any more
                continue
            kk = k
            while kk > 0 and not np.isfinite(hb[kk]):
                kk -= 1
            out[f"b{s}"] = hb[kk]
            out[f"m{s}"] = hm[kk]
            out[f"pb{s}"] = pkb[k] if np.isfinite(pkb[k]) else np.nan
            out[f"pm{s}"] = pkm[k] if np.isfinite(pkm[k]) else np.nan
            ip = int(np.argmax(np.where(np.isfinite(hb[:k + 1]), hb[:k + 1], -np.inf)))
            out[f"tp{s}"] = ht[ip] - r.t_in
            out[f"f{s}"] = hf[k]
            out[f"pf{s}"] = pkf[k] if np.isfinite(pkf[k]) else np.nan
        # after the exit: same contract
        pb_ = np.where(ok[i1:iE], bid[i1:iE], np.nan)
        pt_ = t[i1:iE]
        pf_ = (fm[i1:iE] - f0) * d
        for h in POST:
            k = int(np.searchsorted(pt_, r.t_out + h, side="right"))
            if k <= 1 or pt_[k - 1] < r.t_out + h - 5:
                continue
            seg = pb_[:k]
            if not np.isfinite(seg).any():
                continue
            out[f"xb{h}"] = seg[np.isfinite(seg)][-1]
            out[f"xmax{h}"] = float(np.nanmax(seg))
            out[f"xmin{h}"] = float(np.nanmin(seg))
            out[f"xf{h}"] = pf_[k - 1]
        rows.append(out)
    print(part, len(tr), "trades on the day; rows so far", len(rows), round(time.time() - T0, 1), "s", flush=True)
    del z, opt, age
R = pd.DataFrame(rows)
R.to_pickle(os.path.join(W, f"c20_paths_{tag}.pkl"))
print("saved", R.shape, os.path.join(W, f"c20_paths_{tag}.pkl"), round(time.time() - T0, 1), "s")
