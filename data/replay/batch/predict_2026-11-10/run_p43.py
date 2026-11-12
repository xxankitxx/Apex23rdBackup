"""11 Nov 2026, evening (docs/50): the overnight replay p43. All 16 recorded sessions (19 Oct to 11 Nov) on the code
frozen for 12 Nov: chronological hazard artefacts through the registry (a session is forecast only by a model fitted
on earlier sessions; the first five have none and the forecast books stay silent), the exact-contract forecast books,
the re-entry twin rx_c20_9y, 106 books, and the MISSED-SIGNAL RECORDER ON (the champion's untraded triggers, for the
admission model). Resource plan, stated before the run: 8 runs at a time (8 physical cores), each run two tapes one
after the other; started in the evening; anything unfinished at the deadline is stopped so nothing overlaps the
12 Nov live session.

Usage: py -3.13 run_p43.py [HH:MM deadline, default 08:10]"""
import datetime, os, subprocess, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
GROUPS = [['2026-10-19', '2026-10-30'], ['2026-10-21', '2026-11-02'], ['2026-10-22', '2026-11-03'], ['2026-10-23', '2026-11-04'],
          ['2026-10-26', '2026-11-05'], ['2026-10-27', '2026-11-06'], ['2026-10-28', '2026-11-09'], ['2026-10-29', '2026-11-11']]
hh, mm = (sys.argv[1] if len(sys.argv) > 1 else '08:10').split(':')
deadline = datetime.datetime.now().replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
if deadline < datetime.datetime.now():
    deadline += datetime.timedelta(days=1)
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
procs = {}
for g, days in enumerate(GROUPS, 1):
    tapes = [os.path.join(ROOT, 'data', 'ticks', d + '.jsonl.gz') for d in days]
    for tp in tapes:
        assert os.path.isfile(tp), tp
    rid = f'p43_g{g}'
    log = open(os.path.join(ROOT, 'data', 'replay', 'batch', rid + '.launch.log'), 'w')
    procs[' '.join(days)] = subprocess.Popen([sys.executable, '-m', 'apex.replay_batch'] + tapes + ['--run-id', rid, '--seed', 'data', '--record-missed'],
                                            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    time.sleep(2)                       # each run takes its own port from its process id
print('started', len(procs), 'runs at', time.strftime('%H:%M:%S'), 'deadline', deadline.strftime('%H:%M'), flush=True)
while any(p.poll() is None for p in procs.values()) and datetime.datetime.now() < deadline:
    time.sleep(30)
for d, p in procs.items():
    if p.poll() is None:
        subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)   # this run and its children only
        print('STOPPED at the deadline, not finished:', d, flush=True)
    else:
        print('finished', d, 'exit', p.returncode, flush=True)
print('done at', time.strftime('%H:%M:%S'), flush=True)
