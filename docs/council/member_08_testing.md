# Member 08: Test strategy and test quality

## Lens
`tests/test_core.py` (28 tests, all pass). I asked which tests pass for the wrong reason, which critical paths have no test, and which property-based or replay tests are missing. Methods:
- I read the code.
- I ran a **mutation run**: 27 one-line breaks to safety-critical logic, with the full suite run against each (`/tmp/council/m08/mutate.py`).
- I ran unit probes (`/tmp/council/m08/probes.py`).
- I ran a headless sim with shared-memory names and the tick directory isolated (`/tmp/council/m08/e2e.py`, `run_mod.py`).

## Teardown

**T1 (critical, verified by mutation): the suite kills 1 of 27 mutants.** Only "remove the ttq monotonic guard" fails a test. The suite stays green after each of these breaks:
- Exits: the futures-stale gate, THESIS-VOID, the 0DTE 15:00 flatten, and the BOOK exit (`paper.py:370-395`).
- Entries: the once-per-episode check, the L* LATE check, the IV-rise cap, the synchrony check, the 09:25–15:15 window, and promoted gates (`paper.py:146-186`).
- Contract choice: the 0DTE delta band, and the age-<15 s quote filter (`paper.py:113,125`).
- Restart: `fired_episodes` not restored (`paper.py:52`).
- Feed parsing: an OI-zero overwrite, cash tbq/tsq swapped, cash ltt/close swapped (`feed_core.py:163,170-171`).
- Table: the snapshot seqlock re-read removed (`table.py:133`).
- Learning: LODO dropped, `already_learned` always False, `record_day` not idempotent (`learning.py:155,165,231`).
- Every engine wiring change: guard-taints-episode, `learn_scales=not guard.on`, history reset on renumber, end_day idempotence (`engine_main.py:104,159,231,242`).
- The replay clock (`feed_replay.py:80`) and the gateway's odd-seq filter (`gateway.py:87`).

The v1 trigger is frozen (D-033), but the only thing that holds it frozen is the tests, and today they would not notice the trigger being changed.

**T2 (high, read): the tests check copies of the glue code, not the engine.** No test imports `engine_main`, `gateway`, `feed_replay`, `feed_sim`, `ledger` restart behaviour, or `run_apex`. `test_reconnect_jump_cannot_fire` (`test_core.py:250-254`) re-types `engine_main.py:231-243` by hand: guard, then `domino.update(learn_scales=...)`, then setting `episode["gap"]`. The mutation that removes those lines from the engine survives. `Engine.step` has no test at all, so neither do the day roll (`engine_main.py:187-193`), `end_day` (`:158`), restart mid-position (`start_day` → `load_books`, `:133`), or the shutdown learn (`:717`).

**T3 (high, verified by probe P1): learning runs on non-trading days, and a weekend evening promotes a challenger.** `Engine.step` calls `end_day()` at 15:31 every day with no `is_trading_day` check (`engine_main.py:192`). `record_day` stores empty books as 0 % days (`learning.py:158-177`). The live feed process keeps running over weekends (`feed_breeze.py:518`), so an engine left up from Friday learns on Saturday. Probe: a challenger reached streak 1 on Fri 13 Nov. Then `record_day`+`learn` for Sat 14 Nov (empty books) promoted it: `{'day': '2026-11-14', 'event': 'champion', 'from': 'm2.0_s0.5', 'to': 'm1.5_s0.4'}`. The "2 passing evenings" rule (PROMOTE_STREAK) was met with no new trading day. The zero-difference day also counts toward CHALLENGER_MIN_DAYS. No test covers this.

**T4 (medium, verified by probe and reading): tests that pass vacuously or for the wrong reason.**
- `test_gex_map_regime_walls_flip:185-187`: the flip-escape assert sits under `if both["regime"] == "DAMPEN"`. The real regime is `MIXED`, so it never runs.
- `test_exit_waits_for_fresh_quote...:312`: the "futures stale → no decision" assert also passes with the fut_age gate deleted (mutant survived), because the 8-second-old option quote defers the exit anyway.
- `test_learning_sprt:90`: "champion was replaced" is reached through the **KILL** path (log: champion retired 2026-11-05, status GO), not challenger promotion. It also uses legacy `pnl_pts` (no `ret_pct`), so it never tests the D-064 unit.
- `test_learning_sprt` does not call `_reset_learning()`. Its result depends on file order and on the shared `APEX_DATA` temp dir.

**T5 (medium, verified by probe P4): replay does not match live after a feed restart.** Live `BreezeFeed.__init__` zeroes all rows (`feed_breeze.py:235`). Replay's `install_registry` (`feed_replay.py:35-41`) does not. When a recorded day contains a second `reg` record (feed restart with a new band centre, so option ids get new strikes), the old occupant's `ttq` stays in each row. The monotonic guard (`feed_core.py:152`) then drops the new contract's quotes until its volume passes the old one. Probe: an option quote on a reused row returned `-1`, and ltp stayed at 25200. Replay is the owner's way of checking a rule (README), and this is where it diverges. The same guard also drops every next-day quote if a feed process survives midnight; that path is unverified live, because the Breeze session probably dies first.

**T6 (medium, read): replay and sim results depend on speed and CPU load.** The engine steps on wall-clock sleeps, `time.sleep(max(0.1/speed - elapsed, 0.005))` (`engine_main.py:708-709`). At `--speed 50` the 5 ms floor means one engine step per 0.25 virtual seconds, not 0.1. When the feed falls behind it rebases (`feed_sim.py:426`, `feed_replay.py:78`). The same file replayed at different speeds, or on a busy machine, gives different trades, so a golden-master replay test cannot be written today. Under load from other council runs, my isolated sim ran at about 25× instead of 50×. I did not finish a two-speed A/B run for lack of time; this is inferred from the code.

**T7 (medium, read and probe P6): restart mid-position fails silently.** `load_books` returns `None` on any parse error (`paper.py:441-450`). `start_day` then builds fresh books at ₹1,00,000 and flat, and the next `save_books` overwrites the evidence. Probe: a truncated JSON gave `None` with no log line. `Book.ctl` is not saved, so `premium_momentum` re-arms after a restart and can fire again on the same burst. `Ledger.seen` resets, so an episode still in progress is written twice to `candidates_*.jsonl`.

**T8 (low, read): `StateBlob.write` returns silently when the state exceeds 2 MB** (`table.py:165`). The dashboard would freeze with no error. Observed size at 09:25 sim was 19 KB, so this is a latent risk only.

**T9 (low, observed): test and sim isolation leaks.**
- `TICKS_DIR` and `TOKEN_CACHE_JSON` ignore `APEX_DATA` (`config.py:16,24`).
- The shared-memory names are fixed (`config.py:38-39`), and `Table.__init__` binds them as default arguments at import time.
- So `sim --record` always writes into the repository's `data/ticks`, and two sims on one machine share one table.

Disclosure: before I noticed this, my first un-isolated sim probe added data to `ApexOptions/data/ticks/2026-10-19_sim.jsonl.gz`. Another council member's process was writing to the same file at the same time. Treat that file as polluted and delete it. I left it in place because it is not only mine.

## Good things
- Several tests are scenario tests, not unit pokes. `test_reconnect_jump_cannot_fire` first shows the artefact really looks like a Triangle (`zmax>=2, smax>=0.5`) and only then shows the guard blocks it (`test_core.py:259-268`).
- Learning maths is checked against independent reference values: the t tail 0.0169, t_crit 3.364, SPRT lines 110.9/−62.3, Wilson bounds (`:355-359`, `:514`).
- `test_exit_never_prices_off_another_contract` and `test_exit_ignores_blackout_prints` encode real audit findings (R1, R2) as regression tests.
- `test_paper_only_no_order_calls` is a cheap structural guard for the paper-only rule.
- `apply_packet` tests a shared numeric token across the cash and F&O segments, plus out-of-order cumulative volume (`:28-48`). One parser for live, sim and replay (`feed_core.py`) is the right foundation for a replay test.
- `random_schedule` is seeded per day and per book, so it is reproducible (`paper.py:226`), and a test asserts that.
- The suite needs numpy only and runs in seconds.

## Ideas from GitHub
1. **HypothesisWorks/hypothesis**: https://github.com/HypothesisWorks/hypothesis, MPL-2.0 (LICENSE.txt read). Borrow `RuleBasedStateMachine` with `@rule`/`@invariant`/`@precondition` from the stateful-testing docs. Map it to a **test-only** `BookMachine`. Rules: open, tick(fut, opt quote, age, blackout), restart (`save_books`/`load_books`), clock jump. Invariants:
   - capital equals 1,00,000 plus the sum of `pnl_rs`;
   - at most one position;
   - no price exit while blackout is on;
   - an exit is priced only off the held key;
   - after a `pending` stop, a later exit is a STOP;
   - a round trip through restart is the identity.

   Add a separate `@given` property for `apply_packet`: any list of 21 or 23 strings, blanks or `None` never raises, and the seq counter stays even. Test dependency only (`pip install hypothesis`); engine code does not change.
2. **syrupy-project/syrupy**: https://github.com/syrupy-project/syrupy, MIT. Snapshot assertions (`assert x == snapshot`, `--snapshot-update`, and a test fails when its snapshot is missing). Map it to a **golden-replay tool**: commit one short recorded session (about 20 minutes, gzip) and replay it through `apply_packet` → `Engine.step`, driven by a stepped virtual clock (see idea 3). Snapshot every book's trades, ledger labels and advisor verdicts. Any change to frozen-trigger behaviour then shows up as a reviewed snapshot diff, which fits I-11 and D-033.
3. **nautechsystems/nautilus_trader**: https://github.com/nautechsystems/nautilus_trader, LGPL-3.0, so concept only and no code. Its README says "the same architecture, execution semantics, and time model operate across both" backtest and live, with a "deterministic event-driven runtime". Map it to a **replay mode where the engine owns the clock**: the feed applies all packets up to t, then the engine steps t+0.1 s in lock-step through a ctrl handshake, not wall-clock sleeps. This fixes T6, makes idea 2 possible, and turns replay into a real controlled experiment for variants.

## Top 3
1. **Mutation-driven safety tests (S, before Monday).** Add one small test per surviving mutant in the exit, entry and contract groups. Add a test for the `load_books` round trip, plus a loud warning when parsing fails. Add a test that `end_day` is skipped on non-trading days. Fix `end_day` with `if not config.is_trading_day(...)` (T3); it touches the learning loop, not the trigger. Re-run `/tmp/council/m08/mutate.py` until the 13 paper/learning mutants are killed.
2. **An Engine-level harness (M, before Monday for the day-roll subset).** Drive a real `Engine` from a fake `Table` and set `ctrl.now_ns`. Cover: 15:24 position → 15:25 TIME exit → 15:31 learn exactly once; a restart at 11:00 with an open position and pending stop; a renumbered registry; a date change at midnight. This kills the engine mutants and replaces the glue code copied into T2's tests.
3. **Deterministic lock-step replay plus a golden snapshot and Hypothesis machine (L, later).** Zero rows on every `reg` in replay (T5). Isolate `TICKS_DIR` and the shared-memory names per `APEX_DATA` (T9). Then build ideas 3, 2 and 1 in that order.
