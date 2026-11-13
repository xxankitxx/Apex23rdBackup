import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05: one-off extract of the columns this study needs into a compact pickle (read-only on the inputs)."""
import json, os, time
import pyarrow as pa, pyarrow.parquet as pq
pa.set_cpu_count(1); pa.set_io_thread_count(1)
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
pf = pq.ParquetFile(P)
names = pf.schema_arrow.names
core = ["day", "book", "key", "strike", "rr", "expiry", "entry", "entry_bid", "entry_ask", "t_in", "time_in", "dir",
        "fut_in", "delta_in", "iv_in", "why", "ep_type", "peak_pts", "worst_pts", "regime", "dte_in", "trigger_t",
        "exit", "exit_bid", "exit_ask", "time_out", "t_out", "hold_s", "reason", "pnl_pts", "pnl_rs", "ret_pct",
        "fut_out", "iv_out", "delta_out", "ret_pct_mid", "peak_bid", "peak_t", "exit_fill_delay_s", "lots", "qty"]
hcols = [n for n in names if (n.startswith("h") and n.split("_")[0][1:].isdigit()) or n.startswith("hexit")]
# entry weather: every numeric/bool wx_ item (the search runs over all of them); strings dropped
sch = pf.schema_arrow
wx = []
for n in names:
    if n.startswith("wx_"):
        ty = str(sch.field(n).type)
        if ty.startswith(("double", "float", "int", "bool")):
            wx.append(n)
cols = [c for c in core if c in names] + hcols + wx
df = pq.read_table(P, columns=cols, use_threads=False).to_pandas()
for c in wx:
    if df[c].dtype == bool:
        df[c] = df[c].astype("float32")
    elif str(df[c].dtype) == "object":
        try:
            df[c] = df[c].astype("float32")          # bool with None -> 1/0/NaN
        except Exception:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if str(df[c].dtype).startswith("float64"):
        df[c] = df[c].astype("float32")
for c in hcols:
    if str(df[c].dtype) in ("object", "bool"):
        try:
            df[c] = df[c].astype("float64")
        except Exception:
            df[c] = pd.to_numeric(df[c], errors="coerce")
print("dtypes", df.dtypes.astype(str).value_counts().to_dict(), flush=True)
df.to_pickle(os.path.join(W, "tr.pkl"))
print("trades", df.shape, "wx numeric", len(wx), "h cols", len(hcols), round(time.time() - T0, 1), "s", flush=True)

# Conductor account trades (p44_sim except the four rerun days, which come from p44_simr)
RR = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
rows = []
for run, keep in (("p44_sim", lambda d: d not in RR), ("p44_simr", lambda d: d in RR)):
    d = json.load(open(os.path.join(r"D:\ApexOptions\data\replay\batch", run, "conductor_sim.json"), encoding="utf-8"))
    for day, rec in d["days"].items():
        if not keep(day):
            continue
        for k, t in enumerate(rec["trades"]):
            r = {kk: v for kk, v in t.items() if isinstance(v, (int, float, str)) or v is None}
            r["day"], r["seq"], r["run"] = day, k, run
            rows.append(r)
C = pd.DataFrame(rows)
C.to_pickle(os.path.join(W, "cond.pkl"))
print("conductor trades", C.shape, C.groupby("day").size().to_dict(), flush=True)
print("days total ret", C.groupby("day").apply(lambda g: g.capital_after.iloc[-1] / 1e5 * 100 - 100).round(1).to_dict())
print("done", round(time.time() - T0, 1), "s")
