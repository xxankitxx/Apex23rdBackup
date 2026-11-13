"""R06: reprice the same entry/exit seconds on other strikes and the next weekly from ds_v2 quotes; greeks attribution
per trade; intraday theta clock (measured straddle decay vs calendar and kit theta). Read-only. Usage: a3_reprice.py DAY..."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, time
import numpy as np, pandas as pd
from scipy.special import ndtr
from datetime import datetime, timezone, timedelta
T0 = time.time()
IST = timezone(timedelta(hours=5, minutes=30))
DS = r"D:\ApexOptions\data\research\ds_v2"
W = r"D:\ApexOptions\data\research\13nov\work\R06"
B = r"D:\ApexOptions\data\replay\batch"
DAYS = sys.argv[1:] or ["2026-11-03", "2026-11-06", "2026-11-09"]
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
MAXAGE = 10.0
SIMR = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
PART = {"2026-10-27": ["2026-10-27.p2", "2026-10-27.p3"], "2026-10-23": ["2026-10-23", "2026-10-23.p2"],
        "2026-10-19": ["2026-10-19", "2026-10-19.p2", "2026-10-19.p3", "2026-10-19.p5"],
        "2026-10-29": ["2026-10-29.p3", "2026-10-29.p4", "2026-10-29.p5"], "2026-11-11": ["2026-11-11.p4"]}


def cond_trades(day):
    f = B + (r"\p44_simr\conductor_sim.json" if day in SIMR else r"\p44_sim\conductor_sim.json")
    d = json.load(open(f, encoding="utf-8"))["days"].get(day) or {}
    return [dict(t, day=day, book="CONDUCTOR") for t in d.get("trades") or []]


def years(exp_iso, te):
    e = datetime.fromisoformat(exp_iso).replace(hour=15, minute=30, tzinfo=IST).timestamp()
    same = datetime.fromtimestamp(te, IST).date().isoformat() == exp_iso
    return max(e - te, 600.0 if same else 60.0) / (365.0 * 86400.0)


def b76(F, K, T, s, call):
    sT = s * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    d2 = d1 - sT
    return np.where(call, F * ndtr(d1) - K * ndtr(d2), K * ndtr(-d2) - F * ndtr(-d1))


def ivol(p, F, K, T, call):
    p, K, call = np.atleast_1d(np.asarray(p, float)), np.atleast_1d(np.asarray(K, float)), np.atleast_1d(call)
    intr = np.where(call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    ok = np.isfinite(p) & (p > intr + 0.05)
    lo, hi = np.full(p.shape, 0.005), np.full(p.shape, 5.0)
    for _ in range(45):
        m = 0.5 * (lo + hi)
        below = b76(F, K, T, m, call) < p
        lo, hi = np.where(below, m, lo), np.where(below, hi, m)
    return np.where(ok, 0.5 * (lo + hi), np.nan)


def grk(F, K, T, s, call):
    sq = np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * s * s * T) / (s * sq)
    pdf = np.exp(-0.5 * d1 * d1) / np.sqrt(2 * np.pi)
    delta = np.where(call, ndtr(d1), ndtr(d1) - 1.0)
    gamma = pdf / (F * s * sq)
    th_year = -(F * pdf * s) / (2 * sq)
    vega = F * pdf * sq / 100.0
    return delta, gamma, th_year / 525600.0, vega          # theta per CALENDAR minute; kit = x 1440/375


def load_day(day):
    parts = PART.get(day, [day])
    zs = [np.load(DS + f"\\{p}.npz") for p in parts]
    zs = [z for z in zs if len(z["t"]) > 0]
    out = {}
    k0 = zs[0]
    for key in ("strikes", "strikes2", "expiry", "expiry2"):
        out[key] = k0[key]
    for z in zs[1:]:
        if list(z["strikes"]) != list(k0["strikes"]) or list(z["strikes2"]) != list(k0["strikes2"]):
            print("WARN strike lists differ across parts", day)
    for key in ("t", "fut", "opt", "age", "opt2", "age2"):
        out[key] = np.concatenate([z[key] for z in zs]) if len(zs) > 1 else zs[0][key]
    return out


rows_out, clock_out, ivpath_out = [], [], []
tab = pd.read_parquet(W + r"\t_small.parquet", columns=["day", "book", "rr", "strike", "entry", "exit", "t_in", "t_out", "ret_pct"])
for day in DAYS:
    z = load_day(day)
    t, fut = z["t"], z["fut"]
    opt, age, opt2, age2 = z["opt"], z["age"], z["opt2"], z["age2"]
    ks, ks2 = z["strikes"].astype(int), z["strikes2"].astype(int)
    exp, exp2 = str(z["expiry"]), str(z["expiry2"])
    bid, ask = opt[..., 0], opt[..., 1]
    okq = np.isfinite(bid) & np.isfinite(ask) & (bid > 0)
    print(day, "rows", len(t), "exp", exp, exp2, "strikes", len(ks), len(ks2), "bid<=ask share",
          round(float((bid[okq] <= ask[okq]).mean()), 4), flush=True)
    si = {int(k): i for i, k in enumerate(ks)}
    si2 = {int(k): i for i, k in enumerate(ks2)}
    fmid = np.where(np.isfinite(fut[:, 0]) & np.isfinite(fut[:, 1]) & (fut[:, 0] > 0), 0.5 * (fut[:, 0] + fut[:, 1]), fut[:, 2])

    def q(which, r, K, rr):
        """(bid, ask, age) of a contract at row r"""
        a_, g_, m_ = (opt, age, si) if which == 0 else (opt2, age2, si2)
        j = m_.get(int(K))
        if j is None or r < 0 or r >= len(t):
            return np.nan, np.nan, 1e9
        c = 0 if rr == "CE" else 1
        return float(a_[r, j, c, 0]), float(a_[r, j, c, 1]), float(g_[r, j, c])

    def fwd(r, which=0):
        a_, g_, kk = (opt, age, ks) if which == 0 else (opt2, age2, ks2)
        ref = fmid[r]
        if not np.isfinite(ref) or len(kk) == 0:
            return np.nan
        order = np.argsort(np.abs(kk - ref))
        vals = []
        for jj in order[:6]:
            cb, ca, pb, pa = a_[r, jj, 0, 0], a_[r, jj, 0, 1], a_[r, jj, 1, 0], a_[r, jj, 1, 1]
            if np.isfinite([cb, ca, pb, pa]).all() and min(cb, pb) > 0 and g_[r, jj, 0] < MAXAGE and g_[r, jj, 1] < MAXAGE:
                vals.append(kk[jj] + 0.5 * (cb + ca) - 0.5 * (pb + pa))
            if len(vals) == 2:
                break
        F = float(np.mean(vals)) if vals else float(ref)
        return F if abs(F - ref) < 150 else float(ref)

    # ---------------- trades
    trs = cond_trades(day) + tab[(tab.day == day) & tab.book.isin(POOL)].to_dict("records")
    for tr_ in trs:
        ti, to = float(tr_["t_in"]), float(tr_["t_out"])
        ri = int(np.searchsorted(t, ti, "right") - 1)
        ro = int(np.searchsorted(t, to, "right") - 1)
        K, rr = int(tr_["strike"]), tr_["rr"]
        dK = -50 if rr == "CE" else 50
        cl = rr == "CE"
        sgn = 1 if cl else -1
        Fi, Fo = fwd(ri), fwd(ro)
        Fi2, Fo2 = (fwd(ri, 1), fwd(ro, 1)) if exp2 else (np.nan, np.nan)
        Ti, To = years(exp, ti), years(exp, to)
        Ti2, To2 = (years(exp2, ti), years(exp2, to)) if exp2 else (np.nan, np.nan)
        rec = dict(day=day, book=tr_["book"], src=tr_.get("src"), rr=rr, K=K, t_in=ti, t_out=to, hold_min=(to - ti) / 60,
                   rec_entry=tr_["entry"], rec_exit=tr_["exit"], rec_ret=tr_["ret_pct"], F_in=Fi, F_out=Fo,
                   dF_with=sgn * (Fo - Fi) if np.isfinite(Fi) and np.isfinite(Fo) else np.nan)
        for off in (-1, 0, 1):
            rec[f"ask_off{off}"] = q(0, ri + off, K, rr)[1]
            rec[f"bid_out_off{off}"] = q(0, ro + off, K, rr)[0]
        alts = {"base": (0, K), "itm1": (0, K + dK), "itm2": (0, K + 2 * dK), "otm1": (0, K - dK),
                "nw_same": (1, K), "nw_itm1": (1, K + dK), "nw_itm2": (1, K + 2 * dK)}
        for nm, (wh, KK) in alts.items():
            if wh == 1 and not exp2:
                continue
            bi, ai, gi = q(wh, ri, KK, rr)
            bo, ao, go = q(wh, ro, KK, rr)
            ok = bool(np.isfinite(ai) and np.isfinite(bo) and ai > 0 and bo >= 0 and gi <= MAXAGE and go <= MAXAGE)
            rec[f"{nm}_ok"] = ok
            rec[f"{nm}_ret"] = 100 * (bo / ai - 1) if ok else np.nan
            mi, mo = 0.5 * (bi + ai), 0.5 * (bo + ao)
            rec[f"{nm}_retmid"] = 100 * (mo / mi - 1) if ok and np.isfinite(mi) and np.isfinite(mo) and mi > 0 else np.nan
            rec[f"{nm}_ask"] = ai
            rec[f"{nm}_sprd_pct"] = 100 * (ai - bi) / mi if np.isfinite(bi) and np.isfinite(mi) and mi > 0 else np.nan
            F_, T_ = (Fi, Ti) if wh == 0 else (Fi2, Ti2)
            F2, T2 = (Fo, To) if wh == 0 else (Fo2, To2)
            if np.isfinite(mi) and np.isfinite(F_) and np.isfinite(T_):
                s0 = float(ivol(mi, F_, KK, T_, cl)[0])
                if np.isfinite(s0):
                    d_, g_, th_, v_ = (float(x) for x in grk(F_, KK, T_, s0, cl))
                    rec[f"{nm}_iv"], rec[f"{nm}_delta"], rec[f"{nm}_gamma"] = 100 * s0, d_, g_
                    rec[f"{nm}_th_cal"], rec[f"{nm}_vega"] = th_, v_
                    rec[f"{nm}_gear_pct_pt"] = 100 * abs(d_) / mi
                    if ok and np.isfinite(mo) and np.isfinite(F2):
                        s1 = float(ivol(mo, F2, KK, T2, cl)[0])
                        dF = F2 - F_
                        rec[f"{nm}_iv_out"] = 100 * s1 if np.isfinite(s1) else np.nan
                        rec[f"{nm}_a_delta"] = d_ * dF
                        rec[f"{nm}_a_gamma"] = 0.5 * g_ * dF * dF
                        rec[f"{nm}_a_theta_cal"] = th_ * (to - ti) / 60
                        rec[f"{nm}_a_vega"] = v_ * (100 * (s1 - s0)) if np.isfinite(s1) else np.nan
                        rec[f"{nm}_a_total_mid"] = mo - mi
                        rec[f"{nm}_spread_cost"] = (ai - bi) / 2 + (ao - bo) / 2
        if np.isfinite(rec.get("base_delta", np.nan)) and exp2 and np.isfinite(Fi2):
            best = None
            for KK in ks2:
                if abs(KK - K) > 300:
                    continue
                bi, ai, gi = q(1, ri, KK, rr)
                if not (np.isfinite(ai) and np.isfinite(bi) and gi <= MAXAGE and bi > 0):
                    continue
                s0 = float(ivol(0.5 * (bi + ai), Fi2, KK, Ti2, cl)[0])
                if not np.isfinite(s0):
                    continue
                d_ = float(grk(Fi2, KK, Ti2, s0, cl)[0])
                e = abs(abs(d_) - abs(rec["base_delta"]))
                if best is None or e < best[0]:
                    best = (e, int(KK), d_)
            if best:
                KK = best[1]
                bi, ai, gi = q(1, ri, KK, rr)
                bo, ao, go = q(1, ro, KK, rr)
                ok = bool(np.isfinite(ai) and np.isfinite(bo) and gi <= MAXAGE and go <= MAXAGE and ai > 0)
                rec["nw_dm_K"], rec["nw_dm_delta"], rec["nw_dm_ok"] = KK, best[2], ok
                rec["nw_dm_ret"] = 100 * (bo / ai - 1) if ok else np.nan
        rows_out.append(rec)
    print(day, "trades", len(trs), "elapsed", round(time.time() - T0, 1), flush=True)

    pd.DataFrame(rows_out).to_csv(W + "/reprice_" + day[5:] + ".csv", index=False)
    if __import__("os").environ.get("NOCLOCK"):
        continue
    # ---------------- theta clock: 5-min ATM straddle change at a fixed strike, vs calendar theta
    hm = ((t.astype(np.int64) + 19800) % 86400) / 60.0
    rs = np.nonzero((hm >= 9 * 60 + 25) & (hm <= 15 * 60 + 10))[0][::60]
    for r0 in rs:
        r1 = int(np.searchsorted(t, t[r0] + 300, "left"))
        if r1 >= len(t) or t[r1] - t[r0] > 310:
            continue
        F0, F1 = fwd(r0), fwd(r1)
        if not (np.isfinite(F0) and np.isfinite(F1)):
            continue
        K0 = int(ks[np.argmin(np.abs(ks - F0))])
        c0b, c0a, gc0 = q(0, r0, K0, "CE"); p0b, p0a, gp0 = q(0, r0, K0, "PE")
        c1b, c1a, gc1 = q(0, r1, K0, "CE"); p1b, p1a, gp1 = q(0, r1, K0, "PE")
        if max(gc0, gp0, gc1, gp1) > 5 or not np.isfinite([c0b, c0a, p0b, p0a, c1b, c1a, p1b, p1a]).all():
            continue
        S0 = 0.5 * (c0b + c0a + p0b + p0a); S1 = 0.5 * (c1b + c1a + p1b + p1a)
        T_ = years(exp, float(t[r0]))
        sc = float(ivol(0.5 * (c0b + c0a), F0, K0, T_, True)[0])
        sp = float(ivol(0.5 * (p0b + p0a), F0, K0, T_, False)[0])
        s = np.nanmean([sc, sp])
        if not np.isfinite(s):
            continue
        dc, gc, thc, vc = (float(x) for x in grk(F0, K0, T_, s, True))
        dp, gp, thp, vp = (float(x) for x in grk(F0, K0, T_, s, False))
        dF = F1 - F0
        expl = (dc + dp) * dF + 0.5 * (gc + gp) * dF * dF
        clock_out.append(dict(day=day, hm=float(hm[r0]), K0=K0, S0=S0, dS=S1 - S0, dF=dF, expl=expl,
                              th_cal5=5 * (thc + thp), iv=100 * s, T_min=T_ * 525600))
    # ---------------- ATM IV path through the day (calendar time)
    for hh, mm in ((9, 20), (9, 45), (10, 30), (11, 30), (12, 30), (13, 30), (14, 30), (15, 0), (15, 15)):
        tgt = datetime.fromisoformat(day).replace(hour=hh, minute=mm, tzinfo=IST).timestamp()
        r0 = int(np.searchsorted(t, tgt, "left"))
        if r0 >= len(t) or t[r0] - tgt > 120:
            continue
        F0 = fwd(r0)
        if not np.isfinite(F0):
            continue
        K0 = int(ks[np.argmin(np.abs(ks - F0))])
        T_ = years(exp, float(t[r0]))
        vals = []
        for rr in ("CE", "PE"):
            b_, a_, g_ = q(0, r0, K0, rr)
            if g_ <= MAXAGE and np.isfinite(b_) and np.isfinite(a_):
                vals.append(float(ivol(0.5 * (b_ + a_), F0, K0, T_, rr == "CE")[0]))
        iv2 = []
        if exp2:
            K2 = int(ks2[np.argmin(np.abs(ks2 - F0))]); T2 = years(exp2, float(t[r0])); F2 = fwd(r0, 1)
            for rr in ("CE", "PE"):
                b_, a_, g_ = q(1, r0, K2, rr)
                if g_ <= MAXAGE and np.isfinite(b_) and np.isfinite(a_) and np.isfinite(F2):
                    iv2.append(float(ivol(0.5 * (b_ + a_), F2, K2, T2, rr == "CE")[0]))
        ivpath_out.append(dict(day=day, at=f"{hh:02d}:{mm:02d}", F=F0, K=K0, iv_w0=100 * np.nanmean(vals) if vals else np.nan,
                               iv_w1=100 * np.nanmean(iv2) if iv2 else np.nan, T_min=T_ * 525600))
    del z, opt, age, opt2, age2
    print(day, "done", round(time.time() - T0, 1), flush=True)

tag = "_".join(d[5:] for d in DAYS)
pd.DataFrame(rows_out).to_csv(W + f"\\reprice_{tag}.csv", index=False)
pd.DataFrame(clock_out).to_csv(W + f"\\clock_{tag}.csv", index=False)
pd.DataFrame(ivpath_out).to_csv(W + f"\\ivpath_{tag}.csv", index=False)
print("saved", round(time.time() - T0, 1))
