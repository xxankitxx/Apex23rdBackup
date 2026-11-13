import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 adaptive pool, fast version. Detectors (causal at the checkpoint), policies, LODO + fixed split."""
import os, time, json, warnings
warnings.filterwarnings("ignore")
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 60)
lap = lambda m: print(f"[{time.time()-t00:6.1f}s] {m}", flush=True)
DT = pd.read_csv(os.path.join(W, "day_types.csv")).set_index("day")
FE = pd.read_csv(os.path.join(W, "cp_features.csv")); FE["cp"] = FE["cp"].astype(int).map(lambda x: f"{x:04d}")
AC = pd.read_csv(os.path.join(W, "book_day_after_cp.csv")); AC["cp"] = AC["cp"].astype(int).map(lambda x: f"{x:04d}")
BD = pd.read_csv(os.path.join(W, "book_day.csv"))
PV = pd.read_csv(os.path.join(W, "classifier_per_day.csv")).set_index("day")
base = pd.read_pickle(os.path.join(W, "base.pkl"))
base["trig"] = base["trigger_t"].fillna(base["t_in"])
base["trig_hm"] = ((base["trig"] + 19800.0) % 86400.0) / 60.0
base = base.dropna(subset=["entry", "exit", "t_out", "trig"])
fam = BD.groupby("book")["fam"].first()
DAYS = sorted(DT.index); TEST = [d for d in DAYS if d >= "2026-11-05"]
CPS = {"0945": 585, "1015": 615, "1100": 660}
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
P0 = {b: i for i, b in enumerate(POOL)}
lap("loaded")
BOOKS = sorted(base.book.unique()); BI = {b: i for i, b in enumerate(BOOKS)}
ARR = {}
for d, g in base.groupby("day"):
    g = g.sort_values("trig", kind="stable")
    ARR[d] = dict(b=g.book.map(BI).values, trig=g.trig.values.astype(float), hm=g.trig_hm.values,
                  tout=g.t_out.values.astype(float), en=g.entry.values.astype(float), ex=g.exit.values.astype(float),
                  ret=g.ret_pct.values.astype(float))


def sim(d, before, after, cut, prio):
    A = ARR[d]
    pr = np.full(len(BOOKS), 1e9)
    for b, p in prio.items():
        if b in BI:
            pr[BI[b]] = p
    bset = np.zeros(len(BOOKS), bool); aset = np.zeros(len(BOOKS), bool)
    for b in before:
        bset[BI[b]] = True
    for b in after:
        aset[BI[b]] = True
    m = (bset[A["b"]] & (A["hm"] < cut)) | (aset[A["b"]] & (A["hm"] >= cut))
    idx = np.nonzero(m)[0]
    idx = idx[np.lexsort((pr[A["b"][idx]], A["trig"][idx]))]
    cap = 1e5; held = None; out = []
    for k in idx:
        trig = A["trig"][k]; bk = A["b"][k]
        if held is not None:
            if trig <= held[0] or trig < held[1] or (trig == held[1] and bk == held[2]):
                continue
            held = None
        px = A["en"][k]; lots = int(cap // (px * 65))
        if lots < 1:
            continue
        pnl = (A["ex"][k] - px) * lots * 65; cap += pnl
        held = (trig, A["tout"][k], bk)
        out.append((BOOKS[bk], trig, A["ret"][k], pnl))
    return out, (cap / 1e5 - 1) * 100


cond = {d: sim(d, POOL, POOL, 0, P0) for d in DAYS}
print("Conductor sum %", round(sum(v[1] for v in cond.values()), 1))
cond_after = {cp: {d: sim(d, [], POOL, c, P0)[1] for d in DAYS} for cp, c in CPS.items()}
cond_before = {cp: {d: sim(d, POOL, [], c, P0)[1] for d in DAYS} for cp, c in CPS.items()}
F = {cp: FE[FE.cp == cp].set_index("day").loc[DAYS] for cp in CPS}
DET = {}
for cp in CPS:
    S = F[cp]
    DET[("dec", cp)] = {d: int(S.loc[d, "er"] >= 0.30 and abs(S.loc[d, "Dc"]) >= 0.60) for d in DAYS}
    DET[("gapgo", cp)] = {d: int(abs(S.loc[d, "gap_pct"]) >= 0.30 and np.sign(S.loc[d, "mv_pct"]) == np.sign(S.loc[d, "gap_pct"])) for d in DAYS}
    DET[("cal", cp)] = {d: int(DT.loc[d, "cal"] != "other") for d in DAYS}
    DET[("stump", cp)] = {d: int(PV.loc[d, f"stump{cp}"]) for d in DAYS}
    DET[("oneway", cp)] = {d: int((S.loc[d, "pos"] >= 0.85 and S.loc[d, "mv_pct"] > 0) or (S.loc[d, "pos"] <= 0.15 and S.loc[d, "mv_pct"] < 0)) for d in DAYS}
dd = pd.DataFrame({f"{k[0]}{k[1]}": v for k, v in DET.items()}).loc[DAYS]
dd["cond"] = [cond[d][1] for d in DAYS]
for cp in CPS:
    dd[f"cB{cp}"] = [cond_before[cp][d] for d in DAYS]
    dd[f"cA{cp}"] = [cond_after[cp][d] for d in DAYS]
dd["dtype"] = DT.loc[DAYS, "dtype"]; dd["cal"] = DT.loc[DAYS, "cal"]
dd.to_csv(os.path.join(W, "detectors_per_day.csv"))
print("\nDETECTED (1) per day\n", dd.round(1).to_string())
rows = []
for (dn, cp), v in DET.items():
    for t in (0, 1):
        ds = [d for d in DAYS if v[d] == t]
        x = np.array([cond_after[cp][d] for d in ds])
        ex = [cond_after[cp][d] for d in ds if d not in ("2026-10-26", "2026-10-27")]
        rows.append(dict(det=dn, cp=cp, typ=t, days=len(ds), mean_after=round(x.mean(), 1) if len(x) else np.nan,
                         med_after=round(float(np.median(x)), 1) if len(x) else np.nan, pos=int((x > 0).sum()),
                         mean_ex_2627=round(float(np.mean(ex)), 1) if ex else np.nan))
CA = pd.DataFrame(rows); CA.to_csv(os.path.join(W, "conductor_after_by_detected.csv"), index=False)
print("\nCONDUCTOR return AFTER the checkpoint (flat at the checkpoint), by detected type\n", CA.to_string())
lap("detectors")
ELIG = sorted(b for b in fam.index if fam[b] not in ("conductor", "control", "new-idea controls (n/p/s ctl)") and b in BI)
ntr = base.groupby("book").size()
REPS = {}
for b in ELIG:
    REPS.setdefault(fam[b], []).append(b)
REPS = {f: max(bs, key=lambda b: ntr.get(b, 0)) for f, bs in REPS.items()}
print("family representatives", REPS)
ACp = {cp: AC[AC.cp == cp].pivot(index="book", columns="day", values="ret") for cp in CPS}


def policy(name, cp, d, train, typ):
    t = typ[d]; ds = [x for x in train if typ[x] == t]
    if len(ds) < 3:
        return POOL, POOL, P0, "few"
    vals = [cond_after[cp][x] for x in ds]
    ca = float(np.mean(vals))
    if name == "P1":
        return (POOL, POOL, P0, "keep") if ca > 0 else (POOL, [], P0, "flat")
    if name == "P1m":
        return (POOL, POOL, P0, "keep") if float(np.median(vals)) > 0 else (POOL, [], P0, "flat")
    cands = ELIG if name == "P4" else sorted(REPS.values())
    M = ACp[cp].loc[cands, ds]
    st = pd.DataFrame({"mean": M.mean(axis=1), "pos": (M > 0).mean(axis=1)})
    q = st[(st["mean"] > 0) & (st["pos"] >= 0.6)].sort_values("mean", ascending=False)
    if name == "P4":
        add = [b for b in q.index if b not in POOL][:2]
        pr = dict(P0); pr.update({b: 10 + i for i, b in enumerate(add)})
        return POOL, POOL + add, pr, "+" + ",".join(add)
    if name == "P5":
        q2 = q[q["mean"] > ca]
        if len(q2) == 0 or q2.index[0] in POOL:
            return POOL, POOL, P0, "keep"
        b = q2.index[0]
        return POOL, [b], {b: 0}, "swap " + b


def run(name, cp, det, scheme):
    typ = DET[(det, cp)]; rows = []
    for d in DAYS:
        if scheme == "fixed" and d not in TEST:
            continue
        train = [x for x in DAYS if x != d] if scheme == "lodo" else [x for x in DAYS if x < "2026-11-05"]
        b4, af, pr, note = policy(name, cp, d, train, typ)
        out, ret = sim(d, b4, af, CPS[cp], pr)
        rows.append(dict(day=d, typ=typ[d], note=note, n=len(out), w=sum(1 for x in out if x[3] > 0), ret=ret, cond=cond[d][1],
                         took=set((x[0], x[1]) for x in out), rets=[x[2] for x in out]))
    return pd.DataFrame(rows)


allc = [(d, x) for d in DAYS for x in cond[d][0]]
thr = np.percentile([x[2] for _, x in allc], 90)
TOP = [(d, x[0], x[1]) for d, x in allc if x[2] >= thr]
cn = {d: (len(cond[d][0]), sum(1 for x in cond[d][0] if x[3] > 0)) for d in DAYS}


def score(df):
    r = df.ret.values; c = df.cond.values; n = df.n.sum(); w = df.w.sum()
    cN = sum(cn[d][0] for d in df.day); cW = sum(cn[d][1] for d in df.day)
    tk = [t for t in TOP if t[0] in set(df.day)]
    ix = df.set_index("day")
    kept = sum(1 for (d, b, tg) in tk if (b, tg) in ix.loc[d, "took"])
    early = (df.day < "2026-11-05").values
    return dict(days=len(df), strike=round(100 * w / max(n, 1), 1), c_strike=round(100 * cW / max(cN, 1), 1), trades=int(n), c_trades=int(cN),
                sum_pct=round(r.sum(), 1), c_sum=round(c.sum(), 1), lose_days=int((r < 0).sum()), c_lose=int((c < 0).sum()),
                worst=round(r.min(), 1), c_worst=round(c.min(), 1), ex_best_day=round(r.sum() - r.max(), 1), c_ex_best_day=round(c.sum() - c.max(), 1),
                early_diff=round(r[early].sum() - c[early].sum(), 1), late_diff=round(r[~early].sum() - c[~early].sum(), 1),
                better=int((r > c + 1e-9).sum()), worse=int((r < c - 1e-9).sum()), top_kept=f"{kept}/{len(tk)}")


summ = []; PD = {}
for name in ("P1", "P1m", "P4", "P5"):
    for cp in CPS:
        for det in ("dec", "gapgo", "cal", "stump", "oneway"):
            for scheme in ("lodo", "fixed"):
                if det == "stump" and scheme == "fixed":
                    continue
                df = run(name, cp, det, scheme)
                s = score(df); s.update(policy=name, cp=cp, det=det, scheme=scheme)
                summ.append(s); PD[(name, cp, det, scheme)] = df
    lap(name)
SM = pd.DataFrame(summ)
SM = SM[["policy", "cp", "det", "scheme"] + [c for c in SM.columns if c not in ("policy", "cp", "det", "scheme")]]
SM.to_csv(os.path.join(W, "adaptive_summary.csv"), index=False)
print("\nADAPTIVE POOL variants (sum of daily %, each day from 1 lakh)\n", SM.to_string())
print("variants:", len(SM))
import pickle
pickle.dump({k: v.drop(columns=["took"]) for k, v in PD.items()}, open(os.path.join(W, "adaptive_perday.pkl"), "wb"))
lap("done")
