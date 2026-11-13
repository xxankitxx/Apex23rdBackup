import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions")
import time, math, numpy as np
from apex.table import ROW_DTYPE
from apex.engine.market import Market, WIN
from apex.engine.flow import Flow
from apex import greeks, config
rng = np.random.default_rng(1)
N = config.MAX_ROWS; USED = 137
def mk_snap(t):
    s = np.zeros(N, dtype=ROW_DTYPE)
    s["ltp"][:USED] = 100 + rng.random(USED); s["bid"][:USED] = s["ltp"][:USED]-0.5; s["ask"][:USED] = s["ltp"][:USED]+0.5
    s["ttq"][:USED] = 1e5 + t*10 + rng.integers(0,50,USED); s["bqty"][:USED]=500; s["aqty"][:USED]=600
    s["bq"][:USED] = rng.random((USED,5))*1000; s["aq"][:USED] = rng.random((USED,5))*1000
    s["bo"][:USED] = 5; s["ao"][:USED] = 6; s["depth_ns"][:USED] = int(t*1e9); s["tbq"][:USED]=1e6; s["tsq"][:USED]=1.1e6
    s["recv_ns"][:USED] = int(t*1e9)
    return s
snaps = [mk_snap(1.7e9 + 0.1*k) for k in range(50)]
def bench(fn, n):
    t0 = time.perf_counter()
    for k in range(n): fn(k)
    return (time.perf_counter()-t0)/n*1000
# snapshot copy cost
rows = snaps[0]
print("snapshot copy x2 (ms)", round(bench(lambda k: (rows.copy(), rows["seq"].copy(), rows["seq"].copy()), 300), 3))
m = Market(); f = Flow(N); m.mid_rows=(0,)
for k in range(700): m.push(snaps[k%50], 1.7e9+0.1*k); f.update(m, 0.1)
T=[0]
def step(k):
    T[0]+=0.1; m.push(snaps[k%50], 1.7e9+70+T[0]); f.update(m, 0.1)
print("Market.push (ms)", round(bench(lambda k: m.push(snaps[k%50], 1.7e9+200+0.1*k), 300),3))
print("Flow.update (ms)", round(bench(lambda k: f.update(m, 0.1), 300),3))
# transposed ring layout: column write cost comparison
A = np.full((N, WIN), np.nan); B = np.full((WIN, N), np.nan); v = np.ones(N)
print("8 col writes C-order (n,WIN) ms", round(bench(lambda k: [A.__setitem__((slice(None), k%WIN), v) for _ in range(8)], 2000),4))
print("8 row writes (WIN,n) ms", round(bench(lambda k: [B.__setitem__(k%WIN, v) for _ in range(8)], 2000),4))
print("rb.sum axis1 (512,100) x2 ms", round(bench(lambda k: (f._rb.sum(axis=1), f._rs.sum(axis=1)), 2000),4))
# greeks: 84 options (58 + 26)
K = np.r_[np.repeat(np.arange(25600, 25600+29*50, 50),2), np.repeat(np.arange(25600, 25600+13*50, 50),2)].astype(float)
call = np.tile([True, False], len(K)//2)
F = np.full(len(K), 26000.0); T = np.r_[np.full(58, 4/365), np.full(26, 10/365)]
from apex.greeks import _erf_pos, SQRT2
price = np.maximum(np.where(call, F-K, K-F), 0) + 30 + rng.random(len(K))*20
print("implied_vol 84 rows ms", round(bench(lambda k: greeks.implied_vol(price, F, K, T, call), 200),3))
iv = greeks.implied_vol(price, F, K, T, call)
print("greeks 84 rows ms", round(bench(lambda k: greeks.greeks(F, K, T, iv, call), 500),3))
def iv_stacked(price, F, K, T, is_call, iters=40):
    price = np.asarray(price, dtype=float); K = np.asarray(K, dtype=float); is_call = np.asarray(is_call, dtype=bool)
    F = np.broadcast_to(np.asarray(F, dtype=float), price.shape)
    intrinsic = np.where(is_call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    valid = (price > intrinsic + 0.05) & (price > 0) & np.isfinite(price)
    out = np.full(price.shape, np.nan)
    if not valid.any(): return out
    Tv = np.broadcast_to(np.asarray(T, dtype=float), price.shape)[valid]
    pv, Fv, Kv, cv = price[valid], F[valid], K[valid], is_call[valid]
    sqrtT = np.sqrt(np.maximum(Tv, 1e-8)); lnFK = np.log(Fv / Kv)
    lo = np.full(pv.shape, 0.005); hi = np.full(pv.shape, 5.0)
    n = pv.shape[0]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        sig = np.maximum(mid, 1e-4)
        sT = sig * sqrtT
        d1 = (lnFK + 0.5 * sT * sT) / sT
        d2 = d1 - sT
        x = np.concatenate((d1, d2)) / SQRT2
        e = np.sign(x) * _erf_pos(np.abs(x))
        nn = 0.5 * (1.0 + e); mm = 0.5 * (1.0 - e)
        call = Fv * nn[:n] - Kv * nn[n:]
        put = Kv * mm[n:] - Fv * mm[:n]
        below = np.where(cv, call, put) < pv
        lo = np.where(below, mid, lo); hi = np.where(below, hi, mid)
    out[valid] = 0.5 * (lo + hi)
    return out
a = greeks.implied_vol(price, F, K, T, call); b = iv_stacked(price, F, K, T, call)
print("stacked identical:", np.array_equal(a, b, equal_nan=True))
print("implied_vol stacked ms", round(bench(lambda k: iv_stacked(price, F, K, T, call), 200),3))
# random stress of identity
ok = True
for r in range(200):
    pr = np.maximum(np.where(call, F-K, K-F), 0) + rng.random(len(K))*80
    FF = np.full(len(K), 25500 + rng.random()*1000)
    if not np.array_equal(greeks.implied_vol(pr, FF, K, T, call), iv_stacked(pr, FF, K, T, call), equal_nan=True): ok=False
print("stacked identical over 200 random chains:", ok)
