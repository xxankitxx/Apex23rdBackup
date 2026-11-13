"""13 Nov: the shared patient file swap (apex.fsutil) and the chain snapshot that must never stop a feed or replay."""
import json
import os

from apex import config, fsutil


def _locked(n, real):
    calls = {"n": 0}

    def f(s, d):
        calls["n"] += 1
        if calls["n"] <= n:
            raise PermissionError("locked by antivirus")
        return real(s, d)
    return f, calls


def test_a_short_lock_is_waited_out(tmp_path):
    src, dst = tmp_path / "a.tmp", tmp_path / "a.json"
    src.write_text("new")
    dst.write_text("old")
    real = os.replace
    f, calls = _locked(4, real)
    os.replace = f
    try:
        assert fsutil.replace(str(src), str(dst), budget_s=2.0)
    finally:
        os.replace = real
    assert dst.read_text() == "new" and calls["n"] == 5 and not src.exists()


def test_a_lock_past_the_budget_raises_or_returns_false(tmp_path):
    src, dst = tmp_path / "b.tmp", tmp_path / "b.json"
    src.write_text("new")
    dst.write_text("old")
    real = os.replace
    os.replace = lambda s, d: (_ for _ in ()).throw(PermissionError("locked"))
    try:
        assert fsutil.replace(str(src), str(dst), budget_s=0.05, must=False) is False
        try:
            fsutil.replace(str(src), str(dst), budget_s=0.05)
            raise AssertionError("expected PermissionError")
        except PermissionError:
            pass
    finally:
        os.replace = real
    assert dst.read_text() == "old" and src.exists()          # nothing lost, nothing torn


def test_write_text_puts_the_whole_file_in_place(tmp_path):
    p = tmp_path / "c.json"
    assert fsutil.write_text(str(p), '{"x": 1}', fsync=True)
    assert json.loads(p.read_text()) == {"x": 1} and not (tmp_path / "c.json.tmp").exists()


class _Table:
    def __init__(self):
        self.v = {"chain_version": 3, "chain_ns": 0}

    def c(self, k):
        return self.v[k]

    def set(self, k, x):
        self.v[k] = x

    def now_ns(self):
        return 1


def test_a_refused_chain_snapshot_does_not_raise_or_move_the_version(tmp_path, monkeypatch):
    from apex import feed_breeze
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    t = _Table()
    real = os.replace
    os.replace = lambda s, d: (_ for _ in ()).throw(PermissionError("locked"))
    monkeypatch.setattr(fsutil, "DEFAULT_BUDGET_S", 0.05)
    try:
        orig = fsutil.replace
        monkeypatch.setattr(fsutil, "replace", lambda s, d, budget_s=0.05, must=True: orig(s, d, 0.05, must))
        assert feed_breeze.write_chain(t, {"a": 1}) is False
    finally:
        os.replace = real
    assert t.v["chain_version"] == 3
    assert feed_breeze.write_chain(t, {"a": 2}) is True
    assert t.v["chain_version"] == 4 and json.loads((tmp_path / "chain_latest.json").read_text()) == {"a": 2}
