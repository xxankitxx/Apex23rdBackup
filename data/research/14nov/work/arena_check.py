"""Validate the arena on the recorded sessions, where real per-second option quotes exist (the tape):
(1) the REAL-IV per-second price of ATM contracts against the tape's mid, second by second;
(2) the champion's own entries priced three ways - tape quotes, real-IV, model - trade by trade;
(3) the arena's pool() against the champion alone (no trade lost, no pause)."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import arena, fam, lab1s

rows = []; trs = []
for day in FL.days():
    if arena._wx(day) is None:
        continue
    F = FL.load_day(day)
    ctx = arena.context(day)
    D = ctx["D"]
    # (1) second by second, ATM call and put at 10:00, 11:30, 13:30
    for hhmm in ("10:00", "11:30", "13:30"):
        i0 = FL.row_of(hhmm)
        K0 = float(F["K"][int(np.argmin(np.abs(F["K"] - D["fwd"][i0])))]) if np.isfinite(D["fwd"][i0]) else None
        if K0 is None:
            continue
        j = int(np.flatnonzero(F["K"] == K0)[0])
        for side, c in (("CE", 0), ("PE", 1)):
            tape = 0.5 * (F["opt"][:, j, c, 0] + F["opt"][:, j, c, 1]).astype(float)
            rv = arena.realiv_series(D, K0, side); md = arena.model_series(D, K0, side)
            if rv is None:
                continue
            sl = slice(i0, i0 + 1800)
            ok = np.isfinite(tape[sl]) & np.isfinite(rv[sl])
            if ok.sum() < 600:
                continue
            t, r, m = tape[sl][ok], rv[sl][ok], md[sl][ok]
            rows.append(dict(day=day, dte0=D["dte0"], at=hhmm, side=side, tape_mean=round(t.mean(), 1), realiv_err_pct=round(100 * np.mean(np.abs(r / t - 1)), 2),
                             model_err_pct=round(100 * np.mean(np.abs(m / t - 1)), 2), realiv_ret_corr=round(np.corrcoef(np.diff(t[::30]), np.diff(r[::30]))[0, 1], 3)))
    # (2) the champion's entries, three prices
    X = FL.features(F)
    sig = (fam.sig_brk(F, X, W=600, vmin=28.0, gap=300) if F["dte0"] else fam.sig_pb(F, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0))
    sig = [s for s in sig if not X["gap"][s[0]]]
    tape_tr = FL.run(F, sig)
    for t in tape_tr:
        a = arena.run_day(ctx, [(t["i_in"] - 1, t["side"], "x")], mode="realiv")
        b = arena.run_day(ctx, [(t["i_in"] - 1, t["side"], "x")], mode="model")
        trs.append(dict(day=day, dte0=D["dte0"], tape=t["ret"], realiv=a[0]["ret"] if a else np.nan, model=b[0]["ret"] if b else np.nan))
R = pd.DataFrame(rows); T = pd.DataFrame(trs)
pd.set_option("display.width", 220)
print("(1) per-second price against the tape mid, 30 minutes from each time (mean absolute error, % of the price):")
print(R.groupby("dte0")[["realiv_err_pct", "model_err_pct", "realiv_ret_corr"]].median().rename(index={False: "normal days", True: "expiry days"}).to_string())
print(f"   samples: {len(R)} (sessions {R.day.nunique()})")
print("\n(2) the champion's entries, each priced on the tape, on real-IV and on the model (trade result, %):")
for d0, g in T.groupby("dte0"):
    g = g.dropna()
    print(f"   {'expiry' if d0 else 'normal'} days: {len(g)} trades; mean tape {g.tape.mean():+.2f}, real-IV {g.realiv.mean():+.2f}, model {g.model.mean():+.2f}; "
          f"correlation with tape: real-IV {np.corrcoef(g.tape, g.realiv)[0, 1]:.2f}, model {np.corrcoef(g.tape, g.model)[0, 1]:.2f}; "
          f"winners tape {100 * (g.tape > 0).mean():.0f} %, real-IV {100 * (g.realiv > 0).mean():.0f} %, model {100 * (g.model > 0).mean():.0f} %")
C = arena.champion_trades()
P = arena.pool(C, C.iloc[0:0])
print(f"\n(3) pool(champion, nothing): {len(P)} of {len(C)} champion trades kept")
