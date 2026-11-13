import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
C = pd.read_pickle(W + r"\conductor.pkl")
POOL = ['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
df["reason0"] = df["reason"].astype(str).str.replace("COUNCIL ", "", regex=False).str.split(" (", regex=False).str[0]
df["ret"] = df["ret_pct"] / 100.0
df["pk_bid"] = df["peak_bid"] / df["entry"] - 1
df["pk_ltp"] = df["peak_pts"] / df["entry"]
df["mae"] = df["worst_pts"] / df["entry"]
df["exp"] = (df["day"] == df["expiry"]).astype(int)
df["spr_in"] = (df["entry_ask"] - df["entry_bid"]) / df["entry"]
df["ttp"] = df["peak_t"] - df["t_in"]
# join conductor trades to the pool book rows
C["book"] = C["src"]
key = ["day", "book", "t_in"]
J = C.merge(df, on=key, how="left", suffixes=("_c", ""))
print("conductor rows", len(C), "matched", J["ret_pct"].notna().sum())
bad = J[J["ret_pct"].isna()]
if len(bad): print(bad[["day","book","t_in","time_in_c"]].to_string())
# check returns agree
J["dret"] = (J["ret_pct_c"] - J["ret_pct"]).abs()
print("max |ret diff| conductor vs book row", J["dret"].max())
J.to_pickle(W + r"\conductor_joined.pkl")
out = {}
def summ(g):
    pos = g["pk_bid"].clip(lower=0)
    return pd.Series(dict(
        n=len(g), win=round(100*(g["ret"]>0).mean(),1), mean_ret=round(100*g["ret"].mean(),2), med_ret=round(100*g["ret"].median(),2),
        med_peak_bid=round(100*g["pk_bid"].median(),2), med_peak_ltp=round(100*g["pk_ltp"].median(),2),
        capture_sum=round(100*g["ret"].sum()/pos.sum(),1) if pos.sum()>0 else np.nan,
        med_giveback=round(100*(g["pk_bid"]-g["ret"]).median(),2), med_mae=round(100*g["mae"].median(),2),
        med_hold_min=round(g["hold_s"].median()/60,1), med_ttp_min=round(g["ttp"].median()/60,1),
        up10_lost=int(((g["pk_bid"]>=0.10)&(g["ret"]<=0)).sum()), up5_lost=int(((g["pk_bid"]>=0.05)&(g["ret"]<=0)).sum()),
        logret_sum=round(100*np.log1p(g["ret"]).sum(),1)))
for name, sub in (("conductor", J), ("pool5", df[df.book.isin(POOL)]), ("c20_family", df[df.book.str.startswith(("c20_","rx_c20"))]), ("all_books", df)):
    print("\n=====", name, len(sub))
    t = sub.groupby(["exp","reason0"]).apply(summ, include_groups=False).sort_values(["exp","n"], ascending=[True,False])
    print(t.to_string())
    print("-- total by exp")
    tt = sub.groupby("exp").apply(summ, include_groups=False); print(tt.to_string())
    print("-- total", summ(sub).to_dict())
    out[name] = dict(by_reason=t.reset_index().to_dict("records"), by_exp=tt.reset_index().to_dict("records"), total=summ(sub).to_dict())
# conductor per day
J["win"] = J["ret"] > 0
pdx = J.groupby("day").apply(lambda g: pd.Series(dict(n=len(g), win=int(g.win.sum()), day_ret=round(100*(np.prod(1+g["ret"])-1),1),
        capture=round(100*g["ret"].sum()/g["pk_bid"].clip(lower=0).sum(),1) if g["pk_bid"].clip(lower=0).sum()>0 else np.nan,
        peak_compound=round(100*(np.prod(1+g["pk_bid"].clip(lower=0))-1),1))), include_groups=False)
print("\n== conductor per day: compounded realised vs compounded per-trade peak (bid)")
print(pdx.to_string())
out["conductor_days"] = pdx.reset_index().to_dict("records")
json.dump(out, open(W + r"\a2_teardown.json", "w"), indent=1, default=float)
# trade list for the per-second path study (pool books, Conductor flag), numpy-only consumers
keep = ["day","book","rr","strike","expiry","entry","entry_bid","entry_ask","exit","t_in","t_out","ret_pct","reason0","qty","delta_in",
        "iv_in","peak_bid","hold_s","wx_atr1_15","wx_sigma15","wx_theta_min","wx_rv5","wx_theta_be","wx_gamma","wx_vix","wx_er30","wx_chop30"]
P5 = df[df.book.isin(POOL)].copy()
ck = set(zip(J["day"], J["book"], J["t_in"]))
P5["cond"] = [ (a, b, c) in ck for a, b, c in zip(P5["day"], P5["book"], P5["t_in"]) ]
recs = []
for r in P5[keep + ["cond"]].to_dict("records"):
    recs.append({k: (None if (isinstance(v, float) and not np.isfinite(v)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v)) for k, v in r.items()})
json.dump(recs, open(W + r"\pool_trades.json", "w"), default=float)
print("pool trades written", len(recs), "conductor-flagged", int(P5["cond"].sum()))
