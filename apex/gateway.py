"""
GATEWAY process — serves the dashboard and pushes ticks to the browser.

  /                 the dashboard (static files)
  /api/instruments  the instrument list (id -> contract)
  /api/state        the engine's latest state (JSON)
  /ws/ticks         TICK-BY-TICK: polls the shared table every 4 ms and sends
                    only rows whose seqlock counter changed, as compact arrays
                    [id, ltp, bid, ask, bqty, aqty, ttq, oi, age_ms]
                    plus a header with the feed's hot-path timing
  /ws/state         the engine's state, pushed whenever it changes (~4 Hz); when it has
                    not changed for 1 s a small {"hb":1, engine_age_ms, feed_age_ms} frame
                    is sent instead, so the page can tell "quiet" from "frozen" (C-08)
The gateway never computes anything; a slow browser only slows itself.

Every state payload carries engine_age_ms / feed_age_ms: wall-clock age of the engine's and
the feed's heartbeat in the shared table (None until the first heartbeat).
Local hardening (C-73): only Host 127.0.0.1 / localhost; websocket Origin, when present, must
be this dashboard's own (http://127.0.0.1:PORT or http://localhost:PORT); at most
MAX_CONN concurrent connections per websocket endpoint.
"""
import asyncio
import json
import os
import re
import sys
import time

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import config
from .table import StateBlob, Table

app = FastAPI(title="ApexOptions")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])


@app.middleware("http")
async def no_cache(request, call_next):
    """index.html is served no-store, but /static/app.js and style.css were not: Chrome then keeps
    them for hours (heuristic freshness from Last-Modified), so a redesign shows up only after a hard
    refresh. The dashboard is local and tiny; never cache any of it."""
    resp = await call_next(request)
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp
T = None
B = None
LAST_STATE = b"{}"
LAST_OK = None             # engine_ok_s (WP-2) scraped from the latest blob, for hb frames
MAX_CONN = 4               # per websocket endpoint
CONN = {"ticks": 0, "state": 0}
HB_AFTER_S = 1.0           # /ws/state: heartbeat frame after this long without a new blob
_OK_RE = re.compile(rb'"engine_ok_s":(null|-?[0-9.eE+-]+)')
_LOGGED = {}               # key -> [last wall time logged, suppressed count]


def _log(key, msg):
    """At most one line per key per minute (gateway errors used to be swallowed, C-103)."""
    now = time.time()
    ent = _LOGGED.setdefault(key, [0.0, 0])
    if now - ent[0] < 60:
        ent[1] += 1
        return
    extra = f" (+{ent[1]} more in the last minute)" if ent[1] else ""
    ent[0], ent[1] = now, 0
    line = f"{time.strftime('%H:%M:%S')} gateway {key}: {msg}{extra}"
    try:
        print(line, file=sys.stderr, flush=True)
    except Exception:
        pass
    try:
        with open(os.path.join(config.LOG_DIR, "gateway.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def attach():
    global T, B
    if T is None:
        T = Table()
        B = StateBlob()


def latest_state() -> bytes:
    global LAST_STATE
    global LAST_OK
    _, data = B.read()
    if data:
        LAST_STATE = data
        m = _OK_RE.search(data)
        LAST_OK = None if not m or m.group(1) == b"null" else float(m.group(1))
    return LAST_STATE


def ages() -> dict:
    """Heartbeat ages in ms (wall clock, same machine). None = never written."""
    now = time.time_ns()
    out = {}
    for name, field in (("engine_age_ms", "engine_hb_ns"), ("feed_age_ms", "feed_hb_ns")):
        try:
            hb = int(T.c(field))
        except Exception:
            hb = 0
        out[name] = round((now - hb) / 1e6) if hb > 0 else None
    return out


def with_ages(data: bytes) -> bytes:
    """The blob with engine_age_ms / feed_age_ms appended (no re-parse of the big JSON)."""
    extra = json.dumps(ages(), separators=(",", ":")).encode()[1:-1]
    body = data.rstrip()
    if not body.endswith(b"}") or not body.startswith(b"{"):
        return data
    inner = body[1:-1].strip()
    return b"{" + inner + (b"," if inner else b"") + extra + b"}"


def hb_frame() -> str:
    d = {"hb": 1}
    d.update(ages())
    if LAST_OK is not None:
        d["engine_ok_s"] = LAST_OK
    return json.dumps(d, separators=(",", ":"))


def origin_ok(ws: WebSocket) -> bool:
    """No Origin (a non-browser client) is fine; a browser must be on this dashboard."""
    o = ws.headers.get("origin")
    if o is None:
        return True
    return o.rstrip("/").lower() in (f"http://127.0.0.1:{config.PORT}", f"http://localhost:{config.PORT}")


async def _until_closed(ws: WebSocket):
    """Reads (and ignores) client messages so a vanished browser frees its slot promptly."""
    while True:
        m = await ws.receive()
        if m.get("type") == "websocket.disconnect":
            return


async def serve(ws: WebSocket, name: str, pump):
    """Origin check and connection cap before accept; then run pump(ws) until either it
    ends or the client goes away. Unexpected errors are logged (throttled), never raised."""
    if not origin_ok(ws):
        _log("origin", f"refused /ws/{name} from Origin {ws.headers.get('origin')!r}")
        await ws.close(code=1008)
        return
    if CONN[name] >= MAX_CONN:
        _log("cap", f"refused /ws/{name}: {MAX_CONN} connections already open")
        await ws.close(code=1013)
        return
    CONN[name] += 1
    try:
        attach()
        await ws.accept()
        tasks = {asyncio.ensure_future(pump(ws)), asyncio.ensure_future(_until_closed(ws))}
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in pending:
            try:
                await t
            except BaseException:
                pass
        for t in done:
            e = t.exception()
            if e is not None and not isinstance(e, (WebSocketDisconnect, RuntimeError)):
                _log(f"ws_{name}", f"{type(e).__name__}: {e}")
    except (WebSocketDisconnect, RuntimeError):
        pass
    except Exception as e:
        _log(f"ws_{name}", f"{type(e).__name__}: {e}")
    finally:
        CONN[name] -= 1


@app.get("/")
def index():
    return FileResponse(os.path.join(config.STATIC_DIR, "index.html"),
                        headers={"Cache-Control": "no-store"})


@app.get("/api/instruments")
def instruments():
    try:
        with open(config.INSTRUMENTS_JSON, encoding="utf-8") as f:
            d = json.load(f)
        return {"version": d["version"],
                "items": [{k: it.get(k) for k in ("id", "key", "kind", "sym", "strike", "rr", "expiry", "week", "group")}
                          for it in d["items"]]}
    except Exception:
        return {"version": 0, "items": []}


@app.get("/api/state")
def state():
    attach()
    return Response(with_ages(latest_state()), media_type="application/json",
                    headers={"Cache-Control": "no-store"})


@app.websocket("/ws/ticks")
async def ws_ticks(ws: WebSocket):
    await serve(ws, "ticks", _ticks_pump)


async def _ticks_pump(ws: WebSocket):
    sent = np.zeros(config.MAX_ROWS, dtype=np.uint64)
    last_g = -1
    last_hdr = 0.0
    while True:
        g = int(T.c("gseq"))
        if g != last_g:
            last_g = g
            rows = T.rows
            seq = rows["seq"].copy()
            ch = np.nonzero((seq != sent) & ((seq & 1) == 0))[0]
            if ch.size:
                r = rows[ch]                                   # copy
                seq2 = rows["seq"][ch]                         # C-40: re-check after the copy
                good = seq2 == seq[ch]
                if not good.all():                             # torn: leave unsent, the writer's
                    ch, r = ch[good], r[good]                  # end() bumps gseq so we come back
                if ch.size:
                    sent[ch] = seq[ch]
                    now = T.now_ns()
                    age = (now - r["recv_ns"]) / 1e6
                    out = []
                    for j, i in enumerate(ch.tolist()):
                        out.append([i, _n(r["ltp"][j]), _n(r["bid"][j]), _n(r["ask"][j]), _n(r["bqty"][j]),
                                    _n(r["aqty"][j]), _n(r["ttq"][j]), _n(r["oi"][j]), round(float(age[j]), 1)])
                    await ws.send_text(json.dumps({"r": out, "v": int(T.c("reg_version"))}, separators=(",", ":")))
        t = time.monotonic()
        if t - last_hdr >= 1.0:
            last_hdr = t
            T.set("gateway_hb_ns", time.time_ns())
        await asyncio.sleep(0.004)


@app.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    await serve(ws, "state", _state_pump)


async def _state_pump(ws: WebSocket):
    last = None
    last_sent = time.monotonic()
    while True:
        data = latest_state()
        t = time.monotonic()
        if data is not last:
            last = data
            last_sent = t
            await ws.send_text(with_ages(data).decode())
        elif t - last_sent >= HB_AFTER_S:
            last_sent = t
            await ws.send_text(hb_frame())
        await asyncio.sleep(0.05)


def _n(x):
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        return None
    return round(x, 2)


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


def main():
    attach()
    # ws="wsproto": the default "websockets" backend's legacy asyncio protocol has a known
    # race between its periodic keepalive ping and a client disconnect/close (browser refresh,
    # tab close, flaky network) — both try to drain the same transport at once and raise
    # AssertionError("waiter is None or waiter.cancelled()") inside websockets.legacy.protocol.
    # It doesn't crash the gateway (that one connection is just dropped) but floods the console
    # every time a client reconnects. wsproto is a sans-I/O implementation with no such race.
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning",
                ws="wsproto", ws_ping_interval=20)


if __name__ == "__main__":
    main()
