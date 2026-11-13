import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import numpy as np, pandas as pd
from simlib import *
W = r"D:\ApexOptions\data\research\13nov\work\R15"
bd = pd.read_parquet(W + r"\book_day.parquet")
P = bd.pivot(index="book", columns="day", values="ret")[DAYS]
N = bd.pivot(index="book", columns="day", values="n")[DAYS]
Wn = bd.pivot(index="book", columns="day", values="wins")[DAYS]
E, L = P[EARLY], P[LATE]
R = pd.DataFrame({"fam": [family(b) for b in P.index],
  "E_n": N[EARLY].sum(1), "E_sr": 100*Wn[EARLY].sum(1)/N[EARLY].sum(1).clip(lower=1), "E_sum": E.sum(1), "E_med": E.median(1),
  "E_lose": (E < 0).sum(1), "E_worst": E.min(1),
  "L_n": N[LATE].sum(1), "L_sr": 100*Wn[LATE].sum(1)/N[LATE].sum(1).clip(lower=1), "L_sum": L.sum(1), "L_med": L.median(1),
  "L_lose": (L < 0).sum(1), "L_worst": L.min(1), "L_wo_best_day": L.sum(1) - L.max(1),
  "A_sum": P.sum(1), "A_sr": 100*Wn.sum(1)/N.sum(1).clip(lower=1), "A_lose": (P < 0).sum(1), "A_med": P.median(1)}, index=P.index)
# conductor pool account per day
pool = P.loc["conductor"] if "conductor" in P.index else None
acc = np.array([21.78,48.07,7.77,25.23,260.92,532.04,56.23,24.79,-5.56,41.58,-36.25,-26.68,-5.9,100.23,43.17,9.02,-3.98])
R["corr_acc"] = [np.corrcoef(P.loc[b].values, acc)[0,1] if P.loc[b].std() > 0 else np.nan for b in P.index]
R["corr_acc_late"] = [np.corrcoef(L.loc[b].values, acc[12:])[0,1] if L.loc[b].std() > 0 else np.nan for b in P.index]
R = R.round(1); R.to_csv(W + r"\book_stats.csv")
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
print(R.sort_values("L_sum", ascending=False).to_string())
from scipy.stats import spearmanr
X = R[R.fam != "meta"]
for a, b in [("E_sum","L_sum"),("E_sr","L_sr"),("E_med","L_med"),("E_lose","L_lose"),("E_worst","L_worst")]:
    print("spearman", a, b, spearmanr(X[a], X[b]))
PP = P.drop(index=["conductor"]); PP = PP[PP.std(1) > 0]
C = np.corrcoef(PP.values); iu = np.triu_indices_from(C, 1)
print("mean pairwise corr", C[iu].mean(), "median", np.median(C[iu]), "share >0.5", (C[iu] > 0.5).mean())
fams = [family(b) for b in PP.index]; fm = sorted(set(fams))
F = pd.DataFrame(index=fm, columns=fm, dtype=float)
for a in fm:
    for c in fm:
        ia = [i for i, f in enumerate(fams) if f == a]; ic = [i for i, f in enumerate(fams) if f == c]
        v = [C[i, j] for i in ia for j in ic if i != j]
        F.loc[a, c] = np.mean(v) if v else np.nan
print(F.round(2).to_string())
# cross-day dispersion: how often the day's best book is a council book; rank of pool books per day
for d in DAYS:
    s = P[d].drop("conductor").sort_values(ascending=False)
    print(d, "best", s.index[0], round(s.iloc[0],1), "| 9y rank", list(s.index).index("c20_9y")+1, "| median book", round(s.median(),1), "| share books >0", round((s>0).mean(),2))
# family-level daily table
FD = P.drop("conductor").groupby([family(b) for b in P.drop("conductor").index]).median()
print("family median book return per day"); print(FD.round(1).to_string())
