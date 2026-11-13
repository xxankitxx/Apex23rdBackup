import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
J = pd.read_pickle(W + r"\conductor_joined.pkl")
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
SPLIT = "2026-11-05"
def prep(d):
    d = d.copy(); d["ret"] = d.ret_pct / 100; d["pk"] = d.peak_bid / d.entry - 1; d["exp"] = d.day == d.expiry; return d
sets = {"conductor": prep(J), "pool5": prep(df[df.book.isin(['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t'])]),
        "c20 family (all c20 books)": prep(df[df.book.str.contains("c20_")])}
print("plateau: change in sum of log returns (pct pts), discovery | test, trades changed (better/worse)")
for name, d in sets.items():
    line = []
    for x in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        hit = d.exp & (d.pk >= x)
        r = np.where(hit, x, d.ret)
        dl = np.log1p(r) - np.log1p(d.ret)
        e = (d.day < SPLIT).values
        line.append("%.2f: %+.0f | %+.0f (%d/%d)" % (x, 100 * dl[e].sum(), 100 * dl[~e].sum(), int((dl > 1e-9).sum()), int((dl < -1e-9).sum())))
    print(" ", name, "\n    " + "\n    ".join(line))
d = sets["conductor"]; x = 0.60
hit = d.exp & (d.pk >= x); d["r60"] = np.where(hit, x, d.ret)
print(d[hit][["day", "time_in", "book", "pk", "ret", "r60", "reason0"]].round(3).to_string())
dc = lambda s: np.expm1(np.log1p(s).groupby(d.day).sum())
a, b = dc(d.ret), dc(d.r60)
out = pd.DataFrame({"base %": 100 * a, "TP60 %": 100 * b}).round(1)
print(out[out["base %"] != out["TP60 %"]].to_string())
print("account total (compound of day returns on a fresh 1 lakh each day: sum of day %%): base %.0f, TP60 %.0f" % (100 * a.sum(), 100 * b.sum()))
lt = np.log1p(d.r60) - np.log1p(d.ret)
print("without the best changed trade: %+.1f log pts" % (100 * (lt.sum() - lt.max())))
