"""11 Nov 2026 (review of docs/45, point 5): record a FREEZE of the forecast package, so "forward evidence" has a
definite start.

A forward session counts for a package only if the package was frozen BEFORE that session opened and was not changed
since. This script appends one line to apex/predict/freeze_log.jsonl with the wall-clock time, the content hashes of
the artefacts and of every source file that decides a forecast or a forecast-book trade, and the last recorded
session at that moment. check() compares the current files with the newest freeze and lists what changed: a session
after a change is development evidence for that change, not forward evidence for the old package.

Usage: py -3.13 research/predict/freeze.py "what is frozen and why"      append a freeze
       py -3.13 research/predict/freeze.py --check                       compare the tree with the newest freeze"""
import glob, hashlib, json, os, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
LOG = os.path.join(ROOT, 'apex', 'predict', 'freeze_log.jsonl')
FILES = ['apex/predict/features.py', 'apex/predict/targets.py', 'apex/predict/models.py', 'apex/predict/ledger.py',
         'apex/predict/ranges.py', 'apex/predict/registry.py', 'apex/engine/pred.py', 'apex/predict/model_v2.json',
         'apex/predict/ranges_v1.json', 'apex/predict/registry.json']
PARTIAL = {'apex/engine/paper.py': ('def bound_contract', 'def evaluate_gen', 'def gen_bracket', 'def _gen_exit'),
           'apex/engine_main.py': ('def _pred_feed', 'def _pred_note')}


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def func_text(path, heads):
    """The source of the named top-level or class-level functions only: the rest of these large files changes for
    other reasons and must not look like a forecast change."""
    src = open(os.path.join(ROOT, path), encoding='utf-8').read().splitlines()
    out = []
    for h in heads:
        i = next((k for k, line in enumerate(src) if line.strip().startswith(h)), None)
        if i is None:
            out.append(f'<{h} missing>')
            continue
        ind = len(src[i]) - len(src[i].lstrip())
        j = i + 1
        while j < len(src) and (not src[j].strip() or len(src[j]) - len(src[j].lstrip()) > ind):
            j += 1
        out += src[i:j]
    return '\n'.join(out).encode()


def state():
    s = {}
    for f in FILES:
        p = os.path.join(ROOT, f)
        s[f] = sha(open(p, 'rb').read()) if os.path.exists(p) else None
    for f, heads in PARTIAL.items():
        s[f + ' (forecast functions)'] = sha(func_text(f, heads))
    sys.path.insert(0, ROOT)
    os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
    from apex import config
    s['config.PREDICT_MODEL'] = os.path.basename(config.PREDICT_MODEL)
    s['config.PRED_BOOKS'] = sorted(config.PRED_BOOKS)
    return s


def newest():
    if not os.path.exists(LOG):
        return None
    rows = [json.loads(x) for x in open(LOG, encoding='utf-8') if x.strip()]
    return rows[-1] if rows else None


if __name__ == '__main__':
    if '--check' in sys.argv:
        last = newest()
        if last is None:
            print('no freeze recorded')
            sys.exit(1)
        cur = state()
        diff = sorted(k for k in set(cur) | set(last['state']) if cur.get(k) != last['state'].get(k))
        print('newest freeze:', last['frozen_at'], '|', last['note'])
        print('unchanged since' if not diff else 'CHANGED since the freeze: ' + ', '.join(diff))
        sys.exit(0 if not diff else 2)
    ticks = sorted(os.path.basename(p)[:10] for p in glob.glob(os.path.join(ROOT, 'data', 'ticks', '2026-*.jsonl.gz')))
    art = json.load(open(os.path.join(ROOT, 'apex', 'predict', 'model_v2.json')))
    row = dict(frozen_at=time.strftime('%Y-%m-%d %H:%M:%S'), note=' '.join(a for a in sys.argv[1:] if not a.startswith('--')),
               last_recorded_session=ticks[-1] if ticks else None, model_hash=art.get('hash'),
               model_training_cutoff=art.get('training_cutoff'), state=state(),
               rule='a session is forward evidence for this package only if it opened after frozen_at and --check is clean at its end')
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row) + '\n')
    print(json.dumps({k: row[k] for k in ('frozen_at', 'note', 'last_recorded_session', 'model_hash', 'model_training_cutoff')}, indent=1))
