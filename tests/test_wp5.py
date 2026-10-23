"""WP-5 checks (gateway and dashboard): python tests/test_wp5.py

The gateway tests need fastapi + httpx (TestClient); without them they are skipped with a
printed note, so a numpy-only run still passes. The static app.js check always runs.
"""
import asyncio
import json
import os
import re
import sys
import tempfile
import time

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite

try:
    from fastapi.testclient import TestClient  # noqa: E402  (needs httpx)
    from starlette.websockets import WebSocketDisconnect  # noqa: E402
    from apex import gateway  # noqa: E402
    from apex.table import StateBlob, Table  # noqa: E402
    HAVE_API = True
except Exception as e:  # pragma: no cover
    HAVE_API = False
    WHY = f"{type(e).__name__}: {e}"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = f"http://127.0.0.1:{config.PORT}"
_SHM = {}


def _setup():
    """Private shared memory (never the live names), attached to the gateway module."""
    if not _SHM:
        tag = f"{os.getpid()}"
        _SHM["t"] = Table(create=True, name=f"t_wp5_{tag}")
        _SHM["b"] = StateBlob(create=True, name=f"b_wp5_{tag}")
    gateway.T, gateway.B = _SHM["t"], _SHM["b"]
    gateway.LAST_STATE, gateway.LAST_OK = b"{}", None
    gateway.CONN.update(ticks=0, state=0)
    return _SHM["t"], _SHM["b"]


def _teardown():
    for k in ("t", "b"):
        if k in _SHM:
            _SHM[k].close(); _SHM[k].unlink()
    _SHM.clear()


def _client():
    return TestClient(gateway.app, base_url=BASE)


def _ws(c, path, headers=None):
    return c.websocket_connect(f"ws://127.0.0.1:{config.PORT}{path}", headers=headers or {})


def _refused(c, path, headers=None):
    """Close code if the gateway refused the websocket, else None."""
    try:
        with _ws(c, path, headers) as ws:
            ws.receive_text()
    except WebSocketDisconnect as e:
        return e.code
    return None


# ── (a) Host allow-list ───────────────────────────────────────────────────
def test_host_allowlist():
    _setup()
    c = _client()
    assert c.get("/api/state", headers={"Host": "evil.example"}).status_code == 400
    assert c.get("/api/state", headers={"Host": "evil.example:8780"}).status_code == 400
    # the owner's own browser
    assert c.get("/api/state", headers={"Host": f"127.0.0.1:{config.PORT}"}).status_code == 200
    assert c.get("/api/state", headers={"Host": f"localhost:{config.PORT}"}).status_code == 200


# ── (b) websocket Origin check ────────────────────────────────────────────
def test_ws_origin():
    t, b = _setup()
    b.write({"now": "x"})
    c = _client()
    assert _refused(c, "/ws/state", {"Origin": "https://evil.example"}) == 1008
    assert _refused(c, "/ws/ticks", {"Origin": "https://evil.example"}) == 1008
    assert _refused(c, "/ws/state", {"Origin": f"http://127.0.0.1:{config.PORT + 1}"}) == 1008
    for origin in (f"http://127.0.0.1:{config.PORT}", f"http://localhost:{config.PORT}", None):
        gateway.LAST_STATE = b"{}"; b._seq = 0
        h = {"Origin": origin} if origin else {}
        with _ws(c, "/ws/state", h) as ws:
            d = json.loads(ws.receive_text())
            assert d.get("now") == "x", (origin, d)
    with c.websocket_connect(f"ws://localhost:{config.PORT}/ws/ticks",
                             headers={"Origin": f"http://localhost:{config.PORT}"}):
        pass                                               # localhost Host + Origin accepted
    assert gateway.CONN["state"] == 0                      # slots released on close


def test_ws_connection_cap():
    t, b = _setup()
    b.write({"now": "x"})
    c = _client()
    h = {"Origin": f"http://localhost:{config.PORT}"}
    opened = []
    try:
        for _ in range(gateway.MAX_CONN):
            cm = _ws(c, "/ws/state", h)
            opened.append((cm, cm.__enter__()))
        deadline = time.time() + 2
        while gateway.CONN["state"] < gateway.MAX_CONN and time.time() < deadline:
            time.sleep(0.01)
        assert gateway.CONN["state"] == gateway.MAX_CONN
        assert _refused(c, "/ws/state", h) == 1013
    finally:
        for cm, _ in opened:
            cm.__exit__(None, None, None)
    deadline = time.time() + 2
    while gateway.CONN["state"] and time.time() < deadline:
        time.sleep(0.01)
    assert gateway.CONN["state"] == 0


# ── (c) staleness fields and heartbeat frames ─────────────────────────────
def test_state_has_ages():
    t, b = _setup()
    now = time.time_ns()
    t.set("engine_hb_ns", now - 5_000_000_000)
    t.set("feed_hb_ns", now - 1_000_000_000)
    b.write({"now": "2026-10-19 10:00:00", "engine_ok_s": 36000.5, "pos": None})
    c = _client()
    d = c.get("/api/state").json()
    assert 4900 <= d["engine_age_ms"] <= 6000, d
    assert 900 <= d["feed_age_ms"] <= 2000, d
    assert d["engine_ok_s"] == 36000.5 and d["now"] == "2026-10-19 10:00:00"
    t.set("engine_hb_ns", 0)
    assert c.get("/api/state").json()["engine_age_ms"] is None      # never written


def test_with_ages_empty_and_odd_blobs():
    _setup()
    assert set(json.loads(gateway.with_ages(b"{}"))) == {"engine_age_ms", "feed_age_ms"}
    assert gateway.with_ages(b"not json") == b"not json"            # never corrupts a frame


def test_ws_state_heartbeat_frame():
    t, b = _setup()
    t.set("engine_hb_ns", time.time_ns() - 3_000_000_000)
    b.write({"now": "x", "engine_ok_s": 12.0})
    c = _client()
    with _ws(c, "/ws/state") as ws:
        first = json.loads(ws.receive_text())
        assert first["now"] == "x" and "engine_age_ms" in first
        t0 = time.monotonic()
        hb = json.loads(ws.receive_text())                 # blob unchanged -> heartbeat
        assert hb.get("hb") == 1 and "now" not in hb, hb
        assert hb["engine_age_ms"] >= 3000 and "feed_age_ms" in hb and hb["engine_ok_s"] == 12.0
        assert 0.5 <= time.monotonic() - t0 <= 2.5


# ── torn-read re-check in the tick diff loop (C-40) ───────────────────────
class _TearingRows:
    """Rows view whose second read of 'seq' shows row 1 mid-write (a writer began after the copy)."""
    def __init__(self, rows):
        self.r, self.n = rows, 0

    def __getitem__(self, k):
        if isinstance(k, str) and k == "seq":
            self.n += 1
            s = self.r["seq"].copy()
            if self.n == 2:
                s[1] += 1
            return s
        return self.r[k]


class _FakeWS:
    def __init__(self):
        self.sent = []

    async def send_text(self, s):
        self.sent.append(json.loads(s))


def test_ticks_torn_row_skipped():
    t, b = _setup()
    for i in (0, 1):
        t.begin(i); t.rows["ltp"][i] = 100 + i; t.end(i, time.time_ns())
    real = t.rows
    t.rows = _TearingRows(real)
    ws = _FakeWS()
    try:
        asyncio.run(asyncio.wait_for(gateway._ticks_pump(ws), 0.03))
    except asyncio.TimeoutError:
        pass
    finally:
        t.rows = real
    ids = [r[0] for f in ws.sent for r in f["r"]]
    assert ids.count(0) == 1, ws.sent
    assert 1 not in ids, ws.sent                         # torn row not sent from the bad copy
    # untorn now: the next pass (after the writer's end bumps gseq) sends row 1
    t.begin(1); t.end(1, time.time_ns())
    ws2 = _FakeWS()
    try:
        asyncio.run(asyncio.wait_for(gateway._ticks_pump(ws2), 0.03))
    except asyncio.TimeoutError:
        pass
    assert 1 in [r[0] for f in ws2.sent for r in f["r"]]


def test_log_throttle():
    _setup()
    gateway._LOGGED.clear()
    path = os.path.join(config.LOG_DIR, "gateway.log")
    n0 = len(open(path).readlines()) if os.path.exists(path) else 0
    for _ in range(5):
        gateway._log("unit", "boom")
    assert len(open(path).readlines()) - n0 == 1
    assert gateway._LOGGED["unit"][1] == 4


# ── (d) static checks on the dashboard ────────────────────────────────────
def test_static_app_js():
    js = open(os.path.join(ROOT, "apex", "static", "app.js"), encoding="utf-8").read()
    html = open(os.path.join(ROOT, "apex", "static", "index.html"), encoding="utf-8").read()
    css = open(os.path.join(ROOT, "apex", "static", "style.css"), encoding="utf-8").read()
    assert "function checkStale" in js and "ENGINE STALE" in js and "DISCONNECTED" in js
    assert "engine_age_ms" in js and "d.hb" in js                 # heartbeat frames handled
    assert not re.search(r"setTimeout\(\s*connect\w*\s*,\s*\d+\s*\)", js), "fixed-delay reconnect"
    assert "Math.pow(1.3" in js and "Math.random()" in js and "10000" in js
    assert 'id="stale"' in html and re.search(r'id="verdict"[^>]*aria-live="polite"', html)
    assert re.search(r"\.leg \.meta \{[^}]*white-space: normal", css)
    assert not re.search(r"\.leg \.meta \{[^}]*nowrap", css)
    # OI map: puts in the PE colour (down), calls in the CE colour (up)
    assert re.search(r"alpha\(C\.down[^;]*;\s*const pw = pe", js) and re.search(r"alpha\(C\.up[^;]*;\s*const cw = ce", js)
    assert "f.dir * fwin" in js                                   # force colour from dir × verdict


API_TESTS = {"test_host_allowlist", "test_ws_origin", "test_ws_connection_cap", "test_state_has_ages",
             "test_with_ages_empty_and_odd_blobs", "test_ws_state_heartbeat_frame",
             "test_ticks_torn_row_skipped", "test_log_throttle"}

if __name__ == "__main__":
    try:
        for name, fn in list(globals().items()):
            if name.startswith("test_") and callable(fn):
                if name in API_TESTS and not HAVE_API:
                    print(f"skip {name} (fastapi/httpx not importable: {WHY})")
                    continue
                fn()
                print("ok", name)
    finally:
        if HAVE_API:
            _teardown()
    print("all passed")
