# Audit of the review-driven changes (18 Oct 2026, 03:00 IST)

**Question:** was every weakness from the four external teardowns (`04_EXTERNAL_REVIEWS.md`) and the four "how would you strengthen it" answers (`05_STRENGTHENING.md`) real, and was each fix built correctly?

**Method:** three passes.
1. A re-read of every changed file against the weakness it claims to fix, plus a numeric check of every figure quoted in the documents.
2. A separate reviewer with no knowledge of this conversation, given only the code and a list of what to try to break (§4).
3. An end-to-end drill: a new `--gap` option in the simulator silences the feed for 40 s at 10:30 and lets the market move 30 points meanwhile, so the resume tick carries the whole move, which is the exact failure F1 describes.

---

## 1. Were the weaknesses valid?

| # | Weakness | Valid? | Evidence |
|---|---|---|---|
| F1 | A feed reconnect can fake a Triangle | **Yes, confirmed in the real engine.** | The drill produced a candidate at 10:30:41 with **z = 8.17** (trigger is 2.0) one second after the feed resumed. Without the guard this would have entered. |
| F2 | Learning scored premium points, but all-in sizing earns a percentage | **Yes.** | A +4 pt gain is 2 % on a ₹200 option and 10 % on a ₹40 one; the old loop scored them equal. Expiry-day trades (₹20–60 premiums) carried the least weight while having the largest % results. |
| F3 | No null: nothing tested the basket against futures-alone or against random entries | **Yes.** | Every registered variant had s* ≥ 0.4; RAW is the champion without gates, not a null. |
| F4 | Challenger test set for 8 challengers, now 12, tested every evening | **Yes.** | p(t ≥ 2.5, df 9) = 0.0169; across 12 independent challengers ≈ 19 % per look (checked: 0.185). |
| F5 | Advisor promotion deleted vetoed trades from a list, ignoring path dependence | **Yes.** | One position at a time + intraday compounding: skipping a trade changes every later trade. |
| F6 | The straddle-spike book had no baseline without the theta model | **Yes.** | Nothing tested whether "excess over theta" beats plain premium momentum. |
| S1 | The trigger recognises movement, not market state (ChatGPT) | **Yes.** | The same z = 2 fires in a clean trend and in a range; nothing distinguished them. |
| S2 | Learning only from executed trades (ChatGPT) | **Yes.** | A filter that removes good opportunities left no trace. |
| S3 | A bad tick can look like a move (Gemini, adapted) | **Yes, minor.** | A single > 1 % print inside 2 s would enter the 15-s impulse. |
| — | Threads/GIL, terminal UI in the engine, live auto-tuning, `list(deque)` (Gemini) | **No.** | None of these exist in Apex (`grep` confirms). Gemini reviewed a different program. |
| — | Licence, stars, contributor files (DeepSeek) | **Not applicable.** | Personal research system. |

## 2. Was the strengthening built correctly? What this audit found and fixed

The re-read found **four defects** in the fixes themselves. All are now corrected, with tests (28 pass).

| # | Defect found in tonight's own code | Severity | Fix |
|---|---|---|---|
| A1 | **The resume rule covered the 15-s impulse window but not the 5-minute windows.** After a gap lifted (20 s of clean data), the straddle watch's 5-min change and the premium-momentum book's 5-min leg rise still contained the jump for up to 5 minutes. A straddle "spike" born in that window could have been traded by `straddle_spike`, and `premium_momentum` could have fired on it. | **High** (same class as F1) | A **settling period** (`SETTLE_S = 300`) after every lifted gap: spikes born in it are tainted, `premium_momentum` waits, and the dashboard shows `settling_s`. The regime classifier drops its price windows when a gap lifts so no 5-min feature spans the jump (`Regime.after_gap`). |
| A2 | **TIME exits on a stale option quote were not tagged** `stale_exit`, so a 15:25 flatten priced on a 40-s-old quote would enter the learning data as clean. | Medium | Clock exits never wait (by design) but are now tagged when the quote is older than 5 s. |
| A3 | **Two definitions of "resolved" in the diagnostics**: the by-decision/by-regime tables counted NEITHER as a miss, the per-advisor table excluded it. The two hit rates were not comparable. | Low | One definition everywhere: NEITHER (within 15 min, not truncated by the close) is a miss. |
| A4 | **Nothing proved F1's fix inside the real multi-process engine**, only in a unit test that drives `Market` and `Domino` directly. | Process | `python run_apex.py sim --gap 37800,40,30` (start second-of-day, length, jump). Result in §3. |

Everything else checked out:
- Guard: starts in blackout; lifts after 20 s continuous fresh futures quotes; σ and volume baselines frozen while on; episodes alive during a gap tainted for their whole life; pre-open quiet quotes are not treated as a gap.
- Exits: price-driven exits wait while the futures quote is > 3 s old; a triggered exit waits ≤ 10 s for an option quote < 5 s old, stays committed if price bounces meanwhile, then exits at the last price tagged `stale_exit`.
- Learning: unit is `ret_pct`; day = log growth; SPRT lines 110.9 / −62.3 + 1.25 n (recomputed by hand); exact Student-t via the incomplete beta matches scipy to 4 decimals; Bonferroni α/12 → t ≥ 3.36 at 10 days; 2-evening persistence; controls can never be champion or challenger; gated books decide advisor promotion.
- Controls: deterministic random schedule per day (reproducible in replay); one entry per slot; momentum re-arms only after the rise halves.
- Regime: no look-ahead (only prices up to now; percentiles within today only); thresholds set against a simulated random walk (ER on 20 steps: mean 0.224, P(≥ 0.35) = 0.216, P(< 0.20) = 0.513, all re-checked tonight); every state reachable.
- Ledger: one candidate per episode; TARGET/STOP by ±d*; option returns at +1/+5/+15 min; closed before learning reads it at the day roll and at shutdown.
- Numbers quoted in the documents: all reproduced (`wilson(8, 10) = 0.49–0.94`, t-values, SPRT lines, ER baseline).

## 3. The drill (real engine, real processes)

`python run_apex.py sim --speed 60 --no-browser --gap 37800,40,30`

| Time (sim) | What happened |
|---|---|
| 10:29:59 | Tape: *data gap: feed not live — entries paused until 20 s of fresh data* |
| 10:30:40 | Feed resumes; futures and every heavyweight jump +30 at once |
| 10:30:41 | Candidate ledger: **z = 8.17**, `ep_gap = True`, decision *DATA GAP: feed stale: futures quote 40 s old*, not fired |
| 10:31:01 | Tape: *data back after 62 s; entries resume*; regime windows reset; `settling_s` = 300 |
| 10:31–10:36 | Later candidates have normal z (2.0–2.5) and `ep_gap = False`: σ did not absorb the jump |
| 10:36:01 | Settling over |
| Whole day | 0 tracebacks |

One honest note on the drill: in the simulator the cumulative volume does not jump on resume, so the artefact's synchrony read 0 % (volume gate). In the live feed the volume does jump, which the unit test models (synchrony ≥ 50 %). The guard does not depend on synchrony either way.

## 4. Independent reviewer: what a fresh pair of eyes found

A separate reviewer with no knowledge of this conversation was given the code and a list of things to try to break. It confirmed the four defects above were real fixes to make, and found **seven more**, all now fixed with tests (28 pass).

| # | Finding (confirmed by the reviewer with a probe) | Severity | Fix |
|---|---|---|---|
| R1 | **An implausible print still moved the trailing stop.** `check_exit` updated `best` from the futures price before checking the blackout, so a +2 % bad print armed the trail and the next real tick exited at a loss; a −1 % print fired a STOP at once if the option quote was fresh. | **High** | No price-driven decision while the blackout is on: `best`, `peak`, STOP/TRAIL/THESIS/BOOK are all skipped; TIME exits and an already-committed pending exit still run. |
| R2 | **The held contract could be priced off a different contract.** When a feed restart renumbers rows, `by_id[pos["id"]]` is whatever row now owns that number (probe: a 25150 CE exited at ₹20 on a 24000 PE's quote, untagged). | **High** | Price by key only; the id fallback must carry the same key, otherwise the exit defers and then closes at the last known price, tagged. |
| R3 | **The regime read COMPRESSION for five minutes after every gap.** `after_gap` emptied the windows, so efficiency and activity read 0 and the label fell through to COMPRESSION (and vetoed). | Medium | After a gap the state is WARMING until the 5-minute window is full again. |
| R4 | **`learn()` was not idempotent.** Each call advanced the 2-evening streaks and appended log entries, so running `run_apex.py learn` twice in one evening satisfied the persistence rule in one real evening. | Medium | Streaks and promotions move once per evening however often it runs; `run_apex.py learn` refuses a repeat without `--force`. |
| R5 | **A manual `learn` during the session lost the day's record.** `end_day` returned before saving books, the CSV, the ledger and `days.jsonl`. | Medium | Everything is recorded unconditionally; only the decision step is skipped. |
| R6 | **Rejections by a gate whose name contains "late" were filed as lateness** in the candidate tables (`gate iv_late` → "late"). | Low | Gate reasons are classed first. |
| R7 | **The promotion day counted toward the new champion's record** (selection bias: the day that chose it was its first scored day). | Low | All "since" filters are strictly after the promotion day and the registration day. |

Of the reviewer's further concerns, these were acted on:
- **Engine pause ≠ feed pause.** If the *engine* stalls (OS sleep, a long GC) while the feed keeps writing, the futures quote is fresh but the engine's own price ring has a hole, and the stall move reads as a 15-s impulse. The guard now treats a hole in the engine's own sampling (> 10 s between steps; live steps are 100 ms) as a data gap. A 3-s hole cannot fake a 15-s impulse, and the simulator at 30× has 3–4 s scheduling holes, which an earlier 3-s threshold flagged dozens of times a day; at 10 s the drill day shows only the injected gap.
- **`futures_only` changed the exit too**: `s* = 0` made the THESIS-VOID exit fire on any opposite impulse. It now uses the champion's `s_exit = 0.5` so only the entry differs.
- **`random_entry` could take its side from a 1-min move spanning the gap**: it now waits for the first minute of settling.
- **The ledger followed candidates through blackouts**: following pauses during a blackout and the record is tagged `follow_gap`.
- **A champion in `state.json` that is no longer registered** hung the engine silently: it now falls back to the default champion with a log line.
- **Heavyweight prices of 0 (no quote yet)** counted as −100 % in breadth: masked.

Not acted on (judged minor): the momentum book's `armed` state is not persisted across a mid-day restart (a burst could be traded twice after a restart); VWAP books the gap's volume at the resume price.

The reviewer also confirmed what it could not break: controls and gated books can never become champion or challenger; the SPRT lines are the correct Wald form; no points/% unit mix beyond the documented legacy fallback; a random slot cannot fire twice; pending exits cannot be lost or double-closed; the incomplete-beta Student-t matches scipy.

## 5. Residual limitations (known, not fixed tonight)

- The guard watches the **futures** quote only. A partial outage in which the futures tick but the heavyweights freeze is not detected; the basket would read "no move" (synchrony 0), which fails the trigger safely, but a basket that freezes *then* jumps while the futures were live is not covered. Breeze delivers all subscriptions on one socket, so a partial freeze is unlikely; a per-stock staleness gate in the synchrony calculation is the next step if the live tick ages show otherwise.
- The regime label after a gap needs 15 minutes to rebuild its range (30-min window) and reads `broke = 0` meanwhile.
- The SPRT σ (10 %) is an assumption until ~30 live trades; the report prints the observed value.
- The simulator proves plumbing, not edge.
