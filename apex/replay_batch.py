"""
Replay BATCH driver (7 Nov, stakeholder review 7.2 / 7.3 / 7.4). Built now, run only at the Conductor build (owner:
"We will run all replays only when we build the conductor").

  python -m apex.replay_batch TAPE [TAPE ...] [--run-id ID] [--record-missed] [--seed DIR]

* ONE folder per run (7.2): data/replay/batch/<run_id>/ is created fresh (an existing folder is refused), APEX_DATA
  points at it, and every tape of the run is replayed there in the order given, one child process each, so the paper
  books, decisions, events, missed_* files, engine.log and learning/state.json of two runs can never mix. Two runs of
  the same tapes in two folders are what the determinism check compares.
* A run MANIFEST (7.3), data/replay/batch/<run_id>/manifest.json, written at the start and completed at the end:
  tapes with their sha256, git commit (+ dirty flag), feed_core.source_hash(), REPLAY_STEP_S, the switches
  (APEX_RECORD_MISSED, APEX_FAST, LAST_ENTRY, FLATTEN_AT, CAS_TEST, LEARN_DECIDE), a hash of config.VARIANTS, the
  starting learning state (default book, gates, candidates, file hash); per tape the book list in the engine's own
  order (the same-tick tiebreak order), trades per book, recorder rows / errors / faults and the wall time.
* Never the dashboard (7.4): the children use private shared-memory names and their own APEX_PORT, so a batch can
  never collide with a live session. There is no --gateway here, on purpose.
* --seed DIR copies DIR/learning/state.json (and days.jsonl) into the run before the first tape: the seeded register.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    st = g("status", "--porcelain", "--", "apex")
    return {"commit": g("rev-parse", "HEAD"), "dirty": None if st is None else bool(st)}


def switches(config, env=None):
    """The settings that change what a replay trades (7.3); also echoed by every child, and checked equal."""
    env = os.environ if env is None else env
    return {"APEX_RECORD_MISSED": env.get("APEX_RECORD_MISSED") == "1", "APEX_FAST": env.get("APEX_FAST") == "1",
            "REPLAY_STEP_S": config.REPLAY_STEP_S, "LAST_ENTRY": list(config.LAST_ENTRY),
            "FLATTEN_AT": list(config.FLATTEN_AT), "CAS_TEST": bool(getattr(config, "CAS_TEST", False)),
            "LEARN_DECIDE": bool(getattr(config, "LEARN_DECIDE", True)),
            "VARIANTS_sha256": hashlib.sha256(json.dumps(config.VARIANTS, sort_keys=True, default=str)
                                              .encode()).hexdigest()}


def learning_start(run_dir):
    p = os.path.join(run_dir, "learning", "state.json")
    if not os.path.exists(p):
        return {"file": None, "note": "no state.json: the engine starts from the defaults"}
    try:
        s = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return {"file": p, "error": repr(e)}
    return {"file": p, "sha256": _sha256(p), "champion": s.get("champion"), "gates": s.get("gates"),
            "candidates": sorted(s.get("candidates") or {}) if isinstance(s.get("candidates"), dict)
            else s.get("candidates")}


def _write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


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
    for cand in (sp, os.path.join(config.DATA_DIR, f"missed_summary_{day}.json")):
        if os.path.exists(cand):
            try:
                summ = json.load(open(cand, encoding="utf-8"))
            except Exception as e:
                summ = {"error": repr(e)}
            break
    _write(out, {"tape": tape, "day": day, "switches": switches(config),
                 "books": list(eng.books),                 # the engine's own order = the same-tick tiebreak order
                 "trades": {n: len(bk.trades) for n, bk in eng.books.items()},
                 "missed": summ, "wall_s": round(time.perf_counter() - w0, 1)})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tapes", nargs="*")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--record-missed", action="store_true")
    ap.add_argument("--seed", default=None, help="a data folder whose learning/state.json (+ days.jsonl) seeds the run")
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
    run_id = a.run_id or time.strftime("%Y%m%d-%H%M%S")
    base = a.base or os.path.join(ROOT, "data", "replay", "batch")
    run_dir = os.path.join(base, run_id)
    if os.path.exists(run_dir):
        sys.exit(f"run folder exists: {run_dir} (one folder per run; pick another --run-id)")
    os.makedirs(os.path.join(run_dir, "learning"))
    if a.seed:
        for f in ("state.json", "days.jsonl"):
            src = os.path.join(a.seed, "learning", f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(run_dir, "learning", f))
    env = dict(os.environ, APEX_DATA=run_dir, APEX_FAST="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
               APEX_PORT=str(20000 + os.getpid() % 20000))    # never 8780: its own SHM default names too
    env.pop("APEX_RECORD_MISSED", None)
    if a.record_missed:
        env["APEX_RECORD_MISSED"] = "1"
    from . import config, feed_core
    man = {"run_id": run_id, "run_dir": run_dir, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "git": _git(), "source_hash": feed_core.source_hash(), "seed": a.seed,
           "switches": switches(config, env), "learning_start": learning_start(run_dir),
           "tapes": [{"path": os.path.abspath(p), "sha256": _sha256(p), "bytes": os.path.getsize(p)} for p in a.tapes],
           "results": [], "status": "running"}
    mpath = os.path.join(run_dir, "manifest.json")
    _write(mpath, man)
    print(f"batch run folder: {run_dir}", flush=True)
    w0, ok = time.perf_counter(), True
    for i, p in enumerate(a.tapes):
        out = os.path.join(run_dir, f"tape_{i:02d}.json")
        r = subprocess.run([sys.executable, "-m", "apex.replay_batch", "--child", os.path.abspath(p), "--out", out],
                           cwd=ROOT, env=env)
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
    m = [x.get("missed") or {} for x in man["results"]]
    man.update(status="ok" if ok else "FAILED", finished=time.strftime("%Y-%m-%d %H:%M:%S"),
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
