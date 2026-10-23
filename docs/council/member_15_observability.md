# Member 15: Observability, logging and audit trail

## Lens
After a bad day, can the owner rebuild why each decision was made? I looked at the tick tape (`feed_core.Recorder`), engine/feed logs, the dashboard state blob, books JSON, trades CSV, the candidates/episodes/straddle jsonl files, `days.jsonl` and `report.md`. I ran the tests (they all pass) and wrote two probe scripts in `/tmp/council/15/`.

## Teardown

**1. CRITICAL: one feed crash corrupts the rest of the day's tick tape, and replay then crashes on it. Verified by probe.**
- `feed_breeze.py:507-530`: `run()` has no `try/finally`. Any exception that is not a KeyboardInterrupt skips `shutdown()`, so `rec.stop()` never runs. The recorder is a daemon thread (`feed_core.py:213`), so the gzip member is never closed. The same is true for a hard kill (supervisor `terminate()`/`kill()` at `run_apex.py:110-116`, console close, power loss).
- The supervisor restarts the feed (`run_apex.py:96-101`). The new `Recorder` opens the same `data/ticks/DAY.jsonl.gz` in `"at"` mode (`feed_core.py:225`) and appends a new member after the broken one.
- Probe (`/tmp/council/15/probe_gz.py`): process 1 writes and flushes 1,000 lines, then `os._exit`. Process 2 appends 1,000 more lines and closes cleanly. Reading the file back fails after 785 lines with `zlib.error: invalid block type`. Every line written after the restart is unreadable.
- `feed_replay.py:61` catches `(EOFError, OSError)`, but `zlib.error` is not an `OSError` (checked: `issubclass(zlib.error, OSError) == False`). I ran the replay loop's own except clause against the file and the exception escapes, so the replay feed dies with a traceback.
- Failure scenario: the feed throws once at 11:00 and is restarted. The tape for 11:00-15:30 is lost for good, and the very day you most need to replay is the one that cannot be replayed.
- Fix (size S): wrap the loop in `try/finally: self.shutdown()`. Give each process start its own file (`DAY.<pid or start_ns>.jsonl.gz`) and have replay merge the parts in order. Catch `zlib.error` and `gzip.BadGzipFile` in replay.

**2. HIGH: the champion's reason path is never saved, only one sample of it.**
- `engine_main.py:567-568`: `last_reason` is overwritten every 100 ms. It reaches disk only twice per episode: at the m* crossing (`ledger.py:80`, `decision_at_cross`) and at onset (`extras.py:177`, `verdict_at_onset`).
- `self.events` (`engine_main.py:69`, `deque(maxlen=120)`) holds ENTRY, EXIT, GAP, ARMED, SPIKE and LEARN events. It lives in memory and in the dashboard blob, and is never written to a file (verified by grep: no writer exists).
- Failure scenario: an episode shows "synchrony 0.42 < 0.5" at the cross, then 20 s later "LATE: futures already 31 pts". The owner sees only the first reason, so `diagnostics.reason_class` puts the miss in "basket too thin" when the real blocker was lateness. A restart in the middle of the day also wipes the event tape.
- Fix (size S): add `decisions_DAY.jsonl`. For every book, append a row whenever its reason class changes (dedupe on class), with `t`, book, reason, z, S, moved, iv_rise and episode id. Also append every `ev()` call to `events_DAY.jsonl`. This adds a few hundred lines a day.

**3. HIGH: the tick tape can drop data without telling anyone.**
- `feed_core.py:218-221`: when the queue is full, `Recorder.put` increments `self.dropped`. Nothing ever reads `dropped` (grep shows only the two lines that define and increment it). It is not in the table, the log or the dashboard.
- Replay would then differ from live with no warning. Fix (size S): publish `rec_dropped` as a table counter, log it at stop, and write a final `{"k":"meta","dropped":N}` line to the tape.

**4. MEDIUM: engine log timestamps use the wall clock, so sim/replay logs don't line up with market time.**
- `engine_main.py:42` uses `datetime.now(IST)`, but `ev()` and every jsonl record use the virtual `now_dt`. A replay at 20x speed logs "12:03:11 ENGINE ledger: KeyError" with no way to tie it to the 10:41 candidate. Fix: log both, `wall | mkt=HH:MM:SS`.

**5. MEDIUM: replay and sim reruns double-count in the diagnostics.**
- `Ledger._write` (`ledger.py:122`), `EpisodeLog._flush` (`extras.py:192`) and StraddleWatch all append, and `diagnostics.load_candidates` (`diagnostics.py:33-46`) does not dedupe. Replaying the same day twice into `data/replay` doubles that day's candidates, which narrows the Wilson intervals with fake data. `record_day` is idempotent; these files are not. Verified by reading only. Fix: dedupe on `(day, id)` in `load_candidates`, or truncate the per-day files in `start_day` when the books file does not exist yet.

**6. MEDIUM: no record says which code or config produced it.**
- No trade, candidate, `days.jsonl` row or report stamps `apex.__version__` or a hash of `config.VARIANTS`/thresholds. `learning._r` already has to guess "legacy rows: premium points" (`learning.py:57-60`). `report.md` is overwritten every evening (`learning.py:403`), so the report that justified yesterday's champion change is gone. Only one-line entries survive in `state.log`.
- Fix (size S): add `v` (version) and `cfg` (an 8-character sha of the frozen params plus advisor list) to every record, and also write `report_DAY.md`.

**7. MEDIUM: a stalled engine or an oversized state blob just looks like a frozen screen.**
- `StateBlob.write` (`table.py:165-166`) silently `return`s when the state is over 2 MB.
- `engine_hb_ns` is written (`engine_main.py:705`) but never read anywhere. The supervisor only checks for process exit, and `app.js` has no staleness check (grep for stale/hb finds nothing).
- Failure scenario: the engine hangs inside a Greeks solve. The dashboard keeps showing the last ENTRY with live-looking numbers, and no gap event is recorded because the guard runs inside the same stalled loop.
- Fix: the gateway compares `engine_hb_ns` with the current time and adds `engine_age_s`, and the UI shows a red banner when it exceeds 2 s. Log the oversize case once per minute.

**8. LOW: what survives in the analysis files is thinner than what was recorded.**
- `days.jsonl` stores advisors as booleans only (`learning.py:172`).
- The trades CSV (`paper.py:456-458`) is champion-only and drops `episode`, `delta_in`, `iv_in`, `stop_fut`, `peak_pts`, `exit_quote_age` and the advisors.
- The full detail is in `paper/DAY.json`, so nothing is lost, but the owner's spreadsheet view hides it.
- `run()` logs a full traceback on every failing step (`engine_main.py:702`) with no rotation.

## Good things
- **The position record is a real audit snapshot.** `paper.open_trade` (`paper.py:318-328`) freezes the reason string, every advisor's verdict *with its `why` text*, delta, IV, entry bid/ask, regime and episode id. `close_trade` adds exit bid/ask, quote age, `stale_exit` and `fut_out`.
- **Books are written atomically** (`paper.py:433-438`, tmp file plus `os.replace`) after every trade change (`engine_main.py:585`), so a crash loses no trades.
- **The candidate ledger** (`ledger.py`) is the strongest observability piece. It records every m* crossing, taken or not, labels it with no reference to whether it was taken, and marks `follow_gap`/`truncated` honestly. `diagnostics._row` excludes truncated NEITHER rows correctly.
- **Episode and spike ids come from the virtual clock** (`domino.py:166`, `straddle_watch.py:254`). They are deterministic in replay and do not collide after an engine restart.
- **The tape records raw packets with receive time, plus REST, chain and registry snapshots** (`feed_breeze.py:545`, `:504`), so replay can rebuild row re-numbering.
- `record_day` is idempotent per day and records empty days (`learning.py:158-180`), and `test_learn_is_idempotent_per_evening` tests it.
- Observers are wrapped in rate-limited try/log (`engine_main.py:238-241`, `255-258`, `290-293`), so a broken advisor cannot stop the loop.

## Ideas from GitHub
1. **freqtrade/freqtrade**, https://github.com/freqtrade/freqtrade, GPL-3.0 (concept only, no code).
   - `docs/advanced-backtesting.md` and `freqtrade/data/entryexitanalysis.py`: `backtesting-analysis --analysis-groups 0..5` gives profit by `enter_tag` × `exit_tag`, and `--rejected-signals` prints every signal that was suppressed.
   - Mapping: an `run_apex.py report --groups` tool that reads `paper/DAY.json` plus the new `decisions_DAY.jsonl`. It would show tables by entry reason class × exit reason (STOP, TRAIL, THESIS, TIME), and by rejection class over time, not just the reason at the cross.
   - This is an offline tool, so it does not touch the trigger.
2. **simonw/sqlite-utils**, https://github.com/simonw/sqlite-utils, Apache-2.0.
   - `sqlite-utils memory` (docs/cli.rst:464-496) loads CSV/JSON files into a temporary in-memory database and runs SQL on them in one command. `insert --nl` loads jsonl.
   - Mapping: a `run_apex.py autopsy DAY` tool. It loads `candidates_`, `episodes_`, `straddle_`, `decisions_` and the trades into one SQLite file keyed on episode id, so "why no trade at 10:41?" becomes a single join.
   - This is a dev tool only, with no runtime dependency.
3. **hynek/structlog**, https://github.com/hynek/structlog, MIT/Apache-2.0.
   - `contextvars.bind_contextvars`/`merge_contextvars` (`src/structlog/contextvars.py:82,119`) bind context once, and every later log line carries it as JSON.
   - Mapping: in `engine_main.step`, bind `mkt_t`, `episode`, `champion`, `cfg` and `v`. Then every `log()` line and decision row is machine-joinable to the ledger. This fixes findings 4 and 6 together.
   - Swapping the 6-line `log()` for a JSON formatter is enough; adding the dependency is optional.

## Top 3
1. **Make the tick tape survive a crash** (finding 1): `try/finally` shutdown, one file per process start, and replay catching `zlib.error`. Size S, **before Monday.**
2. **Persist the decision and event tape** (findings 2 and 3): `decisions_DAY.jsonl` written when a reason class changes, `events_DAY.jsonl`, and the recorder drop counter surfaced. Size S, **before Monday.**
3. **Provenance and liveness** (findings 6 and 7): stamp version and config hash on every record, write a dated `report_DAY.md`, and add an engine heartbeat staleness banner. Size S-M, **later** (the heartbeat banner part could go before Monday).
