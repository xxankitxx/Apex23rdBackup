"""Every test runs against a throw-away copy of the data tree, never the live one (2 Nov 2026).

On 2 Nov 2026 a test run on the owner's machine deleted data/learning/days.jsonl and defects.json, overwrote
state.json with a synthetic scoreboard, rewrote the 21-23 Oct paper files and left 45 report files for dates up to
Feb 2027: tests wrote through config.PAPER_DIR / LEARN_DIR and through the module-level paths that learning.py and
defects.py fix at import. This fixture points every one of those at a fresh temporary directory for the whole
session, so the suite can be run on the trading machine at any hour. The engine's data tree is tracked before and
after the session; a test that still reaches it fails the run.
"""
import os
import shutil
import tempfile

import pytest

from apex import config
from apex.engine import defects, learning

_LIVE = {}


def _snapshot(root):
    out = {}
    for base, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
                out[p] = (st.st_size, st.st_mtime_ns)
            except OSError:
                pass
    return out


@pytest.fixture(scope="session", autouse=True)
def _isolated_data_tree():
    live = config.DATA_DIR
    before = _snapshot(live) if os.path.isdir(live) else {}
    tmp = tempfile.mkdtemp(prefix="apex-tests-")
    sub = {"DATA_DIR": "", "TICKS_DIR": "ticks", "PAPER_DIR": "paper", "LEARN_DIR": "learning", "LOG_DIR": "logs"}
    files = {"KILL_FILE": "KILL", "INSTRUMENTS_JSON": "instruments.json", "TOKEN_CACHE_JSON": "token_cache.json"}
    saved = {k: getattr(config, k) for k in list(sub) + list(files)}
    for k, d in sub.items():
        path = os.path.join(tmp, d) if d else tmp
        os.makedirs(path, exist_ok=True)
        setattr(config, k, path)
    for k, f in files.items():
        setattr(config, k, os.path.join(tmp, f))
    saved_mod = (learning.STATE, learning.DAYS, learning.REPORT, defects.DEFECTS_FILE)
    learning.STATE = os.path.join(config.LEARN_DIR, "state.json")
    learning.DAYS = os.path.join(config.LEARN_DIR, "days.jsonl")
    learning.REPORT = os.path.join(config.LEARN_DIR, "report.md")
    defects.DEFECTS_FILE = os.path.join(config.LEARN_DIR, "defects.json")
    try:
        yield tmp
    finally:
        for k, v in saved.items():
            setattr(config, k, v)
        learning.STATE, learning.DAYS, learning.REPORT, defects.DEFECTS_FILE = saved_mod
        shutil.rmtree(tmp, ignore_errors=True)
        after = _snapshot(live) if os.path.isdir(live) else {}
        changed = sorted(p for p in set(before) | set(after)
                         if before.get(p) != after.get(p) and os.sep + "logs" + os.sep not in p)
        if changed:
            pytest.fail("the test session touched the LIVE data tree: " + ", ".join(changed[:10]), pytrace=False)
