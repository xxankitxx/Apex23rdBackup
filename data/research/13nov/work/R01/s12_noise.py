import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 12: Zarattini-Aziz-Barbon style NOISE BOUNDARY on the Nifty futures path (minute path rebuilt from the
# trade table's entry/exit futures prints, minutes.pkl). sigma(t) = mean over the previous <= 14 days of
# |fut(t) - fut(09:16)|; signal at checkpoints when |fut - open| > k * sigma(t), side = sign. Walk-forward by
# construction (only earlier days), first day used = 6th recorded day. Outcome in FUTURES POINTS (not option %):
# move after 30 / 60 min in the signal's direction, and whether the account was silent at the signal.
import numpy as np, pandas as pd
mm = pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R01\minutes.pkl")
days = sorted(mm.day.unique()); paths = {d: g.sort_values("i") for d, g in mm.groupby("day")}
rows = []
for k in (1.0, 1.5, 2.0):
    for step in (15, 30):
        for di, d in enumerate(days):
            if di < 5: continue
            prev = days[max(0, di - 14):di]
            L = min(len(paths[x]) for x in prev + [d])
            sig = np.mean([np.abs(paths[x].fut.values[:L] - paths[x].fut.values[0]) for x in prev], axis=0)
            g = paths[d]; f = g.fut.values[:L]; stt = g.state.values[:L]; o = f[0]
            fired_side = 0
            for i in range(29, L - 1, step):            # first checkpoint 09:45
                dev = f[i] - o
                if abs(dev) > k * sig[i] and np.sign(dev) != fired_side:
                    s = np.sign(dev); fired_side = s
                    m30 = s * (f[min(i + 30, L - 1)] - f[i]); m60 = s * (f[min(i + 60, L - 1)] - f[i])
                    mae = s * (np.min(s * f[i:min(i + 60, L)]) * s - f[i]) if False else float(np.min(s * (f[i:min(i + 60, L)] - f[i])))
                    rows.append(dict(k=k, step=step, day=d, W="D" if d <= "2026-11-04" else "T", t=i, dev=round(dev, 1), sig=round(sig[i], 1),
                                     m30=round(m30, 1), m60=round(m60, 1), mae60=round(mae, 1), state=stt[i]))
R = pd.DataFrame(rows)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
a = R.groupby(["k", "step", "W"]).agg(n=("m60", "size"), days=("day", "nunique"), win30=("m30", lambda x: (x > 0).mean()), med30=("m30", "median"),
     win60=("m60", lambda x: (x > 0).mean()), med60=("m60", "median"), mean60=("m60", "mean"), mae=("mae60", "median"), silent=("state", lambda x: (x == "silent").mean())).round(2)
print("variants 6 (k x step); outcome = futures points in the signal's direction"); print(a.to_string())
print(R[(R.k == 1.0) & (R.step == 30)].to_string(index=False))
R.to_csv(r"D:\ApexOptions\data\research\13nov\work\R01\noise_signals.csv", index=False)
