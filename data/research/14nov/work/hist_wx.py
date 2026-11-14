"""A year of the CAPTURED-DATA inputs from broker history, 1-minute bars (one call per contract per session):
the 14 heavyweights (cash), the BANKNIFTY and FINNIFTY near futures, and the weekly option chain (ATM at the open
+- 6 strikes, calls and puts: price, volume, OPEN INTEREST). Read-only, paced, resumable; one parquet per session in
data/research/hist_wx/. Logs in the way the feed does (nothing from the secrets folder is printed).

    py -3.13 hist_wx.py [--max-calls N] <day> [more days]
"""
import os, sys, json, time, datetime as dt
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import numpy as np, pandas as pd
import hist1s

OUT = r"D:\ApexOptions\data\research\hist_wx"
HW = {"HDFCBANK": "HDFBAN", "ICICIBANK": "ICIBAN", "RELIANCE": "RELIND", "BHARTIARTL": "BHAAIR", "LT": "LARTOU", "SBIN": "STABAN", "AXISBANK": "AXIBAN",
      "INFY": "INFTEC", "KOTAKBANK": "KOTMAH", "M&M": "MAHMAH", "TCS": "TCS", "ITC": "ITC", "BAJFINANCE": "BAJFI", "HINDUNILVR": "HINLEV"}
SIS = {"BANKNIFTY": "CNXBAN", "FINNIFTY": "NIFFIN"}
NK = 6
PACE_S = 0.35
CALLS = {"n": 0}


def _call(bz, **kw):
    time.sleep(PACE_S)
    CALLS["n"] += 1
    hist1s._note_calls()
    for attempt in (1, 2, 3):
        try:
            r = bz.get_historical_data_v2(interval="1minute", **kw)
        except Exception as e:
            r = {"Success": None, "Error": f"{type(e).__name__}: {e}"}
        err = str((r or {}).get("Error") or "").lower()
        if any(k in err for k in ("session", "authenticat", "unauthor")):
            raise RuntimeError("the broker refused the session: " + err[:120])
        if "limit" in err:
            raise RuntimeError("the broker says the call limit is reached: " + err[:120])
        if (r or {}).get("Success") is not None or not err:
            return (r or {}).get("Success") or []
        time.sleep(2.0 * attempt)
    return []


def _frame(rows, tag):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    cols = [c for c in ("datetime", "open", "high", "low", "close", "volume", "open_interest") if c in df]
    df = df[cols].copy()
    for c in cols[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["what"] = tag
    return df


def session(day, fut_exp, opt_exp, atm, max_calls=10 ** 9):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{day}.parquet")
    if os.path.exists(path):
        return "have"
    bz = hist1s.session()
    f0, f1 = f"{day}T09:15:00.000Z", f"{day}T15:30:00.000Z"
    parts = []
    jobs = [("eq:" + s, dict(stock_code=c, exchange_code="NSE", product_type="cash")) for s, c in HW.items()]
    jobs += [("fut:" + s, dict(stock_code=c, exchange_code="NFO", product_type="futures", expiry_date=fut_exp + "T07:00:00.000Z")) for s, c in SIS.items()]
    for k in range(-NK, NK + 1):
        K = int(atm + 50 * k)
        for right in ("call", "put"):
            jobs.append((f"opt:{K}:{right}", dict(stock_code="NIFTY", exchange_code="NFO", product_type="options", expiry_date=opt_exp + "T07:00:00.000Z", right=right, strike_price=str(K))))
    if CALLS["n"] + len(jobs) > max_calls:
        return None
    for tag, kw in jobs:
        df = _frame(_call(bz, from_date=f0, to_date=f1, **kw), tag)
        if df is not None:
            parts.append(df)
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["datetime", "what"])
    out.to_parquet(path + ".tmp"); os.replace(path + ".tmp", path)
    return len(jobs)


if __name__ == "__main__":
    a = sys.argv[1:]
    mc = 10 ** 9
    if a and a[0] == "--max-calls":
        mc = int(a[1]); a = a[2:]
    import h4, pickle
    meta = {d["day"]: d for d in pickle.load(open(h4.PKL, "rb"))}
    futexp = json.load(open(os.path.join(hist1s.OUT, "fut_expiry.json")))
    for day in a:
        m = meta.get(day)
        if m is None:
            print(day, "not in the session list"); continue
        F = m["c"][0] - m["basis"]
        atm = int(round(F / 50.0) * 50)
        try:
            r = session(day, futexp[day], m["expiry"], atm, mc)
        except RuntimeError as e:
            print("stopped:", e); break
        print(day, "expiry", m["expiry"], "atm", atm, "->", r, "calls", CALLS["n"], flush=True)
        if r is None:
            print("call cap reached"); break
