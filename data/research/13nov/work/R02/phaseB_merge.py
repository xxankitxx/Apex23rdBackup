"""PHASE B: merge the per-second exit runs and score every variant walk-forward.
Discovery 19 Oct - 4 Nov, test 5 - 11 Nov (12 Nov is not built). Usage: py -3.13 phaseB_merge.py [glob]  (default a4_B_*.json)
Reports per variant: strike rate, change in the sum of log returns (all-in compounding) per window, per test day,
losing book-days, the Conductor's trades as a subset (compounded per day), without the best trade and best day.
Promotion screen (docs/28 s.2, trade level): better in discovery AND test, positive without its best trade and best
day, strike rate not lower, losing book-days not more, worst day not worse."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, glob, os
import numpy as np
W = r"D:\ApexOptions\data\research\13nov\work\R02"
SPLIT = "2026-11-05"
pat = sys.argv[1] if len(sys.argv) > 1 else "a4_B_*.json"
R, seen = [], set()
for f in sorted(glob.glob(os.path.join(W, pat))):
    for r in json.load(open(f, encoding="utf-8"))["trades"]:
        k = (r["day"], r["book"], r["t_in"])
        if k not in seen:
            seen.add(k); R.append(r)
names = [n for n in R[0]["v"] if all(n in r["v"] for r in R)]
day = np.array([r["day"] for r in R]); book = np.array([r["book"] for r in R]); cond = np.array([r["cond"] for r in R])
ex = np.array([r["exp"] for r in R]); act = np.array([r["actual"] for r in R])
base = np.array([r["v"]["base"][0] for r in R]); lb = np.log1p(np.clip(base, -0.99, None))
disc = day < SPLIT
print("trades", len(R), "| discovery", int(disc.sum()), "test", int((~disc).sum()), "| conductor", int(cond.sum()), "| expiry", int(ex.sum()))
print("fidelity: median |rebuilt base - actual| %.2f pct pts; within 2 pts %d of %d" % (100 * np.median(np.abs(base - act)), int((np.abs(base - act) <= 0.02).sum()), len(R)))
ph = np.array([max(r["peak_hold"], 0) for r in R]); pf = np.array([max(r["peak_flat"], 0) for r in R])
print("available move: actual keeps %.0f %% of the peaks inside the hold and %.0f %% of the peaks to the flat time" % (100 * act.sum() / ph.sum(), 100 * act.sum() / pf.sum()))
tdays = sorted(set(day[~disc]))
def bookdays(lg, m):
    keys = sorted({(b, d) for b, d, mm in zip(book, day, m) if mm})
    return np.array([lg[(book == b) & (day == d)].sum() for b, d in keys])
def conddays(lg, m):
    ds = sorted(set(day[m & cond]))
    return np.array([lg[cond & (day == d)].sum() for d in ds])
rows = []
for n in names:
    v = np.array([r["v"][n][0] for r in R]); lg = np.log1p(np.clip(v, -0.99, None)); dl = lg - lb
    rec = dict(variant=n)
    for w, m in (("disc", disc), ("test", ~disc)):
        if not m.any():
            m = np.zeros(len(R), bool); m[0] = True        # empty window (smoke test only): placeholder
        bd, bb = bookdays(lg, m), bookdays(lb, m)
        cd, cb = conddays(lg, m), conddays(lb, m)
        rec[w] = dict(n=int(m.sum()), win=100 * float((v[m] > 0).mean()), win_base=100 * float((base[m] > 0).mean()),
                      dlog=100 * float(dl[m].sum()), dlog_no_best_trade=100 * float(dl[m].sum() - max(dl[m].max(), 0)),
                      losing_bookdays=int((bd < 0).sum()), losing_bookdays_base=int((bb < 0).sum()),
                      worst_bookday=100 * float(np.expm1(bd.min())) if len(bd) else None, worst_bookday_base=100 * float(np.expm1(bb.min())) if len(bb) else None,
                      cond_dlog=100 * float((cd - cb).sum()) if len(cd) else 0.0,
                      cond_dlog_no_best_day=100 * float((cd - cb).sum() - max((cd - cb).max(), 0)) if len(cd) else 0.0)
    rec["test_days"] = {d: round(100 * float(dl[day == d].sum()), 1) for d in tdays}
    a, b = rec["disc"], rec["test"]
    rec["passes"] = bool(a["dlog"] > 0 and b["dlog"] > 0 and a["dlog_no_best_trade"] > 0 and b["dlog_no_best_trade"] > 0
                         and a["win"] >= a["win_base"] - 0.5 and b["win"] >= b["win_base"] - 0.5
                         and a["losing_bookdays"] <= a["losing_bookdays_base"] and b["losing_bookdays"] <= b["losing_bookdays_base"]
                         and (a["worst_bookday"] or 0) >= (a["worst_bookday_base"] or 0) - 0.5 and (b["worst_bookday"] or 0) >= (b["worst_bookday_base"] or 0) - 0.5)
    rows.append(rec)
rows.sort(key=lambda r: -r["disc"]["dlog"])
print("\n%-36s | %-34s | %-34s | test days | pass" % ("variant (sorted by discovery)", "disc: win base->new, dlog, noBest, cond", "test: win base->new, dlog, noBest, cond"))
for r in rows:
    a, b = r["disc"], r["test"]
    print("%-36s | %4.1f->%4.1f %+7.1f %+7.1f %+6.1f | %4.1f->%4.1f %+7.1f %+7.1f %+6.1f | %s | %s" % (
        r["variant"], a["win_base"], a["win"], a["dlog"], a["dlog_no_best_trade"], a["cond_dlog"],
        b["win_base"], b["win"], b["dlog"], b["dlog_no_best_trade"], b["cond_dlog"],
        " ".join("%+.0f" % x for x in r["test_days"].values()), "PASS" if r["passes"] else ""))
print("\nvariants tried:", len(names) - 1, "| passing the screen:", sum(r["passes"] for r in rows if r["variant"] != "base"),
      "(by chance alone expect a few of", len(names) - 1, "to pass when the screen is loose: treat a lone pass as a lead, not proof)")
json.dump(rows, open(os.path.join(W, "phaseB_merge.json"), "w"), indent=1)
