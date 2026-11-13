"""PHASE B (run after the 15:30 close; do not run during market hours). R19, 13 Nov.

Why: the council books (all five pool books, the Conductor, RAW) have NO hold marks in the trade table:
apex/engine/council/__init__.py:158-164 updates last / peak / worst for a held position but never calls
weather5.hold_tick (paper.py:1461 does, for every other book). So no exit rule for the books that actually trade can
be tested from h<mark>_* columns. This script rebuilds BID-based marks for every pool-book trade from the per-second
ds_v2 option quotes, one day part at a time.

Output: work/R19/pool_holdmarks.parquet with, per trade (day, book, key, t_in):
  hb{m}_ret   return in % if sold at the bid m seconds after entry (NaN if the trade had already closed)
  hb{m}_peak  best bid return in % seen up to m seconds
  hb{m}_worst worst bid return in % seen up to m seconds
for m in MARKS. 12 Nov is not in ds_v2 (not built), so its trades get NaN.

Then: py -3.13 harness.py --exit "hb300_ret < -6" --mark 300 --holdfile work/R19/pool_holdmarks.parquet
Rules: py -3.13, lowprio first, one script at a time, under 3 minutes and 1.5 GB (one part loaded at a time).
"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio  # noqa
import glob, json, os, time
import numpy as np, pandas as pd

DS = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R19\pool_holdmarks.parquet"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
MARKS = (60, 120, 180, 300, 600, 900, 1200, 1800)
CE, PE, BID = 0, 1, 0          # opt[t, strike, CE/PE, bid/ask]; check ds2.py if the order differs
t0 = time.time()
tr = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet",
                     columns=["day", "book", "key", "strike", "rr", "t_in", "t_out", "entry"])
tr = tr[tr.book.isin(POOL)].reset_index(drop=True)
cols = {f"hb{m}_{k}": np.full(len(tr), np.nan) for m in MARKS for k in ("ret", "peak", "worst")}
for day in sorted(tr.day.unique()):
    parts = sorted(glob.glob(os.path.join(DS, f"{day}*.npz")))
    for p in parts:
        man = p.replace(".npz", ".manifest.json")
        if os.path.exists(man) and json.load(open(man)).get("rows", 0) == 0:
            continue
        z = np.load(p, allow_pickle=False)
        t = z["t"]; opt = z["opt"]; strikes = z["strikes"]
        sub = tr[(tr.day == day) & (tr.t_in >= t[0]) & (tr.t_in <= t[-1])]
        for i, r in sub.iterrows():
            js = np.where(np.isclose(strikes, float(r.strike)))[0]
            if not len(js):
                continue
            k = CE if r.rr == "CE" else PE
            a = np.searchsorted(t, r.t_in, "left")
            for m in MARKS:
                if r.t_in + m >= r.t_out:
                    break
                b = np.searchsorted(t, r.t_in + m, "right") - 1
                if b <= a or b >= len(t):
                    break
                bid = opt[a:b + 1, js[0], k, BID].astype(float)
                bid = bid[np.isfinite(bid) & (bid > 0)]
                if not len(bid):
                    continue
                cols[f"hb{m}_ret"][i] = 100.0 * (bid[-1] / r.entry - 1.0)
                cols[f"hb{m}_peak"][i] = 100.0 * (bid.max() / r.entry - 1.0)
                cols[f"hb{m}_worst"][i] = 100.0 * (bid.min() / r.entry - 1.0)
        del z, opt
        print(day, os.path.basename(p), round(time.time() - t0, 1), flush=True)
        if time.time() - t0 > 170:
            print("time budget reached; rerun with the remaining days")
            break
out = pd.concat([tr[["day", "book", "key", "t_in"]], pd.DataFrame(cols)], axis=1)
out.to_parquet(OUT)
print("wrote", OUT, out.filter(like="_ret").notna().sum().to_dict())
