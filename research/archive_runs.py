"""10 Nov 2026 (docs/41 section 8): pack finished replay run folders into verified archives. Lossless.

For each folder given: write <archive dir>/<name>.tar.gz, read the archive back and compare the sha256 of EVERY member
with the file on disk, write a manifest (file list, sizes, hashes), and only then remove the folder. If anything
differs, the folder is left exactly as it was and the archive is deleted. Never follows links. Refuses a folder that
has a file modified in the last 30 minutes (a run that may still be writing).

Restore: py -3.13 research/archive_runs.py --restore data/archive/<name>.tar.gz
Usage:   py -3.13 research/archive_runs.py [--dry] <folder> [<folder> ...]"""
import hashlib, json, os, shutil, sys, tarfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(ROOT, "data", "archive")


def sha(fobj):
    h = hashlib.sha256()
    for b in iter(lambda: fobj.read(1 << 20), b""):
        h.update(b)
    return h.hexdigest()


def files_of(folder):
    out = []
    for dp, dn, fn in os.walk(folder, followlinks=False):
        for f in fn:
            p = os.path.join(dp, f)
            if os.path.islink(p):
                raise SystemExit(f"link inside {folder}: {p} (not archived)")
            out.append(p)
    return sorted(out)


def pack(folder, dry=False):
    folder = os.path.abspath(folder)
    if not folder.startswith(os.path.join(ROOT, "data", "replay") + os.sep) or not os.path.isdir(folder):
        raise SystemExit(f"not a replay run folder under this repository: {folder}")
    rel = os.path.relpath(folder, ROOT).replace("\\", "/")
    fs = files_of(folder)
    newest = max((os.path.getmtime(p) for p in fs), default=0)
    if time.time() - newest < 1800:
        print(f"SKIP {rel}: a file changed in the last 30 minutes")
        return None
    size = sum(os.path.getsize(p) for p in fs)
    if dry:
        print(f"would archive {rel}: {len(fs)} files, {size / 1e6:.1f} MB")
        return dict(folder=rel, files=len(fs), bytes=size)
    os.makedirs(ARCH, exist_ok=True)
    name = rel.replace("data/replay/", "").replace("/", "__")
    dst = os.path.join(ARCH, name + ".tar.gz")
    if os.path.exists(dst):
        raise SystemExit(f"archive exists: {dst}")
    hashes = {}
    for p in fs:
        with open(p, "rb") as f:
            hashes[os.path.relpath(p, ROOT).replace("\\", "/")] = (sha(f), os.path.getsize(p))
    with tarfile.open(dst, "w:gz", compresslevel=9) as tar:
        for p in fs:
            tar.add(p, arcname=os.path.relpath(p, ROOT).replace("\\", "/"), recursive=False)
    seen = 0
    with tarfile.open(dst, "r:gz") as tar:
        for m in tar:
            if not m.isfile():
                continue
            h = sha(tar.extractfile(m))
            if hashes.get(m.name, (None,))[0] != h or hashes[m.name][1] != m.size:
                os.remove(dst)
                raise SystemExit(f"VERIFY FAILED for {m.name}: folder left untouched, archive removed")
            seen += 1
    if seen != len(fs):
        os.remove(dst)
        raise SystemExit(f"VERIFY FAILED: {seen} members for {len(fs)} files; folder left untouched")
    for p in fs:                                             # unchanged since hashing?
        if os.path.getsize(p) != hashes[os.path.relpath(p, ROOT).replace("\\", "/")][1]:
            os.remove(dst)
            raise SystemExit(f"{p} changed while archiving: folder left untouched")
    man = dict(folder=rel, archive=os.path.relpath(dst, ROOT).replace("\\", "/"), archived=time.strftime("%Y-%m-%d %H:%M:%S"),
               files=len(fs), bytes=size, archive_bytes=os.path.getsize(dst), archive_sha256=sha(open(dst, "rb")),
               restore=f"py -3.13 research/archive_runs.py --restore {os.path.relpath(dst, ROOT).replace(chr(92), '/')}",
               members={k: dict(sha256=v[0], bytes=v[1]) for k, v in hashes.items()})
    with open(dst[:-7] + ".manifest.json", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    shutil.rmtree(folder)
    print(f"archived {rel}: {len(fs)} files, {size / 1e6:.1f} MB -> {man['archive_bytes'] / 1e6:.1f} MB")
    return {k: man[k] for k in ("folder", "archive", "files", "bytes", "archive_bytes")}


def restore(arc):
    arc = os.path.abspath(arc)
    with tarfile.open(arc, "r:gz") as tar:
        for m in tar:
            dst = os.path.abspath(os.path.join(ROOT, m.name))
            if not dst.startswith(os.path.join(ROOT, "data", "replay") + os.sep) or os.path.exists(dst):
                raise SystemExit(f"will not write {dst}")
        tar.extractall(ROOT)
    print("restored from", arc, "(the archive is kept)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--restore":
        restore(a[1])
    else:
        dry = "--dry" in a
        done = [pack(f, dry) for f in a if f != "--dry"]
        done = [d for d in done if d]
        tot, arc = sum(d["bytes"] for d in done), sum(d.get("archive_bytes", 0) for d in done)
        print(f"total {tot / 1e6:.1f} MB in {len(done)} folders" + ("" if dry else f" -> {arc / 1e6:.1f} MB; freed {(tot - arc) / 1e6:.1f} MB"))
        if not dry and done:
            log = os.path.join(ARCH, "archive_log.jsonl")
            with open(log, "a", encoding="utf-8") as f:
                for d in done:
                    f.write(json.dumps(d) + "\n")
