import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 PHASE B (after the 15:30 close; one invocation at a time; each well under 3 minutes on an idle machine).

Step 1, features, ONE part per call (reuses s2_part.run):
    py -3.13 phaseB_ms_alldays.py feat <part>
  for every ds_v2 part with rows > 0 that has no work/R07/feat_<part>.npz yet:
    2026-10-19 2026-10-19.p2 2026-10-19.p3 2026-10-19.p5 2026-10-21 2026-10-22 2026-10-23 2026-10-23.p2 2026-10-26
    2026-10-27.p2 2026-10-27.p3 2026-10-28 2026-10-29.p3 2026-10-29.p4 2026-10-29.p5 2026-10-30 2026-11-02 2026-11-03
    2026-11-04 2026-11-05 2026-11-06 2026-11-09 2026-11-11.p4
  (`py -3.13 phaseB_ms_alldays.py todo` prints the parts still missing.)
Step 2, the rolling walk-forward over every part in date order (train on all earlier parts, test the next) and the
trade join on all days:
    py -3.13 phaseB_ms_alldays.py eval
  = s3_eval.py with every part; writes s3_forecast.json and s3_trades_ms.parquet (all days);
  then s5_increment.py (does trade flow / the forward-future gap add to the Lab), s6_who_leads.py (does the gap
  predict the FUTURE or the FORWARD), s7_lab_target.py (the Lab's 46 features on a forward target) and
  s8_trade_gap.py (gap and resumption speed at every trade's trigger) on every part, one after another.
Step 3, the pre-registered gates on the Conductor's own trades:
    py -3.13 phaseB_ms_gate.py"""
import glob, json, os, subprocess

W = r"D:\ApexOptions\data\research\13nov\work\R07"
DS = r"D:\ApexOptions\data\research\ds_v2"


def parts_with_rows():
    out = []
    for m in sorted(glob.glob(os.path.join(DS, "*.manifest.json"))):
        j = json.load(open(m))
        if j.get("rows", 0) > 0:
            out.append(os.path.basename(m)[:-len(".manifest.json")])
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "todo"
    allp = parts_with_rows()
    if cmd == "todo":
        print([p for p in allp if not os.path.exists(os.path.join(W, f"feat_{p}.npz"))])
    elif cmd == "feat":
        sys.path.insert(0, W)
        import s2_part
        s2_part.run(sys.argv[2])
    elif cmd == "eval":
        have = [p for p in allp if os.path.exists(os.path.join(W, f"feat_{p}.npz"))]
        # one process, sequential (s3_eval reads one part at a time)
        for sc in ("s3_eval.py", "s5_increment.py", "s6_who_leads.py", "s7_lab_target.py", "s8_trade_gap.py"):
            with open(os.path.join(W, "phaseB_" + sc.replace(".py", "_out.txt")), "w") as fo:
                subprocess.run([sys.executable, os.path.join(W, sc)] + have, check=False, stdout=fo, stderr=subprocess.STDOUT)
