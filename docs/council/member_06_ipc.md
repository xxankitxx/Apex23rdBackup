# Member 06: Concurrency, shared memory and process supervision

## Lens
I looked at `apex/table.py` (the row seqlock, `snapshot()` and `StateBlob`), `run_apex.py supervise()`, how the feed, engine and gateway attach and restart, how shutdown works, and the Windows-specific behaviour of shared memory and files. I wrote and ran probe scripts in two real processes (`/tmp/council/06/probe*.py`, Python 3.13, numpy 2.5, 2 cores). `tests/test_core.py` passes.

## Teardown

**T1. `snapshot()` hands back torn rows, and its retry hardly ever fixes them. Severity: medium. Verified by probe.**
In `table.py:131-137`, the three re-reads run back to back with no pause. A Python-level row write (`apply_packet`, about 20 numpy scalar stores) takes tens of µs, so all three retries usually land inside the same write. After the loop the row is returned anyway, with no mask saying it is bad.
- Probe with one row written non-stop: **18 % of snapshots returned a torn row 0** (fields from two different ticks), and 24 % returned an odd `seq`.
- Probe with 200 rows round-robin and a 10 Hz reader: 1 torn row per 283 snapshots at a 50 ms writer gap, and 41 per 158 at zero gap.
- Failure scenario: the futures row mixes the new `ltp` with the old `bid`/`ask`/`ltt`. The result is a momentary fake spread or price that reaches Market, the Flow deltas and the DataGuard spike test.
- Fix, verified: put `time.sleep(0)` between retries, test `before & 1`, and return the indices that are still unresolved. The probe then gave **0 torn rows accepted** out of 195, with 1 row correctly flagged.
- `gateway.py:80-91` has the same flaw. It checks `seq` and then copies `rows[ch]` without checking again, so torn ticks reach the browser. That one is display only.

**T2. An exception between `begin()` and `end()` flips the row's parity for good. Severity: medium. Verified by probe.**
`feed_core.py:184-194` (the depth branch) calls `len(lv[k])` with no try/finally. A depth level of `None` raises `TypeError` while `seq` is odd.
- The probe confirmed it: `seq` is 1 after the exception and 3 after the next good quote. From then on every stable state of that row looks "mid-write" and every real mid-write looks stable.
- The gateway filters out odd rows (`gateway.py:82`), so that contract freezes on the dashboard. The engine's `snapshot()` accepts the real torn copies.
- The exception also escapes `on_message` into the SDK thread (`feed_breeze.py:406`).
- It only clears when a live feed restarts, because `feed_breeze.py:235` zeroes the rows. In sim and replay it never clears.

**T3. Nothing checks whether the processes are still alive and working. Severity: medium-high. Verified by read and grep.**
- `engine_hb_ns`, `feed_hb_ns` and `gateway_hb_ns` are written (`engine_main.py:705`, `feed_breeze.py:518`, `gateway.py:101`), but no code reads them: grep finds no reader in Python or in `app.js`.
- `supervise()` only calls `poll()` to see whether a process has exited (`run_apex.py:85-100`). A hung engine is never restarted.
- The dashboard keeps serving `LAST_STATE` with no age shown. `app.js:46,74` only reconnects when the websocket closes.
- Failure scenario: the engine hangs or wedges with an open paper position. The dashboard looks normal while the exits stop running.
- `StateBlob.write` silently throws away an oversized state (`table.py:165-166`), which produces the same symptom with nothing in the log.

**T4. An engine restart loses the trailing-stop state of an open trade. Severity: medium. Verified by read.**
- `pos["best"]`, `pos["trail"]` and `peak_pts` change on every step (`paper.py:353-362`).
- `save_books` only runs when an entry or exit happens (`engine_main.py:549-586`).
- `run_apex.py:87` says "books are on disk", but after a live restart `start_day` reloads `pos` as it was at entry. A trade that had already switched to the trailing stop drops back to the wide initial stop.

**T5. The shutdown kill window can truncate the whole learning history. Severity: medium. Verified by read.**
- `run_apex.py:105-117` gives feed and engine one shared 12 s deadline. It waits for the feed first, whose Recorder join can take up to 5 s, then for the engine. After that, `terminate()` runs, which is a hard `TerminateProcess` on Windows.
- After 15:30 the engine's stop path runs `end_day()`, which calls `learning.record_day`. That function rewrites **all of `days.jsonl` in place** with `open(DAYS, "w")` (`learning.py:175`), not tmp+replace.
- A kill in the middle of that write leaves the multi-day record truncated. Closing the console window has the same effect: Windows sends CTRL_CLOSE_EVENT and hard-kills after about 5 s.

**T6. Two save paths have no Windows retry. Severity: low-medium. Verified by read.**
- `feed_core.py:41` has a `replace_retry` helper, but `paper.save_books` (`paper.py:438`) and the learning state (`learning.py:150`) call plain `os.replace`.
- On Windows, antivirus, the search indexer or OneDrive can briefly hold the destination file, which raises `PermissionError`.
- Inside `run_books` that exception lands after the exit is already applied in memory. The `changed` flag is then lost, so the exit is not on disk until the next entry or exit.

**T7. The restart policies are crude. Severity: low. Verified by read.**
- The engine is respawned with no backoff and no limit (`run_apex.py:85-88`). A crash at import becomes a 1 Hz respawn loop that keeps appending to `engine.log`.
- The feed's `restarts` counter never resets. After about 12 restarts, every later death waits 60 s, and 90 s once it passes 20, even if the previous run was healthy for hours.
- In sim and replay a feed crash goes unnoticed. The engine waits forever for `feed_state == 7` (`engine_main.py:706`).

**T8. Linux only: a second instance can replace a segment that is still in use. Severity: low. Verified by read.**
`_open(create=True)` unlinks a live segment (`table.py:69-76`). On POSIX that lets a second instance start next to orphaned children, with two engines then writing the same paper files. The port check catches this only while the orphaned gateway is still running. Windows correctly raises `FileExistsError` here.

**T9. Possible but not observed: the `StateBlob` header may not be atomic. Severity: low, unverified.**
`seq` and `len` are written with one 12-byte `pack_into`, which is not guaranteed atomic, so a reader could pair a new `seq` with an old `len`. A probe hammering it read 3,067 frames with 0 invalid JSON.

## Good things
- **Clean single-writer layout.** There is one writer per segment, fixed-layout numpy rows, and a `u8` seq that cannot wrap round to an old value (no ABA). The gateway skips work when `gseq` has not changed (`gateway.py:76-78`). Every field is 8 bytes, so they all sit on 8-byte boundaries and x86 reads each one whole.
- **Windows shared-memory handling is right.** `track=False` keeps the 3.13 resource tracker from unlinking the segment (`table.py:77-84`). The Windows `FileExistsError` is turned into an actionable message (`run_apex.py:61-65`). The supervisor keeps a handle for the whole session, so the segment never disappears under the children.
- **Clean stop.** The children ignore SIGINT and stop through the `ctrl.stop` flag. The feed also handles engineio re-installing SIGINT (`feed_breeze.py:528`).
- **Row renumbering is handled.** Positions are tracked by contract key, not row id (`paper.py:343-348`). The engine detects renumbering and resets its price history (`engine_main.py:101-108`). A live feed restart zeroes the rows, which also resets their parity.
- **Atomic writes where they exist.** The registry and chain use atomic writes with a Windows retry (`feed_core.py:41-49, 94`). `record_day` and `learn` are idempotent per evening, and a test covers it.
- **The feed heals itself.** It reconnects after 30 s of silence in market hours and genuinely tears down the old stream (`feed_breeze.py:450-455, 520-523`).

## Ideas from GitHub
1. **rigtorp/Seqlock**, https://github.com/rigtorp/Seqlock, MIT (cloned).
   - What to borrow: in `include/rigtorp/Seqlock.h`, `load()` loops `while (seq0 != seq1 || seq0 & 1)` until it gets a clean copy, and `store()` is a single function that bumps `seq` on both sides of the write.
   - Where it goes (tool/infra, deployed between sessions): wrap `Table.begin/end` in one `write_row()` context manager (with `finally: end`). Give `snapshot()` a bounded, yielding retry that returns a `bad` mask; the engine reuses the previous frame's row for any masked row.
2. **Supervisor/superlance**, https://github.com/Supervisor/superlance, BSD-style repoze licence (cloned). This is a concept borrow.
   - What to borrow: `superlance/httpok.py`, which on a TICK event checks a process's health and restarts it if it is unhealthy, even though it never exited.
   - Where it goes (an observer plus the supervisor): `supervise()` reads `engine_hb_ns` and `feed_hb_ns` every second. If a heartbeat is older than 10 s in market hours, it logs, terminates and respawns that process. It also publishes `hb_age` for a red "ENGINE STALE" banner.
3. **untitaker/python-atomicwrites**, https://github.com/untitaker/python-atomicwrites, MIT (archived, cloned).
   - What to borrow: `atomicwrites/__init__.py`, which fsyncs the temp file and then calls `MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH)` on Windows.
   - Where it goes: one `atomic_write(path, text)` helper in `feed_core`, with `replace_retry`, used by `record_day`, `save_books`, the learning state and the report. That closes T5 and T6.
4. **tox-dev/filelock**, https://github.com/tox-dev/filelock, MIT (cloned).
   - What to borrow: the exclusive cross-platform lock file (`src/filelock/_windows.py` uses `msvcrt.locking`).
   - Where it goes: `supervise()` holds `data/<mode>/apex.lock` for the whole session. That guarantees one instance per data directory on any OS, whatever the shared-memory semantics (T8).

## Top 3
1. **A heartbeat watchdog in `supervise()` plus a dashboard staleness banner** (T3, with T7 backoff and reset). Size M, **before Monday**.
2. **Seqlock hardening**: a try/finally writer, a yielding snapshot retry that returns a bad mask, and a re-check in the gateway (T1, T2). Size S, **before Monday**. The fix has already been validated by probe.
3. **Durability** (T4, T5, T6):
   - Save books when `best` or `trail` changes, throttled to 1 Hz.
   - Make `days.jsonl` atomic.
   - Give the engine its own shutdown deadline and wait for it first.
   - Use `replace_retry` everywhere.

   Size S/M, **before Monday**. The `days.jsonl` part alone is S.
