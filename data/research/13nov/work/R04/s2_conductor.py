import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 2: the EXACT Conductor account under every single weather line, and a beam of 2- and 3-item ANDs.
The Conductor mirrors the five pool books (apex/engine/conductor.py), so a pool rule = drop that book's trigger at the
account; the books themselves run unchanged. Discovery 19 Oct - 4 Nov picks; 5 - 12 Nov tests.
  py -3.13 -u s2_conductor.py [BUDGET_S] [BEAM_K]
Objective on discovery: sum over days of log(1 + day return). Constraints: >= 2/3 of the unfiltered account's
top-10 % discovery trades still taken (same side, within 60 s, or already held), strike rate not lower, at least
half the unfiltered account's discovery trades. Null: event photos permuted within each day (all five books' rows of
a trigger move together), the whole single-line search re-run, best objective recorded (max statistic)."""
import json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L

budget = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
BEAM_K = int(sys.argv[2]) if len(sys.argv) > 2 else 20
d = L.load()
prio = {b: i for i, b in enumerate(L.POOL)}
R = np.flatnonzero(np.isin(d.book, L.POOL) & np.isfinite(d.entry) & np.isfinite(d.exit) & np.isfinite(d.t_in))
pr = np.array([prio[b] for b in d.book[R]])
o = np.lexsort((pr, d.trig[R], d.di[R]))
R = R[o]
nR = len(R)
trig, tout, px, ex = d.trig[R], d.t_out[R], d.entry[R], d.exit[R]
bk = np.array([prio[b] for b in d.book[R]])
rr = (d.rr[R] == "CE").astype(int)
dayi = d.di[R]
days = d.days
disc_days = [i for i, x in enumerate(days) if x < L.TEST0]
test_days = [i for i, x in enumerate(days) if x >= L.TEST0]
# events: (day, trigger second); rep row = the first (highest priority) row
ev = np.zeros(nR, dtype=np.int64)
k = 0
for j in range(nR):
    if j > 0 and (dayi[j] != dayi[j - 1] or trig[j] != trig[j - 1]):
        k += 1
    ev[j] = k
nE = k + 1
ev_rep = np.zeros(nE, dtype=np.int64)
ev_rep[ev[::-1]] = np.arange(nR)[::-1]
ev_day = dayi[ev_rep]
print("pool rows", nR, "events", nE, round(time.time() - t0, 1), flush=True)


def sim(K):
    """K: (C, nR) bool keep. Returns day returns (C, ndays) in %, taken (C, nR) bool."""
    C = K.shape[0]
    out = np.zeros((C, len(days)))
    T = np.zeros((C, nR), bool)
    for di in range(len(days)):
        js = np.flatnonzero(dayi == di)
        cap = np.full(C, L.CAP0)
        h_trig = np.full(C, -np.inf); h_out = np.full(C, -np.inf); h_bk = np.full(C, -1)
        for j in js:
            busy = (trig[j] <= h_trig) | (trig[j] < h_out) | ((trig[j] == h_out) & (bk[j] == h_bk))
            lots = np.floor(cap / (px[j] * L.LOT))
            tk = ~busy & K[:, j] & (lots >= 1)
            if tk.any():
                cap[tk] += (ex[j] - px[j]) * lots[tk] * L.LOT
                h_trig[tk] = trig[j]; h_out[tk] = tout[j]; h_bk[tk] = bk[j]
                T[tk, j] = True
        out[:, di] = 100.0 * (cap / L.CAP0 - 1.0)
    return out, T


# unfiltered account (validation against p44_sim / p44_simr)
base_ret, base_T = sim(np.ones((1, nR), bool))
print("unfiltered day %:", {days[i]: round(float(base_ret[0, i]), 1) for i in range(len(days))}, flush=True)
bt = np.flatnonzero(base_T[0])
disc_rows = bt[np.isin(dayi[bt], disc_days)]
nbig = max(1, int(round(0.10 * len(disc_rows))))
big = disc_rows[np.argsort(-d.ret[R[disc_rows]])[:nbig]]
big = big[d.ret[R[big]] > 0]
# a big trade is "kept" if the filtered account took a row of the same day and side within 60 s of it, or held one then
Mb = np.zeros((nR, len(big)), np.float32)
for i, b in enumerate(big):
    same = (dayi == dayi[b]) & (rr == rr[b])
    Mb[:, i] = (same & ((np.abs(trig - trig[b]) <= 60) | ((trig <= trig[b]) & (trig[b] < tout)))).astype(np.float32)
base_disc_n = int(np.isin(dayi[bt], disc_days).sum())
base_disc_sr = float((d.ret[R[disc_rows]] > 0).mean())
print("base disc trades", base_disc_n, "sr", round(base_disc_sr, 3), "big", len(big), flush=True)

# candidate lines: from the discovery events' values (quantiles, as s1)
XR = d.X[R].astype(np.float64)                  # (nR, F)
F = XR.shape[1]
disc_ev = np.flatnonzero(np.isin(ev_day, disc_days))
cand = []                                       # (feature, op, line)
for f in range(F):
    xs = np.sort(XR[ev_rep[disc_ev], f][np.isfinite(XR[ev_rep[disc_ev], f])])
    for ln in L.lines_for(xs, d.kinds[f]):
        cand.append((f, 1, float(ln)))
        cand.append((f, 0, float(ln)))
cf = np.array([c[0] for c in cand]); cop = np.array([c[1] for c in cand]); cln = np.array([c[2] for c in cand])
C = len(cand)
print("candidates", C, round(time.time() - t0, 1), flush=True)


def keepK(Xv, idx):
    v = Xv[:, cf[idx]].T                         # (c, nR)
    fin = np.isfinite(v)
    ge = v >= cln[idx][:, None]
    return fin & np.where(cop[idx][:, None] == 1, ge, ~ge)


def score(ret_days, T):
    lg = np.log1p(ret_days / 100.0)
    obj = lg[:, disc_days].sum(1)
    dmask = np.isin(dayi, disc_days)
    n = T[:, dmask].sum(1)
    w = (T[:, dmask] & (d.ret[R][dmask] > 0)).sum(1)
    sr = np.divide(w, n, out=np.zeros(len(n)), where=n > 0)
    kb = ((T.astype(np.float32) @ Mb) > 0).sum(1)
    ok = (kb >= np.ceil(2.0 / 3.0 * len(big) - 1e-9)) & (sr >= base_disc_sr) & (n >= 0.5 * base_disc_n)
    return obj, ok, n, sr, kb


def chunks(idx, size=4000):
    for s in range(0, len(idx), size):
        yield idx[s:s + size]


def evaluate(Xv, idx_list=None, extra=None):
    """All single candidates (or AND with extra mask (nR,) bool). Returns obj, ok, n, sr, kb, ret_days, T for all."""
    idx_all = np.arange(C)
    objs, oks, ns, srs, kbs, rets, Ts = [], [], [], [], [], [], []
    for idx in chunks(idx_all):
        K = keepK(Xv, idx)
        if extra is not None:
            K &= extra[None, :]
        rd, T = sim(K)
        ob, ok, n, sr, kb = score(rd, T)
        objs.append(ob); oks.append(ok); ns.append(n); srs.append(sr); kbs.append(kb); rets.append(rd); Ts.append(T)
    return (np.concatenate(objs), np.concatenate(oks), np.concatenate(ns), np.concatenate(srs), np.concatenate(kbs),
            np.concatenate(rets), np.concatenate(Ts))


base_obj = float(np.log1p(base_ret[0, disc_days] / 100.0).sum())
obj, ok, n, sr, kb, rets, Ts = evaluate(XR)
print("singles done", round(time.time() - t0, 1), "valid", int(ok.sum()), flush=True)
objm = np.where(ok, obj, -np.inf)


def describe(ci_list, retd, T):
    out = {"conds": [(d.names[cf[c]], ">=" if cop[c] == 1 else "<", round(float(cln[c]), 6)) for c in ci_list]}
    out["disc_obj"] = round(float(np.log1p(retd[disc_days] / 100).sum()), 4)
    out["disc_days"] = {days[i]: round(float(retd[i]), 2) for i in disc_days}
    out["test_days"] = {days[i]: round(float(retd[i]), 2) for i in test_days}
    tk = np.flatnonzero(T)
    for nm, dd in (("disc", disc_days), ("test", test_days)):
        r = tk[np.isin(dayi[tk], dd)]
        out[nm + "_n"] = len(r)
        out[nm + "_sr"] = round(float((d.ret[R[r]] > 0).mean()), 3) if len(r) else None
    out["test_obj"] = round(float(np.log1p(retd[test_days] / 100).sum()), 4)
    return out


base_desc = describe([], base_ret[0], base_T[0])
# the register's hand-written and shadow rules, applied to the pool pairs at the account (out-of-sample check)
col = {nm: XR[:, d.names.index(nm)] for nm in ("agree_same", "expiry_day", "mins_open", "er60", "dir60")}
b9y, b9s = bk == 0, bk == 1
named = {
    "R-019 (9y agree_same>=7)": ~(b9y & ~(col["agree_same"] >= 7)),
    "R-020 (9s agree_same>=6)": ~(b9s & ~(col["agree_same"] >= 6)),
    "R-004 (normal days: no entry from 12:00)": ~((col["expiry_day"] == 0) & (col["mins_open"] >= 165)),
    "R-002 (normal days: ER60>=0.35 our way)": ~((col["expiry_day"] == 0) & ~((col["mins_open"] >= 60) & (col["er60"] >= 0.35) & (col["dir60"] == 1))),
}
named["R-019 + R-020"] = named["R-019 (9y agree_same>=7)"] & named["R-020 (9s agree_same>=6)"]
nk = np.array(list(named.values()))
nret, nT = sim(nk)
named_out = {}
for i, nm in enumerate(named):
    named_out[nm] = describe([], nret[i], nT[i])
    print("NAMED", nm, named_out[nm]["test_days"], named_out[nm]["test_n"], named_out[nm]["test_sr"], flush=True)
best_single = np.argsort(-objm)[:60]
singles = []
seenf = set()
for c in best_single:
    if not np.isfinite(objm[c]):
        break
    dsc = describe([c], rets[c], Ts[c])
    dsc["first_of_feature"] = cf[c] not in seenf
    seenf.add(cf[c])
    singles.append(dsc)
# best line per feature (for the information table)
per_feat = {}
for c in np.argsort(-objm):
    if not np.isfinite(objm[c]):
        break
    if cf[c] in per_feat:
        continue
    per_feat[int(cf[c])] = {"f": d.names[cf[c]], "op": ">=" if cop[c] == 1 else "<", "line": float(cln[c]),
                            "dObj": round(float(objm[c] - base_obj), 4),
                            "test_dObj": round(float(np.log1p(rets[c][test_days] / 100).sum() - np.log1p(base_ret[0, test_days] / 100).sum()), 4)}
print("best single", singles[0]["conds"] if singles else None, round(time.time() - t0, 1), flush=True)

# beam: pairs then triples
beam = [c for c in best_single[:BEAM_K] if np.isfinite(objm[c])]
pairs = []
for a in beam:
    ka = keepK(XR, np.array([a]))[0]
    ob2, ok2, n2, sr2, kb2, r2, T2 = evaluate(XR, extra=ka)
    ok2 &= cf != cf[a]
    o2 = np.where(ok2, ob2, -np.inf)
    for c in np.argsort(-o2)[:5]:
        if np.isfinite(o2[c]):
            pairs.append((float(o2[c]), a, int(c), r2[c], T2[c]))
    if time.time() - t0 > budget * 0.6:
        break
pairs.sort(key=lambda x: -x[0])
uniq, seen = [], set()
for p in pairs:
    key = tuple(sorted((p[1], p[2])))
    if key in seen:
        continue
    seen.add(key)
    uniq.append(p)
pairs = uniq
print("pairs", len(pairs), round(time.time() - t0, 1), flush=True)
triples = []
for (_o, a, b, _r, _T) in pairs[: max(3, BEAM_K // 2)]:
    if time.time() - t0 > budget * 0.8:
        break
    kab = keepK(XR, np.array([a, b])).all(0)
    ob3, ok3, n3, sr3, kb3, r3, T3 = evaluate(XR, extra=kab)
    ok3 &= (cf != cf[a]) & (cf != cf[b])
    o3 = np.where(ok3, ob3, -np.inf)
    c = int(np.argmax(o3))
    if np.isfinite(o3[c]):
        triples.append((float(o3[c]), a, b, c, r3[c], T3[c]))
triples.sort(key=lambda x: -x[0])
print("triples", len(triples), round(time.time() - t0, 1), flush=True)

# permutation null of the best single (max statistic), event photos permuted within day
rng = np.random.default_rng(int(os.environ.get('R04_SEED', '1311')))
null_best = []
rows_of = {}
for j in range(nR):
    rows_of.setdefault(ev[j], {})[bk[j]] = j
while time.time() - t0 < budget:
    perm_ev = np.arange(nE)
    for di in disc_days + test_days:
        e = np.flatnonzero(ev_day == di)
        perm_ev[e] = e[rng.permutation(len(e))]
    # row j of event e takes the photo of the same book's row in event perm(e), else that event's first row
    src = np.empty(nR, dtype=np.int64)
    for j in range(nR):
        tgt = rows_of[perm_ev[ev[j]]]
        src[j] = tgt.get(bk[j], ev_rep[perm_ev[ev[j]]])
    Xp = XR[src]
    obp, okp, *_ = evaluate(Xp)
    v = np.where(okp, obp, -np.inf).max()
    null_best.append(float(v))
null_best = np.array(null_best)
if os.environ.get('R04_ACCUM'):          # phase B: accumulate the null across several short runs (different seeds)
    fa = os.path.join(L.HERE, 'out_s2_null_accum.json')
    acc = json.load(open(fa)) if os.path.exists(fa) else {'real_best': float(objm.max()), 'null': [], 'seeds': []}
    acc['null'] += [float(v) for v in null_best]; acc['seeds'].append(os.environ.get('R04_SEED'))
    json.dump(acc, open(fa, 'w'))
    print('accumulated', len(acc['null']), 'p', (1 + sum(v >= acc['real_best'] for v in acc['null'])) / (1 + len(acc['null'])), flush=True)
real_best = float(objm.max())
pval = float((1 + np.sum(null_best >= real_best)) / (1 + len(null_best))) if len(null_best) else None
print("null perms", len(null_best), "p(best single)", pval, round(time.time() - t0, 1), flush=True)

out = {"base": base_desc, "base_obj": base_obj, "n_candidates": C, "n_valid": int(ok.sum()), "named": named_out,
       "big_trades": [{"day": d.day[R[b]], "time": d.time_in[R[b]], "book": d.book[R[b]], "ret": float(d.ret[R[b]])} for b in big],
       "singles": singles, "per_feature": list(per_feat.values()),
       "pairs": [dict(describe([a, b], r_, T_), obj=o_) for (o_, a, b, r_, T_) in pairs[:30]],
       "triples": [dict(describe([a, b, c], r_, T_), obj=o_) for (o_, a, b, c, r_, T_) in triples[:20]],
       "null": {"perms": len(null_best), "best_real": real_best, "null_q50": float(np.median(null_best)) if len(null_best) else None,
                "null_q95": float(np.quantile(null_best, 0.95)) if len(null_best) else None, "p": pval},
       "secs": round(time.time() - t0, 1)}
json.dump(out, open(os.path.join(L.HERE, "out_s2_conductor.json"), "w"), default=float)
print("BASE", base_desc)
for s in singles[:10]:
    print("S", s["conds"], s["disc_obj"], s["disc_n"], s["disc_sr"], "| test", s["test_days"], s["test_n"], s["test_sr"])
for p in out["pairs"][:8]:
    print("P", p["conds"], p["disc_obj"], p["disc_n"], p["disc_sr"], "| test", p["test_days"], p["test_n"], p["test_sr"])
for p in out["triples"][:5]:
    print("T", p["conds"], p["disc_obj"], p["disc_n"], p["disc_sr"], "| test", p["test_days"], p["test_n"], p["test_sr"])
print("done", out["secs"], flush=True)
