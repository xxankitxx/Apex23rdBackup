import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, json, time, os
T0 = time.time()
PARTS = sys.argv[1:] or ["2026-10-26", "2026-11-05", "2026-11-09"]
ROOT = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
TAG = os.environ.get("R08_TAG", "s04")
BANK = ("bank", "nbfc")


def load(part):
    z = np.load(os.path.join(ROOT, part + ".npz"), allow_pickle=True)
    t = z["t"].astype(np.int64); fut = z["fut"]; fa = z["fa"][:, 0]
    hw = z["hw"].astype(float); hwa = z["hwa"]; sf = z["sf"].astype(float); sfa = z["sfa"]
    w = z["w"].astype(float); g = z["g"]; sym = z["sym"]
    n = int(t[-1] - t[0] + 1); idx = t - t[0]

    def grid(a):
        o = np.full((n,) + a.shape[1:], np.nan); o[idx] = a; return o
    mid = 0.5 * (fut[:, 0] + fut[:, 1]); okf = (fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa <= 3)
    F = grid(np.where(okf, mid, np.nan))
    cash = np.where((hw > 0) & (hwa <= 5), hw, np.nan)
    sfm = 0.5 * (sf[:, :, 0] + sf[:, :, 1])
    sfm = np.where((sf[:, :, 0] > 0) & (sf[:, :, 1] >= sf[:, :, 0]) & (sfa <= 5), sfm, np.nan)
    return dict(t0=int(t[0]), n=n, F=F, lc=np.log(grid(cash)), ls=np.log(grid(sfm)), w=w, g=g, sym=sym)


def basket(lp, w, L, mask=None):
    """weighted mean log return over L s (index-equivalent fraction); NaN if covered weight < 70 %"""
    d = np.full(lp.shape, np.nan); d[L:] = lp[L:] - lp[:-L]
    ww = w * (mask if mask is not None else 1.0)
    ok = np.isfinite(d) & (ww > 0)
    num = np.where(ok, d * ww, 0).sum(1); den = np.where(ok, ww, 0).sum(1)
    tot = ww.sum()
    return np.where(den >= 0.7 * tot, num / np.where(den > 0, den, 1), np.nan)


def breadth(lp, w, L):
    d = np.full(lp.shape, np.nan); d[L:] = lp[L:] - lp[:-L]
    ok = np.isfinite(d); ww = np.where(ok, w, 0)
    den = ww.sum(1)
    return np.where(den >= 0.7 * w.sum(), (np.sign(np.where(ok, d, 0)) * ww).sum(1) / np.where(den > 0, den, 1), np.nan)


def dF(F, L):
    o = np.full(F.shape, np.nan); o[L:] = F[L:] - F[:-L]; return o


def fwd(F, h):
    o = np.full(F.shape, np.nan); o[:-h] = F[h:] - F[:-h]; return o


res, data = {}, {}
for part in PARTS:
    D = load(part); F = D["F"]; w = D["w"]
    r = {"n": D["n"], "fut_valid": float(np.isfinite(F).mean())}
    xc = {}
    for S in (5, 10, 30, 60, 300):
        fF = dF(F, S)[S::S]; fC = (basket(D["lc"], w, S) * F)[S::S]; fS = (basket(D["ls"], w, S) * F)[S::S]
        row = {}
        for nm, x in (("cash", fC), ("sfut", fS)):
            cc = {}
            for k in range(-3, 4):          # k > 0: the basket's return k steps EARLIER vs the future's now (basket leads)
                if k >= 0:
                    a, b = fF[k:], x[:len(x) - k]
                else:
                    a, b = fF[:len(fF) + k], x[-k:]
                m = np.isfinite(a) & np.isfinite(b)
                cc[k] = round(float(np.corrcoef(a[m], b[m])[0, 1]), 3) if m.sum() > 20 else None
            row[nm] = cc
        xc[S] = row
    r["xcorr"] = xc
    data[part] = D
    res[part] = r
    print(part, "xcorr done", round(time.time() - T0, 1), flush=True)


def design(D, h, L):
    F = D["F"]; w = D["w"]; g = D["g"]
    own = dF(F, L); cash = basket(D["lc"], w, L) * F; sfut = basket(D["ls"], w, L) * F
    bm = np.isin(g, BANK).astype(float)
    bank = basket(D["lc"], w, L, bm) * F
    nonb = basket(D["lc"], w, L, 1.0 - bm) * F
    b60 = breadth(D["lc"], w, 60)
    y = fwd(F, h)
    X = np.c_[own, cash - own, sfut - own, bank - nonb, b60]
    sl = slice(L, None, max(h, 5))
    X, y = X[sl], y[sl]
    m = np.isfinite(X).all(1) & np.isfinite(y)
    return X[m], y[m]


names = ["own", "cash_gap", "sfut_gap", "bank_minus_rest", "breadth60"]
gr = {}
for h, L in ((5, 10), (10, 10), (30, 30), (60, 60), (300, 120)):
    Xs = {p: design(data[p], h, L) for p in PARTS}
    out = {}
    for test in PARTS:
        trn = [p for p in PARTS if p != test]
        Xa = np.vstack([Xs[p][0] for p in trn]); ya = np.concatenate([Xs[p][1] for p in trn])
        Xt, yt = Xs[test]
        sets = {"own": [0], "own+cash": [0, 1], "own+sfut": [0, 2], "own+all": [0, 1, 2, 3, 4],
                "cash_only": [1], "sfut_only": [2], "bank_rest": [3], "breadth": [4]}
        o = {}
        for sn, ix in sets.items():
            A = np.c_[np.ones(len(Xa)), Xa[:, ix]]; beta = np.linalg.lstsq(A, ya, rcond=None)[0]
            pt = np.c_[np.ones(len(Xt)), Xt[:, ix]] @ beta
            r2 = 1 - np.sum((yt - pt) ** 2) / np.sum((yt - yt.mean()) ** 2)
            dev = pt - beta[0]
            big = np.abs(dev) >= np.quantile(np.abs(dev), 0.9)
            hit = float(np.mean(np.sign(dev[big]) == np.sign(yt[big]))) if big.sum() > 10 else None
            mv = float(np.mean(np.sign(dev[big]) * yt[big])) if big.sum() > 10 else None
            o[sn] = dict(r2=round(float(r2), 4), hit10=None if hit is None else round(hit, 3),
                         pts10=None if mv is None else round(mv, 2), n=int(len(yt)), ntop=int(big.sum()),
                         beta=[round(float(b), 4) for b in beta])
        out[test] = o
    gr[f"h{h}_L{L}"] = out
    print("granger", h, L, round(time.time() - T0, 1), flush=True)

ev = {}
for part in PARTS:
    D = data[part]; F = D["F"]; w = D["w"]
    b60 = breadth(D["lc"], w, 60); own60 = dF(F, 60); cash60 = basket(D["lc"], w, 60) * F
    f30, f60, f300 = fwd(F, 30), fwd(F, 60), fwd(F, 300)
    th = []
    last = -10 ** 9
    for i in range(90, len(b60)):
        if not np.isfinite(b60[i]):
            continue
        if abs(b60[i]) >= 0.8 and i - last > 120:
            prev = b60[i - 30]
            if np.isfinite(prev) and abs(prev) < 0.3:
                d = np.sign(b60[i]); last = i
                th.append((d, own60[i] * d, f30[i] * d, f60[i] * d, f300[i] * d))
    q = np.nanquantile(np.abs(own60), 0.9)
    dv, cf = [], []
    last = last2 = -10 ** 9
    for i in range(60, len(own60)):
        o_, c_ = own60[i], cash60[i]
        if not (np.isfinite(o_) and np.isfinite(c_)) or abs(o_) < q:
            continue
        d = np.sign(o_)
        if c_ * d <= -3 and i - last > 120:
            last = i; dv.append((own60[i] * d, c_ * d, f30[i] * d, f60[i] * d, f300[i] * d))
        elif c_ * d >= abs(o_) * 0.9 and i - last2 > 120:
            last2 = i; cf.append((own60[i] * d, c_ * d, f30[i] * d, f60[i] * d, f300[i] * d))

    def summ(a, k0=2):
        a = np.array(a, float)
        if len(a) == 0:
            return dict(n=0)
        s = {"n": int(len(a))}
        for j, nm in ((k0, "f30"), (k0 + 1, "f60"), (k0 + 2, "f300")):
            x = a[:, j][np.isfinite(a[:, j])]
            s[nm] = dict(mean=round(float(x.mean()), 2), hit=round(float((x > 0).mean()), 3)) if len(x) else None
        return s
    ev[part] = dict(thrust=summ(th, 2), q90_own60=round(float(q), 1), diverge=summ(dv), confirm=summ(cf))
    print("events", part, round(time.time() - T0, 1), flush=True)

json.dump(dict(xcorr={p: res[p] for p in PARTS}, granger=gr, events=ev, names=names),
          open(os.path.join(OUT, TAG + "_leadlag.json"), "w"), indent=1)
for p in PARTS:
    print(p, "fut_valid", round(res[p]["fut_valid"], 3))
    for S, row in res[p]["xcorr"].items():
        print("  S", S, "cash", row["cash"], "sfut", row["sfut"])
for k, v in gr.items():
    for test, o in v.items():
        print(k, "test", test, {sn: (x["r2"], x["hit10"], x["pts10"]) for sn, x in o.items()})
print(json.dumps(ev, indent=1))
print("secs", round(time.time() - T0, 1))
