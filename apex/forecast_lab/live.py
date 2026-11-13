"""Forecast Lab, live runner. A separate process: once a second it maps the feed's shared-memory table READ-ONLY, copies
the rows it needs and closes the mapping again, runs the lab, and writes the dashboard's file
apex/static/live/forecast_lab.json (forecast_lab_<port>.json on any port but the default). It never writes to the
shared table and never holds it open between reads, so a restart of the trading system (run_apex.py) can always
re-create the table. It talks to the engine only through one read of /api/state every 5 s. Below-normal priority,
one thread.

Usage: py -3.13 -m apex.forecast_lab.live          (APEX_PORT and APEX_DATA as the live session: normally unset)
Stops by itself at 15:40 IST, on Ctrl+C, on a console close, or when data/forecast_lab/STOP is created after it
started (it saves its learning and exits). A STOP file older than the start is removed at start.
One runner at a time: data/forecast_lab/live.lock is locked for the life of the process (the OS frees it on death);
it holds the pid and the start time.
Learning state: data/forecast_lab/state.json, then state.prev.json, then state_warm.json, then a cold start; the first
that LOADS is used, and the log and runner.learning say which and why. A migrated or rejected state.json is copied to
state.v<n>.<day>.json before it is first overwritten. Every save copies the previous file to state.prev.json.
data/forecast_lab/use_brain.json ({"use": false, "why": "..."}) runs the lab without the trained models (read every
60 s). APEX_LAB_STOP_AT=HH:MM (or 'none') moves the stop time, for drills only."""
import json
import os
import shutil
import sys
import threading
import time
import traceback
import urllib.request
from collections import deque
from datetime import datetime
from multiprocessing import shared_memory

os.environ["OMP_NUM_THREADS"] = "1"                 # forced: an inherited value must not give the lab more threads
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import numpy as np  # noqa: E402

from .. import fsutil
from .. import config  # noqa: E402
from ..table import CTRL_BYTES, CTRL_DTYPE, MAGIC, ROW_DTYPE, TABLE_BYTES, clean  # noqa: E402
from .core import STATE_VERSION, Lab  # noqa: E402

DEFAULT_PORT = 8780
OUT_DIR = os.path.join(config.STATIC_DIR, "live")
STATE_DIR = os.path.join(config.DATA_DIR, "forecast_lab")
STATE = os.path.join(STATE_DIR, "state.json")
PREV = os.path.join(STATE_DIR, "state.prev.json")
WARM = os.path.join(STATE_DIR, "state_warm.json")
BRAIN = os.path.join(STATE_DIR, "brain.joblib")       # the trained models (research/forecast_lab/train.py final)
USE_BRAIN = os.path.join(STATE_DIR, "use_brain.json")
CHECKPOINT = os.path.join(STATE_DIR, "checkpoint.json")
LOCKF = os.path.join(STATE_DIR, "live.lock")
STOPF = os.path.join(STATE_DIR, "STOP")          # create this file to stop the runner cleanly (it saves and exits)
NIGHTLY = os.path.join(config.DATA_DIR, "nightly_status.json")
LOCK_AT = 1 << 20                                  # the locked byte sits far past the pid text, so readers never touch it
STOP_AT = (15, 40)
NO_TABLE_WAIT_S = 5.0                              # no shared table: try again this often
ENGINE_MAX_AGE_S = 20.0                            # an engine report older than this is not used
STATUS_EVERY_S = 600.0
SAVE_EVERY_S = 60.0
ERR_EVERY_S = 60.0                                 # the same error is logged at most once a minute, with a count


def out_path(port=None, out_dir=None):
    """The dashboard file: forecast_lab.json on the default port, forecast_lab_<port>.json on any other, so a second
    lab (a drill, a replay) never overwrites the live one."""
    port = int(config.PORT if port is None else port)
    name = "forecast_lab.json" if port == DEFAULT_PORT else f"forecast_lab_{port}.json"
    return os.path.join(out_dir or OUT_DIR, name)


def stop_at():
    v = (os.environ.get("APEX_LAB_STOP_AT") or "").strip().lower()
    if v == "none":
        return None
    if v:
        try:
            hh, mm = v.split(":")
            return int(hh), int(mm)
        except ValueError:
            pass
    return STOP_AT


def below_normal():
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = ctypes.c_void_p          # a pseudo-handle: must not be truncated
            k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            # 13 Nov (R13 idea 1): below normal starved the Lab behind research jobs of the same class (29 % of its
            # seconds lost). The engine and feed run ABOVE_NORMAL under run_apex.py, so NORMAL cannot delay them.
            # APEX_LAB_PRIORITY=below keeps the old class (drills, or an engine started by hand at normal).
            cls = 0x00004000 if os.environ.get("APEX_LAB_PRIORITY", "normal") == "below" else 0x00000020
            k32.SetPriorityClass(k32.GetCurrentProcess(), cls)
        except Exception as e:
            return f"priority not lowered: {type(e).__name__}"
    else:
        try:
            os.nice(5)
        except Exception as e:
            return f"priority not lowered: {type(e).__name__}"
    return None


class Writer:
    """Atomic writes (tmp + os.replace) with the failures counted, not hidden."""

    def __init__(self):
        self.fails = 0
        self.last_err = None

    def write(self, path, text, budget_s=fsutil.SNAPSHOT_BUDGET_S):
        tmp = f"{path}.{threading.get_ident()}.tmp"        # per thread: a console-close save never shares a tmp file
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            self.fails += 1
            self.last_err = f"{os.path.basename(path)}: {type(e).__name__}"
            return False
        # 13 Nov: fsutil.replace waits out a Windows lock (Defender, the static server reading it) inside a budget;
        # a refused dashboard write is retried by the next second's write, so it gets a short budget.
        if fsutil.replace(tmp, path, budget_s=budget_s, must=False):
            return True
        self.fails += 1
        self.last_err = fsutil.STATS["last"] or f"{os.path.basename(path)}: replace refused"
        return False


_W = Writer()


class DashWriter:
    """13 Nov: the dashboard file is written off the loop. The loop hands over the newest text and goes on; this
    thread writes it and waits out a Windows lock (Defender scanning the fresh file, the gateway reading it) for up to
    DASH_BUDGET_S. A newer payload replaces one still waiting (latest wins), so a lock never delays the forecast and
    never queues old seconds. 12 Nov: 1,726 refused writes, each holding the loop up to 150 ms; 13 Nov morning: 510
    with a 0.25 s budget. What counts now is how old the file on disk is (stale_s), not each refused try."""

    def __init__(self, budget_s=None, post=False):
        self.budget_s = DASH_BUDGET_S if budget_s is None else budget_s
        # 13 Nov (R13 idea 3): with post=True each payload goes to the gateway in memory (127.0.0.1 only); the file on
        # disk is then rewritten only every DISK_EVERY_S, for a restart and for an older gateway. The gateway's
        # reader was what held the file open while the Lab swapped it (965 refusals on 13 Nov).
        self.post = post
        self.posted = 0
        self._disk_t = 0.0
        self.cv = threading.Condition()
        self.job = None
        self.busy = False
        self.landed_t = None        # the payload time (pv["t"]) of the last file that landed
        self.landed_wall = None     # wall time it landed
        self.refused = 0            # swaps refused past the budget (the next payload tries again)
        self.superseded = 0         # payloads replaced by a newer one before they were written
        self.writes = 0
        self.last_err = None
        self._k = 0
        self.thread = threading.Thread(target=self._run, name="DashWriter", daemon=True)
        self.thread.start()

    def put(self, path, text, t=None):
        with self.cv:
            if self.job is not None:
                self.superseded += 1
            self.job = (path, text, t)
            self.cv.notify_all()

    def _run(self):
        while True:
            with self.cv:
                while self.job is None:
                    self.cv.wait()
                path, text, t = self.job
                self.job, self.busy = None, True
            if self.post and self._post(path, text):
                with self.cv:
                    self.posted += 1
                    self.landed_wall = time.time()
                    if t is not None:
                        self.landed_t = t
                if time.time() - self._disk_t < DISK_EVERY_S:
                    with self.cv:
                        self.busy = False
                        self.cv.notify_all()
                    continue
                self._disk_t = time.time()
            try:
                self._k ^= 1                                     # two temporary names: a scan holding one never
                tmp = f"{path}.dash{self._k}.tmp"                # blocks the next write
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(text)
                if fsutil.replace(tmp, path, budget_s=self.budget_s, must=False):
                    with self.cv:
                        self.writes += 1
                        self.landed_wall = time.time()
                        if t is not None:
                            self.landed_t = t
                else:
                    with self.cv:
                        self.refused += 1
                        self.last_err = fsutil.STATS["last"]
            except OSError as e:
                with self.cv:
                    self.refused += 1
                    self.last_err = f"{os.path.basename(path)}: {type(e).__name__}"
            finally:
                with self.cv:
                    self.busy = False
                    self.cv.notify_all()

    @staticmethod
    def _post(path, text):
        url = f"http://127.0.0.1:{config.PORT}/api/lab/{os.path.basename(path)}"
        try:
            req = urllib.request.Request(url, data=text.encode("utf-8"), method="POST",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=0.5) as r:
                return r.status == 204
        except Exception:
            return False                                         # gateway down or older: the file path still works

    def stale_s(self, now=None):
        """Seconds since the dashboard file last changed on disk (None before the first write)."""
        return None if self.landed_wall is None else round((now or time.time()) - self.landed_wall, 1)

    def flush(self, timeout=3.0):
        end = time.monotonic() + timeout
        with self.cv:
            while self.job is not None or self.busy:
                left = end - time.monotonic()
                if left <= 0:
                    return False
                self.cv.wait(min(left, 0.1))
        return True


DASH_BUDGET_S = 2.0
DISK_EVERY_S = 15.0          # with the in-memory hand-off, the disk copy is refreshed this often


def write_atomic(path, text, budget_s=fsutil.SNAPSHOT_BUDGET_S):
    return _W.write(path, text, budget_s)


def dumps_payload(obj):
    """The payload as JSON, NaN and infinities as null (table.clean), so one bad number never stops the file."""
    return json.dumps(clean(obj), separators=(",", ":"), default=str, allow_nan=False)


def error_payload(why, t, last_ok_t, errors, runner=None):
    """What the dashboard reads when a step or the panel failed, or the runner stopped: never the old verdict."""
    now = datetime.fromtimestamp(t, config.IST)
    return dict(ok=False, why=why, t=t, now=now.strftime("%H:%M:%S"), date=now.date().isoformat(),
                last_ok_t=last_ok_t, errors=errors, hist=[], say=dict(now=[why]), runner=runner)


# ── one runner at a time, and the STOP file ────────────────────────────────────────────────────────────────────
class RunLock:
    """An OS lock on data/forecast_lab/live.lock, held for the life of the process. A dead runner leaves no stale
    lock (the OS frees it), so a reused pid can never block a start. The file holds the pid and the start time."""

    def __init__(self, path):
        self.path = path
        self.fd = None

    def acquire(self, started):
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            os.lseek(fd, LOCK_AT, os.SEEK_SET)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False
        text = json.dumps(dict(pid=os.getpid(), started=round(started, 3),
                               started_ist=datetime.fromtimestamp(started, config.IST).strftime("%Y-%m-%d %H:%M:%S")))
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text.encode("utf-8"))
        self.fd = fd
        return True

    def release(self):
        if self.fd is None:
            return
        try:
            os.lseek(self.fd, LOCK_AT, os.SEEK_SET)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass
        self.fd = None


def read_lock(path):
    """{pid, started, started_ist} from a lock file, or None (run_apex.py names the lab's pid from it)."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.loads(f.read(4096) or "null")
    except (OSError, ValueError):
        return None


def clear_old_stop(path, started):
    """A STOP file made before this process started is left over from an earlier run: remove it. Returns a log line
    or None."""
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return None
    if mt <= started:
        try:
            os.remove(path)
        except OSError as e:
            return f"old STOP file could not be removed ({type(e).__name__}); it is ignored"
        return f"old STOP file removed (made {datetime.fromtimestamp(mt, config.IST).strftime('%d %b %H:%M:%S')})"
    return None


def stop_requested(path, started):
    """True only for a STOP file created after this process started."""
    try:
        return os.path.getmtime(path) > started
    except OSError:
        return False


# ── the shared table, mapped per read ──────────────────────────────────────────────────────────────────────────
def read_table(name=None):
    """Open the shared table by name, copy the control block and every row (seqlock-checked), drop every view and
    close the mapping. Returns ((ctrl, rows), None) or (None, why). Nothing stays mapped between calls, so the
    supervisor can always re-create the table."""
    name = name or config.SHM_TABLE
    try:
        try:
            shm = shared_memory.SharedMemory(name=name, track=False)
        except TypeError:                                  # Python < 3.13
            shm = shared_memory.SharedMemory(name=name)
    except FileNotFoundError:
        return None, "trading system not running"
    except OSError as e:
        return None, f"shared table cannot be opened ({type(e).__name__})"
    cv = rv = None
    try:
        if shm.size < TABLE_BYTES:
            return None, "shared table has the wrong size"
        cv = np.ndarray((1,), dtype=CTRL_DTYPE, buffer=shm.buf, offset=0)
        ctrl = cv.copy()[0]
        cv = None
        if int(ctrl["magic"]) != MAGIC:
            return None, "shared table not initialised yet"
        if int(ctrl["stop"]) != 0:
            return None, "trading system is stopping"
        rv = np.ndarray((config.MAX_ROWS,), dtype=ROW_DTYPE, buffer=shm.buf, offset=CTRL_BYTES)
        s0 = rv["seq"].copy()
        snap = rv.copy()
        s1 = rv["seq"].copy()
        bad = np.nonzero((s0 != s1) | ((s0 & 1) == 1) | ((s1 & 1) == 1))[0]
        tries = 0
        while bad.size and tries < 5:                     # a row caught mid-write: read it again
            time.sleep(0)
            tries += 1
            before = rv["seq"][bad].copy()
            snap[bad] = rv[bad]
            after = rv["seq"][bad].copy()
            bad = bad[(before != after) | ((before & 1) == 1) | ((after & 1) == 1)]
        rv = None
        return (ctrl, snap), None
    finally:
        cv = rv = None
        try:
            shm.close()
        except BufferError:                               # a view escaped: never expected; say so rather than hide it
            sys.stderr.write("forecast lab: shared table view still exported at close\n")


# ── the chain ──────────────────────────────────────────────────────────────────────────────────────────────────
class Chain:
    """Row ids of the Nifty future, the near weekly chain and the heavyweights, from instruments.json. Built into
    locals and swapped in only when complete. instruments.json is trusted only when its version equals the table's
    reg_version (a test rig may have overwritten the file)."""

    def __init__(self):
        self.version = None
        self.mtime = None
        self.ready = False
        self.why = "not loaded"
        self._tried = None

    def load(self, reg_version=0):
        with open(config.INSTRUMENTS_JSON, encoding="utf-8") as f:
            d = json.load(f)
        mtime = os.path.getmtime(config.INSTRUMENTS_JSON)
        ver = d.get("version")
        if reg_version and ver != reg_version:
            raise ValueError(f"instruments.json is version {ver}, the shared table says {reg_version}")
        items = d["items"]
        fut = next(it["id"] for it in items if it["key"] == "NIFTY|FUT")
        today = datetime.now(config.IST).date().isoformat()
        exps = sorted({it["expiry"] for it in items if it["kind"] == "opt" and it.get("sym") == "NIFTY" and it["expiry"] >= today})
        expiry = exps[0] if exps else None
        opts = [it for it in items if it["kind"] == "opt" and it.get("sym") == "NIFTY" and it["expiry"] == expiry]
        K = np.array(sorted({float(it["strike"]) for it in opts}), float)
        idx = {k: j for j, k in enumerate(K)}
        ids = np.full((len(K), 2), -1, int)
        for it in opts:
            ids[idx[float(it["strike"])], 0 if it.get("rr", "CE") == "CE" else 1] = it["id"]
        eq = sorted((it for it in items if it["kind"] == "eq" and it.get("wn")), key=lambda it: -float(it["wn"]))
        hw_ids = np.array([it["id"] for it in eq], int)                     # heavyweights, by index weight
        hw_syms = tuple(str(it.get("sym") or it.get("key")) for it in eq)
        hw_w = np.array([float(it["wn"]) for it in eq], float)
        hw_bank = np.array([it.get("group") in ("bank", "nbfc") for it in eq], bool)
        # 13 Nov (owner point 5, R09): the sister indices. BANKNIFTY from its futures mid (its last price changes in only
        # 28 % of seconds), FINNIFTY from the index itself (its future is illiquid: 74 % of photographs read 0).
        byk = {it["key"]: it["id"] for it in items}
        sis_ids = (byk.get("BANKNIFTY|FUT"), byk.get("BANKNIFTY|SPOT"), byk.get("FINNIFTY|SPOT"))
        # complete: swap in (nothing above touched self, so a bad file leaves the previous chain whole)
        self.fut, self.expiry, self.K, self.ids = fut, expiry, K, ids
        self.hw_ids, self.hw_syms, self.hw_w, self.hw_bank = hw_ids, hw_syms, hw_w, hw_bank
        self.sis_ids = sis_ids
        self.version, self.mtime, self.ready, self.why = ver, mtime, True, None

    def maybe_reload(self, reg_version):
        """Reload when the table's registry version or the file changes. Returns a log line when something
        happened, else None. A failed attempt is not retried until the version or the file changes again."""
        try:
            mt = os.path.getmtime(config.INSTRUMENTS_JSON)
        except OSError:
            self.why = "instruments.json is missing"
            return None if self.ready else self.why
        v = int(reg_version or 0)
        if self.ready and not ((v and v != self.version) or mt != self.mtime):
            return None
        if self._tried == (v, mt):
            return None
        self._tried = (v, mt)
        try:
            self.load(v)
            return f"chain loaded: registry {self.version}, expiry {self.expiry}, {len(self.K)} strikes, {len(self.hw_ids)} heavyweights"
        except (OSError, ValueError, KeyError, StopIteration, TypeError) as e:
            self.why = f"chain not loaded: {type(e).__name__}: {e}"
            return self.why + ("; keeping the previous chain" if self.ready else "")


SIS_STALE_S = 5.0            # a sister quote older than this is not used (R09)


def sister_prices(snap, sis_ids, age):
    """(BANKNIFTY, FINNIFTY) for the stand's sister lead: BANKNIFTY futures mid (else its index), FINNIFTY index; NaN
    when missing or older than SIS_STALE_S."""
    if not sis_ids:
        return None
    bf, bs, fs = sis_ids

    def fresh(i):
        return i is not None and float(age(np.array([i]))[0]) <= SIS_STALE_S
    bn = np.nan
    if fresh(bf):
        b, a = float(snap["bid"][bf]), float(snap["ask"][bf])
        if b > 0 and a >= b:
            bn = 0.5 * (b + a)
    if not np.isfinite(bn) and fresh(bs) and float(snap["ltp"][bs]) > 0:
        bn = float(snap["ltp"][bs])
    fn = float(snap["ltp"][fs]) if fresh(fs) and float(snap["ltp"][fs]) > 0 else np.nan
    return (bn, fn)


def build_inp(snap, ch, now_ns):
    f = ch.fut
    age = lambda ids: np.where(snap["recv_ns"][ids] > 0, (now_ns - snap["recv_ns"][ids].astype(float)) / 1e9, np.inf)
    fage = float(age(np.array([f]))[0])
    has_depth = bool(np.isfinite(snap["bq"][f, 0]) and snap["depth_ns"][f] > 0)
    bq = float(np.nansum(snap["bq"][f])) if has_depth else float(snap["bqty"][f])
    aq = float(np.nansum(snap["aq"][f])) if has_depth else float(snap["aqty"][f])
    ids = ch.ids
    ok = ids >= 0
    safe = np.where(ok, ids, 0)
    ob = np.where(ok, snap["bid"][safe], np.nan).astype(float)
    oa = np.where(ok, snap["ask"][safe], np.nan).astype(float)
    og = np.where(ok, age(safe.ravel()).reshape(safe.shape), np.inf)
    stale = fage > 3.0
    hw = None
    if len(ch.hw_ids):
        hw = np.where(age(ch.hw_ids) <= 30.0, snap["ltp"][ch.hw_ids].astype(float), np.nan)
        hw = np.where(hw > 0, hw, np.nan)
    sis = sister_prices(snap, getattr(ch, "sis_ids", None), age)
    return dict(hw=hw, hw_w=ch.hw_w, hw_bank=ch.hw_bank, hw_syms=ch.hw_syms, t=now_ns / 1e9, sis=sis,
                fb=np.nan if stale else float(snap["bid"][f]), fa=np.nan if stale else float(snap["ask"][f]),
                fl=float(snap["ltp"][f]), fv=float(snap["ttq"][f]), fbq=bq, faq=aq, K=ch.K, ob=ob, oa=oa, og=og,
                expiry=ch.expiry, fage=fage)


# ── the engine's report ────────────────────────────────────────────────────────────────────────────────────────
POS_FIELDS = ("key", "strike", "rr", "expiry", "entry", "qty", "t_in", "fut_in", "iv_in", "delta_in", "entry_bid",
              "entry_ask", "src", "book", "bid_now", "last", "hold_s")
RULE_FIELDS = ("sl_px", "trail_px", "fwd_best", "fwd_now", "trail_pts", "floor_px", "floor_kind", "pt_trail_px",
               "clock_left_s", "flat_at", "bid_now")


def parse_engine(s, now=None):
    """The engine's /api/state reduced to what the lab uses, stamped with the ENGINE's time: t = now minus
    engine_age_ms (the gateway keeps serving its last good blob while the engine is stalled)."""
    now = time.time() if now is None else now
    age_ms = s.get("engine_age_ms")
    try:
        age_s = max(0.0, float(age_ms) / 1000.0) if age_ms is not None else 0.0
    except (TypeError, ValueError):
        age_s = 0.0
    cd = s.get("conductor") or {}
    pos = s.get("pos") or None
    fc = s.get("forecast") or {}
    pv = None
    if pos:
        pv = {k: pos.get(k) for k in POS_FIELDS}
        rules = pos.get("rules") or {}
        pv["rules"] = {k: rules.get(k) for k in RULE_FIELDS}
    return dict(account=dict(reason=cd.get("reason"), owner=cd.get("owner"), pos=(pos or {}).get("key")),
                pos=pv,
                old_rows=[dict(strike=r.get("strike"), side=r.get("side"), up=r.get("up"), down=r.get("down"),
                               tag=r.get("tag")) for r in (fc.get("rows") or [])],
                expiry=fc.get("expiry"), t=now - age_s, age_s=age_s)


def engine_view(info, now=None, max_age=ENGINE_MAX_AGE_S, err=None):
    """What the lab may use from the engine now. A report older than max_age (or none) keeps no held position and
    no engine pick, and says the account state is unknown."""
    now = time.time() if now is None else now
    if info is None:
        why = "account state unknown (engine not reachable" + (f": {err})" if err else ")")
        return dict(account=dict(reason=why, owner=None, pos=None), pos=None, old_rows=[], expiry=None, t=None)
    age = now - float(info.get("t") or 0.0)
    if age > max_age:
        return dict(account=dict(reason=f"account state unknown (engine report {age:.0f} s old)", owner=None, pos=None),
                    pos=None, old_rows=[], expiry=info.get("expiry"), t=info.get("t"))
    return info


class EngineReader(threading.Thread):
    """Every 5 s: the account's state and the old model's numbers from the gateway (read only). Two failed reads in a
    row drop what it knew."""

    def __init__(self):
        super().__init__(daemon=True)
        self.info = None
        self.err = None
        self.fails = 0
        self.halt = threading.Event()

    def run(self):
        url = f"http://127.0.0.1:{config.PORT}/api/state"
        while not self.halt.is_set():
            try:
                with urllib.request.urlopen(url, timeout=2.0) as r:
                    s = json.loads(r.read().decode("utf-8"))
                self.info = parse_engine(s)
                self.err = None
                self.fails = 0
            except Exception as e:                   # the engine or gateway may be restarting: carry on without
                self.err = f"{type(e).__name__}: {e}"
                self.fails += 1
                if self.fails >= 2:
                    self.info = None
            self.halt.wait(5.0)


# ── learning state ─────────────────────────────────────────────────────────────────────────────────────────────
def state_version_of(s):
    if not isinstance(s, dict):
        return None
    return s.get("state_version", s.get("version"))


def pick_state(lab, candidates):
    """Try each (path, source) in order and keep the first state that LOADS. Returns (learning, notes, keep): learning
    is the runner block, notes the log lines, keep the (path, version, day) of a state.json that must be copied aside
    before the first save (it was migrated or rejected)."""
    notes, keep = [], []
    for path, source in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                s = json.load(f)
        except (OSError, ValueError) as e:
            why = f"unreadable: {type(e).__name__}"
            notes.append(f"learning state: {source}: {why}")
            if path == STATE or os.path.basename(path) == "state.json":
                keep.append((path, "bad", None))
            continue
        ok, why, carried = lab.load(s, bounds=True)
        notes.append(f"learning state: {source}: {why}")
        ver = state_version_of(s)
        if os.path.basename(path) == "state.json" and (not ok or ver != STATE_VERSION):
            keep.append((path, ver, s.get("day") if isinstance(s, dict) else None))
        if ok:
            return dict(ok=True, source=source, state_version=ver, why=why, carried=carried,
                        updates=int(sum(h.n for h in lab.hedge)), restarts=lab.restarts,
                        alltime=dict(lab.alltime)), notes, keep
    notes.append("learning state: cold start (no saved state loaded)")
    return dict(ok=False, source="cold", state_version=None, why="cold start: no saved state loaded", carried=[],
                updates=0, restarts=0, alltime=dict(lab.alltime)), notes, keep


def state_from_label(learning):
    """The old runner.state_from field, kept for the panel. It never says 'live state' unless the file fully loaded."""
    if learning.get("ok") and learning.get("why") == "loaded":
        return "live state" if learning.get("source") == "state.json" else learning.get("source")
    if learning.get("ok"):
        return f"{learning.get('source')}, {learning.get('why')}"
    return f"none ({learning.get('why')})"


def copy_aside(path, ver, day, today):
    """Copy a state file that is about to be overwritten to state.v<n>.<day>.json, once. Returns a log line."""
    dst = os.path.join(os.path.dirname(path), f"state.v{ver}.{day or today}.json")
    if os.path.exists(dst):
        return f"old state already kept as {os.path.basename(dst)}"
    try:
        shutil.copy2(path, dst)
        return f"old state copied to {os.path.basename(dst)}"
    except OSError as e:
        return f"old state could not be copied to {os.path.basename(dst)}: {type(e).__name__}"


def save_state(lab, path=None, prev=None):
    """Copy the current file to state.prev.json, then write the new state atomically. Returns True on success."""
    path = path or STATE
    prev = prev or PREV
    if os.path.exists(path):
        try:
            tmp = f"{prev}.{threading.get_ident()}.tmp"
            shutil.copyfile(path, tmp)
            fsutil.replace(tmp, prev)
        except OSError as e:
            _W.fails += 1
            _W.last_err = f"state.prev.json: {type(e).__name__}"
    return write_atomic(path, json.dumps(clean(lab.to_json()), allow_nan=False, default=_plain), fsutil.DEFAULT_BUDGET_S)


def _plain(o):
    """json default for the saved state: arrays and numpy numbers as plain lists and numbers."""
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return clean(o.item())
    raise TypeError(type(o).__name__)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        return dict(ok=False, why=f"unreadable: {type(e).__name__}")


def brain_choice(path=None):
    """(use, why) from use_brain.json; a missing file means use the trained models when they load."""
    d = read_json(path or USE_BRAIN)
    if not isinstance(d, dict) or "use" not in d:
        return True, None
    return bool(d.get("use")), (d.get("why") or "use_brain.json says off")


# ── logging ────────────────────────────────────────────────────────────────────────────────────────────────────
class Log:
    def __init__(self, path):
        self.path = path
        self.seen = {}                     # message -> [last logged time, count since]
        self.errors = 0

    def __call__(self, msg):
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(config.IST).strftime('%H:%M:%S')} {msg}\n")
        except OSError as e:
            sys.stderr.write(f"forecast lab log unwritable ({type(e).__name__}): {msg}\n")

    def error(self, exc, now=None):
        """A traceback, the innermost 8 frames, at most once a minute per message, with the count since."""
        now = time.time() if now is None else now
        self.errors += 1
        key = f"{type(exc).__name__}: {exc}"[:200]
        last = self.seen.get(key)
        if last and now - last[0] < ERR_EVERY_S:
            last[1] += 1
            return False
        n = last[1] if last else 0
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=-8))
        self(f"error{f' (x{n + 1} since last line)' if n else ''}: " + tb.strip().replace("\n", " | "))
        self.seen[key] = [now, 0]
        return True


def pctl(xs, q):
    return round(float(np.percentile(np.asarray(xs, float), q)), 1) if xs else None


# ── the runner ─────────────────────────────────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    started = time.time()
    day = datetime.now(config.IST).date().isoformat()
    log = Log(os.path.join(STATE_DIR, f"log_{day}.txt"))
    lock = RunLock(LOCKF)
    if not lock.acquire(started):
        other = read_lock(LOCKF) or {}
        print(f"another Forecast Lab is running (pid {other.get('pid')}); not starting a second one")
        return 1
    out = out_path()
    lab = None
    saved_once = threading.Lock()
    done = {"saved": False}

    def final_save(why):
        with saved_once:
            if done["saved"] or lab is None:
                return
            done["saved"] = True
            try:
                ok = save_state(lab)
                log(f"learning state saved ({why})" if ok else f"learning state NOT saved ({why}): {_W.last_err}")
            except Exception as e:
                log.error(e)

    handler = None
    last_ok_t = None
    try:
        msg = below_normal()
        if msg:
            log(msg)
        old = clear_old_stop(STOPF, started)
        if old:
            log(old)
        if sys.platform == "win32":                       # a closed console never raises KeyboardInterrupt: save here
            try:
                import ctypes
                HANDLER = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)

                def on_ctrl(kind):
                    if kind in (2, 5, 6):                 # CTRL_CLOSE, CTRL_LOGOFF, CTRL_SHUTDOWN
                        final_save("console closed")
                        return 1
                    return 0                              # Ctrl+C / Ctrl+Break: Python's own handling
                handler = HANDLER(on_ctrl)
                ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)
            except Exception as e:
                log(f"console-close handler not set: {type(e).__name__}")
        import atexit
        atexit.register(final_save, "exit")
        from .brain import Brain
        use, off_why = brain_choice()
        br = Brain(BRAIN) if use else None
        brain_txt = (f"through {br.meta.get('trained_through')} ({br.meta.get('sessions')} sessions, {br.meta.get('hash')})"
                     if br is not None and br.ok else (f"off: {off_why}" if not use else f"none ({br.why})"))
        lab0 = Lab(state=None, brain=br)
        learning, notes, keep = pick_state(lab0, ((STATE, "state.json"), (PREV, "state.prev.json"), (WARM, "state_warm.json")))
        for n in notes:
            log(n)
        for path, ver, sday in keep:
            log(copy_aside(path, ver, sday, day))
        lab = lab0                                       # only now may a save replace state.json (never a half-started lab)
        if hasattr(lab, "restore_checkpoint"):           # PKG-09: same-day intraday checkpoint
            ck = read_json(CHECKPOINT)
            if isinstance(ck, dict) and ck.get("ok", True) is not False:
                try:
                    r = lab.restore_checkpoint(ck)
                    log(f"checkpoint: {r}")
                except Exception as e:
                    log.error(e)
        try:
            from . import record as REC                   # PKG-09: the decision record
        except ImportError:
            REC = None
        log(f"started pid {os.getpid()}; learning: {learning['source']}: {learning['why']}; "
            f"updates {learning['updates']}; trained models: {brain_txt}; output {os.path.basename(out)}")
        eng = EngineReader()
        eng.start()
        dash = DashWriter(post=True)                               # 13 Nov: the dashboard file is written off the loop
        ch = Chain()
        last_sec = None
        last_save = last_side = last_status = time.time()
        last_do = None
        table_why = None
        loop_ms, read_ms = deque(maxlen=600), deque(maxlen=600)
        skipped = stale_s = 0
        nightly = read_json(NIGHTLY)
        STOP = stop_at()
        while True:
            now = datetime.now(config.IST)
            if STOP is not None and (now.hour, now.minute) >= STOP:
                log("stop time reached")
                break
            if stop_requested(STOPF, started):
                log("stop file found")
                try:
                    os.remove(STOPF)
                except OSError as e:
                    log(f"stop file not removed: {type(e).__name__}")
                break
            time.sleep(max(0.0, 1.0 - (time.time() % 1.0)) + 0.15)       # just after each wall second
            wall = time.time()
            runner = dict(pid=os.getpid(), started=round(started), state_from=state_from_label(learning),
                          learning=dict(learning, restarts=lab.restarts, updates=int(sum(h.n for h in lab.hedge))),
                          engine_read_err=eng.err, expiry=getattr(ch, "expiry", None),
                          strikes=len(getattr(ch, "K", ())), brain=("on" if lab.brain is not None else f"off: {off_why or (br.why if br is not None else 'none')}"),
                          nightly=nightly, errors=log.errors, write_fails=_W.fails + dash.refused,
                          dash_age_s=dash.stale_s(), output=os.path.basename(out))
            try:
                r0 = time.perf_counter()
                got, why = read_table()
                read_ms.append((time.perf_counter() - r0) * 1e3)
                if got is None:
                    if why != table_why:
                        log(f"shared table: {why}; trying again every {NO_TABLE_WAIT_S:.0f} s")
                        table_why = why
                    dash.put(out, dumps_payload(error_payload(why, wall, last_ok_t, log.errors, runner)))
                    time.sleep(NO_TABLE_WAIT_S - 1.0)
                    continue
                if table_why is not None:
                    log("shared table: attached")
                    table_why = None
                ctrl, snap = got
                note = ch.maybe_reload(int(ctrl["reg_version"]))
                if note:
                    log(note)
                if not ch.ready:
                    dash.put(out, dumps_payload(error_payload(ch.why, wall, last_ok_t, log.errors, runner)))
                    continue
                v = int(ctrl["now_ns"])
                now_ns = v if v > 0 else time.time_ns()
                sec = now_ns // 1_000_000_000
                if sec == last_sec:
                    continue
                if last_sec is not None and sec - last_sec > 1:
                    skipped += int(sec - last_sec - 1)
                last_sec = sec
                c0 = time.perf_counter()
                inp = build_inp(snap, ch, now_ns)
                if not np.isfinite(inp["fage"]) or inp["fage"] > 5.0:
                    stale_s += 1
                ei = eng.info                             # one read: the reader thread may set it to None meanwhile
                inp["engine"] = engine_view(ei, err=eng.err)
                lab.step(inp)
                while lab.events:
                    log(lab.events.popleft())
                pv = lab.panel()
                hb = int(ctrl["feed_hb_ns"])
                runner.update(loop_ms=round((time.perf_counter() - c0) * 1e3, 1),
                              table_read_ms=round(read_ms[-1], 2),
                              feed_hb_age_s=round((time.time_ns() - hb) / 1e9, 1) if hb > 0 else None,
                              engine_age_s=(round(time.time() - ei["t"], 1) if ei else None),
                              restarts=lab.restarts)
                runner["learning"]["restarts"] = lab.restarts
                pv["runner"] = runner
                if REC is not None and hasattr(REC, "tick"):
                    try:
                        REC.tick(lab, pv, wall)
                    except Exception as e:
                        log.error(e)
                dash.put(out, dumps_payload(pv), pv.get("t"))
                if dash.landed_t is not None:
                    last_ok_t = dash.landed_t
                loop_ms.append((time.perf_counter() - c0) * 1e3)
                do = ((pv.get("say") or {}).get("do") or [""])[0][:40]       # the decision, not its changing numbers
                if do and do != last_do:
                    try:
                        with open(os.path.join(STATE_DIR, f"advice_{day}.jsonl"), "a", encoding="utf-8") as f:
                            f.write(json.dumps(clean(dict(t=pv.get("now"), do=pv["say"]["do"], F=pv.get("F"))), default=str) + "\n")
                    except OSError as e:
                        log(f"advice log unwritable: {type(e).__name__}")
                    last_do = do
                if time.time() - last_save > SAVE_EVERY_S:
                    if not save_state(lab):
                        log(f"learning state not saved: {_W.last_err}")
                    if hasattr(lab, "checkpoint"):
                        try:
                            ck = lab.checkpoint()
                            if isinstance(ck, dict):
                                write_atomic(CHECKPOINT, dumps_payload(ck), fsutil.DEFAULT_BUDGET_S)
                        except Exception as e:
                            log.error(e)
                    last_save = time.time()
                if time.time() - last_side > 60:          # the nightly status and the brain switch, once a minute
                    nightly = read_json(NIGHTLY)
                    use2, why2 = brain_choice()
                    if use2 != use:
                        log(f"use_brain.json changed: trained models {'on' if use2 else 'off: ' + str(why2)}; lab rebuilt")
                        st = json.loads(json.dumps(clean(lab.to_json()), default=_plain))
                        br2 = Brain(BRAIN) if use2 else None
                        lab2 = Lab(state=None, brain=br2)
                        ok, lw, carried = lab2.load(st, bounds=True)
                        if ok:
                            lab, br = lab2, br2
                            log(f"learning state: rebuilt lab: {lw}")
                            learning = dict(learning, why=lw, carried=carried)
                        else:                             # never trade the day's learning for a cold lab
                            log(f"learning state: rebuild refused ({lw}); the lab keeps running as it was")
                        use, off_why = use2, why2
                    last_side = time.time()
                if time.time() - last_status > STATUS_EVERY_S:
                    ei = eng.info
                    log(f"status: loop p50 {pctl(loop_ms, 50)} ms p95 {pctl(loop_ms, 95)} ms; table read p95 "
                        f"{pctl(read_ms, 95)} ms; skipped {skipped} s; stale {stale_s} s; errors {log.errors}; "
                        f"write fails {_W.fails}; dashboard handed over in memory {dash.posted}, file writes {dash.writes}, refused {dash.refused}, "
                        f"superseded {dash.superseded}, file age {dash.stale_s()} s; engine report "
                        f"{(str(round(time.time() - ei['t'])) + ' s old') if ei else 'none (' + str(eng.err) + ')'}; "
                        f"learning {learning['source']}: {learning['why']}; updates {int(sum(h.n for h in lab.hedge))}; "
                        f"restarts {lab.restarts}")
                    last_status = time.time()
            except Exception as e:
                log.error(e)
                dash.put(out, dumps_payload(error_payload(f"forecaster error: {type(e).__name__}: {e}"[:300], wall,
                                                          last_ok_t, log.errors, runner)))
                time.sleep(1.0)
    except KeyboardInterrupt:
        log("stopped by Ctrl+C")
    except Exception as e:
        log.error(e)
    finally:
        final_save("stop")
        try:
            d = locals().get("dash")
            if d is not None:
                d.flush(3.0)                              # the last forecast lands before the "stopped" notice
            t = time.time()
            write_atomic(out, dumps_payload(error_payload(
                f"Forecaster stopped at {datetime.fromtimestamp(t, config.IST).strftime('%H:%M on %d %b')}.",
                t, last_ok_t, log.errors)), fsutil.DEFAULT_BUDGET_S)
        except Exception as e:
            log.error(e)
        lock.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
