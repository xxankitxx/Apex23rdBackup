import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, numpy as np
W = r"D:\ApexOptions\data\research\13nov\work\R02"
R = []
for tag in ("d1106", "d1109c", "d1111"):
    R += json.load(open(W + "/a4_" + tag + ".json"))["trades"]
names = list(R[0]["v"])
act = np.array([r["actual"] for r in R]); base = np.array([r["v"]["base"][0] for r in R])
days = sorted({r["day"] for r in R}); cond = np.array([r["cond"] for r in R]); ex = np.array([r["exp"] for r in R])
dayv = np.array([r["day"] for r in R])
ph = np.array([max(r["peak_hold"], 0) for r in R]); pf = np.array([max(r["peak_flat"], 0) for r in R])
print("trades", len(R), "cond", cond.sum(), "expiry-day trades", ex.sum(), {d: int((dayv == d).sum()) for d in days})
print("capture: actual sum %.0f%%, peak in hold %.0f%%, peak to flat %.0f%% -> %.0f%% / %.0f%%" % (100*act.sum(), 100*ph.sum(), 100*pf.sum(), 100*act.sum()/ph.sum(), 100*act.sum()/pf.sum()))
print("cond only: actual %.0f%% peak-hold %.0f%% flat %.0f%%" % (100*act[cond].sum(), 100*ph[cond].sum(), 100*pf[cond].sum()))
def comp(v, msk):
    out = []
    for d in days:
        m = msk & (dayv == d)
        if m.sum(): out.append(100 * (np.prod(1 + v[m]) - 1))
    return out
rows = []
lb = np.log1p(np.clip(base, -0.99, None))
for n in names:
    v = np.array([r["v"][n][0] for r in R]); lg = np.log1p(np.clip(v, -0.99, None))
    hold = np.median([r["v"][n][2] for r in R]) / 60
    pdx = [100 * (lg - lb)[dayv == d].sum() for d in days]
    cd = comp(v, cond)
    rows.append((n, 100 * (v > 0).mean(), 100 * v.mean(), 100 * (lg - lb).sum(), pdx, 100 * (lg - lb)[cond].sum(), 100 * (lg - lb)[ex].sum(), 100 * (lg - lb)[~ex].sum(), hold, cd))
rows.sort(key=lambda x: -x[3])
print("%-34s %5s %6s %8s | %s | %7s %7s %7s %5s | cond day compounded %%" % ("variant", "win", "mean", "dlog", " ".join(d[5:] for d in days), "dcond", "dexp", "dnorm", "hold"))
for r in rows:
    print("%-34s %5.1f %6.2f %+8.1f | %s | %+7.1f %+7.1f %+7.1f %5.1f | %s" % (r[0], r[1], r[2], r[3], " ".join("%+6.1f" % x for x in r[4]), r[5], r[6], r[7], r[8], " ".join("%+.1f" % x for x in r[9])))
# exit reason of base on these trades and per-trade capture by reason
from collections import defaultdict
agg = defaultdict(lambda: [0, 0.0, 0.0])
for r in R:
    k = r["v"]["base"][1]; agg[k][0] += 1; agg[k][1] += r["v"]["base"][0]; agg[k][2] += max(r["peak_hold"], 0)
print({k: (v[0], round(100*v[1],1), round(100*v[2],1)) for k, v in agg.items()})
# theta paid vs peak
print("median theta paid pts over hold: exp %.1f norm %.1f" % (np.median([r["theta_paid_pts"] for r in R if r["exp"]]), np.median([r["theta_paid_pts"] for r in R if not r["exp"]])))
json.dump([dict(variant=r[0], win=r[1], mean=r[2], dlog=r[3], per_day=r[4], dcond=r[5], dexp=r[6], dnorm=r[7], hold_min=r[8], cond_days=r[9]) for r in rows], open(W + r"\a6_merge.json", "w"), indent=1)
