"""Does the broker's 1-second future reproduce the recorded session? Same day, tape against broker history: the price
series, then the champion's pattern fired from each."""
import sys; sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import fam, hist1s
day = sys.argv[1] if len(sys.argv) > 1 else "2026-11-06"
D = FL.load_day(day)
import os, json
exp_ = json.load(open(os.path.join(hist1s.OUT, "fut_expiry.json")))[day]
df = pd.read_parquet(os.path.join(hist1s.OUT, f"fut_{exp_}_x_0_{day}.parquet"))
bf = hist1s.grid(df, day)
tape = FL._ffill0(D["fmid"])
ok = np.isfinite(bf) & np.isfinite(tape)
d = bf[ok] - tape[ok]
print(f"{day}: broker seconds with a trade {len(df)} of 22500; tape futures mid against broker last trade: mean diff {d.mean():+.2f} pts, mean abs {np.abs(d).mean():.2f}, 95th pct abs {np.quantile(np.abs(d), 0.95):.2f}, correlation of 60-s changes {np.corrcoef(np.diff(bf[ok][::60]), np.diff(tape[ok][::60]))[0, 1]:.4f}")
basis = float(np.nanmedian(tape - D["fwd"]))
X = FL.features(D)
s_tape = [s for s in fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)]
D2 = FL.Day(dict(D)); D2["fwd"] = bf - basis; D2["fs"] = FL.ema(D2["fwd"], 5.0)
X2 = FL.features(D2)
s_brk = [s for s in fam.sig_pb(D2, X2, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)]
print("pattern fired from the TAPE forward:  ", [(FL.hm(i), i % 60, sd) for i, sd, _ in s_tape])
print("pattern fired from the BROKER future: ", [(FL.hm(i), i % 60, sd) for i, sd, _ in s_brk])
ta = FL.run(D, s_tape); tb = FL.run(D, s_brk)          # both priced on the tape's real option quotes
f = lambda tr: " ".join(f"{FL.hm(t['i_in'])}{t['side'][0]}{t['ret']:+.0f}" for t in tr)
print("trades (tape signals):  ", f(ta)); print("trades (broker signals):", f(tb))
