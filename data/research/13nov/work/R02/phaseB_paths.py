"""PHASE B (after the 15:30 close only). R02 per-second exit variants on every built ds_v2 part, 20 trades per run.
Usage (one run at a time, each well under 3 minutes on an idle machine):
    py -3.13 phaseB_paths.py <part> <chunk>        e.g.  py -3.13 phaseB_paths.py 2026-10-27.p2 0
Writes a4_B_<part>_<chunk>.json. phaseB_list.txt holds every (part, chunk) command; then run phaseB_merge.py."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import os, runpy
W = r"D:\ApexOptions\data\research\13nov\work\R02"
part, chunk = sys.argv[1], int(sys.argv[2])
os.environ["R02_CHUNK"] = f"{chunk}:20"
os.environ["R02_TAG"] = f"B_{part}_{chunk}"
sys.argv = [W + r"\a4_paths.py", part]
runpy.run_path(W + r"\a4_paths.py", run_name="__main__")
