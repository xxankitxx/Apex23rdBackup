"""1-second broker history (ICICI Breeze get_historical_data_v2, interval "1second"): read-only, paced, resumable.
One parquet per (kind, contract, session) under data/research/hist1s/. Logs in the way the feed does; nothing from the
secrets folder is printed. The paper-only interlock is installed. Counts its calls in data/research/hist1s/calls.json.

    py -3.13 hist1s.py fut 2026-11-06 [more days]            the near-month future, whole session
    py -3.13 hist1s.py --max-calls 1200 fut <days...>        stop after that many broker calls
"""
import os, sys, time, json, datetime as dt
sys.path.insert(0, r"D:\ApexOptions")
import numpy as np, pandas as pd

OUT = r"D:\ApexOptions\data\research\hist1s"
PACE_S = 0.8                                  # at most 75 calls a minute (the broker allows 100)
WIN_S = 900                                   # seconds per call (the broker caps a reply at 1000 rows)
_BZ = None
CALLS = {"n": 0}


def session():
    global _BZ
    if _BZ is not None:
        return _BZ
    from apex import feed_breeze as fb
    try:
        from apex import interlock
    except ImportError:
        interlock = None
    fb.install_trust()
    from breeze_connect import BreezeConnect
    c = fb.load_credentials("")
    bz = BreezeConnect(api_key=c["api_key"])
    if interlock:
        interlock.install(bz); interlock.patch_requests()
    bz.generate_session(api_secret=c["api_secret"], session_token=c["session_token"])
    del c
    _BZ = bz
    return bz


def _note_calls(n=1):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "calls.json")
    today = dt.date.today().isoformat()
    try:
        d = json.load(open(p))
    except Exception:
        d = {}
    d[today] = int(d.get(today, 0)) + n
    json.dump(d, open(p, "w"))
    CALLS["n"] += n
    return d[today]


def fetch(day, product, expiry, right="", strike="", max_calls=10 ** 9, t0="09:15:00", t1="15:30:00", path=None):
    """the whole session of one contract, second by second. Returns a DataFrame (may be empty) or None when the call
    budget ran out before the session was complete (nothing is saved then)."""
    os.makedirs(OUT, exist_ok=True)
    name = f"{product[:3]}_{expiry}_{right or 'x'}_{strike or 0}_{day}.parquet"
    path = path or os.path.join(OUT, name)
    if os.path.exists(path):
        return pd.read_parquet(path)
    bz = session()
    a = dt.datetime.fromisoformat(f"{day}T{t0}"); end = dt.datetime.fromisoformat(f"{day}T{t1}")
    parts = []
    last = None
    while a < end:
        b = min(a + dt.timedelta(seconds=WIN_S - 1), end)
        if CALLS["n"] >= max_calls:
            return None
        if last is not None:
            w = PACE_S - (time.monotonic() - last)
            if w > 0:
                time.sleep(w)
        last = time.monotonic()
        _note_calls()
        r = None
        for attempt in (1, 2, 3):
            try:
                r = bz.get_historical_data_v2(interval="1second", from_date=a.strftime("%Y-%m-%dT%H:%M:%S.000Z"), to_date=b.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                              stock_code="NIFTY", exchange_code="NFO", product_type=product, expiry_date=expiry + "T07:00:00.000Z",
                                              right=right, strike_price=str(strike) if strike != "" else "")
            except Exception as e:
                r = {"Success": None, "Error": f"{type(e).__name__}: {e}"}
            err = str((r or {}).get("Error") or "").lower()
            if any(k in err for k in ("session", "authenticat", "unauthor")):
                raise RuntimeError("the broker refused the session: " + err[:120])
            if "limit" in err:
                raise RuntimeError("the broker says the call limit is reached: " + err[:120])
            if (r or {}).get("Success") is not None or not err:
                break
            time.sleep(2.0 * attempt)
        rows = (r or {}).get("Success") or []
        if rows:
            parts.append(pd.DataFrame(rows)[["datetime", "open", "high", "low", "close", "volume", "open_interest"]] if "volume" in rows[0]
                         else pd.DataFrame(rows)[["datetime", "open", "high", "low", "close", "open_interest"]])
        a = b + dt.timedelta(seconds=1)
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["datetime", "open", "high", "low", "close"])
    for k in ("open", "high", "low", "close", "volume", "open_interest"):
        if k in df:
            df[k] = pd.to_numeric(df[k], errors="coerce")
    df = df.drop_duplicates("datetime").sort_values("datetime").reset_index(drop=True)
    df.to_parquet(path)
    return df


def grid(df, day, col="close"):
    """a per-second array 09:15:00 .. 15:30:00 (22,501 rows), forward-filled from the last traded second."""
    N = 22501
    out = np.full(N, np.nan)
    if df is None or not len(df):
        return out
    t = pd.to_datetime(df.datetime)
    i = ((t - pd.Timestamp(day + " 09:15:00")).dt.total_seconds()).to_numpy().astype(int)
    ok = (i >= 0) & (i < N)
    out[i[ok]] = df[col].to_numpy(float)[ok]
    idx = np.where(np.isfinite(out), np.arange(N), 0)
    np.maximum.accumulate(idx, out=idx)
    f = out[idx]
    f[~np.maximum.accumulate(np.isfinite(out))] = np.nan
    return f


if __name__ == "__main__":
    a = sys.argv[1:]
    mc = 10 ** 9
    if a and a[0] == "--max-calls":
        mc = int(a[1]); a = a[2:]
    kind, days = a[0], a[1:]
    FUTEXP = json.load(open(os.path.join(OUT, "fut_expiry.json"))) if os.path.exists(os.path.join(OUT, "fut_expiry.json")) else {}
    for d in days:
        if kind == "fut":
            e = FUTEXP.get(d)
            if not e:
                print(d, "no future expiry known"); continue
            df = fetch(d, "futures", e, max_calls=mc)
            print(d, "future", e, "rows", None if df is None else len(df), "calls so far", CALLS["n"], flush=True)
            if df is None:
                break


def fetch_window(day, expiry, right, strike, i0, i1):
    """seconds i0..i1 of the session (rows since 09:15:00) of one option contract; cached per window. One call per
    15 minutes asked. Returns the per-second close on the full session grid (NaN outside the window), or None."""
    os.makedirs(os.path.join(OUT, "opt"), exist_ok=True)
    path = os.path.join(OUT, "opt", f"{expiry}_{right}_{int(strike)}_{day}_{i0}_{i1}.parquet")
    base = dt.datetime.fromisoformat(f"{day}T09:15:00")
    t0 = (base + dt.timedelta(seconds=int(i0))).strftime("%H:%M:%S")
    t1 = (base + dt.timedelta(seconds=int(i1))).strftime("%H:%M:%S")
    df = fetch(day, "options", expiry, right, int(strike), t0=t0, t1=t1, path=path)
    if df is None:
        return None
    return grid_window(df, day, i0, i1)


def grid_window(df, day, i0, i1):
    N = 22501
    out = np.full(N, np.nan)
    if df is None or not len(df):
        return out
    t = pd.to_datetime(df.datetime)
    i = ((t - pd.Timestamp(day + " 09:15:00")).dt.total_seconds()).to_numpy().astype(int)
    ok = (i >= i0) & (i <= i1) & (i < N)
    out[i[ok]] = df["close"].to_numpy(float)[ok]
    seg = out[i0:i1 + 1]
    idx = np.where(np.isfinite(seg), np.arange(len(seg)), 0)
    np.maximum.accumulate(idx, out=idx)
    f = seg[idx]; f[~np.maximum.accumulate(np.isfinite(seg))] = np.nan
    out[i0:i1 + 1] = f
    return out
