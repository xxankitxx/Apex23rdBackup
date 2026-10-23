"""
Feed core — shared by the live Breeze feed, the synthetic simulator and the
replayer, so all three drive the system through ONE parser.

Raw Breeze packet layouts (verified in breeze_connect 1.0.69 `parse_data`):
  quote, NSE cash  : 21-element list, symbol "4.1!<token>"
     [symbol, open, last, high, low, change, bPrice, bQty, sPrice, sQty, ltq,
      avgPrice, ttq, totalBuyQt, totalSellQ, ttv, trend, lowerCkt, upperCkt,
      ltt_epoch, close]
  quote, NFO       : 23-element list
     [... avgPrice(11), OI(12), CHNGOI(13), ttq(14), totalBuyQt(15),
      totalSellQ(16), ttv(17), trend(18), lowerCkt(19), upperCkt(20),
      ltt_epoch(21), close(22)]
  depth            : [symbol "4.2!<token>", time_epoch,
                      [[bRate, bQty, bOrders, bFlag, sRate, sQty, sOrders, sFlag] x 5]]
We read the raw list (hooked before the SDK's dict building), keep `ltt` as a
number, and never call strftime on the hot path.
"""
import gzip
import json
import os
import queue
import threading
import time
from collections import deque

import numpy as np

from . import config


def _f(x) -> float:
    try:
        if x is None or x == "":
            return np.nan
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def replace_retry(src, dst, tries=8):
    """os.replace that tolerates a Windows sharing violation while a reader has the file open."""
    for k in range(tries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            time.sleep(0.05 * (k + 1))
    os.replace(src, dst)


class Registry:
    """Instrument list. Each instrument: id, key, kind, sym, strike, right,
    expiry, token (quote token, e.g. '4.1!35001'), depth (bool), hero (bool),
    weights."""

    def __init__(self):
        self.items = []
        self.by_key = {}
        self.by_token = {"eq": {}, "fo": {}}   # numeric token -> id, per segment
        self.version = 0

    def add(self, key, kind, sym, token, strike=0.0, right="", expiry="",
            depth=False, hero=False, seg="fo", **extra):
        if key in self.by_key:
            it = self.items[self.by_key[key]]
            it["depth"] = it["depth"] or depth
            it["hero"] = hero
            # C-36: a contract first added without depth (outside the build-centre hero band)
            # gets its depth token when a re-centre asks for it; subscribe_all joins it.
            dt = extra.get("depth_token")
            if dt and not it.get("depth_token"):
                it["depth_token"] = dt
            return it["id"]
        if len(self.items) >= config.MAX_ROWS:
            raise RuntimeError("instrument table full")
        i = len(self.items)
        it = dict(id=i, key=key, kind=kind, sym=sym, token=token, strike=float(strike),
                  right=right, expiry=expiry, depth=bool(depth), hero=bool(hero), seg=seg, **extra)
        self.items.append(it)
        self.by_key[key] = i
        if token:
            self.by_token[seg][str(token).split("!")[-1]] = i
        return i

    @staticmethod
    def tokens_from_items(items):
        bt = {"eq": {}, "fo": {}}
        for it in items:
            if it.get("token"):
                bt[it.get("seg", "fo")][str(it["token"]).split("!")[-1]] = it["id"]
        return bt

    def save(self, table=None):
        self.version += 1
        tmp = config.INSTRUMENTS_JSON + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"version": self.version, "items": self.items}, f)
        replace_retry(tmp, config.INSTRUMENTS_JSON)
        if table is not None:
            table.set("reg_version", self.version)

    @staticmethod
    def load():
        with open(config.INSTRUMENTS_JSON, encoding="utf-8") as f:
            return json.load(f)


class HotStats:
    """Per-second hot-path timing (µs), published to the control block."""

    def __init__(self, table):
        self.t = table
        self.buf = deque(maxlen=20000)
        self.n = 0
        self.last = time.monotonic()

    def add(self, us: float):
        self.buf.append(us)
        self.n += 1
        now = time.monotonic()
        if now - self.last >= 1.0:
            a = np.fromiter(self.buf, float) if self.buf else np.zeros(1)
            self.t.set("hot_p50_us", float(np.percentile(a, 50)))
            self.t.set("hot_p99_us", float(np.percentile(a, 99)))
            self.t.set("hot_max_us", float(a.max()))
            self.t.set("msgs_per_s", self.n / (now - self.last))
            self.buf.clear()
            self.n = 0
            self.last = now


VOLUME_RESET_FRAC = 0.2       # D-095: cumulative volume falling below 20 % of the held count = a new session


def _ist_day(epoch_s):
    """IST calendar day number of an exchange epoch stamp, or None if it is missing/implausible."""
    if not (epoch_s == epoch_s) or epoch_s < 1.0e9:
        return None
    return int((epoch_s + 19800) // 86400)


# D-138 (external review: "protocol-shape canary"): packets whose layout is not the verified one are counted by shape, so a
# Breeze format change shows up in the feed log within a minute instead of silently degrading the data.
SHAPE_ODD = {}


def _odd(shape):
    SHAPE_ODD[shape] = SHAPE_ODD.get(shape, 0) + 1


def apply_packet(table, by_token, raw, recv_ns: int) -> int:
    """Write one raw Breeze packet into the table. Returns row id or -1.
    by_token = {"eq": {tok: id}, "fo": {tok: id}} — NSE cash and NFO share the
    '4.' prefix, so a quote's length (21 cash / 23 F&O) picks the segment."""
    if not isinstance(raw, (list, tuple)) or not raw or not isinstance(raw[0], str):
        return -1
    sym = raw[0]
    if "!" not in sym:
        return -1
    head, tok = sym.split("!", 1)
    kind = head.split(".")[-1] if "." in head else "1"
    n = len(raw)
    if kind == "1" and n not in (21, 23):
        _odd(f"quote len {n}")            # D-138: not the verified 21 / 23-element layout (counted before the lookup)
    if kind == "1":
        i = by_token["fo" if n == 23 else "eq"].get(tok, -1)
    else:
        i = by_token["fo"].get(tok, by_token["eq"].get(tok, -1))
    if i < 0:
        return -1
    r = table.col                         # T02: cached column views (same cells, same values)
    if kind == "1" and n in (21, 23):
        ltp = _f(raw[2])
        ttq_new = _f(raw[14] if n == 23 else raw[12])
        ltt_new = _f(raw[21] if n == 23 else raw[19])
        old_ttq = r["ttq"][i]
        old_ltt = r["ltt"][i]
        # Ordering guard, FIELD BY FIELD (D-095, live 19 Oct 2026). SDK threads reorder packets, and on
        # connect Breeze replays the PREVIOUS session's last quote with that whole day's traded
        # quantity (305 M); even the 09:15:00 packet still carries it before the exchange resets the
        # counter. The old rule (drop the packet if its volume is lower than the held one) therefore
        # rejected every live packet of the day and froze ~99 % of call quotes at Friday's close.
        # Breeze's exchange stamp jitters by ~1 s (tick packets carry ltt+1 with older bid/ask), so it
        # cannot order packets within a session either. Rules:
        #   * a packet stamped on an EARLIER trading day than the held quote: dropped entirely;
        #   * price fields (ltp, ltt, OHLC, avg, close) advance unless the packet is >= 2 s older
        #     than the held quote within the same day;
        #   * bid/ask/sizes/OI/book totals always take the newest arrival;
        #   * cumulative volume never steps backwards within a session (a small decrease is a
        #     reordered packet: keep the held count); a collapse below VOLUME_RESET_FRAC of the held
        #     count is the session counter resetting: take it.
        d_new = _ist_day(ltt_new)
        d_old = _ist_day(old_ltt)
        if d_new is not None and d_old is not None and d_new < d_old:
            return -1
        px_ok = not (d_new is not None and d_new == d_old and ltt_new < old_ltt - 2.0)
        if ttq_new == ttq_new and (old_ttq <= 0 or ttq_new >= old_ttq or ttq_new < VOLUME_RESET_FRAC * old_ttq):
            ttq_set = ttq_new
        else:
            ttq_set = old_ttq
        table.begin(i)
        try:                              # C-41: end() always runs, so seq never stays odd
            if px_ok:
                if ltp == ltp and ltp > 0:
                    r["ltp"][i] = ltp
                r["open"][i] = _f(raw[1]); r["high"][i] = _f(raw[3]); r["low"][i] = _f(raw[4])
                r["avg"][i] = _f(raw[11])
                if ltt_new == ltt_new:
                    r["ltt"][i] = ltt_new
                r["close"][i] = _f(raw[22] if n == 23 else raw[20])
            r["bid"][i] = _f(raw[6]); r["bqty"][i] = _f(raw[7])
            r["ask"][i] = _f(raw[8]); r["aqty"][i] = _f(raw[9])
            r["ttq"][i] = ttq_set
            if n == 23:
                oi = _f(raw[12])
                if oi == oi and oi > 0:
                    r["oi"][i] = oi
                r["tbq"][i] = _f(raw[15]); r["tsq"][i] = _f(raw[16])
            else:
                r["tbq"][i] = _f(raw[13]); r["tsq"][i] = _f(raw[14])
        finally:
            table.end(i, recv_ns)
        return i
    if kind == "1" and n >= 6:            # unexpected layout: keep at least the price
        ltp = _f(raw[2])
        if ltp == ltp and ltp > 0:
            table.begin(i)
            try:
                r["ltp"][i] = ltp
            finally:
                table.end(i, recv_ns)
            return i
        return -1
    if kind == "2" and n >= 3 and isinstance(raw[2], (list, tuple)):
        lv = raw[2]
        table.begin(i)
        try:                              # C-41: a malformed level is NaN, never an exception mid-write
            for k in range(5):
                b = lv[k] if k < len(lv) else None
                ok = False
                if isinstance(b, (list, tuple)) and len(b) >= 8:
                    try:
                        r["bpx"][i, k] = _f(b[0]); r["bq"][i, k] = _f(b[1]); r["bo"][i, k] = _f(b[2])
                        r["apx"][i, k] = _f(b[4]); r["aq"][i, k] = _f(b[5]); r["ao"][i, k] = _f(b[6])
                        ok = True
                    except Exception:
                        ok = False
                if not ok:
                    if k < len(lv):
                        _odd("depth level")       # D-138: a present but malformed depth level
                    r["bpx"][i, k] = r["bq"][i, k] = r["bo"][i, k] = np.nan
                    r["apx"][i, k] = r["aq"][i, k] = r["ao"][i, k] = np.nan
            r["depth_ns"][i] = recv_ns
        finally:
            # D-096: a depth packet refreshes depth_ns only. recv_ns is the QUOTE's receive time, which
            # the engine reads as quote age; depth packets kept frozen call quotes looking 0-2 s old
            # all morning on 19 Oct (their price was 2,600+ s old) and beat every staleness check.
            table.end(i, int(r["recv_ns"][i]))
        return i
    return -1


SCHEMA = 1


def _git_short():
    """Short git hash of the code tree, or None (no git, not a checkout, timeout)."""
    try:
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True,
                           text=True, timeout=3)
        h = r.stdout.strip()
        return h if r.returncode == 0 and h else None
    except Exception:
        return None


def source_hash():
    """D-107 (council m25/m29): a hash of the code itself (apex/**/*.py), stamped into every tape and
    shown at engine start, so a replay can tell whether it runs the code that recorded the day.
    The owner's folder is not a git checkout, so the git hash is usually None."""
    import hashlib
    root = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha1()
    for dp, _, fs in sorted(os.walk(root)):
        if "__pycache__" in dp:
            continue
        for f in sorted(fs):
            if f.endswith(".py"):
                try:
                    with open(os.path.join(dp, f), "rb") as fh:
                        h.update(f.encode() + b"\0" + fh.read())
                except OSError:
                    pass
    return h.hexdigest()[:12]


def config_hash():
    """sha1 of the frozen rule set: VARIANTS, CONTROLS, the guard constants and IV_RISE_CAP (C-49)."""
    import hashlib
    try:
        from .engine import guard
        g = {k: getattr(guard, k) for k in dir(guard)
             if k.isupper() and isinstance(getattr(guard, k), (int, float, str, bool, tuple, list, set, frozenset))}
        g = {k: sorted(v) if isinstance(v, (set, frozenset)) else v for k, v in g.items()}
    except Exception:
        g = None
    blob = json.dumps({"VARIANTS": config.VARIANTS, "CONTROLS": list(config.CONTROLS), "GUARD": g,
                       "IV_RISE_CAP": config.IV_RISE_CAP}, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()


def part_path(base_dir: str, stem: str, part: int) -> str:
    """Part 1 is STEM.jsonl.gz; later parts (a restarted feed) are STEM.pN.jsonl.gz."""
    return os.path.join(base_dir, f"{stem}.jsonl.gz" if part <= 1 else f"{stem}.p{part}.jsonl.gz")


class Recorder:
    """One gzip file per Recorder start (C-01): data/ticks/YYYY-MM-DD.jsonl.gz, and after a
    restart YYYY-MM-DD.p2.jsonl.gz, .p3 ... — a crashed part (no gzip trailer) never has a
    new member appended behind it, so every part stays readable up to its crash point.
    Every raw packet, REST result and registry snapshot, in arrival order, with its receive
    time. The first record is a `meta` header (schema, code, config hash, part); the last,
    on a clean stop, is a `meta` with the drop and line counts. The writer is a background
    thread; the hot path only does queue.put_nowait."""

    def __init__(self, day: str, enabled: bool = True, suffix: str = ""):
        self.enabled = enabled
        self.q = queue.Queue(maxsize=1_000_000)
        self.dropped = 0
        self.lines = 0
        self.part = 1
        stem = f"{day}{suffix}"
        self.path = part_path(config.TICKS_DIR, stem, 1)   # ~8x smaller than plain text
        self._stop = threading.Event()
        if enabled:
            part = 1
            while True:                     # claim the first free part name atomically (never append)
                p = part_path(config.TICKS_DIR, stem, part)
                try:
                    with open(p, "xb"):
                        pass
                    break
                except FileExistsError:
                    part += 1
            self.part, self.path = part, p
            self.meta = {"schema": SCHEMA, "apex": _apex_version(), "git": _git_short(), "src": source_hash(),
                         "cfg": config_hash(), "part": part}
            self.th = threading.Thread(target=self._run, name="Recorder", daemon=True)
            self.th.start()

    def put(self, kind: str, recv_ns: int, data):
        if not self.enabled:
            return
        try:
            self.q.put_nowait((kind, recv_ns, data))
        except queue.Full:
            self.dropped += 1

    def _line(self, f, k, t, d):
        f.write(json.dumps({"k": k, "t": t, "d": d}, separators=(",", ":"), default=str))
        f.write("\n")
        self.lines += 1

    def _run(self):
        with gzip.open(self.path, "wt", encoding="utf-8", compresslevel=3) as f:
            self._line(f, "meta", time.time_ns(), self.meta)
            f.flush()
            last_flush = time.monotonic()
            try:
                while not self._stop.is_set() or not self.q.empty():
                    try:
                        k, t, d = self.q.get(timeout=0.25)
                        self._line(f, k, t, d)
                    except queue.Empty:
                        pass
                    if time.monotonic() - last_flush > 1.0:
                        f.flush()
                        last_flush = time.monotonic()
            finally:                         # C-21: the drop count is part of the recording
                try:
                    self._line(f, "meta", time.time_ns(),
                               {"end": 1, "part": self.part, "dropped": self.dropped, "lines": self.lines + 1})
                except Exception:
                    pass
                f.flush()

    def stop(self):
        self._stop.set()
        if self.enabled:
            self.th.join(timeout=5)


def _apex_version():
    try:
        from . import __version__
        return __version__
    except Exception:
        return None
