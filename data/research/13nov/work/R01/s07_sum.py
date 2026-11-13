import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
W = r"D:\ApexOptions\data\research\13nov\work\R01"
R = pd.concat([pd.read_pickle(W + f"/fillers_{a}.pkl") for a in (0, 45, 72)], ignore_index=True)
R.to_pickle(W + "/fillers_all.pkl")
pd.set_option("display.width", 280); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 30)
cols = ["book","filt","D_sumlog","D_up","D_dn","D_worst","D_nfill","D_fsr","D_acct_sr","T_sumlog","T_up","T_dn","T_worst","T_nfill","T_fsr","T_acct_sr","T_days"]
print("variants", len(R), "books", R.book.nunique())
sel = R[(R.D_sumlog > 0) & (R.D_up > R.D_dn) & (R.D_worst > -0.10) & (~R.control)]
print("selected on discovery:", len(sel), "books", sel.book.nunique())
print(sel.sort_values("D_sumlog", ascending=False)[cols].to_string(index=False))
print("selected positive on test:", int((sel.T_sumlog > 0).sum()), "of", len(sel), "| all positive on test:", int((R.T_sumlog > 0).sum()), "of", len(R))
print("selected: T_up>=T_dn and T_worst>-0.05:", int(((sel.T_up >= sel.T_dn) & (sel.T_worst > -0.05) & (sel.T_sumlog > 0)).sum()))
print("\nTOP 20 BY TEST (reference only):"); print(R.sort_values("T_sumlog", ascending=False)[cols].head(20).to_string(index=False))
print("\ncontrols:"); print(R[R.control][cols].to_string(index=False))
print("\nby filter: median sumlog D/T, share positive T"); print(R.groupby("filt").agg(D=("D_sumlog","median"), T=("T_sumlog","median"), Tpos=("T_sumlog", lambda x: (x>0).mean())).to_string())
