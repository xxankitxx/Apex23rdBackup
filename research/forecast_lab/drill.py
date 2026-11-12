"""Forecast Lab runtime drills (PKG-02, from the L8-I2 checklist). Each failure mode becomes an assertion with a
recovery time. NOT a test-suite job: it starts the live runner as a child process for several minutes.

Run only with the owner's OK, on an idle machine, outside market hours, never beside a replay:
    set APEX_PORT=8808
    set APEX_DATA=<a fresh scratch folder>
    py -3.13 research/forecast_lab/drill.py

It plays the supervisor and the feed itself on the port-8808 shared memory (never the live names), with a tiny
instruments.json in the scratch folder, and starts `py -3.13 -m apex.forecast_lab.live` with APEX_LAB_STOP_AT=none.
Results: <APEX_DATA>/forecast_lab/drills.json (one row per drill: name, ok, seconds, detail). Exit code 0 when every
drill passed. Drills that need the real feed, engine or gateway (engine hang, nightly, power loss) are listed in
MANUAL with what to check by hand.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

MANUAL = [
    "engine hang with the gateway up: runner.engine_age_s grows and the account line says 'engine report N s old' after 20 s",
    "gateway down: after two failed reads (10 s) the held position and the engine pick disappear",
    "power loss during a save: state.prev.json still loads (state.json then state.prev.json then state_warm.json)",
    "console close (click the X): the log ends with 'learning state saved (console closed)'",
    "real run_apex restart with the Lab attached (port 8808 sim): the restart succeeds and the Lab re-attaches within 5 s",
]


def guard():
    port = int(os.environ.get("APEX_PORT") or 0)
    data = os.environ.get("APEX_DATA") or ""
    if port in (0, 8780):
        sys.exit("drill: set APEX_PORT to a scratch port (8808), never the live one")
    if not data or os.path.abspath(data).startswith(os.path.join(ROOT, "data")):
        sys.exit("drill: set APEX_DATA to a fresh scratch folder outside the repository's data tree")
    from apex import config
    now = datetime.now(config.IST)
    if now.weekday() < 5 and (9, 0) <= (now.hour, now.minute) < (15, 45) and "--any-time" not in sys.argv:
        sys.exit("drill: not during market hours (pass --any-time only on a non-trading day)")
    return port, data


class Feed:
    """Plays the supervisor (creates the table) and the feed (one future and a two-strike chain, heartbeat)."""

    def __init__(self, Table, config):
        self.Table, self.config = Table, config
        self.t = None
        self.F = 25000.0

    def create(self):
        import run_apex
        from apex.table import StateBlob
        self.t, self.b = run_apex.create_shared(self.Table, StateBlob, self.config.DATA_DIR)
        self.t.set("reg_version", 1)

    def close(self):
        if self.t is not None:
            self.t.set("stop", 1)
            time.sleep(0.5)
            self.t.close()
            self.t.unlink()
            self.b.close()
            self.b.unlink()
            self.t = None

    def tick(self):
        if self.t is None:
            return
        now = time.time_ns()
        self.F += 0.5
        c = self.t.col
        for i, (bid, ask) in enumerate([(self.F - 0.5, self.F + 0.5), (120.0, 121.0), (110.0, 111.0)]):
            self.t.begin(i)
            c["bid"][i], c["ask"][i], c["ltp"][i] = bid, ask, 0.5 * (bid + ask)
            c["ttq"][i] += 10.0
            self.t.end(i, now)
        self.t.set("feed_hb_ns", now)


def instruments(path, version, heavy):
    exp = "2099-01-01"
    items = [dict(id=0, key="NIFTY|FUT", kind="fut", sym="NIFTY"),
             dict(id=1, key=f"NIFTY|{exp}|25000|CE", kind="opt", sym="NIFTY", expiry=exp, strike=25000, rr="CE"),
             dict(id=2, key=f"NIFTY|{exp}|25000|PE", kind="opt", sym="NIFTY", expiry=exp, strike=25000, rr="PE")]
    items += [dict(id=3 + j, key=f"S{j}|EQ", kind="eq", sym=f"S{j}", wn=10.0 - j, group="other") for j in range(heavy)]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dict(version=version, items=items), f)
    os.replace(tmp, path)


def main():
    port, data = guard()
    from apex import config
    from apex.forecast_lab import live as L
    from apex.table import Table
    lab_dir = os.path.join(config.DATA_DIR, "forecast_lab")
    os.makedirs(lab_dir, exist_ok=True)
    out = L.out_path(port)
    log_path = os.path.join(lab_dir, f"log_{datetime.now(config.IST).date().isoformat()}.txt")
    instruments(config.INSTRUMENTS_JSON, 1, 14)
    env = dict(os.environ, APEX_LAB_STOP_AT="none", OMP_NUM_THREADS="1")
    feed = Feed(Table, config)
    rows = []
    procs = []

    def start_lab():
        p = subprocess.Popen([sys.executable, "-m", "apex.forecast_lab.live"], cwd=ROOT, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        procs.append(p)
        return p

    def payload():
        try:
            with open(out, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def wait(cond, limit, tick=True):
        t0 = time.time()
        while time.time() - t0 < limit:
            if tick:
                feed.tick()
            try:
                if cond():
                    return round(time.time() - t0, 1)
            except Exception:
                pass
            time.sleep(0.25)
        return None

    def logtext():
        try:
            with open(log_path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def record(name, secs, limit, detail=""):
        rows.append(dict(name=name, ok=secs is not None, seconds=secs, limit=limit, detail=detail))
        print(f"{'PASS' if secs is not None else 'FAIL'}  {name}  ({secs} s, limit {limit} s) {detail}", flush=True)

    try:
        # 15. a STOP file left from an earlier run must not stop this start
        open(os.path.join(lab_dir, "STOP"), "w").close()
        time.sleep(1.1)
        # 1. the Lab starts before the trading system: it waits and says so
        lab = start_lab()
        record("no table: waits with ok:false 'trading system not running'",
               wait(lambda: (payload() or {}).get("why") == "trading system not running", 15, tick=False), 15)
        record("stale STOP ignored at start", 0.0 if lab.poll() is None and "old STOP file removed" in logtext() else None, 0)
        # 14. a second runner is refused by the lock
        second = start_lab()
        try:
            second.wait(timeout=20)
            record("second runner refused", 0.0 if second.returncode == 1 else None, 20, f"exit {second.returncode}")
        except subprocess.TimeoutExpired:
            second.kill()
            record("second runner refused", None, 20, "it kept running")
        # attach
        feed.create()
        record("attaches when the table appears", wait(lambda: (payload() or {}).get("ok") is True, 15), 15)
        # 2-3. a supervisor restart while the Lab runs: the create succeeds, the Lab re-attaches
        feed.close()
        record("supervisor stop seen", wait(lambda: (payload() or {}).get("ok") is False, 10, tick=False), 10)
        t0 = time.time()
        try:
            feed.create()
            record("supervisor re-create with the Lab attached", round(time.time() - t0, 1), 3)
        except SystemExit as e:
            record("supervisor re-create with the Lab attached", None, 3, str(e))
            feed.create()
        record("re-attaches after the restart", wait(lambda: (payload() or {}).get("ok") is True, 10), 5)
        # 4. a feed restart with one heavyweight fewer: no errors, the chain reloads
        n_err = logtext().count(" error")
        instruments(config.INSTRUMENTS_JSON, 2, 13)
        feed.t.set("reg_version", 2)
        secs = wait(lambda: "13 heavyweights" in logtext(), 10)
        time.sleep(3)
        record("heavyweight list change", secs if logtext().count(" error") == n_err else None, 10)
        # 5. a rig overwrote instruments.json: version differs from the table's, the old chain is kept
        instruments(config.INSTRUMENTS_JSON, 99, 13)
        record("instruments.json at another version is not trusted",
               wait(lambda: "version 99" in logtext() and (payload() or {}).get("ok") is True, 10), 10)
        instruments(config.INSTRUMENTS_JSON, 2, 13)
        # 11. a missing future in the registry: ok:false within 2 s, never an old verdict
        # (a step exception itself is covered by tests/test_forecast_lab_state.py)
        # 13. a hard kill, then a start: the lock is free
        lab.kill()
        lab.wait()
        lab = start_lab()
        record("start after a hard kill", wait(lambda: (payload() or {}).get("ok") is True and lab.poll() is None, 20), 20)
        # STOP after the start: saves and exits
        open(os.path.join(lab_dir, "STOP"), "w").close()
        try:
            lab.wait(timeout=15)
            ok = "learning state saved" in logtext() and os.path.exists(os.path.join(lab_dir, "state.json"))
            record("STOP after start: saves and exits", 0.0 if ok else None, 15)
        except subprocess.TimeoutExpired:
            record("STOP after start: saves and exits", None, 15, "still running")
        pv = payload() or {}
        record("stopped payload is ok:false", 0.0 if pv.get("ok") is False and "stopped" in str(pv.get("why")) else None, 0)
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
        feed.close()
    res = dict(when=datetime.now(config.IST).strftime("%Y-%m-%d %H:%M:%S"), port=port, rows=rows, manual=MANUAL,
               passed=sum(r["ok"] for r in rows), total=len(rows))
    path = os.path.join(lab_dir, "drills.json")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    os.replace(path + ".tmp", path)
    try:
        os.remove(out)                                   # the drill's own per-port dashboard file
    except OSError:
        pass
    print(f"{res['passed']} of {res['total']} drills passed; {path}")
    return 0 if res["passed"] == res["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
