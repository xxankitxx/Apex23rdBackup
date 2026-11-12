"""PR-004: the pricing-only scorecard (PKG-08, 12 Nov 2026; lifted from the council's L2 scratch study).

Given the REALISED forward move, how well does each pricing convention predict a fixed contract's mid h seconds later?
This isolates the option mapping (the decay clock, how IV reacts to a move) from the market's direction, which no
pricer can know. Every 15 s, every strike within 150 points of the forward, both rights, premium of 5 or more:

  naive          the mid does not change
  delta          mid + Delta x dFs
  calendar       Black-76 at the realised forward, total variance iv^2 T run down on the calendar clock (T - h/SPY)
  trade384       the old Lab clock: a calendar day of variance spread over 375 trading minutes (x 3.84)
  business       the business clock (apex/forecast_lab/clock.py): variance run down at k_ts = T_cal SPY / tau_left
  business_mny   business clock, sticky moneyness instead of sticky strike (the smile slides with the forward)
  business_beta  business clock with an online fixed-strike IV beta per moneyness bucket, fitted only on checks that
                 matured before (a challenger: it is used nowhere unless it beats sticky strike here)

Each prediction is scored against the actual mid at t + h: MAE and bias in % of the starting premium, by DTE bucket
(0, 1, 2+ days), per session and pooled. No convention has a fitted number except business_beta, whose fit is causal
(walk-forward within and across sessions in date order), so the whole run is out of sample.

The PR-004 verdict (Stage B of PKG-08 ships only on a pass):
  * at 15 minutes, |bias| of 'business' is no worse than 'calendar' on at least 2/3 of sessions, and
  * on expiry days (bucket 0), |bias| of 'business' at 15 minutes is at most 1 % of premium.

It also measures the IV noise table clock.py uses in Stage B: the sd (vol points) of the at-the-money IV change at
5, 15 and 30 minutes after taking out a fitted beta x dFs, per clock bucket (exp, 1-2, 3+), and writes it under
'iv_sd' (a bucket with fewer than MIN_IV_N observations is left out, so clock.py keeps its default for it).

Output: data/forecast_lab/reprice.json (atomic write). ledger_row(day) and append_ledger(row) give one row per day for
the nightly record (PKG-10 calls them; this script does not schedule anything).

Run (owner's OK first: about 10-20 minutes on an idle machine for the 16 recorded sessions, one process):
    py -3.13 research/forecast_lab/reprice_study.py [--days 2026-10-19 2026-10-21 ...] [--out path.json]
Read-only on the tapes (data/research/ds_v2); it writes only the output file."""
import argparse
import glob
import heapq
import json
import math
import os
import sys
import time
from datetime import datetime

os.environ.setdefault("OMP_NUM_THREADS", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402

from apex import config, greeks  # noqa: E402
from apex.forecast_lab import clock as CK  # noqa: E402
from apex.forecast_lab.core import SPY, b76, b76_greeks, iv_newton  # noqa: E402

DS = os.path.join(ROOT, "data", "research", "ds_v2")
OUT = os.path.join(config.DATA_DIR, "forecast_lab", "reprice.json")
LEDGER = os.path.join(config.DATA_DIR, "forecast_lab", "reprice_ledger.jsonl")
OPEN_S, CLOSE_S = 9 * 3600 + 15 * 60, 15 * 3600 + 30 * 60
HS = (300, 900, 1800)
EVERY = 15
NEAR = 150.0
MIN_PREMIUM = 5.0
MIN_IV_N = 200
MNY_EDGES = (-0.02, -0.01, -0.004, 0.004, 0.01, 0.02)      # log-moneyness buckets of the beta challenger
MODELS = ("naive", "delta", "calendar", "trade384", "business", "business_mny", "business_beta")
BIAS_EXPIRY_MAX = 1.0                                     # % of premium
SHARE_SESSIONS = 2.0 / 3.0


def sod(t):
    return (int(t) + 19800) % 86400


def bucket(dte):
    return "0" if dte < 1.0 else ("1" if dte < 2.0 else "2+")


def parts_for(day, ds=DS):
    return sorted(glob.glob(os.path.join(ds, f"{day}*.npz")))


def snapshots(path):
    """Every EVERY seconds in the session: forward, calendar T, business clock, strike IVs and mids. {t: dict}."""
    z = np.load(path)
    if z["t"].ndim != 1 or len(z["t"]) == 0:
        return {}
    n = len(z["strikes"])
    order = np.argsort(z["strikes"])
    K = z["strikes"][order].astype(float)
    o = z["opt"][:, :n].astype(float)[:, order]
    age = z["age"][:, :n].astype(float)[:, order]
    t = z["t"].astype(float)
    fut, fa = z["fut"].astype(float), z["fa"].astype(float)
    exp = str(z["expiry"])
    S = {}
    for i in range(len(t)):
        ti = int(t[i])
        if ti % EVERY:
            continue
        s = sod(t[i])
        if not (OPEN_S + 300 <= s < CLOSE_S - 30):
            continue
        fb, fk = fut[i, 0], fut[i, 1]
        if not (np.isfinite(fb) and np.isfinite(fk) and fb > 0 and fk >= fb and fa[i, 0] <= 3.0):
            continue
        ob, oa, og = o[i, :, :, 0], o[i, :, :, 1], age[i]
        two = (ob > 0) & (oa >= ob) & (og <= 15.0)
        mid = np.where(two, 0.5 * (ob + oa), np.nan)
        Fs = greeks.synthetic_forward(K, mid[:, 0], mid[:, 1], 0.5 * (fb + fk))
        if not Fs or not np.isfinite(Fs):
            continue
        Fs = float(Fs)
        now = datetime.fromtimestamp(t[i], config.IST)
        T = greeks.years_to_expiry(exp, now)
        k, tau, _ = CK.k_ts(now, exp, T)
        cs = K >= Fs
        with np.errstate(all="ignore"):
            iv = iv_newton(np.where(cs, mid[:, 0], mid[:, 1]), Fs, K, T, cs)
        okv = np.isfinite(iv)
        atm = float(np.interp(Fs, K[okv], iv[okv])) if okv.sum() >= 2 else np.nan
        S[ti] = dict(Fs=Fs, T=T, k=k, iv=iv, atm=atm, mid=mid, dte=T * 365.0, exp=exp)
    S["_K"] = K
    return S


class BetaOnline:
    """Fixed-strike IV beta per (DTE bucket, moneyness bucket): a ratio of running sums, updated only with checks that
    have matured (causal), shrunk to 0 (sticky strike) by a prior of PRIOR_XX points^2."""
    PRIOR_XX = 2.0e5

    def __init__(self):
        self.sxx, self.sxy = {}, {}

    def key(self, b, lk):
        return b, int(np.searchsorted(MNY_EDGES, lk))

    def beta(self, b, lk):
        k = self.key(b, lk)
        return self.sxy.get(k, 0.0) / (self.PRIOR_XX + self.sxx.get(k, 0.0))

    def learn(self, b, lk, dF, div):
        k = self.key(b, lk)
        self.sxx[k] = self.sxx.get(k, 0.0) + dF * dF
        self.sxy[k] = self.sxy.get(k, 0.0) + dF * div


def score_part(S, acc, beta, ivs, pending, day):
    """Add one part's checks to acc[(day, bucket, h)][model] = [n, sum |e|, sum e]; IV changes to ivs. pending is a
    heap of (time matured, ...) beta lessons; each is learned only once its check time has passed."""
    K = S.get("_K")
    if K is None:
        return
    keys = sorted(k for k in S if k != "_K")
    for ti in keys:
        a = S[ti]
        # matured beta lessons first (strictly before this check is made)
        while pending and pending[0][0] <= ti:
            _, b_, lk_, dF_, div_ = heapq.heappop(pending)
            beta.learn(b_, lk_, dF_, div_)
        b = bucket(a["dte"])
        sel = np.where(np.isfinite(a["iv"]) & (np.abs(K - a["Fs"]) <= NEAR))[0]
        for h in HS:
            c = S.get(ti + h)
            if c is None:
                continue
            tc = a["T"] * SPY                                    # calendar seconds left
            if a["k"] is None or tc - h * a["k"] < 120.0:        # too close to the expiry for this horizon
                continue
            dF = c["Fs"] - a["Fs"]
            if np.isfinite(a["atm"]) and np.isfinite(c["atm"]):
                ivs.setdefault((CK.dte_bucket(a["dte"]), h), []).append((dF, (c["atm"] - a["atm"]) * 100.0))
            okv = np.isfinite(a["iv"])
            for j in sel:
                iv0 = float(a["iv"][j])
                lk = math.log(K[j] / a["Fs"])
                if np.isfinite(c["iv"][j]):
                    heapq.heappush(pending, (ti + h, b, lk, dF, float(c["iv"][j]) - iv0))
                for rr in (0, 1):
                    m0, m1 = a["mid"][j, rr], c["mid"][j, rr]
                    if not (np.isfinite(m0) and np.isfinite(m1)) or m0 < MIN_PREMIUM:
                        continue
                    call = rr == 0
                    anc = m0 - float(b76(a["Fs"], K[j], a["T"], iv0, call))
                    g = b76_greeks(a["Fs"], K[j], a["T"], iv0, call)
                    w0 = iv0 * iv0 * a["T"]

                    def px(w):                               # total variance w left, at the realised forward
                        return float(b76(c["Fs"], K[j], 1.0, math.sqrt(max(w, 1e-12)), call)) + anc
                    f_cal = max(0.0, 1.0 - h / tc)
                    f_384 = max(0.0, 1.0 - h * (1440.0 / 375.0) / tc)
                    f_biz = max(0.0, 1.0 - h * a["k"] / tc)
                    iv_m = float(np.interp(K[j] * a["Fs"] / c["Fs"], K[okv], a["iv"][okv]))
                    bb = beta.beta(b, lk)
                    pred = dict(naive=m0, delta=m0 + float(g["delta"]) * dF, calendar=px(w0 * f_cal),
                                trade384=px(w0 * f_384), business=px(w0 * f_biz),
                                business_mny=px(iv_m * iv_m * a["T"] * f_biz),
                                business_beta=px(max(iv0 + bb * dF, 0.01) ** 2 * a["T"] * f_biz))
                    A = acc.setdefault((day, b, h), {})
                    for nm, v in pred.items():
                        e = (v - m1) / m0 * 100.0
                        d = A.setdefault(nm, [0, 0.0, 0.0])
                        d[0] += 1
                        d[1] += abs(e)
                        d[2] += e


def summarise(acc):
    """Pooled and per-session tables from the raw sums."""
    pooled, per = {}, {}
    for (day, b, h), A in acc.items():
        for tgt in (pooled.setdefault((b, h), {}), per.setdefault((day, b, h), {})):
            for nm, d in A.items():
                x = tgt.setdefault(nm, [0, 0.0, 0.0])
                x[0] += d[0]
                x[1] += d[1]
                x[2] += d[2]

    def fmt(T):
        return {nm: dict(n=d[0], mae_pct=round(d[1] / d[0], 3), bias_pct=round(d[2] / d[0], 3))
                for nm, d in T.items() if d[0]}
    return ({f"{b}|{h}": fmt(T) for (b, h), T in sorted(pooled.items())},
            {f"{day}|{b}|{h}": fmt(T) for (day, b, h), T in sorted(per.items())})


def verdict(per_session, pooled):
    """PR-004 from the tables: (passed, reasons)."""
    days = sorted({k.split("|")[0] for k in per_session})
    wins, n = 0, 0
    for day in days:
        rows = [v for k, v in per_session.items() if k.startswith(day + "|") and k.endswith("|900")]
        nb = sum(r["business"]["n"] for r in rows if "business" in r)
        if not nb:
            continue
        bb = sum(r["business"]["bias_pct"] * r["business"]["n"] for r in rows if "business" in r) / nb
        nc = sum(r["calendar"]["n"] for r in rows if "calendar" in r)
        bc = sum(r["calendar"]["bias_pct"] * r["calendar"]["n"] for r in rows if "calendar" in r) / max(nc, 1)
        n += 1
        wins += abs(bb) <= abs(bc)
    exp = (pooled.get("0|900") or {}).get("business")
    why = []
    share = wins / n if n else 0.0
    ok1 = n > 0 and share >= SHARE_SESSIONS
    why.append(f"15-min |bias|: business no worse than calendar on {wins} of {n} sessions ({share:.0%}; needs 67 %)")
    ok2 = exp is not None and abs(exp["bias_pct"]) <= BIAS_EXPIRY_MAX
    why.append("expiry days, 15 min: " + (f"business bias {exp['bias_pct']:+.2f} % (needs within 1 %)" if exp else
                                          "no expiry-day checks"))
    return bool(ok1 and ok2), why


def iv_sd_table(ivs):
    """sd (vol points) of the ATM IV change after a fitted beta x dF, per clock bucket at 5/15/30 min."""
    out = {}
    for b in ("exp", "1-2", "3+"):
        row = []
        for h in CK.IV_SD_H:
            x = np.array(ivs.get((b, h), []), float)
            if len(x) < MIN_IV_N:
                row = None
                break
            dF, dv = x[:, 0], x[:, 1]
            bb = float(np.dot(dF, dv) / max(np.dot(dF, dF), 1e-9))
            row.append(round(float(np.std(dv - bb * dF)), 3))
        if row and all(a <= c for a, c in zip(row, row[1:])):
            out[b] = row
    return out


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def run(days, ds=DS, log=print):
    acc, ivs, beta = {}, {}, BetaOnline()
    t0 = time.time()
    pending = []
    for day in days:
        for p in parts_for(day, ds):
            try:
                S = snapshots(p)
            except (OSError, KeyError, ValueError) as e:
                log(f"{os.path.basename(p)}: not read ({type(e).__name__}: {e})")
                continue
            score_part(S, acc, beta, ivs, pending, day)
            log(f"{os.path.basename(p)} {time.time() - t0:.0f}s")
        while pending:                                   # the day is over: every lesson has matured
            _, b_, lk_, dF_, div_ = heapq.heappop(pending)
            beta.learn(b_, lk_, dF_, div_)
    pooled, per = summarise(acc)
    ok, why = verdict(per, pooled)
    return dict(built=datetime.now(config.IST).isoformat(timespec="seconds"), days=list(days), pooled=pooled,
                per_session=per, pr004=dict(passed=ok, why=why), iv_sd=iv_sd_table(ivs),
                secs=round(time.time() - t0, 1))


def ledger_row(day, ds=DS):
    """One nightly row for the day (PKG-10 calls this): the day's 5/15/30-min MAE and bias of each model by bucket."""
    res = run([day], ds, log=lambda *_: None)
    return dict(day=day, kind="reprice", pooled=res["pooled"], iv_sd=res["iv_sd"], secs=res["secs"])


def append_ledger(row, path=LEDGER):
    """Append one row (a day already on file is not added twice)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("day") == row.get("day"):
                        return False
                except ValueError:
                    continue
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", nargs="*", help="sessions (default: every recorded one)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--ds", default=DS)
    a = ap.parse_args()
    days = a.days or sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(a.ds, "*.npz"))})
    res = run(days, a.ds)
    write_atomic(a.out, res)
    for k, v in res["pooled"].items():
        if k.endswith("|900"):
            print(k, " | ".join(f"{nm} mae {x['mae_pct']:.2f} bias {x['bias_pct']:+.2f}" for nm, x in v.items()))
    print("PR-004", "PASSED" if res["pr004"]["passed"] else "NOT PASSED", "; ".join(res["pr004"]["why"]))
    print("IV noise (vol points, 5/15/30 min):", res["iv_sd"])
    print(f"written {a.out} in {res['secs']} s")


if __name__ == "__main__":
    main()
