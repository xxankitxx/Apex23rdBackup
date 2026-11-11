"""11 Nov 2026 (docs/42, first block): replay with the repaired forecast books (the scored contract is the bought
contract, model_v2 lines, held contracts covered). One tape per run folder p42_<mmdd>, all in parallel, the recorder
off. The days are the LAST TEN sessions (27 Oct to 9 Nov), fixed before the run: ten is what fits before the
11 Nov open on 8 cores. Anything unfinished at the deadline is stopped, so nothing overlaps the live session.

Usage: py -3.13 run_p42.py [HH:MM deadline, default 08:15]"""
import datetime, os, subprocess, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
DAYS = ['2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05',
        '2026-11-06', '2026-11-09']
hh, mm = (sys.argv[1] if len(sys.argv) > 1 else '08:15').split(':')
deadline = datetime.datetime.now().replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
procs = {}
for d in DAYS:
    tape = os.path.join(ROOT, 'data', 'ticks', d + '.jsonl.gz')
    assert os.path.isfile(tape), tape
    rid = 'p42_' + d[5:7] + d[8:10]
    log = open(os.path.join(ROOT, 'data', 'replay', 'batch', rid + '.launch.log'), 'w')
    procs[d] = subprocess.Popen([sys.executable, '-m', 'apex.replay_batch', tape, '--run-id', rid, '--seed', 'data'],
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
