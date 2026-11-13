"""R06 phase B (run after the 15:30 close, alone, same rules): reprice every Conductor and pool-book trade on every day
that has ds_v2 quotes (16 days, 12 Nov is not built), one day at a time, then aggregate.
    py -3.13 phaseB_reprice_all.py
Writes reprice_<mm-dd>.csv, clock_<mm-dd>.csv, ivpath_<mm-dd>.csv per day in this folder, then runs a4_aggregate.py
over all of them (stdout -> phaseB_reprice_all.txt). Each day is a separate a3 run (about 20 s of CPU on an idle
machine); the loop is sequential, no multiprocessing."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import os, runpy, contextlib, io
W = r"D:\ApexOptions\data\research\13nov\work\R06"
DAYS = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
        "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11"]
for d in DAYS:
    if os.path.exists(W + f"\\reprice_{d[5:]}.csv") and os.path.exists(W + f"\\clock_{d[5:]}.csv"):
        print("have", d)
        continue
    sys.argv = ["a3_reprice.py", d]
    runpy.run_path(W + r"\a3_reprice.py", run_name="__main__")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    sys.argv = ["a4_aggregate.py"] + [d[5:] for d in DAYS]
    runpy.run_path(W + r"\a4_aggregate.py", run_name="__main__")
open(W + r"\phaseB_reprice_all.txt", "w", encoding="utf-8").write(buf.getvalue())
print(buf.getvalue())
