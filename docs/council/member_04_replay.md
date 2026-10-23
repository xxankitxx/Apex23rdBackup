# Member 04: Replay and backtest reproducibility

## Lens
Can a recorded day be replayed with the same decisions every time, and the same as live? I read `feed_replay.py`, `feed_core.py` (`Recorder`, `apply_packet`), the recorder hooks in `feed_breeze.py`/`feed_sim.py`, `engine_main.py`, `guard.py`, persistence in `paper.py`/`learning.py`/`ledger.py`, and `run_apex.py`, and looked for look-ahead.

**Tests** (private copies in `/tmp/council/04/`, each with its own shared-memory names and port; a first run paused by another member was discarded and re-run):
1. Recorded one sim day (`--speed 40 --seed 7 --record`): 6,560,755 packets, 469 MB gzip.
2. Replayed it twice at speed 40 (R1, R2; run concurrently, so competing for CPU as on a real evening).
3. Replayed a 09:15–10:05 cut twice in one folder (R3).
4. Replayed a crash-then-restart file (R4).

## Teardown

**F1. The multi-process replay is not deterministic. Two replays of the same file give different trades. CRITICAL.** Verified with R1 against R2.
- **Where:** `engine_main.py:708-709`. The engine sleeps `0.1/speed − loop time` on the wall clock and reads whatever the feed has written by then. It is not locked to the recorded timeline.
- **Measured (my probe added to the copy):** at speed 40 the engine's median step was 0.75–1.0 virtual seconds, and the 90th percentile 1.25–1.5 s. Live runs at 100 ms. So replay samples the 15-second impulse and run-score windows about 10 times more coarsely than live, and the sampling grid changes with CPU load.
- **Result:** across the two replays, **0 of 17 books matched.**

  | Book | R1 | R2 |
  |---|---|---|
  | futures_only | 85 trades, +705.3 pts | 81 trades, +753.8 pts |
  | straddle_spike | 41 trades, +287.2 pts | 43 trades, +253.4 pts |
  | m2.0_s0.5 | +91.8 pts | +86.9 pts |

  The same entry (09:59:03 PE 25100) exits at different prices. The original sim run against a replay differs too: m2.5_s0.5 has 1 trade in one and 2 in the other.
- **Why it matters:** "check a changed rule against real sessions" (`feed_replay.py:6-7`) fails when two runs of the *same* rule differ by about 5–15 % of P&L; variants and controls would be judged partly on scheduling noise.
- **Context:** the design asked for "lockstep + timed" replay (`01_MASTER_DESIGN.md:274`); only timed exists, and `05_STRENGTHENING.md:135` flagged it "not yet verified".

**F2. Replaying the same day twice adds the second run on top of the first. HIGH.** Verified with R3.
- **Where:** `engine_main.py:133`. `paper.load_books(day)` reloads `data/replay/paper/<day>.json` from the previous replay. The observer files (`ledger.py:122`, `extras.py:192`, `straddle_watch.py:299`) open in append mode.
- **Result after the second replay:**
  - futures_only went from 9 to 19 trades, and its capital from ₹2,43,195 to ₹6,04,644. The second run compounded on top of the first.
  - candidates went from 16 to 32 lines, and episodes from 21 to 43.
  - Learning logged "already learned — decisions not repeated".
- **Also:** state carries over between *different* replay days through `data/replay/learning/state.json`, so the result of a replay depends on which replays were run before it (D-053 isolates replay from live, but not one replay from another).

**F3. A feed crash followed by a supervisor restart leaves a tick file that replay cannot read past the crash. Replay then hangs. HIGH.** Verified with a probe and R4.
- **Where:**
  - `feed_core.py:338` opens the day file in gzip append mode (`"at"`).
  - `feed_breeze.py:571-578` re-raises the error, so the Recorder's daemon thread is killed before the gzip trailer is written. Up to about 1 s of queued packets is lost as well.
  - The restarted feed appends a second gzip member after the truncated one.
- **Result:** reading fails with `zlib.error: invalid block type`. In my probe, 4,978 of 8,000 lines were readable, and the 3,000 lines written after the restart were lost even though they are intact on disk.
- **The replay side makes it worse:** `feed_replay.py:61` catches only `(EOFError, OSError)`, and `zlib.error` is not a subclass of either. The replay feed dies, `feed_state` never reaches 7, and the engine waits forever. R4 hung until `timeout` killed it (exit 124), with no end of day and no learning.
- **Why it matters:** feed-crash days are exactly the gap days D-063 exists to study.

**F4. Feed outages are not in the recording, so replay rebuilds them differently. MEDIUM.** Verified by reading.
- **Where:**
  - `feed_replay.py:47` sets `feed_state=6` for the whole replay. The live states 1, 3 and 4 (connecting, reconnecting, dead) are never recorded.
  - `feed_replay.py:80` advances `now_ns` only when a record arrives. During a live websocket stall, the replay clock freezes (only `vix`/`chain` REST records move it), so the futures quote never looks stale.
- **What happens instead:** the blackout appears late, as "engine paused" when the 30 s jump arrives (`guard.py:50`), instead of as "stale" after 3 s. Clock-driven TIME exits inside the gap fire at the resume price in replay but at the stale price live.
- **Smaller recording gaps:**
  - `Recorder.dropped` (`feed_core.py:335`) is counted but never logged or written, so packets lost to a full queue disappear silently.
  - Sim recordings contain no `vix` records (`feed_sim.py:419`).

**F5. Recording order is not application order. MEDIUM.** Verified by reading, not reproduced.
- **Where:** `feed_breeze.py:404-407`. `recv` is stamped before the lock, `apply_packet` runs under the lock, and `rec.put` runs after the lock is released. The SDK dispatches each packet on its own thread, so two packets can be applied as A then B but recorded as B then A.
- **Effect:** the recorded timestamps can go backwards. The `ttq` monotonic guard (`feed_core.py:266`) then drops a different packet in replay than it dropped live, so rows differ from the very first packet. Since `on_message` already holds the lock, moving `rec.put` inside it fixes this.

**F6. Nothing records which code and state produced a recording. MEDIUM.** Verified by reading.
- A tick file holds packets, registry, chain and VIX. It does not hold the git commit, a hash of `VARIANTS`/`CONTROLS`, or the live learning state at the open (champion, gates, candidates).
- So a replay of Monday runs with whatever champion `data/replay` happens to hold, and "the same decisions as live" cannot be reproduced even in principle. `cmd_learn --mode replay` also learns the *wall* date (`run_apex.py:305`), not the replayed day.

**Low:**
- Fixed shared-memory names (`config.py:38-39`) plus the port check mean yesterday cannot be replayed while live is running.
- A 469 MB gzip per sim day may not sustain high replay speeds (unverified for live-sized days).
- No look-ahead found: `now_ns` is set before each packet is applied, the chain is stamped on arrival, the random control is seeded per day and book, and learning reads only finished days. The only skew is the snapshot running up to (loop time × speed) ahead of `now_s`.

## Good things
- **One parser** (`apply_packet`, `feed_core.py:242`) for live, sim and replay, fed the raw Breeze list, so a parser fix can be replayed over old days.
- **Non-blocking hot path:** only `put_nowait` (`feed_core.py:329-335`).
- **Registry snapshots in the stream**, and `load_registry` resets history when row ids move (`engine_main.py:103`).
- **Deterministic random control:** `random.Random(f"{day}:{name}")` (`paper.py:229`).
- **Learning dedupes by day** (`learning.py:153-176`), which kept F2 out of the learning state.
- **The engine-pause guard** (`guard.py:50`) is the right defence against a sampling hole, and it is tested.
- **Sim `--gap` and `--record`** make fixtures possible without a broker login.

## Ideas from GitHub
1. **QuantConnect/Lean** (Apache-2.0), https://github.com/QuantConnect/Lean, file `Engine/DataFeeds/SubscriptionSynchronizer.cs` (opened). Frontier clock: consume data only while `EmitTimeUtc <= frontierUtc`, build one slice, then step the algorithm. **Apex mapping:** a **tool**, `apex/replay_lockstep.py`, running in one process. It builds `Table` and `Engine` in-process, applies packets with `t ≤ k·100 ms`, calls `Engine.step()` once per 100 ms of virtual time, and skips `publish()` and the sleeps. This fixes F1 and is the base for the twice-identical test.
2. **nautechsystems/nautilus_trader** (LGPL-3.0, concept only), https://github.com/nautechsystems/nautilus_trader, file `crates/common/src/clock/virtual.rs` (cloned). `VirtualClock.advance_time` returns due timers "in ascending order by event timestamp and timer name" and panics if time goes backwards. **Apex mapping:** in the lockstep tool, make the 4 Hz Greeks, the 1 Hz history and the 15:31 end of day ordered virtual timers, and add a **replay assertion** that recorded `t` never decreases (detects F5).
3. **databento/dbn** (Apache-2.0), https://github.com/databento/dbn, README (opened). A "self-describing metadata header" on every data file. **Apex mapping:** the `Recorder` writes a first `meta` record (schema version, git commit, a hash of `VARIANTS`/`CONTROLS`/guard constants, the learning state at the open) and a closing one with `dropped`. Replay seeds its run folder from the header and warns when the code hash differs (F6).

## Top 3
1. **Self-describing, crash-safe recordings** (S, **before Monday**: the first live file cannot be fixed after it is written). Add the `meta` header; open a new part file on every Recorder start instead of appending a gzip member; write `dropped`; add a 250 ms `hb` record with `feed_state` (F4); move `rec.put` inside the lock (F5); in replay, also catch `zlib.error` and still set `feed_state=7`.
2. **One folder per replay run** (S, **before Monday**): `data/replay/<file-stem>-<run-timestamp>/`, seeded from the `meta` learning state, so a replay never resumes another replay's books, ledger or learning (F2).
3. **Lockstep replay plus a twice-identical CI test** (M, **later**, but before any rule change or advisor is judged on replayed days). Use Monday's recording as the fixture, and assert byte-identical `paper/<day>.json` and `candidates_<day>.jsonl` across two runs (F1).
