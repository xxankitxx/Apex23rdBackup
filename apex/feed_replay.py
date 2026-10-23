"""
REPLAY feed — plays a recorded day (data/ticks/YYYY-MM-DD.jsonl.gz, written by the
live feed or `sim --record`) back through the SAME parser, at any speed.

The recorded receive time becomes the system clock, so the engine, the paper
books and the dashboard behave exactly as they did (or would have) live. This is
how a changed rule is checked against real sessions before it is trusted.

A day recorded across feed restarts has parts (DAY.jsonl.gz, DAY.p2.jsonl.gz, ...); give
the first and the rest are played after it. A part cut off by a crash is read up to the
crash and the next part follows. The feed state always ends at DONE (7).

Run via:  python run_apex.py replay data/ticks/2026-10-19.jsonl.gz [--speed 20]
"""
import argparse
import glob
import gzip
import json
import os
import re
import time
import zlib
from datetime import datetime

import numpy as np

from . import config
from .feed_breeze import write_chain
from .feed_core import HotStats, Registry, apply_packet
from .table import Table

LOG = None


def log(msg):
    line = f"{datetime.now(config.IST).strftime('%H:%M:%S')} REPLAY {msg}"
    print(line, flush=True)
    try:
        LOG.write(line + "\n"); LOG.flush()
    except Exception:
        pass


def install_registry(table, items, version, prev_items=None, zero=False):
    """Install a recorded registry. Like the live feed's start (BreezeFeed.__init__), the rows
    are zeroed whenever the instrument ids move (C-47) — otherwise the ttq guard compares a new
    contract's quotes against the old occupant of its row and drops them — or when `zero` is
    set (the first registry of a restarted part, where the live feed zeroed its table)."""
    if prev_items is not None and not zero:
        old = {it.get("id"): it.get("key") for it in prev_items}
        zero = any(it.get("id") in old and old[it.get("id")] != it.get("key") for it in items)
    if zero:
        table.rows[:] = np.zeros(config.MAX_ROWS, dtype=table.rows.dtype)
    tmp = config.INSTRUMENTS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": version, "items": items}, f)
    os.replace(tmp, config.INSTRUMENTS_JSON)
    table.set("reg_version", version)
    return Registry.tokens_from_items(items)


_PART_RE = re.compile(r"\.p(\d+)\.jsonl(\.gz)?$")


def expand_parts(path):
    """[path] + its restart parts STEM.p2.jsonl.gz, .p3 ... sorted by part number (C-01).
    A path that is itself a .pN part is played alone."""
    if _PART_RE.search(os.path.basename(path)):
        return [path]
    base = os.path.basename(path)
    for ext in (".jsonl.gz", ".jsonl"):
        if base.endswith(ext):
            stem, sfx = base[:-len(ext)], ext
            break
    else:
        return [path]
    d = os.path.dirname(path) or "."
    parts = []
    for g in glob.glob(os.path.join(glob.escape(d), glob.escape(stem) + ".p*" + sfx)):
        m = _PART_RE.search(os.path.basename(g))
        if m and os.path.basename(g) == f"{stem}.p{m.group(1)}{sfx}":
            parts.append((int(m.group(1)), g))
    return [path] + [g for _, g in sorted(parts)]


READ_ERRORS = (EOFError, OSError, zlib.error, gzip.BadGzipFile)


def iter_records(path):
    """Yield (part_no, record) over every part. A part cut off by a crash ends where its
    readable data ends ("part N ends early") and the next part is read; never raises for a
    damaged part. Unparseable lines are skipped."""
    for n, p in enumerate(expand_parts(path), 1):
        opener = gzip.open if p.endswith(".gz") else open
        try:
            with opener(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(r, dict):
                        yield n, r
        except READ_ERRORS as e:
            log(f"part {n} ends early ({os.path.basename(p)}): {type(e).__name__}: {e}")


def run(path, speed, table_name=None):
    t = Table(name=table_name) if table_name else Table()
    t.set("speed", speed)
    t.set("feed_state", 6)
    try:
        hot = HotStats(t)
        by_token = None
        items = None
        version = 0
        n = 0
        part = 1
        new_part = False
        real0 = v0 = None
        lock = bool(config.REPLAY_LOCKSTEP)
        step_ns = int(config.REPLAY_STEP_S * 1e9)
        t.set("lockstep", 1 if lock else 0)
        t.set("eng_vt_ns", 0)
        boundary = None

        def publish_until(vns):
            """D-105: advance the virtual clock in fixed STEP boundaries up to vns, waiting at each for
            the engine to finish its step. Every packet stamped <= a boundary is in the table before
            the engine sees that boundary, exactly as live (where the engine samples every 100 ms)."""
            nonlocal boundary, lock
            while boundary is not None and vns > boundary:
                t.set("now_ns", boundary)
                deadline = time.monotonic() + 30.0
                while int(t.c("eng_vt_ns")) < boundary and not int(t.c("stop")):
                    if time.monotonic() > deadline:
                        if int(t.c("eng_vt_ns")) == 0:
                            log("lock-step: no engine acknowledged in 30 s — replaying free-running")
                            lock = False
                            t.set("lockstep", 0)
                            t.set("now_ns", vns)
                            return
                        log("lock-step: engine did not acknowledge for 30 s — continuing")
                        break
                    time.sleep(0.0002)
                boundary += step_ns

        for pn, r in iter_records(path):
            if int(t.c("stop")):
                break
            if pn != part:
                part, new_part = pn, True
                log(f"part {pn} begins")
            k = r.get("k")
            if k == "meta":                   # header/footer: logged, never on the clock
                log(f"meta {json.dumps(r.get('d'), default=str)[:200]}")
                continue
            try:
                vns, d = int(r.get("t", 0)), r.get("d")
            except (TypeError, ValueError):
                continue
            if real0 is None:
                real0, v0 = time.perf_counter(), vns
            sp = max(float(t.c("speed")), 0.1)
            due = real0 + (vns - v0) / 1e9 / sp
            lag = due - time.perf_counter()
            if lag > 0.002:
                time.sleep(lag)
            elif lag < -2.0:
                real0, v0 = time.perf_counter(), vns
            if lock:
                if boundary is None and k == "p":
                    boundary = (vns // step_ns + 1) * step_ns
                publish_until(vns)
            else:
                t.set("now_ns", vns)
            if k == "reg":
                version += 1
                by_token = install_registry(t, d, version, prev_items=items, zero=new_part)
                items, new_part = d, False
                log(f"registry: {len(d)} instruments")
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
        if lock and boundary is not None:
            publish_until(boundary + 2 * step_ns)
        # let the engine see the close and finish the day
        time.sleep(1.5)
        log(f"done: {n} packets")
    finally:                                  # C-78: whatever happened, the engine is told the day is over
        t.set("feed_state", 7)


def main():
    global LOG
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)   # Ctrl+C is the supervisor's: it sets ctrl.stop
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--speed", type=float, default=10.0)
    a = ap.parse_args()
    LOG = open(os.path.join(config.LOG_DIR, "replay.log"), "a", encoding="utf-8")
    run(a.file, a.speed)


if __name__ == "__main__":
    main()
