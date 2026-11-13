import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import re, json
lab = []
for ln in open(r"D:\ApexOptions\data\forecast_lab\log_2026-11-13.txt", encoding="utf-8"):
    m = re.match(r"(\d\d:\d\d):\d\d status: loop p50 ([\d.]+) ms p95 ([\d.]+) ms.*?skipped (\d+) s; stale (\d+) s.*?write fails (\d+)", ln)
    if m: lab.append((m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6))))
perf = [json.loads(l) for l in open(r"D:\ApexOptions\data\logs\perf_2026-11-13.jsonl")]
print("window_end lab_p50 lab_p95 skipped+ writefail+ | eng_ticks/min eng_mean_ms eng_p95_med")
prev = (None, 0, 0, 0, 0, 0); pend = "09:00"
for row in lab:
    sel = [r for r in perf if pend <= r["mkt"] < row[0]]
    if sel:
        tpm = sum(r["n"] for r in sel) / len(sel); mean = sum(r["sum_ms"] for r in sel) / max(1, sum(r["n"] for r in sel))
        p95 = sorted(r["p95"] for r in sel)[len(sel)//2]
    else: tpm = mean = p95 = float("nan")
    print(f"{pend}-{row[0]}  {row[1]:7.1f} {row[2]:8.1f} {row[3]-prev[3]:5d} {row[5]-prev[5]:5d} | {tpm:6.0f} {mean:7.1f} {p95:7.1f}")
    prev = row; pend = row[0]
