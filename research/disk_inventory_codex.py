"""Read-only workspace disk inventory; does not follow links or delete files."""
import collections
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
groups = collections.defaultdict(lambda: [0, 0])
large, caches, errors = [], [], []
for base, dirs, files in os.walk(root, followlinks=False):
    dirs[:] = [d for d in dirs if not Path(base, d).is_symlink() and not os.path.isjunction(Path(base, d))]
    for name in files:
        p = Path(base, name)
        try:
            if p.is_symlink():
                continue
            s = p.stat()
        except OSError as e:
            errors.append({'path': str(p), 'error': str(e)})
            continue
        rel = p.relative_to(root)
        group = '/'.join(rel.parts[:2]) if len(rel.parts) > 2 else rel.parts[0]
        groups[group][0] += s.st_size
        groups[group][1] += 1
        if s.st_size >= 20 * 1024 * 1024:
            large.append({'path': str(p), 'bytes': s.st_size, 'mtime': s.st_mtime})
        if '__pycache__' in rel.parts or '.pytest_cache' in rel.parts:
            caches.append({'path': str(p), 'bytes': s.st_size})
result = {'root': str(root), 'total_bytes': sum(v[0] for v in groups.values()),
          'groups': dict(sorted(groups.items(), key=lambda kv: -kv[1][0])),
          'large_files': sorted(large, key=lambda r: -r['bytes']),
          'rebuildable_cache_files': caches, 'errors': errors}
out = root / 'data/replay/batch/codex_predictive_review_2026-11-10'
out.mkdir(parents=True, exist_ok=True)
(out / 'disk_inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'total_GiB': result['total_bytes'] / 2**30,
                  'groups_GiB': {k: round(v[0] / 2**30, 4) for k, v in list(result['groups'].items())[:20]},
                  'cache_MiB': sum(x['bytes'] for x in caches) / 2**20, 'errors': len(errors)}, indent=2))
