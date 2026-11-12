"""One nightly runner for ApexOptions (12 Nov 2026; docs/53). Called by research/forecast_lab/nightly_today.py.

  - One run at a time: an OS lock on data/nightly.lock (the OS frees it if the process dies).
  - Refuses 09:00-15:40 on trading days unless --force, and a catch-up stops before the next day once that time is
    reached (the remaining days go to missed_days for the next run).
  - Never collides with a replay or the live Forecast Lab: while a replay manifest says "running" (and its folder
    changed in the last 45 minutes) or data/forecast_lab/live.lock is held, it waits, checking every 5 minutes, up
    to --max-wait-min (default 240); then it records "skipped: replay running". The same check runs before each step.
  - One thread, below-normal priority, a time limit on every step; it logs a planned end time from the last run.
  - Steps, in order, for each day to catch up (research/forecast_lab/nightly_today.missing_days), each skipped when
    its script is absent:
      1 lab             research/forecast_lab/nightly.py <day>          (the Forecast Lab nightly, rule PR-003)
      2 hazard          research/predict/nightly_hazard.py <day>
      3 label_parity    research/predict/label_parity.py <day>          (needs data/paper/forecasts_<day>.jsonl)
        lab_parity      research/forecast_lab/decision_card.py --parity <day>
      4 standard        research/conductor/standard_nightly.py <day>
      5 reprice         research/forecast_lab/reprice_study.py <day>
        straddle_clock  research/forecast_lab/straddle_clock.py <day>
      6 replay_parity   research/conductor/parity.py <day>              (only with the owner's standing OK)
    A failed lab step stops the catch-up (the days must be learned in order); the next run starts from that day.
  - Writes data/nightly_status.json {day, steps, missed_days, end_t, ...}; the Forecast Lab header shows it.
The owner's standing OK lives in data/nightly_owner_ok.json, e.g. {"online_walks": true, "replay_parity": true}.

  py -3.13 research/nightly_all.py [--force] [--max-wait-min N] [--day YYYY-MM-DD]"""
import glob, json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, 'forecast_lab'))
DATA = os.environ.get('APEX_DATA') or os.path.join(ROOT, 'data')
IST = timezone(timedelta(hours=5, minutes=30))
LOCK_AT = 1 << 20
POLL_S = 300
REPLAY_FRESH_S = 45 * 60
MARKET = ('09:00', '15:40')
DEFAULT_SECS = dict(lab=900, hazard=1200, label_parity=300, lab_parity=300, standard=900, reprice=600,
                    straddle_clock=300, replay_parity=3600)

# name, script (repo-relative), extra args before the day, time limit (s), files that must exist ({day}), owner OK key
STEPS = (
    ('lab', 'research/forecast_lab/nightly.py', (), 3 * 3600, (), None),
    ('hazard', 'research/predict/nightly_hazard.py', (), 3600, (), None),
    ('label_parity', 'research/predict/label_parity.py', (), 1800, ('data/paper/forecasts_{day}.jsonl', 'data/paper/outcomes_{day}.jsonl'), None),
    ('lab_parity', 'research/forecast_lab/decision_card.py', ('--parity',), 1800, (), None),
    ('standard', 'research/conductor/standard_nightly.py', (), 3600, (), None),
    ('reprice', 'research/forecast_lab/reprice_study.py', (), 1800, (), None),
    ('straddle_clock', 'research/forecast_lab/straddle_clock.py', (), 1800, (), None),
    ('replay_parity', 'research/conductor/parity.py', (), 3 * 3600, (), 'replay_parity'),
)


def now_ist():
    return datetime.now(IST)


def say(msg):
    print(now_ist().strftime('%H:%M:%S ') + str(msg), flush=True)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = f'{path}.tmp{os.getpid()}'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        say(f'WARNING: {path} unreadable ({type(e).__name__}); treated as missing')
        return None


# ── locks ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _lock_byte(fd, take):
    os.lseek(fd, LOCK_AT, os.SEEK_SET)
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_NBLCK if take else msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, (fcntl.LOCK_EX | fcntl.LOCK_NB) if take else fcntl.LOCK_UN)


class Lock:
    """An OS lock held for the life of the process; a dead process leaves no stale lock."""

    def __init__(self, path):
        self.path, self.fd = path, None

    def acquire(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            _lock_byte(fd, True)
        except OSError:
            os.close(fd)
            return False
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps(dict(pid=os.getpid(), started=now_ist().strftime('%Y-%m-%d %H:%M:%S'))).encode())
        self.fd = fd
        return True

    def release(self):
        if self.fd is None:
            return
        try:
            _lock_byte(self.fd, False)
        except OSError as e:
            say(f'lock release: {e}')
        os.close(self.fd)
        self.fd = None


def lock_held(path):
    """Is another process holding this OS lock? (probe: take and release at once)."""
    if not os.path.exists(path):
        return False
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return False
    try:
        _lock_byte(fd, True)
    except OSError:
        os.close(fd)
        return True
    try:
        _lock_byte(fd, False)
    except OSError as e:
        say(f'probe release of {path}: {e}')
    os.close(fd)
    return False


# ── what else is running ────────────────────────────────────────────────────────────────────────────────────────
def running_replays(batch=None, now=None, fresh_s=REPLAY_FRESH_S):
    """Replay runs whose manifest says running and whose folder changed recently (a crashed run's stale manifest
    is ignored and named)."""
    batch = batch or os.path.join(ROOT, 'data', 'replay', 'batch')
    now = time.time() if now is None else now
    live, stale = [], []
    for mp in glob.glob(os.path.join(batch, '*', 'manifest.json')):
        m = read_json(mp)
        if not isinstance(m, dict) or m.get('status') != 'running':
            continue
        run = os.path.dirname(mp)
        newest = 0.0
        for p in [mp] + [q for pat in ('*.out', '*.json', os.path.join('logs', '*'), os.path.join('paper', '*'),
                                       os.path.join('learning', '*')) for q in glob.glob(os.path.join(run, pat))]:
            try:
                newest = max(newest, os.path.getmtime(p))
            except OSError:
                pass
        (live if now - newest <= fresh_s else stale).append(os.path.basename(run))
    return sorted(live), sorted(stale)


def busy(data=None, batch=None, now=None):
    """Why the machine is not free for the nightly, or None."""
    live, _ = running_replays(batch, now)
    if live:
        return 'replay running: ' + ', '.join(live)
    if lock_held(os.path.join(data or DATA, 'forecast_lab', 'live.lock')):
        return 'the live Forecast Lab is running'
    return None


def wait_quiet(check, max_wait_s, poll_s=POLL_S, sleep=time.sleep, clock=time.time):
    """(ok, why): waits while check() names a reason, up to max_wait_s."""
    t0 = clock()
    why = check()
    while why:
        if clock() - t0 + poll_s > max_wait_s:
            return False, why
        say(f'waiting: {why}; next check in {poll_s // 60} min')
        sleep(poll_s)
        why = check()
    return True, None


def is_trading_day(d):
    try:
        sys.path.insert(0, ROOT)
        from apex import config as C
        return C.is_trading_day(d)
    except Exception as e:                         # reported: then weekdays count as trading days (the safe side)
        say(f'WARNING: holiday calendar not read ({type(e).__name__}: {e}); weekdays treated as trading days')
        return d.weekday() < 5


def market_hours(now):
    return is_trading_day(now.date()) and MARKET[0] <= now.strftime('%H:%M') < MARKET[1]


def below_normal():
    if sys.platform != 'win32':
        try:
            os.nice(5)
        except OSError as e:
            say(f'priority unchanged: {e}')
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        if not k.SetPriorityClass(k.GetCurrentProcess(), 0x4000):     # BELOW_NORMAL_PRIORITY_CLASS; children inherit
            say('priority unchanged: SetPriorityClass refused')
    except (OSError, AttributeError) as e:
        say(f'priority unchanged: {e}')


# ── the run ─────────────────────────────────────────────────────────────────────────────────────────────────────
def planned_secs(prev, names, n_days):
    hist = ((prev or {}).get('history') or {}) if isinstance(prev, dict) else {}
    return sum(float(hist.get(n, DEFAULT_SECS.get(n, 600))) for n in names) * max(n_days, 1)


def run_step(name, script, extra, day, limit, root=ROOT, env=None, runner=subprocess.run):
    path = os.path.join(root, script)
    t0 = time.time()
    try:
        r = runner([sys.executable, path, *extra, day], cwd=root, env=env, timeout=limit)   # output: inherited (the log)
    except subprocess.TimeoutExpired:
        return dict(status='fail', secs=round(time.time() - t0, 1), why=f'time limit {limit} s reached')
    secs = round(time.time() - t0, 1)
    if r.returncode != 0:
        return dict(status='fail', secs=secs, why=f'exit code {r.returncode}')
    return dict(status='ok', secs=secs, why=None)


def main(argv=None, now=None, data=None, root=ROOT, sleep=time.sleep, runner=subprocess.run, days=None, ticks=None,
         clock=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    data = data or DATA
    if clock is None:                              # a fixed start time (tests) keeps the per-day check at that time
        clock = (lambda: now) if now is not None else now_ist
    now = now or now_ist()
    force = '--force' in argv
    max_wait = int(argv[argv.index('--max-wait-min') + 1]) * 60 if '--max-wait-min' in argv else 240 * 60
    status_p = os.path.join(data, 'nightly_status.json')
    prev = read_json(status_p)
    st = dict(day=now.strftime('%Y-%m-%d'), started=now.strftime('%Y-%m-%d %H:%M:%S'), steps={}, missed_days=[],
              processed_days=[], outcome='running', end_t=None, notes=[],
              history=(prev or {}).get('history', {}) if isinstance(prev, dict) else {})

    def save(outcome=None):
        if outcome:
            st['outcome'] = outcome
            st['end_t'] = now_ist().strftime('%Y-%m-%d %H:%M:%S')
        write_json(status_p, st)
    lock = Lock(os.path.join(data, 'nightly.lock'))
    if not lock.acquire():
        say('another nightly run holds data/nightly.lock: nothing done')
        return 0
    try:
        if market_hours(now) and not force:
            say('refused: market hours (09:00-15:40 on a trading day); use --force to run anyway')
            save('refused: market hours')
            return 0
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        below_normal()
        ok, why = wait_quiet(lambda: busy(data, os.path.join(root, 'data', 'replay', 'batch')), max_wait, sleep=sleep)
        if not ok:
            say(f'skipped: {why}')
            save('skipped: ' + why)
            return 0
        if days is None:
            import nightly_today as NT
            lab_dir = os.path.join(data, 'forecast_lab')
            if '--day' in argv:
                days, notes = [argv[argv.index('--day') + 1]], []
            else:
                days, notes = NT.missing_days(lab_dir, ticks=ticks or NT.TICKS, now=now)
            st['notes'] += notes
        ok_owner = read_json(os.path.join(data, 'nightly_owner_ok.json')) or {}
        names = [s[0] for s in STEPS if os.path.exists(os.path.join(root, s[1])) and (s[5] is None or ok_owner.get(s[5]))]
        plan = planned_secs(prev, names, len(days))
        st['planned_end'] = (now_ist() + timedelta(seconds=plan)).strftime('%Y-%m-%d %H:%M:%S')
        say(f"days to run: {', '.join(days) or 'none'}; steps: {', '.join(names) or 'none'}; planned end {st['planned_end']}")
        for n in st['notes']:
            say(n)
        save()
        if not days:
            save('ok: nothing to do')
            return 0
        failed = False
        for i, day in enumerate(days):
            if failed:
                st['missed_days'].append(day)
                continue
            if not force and market_hours(clock()):          # a late start (a wake at 08:55) must not run into the session
                st['notes'].append(f'market hours began: {day} and later days left for the next run')
                say(st['notes'][-1])
                st['missed_days'].append(day)
                failed = True
                continue
            for name, script, extra, limit, needs, ok_key in STEPS:
                key = f'{day} {name}'
                if not os.path.exists(os.path.join(root, script)):
                    st['steps'][key] = dict(status='skip', secs=0, why=f'{script} not present')
                    continue
                if ok_key and not ok_owner.get(ok_key):
                    st['steps'][key] = dict(status='skip', secs=0, why=f'needs the owner\'s standing OK ("{ok_key}")')
                    continue
                miss = [n.format(day=day) for n in needs if not os.path.exists(os.path.join(root, n.format(day=day)))]
                if miss:
                    st['steps'][key] = dict(status='skip', secs=0, why='input missing: ' + ', '.join(miss))
                    continue
                q, qwhy = wait_quiet(lambda: busy(data, os.path.join(root, 'data', 'replay', 'batch')), max_wait, sleep=sleep)
                if not q:
                    st['steps'][key] = dict(status='skip', secs=0, why=qwhy)
                    if name == 'lab':
                        failed = True
                        break
                    continue
                say(f'step {name} for {day}')
                res = run_step(name, script, extra, day, limit, root, env, runner)
                st['steps'][key] = res
                if res['status'] == 'ok':
                    st['history'][name] = res['secs']
                say(f"step {name} for {day}: {res['status']}" + (f" ({res['why']})" if res['why'] else '') + f", {res['secs']} s")
                save()
                if name == 'lab' and res['status'] != 'ok':
                    failed = True
                    break
            if failed:
                st['missed_days'].append(day)
            else:
                st['processed_days'].append(day)
        fails = [k for k, v in st['steps'].items() if v['status'] == 'fail']
        save('ok' if not fails and not st['missed_days'] else ('failed: ' + ', '.join(fails) if fails else 'incomplete'))
        return 1 if fails else 0
    finally:
        lock.release()


if __name__ == '__main__':
    sys.exit(main())
