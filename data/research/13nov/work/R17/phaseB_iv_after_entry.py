import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R17 phase B (run after the 15:30 close; one day part at a time; well under 3 min and 1.5 GB per part).

Question: the Conductor's losers have IV falling after entry (iv_out - iv_in < 0 in most losers, > +0.3 vol pts in 76-93 % of
winners). The c20 pool books record NO hold marks (h60/h300 are empty for every c20 book in trades_all_books.parquet,
because council exits do not pass through paper.check_exit where weather5.hold_tick runs). So this script rebuilds the
first 5 minutes of every c20 pool trade from the per-second tape (data/research/ds_v2) and tests a yes/no early exit:

    at mark M seconds (60, 120, 180, 300): exit at the bid when
        (ATM-contract implied vol now - IV at entry) < IV_TH   and   bid gain since entry < G_TH

Black-76 IV from the mid of the held contract, forward = futures mid, T = time to 15:30 IST on the expiry date.
Discovery days 19 Oct to 4 Nov, test days 5 Nov to 11 Nov (12 Nov has no ds_v2 part). The account is re-simulated with
the R17 simulator (sim.py, same walk as apex/conductor/account_sim.py) so an earlier exit frees the account earlier.
Output: work/R17/phaseB_iv_after_entry.json and a printed table. Read-only on every input.

    py -3.13 D:\\ApexOptions\\data\\research\\13nov\\work\\R17\\phaseB_iv_after_entry.py [DAY ...]
"""
import os, json, glob, math
from datetime import datetime, timedelta, timezone
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402

DS = r"D:\ApexOptions\data\research\ds_v2"
IST = timezone(timedelta(hours=5, minutes=30))
MARKS = (60, 120, 180, 300)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phaseB_iv_after_entry.json")


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def b76(F, K, T, v, cp):
    if T <= 0 or v <= 0:
        return max(0.0, (F - K) if cp == "CE" else (K - F))
    s = v * math.sqrt(T); d1 = (math.log(F / K) + 0.5 * s * s) / s; d2 = d1 - s
    return F * _ncdf(d1) - K * _ncdf(d2) if cp == "CE" else K * _ncdf(-d2) - F * _ncdf(-d1)


def iv(px, F, K, T, cp):
    lo, hi = 0.01, 3.0
    if not (px > 0 and F > 0 and T > 0):
        return None
    if px <= b76(F, K, T, lo, cp) or px >= b76(F, K, T, hi, cp):
        return None
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if b76(F, K, T, m, cp) > px:
            hi = m
        else:
            lo = m
    return 100.0 * 0.5 * (lo + hi)


def t_exp(t, expiry):
    e = datetime.strptime(expiry, "%Y-%m-%d").replace(hour=15, minute=30, tzinfo=IST).timestamp()
    return max(1.0, e - t) / (365.0 * 86400.0)


def marks_for_day(day, rows):
    """rows: trades of one day (pool books). Returns {index: {M: (bid_gain_pct, iv_chg)}}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(DS, f"{day}*.npz"))):
        z = np.load(p)
        t = z["t"]
        if len(t) == 0:
            continue
        strikes = list(z["strikes"]); exp = str(z["expiry"])
        opt, fut = z["opt"], z["fut"]
        for i, r in rows.iterrows():
            if i in out or not (t[0] <= r.t_in <= t[-1]):
                continue
            if str(r.expiry)[:10] != exp or float(r.strike) not in strikes:
                continue                                   # next-weekly contracts would need opt2; skipped and counted
            k = strikes.index(float(r.strike)); c = 0 if r.rr == "CE" else 1
            j0 = int(np.searchsorted(t, r.t_in))
            if j0 >= len(t):
                continue
            def at(j):
                bid, ask = float(opt[j, k, c, 0]), float(opt[j, k, c, 1])
                F = 0.5 * (float(fut[j, 0]) + float(fut[j, 1]))
                mid = 0.5 * (bid + ask) if bid > 0 and ask > 0 else None
                v = iv(mid, F, float(r.strike), t_exp(float(t[j]), exp), r.rr) if mid else None
                return bid, v
            _, v0 = at(j0)
            res = {}
            for M in MARKS:
                if r.t_out - r.t_in <= M + 1:
                    break
                j = int(np.searchsorted(t, r.t_in + M))
                if j >= len(t):
                    break
                bid, v = at(j)
                if bid > 0 and v is not None and v0 is not None:
                    res[M] = (100.0 * (bid / float(r.entry) - 1.0), v - v0)
            out[i] = res
        del z, opt, fut
    return out


def main(days=None):
    df = sim.load(slim=False)
    exp = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "t_in", "expiry"],
                          filters=[("book", "in", sim.ORDER)])
    df = df.merge(exp, on=["day", "book", "t_in"], how="left")
    days = days or sorted(d for d in df.day.unique() if d <= "2026-11-11")
    marks = {}
    only_marks = "--marks-only" in sys.argv
    for d in days:
        cp = os.path.join(os.path.dirname(OUT), f"phaseB_marks_{d}.json")
        if os.path.exists(cp):                       # cached from an earlier run (run one day per call to stay < 3 min)
            mk = {int(k): {int(m): tuple(v) for m, v in x.items()} for k, x in json.load(open(cp)).items()}
        else:
            mk = marks_for_day(d, df[df.day == d])
            json.dump({str(k): {str(m): v for m, v in x.items()} for k, x in mk.items()}, open(cp, "w"))
        marks.update(mk)
        print(d, "trades with marks:", sum(1 for i in marks if df.loc[i, "day"] == d), flush=True)
    if only_marks:
        return
    keep = ["day", "book", "rr", "entry", "exit", "trig", "t_in", "t_out", "ret_pct", "fut_in", "fut_out", "iv_in", "iv_out", "pri"]
    base = sim.sim(df[keep].copy())
    rows = []
    for M in MARKS:
        for th in (-1.0, -0.5, -0.25, 0.0):
            for g in (-8.0, -4.0, 0.0, 999.0):
                d2 = df[keep].copy()
                for i, mk in marks.items():
                    if M in mk and mk[M][1] < th and mk[M][0] < g:
                        d2.loc[i, "exit"] = d2.loc[i, "entry"] * (1 + mk[M][0] / 100.0)
                        d2.loc[i, "ret_pct"] = mk[M][0]; d2.loc[i, "t_out"] = d2.loc[i, "t_in"] + M
                r = sim.sim(d2)
                row = {"M": M, "iv_lt": th, "gain_lt": g}
                for name, ds in (("E", sim.EARLY), ("L", [x for x in sim.LATE if x in r])):
                    n = sum(r[x]["n"] for x in ds if x in r); w = sum(r[x]["w"] for x in ds if x in r)
                    row[name + "_tot"] = round(sum(r[x]["ret_day"] for x in ds if x in r), 1)
                    row[name + "_sr"] = round(100.0 * w / max(n, 1), 1)
                    row[name + "_ldays"] = sum(r[x]["ret_day"] < 0 for x in ds if x in r)
                    row[name + "_by_day"] = {x[5:]: round(r[x]["ret_day"] - base[x]["ret_day"], 1) for x in ds if x in r}
                rows.append(row)
    R = pd.DataFrame(rows)
    print(R.drop(columns=["E_by_day", "L_by_day"]).to_string())
    print("variants tried:", len(R), "(choose on E_* only; read L_* once)")
    json.dump({"rows": rows, "n_marked": len(marks)}, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")] or None)
