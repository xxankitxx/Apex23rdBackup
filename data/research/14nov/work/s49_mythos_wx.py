"""The holdout year's real 1-minute option bars (MYTHOS history.db, read-only) in the arena's hist_wx format, so the
holdout sessions that have them can be priced on real IV. Futures and heavyweights are not added (M stays None)."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import pandas as pd
import lab1
OUT = "D:/ApexOptions/data/research/hist_wx_mythos"
os.makedirs(OUT, exist_ok=True)
o = lab1._tab("opt")
n = 0
for day, g in o.groupby("day"):
    if not ("2024-11-14" <= day <= "2025-11-13"):
        continue
    g = g[g.expiry == g.expiry.min()]
    df = pd.DataFrame({"datetime": g.ts, "open": g.o, "high": g.h, "low": g.l, "close": g.c, "volume": g.v, "open_interest": g.oi,
                       "what": "opt:" + g.strike.astype(int).astype(str) + ":" + g.right})
    p = os.path.join(OUT, f"{day}.parquet")
    df.to_parquet(p + ".tmp"); os.replace(p + ".tmp", p)
    n += 1
print("holdout sessions with real option bars:", n)
