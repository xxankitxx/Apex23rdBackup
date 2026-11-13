import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 PHASE B step 3 (after the close; needs s8_trade_gap.parquet built on ALL parts by phaseB_ms_alldays.py eval).
Pre-registered yes/no vetoes on the c20 pool books' trades and on the Conductor's own trades, discovered on
19 Oct - 4 Nov, tested on 5 - 11 Nov (ds_v2 has no 12 Nov). Variants are fixed here, before the run:
  V1  veto when the forward's own move in the 5 s before the trigger, with the trade, is below the early 33rd pct
  V2  veto when it is below the early median
  V3  veto when the future is AHEAD of the forward at the trigger (gap_dev_w < early 33rd pct)
  V4  veto when the future is far BEHIND the forward (gap_dev_w > early 67th pct)
  V5  veto when the forward fell back after the fill decision window: NOT allowed (uses rows after the trigger) - listed
      only to state that it was not tried.
Six variants x two universes = 8 tests; report every one (multiple testing). A veto removes the trade (the freed
account taking a later trade is not modelled for the pool universe; for the Conductor universe it is also not
modelled, so the Conductor numbers are an upper bound on the harm and a rough guide to the gain).
Report per test day, strike rate first, return compounded per day (all-in), losing days, and the owner's checks:
positive without its best trade and without its best day."""
import json
import numpy as np, pandas as pd

W = r"D:\ApexOptions\data\research\13nov\work\R07"
B = r"D:\ApexOptions\data\replay\batch"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
R4 = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
G = pd.read_parquet(f"{W}\\s8_trade_gap.parquet")
G["day"] = G["day"].astype(str); G["t_in"] = G["t_in"].astype(float)
rows = []
for run, keep in (("p44_sim", lambda d: d not in R4), ("p44_simr", lambda d: d in R4)):
    j = json.load(open(f"{B}\\{run}\\conductor_sim.json"))
    for d, v in j["days"].items():
        if keep(d):
            for t in v.get("trades", []):
                rows.append(dict(day=d, book=t["src"], t_in=float(t["t_in"]), ret=float(t["ret_pct"])))
C = pd.DataFrame(rows).merge(G.drop(columns=["ret_pct"]), on=["day", "book", "t_in"], how="inner")
P = G[G.book.isin(POOL)].rename(columns={"ret_pct": "ret"})


def comp(r):
    return 100 * (np.prod(1 + np.asarray(r) / 100) - 1)


def card(df):
    if df.empty:
        return "n 0"
    per = df.groupby("day")["ret"].apply(comp)
    best_t = df.ret.idxmax()
    no_bt = df.drop(index=best_t)
    no_bd = df[df.day != per.idxmax()]
    return (f"n {len(df)}  strike {100 * (df.ret > 0).mean():.0f}%  return {comp(per.values):+.1f}%  losing days {int((per < 0).sum())}"
            f"  worst day {per.min():+.1f}%  w/o best trade {comp(no_bt.groupby('day')['ret'].apply(comp).values):+.1f}%"
            f"  w/o best day {comp(no_bd.groupby('day')['ret'].apply(comp).values):+.1f}%  per day "
            + str({d[5:]: round(v, 1) for d, v in per.items()}))


for nm, U in (("POOL books (each book's own trades, pooled)", P), ("CONDUCTOR trades", C)):
    E, L = U[U.day <= "2026-11-04"], U[U.day > "2026-11-04"]
    print(f"\n==== {nm}: early {len(E)} trades, late {len(L)}")
    print("  base early:", card(E)); print("  base late: ", card(L))
    e_f5, e_g = E.fwd5_w.dropna(), E.gap_dev_w.dropna()
    V = {"V1": ("fwd5_w", "below", np.percentile(e_f5, 33.3)), "V2": ("fwd5_w", "below", np.median(e_f5)),
         "V3": ("gap_dev_w", "below", np.percentile(e_g, 33.3)), "V4": ("gap_dev_w", "above", np.percentile(e_g, 66.7))}
    for k, (c, side, cut) in V.items():
        veto = (U[c] < cut) if side == "below" else (U[c] > cut)
        K = U[~veto.fillna(False)]
        print(f"  {k} veto {c} {side} {cut:+.2f}:")
        print("     early:", card(K[K.day <= "2026-11-04"]))
        print("     late: ", card(K[K.day > "2026-11-04"]))
