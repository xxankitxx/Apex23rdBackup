"""The champion's own entries as an arena generator (the replica checked against the recorded trades: 0.999 / 0.986):
normal days the 20-minute pullback (40 points, 50-75 % retrace inside 15 minutes, 5-point resumption), expiry days
the 10-minute breakout with 20 points in 150 s. Its exits are the arena's defaults (the champion's ladder)."""
import sys
sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import fam, lab1s


def signals(ctx):
    D, X = ctx["D"], ctx["X"]
    if D["dte0"]:
        return lab1s.sig_exp(D, X)
    return fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)
