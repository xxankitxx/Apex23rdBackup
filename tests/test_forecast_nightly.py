"""The one nightly runner and the Forecast Lab nightly (PKG-10, docs/53, rule PR-003).

Everything runs on synthetic sessions in a temporary folder with a stand-in trainer, so nothing here fits a real
model, reads a tape or touches data/. The back-fill test uses an extract of the walk files and the real docs/50."""
import json
import os
import sys
import time
import types
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for p in (os.path.join(ROOT, 'research', 'forecast_lab'), os.path.join(ROOT, 'research'), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
import backfill_ledger as BF  # noqa: E402
import nightly as N  # noqa: E402
import nightly_all as NA  # noqa: E402
import nightly_today as NT  # noqa: E402
from apex.forecast_lab import brain as B  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
DAYS = ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-09', '2026-11-11']


# ── a stand-in trainer: same interface as research/forecast_lab/train.py ─────────────────────────────────────────
def synth_day(day, n=360, scale=1.0, seed=None):
    rng = np.random.default_rng(seed if seed is not None else int(day.replace('-', '')))
    y, m, d = (int(x) for x in day.split('-'))
    t0 = datetime(y, m, d, 9, 30, tzinfo=IST).timestamp()
    t = t0 + np.arange(n) * 30.0
    vref = np.full(n, 0.5)
    Hs = np.asarray(B.H, float)
    var = vref[:, None] * Hs[None, :] * scale
    dF = rng.normal(0, 1, (n, len(B.H))) * np.sqrt(var)
    RV = var * np.exp(rng.normal(0, 0.3, (n, len(B.H))))
    X = rng.normal(0, 1, (n, B.NF))
    return dict(day=day, t=t, F=np.full(n, 24000.0), vref=vref, X=X, dF=dF, RV=RV)


class FakeTrainer(types.SimpleNamespace):
    """load(day) gives a synthetic session; fit(days) a brain object Brain() accepts. Days in self.bad get a
    shape so narrow that the 80 % range catches almost nothing on any unseen day."""

    def load(self, day):
        return synth_day(day)

    def fit(self, days):
        self.fits.append([d['day'] for d in days])
        return fake_brain([d['day'] for d in days], bad=days[-1]['day'] in self.bad)


def fake_brain(days, bad=False, bias=0.0):
    nf = B.NF
    qz = [-0.05, -0.02, 0.0, 0.02, 0.05] if bad else list(N.ZN)
    obj = dict(feats=B.FEATS, H=B.H, med=[0.0] * nf, sd=[1.0] * nf, vol=[[bias] + [0.0] * nf for _ in B.H],
               lin=[[0.0] * (nf + 1) for _ in B.H], gbm=[None] * len(B.H), qz=[qz for _ in B.H], volvol=[0.0] * len(B.H),
               iv={})
    h = __import__('hashlib').sha256(json.dumps([days, bad, bias]).encode()).hexdigest()[:12]
    obj['meta'] = dict(trained_through=days[-1], sessions=len(days), days=list(days), built='test', rows=1, hash=h)
    return obj


def make_lab(tmp_path, days=DAYS, bad=()):
    lab = tmp_path / 'forecast_lab'
    col = lab / 'collect'
    col.mkdir(parents=True)
    for d in days:
        (col / f'{d}.joblib').write_bytes(b'')
    T = FakeTrainer(COL=str(col), MIN_TRAIN=5, fits=[], bad=set(bad))
    return str(lab), T


def put_brain(lab, name, obj):
    import joblib
    joblib.dump(obj, os.path.join(lab, name), compress=3)


def live_hash(lab, name='brain.joblib'):
    obj, why = N.load_obj(os.path.join(lab, name))
    assert obj is not None, why
    return obj['meta']['hash'], obj['meta']['trained_through']


def run(lab, T, day, **kw):
    kw.setdefault('convert', False)
    kw.setdefault('online', False)
    return N.run_day(day, lab=lab, T=T, log=lambda m: None, **kw)


# ── idempotent, rollback, atomic ─────────────────────────────────────────────────────────────────────────────────
def test_second_run_same_day_is_noop(tmp_path):
    lab, T = make_lab(tmp_path)
    put_brain(lab, 'brain.joblib', fake_brain(DAYS[:5]))
    r = run(lab, T, DAYS[5])
    assert r['status'] == 'ok'
    assert live_hash(lab)[1] == DAYS[5]                       # tonight's refit is live
    assert live_hash(lab, 'brain_prev.joblib')[1] == DAYS[4]  # the brain that ran on the day is kept
    files = {f: open(os.path.join(lab, f), 'rb').read() for f in ('ledger.jsonl', 'brain.joblib', 'brain_prev.joblib', 'brain.meta.json')}
    fits = len(T.fits)
    r2 = run(lab, T, DAYS[5])
    assert r2['status'] == 'skip'
    assert len(T.fits) == fits
    for f, b in files.items():
        assert open(os.path.join(lab, f), 'rb').read() == b, f
    rows = N.read_ledger(lab)
    assert sum(1 for x in rows if x.get('kind') == 'decision') == 1
    meta = json.load(open(os.path.join(lab, 'brain.meta.json')))
    assert meta['trained_through'] == DAYS[5] and meta['feat_hash'] == N.feat_hash() and len(meta['c_h']) == len(B.H)
    assert 'sklearn' in meta and 'git' in meta
    # forced re-run: the incumbent is the brain recorded for that day, and brain_prev is never replaced by a
    # brain trained through the day itself
    r3 = run(lab, T, DAYS[5], force=True)
    assert r3['status'] == 'ok'
    assert live_hash(lab, 'brain_prev.joblib')[1] == DAYS[4]
    rows = N.read_ledger(lab)
    assert sum(1 for x in rows if x.get('kind') == 'decision') == 1
    inc = [x for x in rows if x.get('procedure') == 'P-incumbent' and x['day'] == DAYS[5]]
    assert inc and inc[0]['model']['trained_through'] == DAYS[4]


def test_refused_candidate_rolls_back_and_keeps_brain_prev(tmp_path):
    lab, T = make_lab(tmp_path, bad={DAYS[4]})
    good = fake_brain(DAYS[:4])
    bad = fake_brain(DAYS[:5], bad=True)
    put_brain(lab, 'brain_prev.joblib', good)
    put_brain(lab, 'brain.joblib', bad)
    r = run(lab, T, DAYS[5])
    assert r['status'] == 'ok'
    dec = [x for x in N.read_ledger(lab) if x.get('kind') == 'decision'][-1]
    assert dec['held_out']['ok'] is False and 'caught' in dec['held_out']['why']
    assert 'rolled back' in dec['brain_action']
    assert live_hash(lab) == (good['meta']['hash'], DAYS[3])             # the better, older brain is live again
    assert live_hash(lab, 'brain_prev.joblib') == (good['meta']['hash'], DAYS[3])   # and brain_prev is kept
    assert N.find_archived(lab, bad['meta']['hash'])                      # the loser is archived, not lost
    assert not N.find_archived(lab, fake_brain(DAYS[:6])['meta']['hash'])  # tonight's refit was not installed
    meta = json.load(open(os.path.join(lab, 'brain.meta.json')))
    assert meta['rolled_back_from'] == bad['meta']['hash']


def test_crash_between_tmp_and_replace_leaves_old_brain_loadable(tmp_path, monkeypatch):
    lab, T = make_lab(tmp_path)
    old = fake_brain(DAYS[:4])
    new = fake_brain(DAYS[:5])
    put_brain(lab, 'brain.joblib', old)
    src = N.archive(lab, new)
    real = os.replace

    def crash(a, b):
        if str(b).endswith('brain.joblib'):
            raise OSError('power cut')
        return real(a, b)
    monkeypatch.setattr(N.os, 'replace', crash)
    with pytest.raises(OSError):
        N.install(lab, src, DAYS[5], log=lambda m: None)
    monkeypatch.setattr(N.os, 'replace', real)
    assert live_hash(lab) == (old['meta']['hash'], DAYS[3])                 # the old brain still loads
    assert os.path.exists(os.path.join(lab, 'brain.joblib.tmp'))             # a left-over temp file ...
    assert 'installed' in N.install(lab, src, DAYS[5], log=lambda m: None)   # ... does not stop the next install
    assert live_hash(lab) == (new['meta']['hash'], DAYS[4])
    # a torn file is never installed: the archive copy is verified first
    with open(src, 'r+b') as f:
        f.truncate(50)
    with pytest.raises(RuntimeError):
        N.install(lab, src, DAYS[6], log=lambda m: None)
    assert live_hash(lab) == (new['meta']['hash'], DAYS[4])


def test_archive_never_overwrites(tmp_path):
    lab, _ = make_lab(tmp_path)
    obj = fake_brain(DAYS[:5])
    p = N.archive(lab, obj)
    before = os.path.getmtime(p), open(p, 'rb').read()
    time.sleep(0.05)
    assert N.archive(lab, obj) == p
    assert (os.path.getmtime(p), open(p, 'rb').read()) == before
    assert os.path.basename(p) == f"brain_{DAYS[4]}_{obj['meta']['hash']}.joblib"


# ── catch-up ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_catch_up_processes_two_missing_days_in_order(tmp_path):
    lab, T = make_lab(tmp_path)
    put_brain(lab, 'brain.joblib', fake_brain(DAYS[:5]))
    json.dump(dict(trained_through=DAYS[4]), open(os.path.join(lab, 'brain.meta.json'), 'w'))
    ticks = tmp_path / 'ticks'
    ticks.mkdir()
    for d in DAYS:
        (ticks / f'{d}.jsonl.gz').write_bytes(b'')
    late = datetime(2026, 11, 11, 17, 0, tzinfo=IST)
    early = datetime(2026, 11, 11, 15, 0, tzinfo=IST)
    days, notes = NT.missing_days(lab, str(ticks), now=late)
    assert days == DAYS[5:7]
    d2, notes2 = NT.missing_days(lab, str(ticks), now=early)
    assert d2 == [DAYS[5]] and 'before 15:45' in notes2[0]
    root = tmp_path / 'repo'
    (root / 'research' / 'forecast_lab').mkdir(parents=True)
    (root / 'research' / 'forecast_lab' / 'nightly.py').write_text('# stand-in')
    calls = []

    def runner(cmd, **kw):
        day = cmd[-1]
        calls.append((os.path.basename(cmd[-2]), day))
        r = N.run_day(day, lab=lab, T=T, convert=False, online=False, log=lambda m: None)
        return types.SimpleNamespace(returncode=0 if r['status'] == 'ok' else 1)
    data = os.path.dirname(lab)
    rc = NA.main([], now=late, data=data, root=str(root), runner=runner, ticks=str(ticks), sleep=lambda s: None)
    assert rc == 0
    assert calls == [('nightly.py', DAYS[5]), ('nightly.py', DAYS[6])]
    dec = [x['day'] for x in N.read_ledger(lab) if x.get('kind') == 'decision']
    assert dec == DAYS[5:7]
    assert live_hash(lab)[1] == DAYS[6]
    st = json.load(open(os.path.join(data, 'nightly_status.json')))
    assert st['processed_days'] == DAYS[5:7] and st['outcome'] == 'ok'
    assert st['steps'][f'{DAYS[5]} hazard']['status'] == 'skip'
    assert st['steps'][f'{DAYS[5]} replay_parity']['status'] == 'skip'
    # nothing left: a second run does nothing
    assert NT.missing_days(lab, str(ticks), now=late)[0] == []


def test_failed_day_stops_the_catch_up(tmp_path):
    root = tmp_path / 'repo'
    (root / 'research' / 'forecast_lab').mkdir(parents=True)
    (root / 'research' / 'forecast_lab' / 'nightly.py').write_text('# stand-in')
    calls = []

    def runner(cmd, **kw):
        calls.append(cmd[-1])
        return types.SimpleNamespace(returncode=1)
    data = str(tmp_path / 'data')
    rc = NA.main([], now=datetime(2026, 11, 11, 17, 0, tzinfo=IST), data=data, root=str(root), runner=runner,
                 days=DAYS[5:7], sleep=lambda s: None)
    assert rc == 1 and calls == [DAYS[5]]
    st = json.load(open(os.path.join(data, 'nightly_status.json')))
    assert st['missed_days'] == DAYS[5:7] and st['outcome'].startswith('failed')


# ── the rule (PR-003) ───────────────────────────────────────────────────────────────────────────────────────────
def row(day, proc, basis, score, walk=False, hscale=1.0):
    hs = {str(h): dict(n=100, is80=score * 100 * (hscale if h != N.PRIMARY_H else 1.0), inside=80.0) for h in B.H}
    return N.score_row(day, proc, basis, hs, walk=walk, dte=3)


def test_decision_rule_fast_off(tmp_path):
    days = [f'2026-10-{x:02d}' for x in (20, 21, 22, 23, 26)]
    lose = [row(d, 'P-incumbent', 'online', 11.0 if i != 2 else 9.0, walk=True) for i, d in enumerate(days)]
    plain = [row(d, 'P-plain', 'online', 10.0, walk=True) for d in days]
    fo = N.fast_off(lose + plain, days[-1])
    assert fo['hit'] and fo['lost'] == 4 and fo['of'] == 5
    dec = N.decide(lose + plain, days[-1], dict(brain='refit', use_brain=True))
    assert dec['use_brain'] is False and dec['live_procedure'] == 'P-plain' and dec['actions']
    three = [row(d, 'P-incumbent', 'online', 11.0 if i < 3 else 9.0, walk=True) for i, d in enumerate(days)]
    assert not N.fast_off(three + plain, days[-1])['hit']
    # only the last five days count
    old = [row('2026-10-1' + str(k), 'P-incumbent', 'online', 99.0) for k in range(5)] + \
          [row('2026-10-1' + str(k), 'P-plain', 'online', 1.0) for k in range(5)]
    assert not N.fast_off(old + three + plain, days[-1])['hit']
    # end to end: four losing walk days in the ledger and one more night -> use_brain.json is switched off
    lab, T = make_lab(tmp_path)
    put_brain(lab, 'brain.joblib', fake_brain(DAYS[:5]))
    seed = []
    for d in ('2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30'):
        seed += [row(d, 'P-incumbent', 'online', 1e6, walk=True), row(d, 'P-plain', 'online', 1.0, walk=True)]
    N.write_ledger(lab, seed)
    r = run(lab, T, DAYS[5])
    assert r['status'] == 'ok' and r['decision'] == 'P-plain'
    u = json.load(open(os.path.join(lab, 'use_brain.json')))
    assert u['use'] is False and u['rule'] == 'PR-003' and 'of the last 5 days' in u['why'] and 'rule: 4 of 5' in u['why']


def test_slow_on_bootstrap(tmp_path):
    rng = np.random.default_rng(3)
    days = [f'2026-12-{x:02d}' for x in range(1, 13)]
    good = [row(d, 'P-candidate', 'online', 10.0 * (0.95 + rng.normal(0, 0.01)), hscale=0.9) for d in days]
    plain = [row(d, 'P-plain', 'online', 10.0) for d in days]
    b = N.better(good + plain, days[-1], 'P-candidate')
    assert b['met'] and b['n'] == 12 and b['interval'][1] < 0 and b['horizons_better'] >= 4
    assert not N.better(good[:9] + plain[:9], days[8], 'P-candidate')['met']           # fewer than 10 common days
    mixed = [row(d, 'P-candidate', 'online', 10.0 * (0.8 if i % 2 else 1.2)) for i, d in enumerate(days)]
    assert not N.better(mixed + plain, days[-1], 'P-candidate')['met']                 # interval includes 0
    walk = [dict(r, walk=True) for r in good]
    assert not N.better(walk + plain, days[-1], 'P-candidate')['met']                 # walk days never switch on
    dec = N.decide(good + plain, days[-1], dict(brain='refit', use_brain=False))
    assert dec['use_brain'] is False and dec['live_procedure'] == 'P-plain'           # proposed, never applied
    assert dec['proposals'] and dec['proposals'][0].startswith('slow-on')
    assert N.boot_interval([0.1] * 10) == (pytest.approx(0.1), pytest.approx(0.1))


def test_offline_scores_and_mean_correction():
    d = synth_day('2026-11-04', n=2000, scale=1.3)
    V = N.clock_var(d)
    hs, blocks = N.score(d, V, [N.ZN] * len(B.H))
    r = hs[str(N.PRIMARY_H)]
    assert r['n'] == 2000 and 0.6 < r['inside'] / r['n'] < 0.85               # clock too narrow by sqrt(1.3)
    assert sum(blocks['n']) == r['n'] and len(blocks['is80']) == 13
    c = N.mean_ratio([d], N.clock_var)
    assert np.all(c > 1.2)                                                     # RV is 1.3x the clock on average
    hs2, _ = N.score(d, V, [N.ZN] * len(B.H), c)
    assert hs2['300']['qlike_c'] < hs2['300']['qlike']                         # the corrected forecast scores better
    pc = N.fit_plain_cal([synth_day(x, scale=1.3) for x in DAYS[:4]])
    assert np.array(pc['table']).shape == (len(B.H), B.N_TOD)
    assert abs(float(np.mean(pc['table'][3])) - np.log(1.3) + 0.045) < 0.15   # geometric mean of RV/clock
    hs3, _ = N.score(d, N.plaincal_var(pc, d), pc['zq'], pc['c'])
    assert abs(hs3['300']['inside'] / hs3['300']['n'] - 0.8) < 0.05


def test_held_out_check():
    good = fake_brain(DAYS[:4])
    d = synth_day(DAYS[4])
    hs, _ = N.score(d, N.brain_var(good, d), good['qz'])
    assert N.held_out(good, hs)[0]
    bad = fake_brain(DAYS[:4], bad=True)
    hs, _ = N.score(d, N.brain_var(bad, d), bad['qz'])
    ok, why = N.held_out(bad, hs)
    assert not ok and 'must be 65 to 95' in why
    nan = fake_brain(DAYS[:4])
    nan['vol'][0][0] = float('nan')
    assert N.held_out(nan, hs) == (False, 'a fitted weight is not finite')


def test_ledger_tolerates_a_torn_line(tmp_path):
    lab = str(tmp_path)
    N.write_ledger(lab, [dict(kind='decision', rule='PR-003', day='2026-11-11')])
    with open(N.ledger_path(lab), 'a', encoding='utf-8') as f:
        f.write('{"kind": "sco')
    rows = N.read_ledger(lab)
    assert len(rows) == 1 and N.decision_days(rows) == {'2026-11-11'}


def test_owner_switch_is_logged(tmp_path):
    lab = str(tmp_path)
    N.set_procedure('plain', 'testing the switch', lab=lab, day='2026-11-12')
    assert json.load(open(os.path.join(lab, 'use_brain.json')))['use'] is False
    N.set_procedure('hold', 'freeze', lab=lab, day='2026-11-12')
    assert N.read_procedure(lab) == dict(brain='hold', use_brain=False)
    assert [r['set'] for r in N.read_ledger(lab)] == ['plain', 'hold']
    with pytest.raises(SystemExit):
        N.set_procedure('plain', '', lab=lab)


def test_parity_against_live_record():
    sv = dict(fut=[dict(h=300, n=4000, cov=0.80, crps=11.0, width=48.0)])
    live = dict(score=dict(fut=[dict(h=300, n=3990, cov=0.79, crps=11.2, width=47.0)]), restarts=0)
    p = N.parity(live, sv)
    assert p['ok'] is True and p['cov_diff'] == -0.01
    live['score']['fut'][0]['crps'] = 12.0
    assert N.parity(live, sv)['ok'] is False
    assert N.parity({}, sv)['ok'] is None


def test_online_rows_from_a_score_view():
    sv = dict(fut=[dict(h=300, n=200, cov=0.8, crps=10.0, crps_plain=10.5, width=40.0, pin=6.0)],
              opt=[dict(h=300, n=50, cov=0.79, pin=2.0, width=12.0, err=3.4, err_naive=3.4, brier=0.25, brier_base=0.25)])
    hs = N.online_hs(sv)
    assert hs['300']['is80'] == pytest.approx(10 * 6.0 * 200)
    r = N.score_row('2026-11-12', 'P-plain', 'online', hs, option=N.option_side(sv))
    assert r['primary'] == pytest.approx(60.0) and r['option'][0]['err_naive'] == 3.4


def test_walk_state_chain(tmp_path):
    lab = str(tmp_path)
    os.makedirs(os.path.join(lab, 'nightly_walk'))
    assert N.walk_state_in(lab, 'P-plain', '2026-11-12') == (None, 'cold')
    open(os.path.join(lab, 'state_warm.json'), 'w').write('{}')
    assert N.walk_state_in(lab, 'P-plain', '2026-11-12')[1] == 'warm'
    for f in ('P-plain_2026-11-11.json', 'P-plain_2026-11-11.out.json', 'P-plain_2026-11-12.json'):
        open(os.path.join(lab, 'nightly_walk', f), 'w').write('{}')
    p, src = N.walk_state_in(lab, 'P-plain', '2026-11-12')
    assert src == 'chained' and p.endswith('P-plain_2026-11-11.json')


# ── the runner's guards ─────────────────────────────────────────────────────────────────────────────────────────
def test_refuses_market_hours_and_waits_for_replay_lock(tmp_path):
    root = tmp_path / 'repo'
    (root / 'research' / 'forecast_lab').mkdir(parents=True)
    (root / 'research' / 'forecast_lab' / 'nightly.py').write_text('# stand-in')
    data = str(tmp_path / 'data')
    calls, sleeps = [], []

    def runner(cmd, **kw):
        calls.append(cmd[-1])
        return types.SimpleNamespace(returncode=0)
    wed_11 = datetime(2026, 11, 11, 11, 0, tzinfo=IST)
    assert NA.main([], now=wed_11, data=data, root=str(root), runner=runner, days=[DAYS[6]]) == 0
    assert calls == [] and json.load(open(os.path.join(data, 'nightly_status.json')))['outcome'] == 'refused: market hours'
    sat = datetime(2026, 11, 14, 11, 0, tzinfo=IST)                       # not a trading day: allowed
    assert not NA.market_hours(sat) and NA.market_hours(wed_11)
    assert not NA.market_hours(datetime(2026, 11, 10, 11, 0, tzinfo=IST))  # NSE holiday
    NA.main(['--force'], now=wed_11, data=data, root=str(root), runner=runner, days=[DAYS[6]], sleep=lambda s: None)
    assert calls == [DAYS[6]]
    # a running replay: wait, then go once it finishes
    run_dir = root / 'data' / 'replay' / 'batch' / 'p99_g1'
    run_dir.mkdir(parents=True)
    man = run_dir / 'manifest.json'
    man.write_text(json.dumps(dict(status='running')))

    def sleep(s):
        sleeps.append(s)
        man.write_text(json.dumps(dict(status='ok')))
    calls.clear()
    eve = datetime(2026, 11, 11, 17, 0, tzinfo=IST)
    assert NA.main([], now=eve, data=data, root=str(root), runner=runner, days=[DAYS[6]], sleep=sleep) == 0
    assert sleeps == [NA.POLL_S] and calls == [DAYS[6]]
    # still running after the wait: skipped and said so
    man.write_text(json.dumps(dict(status='running')))
    calls.clear()
    NA.main(['--max-wait-min', '1'], now=eve, data=data, root=str(root), runner=runner, days=[DAYS[6]], sleep=lambda s: None)
    st = json.load(open(os.path.join(data, 'nightly_status.json')))
    assert calls == [] and st['outcome'].startswith('skipped: replay running') and 'p99_g1' in st['outcome']
    # a crashed replay's stale manifest does not block
    old = time.time() - 3 * 3600
    os.utime(man, (old, old))
    assert NA.running_replays(str(root / 'data' / 'replay' / 'batch')) == ([], ['p99_g1'])
    # the live Forecast Lab's lock, and a second nightly
    lk = NA.Lock(os.path.join(data, 'forecast_lab', 'live.lock'))
    assert lk.acquire()
    try:
        assert NA.busy(data, str(root / 'data' / 'replay' / 'batch')) == 'the live Forecast Lab is running'
    finally:
        lk.release()
    assert NA.busy(data, str(root / 'data' / 'replay' / 'batch')) is None
    other = NA.Lock(os.path.join(data, 'nightly.lock'))
    assert other.acquire()
    try:
        calls.clear()
        assert NA.main([], now=eve, data=data, root=str(root), runner=runner, days=[DAYS[6]], sleep=lambda s: None) == 0
        assert calls == []
    finally:
        other.release()


def test_owner_ok_gates_the_replay_parity_step(tmp_path):
    root = tmp_path / 'repo'
    for s in ('research/forecast_lab/nightly.py', 'research/conductor/parity.py'):
        p = root / s
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('# stand-in')
    data = tmp_path / 'data'
    data.mkdir()
    seen = []

    def runner(cmd, **kw):
        seen.append(os.path.basename(cmd[-2]))
        return types.SimpleNamespace(returncode=0)
    eve = datetime(2026, 11, 11, 17, 0, tzinfo=IST)
    NA.main([], now=eve, data=str(data), root=str(root), runner=runner, days=[DAYS[6]], sleep=lambda s: None)
    assert seen == ['nightly.py']
    (data / 'nightly_owner_ok.json').write_text(json.dumps(dict(replay_parity=True)))
    seen.clear()
    NA.main([], now=eve, data=str(data), root=str(root), runner=runner, days=[DAYS[6]], sleep=lambda s: None)
    assert seen == ['nightly.py', 'parity.py']
    st = json.load(open(data / 'nightly_status.json'))
    assert st['history']['lab'] >= 0 and st['planned_end']


# ── the back-fill ───────────────────────────────────────────────────────────────────────────────────────────────
WALK_FIXTURE = json.loads((
    '{"brain":{"2026-10-27":{"score":{"fut":[{"h":60,"n":4272,"cov":0.797,"width":21.86,"pin":3.3229,"crps":5.004'
    '5,"crps_plain":5.2794},{"h":300,"n":4176,"cov":0.766,"width":47.7,"pin":7.8594,"crps":11.3943,"crps_plain":1'
    '1.9027},{"h":600,"n":4094,"cov":0.708,"width":62.24,"pin":10.995,"crps":15.9966,"crps_plain":16.6633},{"h":1'
    '800,"n":3854,"cov":0.641,"width":99.69,"pin":21.1773,"crps":28.792,"crps_plain":28.8737}],"opt":[{"h":60,"n"'
    ':2496,"cov":0.796,"width":16.76,"pin":2.4967,"err":5.19,"err_naive":5.19},{"h":300,"n":2465,"cov":0.786,"wid'
    'th":42.39,"pin":6.3098,"err":11.93,"err_naive":12.03},{"h":600,"n":2450,"cov":0.785,"width":61.26,"pin":9.69'
    '02,"err":18.03,"err_naive":18.12},{"h":1800,"n":2450,"cov":0.784,"width":112.79,"pin":17.7545,"err":32.85,"e'
    'rr_naive":31.96}]}},"2026-10-28":{"score":{"fut":[{"h":60,"n":4258,"cov":0.808,"width":23.76,"pin":3.1925,"c'
    'rps":4.707,"crps_plain":4.7823},{"h":300,"n":4162,"cov":0.833,"width":59.64,"pin":7.4905,"crps":10.975,"crps'
    '_plain":10.8101},{"h":600,"n":4081,"cov":0.861,"width":89.63,"pin":10.7552,"crps":15.8594,"crps_plain":15.31'
    '28},{"h":1800,"n":3842,"cov":0.856,"width":177.71,"pin":21.171,"crps":28.9207,"crps_plain":26.509}],"opt":[{'
    '"h":60,"n":2844,"cov":0.807,"width":6.96,"pin":0.9241,"err":1.8,"err_naive":1.79},{"h":300,"n":2780,"cov":0.'
    '824,"width":18.99,"pin":2.3266,"err":3.84,"err_naive":3.81},{"h":600,"n":2726,"cov":0.846,"width":31.91,"pin'
    '":3.6401,"err":5.53,"err_naive":5.42},{"h":1800,"n":2568,"cov":0.873,"width":70.51,"pin":7.515,"err":9.96,"e'
    'rr_naive":9.16}]}},"2026-10-29":{"score":{"fut":[{"h":60,"n":4333,"cov":0.803,"width":18.12,"pin":2.567,"crp'
    's":3.8735,"crps_plain":3.9715},{"h":300,"n":4286,"cov":0.803,"width":37.64,"pin":5.7405,"crps":8.2907,"crps_'
    'plain":8.5409},{"h":600,"n":4226,"cov":0.774,"width":52.3,"pin":8.2455,"crps":12.0751,"crps_plain":12.3893},'
    '{"h":1800,"n":3986,"cov":0.792,"width":115.27,"pin":15.4453,"crps":23.4836,"crps_plain":23.4558}],"opt":[{"h'
    '":60,"n":2887,"cov":0.803,"width":6.24,"pin":0.882,"err":1.85,"err_naive":1.84},{"h":300,"n":2855,"cov":0.80'
    '7,"width":13.03,"pin":1.9023,"err":3.65,"err_naive":3.64},{"h":600,"n":2815,"cov":0.799,"width":21.16,"pin":'
    '2.9388,"err":5.3,"err_naive":5.29},{"h":1800,"n":2655,"cov":0.746,"width":48.73,"pin":7.3858,"err":10.77,"er'
    'r_naive":10.7}]}},"2026-10-30":{"score":{"fut":[{"h":60,"n":4357,"cov":0.797,"width":19.14,"pin":2.7084,"crp'
    's":4.106,"crps_plain":4.2636},{"h":300,"n":4309,"cov":0.784,"width":39.02,"pin":5.626,"crps":8.841,"crps_pla'
    'in":9.1321},{"h":600,"n":4249,"cov":0.783,"width":57.69,"pin":7.6897,"crps":12.2548,"crps_plain":12.4353},{"'
    'h":1800,"n":4009,"cov":0.811,"width":123.02,"pin":14.6307,"crps":24.987,"crps_plain":24.321}],"opt":[{"h":60'
    ',"n":2904,"cov":0.793,"width":7.86,"pin":1.0985,"err":2.4,"err_naive":2.39},{"h":300,"n":2872,"cov":0.791,"w'
    'idth":16.8,"pin":2.3355,"err":4.98,"err_naive":4.98},{"h":600,"n":2832,"cov":0.799,"width":27.44,"pin":3.561'
    '2,"err":6.7,"err_naive":6.72},{"h":1800,"n":2672,"cov":0.792,"width":65.95,"pin":9.1626,"err":13.81,"err_nai'
    've":13.59}]}},"2026-11-02":{"score":{"fut":[{"h":60,"n":4316,"cov":0.808,"width":16.94,"pin":2.3409,"crps":3'
    '.5308,"crps_plain":4.3762},{"h":300,"n":4268,"cov":0.804,"width":42.08,"pin":5.7121,"crps":8.5007,"crps_plai'
    'n":9.9135},{"h":600,"n":4208,"cov":0.811,"width":63.19,"pin":8.4005,"crps":12.4668,"crps_plain":14.438},{"h"'
    ':1800,"n":3970,"cov":0.783,"width":131.43,"pin":16.5449,"crps":23.6594,"crps_plain":26.8014}],"opt":[{"h":60'
    ',"n":2880,"cov":0.802,"width":9.05,"pin":1.2503,"err":2.6,"err_naive":2.58},{"h":300,"n":2848,"cov":0.805,"w'
    'idth":22.14,"pin":3.0335,"err":5.88,"err_naive":5.89},{"h":600,"n":2808,"cov":0.808,"width":32.69,"pin":4.25'
    '57,"err":8.85,"err_naive":8.82},{"h":1800,"n":2650,"cov":0.751,"width":60.11,"pin":8.2406,"err":16.04,"err_n'
    'aive":16.02}]}},"2026-11-03":{"score":{"fut":[{"h":60,"n":4356,"cov":0.807,"width":17.06,"pin":2.4326,"crps"'
    ':3.667,"crps_plain":4.8249},{"h":300,"n":4310,"cov":0.794,"width":38.56,"pin":5.498,"crps":8.0098,"crps_plai'
    'n":10.556},{"h":600,"n":4250,"cov":0.776,"width":59.4,"pin":7.7689,"crps":11.91,"crps_plain":15.1301},{"h":1'
    '800,"n":4010,"cov":0.913,"width":132.97,"pin":14.1601,"crps":19.6043,"crps_plain":25.267}],"opt":[{"h":60,"n'
    '":2558,"cov":0.796,"width":14.57,"pin":2.1113,"err":4.26,"err_naive":4.22},{"h":300,"n":2558,"cov":0.797,"wi'
    'dth":30.6,"pin":4.6186,"err":8.37,"err_naive":8.38},{"h":600,"n":2558,"cov":0.812,"width":48.9,"pin":6.5613,'
    '"err":12.33,"err_naive":12.15},{"h":1800,"n":2558,"cov":0.833,"width":118.27,"pin":13.3706,"err":19.05,"err_'
    'naive":18.88}]}},"2026-11-04":{"score":{"fut":[{"h":60,"n":4338,"cov":0.799,"width":22.14,"pin":3.0257,"crps'
    '":4.6741,"crps_plain":4.8121},{"h":300,"n":4289,"cov":0.806,"width":49.44,"pin":7.2375,"crps":11.2138,"crps_'
    'plain":11.2989},{"h":600,"n":4231,"cov":0.834,"width":78.79,"pin":10.7099,"crps":16.6138,"crps_plain":16.587'
    '7},{"h":1800,"n":3991,"cov":0.771,"width":110.43,"pin":16.4875,"crps":26.2433,"crps_plain":26.6011}],"opt":['
    '{"h":60,"n":2900,"cov":0.801,"width":6.4,"pin":0.8659,"err":1.9,"err_naive":1.9},{"h":300,"n":2868,"cov":0.7'
    '98,"width":16.3,"pin":2.2548,"err":4.38,"err_naive":4.38},{"h":600,"n":2830,"cov":0.806,"width":26.97,"pin":'
    '3.6666,"err":6.58,"err_naive":6.55},{"h":1800,"n":2670,"cov":0.747,"width":49.22,"pin":7.0702,"err":10.7,"er'
    'r_naive":10.71}]}},"2026-11-05":{"score":{"fut":[{"h":60,"n":4331,"cov":0.803,"width":18.41,"pin":2.5134,"cr'
    'ps":3.7993,"crps_plain":4.5312},{"h":300,"n":4283,"cov":0.793,"width":42.91,"pin":5.6875,"crps":8.9464,"crps'
    '_plain":10.5411},{"h":600,"n":4223,"cov":0.784,"width":56.91,"pin":8.2401,"crps":12.742,"crps_plain":15.1955'
    '},{"h":1800,"n":3983,"cov":0.75,"width":96.33,"pin":16.4665,"crps":22.5274,"crps_plain":27.1966}],"opt":[{"h'
    '":60,"n":2888,"cov":0.801,"width":6.23,"pin":0.8637,"err":1.74,"err_naive":1.74},{"h":300,"n":2856,"cov":0.8'
    '05,"width":15.7,"pin":2.0221,"err":4.09,"err_naive":4.08},{"h":600,"n":2816,"cov":0.811,"width":22.66,"pin":'
    '2.9417,"err":5.81,"err_naive":5.81},{"h":1800,"n":2656,"cov":0.782,"width":57.37,"pin":8.0604,"err":9.88,"er'
    'r_naive":9.57}]}},"2026-11-06":{"score":{"fut":[{"h":60,"n":4315,"cov":0.8,"width":27.58,"pin":3.9014,"crps"'
    ':5.8678,"crps_plain":6.6574},{"h":300,"n":4246,"cov":0.795,"width":61.53,"pin":8.9318,"crps":13.3126,"crps_p'
    'lain":14.9884},{"h":600,"n":4186,"cov":0.8,"width":88.62,"pin":12.8175,"crps":19.4037,"crps_plain":22.0396},'
    '{"h":1800,"n":3948,"cov":0.744,"width":156.18,"pin":20.3704,"crps":34.1596,"crps_plain":41.0803}],"opt":[{"h'
    '":60,"n":2878,"cov":0.798,"width":8.15,"pin":1.1808,"err":2.46,"err_naive":2.45},{"h":300,"n":2832,"cov":0.7'
    '96,"width":19.14,"pin":2.9867,"err":5.58,"err_naive":5.6},{"h":600,"n":2791,"cov":0.79,"width":28.54,"pin":4'
    '.5331,"err":8.14,"err_naive":8.26},{"h":1800,"n":2634,"cov":0.702,"width":56.02,"pin":9.0881,"err":15.06,"er'
    'r_naive":15.6}]}},"2026-11-09":{"score":{"fut":[{"h":60,"n":4349,"cov":0.799,"width":27.37,"pin":3.8035,"crp'
    's":5.953,"crps_plain":6.4111},{"h":300,"n":4301,"cov":0.83,"width":63.55,"pin":8.7982,"crps":13.2514,"crps_p'
    'lain":14.102},{"h":600,"n":4241,"cov":0.864,"width":98.01,"pin":12.617,"crps":18.8625,"crps_plain":19.6655},'
    '{"h":1800,"n":4001,"cov":0.952,"width":196.65,"pin":22.0211,"crps":31.1622,"crps_plain":32.9274}],"opt":[{"h'
    '":60,"n":2553,"cov":0.803,"width":19.04,"pin":2.6786,"err":5.83,"err_naive":5.79},{"h":300,"n":2553,"cov":0.'
    '814,"width":46.19,"pin":6.4877,"err":12.67,"err_naive":12.68},{"h":600,"n":2553,"cov":0.825,"width":71.07,"p'
    'in":9.6594,"err":18.1,"err_naive":18.03},{"h":1800,"n":2552,"cov":0.795,"width":188.45,"pin":25.1088,"err":3'
    '0.63,"err_naive":31.02}]}},"2026-11-11":{"score":{"fut":[{"h":60,"n":4335,"cov":0.802,"width":22.53,"pin":3.'
    '0936,"crps":4.7984,"crps_plain":4.9461},{"h":300,"n":4287,"cov":0.771,"width":48.56,"pin":7.8315,"crps":11.4'
    '828,"crps_plain":11.4922},{"h":600,"n":4227,"cov":0.719,"width":63.28,"pin":11.498,"crps":17.322,"crps_plain'
    '":17.2247},{"h":1800,"n":3987,"cov":0.736,"width":116.6,"pin":20.2993,"crps":27.8321,"crps_plain":27.3932}],'
    '"opt":[{"h":60,"n":2892,"cov":0.81,"width":5.61,"pin":0.736,"err":1.51,"err_naive":1.51},{"h":300,"n":2860,"'
    'cov":0.831,"width":13.45,"pin":1.8237,"err":3.45,"err_naive":3.44},{"h":600,"n":2820,"cov":0.846,"width":21.'
    '73,"pin":2.6389,"err":5.16,"err_naive":5.12},{"h":1800,"n":2660,"cov":0.789,"width":47.86,"pin":6.523,"err":'
    '8.06,"err_naive":8.01}]}}},"plain":{"2026-10-27":{"score":{"fut":[{"h":60,"n":4272,"cov":0.796,"width":21.85'
    ',"pin":3.3186,"crps":4.9884,"crps_plain":5.2794},{"h":300,"n":4176,"cov":0.787,"width":51.18,"pin":7.7162,"c'
    'rps":11.5084,"crps_plain":11.9027},{"h":600,"n":4094,"cov":0.754,"width":70.39,"pin":10.5117,"crps":16.4843,'
    '"crps_plain":16.6633},{"h":1800,"n":3854,"cov":0.788,"width":120.72,"pin":19.4856,"crps":28.4391,"crps_plain'
    '":28.8737}],"opt":[{"h":60,"n":2496,"cov":0.797,"width":16.56,"pin":2.4899,"err":5.19,"err_naive":5.19},{"h"'
    ':300,"n":2465,"cov":0.793,"width":42.83,"pin":6.28,"err":12.04,"err_naive":12.03},{"h":600,"n":2450,"cov":0.'
    '799,"width":66.58,"pin":9.0898,"err":18.07,"err_naive":18.12},{"h":1800,"n":2450,"cov":0.816,"width":151.56,'
    '"pin":18.8425,"err":32.19,"err_naive":31.96}]}},"2026-10-28":{"score":{"fut":[{"h":60,"n":4258,"cov":0.805,"'
    'width":20.66,"pin":2.9744,"crps":4.4885,"crps_plain":4.7823},{"h":300,"n":4162,"cov":0.803,"width":50.42,"pi'
    'n":6.9234,"crps":10.5301,"crps_plain":10.8101},{"h":600,"n":4081,"cov":0.799,"width":69.46,"pin":9.5957,"crp'
    's":15.0362,"crps_plain":15.3128},{"h":1800,"n":3842,"cov":0.838,"width":116.99,"pin":17.351,"crps":26.0041,"'
    'crps_plain":26.509}],"opt":[{"h":60,"n":2844,"cov":0.824,"width":7.61,"pin":0.9657,"err":1.79,"err_naive":1.'
    '79},{"h":300,"n":2780,"cov":0.834,"width":20.57,"pin":2.4447,"err":3.84,"err_naive":3.81},{"h":600,"n":2726,'
    '"cov":0.85,"width":34.65,"pin":3.9268,"err":5.51,"err_naive":5.42},{"h":1800,"n":2568,"cov":0.852,"width":49'
    '.94,"pin":5.484,"err":9.92,"err_naive":9.16}]}},"2026-10-29":{"score":{"fut":[{"h":60,"n":4333,"cov":0.804,"'
    'width":17.8,"pin":2.5654,"crps":3.892,"crps_plain":3.9715},{"h":300,"n":4286,"cov":0.81,"width":37.85,"pin":'
    '5.7324,"crps":8.2749,"crps_plain":8.5409},{"h":600,"n":4226,"cov":0.781,"width":53.53,"pin":8.2777,"crps":12'
    '.0534,"crps_plain":12.3893},{"h":1800,"n":3986,"cov":0.687,"width":93.35,"pin":14.7925,"crps":23.2237,"crps_'
    'plain":23.4558}],"opt":[{"h":60,"n":2887,"cov":0.803,"width":6.19,"pin":0.8795,"err":1.85,"err_naive":1.84},'
    '{"h":300,"n":2855,"cov":0.809,"width":12.99,"pin":1.9172,"err":3.64,"err_naive":3.64},{"h":600,"n":2815,"cov'
    '":0.8,"width":21.73,"pin":2.9898,"err":5.27,"err_naive":5.29},{"h":1800,"n":2655,"cov":0.748,"width":50.02,"'
    'pin":7.418,"err":10.74,"err_naive":10.7}]}},"2026-10-30":{"score":{"fut":[{"h":60,"n":4357,"cov":0.796,"widt'
    'h":18.5,"pin":2.6762,"crps":4.1048,"crps_plain":4.2636},{"h":300,"n":4309,"cov":0.774,"width":39.36,"pin":5.'
    '6149,"crps":8.979,"crps_plain":9.1321},{"h":600,"n":4249,"cov":0.789,"width":58.43,"pin":7.7212,"crps":12.23'
    '81,"crps_plain":12.4353},{"h":1800,"n":4009,"cov":0.783,"width":116.5,"pin":14.641,"crps":24.6164,"crps_plai'
    'n":24.321}],"opt":[{"h":60,"n":2904,"cov":0.793,"width":7.63,"pin":1.0803,"err":2.4,"err_naive":2.39},{"h":3'
    '00,"n":2872,"cov":0.79,"width":16.71,"pin":2.3161,"err":4.99,"err_naive":4.98},{"h":600,"n":2832,"cov":0.804'
    ',"width":26.75,"pin":3.4427,"err":6.72,"err_naive":6.72},{"h":1800,"n":2672,"cov":0.789,"width":68.57,"pin":'
    '9.4123,"err":13.66,"err_naive":13.59}]}},"2026-11-02":{"score":{"fut":[{"h":60,"n":4316,"cov":0.81,"width":1'
    '7.14,"pin":2.332,"crps":3.6483,"crps_plain":4.3762},{"h":300,"n":4268,"cov":0.807,"width":49.95,"pin":6.4706'
    ',"crps":9.1666,"crps_plain":9.9135},{"h":600,"n":4208,"cov":0.805,"width":74.93,"pin":9.8376,"crps":13.5086,'
    '"crps_plain":14.438},{"h":1800,"n":3970,"cov":0.782,"width":157.16,"pin":19.0076,"crps":25.808,"crps_plain":'
    '26.8014}],"opt":[{"h":60,"n":2880,"cov":0.805,"width":9.05,"pin":1.2463,"err":2.58,"err_naive":2.58},{"h":30'
    '0,"n":2848,"cov":0.815,"width":23.96,"pin":3.1631,"err":5.9,"err_naive":5.89},{"h":600,"n":2808,"cov":0.824,'
    '"width":35.36,"pin":4.5149,"err":8.85,"err_naive":8.82},{"h":1800,"n":2650,"cov":0.792,"width":69.68,"pin":8'
    '.7785,"err":16.13,"err_naive":16.02}]}},"2026-11-03":{"score":{"fut":[{"h":60,"n":4356,"cov":0.807,"width":1'
    '6.89,"pin":2.4004,"crps":3.7327,"crps_plain":4.8249},{"h":300,"n":4310,"cov":0.825,"width":44.76,"pin":5.943'
    '4,"crps":8.5738,"crps_plain":10.556},{"h":600,"n":4250,"cov":0.834,"width":75.97,"pin":9.0998,"crps":12.8986'
    ',"crps_plain":15.1301},{"h":1800,"n":4010,"cov":0.972,"width":181.64,"pin":18.4634,"crps":22.3321,"crps_plai'
    'n":25.267}],"opt":[{"h":60,"n":2558,"cov":0.794,"width":13.94,"pin":2.0572,"err":4.25,"err_naive":4.22},{"h"'
    ':300,"n":2558,"cov":0.82,"width":31.02,"pin":4.6415,"err":8.4,"err_naive":8.38},{"h":600,"n":2558,"cov":0.83'
    '3,"width":49.6,"pin":6.445,"err":12.22,"err_naive":12.15},{"h":1800,"n":2558,"cov":0.863,"width":159.01,"pin'
    '":17.0725,"err":18.74,"err_naive":18.88}]}},"2026-11-04":{"score":{"fut":[{"h":60,"n":4338,"cov":0.797,"widt'
    'h":21.68,"pin":2.9851,"crps":4.6831,"crps_plain":4.8121},{"h":300,"n":4289,"cov":0.799,"width":49.25,"pin":7'
    '.3728,"crps":11.3246,"crps_plain":11.2989},{"h":600,"n":4231,"cov":0.775,"width":69.14,"pin":11.0006,"crps":'
    '16.7977,"crps_plain":16.5877},{"h":1800,"n":3991,"cov":0.678,"width":89.61,"pin":17.9297,"crps":26.7384,"crp'
    's_plain":26.6011}],"opt":[{"h":60,"n":2900,"cov":0.814,"width":7.19,"pin":0.9191,"err":1.9,"err_naive":1.9},'
    '{"h":300,"n":2868,"cov":0.813,"width":18.5,"pin":2.426,"err":4.39,"err_naive":4.38},{"h":600,"n":2830,"cov":'
    '0.817,"width":29.28,"pin":3.782,"err":6.59,"err_naive":6.55},{"h":1800,"n":2670,"cov":0.836,"width":53.38,"p'
    'in":6.3048,"err":10.77,"err_naive":10.71}]}},"2026-11-05":{"score":{"fut":[{"h":60,"n":4331,"cov":0.807,"wid'
    'th":18.61,"pin":2.5094,"crps":3.8782,"crps_plain":4.5312},{"h":300,"n":4283,"cov":0.789,"width":46.71,"pin":'
    '6.2318,"crps":9.7649,"crps_plain":10.5411},{"h":600,"n":4223,"cov":0.784,"width":76.36,"pin":10.363,"crps":1'
    '4.3978,"crps_plain":15.1955},{"h":1800,"n":3983,"cov":0.796,"width":142.05,"pin":20.7031,"crps":25.4364,"crp'
    's_plain":27.1966}],"opt":[{"h":60,"n":2888,"cov":0.802,"width":6.15,"pin":0.8579,"err":1.74,"err_naive":1.74'
    '},{"h":300,"n":2856,"cov":0.813,"width":16.66,"pin":2.1143,"err":4.11,"err_naive":4.08},{"h":600,"n":2816,"c'
    'ov":0.837,"width":24.75,"pin":3.146,"err":5.95,"err_naive":5.81},{"h":1800,"n":2656,"cov":0.798,"width":49.4'
    '7,"pin":7.0527,"err":10.46,"err_naive":9.57}]}},"2026-11-06":{"score":{"fut":[{"h":60,"n":4315,"cov":0.797,"'
    'width":27.31,"pin":3.8669,"crps":5.9352,"crps_plain":6.6574},{"h":300,"n":4246,"cov":0.805,"width":72.92,"pi'
    'n":9.9952,"crps":14.1471,"crps_plain":14.9884},{"h":600,"n":4186,"cov":0.806,"width":111.83,"pin":15.2402,"c'
    'rps":20.8214,"crps_plain":22.0396},{"h":1800,"n":3948,"cov":0.714,"width":207.2,"pin":26.1199,"crps":37.4909'
    ',"crps_plain":41.0803}],"opt":[{"h":60,"n":2878,"cov":0.797,"width":8.08,"pin":1.1846,"err":2.46,"err_naive"'
    ':2.45},{"h":300,"n":2832,"cov":0.804,"width":21.07,"pin":3.1075,"err":5.62,"err_naive":5.6},{"h":600,"n":279'
    '1,"cov":0.804,"width":33.56,"pin":4.8357,"err":8.18,"err_naive":8.26},{"h":1800,"n":2634,"cov":0.752,"width"'
    ':54.73,"pin":7.7747,"err":15.13,"err_naive":15.6}]}},"2026-11-09":{"score":{"fut":[{"h":60,"n":4349,"cov":0.'
    '805,"width":27.88,"pin":3.8836,"crps":6.0451,"crps_plain":6.4111},{"h":300,"n":4301,"cov":0.835,"width":64.6'
    '1,"pin":9.0062,"crps":13.4957,"crps_plain":14.102},{"h":600,"n":4241,"cov":0.866,"width":101.01,"pin":13.046'
    '8,"crps":19.2111,"crps_plain":19.6655},{"h":1800,"n":4001,"cov":0.956,"width":207.11,"pin":23.1378,"crps":32'
    '.5691,"crps_plain":32.9274}],"opt":[{"h":60,"n":2553,"cov":0.806,"width":19.17,"pin":2.7022,"err":5.83,"err_'
    'naive":5.79},{"h":300,"n":2553,"cov":0.812,"width":48.35,"pin":6.7825,"err":12.72,"err_naive":12.68},{"h":60'
    '0,"n":2553,"cov":0.823,"width":75.07,"pin":10.2103,"err":18.15,"err_naive":18.03},{"h":1800,"n":2552,"cov":0'
    '.796,"width":201.72,"pin":26.5685,"err":31.16,"err_naive":31.02}]}},"2026-11-11":{"score":{"fut":[{"h":60,"n'
    '":4335,"cov":0.799,"width":22.06,"pin":3.0826,"crps":4.8092,"crps_plain":4.9461},{"h":300,"n":4287,"cov":0.7'
    '64,"width":47.52,"pin":7.7633,"crps":11.4189,"crps_plain":11.4922},{"h":600,"n":4227,"cov":0.713,"width":61.'
    '65,"pin":11.361,"crps":17.2234,"crps_plain":17.2247},{"h":1800,"n":3987,"cov":0.718,"width":100.34,"pin":18.'
    '8982,"crps":27.2619,"crps_plain":27.3932}],"opt":[{"h":60,"n":2892,"cov":0.839,"width":6.57,"pin":0.8072,"er'
    'r":1.51,"err_naive":1.51},{"h":300,"n":2860,"cov":0.859,"width":16.97,"pin":2.1246,"err":3.45,"err_naive":3.'
    '44},{"h":600,"n":2820,"cov":0.863,"width":27.04,"pin":3.2349,"err":5.16,"err_naive":5.12},{"h":1800,"n":2660'
    ',"cov":0.8,"width":61.58,"pin":7.5648,"err":8.13,"err_naive":8.01}]}}}}'
))


def test_backfill_reproduces_docs50_table(tmp_path):
    wb, wp = WALK_FIXTURE['brain'], WALK_FIXTURE['plain']
    ok, diffs, errata = BF.check_table(wb, wp)
    assert ok, diffs
    assert {(e[0], e[1], e[2]) for e in errata} == set(BF.KNOWN_ERRATA)
    t = BF.table_s7(wb, wp)
    assert t['fut'][1] == ['5 min', '79.8 % / 80.0 %', '48.2 / 50.4', '6 of 11', '8 of 11']
    # a changed walk file is caught
    wb2 = json.loads(json.dumps(wb))
    wb2['2026-11-11']['score']['fut'][1]['pin'] = 1.0
    assert not BF.check_table(wb2, wp)[0]
    rows = BF.build_rows({}, wb, wp, str(tmp_path), dte=lambda d: 0 if d in ('2026-10-27', '2026-11-03', '2026-11-09') else 3, metas={})
    assert len(rows) == 22 and all(r['walk'] for r in rows)
    r = [x for x in rows if x['day'] == '2026-11-11' and x['procedure'] == 'P-incumbent'][0]
    assert r['primary'] == pytest.approx(10 * 7.8315, rel=1e-6)
    retro = BF.retrospective(rows)
    assert retro['days'] == 11
    assert [s['used'] for s in retro['sequence'][:5]] == ['trained'] * 4 + ['plain']   # fast-off after four losses
    assert retro['against_always_plain']['better'] == 0
    allr = BF.merge(str(tmp_path), rows)
    again = BF.merge(str(tmp_path), rows)                     # idempotent: walk rows replaced, not duplicated
    assert len(again) == len(allr) == 22
    s = N.summarize(again)
    assert s['all']['days'] == 11 and s['all']['trained_better'] == 6
    assert s['strata']['dte0-1']['days'] == 3 and s['strata']['dte2+']['days'] == 8


def test_sklearn_mismatch_is_reported(tmp_path):
    lab, T = make_lab(tmp_path)
    put_brain(lab, 'brain.joblib', fake_brain(DAYS[:5]))
    json.dump(dict(trained_through=DAYS[4], sklearn='0.0.1'), open(os.path.join(lab, 'brain.meta.json'), 'w'))
    said = []
    N.run_day(DAYS[5], lab=lab, T=T, convert=False, online=False, check_only=True, log=said.append)
    assert any('scikit-learn 0.0.1' in s for s in said)
    assert not os.path.exists(N.ledger_path(lab))                       # check-only writes nothing


# ── review additions (PKG-10 review) ─────────────────────────────────────────────────────────────────────────────
def test_walk_day_summary_is_in_the_lab_daily_record_format(tmp_path):
    from apex.forecast_lab import core as C
    wb, wp = WALK_FIXTURE['brain'], WALK_FIXTURE['plain']
    days_dir = tmp_path / 'days'
    days_dir.mkdir()
    for d in ('2026-11-06', '2026-11-11'):
        (days_dir / f'{d}.json').write_text(json.dumps(BF.day_summary(d, wb, wp, None, 3)), encoding='utf-8')
    notes = []
    got = C.read_days(str(days_dir), note=notes.append)
    assert len(got) == 2 and not notes
    s = C.day_summary(got[1])
    assert s['day'] == '2026-11-11' and s['forward'] is False
    assert s['cov5'] == pytest.approx(0.771, abs=1e-3)                       # walk_brain 11 Nov, 5 min
    assert got[1]['H'] == [60, 300, 600, 1800]
    assert C.cross_day(got, '2026-11-12')['days'] == 0                      # walk days never count as evidence
    hs, sums = BF.score_sums(dict(fut=[dict(h=300, n=10, cov=0.5)], opt=[]))
    assert hs == [300] and sums['n'] == [10.0] and sums['cov'] == [5.0] and sums['crps'] == [None] and sums['on'] == [None]


def test_parity_reads_the_live_daily_record_sums():
    sv = dict(fut=[dict(h=300, n=4000, cov=0.80, crps=11.0, width=48.0)])
    live = dict(day='2026-11-12', H=[60, 300], score=dict(n=[4000, 3990], cov=[3200, 3152.1], crps=[40000, 3990 * 11.2],
                                                           width=[1, 3990 * 47.0]), restarts=1)
    p = N.parity(live, sv)
    assert p['ok'] is True and p['cov_live'] == pytest.approx(0.79) and p['counters']['restarts'] == 1
    live['score']['crps'][1] = 3990 * 12.0
    assert N.parity(live, sv)['ok'] is False
    assert N.parity(dict(H=[60], score=dict(n=[5], cov=[4])), sv)['ok'] is None      # no 5-minute column


def test_hand_run_refuses_while_the_day_lock_is_held(tmp_path, monkeypatch):
    lab = str(tmp_path / 'forecast_lab')
    monkeypatch.setattr(N, 'LAB', lab)
    held = N.day_lock(lab)
    assert held is not None
    try:
        assert N.day_lock(lab) is None
        called = []
        monkeypatch.setattr(N, 'run_day', lambda *a, **k: called.append(a) or dict(status='ok'))
        assert N.main(['2026-11-12', '--no-convert']) == 1 and called == []
        assert N.main(['2026-11-12', '--check-only']) == 0 and called          # check-only writes nothing: no lock
    finally:
        held.release()
    again = N.day_lock(lab)
    assert again is not None
    again.release()


def test_catch_up_stops_when_market_hours_begin(tmp_path):
    root = tmp_path / 'repo'
    (root / 'research' / 'forecast_lab').mkdir(parents=True)
    (root / 'research' / 'forecast_lab' / 'nightly.py').write_text('# stand-in')
    data = str(tmp_path / 'data')
    calls = []

    def runner(cmd, **kw):
        calls.append(cmd[-1])
        return types.SimpleNamespace(returncode=0)
    times = iter([datetime(2026, 11, 12, 8, 50, tzinfo=IST), datetime(2026, 11, 12, 9, 1, tzinfo=IST)])
    rc = NA.main([], now=datetime(2026, 11, 12, 8, 45, tzinfo=IST), data=data, root=str(root), runner=runner,
                 days=DAYS[5:7], sleep=lambda s: None, clock=lambda: next(times))
    st = json.load(open(os.path.join(data, 'nightly_status.json')))
    assert rc == 0 and calls == [DAYS[5]]
    assert st['processed_days'] == [DAYS[5]] and st['missed_days'] == [DAYS[6]] and st['outcome'] == 'incomplete'
    assert any('market hours began' in n for n in st['notes'])


def test_rollback_keeps_c_h_in_the_meta(tmp_path):
    lab, T = make_lab(tmp_path, bad={DAYS[4]})
    put_brain(lab, 'brain_prev.joblib', fake_brain(DAYS[:4]))
    put_brain(lab, 'brain.joblib', fake_brain(DAYS[:5], bad=True))
    assert run(lab, T, DAYS[5])['status'] == 'ok'
    meta = json.load(open(os.path.join(lab, 'brain.meta.json')))
    assert meta['rolled_back_from'] and len(meta['c_h']) == len(B.H) and all(c > 0 for c in meta['c_h'])
