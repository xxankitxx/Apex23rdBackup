"""Is the pattern's own recent record a usable regime switch? Four years, 1-minute lab, normal days.
Shadow accounts of the pullback pattern and of the fades run every day; the question is whether trading one only when
its trailing record is positive (or switching to whichever has done better) beats trading it always."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab1, h4
S = pd.read_parquet(os.path.join(lab1.W, "search4y.parquet"))
ALL = h4.load()
days = [D["day"] for D in ALL if not D["dte0"]]
rv = {D["day"]: D["rv20"] for D in ALL}
NAMES = {"pattern": "pullback W20 pb0.4", "fade20": "fade a 20m move of 0.6 sigma", "fade60": "fade a 60m move of 0.7 sigma", "fade20b": "fade a 20m move of 0.4 sigma", "orbfade": "opening range 15m FADE"}
TR = {k: S[S.variant == v] for k, v in NAMES.items()}
DAY = pd.DataFrame({k: g.groupby("day").ret.sum().reindex(days).fillna(0.0) for k, g in TR.items()})
CNT = pd.DataFrame({k: g.groupby("day").size().reindex(days).fillna(0) for k, g in TR.items()})
pd.set_option("display.width", 230)
print("sessions", len(days), "| trades:", {k: len(g) for k, g in TR.items()})
q = DAY.groupby(DAY.index.str[:4] + "Q" + ((DAY.index.str[5:7].astype(int) - 1) // 3 + 1).astype(str)).sum()
print("\ncorrelation of QUARTERLY results (17 quarters):\n", q.corr().round(2).to_string())
print("\nquarterly sums (% points):\n", q.round(0).astype(int).T.to_string())


def stats(name, mask, label):
    d = DAY[name][mask]; n = CNT[name][mask].sum()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 5 and d.std() > 0 else np.nan
    return dict(rule=label, sessions=int(mask.sum()), trades=int(n), per_trade=round(d.sum() / max(n, 1), 2), per_session=round(d.mean(), 2), t=round(t, 1), total=round(d.sum()))


for name in ("pattern", "fade20", "fade60", "orbfade"):
    print(f"\n=== {name}: trade it only when its own trailing record is positive ===")
    out = []
    for half, sel in (("2022-24", DAY.index < h4.SPLIT), ("2025-26", DAY.index >= h4.SPLIT)):
        out.append(dict(stats(name, sel, "always"), half=half))
        for L in (10, 20, 40, 60):
            tr = DAY[name].rolling(L, min_periods=L // 2).sum().shift(1)
            out.append(dict(stats(name, sel & (tr > 0).to_numpy(), f"trailing {L} sessions > 0"), half=half))
            out.append(dict(stats(name, sel & (tr <= 0).to_numpy(), f"trailing {L} sessions <= 0"), half=half))
    print(pd.DataFrame(out)[["half", "rule", "sessions", "trades", "per_trade", "per_session", "t", "total"]].to_string(index=False))

print("\n=== switch: each day trade whichever of the pattern / fade60 has the better trailing record (none if both negative) ===")
out = []
for L in (10, 20, 40, 60):
    a = DAY["pattern"].rolling(L, min_periods=L // 2).sum().shift(1); b = DAY["fade60"].rolling(L, min_periods=L // 2).sum().shift(1)
    pick = np.where((a > b) & (a > 0), "pattern", np.where((b >= a) & (b > 0), "fade60", "none"))
    r = np.where(pick == "pattern", DAY["pattern"], np.where(pick == "fade60", DAY["fade60"], 0.0))
    for half, sel in (("2022-24", DAY.index < h4.SPLIT), ("2025-26", DAY.index >= h4.SPLIT)):
        x = r[sel]; both = (DAY["pattern"] + DAY["fade60"])[sel]
        out.append(dict(L=L, half=half, switch_total=round(x.sum()), switch_per_session=round(x.mean(), 2), t=round(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), 1), days_pattern=int((pick[sel] == "pattern").sum()),
                        days_fade=int((pick[sel] == "fade60").sum()), days_none=int((pick[sel] == "none").sum()), both_always_total=round(both.sum())))
print(pd.DataFrame(out).to_string(index=False))

print("\n=== by the volatility of the last 20 sessions (thirds, cut on 2022-24) ===")
r = pd.Series({d: rv[d] for d in days})
c1, c2 = r[r.index < h4.SPLIT].quantile([1 / 3, 2 / 3])
for name in ("pattern", "fade20", "fade60"):
    out = []
    for half, sel in (("2022-24", DAY.index < h4.SPLIT), ("2025-26", DAY.index >= h4.SPLIT)):
        for lab, m in (("quiet", r <= c1), ("middle", (r > c1) & (r <= c2)), ("lively", r > c2)):
            out.append(dict(stats(name, sel & m.to_numpy(), lab), half=half))
    print(name); print(pd.DataFrame(out)[["half", "rule", "sessions", "trades", "per_trade", "t"]].to_string(index=False))
