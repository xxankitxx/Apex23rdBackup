# 51. The build plan from the 11 Nov round table

Written on the night of 11 Nov 2026, while the p43 overnight replay was running.
Ten review lenses took the system apart. This page says what will be built, in what order, what stays off,
and what waits for you.

**Nothing in this plan changes a live trading decision without your yes.** Every change that could alter a trade
sits behind a config flag that starts OFF. No long run starts without your OK.

## 1. The plan in short

- The forecaster becomes a measured volatility and range tool. It stops being shown as a direction call.
  The evidence: a perfect 15-minute volatility forecast ranks the pool's winners at AUC 0.54. A perfect direction
  forecast ranks them at 0.83. So no entry, hold or exit rule is built on the forecaster's volatility numbers.
- Live fills can be brought back to how the replays fill, once you turn the flag on. On 9 Nov, 36 of 48 ownerships
  lapsed live. The replay of the same tape filled 10 more.
- The Conductor sometimes buys through a pool member's own frozen veto. That is measured every night as a shadow
  twin. You decide the trade-off, because the twin trades less.
- A held-trade card shows, in rupees from your actual entry, what the next 5 to 15 minutes can plausibly do against
  the book's own stop, trail, floor and clock. Probabilities stay hidden until their own record earns them.
- No live exit changes. Every exit idea goes through one test bench that runs the real strategy code.
- Decay, rent and the implied move use one clock: calendar time left divided by trading time left. It is exactly 1
  on expiry day. The old trading clock overstated expiry-day decay by about 3.84 times.
- One nightly runner scores the forecaster against the plain clock on days it never saw, and rolls back a model
  that loses.
- Every twin and trading rule is judged by your 7-test standard (docs/28 section 2), strike rate first. Forecast
  and pricing changes are judged on a fixed score instead (the "metric" entries in the ledger).

## 2. The pre-registration ledger (PKG-01, done)

`research/preregistry.jsonl` holds 12 entries, PR-001 to PR-012. Each one fixes the rule, its line, the standard,
the first day that counts as evidence, the minimum sample and the verdict rule. They were written at 23:57 on
11 Nov, before any evidence that counts for them existed or was looked at. Some numbers were already seen by the
round table (for example the in-sample family veto result and the raw 1-minute hit rate). Each entry names them,
and they never count as evidence. New studies only add lines; nothing is edited after the fact.

| Id | What it decides | First evidence | Minimum before a verdict |
|---|---|---|---|
| PR-001 | Retire p02_clock, p02_top1, p05_adaptive, fx_c20_9y and fr_c20_9y as negative controls if p02_clock wins less often than the Conductor or fails 3 or more of the 7 tests | p43 result, 12 Nov 08:10 | 11 p43 sessions |
| PR-002 | Family veto twin conductor_fv | 12 Nov | 20 vetoed triggers (about 3 to 5 weeks) |
| PR-003 | Which forecaster volatility model runs live (fast off, slow on) | 12 Nov | 10 forward days to switch on, 5 to switch off |
| PR-004 | The business clock for option paths | repricing scorecard | every unseen tape session |
| PR-005 | Whether any direction claim survives (tradeable 1-minute hit rate 55 % on 8 of 11 days) | walk days, not yet scored | 11 walk days |
| PR-006 | Oracle gate: a rule must pass with perfect knowledge first, then as a forecast, then on new days | 12 Nov | 115 reconstructed trades |
| PR-007 | Five admission rows, including a random-skip control | 12 Nov | 20 blocked triggers per row |
| PR-008 | Five exit-bench rows, one fixed parameter each | first decision-tape day | the bench's fidelity gate first |
| PR-009 | Keep or retire the re-entry twin rx_c20_9y | the session after its fix lands | 10 sessions |
| PR-010 | The Lab's "earned" gates: false claims at most 5 % on no-skill days | simulation | 10,000 simulated days |
| PR-011 | One Hedge learning-rate change | paired walk | 11 walk days |
| PR-012 | The late-observed fill, judged by live and replay trade lists agreeing | 12 Nov | 1 to 3 healthy sessions |

The ledger keeps a running count of hypotheses tested. It starts at 65, the ideas the round table examined, and
reaches 82 after these entries. Later reports adjust their luck margins for that count.

## 3. The 16 packages

Order: PKG-01 first, before p43 finishes at 08:10. Before 09:15 on 12 Nov, only where tests pass: PKG-02 (you then
start the Lab by hand and check the header says learning "migrated v1"), PKG-03, PKG-04, PKG-05, and PKG-06 step 1
with its flag OFF. The rest land on later evenings, after the close.

"Engine" means the package touches files the trading engine loads. Those edits wait until the overnight replay's
second tapes have started, and must be tested and timed before about 08:45.

| Package | What it does | Engine | Flag | Waits for you |
|---|---|---|---|---|
| PKG-01 Pre-registration and this plan | Writes the ledger above and this page | No | None | Nothing |
| PKG-02 Lab pre-open safety | The Lab starts with only the learning it can honestly carry and says so ("migrated v1"). It can never block a trading restart. It never shows a dead verdict as live | No | None | The after-hours drill run on an idle evening |
| PKG-03 Honest Lab statements | Each claim and horizon must earn its own record against a no-skill baseline. No buy case and no "Flat" while you hold. No "80 %" where the day caught less | No | None | Optional replay of contradicted statements over 11 walk days |
| PKG-04 Trade-first page | While holding, the position band and live commentary come first with no layout shift. A stopped Lab is unmistakable. The page redraws only what changed | No | None | A look in your browser during one live session |
| PKG-05 Engine hardening and observers | Small fixes so shadow twins measure what they claim. Logs every veto and every lapse. A dashboard fault can no longer slow the loop. No Conductor decision changes | Yes | VETO_LOG, LAPSE_DIAG, both ON: they only log and change no decision | A one-day replay identity check |
| PKG-06 Stall-proof entry fills | An entry whose print came inside the 3-second window is no longer lapsed because the engine was late. Trigger-step stalls are cut | Yes | FILL_LATE_OBSERVED, COUNCIL_FILL_EVERY_STEP, PHOTO_CACHE, RESTORE_ARM_ON_LAPSE, TRADE_SAVE_ASYNC, all OFF | Each flag flip; the stall-injected 9 Nov replay; the p41 A/B; the photo identity replay; parity.py nightly |
| PKG-07 Hazard shadow books measured honestly | The forecast ledger fills on the training label's rule. The p05 calibrator learns only from finished outcomes. The engine panel stops naming an unearned side | Yes | None (shadow only) | Nothing |
| PKG-08 One business clock | Decay, rent and implied move all use the same clock. Option-path changes are accepted only on a pricing scorecard (PR-004) | No | None | The repricing scorecard over the 16 tapes (10 to 20 minutes) |
| PKG-09 Feed gate, checkpoint, decision record | The Lab never learns from a frozen quote. It survives a mid-session restart. One record ties its numbers to every trigger, entry, held minute and exit | No | None | The injected-freeze and restart tape runs; the back-fill walk (about 50 minutes) |
| PKG-10 One nightly runner | Runs once a night, can be re-run safely, keeps an archive of every model, scores against the clock on the unseen day (PR-003) and rolls back a loser. Never runs in market hours or beside a replay | No | None | The scheduled-task changes in docs/53; the first full timed nightly |
| PKG-11 Trained volatility layer repaired | Fixes the known biases (forecast about 1.17 times low, tilted quantiles, Hedge chasing the last outcome) in one feature bump, one re-collect and one walk. Settles the direction question (PR-005) | No | None | The re-collect of 16 sessions, the refit and the walks (about 50 minutes each) |
| PKG-12 The 7-test standard every night | Scores the Conductor, its pool books and every twin by your standard: distinct entries, split by days to expiry, best day removed. Runs the oracle gate and the family veto offline | No | None | Whether the family veto is judged as a pool rule or at Conductor level |
| PKG-13 Decision tape and exit bench | Saves each day's decision inputs after the close. Tests exit ideas on the real strategy code, behind a fidelity gate | Yes | DECISION_TAPE, OFF | Enabling the tape live; one replay batch with the tape on; the first fidelity runs |
| PKG-14 Held-trade card | Rupee ranges from your entry, the book's own levels, and why the trade is up or down. No new exit level, no unearned direction | No | None | The score_held walk (about 50 minutes) before any probability is shown |
| PKG-15 Engine hazard model fitted nightly | A fixed nightly fit with files that are never overwritten. An activity-only model by default. One outcome definition for live and training | Yes | None (shadow only) | The nightly hazard fit (about 25 minutes); the label v3 relabel and refit |
| PKG-16 Engine panels in your terms | A "Twins vs the Conductor" board on the 7 tests, strike rate first. The Conductor's entry line (fills, lapses, vetoes). Activity without a side. Why the account is flat | No | None | A look in your browser during one live session |

## 4. Not built, and why

The round table set aside 21 ideas or parts of ideas. All 21 are listed here.

1. L1-I6, a volatility-scaled forward trail: it lost 41k to 98k, in both windows, on the exit simulator.
2. L2-I8, the seq rent gate: it fires too rarely to reach 20 differing decisions, and it would change a frozen
   pool rule. PKG-12 audits the live seqcal and FY_RVI vetoes offline instead.
3. L6-I4, the two rent twins: no separation between winners and losers, and the entry one fails the trade-count
   test. The exit one lost 1.77 lakh on the bench. It survives only as one exit-bench row (PR-008).
4. L9-I6, a Conductor twin on rent below 1: the same refuted gate, and it fails the trade-count test.
5. L3-I4, a "forecast range at least the break-even move" entry rule: break-even is only 4 to 19 % of the move,
   so it would almost never block.
6. L5-I1, activity at the trigger as a live rule: within a day it does not separate winners (AUC 0.44). It stays
   as one admission row (PR-007).
7. L5-I4, a 300-second dead-trade label: it does not fit 10 to 15 minute exits, and its proxy lost 17k on the
   bench. It stays as one exit-bench row (PR-008).
8. L8-I8, a Lab feed inside the replays: no Lab number has passed the oracle gate yet. Built only when one does.
9. L3-I5, filling in triggers missed while the account was busy: those triggers were net losers (18 triggers,
   8 winners, minus 66 points).
10. L7-I6, a display clock: it is the 3.84 clock that the expiry-day quotes refuted. Replaced by the one clock.
11. L10-I1, decay factors fitted per days to expiry: 16 sessions would overfit; the parameter-free clock already
    matches. Its straddle test stays as a nightly monitor.
12. L9-I7, a matched-label refit of the re-entry model: it cannot be judged (no hold-out decisions). Replaced by
    fixing its inputs and scoring it every night (PR-009).
13. L4-I2 step 1, a new futures-mid input for re-entry: the code already feeds the futures mid. PKG-13 checks
    this first, and the input changes only if that check fails.
14. L2-I5, a copy of the exit logic inside the Lab: a re-implementation reproduced only 67 of 92 exits.
15. L1-I4 on the panel, the chance that a move beats break-even: it has no skill (AUC 0.50 to 0.52). The study
    stays offline.
16. L7-I5, a new hook inside the five frozen pool strategy files: it risks their behaviour and step time. PKG-16
    builds the why-flat line from reasons already published.
17. L10-I2, re-basing the Lab on the options' forward: deferred. Built only if PR-005 passes.
18. L6-I6 part (d), the morning Hedge shrink: it would confound the learning-rate fix, which is judged first
    (PR-011).
19. L2-I1, a fitted intraday variance profile: fitted on 16 sessions. It runs only as a challenger on the
    repricing scorecard.
20. L2-I6, an expiry settlement window: not checked against the exchange's method, and only 4 expiry days. It
    runs only as a challenger on the repricing scorecard.
21. L5-I6, the 09:16 opening-forecast fix: deferred. Nothing kept needs it. Revisited only if the admission study
    keeps an activity row.

One open item: requiring a trade after the trigger before filling (L3-B6 step 2). PKG-05 first counts how many
live fills it would touch.

## 5. Long runs that wait for your OK

Each one runs on an idle machine, outside market hours, never beside your replays.

1. The stall-injected 9 Nov replay, old fill against new fill (PKG-06).
2. The p41 A/B for filling on every step (PKG-06). It also restarts the docs/28 evidence windows.
3. A one-day replay identity check for PKG-05 and PKG-06.
4. The photo-cache byte-identity day (PKG-06).
5. The repricing scorecard over the 16 tapes (PKG-08).
6. The single re-collect of the 16 sessions, the refit and the walks: brain, plain and the Hedge pair (PKG-11).
7. The injected-freeze and restart tape runs (PKG-09).
8. The back-fill walk of the decision record (PKG-09).
9. The score_held walk (PKG-14).
10. A replay batch with the decision tape on (PKG-13).
11. The nightly hazard fit, and the label v3 relabel and refit (PKG-15).
12. The first full timed nightly (PKG-10).
13. The Lab drill run against scratch data (PKG-02).
14. The optional replay of contradicted Lab statements over the 11 walk days (PKG-03).
15. parity.py as a standing nightly replay job, and the nightly replay parity step (PKG-06 and PKG-10).
16. The first exit-bench fidelity and variant runs (PKG-13).
17. PKG-11's step 1 and step 2 scripts, if either runs longer than 2 minutes.

## 6. Decisions only you can make

1. Is "strike rate first" a strict order, or must all 7 tests pass together? The record cannot settle it. On 92
   trades the earliest family exit gives 54 to 64 winners but loses 5.47 lakh. On 77 shared entries the 9t rent trail
   wins 75 % against 64 % but returns +500 against +916 points.
2. Judge the family veto (PR-002) as a pool rule, R-021, where test 6 is exempt? Or as a Conductor twin, where test
   6 applies and fails by design (7.2 to 6.1 trades a day)? No verdict is possible before 20 vetoed triggers, about
   3 to 5 weeks. Even if the effect is real, the chance of passing both windows is about 12 to 48 %.
3. Turn FILL_LATE_OBSERVED on after 1 to 3 sessions of would-fill observation (PR-012). It only matters on stall
   days: 0 lapses on 11 Nov, 36 of 48 on 9 Nov. It fills only at the exact in-window print. Separately, approve the
   replay A/B for COUNCIL_FILL_EVERY_STEP.
4. Approve the long runs in section 5.
5. Apply the scheduled-task changes in docs/53, and choose how the Lab is supervised: its own weekday task with
   restart on failure, or a low-priority child of run_apex. These are written as instructions, not applied.
6. Accept PR-001's outcome on p43. The five books would keep running for the record, but their call-vs-put lean
   leaves the panel.
7. rx_c20_9y: keep it as a scored shadow (its record restarts at zero when the fix lands, and it would buy about
   once a month), or retire it now.
8. Turn the decision tape on in the live engine: about 30 to 60 MB a day, written after the close.
9. Commit the untracked Forecast Lab code in the next big batch, so models, records and bug reports tie to code.
10. Accept that the Lab's buy case and direction claims will read "not earned" for at least 5 forward days by
    design, and that the volatility bands may run a little narrow at the 12 Nov open while kappa re-learns.

## 7. Where things are

- The ledger: `research/preregistry.jsonl`, checked by `tests/test_preregistry.py`.
- The promotion standard: docs/28 section 2.
- The nightly runbook: docs/53 (PKG-10). The exit bench: docs/52 (PKG-13).
