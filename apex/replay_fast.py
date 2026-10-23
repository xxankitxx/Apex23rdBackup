"""
FAST replay (T02, council 5): the recorded day through the SAME parser (feed_replay.iter_records /
apply_packet / install_registry / write_chain) and the SAME engine (engine_main.Engine), in ONE process.

Lock-step semantics are those of feed_replay.publish_until + engine_main.run, exactly:
  * the first boundary is the next REPLAY_STEP_S multiple after the first packet;
  * every packet stamped <= a boundary is in the table before the engine steps that boundary;
  * one Engine.tick() per boundary, in order; after the last packet two more boundaries, then one extra
    tick at the final clock (what engine_main.run does when it sees feed_state 7), then end_day.
Nothing waits on shared memory (no 0.2-ms polling hand-shakes, no cross-process scheduling), so the wall
time is the engine's own compute plus gzip/json parsing. Set APEX_FAST=1 (run_apex does) so the engine
also skips the restart-safety book saves and fsync (config.REPLAY_FAST). The paper books, trades CSV,
decisions and candidates files are identical to a lock-step 3-process replay (verified on the 19 Oct tape).

The dashboard: the state blob is still written at the usual 4 Hz of WALL time (Engine.tick); start the
gateway with --gateway to watch it, or leave it off for a pure compute run.

Run via:  python run_apex.py replay data/ticks/2026-10-19.jsonl.gz --fast [--gateway]
"""
import argparse
import json
import os
import sys
import time

from . import config, engine_main, feed_replay
from .engine import paper
from .feed_breeze import write_chain
from .feed_core import HotStats, apply_packet
from .table import StateBlob, Table



def run(path, table=None, blob=None, log=print):
    t = table or Table(create=True)
    blob = blob or StateBlob(create=True)
    t.set("speed", 1000.0)
    t.set("feed_state", 6)
    t.set("lockstep", 1)
    hot = HotStats(t)
    eng = engine_main.Engine(t, blob, "replay")
    step_ns = int(config.REPLAY_STEP_S * 1e9)
    st = {"boundary": None, "steps": 0, "tick_s": 0.0, "last_pub": -1e18}
    wall0 = time.perf_counter()

    def tick_at(boundary):
        t.set("now_ns", boundary)
        t0 = time.perf_counter()
        eng.tick()                        # step + the wall-clock 4-Hz publish (an observer; ~8 ms each)
        st["tick_s"] += time.perf_counter() - t0
        st["steps"] += 1
        t.set("eng_vt_ns", boundary)
        eng.loop_ms = (time.perf_counter() - t0) * 1000

    def publish_until(vns):
        while st["boundary"] is not None and vns > st["boundary"]:
            tick_at(st["boundary"])
            st["boundary"] += step_ns

    by_token, items, version, part, new_part, n = None, None, 0, 1, False, 0
    try:
        for pn, r in feed_replay.iter_records(path):
            if int(t.c("stop")):
                break
            if pn != part:
                part, new_part = pn, True
                log(f"part {pn} begins")
            k = r.get("k")
            if k == "meta":
                log(f"meta {json.dumps(r.get('d'), default=str)[:200]}")
                continue
            try:
                vns, d = int(r.get("t", 0)), r.get("d")
            except (TypeError, ValueError):
                continue
            if st["boundary"] is None and k == "p":
                st["boundary"] = (vns // step_ns + 1) * step_ns
            publish_until(vns)
            if k == "reg":
                version += 1
                by_token = feed_replay.install_registry(t, d, version, prev_items=items, zero=new_part)
                items, new_part = d, False
                log(f"registry: {len(d)} instruments")
                if not eng.items:
                    eng.load_registry()
            elif k == "p" and by_token is not None:
                t0 = time.perf_counter_ns()
                apply_packet(t, by_token, d, vns)
                hot.add((time.perf_counter_ns() - t0) / 1000.0)
                n += 1
            elif k == "chain":
                write_chain(t, d)
            elif k == "vix":
                t.set("vix", float(d)); t.set("vix_ns", vns)
            t.set("feed_hb_ns", time.time_ns())
        if st["boundary"] is not None:
            publish_until(st["boundary"] + 2 * step_ns)
        log(f"done: {n} packets")
    finally:
        t.set("feed_state", 7)
    # engine_main.run on feed_state 7: one more tick at the same clock, save, close, learn, publish
    eng.tick()
    if eng.books:
        eng._safe("stop: save books", lambda: paper.save_books(eng.books, eng.day))
        if eng.eplog:
            eng._safe("stop: episode log", eng.eplog.close)
        eng._safe("stop: straddle watch", eng.watch.close)
        if getattr(eng, "ledger", None) is not None:
            eng._safe("stop: ledger", eng.ledger.close)
        try:
            eng.end_day()
        except Exception:
            import traceback
            engine_main.log("end_day at stop: " + traceback.format_exc())
    eng._safe("stop: publish", eng.publish)
    wall = time.perf_counter() - wall0
    log(f"fast replay: {st['steps']} engine steps in {wall:.0f} s wall "
        f"({1000 * st['tick_s'] / max(st['steps'], 1):.2f} ms per step, {n} packets)")
    engine_main.log("stopped")
    return eng


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--gateway", action="store_true", help="also serve the dashboard (a separate process)")
    a = ap.parse_args()
    os.environ["APEX_FAST"] = "1"
    config.REPLAY_FAST = True
    engine_main.LOG = open(os.path.join(config.LOG_DIR, "engine.log"), "a", encoding="utf-8")
    feed_replay.LOG = open(os.path.join(config.LOG_DIR, "replay.log"), "a", encoding="utf-8")
    if a.gateway:
        t, b = Table(create=True), StateBlob(create=True)             # the gateway reads the default names
    else:
        # private names: a pure compute run never collides with a live session or another replay on this machine
        t, b = Table(create=True, name=f"{config.SHM_TABLE}_fast{os.getpid()}"), StateBlob(create=True, name=f"{config.SHM_STATE}_fast{os.getpid()}")
    gw = None
    if a.gateway:
        import subprocess
        gw = subprocess.Popen([sys.executable, "-m", "apex.gateway"], env=dict(os.environ))
    try:
        run(a.file, t, b, log=feed_replay.log)
    finally:
        t.set("stop", 1)
        if gw is not None:
            try:
                gw.terminate()
            except Exception:
                pass
        t.close(); b.close(); t.unlink(); b.unlink()


if __name__ == "__main__":
    main()
