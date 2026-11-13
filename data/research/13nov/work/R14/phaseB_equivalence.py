"""R14 phase B: the equivalence gate for every speed change (docs/research/13nov/R14_engine_speed.md).
NEEDS THE OWNER'S OK: it runs replays (apex.replay_batch), which the 13 Nov safety rules forbid during the session.
By default it only PRINTS the commands. Run after 15:30 with --run once the owner has said yes.

Protocol (per change, or per batch of changes):
  A  = the committed code (git worktree at HEAD)          B = the same tree with the change applied
  A' = A again (the noise floor: wall-clock fields in the photograph, eng_* and save_*, differ run to run)
  Days: 27 Oct (heaviest trading), 3 Nov (an expiry Tuesday), 12 Nov (the newest tape).
  Pass: replay_compare A B differs ONLY where replay_compare A A' differs (the eng_* / save_* photo fields); every
  trade of all 107 books and the Conductor, every decision line, every strikes line: identical."""
import argparse, os, subprocess, sys
ROOT = r"D:\ApexOptions"
TAPES = [r"data\ticks\2026-10-27.jsonl.gz", r"data\ticks\2026-11-03.jsonl.gz", r"data\ticks\2026-11-12.jsonl.gz"]
def cmds(tree, run_id, port):
    env = f"set APEX_PORT={port}&& set OMP_NUM_THREADS=1&& "
    return f'cd /d {tree} && {env}py -3.13 -m apex.replay_batch {" ".join(os.path.join(ROOT, t) for t in TAPES)} --run-id {run_id} --seed {ROOT}\data'
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--tree-b", required=False, default=r"D:\ApexOptions_r14b")
    ap.add_argument("--run", action="store_true", help="actually run (only with the owner's OK, after the close)")
    a = ap.parse_args()
    plan = [(ROOT, "r14_A", 8771), (ROOT, "r14_A2", 8772), (a.tree_b, "r14_B", 8773)]
    for tree, rid, port in plan:
        c = cmds(tree, rid, port); print(c)
        if a.run: subprocess.run(c, shell=True, check=True)          # one after another, never in parallel
    for x, y in (("r14_A", "r14_A2"), ("r14_A", "r14_B")):
        c = f"py -3.13 -m apex.replay_compare {ROOT}\data\replay\batch\{x} {ROOT}\data\replay\batch\{y}"
        print(c)
        if a.run: subprocess.run(c, shell=True)
