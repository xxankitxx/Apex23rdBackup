"""What do 1-minute bars lose? The champion's pattern on the 18 recorded sessions: per-second fastlab against lab1 on
1-minute bars built from the same sessions (real quotes), and lab1's model option against the real one."""
import os, sys, json
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam, lab1


def one(day):
    F = FL.load_day(day)
    X = FL.features(F)
    if F["dte0"]:
        sig = fam.sig_brk(F, X, W=600, vmin=28.0, gap=300)
    else:
        sig = fam.sig_pb(F, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)
    sec = FL.run(F, [s for s in sig if not X["gap"][s[0]]])
    D = lab1.from_fastlab(day)
    s1 = lab1.sig_brk(D) if D["dte0"] else lab1.sig_pb(D)
    m1 = lab1.run(D, s1)
    D["vix"] = float(np.nanmedian(X["vix"])) if np.isfinite(X["vix"]).any() else 12.0
    mm = lab1.run(D, s1, model=True)
    comp = lambda tr: 100 * (np.prod([1 + t["ret"] / 100 for t in tr]) - 1) if tr else 0.0
    return dict(day=day, expiry=F["dte0"], dte=D["dte"], sec_n=len(sec), sec_win=sum(t["ret"] > 0 for t in sec), sec_day=round(comp(sec), 1), sec_sum=round(sum(t["ret"] for t in sec), 1),
                min_n=len(m1), min_win=sum(t["ret"] > 0 for t in m1), min_day=round(comp(m1), 1), min_sum=round(sum(t["ret"] for t in m1), 1),
                model_n=len(mm), model_win=sum(t["ret"] > 0 for t in mm), model_day=round(comp(mm), 1), model_sum=round(sum(t["ret"] for t in mm), 1))


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=8) as ex:
        R = pd.DataFrame(list(ex.map(one, FL.days())))
    C = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
    R["conductor_day"] = [round(C[d]["ret_day_pct"], 1) if d in C else np.nan for d in R.day]
    pd.set_option("display.width", 250)
    print(R.to_string(index=False))
    for nm, g in (("normal", R[~R.expiry]), ("expiry", R[R.expiry])):
        print(f"\n{nm}: per-second trades {g.sec_n.sum()} win {100 * g.sec_win.sum() / g.sec_n.sum():.0f} % sum {g.sec_sum.sum():+.0f} | 1-minute real {g.min_n.sum()} win {100 * g.min_win.sum() / max(g.min_n.sum(), 1):.0f} % sum {g.min_sum.sum():+.0f}"
              f" | 1-minute model {g.model_n.sum()} win {100 * g.model_win.sum() / max(g.model_n.sum(), 1):.0f} % sum {g.model_sum.sum():+.0f}")
        print(f"   day-result correlation: per-second vs 1-minute real {np.corrcoef(g.sec_day, g.min_day)[0, 1]:.2f}; 1-minute real vs model {np.corrcoef(g.min_day, g.model_day)[0, 1]:.2f}; "
              f"1-minute real vs the real Conductor {np.corrcoef(g.min_day[g.conductor_day.notna()], g.conductor_day.dropna())[0, 1]:.2f}")
