"""13 Nov: one flat table of every book's trade on the 17 replayed days (p44, current code, pool as of all), with the
457-field weather photograph at the trigger (wx_*) and the hold marks (h<mark>_*). Read-only on the replay folders."""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowprio  # noqa
import pandas as pd
B = r"D:\ApexOptions\data\replay\batch"
SRC = {  # day -> run folder (the four days that died in g4-g6 come from their clean reruns r1-r4)
    "2026-10-19": "p44_g1", "2026-10-21": "p44_g1", "2026-10-22": "p44_g2", "2026-10-23": "p44_g2",
    "2026-10-26": "p44_g3", "2026-10-27": "p44_g3", "2026-10-28": "p44_r1", "2026-10-29": "p44_g4",
    "2026-10-30": "p44_r2", "2026-11-02": "p44_r3", "2026-11-03": "p44_r4", "2026-11-04": "p44_g6",
    "2026-11-05": "p44_g7", "2026-11-06": "p44_g7", "2026-11-09": "p44_g8", "2026-11-11": "p44_g8",
    "2026-11-12": "p44_g9"}
SKIP = {"slices", "advisors", "trail", "weather_hold", "weather_trig", "last", "best", "signal_trig", "edge_trig"}
rows = []
for day, run in SRC.items():
    p = os.path.join(B, run, "paper", f"{day}.json")
    d = json.load(open(p, encoding="utf-8"))
    for name, b in d.items():
        if not isinstance(b, dict):
            continue
        for t in b.get("trades") or []:
            r = {"day": day, "book": name}
            for k, v in t.items():
                if k in SKIP:
                    continue
                if isinstance(v, (int, float, str, bool)) or v is None:
                    r[k] = v
            for k, v in (t.get("weather_trig") or {}).items():
                if isinstance(v, (int, float, bool)) or v is None:
                    r["wx_" + k] = v
                elif isinstance(v, str) and len(v) < 40:
                    r["wx_" + k] = v
            for m in (t.get("weather_hold") or []):
                mk = m.get("mark")
                for k, v in m.items():
                    if k != "mark" and (isinstance(v, (int, float, bool)) or v is None):
                        r[f"h{mk}_{k}"] = v
            rows.append(r)
df = pd.DataFrame(rows)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades_all_books.parquet")
df.to_parquet(out)
print(len(df), "trades,", df["book"].nunique(), "books,", df.shape[1], "columns ->", out)
print(df.groupby("day").size().to_string())
