import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Exit twins already in the replay: books with the same entry logic and different exits (docs/28 section 10).
Per day: compounded book return (all-in, trades in time order), strike rate; early (19 Oct - 4 Nov) vs late (5 - 12 Nov)."""
import json
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
df["ret"] = df["ret_pct"] / 100.0
SPLIT = "2026-11-05"
PAIRS = {"c20_9x": ["c20_9t", "c20_9v", "c20_9e", "c20_9h", "c20_8x", "c20_9x_r004"],
         "c20_9y": ["fx_c20_9y", "fr_c20_9y", "rx_c20_9y"]}
days = sorted(df.day.unique())
def bookday(b):
    s = df[df.book == b].sort_values("t_in")
    g = s.groupby("day")["ret"]
    d = g.apply(lambda r: np.prod(1 + r) - 1).reindex(days).fillna(0.0)
    return d, s
out = {}
for base, twins in PAIRS.items():
    if base not in set(df.book):
        continue
    db, sb = bookday(base)
    print(f"\n== {base}: trades {len(sb)}, win {100*(sb.ret>0).mean():.1f} %, early sum of day % {100*db[db.index<SPLIT].sum():+.0f}, late {100*db[db.index>=SPLIT].sum():+.0f}")
    for tw in twins:
        if tw not in set(df.book):
            print("  (missing)", tw); continue
        dt, st = bookday(tw)
        diff = dt - db
        e, l = diff[diff.index < SPLIT], diff[diff.index >= SPLIT]
        rec = dict(trades=len(st), win=round(100 * (st.ret > 0).mean(), 1), base_win=round(100 * (sb.ret > 0).mean(), 1),
                   early_days_better=int((e > 0.001).sum()), early_days_worse=int((e < -0.001).sum()), early_sum_diff=round(100 * e.sum(), 1),
                   late_days_better=int((l > 0.001).sum()), late_days_worse=int((l < -0.001).sum()), late_sum_diff=round(100 * l.sum(), 1),
                   losing_days=int((dt < 0).sum()), base_losing_days=int((db < 0).sum()),
                   worst_day=round(100 * dt.min(), 1), base_worst_day=round(100 * db.min(), 1),
                   per_day_diff={k: round(100 * v, 1) for k, v in diff.items()})
        out[f"{tw} vs {base}"] = rec
        print(f"  {tw:12s} trades {rec['trades']:3d} win {rec['win']:5.1f} (base {rec['base_win']}) | early: better/worse days {rec['early_days_better']}/{rec['early_days_worse']} "
              f"sum of day % {rec['early_sum_diff']:+.1f} | late: {rec['late_days_better']}/{rec['late_days_worse']} {rec['late_sum_diff']:+.1f} | losing days {rec['losing_days']} (base {rec['base_losing_days']}) worst {rec['worst_day']} (base {rec['base_worst_day']})")
        print("     per day diff:", " ".join(f"{k[5:]}:{v:+.0f}" for k, v in rec["per_day_diff"].items()))
json.dump(out, open(W + r"\a5_twins.json", "w"), indent=1)
