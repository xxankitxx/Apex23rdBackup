"""
ApexOptions — one entry point.  PAPER TRADING ONLY: no order is ever sent.

  python run_apex.py session  [--profile p2]     save today's Breeze session token (once a day)
  python run_apex.py preflight [--profile p2]    checks before the open: GO / NO-GO
  python run_apex.py live     [--profile p2]     live data from Breeze, paper trades
  python run_apex.py sim      [--speed 10] [--days 1] [--seed 7] [--record] [--continue]
                                                 synthetic market, no login (try it now);
                                                 every run starts fresh at ₹1,00,000 in its own
                                                 folder data/sim/<YYYYmmdd-HHMMSS>/ (--continue
                                                 resumes the most recent run instead)
  python run_apex.py replay data/ticks/2026-10-19.jsonl.gz [--speed 10]
  python run_apex.py acceptance data/ticks/2026-10-19.jsonl.gz [--fast]   replay + behaviour checks (D-119): PASS before any
                                                 code change trades live
  python run_apex.py learn  [--mode m | --dir D] re-run the after-close learning step
  python run_apex.py report [--mode m | --dir D] print today's paper trades + learning report

Dashboard: http://127.0.0.1:8780   (MYTHOS keeps 8765; both can run together)

The supervisor creates the shared memory, starts FEED, ENGINE and GATEWAY as
separate processes, restarts the live feed if it dies, and on Ctrl+C asks
everything to stop cleanly (books are saved, the day is learned after the close).
Every sim run gets its own folder data/sim/<YYYYmmdd-HHMMSS>/ (a fresh ₹1,00,000 and a
fresh learning state; --continue resumes the latest), and every replay run gets
its own folder data/replay/<file-stem>/<YYYYmmdd-HHMMSS>/ (printed at start), so a
second replay of the same day never stacks on the first (C-20) and neither ever
touches the live paper account's record.  learn/report --dir <that folder>.
"""
import argparse
import getpass
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def data_dir_for(mode):
    if mode == "live":
        return os.path.join(ROOT, "data")
    return os.path.join(ROOT, "data", mode)


def sim_run_dir(resume=False, stamp=None):
    """data/sim/<YYYYmmdd-HHMMSS>/ — one fresh folder per simulator run, so a new run never reloads the
    last run's paper books (the simulator always plays the same date, so books saved under that date
    used to be reloaded and capital carried over from run to run). resume=True reuses the latest run."""
    base = data_dir_for("sim")
    if resume:
        last = latest_sim_dir()
        if last:
            return last
    return os.path.join(base, stamp or time.strftime("%Y%m%d-%H%M%S"))


def latest_sim_dir():
    """The most recent sim run folder (names sort by time), or None."""
    base = data_dir_for("sim")
    try:
        runs = sorted(d for d in os.listdir(base)
                      if len(d) == 15 and d[8] == "-" and d.replace("-", "").isdigit()
                      and os.path.isdir(os.path.join(base, d)))
    except OSError:
        return None
    return os.path.join(base, runs[-1]) if runs else None


def replay_run_dir(path, stamp=None):
    """data/replay/<file-stem>/<YYYYmmdd-HHMMSS>/ — one fresh folder per replay run (C-20)."""
    stem = os.path.basename(path)
    for ext in (".gz", ".jsonl", ".json"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
    stamp = stamp or time.strftime("%Y%m%d-%H%M%S")
    return os.path.join(data_dir_for("replay"), stem or "replay", stamp)


def child_env(mode, data_dir=None):
    env = dict(os.environ)
    env["APEX_DATA"] = data_dir or data_dir_for(mode)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def spawn(module, args, mode, data_dir=None):
    return subprocess.Popen([sys.executable, "-m", module] + args, cwd=ROOT, env=child_env(mode, data_dir))


STALE_S = 10.0          # a heartbeat older than this in market hours is reported (C-08)
STALE_GRACE_S = 60.0    # a process that has not beaten at all yet gets this long (login, registry)
STALE_EVERY_S = 60.0    # ... and each warning repeats at most once a minute


def stale_report(now_ns, engine_hb_ns, feed_hb_ns, started_ns):
    """[(name, age_s)] for every heartbeat that is stale. A heartbeat of 0 (never beat)
    is measured from the supervisor start and only after STALE_GRACE_S."""
    out = []
    for name, hb in (("ENGINE", engine_hb_ns), ("FEED", feed_hb_ns)):
        hb = int(hb or 0)
        if hb > 0:
            age = (now_ns - hb) / 1e9
            if age > STALE_S:
                out.append((name, age))
        else:
            age = (now_ns - started_ns) / 1e9
            if age > STALE_GRACE_S:
                out.append((name, age))
    return out


def in_market_hours(config, now):
    return (config.is_trading_day(now.date())
            and config.mins(config.MARKET_OPEN) <= config.hm(now) <= config.mins(config.MARKET_CLOSE))


def wait_for(p, deadline):
    while p.poll() is None and time.time() < deadline:
        time.sleep(0.2)
    return p.poll() is not None


FEED_STOP_S = 12.0      # the feed gets this long to stop cleanly ...
ENGINE_STOP_S = 20.0    # ... then the engine gets its OWN deadline (books + learning, C-09)
FEED_RESET_S = 600.0    # a feed that has run this long resets the restart counter (C-78)


def stop_children(procs, say=print, feed_s=None, engine_s=None):
    """After ctrl.stop is set: wait for the feed, then give the engine its own deadline,
    and only then terminate whatever is still running (gateway, a hung child)."""
    feed_s = FEED_STOP_S if feed_s is None else feed_s
    engine_s = ENGINE_STOP_S if engine_s is None else engine_s
    try:
        if "feed" in procs:
            wait_for(procs["feed"], time.time() + feed_s)
        if "engine" in procs and not wait_for(procs["engine"], time.time() + engine_s):
            say(f"ENGINE did not stop within {engine_s:.0f} s — terminating it")
    except KeyboardInterrupt:              # a second Ctrl+C: stop waiting, still clean up
        say("second Ctrl+C — terminating without waiting")
    for p in procs.values():
        if p.poll() is None:
            p.terminate()
    for p in procs.values():
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


def supervise(mode, feed_args, speed=1.0, open_browser=True, data_dir=None):
    data_dir = data_dir or data_dir_for(mode)
    os.environ["APEX_DATA"] = data_dir
    from apex import config
    from apex.table import StateBlob, Table
    if mode == "live" and not config.is_trading_day(config.now_ist().date()):
        print(f"\n  WARNING: today ({config.now_ist().date()}) is an NSE holiday / not a trading day — "
              "no market data will arrive (C-92).\n", flush=True)
    if mode in ("replay", "sim"):
        print(f"  {mode} run folder: {data_dir}", flush=True)
    if port_busy(config.PORT):
        sys.exit(f"Port {config.PORT} is busy — is another ApexOptions running?")
    try:
        t = Table(create=True)
        b = StateBlob(create=True)
    except FileExistsError:
        sys.exit("Another ApexOptions process still holds the shared memory — close the old console (Task Manager: python.exe) and retry.")
    t.set("speed", speed)
    feed_mod = {"live": "apex.feed_breeze", "sim": "apex.feed_sim", "replay": "apex.feed_replay"}[mode]
    procs = {
        "feed": spawn(feed_mod, feed_args, mode, data_dir),
        "engine": spawn("apex.engine_main", [mode], mode, data_dir),
        "gateway": spawn("apex.gateway", [], mode, data_dir),
    }
    started_ns = time.time_ns()
    feed_started = time.time()
    last_warn = {}
    try:
        slog = open(os.path.join(config.LOG_DIR, "supervisor.log"), "a", encoding="utf-8")
    except Exception:
        slog = None

    def say(msg):
        line = f"{time.strftime('%H:%M:%S')} SUPERVISOR {msg}"
        print(line, flush=True)
        try:
            slog.write(line + "\n"); slog.flush()
        except Exception:
            pass
    url = f"http://{config.HOST}:{config.PORT}"
    print(f"\n  ApexOptions [{mode.upper()} · PAPER]  dashboard: {url}\n  Ctrl+C to stop.\n", flush=True)
    if open_browser:
        time.sleep(1.5)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    restarts = 0
    try:
        while True:
            time.sleep(1.0)
            if procs["engine"].poll() is not None:
                if mode == "live":
                    print("ENGINE exited — restarting (books are on disk)", flush=True)
                    procs["engine"] = spawn("apex.engine_main", [mode], mode, data_dir)
                else:
                    break                       # sim/replay finished and learned
            if procs["gateway"].poll() is not None:
                procs["gateway"] = spawn("apex.gateway", [], mode, data_dir)
            if mode == "live" and restarts and time.time() - feed_started >= FEED_RESET_S:
                restarts = 0                    # a feed that has stayed up 10 min starts afresh
            if procs["feed"].poll() is not None and mode == "live":
                restarts += 1
                if restarts > 20:
                    print("FEED keeps dying — see data/logs/feed.log", flush=True)
                    time.sleep(30)
                print(f"FEED exited (code {procs['feed'].returncode}) — restarting", flush=True)
                time.sleep(min(5 * restarts, 60))
                procs["feed"] = spawn(feed_mod, feed_args, mode, data_dir)
                feed_started = time.time()
            if mode == "live":
                # warn only (C-08): no auto-restart on a stale heartbeat yet
                try:
                    if in_market_hours(config, config.now_ist()):
                        for name, age in stale_report(time.time_ns(), t.c("engine_hb_ns"),
                                                      t.c("feed_hb_ns"), started_ns):
                            if time.time() - last_warn.get(name, 0.0) >= STALE_EVERY_S:
                                last_warn[name] = time.time()
                                say(f"{name} STALE {age:.0f} s — heartbeat not advancing (see data/logs/{name.lower()}.log)")
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\nstopping…", flush=True)
    finally:
        t.set("stop", 1)
        # the feed first, then the engine on its OWN deadline: the engine saves the books and
        # writes the learning record after the feed is gone, and nothing is terminated
        # before the engine has had its full time (C-09)
        stop_children(procs, say)
        t.close(); b.close(); t.unlink(); b.unlink()
        try:
            slog.close()
        except Exception:
            pass
        print(f"stopped. Paper books: {os.path.join(data_dir, 'paper')}", flush=True)


def port_busy(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return False
    except OSError:
        return True
    finally:
        s.close()


# ── session ────────────────────────────────────────────────────────────────
def cmd_session(profile):
    from apex import config
    name = f"breeze_{profile}.json" if profile else "breeze.json"
    path = os.path.join(config.SECRETS_DIR, name)
    c = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    if not c.get("api_key"):
        c["api_key"] = getpass.getpass("Breeze API key (hidden): ").strip()
        c["api_secret"] = getpass.getpass("Breeze API secret (hidden): ").strip()
    login = "https://api.icicidirect.com/apiuser/login?api_key=" + urllib.parse.quote_plus(c["api_key"])
    print("\nLog in here (the browser opens it), then copy the API_Session value from the address bar:\n  " + login)
    try:
        webbrowser.open(login)
    except Exception:
        pass
    tok = input("\nSession token: ").strip()
    m = re.search(r"apisession=(\w+)", tok, re.I)
    c["session_token"] = m.group(1) if m else tok
    os.makedirs(config.SECRETS_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(c, f)
    print(f"saved to {path} (gitignored, never committed). Now: python run_apex.py preflight"
          + (f" --profile {profile}" if profile else ""))


# ── preflight ──────────────────────────────────────────────────────────────
# C-32: the key may be quoted (JSON: "api_key": "..."), the value may be unquoted (.env) and
# may contain / = . (base64-ish); PLACEHOLDER is tested on the VALUE only.
KEYLIKE = re.compile(r"""(?i)["']?(api_?key|api_?secret|session_?token)["']?\s*[:=]\s*["']?([^\s"',]{8,})""")
# obvious stand-ins quoted in docs/research notes (e.g. api_key="sk-no-key-required") are not leaks
PLACEHOLDER = re.compile(r"no-?key|your[_-]?|xxx|example|placeholder|dummy|change ?me|sample|redacted|<[^>]*>|\.\.\.", re.I)
SCAN_SKIP = {"secrets", "data", "logs", ".git", "__pycache__"}
# exact (file, value) pairs known to be test vectors, not credentials: the council report
# quotes the scanner's own test string. Anything else in that file is still reported.
SCAN_ALLOW = {("docs/07_COUNCIL_REPORT.md", "abc/def=ghi.jkl")}
SCAN_EXT = (".py", ".md", ".json", ".js", ".html", ".txt", ".cfg", ".ini",
            ".yml", ".yaml", ".toml", ".env", ".ps1", ".bat", ".csv", ".ipynb")


def credential_hits(text):
    """The values in text that look like a real credential (not a doc stand-in)."""
    return [m.group(2) for m in KEYLIKE.finditer(text) if not PLACEHOLDER.search(m.group(2))]


def scan_credentials(root=ROOT):
    """Files under root (relative paths) holding credential-shaped strings. Only the
    TOP-LEVEL folder of each path decides a skip (C-75): a checkout under ...\\data\\...
    is still scanned, and .github is not mistaken for .git."""
    leaks = []
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        if rel != "." and rel.split(os.sep)[0] in SCAN_SKIP:
            dn[:] = []
            continue
        for f in fn:
            if f.endswith(SCAN_EXT) or f == ".env" or f.startswith(".env."):
                try:
                    with open(os.path.join(dp, f), encoding="utf-8", errors="ignore") as fh:
                        relf = os.path.normpath(os.path.join(rel, f)).replace(os.sep, "/")
                        if any((relf, v) not in SCAN_ALLOW for v in credential_hits(fh.read())):
                            leaks.append(relf)
                except Exception:
                    pass
    return leaks


def gitignore_ok(root=ROOT):
    """secrets/, data/ and logs/ are all ignored: `git check-ignore` when git is there,
    otherwise a look at .gitignore."""
    try:
        r = [subprocess.run(["git", "-C", root, "check-ignore", "-q", p], capture_output=True,
                            timeout=10).returncode for p in ("secrets/x", "data/x", "logs/x")]
        if all(c in (0, 1) for c in r):          # 128 = not a repository / git error -> fall back
            return all(c == 0 for c in r)
    except Exception:
        pass
    gi = os.path.join(root, ".gitignore")
    try:
        text = open(gi, encoding="utf-8").read()
    except Exception:
        return False
    lines = {ln.strip().strip("/") for ln in text.splitlines()}
    return {"secrets", "data", "logs"} <= lines


def cmd_preflight(profile):
    from apex import config
    res = []

    def check(name, ok, note=""):
        res.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + note) if note else ''}")

    print("ApexOptions preflight (paper mode)\n")
    probs = config.validate()
    check("configuration self-check", not probs, "; ".join(probs) if probs else "")
    # wsproto: the gateway's websocket backend (uvicorn ws="wsproto"); truststore: Windows-store
    # TLS trust for the live stream.  Both are in requirements.txt; a missing one is a real FAIL
    # (an earlier version printed PASS for a missing truststore, which hid the problem).
    for mod in ("numpy", "fastapi", "uvicorn", "wsproto", "breeze_connect", "truststore"):
        try:
            __import__(mod)
            check(f"python package {mod}", True)
        except Exception:
            check(f"python package {mod}", False, f"pip install {mod}   (or: pip install -r requirements.txt)")
    now = config.now_ist()
    gaps = config.holiday_coverage_gaps(now)
    check("NSE holiday calendar covers today .. the farthest expiry", not gaps,
          f"no NSE_HOLIDAYS entries for {', '.join(map(str, gaps))} — add them to config.NSE_HOLIDAYS" if gaps else "")
    trading = config.is_trading_day(now.date())
    check("today is a trading day (for live)", trading,
          "" if trading else f"{now.date()} is an NSE holiday / not a trading day — live would get no market data")
    w = config.weekly_expiries(now, 2)
    check("weekly expiries", len(w) == 2, f"{w[0]} and {w[1]}" if len(w) == 2 else "")
    leaks = scan_credentials(ROOT)
    check("no credential-shaped strings outside secrets/", not leaks, ", ".join(leaks))
    check(".gitignore excludes secrets/, data/ and logs/", gitignore_ok(ROOT))
    check(f"port {config.PORT} free", not port_busy(config.PORT))
    trust = "n/a"
    try:
        from apex.feed_breeze import install_trust
        trust = install_trust()
    except Exception as e:
        trust = str(e)
    # (the fallback text mentions 'truststore' too — test the prefix, not a substring)
    check("TLS trust", trust.startswith("truststore"), trust)
    for host in ("api.icicidirect.com", "livestream.icicidirect.com"):
        try:
            import ssl
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=6) as s:
                with ctx.wrap_socket(s, server_hostname=host):
                    pass
            check(f"TLS handshake {host}", True)
        except Exception as e:
            check(f"TLS handshake {host}", False, str(e)[:120])
    try:
        from apex.feed_breeze import load_credentials
        c = load_credentials(profile)
        check("credentials file", True, "secrets/" + (f"breeze_{profile}.json" if profile else "breeze.json"))
        br = None
        try:
            from breeze_connect import BreezeConnect
            br = BreezeConnect(api_key=c["api_key"])
            # paper-only interlock (C-33): order-like methods raise, and only data endpoints
            # (customerdetails, SecurityMaster.zip, quotes, optionchain, ...) may be requested
            from apex import interlock
            interlock.install(br)
            interlock.patch_requests()
            br.generate_session(api_secret=c["api_secret"], session_token=c["session_token"])
            check("Breeze session valid today", True)
        except Exception as e:
            check("Breeze session valid today", False, f"{str(e)[:100]} — run: python run_apex.py session")
        if br is not None:
            # the contracts the feed must resolve offline (the SDK returns '4.1!False' for unknown ones)
            br.interval = ""
            w0 = config.weekly_expiries(now, 1)[0]
            mexp = config.monthly_expiry(now)
            probes = [("NIFTY index", dict(exchange_code="NSE", stock_code="NIFTY")),
                      ("NIFTY futures " + config.ws_expiry(mexp), dict(exchange_code="NFO", stock_code="NIFTY", product_type="futures", expiry_date=config.ws_expiry(mexp))),
                      ("HDFC Bank cash (HDFBAN)", dict(exchange_code="NSE", stock_code="HDFBAN"))]
            spot = 0.0
            try:
                r = br.get_quotes(stock_code="NIFTY", exchange_code="NSE", product_type="cash", expiry_date="", right="", strike_price="")
                rows = (r or {}).get("Success") or []
                spot = float(rows[0].get("ltp") or 0) or float(rows[0].get("previous_close") or 0) if rows else 0.0
            except Exception:
                pass
            check("NIFTY quote by REST", spot > 0, f"{spot:.1f}" if spot else "no ltp/previous_close in response")
            if spot > 0:
                atm = round(spot / config.STRIKE_STEP) * config.STRIKE_STEP
                probes.append((f"NIFTY {int(atm)} CE {config.ws_expiry(w0)}",
                               dict(exchange_code="NFO", stock_code="NIFTY", product_type="options", expiry_date=config.ws_expiry(w0), strike_price=str(int(atm)), right="call")))
            for name, kw in probes:
                try:
                    r = br.get_stock_token_value(get_exchange_quotes=True, get_market_depth=False, **kw)
                    ok = isinstance(r, tuple) and r[0] and "False" not in str(r[0])
                    check(f"token: {name}", bool(ok), str(r[0]) if ok else f"not in the security master ({str(r)[:60]})")
                except Exception as e:
                    check(f"token: {name}", False, str(e)[:80])
            # The SDK's ws_connect() reports every failure as 'Failed to connect to live stream'.
            # Do the same handshake in two visible steps instead, keeping the real error text.
            from apex.feed_breeze import connect_stream, drop_stream, stream_hint, stream_probe, stream_versions
            try:
                check("stream libraries", True, stream_versions())
            except Exception as e:
                check("stream libraries", False, str(e)[:120])
            proxies = sorted(k for k in os.environ if k.lower() in ("https_proxy", "http_proxy", "all_proxy", "wss_proxy"))
            if proxies:
                print(f"         note: proxy variables set ({', '.join(proxies)}) — the websocket goes through that proxy too")
            try:
                ok, det = stream_probe()
            except Exception as e:
                ok, det = False, f"{type(e).__name__}: {str(e)[:140]}"
            hint = stream_hint(det) if not ok else ""
            check("livestream engine.io handshake (raw websocket)", ok, det + (f" → {hint}" if hint else ""))
            if ok:
                try:
                    connect_stream(br)
                    check("websocket connect + auth (livestream)", True)
                except Exception as e:
                    det = str(e)[:160]
                    hint = stream_hint(det)
                    check("websocket connect + auth (livestream)", False, det + (f" → {hint}" if hint else ""))
                finally:
                    drop_stream(br)
            else:
                check("websocket connect + auth (livestream)", False, "skipped — the raw handshake above failed first")
    except SystemExit as e:
        check("credentials file", False, str(e))
    ok = all(res)
    go = "GO — start with:  python run_apex.py live" + (f" --profile {profile}" if profile else "")
    print("\n  " + (go if ok else "NO-GO — fix the FAIL lines above"))
    return ok


def _mode_dir(mode, data_dir):
    if data_dir:
        return os.path.abspath(data_dir)
    if mode == "sim":
        return latest_sim_dir() or data_dir_for("sim")
    return data_dir_for(mode)


def cmd_learn(mode, force=False, data_dir=None):
    os.environ["APEX_DATA"] = _mode_dir(mode, data_dir)
    from apex import config
    from apex.engine import learning
    day = config.now_ist().date().isoformat()
    if learning.already_learned(day) and not force:
        print(f"{day} was already learned; the report is below. Use --force to re-run (streaks and "
              f"promotions move only once per evening either way).")
        print(open(learning.REPORT, encoding="utf-8").read())
        return learning.load_state()
    s = learning.learn(day)
    print(open(learning.REPORT, encoding="utf-8").read())
    return s


def cmd_report(mode, data_dir=None):
    os.environ["APEX_DATA"] = _mode_dir(mode, data_dir)
    from apex import config
    from apex.engine import learning
    paper = os.path.join(config.DATA_DIR, "paper")
    files = sorted(f for f in os.listdir(paper) if f.startswith("trades_")) if os.path.isdir(paper) else []
    if files:
        print(f"== {files[-1]} ==")
        print(open(os.path.join(paper, files[-1]), encoding="utf-8").read())
    if os.path.exists(learning.REPORT):
        print(open(learning.REPORT, encoding="utf-8").read())


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="ApexOptions (paper trading)")
    ap.add_argument("cmd", choices=["live", "sim", "replay", "acceptance", "session", "preflight", "learn", "report"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--profile", default="", help="second Breeze account: secrets/breeze_<profile>.json")
    ap.add_argument("--speed", type=float, default=10.0)
    ap.add_argument("--fast", action="store_true", help="replay: single-process lock-step replay (T02), same books, 5-10x faster")
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--gap", default="", help="sim drill: feed outage START_SOD,SECONDS,JUMP_PTS (e.g. 37800,40,30)")
    ap.add_argument("--continue", dest="resume", action="store_true",
                    help="sim: resume the most recent sim run (its capital and books) instead of a fresh one")
    ap.add_argument("--force", action="store_true", help="learn: re-run even if today was already learned")
    ap.add_argument("--mode", default="live", help="for learn/report: live | sim | replay")
    ap.add_argument("--dir", default="", help="for learn/report: a run folder, e.g. data/replay/<day>/<stamp>")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    if a.cmd == "session":
        cmd_session(a.profile)
    elif a.cmd == "preflight":
        sys.exit(0 if cmd_preflight(a.profile) else 1)
    elif a.cmd == "learn":
        if a.dir and not os.path.isdir(a.dir):
            sys.exit(f"--dir {a.dir}: no such folder")
        cmd_learn(a.mode, a.force, a.dir or None)
    elif a.cmd == "report":
        if a.dir and not os.path.isdir(a.dir):
            sys.exit(f"--dir {a.dir}: no such folder")
        cmd_report(a.mode, a.dir or None)
    elif a.cmd == "live":
        supervise("live", [a.profile] if a.profile else [], 1.0, not a.no_browser)
    elif a.cmd == "sim":
        args = ["--speed", str(a.speed), "--days", str(a.days), "--seed", str(a.seed)] + (["--record"] if a.record else [])
        if a.gap:
            args += ["--gap", a.gap]
        supervise("sim", args, a.speed, not a.no_browser, data_dir=sim_run_dir(resume=a.resume))
    elif a.cmd == "acceptance":
        # D-119 (council 4, m27): replay a recorded day lock-step, then the behaviour checks of apex/acceptance.py
        if not a.file or not os.path.exists(a.file):
            sys.exit("acceptance needs a recorded file, e.g. data/ticks/2026-10-19.jsonl.gz")
        run_dir = replay_run_dir(a.file)
        if a.fast:                                   # council 5 T02: the single-process replay, same books, ~3x faster
            os.environ["APEX_DATA"] = run_dir
            os.environ["APEX_FAST"] = "1"
            print(f"  replay run folder: {run_dir}  (fast, single process)", flush=True)
            sys.argv = ["apex.replay_fast", os.path.abspath(a.file)]
            from apex import replay_fast
            replay_fast.main()
        else:
            supervise("replay", [os.path.abspath(a.file), "--speed", "1000"], 1000.0, False, data_dir=run_dir)
        from apex import acceptance
        fails, notes = acceptance.check_run(run_dir)
        print("\n".join(notes))
        print("\nACCEPTANCE: " + ("FAIL" if fails else "PASS (behaviour only — not a profit claim)"))
        for f in fails:
            print("  - " + f)
        sys.exit(1 if fails else 0)
    elif a.cmd == "replay" and a.fast:
        # T02 (council 5): feed + engine in one process, same lock-step boundaries, identical books, 5-10x faster
        if not a.file:
            sys.exit("replay needs a recorded file, e.g. data/ticks/2026-10-19.jsonl.gz")
        run_dir = replay_run_dir(a.file)
        os.environ["APEX_DATA"] = run_dir
        os.environ["APEX_FAST"] = "1"
        print(f"  replay run folder: {run_dir}  (fast, single process{', dashboard on' if not a.no_browser else ''})", flush=True)
        sys.argv = ["apex.replay_fast", os.path.abspath(a.file)] + ([] if a.no_browser else ["--gateway"])
        from apex import replay_fast
        replay_fast.main()
    elif a.cmd == "replay":
        if not a.file or not os.path.exists(a.file):
            sys.exit("replay needs a recorded file, e.g. data/ticks/2026-10-19.jsonl.gz")
        supervise("replay", [os.path.abspath(a.file), "--speed", str(a.speed)], a.speed, not a.no_browser,
                  data_dir=replay_run_dir(a.file))


if __name__ == "__main__":
    main()
