import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R16 extras: gex_room advisor veto, IV/RV (variance premium), gamma regime by window, Gao on Nifty.
import numpy as np, pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
c = ["day", "book", "rr", "ret_pct", "t_in", "t_out", "spot_in", "fut_in", "fut_out", "wx_adv_gex_room", "wx_gex_regime",
     "wx_e_iv_rv", "wx_to_pdc", "wx_day_move", "wx_max_pain_dist", "wx_expiry_day", "wx_dte", "wx_mins_open", "wx_vwap_ext"]
df = pd.read_parquet(P, columns=c); df["day"] = df.day.astype(str)
df["d"] = np.where(df.rr.eq("CE"), 1, -1)
df["late"] = df.day > "2026-11-04"
pd.set_option("display.width", 220)
def tab(by, X, name):
    g = X.groupby(["late"] + by).ret_pct.agg(n="size", sr=lambda s: round((s > 0).mean() * 100, 1), mean=lambda s: round(s.mean(), 2))
    print("\n##", name); print(g.to_string())
for nm, X in (("all107", df), ("pool5", df[df.book.isin(POOL)])):
    tab(["wx_gex_regime"], X, nm + " by gamma regime")
    tab(["wx_adv_gex_room"], X, nm + " by gex_room veto")
    X = X.assign(ivrv=pd.cut(pd.to_numeric(X.wx_e_iv_rv, errors="coerce"), [0, 1.3, 1.7, 2.2, 9]))
    tab(["ivrv"], X, nm + " by IV/RV ratio")
    X = X.assign(vw=np.sign(pd.to_numeric(X.wx_vwap_ext, errors="coerce")))
    tab(["vw"], X, nm + " by VWAP side (+1 = our side)")
# expiry day: max pain pull. On expiry days, does trading TOWARD max pain do better?
E = df[pd.to_numeric(df.wx_dte, errors="coerce") < 1].copy()
E["mp"] = pd.to_numeric(E.wx_max_pain_dist, errors="coerce")
E["toward"] = np.where(E.mp.isna(), np.nan, np.sign(E.mp))
E["pm"] = pd.to_numeric(E.wx_mins_open, errors="coerce") >= 240
print("\n## expiry days (dte<1)", sorted(E.day.unique()))
print(E.groupby(["pm", "toward"]).ret_pct.agg(n="size", sr=lambda s: round((s > 0).mean() * 100, 1), mean=lambda s: round(s.mean(), 2)).to_string())
# Gao: previous close to 09:45 vs 14:55 to 15:25 (spot proxy from prints; pdc recovered from to_pdc)
x = df.dropna(subset=["spot_in"]).copy()
x["hm"] = pd.to_datetime(x.t_in.astype(float), unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata").dt.strftime("%H:%M")
x["tpdc"] = pd.to_numeric(x.wx_to_pdc, errors="coerce")
x["pdc_a"] = x.spot_in + x.tpdc * x.d; x["pdc_b"] = x.spot_in - x.tpdc * x.d
y = df.copy(); y["hm"] = pd.to_datetime(y.t_out.astype(float), unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata").dt.strftime("%H:%M")
rows = []
for d, g in x.groupby("day"):
    sa, sb = g.pdc_a.std(), g.pdc_b.std(); pdc = (g.pdc_a if sa < sb else g.pdc_b).median()
    a = g[(g.hm >= "09:44") & (g.hm <= "09:50")]
    f = pd.concat([g[["hm", "fut_in"]].rename(columns={"fut_in": "f"}), y[y.day == d][["hm", "fut_out"]].rename(columns={"fut_out": "f"})])
    f["f"] = pd.to_numeric(f.f, errors="coerce")
    b = f[(f.hm >= "14:50") & (f.hm <= "14:58")].f; e = f[(f.hm >= "15:20") & (f.hm <= "15:25")].f
    rows.append(dict(day=d, pdc=round(pdc, 1), first=round(a.spot_in.median() - pdc, 1) if len(a) else np.nan,
                     last30=round(e.median() - b.median(), 1) if len(b) and len(e) else np.nan, std_pdc=round(min(sa, sb), 2)))
G = pd.DataFrame(rows); G["agree"] = np.sign(G["first"]) == np.sign(G.last30)
print("\n## Gao on Nifty"); print(G.to_string(index=False))
ok = G.dropna(subset=["first", "last30"]); print("agree", int(ok.agree.sum()), "of", len(ok))
