import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 day types and regimes. One run: (A) extract the needed columns and the futures paths (cached), (B) day labels,
(C) checkpoint features, (D) book and family results by day type, (E) Conductor reproduction.
Outputs CSV/JSON into work/R03. Classifier and adaptive pool are in s04 (reads these outputs)."""
import os, json, time, glob, re, traceback
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 60)


def lap(msg):
    print(f"[{time.time() - t00:6.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------- A. extract (cached)
WANT = """mins_open dte expiry_day day_before_expiry weekday er60 er_day dir60 pos_in_range give range_on dist_hi dist_lo
or_pos gap_pts gap_filled or15_pos or30_pos or45_pos er30 new_highs new_lows vwap_ext to_pdh to_pdl to_pdc hi_age_min
lo_age_min vix vix_chg_open vix_day_pos range_now range_vs_norm rv5_vs_norm norm_days fut_vol_vs_norm hw_vol_vs_norm
vwap_side_min vwap_cross_n vwap_z vwap_stretch_share pd_range range_vs_pd inside_pd pd_close_pos day_move day_move_share
open_side_min reversals60 chop30 chop60 regime hmm_state hmm_drift breadth900_dir breadth60_dir breadth_net hw_disp300
strad_vs_open_pct day_move_vs_strad range_vs_strad strad_now atm_iv_day_pos atm_iv_med e_iv_rv term_atm skew_atm pcr
max_pain_dist bn300 fn300 bn_minus_nifty300 wmove60 wmove60_bank gex_regime gex_balance rv15_spot sigma15 speed15
ma20_slope ma_stack rsi14_5m""".split()
fb = os.path.join(W, "base.pkl")
fw = os.path.join(W, "wx.pkl")
fp = os.path.join(W, "fut_paths.npz")
if os.path.exists(fb):
    base = pd.read_pickle(fb)
else:
    c = ["day", "book", "trigger_t", "t_in", "t_out", "time_in", "entry", "exit", "ret_pct", "pnl_rs", "rr", "dir", "why",
         "reason", "fut_in", "fut_out", "spot_in", "ep_type", "regime"]
    base = pd.read_parquet(P, columns=c)
    base.to_pickle(fb)
lap(f"base {base.shape}")
if os.path.exists(fw):
    wx = pd.read_pickle(fw)
else:
    import pyarrow.parquet as pq
    names = set(pq.ParquetFile(P).schema.names)
    cols = ["day", "book", "trigger_t", "t_in", "dir", "rr", "spot_in"] + ["wx_" + w for w in WANT if "wx_" + w in names]
    print("missing wx", [w for w in WANT if "wx_" + w not in names])
    wx = pd.read_parquet(P, columns=cols)
    wx.to_pickle(fw)
lap(f"wx {wx.shape}")
Z = {}
for f in sorted(glob.glob(os.path.join(W, "paths", "*.npz"))):
    q = np.load(f); dn = os.path.basename(f)[:10]
    Z[dn + "_t"] = q["t"]; Z[dn + "_F"] = q["F"]
lap(f"paths {len(Z)} arrays")

DAYS = sorted(base["day"].unique())
LV = json.load(open(r"D:\ApexOptions\data\learning\day_levels.json", encoding="utf-8"))
OPEN_M, END_M = 555, 925                       # 09:15 .. 15:25 IST


def hm(t):
    return ((np.asarray(t, float) + 19800.0) % 86400.0) / 60.0


def ep_of(day, h, m):                         # epoch of an IST clock on a day
    import datetime as _dt
    d = _dt.datetime.fromisoformat(day).replace(hour=h, minute=m, tzinfo=_dt.timezone(_dt.timedelta(hours=5, minutes=30)))
    return d.timestamp()


# ---------------------------------------------------------------- B. minute paths
def minute_path(day):
    """futures close at each minute mark 09:15..15:25 (index 0 = 09:15). Source: forecast-lab collect (per-second
    futures mid) when present, else every book's entry/exit futures print (12 Nov)."""
    if day + "_t" in Z:
        t, F = Z[day + "_t"], Z[day + "_F"]
        src = "collect"
    else:
        b = base[base.day == day]
        t = np.r_[b.t_in.values, b.t_out.values].astype(float)
        F = np.r_[b.fut_in.values, b.fut_out.values].astype(float)
        ok = np.isfinite(t) & np.isfinite(F) & (F > 0)
        t, F = t[ok], F[ok]
        o = np.argsort(t, kind="stable")
        t, F = t[o], F[o]
        src = "trades"
    h = hm(t)
    ok = (h >= OPEN_M) & (h <= END_M + 0.99)
    t, F, h = t[ok], F[ok], h[ok]
    marks = np.arange(OPEN_M, END_M + 1)
    idx = np.searchsorted(h, marks + 1.0 / 60, side="right") - 1      # last print at or before the minute mark (+1 s)
    m = np.where(idx >= 0, F[np.clip(idx, 0, len(F) - 1)], np.nan)
    o = F[0]
    # per-minute high / low (for true extremes)
    mi = np.floor(h - OPEN_M).astype(int)
    hi = np.full(len(marks), np.nan); lo = np.full(len(marks), np.nan)
    np.fmax.at(hi, np.clip(mi, 0, len(marks) - 1), F)
    np.fmin.at(lo, np.clip(mi, 0, len(marks) - 1), F)
    return {"src": src, "open": float(o), "close_m": m, "hi_m": hi, "lo_m": lo, "n": len(F)}


paths = {}
for d in DAYS:
    try:
        paths[d] = minute_path(d)
    except Exception:
        traceback.print_exc()
lap("minute paths")
# validation: 11 Nov path from trades vs from collect
try:
    b = base[base.day == "2026-11-11"]
    t = np.r_[b.t_in.values, b.t_out.values].astype(float); F = np.r_[b.fut_in.values, b.fut_out.values].astype(float)
    ok = np.isfinite(t) & np.isfinite(F) & (F > 0); t, F = t[ok], F[ok]; o = np.argsort(t); t, F = t[o], F[o]
    h = hm(t); marks = np.arange(OPEN_M, END_M + 1)
    idx = np.searchsorted(h, marks + 1.0 / 60, side="right") - 1
    mt = np.where(idx >= 0, F[np.clip(idx, 0, len(F) - 1)], np.nan)
    mc = paths["2026-11-11"]["close_m"]
    dd = mt - mc
    print("VALIDATE 11 Nov trades-path minus collect-path: median abs", np.nanmedian(np.abs(dd)), "p90", np.nanpercentile(np.abs(dd), 90),
          "trade-path hi/lo", np.nanmax(F[(h >= OPEN_M) & (h <= END_M)]), np.nanmin(F[(h >= OPEN_M) & (h <= END_M)]),
          "collect hi/lo", np.nanmax(paths["2026-11-11"]["hi_m"]), np.nanmin(paths["2026-11-11"]["lo_m"]))
except Exception:
    traceback.print_exc()

# gap (spot, the engine's own: first trusted print minus previous close), dte, weekday, from the photos
wx["d"] = np.where(wx["rr"] == "CE", 1.0, -1.0)
g = wx.dropna(subset=["wx_gap_pts"]).copy()
g["gap"] = g["wx_gap_pts"] * g["d"]
gap = g.groupby("day")["gap"].median()
dte = wx.groupby("day")["wx_dte"].median()
wkd = wx.groupby("day")["wx_weekday"].median()
basis = (base["fut_in"] - base["spot_in"]).groupby(base["day"]).median()


def label_day(p, gp, prev_close_spot, bas):
    m = p["close_m"]
    hi_m, lo_m = p["hi_m"], p["lo_m"]
    O = p["open"]; C = m[-1] if np.isfinite(m[-1]) else m[np.isfinite(m)][-1]
    H = np.nanmax(hi_m); L = np.nanmin(lo_m)
    tH = int(np.nanargmax(hi_m)); tL = int(np.nanargmin(lo_m))
    R = H - L
    mm = m[np.isfinite(m)]
    path = np.sum(np.abs(np.diff(mm)))
    er = abs(C - O) / path if path > 0 else np.nan
    D = (C - O) / R
    first_leg_up = tH < tL     # high made first
    up = H - O; dn = O - L
    out = dict(O=O, H=H, L=L, C=C, R=R, net=C - O, D=D, er=er, tH=tH, tL=tL, cpos=(C - L) / R,
               path_over_R=path / R, gap=gp, gap_pct=100 * gp / O if np.isfinite(gp) else np.nan)
    # shape, first match wins (declared before results were seen)
    if D >= 0.55 and out["cpos"] >= 0.75:
        shape = "trend_up"
    elif D <= -0.55 and out["cpos"] <= 0.25:
        shape = "trend_down"
    elif (not first_leg_up) and dn >= 0.35 * R and (C - L) >= 0.65 * R:
        shape = "V_up"            # fell first, then recovered most of the range
    elif first_leg_up and up >= 0.35 * R and (H - C) >= 0.65 * R:
        shape = "V_down"          # rose first, then gave most of it back
    else:
        shape = "range"
    out["shape"] = shape
    # gap overlay: |gap| >= 0.30 % ; go = the day kept going the gap's way and never filled it
    gk = "no_gap"
    if np.isfinite(gp) and abs(out["gap_pct"]) >= 0.30:
        pdc_f = prev_close_spot + bas if prev_close_spot is not None and np.isfinite(bas) else np.nan
        filled = (L <= pdc_f) if gp > 0 else (H >= pdc_f)
        go = np.sign(C - O) == np.sign(gp) and not filled
        gk = "gap_go" if go else ("gap_fill" if filled else "gap_fade")
    out["gapk"] = gk
    return out


rows = []
for d in DAYS:
    prev = sorted(k for k in LV if k < d)
    pcs = LV[prev[-1]]["close"] if prev else None
    o = label_day(paths[d], float(gap.get(d, np.nan)), pcs, float(basis.get(d, np.nan)))
    o.update(day=d, src=paths[d]["src"], dte=float(dte.get(d, np.nan)), weekday=float(wkd.get(d, np.nan)))
    o["cal"] = "expiry" if o["dte"] == 0 else ("day_before" if o["dte"] == 1 else "other")
    rows.append(o)
DT = pd.DataFrame(rows).set_index("day")
DT["tH_clock"] = DT["tH"].map(lambda x: f"{(OPEN_M + x) // 60:02d}:{(OPEN_M + x) % 60:02d}")
DT["tL_clock"] = DT["tL"].map(lambda x: f"{(OPEN_M + x) // 60:02d}:{(OPEN_M + x) % 60:02d}")
DT.to_csv(os.path.join(W, "day_types.csv"))
print(DT[["src", "cal", "shape", "gapk", "O", "H", "L", "C", "R", "net", "D", "er", "cpos", "path_over_R", "gap", "gap_pct",
          "tH_clock", "tL_clock"]].round(2).to_string())
lap("day labels")

# ---------------------------------------------------------------- C. checkpoint features (path and photos)
CPS = {"0945": (9, 45), "1015": (10, 15), "1100": (11, 0)}
feat = []
for d in DAYS:
    p = paths[d]; m = p["close_m"]; O = p["open"]
    C = DT.loc[d, "C"]
    for cn, (hh, mi) in CPS.items():
        k = (hh * 60 + mi) - OPEN_M
        seg = m[:k + 1]; seg = seg[np.isfinite(seg)]
        hi = np.nanmax(p["hi_m"][:k]); lo = np.nanmin(p["lo_m"][:k])
        Fc = seg[-1]
        rng = hi - lo
        path = np.sum(np.abs(np.diff(seg)))
        orh = np.nanmax(p["hi_m"][:30]); orl = np.nanmin(p["lo_m"][:30])
        f15 = m[max(0, k - 15)]
        rest = m[k:]; rest = rest[np.isfinite(rest)]
        rhi, rlo = np.nanmax(p["hi_m"][k:]), np.nanmin(p["lo_m"][k:])
        rpath = np.sum(np.abs(np.diff(rest)))
        feat.append(dict(day=d, cp=cn, mv_pct=100 * (Fc - O) / O, rng_pct=100 * rng / O, er=abs(Fc - O) / path if path > 0 else np.nan,
                         pos=(Fc - lo) / rng if rng > 0 else np.nan, Dc=(Fc - O) / rng if rng > 0 else np.nan,
                         chop=path / rng if rng > 0 else np.nan, mv15_pct=100 * (Fc - f15) / O,
                         or_rng_pct=100 * (orh - orl) / O,
                         or_out=(1 if Fc > orh else -1 if Fc < orl else 0) if k > 30 else 0,
                         gap_pct=DT.loc[d, "gap_pct"], cal=DT.loc[d, "cal"],
                         rest_net_pct=100 * (C - Fc) / O, rest_rng_pct=100 * (rhi - rlo) / O,
                         rest_er=abs(C - Fc) / rpath if rpath > 0 else np.nan,
                         rest_D=(C - Fc) / (rhi - rlo) if rhi > rlo else np.nan))
FE = pd.DataFrame(feat)
# causal norm of the range so far: median of EARLIER days at the same checkpoint
FE["rng_vs_prev"] = np.nan
for cn in CPS:
    sub = FE[FE.cp == cn].sort_values("day")
    vals = []
    for i, r in sub.iterrows():
        FE.loc[i, "rng_vs_prev"] = r.rng_pct / np.median(vals) if len(vals) >= 3 else np.nan
        vals.append(r.rng_pct)
# the engine's own photo at the checkpoint: the last trigger of any book in the 20 min before it
wx["hm"] = hm(wx["trigger_t"].fillna(wx["t_in"]))
SG = ["wx_vwap_ext", "wx_day_move", "wx_gap_pts", "wx_dir60", "wx_day_move_vs_strad", "wx_wmove60", "wx_bn300", "wx_fn300",
      "wx_ma20_slope", "wx_hmm_drift"]
for c_ in SG:
    if c_ in wx:
        wx[c_ + "_u"] = wx[c_] * wx["d"]           # back to "up" = positive
PH = ["wx_er_day", "wx_or_pos", "wx_vwap_ext_u", "wx_day_move_u", "wx_range_now", "wx_range_vs_norm", "wx_range_vs_pd",
      "wx_vix_chg_open", "wx_vix", "wx_vwap_cross_n", "wx_reversals60", "wx_chop60", "wx_er30", "wx_pos_in_range",
      "wx_give", "wx_range_on", "wx_new_highs", "wx_new_lows", "wx_strad_vs_open_pct", "wx_range_vs_strad",
      "wx_atm_iv_day_pos", "wx_e_iv_rv", "wx_pcr", "wx_bn300_u", "wx_fn300_u", "wx_wmove60_u", "wx_hmm_state", "wx_regime",
      "wx_rv5_vs_norm", "wx_fut_vol_vs_norm", "wx_inside_pd", "wx_dir60_u"]
PH = [c_ for c_ in PH if c_ in wx]
ph_rows = []
for d in DAYS:
    w = wx[wx.day == d].sort_values("hm")
    for cn, (hh, mi) in CPS.items():
        c_m = hh * 60 + mi
        s = w[(w.hm <= c_m) & (w.hm > c_m - 20)]
        r = {"day": d, "cp": cn, "ph_n": len(s)}
        if len(s):
            last = s.iloc[-1]
            for c_ in PH:
                r[c_] = last[c_]
        ph_rows.append(r)
PHD = pd.DataFrame(ph_rows)
FE = FE.merge(PHD, on=["day", "cp"], how="left")
FE.to_csv(os.path.join(W, "cp_features.csv"), index=False)
print(FE[["day", "cp", "mv_pct", "rng_pct", "er", "pos", "Dc", "chop", "mv15_pct", "or_out", "rng_vs_prev", "rest_net_pct",
          "rest_er", "rest_D", "ph_n", "wx_er_day", "wx_or_pos", "wx_vwap_ext_u", "wx_range_vs_norm"]].round(3).to_string())
lap("checkpoint features")

# ---------------------------------------------------------------- D. books and families by day type
CONTROLS = {"futures_only", "random_entry", "premium_momentum"}


def family(b):
    if b == "conductor":
        return "conductor"
    if b in CONTROLS:
        return "control"
    if b == "RAW":
        return "c20 council (RAW copy)"
    if re.match(r"^(fx|fr|rx)_c20", b):
        return "c20 exit/re-entry twins"
    if b.startswith("c20_"):
        return "c20 council"
    if b.startswith("t28_"):
        return "t28 45-min pullback"
    if b.startswith("lvl_trail"):
        return "lvl_trail pullback"
    if b.startswith("spot_dual") or b == "spot_pb45":
        return "spot 45-min pullback"
    if b.startswith("spot_dc12_t12_first") or b.startswith("spot_ft"):
        return "spot first-touch"
    if b.startswith("spot_dc12"):
        return "spot retest"
    if b.startswith("spot_orb"):
        return "opening range"
    if re.match(r"^m\d", b):
        return "impulse+basket m-grid"
    if b.startswith("gap"):
        return "basket gap"
    if b.startswith("edge"):
        return "edge"
    if b.startswith("straddle"):
        return "straddle spike"
    if b.startswith("fade"):
        return "burst fade"
    return b.split("_")[0]


base["fam"] = base["book"].map(family)
base["trig"] = base["trigger_t"].fillna(base["t_in"])
base["trig_hm"] = hm(base["trig"])
fm = base.groupby("book")["fam"].first()
print("FAMILIES:", base.groupby("fam")["book"].nunique().to_dict())
print("BOOKS:", {f: sorted(fm[fm == f].index.tolist()) for f in sorted(fm.unique())})


def bookday(df):
    df = df.sort_values("t_in")
    r = df["ret_pct"].astype(float).values / 100.0
    return pd.Series({"n": len(r), "w": int((r > 0).sum()), "ret": float(np.prod(1 + r) - 1) * 100})


BD = base.groupby(["book", "day"]).apply(bookday).reset_index()
allidx = pd.MultiIndex.from_product([sorted(base.book.unique()), DAYS], names=["book", "day"])
BD = BD.set_index(["book", "day"]).reindex(allidx).fillna({"n": 0, "w": 0, "ret": 0.0}).reset_index()
BD["fam"] = BD["book"].map(fm)
BD = BD.merge(DT[["shape", "gapk", "cal"]].reset_index(), on="day")
BD.to_csv(os.path.join(W, "book_day.csv"), index=False)
# after-checkpoint book-day returns (trigger at or after the checkpoint)
ac = []
for cn, (hh, mi) in CPS.items():
    sub = base[base.trig_hm >= hh * 60 + mi]
    x = sub.groupby(["book", "day"]).apply(bookday).reset_index()
    x = x.set_index(["book", "day"]).reindex(allidx).fillna({"n": 0, "w": 0, "ret": 0.0}).reset_index()
    x["cp"] = cn
    ac.append(x)
AC = pd.concat(ac)
AC.to_csv(os.path.join(W, "book_day_after_cp.csv"), index=False)
lap("book-day tables")


def fam_table(BD, key):
    g = BD[BD.fam != "conductor"].groupby(["fam", key, "day"]).agg(ret=("ret", "mean"), n=("n", "sum"), w=("w", "sum")).reset_index()
    t = g.groupby(["fam", key]).agg(days=("day", "nunique"), mean_day_ret=("ret", "mean"), med_day_ret=("ret", "median"),
                                    pos_days=("ret", lambda s: int((s > 0).sum())), trades=("n", "sum"), wins=("w", "sum")).reset_index()
    t["strike"] = 100 * t["wins"] / t["trades"].replace(0, np.nan)
    return t


for key in ("shape", "gapk", "cal"):
    t = fam_table(BD, key)
    t.to_csv(os.path.join(W, f"fam_by_{key}.csv"), index=False)
    piv = t.pivot(index="fam", columns=key, values="mean_day_ret").round(1)
    piv2 = t.pivot(index="fam", columns=key, values="strike").round(0)
    print(f"\nFAMILY mean book-day return % by {key}\n", piv.to_string())
    print(f"\nFAMILY strike rate % by {key}\n", piv2.to_string())
print("\nDAYS per shape", DT["shape"].value_counts().to_dict(), "gap", DT["gapk"].value_counts().to_dict(), "cal", DT["cal"].value_counts().to_dict())
# family x day matrix (mean book-day return)
FD = BD[BD.fam != "conductor"].groupby(["fam", "day"])["ret"].mean().unstack().round(1)
FD.to_csv(os.path.join(W, "fam_day.csv"))
print("\nFAMILY x DAY mean book-day return %\n", FD.to_string())
lap("family tables")

# ---------------------------------------------------------------- E. Conductor reproduction
POOL = [("c20_9y", 12.088), ("c20_9s", 11.441), ("c20_9v", 9.897), ("c20_9x", 9.605), ("c20_9t", 4.385)]


def sim_day(tr, prio):
    """account_sim.simulate_day without rules: tr = one day's candidate trades, prio = {book: rank}."""
    tr = tr.assign(_p=tr["book"].map(prio)).sort_values(["trig", "_p"], kind="stable")
    cap = 100000.0; held = None; out = []
    for r in tr.itertuples(index=False):
        trig = float(r.trig)
        if held is not None:
            h_trig, h_out, h_book = held
            if trig <= h_trig or trig < h_out or (trig == h_out and r.book == h_book):
                continue
            held = None
        px = float(r.entry)
        lots = int(cap // (px * 65))
        if lots < 1:
            continue
        pnl = (float(r.exit) - px) * lots * 65
        cap += pnl
        held = (trig, float(r.t_out), r.book)
        out.append({"book": r.book, "trig": trig, "t_out": float(r.t_out), "ret_pct": float(r.ret_pct), "pnl": pnl, "cap": cap})
    return out, cap


prio0 = {b: i for i, (b, _) in enumerate(POOL)}
rep = []
for d in DAYS:
    tr = base[(base.day == d) & base.book.isin(prio0)].dropna(subset=["entry", "exit", "t_out"])
    out, cap = sim_day(tr, prio0)
    rep.append({"day": d, "n": len(out), "w": sum(1 for x in out if x["pnl"] > 0), "pnl": cap - 1e5, "ret": (cap / 1e5 - 1) * 100})
REP = pd.DataFrame(rep).set_index("day")
# the shipped Conductor sims
cs = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", encoding="utf-8"))["days"]
csr = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json", encoding="utf-8"))["days"]
ship = {}
for d in DAYS:
    src = csr if d in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03") else cs
    if d in src:
        ship[d] = (src[d]["n"], src[d]["pnl_rs"], src[d]["ret_day_pct"])
REP["ship_n"] = [ship.get(d, (np.nan,) * 3)[0] for d in REP.index]
REP["ship_pnl"] = [ship.get(d, (np.nan,) * 3)[1] for d in REP.index]
REP = REP.join(DT[["shape", "gapk", "cal"]])
REP.to_csv(os.path.join(W, "conductor_repro.csv"))
print("\nCONDUCTOR reproduction from the parquet vs shipped sims\n", REP.round(1).to_string())
print("totals: repro", round(REP.pnl.sum()), "ship", round(np.nansum(REP.ship_pnl)))
lap("done")
