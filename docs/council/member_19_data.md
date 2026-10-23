# Member 19 — Data storage, persistence & lifecycle

## Lens
What lands under `data/` (ticks, paper books, learning state, `days.jsonl`, candidates, episodes, straddle), and whether it holds up through crashes, mid-day restarts, months of growth and schema changes. Method: read `paper.py`, `learning.py`, `engine_main.py`, `ledger.py`, `extras.py`, `feed_core.py`, `feed_replay.py`, `feed_breeze.py`, `run_apex.py`, `table.py`, `diagnostics.py`. Wrote three probe scripts in `/tmp/council/19/` against a scratch `APEX_DATA`. The test suite passes at baseline.

## Teardown

**F1 — CRITICAL. A live session stopped before 15:30 is never recorded for learning.** `engine_main.py:717` runs `end_day()` on shutdown only when `mode != "live"` or the time is ≥ 15:30. `end_day()` is the only caller of `learning.record_day` (`engine_main.py:165`; grep finds no other caller outside the tests). On the next morning a fresh process starts with `self.day = None`, so `step()` (`:187`) goes straight to `start_day(today)` and the previous day is never closed. `run_apex.py learn` (`cmd_learn`, `:298`) runs `learn()` without calling `record_day`, and `learn()` reads only `days.jsonl` (`learning.py:180`).
*Scenario:* the owner presses Ctrl+C at 15:27, after the 15:25 flatten, which is the natural moment to stop. Or the PC sleeps or crashes at 15:29. That day's trades exist in `paper/<day>.json` but never reach `days.jsonl`. SPRT, challenger t-tests and advisor screens all run on a sample with days silently missing, and the missing days are not random: they are the days the owner or the machine stopped early. *Verified:* by reading the code path end to end.

**F2 — HIGH. `days.jsonl` is rewritten in place without an atomic swap, and its reader cannot survive one bad line.** `record_day` reads every row, then calls `open(DAYS, "w")` and rewrites the entire history (`learning.py:175-177`). It does not write to a temp file and swap it in, which `save_state` and `save_books` both do. A crash or power cut during that write truncates the only learning record. Neither reader (`learning.py:164`, `:187`) catches decode errors.
*Probe:* I appended one torn line. After that, `record_day` and `learn()` both raise `JSONDecodeError`. Every later evening then fails inside `end_day`: the exception is swallowed by the run loop at `:701`, and `_learned` is already set, so nothing retries. Learning stops permanently and silently. *Verified:* probe.

**F3 — HIGH. Open-position exit state is not saved between entry and exit, so a restart can revert an armed trail to the original stop.** `run_books` saves only when an entry or exit happened (`engine_main.py:585`). `check_exit` updates `pos["best"]`, `pos["trail"]`, `pos["peak_pts"]`, `pos["pending"]` (a committed exit) and `pos["last"]` on every step without saving (`paper.py:355-366, 400`). The supervisor restarts a dead engine with the message "books are on disk" (`run_apex.py:89`), but the books on disk are as they were at entry.
*Probe:* entry at futures 25000 with d*=12; futures run to 25040, so the trail arms and the stop sits at 25028. The engine "crashes" and reloads, and comes back with `trail=False`, `best=25000`. At 25025 the live book exits on TRAIL and the restarted book holds, with its stop back at 24988→25013 after re-arming. The record now depends on crash timing; a committed `pending` exit is also forgotten. *Verified:* probe.

**F4 — HIGH. A crashed feed leaves a tick file that replay cannot read past the crash.** The `Recorder` appends a gzip member per process (`feed_core.py:224`, mode `"at"`). In `feed_breeze.main()` (`:574-578`) the exception path re-raises without calling `rec.stop()`, and the writer is a daemon thread, so a crash leaves a member with no trailer and loses whatever was still queued. The supervisor then restarts the feed, which appends a new member to the same file.
*Probe:* 5,000 lines with a hard exit, then 3,000 lines appended. Reading back gives `zlib.error: invalid block type` after 4,987 lines. Every tick after the restart is unreadable. `feed_replay.py:61` catches `(EOFError, OSError)`, but `zlib.error` subclasses neither, so the replay process itself dies instead of logging "recording ends early". *Verified:* probe.

**F5 — MEDIUM. Corrupt state silently resets to defaults, and the next save overwrites the evidence.**
- `learning.load_state` (`:132-139`) catches every exception and returns the registered defaults: champion back to default, `retired`, `candidates`, streaks and `log` emptied. The next `save_state` writes those defaults over the file.
- `paper.load_books` (`:449`) returns `None` on any parse error, so every book restarts at ₹1,00,000 flat, and the first `save_books` replaces the corrupt file.
- None of `save_books`, `save_state` or `Registry.save` calls `fsync`. On Windows/NTFS a power loss after `os.replace` can leave a zero-length file, which then triggers exactly this silent reset.

*Verified:* by reading. The fsync and power-loss behaviour is not reproduced (unverified).

**F6 — MEDIUM. A restart throws away what the observers were following.** `Ledger.open`/`seen` (`ledger.py:45`), the open episodes in `EpisodeLog` and the straddle state live only in memory. A restart drops every candidate still inside its 15-minute follow, and those records are never written, not even as `truncated`. The candidate base rates (D-070) therefore under-count exactly the stretches around crashes. The `momentum` control's `armed` flags (`paper.py:268`) also reset on restart, which can re-fire.

*Verified:* by reading.

**F7 — LOW–MEDIUM. Nothing limits disk growth, and no file has a schema version.** OQ-18 decided 90-day tick retention, and G5 asks for a disk check at preflight and at 12:00. Neither exists in code: grep finds no prune, `disk_usage` or retention logic. `Recorder.dropped` is counted but never published. At the estimated 1–2.5 GB/day, a year of ticks is 250–600 GB. The logs (`engine.log`, `feed.log`) are append-only with no rotation, and a recurring exception logs a full traceback every 0.5 s (`engine_main.py:702`). No file carries a schema version: old rows are read through `t.get("ret_pct")` fallbacks (`learning.py:57`), which cannot tell a pre-D-064 row from a buggy one.

*Verified:* by reading and grep.

## Good things
- **Temp file then `os.replace`** is used for books (`paper.py:433-438`), learning state (`learning.py:146-150`), the registry, and the chain snapshot, which uses `replace_retry` for Windows sharing violations (`feed_core.py:41-49`).
- **Separate data roots for sim and replay**: `APEX_DATA` is set per mode (`run_apex.py:40-46`), so a simulator can never pollute the live paper record. - **Episode, spike and control ids are derived from time**: `int(now_s*10)`, `int(now_s)`, `-(1e7+sod)` (`domino.py:166`, `straddle_watch.py:254`, `paper.py:256`). Because of this, `fired_episodes` survives a restart without id reuse, and random-control schedules come from a fixed seed (`random_schedule`).
- **Positions are matched by contract key, not row id** (`paper.py:343`): a feed restart that renumbers rows cannot price an exit off another contract (covered by a test).
- **`record_day` is idempotent per day** and records empty days as 0 % days (`learning.py:158-165`). The candidate reader skips bad lines (`diagnostics.py:42-45`), and the StateBlob seqlock skips oversize states instead of tearing them (`table.py:163-182`).

## Ideas from GitHub
1. **untitaker/python-atomicwrites**, https://github.com/untitaker/python-atomicwrites, MIT (archived 2022). Its README sets out the protocol: temp file in the same directory, `fsync` on the file, rename, then `fsync` on the parent directory (`_commit` on Windows). *Map:* no dependency needed. Add a ~15-line `apex/fsio.py` with `atomic_write_json(path, obj)` (write tmp, flush, `os.fsync`, `replace_retry`) and an `atomic_write_lines(path, rows)`. Route `save_books`, `save_state`, `Registry.save`, `write_chain` and above all `record_day` through it.2. **freqtrade/freqtrade**, https://github.com/freqtrade/freqtrade, **GPL-3.0, so the concept only and no code copied**. In `freqtrade/persistence/migrations.py`, `check_migrate()` detects the shape of a stored record (whether a `record_version` column exists), migrates on startup with defaults for missing fields, renames legacy values (`sell_signal`→`exit_signal`), and refuses records too old to migrate. *Map:* add `"schema": N` to every row in `days.jsonl`, the candidates, the episodes and the books, plus a `migrate(row)` table in `learning.py` that upgrades old rows when they are loaded and refuses unknown versions loudly. That replaces the scattered `t.get(...)` fallbacks and makes "pre-D-064 row" explicit.
3. **wbolster/jsonlines**, https://github.com/wbolster/jsonlines, BSD-3-Clause. A JSON Lines reader and writer with an explicit invalid-line policy (`skip_invalid` / raise). *Map:* one shared reader for every `*.jsonl` under `data/`, with a policy decided per file: learning inputs skip and count bad lines, and the report prints "N corrupt rows skipped". This removes F2's permanent stall and makes the tolerance in `diagnostics.py` uniform.

## Top 3
1. **Make sure no day goes unrecorded (F1 + F2)** — S, **before Monday.**
   - In `start_day`, and in `cmd_learn`, scan `paper/*.json` for days after the last day in `days.jsonl` and `record_day` them. Flag a stale open `pos` as `unclosed`.
   - Make `record_day` write tmp, fsync and replace.
   - Make `_load_days` and `record_day` skip and count torn lines.
   - Add a test: engine stopped at 15:27, next-day start, and the previous day appears in `days.jsonl`.
2. **Persist exit state and make tick files survive a feed crash (F3 + F4)** — S/M, **before Monday.**
   - Save books once a second while any book has `pos` (or whenever `trail`, `best` or `pending` changes).
   - In `feed_breeze.main()`, wrap `run()` in `try/finally: rec.stop()`.
   - Give each feed process its own segment file (`DAY.partN.jsonl.gz`), have replay chain the segments, and catch `zlib.error` in replay.
   - Add tests for restart-with-armed-trail and truncated-segment replay.
3. **Lifecycle hygiene (F5 + F7)** — M, **later.**
   - On a parse failure, rename the bad state or books file to `.corrupt-<ts>` and show a red dashboard banner instead of silently resetting.
   - Add a `schema` field and migrate-on-load (idea 2).
   - Prune ticks after 90 days, and check free disk at preflight and at 12:00.
   - Publish `Recorder.dropped`, and use a `RotatingFileHandler`-style cap on the logs.
