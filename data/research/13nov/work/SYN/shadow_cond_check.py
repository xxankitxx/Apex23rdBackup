"""13 Nov: the shadow Conductors (conductor_sl, conductor_wp60) through the offline account simulator on the 17 p44
days, pool on every day (APEX_POOL_ASOF=all), against the plain Conductor. Strike rate first. Read-only on the runs."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio  # noqa
sys.path.insert(0, r"D:\ApexOptions")
import os
from apex.conductor import account_sim as A, diary
from apex.engine import conductor as cond
B = r"D:\ApexOptions\data\replay\batch"
RUN = {"2026-10-19": "g1", "2026-10-21": "g1", "2026-10-22": "g2", "2026-10-23": "g2", "2026-10-26": "g3", "2026-10-27": "g3",
       "2026-10-28": "r1", "2026-10-29": "g4", "2026-10-30": "r2", "2026-11-02": "r3", "2026-11-03": "r4", "2026-11-04": "g6",
       "2026-11-05": "g7", "2026-11-06": "g7", "2026-11-09": "g8", "2026-11-11": "g8", "2026-11-12": "g9"}
days = {}
for rd in sorted(set(RUN.values())):
    b, _ = diary.load_days(os.path.join(B, "p44_" + rd))
    days.update({d: v for d, v in b.items() if RUN.get(d) == rd})
pool = cond.load_pool()
for pol in (None, "sidelock", "whipsaw"):
    res = A.simulate(days, pool, "all", policy=pol)
    for win, sel in (("early", lambda d: d < "2026-11-05"), ("late", lambda d: d >= "2026-11-05")):
        ds = [d for d in sorted(res) if sel(d)]
        n = sum(res[d]["n"] for d in ds); w = sum(res[d]["wins"] for d in ds)
        rets = [res[d]["ret_day_pct"] for d in ds]
        print(f"{pol or 'conductor':9s} {win:5s} trades {n:3d} strike {100*w/max(n,1):5.1f} % sum {sum(rets):8.1f} worst {min(rets):6.1f} losing days {sum(r < 0 for r in rets)}")
    print("   per day:", " ".join(f"{d[5:]}:{res[d]['ret_day_pct']:+.1f}" for d in sorted(res)))
