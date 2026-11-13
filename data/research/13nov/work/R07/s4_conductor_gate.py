import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 4: walk-forward yes/no vetoes from the microstructure weather items on the CONDUCTOR's own trades.
Discover on 19 Oct - 4 Nov, test on 5 - 12 Nov. A veto removes the trade (the freed account taking a later trade is
NOT modelled). Variants per feature: veto below the early 33rd / 67th percentile, or above it (4 per feature)."""
import json
import numpy as np, pandas as pd

W = r"D:\ApexOptions\data\research\13nov\work\R07"
B = r"D:\ApexOptions\data\replay\batch"
R4 = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
rows = []
for run, keep in (("p44_sim", lambda d: d not in R4), ("p44_simr", lambda d: d in R4)):
    j = json.load(open(f"{B}\\{run}\\conductor_sim.json"))
    for d, v in j["days"].items():
        if not keep(d):
            continue
        for t in v.get("trades", []):
            rows.append(dict(day=d, book=t["src"], t_in=float(t["t_in"]), ret=float(t["ret_pct"]), rr=t["rr"]))
C = pd.DataFrame(rows)
print("conductor trades", len(C), "days", C.day.nunique())
F = pd.read_parquet(f"{W}\\flowcols.parquet")
F["day"] = F["day"].astype(str)
F["t_in"] = F["t_in"].astype(float)
F = F.drop_duplicates(["day", "book", "t_in"])
M = C.merge(F, on=["day", "book", "t_in"], how="left", suffixes=("", "_b"))
print("joined", int(M["ret_pct"].notna().sum()), "of", len(M))
M["ent_spr_pct"] = 100 * (M["entry_ask"] - M["entry_bid"]) / ((M["entry_ask"] + M["entry_bid"]) / 2)
EARLY = M.day <= "2026-11-04"
skip = {"day", "book", "t_in", "ret", "rr", "ret_pct", "trigger_t", "dir", "reason", "strike", "entry", "entry_bid",
        "entry_ask", "mid_in", "hold_s", "fut_in", "rr_b"}
feats = [c for c in M.columns if c not in skip and pd.api.types.is_numeric_dtype(M[c])]


def card(df):
    if len(df) == 0:
        return dict(n=0, sr=np.nan, ret=0.0, lose_days=0, worst=0.0)
    per = df.groupby("day")["ret"].apply(lambda r: 100 * (np.prod(1 + r.values / 100) - 1))
    return dict(n=len(df), sr=round(100 * (df.ret > 0).mean(), 1), ret=round(100 * (np.prod(1 + per.values / 100) - 1), 1),
                lose_days=int((per < 0).sum()), worst=round(per.min(), 1))


def per_day(df, days):
    out = {}
    for d in days:
        r = df[df.day == d].ret.values
        out[d[5:]] = round(100 * (np.prod(1 + r / 100) - 1), 1) if len(r) else 0.0
    return out


base_e, base_l = card(M[EARLY]), card(M[~EARLY])
print("BASE early", base_e, "late", base_l)
late_days = sorted(M[~EARLY].day.unique())
print("BASE late per day", per_day(M[~EARLY], late_days))
res = []
nvar = 0
for f in feats:
    x = M[f].astype(float)
    xe = x[EARLY].dropna()
    if len(xe) < 30:
        continue
    for q in (33.3, 66.7):
        cut = float(np.percentile(xe, q))
        for side in ("below", "above"):
            nvar += 1
            veto = (x < cut) if side == "below" else (x > cut)
            veto = veto & x.notna()
            ke, kl = M[EARLY & ~veto], M[~EARLY & ~veto]
            ce, cl = card(ke), card(kl)
            res.append(dict(f=f, q=q, side=side, cut=round(cut, 4), e_n=ce["n"], e_sr=ce["sr"], e_ret=ce["ret"],
                            e_ld=ce["lose_days"], l_n=cl["n"], l_sr=cl["sr"], l_ret=cl["ret"], l_ld=cl["lose_days"],
                            l_worst=cl["worst"]))
R = pd.DataFrame(res)
print("variants tried", nvar, "features", len(feats))
# the discovery pick: best early compounded return per feature, which must also keep early strike rate >= base
R["e_gain"] = R.e_ret - base_e["ret"]
best = R.sort_values("e_ret", ascending=False).groupby("f").head(1)
best = best[best.e_sr >= base_e["sr"]].sort_values("e_ret", ascending=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print("\nTOP 15 early picks and their late result (late base: sr %.1f ret %.1f%% lose_days %d)" % (base_l["sr"], base_l["ret"], base_l["lose_days"]))
print(best.head(15).to_string(index=False))
top = best.head(15)
print("\nof the top-15 early picks, late return better than base:", int((top.l_ret > base_l["ret"]).sum()),
      " late strike rate better:", int((top.l_sr > base_l["sr"]).sum()))
allp = best
print("of all", len(allp), "early picks: late ret better", int((allp.l_ret > base_l["ret"]).sum()),
      "; late sr better", int((allp.l_sr > base_l["sr"]).sum()))
R.to_csv(f"{W}\\s4_conductor_gate.csv", index=False)
# winners vs losers medians at the trigger, Conductor trades, both windows
print("\nMEDIAN (winners | losers) of selected items on the Conductor's trades")
for f in ["wx_e_fut_ofi60", "wx_e_fut_imb5", "wx_e_fut_tot_imb", "wx_fut_imb_q", "wx_fut_imb_o", "wx_agg_net", "wx_fut_lead",
          "wx_fut_spread", "wx_opt_book_imb", "wx_opt_lead", "wx_quote_age", "wx_sync_opt_age_s", "wx_kyle_lambda",
          "wx_absorb60", "ent_spr_pct", "wx_e_syn_dev", "wx_e_fut_micro", "wx_hw_book_imb"]:
    if f not in M:
        continue
    s = []
    for nm, msk in (("early", EARLY), ("late", ~EARLY)):
        g = M[msk]
        s.append(f"{nm}: {g[g.ret > 0][f].median():+.3f} | {g[g.ret <= 0][f].median():+.3f}")
    print(f.ljust(20), "   ".join(s))
