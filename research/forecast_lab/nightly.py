"""Forecast Lab nightly routine for ONE day D (docs/53; rule PR-003 in research/preregistry.jsonl). 12 Nov 2026.

It judges which volatility procedure the live Lab should run, using only days the models had not seen:

  1. tape -> research format (ds_v2) for every part of D not converted yet, then collect D through the lab.
  2. CONTESTANTS, each fitted strictly before D and scored on D:
       P-incumbent   the brain file that was live during D
       P-candidate   the brain fitted on every session up to D-1 (the refit-every-night procedure)
       P-plain-cal   the 10-minute clock x exp(intercept + 25-bucket time-of-day table shrunk to the mean),
                     fitted on the earlier sessions only (offline only: the live Lab cannot run it yet)
       P-clock       the plain 10-minute clock (reference)
       P-harp        only when research/forecast_lab/har_plus.py provides nightly_contestant() (forward only)
     Offline scores come straight from the collected arrays. With the owner's standing OK
     (data/nightly_owner_ok.json {"online_walks": true}) the brains and the plain Lab (P-plain) are also run through
     a one-session tape walk with the online layers on, because live kappa absorbs bias an offline score misreads.
  3. Scores, as SUMS per horizon (so days can be pooled): the 80 % interval (Winkler) score of the futures move
     (primary, at 5 min), coverage, width, pinball over the five quantiles, QLIKE raw and with the mean correction
     c_h = mean(RV / forecast) measured on the contestant's own training sessions, n; 30-minute block sums at 5 min;
     the days-to-expiry stratum. Online walks add the option side (band coverage, pinball, middle error against "no
     change", the profit-chance Brier against its base rate).
  4. One row per (day, procedure, basis) goes to data/forecast_lab/ledger.jsonl, then one decision row.
  5. PR-003. Fast-off: when the live brain loses to the plain clock on the primary score on 4 or more of the last 5
     days with a score, use_brain.json is written {"use": false} and the Lab runs without the trained layer from its
     next minute. Slow-on and switch are PROPOSED only (the owner promotes): the 90 % day-block bootstrap interval
     (2,000 draws) of the mean daily log-ratio must exclude 0 over at least 10 common forward days, with at least 4 of
     7 horizons better.
  6. Held-out check, in place of the old in-sample sanity check: the candidate fitted through D-1 must have finite
     weights and its 80 % range must catch 65-95 % on D. Passed (refit procedure): the brain fitted through D is
     installed. Failed: it is not installed, and if the failed model is the live one, brain_prev is put back.

Brains are archived as data/forecast_lab/brains/archive/brain_<trained through>_<hash>.joblib, written as a temp
file, checked to load with the same hash, then renamed; an archived file is never overwritten. brain.joblib and
brain.meta.json are replaced the same way. A brain trained through D or later is never copied into brain_prev.
A second run for a day that already has a decision row does nothing (use --force to redo it).

  py -3.13 research/forecast_lab/nightly.py 2026-11-12                 one day (normally called by nightly_all.py)
  py -3.13 research/forecast_lab/nightly.py 2026-11-12 --check-only    score and print; nothing written
  py -3.13 research/forecast_lab/nightly.py 2026-11-12 --force         redo a day that is already done
  py -3.13 research/forecast_lab/nightly.py --set-procedure refit|hold|plain|brain-on --why "..."   the owner's switch
Options: --no-convert (skip tape conversion and collect), --online / --no-online (override the standing OK)."""
import glob, hashlib, json, math, os, shutil, subprocess, sys, time
from datetime import datetime, timedelta, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
ENV = dict(os.environ, PYTHONIOENCODING='utf-8', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')   # before train.py
LIVE_DATA = os.path.join(ROOT, 'data')
DATA = os.environ.get('APEX_DATA') or LIVE_DATA
LAB = os.path.join(DATA, 'forecast_lab')
IST = timezone(timedelta(hours=5, minutes=30))

from apex.forecast_lab import brain as B  # noqa: E402  (numpy only; not part of the engine)

H = B.H
PRIMARY_H = 300
QS = (0.10, 0.25, 0.50, 0.75, 0.90)
ZN = (-1.2815516, -0.6744898, 0.0, 0.6744898, 1.2815516)       # normal quantiles for the plain clock
K_TOD = 180.0            # time-of-day shrinkage: one session's origins in a 15-minute bucket (fixed in advance)
HOLD_COVER = (0.65, 0.95)  # held-out 80 % coverage must fall inside the drift-alarm bounds (design targets)
FAST_OFF_N, FAST_OFF_LOSSES = 5, 4
SLOW_MIN_DAYS, BOOT_DRAWS, BOOT_LEVEL, MIN_H_BETTER, BOOT_SEED = 10, 2000, 0.90, 4, 20261111
RULE = 'PR-003'
OPEN_S = B.OPEN_S
WALK_TIMEOUT_S = 1800
PROC_LABEL = {'refit': 'P-candidate', 'hold': 'P-incumbent'}
PLAIN_FOR = {'online': 'P-plain', 'offline': 'P-plain-cal'}    # the plain procedure on each scoring basis


def say(msg):
    print(datetime.now(IST).strftime('%H:%M:%S ') + str(msg), flush=True)


def now_txt():
    return datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')


# ── files ───────────────────────────────────────────────────────────────────────────────────────────────────────
def write_atomic(path, text):
    """tmp + fsync + os.replace: a reader sees the old file or the new one, never half of one."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = f'{path}.tmp{os.getpid()}'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_json(path, obj):
    write_atomic(path, json.dumps(obj, indent=1, default=_plain))


def _plain(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f'not JSON: {type(o).__name__}')


def read_json(path):
    """The file's object; None when missing. A damaged file is reported and treated as missing."""
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        say(f'WARNING: {os.path.basename(path)} unreadable ({type(e).__name__}: {e}); treated as missing')
        return None


def ledger_path(lab):
    return os.path.join(lab, 'ledger.jsonl')


def read_ledger(lab):
    rows, bad = [], 0
    try:
        with open(ledger_path(lab), encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    bad += 1
                    continue
                if isinstance(r, dict):
                    rows.append(r)
                else:
                    bad += 1
    except FileNotFoundError:
        return []
    if bad:
        say(f'WARNING: ledger.jsonl has {bad} unreadable line(s); they are skipped')
    return rows


def write_ledger(lab, rows):
    write_atomic(ledger_path(lab), ''.join(json.dumps(r, default=_plain) + '\n' for r in rows))


def decision_days(rows):
    return {r['day'] for r in rows if r.get('kind') == 'decision' and r.get('rule') == RULE}


def owner_ok(data_dir=None):
    d = read_json(os.path.join(data_dir or DATA, 'nightly_owner_ok.json'))
    return d if isinstance(d, dict) else {}


# ── brains: load, archive, install ──────────────────────────────────────────────────────────────────────────────
def feat_hash():
    return hashlib.sha256(json.dumps([list(B.FEATS), list(H)]).encode()).hexdigest()[:12]


def load_obj(path):
    """(obj, why): obj only when the file loads and Brain accepts it."""
    if not path or not os.path.exists(path):
        return None, 'no file'
    try:
        import joblib
        obj = joblib.load(path)
    except Exception as e:                                    # a torn or foreign file: say so, never crash the night
        return None, f'unreadable ({type(e).__name__}: {e})'
    br = B.Brain(obj=obj) if isinstance(obj, dict) else None
    if br is None or not br.ok:
        return None, (br.why if br is not None else 'not a brain')
    return obj, None


def meta_of(obj):
    return (obj or {}).get('meta') or {}


def archive_dir(lab):
    return os.path.join(lab, 'brains', 'archive')


def archive_path(lab, obj):
    m = meta_of(obj)
    return os.path.join(archive_dir(lab), f"brain_{m.get('trained_through')}_{m.get('hash')}.joblib")


def find_archived(lab, h):
    hits = sorted(glob.glob(os.path.join(archive_dir(lab), f'brain_*_{h}.joblib'))) if h else []
    return hits[0] if hits else None


def _verified_copy(write_tmp, dest, want_hash):
    """Write dest via a temp file that must load as a brain with the expected hash before it is renamed."""
    tmp = dest + '.tmp'
    write_tmp(tmp)
    obj, why = load_obj(tmp)
    if obj is None or meta_of(obj).get('hash') != want_hash:
        try:
            os.remove(tmp)
        except OSError as e:
            say(f'WARNING: temp file {tmp} not removed: {e}')
        raise RuntimeError(f'{os.path.basename(dest)}: the written file did not verify ({why or "hash differs"}); '
                           f'the old file is untouched')
    os.replace(tmp, dest)


def archive(lab, obj):
    """The archived path of obj; written once (temp, verify, rename) and never overwritten."""
    import joblib
    p = archive_path(lab, obj)
    if os.path.exists(p):
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    _verified_copy(lambda tmp: joblib.dump(obj, tmp, compress=3), p, meta_of(obj).get('hash'))
    return p


def git_commit():
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def sk_version():
    try:                                                          # the version without importing sklearn
        from importlib.metadata import version
        return version('scikit-learn')
    except Exception as e:                                        # recorded as unknown, and said
        say(f'sklearn version not read ({type(e).__name__})')
        return None


def full_meta(obj, c_h=None):
    m = dict(meta_of(obj))
    m['sklearn'] = sk_version()
    m['feat_hash'] = feat_hash()
    if c_h is not None:
        m['c_h'] = [round(float(x), 6) for x in c_h]
    m['git'] = git_commit()
    m['installed'] = now_txt()
    return m


def install(lab, src, day, c_h=None, log=say):
    """Make the archived brain at src the live brain.joblib. The previous live file becomes brain_prev only when it
    was trained before day (never a same-day or newer brain). Returns what happened."""
    live, prev = os.path.join(lab, 'brain.joblib'), os.path.join(lab, 'brain_prev.joblib')
    new, why = load_obj(src)
    if new is None:
        raise RuntimeError(f'cannot install {src}: {why}')
    cur, _ = load_obj(live)
    nh = meta_of(new).get('hash')
    if cur is not None and meta_of(cur).get('hash') == nh:
        return f'already live ({nh})'
    if cur is not None:
        ct = str(meta_of(cur).get('trained_through'))
        if ct < day:
            _verified_copy(lambda tmp: shutil.copyfile(live, tmp), prev, meta_of(cur).get('hash'))
        else:
            log(f'brain_prev kept: the live file is trained through {ct}, not before {day}')
    _verified_copy(lambda tmp: shutil.copyfile(src, tmp), live, nh)
    write_json(os.path.join(lab, 'brain.meta.json'), full_meta(new, c_h))           # after the brain, atomically
    return f"installed {nh} (trained through {meta_of(new).get('trained_through')})"


def rollback(lab, failed_hash, log=say, c_of=None):
    """When the live brain is the one that failed its held-out day, put brain_prev back. brain_prev is kept.
    c_of(obj) gives the restored brain's c_h for its meta (None: not recorded)."""
    live, prev = os.path.join(lab, 'brain.joblib'), os.path.join(lab, 'brain_prev.joblib')
    cur, _ = load_obj(live)
    if cur is None or meta_of(cur).get('hash') != failed_hash:
        return 'the failed model is not the live one: brain.joblib left as it is'
    old, why = load_obj(prev)
    if old is None:
        return f'NO ROLLBACK POSSIBLE: brain_prev.joblib {why}; brain.joblib left as it is'
    if str(meta_of(old).get('trained_through')) >= str(meta_of(cur).get('trained_through')):
        return 'NO ROLLBACK: brain_prev is not older than the live file; brain.joblib left as it is'
    _verified_copy(lambda tmp: shutil.copyfile(prev, tmp), live, meta_of(old).get('hash'))
    write_json(os.path.join(lab, 'brain.meta.json'), dict(full_meta(old, c_of(old) if c_of else None),
                                                          rolled_back_from=failed_hash))
    return f"rolled back to brain_prev ({meta_of(old).get('hash')}, trained through {meta_of(old).get('trained_through')})"


# ── models on the collected arrays ──────────────────────────────────────────────────────────────────────────────
def tod_idx(t):
    s = (np.asarray(t, float).astype(np.int64) + 19800) % 86400 - OPEN_S
    return np.clip(s // B.TOD_BUCKET_S, 0, B.N_TOD - 1).astype(int)


def brain_var(obj, d):
    Z = B.Brain(obj=obj).z(d['X'])
    V = np.empty((len(Z), len(H)))
    for j, h in enumerate(H):
        w = np.asarray(obj['vol'][j], float)
        V[:, j] = d['vref'] * h * np.exp(np.clip(w[0] + Z @ w[1:], -3.0, 3.0))
    return V


def clock_var(d):
    return np.asarray(d['vref'], float)[:, None] * np.asarray(H, float)[None, :]


def mean_ratio(days, varf):
    """c_h = pooled mean of RV / forecast per horizon over these sessions (1.0 where nothing is usable)."""
    s, n = np.zeros(len(H)), np.zeros(len(H))
    for d in days:
        V, RV = varf(d), d['RV']
        ok = np.isfinite(RV) & (RV > 0) & np.isfinite(V) & (V > 0)
        s += np.where(ok, RV / np.where(ok, V, 1.0), 0.0).sum(0)
        n += ok.sum(0)
    return np.where(n > 0, s / np.maximum(n, 1), 1.0)


def z_quantiles(days, varf):
    out = []
    zs = [[] for _ in H]
    for d in days:
        V, dF = varf(d), d['dF']
        z = dF / np.sqrt(np.where(V > 0, V, np.nan))
        for j in range(len(H)):
            zz = z[:, j]
            zs[j].append(zz[np.isfinite(zz)])
    for j in range(len(H)):
        a = np.concatenate(zs[j]) if zs[j] else np.zeros(0)
        out.append([float(q) for q in np.percentile(a, [q * 100 for q in QS])] if len(a) > 50 else list(ZN))
    return out


def fit_plain_cal(days):
    """P-plain-cal on earlier sessions: log(RV / clock) = intercept + time-of-day bucket, shrunk to the intercept."""
    table = np.zeros((len(H), B.N_TOD))
    for j, h in enumerate(H):
        sb, nb = np.zeros(B.N_TOD), np.zeros(B.N_TOD)
        for d in days:
            y = np.log(np.maximum(d['RV'][:, j], 1e-12) / np.maximum(d['vref'] * h, 1e-12))
            ok = np.isfinite(y) & np.isfinite(d['RV'][:, j]) & (d['RV'][:, j] > 0)
            b = tod_idx(d['t'])[ok]
            sb += np.bincount(b, weights=np.clip(y[ok], -3, 3), minlength=B.N_TOD)
            nb += np.bincount(b, minlength=B.N_TOD)
        a = sb.sum() / nb.sum() if nb.sum() else 0.0
        table[j] = (sb + K_TOD * a) / (nb + K_TOD)
    m = dict(kind='plain_cal', table=table.tolist(), days=[d['day'] for d in days], k=K_TOD)
    vf = lambda d: plaincal_var(m, d)
    m['c'] = mean_ratio(days, vf).tolist()
    m['zq'] = z_quantiles(days, vf)
    return m


def plaincal_var(m, d):
    tb = np.asarray(m['table'], float)
    b = tod_idx(d['t'])
    return clock_var(d) * np.exp(np.clip(tb[:, b].T, -3.0, 3.0))


def score(d, V, zq, c=None):
    """Sums per horizon on day d for variance forecasts V (n x horizons) and standardised quantiles zq (horizons x 5)."""
    t, dF, RV = d['t'], d['dF'], d['RV']
    blk = np.clip(((np.asarray(t, float).astype(np.int64) + 19800) % 86400 - OPEN_S) // 1800, 0, 12).astype(int)
    out, blocks = {}, None
    c = np.ones(len(H)) if c is None else np.asarray(c, float)
    for j, h in enumerate(H):
        sd = np.sqrt(np.where(V[:, j] > 0, V[:, j], np.nan))
        y = dF[:, j]
        ok = np.isfinite(y) & np.isfinite(sd)
        q = np.asarray(zq[j], float)[None, :] * sd[ok, None]
        yy = y[ok]
        L, U = q[:, 0], q[:, 4]
        is80 = (U - L) + 10.0 * np.maximum(L - yy, 0) + 10.0 * np.maximum(yy - U, 0)
        e = yy[:, None] - q
        tau = np.asarray(QS)[None, :]
        pin = np.mean(np.maximum(tau * e, (tau - 1.0) * e), axis=1)
        rv, v = RV[:, j], V[:, j]
        okq = np.isfinite(rv) & (rv > 0) & np.isfinite(v) & (v > 0)
        r1 = rv[okq] / v[okq]
        r2 = r1 / c[j]
        out[str(h)] = dict(n=int(ok.sum()), is80=float(is80.sum()), inside=float(((yy >= L) & (yy <= U)).sum()),
                           width=float((U - L).sum()), pin=float(pin.sum()), nq=int(okq.sum()),
                           qlike=float((r1 - np.log(r1) - 1).sum()), qlike_c=float((r2 - np.log(r2) - 1).sum()))
        if h == PRIMARY_H:
            bi = blk[ok]
            blocks = dict(is80=np.bincount(bi, weights=is80, minlength=13).round(3).tolist(),
                          n=np.bincount(bi, minlength=13).tolist())
    return out, blocks


def primary(hs):
    r = (hs or {}).get(str(PRIMARY_H)) or {}
    return r['is80'] / r['n'] if r.get('n') and r.get('is80') is not None else None


def mean_h(hs, key='is80'):
    return {h: (r[key] / r['n'] if r.get('n') and r.get(key) is not None else None) for h, r in (hs or {}).items()}


# ── days to expiry ──────────────────────────────────────────────────────────────────────────────────────────────
def dte_of(day):
    """Calendar days from day to the next weekly expiry (holiday-shifted), or None when it cannot be worked out."""
    try:
        from apex import config as C
        y, m, dd = (int(x) for x in day.split('-'))
        e = C.weekly_expiries(datetime(y, m, dd, 10, 0, tzinfo=C.IST), 1)[0]
        return (e - datetime(y, m, dd).date()).days
    except Exception as e:                                    # reported, never fatal: the stratum is then unknown
        say(f'WARNING: days to expiry for {day} not worked out ({type(e).__name__}: {e})')
        return None


def stratum(dte):
    return None if dte is None else ('dte0-1' if dte <= 1 else 'dte2+')


# ── rows ────────────────────────────────────────────────────────────────────────────────────────────────────────
def score_row(day, proc, basis, hs, blocks=None, model=None, walk=False, dte=None, **extra):
    hv = mean_h(hs)
    cov = [r['inside'] / r['n'] for r in (hs or {}).values() if r.get('n') and r.get('inside') is not None]
    r = dict(kind='score', day=day, procedure=proc, basis=basis, walk=walk, model=model, dte=dte, stratum=stratum(dte),
             primary=primary(hs), cover80=float(np.mean(cov)) if cov else None,
             is80_mean={h: (round(v, 4) if v is not None else None) for h, v in hv.items()},
             h=hs, blocks=blocks, written=now_txt())
    r.update(extra)
    return r


def model_ref(obj):
    m = meta_of(obj)
    return dict(hash=m.get('hash'), trained_through=m.get('trained_through'), sessions=m.get('sessions'))


def online_hs(sv):
    """Sums per horizon from a Lab score view (core._score_view): pin there is the 10 % + 90 % pinball, so the
    80 % interval score is 10 x pin."""
    out = {}
    for r in (sv or {}).get('fut') or []:
        n = r.get('n') or 0
        if not n or r.get('pin') is None:
            continue
        out[str(r['h'])] = dict(n=int(n), is80=10.0 * r['pin'] * n, inside=(r.get('cov') or 0) * n,
                                width=(r.get('width') or 0) * n, crps=(r.get('crps') or 0) * n,
                                crps_plain=(r.get('crps_plain') or 0) * n, from_means=True)
    return out


def option_side(sv):
    keep = ('h', 'n', 'cov', 'pin', 'width', 'err', 'err_naive', 'err_decay', 'brier', 'brier_base')
    return [{k: r.get(k) for k in keep} for r in (sv or {}).get('opt') or []]


# ── online walk (one session, the online layers on) ─────────────────────────────────────────────────────────────
def walk_one(day, brain_path, state_in, out):
    """Child process: the whole Lab over day D's recorded parts, from state_in, with that brain (or none)."""
    from apex.forecast_lab import tape
    from apex.forecast_lab.core import Lab
    br = B.Brain(brain_path) if brain_path and brain_path != 'none' else None
    if br is not None and not br.ok:
        raise SystemExit(f'brain {brain_path}: {br.why}')
    st = None
    if state_in and state_in != 'none':
        with open(state_in, encoding='utf-8') as f:
            st = json.load(f)
    parts = tape.parts_for(day)
    if not parts:
        raise SystemExit(f'no ds_v2 parts for {day}')
    lab = Lab(state=st, options=True, brain=br)
    lab.simulate = True
    t0 = time.time()
    for p in parts:
        tape.feed(lab, p)
    sv = lab._score_view()
    write_json(out, dict(day=day, brain=bool(br is not None), score=sv, wall_s=round(time.time() - t0, 1),
                         restarts=getattr(lab, 'restarts', None), state=json.loads(json.dumps(lab.to_json(), default=_plain))))


def walk_state_in(lab, proc, day):
    """The procedure's own chained state (end of its last walked day before D), else the warm state, else cold."""
    hits = sorted(p for p in glob.glob(os.path.join(lab, 'nightly_walk', f'{proc}_*.json'))
                  if not p.endswith('.out.json') and os.path.basename(p)[len(proc) + 1:len(proc) + 11] < day)
    if hits:
        return hits[-1], 'chained'
    w = os.path.join(lab, 'state_warm.json')
    return (w, 'warm') if os.path.exists(w) else (None, 'cold')


def run_walk(lab, proc, day, brain_path, state_in=None, timeout=WALK_TIMEOUT_S):
    """(score view, why) of a one-session walk in a child process with a time limit."""
    if state_in is None:
        state_in, src = walk_state_in(lab, proc, day)
    else:
        src = 'given'
    out = os.path.join(lab, 'nightly_walk', f'{proc}_{day}.out.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.abspath(__file__), '--walk-one', day, brain_path or 'none',
                            state_in or 'none', out], cwd=ROOT, env=ENV, timeout=timeout, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, f'walk timed out after {timeout} s'
    if r.returncode != 0:
        return None, f'walk failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[-300:]}'
    res = read_json(out)
    if not res:
        return None, 'walk wrote no result'
    write_json(os.path.join(lab, 'nightly_walk', f'{proc}_{day}.json'), res.get('state') or {})
    res.pop('state', None)
    write_json(out, res)
    res['state_from'] = src
    res['secs'] = round(time.time() - t0, 1)
    return res, None


def fut_at(sv, h, H_list=None):
    """The futures row {n, cov, crps, width} at horizon h from either a Lab score view ({fut: [{h, n, cov, ...}]}) or
    the daily-record sums the live Lab writes ({name: [one sum per H]} with the record's H list); None if absent."""
    if not isinstance(sv, dict):
        return None
    if isinstance(sv.get('fut'), list):
        for r in sv['fut']:
            if isinstance(r, dict) and r.get('h') == h:
                return r
        return None
    hs = list(H_list or H)
    if h not in hs or not isinstance(sv.get('n'), list):
        return None
    j = hs.index(h)

    def get(k):
        v = sv.get(k)
        try:
            return float(v[j]) if isinstance(v, list) and v[j] is not None else None
        except (IndexError, TypeError, ValueError):
            return None
    n = get('n')
    if not n:
        return None
    mean = lambda k: (get(k) / n) if get(k) is not None else None
    return dict(h=h, n=n, cov=mean('cov'), crps=mean('crps'), width=mean('width'))


def parity(live_rec, walk_sv, h=PRIMARY_H):
    """Live record of day D against the offline re-run of D with the same brain (L8-I5). Tolerance: 2 points of
    coverage and 3 % of CRPS at 5 min."""
    rec = live_rec or {}
    a = fut_at(rec.get('score', rec.get('sums')), h, rec.get('H'))
    b = fut_at(walk_sv, h)
    if a is None or b is None or not a.get('n') or not b.get('n'):
        return dict(ok=None, why='no 5-minute score on one side')
    if a.get('cov') is None or b.get('cov') is None:
        return dict(ok=None, why='no 5-minute coverage on one side')
    dc = a['cov'] - b['cov']
    dcr = ((a.get('crps') or 0) / b['crps'] - 1.0) if b.get('crps') else None
    ok = abs(dc) <= 0.02 and dcr is not None and abs(dcr) <= 0.03
    return dict(ok=bool(ok), cov_live=a.get('cov'), cov_rerun=b.get('cov'), crps_live=a.get('crps'), crps_rerun=b.get('crps'),
                n_live=a.get('n'), n_rerun=b.get('n'), width_live=a.get('width'), width_rerun=b.get('width'),
                cov_diff=round(dc, 4), crps_diff=None if dcr is None else round(dcr, 4),
                counters={k: (live_rec or {}).get(k) for k in ('restarts', 'skipped', 'stale_s', 'errors', 'loop_p95')})


# ── the rule (PR-003) ───────────────────────────────────────────────────────────────────────────────────────────
def index(rows):
    """(day, procedure, basis) -> row; a forward row wins over a back-filled walk row of the same key."""
    ix = {}
    for r in rows:
        if r.get('kind') != 'score':
            continue
        k = (r['day'], r['procedure'], r['basis'])
        if k not in ix or (ix[k].get('walk') and not r.get('walk')):
            ix[k] = r
    return ix


def pair(ix, day, a, b=None):
    """(row a, row b, basis) on the best shared basis (online first), or None. b None means the plain procedure."""
    for basis in ('online', 'offline'):
        ra = ix.get((day, a, basis))
        rb = ix.get((day, b or PLAIN_FOR[basis], basis))
        if ra and rb and ra.get('primary') is not None and rb.get('primary') is not None:
            return ra, rb, basis
    return None


def fast_off(rows, day):
    """Did the live brain lose to the plain clock on 4 or more of the last 5 days with a score (walk days count)?"""
    ix = index(rows)
    days = sorted({k[0] for k in ix if k[0] <= day})
    comps = [(d, pair(ix, d, 'P-incumbent')) for d in days]
    comps = [(d, p) for d, p in comps if p][-FAST_OFF_N:]
    lost = [d for d, (a, b, _) in comps if a['primary'] > b['primary']]
    hit = len(lost) >= FAST_OFF_LOSSES
    why = (f'the live trained layer lost to the plain clock on {len(lost)} of the last {len(comps)} days '
           f'on the 5-minute 80 % range score' + (' (rule: 4 of 5)' if hit else ''))
    return dict(hit=hit, lost=len(lost), of=len(comps), days=[d for d, _ in comps], lost_days=lost,
                bases=[p[2] for _, p in comps], why=why)


def boot_interval(x, draws=BOOT_DRAWS, level=BOOT_LEVEL, seed=BOOT_SEED):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, len(x), size=(draws, len(x)))].mean(1)
    lo, hi = np.percentile(m, [50 * (1 - level), 100 - 50 * (1 - level)])
    return float(lo), float(hi)


def better(rows, day, a, b=None, forward_only=True):
    """Is procedure a better than b (default: the plain clock) by the slow rule? Day-block bootstrap of the mean
    daily log-ratio of the primary score, at least 10 common forward days, at least 4 of 7 horizons better."""
    ix = index(rows)
    days = sorted({k[0] for k in ix if k[0] <= day})
    common = []
    for d in days:
        p = pair(ix, d, a, b)
        if p and (not forward_only or not (p[0].get('walk') or p[1].get('walk'))):
            common.append((d, p))
    name_b = b or 'the plain clock'
    if len(common) < SLOW_MIN_DAYS:
        return dict(met=False, n=len(common), why=f'{a} against {name_b}: {len(common)} of {SLOW_MIN_DAYS} common forward days')
    lr = [math.log(pa['primary'] / pb['primary']) for _, (pa, pb, _) in common]
    lo, hi = boot_interval(lr)
    hb = 0
    for h in (str(x) for x in H):
        va = [pa['is80_mean'].get(h) for _, (pa, pb, _) in common]
        vb = [pb['is80_mean'].get(h) for _, (pa, pb, _) in common]
        ok = [(x, y) for x, y in zip(va, vb) if x is not None and y is not None]
        if ok and np.mean([x for x, _ in ok]) < np.mean([y for _, y in ok]):
            hb += 1
    met = hi < 0 and hb >= MIN_H_BETTER
    return dict(met=bool(met), n=len(common), mean_log_ratio=round(float(np.mean(lr)), 4), interval=[round(lo, 4), round(hi, 4)],
                horizons_better=hb, why=(f'{a} against {name_b} over {len(common)} common forward days: mean log-ratio '
                                         f'{np.mean(lr):+.3f}, 90 % interval {lo:+.3f} to {hi:+.3f}, better on {hb} of {len(H)} horizons'))


def read_procedure(lab):
    p = read_json(os.path.join(lab, 'procedure.json'))
    brain = (p or {}).get('brain') if isinstance(p, dict) else None
    u = read_json(os.path.join(lab, 'use_brain.json'))
    use = bool(u.get('use')) if isinstance(u, dict) and 'use' in u else True
    return dict(brain=brain if brain in ('refit', 'hold') else 'refit', use_brain=use)


def decide(rows, day, proc):
    """The PR-003 decision for the day after D, from the ledger alone. Fast-off acts; slow-on and switch propose."""
    fo = fast_off(rows, day)
    use_next = proc['use_brain'] and not fo['hit']
    acts, props = [], []
    if proc['use_brain'] and fo['hit']:
        acts.append('fast-off: use_brain.json set to off')
    if not proc['use_brain']:
        so = better(rows, day, PROC_LABEL[proc['brain']])
        if so['met']:
            props.append('slow-on: ' + so['why'] + '. The owner may turn the trained layer back on.')
    else:
        so = None
    other = 'hold' if proc['brain'] == 'refit' else 'refit'
    sw = better(rows, day, PROC_LABEL[other], PROC_LABEL[proc['brain']])
    if sw['met']:
        props.append(f"switch to {other}: " + sw['why'] + '. The owner may switch.')
    live = PROC_LABEL[proc['brain']] if use_next else 'P-plain'
    return dict(kind='decision', day=day, rule=RULE, live_procedure=live, use_brain=use_next, brain_proc=proc['brain'],
                fast_off=fo, slow_on=so, switch=sw, actions=acts, proposals=props,
                why=fo['why'] + ('' if not props else '; ' + ' '.join(props)))


def summarize(rows):
    """The cumulative record for the panel and the owner: trained (live brain) against plain, by day, in strata."""
    ix = index(rows)
    days = sorted({k[0] for k in ix})
    comps = [(d, pair(ix, d, 'P-incumbent')) for d in days]
    comps = [(d, p) for d, p in comps if p]

    def block(cs):
        if not cs:
            return dict(days=0)
        lr = [math.log(a['primary'] / b['primary']) for _, (a, b, _) in cs]
        gain = [b['primary'] - a['primary'] for _, (a, b, _) in cs]
        tot = sum(gain)
        out = dict(days=len(cs), trained_better=int(sum(g > 0 for g in gain)), walk_days=int(sum(bool(a.get('walk')) for _, (a, _, _) in cs)),
                   mean_log_ratio=round(float(np.mean(lr)), 4),
                   best_day=cs[int(np.argmax(gain))][0], best_day_share=round(max(gain) / tot, 3) if tot > 0 else None)
        if len(cs) >= 2:
            out['interval90'] = [round(x, 4) for x in boot_interval(lr)]
        return out
    strata = {}
    for s in ('dte0-1', 'dte2+'):
        strata[s] = block([(d, p) for d, p in comps if p[0].get('stratum') == s])
    alls = block(comps)
    dec = [r for r in rows if r.get('kind') == 'decision' and r.get('rule') == RULE]
    line = None
    if alls.get('days'):
        line = f"trained better than plain on {alls['trained_better']} of {alls['days']} days"
        if alls.get('interval90'):
            line += f" (90 % day-block interval of the log-ratio {alls['interval90'][0]:+.3f} to {alls['interval90'][1]:+.3f}; below 0 favours trained)"
    return dict(written=now_txt(), rule=RULE, metric='80 % range score of the futures move at 5 min, per day',
                all=alls, strata=strata, line=line, last_decision=dec[-1] if dec else None)


# ── one day ─────────────────────────────────────────────────────────────────────────────────────────────────────
def collected_days(col):
    return sorted(os.path.basename(p)[:10] for p in glob.glob(os.path.join(col, '*.joblib')))


def convert_and_collect(day, timeout=1800):
    ds = os.path.join(ROOT, 'data', 'research', 'ds_v2')
    for tape in sorted(glob.glob(os.path.join(ROOT, 'data', 'ticks', f'{day}*.jsonl.gz'))):
        part = os.path.basename(tape)[:-len('.jsonl.gz')]
        if not os.path.exists(os.path.join(ds, part + '.npz')):
            say(f'converting {part}')
            subprocess.run([sys.executable, os.path.join(ROOT, 'data', 'replay', 'batch', 'gen2_research_v2_2026-11-10', 'ds2.py'), part],
                           cwd=ROOT, env=ENV, check=True, timeout=timeout)
    say(f'collecting {day}')
    subprocess.run([sys.executable, '-m', 'apex.forecast_lab.tape', 'collect', day], cwd=ROOT, env=ENV, check=True, timeout=timeout)


def find_fit(lab, T, data, cache):
    """The brain fitted on exactly these sessions: from the cache, the archive, or a new fit (archived)."""
    want = [d['day'] for d in data]
    key = tuple(want)
    if key in cache:
        return cache[key]
    for p in sorted(glob.glob(os.path.join(archive_dir(lab), f'brain_{want[-1]}_*.joblib'))):
        obj, _ = load_obj(p)
        if obj is not None and list(meta_of(obj).get('days') or []) == want:
            cache[key] = obj
            return obj
    say(f'fitting on {len(data)} sessions through {want[-1]}')
    obj = T.fit(data)
    archive(lab, obj)
    cache[key] = obj
    return obj


def held_out(obj, hs):
    w = np.concatenate([np.ravel(np.asarray(obj['vol'], float)), np.ravel(np.asarray(obj['lin'], float)), np.ravel(np.asarray(obj['qz'], float))])
    if not np.all(np.isfinite(w)):
        return False, 'a fitted weight is not finite'
    cov = [r['inside'] / r['n'] for r in hs.values() if r.get('n')]
    if not cov:
        return False, 'no scored origins on the held-out day'
    c = float(np.mean(cov))
    lo, hi = HOLD_COVER
    if not lo <= c <= hi:
        return False, f'its 80 % range caught {c * 100:.0f} % on the unseen day (must be {lo * 100:.0f} to {hi * 100:.0f})'
    return True, f'weights finite; its 80 % range caught {c * 100:.0f} % on the unseen day'


def harp_contestant(prior, today):
    """PKG-11 hook: research/forecast_lab/har_plus.py nightly_contestant(prior_days, day) -> dict(var=(n x 7), zq=(7 x 5))."""
    try:
        import har_plus
    except ImportError:
        return None, 'har_plus.py not present'
    fn = getattr(har_plus, 'nightly_contestant', None)
    if fn is None:
        return None, 'har_plus.py has no nightly_contestant()'
    m = fn(prior, today)
    return m, None


def run_day(day, lab=None, T=None, force=False, convert=True, online=None, check_only=False, log=say):
    lab = lab or LAB
    rows = read_ledger(lab)
    if day in decision_days(rows) and not force and not check_only:
        log(f'{day}: already done (the ledger has its decision row); nothing to do. Use --force to redo it.')
        return dict(day=day, status='skip', why='already in the ledger')
    if online is None:
        online = bool(owner_ok().get('online_walks'))
    if convert and not check_only:
        if os.path.abspath(lab) == os.path.abspath(os.path.join(LIVE_DATA, 'forecast_lab')):
            convert_and_collect(day)
        else:
            log('conversion and collect skipped: not the live data tree')
    if T is None:
        import train as T
        T.COL = os.path.join(lab, 'collect')
    days = collected_days(T.COL)
    if day not in days:
        log(f'{day}: no collected data')
        return dict(day=day, status='fail', why='no collected data')
    prior_days = [d for d in days if d < day]
    if not prior_days:
        return dict(day=day, status='fail', why='no earlier session to fit on')
    t0 = time.time()
    prior = [T.load(d) for d in prior_days]
    today = T.load(day)
    by_day = {d['day']: d for d in prior}
    dte = dte_of(day)
    proc = read_procedure(lab)
    old = [r for r in rows if r.get('day') == day and r.get('kind') == 'decision' and r.get('rule') == RULE]
    # the brain that was live during D: brain.joblib, or on a re-run the file recorded then / brain_prev
    inc = None
    if old and old[-1].get('incumbent'):
        inc, _ = load_obj(find_archived(lab, old[-1]['incumbent']))
    for p in (os.path.join(lab, 'brain.joblib'), os.path.join(lab, 'brain_prev.joblib')):
        if inc is None:
            o, why = load_obj(p)
            if o is not None and str(meta_of(o).get('trained_through')) < day:
                inc = o
            elif why and why != 'no file':
                log(f'WARNING: {os.path.basename(p)} {why}')
    lm = read_json(os.path.join(lab, 'brain.meta.json')) or {}
    cur_sk = sk_version() if lm.get('sklearn') else None
    if cur_sk and lm.get('sklearn') != cur_sk:
        log(f"WARNING: the live brain was saved with scikit-learn {lm.get('sklearn')}, this machine has {cur_sk}: "
            f"its trees may load differently")
    cache = {}
    if inc is not None:                                         # the live file already fitted on these sessions
        cache[tuple(meta_of(inc).get('days') or [])] = inc
    cand = find_fit(lab, T, prior, cache) if not check_only else None
    if check_only:
        cand = inc if inc is not None and list(meta_of(inc).get('days') or []) == prior_days else T.fit(prior)
    if inc is not None and not check_only:
        archive(lab, inc)
    new = []

    def brain_row(name, obj):
        tr = [by_day[x] for x in (meta_of(obj).get('days') or []) if x in by_day] or prior
        c = mean_ratio(tr, lambda d: brain_var(obj, d))
        hs, bl = score(today, brain_var(obj, today), obj['qz'], c)
        return score_row(day, name, 'offline', hs, bl, model_ref(obj), dte=dte, c_h=c.round(4).tolist())
    rc = brain_row('P-candidate', cand)
    new.append(rc)
    if inc is not None:
        new.append(dict(rc, procedure='P-incumbent', same_as='P-candidate') if meta_of(inc).get('hash') == meta_of(cand).get('hash')
                   else brain_row('P-incumbent', inc))
    pc = fit_plain_cal(prior)
    hs, bl = score(today, plaincal_var(pc, today), pc['zq'], pc['c'])
    new.append(score_row(day, 'P-plain-cal', 'offline', hs, bl, dict(sessions=len(prior), k=K_TOD), dte=dte, c_h=np.round(pc['c'], 4).tolist()))
    cc = mean_ratio(prior, clock_var)
    hs, bl = score(today, clock_var(today), [ZN] * len(H), cc)
    new.append(score_row(day, 'P-clock', 'offline', hs, bl, None, dte=dte, c_h=cc.round(4).tolist()))
    try:
        hm, hwhy = harp_contestant(prior, today)
        if hm is not None:
            hs, bl = score(today, np.asarray(hm['var'], float), hm['zq'], hm.get('c'))
            new.append(score_row(day, 'P-harp', 'offline', hs, bl, hm.get('model'), dte=dte))
    except Exception as e:                                       # a contestant's failure never stops the night
        log(f'WARNING: P-harp failed ({type(e).__name__}: {e})')
    ok_hold, why_hold = held_out(cand, rc['h'])
    for r in new:
        if r['procedure'] in ('P-candidate', 'P-incumbent', 'P-plain-cal', 'P-clock'):
            q = r['h'][str(PRIMARY_H)]
            log(f"{day} {r['procedure']:<12} offline: 5-min 80 % range score {r['primary']:.2f}, caught "
                f"{q['inside'] / max(q['n'], 1) * 100:.1f} %, QLIKE raw {q['qlike'] / max(q['nq'], 1):.4f} corrected {q['qlike_c'] / max(q['nq'], 1):.4f}")
    log(f'HELD-OUT CHECK (fitted through {meta_of(cand).get("trained_through")}, scored on {day}): '
        f"{'passed' if ok_hold else 'FAILED'}: {why_hold}")
    if check_only:
        return dict(day=day, status='check', rows=new, held_out=(ok_hold, why_hold))
    # online walks, with the owner's standing OK
    walks = {}
    if online:
        targets = [('P-candidate', archive(lab, cand), cand)]
        if inc is not None and meta_of(inc).get('hash') != meta_of(cand).get('hash'):
            targets.append(('P-incumbent', archive(lab, inc), inc))
        targets.append(('P-plain', None, None))
        for name, path, obj in targets:
            st_in = None
            morning = os.path.join(lab, f'state_morning_{day}.json')
            if name == 'P-incumbent' or (name == 'P-candidate' and inc is not None and meta_of(inc).get('hash') == meta_of(cand).get('hash')):
                st_in = morning if os.path.exists(morning) else None
            res, why = run_walk(lab, name, day, path, st_in)
            if res is None:
                log(f'WARNING: online walk {name} {why}')
                continue
            walks[name] = res
            new.append(score_row(day, name, 'online', online_hs(res['score']), None, model_ref(obj) if obj else None, dte=dte,
                                 option=option_side(res['score']), state_from=res.get('state_from'), secs=res.get('secs')))
            log(f"{day} {name:<12} online: 5-min 80 % range score {new[-1]['primary']}, {res.get('secs')} s")
        if inc is not None and meta_of(inc).get('hash') == meta_of(cand).get('hash') and 'P-candidate' in walks:
            pr = [r for r in new if r['procedure'] == 'P-candidate' and r['basis'] == 'online'][0]
            new.append(dict(pr, procedure='P-incumbent', same_as='P-candidate'))
        live_rec = read_json(os.path.join(lab, 'days', f'{day}.json'))
        live_walk = walks.get('P-incumbent') or walks.get('P-candidate')
        if isinstance(live_rec, dict) and not live_rec.get('walk') and live_walk:
            pp = parity(live_rec, live_walk['score'])
            new.append(dict(kind='parity', day=day, written=now_txt(), state_from=live_walk.get('state_from'), **pp))
            log(f'LIVE PARITY {day}: ' + ('within tolerance' if pp.get('ok') else f'outside tolerance or not comparable: {pp}'))
    # the ledger first (a crash after this point re-runs only the decision), then the brain file, then the decision
    rows = [r for r in rows if not (r.get('day') == day and r.get('kind') in ('score', 'parity', 'decision') and not r.get('walk'))]
    rows += new
    write_ledger(lab, rows)
    dec = decide(rows, day, proc)
    nxt = None
    if proc['brain'] == 'refit':
        if ok_hold:
            nxt = find_fit(lab, T, prior + [today], cache)
            m_c = mean_ratio(prior + [today], lambda d: brain_var(nxt, d))
            dec['brain_action'] = install(lab, archive(lab, nxt), day, m_c, log)
        else:
            c_of = lambda o: mean_ratio([by_day[x] for x in (meta_of(o).get('days') or []) if x in by_day] or prior,
                                        lambda d: brain_var(o, d))
            dec['brain_action'] = ('refit NOT installed (held-out check failed); '
                                   + rollback(lab, meta_of(cand).get('hash'), log, c_of))
    else:
        dec['brain_action'] = 'hold: brain.joblib unchanged'
    if dec['actions'] and proc['use_brain'] and not dec['use_brain']:
        write_json(os.path.join(lab, 'use_brain.json'), dict(use=False, why=dec['fast_off']['why'], t=now_txt(), rule=RULE, day=day))
    dec.update(incumbent=meta_of(inc).get('hash') if inc is not None else None, candidate=meta_of(cand).get('hash'),
               next_brain=meta_of(nxt).get('hash') if nxt is not None else None, held_out=dict(ok=ok_hold, why=why_hold),
               written=now_txt(), secs=round(time.time() - t0, 1))
    rows.append(dec)
    write_ledger(lab, rows)
    write_json(os.path.join(lab, 'record_summary.json'), summarize(rows))
    log(f"DECISION {day} ({RULE}): tomorrow runs {dec['live_procedure']}; {dec['brain_action']}. {dec['why']}")
    return dict(day=day, status='ok', decision=dec['live_procedure'], why=dec['why'], secs=dec['secs'])


def set_procedure(choice, why, lab=None, day=None):
    """The owner's switch. refit / hold set procedure.json; plain / brain-on set use_brain.json. Logged in the ledger."""
    lab = lab or LAB
    if not why:
        raise SystemExit('--why "<reason>" is required')
    if choice in ('refit', 'hold'):
        write_json(os.path.join(lab, 'procedure.json'), dict(brain=choice, why=why, t=now_txt(), by='owner'))
    elif choice in ('plain', 'brain-on'):
        write_json(os.path.join(lab, 'use_brain.json'), dict(use=choice == 'brain-on', why=why, t=now_txt(), by='owner'))
    else:
        raise SystemExit('choose one of refit, hold, plain, brain-on')
    rows = read_ledger(lab)
    rows.append(dict(kind='owner', day=day or datetime.now(IST).strftime('%Y-%m-%d'), set=choice, why=why, written=now_txt()))
    write_ledger(lab, rows)
    return choice


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['--walk-one']:
        walk_one(*argv[1:5])
        return 0
    if '--set-procedure' in argv:
        i = argv.index('--set-procedure')
        why = argv[argv.index('--why') + 1] if '--why' in argv else None
        print('set:', set_procedure(argv[i + 1], why))
        return 0
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    online = True if '--online' in argv else (False if '--no-online' in argv else None)
    check_only = '--check-only' in argv
    lock = None
    if not check_only:                     # a hand run and the scheduled run never work on the ledger at once
        lock = day_lock()
        if lock is None:
            say(f'another nightly.py holds {os.path.join(LAB, "nightly_day.lock")}: nothing done')
            return 1
    try:
        r = run_day(args[0], force='--force' in argv, convert='--no-convert' not in argv and not check_only,
                    online=online, check_only=check_only)
    finally:
        if lock is not None:
            lock.release()
    return 0 if r['status'] in ('ok', 'skip', 'check') else 1


def day_lock(lab=None):
    """The OS lock on <lab>/nightly_day.lock (separate from nightly_all's data/nightly.lock, which the parent holds
    while it runs this script), or None when another process holds it. The OS frees it if the process dies."""
    rd = os.path.join(ROOT, 'research')
    if rd not in sys.path:
        sys.path.insert(0, rd)
    import nightly_all as NA
    lk = NA.Lock(os.path.join(lab or LAB, 'nightly_day.lock'))
    return lk if lk.acquire() else None


if __name__ == '__main__':
    sys.exit(main())
