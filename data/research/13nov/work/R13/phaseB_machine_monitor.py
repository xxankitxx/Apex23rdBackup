import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (needs the owner's OK: it runs for a whole session). A tiny read-only monitor: every 10 s it appends one
line to work/R13/machine_<day>.csv with total CPU %, the cores' performance % (clock against rated), free memory, and
the engine's last tick-time line. Lets the owner see whether slow ticks follow heat throttling or other jobs.
    py -3.13 phaseB_machine_monitor.py            (stops at 15:35 IST; Ctrl+C any time)
Uses typeperf (built into Windows). No process is started except typeperf itself, one sample at a time."""
import subprocess, time, csv, os
from datetime import datetime, timedelta, timezone
IST = timezone(timedelta(hours=5, minutes=30))
C = [r"\Processor(_Total)\% Processor Time", r"\Processor Information(_Total)\% Processor Performance",
     r"\Memory\Available MBytes"]
day = datetime.now(IST).date().isoformat()
out = fr"D:\ApexOptions\data\research\13nov\work\R13\machine_{day}.csv"
def last_tick_line():
    try:
        with open(r"D:\ApexOptions\data\logs\engine.log", "rb") as f:
            f.seek(max(0, os.path.getsize(r"D:\ApexOptions\data\logs\engine.log") - 4000))
            lines = [l for l in f.read().decode("utf-8", "replace").splitlines() if "tick time last minute" in l]
        return lines[-1][:160] if lines else ""
    except OSError:
        return ""
while datetime.now(IST).strftime("%H:%M") < "15:35":
    r = subprocess.run(["typeperf"] + C + ["-sc", "1"], capture_output=True, text=True, timeout=20).stdout.splitlines()
    vals = r[2].split(",")[1:] if len(r) > 2 else []
    with open(out, "a", newline="") as f:
        csv.writer(f).writerow([datetime.now(IST).strftime("%H:%M:%S")] + [v.strip('"') for v in vals] + [last_tick_line()])
    time.sleep(10)
