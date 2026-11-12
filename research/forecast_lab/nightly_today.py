"""Scheduled entry for the nightly routine (Windows task "ApexForecastNightly", 16:30 Monday to Friday; docs/53).
A thin wrapper: it runs research/nightly_all.py, which takes the nightly lock, refuses market hours, waits for a
running replay, and then catches up every taped day after the last day in data/forecast_lab/ledger.jsonl, in
order (today only from 15:45). Everything goes to data/forecast_lab/nightly_<today>.log.

  py -3.13 research/forecast_lab/nightly_today.py            (extra arguments are passed to nightly_all.py)"""
import glob, json, os, subprocess, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DATA = os.environ.get('APEX_DATA') or os.path.join(ROOT, 'data')
LAB = os.path.join(DATA, 'forecast_lab')
TICKS = os.path.join(ROOT, 'data', 'ticks')
IST = timezone(timedelta(hours=5, minutes=30))
TODAY_AFTER = '15:45'            # today's tape may still be growing before this
CATCH_UP_MAX = 10                # days per run; the rest are left for the next run, in order


def taped_days(ticks=TICKS):
    return sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(ticks, '*.jsonl.gz'))})


def last_done(lab=LAB):
    """The last day the nightly has dealt with: the newest decision row or back-filled walk row in the ledger, else
    the live brain's trained_through, else None."""
    best = None
    try:
        with open(os.path.join(lab, 'ledger.jsonl'), encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict) and (r.get('kind') == 'decision' or (r.get('kind') == 'score' and r.get('walk'))):
                    if best is None or str(r.get('day')) > best:
                        best = str(r.get('day'))
    except FileNotFoundError:
        pass
    if best is None:
        try:
            with open(os.path.join(lab, 'brain.meta.json'), encoding='utf-8') as f:
                best = json.load(f).get('trained_through')
        except (OSError, ValueError):
            best = None
    return best


def missing_days(lab=LAB, ticks=TICKS, now=None, cap=CATCH_UP_MAX):
    """(days to run now in order, notes). Days after the last one done; today only after 15:45."""
    now = now or datetime.now(IST)
    today = now.strftime('%Y-%m-%d')
    last = last_done(lab)
    days = [d for d in taped_days(ticks) if last is None or d > last]
    if last is None:
        days = [d for d in days if d == today]             # nothing on record: never re-teach the whole history
    notes = []
    if today in days and now.strftime('%H:%M') < TODAY_AFTER:
        days.remove(today)
        notes.append(f'today ({today}) left for later: before {TODAY_AFTER} the session may still be running')
    if len(days) > cap:
        notes.append(f'{len(days) - cap} more day(s) left for the next run: ' + ', '.join(days[cap:]))
        days = days[:cap]
    return days, notes


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    day = datetime.now(IST).strftime('%Y-%m-%d')
    os.makedirs(LAB, exist_ok=True)
    log = os.path.join(LAB, f'nightly_{day}.log')
    env = dict(os.environ, PYTHONIOENCODING='utf-8', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    with open(log, 'a', encoding='utf-8') as f:
        f.write(datetime.now(IST).strftime('%H:%M:%S ') + 'starting research/nightly_all.py\n')
        f.flush()
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'research', 'nightly_all.py')] + argv,
                           cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
        f.write(datetime.now(IST).strftime('%H:%M:%S ') + f'finished with exit code {r.returncode}\n')
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
