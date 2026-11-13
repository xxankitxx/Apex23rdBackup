import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd, json
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
F = ["wmove10","wmove30","wmove60","wmove60_bank","wmove60_it","wmove60_energy","wmove60_other","breadth_dir",
     "breadth60_dir","breadth900_dir","breadth_net","breadth_chg5","hw_n_with","lead3_agree","lead1_move60","lead1_move300",
     "hw_disp300","hw_top3_share","hw_at_ext30","hw_book_imb","hw_book_imb_t","hw_book_chg30","hw_vol_surge","sync_dir",
     "basket_gap","bank_z","bn60","bn300","bn_minus_nifty60","bn_minus_nifty300","fn60","fn300","mv10","mv30","mv60","mv300","hw_cover60_w"]
cols = ["day","book","t_in","ret_pct","rr"] + ["wx_"+f for f in F]
df = pd.read_parquet(P, columns=cols)
df.columns = [c[3:] if c.startswith("wx_") else c for c in cols]
TW = 61.42 / 100.0
for L in (10, 30, 60):
    df[f"div{L}"] = df[f"wmove{L}"] / TW - df[f"mv{L}"]          # weighted heavyweights (index-equivalent) minus Nifty spot, with the trade
df["conf60"] = np.where(df["mv60"].abs() >= 3, df["wmove60"] / TW / df["mv60"].where(df["mv60"].abs() >= 3), np.nan)
df["bankshare60"] = np.where(df["wmove60"].abs() > 1, df["wmove60_bank"] / df["wmove60"].where(df["wmove60"].abs() > 1), np.nan)
df["exbank60"] = df["wmove60"] - df["wmove60_bank"]
df["win"] = (df["ret_pct"] > 0).astype(int)
days = sorted(df.day.unique()); print(days)
early = [d for d in days if d <= "2026-11-04"]; late = [d for d in days if d >= "2026-11-05"]
pool = ["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t"]
feats = F + ["div10","div30","div60","conf60","bankshare60","exbank60"]
def auc(x, y):
    m = np.isfinite(x); x, y = x[m], y[m]
    if y.sum() < 5 or (1-y).sum() < 5: return np.nan, int(m.sum())
    r = pd.Series(x).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1*(n1+1)/2) / (n1*n0), int(len(y))
out = []
for name, sub in (("all", df), ("pool", df[df.book.isin(pool)])):
    for f in feats:
        a1, n1 = auc(sub[sub.day.isin(early)][f].astype(float).values, sub[sub.day.isin(early)]["win"].values)
        a2, n2 = auc(sub[sub.day.isin(late)][f].astype(float).values, sub[sub.day.isin(late)]["win"].values)
        cov = float(sub[f].notna().mean())
        out.append(dict(set=name, f=f, auc_early=round(a1,3), n_early=n1, auc_late=round(a2,3), n_late=n2, cover=round(cov,3)))
o = pd.DataFrame(out)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(o.to_string())
o.to_csv(r"D:\ApexOptions\data\research\13nov\work\R08\s03_auc.csv", index=False)
print("pool trades per day", df[df.book.isin(pool)].groupby("day").size().to_dict())
