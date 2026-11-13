# 55. Runtime fixes and speed-ups before the 13 Nov session

Owner, 13 Nov early morning: "Make the code production ready. Thoroughly check all logs, find and remove all runtime
bugs and errors that we have encountered till now. Make the code highly optimized and fast."

No decision logic changed: no book, rule, Conductor or pool file was touched. Everything below is persistence,
process set-up, display cadence or the Forecast Lab's display.

## What the logs showed (9 to 12 Nov)

| Where | What | Count | Cause |
|---|---|---|---|
| engine.log | books file swap refused, `PermissionError: [WinError 5]` | in the per-minute line most of 12 Nov | Windows (Defender, indexer) holding the fresh 14 MB file; the saver retried later, nothing lost |
| replays p44 | four days died at a `chain_latest.json` swap | 4 of 17 | the helper gave up after 1.8 s and raised |
| Forecast Lab | dashboard file writes refused | 1,726 | same lock, 5 tries 30 ms apart |
| Forecast Lab | loop p50 10 ms at 09:00, 250 ms at 15:00; 2,468 s skipped | | machine-wide contention: the engine's step slowed 4 times in the same minutes (all of its parts at once) |
| engine | books file rewritten about 4,700 times on 12 Nov, 14 to 17 MB each | | "exit state" saves allowed once a second |
| engine | full state published 4 times a second | 1,292 s of CPU in the session | |
| all processes | numpy's OpenBLAS pool of 16 threads in the feed and engine | | not capped outside the replays and the Lab |
| feed.log | "Session key is expired" tracebacks at start | 5 | today's session token not yet saved; the log now says what to do |
| feed.log | broker network drops, empty replies (`Expecting value`) | about 400 | broker side; the poller already carries on |
| account_sim | crash printing the rupee sign on a cp1252 console | | |

## Changes

1. `apex/fsutil.py` (new): one patient file swap for every writer. Retries a Windows lock with a growing wait inside a
   time budget (3 s for durable files, 0.25 s for files rewritten every second). Snapshot writers never raise.
   Used by the engine's books, learning, day state, strike levels and warm files, the feed's registry and chain
   snapshot, the replay driver, the Conductor's register and clock norms, and the Forecast Lab.
2. `feed_breeze.write_chain`: a refused swap returns False and leaves the chain version alone (four replays died here).
3. `engine_main`: exit-state saves (a trail or best moved, no trade) at most every 10 s (`EXIT_SAVE_MIN_S`, was 1 s).
   Entries and exits still save at once. About 3 times fewer 14 MB rewrites.
4. `engine_main`: dashboard state published twice a second (`PUBLISH_EVERY_S`, was 4 times).
5. `run_apex.py`: every child process gets one math-library thread (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
   `MKL_NUM_THREADS` = 1 unless already set), as the replays have always run.
6. Forecast Lab: the measured-decay rows are cached on their exact inputs (the quotes in the window and the chain's
   clock change every 5 s, the panel asks every second, and a strike's call and put solved the same implied vols
   twice). Payloads are identical with and without the cache.
7. Feed login: a refused session says in plain words to save a fresh session token and restart.
8. `account_sim`: prints without the rupee sign when the console cannot show it.

## Not done here

* Windows Defender exclusion for `D:\ApexOptions\data` would remove most of the file-lock and scan load. It is a
  security setting; only the owner should change it (Windows Security, Virus and threat protection, Exclusions).
* The heaviest books (`spot_dc12_t12_first*`, about 250 ms on a slow tick) are decision code under the 7-test
  standard; speeding them up needs a replay proof that every trade is unchanged.

Tests: `tests/test_fsutil.py` (new) and the full suite; see the commit.
