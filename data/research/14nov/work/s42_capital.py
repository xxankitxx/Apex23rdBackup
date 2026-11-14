"""What an all-in account would have done over the year before the recorded window (14 Nov 2025 to 16 Oct 2026),
compounding trade by trade: the champion as it is (normal days + expiry days), and the alternatives."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import hist1s
from s38_year_summary import one_account, M
E = pd.read_parquet(os.path.join(hist1s.OUT, "expiry_class.parquet"))
EF = pd.read_parquet(os.path.join(hist1s.OUT, "expiry_fades.parquet"))
norm = {"champion": one_account(M[M.book.isin(["c20_9x"])]), "champion + three fades": one_account(M[M.book.isin(["c20_9x", "fade20", "fade60", "orbfade"])]),
        "three fades": one_account(M[M.book.isin(["fade20", "fade60", "orbfade"])])}
exp = {"breakout (as live)": E, "no trading": E.iloc[0:0], "60-minute fade only": EF[EF.variant == "fade 60m 0.7"]}


def path(frames):
    T = pd.concat([f[["day", "i_in", "ret"]] for f in frames if len(f)]).sort_values(["day", "i_in"])
    T = T[T.day < "2026-10-19"]
    cap = 100.0; peak = 100.0; dd = 0.0; lows = []
    by_m = {}
    for r in T.itertuples():
        cap *= 1 + r.ret / 100.0
        peak = max(peak, cap); dd = min(dd, cap / peak - 1)
        by_m[r.day[:7]] = cap
    return cap, dd, len(T), by_m


rows = []
for nn, nf in norm.items():
    for en, ef in exp.items():
        cap, dd, n, by_m = path([nf, ef])
        rows.append(dict(normal_days=nn, expiry_days=en, trades=n, end_capital_per_100=round(cap, 1), deepest_fall=f"{100 * dd:.0f} %",
                         log10_growth=round(np.log10(cap / 100.0), 2), month_ends=" ".join(f"{v:.0f}" for v in list(by_m.values())[::2])))
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
print("An account of 100 on 14 Nov 2025, all-in on every trade, to 16 Oct 2026 (per-second, real classes; model option on normal days, real option seconds on expiry days):")
print(pd.DataFrame(rows).to_string(index=False))
