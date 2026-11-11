"""10 Nov 2026 (docs/40 section 9, docs/41): a registry of every replay / research run folder: who made it, whether it
is still being written, how big it is, whether git tracks it, which documents cite it, and a retention class.
Read-only: it never deletes. Output: data/research/run_registry.json and a table on the screen.

Retention classes
  active       a file changed in the last 30 minutes: never touch
  evidence     tracked in git, or cited by a document / the changelog: keep (archive only on the owner's word)
  regenerable  untracked and uncited, and its inputs (the tapes) still exist: a candidate for removal after review
Usage: py -3.13 research/run_registry.py"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY = os.path.join(ROOT, "data", "replay")


def tree(folder):
    n = size = 0
    newest = 0.0
    for dp, _, fn in os.walk(folder):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            n += 1
            size += st.st_size
            newest = max(newest, st.st_mtime)
    return n, size, newest


def main():
    tracked = {}
    try:
        out = subprocess.run(["git", "ls-files", "data/replay", "data/research"], cwd=ROOT, capture_output=True, text=True,
                             timeout=120).stdout
        for line in out.splitlines():
            parts = line.split("/")
            key = "/".join(parts[:4] if parts[2] == "batch" else parts[:3 if parts[1] == "research" else 4])
            tracked[key] = tracked.get(key, 0) + 1
    except Exception:
        pass
    docs = ""
    for dp, _, fn in os.walk(os.path.join(ROOT, "docs")):
        for f in fn:
            if f.endswith(".md"):
                docs += open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
    for f in ("CHANGELOG.md", "CLAUDE_SHADOW_BOOK_HANDOFF.md"):
        if os.path.exists(os.path.join(ROOT, f)):
            docs += open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read()
    runs = []
    cands = []
    if os.path.isdir(os.path.join(REPLAY, "batch")):
        cands += [os.path.join(REPLAY, "batch", d) for d in sorted(os.listdir(os.path.join(REPLAY, "batch")))]
    for d in sorted(os.listdir(REPLAY)):
        p = os.path.join(REPLAY, d)
        if d != "batch" and os.path.isdir(p):
            cands += [os.path.join(p, s) for s in sorted(os.listdir(p))]
    res = os.path.join(ROOT, "data", "research")
    if os.path.isdir(res):
        cands += [os.path.join(res, d) for d in sorted(os.listdir(res)) if os.path.isdir(os.path.join(res, d))]
    now = time.time()
    for p in cands:
        if not os.path.isdir(p):
            continue
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        n, size, newest = tree(p)
        man = {}
        mp = os.path.join(p, "manifest.json")
        if os.path.exists(mp):
            try:
                man = json.load(open(mp, encoding="utf-8"))
            except Exception:
                man = {"unreadable": True}
        name = os.path.basename(p)
        cited = name in docs or rel in docs
        trk = tracked.get(rel, 0)
        if now - newest < 1800:
            cls = "active"
        elif trk or cited:
            cls = "evidence"
        else:
            cls = "regenerable"
        runs.append(dict(folder=rel, files=n, bytes=size, last_write=time.strftime("%Y-%m-%d %H:%M", time.localtime(newest)) if newest else None,
                         producer=("apex.replay_batch" if man.get("run_id") else ("research script" if "/research/" in rel or "research" in name or "predict" in name
                                                                                   or "review" in name else "run_apex replay")),
                         state=("active" if cls == "active" else (man.get("status") or ("complete" if man.get("finished") else "no manifest status"))),
                         started=man.get("started"), finished=man.get("finished"), code=(man.get("git") or {}).get("commit"),
                         tapes=[os.path.basename(t.get("path", "")) for t in man.get("tapes", [])] or None,
                         tracked_files=trk, cited_in_docs=bool(cited), retention=cls))
    out = dict(built=time.strftime("%Y-%m-%d %H:%M:%S"), root=ROOT, runs=runs,
               totals={c: dict(folders=sum(1 for r in runs if r["retention"] == c), bytes=sum(r["bytes"] for r in runs if r["retention"] == c))
                       for c in ("active", "evidence", "regenerable")})
    dst = os.path.join(ROOT, "data", "research", "run_registry.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(out, open(dst, "w", encoding="utf-8"), indent=1)
    for c, t in out["totals"].items():
        print(f"{c:12s} {t['folders']:4d} folders {t['bytes'] / 1e6:9.1f} MB")
    print("regenerable (review before removing anything):")
    for r in sorted((r for r in runs if r["retention"] == "regenerable"), key=lambda r: -r["bytes"]):
        print(f"  {r['bytes'] / 1e6:8.1f} MB  {r['folder']}  last write {r['last_write']}")
    print("written:", os.path.relpath(dst, ROOT))


if __name__ == "__main__":
    sys.exit(main())
