"""7 Nov (review 7.2-7.4): the replay batch driver, without running a replay (the child is faked)."""
import json
import os
import subprocess
import tempfile

import pytest

from apex import config, replay_batch


def _tape(d):
    p = os.path.join(d, "2026-11-06.jsonl.gz")
    open(p, "wb").write(b"not a real tape")
    return p


def _fake_child(calls, books=("t28_core", "RAW")):
    def run(cmd, cwd=None, env=None, **kw):
        calls.append(env)
        out = cmd[cmd.index("--out") + 1]
        json.dump({"tape": cmd[cmd.index("--child") + 1], "day": "2026-11-06",
                   "switches": replay_batch.switches(config, env), "books": list(books),
                   "trades": {b: 2 for b in books},
                   "missed": {"rows": 5, "cf_errors": 0, "recorder_faults": 0}, "wall_s": 1.0},
                  open(out, "w"))
        return subprocess.CompletedProcess(cmd, 0)
    return run


def test_one_folder_per_run_and_manifest(monkeypatch):
    base, src = tempfile.mkdtemp(), tempfile.mkdtemp()
    tape = _tape(src)
    seed = os.path.join(src, "seed")
    os.makedirs(os.path.join(seed, "learning"))
    json.dump({"champion": "c20_9x", "gates": ["g1"], "candidates": {}},
              open(os.path.join(seed, "learning", "state.json"), "w"))
    calls = []
    monkeypatch.setattr(replay_batch.subprocess, "run", _fake_child(calls))
    monkeypatch.setattr(replay_batch, "_git", lambda: {"commit": "abc", "dirty": False})
    assert replay_batch.main([tape, "--run-id", "r1", "--base", base, "--record-missed", "--seed", seed]) == 0
    run_dir = os.path.join(base, "r1")
    m = json.load(open(os.path.join(run_dir, "manifest.json")))
    assert m["status"] == "ok" and m["tapes"][0]["sha256"] and m["git"]["commit"] == "abc"
    assert m["learning_start"]["champion"] == "c20_9x" and m["learning_start"]["gates"] == ["g1"]
    assert m["switches"]["APEX_RECORD_MISSED"] and m["switches"]["APEX_FAST"]
    assert m["results"][0]["books"] == ["t28_core", "RAW"]
    assert m["totals"] == {"trades": 4, "missed_rows": 5, "cf_errors": 0, "recorder_faults": 0}
    env = calls[0]
    assert env["APEX_DATA"] == run_dir and env["APEX_PORT"] != "8780"
    # a second run with the same id is refused: never two runs in one folder
    with pytest.raises(SystemExit):
        replay_batch.main([tape, "--run-id", "r1", "--base", base])


def test_switch_mismatch_fails_the_run(monkeypatch):
    base, src = tempfile.mkdtemp(), tempfile.mkdtemp()
    tape = _tape(src)
    real = _fake_child([])

    def run(cmd, cwd=None, env=None, **kw):
        r = real(cmd, cwd=cwd, env=env)
        out = cmd[cmd.index("--out") + 1]
        d = json.load(open(out))
        d["switches"]["LEARN_DECIDE"] = not d["switches"]["LEARN_DECIDE"]
        json.dump(d, open(out, "w"))
        return r
    monkeypatch.setattr(replay_batch.subprocess, "run", run)
    assert replay_batch.main([tape, "--run-id", "r2", "--base", base]) == 1
    m = json.load(open(os.path.join(base, "r2", "manifest.json")))
    assert m["status"] == "FAILED" and m["results"][0]["switch_mismatch"]
    assert not m["switches"]["APEX_RECORD_MISSED"]
