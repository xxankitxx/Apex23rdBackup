"""Every test runs against a throw-away copy of the data tree, never the live one (2 Nov 2026).

On 2 Nov 2026 a test run on the owner's machine deleted data/learning/days.jsonl and defects.json, overwrote
state.json with a synthetic scoreboard, rewrote the 21-23 Oct paper files and left 45 report files for dates up to
Feb 2027: tests wrote through config.PAPER_DIR / LEARN_DIR and through the module-level paths that learning.py and
defects.py fix at import. This fixture points every one of those at a fresh temporary directory for the whole
session, so the suite can be run on the trading machine at any hour. The engine's data tree is tracked before and
after the session; a test that still reaches it fails the run.
"""
import os
import re
import shutil
import tempfile
import types

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


# Engine switches, per module (7 Nov 2026). Most suites set config.FILL_NEXT_PRINT = False at import to test the
# exit/entry logic on same-step fills (the D-126 and council suites test it as shipped, True); test_wp1 sets
# REPLAY_LOCKSTEP = False to run the replay feed alone. Imports all happen at collection, before any test runs, so
# without this the last import wins for every module and the order of the files decides the result. Each module now
# runs with the value it asked for: False when its source (or a suite it imports, e.g. test_c6_feed -> test_wp2)
# switches it off at module level, else the shipped value.
_SWITCHES = ("FILL_NEXT_PRINT", "REPLAY_LOCKSTEP")
_SHIPPED = {k: getattr(config, k) for k in _SWITCHES}
_OFF = {k: re.compile(r"^\w+\." + k + r"\s*=\s*False", re.M) for k in _SWITCHES}


def _sources(mod):
    for m in [mod] + [v for v in vars(mod).values() if isinstance(v, types.ModuleType)
                      and getattr(v, "__name__", "").startswith("test_")]:
        try:
            with open(m.__file__, encoding="utf-8") as f:
                yield f.read()
        except (OSError, TypeError, AttributeError):
            pass


@pytest.fixture(scope="module", autouse=True)
def _engine_switches_per_module(request):
    src = list(_sources(request.module))
    for k in _SWITCHES:
        setattr(config, k, False if any(_OFF[k].search(t) for t in src) else _SHIPPED[k])
    yield
    for k in _SWITCHES:
        setattr(config, k, _SHIPPED[k])


# The owner's champion (9 Nov 2026: the Conductor) is a live setting, not a test fixture. The suites that test the
# learning loop and the exit / entry mechanics were written against a plain champion book, so every test runs with the
# owner's choice equal to CHAMPION_DEFAULT unless it is marked `owner_champion` (the tests that check the shipped value).
_OWNER_SHIPPED = config.CHAMPION_OWNER


def pytest_configure(config):
    config.addinivalue_line("markers", "owner_champion: run with the shipped config.CHAMPION_OWNER")


@pytest.fixture(autouse=True)
def _plain_champion(request):
    from apex import config as cfg
    cfg.CHAMPION_OWNER = _OWNER_SHIPPED if request.node.get_closest_marker("owner_champion") else (cfg.CHAMPION_DEFAULT, "2026-10-30")
    yield
    cfg.CHAMPION_OWNER = _OWNER_SHIPPED
