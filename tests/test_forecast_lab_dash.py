"""13 Nov: the Forecast Lab writes its dashboard file off the loop (live.DashWriter): latest wins, a lock never blocks
the caller, refusals are counted and the age of the file on disk is what is reported."""
import json
import os
import time

from apex import fsutil
from apex.forecast_lab import live as L


def test_put_returns_at_once_and_the_newest_payload_lands(tmp_path):
    p = str(tmp_path / "forecast_lab.json")
    d = L.DashWriter(budget_s=0.5)
    for i in range(20):
        d.put(p, json.dumps({"i": i}), t=i)
    assert d.flush(3.0)
    assert json.load(open(p)) == {"i": 19} and d.landed_t == 19
    assert d.writes + d.superseded == 20 and d.refused == 0
    assert d.stale_s() is not None and d.stale_s() < 3.0


def test_a_locked_target_is_counted_and_does_not_block_the_caller(tmp_path, monkeypatch):
    p = str(tmp_path / "forecast_lab.json")
    open(p, "w").write('{"old": 1}')
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda s, dd: (_ for _ in ()).throw(PermissionError("locked")))
    d = L.DashWriter(budget_s=0.1)
    t0 = time.perf_counter()
    d.put(p, '{"new": 1}', t=1)
    assert time.perf_counter() - t0 < 0.05                      # the loop never waits on the lock
    assert d.flush(3.0)
    assert d.refused == 1 and d.landed_t is None and json.load(open(p)) == {"old": 1}
    monkeypatch.setattr(os, "replace", real)
    d.put(p, '{"new": 2}', t=2)
    assert d.flush(3.0) and json.load(open(p)) == {"new": 2} and d.landed_t == 2
    assert fsutil.STATS["refused"] >= 1


def test_in_memory_hand_off_skips_the_disk_and_falls_back_when_the_gateway_is_down(tmp_path, monkeypatch):
    """13 Nov (R13 idea 3): with post=True the payload goes to the gateway; the file is refreshed only every
    DISK_EVERY_S. When the post fails (gateway down) the file is written as before."""
    p = str(tmp_path / "forecast_lab.json")
    sent = []
    monkeypatch.setattr(L.DashWriter, "_post", staticmethod(lambda path, text: sent.append(text) or True))
    d = L.DashWriter(budget_s=0.5, post=True)
    d.put(p, '{"a": 1}', t=1)
    assert d.flush(3.0)
    d.put(p, '{"a": 2}', t=2)
    assert d.flush(3.0)
    assert sent == ['{"a": 1}', '{"a": 2}'] and d.posted == 2 and d.landed_t == 2
    assert d.writes == 1 and json.load(open(p)) == {"a": 1}          # disk copy only once in DISK_EVERY_S
    monkeypatch.setattr(L.DashWriter, "_post", staticmethod(lambda path, text: False))
    d.put(p, '{"a": 3}', t=3)
    assert d.flush(3.0) and json.load(open(p)) == {"a": 3} and d.writes == 2


def test_gateway_serves_the_posted_copy_and_refuses_other_names():
    import asyncio
    from starlette.requests import Request
    from apex import gateway as G

    def req(body):
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        return Request({"type": "http", "method": "POST", "headers": []}, receive)
    assert asyncio.run(G.lab_put("forecast_lab.json", req(b'{"x": 1}'))).status_code == 204
    r = G.live_file("forecast_lab.json")
    assert r.status_code == 200 and json.loads(r.body) == {"x": 1}
    assert asyncio.run(G.lab_put("other.json", req(b"{}"))).status_code == 404
    assert asyncio.run(G.lab_put("forecast_lab.json", req(b""))).status_code == 413
    assert G.live_file("../x.json").status_code == 404
    G.LAB_MEM.clear()
