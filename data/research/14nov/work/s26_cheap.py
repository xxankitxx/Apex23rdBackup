"""Two checks. (1) Real option sessions: is buying better when options are cheap against recent movement (ATM implied
volatility / 20-session realised)? (2) Recorded sessions: how many index points better is the per-second entry of the
champion's pattern than the 1-minute version's entry on the same days?"""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1, h4, fam
from s24_fade import attach_real
ALL = h4.load(); attach_real(ALL)
rows = []
for D in ALL:
    if not D["opt"] or D["dte0"] or not D["rv20"]:
        continue
    b = 15
    F = D["c"][b] - D["basis"]
    ks = sorted({k for (k, r) in D["opt"]}); k = min(ks, key=lambda x: abs(x - F))
    if (k, "CE") not in D["opt"] or (k, "PE") not in D["opt"]:
        continue
    st = D["opt"][(k, "CE")][b, 3] + D["opt"][(k, "PE")][b, 3]
    if not np.isfinite(st):
        continue
    iv = st / (0.7979 * F * np.sqrt(D["T"][b]))
    blind = lab1.run(D, h4.fam(D, "blind", bars=(30, 75, 135, 195, 255, 300)), model=False)
    pat = lab1.run(D, h4.fam(D, "pb", W=20, pb=0.5), model=False)
    fd = lab1.run(D, h4.fam(D, "fade", W=20, z=0.5), model=False)
    rng = D["h"].max() - D["l"].min()
    rows.append(dict(day=D["day"], dte=D["dte"], ratio=iv / D["rv20"], iv=100 * iv, blind=np.mean([t["ret"] for t in blind]) if blind else np.nan, n_blind=len(blind),
                     pat=np.mean([t["ret"] for t in pat]) if pat else np.nan, fade=np.mean([t["ret"] for t in fd]) if fd else np.nan, day_range_over_implied=rng / (F * iv / np.sqrt(252))))
R = pd.DataFrame(rows)
R["tercile"] = pd.qcut(R.ratio, 3, labels=["cheap (IV low vs movement)", "middle", "dear (IV high vs movement)"])
pd.set_option("display.width", 220)
print(f"real-option normal sessions: {len(R)}; implied / realised volatility at 09:30: median {R.ratio.median():.2f} (above 1 = options cost more than recent movement)")
print(R.groupby("tercile").agg(sessions=("day", "size"), ratio=("ratio", "median"), blind_mean=("blind", "mean"), blind_days_pos=("blind", lambda s: f"{int((s > 0).sum())}/{s.notna().sum()}"),
                               pattern_mean=("pat", "mean"), fade_mean=("fade", "mean"), day_range_vs_implied=("day_range_over_implied", "median")).round(2).to_string())
print("rank correlation of the ratio with the day's blind-buy result:", round(R.ratio.corr(R.blind, method="spearman"), 2))

# (2) entry timing on the recorded sessions
print("\nentry timing, recorded normal sessions: the same arm, fired per second against fired on the 1-minute close")
gain = []
for day in FL.days():
    F = FL.load_day(day)
    if F["dte0"]:
        continue
    X = FL.features(F)
    sec = [s for s in fam.sig_pb(F, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0) if not X["gap"][s[0]]]
    D = lab1.from_fastlab(day)
    mn = lab1.sig_pb_hl(D)
    fw = FL._ffill0(F["fwd"])
    for (i, side, _) in sec:
        b = i // 60
        near = [m for m in mn if m[1] == side and -1 <= m[0] - b <= 6]
        if not near:
            continue
        m = near[0]
        px_sec = fw[min(i + 1, len(fw) - 1)]
        px_min = D["o"][min(m[0] + 1, lab1.NB - 1)]
        sg = 1 if side == "CE" else -1
        gain.append(dict(day=day, side=side, delay_s=(m[0] + 1) * 60 - i, better_pts=sg * (px_min - px_sec)))
G = pd.DataFrame(gain)
print(f"matched entries {len(G)}: the per-second entry comes {G.delay_s.median():.0f} s earlier (median) and is {G.better_pts.mean():+.1f} index points better on average (median {G.better_pts.median():+.1f}); better on {100 * (G.better_pts > 0).mean():.0f} % of them")
