"""When c20_9y does not take a trigger, the next pool book takes the same signal. Which trades are those, did 9y have
its own position open at the time (busy) or did it refuse (veto), and how did they do? Early vs late days."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, collections
import pandas as pd, numpy as np
df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "t_in", "t_out", "trigger_t", "ret_pct"])
pool = df[df.book.isin(["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"])]
trades = []
for f, keep in (("p44_sim", lambda d: d not in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")), ("p44_simr", lambda d: d in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"))):
    for day, x in json.load(open(rf"D:\ApexOptions\data\replay\batch\{f}\conductor_sim.json"))["days"].items():
        if keep(day):
            for t in x["trades"]: trades.append(dict(t, day=day))
rows = []
for t in trades:
    if t["src"] == "c20_9y": continue
    y = pool[(pool.day == t["day"]) & (pool.book == "c20_9y")]
    busy = bool(((y.t_in <= t["trigger_t"]) & (y.t_out > t["trigger_t"])).any())
    same = pool[(pool.day == t["day"]) & ((pool.trigger_t - t["trigger_t"]).abs() <= 2)]
    rows.append(dict(day=t["day"], time=t["time_in"], src=t["src"], ret=t["ret_pct"], y_busy=busy,
                     books_fired=",".join(sorted(same.book.str.replace("c20_", "")))))
def comp(v):
    r = 1.0
    for x in v: r *= 1 + x / 100
    return 100 * (r - 1)
for r in rows: print(r)
for lab, lo, hi in (("early", "2026-10-19", "2026-11-04"), ("late", "2026-11-05", "2026-11-12")):
    s = [r for r in rows if lo <= r["day"] <= hi]
    v = [r for r in s if not r["y_busy"]]
    print(f"{lab}: non-9y owners {len(s)}; 9y refused (not busy) {len(v)}: won {sum(r['ret'] > 0 for r in v)}, compounded {comp([r['ret'] for r in v]):+.1f}%, days {len(set(r['day'] for r in v))}")
json.dump(rows, open(r"D:\ApexOptions\data\research\13nov\work\R12\s6_owner_handoff.json", "w"), indent=1)
