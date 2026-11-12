"""Back-fill the Forecast Lab ledger with the 11 walk days, 27 Oct to 11 Nov (docs/50 section 7; docs/53).

Reads data/forecast_lab/walk_forward.json (the trained layer alone, offline), walk_brain.json and walk_plain.json
(the whole Lab day after day with and without the trained layer, online learning carried) and the dated brains in
data/forecast_lab/brains/ (for each walk day's model hash). Writes, all flagged "walk":
  ledger.jsonl        P-incumbent and P-plain rows (basis online) and the offline P-incumbent / P-clock rows
                      (QLIKE and coverage only) for each walk day; rows already there that are not walk rows are kept
  days/<day>.json     one summary per walk day (written only when absent or itself a walk summary: a live record is
                      never replaced)
  record_summary.json the cumulative record (research/forecast_lab/nightly.summarize)
Before writing anything it rebuilds the docs/50 section 7 tables from the walk files and stops if any cell differs
from the document, apart from the two errata listed in KNOWN_ERRATA. It then applies PR-003 day by day to the walk
days, using only earlier days, and prints how the chosen procedure compares with always-trained and always-plain.

  py -3.13 research/forecast_lab/backfill_ledger.py                       (reads and writes data/forecast_lab)
  py -3.13 research/forecast_lab/backfill_ledger.py --out <folder>        (writes there instead; for a dry run)
  py -3.13 research/forecast_lab/backfill_ledger.py --check               (table check and retrospective only)"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import nightly as N  # noqa: E402

DOC = os.path.join(ROOT, 'docs', '50_FORECAST_LAB_V2_AND_PENDING_WORK.md')
TABLE_H = (60, 300, 600, 1800)
H_NAME = {60: '1 min', 300: '5 min', 600: '10 min', 1800: '30 min'}
# docs/50 s7 cells the walk files do not give (the document's own rounding slip; computed value in the comment).
KNOWN_ERRATA = {('opt', '1 min', 5): '2.86 %',      # walk files: mean "no change" error 2.8545 -> 2.85 %
                ('opt', '5 min', 5): '6.27 %'}      # walk files: 6.2645 -> 6.26 %


def load_walk(src):
    out = []
    for f in ('walk_forward.json', 'walk_brain.json', 'walk_plain.json'):
        d = N.read_json(os.path.join(src, f))
        if not isinstance(d, dict):
            raise SystemExit(f'{f} missing or unreadable in {src}')
        out.append(d)
    return out


def at(rows, h):
    for r in rows or []:
        if r.get('h') == h:
            return r
    return None


def table_s7(wb, wp):
    """The two docs/50 s7 tables, cell by cell, as the document prints them: per-session means over the walk days."""
    days = sorted(set(wb) & set(wp))
    n = len(days)
    out = {}
    for part in ('fut', 'opt'):
        rows = []
        for h in TABLE_H:
            rb = [at(wb[d]['score'][part], h) for d in days]
            rp = [at(wp[d]['score'][part], h) for d in days]
            m = lambda R, k: float(np.mean([r[k] for r in R]))
            cells = [H_NAME[h], f"{m(rb, 'cov') * 100:.1f} % / {m(rp, 'cov') * 100:.1f} %",
                     f"{m(rb, 'width'):.1f} / {m(rp, 'width'):.1f}",
                     f"{sum(a['pin'] < b['pin'] for a, b in zip(rb, rp))} of {n}"]
            if part == 'fut':
                cells.append(f"{sum(a['crps'] < b['crps'] for a, b in zip(rb, rp))} of {n}")
            else:
                cells += [f"{m(rb, 'err'):.2f} %", f"{m(rb, 'err_naive'):.2f} %"]
            rows.append(cells)
        out[part] = rows
    return out


def parse_doc(path=DOC):
    """The two section 7 tables from the document, as lists of cell strings."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    sec = text.split('\n## 7.', 1)[1].split('\n## 8.', 1)[0]
    fut_txt, opt_txt = sec.split('Option premiums', 1)
    grab = lambda t: [[c.strip() for c in ln.strip().strip('|').split('|')] for ln in t.splitlines()
                      if re.match(r'^\|\s*\d+ min\s*\|', ln.strip())]
    return dict(fut=grab(fut_txt), opt=grab(opt_txt))


def check_table(wb, wp, doc=DOC):
    """(ok, differences, errata seen). ok only when every cell matches, apart from the listed errata exactly."""
    got, want = table_s7(wb, wp), parse_doc(doc)
    diffs, errata = [], []
    for part in ('fut', 'opt'):
        if len(got[part]) != len(want[part]):
            diffs.append((part, 'rows', len(got[part]), len(want[part])))
            continue
        for g, w in zip(got[part], want[part]):
            for k, (a, b) in enumerate(zip(g, w)):
                if a == b:
                    continue
                key = (part, g[0], k)
                if KNOWN_ERRATA.get(key) == b:
                    errata.append((part, g[0], k, a, b))
                else:
                    diffs.append((part, g[0], k, a, b))
    return (not diffs and len(errata) == len(KNOWN_ERRATA)), diffs, errata


def brain_meta_for(src, day):
    """The walk's brain for day D was fitted through the previous recorded session: brains/brain_<prev>.joblib."""
    cands = sorted(p for p in glob.glob(os.path.join(src, 'brains', 'brain_*.joblib')) if os.path.basename(p)[6:16] < day)
    if not cands:
        return None
    obj, why = N.load_obj(cands[-1])
    if obj is None:
        N.say(f'WARNING: {os.path.basename(cands[-1])} {why}')
        return dict(hash=None, trained_through=os.path.basename(cands[-1])[6:16], sessions=None)
    return N.model_ref(obj)


def build_rows(wf, wb, wp, src, dte=N.dte_of, metas=None):
    rows = []
    for d in sorted(set(wb) & set(wp)):
        x = dte(d)
        meta = (metas or {}).get(d) if metas is not None else brain_meta_for(src, d)
        for name, W, model in (('P-incumbent', wb, meta), ('P-plain', wp, None)):
            sv = W[d]['score']
            rows.append(N.score_row(d, name, 'online', N.online_hs(sv), None, model, walk=True, dte=x,
                                    option=N.option_side(sv), source=f"walk_{'brain' if name == 'P-incumbent' else 'plain'}.json"))
        if d in wf:
            hs_b, hs_c = {}, {}
            for h, r in wf[d].items():
                n = int(r.get('n') or 0)
                hs_b[str(h)] = dict(n=n, nq=n, qlike=r['qlike'] * n, inside=r['cover80'] * n, from_means=True)
                hs_c[str(h)] = dict(n=n, nq=n, qlike=r['qlike_base'] * n, inside=r['cover80_base'] * n, from_means=True)
            rows.append(N.score_row(d, 'P-incumbent', 'offline', hs_b, None, meta, walk=True, dte=x, source='walk_forward.json',
                                    note='trained layer alone, raw (no mean correction); no interval score'))
            rows.append(N.score_row(d, 'P-clock', 'offline', hs_c, None, None, walk=True, dte=x, source='walk_forward.json'))
    return rows


# score-view field -> the Lab's score-sum name (apex/forecast_lab/core.read_days format); a mean is turned back into
# a sum by multiplying with the row's n (the rounded means of the walk files, so the sums are close, not exact)
FUT_SUMS = (('cov', 'cov'), ('crps', 'crps'), ('crps_plain', 'crps_plain'), ('width', 'width'), ('pin', 'pin'))
OPT_SUMS = (('cov', 'ocov'), ('pin', 'opin'), ('width', 'owidth'), ('err', 'oerr'), ('err_naive', 'oerr_naive'),
            ('err_decay', 'oerr_decay'), ('brier', 'obrier'), ('brier_base', 'obrier_base'))


def score_sums(sv):
    """(H, {name: [one sum per H]}) from a Lab score view {fut: [...], opt: [...]}, in the format core.read_days reads.
    A value the view does not carry stays None."""
    fut = {r.get('h'): r for r in (sv or {}).get('fut') or [] if isinstance(r, dict)}
    opt = {r.get('h'): r for r in (sv or {}).get('opt') or [] if isinstance(r, dict)}
    hs = sorted(h for h in set(fut) | set(opt) if isinstance(h, int))
    out = {k: [None] * len(hs) for k in ['n', 'dir_n', 'dir_hit', 'on'] + [b for _, b in FUT_SUMS + OPT_SUMS]}

    def put(r, pairs, n_key, j):
        n = (r or {}).get('n')
        if not n:
            return
        out[n_key][j] = float(n)
        for a, b in pairs:
            if isinstance(r.get(a), (int, float)):
                out[b][j] = float(r[a]) * n
    for j, h in enumerate(hs):
        put(fut.get(h), FUT_SUMS, 'n', j)
        put(opt.get(h), OPT_SUMS, 'on', j)
        f = fut.get(h) or {}
        if f.get('dir_n') is not None:
            out['dir_n'][j] = float(f['dir_n'])
            if isinstance(f.get('dir_hit'), (int, float)):
                out['dir_hit'][j] = float(f['dir_hit']) * f['dir_n']
    return hs, out


def day_summary(d, wb, wp, meta, dte):
    """days/<day>.json for a walk day, in the Lab's daily-record format. forward is false: the walk was run with
    today's knowledge of the method, so it is shown in the record by day but never counts as evidence for what the
    Lab may claim (core.cross_day skips it). PR-003 uses the walk days for the fast-off check only."""
    hs, sums = score_sums(wb[d]['score'])
    hp, sums_p = score_sums(wp[d]['score'])
    return dict(day=d, H=hs, forward=False, walk=True, source='walk_brain.json, walk_plain.json (docs/50 section 7)',
                dte=dte, stratum=N.stratum(dte), brain=meta, score=sums, plain=dict(H=hp, score=sums_p),
                score_view=wb[d]['score'], plain_score_view=wp[d]['score'], weights5=wb[d].get('weights5'),
                note='sums = per-day mean x n from the rounded means of the walk files')


def retrospective(rows):
    """PR-003 applied day by day to the walk days, each decision from earlier days only."""
    ix = N.index(rows)
    days = sorted({k[0] for k in ix if ix[k].get('walk')})
    use = True
    seq = []
    for d in days:
        p = N.pair(ix, d, 'P-incumbent')
        if not p:
            continue
        b, pl = p[0]['primary'], p[1]['primary']
        chosen = b if use else pl
        seq.append(dict(day=d, used='trained' if use else 'plain', chosen=chosen, trained=b, plain=pl))
        fo = N.fast_off([r for r in rows if r.get('day', '') <= d], d)
        if use and fo['hit']:
            use = False
    cmp = lambda key: dict(better=sum(s['chosen'] < s[key] for s in seq), worse=sum(s['chosen'] > s[key] for s in seq),
                           same=sum(s['chosen'] == s[key] for s in seq))
    trail = [seq[i]['day'] for i in range(len(seq) - 4) if sum(s['chosen'] > s['plain'] for s in seq[i:i + 5]) >= 4]
    return dict(days=len(seq), sequence=seq, against_always_trained=cmp('trained'), against_always_plain=cmp('plain'),
                windows_trailing_plain_4_of_5=trail, total_chosen=round(sum(s['chosen'] for s in seq), 3),
                total_trained=round(sum(s['trained'] for s in seq), 3), total_plain=round(sum(s['plain'] for s in seq), 3))


def merge(out, rows):
    old = N.read_ledger(out)
    keep = [r for r in old if not (r.get('kind') == 'score' and r.get('walk'))]
    allr = sorted(rows, key=lambda r: (r['day'], r['procedure'], r['basis'])) + keep
    N.write_ledger(out, allr)
    return allr


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    src = argv[argv.index('--src') + 1] if '--src' in argv else N.LAB
    out = argv[argv.index('--out') + 1] if '--out' in argv else src
    wf, wb, wp = load_walk(src)
    ok, diffs, errata = check_table(wb, wp)
    for e in errata:
        print(f'docs/50 s7 known erratum: {e[0]} {e[1]} column {e[2]}: walk files give {e[3]}, the document prints {e[4]}')
    if not ok:
        print('THE WALK FILES DO NOT REPRODUCE docs/50 s7:', diffs)
        return 1
    print('docs/50 s7 reproduced from the walk files (every other cell identical)')
    metas = {d: brain_meta_for(src, d) for d in sorted(set(wb) & set(wp))}
    rows = build_rows(wf, wb, wp, src, metas=metas)
    retro = retrospective(rows)
    print(json.dumps({k: v for k, v in retro.items() if k != 'sequence'}, indent=1))
    for s in retro['sequence']:
        print(f"  {s['day']}: ran {s['used']:<7} score {s['chosen']:.2f} (trained {s['trained']:.2f}, plain {s['plain']:.2f})")
    if '--check' in argv:
        return 0
    allr = merge(out, rows)
    for d in metas:
        p = os.path.join(out, 'days', f'{d}.json')
        cur = N.read_json(p)
        if cur is None or (isinstance(cur, dict) and cur.get('walk')):
            if cur is None and os.path.exists(p):
                print(f'{p} exists but is unreadable: left as it is')
                continue
            N.write_json(p, day_summary(d, wb, wp, metas[d], N.dte_of(d)))
    N.write_json(os.path.join(out, 'record_summary.json'), dict(N.summarize(allr), retrospective=retro))
    print(f"ledger: {len(rows)} walk rows written to {N.ledger_path(out)}; days/ summaries and record_summary.json written")
    return 0


if __name__ == '__main__':
    sys.exit(main())
