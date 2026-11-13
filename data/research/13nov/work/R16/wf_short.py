import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R16 shortlist: fixed, untuned "natural" thresholds from the literature (no fitting), per test day,
# robustness (without best trade / best day), both windows, pool books, all 107 books, Conductor.
import json, numpy as np, pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
OUT = r"D:\ApexOptions\data\research\13nov\work\R16"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
cols = ["day", "book", "t_in", "rr", "ret_pct", "spot_in", "fut_in", "fut_out", "t_out",
        "wx_ma60_dist", "wx_ma20_dist", "wx_rsi14_5m", "wx_pos60", "wx_ma_stack", "wx_vwap_ext",
        "wx_gex_flip_ahead", "wx_gex_regime", "wx_squeeze", "wx_e_iv_rv", "wx_day_move", "wx_to_pdc", "wx_mins_open",
        "wx_ma20_slope", "wx_er60"]
df = pd.read_parquet(P, columns=cols); df["day"] = df.day.astype(str); df["t_in"] = df.t_in.astype(float)
for c in cols[9:]:
    if c != "wx_gex_regime": df[c] = pd.to_numeric(df[c], errors="coerce")
RULES = {
  "T1 above 60m MA our way (ma60_dist>0)": lambda X: X.wx_ma60_dist > 0,
  "T2 RSI14 5m on our side (>50)":          lambda X: X.wx_rsi14_5m > 50,
  "T3 upper half of 60m range our way":     lambda X: X.wx_pos60 > 0.5,
  "T4 VWAP side our way (vwap_ext>0)":      lambda X: X.wx_vwap_ext > 0,
  "T5 2 of 3 MAs with us (ma_stack>=2)":    lambda X: X.wx_ma_stack >= 2,
  "T6 trend vote: T1+T2+T4 >=2":            lambda X: ((X.wx_ma60_dist > 0).astype(int) + (X.wx_rsi14_5m > 50).astype(int) + (X.wx_vwap_ext > 0).astype(int)) >= 2,
  "T7 day move our way (Gao-style)":        lambda X: X.wx_day_move > 0,
  "G1 gamma not DAMPEN":                    lambda X: X.wx_gex_regime.astype(str) != "DAMPEN",
  "V1 IV below RV (e_iv_rv<0)":             lambda X: X.wx_e_iv_rv < 0,
  "S1 range compression ended (squeeze>0.4)": lambda X: X.wx_squeeze > 0.4,
}
def comp(x): return (np.prod(1 + np.asarray(x) / 100.0) - 1) * 100
def stats(T, r, days):
    if len(T) == 0: return {}
    dr = {d: comp(g[r]) for d, g in T.groupby("day")}; v = np.array([dr.get(d, 0.0) for d in days])
    # without best trade, without best day
    bt = T[r].idxmax(); Tb = T.drop(bt)
    drb = {d: comp(g[r]) for d, g in Tb.groupby("day")}; vb = np.array([drb.get(d, 0.0) for d in days])
    bd = days[int(np.argmax(v))]; vd = np.array([x for d, x in zip(days, v) if d != bd])
    return dict(n=len(T), sr=round((T[r] > 0).mean() * 100, 1), mean=round(T[r].mean(), 2),
                comp=round(comp(v), 1), lose=int((v < 0).sum()), worst_day=round(v.min(), 1),
                no_best_trade=round(comp(vb), 1), no_best_day=round(comp(vd), 1),
                top10_kept=None)
def run(U, r, label):
    out = []
    for win, m in (("early 19Oct-4Nov", U.day <= "2026-11-04"), ("late 5-12Nov", U.day > "2026-11-04")):
        W = U[m]; days = sorted(W.day.unique())
        b = stats(W, r, days); top = set(W[r].nlargest(10).index)
        out.append(dict(univ=label, win=win, rule="BASE", **b, top10=10))
        for nm, f in RULES.items():
            k = f(W).fillna(False) if hasattr(f(W), "fillna") else f(W)
            # rule is silent when its input is missing
            src = {"T1": "wx_ma60_dist", "T2": "wx_rsi14_5m", "T3": "wx_pos60", "T4": "wx_vwap_ext", "T5": "wx_ma_stack",
                   "T7": "wx_day_move", "V1": "wx_e_iv_rv", "S1": "wx_squeeze"}.get(nm[:2])
            if src: k = k | W[src].isna()
            K = W[k.astype(bool)]
            s = stats(K, r, days); s["top10_kept"] = len(top & set(K.index))
            out.append(dict(univ=label, win=win, rule=nm, **s))
    return out
rows = []
pool = df[df.book.isin(POOL)]
rows += run(pool, "ret_pct", "pool5")
# all books: per-book compounding is meaningless across books; report trade-level only
A = df.copy()
for win, m in (("early", A.day <= "2026-11-04"), ("late", A.day > "2026-11-04")):
    W = A[m]
    for nm, f in RULES.items():
        k = f(W).fillna(False).astype(bool)
        rows.append(dict(univ="all107(trade-level)", win=win, rule=nm, n=int(k.sum()),
                         sr=round((W[k].ret_pct > 0).mean() * 100, 1), mean=round(W[k].ret_pct.mean(), 2),
                         sr_out=round((W[~k].ret_pct > 0).mean() * 100, 1), mean_out=round(W[~k].ret_pct.mean(), 2)))
# Conductor
cs = []
for f, excl in ((r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", True),
                (r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json", False)):
    j = json.load(open(f))
    for day, v in j["days"].items():
        swap = day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")
        if excl == swap: continue
        for t in v.get("trades", []):
            cs.append({"day": day, "book": t["src"], "t_in": float(t["t_in"]), "c_ret": t["ret_pct"]})
cm = pd.DataFrame(cs).merge(pool.drop(columns=["ret_pct"]), on=["day", "book", "t_in"], how="left")
rows += run(cm, "c_ret", "conductor(skip only)")
R = pd.DataFrame(rows); R.to_csv(OUT + r"\wf_short_results.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
# per test day for the top rule candidates on Conductor and pool
for U, r, lab in ((pool, "ret_pct", "pool5"), (cm, "c_ret", "conductor")):
    W = U[U.day > "2026-11-04"]
    for nm in ["BASE", "T1 above 60m MA our way (ma60_dist>0)", "T6 trend vote: T1+T2+T4 >=2", "T4 VWAP side our way (vwap_ext>0)"]:
        K = W if nm == "BASE" else W[(RULES[nm](W).fillna(False)) | W[{"T1": "wx_ma60_dist", "T4": "wx_vwap_ext"}.get(nm[:2], "wx_ma60_dist")].isna()]
        line = [f"{d[5:]}: n{len(g)} sr{(g[r]>0).mean()*100:.0f}% {comp(g[r]):+.1f}%" for d, g in K.groupby("day")]
        print(lab, nm[:30], " | ".join(line))
# Gao et al. on Nifty: first-30-min return vs last-30-min return, from futures prints in the trade table
pts = pd.concat([df[["day", "t_in", "fut_in"]].rename(columns={"t_in": "t", "fut_in": "f"}),
                 df[["day", "t_out", "fut_out"]].rename(columns={"t_out": "t", "fut_out": "f"})])
pts["t"] = pd.to_numeric(pts.t, errors="coerce"); pts["f"] = pd.to_numeric(pts.f, errors="coerce"); pts = pts.dropna()
pts["hm"] = pd.to_datetime(pts.t, unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata").dt.strftime("%H:%M")
g = []
for d, x in pts.groupby("day"):
    x = x.sort_values("t")
    def at(h1, h2):
        y = x[(x.hm >= h1) & (x.hm <= h2)]
        return y.f.iloc[0] if len(y) else np.nan
    o, f30, f1455, f1525 = at("09:15", "09:20"), at("09:45", "09:50"), at("14:50", "14:56"), at("15:20", "15:25")
    g.append(dict(day=d, first30=round(f30 - o, 1), mid=round(f1455 - f30, 1), last30=round(f1525 - f1455, 1)))
G = pd.DataFrame(g); G["same_sign"] = np.sign(G.first30) == np.sign(G.last30)
print(G.to_string(index=False)); print("agree", G.same_sign.sum(), "of", G[["first30", "last30"]].dropna().shape[0])
G.to_csv(OUT + r"\gao_nifty.csv", index=False)
