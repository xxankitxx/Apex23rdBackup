"""Real option prices for the year's NORMAL-day trades, from the broker's 1-minute option bars (data/research/hist_wx,
ATM at the open +- 6 strikes): every trade of the champion class and the fades (s32 classes_run) re-priced at the
real bar of its strike - bought at the open of the minute after the signal, sold at the close of its exit minute -
against the model price the year test used. No broker calls."""
import os, sys, glob
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import hist1s
from s44_wxfeat import minute_grid
WX = r"D:\ApexOptions\data\research\hist_wx"
HALF = 0.0011
comp = lambda r: 100 * (np.prod(1 + np.asarray(r, float) / 100) - 1)
K = pd.read_parquet(os.path.join(hist1s.OUT, "classes_run.parquet"))
K = K[(K.src == "model chain") & K.book.isin(["c20_9x", "fade20", "fade60", "orbfade"])]
rows = []; miss = 0
for day, g in K.groupby("day"):
    p = os.path.join(WX, f"{day}.parquet")
    if not os.path.exists(p):
        continue
    wx = pd.read_parquet(p)
    cache = {}
    for r in g.itertuples():
        key = f"opt:{int(r.K)}:{'call' if r.side == 'CE' else 'put'}"
        if key not in cache:
            cache[key] = (minute_grid(wx, key, "open"), minute_grid(wx, key, "close"))
        o, c = cache[key]
        m_in, m_out = int(r.i_in) // 60, min(int(r.i_out) // 60, 374)
        e = o[m_in] if np.isfinite(o[m_in]) else c[max(m_in - 1, 0)]
        x = c[m_out]
        if not (np.isfinite(e) and np.isfinite(x) and e > 0):
            miss += 1; continue
        rows.append(dict(day=day, book=r.book, side=r.side, model=r.ret, real=100 * (x * (1 - HALF) / (e * (1 + HALF)) - 1)))
T = pd.DataFrame(rows)
print(f"trades re-priced on real 1-minute bars: {len(T)} (strike outside the downloaded band or no bar: {miss}); sessions {T.day.nunique()}")
out = []
for b, g in T.groupby("book"):
    out.append(dict(book=b, trades=len(g), model_per_trade=round(g.model.mean(), 2), real_per_trade=round(g.real.mean(), 2), model_win=round(100 * (g.model > 0).mean()),
                    real_win=round(100 * (g.real > 0).mean()), correlation=round(np.corrcoef(g.model, g.real)[0, 1], 2), real_minus_model=round((g.real - g.model).mean(), 2)))
print(pd.DataFrame(out).to_string(index=False))
T.to_parquet(os.path.join(WX, "real_minute_check.parquet"))
