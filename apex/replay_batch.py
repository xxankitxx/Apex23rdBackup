"""
Replay BATCH driver (7 Nov, stakeholder review 7.2 / 7.3 / 7.4; round 2: 6.2-6.8). Built now, run only at the Conductor
build (owner: "We will run all replays only when we build the conductor").

  python -m apex.replay_batch TAPE [TAPE ...] [--run-id ID] [--record-missed] [--seed DIR]
  python -m apex.replay_compare RUN_A RUN_B           (the other half of the gate)

* ONE folder per run (7.2): data/replay/batch/<run_id>/ is created fresh (an existing folder is refused), APEX_DATA
  points at it, and the tapes are replayed there ONE AFTER ANOTHER in date order, one child process each. Never two
  tapes of one run at once: end_day rewrites learning/days.jsonl, state.json and day_levels.json, and every child
  appends to the same engine.log. "Three in parallel" means three run folders, merged afterwards (6.7).
* A run MANIFEST (7.3), manifest.json, written at the start and completed at the end: every tape PART that will be read
  (a restarted feed writes <day>.p2.jsonl.gz ...) with its sha256 (6.4) and the tape's own first meta record; git
  commit (+ dirty flag); feed_core.source_hash(); Python and numpy versions; the switches that change what a replay
  trades plus a hash of EVERY config constant (6.3); the seeded files and their hashes. Per tape: what the engine
  actually ran with (default book, gates, gate: books, book order = the same-tick tiebreak order; 6.2), trades per
  book, recorder rows / errors / faults, wall time, return code; the child's own output is in tape_XX.out (6.5).
* Never the dashboard (7.4): private shared-memory names and their own APEX_PORT. No --gateway here, on purpose.
* --seed DIR copies from DIR/learning/: state.json, days.jsonl (the seeded register), day_levels.json (yesterday's
  high / low / close for the level exits), strike_levels.json (the strike-levels prior) and defects.json (6.6, 8.1).
  For a faithful full pass seed from the live data folder and give the tapes in date order with no gaps.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from apex import fsutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_FILES = ("state.json", "days.jsonl", "day_levels.json", "strike_levels.json", "defects.json",
              "clock_norms.json")      # 8 Nov: earlier days' clock norms (weather items 7, 17, 25, 34); read for days < today only


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git():
    def g(*a):
        try:
            r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=20)
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None
    head = g("rev-parse", "HEAD")
    if head is None:                                    # not a checkout (or no git): skip the slower call (6.8)
        return {"commit": None, "dirty": None}
    st = g("status", "--porcelain", "--", "apex")
    return {"commit": head, "dirty": None if st is None else bool(st)}


def tape_parts(path):
    """Every file feed_replay will read for this tape, in order (6.4)."""
    from .feed_replay import expand_parts
    return [os.path.abspath(p) for p in expand_parts(path)]


def tape_meta(path):
    """The tape's first meta record (src, cfg, part ...), or None."""
    try:
        from .feed_replay import iter_records
        for _pn, r in iter_records(path):
            if r.get("k") == "meta":
                return r.get("d")
            if r.get("k") in ("p", "reg"):
                return None
    except Exception as e:
        return {"error": repr(e)}
    return None


def switches(config, env=None):
    """The settings that change what a replay trades (7.3), readable; plus a hash of every config constant (6.3)."""
    from .feed_core import config_hash_full
    env = os.environ if env is None else env
    return {"APEX_RECORD_MISSED": env.get("APEX_RECORD_MISSED") == "1", "APEX_FAST": env.get("APEX_FAST") == "1",
            "APEX_PRIOR_LEVELS": env.get("APEX_PRIOR_LEVELS") or None,
            "REPLAY_STEP_S": config.REPLAY_STEP_S, "LAST_ENTRY": list(config.LAST_ENTRY),
            "FLATTEN_AT": list(config.FLATTEN_AT), "CAS_TEST": bool(getattr(config, "CAS_TEST", False)),
            "LEARN_DECIDE": bool(config.LEARN_DECIDE),
            "VARIANTS_sha256": hashlib.sha256(json.dumps(config.VARIANTS, sort_keys=True, default=str)
                                              .encode()).hexdigest(),
            "config_full_sha1": config_hash_full()}


def seeded(run_dir):
    """The run's starting files and their hashes (what the first tape reads)."""
    out = {}
    for f in SEED_FILES:
        p = os.path.join(run_dir, "learning", f)
        out[f] = _sha256(p) if os.path.exists(p) else None
    p = os.path.join(run_dir, "learning", "state.json")
    if os.path.exists(p):
        try:
            s = json.load(open(p, encoding="utf-8"))
            out["state"] = {"champion": s.get("champion"), "gates": s.get("gates"),
                            "candidates": sorted(s.get("candidates") or {}) if isinstance(s.get("candidates"), dict)
                            else s.get("candidates")}
        except Exception as e:
            out["state"] = {"error": repr(e)}
    return out


def _write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=str)
    fsutil.replace(tmp, path)


def child(tape, out):
    """One tape, in this process; APEX_DATA, APEX_PORT and APEX_FAST were set by the parent before Python started."""
    from . import config, engine_main, feed_replay, replay_fast
    from .table import StateBlob, Table
    assert os.environ.get("APEX_DATA") and os.path.abspath(config.DATA_DIR) == os.path.abspath(os.environ["APEX_DATA"])
    config.REPLAY_FAST = True
    engine_main.LOG = open(os.path.join(config.LOG_DIR, "engine.log"), "a", encoding="utf-8")
    feed_replay.LOG = open(os.path.join(config.LOG_DIR, "replay.log"), "a", encoding="utf-8")
    tag = f"_batch{os.getpid()}"                         # private names: never the live session's (7.4)
    t, b = Table(create=True, name=config.SHM_TABLE + tag), StateBlob(create=True, name=config.SHM_STATE + tag)
    w0 = time.perf_counter()
    try:
        eng = replay_fast.run(tape, t, b, log=feed_replay.log)
    finally:
        t.set("stop", 1)
        t.close(); b.close(); t.unlink(); b.unlink()
    day = getattr(eng, "day", None)
    summ = None
    sp = os.path.join(config.PAPER_DIR, f"missed_summary_{day}.json")
    if os.path.exists(sp):
        try:
            summ = json.load(open(sp, encoding="utf-8"))
        except Exception as e:
            summ = {"error": repr(e)}
    _write(out, {"tape": tape, "day": day, "switches": switches(config),
                 "ran_with": {"champion": getattr(eng, "champion", None),          # after load_state's own fix-ups (6.2)
                              "gates": list(getattr(eng, "gates", []) or []),
                              "gate_books": [n for n in eng.books if str(n).startswith("gate:")]},
                 "books": list(eng.books),                 # the engine's own order = the same-tick tiebreak order
                 "trades": {n: len(bk.trades) for n, bk in eng.books.items()},
                 "missed": summ, "wall_s": round(time.perf_counter() - w0, 1)})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tapes", nargs="*")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--record-missed", action="store_true")
    ap.add_argument("--seed", default=None, help="a data folder whose learning/ files seed the run (see --help)")
    ap.add_argument("--base", default=None, help=argparse.SUPPRESS)          # tests: a folder outside data/
    ap.add_argument("--child", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--out", default=None, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.child:
        return child(a.child, a.out)
    if not a.tapes:
        ap.error("give at least one tape")
    for p in a.tapes:
        if not os.path.isfile(p):
            ap.error(f"no such tape: {p}")
    from . import config, feed_core
    if not hasattr(config, "LEARN_DECIDE"):              # 6.8: never run silently with the learning loop deciding
        sys.exit("config.LEARN_DECIDE is not defined")
    run_id = a.run_id or time.strftime("%Y%m%d-%H%M%S")
    base = a.base or os.path.join(ROOT, "data", "replay", "batch")
    run_dir = os.path.join(base, run_id)
    if os.path.exists(run_dir):
        sys.exit(f"run folder exists: {run_dir} (one folder per run; pick another --run-id)")
    os.makedirs(os.path.join(run_dir, "learning"))
    if a.seed:
        for f in SEED_FILES:
            src = os.path.join(a.seed, "learning", f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(run_dir, "learning", f))
    env = dict(os.environ, APEX_DATA=run_dir, APEX_FAST="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
               APEX_PORT=str(20000 + os.getpid() % 20000))    # never 8780: its own SHM default names too
    env.pop("APEX_RECORD_MISSED", None)
    if a.record_missed:
        env["APEX_RECORD_MISSED"] = "1"
    try:
        import numpy
        npv = numpy.__version__
    except Exception:
        npv = None
    tapes = []
    for p in a.tapes:
        parts = tape_parts(p)
        tapes.append({"path": os.path.abspath(p), "meta": tape_meta(p),
                      "parts": [{"path": q, "sha256": _sha256(q), "bytes": os.path.getsize(q)} for q in parts]})
    man = {"run_id": run_id, "run_dir": run_dir, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "git": _git(), "source_hash": feed_core.source_hash(), "seed": a.seed,
           "python": sys.version, "numpy": npv, "platform": platform.platform(),
           "switches": switches(config, env), "seeded": seeded(run_dir),
           "tapes": tapes, "results": [], "status": "running"}
    mpath = os.path.join(run_dir, "manifest.json")
    _write(mpath, man)
    print(f"batch run folder: {run_dir}", flush=True)
    w0, ok, status = time.perf_counter(), True, None
    try:
        for i, p in enumerate(a.tapes):
            out = os.path.join(run_dir, f"tape_{i:02d}.json")
            with open(os.path.join(run_dir, f"tape_{i:02d}.out"), "w", encoding="utf-8") as fo:   # 6.5
                r = subprocess.run([sys.executable, "-m", "apex.replay_batch", "--child", os.path.abspath(p),
                                    "--out", out], cwd=ROOT, env=env, stdout=fo, stderr=subprocess.STDOUT)
            res = {"tape": os.path.abspath(p), "returncode": r.returncode}
            if r.returncode == 0 and os.path.exists(out):
                res.update(json.load(open(out, encoding="utf-8")))
                if res.get("switches") != man["switches"]:
                    res["switch_mismatch"] = True
                    ok = False
            else:
                ok = False
            man["results"].append(res)
            _write(mpath, man)
        status = "ok" if ok else "FAILED"
    except BaseException:
        status = "aborted"                                 # 6.8: Ctrl+C or a crash never leaves "running"
        raise
    finally:
        m = [x.get("missed") or {} for x in man["results"]]
        man.update(status=status or "aborted", finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                   wall_s=round(time.perf_counter() - w0, 1),
                   totals={"trades": sum(sum((x.get("trades") or {}).values()) for x in man["results"]),
                           "missed_rows": sum(int(x.get("rows") or 0) for x in m),
                           "cf_errors": sum(int(x.get("cf_errors") or 0) for x in m),
                           "recorder_faults": sum(int(x.get("recorder_faults") or 0) for x in m)})
        _write(mpath, man)
    print(f"batch {man['status']}: {len(a.tapes)} tape(s), {man['totals']}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
