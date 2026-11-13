import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
df = pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R01\trades_small.pkl")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 60)
g = df.groupby("book").agg(n=("ret_pct","size"), days=("day","nunique"), win=("ret_pct", lambda x: round((x>0).mean(),2)),
    mean=("ret_pct", lambda x: round(x.mean(),2)), sumlog=("ret_pct", lambda x: round(np.log1p(x/100).sum(),2)),
    why=("why", lambda x: str(x.dropna().iloc[0])[:55] if x.notna().any() else ""))
print(g.sort_values("sumlog", ascending=False).to_string())
