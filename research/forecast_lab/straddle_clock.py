"""Nightly monitor of the decay clock (PKG-08, 12 Nov 2026; the council's L10 straddle test).

For each recorded session: the at-the-money straddle at a FIXED strike (the one nearest the parity forward at 10:00),
in 1-minute steps from 10:00 to 14:30. Each step's change, net of its delta (Delta dF) and its gamma (0.5 Gamma dF^2),
is the decay plus the IV change. Summed over the window and divided by the calendar-clock decay at constant IV over
the same minutes, it gives the realised decay factor. The business clock (apex/forecast_lab/clock.py) predicts that
factor as k_ts: exactly 1 on expiry day, about 2.5 the day before, about 5 to 6 midweek. The old Lab clock said 3.84
every day.

Acceptance (with the repricing scorecard, before PKG-08 Stage B ships): the factor falls in 0.5 to 1.1 on every
expiry day. The factor on other days is noisy (IV moves dominate a single day), so it is reported, not judged.

Output: data/forecast_lab/straddle_clock.json (atomic), one entry per session part, with the day's DTE bucket, the
realised factor, the business clock's mean k over the same minutes, the gamma P&L and the net decay.

Run (owner's OK first; a few minutes for the 16 recorded sessions on an idle machine, one process):
    py -3.13 research/forecast_lab/straddle_clock.py [--days ...] [--out path.json]
Read-only on the tapes (data/research/ds_v2)."""
import argparse
import glob
import json
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
OUT = os.path.join(config.DATA_DIR, "forecast_lab", "straddle_clock.json")
START_S, END_S = 10 * 3600, 14 * 3600 + 30 * 60
STEP = 60
EXPIRY_BAND = (0.5, 1.1)


def sod(t):
    return (int(t) + 19800) % 86400


def straddle(F, K, T, s):
    c = float(b76(F, K, T, s, True))
    p = float(b76(F, K, T, s, False))
    g = b76_greeks(F, np.array([K]), T, s, np.array([True]))
    return c + p, 2.0 * float(g["delta"][0]) - 1.0, 2.0 * float(g["gamma"][0])


def straddle_iv(S, F, K, T):
    """The straddle's own IV: the call's IV from parity (the straddle is 2C - (F - K))."""
    c = 0.5 * (S + F - K)
    v = iv_newton(np.array([c]), F, np.array([K]), T, np.array([True]))
    return float(v[0])


def part_factor(path):
    """dict for one tape part, or None when it has too few clean minutes."""
    z = np.load(path)
    if z["t"].ndim != 1 or len(z["t"]) == 0:
        return None
    t = z["t"].astype(float)
    n = len(z["strikes"])
    K = z["strikes"].astype(float)
    exp = str(z["expiry"])
    o = z["opt"][:, :n].astype(float)
    age = z["age"][:, :n].astype(float)
    mid = np.where((o[..., 0] > 0) & (o[..., 1] >= o[..., 0]) & (age <= 3), 0.5 * (o[..., 0] + o[..., 1]), np.nan)
    s = (t.astype(int) + 19800) % 86400
    inwin = np.where((s >= START_S) & (s < END_S))[0]
    if len(inwin) < 600:
        return None
    i0 = int(inwin[0])
    fs = K + mid[i0, :, 0] - mid[i0, :, 1]
    if not np.isfinite(fs).any():
        return None
    j = int(np.nanargmin(np.abs(K - np.nanmedian(fs[np.isfinite(fs)]))))
    res = th = gp = 0.0
    ks, steps = [], 0
    prev = None
    last = -1e9
    for i in inwin:
        if t[i] - last < STEP - 0.5:
            continue
        last = t[i]
        c, p = mid[i, j]
        if not (np.isfinite(c) and np.isfinite(p)):
            prev = None
            continue
        F, S = K[j] + c - p, c + p
        now = datetime.fromtimestamp(float(t[i]), config.IST)
        T = greeks.years_to_expiry(exp, now)
        sig = straddle_iv(S, F, K[j], T)
        if not np.isfinite(sig):
            prev = None
            continue
        if prev is not None and abs(t[i] - prev[0] - STEP) < 3:
            _, F0, S0, T0, s0, dl0, g0, k0 = prev
            dF = F - F0
            th += straddle(F0, K[j], max(T0 - STEP / SPY, 1e-9), s0)[0] - straddle(F0, K[j], T0, s0)[0]
            gp += 0.5 * g0 * dF * dF
            res += (S - S0) - dl0 * dF - 0.5 * g0 * dF * dF
            if k0 is not None:
                ks.append(k0)
            steps += 1
        _, dl, g = straddle(F, K[j], T, sig)
        k, _, _ = CK.k_ts(now, exp, T)
        prev = (t[i], F, S, T, sig, dl, g, k)
    if steps < 60 or th >= 0:
        return None
    day = datetime.fromtimestamp(float(t[i0]), config.IST).date()
    dte = (datetime.fromisoformat(exp).date() - day).days
    return dict(part=os.path.basename(path), day=day.isoformat(), expiry=exp, dte=dte,
                bucket="exp" if dte == 0 else ("1-2" if dte <= 2 else "3+"), strike=float(K[j]), minutes=steps,
                factor=round(res / th, 3), k_mean=round(float(np.mean(ks)), 3) if ks else None,
                gamma_pnl=round(gp, 2), net_decay=round(res, 2), calendar_decay=round(th, 2))


def judge(rows):
    """(ok, why): every expiry-day factor in EXPIRY_BAND."""
    ex = [r for r in rows if r["bucket"] == "exp"]
    bad = [r for r in ex if not (EXPIRY_BAND[0] <= r["factor"] <= EXPIRY_BAND[1])]
    if not ex:
        return False, "no expiry-day parts"
    return not bad, (f"expiry-day factors {', '.join(f'{r['day']} {r['factor']:.2f}' for r in ex)}"
                     f" (needs {EXPIRY_BAND[0]} to {EXPIRY_BAND[1]})")


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def run(days, ds=DS, log=print):
    rows, t0 = [], time.time()
    for day in days:
        for p in sorted(glob.glob(os.path.join(ds, f"{day}*.npz"))):
            try:
                r = part_factor(p)
            except (OSError, KeyError, ValueError) as e:
                log(f"{os.path.basename(p)}: not read ({type(e).__name__}: {e})")
                continue
            if r is None:
                log(f"{os.path.basename(p)}: too few clean minutes")
                continue
            rows.append(r)
            log(f"{r['part']} {r['bucket']} factor {r['factor']:+.2f} business k {r['k_mean']} [{time.time() - t0:.0f}s]")
    ok, why = judge(rows)
    return dict(built=datetime.now(config.IST).isoformat(timespec="seconds"), rows=rows, expiry_ok=ok, why=why,
                secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", nargs="*")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--ds", default=DS)
    a = ap.parse_args()
    days = a.days or sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(a.ds, "*.npz"))})
    res = run(days, a.ds)
    write_atomic(a.out, res)
    print(("PASSED: " if res["expiry_ok"] else "NOT PASSED: ") + res["why"])
    print(f"written {a.out} in {res['secs']} s")


if __name__ == "__main__":
    main()
