"""71 days: a blind buy (both sides) by time of day, model option + champion ladder; and Nifty's own movement by time."""
import sys; sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab5
DD = lab5.load()
REC = {"2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03",
       "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11", "2026-11-12", "2026-11-13"}
rows = []
for D in DD:
    c = D["c"]
    X = lab5.feats(D)
    for b in range(1, 67):
        for side in ("CE", "PE"):
            t = lab5.ladder(D, b, side)
            if t is None:
                continue
            sg = 1 if side == "CE" else -1
            m3 = X["m3"][b]
            rows.append(dict(day=D["day"], b=b, side=side, ret=t["ret"], dte0=D["dte0"], dte=D["dte"], rec=D["day"] in REC,
                             w=(np.sign(m3) == sg) if m3 == m3 and m3 != 0 else None, abs60=abs(c[min(b + 12, 73)] - c[b]), rng_prev=(D["h"][max(0, b - 11):b + 1].max() - D["l"][max(0, b - 11):b + 1].min())))
T = pd.DataFrame(rows)
T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\tod71.parquet")
lab = lambda b: f"{(555 + 5 * (b + 1)) // 60:02d}:{(555 + 5 * (b + 1)) % 60:02d}"
T["tb"] = pd.cut(T.b, [0, 3, 6, 9, 12, 18, 24, 36, 48, 60, 67], labels=["09:20-30", "09:35-45", "09:50-10:00", "10:05-15", "10:20-45", "10:50-11:15", "11:20-12:15", "12:20-13:15", "13:20-14:15", "14:20-14:50"])
for nm, g in (("NORMAL days, all 71-day history", T[~T.dte0]), ("NORMAL days NOT in the recorded set (independent)", T[~T.dte0 & ~T.rec]), ("EXPIRY days", T[T.dte0])):
    print(f"\n{nm}: {g.day.nunique()} days")
    out = []
    for tb, s in g.groupby("tb"):
        dd = s.groupby("day").ret.mean()
        w = s[s.w == True]
        dw = w.groupby("day").ret.mean()
        tt = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
        out.append(dict(time=tb, n=len(s), win=round(100 * (s.ret > 0).mean()), mean=round(s.ret.mean(), 2), t=round(tt, 1), days_pos=f"{int((dd > 0).sum())}/{len(dd)}",
                        with_mean=round(w.ret.mean(), 2), with_days=f"{int((dw > 0).sum())}/{len(dw)}", abs_move_next_60=round(s.abs60.mean(), 1), range_prev_60=round(s.rng_prev.mean(), 1)))
    print(pd.DataFrame(out).to_string(index=False))
# by days to expiry (normal days), the 12:20-13:15 window against the rest
print("\n12:20-13:15 window by trading days to expiry (normal days):")
g = T[~T.dte0 & (T.tb == "12:20-13:15")]
print(g.groupby("dte").agg(days=("day", "nunique"), mean=("ret", lambda r: round(r.mean(), 2)), win=("ret", lambda r: round(100 * (r > 0).mean()))).to_string())
