"""Turn the fetched 5-minute / 15-minute history into one panel per interval (IST, one row per bar)."""
import glob, json, os
import numpy as np, pandas as pd
SRC = r"C:\Users\Ankit Madhogaria\.claude\projects\D--ApexOptions\4fc710fd-915d-4b6c-be6c-118168a8b13b\tool-results"
OUT = r"D:\ApexOptions\data\research\14nov\work\tv"
os.makedirs(OUT, exist_ok=True)
got = {}
for p in sorted(glob.glob(os.path.join(SRC, "mcp-*-mcp-tv-get-ohlcv-*.txt"))):
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print("unreadable", os.path.basename(p), e); continue
    b = j.get("bars")
    if not isinstance(b, dict) or "t" not in b:
        continue
    sym = (j.get("symbol") or j.get("description") or "?").replace("NSE:", "").replace("!", "")
    iv = j.get("interval")
    df = pd.DataFrame({k: b[k] for k in ("t", "o", "h", "l", "c", "v")})
    df["ts"] = pd.to_datetime(df.t + 19800, unit="s")
    got[(sym, iv)] = df
    print(f"{sym:12} {iv:4} bars {len(df):5} {df.ts.iloc[0]} .. {df.ts.iloc[-1]}  days {df.ts.dt.date.nunique()}")
for iv in sorted({k[1] for k in got}):
    cols = {}
    for (sym, i2), df in got.items():
        if i2 != iv:
            continue
        d = df.set_index("ts")
        for k in ("o", "h", "l", "c", "v"):
            cols[f"{sym}_{k}"] = d[k]
    P = pd.DataFrame(cols).sort_index()
    P.to_parquet(os.path.join(OUT, f"panel_{iv}.parquet"))
    print(iv, "panel", P.shape, "symbols", sorted({c.rsplit('_', 1)[0] for c in P.columns}))
