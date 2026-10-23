# 07 — Council report: 20-member review of ApexOptions (baseline 85b65ed)

*Assembled 18 Oct 2026 from the 20 independent reports in `/mnt/user-data/outputs/council/member_01…20_*.md`. The assembly speaks for the council. Where members agreed, their findings are merged. Where they disagreed, or a claim looked doubtful, the assembly checked the code itself: it read the code and ran probes in `/tmp/council/assembly/` on a private copy. Nothing in the repository was changed except this file.*

**Owner's fixed rules.** Every recommendation below follows them:
- paper trading only;
- slippage, charges, sizing and trade frequency are out of scope;
- the v1 trigger's four numbers are frozen (D-033), and nothing changes intraday (I-11);
- new ideas enter only as logged advisors, pre-registered variants or controls, or observers.

Anything that would change frozen trigger behaviour is listed in §5 for the owner and is **not** in the before-Monday build.

**How severity was set.** Each finding gets the highest severity any member gave it. It is lowered only if the assembly's check showed the claim was narrower than stated, and the entry says so when that happened.

**How to read "Verified".**
- *A-read*: the assembly read the code and confirmed it.
- *A-probe*: the assembly ran its own probe.
- *M-probe (NN)*: member NN ran a probe the assembly did not repeat.
- *unverified*: nobody reproduced it; flagged as such.

---

## 1. Executive summary

The council is unanimous on the design. The *evidence architecture* is unusually good for a personal system:
- one frozen four-number trigger, with everything else running as logged advisors;
- pre-registered variants and controls, all trading the same ticks;
- gated books that are judged out of sample;
- a candidate ledger that records every opportunity, taken or not;
- a blackout guard against reconnect artefacts.

Member 20, the sceptic, called it "better than almost any retail system I have seen".

What the code does today falls short of that design in four ways:

1. **Data that must not be lost can be lost or corrupted.**
   - A feed crash followed by a restart makes the rest of the day's tick tape unreadable, and replay then hangs (C-01). Four members found this independently; the assembly reproduced it.
   - A live session stopped before 15:30 is never recorded for learning (C-03).
   - `days.jsonl` is rewritten in place, and one torn line stops learning for good (C-09).
   - An open trade's trailing-stop state is not saved, so it is lost on restart (C-11).

2. **Failures are silent.**
   - An exception in any one advisor skips every exit while an episode is live (C-07).
   - No process reads the heartbeats, and the dashboard cannot tell a frozen engine from a live one (C-08).
   - Dropped recorder packets are counted but never reported (C-21).

3. **The statistical gate is weaker than its documents claim.**
   - The SPRT assumes a per-trade standard deviation of 10 %. Three members independently showed by Monte Carlo that at a realistic 15–30 %, GO and KILL are close to coin flips (C-02).
   - Repeated evening looks inflate promotions 2–4× (C-25).
   - The `random_entry` null favours a champion that trades less (C-27).
   - The domino's BASKET-LED label reads 10–15 % on data with no lead at all. That is right at the D-015 kill line (C-04). Two members found this independently.

4. **Several advisors are mis-measured, which would corrupt their learning records from day one.**
   - The book advisor reads the wrong side of the book for every PE (C-12).
   - `gex_room` compares weekly strikes with the monthly futures price (C-14).
   - Force's ρ converges to 1, so BREAK-IMMINENT can never fire (C-13).
   - A half-failed chain poll is published as a valid chain (C-15).
   - The straddle's theta clock is 3.84× too fast on 0DTE (C-17).

   A separate group of issues touches the *inputs* of the frozen trigger: the floating-strike ATM IV fed to the IV cap, stock sigmas learned on pre-open zeros, two over-estimated index weights, depth packets refreshing quote age, and stops muted during the 20-s resume. These are measurement questions, not number changes, but they change trigger behaviour, so they go to the owner (§5).

**Monday 19 Oct** is the first live session and a 0DTE expiry, because Tue 20 Oct is a holiday. Members 02, 05 and 10 each confirmed the calendar handles this. The council's before-Monday plan (§6) is seven work packages with non-overlapping file sets. Together they:
- make the recording, the learning record and open-position state crash-safe;
- isolate advisor faults from exits and make staleness visible;
- fix the advisor measurement bugs listed above;
- harden the paper-only guarantee and the credential scanner;
- add observers so that the owner's §5 decisions can be made from Monday's data.

None of them touches `domino.py`, `guard.py` or the trigger branch of `paper.evaluate_entry`.

**Counts:** 106 distinct findings: 6 critical, 28 high, 44 medium, 28 low.

---

## 2. The consolidated teardown

### Disagreements and doubtful claims the assembly resolved

| Topic | Members | Assembly conclusion |
|---|---|---|
| Can a broken advisor stop the loop? | 15 and 16: observers are wrapped and cannot. 07: `advise()` is unguarded. | **07 is right.** `regime`, `watch`, `gex` and `ledger` are wrapped. `advise()` (`engine_main.py:284`) and `straddle.update`, `bank.update`, `lag.update`, `force.update` (`:250-262`) are not, and they all run before `run_books` (`:287`). → C-07 |
| Is the snapshot seqlock sound? | 16: cheap and correct. 06: returns torn rows. | **06 is right about the mechanism.** `table.py:125-138` re-reads back to back with no yield and returns the row even if it is still bad. 16 measured cost, not correctness. → C-40 |
| Do sim, replay and live share `chain_latest.json`? | 13: yes. | **Partly wrong.** `run_apex.data_dir_for` gives each mode its own `APEX_DATA`. The real risk is that a previous *live* session's file loads at start and becomes `oi0` (`levels.py:53-66`). → C-50 |
| Test count | 28 / 31 / "60+" | The assembly counts **28** `def test_` functions in `tests/test_core.py`. All pass on a copy. |
| Calendar time | 11: calendar T is negligible for IV drift. 10: calendar DTE picks the wrong delta band on Fridays. | Different questions, and both stand. → C-88 and owner item O-2 |
| Force line numbers | 01 cites `levels.py:419-442` | The file has 200 lines. The real locations are `levels.py:121-139` (levels, session high) and `:159-181` (ρ/π and verdicts). The logic of the finding is confirmed. |
| Severity of replay non-determinism | 04: critical. 08 and 16: medium. | Kept **critical** under the severity rule, because replay is how the owner checks rules. It has no effect on live data. → C-05 |
| BASKET-LED null rate | 12: 14.6 %. 20: 10 %. | Two different synthetic markets, same conclusion: the null rate sits at or near the 15 % kill line. → C-04 |
| Polluted sim tick file | 08 asked for `data/ticks/2026-10-19_sim.jsonl.gz` to be deleted | It is **no longer present**: `data/ticks/` is empty and git is clean. |

### CRITICAL

**C-01 · A feed crash and restart make the rest of the day's tick tape unreadable, and replay then hangs.**
- **Where:**
  - `feed_core.py:224`: the Recorder opens the day file with `gzip.open(…, "at")` in a daemon thread.
  - `feed_breeze.py:508-530`: `run()` has no `try/finally`.
  - `feed_breeze.py:570-578`: `main()` re-raises without `rec.stop()`.
  - `feed_replay.py:61`: catches only `(EOFError, OSError)`.
- **Failure:** the feed dies at 11:00 and the supervisor respawns it. The new process appends a second gzip member behind the untrailed one. Reading then fails with `zlib.error: invalid block type`, which is not an `OSError`, so replay dies. `feed_state` never reaches 7 and the engine waits for ever. Everything after 11:00 is lost, including the gap days D-063 exists to study.
- **Found by:** 04, 05, 15, 19.
- **Verified:** A-probe (`/tmp/council/assembly/gz.py`: 922 of 2,000 lines readable, then `zlib.error` escapes the replay clause; `issubclass(zlib.error, OSError)` is False), plus M-probes by 04, 05, 15 and 19.

**C-02 · The SPRT's assumed σ = 10 % makes GO and KILL close to coin flips, and every new champion gets a fresh shot at GO.**
- **Where:** `config.py:121` (`SPRT_SIGMA_PCT`), `learning.py:69-73` (lines), `:252-258` (status), `:286-313` (KILL re-arms the SPRT).
- **Failure (true mean 0):**
  - at sd 20 %, P(GO) is 0.23–0.24 (members 03, 20);
  - at sd 25 %, false GO is 25 % and KILL of a real +2.5 % edge is 57 % (member 14);
  - with serial champions after a KILL, P(GO) reaches 0.64 at sd 15 % and 0.89 at sd 20 % (member 20).

  The code's own remedy ("re-register if the sd persists", `:263-264`) only appears after 30 trades, and changing the test after looking at the data is itself a sequential-validity problem.
- **Found by:** 03, 14, 20.
- **Verified:** M-probe ×3 (independent Monte Carlo runs using the real `sprt_lines`), plus A-read.

**C-03 · A live session stopped before 15:30 is never recorded for learning.**
- **Where:** `engine_main.py:717-718` runs `end_day()` on shutdown only if `mode != "live"` or the time is ≥ 15:30. `end_day()` is the only caller of `learning.record_day`. `start_day` the next morning does not close the previous day (`:187-188`). `cmd_learn` (`run_apex.py:298`) does not record either.
- **Failure:** Ctrl+C at 15:27, after the 15:25 flatten, or a sleep or crash at 15:29. The day's trades stay in `paper/<day>.json` but never reach `days.jsonl`. The missing days are not random, which biases the SPRT, the challengers and the advisor screens.
- **Found by:** 19.
- **Verified:** A-read of the full path.

**C-04 · The episode classifier calls 10–15 % of episodes BASKET-LED when no stock leads, and it cannot see futures leadership.**
- **Where:** `domino.py:183-198`. The earliest of 14 noisy stock crossings races one futures clock. `ft is None` → BASKET-LED. The ±2 s CO-FIRST band swallows a real 1-s futures lead.
- **Failure:** member 12's null gave 14.6 % BASKET-LED, and FUTURES-LED stayed at 0 % even when futures truly led by 1 s. Member 20's null gave 10 %. The D-015 study's kill line is "basket-led < 15 %", so the thesis can pass or fail on noise.
- **Found by:** 12, 20.
- **Verified:** M-probe ×2 (independent synthetic markets driving the real `Domino`), plus A-read.

**C-05 · Multi-process replay is not deterministic: two replays of the same file give different trades.**
- **Where:** `engine_main.py:709`, `time.sleep(max(0.1/speed − elapsed, 0.005))`. The engine samples whatever the feed has written by then, so the effective step depends on speed and CPU load. `Flow._rb/_rs` (`flow.py:66-67, 103-106`) is a ring of 100 *samples* called "10 s".
- **Failure:** member 04's two replays at speed 40 matched on 0 of 17 books; for example futures_only had 85 trades/+705 pts in one and 81/+754 in the other. Member 16 showed that at speed ≥ 10 the engine cannot sample at 10 Hz virtual. A rule change judged on replay is judged partly on scheduling noise.
- **Found by:** 04, 08, 16.
- **Verified:** M-probe (04: R1 vs R2; 16: 0.1 s vs 0.2 s cadence runs), plus A-read.

**C-06 · The test suite kills 1 of 27 safety-critical mutants, so nothing would catch a change to the frozen trigger.**
- **Where:** `tests/test_core.py`. The suite stays green with any of these removed:
  - the fut-stale gate, THESIS-VOID, the 0DTE 15:00 flatten, the BOOK exit;
  - once-per-episode, LATE, the IV cap, synchrony, the entry window;
  - the 0DTE delta band and the quote-age filter;
  - `fired_episodes` restore;
  - the seqlock re-read;
  - LODO and idempotence;
  - every `engine_main` wiring line.
- **Failure:** a future edit silently changes v1, and CI stays green.
- **Found by:** 08 (07 and 08 also note the orchestrator has no tests, see C-31).
- **Verified:** M-probe (08's mutation run). A-read confirms that no test imports `engine_main`.

### HIGH

**C-07 · One failing advisor or observer skips every exit while an episode is live, and the heartbeat still says all is well.**
- **Where:** `engine_main.py:284` (`advise()`) and `:250-262` (`straddle/bank/lag/force.update`) are unguarded and run before `run_books` (`:287`). The catch-all at `:701-703` sleeps 0.5 s and loops. `engine_hb_ns` is written even after an exception (`:705`).
- **Failure:** member 07's probe made `advise()` raise. 312 of 685 steps skipped all exits, and a position stayed open while futures moved 99 pts against it.
- **Found by:** 07 (15 and 16 assumed the opposite).
- **Verified:** M-probe (07), plus A-read.

**C-08 · No process detects a stalled engine or gateway, and the dashboard looks live when it is frozen.**
- **Where:**
  - `engine_hb_ns`, `feed_hb_ns` and `gateway_hb_ns` are written (`engine_main.py:705`, `feed_breeze.py:518`, `gateway.py:101`) but nothing reads them.
  - `supervise()` only polls for process exit (`run_apex.py:83-101`).
  - `app.js:46,74` reconnects only on close; the health dot reflects tick age only.
  - `StateBlob.write` silently drops a state over 2 MB (`table.py:165-166`).
- **Failure:** member 09 sent SIGSTOP to the engine. The dot stayed green "live", with the stop line and P&L frozen.
- **Found by:** 06, 07, 08, 09, 15.
- **Verified:** M-probe (09), plus A-read and grep.

**C-09 · `days.jsonl` is rewritten in place, the shutdown deadline can kill that write, and one torn line stops learning for good.**
- **Where:**
  - `learning.py:175` rewrites the whole file with `open(DAYS, "w")`; there is no tmp-and-replace.
  - `learning.py:163-164` and `:184-187` have no decode tolerance.
  - `run_apex.py:105-117` gives feed and engine one shared 12-s deadline, then `terminate()`.
- **Failure:** a kill or power cut mid-write truncates the multi-day record. A torn line makes both `record_day` and `learn` raise. `_learned` is already set, so nothing retries, and learning stops silently on every later evening.
- **Found by:** 06, 19.
- **Verified:** M-probe (19, torn line), plus A-read.

**C-10 · Learning runs on non-trading days, and an idle weekend evening can promote a challenger.**
- **Where:** `engine_main.py:192-193` calls `end_day()` at 15:31 every calendar day. `record_day` stores empty books as 0 % days (`learning.py:158-177`). `learn()`'s `first_look` moves streaks once per date.
- **Failure:** member 08's probe left the engine up from Friday. Saturday's empty day completed `PROMOTE_STREAK` and promoted `m1.5_s0.4` with no new trading data.
- **Found by:** 08.
- **Verified:** M-probe (08), plus A-read.

**C-11 · An open position's exit state is not saved, so a restart reverts an armed trail to the initial stop and forgets a committed exit.**
- **Where:** `check_exit` mutates `best`, `trail`, `peak_pts`, `pending` and `last` every step (`paper.py:351-366, 400`). `run_books` saves only on entry or exit (`engine_main.py:585-586`). The supervisor says "books are on disk" (`run_apex.py:87`).
- **Failure:** member 19's probe: the trail arms at +40, the engine restarts, and the reloaded book has `trail=False`. The live book would have exited at 25,025; the restarted one holds.
- **Found by:** 06, 19.
- **Verified:** M-probe (19), plus A-read.

**C-12 · The book advisor and the BOOK exit read the wrong side of the book for every PE.**
- **Where:** `engine_main.py:301` passes `d = -1` for PE to `Flow.side`, but `side` takes the *contract's own* price direction (`flow.py:175-182`). We only buy, so the opposing side is always the asks.
- **Failure:** a PE whose asks are refilling is reported HOLDING (no veto). A PE whose bids are stacking is vetoed. The held-PE BOOK exit fires on good news. That corrupts half the book advisor's record and the PE trades of `m2.0_s0.5_bookexit`. `coherence()`/`run_score` use the sign correctly.
- **Found by:** 01.
- **Verified:** M-probe (01), plus A-read (`coherence` uses `+1` for a PE in a down move, which confirms the convention).

**C-13 · Force: ρ converges to 1 as cumulative volume grows, so BREAK-IMMINENT can never happen.**
- **Where:** `levels.py:159-161` (`resid = S − (S0 − C)`, `ρ = resid/C`) and `:177` (BREAK-IMMINENT needs ρ < 0.5). S is a bounded 5-level window, C is unbounded, so ρ → 1 + (S − S0)/C → 1.
- **Failure:** member 01's probe drained the opposing side to 25 %, and ρ rose from 0.41 to 0.87 with the verdict going back to TESTING. On a static book ρ stays exactly 1.0, so the `force` veto depends only on A fading.
- **Found by:** 01.
- **Verified:** M-probe (01), plus A-read and algebra.

**C-14 · `gex_room` measures weekly gamma walls against the monthly futures price.**
- **Where:** `engine_main.py:449` passes `ctx["fut"]`, which is `NIFTY|FUT` = `self.mexp`, the monthly contract (`feed_breeze.py:343`). The map is built at the w0 forward (`self.fwd`). `gex.py:115-130` measures `wall − fut`.
- **Failure:** the basis (tens of points; 40–120 per member 13) exceeds the 20 / 30-pt thresholds. "Only 8 pts ahead" can really be 88. The test passes `F` as `fut`, so it misses this.
- **Found by:** 13.
- **Verified:** M-probe (13), plus A-read. `Force.levels` gets the mapping right.

**C-15 · A half-failed chain poll is published as a valid chain.**
- **Where:** `feed_breeze.py:482-506`. If the put leg returns no `Success` rows, `out` still holds the calls and is written. `chain_version` is bumped and the chain is recorded.
- **Failure:** a calls-only chain gives gamma balance +1, regime DAMPEN, `gex_room` vetoes everything for at least 90 s, PCR 0 and no put walls. The bad snapshot also enters replays.
- **Found by:** 13.
- **Verified:** M-probe (13), plus A-read.

**C-16 · ATM IV is a floating-strike snapshot, so it saw-tooths at strike rolls and rises mechanically in sell-offs. It feeds the frozen IV cap.**
- **Where:** `engine_main.py:358-363` takes the strike nearest F. That value feeds `iv_rise_since_onset` (`:269`), then `IV_RISE_CAP` (`paper.py:181-183`), then `iv_late`.
- **Failure:** on a fixed smile, a 2-pt move of F across a strike midpoint jumps ATM IV by 0.57 pts. Under sticky-strike, a 60-pt fall raises it by 1.4–2.2 pts, enough to reject a clean down-impulse as "LATE: ATM IV". CE entries are not affected this way.
- **Owner decision:** O-1.
- **Found by:** 11.
- **Verified:** M-probe (11), plus A-read.

**C-17 · The straddle's expected decay uses two clocks and runs 3.84× too fast. On 0DTE this lowers the effective spike threshold through the afternoon.**
- **Where:** `greeks.py:91` computes `theta_min = theta_year/365/375` on a calendar-time T (`:43-47`). `straddle_watch.py:126-128` and `:185-186` add it up per wall minute.
- **Failure:** an unmoving 0DTE straddle at 14:45 shows a +5.1-pt "excess", above `SPIKE_MIN_PTS` = 4. This affects `straddle_spike`, `gamma_leg`, the premium state and `room` (in a small way).
- **Owner decision:** O-3.
- **Found by:** 02.
- **Verified:** M-probe (02), plus A-read (365×1440 / (365×375) = 3.84).

**C-18 · Quote freshness is message age, not trade age: depth packets refresh `recv_ns`, and frozen depth reads HOLDING.**
- **Where:**
  - `feed_core.py:192-193`: depth packets call `table.end(i, recv_ns)`, which sets `recv_ns` (`table.py:117-119`).
  - That age drives the guard's `fut_age` (`engine_main.py:214-216`), option `age` (`:380`) and `choose_contract`'s `age < 15` (`paper.py:125`).
  - `market.py:48` treats any `depth_ns > 0` as live depth.
- **Failure:**
  - If the quote stream dies while depth keeps flowing, the guard sees no gap.
  - Paper entries can fill at a pre-impulse LTP. This bias favours impulse-timed books over `random_entry`.
  - Frozen depth gives r10 = 0 and reads HOLDING.
- **Owner decision:** O-7 (guard and selection semantics).
- **Found by:** 01, 20.
- **Verified:** M-probe (01, 20), plus A-read.

**C-19 · An empty or failed security master still gives "websocket LIVE" with zero instruments.**
- **Where:** `feed_breeze.py:337-380`. `build()` never checks that `NIFTY|FUT` or the options resolved. `subscribe_all()` returns True when there is nothing to subscribe (`:414-429`).
- **Failure:** the SDK swallows a master download error. Every token is `'4.1!False'`, 0 instruments resolve, the state is LIVE, and the 30-s watchdog reconnects for ever.
- **Found by:** 05.
- **Verified:** M-probe (05, against the 1.0.69 sdist), plus A-read of the Apex side.

**C-20 · Replaying the same day twice stacks the second run on the first, and replays share learning state.**
- **Where:** `engine_main.py:133` reloads `data/replay/paper/<day>.json`. The ledger, episode and straddle files append (`ledger.py:122`, `extras.py:192`, `straddle_watch.py:299`). `data/replay/learning/state.json` is shared across replay days.
- **Failure:** futures_only went from 9 to 19 trades and from ₹2.43 L to ₹6.05 L capital. Diagnostics double-count.
- **Found by:** 04, 15.
- **Verified:** M-probe (04 R3), plus A-read.

**C-21 · Recorder drops are counted but never surfaced.**
- **Where:** `feed_core.py:208, 221`: `self.dropped` is never read, logged or written.
- **Failure:** replay silently differs from live after a queue overflow.
- **Found by:** 04, 15, 19.
- **Verified:** A-read and grep.

**C-22 · The 20-s resume window mutes stops on data that is fresh again, including the first 20 s after every restart.**
- **Where:**
  - `guard.py:103` keeps `on` until 20 s of continuous fresh quotes; the guard starts with `on=True` (`:34`).
  - `paper.py:389` and `:395` drop price exits while `blackout`.
  - `paper.py:357-359` freezes `best`.
- **Failure:** member 18's probe: a 4-s stall, then a fresh fall through the stop. The exit came 12 s late, at −12.1 % against −4.8 % at the stop level (2.5× 1R).
- **Owner decision:** O-4. This behaviour is D-076 as decided; the guard's own docstring says "exits wait for fresh quotes".
- **Found by:** 18.
- **Verified:** M-probe (18), plus A-read.

**C-23 · Every exit is blind to the option's own P&L, and the futures "break-even" trail is not break-even in premium.**
- **Where:** `paper.py:360-364`.
- **Failure:** member 18's model, entering with IV +1.5 and exiting at the same futures level with IV back:
  - the ≥3-DTE "break-even" trail loses −10 % against −4.3 % for an immediate stop;
  - a 12-pt stop is −3 % on one contract and −13 % on another (about −36 % at `MIN_PREMIUM`);
  - a flat 3-h hold bleeds 11–16 %.
- **Status:** a design limitation. It enters only as exit shadows (later).
- **Found by:** 18.
- **Verified:** M-probe (18, model-based), plus A-read.

**C-24 · The SPRT scores the arithmetic mean of per-trade returns, while all-in compounding grows at the log mean.**
- **Where:** `learning.py:252-258`, against the log-growth `_day_ret` (`:61-66`).
- **Failure:** at μ = +2.5 % and sd 30 %, E[ln(1+r)] = −2.78 %/trade. The SPRT can say GO on a shrinking account, and the scoreboard and the challenger test judge different quantities.
- **Found by:** 03.
- **Verified:** M-probe (03), plus A-read.

**C-25 · Checking challengers and gates every evening inflates false promotions 2–4×.**
- **Where:** `learning.py:270-283` and `:352-374`. Bonferroni is applied per look; looks run every evening from day 10 with no end, and consecutive looks share n−1 days.
- **Failure:** FWER is 0.11 at 30 days and 0.23 at 120 (member 03). False promotions are 15–18 % of runs at 80 sessions, and 30 % when the true mean is −3 % (member 14).
- **Found by:** 03, 14.
- **Verified:** M-probe ×2, plus A-read.

**C-26 · GO ignores the design's own bar and is not latched.**
- **Where:** `learning.py:255` uses `tot >= go` only. §9.2/§6.1's conditions (LODO, best-day-dropped, ≤ 40 % from one day, ≥ 15 sessions, ≥ 2 expiries, beating the null) are not wired in.
- **Failure:** 8 trades of +16 % on one trend day print GO (`sprt_lines(8)` gives 120.9). The label can flicker.
- **Found by:** 20.
- **Verified:** A-read plus arithmetic.

**C-27 · The `random_entry` null is unfair: daily log growth confounds edge with trade count.**
- **Where:** `learning.py:61-66, 220-232` and `config.py:114` (Poisson 6/day, never rate-matched). There is one seed per day (`paper.py:229`).
- **Failure:** with no edge, the champion "beats random" in 28 % of runs (nominal 1.7 %). With −3 %/trade it does so in 83 %, so a losing trigger passes the null.
- **Found by:** 14.
- **Verified:** M-probe (14), plus A-read.

**C-28 · LagMeter measures the futures' rise time, not a domino lag.**
- **Where:** `extras.py:117-125` and `domino.py:184`. Pre-onset stock crossings are stamped at onset, and episodes where futures never reach z = 2 are dropped.
- **Failure:** with futures truly leading by 1 s, the median lag reads 0.0 s (n = 127). D-057's lag cannot reject anything.
- **Found by:** 12.
- **Verified:** M-probe (12).

**C-29 · The basket gap is dominated by timestamp skew, and coverage extrapolation turns sector moves into fake gaps.**
- **Where:** `domino.py:127` (`Mb = Σmi·100/wtot`) and the `gap3`/`gap5` variants (`config.py:95-96`, `paper.py:169-173`).
- **Failure:**
  - With a 1-s skew, gap·d ≥ 3 pts holds 23 % of the time while z ≥ 1, so the variants buy pauses.
  - An 8-pt bank-only move gives a 5-pt "gap".
- **Found by:** 12.
- **Verified:** M-probe (12) for skew; arithmetic for coverage.

**C-30 · Stock sigmas and volume baselines learn on pre-open zeros; futures sigma does not.**
- **Where:** `domino.py:87-105`. The futures scale is gated `in_session`; the stock block is not. `guard.py:73-74` allows learning outside session hours.
- **Failure:** with the engine started at 09:00, median stock sigma at 09:25 is 0.19 against 0.47, and P(S ≥ 0.5) over 09:25–09:35 is 45.5 % against 21.2 %. Synchrony doubles exactly when entries open. `vol15_base` → 0 makes the activity filter pass.
- **Owner decision:** O-5 (trigger input).
- **Found by:** 12.
- **Verified:** M-probe (12), plus A-read.

**C-31 · The orchestrator has no tests, and the tests that exist re-type its glue by hand.**
- **Where:** `tests/test_core.py` never imports `engine_main`. `test_reconnect_jump_cannot_fire` (`:250-254`) re-implements `engine_main.py:231-243`. The day roll, `end_day`, restart mid-position and the shutdown learn are untested.
- **Found by:** 07, 08.
- **Verified:** A-read and grep.

**C-32 · The preflight credential scanner misses the JSON the project itself writes.**
- **Where:** `run_apex.py:162` (`KEYLIKE` needs `api_key\s*[=:]`, but JSON has a closing quote before the colon) and `:164` (`PLACEHOLDER` is applied to the whole match).
- **Failure:** a copy of `secrets/breeze.json` in the root passes "[PASS] no credential-shaped strings". 7 of 8 realistic leak shapes are missed.
- **Found by:** 17.
- **Verified:** A-probe (`cmd_session`-style JSON: not caught), plus M-probe (17).

**C-33 · The no-order guard names a method that does not exist, misses five that do, and nothing enforces paper-only at runtime.**
- **Where:** `tests/test_core.py:414`. There is no `place_gtt_order` in SDK 1.0.69; `gtt_*_place/modify/cancel_order`, `aggressive_limit_order_placement`, `set_funds` and `add_margin` are missed. The check is lexical only, and `run_apex.py` is not scanned. `config.PAPER_ONLY` is read only by `validate()`.
- **Found by:** 17.
- **Verified:** M-probe (17, sdist grep), plus A-read of the test regex.

**C-34 · The champion's reason path and the event tape are never saved.**
- **Where:** `last_reason` is overwritten every 100 ms (`engine_main.py:567-568`) and sampled only at the m* cross and at onset. `self.events` (`deque(120)`) is never written to disk.
- **Failure:** a miss is classed "basket too thin" when lateness was the real blocker. A restart wipes the event tape.
- **Found by:** 15.
- **Verified:** A-read and grep.

### MEDIUM

**C-35 · A refill after an earlier drain is classed DRAIN-SLOW, not REFILLING.** `flow.py:165-166`: the DSLOW mask is applied after REFILL with no `r10 ≤ 0.15` guard. "Defenders came back" goes unseen, and `run_score` scores it as a drain. *Found by* 01. *Verified:* M-probe (01) and A-read.

**C-36 · Hero contracts lose depth when Nifty drifts, and re-centring never adds it back.** `feed_core.py:63-68`: `Registry.add` on an existing key flips `depth=True` but never stores `depth_token`. Depth covers ±3 of the *build* centre (`feed_breeze.py:387`) while the heroes are ±2 of the *current* ATM. The book exit is also absent for contracts outside the hero band (`engine_main.py:297`; 18 F5). *Found by* 05, 18. *Verified:* M-probe (05) and A-read.

**C-37 · Packets are applied in arbitrary order; depth and index quotes have no ordering guard, and the recording order is not the application order.** `feed_core.py:180-195` (no guard on depth) and `feed_breeze.py:404-407` (`rec.put` after the lock is released). *Found by* 04, 05. *Verified:* A-read; not reproduced.

**C-38 · Login can hang with no timeout and no log line.** The SDK's `urlopen(SECURITY_MASTER_URL)` is not covered by the `requests` patch (`feed_breeze.py:298-303`). *Found by* 05. *Verified:* M-read of the sdist.

**C-39 · A feed restart re-numbers rows, and the engine discards its warm state (another 10-minute warm-up).** `feed_breeze.py:235` zeroes the table; `engine_main.py:101-108` resets on `moved`. *Found by* 05. *Verified:* A-read.

**C-40 · `snapshot()` returns torn rows, and the gateway does the same.** `table.py:125-138`: the three re-reads run back to back and the row is returned even if still bad. `gateway.py:80-91` checks `seq` and then copies without re-checking. *Found by* 06. *Verified:* M-probe (06: 18 % torn under a hot writer; 0 after a yielding retry).

**C-41 · An exception between `begin()` and `end()` flips a row's seqlock parity for good.** The depth branch at `feed_core.py:182-193` calls `len(lv[k])` with no try/finally, and the exception also escapes into the SDK thread. *Found by* 06. *Verified:* M-probe (06) and A-read.

**C-42 · A restart throws away observer and control state.** `Book.ctl` is not persisted (`paper.py:41`), so `premium_momentum` re-arms. `Ledger.seen/open` (`ledger.py:45`) and the open `EpisodeLog` episodes are dropped. `Regime()` is rebuilt (`engine_main.py:151`, so VWAP restarts). `oi0` resets (`levels.py:65`). *Found by* 08, 11, 13, 19. *Verified:* A-read.

**C-43 · Corrupt state and books reset silently to defaults, and the next save overwrites the evidence.** `learning.load_state` (`:132-139`) and `paper.load_books` (`:441-450`) catch everything; there is no fsync. *Found by* 08, 19. *Verified:* M-probe (08) and A-read.

**C-44 · Advisor names live in three hand-kept lists, and every advisor is screened from the same global registration date.** `engine_main.py:405-453`, `learning.py:49-50`, `app.js:147`. A new advisor that is not added to `ADVISORS` is never screened. Trades from before an advisor existed count as "not vetoed". *Found by* 07. *Verified:* M-probe (07) and A-read.

**C-45 · `config.validate()` accepts unknown or typo'd variant keys and conflicting flags.** `config.py:270-304`. `{'exit_bok': True}` silently clones `m2.0_s0.5` and inflates the Bonferroni divisor. *Found by* 07. *Verified:* M-probe (07).

**C-46 · Some tests pass vacuously or for the wrong reason.**
- `test_gex_map_regime_walls_flip` has its assert guarded by `if DAMPEN`, and the regime is MIXED.
- In the exit-stale test, the option age defers the exit anyway.
- `test_learning_sprt` reaches its result via KILL, uses legacy units and no reset.
- The GEX test passes `F` as `fut`.

*Found by* 08, 13. *Verified:* M-probe (08) and A-read.

**C-47 · Replay does not zero rows on a second `reg` record, so the ttq guard drops the new contract's quotes.** `feed_replay.py:35-41`, against live `feed_breeze.py:235`. *Found by* 08. *Verified:* M-probe (08).

**C-48 · Feed outages are not in the recording, so replay rebuilds them differently.** `feed_replay.py:47` forces `feed_state = 6` for the whole replay, and `now_ns` only advances on records (`:80`). Sim recordings have no VIX. *Found by* 04. *Verified:* A-read.

**C-49 · No recording or record says which code, config or schema produced it.** There is no git hash, `VARIANTS` hash or learning state at the open. `report.md` is overwritten each evening. `cmd_learn --mode replay` learns the wall date (`run_apex.py:305`). There is no `schema` field, so code relies on `t.get("ret_pct")` fallbacks (`learning.py:55-60`). *Found by* 04, 15, 19. *Verified:* A-read.

**C-50 · Stale, foreign or expired chain files are trusted, and chain age is never checked.** `levels.py:53-66` loads whatever is on disk at start (`chain_version` 0 ≠ −1) and makes it `oi0`. The expiry is never compared with `w0`, and `chain_age` is display-only. *Found by* 13 (the cross-mode part was corrected by the assembly). *Verified:* A-read.

**C-51 · The two "wall" definitions disagree, and the stricter one usually finds nothing.** `Pressure._walls` needs 2× the ±3 neighbours (`levels.py:82-93`); `GexMap` needs 1.5× its side. `room` treats "no wall" as "no veto". *Found by* 13. *Verified:* M-probe (13).

**C-52 · The synthetic forward accepts stale legs, uses a 150-pt sanity band, and falls back to spot, not the futures-implied forward.** `greeks.py:100-113` and `engine_main.py:332-345`. On 0DTE a 20-pt error moves the contract out of the 0.65–0.85 band. *Found by* 02. *Verified:* M-probe (02).

**C-53 · D-020's IV band and sticky-IV attribution are not built, and exits record no Greeks.** grep finds no `vanna`, `charm` or attribution code. `close_trade` (`paper.py:416-430`) stores no `iv_out`, `delta_out` or exit DTE. *Found by* 02, 18. *Verified:* A-read and grep.

**C-54 · Regime percentiles ignore time of day, so COMPRESSION is over-labelled in mid-morning.** `regime.py:49, 116`. On a U-shaped volatility profile, COMPRESSION covers 38 % of 10:15–11:15, against 14 % on a flat one. *Found by* 11. *Verified:* M-probe (11).

**C-55 · EXHAUSTION fires heavily on trend days.** `regime.py:150` (`ext_pct ≥ 90 and er1 < 0.25`). Indicative only (single seed). *Found by* 11. *Verified:* M-probe (11).

**C-56 · BankLead ignores the blackout and the session hours.** `extras.py:85-96`. Pre-open zeros shrink its sigma, and a reconnect jump inflates it for about 20 minutes. *Found by* 12. *Verified:* A-read.

**C-57 · Synchrony may be nearly tautological with the impulse, and the basket is cash, not stock futures.** The tracked weight is 61.6 % (`universe.py:57`), so P(S ≥ 0.5 | z ≥ 2) may be near 1. `sfut` rows are subscribed but unused (`domino.py:56`). *Found by* 12, 20. *Verified:* A-read; the magnitude is unverified (the ledger can measure it).

**C-58 · Two "estimate" Nifty weights (TCS 2.70, ITC 2.56) cannot be right.** `universe.py:26-27`: both exceed the factsheet's #10 weight (M&M 2.52) yet appear nowhere in its top 10. They feed synchrony S and the gap variants. **Owner decision:** O-6. *Found by* 10 (12 notes the estimates). *Verified:* M-read against the factsheet.

**C-59 · `EVENT_DAYS` is empty, and its one example date is a Saturday.** `config.py:146-148`. RBI decides on Fri 4 Dec 2026 and Fri 5 Feb 2027, so the `event` advisor can never be judged. *Found by* 10. *Verified:* M-read (RBI release).

**C-60 · There is no 2027 holiday list, and preflight only checks the current year.** `run_apex.py:188`. Tue 26 Jan 2027 (Republic Day) is both the weekly and the monthly expiry. *Found by* 10. *Verified:* A-read.

**C-61 · The post-KILL replacement picks the maximum raw sum over all history (winner's curse).** `learning.py:289-298`. It favours the variants that trade most. *Found by* 03, 14, 20. *Verified:* A-read.

**C-62 · The control comparison reuses the data that selected the champion, and Bonferroni /3 only costs power.** `learning.py:316-327` compares "since registration" rather than since `champion_since`. *Found by* 03. *Verified:* A-read.

**C-63 · Two controls stop matching the champion once it changes.** `futures_only` is hard-wired to m* = 2.0, and `premium_momentum` tests a different hypothesis (`config.py:110-112`). *Found by* 14. *Verified:* A-read.

**C-64 · The advisor pipeline lets noise in cheaply and judges it unevenly.**
- The screen has no variance term: P(≥ 1 false candidate) is 0.55–0.83.
- One candidate is tested at α = 0.05.
- Demotion happens on a point estimate.
- RAW is pooled across champions (`learning.py:330`; `engine_main.py:141`).

*Found by* 03, 14, 20 (07 on the start date). *Verified:* M-probe (03) and A-read.

**C-65 · The candidate ledger records nothing when the champion is `straddle_spike`.** `ledger.py:53` (`not p.get("spike")…`). *Found by* 14. *Verified:* A-read.

**C-66 · Power is low; no rule-level conclusion is trustworthy for many months.** Champion vs random needs about 140 days at σ 10 % and about 880 at σ 25 % (member 14). Challenger power at 0.5 sd with 20 days is 0.27 (member 03). The documents should say so. *Found by* 03, 14. *Verified:* M-probe ×2 and closed form.

**C-67 · Spike and momentum books exit on a different thesis than they entered on.** Their exits are the futures stop/trail and heavyweight THESIS-VOID (`paper.py:366-371`), not the spike-end rule (D-060). *Found by* 18. *Verified:* A-read; not observed in data.

**C-68 · The gold "fire" verdict is recomputed in the browser and ignores the engine's blocks.** `app.js:114-123, 149-157`: you can get a gold glow over "Already traded this move". *Found by* 09. *Verified:* M-read.

**C-69 · The seller-state signal is clipped at 1366×768, and the position panel falls below the fold.** `style.css:96` (`.leg .meta {white-space:nowrap; overflow:hidden}`). *Found by* 09. *Verified:* M-probe (screenshot).

**C-70 · Explanations are destroyed every 250–350 ms by `innerHTML` rebuilds.** `app.js:164-168` and similar. Advisor `why` exists only in a flickering `title=`. *Found by* 09. *Verified:* M-probe (DOM churn).

**C-71 · Colour semantics are inconsistent and sometimes inverted.**
- OI map: puts are green (`app.js:321-322`).
- Force line: green regardless of `force.dir` (`app.js:345`).
- The flash class becomes permanent (`app.js:63-68`).

*Found by* 09. *Verified:* M-probe (screenshot).

**C-72 · There is a per-tick forced reflow, and the main thread is overloaded in sim.** `app.js:66` (`void el.offsetWidth`). `onTick` took 30–41 % of main-thread time at 30× sim; probably low at live rates. *Found by* 09. *Verified:* M-probe.

**C-73 · The gateway accepts any Origin and any Host, including on websockets, with no connection cap.** `gateway.py:73-123` has no TrustedHost or Origin check. Any open web page can read the position and books from `ws://127.0.0.1:8780`. *Found by* 17. *Verified:* M-probe (17, TestClient).

**C-74 · Credentials are stored in plaintext inside the project tree, and the SDK's DEBUG log lives in it too.** `run_apex.py:154-156` writes `secrets/breeze.json`; the SDK writes `logs/apiLogs.log` relative to CWD. *Found by* 17. *Verified:* A-read; the Windows ACL part is unverified.

**C-75 · The scanner's directory skips are substring tests on the absolute path.** `run_apex.py:194`: `.git` also skips `.github`, and a checkout under `…\data…` skips the whole scan. The `.gitignore` check greps only for "secrets". *Found by* 17. *Verified:* M-probe (17) and A-read.

**C-76 · Implied vol takes about half the engine's CPU, and most of that is wasted.** `greeks.py:61-74`: two calls, 40 iterations, both legs priced every time. A prototype was 7× faster with ≤ 0.0002 vol-pt difference. *Found by* 16. *Verified:* M-probe (cProfile).

**C-77 · Engine log timestamps use the wall clock while records use market time.** `engine_main.py:42`. *Found by* 15. *Verified:* A-read.

**C-78 · The restart policies are crude.**
- The engine respawns with no backoff (`run_apex.py:85-88`).
- The feed `restarts` counter never resets.
- In sim and replay a feed crash leaves the engine waiting for ever (`engine_main.py:706`).

*Found by* 06. *Verified:* A-read.

### LOW

- **C-79 · The lead score never takes the book's weight below half.** `flow.py:196`: a contrarian book still gets 50 % weight. *(01; A-read)*
- **C-80 · Force locks onto the old session high or low during a breakout.** `levels.py:121-139`. *(01; A-read)*
- **C-81 · `room` is measured from cash spot and judged against weekly strikes.** After 13:00 on 0DTE, `need` uses a w1 delta (`engine_main.py:410`, `levels.py:95`). *(13; A-read)*
- **C-82 · D-062's DAMPEN exception text disagrees with `gex.py:124-125`.** The code's version is coherent; update the log. *(13; A-read)*
- **C-83 · The 0DTE 14:45 "no entry" branch does the same as the 13:00 branch.** `paper.py:114-117`. **Owner decision:** O-11. *(02; A-read)*
- **C-84 · The `choose_contract` fallback has no upper delta bound.** It can jump about 100 pts ITM on 0DTE (`paper.py:129-131`). **Owner decision:** O-12. *(02; A-read)*
- **C-85 · An expired expiry is still priced, with T floored at 60 s.** `greeks.py:46`. *(02; M-probe)*
- **C-86 · `iv_late` uses one raw sample at each end, and the IV rules mix relative and absolute units.** `engine_main.py:405-407, 538-545`. *(11; A-read)*
- **C-87 · VIX is polled every 60 s but used only for display.** `feed_breeze.py:463`. *(11; A-read)*
- **C-88 · Days-to-expiry is counted in calendar days.** On Fridays before a Monday expiry, dte = 3 selects the ≥3-DTE band (`paper.py:120-121`; `greeks.py:43`). **Owner decision:** O-2. *(10; A-read)*
- **C-89 · The `SUPPRESS_UNTIL` comment predates the F&O futures pre-open (since 8 Dec 2025).** `config.py:56`. Informational; Breeze behaviour unverified. *(10)*
- **C-90 · Lot size and freeze quantity are hard-coded constants that NSE now revises often.** `config.py:47`. No effect today. *(10; A-read)*
- **C-91 · `monthly_expiry_candidates` probes a dead "last Thursday" rule.** It can sit before the primary date (`config.py:235-245`). *(10; M-probe)*
- **C-92 · Nothing warns when `live` is started on a holiday.** *(10; A-read)*
- **C-93 · The 0DTE delta ≥ 0.9 exemption trusts a Greek from a stale quote.** `paper.py:381-384`. **Owner decision:** O-13. *(18; A-read)*
- **C-94 · LODO is redundant inside the paired t-test.** Zero failures in 6,430 passing samples (`learning.py:212-217`). *(03; M-probe)*
- **C-95 · Minor statistics.** The `_day_ret` floor, `t_crit` capped at 50 (`learning.py:120-128`), and the 200-trade limit that is almost never reached. *(03; A-read)*
- **C-96 · Diagnostics are many uncorrected splits of clustered data, with no stated null.** `diagnostics.py:23-31, 65-111`. *(14, 20; A-read)*
- **C-97 · "z" divides by a mean-absolute EWMA, not the sd.** z = 2 is about 1.6σ under normality; document it. *(12; A-read)*
- **C-98 · Isolation leaks.** `TICKS_DIR` and the shared-memory names ignore `APEX_DATA` (`config.py:17, 38-39`). On Linux a second instance can unlink a live segment (`table.py:69-76`). *(04, 06, 08; A-read)*
- **C-99 · Saves without Windows retry or fsync.** `save_books` (`paper.py:433-438`) and `save_state` (`learning.py:146-150`) use plain `os.replace`. `RestLedger` and the token cache use non-atomic writes (`feed_breeze.py:206, 223, 251, 257`). *(06, 17, 19; A-read)*
- **C-100 · Nothing limits disk growth or rotates logs, and the analysis files are thinner than the records.** There is no 90-day tick prune (OQ-18). `engine.log` gets a traceback every 0.5 s on a recurring fault. The trades CSV drops episode, delta, IV and the advisors. *(15, 19; A-read and grep)*
- **C-101 · Code structure.** `ctx` is an untyped bag of about 20 keys, attributes are created lazily, and code is duplicated (three gate loops, three key builders, four error throttles). *(07; A-read)*
- **C-102 · Minor hot-path waste.** `Pressure.refresh` rebuilds every step, `publish` serialises twice, work runs over 512 rows when 121 are used, and `Market.ago` repeats (`levels.py:53-77`, `table.py:164, 208`, `market.py:61-69`). Live headroom is about 6 % of a core. *(16; M-probe)*
- **C-103 · Dashboard and gateway small items.** The gateway swallows exceptions (`gateway.py:103-106`), reconnects have no backoff, there are no `aria-live` regions, "together" means two things, and the OI labels overlap. *(09; M-probe and A-read)*
- **C-104 · Possible spurious reconnect at 09:15:00 (unverified), and a `HotStats` race outside the lock.** `feed_breeze.py:408, 520-525`. *(05)*
- **C-105 · The `StateBlob` header may not be written atomically.** Unverified: 0 invalid frames in a 3,067-frame probe (`table.py:162-182`). *(06)*
- **C-106 · `cmd_session` small items.** It prints the login URL with the key, reads the session token with echoing `input()`, never asks for a missing secret, and creates `secrets/` as an import side effect. *(17; A-read)*

---

## 3. Good things the council agrees on

1. **One frozen four-number trigger; everything else is advisory, with a "would-have" verdict on every trade.**
   - *Where:* `paper.py:135-189`, `engine_main.py:403-453`, D-033.
   - *Members:* 01, 12, 14, 20.
   - *Why it matters:* this is why C-12 to C-15 can be fixed without contaminating v1.
2. **Pre-registered variants and controls, all trading identical ticks, judged by paired tests.**
   - *Where:* `config.py:89-115`, `learning.py:220-232`, `engine_main.py:548-586`.
   - *Members:* 03, 07, 14, 20.
3. **Gated books that are judged out of sample** (`learning.py:364`, `d > since`).
   - *Members:* 03, 14, 20.
4. **The candidate ledger**, which labels every opportunity, taken or not, without reference to the decision.
   - *Where:* `ledger.py:45-135`. *Members:* 14, 15, 20.
   - **The counterfactual episode log** (`extras.py:136-201`) is the dataset that lets C-04, C-28 and C-29 be studied offline. *Member:* 12.
5. **The blackout, settling and taint guard, which is tested.**
   - *Where:* `guard.py` (D-063/072/075/077), and the scales frozen in gaps (`domino.py:87`).
   - *Tests:* `test_reconnect_jump_cannot_fire` shows the artefact really is one before showing it is blocked.
   - *Members:* 08, 11, 12, 16, 20.
6. **A log-growth day unit for all-in compounding, with an exact Student t computed without scipy.**
   - *Where:* `learning.py:61-66, 77-128`. *Members:* 03, 14, 20.
7. **One packet parser for live, sim and replay; a non-blocking hot path; the ttq monotonic guard.**
   - *Where:* `feed_core.py:140-195`, `Recorder.put` uses `put_nowait`. *Members:* 01, 04, 05, 08.
8. **The greeks are numerically sound.**
   - Black-76 on a per-expiry parity forward.
   - Vectorised bisection rather than Newton.
   - An explicit validity cut-off at intrinsic + 0.05, with deep-ITM handling.
   - IV, delta and gamma match independent references to 1e-5 and 1e-12.
   - *Where:* `greeks.py:43-113`. *Members:* 02, 11, 13.
9. **The expiry calendar is holiday-aware and keyed on the contract's own expiry**, so Monday 19 Oct is correctly 0DTE. The 2026 holidays, freeze quantity, lot size and weights carry dated sources.
   - *Where:* `config.py:167-232`, `paper.py:110, 379`, `universe.py`. *Members:* 02, 05, 10.
10. **Exits are matched by contract key, not row id; committed exits stay pending; TIME exits never wait; the trail ignores frozen prints.**
    - *Where:* `paper.py:343-348, 388-403`. *Members:* 06, 07, 18, 19.
11. **Atomic writes, with a Windows retry, where they exist** (books, state, registry, chain).
    - *Where:* `feed_core.py:41-49`, `paper.py:433-438`. *Members:* 06, 13, 19.
    - **Learning is idempotent per evening**, and a test covers it. *Members:* 06, 14, 19.
12. **The Breeze connection is engineered properly.**
    - `connect_error` is registered before connecting, and the real error text is kept.
    - `drop_stream` really tears the socket down.
    - The raw hook is installed before `watch()` binds.
    - Preflight resolves real tokens before the open.
    - *Where:* `feed_breeze.py:148-193`, `run_apex.py:233-300`. *Members:* 05, 10.
13. **Order counts are their own series, explained in order units; window totals are used, never per-level** (D-013).
    - *Where:* `flow.py:120-128`, `market.py:49-52`. *Member:* 01.
14. **Honest framing throughout.**
    - The GEX dealer-sign caveat is stated (`gex.py:12-21`).
    - The UI shows "paper · simulated market" and "changes only after the close".
    - The regime thresholds are pre-registered against a random-walk baseline (`regime.py` docstring).
    - *Members:* 09, 11, 13.
15. **Safety basics are right.**
    - No secret has ever been committed (`git log --all -p`).
    - Credentials are typed through `getpass`.
    - The gateway is loopback-only and read-only, with no POST route, and blocks path traversal.
    - *Members:* 17.

---

## 4. GitHub ideas

**The rule applied.** GPL, LGPL, AGPL, MPL, Commons-Clause and unlicensed repositories are **CONCEPT ONLY**: describe the idea, copy no code. "ADOPT NOW" means it is used in a before-Monday work package. Every one of those is a pattern ported by hand, with no new runtime dependency.

**How licences were checked.** The assembly confirmed a licence from a member's clone where one existed under `/tmp/council/*/`. Otherwise it is "as reported" by the member. The assembly's GitHub API access was blocked in this session.

| # | Repository | Licence | What to borrow | Where it maps in Apex | Proposed by | Decision and reason |
|---|---|---|---|---|---|---|
| 1 | untitaker/python-atomicwrites | MIT (clone; archived) | tmp file → fsync → replace → fsync dir | `learning.record_day`/`save_state`, `paper.save_books` | 06, 19 | **ADOPT NOW** (WP-3, WP-4): about 15 lines by hand, no dependency; closes C-09 and C-99. |
| 2 | rigtorp/Seqlock | MIT (clone) | `load()` retries until seq is even and unchanged; writer wraps the write | `table.snapshot`, `apply_packet` try/finally, gateway re-check | 06 | **ADOPT NOW** (WP-1, WP-5): validated by member 06's probe; closes C-40 and C-41. |
| 3 | encode/starlette — `TrustedHostMiddleware` | BSD-3 (as reported) | Host check on http and websocket scopes | `gateway.py`, plus an Origin check | 17 | **ADOPT NOW** (WP-5): already installed via fastapi; closes C-73. |
| 4 | pladaria/reconnecting-websocket | MIT (clone) | jittered exponential backoff, connection timeout, close and timeout events | `app.js` reconnect plus the stale banner | 09 | **ADOPT NOW as a pattern** (WP-5): a few lines by hand, no library; closes part of C-08. |
| 5 | Supervisor/superlance — `httpok` | BSD-style repoze (clone) | restart a process that is alive but unhealthy | `supervise()` heartbeat check | 06 | **ADOPT NOW, warning only** (WP-6). Auto-restart comes **LATER**, once C-11 is fixed and proven. |
| 6 | databento/dbn | Apache-2.0 (as reported) | a self-describing metadata header on every data file | the Recorder's `meta` first and last records | 04 | **ADOPT NOW as a pattern** (WP-1): the first live file cannot be fixed after it is written; part of C-49 and C-21. |
| 7 | gitleaks/gitleaks | MIT (as reported) | `gitleaks dir` and a custom Breeze rule | pre-commit and CI; preflight uses it when installed | 17 | **ADOPT LATER**: the fixed in-house regex (WP-6) closes C-32 now. |
| 8 | Yelp/detect-secrets | Apache-2.0 (as reported) | `.secrets.baseline` and entropy detectors | replace `PLACEHOLDER` whitelisting | 17 | **CONCEPT ONLY**: WP-6 applies the placeholder to the value only; the full baseline is not needed yet. |
| 9 | jaraco/keyring | MIT (as reported) | OS vault for the permanent `api_secret` | `cmd_session`, `load_credentials` | 17 | **ADOPT LATER**: a credential-flow change is a bad idea the day before the first live login. |
| 10 | tox-dev/filelock | MIT (clone) | an exclusive lock file per data directory | `supervise()` | 06 | **ADOPT LATER**: Windows already raises `FileExistsError`; the risk is Linux-only (C-98). |
| 11 | gostevehoward/confseq | MIT (clone) | betting / predictable-mixture confidence sequences (σ-free, valid under any number of looks) | beside `sprt_lines` as an observer; later the GO rule | 03, 14, 20 | **ADOPT NOW as a report-only observer** (WP-3, about 40 numpy lines written from the paper). Making it the GO rule is owner item O-8. |
| 12 | bashtage/arch — SPA / StepM / MCS, stationary bootstrap, HARX | NCSA (clone) | multiple-comparison tests over correlated books; HAR-RV forecast | offline `report --snoop`; evening VRP tool | 03, 11, 12, 14 | **ADOPT LATER**: needs scipy, so offline only; needs ≥ 10–20 sessions to mean anything. |
| 13 | esvhd/pypbo | AGPL-3.0 (as reported) | PBO (CSCV), MinTRL, deflated Sharpe | a nightly observer section in `report.md` | 14, 20 | **CONCEPT ONLY**: AGPL; write it from the paper after ≥ 16 sessions. |
| 14 | philipperemy/lead-lag | MIT (as reported) | Hayashi–Yoshida / HRY lead-lag on asynchronous ticks | EOD tool on the tick tape; replaces LagMeter as evidence for D-015/D-057 | 12, 20 | **ADOPT LATER**: needs recorded days, and fixes C-28 and C-04 as evidence. |
| 15 | nkaz001/hftbacktest | MIT (clone) | z-scored imbalance over a price range; explicit feed-latency model | a book-advisor variant; latency-injection replay | 01, 12 | **ADOPT LATER**: variants only, after C-12 and C-35 are fixed. |
| 16 | kayasolomon/order-flow-toxicity | MIT (clone) | Cont–Kukanov–Stoikov OFI; labelled synthetic market | an OFI observer next to Force; ground-truth sim mode | 01 | **ADOPT LATER**: the principled replacement for the Force ρ/π of C-13. |
| 17 | QuantConnect/Lean — `SubscriptionSynchronizer`, `TrailingStopRiskManagementModel` | Apache-2.0 (Apex copy present; licence as reported) | frontier-clock lock-step replay; premium-peak trailing stop | `apex/replay_lockstep.py`; a `premium_trail` exit shadow | 04, 18 | **ADOPT LATER**: lock-step replay is the fix for C-05 (size M); exit shadows for C-23. |
| 18 | nautechsystems/nautilus_trader | LGPL-3.0 (clone) | virtual clock with ordered timers; component DEGRADED/FAULTED states; greeks shocks; trailing offset types | lock-step replay; per-advisor fault state; attribution observer; exit-shadow dimensions | 02, 04, 07, 08, 18 | **CONCEPT ONLY**: LGPL. The fault-state idea is used by hand in WP-2 (C-07). |
| 19 | vollib/py_vollib | MIT (clone) | reference Black-76 IV, greeks and doctest values | test oracle for `greeks.py`, as constants only | 02, 11, 13 | **ADOPT LATER**: S-sized, but not needed for Monday; pin the reference values in a test after C-76. |
| 20 | vollib/lets_be_rational | Jäckel permissive notice (as reported) | IV at bid and ask in about 2 iterations | the D-020 IV uncertainty band observer | 02 | **ADOPT LATER**: C-53. |
| 21 | marcdemers/py_vollib_vectorized | MIT (clone) | vectorised LBR IV | offline regression test for the C-76 speed-up | 16 | **ADOPT LATER**: needs numba, scipy and pandas, so test-only. |
| 22 | jasonstrimpel/volatility-trading | GPL-3.0 (clone) | Parkinson, Garman-Klass, Rogers-Satchell and Yang-Zhang estimators | `engine/rv.py` observer and a `vrp` advisor (IV/RV) | 11 | **CONCEPT ONLY**: GPL; the estimators are textbook, so write them from scratch later. |
| 23 | gerrymanoim/exchange_calendars | Apache-2.0 (clone) | the XBOM holiday list | preflight diff of `NSE_HOLIDAYS`, current and next year | 10 | **ADOPT LATER** as a dev or preflight check (must be done before about 19 Jan 2027; C-60). |
| 24 | BennyThadikaran/NseIndiaApi | GPL-3.0 (clone) | NSE holiday-master and `fo_mktlots.csv` endpoints | a clean-room preflight observer | 10 | **CONCEPT ONLY**: GPL. |
| 25 | VarunS2002/Python-NSE-Option-Chain-Analyzer | GPL-3.0 (clone) | change in OI at the boundary strikes ("call/put exits") | a `wall_unwind` observer, then an advisor | 13 | **CONCEPT ONLY**: GPL; build it after C-15 and C-50 are fixed. |
| 26 | jensolson/SPX-Gamma-Exposure | none found (clone has no LICENSE) | the \|Δ\| < 0.95 and IV-range filter; the GEX-vs-forward curve | `GexMap.compute` filter; publish the curve | 13 | **CONCEPT ONLY**: unlicensed. |
| 27 | zerodha/pykiteconnect — ticker | MIT (clone) | ping/pong ghost-connection check; capped backoff | transport-liveness and per-segment silence observers in `feed_breeze` | 05 | **ADOPT LATER**: the 30-s watchdog works; better liveness after the first live week. |
| 28 | marketcalls/openalgo | AGPL-3.0 (clone) | typed AUTH / NETWORK / SERVER connect failures; multi-socket symbol caps | `stream_hint` → stop retrying on AUTH | 05 | **CONCEPT ONLY**: AGPL. |
| 29 | pytest-dev/pluggy | MIT (clone) | declare once, verify at load | an advisor registry (`engine/advisors.py`) | 07 | **ADOPT LATER**: C-44; touches learning and must not rewrite recorded decisions. |
| 30 | pydantic/pydantic | MIT (clone) | `extra='forbid'`, discriminated unions | variant schema in `validate()` | 07 | **CONCEPT ONLY for now**: WP-6 uses a 20-line allowed-keys table (keeps the engine numpy-only). |
| 31 | HypothesisWorks/hypothesis | MPL-2.0 (as reported) | `RuleBasedStateMachine` for book invariants; property tests for `apply_packet` | test-only `BookMachine` | 08 | **CONCEPT ONLY** under the MPL rule. Installing it unmodified as a dev tool is the owner's call. |
| 32 | syrupy-project/syrupy | MIT (as reported) | snapshot assertions | golden-replay test of all books | 08 | **ADOPT LATER**: needs lock-step replay (C-05) first. |
| 33 | leeoniya/uPlot | MIT (clone) | cheap streaming time series | replace hand-drawn traces | 09 | **ADOPT LATER**: a UI rewrite is not for Monday. |
| 34 | tradingview/lightweight-charts | Apache-2.0 (clone) | session shading, price lines, accessibility plugin | futures trace | 09 | **ADOPT LATER**: as above; pick one of #33 or #34. |
| 35 | freqtrade/freqtrade | GPL-3.0 (clone) | analysis by entry×exit tag and rejected signals; record migrations with a version | `report --groups`; a `schema` field plus migrate-on-load | 15, 19 | **CONCEPT ONLY**: GPL. |
| 36 | simonw/sqlite-utils | Apache-2.0 (clone) | `sqlite-utils memory` over jsonl | `run_apex.py autopsy DAY` | 15 | **ADOPT LATER**: dev tool only. |
| 37 | hynek/structlog | MIT / Apache-2.0 (clone) | bound context-vars on every log line | `engine_main.log` with market time, episode, cfg | 15 | **CONCEPT ONLY for now**: WP-2 adds market time to `log()` by hand; the dependency is optional later. |
| 38 | ijl/orjson | MIT / Apache-2.0 (as reported) | native numpy and NaN→null serialisation | `StateBlob.write` | 16 | **ADOPT LATER**, as an optional dependency (C-102). |
| 39 | benfred/py-spy | MIT (as reported) | attach-to-PID sampling profiler | runbook step in the first live week | 16 | **ADOPT LATER**: a tool with zero code in Apex. |
| 40 | polakowo/vectorbt | Apache-2.0 + Commons Clause (as reported) | grid of exit stops with labelled exit types | an evening exit-sweep tool | 18 | **CONCEPT ONLY**: Commons Clause; write it by hand. |
| 41 | wbolster/jsonlines | BSD-3 (as reported) | an explicit invalid-line policy | one shared jsonl reader | 19 | **CONCEPT ONLY**: WP-3 implements skip-and-count by hand. |
| 42 | skfolio/skfolio — `CombinatorialPurgedCV` | BSD-3 (as reported) | purged, embargoed CV by session | validation harness for a future `ml_meta` advisor | 20 | **ADOPT LATER**: only after ≥ 300 resolved candidates (D-071). |

---

## 5. Items needing the owner's decision

Each item below would change frozen trigger behaviour (D-033: the trigger, its lateness test including the IV cap, its four exits, and the v1 contract rule), a pre-registered test, or an owner rule. The council states the options. **It does not decide.** Where an observer is listed, a before-Monday package already logs it, so the decision can be made from Monday's data either way.

**O-1 · How ATM IV, the input to the frozen IV cap (1.5 pts) and to `iv_late`, is measured** (C-16).
- (a) Keep the nearest-strike snapshot.
- (b) Interpolate IV at F between the two bracketing strikes, keeping 1.5.
- (c) Measure the rise at the onset strike (`iv0_strike`).
- (d) Keep (a) for the trigger and run (b) or (c) as a pre-registered variant.

*Observer:* WP-2 logs an interpolated ATM IV and its rise since onset on every candidate and trade.

**O-2 · Days to expiry: calendar or trading days** (C-88). This affects the delta-band choice (`paper.py:120-121`) and the IV/greeks clock (`greeks.py:43`).
- (a) Calendar days, as coded.
- (b) Trading days for the band only.
- (c) Trading time for both.

D-021 does not say which. Fri 6 Nov and Fri 20 Nov are affected.

**O-3 · The theta clock on 0DTE and in general** (C-17). It affects the pre-registered `straddle_spike` variant, `gamma_leg`, the premium state and `room`.
- (a) Keep `/375`.
- (b) Use the wall-clock-consistent rate on expiry day (`/1440`) and keep `/375` otherwise.
- (c) Calibrate the clock from quiet-time drift (D-032).

*Observer:* WP-7 logs the corrected expected path beside the current one.

**O-4 · Price exits during the guard's 20-s resume phase and right after a restart** (C-22; D-076 as decided).
- (a) Keep: no price exit until the blackout lifts.
- (b) Allow STOP and TRAIL once the futures quote is fresh (≤ 3 s) and not a bad print, while entries keep the 20-s rule.

**O-5 · Stock-scale learning before 09:15** (C-30). This affects synchrony S, an input to the frozen trigger.
- (a) Gate the stock sigma and volume baselines on `in_session`, as futures already are (`domino.py:89`).
- (b) Keep the code and always start the engine after 09:15.
- (c) Keep as is.

**O-6 · Index weights for TCS (2.70) and ITC (2.56)** (C-58). These affect synchrony S and the basket gap.
- (a) Update from a dated factsheet or constituent file.
- (b) Cap every estimate at or below the #10 weight (2.52).
- (c) Keep, and add a unit test that flags it.

**O-7 · Quote freshness: message age or quote/trade age** (C-18). This affects the guard's `fut_age` (entries and exits) and `choose_contract`'s `age < 15`.
- (a) Keep `recv_ns` (refreshed by depth).
- (b) Keep a separate `quote_ns` for the guard and contract choice.
- (c) Use trade age (now − `ltt`) for contract choice.

*Observer:* WP-2 and WP-4 log trade age and mid at entry and exit.

**O-8 · The SPRT scoreboard, re-registered before any live data exists** (C-02, C-24, C-26).
- (a) Keep σ = 10 %, the arithmetic unit, and the bare GO line.
- (b) Raise σ to a conservative value (members suggest 30 %) and/or block GO/KILL before 30 trades.
- (c) Switch to per-trade ln(1+r).
- (d) Make the σ-free betting e-value the GO/KILL rule.
- (e) Wire the §9.2/§6.1 day-level conditions into GO, and latch GO.

*Observer:* WP-3 prints (c) and (d) beside the current line.

**O-9 · The look schedule for promotions** (C-25, C-64).
- (a) Every evening, as coded.
- (b) Fixed checkpoints (for example sessions 20, 40, 60, 80) with alpha spending.
- (c) Anytime-valid e-values per challenger and gate.
- Also: test gated books at α/13 over all advisors ever screened, and require a significant reversal before demoting.

**O-10 · Fairness of the controls** (C-27, C-63, C-62).
- (a) Keep.
- (b) Compare on per-trade mean return (the D-064 unit) rather than daily log growth.
- (c) Rate-match `random_entry`, or pool 10–20 seeds.
- (d) Re-point `futures_only` to the current champion's m*, and compare `premium_momentum` only with `straddle_spike`.
- (e) Compare controls since `champion_since`.

**O-11 · 0DTE entries after 14:45** (C-83). D-021 says "none after 14:45"; the code allows next-week entries until 15:15.
- (a) Make the branch return no contract.
- (b) Keep next-week entries and fix D-021.

**O-12 · Delta fallback with no upper bound** (C-84).
- (a) Keep the smallest delta at or above `lo`.
- (b) Cap it (for example at 0.90).
- (c) No contract when the band is empty.

*Observer:* WP-4 logs when the fallback was used.

**O-13 · The 0DTE 15:00 flatten exemption at delta ≥ 0.9 when the held quote is stale** (C-93).
- (a) Keep.
- (b) Require a fresh quote for the exemption.

**O-14 · The post-KILL replacement rule** (C-61).
- (a) The maximum raw sum, as coded.
- (b) The best log-growth record since `champion_since`, by paired test.
- (c) A pre-registered successor order.

**O-15 · `straddle_spike` exits** (C-67).
- (a) Keep the domino exits.
- (b) Pre-register a spike-end exit (D-060) as a new variant or exit shadow.

**O-16 · Unverified event dates** (C-59). The FOMC (about 29 Oct IST), the US midterms (3–4 Nov) and the Union Budget (1 Feb 2027) need the owner's confirmation. WP-6 adds only the RBI dates the member verified.

**O-17 · Whether the advisor fixes in WP-2 and WP-7 count as "bug fixes" or "new pre-registrations"** (C-12, C-13 later, C-14, C-35, C-56). They change logged advisor verdicts and the PE trades of the pre-registered `m2.0_s0.5_bookexit`, not the champion.
- (a) Treat them as bug fixes and tag rows with the code version (WP-1 and WP-2 add it).
- (b) Re-register the affected advisors and variant with a new registration date.

Because no live data exists yet, both are clean before Monday.

---

## 6. The build plan

### 6.1 Rules for the before-Monday build

- Small, safe, testable changes only. **No file touches `apex/engine/domino.py`, `apex/engine/guard.py`, `apex/universe.py`, or the trigger branch of `paper.evaluate_entry`.**
- No change to which trades the champion takes or how it exits, except through the owner's §5 answers.
- Each package owns its files exclusively. Each adds its own `tests/test_wpN.py`, runnable as `python tests/test_wpN.py` with numpy only, in the same style as `tests/test_core.py`. **Nobody edits `tests/test_core.py`.**
- Where two packages meet, the plan states an interface. Each side is written so it works whether or not the other side has merged yet (`dict.get` / optional import), so merge order does not matter.
- Every package must leave `python tests/test_core.py` green and `config.validate()` returning `[]`.
- The changes are deployed between sessions (I-11). Monday's session runs whatever is merged and passing by Sunday night.

### 6.2 Work packages

#### WP-1 · Feed and tick tape: crash-safe recording and feed hardening

**Fixes:** C-01, C-15, C-19, C-21, C-36, C-37 (recording order only), C-38, C-40, C-41, C-47, C-49 (recording header), C-78 (replay always ends).

**Files (only these):** `apex/feed_core.py`, `apex/feed_breeze.py`, `apex/feed_replay.py`, `apex/table.py`, `tests/test_wp1.py`.

**Changes:**
1. **One file per Recorder start.** `Recorder.__init__` picks `DAY{suffix}.jsonl.gz` if it is absent, otherwise the first free `DAY{suffix}.p2.jsonl.gz`, `.p3`, and so on. It never opens in append mode on an existing file. Use `"wt"`.
2. **A `meta` first record:** `{"k":"meta","t":…,"d":{"schema":1,"apex":apex.__version__,"git":<short hash or null>,"cfg":<sha1 of json.dumps of config.VARIANTS, CONTROLS, the guard constants and IV_RISE_CAP, sorted>,"part":n}}`.
3. **A closing `meta` record** in `_run`'s exit path with `dropped` and the line count.
4. **Expose `Recorder.dropped`** through the table's existing control block only if a spare field exists. Otherwise just log it at stop. **Do not change the table dtype.**
5. **`BreezeFeed.run()`:** wrap the body after `build()` in `try/finally: self.shutdown()`.
6. **`main()`:** on any exception, call `rec.stop()` if a recorder exists before re-raising.
7. **`feed_replay.run(path)`:**
   - expand `path` to `[path] + sorted(stem.p*.jsonl.gz, key=part number)`;
   - read each part in turn;
   - catch `(EOFError, OSError, zlib.error, gzip.BadGzipFile)` per part, log "part N ends early", and continue with the next part;
   - put the whole loop in `try/finally` that always sets `feed_state = 7`;
   - ignore `meta` records except for logging them.
8. **`install_registry`** in replay zeroes the rows (as live `BreezeFeed.__init__` does) whenever the instrument ids move.
9. **`on_message`:** move `feed.rec.put("p", recv, data)` inside `with feed.lock:`.
10. **`Registry.add` on an existing key:** if `depth_token` is given and the item has none, store it, so `subscribe_all` joins it on the next re-centre.
11. **`apply_packet`:** wrap every `begin`/`end` pair in `try/finally` so `end` always runs. On a malformed depth level, set that level to NaN rather than raising.
12. **`build()`:** after resolving, `raise SystemExit(...)` if `NIFTY|FUT` is missing or fewer than `2*(WEEKLY_BAND)` w0 options resolved. The supervisor retries, which re-downloads the master.
13. **`poll_chain`:** publish only if both `call` and `put` returned ≥ 1 row and their strike counts are within 20 % of each other. Otherwise log "chain partial: kept previous" and do not bump `chain_version` or record.
14. **Login timeout:** `socket.setdefaulttimeout(60)` before importing `breeze_connect`, and log lines with elapsed seconds before and after `generate_session`.
15. **Paper-only interlock call site (interface with WP-6):** right after the `BreezeConnect` object is created:
    ```python
    try:
        from apex import interlock
    except ImportError:
        interlock = None
    if interlock:
        interlock.install(self.breeze)
    ```
16. **`Table.snapshot`:** between retries call `time.sleep(0)`, and treat `before & 1` as bad. Keep returning the array; return signature unchanged. The torn-row count goes into an attribute `self.last_torn` for logging.

**Tests (`tests/test_wp1.py`):**
- (a) A subprocess writes 1,000 lines and calls `os._exit`. A second Recorder writes 1,000 lines. Assert two part files exist, and that the replay reader yields at least 1,000 lines from part 2 without raising.
- (b) A truncated part followed by a good part: replay continues and sets `feed_state = 7` (use a private table name via the `Table` kwargs).
- (c) Assert the `meta` header is present and parseable.
- (d) `apply_packet` with a depth level `None` leaves `seq` even and does not raise.
- (e) `Registry.add` twice, the second time with `depth_token`, stores the token.
- (f) `poll_chain` with a fake breeze whose put leg returns `{}` does not bump `chain_version`.
- (g) `build()` with a fake token lookup that resolves nothing raises `SystemExit`.
- (h) `snapshot()` against a writer thread that keeps a row odd for 1 ms: the row is retried.

#### WP-2 · Engine loop: fault isolation, liveness, exit-state persistence, advisor input fixes, observers

**Fixes:** C-07, C-08 (engine side), C-11, C-12, C-14, C-34, C-77. It also adds the observers for O-1 and O-7.

**Files (only these):** `apex/engine_main.py`, `tests/test_wp2.py`.

**Changes:**
1. **Add `_safe(name, fn, default)`** with a once-a-minute log throttle.
   - In `advise()`, compute each advisor through `_safe`. On an exception it yields `{"veto": False, "why": "advisor faulted", "faulted": True}`.
   - Wrap `straddle.update`, `bank.update`, `lag.update` and `force.update` (`:250-262`) in `_safe`.
   - Wrap the `advise()` call itself, so that `run_books(ctx)` **always** runs once `ctx` exists.
   - The order of operations does not change.
2. **Heartbeat:** set `engine_hb_ns` only after `step()` returns without an exception. Also set a new **state-blob** field `engine_ok_s`, the market time of the last good step, in `publish()`. **No table dtype change.**
3. **Persist exit state:** in `run_books`, after the exit loop, compute for every book with a `pos` a signature `(key, best, trail, pending reason, stale_exit)`. If it changed since the last save and at least 1.0 s (market time) has passed, call `paper.save_books`. Saves on entry and exit stay immediate.
4. **`book_state`:** call `self.flow.side(i, +1)` for both CE and PE, because we only buy, so the asks always oppose (C-12). Add `"side_fix": 1` to each `book_state` entry so rows are distinguishable.
5. **`advise()`:** call `self.gex.advise(d, getattr(self, "fwd", None) or ctx["fut"])` (C-14).
6. **Event and decision tape:**
   - `ev()` also appends `{"t", "k", "x", "mkt_t"}` to `PAPER_DIR/events_DAY.jsonl`.
   - In `run_books`, for the champion only, append to `decisions_DAY.jsonl` whenever `diagnostics.reason_class(why)` changes. If that helper is not importable, use the reason up to its first ":". Record `t`, reason, z, S, moved and episode id.
   - Both writes are append-only, inside try/except, at most a few hundred lines a day.
7. **`log()`:** prefix lines with wall time *and* `mkt=HH:MM:SS` from `self.now_dt` when it is set.
8. **`option_rows`:** add `"ltt": float(snap["ltt"][i])` if it is finite and greater than 0, else None. This is the interface for WP-4's trade age.
9. **Observer for O-1 in `compute_greeks`:**
   - for w0, also compute `self.atm_iv_interp` as IV linearly interpolated in strike between the two strikes bracketing F, using the mean of CE and PE IV at each strike;
   - store the onset value in the episode (`ep["iv0_interp"]`), next to `iv0`;
   - add `ctx["iv_rise_interp"]`;
   - publish both.

   **The trigger keeps reading `iv_rise_since_onset` unchanged.**
10. **Bug guard:** `end_day()` must not raise out of the stop path (wrap it in try/log). Do not change when it runs; WP-3 handles non-trading days.

**Interfaces:** WP-4 reads `o["ltt"]` and `ctx.get("iv_rise_interp")`. WP-5 reads the state-blob field `engine_ok_s`. WP-7 is unchanged.

**Tests (`tests/test_wp2.py`):** use a private shared-memory table and blob (`Table(create=True, name="t_wp2_…")`), a hand-built registry with NIFTY|FUT, SPOT, 2 w0 strikes CE/PE and 2 stocks, and a set `ctrl.now_ns`. Then:
- (a) Monkeypatch `Engine.advise` (and separately `self.force.update`) to raise. Open a CE position, move futures 13 pts against it, step. Assert a STOP exit is recorded.
- (b) Arm a trail (+15 pts), step until at least 1 s passes, then rebuild `Engine` via `start_day`. Assert the reloaded `pos["trail"]` is True and `best` is preserved.
- (c) With bids refilling on a PE and asks draining, `book_state()[pe_id]["opp_q"]` reflects the asks.
- (d) `advise()` passes `self.fwd` to `gex.advise` (a spy).
- (e) `events_DAY.jsonl` gets a line on `ev()`.
- (f) `engine_hb_ns` is not advanced on a raising step.

#### WP-3 · Learning record: integrity, non-trading days, unrecorded days, report-only observers

**Fixes:** C-03, C-09 (write side), C-10, C-43 (state part). It adds report-only observers for C-02, C-24, C-25 and C-26 (O-8 and O-9 stay with the owner).

**Files (only these):** `apex/engine/learning.py`, `tests/test_wp3.py`.

**Changes:**
1. **Atomic write helper `_atomic_write_lines(path, lines)`:** write tmp, flush, `os.fsync`, then replace with up to 5 retries of 0.2 s on `PermissionError`. Use it for `record_day`, `save_state` and `REPORT`. Also write a dated copy `report_DAY.md`.
2. **Torn-line tolerance:** `record_day` and `_load_days` skip lines that fail `json.loads`, count them, and keep them in `days.jsonl.corrupt` (append) so evidence is never discarded. `learn()` prints "N corrupt rows skipped" in the report.
3. **`load_state`:** on a parse failure, rename the bad file to `state.json.corrupt-<ts>` before returning defaults, and add a report line saying so.
4. **Non-trading days:**
   - `record_day(day, …)` returns without writing if `not config.is_trading_day(date.fromisoformat(day))`;
   - `learn(today)` returns the loaded state unchanged (no streak movement, no save) for a non-trading `today`, writing a one-line report.
5. **Back-fill:** a new `backfill_unrecorded(before_day)`, called at the top of `learn()`. For each `PAPER_DIR/YYYY-MM-DD.json` with day < `before_day`, a trading day, and not present in `days.jsonl`, it reads the JSON directly (`{book: {"trades": [...]}}`, wrapping each in a tiny object with `.trades`) and calls `record_day`. Any book whose `pos` is not null is tagged `"unclosed": true` on that day's row. It logs `{"event": "backfilled", "day": d}` to `s["log"]`.
6. **Report-only observers.** None of these moves state, streaks or champion.
   - (i) Wald lines recomputed with the observed sd (once n ≥ 10).
   - (ii) The SPRT on per-trade `100·ln(1+r/100)`.
   - (iii) A predictable-mixture betting e-value for "mean ≤ 0" on per-trade returns clipped to [−100, +300] %, with the λ schedule fixed in code and documented.
   - (iv) "Champion #k since registration, evening looks n" next to the status.
   - (v) The §9.2 day-level conditions shown as a checklist under the GO line.

**Tests (`tests/test_wp3.py`)** (use a temp `APEX_DATA` and `importlib.reload(config, learning)` as `test_core` does):
- (a) A torn last line in `days.jsonl`: `record_day` and `learn` both succeed, and the report mentions 1 corrupt row.
- (b) A simulated crash mid-write (monkeypatch `os.replace` to raise once) leaves the old `days.jsonl` intact.
- (c) `record_day("2026-10-24", …)` (a Saturday) writes nothing, and `learn("2026-10-24")` leaves streaks unchanged. The promote-on-Saturday scenario from member 08 must not promote.
- (d) Write `paper/2026-10-19.json` without calling `record_day`. `learn("2026-10-21")` back-fills 19 Oct.
- (e) The e-value of an all-zero-return stream stays at or below 1, and a strongly positive stream exceeds 20 (sanity).
- (f) A corrupt `state.json` is preserved as `.corrupt-*`.

#### WP-4 · Paper books: corrupt-file safety, durable saves, exit Greeks and trade-age observers

**Fixes:** C-43 (books part), C-53 (exit Greeks), C-99 (books), C-100 (CSV columns). It adds observers for C-18 / O-7, O-1 and O-12. **No decision logic changes.**

**Files (only these):** `apex/engine/paper.py`, `tests/test_wp4.py`.

**Changes:**
1. **`save_books`:** flush, `os.fsync`, then replace with the same retry loop as WP-3 (a local helper, so there is no cross-package import).
2. **`load_books`:** on a parse failure, rename the file to `<day>.json.corrupt-<ts>` and return None, so the next save cannot overwrite the evidence. Expose `paper.LAST_LOAD_ERROR` (a string) for the engine or dashboard to read later.
3. **`open_trade` records these extra fields in `pos`** (observers only):
   - `trade_age_in = now_s − opt["ltt"]` if `opt.get("ltt")`, else None;
   - `mid_in = (bid+ask)/2` if both are present;
   - `iv_rise_in = ctx.get("iv_rise_since_onset")` and `iv_rise_interp_in = ctx.get("iv_rise_interp")`;
   - `dte_in` (calendar days, as currently computed);
   - `band_fallback` (True when `choose_contract` took the "above" branch: set by passing a flag through `opt` as `opt.get("_fallback")`, which `choose_contract` sets on the returned dict copy only).

   `choose_contract`'s selection itself must not change.
4. **`close_trade` adds:** `trade_age_out`, `mid_out`, `iv_out = o.get("iv")`, `delta_out = o.get("delta")`, and `ret_pct_mid` (return on mid-to-mid, when both mids exist).
5. **`write_trades_csv`:** append the columns `episode`, `delta_in`, `iv_in`, `iv_out`, `delta_out`, `trade_age_in`, `trade_age_out`, `mid_in`, `mid_out`, `ret_pct_mid`, `stop_fut`, `peak_pts`, `exit_quote_age`, `band_fallback`. Existing columns keep their order.

**Tests (`tests/test_wp4.py`):**
- (a) A corrupt `paper/<day>.json` makes `load_books` return None and leaves a `.corrupt-*` file.
- (b) `save_books` survives one injected `PermissionError` from `os.replace`.
- (c) On a synthetic ctx with `ltt`, `open_trade` → `close_trade` records `trade_age_in/out`, `mid_in/out`, `iv_out`, `delta_out`.
- (d) **Behaviour lock:** for a fixed grid of ctx fixtures (0DTE morning, 0DTE 13:30, 1 DTE, ≥3 DTE, empty band), `choose_contract` returns the same contract id as the baseline function, copied into the test as a frozen reference. `evaluate_entry` and `check_exit` return the same results as baseline on a scripted 30-step path. This also starts closing C-06 for the paper mutants.
- (e) The CSV header contains the new columns.

#### WP-5 · Gateway and dashboard: visible staleness, local hardening, torn-read re-check, readability

**Fixes:** C-08 (display side), C-40 (gateway part), C-69, C-71 (Force and OI colours), C-73, C-103 (gateway logging, backoff).

**Files (only these):** `apex/gateway.py`, `apex/static/app.js`, `apex/static/index.html`, `apex/static/style.css`, `tests/test_wp5.py`.

**Changes:**
1. **Gateway staleness.** Every `/ws/state` frame and `/api/state` response gains `engine_age_ms` (from the table's `engine_hb_ns`), `feed_age_ms` (from `feed_hb_ns`) and `engine_ok_s` (passed through if WP-2 provides it). When the blob has not changed for 1 s, send a small `{"hb":1, "engine_age_ms":…, "feed_age_ms":…}` frame.
2. **Gateway hardening.**
   - `app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])`.
   - In both websocket handlers, if an `Origin` header is present and is not `http://127.0.0.1:<PORT>` or `http://localhost:<PORT>`, close with code 1008 before `accept`. A missing Origin (non-browser client) is allowed.
   - Cap each endpoint at 4 concurrent connections.
   - Replace the bare `except Exception: return` with a once-a-minute log line.
3. **Gateway torn-read re-check:** in the tick diff loop, re-read `seq` after copying the rows and skip rows whose `seq` changed or is odd.
4. **`app.js` stale banner and backoff.**
   - A full-width red banner "ENGINE STALE n s" / "DISCONNECTED" when `engine_age_ms > 2000` or no frame arrives for 2 s.
   - While stale, grey the verdict, position and stop.
   - Reconnect with jittered backoff (1 s × 1.3ⁿ, capped at 10 s).
5. **Readability.**
   - Force line colour from `force.dir × verdict`, not the verdict alone.
   - OI map uses the CE/PE palette of the ladder.
   - `.leg .meta` wraps (`white-space: normal`) instead of clipping.
   - Add `aria-live="polite"` on the verdict.

   No other visual redesign.

**Tests (`tests/test_wp5.py`)** (skip with a printed note if fastapi is not importable; numpy-only CI still passes):
- (a) A TestClient `GET /api/state` with `Host: evil.example` returns 400.
- (b) `/ws/state` with `Origin: https://evil.example` is refused, and with `Origin: http://127.0.0.1:<PORT>` is accepted.
- (c) The state payload contains `engine_age_ms`.
- (d) A static check that `app.js` contains the stale-banner handler and no `setTimeout(connect…, 1000)` fixed reconnects.

#### WP-6 · Preflight, paper-only interlock, supervisor, calendar and config checks, CI

**Fixes:** C-20, C-32, C-33, C-45, C-59 (verified dates only), C-60, C-75, C-78 (counter reset), C-92, C-08 (supervisor warning), C-09 (shutdown deadline).

**Files (only these):** `run_apex.py`, `apex/config.py`, `apex/interlock.py` (new), `.github/workflows/tests.yml`, `tests/test_wp6.py`.

**Changes:**
1. **New `apex/interlock.py`.**
   - `install(breeze)`: rebinds every attribute of the instance and its class whose name matches `order|square|gtt|funds|margin|limit_calc` to a function raising `RuntimeError("PAPER_ONLY: blocked <name>")`.
   - `patch_requests()`: wraps `requests.Session.request` so any URL whose last path segment is not in an allowlist (`customerdetails`, `quotes`, `optionchain`, `historicalcharts`, plus whatever the security master and session endpoints need, determined by grep of the 1.0.69 SDK) raises the same error.

   WP-1 calls `install`. `cmd_preflight` calls `install` and `patch_requests` on its own `BreezeConnect`.
2. **Scanner (C-32, C-75).**
   - `KEYLIKE`: `(?i)["']?(api_?key|api_?secret|session_?token)["']?\s*[:=]\s*["']?([^\s"',]{8,})`.
   - `PLACEHOLDER` is tested on the value group only.
   - Skip directories by `os.path.relpath(dp, ROOT).split(os.sep)[0] in {"secrets", "data", "logs", ".git", "__pycache__"}`.
   - Add `.yml .yaml .toml .env .ps1 .bat .csv .ipynb`.
   - Replace the `.gitignore` grep with `git check-ignore -q secrets/x data/x logs/x` when git is available, falling back to the grep.
3. **Preflight calendar (C-60, C-92).**
   - Fail if any date from today to `max(w1, monthly_expiry)` falls in a year with no `NSE_HOLIDAYS` entries.
   - Print "today is an NSE holiday / not a trading day" as a FAIL line for `live`.
4. **`config.py`.**
   - `EVENT_DAYS = {"2026-12-04": "RBI policy decision", "2027-02-05": "RBI policy decision"}`, with the Saturday example removed.
   - `validate()` rejects unknown variant keys (allowed: `m_star s_star L_star d_star s_exit gap_star exit_book spike random momentum`) and more than one of `{gap_star, exit_book, spike, random, momentum}` per variant.

   **No change** to any value in `VARIANTS`, `CONTROLS`, `IV_RISE_CAP`, `SPRT_*` or the weights.
5. **Supervisor.**
   - Every second in live market hours, read `engine_hb_ns` and `feed_hb_ns`. If either is older than 10 s, print and log "ENGINE STALE n s" once per minute. **No auto-restart** (that is later).
   - Reset the feed `restarts` counter after 10 minutes of uptime.
   - Give the engine its own 20-s shutdown deadline after the feed's, and wait for the engine *before* terminating anything.
6. **Replay isolation (C-20).** `supervise("replay")` uses `data/replay/<file-stem>/<YYYYmmdd-HHMMSS>/` as `APEX_DATA` and prints it. `learn` and `report` gain `--dir` to point at a run folder. The live paths are unchanged.
7. **CI:** run `python tests/test_wp{1..7}.py` after `test_core.py`.

**Tests (`tests/test_wp6.py`):**
- (a) The exact `cmd_session` JSON, a `.env` line, and `"api_secret": "abc/def=ghi.jkl"` are all CAUGHT. A doc stand-in `api_key="sk-no-key-required"` is not.
- (b) A tree under a path containing `\data` is still scanned.
- (c) `interlock.install` on a dummy object with `place_order`, `gtt_single_leg_place_order` and `set_funds` makes each raise. `patch_requests` blocks `…/order` and allows `…/quotes`.
- (d) An AST-based no-order guard over `apex/` and `run_apex.py`. It flags `.place_order(`, `getattr(x, "place_order")`, and any name from the full list in C-33. It must pass on the tree.
- (e) `validate()` rejects `{'exit_bok': True}` and `{'spike': True, 'random': True}` and accepts the current registry.
- (f) The holiday-coverage check fails for a date whose `w1` is in a year with no holidays (monkeypatch `NSE_HOLIDAYS`).

#### WP-7 · Advisor and observer correctness (flow, levels, GEX, BankLead, straddle-watch observer)

**Fixes:** C-35, C-18 (depth-staleness part, advisor side only), C-50, C-56. It adds the observer for O-3 (C-17).

**Files (only these):** `apex/engine/flow.py`, `apex/engine/market.py`, `apex/engine/levels.py`, `apex/engine/gex.py`, `apex/engine/extras.py`, `apex/engine/straddle_watch.py`, `tests/test_wp7.py`.

**Changes:**
1. **`flow._classify`:** add `& (r10 <= 0.15)` to the DSLOW mask (C-35).
2. **`Flow.update`:** set every class of rows whose depth is older than 3 s (`now − depth_ns/1e9 > 3`) to UNK. Read `depth_ns` from `m.snap` through a small accessor added to `Market` (`Market.depth_age(now_s)`). `Market`'s existing `has_depth` and ring behaviour do not change.
3. **`Pressure.refresh`:**
   - ignore a chain whose `expiry` is before today's date or whose table `chain_ns` is 0;
   - store `self.chain_ns`;
   - `destination()` returns None, so `room` says "no wall data" and does not veto, when the chain is older than `3 × CHAIN_POLL_S`;
   - set `oi0` only from a chain whose `chain_ns` falls on today's date.
4. **`GexMap`:** remember the build time of the map. `advise()` returns `(False, "gamma map stale")` when it is older than `3 × CHAIN_POLL_S`. **The signature is unchanged.**
5. **`BankLead.update`:** learn its sigma only in session (09:15–15:30 from `now_s`) and only on a finite 15-s change. **The signature is unchanged.** The blackout freeze is later, because it needs a signature change in WP-2's call site.
6. **`StraddleWatch`:** compute and log `expected5_0dte` (theta at `/1440` on expiry day, else equal to `expected5`) and `excess_0dte` beside the existing fields in the straddle jsonl and the view. **Spike detection keeps using the existing `expected5`.**

**Tests (`tests/test_wp7.py`):**
- (a) A 10-s +50 % rise after a 60-s −70 % fall classifies as REFILL.
- (b) A row whose depth is 5 s old classifies as UNK.
- (c) With a chain file whose expiry was last week, `Pressure` has no OI and `destination()` is None. With a chain older than 270 s, `destination()` is None.
- (d) A GEX map older than 270 s returns `(False, "gamma map stale")`.
- (e) BankLead sigma is unchanged by updates with `now_s` at 09:05.
- (f) On a 0DTE fixture, `expected5_0dte / expected5 ≈ 375/1440`, and the spike decision is identical to baseline.

### 6.3 File ownership check

| File | Package |
|---|---|
| `apex/feed_core.py`, `apex/feed_breeze.py`, `apex/feed_replay.py`, `apex/table.py` | WP-1 |
| `apex/engine_main.py` | WP-2 |
| `apex/engine/learning.py` | WP-3 |
| `apex/engine/paper.py` | WP-4 |
| `apex/gateway.py`, `apex/static/*` | WP-5 |
| `run_apex.py`, `apex/config.py`, `apex/interlock.py` (new), `.github/workflows/tests.yml` | WP-6 |
| `apex/engine/flow.py`, `market.py`, `levels.py`, `gex.py`, `extras.py`, `straddle_watch.py` | WP-7 |
| `tests/test_wpN.py` | WP-N |
| **Untouched:** `domino.py`, `guard.py`, `regime.py`, `ledger.py`, `diagnostics.py`, `greeks.py`, `universe.py`, `feed_sim.py`, `audio.py`, `tests/test_core.py`, `docs/*` (except this file) | — |

**Cross-package interfaces.** All are optional reads, so any merge order works:
- WP-1 → WP-6: `apex.interlock.install` (import guarded).
- WP-2 → WP-4: `o["ltt"]` and `ctx["iv_rise_interp"]` (read with `.get`).
- WP-2 → WP-5: `engine_ok_s` (read with `.get`).
- WP-4 internal: `choose_contract`'s `_fallback` flag stays inside `paper.py`.

### 6.4 Later roadmap (after Monday, in order)

1. **The owner's §5 answers.** Implement each as a versioned, pre-registered change with a new registration date (I-11). O-1, O-5, O-6 and O-7 change trigger inputs. O-8 to O-10 and O-14 change the learning loop.
2. **Lock-step replay** (`apex/replay_lockstep.py`, Lean-style frontier clock), plus a twice-identical CI test on Monday's recording, plus a golden snapshot (syrupy concept) (C-05, C-06, C-31).
3. **An engine-level harness and the remaining mutation-killing tests** (C-06, C-31, C-46). Re-run member 08's `mutate.py` until the paper and learning mutants die.
4. **Observer and control persistence across restarts:** `Book.ctl`, `Ledger.seen/open`, regime rebuild from the tape, and a `restarted` tag on labels (C-42). Then supervisor auto-restart on a stale heartbeat (C-08).
5. **Evidence tools for the domino thesis:**
   - a shuffled-time and ±1-s-shift null for the BASKET-LED rate and the lag;
   - Hayashi–Yoshida lead-lag on the tape (`philipperemy/lead-lag`);
   - champion vs `futures_only` trade overlap;
   - P(S ≥ s* | z ≥ m*) from the ledger;
   - `gap_cov` and per-name quote age logged next to `gap`;
   - latency-injection replay (C-04, C-28, C-29, C-57).
6. **Force rebuilt on a rolling-window CKS-OFI observer**, plus a ground-truth-labelled sim mode (C-13, C-79, C-80).
7. **Greeks and IV:**
   - the merged, 20-iteration IV solver with the py_vollib oracle test (C-76);
   - the IV bid/ask band and sticky-IV P&L attribution (C-53);
   - a more robust forward (C-52);
   - refuse expired expiries (C-85).
8. **Exit shadows**, scored in `ret_pct`: premium −X % / trail from peak (Lean), a delta-scaled futures stop, a time stop, and the spike-end rule (C-23, C-67).
9. **Regime v2 as a pre-registered variant:** a time-of-day baseline, a relative EXHAUSTION bar and the restart flag (C-54, C-55). An IV/RV `vrp` observer and advisor (C-87).
10. **Learning-loop statistics**, once O-8 and O-9 are decided: an SPA/StepM `--snoop` report (arch, offline), PBO/MinTRL from the paper, Wilson tables marked exploratory with a null row (C-61 to C-66, C-94 to C-96). An advisor registry with per-advisor start dates (C-44).
11. **Feed:**
    - typed AUTH failures;
    - ping/pong liveness and per-segment silence;
    - ordering guards on depth and index packets;
    - registry seeding from today's `instruments.json`, so a restart keeps row ids;
    - depth re-centred with the ATM (C-36 to C-39, C-104).
12. **Data lifecycle:** a `schema` field with migrate-on-load, a 90-day tick prune, a disk check at preflight and at 12:00, log rotation (C-49, C-100).
13. **Safety:** keyring for `api_secret`, `APEX_SECRETS` outside the tree, the SDK log moved under `data/`, gitleaks in CI (C-74, C-106).
14. **Dashboard:** the engine publishes `entry_ready`/`blocked_by` (C-68); diff rendering and the `why` text visible (C-70); rAF tick batching without forced reflow (C-72); a compact decision strip; uPlot or lightweight-charts.
15. **Calendar:** add the 2027 holidays as soon as NSE publishes them (hard date about 19 Jan 2027); an exchange_calendars diff; lot and freeze cross-checked against the master (C-60, C-90, C-91).
16. **ML only after ≥ 300 resolved candidates:** a single pre-registered `ml_meta` advisor with purged, session-grouped CV, earning its gate through a gated book (member 20).
