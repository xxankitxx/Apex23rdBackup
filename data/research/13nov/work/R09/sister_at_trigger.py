import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R09: clean sister measures at each trade's entry second (from the per-second panel, not the engine's photograph),
on the days that have a panel. Signed in the trade's direction. AUC winner vs loser, and the next-N-second NF futures
move in the trade's direction (does the sister predict the follow-through the option needs?).
Usage: py -3.13 sister_at_trigger.py [day ...]  (default: every day with a panel)"""
import glob, json, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sister_io import load, mid  # noqa: E402
D = r"D:\ApexOptions\data\research\13nov\work\R09\sister"
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
days = sys.argv[1:] or sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(D, "2026-*.npz"))})
df = pd.read_parquet(P, columns=["day", "book", "t_in", "dir", "ret_pct", "wx_bn60", "wx_fn60", "wx_bank_z"], filters=[("day", "in", days)])
rows = []
for d in days:
    t, X, A = load(d)
    NF, BF, FF = mid(X, A, 1, 1), mid(X, A, 5, 3), mid(X, A, 9, 5)
    N = np.where(A[:, 0] <= 5, X[:, 0], np.nan); BN = np.where(A[:, 2] <= 5, X[:, 4], np.nan); FN = np.where(A[:, 4] <= 5, X[:, 8], np.nan)
    VIX = X[:, 12]
    sub = df[df.day == d]
    for r in sub.itertuples():
        i = int(r.t_in) - int(t[0])
        if i < 300 or i >= len(t) - 1:
            continue
        sg = 1.0 if r.dir > 0 else -1.0
        o = dict(day=d, book=r.book, ret=r.ret_pct, win=r.ret_pct > 0, wx_bn60=r.wx_bn60, wx_fn60=r.wx_fn60, wx_bank_z=r.wx_bank_z)

        def ret(x, L):
            a, b = x[i], x[i - L]
            return sg * 1e4 * np.log(a / b) if a > 0 and b > 0 else np.nan
        for L in (5, 15, 30, 60, 300):
            o[f"nf{L}"] = ret(NF, L); o[f"bf{L}"] = ret(BF, L); o[f"ff{L}"] = ret(FF, L)
            o[f"bn{L}"] = ret(BN, L); o[f"fn{L}"] = ret(FN, L); o[f"n{L}"] = ret(N, L)
            o[f"rsb{L}"] = o[f"bf{L}"] - 0.75 * o[f"nf{L}"]; o[f"rsf{L}"] = o[f"ff{L}"] - 0.85 * o[f"nf{L}"]
            o[f"sis{L}"] = 0.5 * (o[f"bf{L}"] + o[f"ff{L}"])
        o["vix60"] = -sg * (VIX[i] - VIX[i - 60]) if VIX[i] > 0 and VIX[i - 60] > 0 else np.nan
        for h in (30, 60, 180):
            j = min(i + h, len(t) - 1)
            o[f"fwd{h}"] = sg * (NF[j] - NF[i]) if NF[j] > 0 and NF[i] > 0 else np.nan
        rows.append(o)
R = pd.DataFrame(rows)
R.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R09\at_trigger.parquet")


def auc(x, y):
    m = np.isfinite(x); x, y = x[m], y[m]
    if len(x) < 20 or y.all() or (~y).all():
        return None
    rk = pd.Series(x).rank().values; n1 = y.sum(); n0 = len(y) - n1
    return round(float((rk[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), 3)


def corr(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    return round(float(np.corrcoef(x[m], y[m])[0, 1]), 3) if m.sum() > 20 else None


out = {}
feats = [c for c in R.columns if c[:2] in ("nf", "bf", "ff", "bn", "fn", "n1", "n3", "n5", "n6", "rs", "si", "vi", "wx") and not c.startswith("fwd")]
for name, S in (("all_books", R), ("pool", R[R.book.isin(POOL)])):
    res = {}
    for f in feats:
        x = S[f].values.astype(float)
        res[f] = dict(auc=auc(x, S.win.values), auc_by_day=[auc(S.loc[S.day == d, f].values.astype(float), S.loc[S.day == d, "win"].values) for d in days],
                      c_fwd60=corr(x, S.fwd60.values.astype(float)), c_fwd180=corr(x, S.fwd180.values.astype(float)))
    out[name] = dict(n=len(S), wins=int(S.win.sum()), res=res)
json.dump(out, open(r"D:\ApexOptions\data\research\13nov\work\R09\at_trigger_results.json", "w"), indent=1)
for name in out:
    print(name, "n", out[name]["n"], "wins", out[name]["wins"])
    for f, v in out[name]["res"].items():
        print(f"  {f:10s} auc {v['auc']} by_day {v['auc_by_day']} corr_fwd60 {v['c_fwd60']} corr_fwd180 {v['c_fwd180']}")
