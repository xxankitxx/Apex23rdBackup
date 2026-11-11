# 39. Operational fixes, research corrections, photograph v5, third shadow batch

10 Nov 2026. Answer to docs/38 and to the owner's instruction after the 9 Nov live session:
"There were operational issues today. I want you to correct them in the code so that they never ever happen again.
Also, then continue to do the other open items."

Status words used here. **Done** means in the code and pinned by a test. **Measured** means a number from a run that
is named. **Not done** means exactly that. Every research figure is discovery on the 15 recorded sessions unless it
says otherwise. Slippage and brokerage are ignored on the owner's instruction. Quote-aware means bought at the ask
and sold at the bid.

**The owner's requirement is not met.** The aim is no losing trade. No book and no signal in this document has that
property. Every table below that has a "lost" column shows losses.

---

## 1. The operational faults of 9 Nov and what now prevents each

| # | What happened on 9 Nov | What the code does now | Where | Test |
|---|---|---|---|---|
| 1 | The engine stood still for 0.9 to 6.5 s on every books save. Exits filled 3 to 6 s late. 36 owner releases lapsed, 27 of them after 12:05:08 | A closed trade is turned into text once and the text is reused. The disk write runs on its own thread. Day end and stop still write directly | `paper._books_chunks`, `paper.save_books_async`, `paper.ClosedTrade` | `tests/test_save_fast.py` |
| 2 | A failed background save would have been dropped and reported as idle. The direct save and the thread shared one temporary file. An older state could land after a newer one | A failed save is kept and retried until it is on disk. Each writer has its own temporary file. Every save carries a generation and an older one is thrown away | `paper` saver (docs/38 O3) | `tests/test_save_fast.py` |
| 3 | Nothing said where the time went | Every step is accounted by phase. A step over the limit writes a SLOW TICK line at once with the phase that took the time. Once a minute the log carries p50, p95, max and the largest phases | `engine_main` (`_lap`, perf log) | `test_slow_tick_is_logged_at_once_with_the_phase_that_took_the_time` |
| 4 | The supervisor stayed silent because every pause was under its 10 s limit | A pause shorter than the stale limit is reported when the heartbeat resumes | `run_apex.py` | `test_pause_under_the_stale_limit_is_reported_when_the_heartbeat_resumes` |
| 5 | A second Ctrl+C killed the engine inside its stop save and left a torn `.tmp` | The second press is ignored while the engine saves. The third forces and says so. A torn `.tmp` from a killed run is removed and logged at the next start | `run_apex.py`, `paper.load_books` | three Ctrl+C tests, `test_torn_tmp_of_a_killed_run_is_removed_and_logged_at_the_next_start` |
| 6 | The day was stopped at 15:32 and was neither closed nor learned | A flat book after the flatten time closes the day and runs the learning step on stop | `engine_main` | `test_stopped_flat_after_the_flatten_time_closes_and_learns_the_day` |
| 7 | Log lines carried a time and no date | Every line carries the date | `engine_main.LOG` | `test_every_log_line_carries_the_date` |
| 8 | A second-generation position lost its bracket on a restart. A model could speak on stale inputs | The bracket is fixed on the position at the fill. Each input (index future, depth, each stock) carries its own age. A model exit speaks only when the model is ready | `paper.gen_bracket`, `engine_main._gen2_feed`, `Gen2.ready` (docs/38 O4, O5) | `tests/test_gen2.py` |

"Never again" is a claim about the causes found. Fault 1 has been measured offline only. It has not yet been seen in a
live session. The check for the next live day is the "tick time" lines in `engine.log`.

### 1.1 Save and step time, measured

Books file of 9 Nov (7.7 MB), before photograph v5:

| Step | Time |
|---|---|
| Load the file | 218 ms |
| Text of all books, first time | 328 ms |
| Text of all books, cached, median | 12.5 ms |
| Text of all books, cached, worst | 31.3 ms |
| Full text without the cache | 266 ms |
| Async save, cost on the step, median | 12.0 ms |
| Async save, cost on the step, worst | 17.9 ms |
| Background flush to disk | 95 ms |
| Direct full save, as on 9 Nov | 297 ms idle, up to 6.5 s live |

New per-second work added today:

| Work | Median | 99th percentile | Worst |
|---|---|---|---|
| `Gen3.update` (one day of recorded seconds, 22,315 calls) | 0.17 ms | 0.76 ms | 2.4 ms |

Profiling replay of the whole 9 Nov tape (`data/replay/2026-11-09/20261110-011109`, port 8792, finished 03:22 on
10 Nov). It ran photograph v4 and gen2 VERSION 2 because it started before today's later changes. 244,670 engine
steps, mean 29.5 ms.

| Market time | Step p50 | Step p95 | Worst step | Steps over 300 ms | Steps over 1 s |
|---|---|---|---|---|---|
| 09:30 to 11:30 | 20 to 31 ms | 71 to 104 ms | 1,027 ms | 43 | 1 |
| 11:30 to 13:30 | 19 to 30 ms | 84 to 125 ms | 1,151 ms | 167 | 2 |
| 13:30 to 14:30 | 19 to 21 ms | 92 to 95 ms | 900 ms | 86 | 0 |
| 14:30 to 15:00 | 16 ms | 73 ms | 1,042 ms | 14 | 1 |
| 15:00 to 15:31 | 14 ms | 72 ms | 262 ms | 0 | 0 |

What it shows:

- **The afternoon slowdown does not come back.** After 14:51 the step is faster than in the morning. On the live day
  the pause grew with the books file all day. With the save fix it does not grow. This points to the save freeze as
  the cause of the afternoon slowdown as well. It is a replay, not a live session.
- **Four steps in the day still took over 1 s and 310 took over 300 ms.** Every one is in the books phase, at a
  moment when about ten or more books trade in the same step. Each such book costs 40 to 80 ms. I take that to be its entry
  photograph, which was not timed on its own. In this replay the books file is also written directly inside the step (a fast replay does not use the
  writer thread), which is 250 to 700 ms of the worst steps. Live, that part is off the step.
- Save lag was 0 all day. 1,440 saves requested by 14:31, 1,440 on disk, no errors.
- The recorded tape ends at 15:32:52 with a cut gzip stream, from the kill on 9 Nov. The replay read to the cut,
  closed the day and learned it.

**Still open:** a step of up to about 0.7 s when many books enter together. It is under the 3 s fill window, so it
does not lapse an entry, but it is not fixed. Sharing one photograph build across the books of a step would remove
most of it. That change is not made.

**Not measured:** save and step time with the v5 fields, `weather_hold` and the four new books in a full engine run.
That needs a replay, and a replay needs the owner's word.

---

## 2. Research corrections (docs/38 Phase 1 and 2)

Conventions of research v2: signal at t, entry at the ask one second later, exit at the bid, horizon 120 s, 15 dates
in 22 recorded parts. The 9 Nov results in docs/37 Part B used other conventions. They are kept as they were and are
not comparable with these.

Corrections to docs/37: the champion lapsed on **27** entries after 12:05:08, not 26. "Without the big trade" has two
figures: +₹4,907.50 at the quantities actually traded, and −₹110.50 when every trade is recomputed all-in from the
capital it would then have had.

### 2.1 N03 path signature

| Variant | Picks | Mean | Note |
|---|---|---|---|
| endpoints | 149 | −2.51 % | |
| lags | 180 | −1.23 % | |
| sig2 | 175 | +4.93 % | −0.50 % without the best pick |
| sig2, order shuffled | 179 | +3.34 % | the control catches the same pick |

Split by the engine's own entry window:

| sig2 | Picks | Sum |
|---|---|---|
| Inside the window the engine can trade | 148 | −29.2 % |
| Outside it | 27 | +892.5 % |

All 6 picks above +50 % are on expiry days after 15:20. The largest is 9 Nov 15:24:55, CE 25050, ask 2.20 to bid
23.10. The engine does not enter then. **N03 has no edge it could have traded.**

### 2.2 N04 cross-strike lead

268,728 rows. Median spread of the target strike 0.25 points.

| Signal | Signals | Rank IC with the later mid, 1 s | Same, 30 s | Quote-aware mean return |
|---|---|---|---|---|
| neighbours minus own | 767 | 0.081 | 0.021 | −0.48 % to −0.93 % |
| own momentum | 850 | negative | negative | −0.24 % to −0.66 % |
| raw cross average | 801 | 0.050 | | negative at every delay and horizon |

The neighbours do tell something about the next mid. The fill costs 0.36 points over the signal mid and that is more
than the information is worth. **No tradable edge.**

### 2.3 N05 surface

| Model | Picks inside the window | Sum | Non-expiry days only |
|---|---|---|---|
| surface | 138 | +228.3 % | −51.7 % |
| IV momentum alone | 134 | +185.1 % | −12.7 % |

The surface never beats IV momentum in a paired comparison. **Not supported.**

### 2.4 Gen2 VERSION 3 (docs/38 O6)

N01's response is fitted on the pressure window itself. The absorption test is two-sided. Confirmation re-checks
strength and sign. `n01_ctl_price_ind` is a price-only control that runs outside the flow model's gate. N02 records
fit diagnostics. VERSION 3 has **not** been replayed. The 9 Nov live results belong to VERSION 2.

---

## 3. Photograph v5

Entry photograph: 114 items (1 to 104, and 105 to 110, 120 to 122, 128).

| Item | Name | Unit and sign | When it is None |
|---|---|---|---|
| 105 | Engine service delay | ms and s, no direction | no step history yet |
| 106 | Persistence health | ms, counts | no save yet |
| 107 | Cross-input synchronisation | s between input ages | an input never seen |
| 108 | Fresh weighted coverage | share of index weight, 0 to 1 | no heavyweights |
| 109 | Flow-sign uncertainty | share of volume, 0 to 1 | gen2 off or not warm |
| 110 | Response-model reliability | fit quality, counts | gen2 off or not warm |
| 120 | Opportunity survival | s, counts of earlier requests | first request of the book |
| 121 | Contract-path continuity | s, counts | contract not seen before |
| 122 | Fill evidence | points, s | no print |
| 128 | Research lineage and support | text, dates | never |

Nothing is flipped for a put. A field that cannot be measured is None, and `v5_missing` says why by item number.

**The one exception to "every item is searched":** 13 fields (`search.TELEMETRY`: the millisecond fields of 105, all
of 106, three text fields of 128) are recorded and mapped but kept out of the nightly rule search. They describe the
machine, differ between a live run and a replay of the same tape, and docs/38 says they are not trade gates.

Continuation photograph (items 123 to 126), stored on the trade as `weather_hold`, never in the entry photograph and
never in the search:

| Item | Name | Fields |
|---|---|---|
| 123 | Held gain maturity | 7 |
| 124 | Held giveback dynamics | 7 |
| 125 | Held premium attribution | 4 |
| 126 | Live thesis disagreement | 6 |

Snapshots at 60, 300, 900 and 1,800 s of age, at the exit request, and at the close when there was no request.
`tests/test_weather_v5.py`, 9 tests.

Coverage of the docs/38 item list (105 to 128, 24 items): **14 built** (105 to 110, 120 to 126, 128). **10 not
built**: 111 to 119 and 127.

---

## 4. S01 and S02: capability check and first look

`data/replay/batch/gen2_research_v2_2026-11-10/s01_s02_check.py`. All 22 parts, 14 stocks, 14 stock futures.

| Capability | Result |
|---|---|
| Weight with fresh cash and a fresh two-sided stock-futures quote, median by part | 0.92 to 1.00 |
| Same, 10th percentile | 0.63 to 1.00 |
| Seconds with at least half the weight paired | 0.92 to 1.00 |
| Stock-futures quote age, median | about 0.5 s |
| Strikes near the forward with both sides fresh, near week and next week, median | 5 of 5 (3 to 4 on the 29 Oct parts) |
| Next-week ATM straddle available | 0.993 to 1.00 of seconds |

Both pass the capability check.

S01 first look. Mean daily rank correlation with the Nifty future's mid move from t+1, rows 10 s apart:

| Quantity (30 s window) | 30 s ahead | Days positive |
|---|---|---|
| Stock futures minus cash, raw | −0.024 | 2 of 15 |
| Cash basket alone | 0.110 | 15 of 15 |
| Stock-futures basket alone | 0.108 | 15 of 15 |
| Nifty future's own move | 0.055 | 15 of 15 |
| Stock-futures move not explained by cash and the index, coefficients from earlier days | 0.112 | 10 of 10 |

The last row is 0.092 at 60 s and 0.061 at 120 s, 10 of 10 days each.

**Correction made after the first run, and labelled in the file:** the first run regressed the raw gap on cash and on
stock futures together. The gap is exactly their difference, so the result was rounding noise. The second run takes
out cash and the index's own move only. The first output is kept as `results_s01_s02_check_run1.txt`.

S02 first look. Target: the near-week straddle's change. Raw next-week variance change −0.01 to −0.02. Near-week
control −0.03 to −0.05. The part the control does not explain 0.018 to 0.031, positive on 7 to 9 of 10 days. That is
small and it is about the straddle, not about one leg. docs/38: "If the model predicts volatility magnitude but no
defensible one-leg opportunity, abstain." **S02 is not built.**

---

## 5. Third shadow batch: `apex/engine/gen3.py`, VERSION 1

Shadow only. Not in the pool. Cannot be champion. gen2 stays frozen at its own version. 99 books in all (was 95).

| Book | Signal | What it is |
|---|---|---|
| `s01_transmit` | `s01_trans` | S01, new candidate |
| `s01_ctl_cash` | `s01_ctl_cash` | control: the cash basket's 30 s move alone |
| `s01_ctl_sfut` | `s01_ctl_sfut` | control: the stock-futures basket's 30 s move alone |
| `s03_recruit` | `s03_recruit` | S03, a redesign of N06. Its control is the frozen `n06_ctl_breadth` |

### 5.1 Frozen manifest (`gen3.P`, hash `6fc9150866a1`, pinned in `tests/test_gen3.py`)

All returns are over 30 s. An input older than 5 s is stale (3 s for the index future). At least 70 % of heavyweight
weight must have fresh cash and a fresh stock-futures quote at both ends of the window. 120 s of clean data before
any signal. A hole of more than 5 s restarts everything.

S01. z = stock-futures basket move − 0.4554 × cash basket move − 0.4359 × Nifty future's move, in index points.

| Rule | Value |
|---|---|
| Entry | absolute z at least 7.0 points |
| and | the cash basket's last 10 s is with the signal |
| and | the index has moved less than 10 points with the signal in the window |
| Re-arm | absolute z below 3.5 |
| Exit | target 12, stop 10 futures points, 120 s |
| Thesis exit | z at least 3.5 the other way, or coverage below 50 % |
| Controls | cash move at least 22.9 points, stock-futures move at least 21.0 points, same bracket |

S03. b = weight up minus weight down over fresh weight, on cash prices.

| Rule | Value |
|---|---|
| Entry | absolute b at least 0.60 |
| and | b has moved at least 0.80 with the direction in 30 s, and did not fall back at 10 s or 20 s |
| and | the same breadth on the stock futures at least 0.50 the same way |
| and | the Nifty future has moved at most 6 points in the window |
| Re-arm | absolute b below 0.30 |
| Exit | target 12, stop 10 futures points, 300 s |
| Thesis exit | breadth 0.20 against the trade |

Where the numbers came from: `s01_s03_calib.py`, 310,025 rows, **signal side only**. One regression of the
stock-futures basket on cash and index, and percentiles of each quantity. No later price was read to choose a number.
7.0 is near the 99th percentile of absolute z (7.24). 22.9 and 21.0 are the 99th percentiles of the two controls.
The 15 sessions are still discovery material for these signals because the coefficients came from them.

### 5.2 Signals per day and a futures-level first look

`gen3_offline.py` feeds the engine's own `Gen3` class from the recorded seconds. Entry at the Nifty future's mid one
second later. The signal's own target, stop and clock. No thesis exit. **No option quote is read. This is not a P&L
and says nothing about a one-leg option trade.**

| Signal | Signals | Per day | Won | Lost | Sum, futures points | Mean | Days positive |
|---|---|---|---|---|---|---|---|
| s01_trans | 402 | 26.8 | 205 | 197 | +286.4 | +0.71 | 8 of 15 |
| s01_ctl_cash | 293 | 19.5 | 159 | 134 | +541.5 | +1.85 | 10 of 15 |
| s01_ctl_sfut | 255 | 17.0 | 127 | 128 | +202.0 | +0.79 | 8 of 15 |
| s03_recruit | 2,186 | 145.7 | 1,155 | 1,031 | +3,487.1 | +1.60 | 15 of 15 |

Reading, plainly:

- **S01 does not beat its cash control.** The rank correlation in section 4 did not turn into a better threshold
  signal. On this evidence S01 is not supported.
- **S03 is positive on all 15 days at the futures mid, and loses 1,031 times out of 2,186.** A mean of 1.6 futures
  points is about 0.8 option points at the money. The option's spread and the entry delay are of the same size, so
  this may vanish through real quotes. The frozen breadth control was also positive on 15 of 15 days in docs/37. S03
  has not yet been compared with it at matched occupancy.
- S03 fires 146 times a day before the book's 60 s cooldown and one-position rule. The book will take far fewer.
- No threshold was moved after seeing these numbers.

### 5.3 Coverage of the six docs/38 shadows

| Shadow | Status |
|---|---|
| S01 cash-futures transmission | **Built**, with both controls. First look does not support it |
| S02 cross-expiry shock | **Not built.** Capability passes. No one-leg forecast found, so docs/38 says abstain |
| S03 breadth recruitment | **Built.** Positive at the futures mid, not yet tested through option quotes or against its control at matched occupancy |
| S04 premium-response residual | **Not built.** N04 and N05 both failed quote-aware in v2. A redesign has no basis yet |
| S05 gain-maturity exit twin | **Not built.** The engine has no matched-entry twin mechanism. The continuation photograph now records what it would need |
| S06 scale-transition entry twin | **Not built.** Needs items 118, 114 and 115, which are not built |

2 of 6 built. 4 of 6 not built.

---

## 6. All specifications tried today

| # | Specification | Kept |
|---|---|---|
| 1 | N03 endpoints, lags, sig2, sig2 shuffled, v2 conventions | reported, rejected |
| 2 | N03 split by engine entry window and expiry audit | reported |
| 3 | N04 neighbours minus own, own momentum, raw cross average, delays 1 to 30 s | reported, rejected |
| 4 | N05 surface against IV momentum, frozen and paired | reported, rejected |
| 5 | S01 raw gap, three controls, residual on cash and stock futures (run 1, wrong) | kept as run 1, labelled |
| 6 | S01 residual on cash and index momentum (run 2) | reported |
| 7 | S02 raw, near-week control, residual | reported, not built |
| 8 | S01 and S03 signal-side calibration, cover 0.7, four S03 threshold pairs counted by occupancy only | (0.6, 0.8) frozen |
| 9 | gen3 VERSION 1 offline feed | reported |

Training cutoffs: every residual coefficient in section 4 uses earlier days only, at least 5. The gen3 coefficients
use all 15 sessions, signal side only.

---

## 7. docs/38 report tables: what exists and what does not

| Table | Status |
|---|---|
| Per-day won, lost, P&L | futures-level only, per day, in `gen3_offline.json`. Not a P&L |
| Clustered opportunities | item 120 records it from now on. No table yet |
| Missed and rejected winners | not done |
| Source and exit comparison | not done |
| Continuation failures | `weather_hold` records from now on. No table yet |
| Freshness and readiness coverage | section 4 |
| Latency and persistence lag | section 1.1, partial |
| All tried specifications | section 6 |
| Training cutoffs | section 6 |
| Trade-level attribution | not done, needs replays |
| Strata: expiry, time of day, interrupted or clean | N03 only |
| Account contribution: alone, pool, pool plus candidate, leave one out | not done, needs replays |

---

## 8. Tests

`tests/test_gen3.py` 10 tests: registration, frozen manifest hash, warm-up, each entry condition, both controls,
stale inputs and gaps, thesis exits, causality, the book plumbing. The two tests that pin the book count now say 99.

---

## 9. Not done

1. A step of up to about 0.7 s live (1.15 s in the replay) when ten or more books enter in the same step. The
   afternoon slowdown itself did not reproduce with the save fix. Neither statement has been checked live.
2. No engine replay of gen2 VERSION 3 or gen3 VERSION 1. So: no option-quote result, no per-book trades, no account
   contribution, no matched-occupancy comparison of S03 with its control. Each day takes about two hours.
3. Step and save time with v5, `weather_hold` and 99 books in a full engine run.
4. Weather items 111 to 119 and 127. S02, S04, S05, S06.
5. N02 constrained against unconstrained, offline.
6. The 9 Nov back-fill into the learning state is not confirmed by a test.
7. The tables marked "not done" in section 7.
8. Nothing has run live with any of today's changes.
