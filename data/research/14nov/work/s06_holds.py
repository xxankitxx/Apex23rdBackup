"""The owner's hold questions, on the Conductor's own trades: what do non-movers and early losers end as?"""
import sys, json; sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
C = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
rows = []
for day in FL.days():
    D = FL.load_day(day)
    for t in (C.get(day, {}).get("trades") or []):
        a = int(round(t["t_in"] - D["t_open"])); b = int(round(t["t_out"] - D["t_open"]))
        j = np.flatnonzero(D["K"] == int(t["strike"]))
        if not len(j) or a < 1 or b <= a:
            continue
        c = 0 if t["rr"] == "CE" else 1
        bid = FL._ffill0(D["opt"][a:b + 1, int(j[0]), c, 0].astype(float))
        e = t["entry"]
        r = 100 * (bid / e - 1)
        pk = np.fmax.accumulate(np.where(np.isfinite(r), r, -99))
        d = dict(day=day, dte0=D["dte0"], ret=t["ret_pct"], hold=(b - a) / 60.0, reason=t["reason"].replace("COUNCIL ", ""), peak=float(np.nanmax(r)))
        for m in (120, 300, 600, 900):
            d[f"r{m}"] = float(r[m]) if len(r) > m else np.nan
            d[f"pk{m}"] = float(pk[m]) if len(r) > m else np.nan
        rows.append(d)
T = pd.DataFrame(rows)
for nm, g in (("NORMAL days", T[~T.dte0]), ("EXPIRY days", T[T.dte0])):
    print(f"\n=== {nm}: {len(g)} Conductor trades, win {100 * (g.ret > 0).mean():.0f} %, mean {g.ret.mean():+.1f} %, median hold {g.hold.median():.0f} min ===")
    print("exit reasons:", g.reason.value_counts().to_dict())
    L = g[g.ret <= 0]; Wn = g[g.ret > 0]
    print(f"losers: {len(L)}, mean {L.ret.mean():+.1f} %, median hold {L.hold.median():.0f} min, held over 15 min: {int((L.hold > 15).sum())}; peak before losing: median {L.peak.median():+.1f} %")
    print(f"winners: {len(Wn)}, mean {Wn.ret.mean():+.1f} %, median hold {Wn.hold.median():.0f} min")
    for m, lab in ((300, "5 min"), (600, "10 min"), (900, "15 min")):
        h = g[g[f"r{m}"].notna()]
        st = h[(h[f"r{m}"].abs() < 4) & (h[f"pk{m}"] < 8)]
        dn = h[h[f"r{m}"] <= -6]
        up = h[h[f"r{m}"] >= 6]
        f = lambda x: f"n {len(x):3d}  later won {100 * (x.ret > 0).mean() if len(x) else float('nan'):3.0f} %  final mean {x.ret.mean() if len(x) else float('nan'):+6.1f} %  if sold then {x[f'r{m}'].mean() if len(x) else float('nan'):+6.1f} %"
        print(f"  still open at {lab}: {len(h)}")
        print(f"     non-mover (within +-4 %, never above +8 %): {f(st)}")
        print(f"     down 6 % or more:                          {f(dn)}")
        print(f"     up 6 % or more:                            {f(up)}")
T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\cond_holds.parquet")
