import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R02")
import numpy as np, runpy, pathlib_r02 as L
n = 3000; t = 1.7e9 + np.arange(n); rng = np.random.default_rng(1)
F = 24000 + np.cumsum(rng.normal(0, 1, n)); bid = np.clip(60 + 0.6 * (F - F[0]) + rng.normal(0, .3, n), 1, None)
p = dict(t=t, bid=bid, ask=bid + 1, F=F, fs=L.ema(F, .2), iv=np.full(n, .12), delta=np.full(n, .6), T=np.full(n, .01), ce=True, exp=True, atr=3.0, ia=n - 1, e=61.0, ok=1.0)
p["theta_min"] = np.full(n, -0.5)
g = runpy.run_path(r"D:\ApexOptions\data\research\13nov\work\R02\a4_paths.py", run_name="not_main") if False else None
src = open(r"D:\ApexOptions\data\research\13nov\work\R02\a4_paths.py", encoding="utf-8").read().split("trades = json.load")[0]
ns = {"__name__": "x"}; exec(compile(src.replace("import pathlib_r02 as L", "import pathlib_r02 as L"), "a4", "exec"), ns)
for exp in (True, False):
    p["exp"] = exp
    for name, V in ns["VARIANTS"].items():
        row, why = L.sim(p, ns["resolve"](V, p), "c20_9x")
print("all", len(ns["VARIANTS"]), "variants ran on both modes")
