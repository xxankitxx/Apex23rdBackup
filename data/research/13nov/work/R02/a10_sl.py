"""Tighter premium stops, exact from the trade table up to the LTP/bid gap: a stop at -x fires iff the hold's worst
bid reached entry(1-x); worst bid ~ worst LTP - half the entry spread. Then ret = -x. Wider stops are not evaluable here."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
J = pd.read_pickle(W + r"\conductor_joined.pkl")
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
SPLIT = "2026-11-05"
def prep(d):
    d = d.copy(); d["ret"] = d.ret_pct / 100; d["exp"] = d.day == d.expiry
    half = 0.5 * (d.entry_ask - d.entry_bid).clip(lower=0).fillna(0)
    d["wb"] = (d.worst_pts - half) / d.entry
    return d
for name, d in (("conductor", prep(J)), ("pool5", prep(df[df.book.isin(['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t'])]))):
    print("==", name)
    for mode in ("exp", "norm"):
        for x in (0.06, 0.08, 0.10, 0.12):
            on = d.exp if mode == "exp" else ~d.exp
            hit = on & (d.wb <= -x) & (d.ret > -x)
            r = np.where(hit, -x, d.ret)
            dl = np.log1p(r) - np.log1p(d.ret); e = (d.day < SPLIT).values
            print("  %s SL %.0f%%: disc %+.0f test %+.0f | changed %d, of which winners cut %d | win %.1f -> %.1f" % (
                mode, 100 * x, 100 * dl[e].sum(), 100 * dl[~e].sum(), int(hit.sum()), int((hit & (d.ret > 0)).sum()), 100 * (d.ret > 0).mean(), 100 * (r > 0).mean()))
