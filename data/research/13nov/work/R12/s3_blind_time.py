"""While the Conductor is flat, how many of its 5 pool books are themselves flat (able to arm and fire)?
A pool book holding its own shadow copy does not run its pullback machine (c20_08.on_second returns in the hold branch),
so it cannot trigger. Blind = Conductor flat and all 5 books holding."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections
import numpy as np, pandas as pd
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "t_in", "t_out", "ret_pct", "dte_in"])
df = df[df.book.isin(POOL)]
sim = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
simr = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"))["days"]
out = []
tot = collections.Counter()
for day in sorted(df.day.unique()):
    src = simr if day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03") else sim
    ct = (src.get(day) or {}).get("trades") or []
    y, m, d = map(int, day.split("-"))
    t0 = datetime(y, m, d, 9, 30, tzinfo=IST).timestamp()   # 09:30: the 20-min impulse needs history
    exp = bool((df[df.day == day].dte_in == 0).any())
    t1 = datetime(y, m, d, 14, 40 if exp else 15, tzinfo=IST).timestamp()
    S = np.arange(t0, t1)
    cflat = np.ones(len(S), bool)
    for t in ct:
        cflat[(S >= t["t_in"]) & (S < t["t_out"])] = False
    nflat = np.full(len(S), 5)
    for b in POOL:
        h = np.zeros(len(S), bool)
        for _, r in df[(df.day == day) & (df.book == b)].iterrows():
            h |= (S >= r.t_in) & (S < r.t_out)
        nflat -= h
    c = collections.Counter(nflat[cflat])
    for k, v in c.items(): tot[k] += v
    out.append(dict(day=day, expiry=exp, flat_min=round(cflat.sum() / 60), flat_share=round(cflat.mean(), 2),
                    blind_min=round(c.get(0, 0) / 60), one_or_two_min=round((c.get(1, 0) + c.get(2, 0)) / 60),
                    all5_min=round(c.get(5, 0) / 60)))
for r in out: print(r)
s = sum(tot.values())
print("Conductor flat seconds by number of pool books able to fire:", {k: f"{100*v/s:.1f}%" for k, v in sorted(tot.items())}, "total flat min", round(s / 60))
json.dump(out, open(r"D:\ApexOptions\data\research\13nov\work\R12\s3_blind_time.json", "w"), indent=1)
