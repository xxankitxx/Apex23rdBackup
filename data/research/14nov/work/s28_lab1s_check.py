"""How far to trust the per-second MODEL option: the recorded sessions' own forward, the same entries, real quotes
against the model. Normal days: the champion's pullback; expiry days: its breakout."""
import os, sys, json
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam, lab1s


def one(day):
    F = FL.load_day(day)
    D = lab1s.session(day, fwd=F["fwd"].copy())
    if D is None:
        return []
    X = lab1s.feats(D)
    sig = lab1s.sig_exp(D, X) if D["dte0"] else fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)
    real = FL.run(F, sig)
    model = lab1s.run(D, sig)
    comp = lambda tr: 100 * (np.prod([1 + t["ret"] / 100 for t in tr]) - 1) if tr else 0.0
    return [dict(day=day, expiry=F["dte0"], real_n=len(real), real_win=sum(t["ret"] > 0 for t in real), real_sum=sum(t["ret"] for t in real), real_day=comp(real),
                 model_n=len(model), model_win=sum(t["ret"] > 0 for t in model), model_sum=sum(t["ret"] for t in model), model_day=comp(model))]


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=8) as ex:
        R = pd.DataFrame(sum(ex.map(one, FL.days()), []))
    pd.set_option("display.width", 220)
    print(R.round(1).to_string(index=False))
    for nm, g in (("normal", R[~R.expiry]), ("expiry", R[R.expiry])):
        print(f"{nm}: real quotes {int(g.real_n.sum())} trades, {100 * g.real_win.sum() / g.real_n.sum():.0f} % winners, {g.real_sum.sum() / g.real_n.sum():+.2f} % a trade | model {int(g.model_n.sum())} trades, "
              f"{100 * g.model_win.sum() / g.model_n.sum():.0f} % winners, {g.model_sum.sum() / g.model_n.sum():+.2f} % a trade | day-result correlation {np.corrcoef(g.real_day, g.model_day)[0, 1]:.2f}")
