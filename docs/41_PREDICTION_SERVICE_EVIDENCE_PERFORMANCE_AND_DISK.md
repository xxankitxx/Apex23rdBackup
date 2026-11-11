# 41. The prediction service: what was built, what the evidence says, performance, disk

10 Nov 2026. Answer to docs/40 and to the owner's request of the same day: tell the champion's good trades from its
bad ones, forecast direction and how fast an option will move, keep improving from real evidence, build shadow books
on that idea, find what slows the live engine, and free disk space without losing captured data.

Status words. **Built** means in the code and pinned by a test. **Measured** means a number from a named run.
**Not done** means exactly that. Slippage and brokerage are ignored on the owner's instruction, but every option
result here is still quote-aware: bought at the ask one second after the forecast, marked and sold at the bid.

**The owner's aim, no losing trade, is not met by anything in this document.** The best line found loses 56 trades
out of 131. Every table with a "lost" column shows losses.

---

## 1. The short answers

| Question | Answer from today's evidence |
|---|---|
| Can the stored weather fields tell the champion's winners from its losers? | **No.** On later days a model fitted on earlier days was worse than a coin (section 4.1) |
| Can the new forecast tell them apart? | **No.** 64 scored entries, no separation (section 4.2). It is recorded on every champion-family entry from now on |
| Can the system forecast how fast an option will move? | **Yes, clearly.** Whether a 5 % move comes inside 30 or 60 s is forecast well on unseen days (section 3.1) |
| Can it forecast which way? | **Only slightly.** Among moves that happened, the forecast picks the side a little better than a coin: 0.53 against 0.50 (section 3.2) |
| Does that make a tradable book? | **One lead, not proven.** The strictest forecast line inside trading hours: 131 trades on 10 unseen days, 75 won, 56 lost, +0.93 % a trade, positive on 10 of 10 days. The wider line was flat (section 3.4) |
| Does learning during the day help? | **Not on this evidence.** The calibrator that learns only from finished outcomes was slightly worse than the frozen forecast (section 3.5). It runs as a shadow so live evidence can overrule this |
| What slows the live engine? | Other jobs on the same machine (measured today: 3 to 4 times slower, up to 17 times at the worst), the save freeze (fixed 9 to 10 Nov), and bursts when many books enter in one step (not fixed). Section 7 |
| Disk | The repository is 4.5 GB of the 206 GB used on drive D. 93 MB freed safely. The large users are other folders (section 8) |

---

## 2. What was built

One shared prediction service, not one model per book.

| Part | File | What it does |
|---|---|---|
| Features | `apex/predict/features.py` | 33 causal numbers each second, the same code offline and in the engine. Schema `0ede257aeb7d` |
| Targets | `apex/predict/targets.py` | Fixed-contract labels with competing events and gaps |
| Models and scores | `apex/predict/models.py` | Regularised logistic model as a plain file, calibrator, Brier, AUC, reliability |
| Forecaster, ledger, maturity queue | `apex/predict/ledger.py` | Loads a frozen file, writes every forecast once, releases an outcome only when it has finished |
| Frozen model | `apex/predict/model_v1.json` | Eight models, hash `88c09e8db35f`. No fitting at run time |
| Shadow signals | `apex/engine/pred.py` | Four signals, forecast exit, admission record |
| Engine wiring | `engine_main._pred_feed`, `_pred_note`, `paper._gen_src`, `paper._gen_exit` | Once a second, observer only |

### 2.1 Features (all from data received before the second)

Directional features are multiplied by the trade's direction, +1 for a call and −1 for a put, so "with the trade" is
positive for both and one model serves both rights. A feature that cannot be measured is missing, never guessed.

| Group | Features | Unit |
|---|---|---|
| Index future's move | mom5, mom15, mom30, mom60, mom180, mom300 | futures points, signed |
| Breadth | br30 (cash), brsf30 (stock futures) | weighted share up minus down, signed |
| Baskets | cash30, sfut30, z30 (the S01 residual) | index points, signed |
| Range | rngpos | position in the 15-minute range, signed |
| Order flow | flow30, flow120, dimb, dimb30 | signed traded quantity over depth; depth imbalance |
| Volatility | rv60, rv300, strad60, strad300 | points per second; straddle change in % |
| State | fspread, tod, dte, expd | points; share of the session; days; flag |
| The contract | prem, spread_pct, mny, om10, om30, om60, lag30, opp30, prem_strad | premium; % of premium; moneyness |

Freshness: index future and option quotes 3 s, stocks and stock futures 5 s, 70 % of heavyweight weight fresh at
both ends of a window, 300 s of history before anything is called ready. A hole of up to 5 s does not restart the
warm-up; a window whose far end falls in a hole is missing.

### 2.2 Targets (declared before any result)

The contract chosen at the forecast is kept for the whole label. Entry at the ask one second later, from a quote
received after the request. Every later mark is the bid.

| Event inside the horizon | Meaning |
|---|---|
| T | the bid reached +5 % of the entry premium first |
| A | the bid reached −5 % first |
| N | neither |
| U | unobservable: no usable bid for more than 10 s, or the data ended, before any event |
| L | no fill at all |

Horizons 30, 60, 180 and 300 s. A gap is neither a stop nor a win. The frozen exit policy the forecast is about:
sell at +5 %, at −5 %, or at 300 s.

### 2.3 The forecast record

Every forecast is written once to `forecasts_<day>.jsonl` with its sequence number, time, contract, the 33 features,
the eight probabilities, model hash, training cutoff, feature schema, target spec, the decision and the reason.
Fills, exits and outcomes are later lines in `outcomes_<day>.jsonl` that point at it. Nothing edits a forecast. A
restart continues the sequence. Four forecasts are sampled every 15 s whether or not anything trades, so the record
is not only of trades the system chose.

### 2.4 Tests

`tests/test_predict.py` 12 tests and `tests/test_pred.py` 8 tests: warm-up and holes, sign and causality of the
features, each target case including gaps and lapses, the policy exit, a planted signal is learned, the forecast is a
proper distribution, the ledger is append-only and survives a restart, only finished outcomes come out and each
once, the queue is bounded, silence without a usable model or fresh inputs, one signal per arming, the book plumbing
and both exits. Full suite after the wiring: 506 passed, 8 skipped, 5 expected failures, 2 failed, 1 error. The two
failures are the commentary speed tests, which fail on a loaded machine. The error is the data fence seeing the
running replays. Neither was re-run on an idle machine.

---

## 3. Forecast evidence on the unselected population

`data/replay/batch/predict_2026-11-10/`. 216,029 forecast origins over 15 sessions: every 5 s, the at-the-money call
and put and the first in-the-money call and put of the near week. Each test day is forecast by models fitted on
earlier days only, at least 5, so there are 10 test days. All of it is discovery material.

Three runs were made and all three are kept:

| Run | Change | Kept in |
|---|---|---|
| 1 | first build, 29 features, any hole restarts the warm-up | `run1/` |
| 2 | holes up to 5 s tolerated; numerical fault in one fit fixed | `run2/` |
| 3 | four order-flow and depth features added (33) | the folder itself |

### 3.1 How fast: will a 5 % move come, and when (run 3)

| Target | Rows | Base rate | AUC | Brier | Brier of the base rate | Skill | Test days with skill |
|---|---|---|---|---|---|---|---|
| +5 % first within 30 s | 149,227 | 9.3 % | 0.851 | 0.0716 | 0.0863 | 17.0 % | 9 of 10 |
| +5 % first within 60 s | 148,425 | 15.9 % | 0.797 | 0.1133 | 0.1366 | 17.0 % | 9 of 10 |
| +5 % first within 180 s | 145,923 | 30.3 % | 0.663 | 0.1978 | 0.2133 | 7.3 % | 9 of 10 |
| +5 % first within 300 s | 144,493 | 36.6 % | 0.607 | 0.2253 | 0.2333 | 3.4 % | 8 of 10 |
| −5 % first within 30 s | 149,227 | 10.9 % | 0.848 | 0.0797 | 0.0993 | 19.8 % | 10 of 10 |
| −5 % first within 60 s | 148,425 | 18.7 % | 0.786 | 0.1268 | 0.1558 | 18.6 % | 9 of 10 |
| −5 % first within 180 s | 145,923 | 35.7 % | 0.651 | 0.2158 | 0.2320 | 7.0 % | 8 of 10 |
| −5 % first within 300 s | 144,493 | 42.9 % | 0.589 | 0.2399 | 0.2464 | 2.6 % | 7 of 10 |

Among origins that did reach +5 % within 300 s (52,898), the forecast's share of that chance placed inside 30 s
ranks the real arrival time with a rank correlation of −0.65. The quarter it called fastest arrived in a median of
21 s, the quarter it called slowest in 134 s.

**Read this carefully.** Most of this skill is knowing when premiums are jumpy: expiry days, cheap premiums, high
recent movement. On expiry days a 5 % move inside 30 s happens 20 to 33 % of the time, on other days 1 to 5 %. The
forecast knows that. It is a forecast of speed and size, and it predicts a fast loss as well as a fast gain.

### 3.2 Which way

| Test | Result |
|---|---|
| Among origins where one barrier was hit within 300 s, does the edge (P target − P adverse) pick the target-first ones? Mean AUC inside each day | 0.533, above 0.5 on 7 of 10 days |
| Same, run 2 | 0.538, 8 of 10 |
| Same, run 1 | 0.531, 7 of 10 |
| Index future more than +5 points in the next 60 s (base 26.2 %) | AUC 0.582; momentum alone 0.50 |
| Index future more than −5 points in the next 60 s (base 22.7 %) | AUC 0.607; momentum alone 0.50 |

The two index rows again mostly measure movement, not side: the same features raise the chance of a rise and of a
fall. The honest direction number is the first row: 0.53. Order-flow and depth features did not raise it.

A non-linear model (gradient boosting, depth 3, 200 trees) was tried in runs 1 and 2: AUC 0.598 against 0.609, side
AUC 0.52 to 0.53, and its trading check lost. It is not used.

### 3.3 What the model leans on

Largest weights of the 300 s target model: premium −0.40, spread −0.32, the option's own 30 s move −0.19, its 60 s
move +0.17, recent movement +0.16, time of day −0.13, position in the range +0.11, 120 s order flow +0.10. For the
adverse model the largest is the spread, +0.56: a wide spread means you start in the hole. So the edge says: tight
spread, the option paused over the last 30 s inside a move that has run for a minute, with the 15-minute trend.

### 3.4 Trading check: one position at a time, enter on the forecast, exit by the frozen policy

Two entry lines were declared before the first run: the 95th and the 99th percentile of the edge in the training
days. 10 test days. Returns are per cent of premium, quote-aware.

| Line | Trades | Won | Lost | Mean per trade | Standard error | Days positive |
|---|---|---|---|---|---|---|
| Run 3, top 5 %, all hours | 865 | 438 | 427 | +0.05 % | 0.23 | 4 of 10 |
| Run 3, top 5 %, entries before 15:15 | 778 | 386 | 392 | −0.06 % | 0.21 | 4 of 10 |
| Run 3, top 1 %, all hours | 153 | 89 | 64 | +1.19 % | 0.65 | 10 of 10 |
| **Run 3, top 1 %, entries before 15:15** | **131** | **75** | **56** | **+0.93 %** | **0.49** | **10 of 10** |
| Run 2, top 5 %, all hours | 1,105 | 563 | 542 | +0.12 % | 0.21 | 7 of 10 |
| Run 2, top 5 %, entries before 15:15 | 995 | 500 | 495 | +0.00 % | 0.19 | 4 of 10 |
| Run 2, top 1 %, all hours | 433 | 235 | 198 | +0.61 % | 0.36 | 8 of 10 |
| Run 1, top 5 %, all hours | 1,123 | 585 | 538 | +0.27 % | 0.20 | 6 of 10 |
| Run 1, top 1 %, all hours | 400 | 212 | 188 | +0.31 % | 0.37 | 7 of 10 |
| Control, run 2: 30 s momentum, top 5 % | 932 | 423 | 509 | −0.41 % | | 3 of 10 |
| Control, run 2: 30 s momentum, top 1 % | 251 | 114 | 137 | −0.51 % | | 4 of 10 |
| Control, run 3: every origin before 15:15 | 2,986 | 1,468 | 1,518 | −0.04 % | 0.11 | 4 of 10 |

Reading:

- **The 5 % line has no edge inside trading hours.** Its gain in runs 1 and 2 came from the last 15 minutes, when the
  engine does not enter. The "entries before 15:15" rows were added after run 1's day table showed that, so they are
  a diagnosis, not a pre-declared test.
- **The 1 % line was positive in all three runs** and, in run 3, on all 10 test days inside trading hours. It is 13
  trades a day, wins 57 %, and its mean is about two standard errors from zero. It is a lead. It is not proof, and
  it is three looks at the same 10 days.
- Momentum alone loses. So the forecast is choosing better moments than the obvious rule.
- Nothing here is all-in account P&L and nothing has been through the engine.

### 3.5 Learning during the day (docs/40 stage C)

A calibrator that receives a forecast's outcome only after fill + 300 s + 10 s, against the same frozen model, on
144,493 forecasts in time order (run 2):

| | Brier | AUC |
|---|---|---|
| Frozen forecast | 0.22482 | 0.609 |
| With the matured-only calibrator | 0.22583 | 0.597 |
| Base rate | 0.23330 | |

It did not help. The mechanism is built and correct (a test pins that no label enters early), and it runs live as a
shadow beside its frozen twin, which is the comparison docs/40 asks for.

---

## 4. The champion's winners and losers

### 4.1 From the weather photograph

`champ_separation.py`. 119 champion-family entry episodes over 14 replay days (siblings entering together are one
episode): 69 won, 25 reached +5 % and gave it back, 25 never developed. 227 numeric photograph fields. Each test
day used a model fitted on earlier days only: the best 3 or 8 fields by rank correlation, then a logistic model. 100
label shuffles per specification.

| Target | Fields | AUC on later days | Shuffle p | Upper half by the model | Lower half |
|---|---|---|---|---|---|
| Won | 3 | 0.31 to 0.32 | 0.98 | 44 % won | 74 % won |
| Won | 8 | 0.26 to 0.27 | 1.00 | 38 to 41 % won | 77 to 79 % won |
| Reached +5 % | 3 | 0.51 | 0.50 to 0.55 | | |
| Reached +5 % | 8 | 0.34 to 0.38 | 0.87 to 0.96 | | |
| Runner (a sibling made 20 %+) | 3 or 8 | 0.44 to 0.55 | 0.15 to 0.70 | | |

**No separation.** For "won" the model was reliably wrong: what marked winners on earlier days marked losers on
later ones. That is the photograph's relations changing between weeks, which is exactly why R-019 and R-020 failed
on their first live day. Trading the opposite of the model would be fitting to this result and is not proposed.
68 scored episodes is very little.

### 4.2 From the forecast (P01 `forecast_select`, off-policy)

`champ_forecast.py`. The forecast for each entry comes from models fitted on unselected origins of earlier days
only. 131 episodes including the 12 live trades of 9 Nov. 64 could be scored; 29 fall in the first 5 days and 38
had no ready features or no fresh quote at the trigger second.

| Score | Won (38 of 64) | Reached +5 % (50 of 64) | Runner (16 of 64) |
|---|---|---|---|
| Edge | AUC 0.39 | 0.37 | 0.47 |
| P target first, 300 s | 0.52 | 0.57 | 0.52 |
| P target first, 60 s | 0.56 | 0.61, shuffle p 0.10 | 0.57 |

| Split | Entries | Won | Lost | Sum of returns | Runners kept |
|---|---|---|---|---|---|
| Upper half of edge | 32 | 16 | 16 | +208.1 % | 9 |
| Lower half of edge | 32 | 22 | 10 | +186.1 % | 7 |

**No separation.** A forecast gate on the champion would not have helped and would have cost runners. The champion
enters when movement is high, which is where the forecast sees high risk on both sides: its edge is negative on all
12 live trades of 9 Nov, including the +64.9 % one (edge −0.04) and the −12.5 % one (edge −0.17).

So P01 is **not built as a gate**. It is built as a record: at every champion-family fill the engine writes the
forecast to the ledger and puts five numbers on the position (`fc`). After some live weeks the question can be
asked again with far more than 64 entries.

The three different problems docs/40 names stay open: entries that never develop (25 of 119), gains given back
(25 of 119), and runners cut early. The continuation photograph (docs/39) records the second and third from now on.

---

## 5. The frozen model

`apex/predict/model_v1.json`, hash `88c09e8db35f`, fitted by `make_artefact.py` on all 15 sessions. Those sessions
are therefore discovery material for it. **Its first honest test is the next live session or a tape recorded after
9 Nov.**

| Line | Value | Where it comes from |
|---|---|---|
| Entry line | edge at least +0.0404 | 95th percentile of the edge on the training origins |
| Strict entry line | edge at least +0.0794 | 99th percentile |
| Exit line | edge below −0.0631 | median |
| Momentum control | 30 s move at least 13.5 points | 95th percentile of its absolute value |

If the file is missing, was fitted on another feature schema or another target spec, every signal is silent and
says why. There is no fallback model.

---

## 6. Prediction-driven shadow books (`apex/engine/pred.py`, VERSION 1)

Shadow only. Not in the pool. Cannot be champion. 103 books in all (was 99); 105 with the two twins of section 12.4.

| Book | Entry | Exit | Status |
|---|---|---|---|
| `p02_clock` | the best edge of the four contracts at or above the entry line | +5 % / −5 % of the entry premium on the bid, 300 s, or the held contract's edge below the exit line | pre-declared line; flat in the offline check inside trading hours |
| `p02_top1` | same, strict line | same | the lead of section 3.4. The book was added after the runs were seen |
| `p02_ctl_mom` | control: 30 s futures momentum at its own line, same sampler | same bracket, no forecast exit | lost in the offline check |
| `p05_adaptive` | as `p02_clock` but on the edge after the matured-only calibrator | same | its frozen twin is `p02_clock` |

One signal per arming: a name speaks again only after 60 s and after its score fell below the line.

Coverage of the five docs/40 roles:

| Role | Status |
|---|---|
| P01 forecast_select | **Record only**, on every champion-family fill. Not a gate: the off-policy test does not support one |
| P02 forecast_clock | **Built**, with its control and the strict variant |
| P03 forecast_runner | **Built** in the evening as `fr_c20_9y`, a twin of c20_9y (section 12.4) |
| P04 forecast_exit | **Built** in the evening as `fx_c20_9y`, a twin of c20_9y (section 12.4). Also works for the forecast books' own positions |
| P05 adaptive_calibration | **Built**, as a shadow beside its frozen twin |

Known limits of VERSION 1:

- The book buys the contract the engine's own strike rule picks for the direction. The forecast was made for the
  at-the-money or first in-the-money strike. When they differ, or the engine picks next week, the premium bracket
  still applies but the forecast exit is silent.
- The forecaster covers the near week only.
- The strike grid is fixed at the first second of the day, 30 strikes each side.

Cost, measured: the service's update took a median of 14.8 ms on a machine that was running the gen3 update at
1.92 ms against 0.166 ms on the idle machine last night. That ratio, 7.7, puts it at about **1.3 ms per second on
an idle machine**. It has not been timed on an idle machine. The ledger of one recorded day was 5.8 MB of forecasts
and 1.3 MB of outcomes at one sample every 5 s; the engine samples every 15 s, so about a third of that.

---

## 7. What slows the engine

### 7.1 Measured

| Cause | Evidence | State |
|---|---|---|
| The books save froze the engine 0.9 to 6.5 s | 9 Nov live log | **Fixed** 9 to 10 Nov (docs/39). Replay of 9 Nov: save lag 0 all day, afternoon faster than morning |
| Other jobs on the same machine | 10 Nov: with four replays and research jobs running, the same gen3 update took 1.9 to 2.9 ms against 0.166 ms the night before, 12 to 17 times slower. The replays' own step went from a median of 20 to 30 ms to 70 to 175 ms | **Guarded** (7.3). Not fixable in the engine alone |
| Many books entering in one step | Profile replay of 9 Nov: 4 steps over 1 s and 310 over 300 ms in the day, all in the books phase | **Not fixed** |
| The missed-signal recorder | 8 to 31 ms a tick in busy minutes of today's batch, one spike of 1,045 ms | Replays only. It is off in a live session |

Where a clean step spends its time (profile replay of 9 Nov, photograph v4, 244,141 steps, 7,208 s in all):

| Phase | Seconds | Share |
|---|---|---|
| Market state | 1,431 | 20 % |
| Books | 1,243 | 17 % |
| Greeks | 1,023 | 14 % |
| Before the books | 794 | 11 % |
| Guard, domino, regime | 649 | 9 % |
| Publish to the dashboard | 640 | 9 % |
| Context | 624 | 9 % |
| Weather base | 382 | 5 % |
| Once-a-second work | 305 | 4 % |

The mean step was 29.5 ms against a 100 ms loop. No single phase is the bottleneck in a normal step. Inside the
books phase the timed single books add up to only 89 s of the 1,243: the cost is spread over 87 books on every tick.
The rule-restricted books, which build a photograph each time their rule is checked, cost 13 s in the day, so they
are not the problem I first suspected.

### 7.2 Suspected, not measured

docs/40 lists these and they stand as suspects: repeated photograph construction when books trigger together,
`weather4._p_books` walking every other book's closed trades for each photograph, synchronous SVI fitting every
60 s, the dashboard publish on the engine thread, the 30 s warm-state checkpoint. **None has been timed on its own.**
A function-level profile needs an idle machine and a short replay. That was not possible today.

The photograph was not split into a shared part and a per-book part. docs/40 is right that a careless cache would
change what a book sees, and it is a refactor of about 1,500 lines that needs an equivalence test first.

### 7.3 Changed in code today

| Change | Where | Test |
|---|---|---|
| In a live session the feed and the engine run above normal priority, so other work on the machine waits for them | `run_apex.spawn_flags` | `test_the_live_feed_and_engine_run_above_normal_priority_and_nothing_else_does` |
| At a live start the launcher lists replay, test and research processes that are running and says to stop them | `run_apex.busy_python`, `supervise` | same test |

**Not measured: the step time of the present configuration (photograph v5, continuation photograph, 103 books) on an
idle machine.** Today's batch cannot give it because the machine was overloaded throughout.

---

## 8. Disk

Drive D: 206 GB used, 24.6 GB free. The repository is 4.5 GB of that.

| Inside the repository | Size | Treatment |
|---|---|---|
| Recorded market tapes | 3.2 GB | Kept. Cannot be recreated |
| Replay runs | 0.8 GB | Kept. They are tracked in git, see below |
| Research datasets | 0.2 GB | Kept. Rebuildable from the tapes in about 2 hours |
| Git history | 142 MB, now 48 MB | **Repacked**, nothing removed |
| Paper records | 85 MB | Kept |

| Done today | Freed |
|---|---|
| Git objects repacked (`git repack -a -d`, then `git prune-packed`; connectivity check clean) | 93 MB |
| Earlier today by the other review: caches removed, SDK log compressed with a verified hash | 152 MB |

What I did not do, and why:

- **Old replay folders (about 480 MB) are tracked in git.** Packing them into archives would delete tracked files
  from the working tree and change what the public repository shows on the next commit. That is the owner's call.
  The tool is written and verified in dry-run only: `research/archive_runs.py`. It compares the hash of every
  archived file with the original before removing anything and can restore.
- **The tapes could shrink by roughly a third (about 1 GB)** if recompressed from gzip to xz with a hash check of
  the decompressed stream. The replay reader would need to read xz, and it costs several processor-hours. Not done.
- Research outputs of today are 30 MB.

The space is elsewhere on the drive. Read-only sizes of the top folders:

| Folder on D: | Size |
|---|---|
| ClaudePinRiskImproved | 44.6 GB |
| ClaudeCodeImproved | 43.7 GB |
| ClaudeCode | 12.3 GB |
| Vaishno | 10.1 GB |
| GCP | 9.4 GB |
| GooglePhotosBackup | 8.0 GB |
| TrinetraDev | 7.7 GB |
| GoogleDriveBackup_7Oct | 7.5 GB |
| GoogleDriveBackup_9June | 7.1 GB |
| GoogleDriveBourse | 6.9 GB |
| Backup28thJan | 5.4 GB |
| ApexOptions | 4.5 GB |

I did not open or change any of them. Three dated backups alone are 20 GB.

---

## 9. The replay batch of 10 Nov

Started 08:04 in four groups, 15 days, photograph v5, 99 books, missed-signal recorder on.

- It ran far slower than the 7 Nov batch: about 9 hours a tape against 2.7. The machine was also running another
  project's replays, a test run, and from 10:00 my own research jobs. I first set the batch to low priority, then
  restored normal priority at 13:30 when the owner said markets were closed.
- At that pace the batch would have run until the evening of 11 Nov, through the live session. **I stopped the four
  batch drivers at 14:45 so no second tape starts.** The four days in progress (19 Oct, 26 Oct, 30 Oct, 5 Nov)
  continue to their end.
- 11 of the 15 approved days are therefore **not replayed**. Their results, and the step time of the present
  configuration, are still owed.
- The forecast books were wired into the engine at 14:50, while those four tapes were already running, so the four
  tapes do not contain them.

---

## 10. Everything tried today on the forecast

| # | Specification | Kept |
|---|---|---|
| 1 | Weather-photograph model for the champion: top 3 or 8 fields, two penalties, three targets, 100 shuffles each | reported, no separation |
| 2 | Forecast features run 1 (29), targets ±5 %, horizons 30/60/180/300 s | `run1/` |
| 3 | Run 2: holes up to 5 s tolerated, damped fit | `run2/` |
| 4 | Run 3: order-flow and depth features (33) | current |
| 5 | Logistic model, penalty 10. No other penalty was tried | used |
| 6 | Gradient boosting, depth 3, 200 trees, rate 0.05 (runs 1 and 2) | reported, rejected |
| 7 | Entry lines at the training 95th and 99th percentile, both declared before run 1 | both reported |
| 8 | "Entries before 15:15" and "premium 20 or more" splits, added after run 1's day table | diagnosis only |
| 9 | Controls: base rate, 30 s momentum alone, the option's own 30 s move alone, every origin | reported |
| 10 | Matured-only calibrator, prior 200, 20 bins | reported, no gain |
| 11 | Forecast against champion entries: edge, P target 300 s, P adverse, P target 60 s; three outcomes; 5,000 shuffles | reported, no separation |

The barrier of 5 %, the four horizons, the one-second delay and the 5 s sampling were fixed before the first run and
never changed. No other barrier or horizon was tried.

---

## 11. Not done

1. No engine replay of the forecast books. No all-in account result, no comparison with the Conductor's account.
2. 11 of the 15 approved replay days. The four running tapes had not finished when this was written.
3. Step time of the present configuration on an idle machine, and a function-level profile.
4. The burst when many books enter together is not fixed. The photograph is not split.
5. P03 and a champion twin for P04 are not built. P01 is a record, not a book.
6. Greeks as a scenario translator (docs/40 section 4) are not built. The forecast is a direct premium forecast.
   Whether a Greek-based translation adds anything was not tested.
7. Premium-return quantiles and interval coverage are not built. Event probabilities and time to event are.
8. Sibling grouping into market episodes exists for the champion tests. The 216,029 origins are not grouped: rows
   5 s apart overlap, so the standard errors in section 3.4 are for trades, which do not overlap, not for rows.
9. A registry of runs with retention classes (docs/40 section 9) is not built.
10. Weather items 111 to 119 and 127, and shadows S02, S04, S05, S06 from docs/38, remain not built.
11. Nothing here has run in a live session.

---

## 12. Update, evening of 10 Nov

### 12.1 The four replayed days, through real option quotes

Batch `g3b_g1` to `g3b_g4`: 19 Oct, 26 Oct, 30 Oct, 5 Nov. Photograph v5, 100 books (before the forecast books).
Returns are per cent of premium on the engine's own fills.

| Book | Trades | Won | Lost | Sum | Mean | By day |
|---|---|---|---|---|---|---|
| `s01_transmit` | 43 | 17 | 26 | −68.7 % | −1.60 % | −41, −16, −4, −8 |
| `s01_ctl_cash` (control) | 36 | 23 | 13 | +25.4 % | +0.71 % | +14, +7, −4, +8 |
| `s01_ctl_sfut` (control) | 42 | 19 | 23 | −6.5 % | −0.15 % | +27, −21, −26, +14 |
| `s03_recruit` | 315 | 148 | 167 | +20.2 % | +0.06 % | −41, +31, +26, +4 |
| `n06_ctl_breadth` (S03's control) | 253 | 120 | 133 | −136.1 % | −0.54 % | −81, −18, −26, −11 |
| `n02_ctl_mr` | 244 | 119 | 125 | +61.7 % | +0.25 % | |
| `n01_ctl_price_ind` | 216 | 95 | 121 | −101.1 % | −0.47 % | |
| `c20_9y` | 21 | 11 | 10 | +250.3 % | +11.92 % | +107, +152, −2, −6 |

- **S01 fails.** It loses and is worse than its cash control. It stays as a shadow with its record; nothing more is
  built on it.
- **S03 is flat**, 148 won against 167 lost, but it is better than its control on three of the four days. 264 of its
  315 exits are its own "recruitment reversed" exit. Four days is too few to say more.
- The Conductor took no trade in these replays: the pool has no member dated before 9 Nov.
- The books file of one day is now 12.6 to 20.7 MB (it was 7.7 MB on 9 Nov with photograph v4).

### 12.2 Step time on the idle machine

`research/profile_replay.py`, 9 Nov tape, 105 books, photograph v5, under the function profiler for 600 s of wall
time. It reached market time 09:27 (25,549 steps). The profiler roughly doubles every figure.

| What | Under the profiler |
|---|---|
| Mean step | 23.5 ms |
| Step median at 09:17 to 09:27 | 16 to 35 ms |
| One entry photograph (29 calls) | 20.7 ms |
| Forecast service, per second | 3.7 ms in all, 2.7 ms in `Pred.update` |
| gen3 feed, per second | 0.73 ms |
| gen2 feed, per second | 0.85 ms |
| Dashboard state write, per publish | 3.3 ms |

Largest parts of a step by cumulative share: all books 20 %, flow 15 %, Greeks 8 %, market history 6 %, publish 5 %,
domino 4.5 %, option rows 4 %. **No single function dominates a normal step.** The present configuration is not
slow in itself at the open: the 103 to 114 ms a step of today's batch came from the overloaded machine and the
missed-signal recorder.

Not covered: the profile stops at 09:27, so it holds only 29 photographs and nothing from late in the day, when a
photograph costs more. The other-books part of the photograph, which docs/40 suspected, walks about 1,300 trades by
the close, which should be well under a millisecond, so it is probably not the cause. The late-day photograph has
still not been profiled.

### 12.3 Premium ranges, and whether the Greeks help (docs/40 sections 3 and 4)

`ranges_greeks.py`. The quote-aware return of the fixed contract at 60 s and 300 s, quantiles 10, 50 and 90 %, each
test day from earlier days only.

- **Baseline:** the training days' plain quantiles.
- **Direct:** a location and scale model of the premium return.
- **Translator:** the same kind of model for the index future's move, 19 scenarios of it repriced with Black-76 at
  the origin's implied volatility, which is held constant.

Pinball loss, lower is better. The range is 10 to 90 %, so the right coverage is 80 %.

| Horizon | Forecaster | Loss at 10 % | Loss at 50 % | Loss at 90 % | Coverage | Median width |
|---|---|---|---|---|---|---|
| 60 s | Baseline | 0.01088 | 0.01866 | 0.01129 | 79.4 % | 9.9 % |
| 60 s | Direct | 0.00969 | 0.01891 | 0.01056 | 82.1 % | 10.7 % |
| 60 s | Translator | **0.00900** | 0.01875 | **0.00986** | 74.0 % | 7.3 % |
| 300 s | Baseline | 0.02249 | 0.03999 | 0.02417 | 79.1 % | 21.6 % |
| 300 s | Direct | 0.01942 | 0.04156 | 0.02430 | 78.9 % | 22.4 % |
| 300 s | Translator | **0.01849** | **0.03993** | **0.02148** | 75.1 % | 16.3 % |

- **The Greeks help with the size of the move, not its direction.** Repricing a forecast of the underlying gives
  the best tails at both horizons. Nobody beats the baseline in the middle, which is section 3.2 again.
- **The translator's range is too narrow:** 74 to 75 % where 80 % is right. Holding volatility constant leaves out
  the part of the premium's movement that comes from volatility changing.
- The baseline's 79 % overall hides 49 to 51 % on expiry days and 91 to 92 % on other days. The two models fix that.
- Full repricing against the local approximations, for the median: delta, gamma and theta together differ from full
  repricing by 0.003 to 0.04 % of premium, delta alone by 0.17 to 0.74 %.

This is an offline result. Ranges are **not yet in the live forecast record**.

### 12.4 The two champion twins (P03, P04)

| Book | Rule added to c20_9y | Never does |
|---|---|---|
| `fx_c20_9y` | exits when, after an observed gain of at least 5 %, the forecast edge of the held contract is below the exit line | act as a stop: a position that never gained is left to the strategy |
| `fr_c20_9y` | holds through the strategy's own SELL while the position is in profit on the bid and the edge is at or above the entry line | hold a losing position, or hold without a forecast |

Same strategy class and the same entries while both are flat. Registered last, so the order of the older books, which
breaks same-tick ties, is unchanged. They are not counted among "books firing" or "the books around" an older book,
and their names do not start with c20, so the family counts the frozen rules read are unchanged.
`tests/test_pred.py` now has 9 tests. 105 books.

Also corrected: the forecast record on champion-family fills was hooked where the council books never pass. It is
now written from the council step.

### 12.5 Run registry

`research/run_registry.py`, read-only, writes `data/research/run_registry.json`: every run folder with its producer,
state, size, git-tracked count, whether a document cites it, and a class.

| Class | Folders | Size |
|---|---|---|
| Active (written in the last 30 minutes) | 4 | 118 MB |
| Evidence (tracked or cited) | 101 | 789 MB |
| Regenerable (untracked and uncited) | 6 | 227 MB |

The 227 MB is almost all the 1-second research dataset, which today's work reads. Nothing was removed.

### 12.6 Overnight replay

Started 17:09 on the owner's instruction: all 15 days, 105 books including the forecast books and the twins, eight
groups in parallel (`p41_g1` to `p41_g8`), the missed-signal recorder off for speed. A watcher stops anything
unfinished at 08:25 on 11 Nov so nothing overlaps the live session.

### 12.7 Still not done

Status on 11 Nov before the open:

1. Account contribution: **done**, section 14.2. Against the Conductor it is one day only.
2. The late-day photograph profile: section 14.4. The fix for many books entering in one step: **not done**.
3. Ranges in the live forecast record and the volatility scenario: **done**, sections 13.1 and 13.2.
4. Missed and rejected winners for the forecast books: **not done**. The recorder was off in the overnight run.

---

## 13. Update, night of 10 Nov

### 13.1 The volatility scenario in the translator (item 3 of section 12.7)

`ranges_greeks2.py`, results in `results_ranges2.txt` and `data/research/predict/ranges_greeks2.json`.
The translator now draws 99 joint scenarios of the future's move and the change in the contract's implied volatility.
The volatility at the horizon is backed out of the observed bid. Same origins and walk-forward as section 12.3.

The rule was written in the script before the run: coverage between 78 % and 82 % at both horizons, then the lowest
tail loss; if nothing qualifies, the direct model.

| Forecaster | Coverage 60 s | Coverage 300 s | Tail loss, both horizons | Qualifies |
|---|---|---|---|---|
| Baseline | 79.4 % | 79.1 % | 0.0688 | yes, but it is the reference |
| Direct | 82.1 % | 78.9 % | 0.0640 | no, by 0.1 point |
| Translator, volatility held | 76.6 % | 77.6 % | 0.0601 | no |
| Translator with volatility scenario | 84.4 % | 81.1 % | 0.0614 | no |

- The volatility scenario repairs the too-narrow range and then overshoots at 60 s.
- The translator figures differ a little from section 12.3 because the scenarios are now 99 drawn pairs, not 19
  quantiles.
- Nothing but the baseline met the rule, so by the rule **the direct model is the one in the live record.**
- On days that are not expiry days the direct model covers 79.9 % at 60 s but only 75.0 % at 300 s. On expiry days
  it covers 87 to 88 %. It is not yet well calibrated by day type.

### 13.2 Ranges in the live forecast record (item 3 of section 12.7)

- `make_ranges.py` fits the direct model on all 15 sessions and writes `apex/predict/ranges_v1.json`
  (hash `dc41cd42f5c8`), a separate file. The probability model `model_v1.json` and its hash are unchanged.
- `apex/predict/ranges.py`, class `Ranger`: no fitting at run time; silent on a missing artefact or another feature
  schema.
- Every forecast record written to the ledger now carries `range`: the 10, 50 and 90 % points of the premium return
  at 60 s and 300 s, and `range_model`. This covers the 15-second samples, the forecast books' signals and the
  champion-family fills.
- **A record only.** No book and no exit reads a range.
- Cost: the range is computed only when a record is written, about 4 records every 15 s. One call is 0.46 ms on the
  loaded machine. That is about 0.1 ms a second. Step time was not re-measured on an idle machine.
- The overnight replay does not have ranges: every tape had loaded its code before this was wired in, on purpose,
  so all 15 days ran on one version.
- Tests: `tests/test_ranges.py`, 6 tests.

### 13.3 One cause of the afternoon slowdown, found and fixed

Source: the minute lines of the finished 9 Nov replay (`p41_g8/tape_00.out`), which ran beside seven other replays,
so absolute figures are high. The growth inside the day is the finding.

| Hour | Median step | 95th percentile | Steps over 300 ms | Publish, ms a step | Weather base, ms a step | Books save, ms a step |
|---|---|---|---|---|---|---|
| 09 | 44 | 132 | 15 | 4.8 | below 0.3 | 1.1 |
| 10 | 38 | 122 | 17 | 5.0 | 1.5 | 1.4 |
| 11 | 37 | 139 | 156 | 6.4 | 2.1 | 3.3 |
| 12 | 38 | 145 | 335 | 7.3 | 2.6 | 2.8 |
| 13 | 41 | 176 | 527 | 9.6 | 3.4 | 4.2 |
| 14 | 45 | 184 | 419 | 10.5 | 4.4 | 4.2 |

The hours are not all complete in the log (10 to 60 minute lines each), so the counts are not rates.
The median step hardly moves. The slow steps multiply, and three parts grow with the day.

**Weather base.** `Weather.base()` runs once a second. Three of its numbers re-scanned the whole day every second:
the day's range, the median at-the-money IV, and the three opening ranges. Measured on a synthetic full day, on the
loaded machine:

| Seconds since the open | Before | After |
|---|---|---|
| 600 | 10.5 ms | 7.4 ms |
| 7,200 | 12.3 ms | 5.8 ms |
| 14,400 | 25.9 ms | 8.9 ms |
| 22,499 | 35.9 ms | 11.9 ms |

The fix keeps running values (`_Prefix`, `_orange` in `apex/engine/weather.py`). `tests/test_weather_base_running.py`,
4 tests, pins that they equal the whole-day scans exactly at every second, also when a query goes back in time.
The weather suites pass with it. What still grows a little is the day-long efficiency ratio, about 375 look-ups a
second by the close. It was left alone.

**Dashboard publish.** Every publish asked each of the 105 books for its statistics, and each book walked all its
closed trades again. On the finished 9 Nov books (2,413 trades) that is 7.9 ms a publish on the loaded machine.
`Book.stats()` now keeps its sums until a trade is added or a closed trade is written to. `ClosedTrade` already
counts its own changes, so the kept numbers cannot go stale. One more test in the same file pins the equality,
including the Conductor rewriting a closed trade.

**Not fixed:**
- The rest of the publish growth: the straddle series and the other views sent whole at every publish. Not measured.
- The books save grows with the trades stored. In a fast replay the save is written inside the step, so this figure
  overstates the live cost, where the write is off the step. The file itself is now 36.7 MB for 9 Nov with 105 books
  and photograph v5. It was 7.7 MB live on 9 Nov with photograph v4.
- The late-day entry photograph under a profiler on an idle machine.

---

## 14. Update, 11 Nov before the open: the 15-day replay and the account contribution

### 14.1 The run

`p41_g1` to `p41_g8`: all 15 tapes, 19 Oct to 9 Nov, 105 books, seeded, the missed-signal recorder off. Started 17:09
on 10 Nov, the last group finished 01:12 on 11 Nov. Every day finished; nothing was stopped by the watcher.
The run has none of the night's changes (ranges, the weather and statistics speed fixes): all tapes ran one code
version.

### 14.2 Account contribution (item 1 of section 12.7)

`data/replay/batch/predict_2026-11-10/contribution.py`, output `data/research/predict/contribution_p41.json`.
All-in on every trade, no sizing, no costs. A trade's return is exit / entry - 1 on the engine's own fills, in per
cent of premium. "Account" is 100 compounded all-in through every trade in order.

**Two limits to read first.**
- The forecast model `model_v1.json` was fitted on these same 15 days. For the forecast books and the twins this run
  is in-sample. It is not a held-out test.
- The Conductor owns the account from 9 Nov only (`CHAMPION_OWNER` is dated), so in a replay it trades on 9 Nov and
  on no earlier day. The comparison with the Conductor is one day. The 15-day comparison is with `c20_9y`, the best
  book of its pool.

| Book | Trades | Won | Lost | Sum % | Mean % | Days up | Days down | Worst trade % | Account | Rank of 106 |
|---|---|---|---|---|---|---|---|---|---|---|
| `c20_9y` | 92 | 54 | 38 | +889.9 | +9.67 | 12 | 3 | -16.2 | 66,240 | 1 |
| `fr_c20_9y`, forecast runner twin | 92 | 54 | 38 | +889.9 | +9.67 | 12 | 3 | -16.2 | 66,240 | 2 |
| `c20_9x` | 102 | 53 | 49 | +761.7 | +7.47 | 11 | 4 | -20.2 | 16,485 | 5 |
| `fx_c20_9y`, forecast exit twin | 139 | 93 | 46 | +561.6 | +4.04 | 10 | 5 | -18.6 | 5,302 | 10 |
| `p05_adaptive` | 795 | 417 | 378 | +356.2 | +0.45 | 11 | 4 | -10.9 | 1,549 | 35 |
| `p02_clock` | 718 | 390 | 328 | +295.8 | +0.41 | 10 | 5 | -11.3 | 721 | 41 |
| `p02_top1` | 294 | 155 | 139 | +84.0 | +0.29 | 7 | 8 | -10.8 | 152 | 63 |
| `p02_ctl_mom`, the control | 558 | 252 | 306 | -130.4 | -0.23 | 7 | 8 | -8.7 | 11 | 98 |
| `s01_ctl_cash`, control | 152 | 90 | 62 | +116.7 | +0.77 | 11 | 4 | -16.8 | 232 | |
| `s03_recruit` | 1,287 | 554 | 733 | +89.1 | +0.07 | 9 | 6 | -11.6 | 133 | 61 |
| `s01_transmit` | 170 | 74 | 96 | -81.2 | -0.48 | 5 | 10 | -13.3 | 39 | 95 |
| `s01_ctl_sfut`, control | 172 | 77 | 95 | -113.4 | -0.66 | 7 | 8 | -18.9 | 23 | |
| `n02_ctl_mr`, control | 1,087 | 534 | 553 | +91.5 | +0.08 | 8 | 7 | -13.2 | 90 | |
| `n01_ctl_price_ind`, control | 973 | 436 | 537 | -335.7 | -0.34 | 5 | 10 | -21.9 | 0.7 | 105 |
| `n06_ctl_breadth`, control | 1,070 | 524 | 546 | -337.9 | -0.32 | 6 | 9 | -24.3 | 0.5 | 106 |
| Conductor, 9 Nov only | 22 | 10 | 12 | +71 | | 1 | 0 | | | 65 |

The Conductor's 22 trades on 9 Nov, by exit: forward trail 10 (5 won), stop 5 (0 won, -76 %), time 2, break-even
lock 2, rent trail 1, premium trail 1. `c20_9y` made +82 % on the same day with 20 trades.

Sum of returns by day, per cent:

| Book | 19 Oct | 21 | 22 | 23 | 26 | 27 | 28 | 29 | 30 | 2 Nov | 3 | 4 | 5 | 6 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `c20_9y` | 107 | 65 | 9 | 66 | 152 | 232 | 50 | 35 | -2 | 44 | 1 | -32 | -6 | 87 | 82 |
| `fx_c20_9y` | 89 | -7 | 28 | -8 | 130 | 107 | 47 | 35 | -2 | 32 | 1 | -29 | -9 | 92 | 56 |
| `p02_clock` | -77 | 27 | 47 | -65 | 21 | 114 | 50 | 24 | -36 | 49 | 93 | -1 | -9 | 12 | 46 |
| `p05_adaptive` | 9 | 32 | 23 | -30 | 77 | 1 | 36 | 56 | -29 | 39 | 98 | -9 | -3 | 3 | 53 |
| `p02_top1` | -31 | 8 | -1 | -13 | -2 | 18 | -9 | 37 | 52 | 3 | 38 | -5 | -3 | -13 | 6 |
| `p02_ctl_mom` | 23 | -55 | -67 | 2 | -63 | 57 | -13 | 5 | -19 | -25 | 21 | -1 | 18 | -54 | 39 |
| `s01_transmit` | -40 | -11 | -5 | 2 | -16 | 39 | 2 | 5 | -4 | 0 | -13 | -11 | -8 | -12 | -10 |
| `s03_recruit` | -41 | 30 | 20 | 0 | 31 | -2 | -7 | -17 | 26 | 11 | -3 | 21 | 4 | 8 | 8 |

**What it says.**
- **No forecast book adds to the account.** `c20_9y` is first of 106 books. Every forecast book and both twins are
  at or below it.
- **The runner twin never changed a trade.** `fr_c20_9y` is `c20_9y` trade for trade on all 15 days. The forecast
  hold never fired in a way that altered an exit.
- **The exit twin wins more often and earns less.** 93 of 139 won against 54 of 92. Its forecast exit closed 67
  trades, 64 of them won, +471 %. But it re-enters, takes 21 stops for -325 % against the parent's 12 for -178 %,
  and gives up the long runners: forward trail +132 % against +349 %, and no ramp-lock or giveback exits. It beat
  the parent on 3 of 15 days.
- **The forecast entry does beat its own control.** `p02_clock` +296 % and `p05_adaptive` +356 % against the
  momentum control's -130 %, ahead of it on 10 of 15 days. In-sample, see above. Per trade it is +0.4 %, against
  +9.7 % for `c20_9y`: before costs, which this project ignores, and far below the champion family either way.
- `p02_top1` is flat. `s01_transmit` fails again, 10 days down of 15, and loses to its cash control. `s03_recruit`
  is flat: its reversal exit closed 1,048 trades, 339 won, -834 %.
- **"No losing trade" is unmet.** No book with trades has zero losing trades on 15 days. `c20_9y` lost 38 of 92; its
  12 stops cost -178 %.

### 14.3 Tests on the idle machine

The full suite, run at 01:14 on 11 Nov with nothing else running, on the code the live engine starts with at 09:15:
**520 passed, 8 skipped, 3 expected failures, 2 unexpected passes, no failure and no error**, in 4 min 39 s. The data-fence errors seen
during the night were the replays writing, as stated then; they are gone.

### 14.4 Corrections after the audit in docs/42 (11 Nov)

The audit in `docs/42_FORECAST_AUDIT_AND_CHAMPION_IMPROVEMENT_PLAN.md` was checked against the code and the saved
replay files. Its findings hold. Section 14.2 above is left as written; these corrections override it.

1. **"No forecast book adds to the account" is withdrawn.** `contribution.py` ranks stand-alone books. It does not
   replay the Conductor with a book added. The correct statement: the stand-alone comparison shows no benefit, and
   the incremental account effect has not been measured.
2. **Day counts were on summed per cent, not on rupees.** All-in sizing makes the two differ. In saved rupee
   profit `c20_9y` is up on 11 days and down on 4 (3 Nov: +0.9 % summed, -2,356 rupees). `fx_c20_9y` is 9 and 6,
   `p02_top1` 6 and 9, `p02_ctl_mom` 6 and 9, `p05_adaptive` 10 and 5. Six book-days change sign.
3. **Rupee totals, summed over independent session books:** `c20_9y` 11,94,372; `fx_c20_9y` 5,89,180; `p02_clock`
   4,02,240; `p05_adaptive` 3,85,996; `p02_top1` 77,821; `p02_ctl_mom` -1,05,385. The "account" column in 14.2 is a
   synthetic 100 compounded and is not a funded account.
4. **The forecast books did not trade the forecast.** The signal names one strike and side; the engine then chose
   its own contract. The traded contract differs on 658 of 718 `p02_clock` trades, 276 of 294 `p02_top1`, 679 of
   795 `p05_adaptive`. Their results in 14.2 say nothing clean about the forecast.
5. **The entry line and the live score are different functions.** The line is a percentile of the raw model
   output; the engine first makes the horizons consistent. On 204,010 origins this changes 1,424 decisions at the
   entry line.
6. **Coverage.** Only four contracts are scored each second. 46 of the 92 `c20_9y` fills carry a forecast.
7. **The twins do not test a holding model.** Both reuse the fresh-entry score. The runner twin intervened zero
   times. The exit twin's result shows that taking quick wins cuts the runners; it is not a test of a continuation
   forecast.
8. **`paper._gen_exit`** treated a quote age of exactly zero as missing and skipped the premium barrier that step.
