"""R14 phase B (after the 15:30 close, same rules: lowprio, one script at a time, < 3 min).
Timings of the bit-identical rewrites proposed in docs/research/13nov/R14_engine_speed.md, measured as the MIN of
repeated runs (robust to pre-emption). Pure numpy / Python on synthetic data of the live sizes: no engine, no shared
memory, no port, no file writes."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions")
import time, math, bisect, gc, numpy as np
from bisect import bisect_right, insort
from apex import greeks
from apex.greeks import _erf_pos, SQRT2
rng = np.random.default_rng(3)
def tmin(fn, reps=9, inner=20):
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(inner): fn()
        best = min(best, (time.perf_counter() - t0) / inner)
    return best * 1000
def row(name, a, b):
    print(f"{name:52s} now {a:8.3f} ms   proposed {b:8.3f} ms   saving {100*(1-b/a):5.1f} %", flush=True)
# 1 implied vol, 84 rows (58 + 26 contracts as on 13 Nov)
exec(open(r"D:\ApexOptions\data\research\13nov\work\R14\iv_fast.py").read())
K = np.r_[np.repeat(np.arange(25600, 25600+29*50, 50),2), np.repeat(np.arange(25600, 25600+13*50, 50),2)].astype(float)
call = np.tile([True, False], len(K)//2); F = np.full(len(K), 26000.0); T = np.r_[np.full(58, 4/365), np.full(26, 10/365)]
price = np.maximum(np.where(call, F-K, K-F), 0) + 30 + rng.random(len(K))*20
assert np.array_equal(greeks.implied_vol(price,F,K,T,call), iv_stacked(price,F,K,T,call), equal_nan=True)
row("implied_vol (stacked erf)", tmin(lambda: greeks.implied_vol(price,F,K,T,call)), tmin(lambda: iv_stacked(price,F,K,T,call)))
row("implied_vol (stacked + in-place buffers)", tmin(lambda: greeks.implied_vol(price,F,K,T,call)), tmin(lambda: iv_inplace(price,F,K,T,call)))
# 2 regime._pct at the close (22,000 samples, twice a second)
hist = [float(abs(x)) for x in rng.normal(20, 8, 22000)]; srt = sorted(hist); x = 21.0
row("regime _pct x2 (22k history)", tmin(lambda: [float(100.0*np.mean(np.fromiter(hist, float) <= x)) for _ in range(2)]),
    tmin(lambda: [float(100.0*(bisect_right(srt, x)/len(srt))) for _ in range(2)]))
# 3 vwap_side_min walk over a 3-hour run vs the run-start index
et = [float(k) for k in range(11000)]; ev = [1.0] * 11000; rs = [0] * 11000
def walk():
    i = len(et) - 1; s0, j = ev[i] > 0, i
    while j > 0 and (ev[j-1] > 0) == s0 and ev[j-1] != 0 and et[j] - et[j-1] <= 120: j -= 1
    return j
row("vwap_side_min (3-hour run on one side)", tmin(walk, inner=5), tmin(lambda: rs[-1]))
# 4 forward view window at 10 Hz
h = [(1e9 + k, 26000.0 + k % 7) for k in range(725)]; ts = [a for a, _ in h]; ps = [b for _, b in h]; now = 1e9 + 725.3
row("fwd view window (725 samples)", tmin(lambda: [px for t, px in h if now - 720 <= t < now - 0.5]),
    tmin(lambda: ps[bisect.bisect_left(ts, now - 720):bisect.bisect_left(ts, now - 0.5)]))
# 5 basis median at 1 Hz (1800 samples)
win = [float(round(v, 2)) for v in rng.normal(30, 3, 1800)]; sw = sorted(win)
row("basis median (1800 samples)", tmin(lambda: float(np.median(win))), tmin(lambda: (sw[899] + sw[900]) / 2.0))
# 6 flow ring sums at 10 Hz
rb = np.zeros((512, 100)); run = np.zeros(512); v = np.zeros(512)
row("flow 10-s ring sums (2 x 512 x 100)", tmin(lambda: (rb.sum(axis=1), rb.sum(axis=1))),
    tmin(lambda: (np.add(run, v, out=run), np.add(run, v, out=run))))
# 7 GC: what a full collection costs on today's tracked-object count is only measurable inside the engine (see report)
print("gc thresholds", gc.get_threshold(), "tracked objects in this script", len(gc.get_objects()), flush=True)
