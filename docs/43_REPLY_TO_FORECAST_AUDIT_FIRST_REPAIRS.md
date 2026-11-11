# Reply to the forecast audit (docs/42): what was checked, what is repaired, what is not

11 November 2026, before the open. Claude's reply to `docs/42_FORECAST_AUDIT_AND_CHAMPION_IMPROVEMENT_PLAN.md`.

## 1. The short answer

The audit is right. Every main finding was checked against the code and the saved replay files and holds. The
15-day replay of section 14 in docs/41 did not test the forecast: the forecast books bought a different option from
the one scored, on a line fitted to a different score. The corrections to docs/41 are in its section 14.4.

Nothing here changes the champion, the pool, the Conductor or any owner rule. All repairs are in the forecast
service and its shadow books.

**"No losing trade" is unmet.** Nothing in this document moves it.

## 2. Each finding, checked

| # | Finding in docs/42 | Checked where | Result |
|---|---|---|---|
| A | The book buys another contract than the one scored | `paper.evaluate_gen` passed only the direction; `choose_contract` then took its own strike by delta band | True. Repaired, section 3.1 |
| B | The entry line and the engine score are different functions | `make_artefact.py` used raw T300 - A300; `Forecaster.forecast` projected first | True. Repaired, section 3.2 |
| C | Only four contracts are scored; held positions fall out | `Pred.update`, `edge_of` | True. Repaired, section 3.3 |
| D | Wrong target for champion admission and for holding | `targets.py`, `held_keep`, `held_exit` | True. Not repaired: it needs new labels and a new model |
| E | The separation study is not champion-specific | `champ_separation.py` averages sibling books | True. Not repaired |
| F | The replay is in-sample; nothing enforces the cut-off | `Forecaster` checked schemas only | True. Flagged now, section 3.4. Not enforced |
| G | Life-cycle faults | see below | One repaired, the rest open |
| - | Day counts on summed per cent, not rupees | `contribution.py` | True. Corrected in docs/41 section 14.4 |
| - | "No forecast book adds to the account" not established | stand-alone ranking only | True. Withdrawn |
| - | The runner twin never intervened | saved trades identical on 15 days | True. Counters added, section 3.5 |

Finding G in detail:

| Item | Status |
|---|---|
| `paper._gen_exit` read a quote age of zero as missing | Repaired, tested |
| Live maturity fill can come later than the offline next-second fill | Open |
| Calibrator updates at first barrier, offline waits the full window | Open |
| The maturity queue can evict a filled origin silently | Open |
| The ledger does not repair a torn last line; no restart of pending state | Open |
| The ledger flush runs inside the engine's forecast feed | Open. The comment that says otherwise is wrong |

## 3. What was repaired tonight

### 3.1 The contract scored is the contract bought (A)

- Each second the engine tells the forecaster which contract it would buy on each side under the owner's rules
  (delta band by days to expiry, premium range, fresh quote). Those two are scored.
- The forecast books choose **only among those two**. The signal carries strike and side.
- `paper.bound_contract`: a forecast book buys exactly the contract of its signal, or nothing. The owner's floors
  still apply (delta at or above 0.52, premium 20 to 600, quote under 15 s, the expiry-day cut-off). The refusal
  text says why, and no other strike is ever substituted.
- The momentum control picks its side by momentum and buys the same executable contract, so it stays a like-for-like
  control.

### 3.2 One scoring function (B)

- `Forecaster.score` is the one pipeline: fitted probabilities, then the projection across horizons. The engine's
  `forecast()` and any offline scoring call it.
- `apex/predict/model_v2.json`, hash `7db140939ea1`: the **same fitted weights** as `model_v1` (hash
  `88c09e8db35f`, kept), with the lines taken from the deployed score.

| Line | Old (raw score) | New (deployed score) | Origins above the old line, deployed score | Above the new line |
|---|---|---|---|---|
| Exit, median | -0.0631 | -0.0625 | 102,700 | 102,005 |
| Entry, 95th percentile | +0.0404 | +0.0388 | 9,557 | 10,201 |
| Top, 99th percentile | +0.0794 | +0.0751 | 1,650 | 2,041 |

204,010 origins. The lines are still percentiles of the fitting data. Fitting them on earlier days only is part of
the chronological rebuild, not done.

### 3.3 Coverage (C)

- Besides the four near contracts, the forecaster now scores the two executable contracts and every contract a book
  holds in the near week, up to 12.
- A contract without a forecast now has a reason: warming up, off the strike grid, no fresh two-sided quote, feed
  not healthy, or not asked for. The fill record `fc.why` carries it. Missing is not a low score and not a veto.

### 3.4 Provenance (F), flag only

- The forecaster knows whether the day is at or before the model's training cut-off (`in_sample`) and shows it.
  Every ledger record already carries the cut-off.
- It does **not** refuse an in-sample replay. A registry of artefacts with effective dates is not built.

### 3.5 The twins count what they did

`Pred.stats` now counts, for the runner twin: asked, no forecast, not in profit, edge below the line, held. For the
exit twin: asked, no forecast, eligible, spoke. The next replay will say why the runner twin never acted.

### 3.6 Tests

`tests/test_forecast_repairs.py`, 9 tests: the vectorised score equals the engine score row for row; the installed
lines reproduce from the deployed score; signals choose only executable contracts; a forecast book buys the scored
contract or nothing; held contracts are scored and a missing forecast says why; the in-sample flag; the twin
counters; the age-zero quote.

Full suite on the idle machine after the repairs: **529 passed, 8 skipped, 3 expected failures, 2 unexpected
passes, no failure, no error.**

## 4. A limit the repair exposes

The model was fitted on the at-the-money strike and the first strike in the money. The owner's rule buys delta 0.52
to 0.70 with three or more days to expiry, 0.60 to 0.80 with one or two, 0.65 to 0.85 on expiry morning. On many
days the executable contract is deeper in the money than anything the model was fitted on. Scoring it is honest about
which contract is traded, but the model is extrapolating. **The model must be refitted on the executable contract.**
That is the first item of the next block.

## 5. Replay with the repaired books

`run_p42.py`: the last ten sessions (27 Oct to 9 Nov), fixed before the run, one run folder each (`p42_<mmdd>`), 105
books, recorder off. Ten days is what fits before the open on this machine. Still in-sample for the model. Results:
section 7, written when the run ends.

## 6. Not done, in the order docs/42 gives

1. Refit on the executable contract; lines from earlier days only; artefact registry with effective dates.
2. Champion-specific episodes and labels: one row per causal trigger of `c20_9y`, its own features, its own result
   under its own exits, including missed and rejected triggers. `FORECAST_SPEC.md`.
3. Coherent hazard model (favourable, adverse, neither by interval), replacing the projection.
4. A held-position continuation model: current gain, peak, drawdown, time held, against selling at the bid now.
5. The six one-mechanism shadow experiments, each with its control.
6. Conductor with and without a candidate book, in rupees, on the same tapes. Not a stand-alone ranking.
7. The open life-cycle items of finding G.
8. Greek scenario forecast against the direct one out of sample; sequence features.

---

## 7. After the second review (11 Nov, 02:00 to 02:20)

The reviewer accepted section 3 as a first repair milestone and not as the forecasting system. That is correct.
`model_v2` has the old weights: nothing new was learned. Two wordings of mine are corrected:

- "The replay did not test the forecast" was too strong. It tested a flawed combined policy and is still
  diagnostic. It did not measure the forecast's trading value cleanly.
- "529 passed" says the suite's checks hold. It says nothing about predictive quality, chronology or profit.

### 7.1 Done in answer to it

| Review point | What was done |
|---|---|
| 1. Full contract identity | The signal carries expiry and the full key. The binding refuses a forecast made for another expiry. The pending entry carries the request. At the fill the position records `fc_sig` (forecast id, scored key, same contract yes or no), and the ledger gets a `fill` record linked to the forecast |
| 2. Held coverage capped by strike order | Now by priority: the account's book first, then books that act on a forecast, then the rest. Pending entries count as held. Cap 24. Seconds over the cap and the worst excess are counted; an unscored contract says "more held contracts than capacity" |
| 5. Life-cycle before experiments | Agreed and reordered, section 7.3. Done now: the fill is the next second or none, as offline; the full queue evicts unfilled origins first and writes a censored outcome; a restart continues signal numbers, closes a torn last line, and marks unresolved forecasts once; the comment about the flush is corrected |
| 6. Shadow is not free | Measured, section 7.2 |

Not yet proven end to end: a pending forecast entry through a real engine step with a delayed fill and a restart in
between. The pending entry is not saved across a restart, so a restart drops it; it cannot fill another contract.
The pieces are tested separately. On the running replay every linked forecast-book trade so far is on the scored
contract.

Tests: 4 more in `tests/test_forecast_repairs.py` (13 in all). One older test pinned the 30-second fill window and
was changed to the new rule.

### 7.2 Cost of the forecast feed

Measured with ten replays running beside it, so the absolute figures are high. Per call, once a second:

| Case | Median | 95th percentile |
|---|---|---|
| First repair, four contracts | 24.7 ms | 63 ms |
| First repair, ten contracts | 41.9 ms | 107 ms |
| Now, five contracts | 12.3 ms | 44 ms |
| Now, ten contracts | 17.7 ms | 68 ms |

The first repair had made scoring slower: the shared function was called one contract at a time. All contracts are
now scored in one pass. About 10 ms of the rest is the market features, which were there before.
**Not measured on an idle machine and not inside a live engine step.** The feed runs inside the step, once a second.

### 7.3 Order from here

1. Finish contract and life-cycle parity: the end-to-end pending, fill and restart test; fill-label parity checked
   on a tape against `targets.label`; idle-machine step time of the repaired engine.
2. Rebuild the training data on the executable contract, with artefacts fitted on earlier days only and a registry
   with effective dates.
3. Champion admission labels and model; held-state continuation labels and model.
4. Controlled one-mechanism shadow comparisons.
5. Conductor with and without each candidate, in rupees.
