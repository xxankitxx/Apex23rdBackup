import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (run after the 15:30 close, nothing else heavy running): build the per-second sister panel for every
recorded tape part, one part at a time, by calling sister_extract.py in sequence (never in parallel).
Skips parts already built, tapes under 1 MB (empty pre-open stubs) and today's tape (still being written).
Each part takes 1-4 minutes on a quiet machine (16 s per 50 MB on a loaded one); the whole set is about 3.7 GB of gzip.
Usage: py -3.13 phaseB_sister_extract_all.py"""
import datetime, glob, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
TICKS = r"D:\ApexOptions\data\ticks"
today = datetime.date.today().isoformat()
for p in sorted(glob.glob(os.path.join(TICKS, "2026-*.jsonl.gz"))):
    part = os.path.basename(p)[:-len(".jsonl.gz")]
    if part.startswith(today) or os.path.getsize(p) < 1_000_000:
        continue
    if os.path.exists(os.path.join(HERE, "sister", part + ".npz")):
        continue
    print("building", part, flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, "sister_extract.py"), part, "100000"], check=False)
