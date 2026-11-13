import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
cols = ["day","book","ret_pct","hold_s","reason","h60_gain_pct","h300_gain_pct","h900_gain_pct","h1800_gain_pct","hexit_gain_pct","hexit_req_gain_pct","ep_type","entry","entry_bid","entry_ask","exit","ret_pct_mid","peak_pts","dte_in"]
df = pd.read_parquet(P, columns=cols)
print(df.shape)
df["c20"] = df.book.str.startswith("c20")
g = df.groupby("book").agg(n=("ret_pct","size"), h60=("h60_gain_pct", lambda s: s.notna().mean()), h300=("h300_gain_pct", lambda s: s.notna().mean()),
     hexit=("hexit_gain_pct", lambda s: s.notna().mean()), hreq=("hexit_req_gain_pct", lambda s: s.notna().mean()), ret=("ret_pct","mean"), win=("ret_pct", lambda s:(s>0).mean()), hold=("hold_s","median"))
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
print(g.sort_values("n",ascending=False).to_string())
