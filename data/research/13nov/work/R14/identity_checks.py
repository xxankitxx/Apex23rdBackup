"""R14: bit-identity checks of the proposed rewrites on synthetic data (no engine, no shared memory)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions")
import bisect, numpy as np
from bisect import bisect_right, insort
rng = np.random.default_rng(7)
ok_all = True
def check(name, ok):
    global ok_all; ok_all &= ok; print(f"{name}: {'IDENTICAL' if ok else 'DIFFERENT'}", flush=True)

# 1 regime._pct: np.mean(np.fromiter(hist) <= x) vs a sorted mirror + bisect_right
def pct_old(hist, x):
    if len(hist) < 60 or x is None: return None
    a = np.fromiter(hist, float); return float(100.0 * np.mean(a <= x))
def pct_new(srt, n, x):
    if n < 60 or x is None: return None
    return float(100.0 * (bisect_right(srt, x) / n))
hist, srt, ok = [], [], True
for k in range(6000):
    v = float(abs(rng.normal(20, 8))) if k % 7 else float(round(rng.normal(20, 8), 1))   # ties too
    x = float(abs(rng.normal(20, 8)))
    if pct_old(hist, x) != pct_new(srt, len(hist), x): ok = False; break
    hist.append(v); insort(srt, v)
check("regime _pct (sorted mirror + bisect)", ok)

# 2 weather._base3 vwap_side_min: backward walk vs an incremental run-start index
def walk(et, ev, t):
    i = bisect_right(et, t) - 1
    if i >= 0 and t - et[i] <= 5.0 and ev[i] != 0:
        s0, j = (ev[i] > 0), i
        while j > 0 and (ev[j - 1] > 0) == s0 and ev[j - 1] != 0 and et[j] - et[j - 1] <= 120:
            j -= 1
        return round((t - et[j]) / 60.0, 1)
    return None
def fast(et, ev, rs, t):
    i = bisect_right(et, t) - 1
    if i >= 0 and t - et[i] <= 5.0 and ev[i] != 0:
        return round((t - et[rs[i]]) / 60.0, 1)
    return None
et, ev, rs, ok, t = [], [], [], True, 0.0
side = 1
for k in range(20000):
    t += 1.0 + (130.0 if rng.random() < 0.002 else 0.0)
    if rng.random() < 0.01: side = -side
    v = 0.0 if rng.random() < 0.003 else side * float(rng.random() * 30)
    et.append(t); ev.append(v)
    j = len(ev) - 1
    rs.append(rs[j - 1] if (j > 0 and ev[j] != 0 and ev[j - 1] != 0 and (ev[j - 1] > 0) == (ev[j] > 0)
                            and et[j] - et[j - 1] <= 120) else j)
    if k % 3 == 0:
        q = t + float(rng.random() * 3)
        if walk(et, ev, q) != fast(et, ev, rs, q): ok = False; break
check("vwap_side_min (run-start index)", ok)

# 3 engine._fwd_view: list comprehension window vs bisect slice (time-sorted deque)
SPOT_DC_S = 720
h, ok = [], True
t = 1e9
for k in range(5000):
    t += 1.0 if rng.random() > 0.01 else 0.4
    h.append((t, 26000 + float(rng.normal()) * 5))
    while h and t - h[0][0] > SPOT_DC_S + 5: h.pop(0)
    now = t + float(rng.random())
    xs = [px for tt, px in h if now - SPOT_DC_S <= tt < now - 0.5]
    ts = [tt for tt, _ in h]; ps = [px for _, px in h]
    ys = ps[bisect.bisect_left(ts, now - SPOT_DC_S):bisect.bisect_left(ts, now - 0.5)]
    if xs != ys: ok = False; break
check("fwd view window (bisect slice)", ok)

# 4 engine._feed_fwd: np.median of the 30-min basis window vs a sorted window (insort / remove)
from collections import deque
win, srt, ok = deque(), [], True
for k in range(4000):
    v = float(round(rng.normal(30, 3), 2))
    win.append(v); insort(srt, v)
    if len(win) > 1800:
        old = win.popleft(); del srt[bisect.bisect_left(srt, old)]
    n = len(srt)
    med = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0
    if float(np.median(list(win))) != float(med): ok = False; print("diff at", k, np.median(list(win)), med); break
check("basis median (sorted window)", ok)

# 5 flow.update 10-s ring sums: sum(axis=1) vs a running sum (integer volumes)
n, W = 512, 100
rb = np.zeros((n, W)); run = np.zeros(n); kk = 0; ok = True
for k in range(3000):
    kk = (kk + 1) % W
    v = np.where(rng.random(n) < 0.3, rng.integers(0, 5000, n).astype(float) * 25.0, 0.0)
    run += v - rb[:, kk]
    rb[:, kk] = v
    if not np.array_equal(rb.sum(axis=1), run): ok = False; break
check("flow 10-s ring sums (running sum, integer lots)", ok)
print("ALL IDENTICAL" if ok_all else "SOME DIFFER")
