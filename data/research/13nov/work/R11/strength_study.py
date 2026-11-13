import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R11: the mock's stand strength (20-min slope + VWAP side), with hysteresis (enter |S|>=40, leave |S|<20, hold 90 s).
# Questions: how often does the stand change, how much of the day is it BULL / BEAR / SIDEWAYS, and is the stand
# right about the next 5 / 15 minutes per day (descriptive, so we expect about 50 %). No fitting: nothing to tune.
import glob, os, json
import numpy as np
USE = ["r300", "r600", "r1800", "vwap", "rng", "dhi", "dlo", "kf", "er300", "vr", "hw120", "bank120", "up60", "imb", "ofi120", "tod", "left"]
C = r"D:\ApexOptions\data\research\13nov\work\R11\cache"
out = {}
for f in sorted(glob.glob(os.path.join(C, "*.npz"))):
    d = os.path.basename(f)[:-4]; c = np.load(f)
    F, t, Z = c["F"], c["t"], c["Z"]
    vw = Z[:, USE.index("vwap")]
    n = len(F); k = 40                                  # rows are 30 s apart: 40 rows = 20 min
    sl = np.r_[F[:k] - F[0], F[k:] - F[:-k]]
    raw = 100 * (0.65 * np.tanh(sl / 40) + 0.35 * np.tanh(vw))   # vwap feature is already in volatility units
    S = np.zeros(n); s = 0.0
    for i in range(n):
        s += (raw[i] - s) * 0.25; S[i] = s
    st = np.zeros(n, int); cur, cand, cs = 0, None, 0
    for i in range(n):
        want = 1 if S[i] >= 40 else -1 if S[i] <= -40 else (0 if abs(S[i]) < 20 else cur)
        if want != cur:
            if cand != want: cand, cs = want, i
            elif i - cs >= 3: cur, cand = want, None
        else: cand = None
        st[i] = cur
    r = dict(changes=int((np.diff(st) != 0).sum()), hours=round(n * 30 / 3600, 2),
             bull=round(float((st == 1).mean()), 2), bear=round(float((st == -1).mean()), 2))
    for h, y in (("5", c["y5"]), ("15", c["y15"])):
        m = (st != 0) & np.isfinite(y) & (y != 0)
        r["hit" + h] = None if m.sum() == 0 else round(float(((y[m] > 0) == (st[m] > 0)).mean()), 3)
        r["pts" + h] = None if m.sum() == 0 else round(float(np.mean(np.where(st[m] > 0, y[m], -y[m]))), 1)
        r["n" + h] = int(m.sum())
    out[d] = r
    print(d, r)
h15 = [v["hit15"] for v in out.values() if v["hit15"] is not None]; h5 = [v["hit5"] for v in out.values() if v["hit5"] is not None]
print("mean hit5", round(np.mean(h5), 3), "days>0.5", sum(x > .5 for x in h5), "/", len(h5))
print("mean hit15", round(np.mean(h15), 3), "days>0.5", sum(x > .5 for x in h15), "/", len(h15))
print("changes/day median", np.median([v["changes"] for v in out.values()]))
json.dump(out, open(os.path.join(os.path.dirname(C), "strength_study.json"), "w"), indent=1)
