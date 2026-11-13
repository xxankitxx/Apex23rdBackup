import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 phase B: more beam-null permutations for the big groups (13 Nov had 0-16). One group per run, about 3 min:
    py -3.13 phaseB_beam_null.py fam:t28      (also fam:spot_dc12, fam:c20, pool_trades)
Writes out_s3_<group>.json (overwrites the 13 Nov file for that group with the larger null)."""
import os, runpy
here = os.path.dirname(os.path.abspath(__file__))
grp = sys.argv[1] if len(sys.argv) > 1 else "fam:c20"
sys.argv = [os.path.join(here, "s3_beam.py"), grp, "160", "8"]
runpy.run_path(sys.argv[0], run_name="__main__")
