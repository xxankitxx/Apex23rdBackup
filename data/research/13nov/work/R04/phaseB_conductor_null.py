import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 phase B (after 15:30 only): a bigger permutation null for the best single weather line at the EXACT Conductor
account (the 13 Nov run had only 7 permutations, p = 0.125). Each run lasts about 3 minutes and appends to
out_s2_null_accum.json; run it 10 times with seeds 1..10:
    for s in 1 2 3 4 5 6 7 8 9 10; do R04_SEED=$s R04_ACCUM=1 py -3.13 phaseB_conductor_null.py; done
Same rules: one script at a time, lowprio, no multiprocessing."""
import os, runpy
os.environ.setdefault("R04_ACCUM", "1")
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = [os.path.join(here, "s2_conductor.py"), "150", "0"]      # 150 s budget, no beam (null only)
runpy.run_path(sys.argv[0], run_name="__main__")
