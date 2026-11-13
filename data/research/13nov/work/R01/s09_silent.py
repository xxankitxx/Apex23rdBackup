import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 9: what the market looked like when c20 was silent (other books' trigger photographs), how other families'
# trades did when they triggered on silent minutes (standalone, D vs T), and the crowd-out cost of a low-priority filler.
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R01"
df = pd.read_pickle(W + r"\trades_small.pkl"); mm = pd.read_pickle(W + r"\minutes.pkl")
df = df[df.entry.notna() & df.exit.notna() & df.t_in.notna()].copy(); df["trig"] = df.trigger_t.fillna(df.t_in)
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
st = {}
for d, g in mm.groupby("day"): st[d] = (g.t.values, g.state.values)
def state(row):
    t, s = st[row.day]; k = np.searchsorted(t, row.trig, side="right") - 1
    return s[k] if 0 <= k < len(s) else "outside"
df["st"] = [state(r) for r in df[["day", "trig"]].itertuples()]
fam = lambda b: ("POOL" if b in POOL else "t28/lvl retest" if b.startswith(("t28", "lvl_trail", "spot_dual", "edge_")) or b == "apex_edge"
     else "orb45" if b.startswith("spot_orb45") else "dc12 break" if b.startswith(("spot_dc12", "spot_ft")) else "pb45" if b.startswith("spot_pb45")
     else "co-first move" if b[:2] in ("m1", "m2") or b.startswith("gap") else "c20 other" if "c20" in b else "control/other")
df["fam"] = df.book.map(fam)
df = df[~df.book.isin(["conductor", "RAW"])]
sgn = np.where(df.rr == "CE", 1.0, -1.0)
for c in ["wx_day_move", "wx_mv300", "wx_mv60", "wx_breadth_dir", "wx_vwap_ext", "wx_dir60", "wx_imp_with", "wx_fmv300"]:
    if c in df: df[c + "_w"] = df[c].astype(float) * sgn
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
# 1. market state: pool triggers vs other books' triggers on silent minutes (one row per distinct trigger minute)
cols = ["wx_er60", "wx_er30", "wx_range_vs_norm", "wx_chop30", "wx_reversals60", "wx_rv5", "wx_mv300", "wx_day_move", "wx_dist_hi", "wx_dist_lo",
        "wx_pos_in_range", "wx_imp_depth", "wx_imp_age_min", "wx_vwap_ext", "wx_breadth_dir", "wx_range_vs_strad", "wx_mins_open", "wx_squeeze", "wx_rv_ratio"]
cols = [c for c in cols if c in df]
df["tmin"] = (df.trig // 60).astype(int)
P = df[df.book.isin(POOL)].drop_duplicates(["day", "tmin"]); S = df[(df.st == "silent") & ~df.book.isin(POOL)].drop_duplicates(["day", "tmin"])
H = df[(df.st == "hold") & ~df.book.isin(POOL)].drop_duplicates(["day", "tmin"])
q = lambda X: X[cols].astype(float).abs().median() if False else X[cols].astype(float).median()
T = pd.DataFrame({"c20 trigger": q(P), "silent minute": q(S), "while holding": q(H)})
T.loc["n minutes"] = [len(P), len(S), len(H)]
print("1. median weather photograph"); print(T.round(3).to_string())
print("\n|mv300| median", P.wx_mv300.astype(float).abs().median(), S.wx_mv300.astype(float).abs().median())
# share of silent minutes by er60 / range bands
S2 = S.copy(); S2["er60b"] = pd.cut(S2.wx_er60.astype(float), [-1, .2, .4, .6, 2]); S2["rvn"] = pd.cut(S2.wx_range_vs_norm.astype(float), [-1, .7, 1, 1.5, 99])
print("\nsilent minutes by er60 band x range_vs_norm band"); print(pd.crosstab(S2.er60b, S2.rvn, margins=True).to_string())
# 2. family quality on silent minutes, standalone, discovery vs test
df["win"] = df.ret_pct > 0; df["lg"] = np.log1p(df.ret_pct / 100); df["W"] = np.where(df.day <= "2026-11-04", "D", "T")
x = df[df.st == "silent"].groupby(["fam", "W"]).agg(n=("lg", "size"), days=("day", "nunique"), sr=("win", "mean"), mean_pct=("ret_pct", "mean"), med=("ret_pct", "median")).round(3)
print("\n2. trades triggered on SILENT minutes, by family (standalone book trades)"); print(x.unstack("W").to_string())
y = df.groupby(["fam", "st"]).agg(n=("lg", "size"), sr=("win", "mean"), mean_pct=("ret_pct", "mean")).round(3)
print("\nall days, by state"); print(y.unstack("st").to_string())
# per-book silent-minute quality, D vs T, top books
z = df[(df.st == "silent") & ~df.book.isin(POOL)].groupby(["book", "W"]).agg(n=("lg", "size"), sr=("win", "mean"), m=("ret_pct", "mean")).unstack("W")
z.columns = [a + "_" + b for a, b in z.columns]; z = z[(z.n_D >= 15) & (z.n_T >= 5)]
print("\nbooks on silent minutes: D sr vs T sr (n_D>=15, n_T>=5), n books", len(z), "corr sr", round(z.sr_D.corr(z.sr_T), 3), "corr mean", round(z.m_D.corr(z.m_T), 3))
print(z.sort_values("m_D", ascending=False).round(3).head(25).to_string())
# 3. per day: silent-minute pool of other families' best opportunities
dd = df[(df.st == "silent") & df.fam.isin(["t28/lvl retest", "orb45", "dc12 break", "co-first move"])].groupby(["day", "fam"]).agg(n=("lg", "size"), sr=("win", "mean"), m=("ret_pct", "mean")).round(2)
print("\n3. per day, silent-minute trades of the four price families"); print(dd.unstack("fam").to_string())
