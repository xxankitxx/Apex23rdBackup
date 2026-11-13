import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions")
import time, math, json, gc, numpy as np
from apex import greeks
from apex.greeks import _erf_pos, SQRT2
rng = np.random.default_rng(2)
def tmin(fn, reps=7, inner=20):
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(inner): fn()
        best = min(best, (time.perf_counter() - t0) / inner)
    return best * 1000
K = np.r_[np.repeat(np.arange(25600, 25600+29*50, 50),2), np.repeat(np.arange(25600, 25600+13*50, 50),2)].astype(float)
call = np.tile([True, False], len(K)//2)
F = np.full(len(K), 26000.0); T = np.r_[np.full(58, 4/365), np.full(26, 10/365)]
price = np.maximum(np.where(call, F-K, K-F), 0) + 30 + rng.random(len(K))*20
exec(open(r"D:\ApexOptions\data\research\13nov\work\R14\iv_fast.py").read())
print("IV identical:", np.array_equal(greeks.implied_vol(price,F,K,T,call), iv_stacked(price,F,K,T,call), equal_nan=True),
      np.array_equal(greeks.implied_vol(price,F,K,T,call), iv_inplace(price,F,K,T,call), equal_nan=True), flush=True)
a = tmin(lambda: greeks.implied_vol(price, F, K, T, call)); b = tmin(lambda: iv_stacked(price, F, K, T, call)); c = tmin(lambda: iv_inplace(price, F, K, T, call))
print(f"implied_vol min ms: original {a:.3f}  stacked {b:.3f}  stacked+inplace {c:.3f}", flush=True)
# greek dict loop (compute_greeks tail) for 84 rows
ivl = list(np.r_[price]/100); isf, rnd = math.isfinite, round
def loop():
    g = {}
    for j in range(84):
        g[j] = {"iv": rnd(ivl[j],2), "delta": rnd(ivl[j],3), "theta_min": rnd(ivl[j],4), "vega": rnd(ivl[j],2), "gamma": rnd(ivl[j],5)}
print(f"greek dict loop 84 rows ms {tmin(loop):.3f}", flush=True)
# photo-size dict json dumps
photo = {f"k{i}": (rng.random() if i % 3 else None) for i in range(457)}
print(f"json.dumps 457-field photo ms {tmin(lambda: json.dumps(photo, default=str)):.3f}  bytes {len(json.dumps(photo))}", flush=True)
# _p_books-like loop: 107 books x trades
class Bk: pass
books = {}
for i in range(107):
    b = Bk(); b.p = {"gen": None}; b.pos = None
    b.trades = [{"pnl_rs": rng.normal(), "t_out": 1e9 + j, "rr": "CE" if j % 2 else "PE"} for j in range(12)]
    books[f"b{i}"] = b
def pbooks():
    closed = []
    for name, bk in books.items():
        for tr in bk.trades:
            if tr.get("pnl_rs") is not None and tr.get("t_out") is not None: closed.append(tr)
    same = sorted((x for x in closed if x.get("rr") == "CE"), key=lambda x: x["t_out"])
    return len(closed), sum(1 for x in closed if x["pnl_rs"] > 0)
print(f"_p_books trade scan (107 books x 12 trades) ms {tmin(pbooks):.3f}", flush=True)
# premium_outcome and all_greeks cost
from apex.quant import passage, greeks_hi
po = lambda: passage.premium_outcome(26000.0, 26000.0, 4/365, 0.12, True, 120.0, 0.10, 0.10, 0.02, 0.9)
print(f"passage.premium_outcome ms {tmin(po, reps=5, inner=5):.3f}", flush=True)
print(f"greeks_hi.all_greeks scalar ms {tmin(lambda: greeks_hi.all_greeks(26000.0, 26000.0, 4/365, 0.12, True)):.3f}", flush=True)
# GC: heap like the engine's afternoon: 1500 trade dicts with 457-field photos, deques of tuples
heap = [{f"k{i}": (1.0 if i % 3 else None) for i in range(457)} for _ in range(1500)]
tups = [[(1.0, 2.0, 3.0, None, 0.5, 0.1, -0.2, 7.0) for _ in range(1000)] for _ in range(84)]
gc.collect()
t0 = time.perf_counter(); gc.collect(); full = (time.perf_counter() - t0) * 1000
print(f"tracked objects {len(gc.get_objects())}; one full gc.collect ms {full:.1f}", flush=True)
gc.freeze()
t0 = time.perf_counter(); gc.collect(); fz = (time.perf_counter() - t0) * 1000
print(f"after gc.freeze(): full gc.collect ms {fz:.1f}", flush=True)
