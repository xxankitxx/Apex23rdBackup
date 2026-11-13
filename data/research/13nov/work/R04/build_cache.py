import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04: one compact cache of the trade table for the weather search (numpy only afterwards).
Reads only the base trade fields and every wx_ column; writes cache.npz + cache_meta.json in this folder."""
import json, os, time
t0 = time.time()
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
HERE = os.path.dirname(os.path.abspath(__file__))
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
TELEMETRY = {"eng_p50_ms", "eng_p95_ms", "eng_max_ms", "eng_over300_n", "save_lag_n", "save_pending_s",
             "save_last_ms", "save_ok_age_s", "save_errors_n", "save_fails_row_n", "lin_schema", "lin_rule_hash",
             "lin_art_cutoff", "v"}
BASE_NUM = ["ret_pct", "pnl_rs", "t_in", "t_out", "trigger_t", "entry", "exit", "hold_s", "dir", "peak_pts",
            "worst_pts", "delta_in", "iv_in", "dte_in", "capital_after", "strike"]
BASE_STR = ["day", "book", "rr", "reason", "why", "ep_type", "time_in", "time_out", "trigger_time", "key"]
sch = pq.ParquetFile(P).schema_arrow
wx = [n for n in sch.names if n.startswith("wx_") and n[3:] not in TELEMETRY]
cols = BASE_STR + BASE_NUM + wx
tb = pq.read_table(P, columns=cols)
print("read", round(time.time() - t0, 1), tb.num_rows, len(cols), flush=True)


def num(name):
    c = tb.column(name)
    if pa.types.is_string(c.type) or pa.types.is_large_string(c.type):
        return None
    return pc.cast(c, pa.float64()).to_numpy(zero_copy_only=False).astype(np.float64)


base = {}
for n in BASE_NUM:
    base[n] = num(n)
strs = {n: [("" if v is None else str(v)) for v in tb.column(n).to_pylist()] for n in BASE_STR}
names, kinds, mats, items = [], [], [], []
for n in wx:
    k = n[3:]
    c = tb.column(n)
    if pa.types.is_string(c.type) or pa.types.is_large_string(c.type):
        vals = c.to_pylist()
        cats = {}
        for v in vals:
            if v is not None:
                cats[v] = cats.get(v, 0) + 1
        for cv, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            if cnt < 30 or len(cats) > 40:
                continue
            a = np.array([np.nan if v is None else float(v == cv) for v in vals])
            names.append(f"{k}={cv}"); kinds.append("ind"); mats.append(a)
        continue
    a = num(n)
    kinds.append("ind" if pa.types.is_boolean(c.type) else "num")
    names.append(k); mats.append(a)
X = np.column_stack(mats).astype(np.float32)
np.savez(os.path.join(HERE, "cache.npz"), X=X, **{"b_" + k: v for k, v in base.items()})
json.dump({"names": names, "kinds": kinds, "strs": strs}, open(os.path.join(HERE, "cache_meta.json"), "w"))
print("done", round(time.time() - t0, 1), X.shape, flush=True)
