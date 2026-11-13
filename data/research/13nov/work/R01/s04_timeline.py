import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R01 step 4: the Conductor's day minute by minute (holding / pool book busy elsewhere / silent), the market's shape on the
# silent stretches (futures path rebuilt from every book's entry and exit prints), and other books' weather there.
import json, time
import numpy as np
import pandas as pd
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R01"
df = pd.read_pickle(W + r"\trades_small.pkl")
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
B = r"D:\ApexOptions\data\replay\batch"
RERUN = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
sim = json.load(open(B + r"\p44_sim\conductor_sim.json", encoding="utf-8"))["days"]
simr = json.load(open(B + r"\p44_simr\conductor_sim.json", encoding="utf-8"))["days"]
cond = {d: (simr[d] if d in RERUN else sim[d]) for d in sim}
IST = 19800.0
days = sorted(df.day.unique())
expd = df.groupby("day")["wx_expiry_day"].agg(lambda x: bool(np.nanmax(x.astype(float))) if x.notna().any() else False)
rows, stretches, conds = [], [], []
for day in days:
    d = df[df.day == day]
    ex = bool(expd.get(day, False))
    t_open = float(np.floor((d.t_in.min() + IST) / 86400) * 86400 - IST + 9 * 3600 + 15 * 60)   # 09:15 IST epoch
    w0, w1 = t_open + 60, t_open + (325 if ex else 345) * 60                                   # 09:16 .. 14:40 / 15:00
    mins = np.arange(w0, w1, 60.0)
    ctr = cond[day]["trades"]
    hold = np.zeros(len(mins), bool)
    for x in ctr:
        hold |= (mins + 30 >= x["trigger_t"]) & (mins + 30 < x["t_out"])
    fam = np.zeros(len(mins), bool)
    p = d[d.book.isin(POOL)]
    for a, b in zip(p.trigger_t.fillna(p.t_in), p.t_out):
        fam |= (mins + 30 >= a) & (mins + 30 < b)
    # futures path from every print the table holds (entry futures at t_in, exit futures at t_out)
    s = pd.concat([pd.Series(d.fut_in.values, index=d.t_in.values), pd.Series(d.fut_out.values, index=d.t_out.values)])
    s = s[(s > 1000) & np.isfinite(s.index.values)].sort_index()
    s = s.groupby(level=0).median()
    fx = np.interp(mins + 30, s.index.values, s.values)
    # nearest sample gap (minutes) as a quality flag
    idx = np.searchsorted(s.index.values, mins + 30)
    gap = np.minimum(np.abs(s.index.values[np.clip(idx, 0, len(s) - 1)] - (mins + 30)),
                     np.abs(s.index.values[np.clip(idx - 1, 0, len(s) - 1)] - (mins + 30))) / 60.0
    state = np.where(hold, "hold", np.where(fam, "pool_busy", "silent"))
    for i, m in enumerate(mins):
        rows.append((day, ex, i, m, state[i], fx[i], gap[i]))
    # silent stretches >= 10 min
    i = 0
    while i < len(mins):
        if state[i] != "silent":
            i += 1
            continue
        j = i
        while j < len(mins) and state[j] == "silent":
            j += 1
        if j - i >= 10:
            seg = fx[i:j + 1] if j < len(fx) else fx[i:j]
            net = seg[-1] - seg[0]
            path = np.sum(np.abs(np.diff(seg)))
            eff = abs(net) / path if path > 0 else 0.0
            # largest 20-min move inside (what c20 needs to arm: 40 pts in 20 min)
            k = min(20, len(seg) - 1)
            m20 = np.max(np.abs(seg[k:] - seg[:-k])) if k > 0 else 0.0
            hi, lo = seg.max(), seg.min()
            # V: a leg of >= 30 one way, then >= 60 % of it back
            ih, il = int(np.argmax(seg)), int(np.argmin(seg))
            first, second = (il, ih) if il < ih else (ih, il)
            leg1 = abs(seg[first] - seg[0]); leg2 = abs(seg[second] - seg[first])
            vshape = leg1 >= 30 and leg2 >= 0.6 * leg1 and leg2 >= 30
            # best 15-min favourable move in either direction (an ATM buyer's opportunity, futures points)
            k15 = min(15, len(seg) - 1)
            best15 = 0.0
            for a in range(len(seg) - 1):
                b2 = seg[a + 1:a + 1 + k15]
                best15 = max(best15, np.max(b2) - seg[a], seg[a] - np.min(b2))
            if abs(net) >= 40 and eff >= 0.45 and m20 >= 40:
                shape = "straight trend"
            elif abs(net) >= 25 and eff >= 0.3 and m20 < 40:
                shape = "slow grind"
            elif vshape:
                shape = "V turn"
            elif hi - lo < 35:
                shape = "quiet range"
            else:
                shape = "two-way chop"
            stretches.append(dict(day=day, expiry=ex, start=pd.Timestamp(mins[i] + IST, unit="s").strftime("%H:%M"),
                                  minutes=j - i, net=round(net, 1), path=round(path, 1), eff=round(eff, 2),
                                  max20=round(m20, 1), range=round(hi - lo, 1), best15=round(best15, 1), shape=shape,
                                  maxgap=round(float(np.max(gap[i:j])), 1)))
        i = j
    nh, nb, ns = int(hold.sum()), int((state == "pool_busy").sum()), int((state == "silent").sum())
    conds.append(dict(day=day, expiry=ex, window_min=len(mins), hold=nh, pool_busy=nb, silent=ns,
                      silent_pct=round(100 * ns / len(mins), 1), trades=len(ctr), ret_pct=cond[day]["ret_day_pct"],
                      first_entry=(ctr[0]["time_in"] if ctr else None),
                      pool_triggers=int(len(p)), med_gap_min=round(float(np.median(gap)), 2)))
mm = pd.DataFrame(rows, columns=["day", "expiry", "i", "t", "state", "fut", "gap"])
mm.to_pickle(W + r"\minutes.pkl")
C = pd.DataFrame(conds)
S = pd.DataFrame(stretches)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(C.to_string(index=False))
print("\nTOTAL window", C.window_min.sum(), "hold", C.hold.sum(), "pool_busy", C.pool_busy.sum(), "silent", C.silent.sum())
print("\nSILENT STRETCHES >= 10 min")
print(S.to_string(index=False))
print("\nBY SHAPE")
print(S.groupby("shape").agg(n=("minutes", "size"), minutes=("minutes", "sum"), best15_med=("best15", "median"),
                             best15_mean=("best15", "mean"), absnet=("net", lambda x: np.abs(x).mean())).to_string())
S.to_csv(W + r"\silent_stretches.csv", index=False)
C.to_csv(W + r"\conductor_days.csv", index=False)
print("done", round(time.time() - t0, 1))
