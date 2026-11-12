# 50. Forecast Lab v2, the engine's hazard model, and the pending items closed on 11 Nov

11 November 2026, after the close. Owner: "complete all the pending tasks ... I want a very very advanced version of
forecast model and not that stupid model you made for today's live market."

This document says what was built, the evidence on sessions each model had not seen, and what is still open.
**Display and shadow only: nothing here changes the champion, the pool or the Conductor.** "No losing trade" is unmet.

## 1. The short answers

1. **The forecaster now has a trained layer** (`apex/forecast_lab/brain.py`): 45 causal inputs, a multi-scale
   volatility model, fat-tailed move quantiles, two trained direction experts (ridge and gradient-boosted trees), and
   implied-volatility dynamics by time of day, days to expiry and moneyness. The online layer of the afternoon
   (expert weighting, calibration, self-scoring) sits on top and still learns from every checked forecast.
2. **Volatility: a real gain.** On 11 unseen sessions the trained volatility model beats the 10-minute clock on 8 or 9
   sessions at every horizon (section 3).
3. **Direction: mostly a feed lead-lag, not foresight.** The trained experts rank the future's next-minute move well
   (IC +0.21, 11 of 11 sessions), but the main input is the options' own forward and the heavyweight stocks moving
   BEFORE the recorded futures quote. Option prices already contain that. The option layer therefore learns, from its
   own checked forecasts, how much of the futures drift to use (section 4).
4. **Engine:** the eight-model forecaster is replaced by one coherent hazard model, loaded through a validated
   registry that never gives a session a model fitted on it. The label fault of docs/46 is fixed (section 5).
5. **Label parity on a real live day** is measured (section 6).
6. **The overnight replay** with the recorder on is the one long job; its plan is in section 9.

## 2. What the v2 forecaster computes

| Layer | Method | File |
|---|---|---|
| Inputs | 45 causal features every 5 s: momentum at 8 clocks; log variance at 4 clocks, the implied level and their ratios; a bipower jump measure; variance ratio, efficiency ratio, 2-minute slope and a Kalman local-trend slope (regime); order-flow imbalance at 2 clocks, book imbalance and its change; distance from VWAP, the day's range, high and low; implied-volatility change at 2 clocks, skew and its change, straddle change, forward-basis change; heavyweight breadth, lead and bank-against-rest; time of day, time left, days to expiry | `brain.features` |
| Volatility | per horizon, a ridge model of log(realised variance / reference variance): a HAR-type multi-scale model with intraday seasonality and the implied level. Rescaled online by its own matured errors | `Brain.vol` |
| Shape | per horizon, the empirical 10/25/50/75/90 % points of the standardised move (fat tails), and a stochastic-volatility mixture in the simulated paths (each path draws its own volatility level) | `Brain.qz`, `volvol` |
| Direction | seven experts: no move, momentum, order flow, reversion, all signals (online recursive least squares), plus two trained ones (ridge; 80 depth-3 boosted trees). Weighted by an exponentially weighted forecaster with fixed share on their matured scores | `core.Lab._origin` |
| Implied volatility | expected drift by (days-to-expiry bucket, 15-minute bucket), blended half and half with today's measured drift; the skew slide d(strike IV)/d(forward) by moneyness bucket; residual noise | `Brain.iv_*` |
| Options | 600 simulated paths, full Black-76 repricing with time running down; decay alone; break-even move; profit chance; the +5 %/-5 % race; a what-if grid (futures move by time) | `core.Lab._simulate` |
| Self-correction | every forecast scored when its time comes; expert weights, coefficients, volatility scale, conformal range width, option band bias and scale, the share of futures drift the option layer uses, the spot-vol beta | `core.Lab._mature_*` |
| Nightly learning | convert the day's tape, collect its inputs, refit the trained layer on all sessions | `research/forecast_lab/nightly.py` |

Speed, measured on today's tape: about 21 ms of processor time a second, the simulation 40 ms every 5 s. A separate
process at below-normal priority; it adds nothing to the engine's step.

## 3. Trained layer alone, on 11 unseen sessions

`research/forecast_lab/train.py walk`: for each session from 27 Oct to 11 Nov, the models are fitted on the earlier
sessions only (5 to 15 of them) and scored once. One ridge strength per family, fixed tree settings, nothing chosen on
a result. Results: `data/forecast_lab/walk_forward.json`.

| Horizon | Volatility error (QLIKE), model | 10-minute clock | Sessions better | 80 % range caught | Direction IC, both experts averaged | Sessions with IC above 0 |
|---|---|---|---|---|---|---|
| 1 min | 0.406 | 0.441 | 8 of 11 | 82.6 % | +0.207 | 11 of 11 |
| 2 min | 0.277 | 0.326 | 8 of 11 | 82.6 % | +0.127 | 11 of 11 |
| 3 min | 0.235 | 0.282 | 8 of 11 | 82.6 % | +0.108 | 10 of 11 |
| 5 min | 0.201 | 0.244 | 9 of 11 | 82.2 % | +0.060 | 7 of 11 |
| 10 min | 0.174 | 0.214 | 9 of 11 | 81.6 % | +0.061 | 6 of 11 |
| 15 min | 0.156 | 0.203 | 9 of 11 | 81.2 % | +0.033 | 6 of 11 |
| 30 min | 0.140 | 0.202 | 8 of 11 | 81.8 % | +0.064 | 6 of 11 |

- Volatility: 8 to 31 % lower error than the clock, on most sessions. The static 80 % range catches 81 to 83 %.
- Direction at 1 to 3 minutes is consistent; from 5 minutes it is not (6 or 7 sessions of 11).
- These 16 sessions have been studied before. This is historical research, not forward proof.

## 4. Why the short-horizon direction skill is not what it looks like

The largest weight of the 1-minute ridge expert is on the change of the forward basis (the options' parity forward
minus the future), then the last two minutes, then heavyweights leading the future. The recorded futures quote
follows the options and the stocks by a few seconds. So "the future will rise in the next minute" is often "the
options have already priced it".

For an option buyer that is no edge by itself. The option layer therefore does not take the futures drift on trust:
it keeps two running errors of its premium forecasts, with the drift and without, and uses the share `odw` that has
been right. The end-to-end result, with online learning, is in section 7.

## 5. Engine: one coherent hazard model, loaded by session

- **Label fix (docs/46 finding 3).** `targets.label`: a recording that ends inside the horizon is unobservable, not
  "neither". Target specification version 2. Effect on the first 15 sessions of the rebuilt table: 179 of 131,585
  "neither at 300 s" rows became unobservable (0.14 %); 358 at 30 s. The earlier M2 scores barely move.
- **Hazard artefacts.** `apex/predict/hazard.py` (scoring), `research/predict/fit_hazard.py` (fitting). Twelve
  artefacts, one per training cut-off from 26 Oct to 11 Nov, each with lines taken from the deployed score on the
  executable rows of its own training sessions. `ledger.Forecaster` scores both kinds through one function.
- **Registry wired into engine start (docs/46 finding 4).** `registry.for_session(day, mode, ...)`,
  `config.PREDICT_MODE = "chronological"`: the engine loads the newest validated artefact fitted on earlier sessions
  only; a session with none leaves the forecaster silent, with the reason in the log; it never falls back to a file
  that has seen the session. `APEX_PREDICT_MODE=discovery` loads the fixed file and reports `in_sample`.
- **Tomorrow (12 Nov)** the engine loads the artefact fitted through 11 Nov, recorded as published before the open.
- The range record's model is refitted on the same data (`ranges_v2.json`).

Hazard model, each session scored once by the artefact fitted before it (executable rows):

| Measure | Result on 11 unseen sessions |
|---|---|
| Three-way log loss | 0.976 against 1.108 for base rates; better on 10 of 11 |
| Side AUC given a 5 % move | 0.530; above 0.5 on 8 of 11 |
| Top 5 % by edge | 3,950 origins; up first 45.3 %, down first 43.0 %; mean 300-s return +0.23 % |
| Today, 11 Nov (a live day, unseen) | log loss 1.031 against 1.275; side AUC **0.443**, below chance; no origin reached the top line |

The probabilities are far better calibrated than the eight-model method. The side signal stays small and failed today.
The four forecast books will trade on this model from tomorrow; their value is unproven.

## 6. Label parity on a real live day (docs/44 M0)

`research/predict/label_parity.py 2026-11-11`: the outcomes the live engine wrote today against the offline labels on
today's tape, for 7,969 sampled forecasts.

| Check | Result |
|---|---|
| Filled or lapsed, same answer | 7,372 of 7,969 (92.5 %) |
| First event at 30 s, among those | 99.5 % the same |
| First event at 300 s | 96.2 % the same |

Traced example: live saw a low of -4.99 % and no event; the tape saw -5.06 % and an adverse event. The engine reads
the bid at its own instant inside a second, the tape row holds the last quote before the second's end. A touch that
lasts under a second is seen by one and missed by the other. Sampling, not logic. The 7.5 % fill disagreement has the
same root (the fill needs a quote newer than the forecast, judged at different instants) and is not traced row by row.

## 7. The whole forecaster, day after day, with and without the trained layer

`py -3.13 -m apex.forecast_lab.tape walk brain brain` and `... walk plain plain`: both run all 16 sessions in order,
online learning carried from day to day, as live. In the first, each session loads the trained layer fitted on the
sessions before it. Scored on the 11 sessions from 27 Oct to 11 Nov. Results: `data/forecast_lab/walk_brain.json`,
`walk_plain.json`. "Sessions better" counts the trained version against the online-only version.

Futures:

| Horizon | 80 % range caught | Range width, points: trained / online only | Range error (pinball), sessions better | Forecast error (CRPS), sessions better |
|---|---|---|---|---|
| 1 min | 80.2 % / 80.2 % | 21.4 / 20.9 | 1 of 11 | 8 of 11 |
| 5 min | 79.8 % / 80.0 % | 48.2 / 50.4 | 6 of 11 | 8 of 11 |
| 10 min | 79.2 % / 79.1 % | 70.0 / 74.8 | 8 of 11 | 7 of 11 |
| 30 min | 79.5 % / 79.2 % | 132.4 / 139.3 | 7 of 11 | 6 of 11 |

Option premiums (the contracts the engine would buy):

| Horizon | 10-90 range caught | Range width, % of premium: trained / online only | Range error, sessions better | Middle forecast error | "No change" error |
|---|---|---|---|---|---|
| 1 min | 80.1 % / 80.7 % | 9.7 / 9.8 | 5 of 11 | 2.87 % | 2.86 % |
| 5 min | 80.5 % / 81.5 % | 23.2 / 24.5 | 9 of 11 | 6.26 % | 6.27 % |
| 10 min | 81.2 % / 82.3 % | 35.8 / 38.6 | 8 of 11 | 9.14 % | 9.12 % |
| 30 min | 78.1 % / 80.4 % | 79.6 / 88.2 | 7 of 11 | 16.07 % | 15.93 % |

What it says:

1. **The ranges are honest and the trained layer makes them tighter.** Both versions catch about 80 %, as designed.
   The trained version does it with ranges 4 to 6 % narrower for the future from 5 minutes on, and 5 to 10 % narrower
   for premiums. That is the gain: a sharper statement of how far things can go, at the same reliability.
2. **Where the premium will be is not forecast better than "no change".** The middle forecast matches "no change" to
   the second decimal at every horizon. The chance-of-profit numbers score 0.250, a coin.
3. **The futures direction calls look good and do not help premiums.** On clear 1-minute calls the direction was
   right 66 % of the time, in both versions: that is the feed lead-lag of section 4. The option layer's learned use
   of that drift did not improve its middle forecast.
4. The "+5 % or -5 % first" probabilities: 0.217 against 0.220 (lower is better), a small gain.
5. So the forecaster's real, repeatable outputs are: how much movement to expect, the range of the future and of
   each premium, what decay costs, what move pays for it, and what each scenario would return. It does **not** know
   which way the market will go beyond a few seconds of feed timing. The panel's "what I would do" stays flat unless
   its own record that day says otherwise.

## 8. Nightly learning

After each close: `py -3.13 research/forecast_lab/nightly.py <day>`. It converts the tape, collects the day and refits
the trained layer on every session; the previous file is kept. The online layer carries over by itself.

## 9. The overnight replay p43 (the one long job)

`data/replay/batch/predict_2026-11-10/run_p43.py`. All 16 sessions, 106 books, the missed-signal recorder ON, on the
code frozen for 12 Nov. Eight runs at a time, two tapes each. Anything unfinished at 08:10 is stopped. It gives: the
champion's untraded triggers (for the admission model), the first chronological test of the forecast books on the
hazard model, the re-entry twin's first evidence, and the full-batch contract check.

## 9a. Idle step time of the frozen engine

One process alone, today's tape (11 Nov), 25 minutes of wall time, market 09:16 to 12:08, 106 books, the hazard
forecaster loaded through the registry, the publish change in:

| Market hour | Median step | 95th percentile | Worst step | Steps over 300 ms | Publish, ms a step | Forecast feed, ms a step |
|---|---|---|---|---|---|---|
| 09:16 to 10:15 | 8.9 ms | 22.9 ms | 419 ms | 1 | 0.19 | 0.23 |
| 10:16 to 11:15 | 9.0 ms | 21.9 ms | 190 ms | 0 | 0.18 | 0.23 |
| 11:16 to 12:08 | 11.9 ms | 32.0 ms | 173 ms | 0 | 0.31 | 0.31 |

Today was a quiet day with few entries, so this is the engine's floor, not a busy-day figure. The afternoon is not
covered. Live today, on a machine at 90 % load from other projects, the median was 25 to 60 ms.

## 10. Still open

- The admission model: waits for p43's untraded triggers.
- The hold-or-sell model: built in the afternoon, never earned an action (docs/49).
- Fill-parity differences traced row by row.
- Idle step time of the frozen engine over a whole day.
- The six single-mechanism shadow experiments of docs/42 beyond the re-entry twin.

## 11. Night of 11 Nov: every sentence earned, input age shown, nightly promotion check

After the second outside review (the advice gate, stale inputs, mixed methods shown as one forecast).

- `core.earned(panel)` decides what may be stated, from the forecaster's own checked forecasts only, after cutting
  overlapping forecasts down to roughly independent checks (count x cadence / horizon).
  Direction: 20 independent clear calls, 60 % right, score better than "no move".
  Buy case: the OPTION forecasts at that holding time must beat a coin (Brier 0.01 under the base) and beat "no
  change", on 20 independent checks. A futures record never earns an option statement.
- `commentary` states measured facts and earned forecasts only. Not earned: "Direction: no call." and "Flat. There is
  no buy case." No exit level is ever given; a held contract gets its range and nothing else. The barrier
  "head to head" with the engine model is removed (the two score different outcomes).
- Input age: the live runner passes the futures quote's age; older than 5 s shows "No forecast"; an option simulation
  older than 20 s is not shown; the panel header prints each age.
- Panel wording: "Verdict", "call candidate / put candidate / held position", "Shadow book forecasts" for the engine
  model; win chance and expected return are shown only at holding times that have earned them.
- `research/forecast_lab/nightly.py`: appends the unseen-day score of the models that ran to
  `data/forecast_lab/record.jsonl`, refits, and replaces `brain.joblib` only if (a) the fresher models were not more
  than 2 % worse than the older ones on that unseen day and (b) the candidate is sane. Dry run on 11 Nov with models
  fitted through 9 Nov: volatility loss 0.1495 against 0.1442 for the 10-minute clock (better on 3 of 7 horizons),
  80 % range caught 76.7 %, and worse than the models fitted through 6 Nov (0.1358). On that day the trained layer
  did NOT beat the simple clock. One day is noisy; the record file is there so this is judged over many days.
- Tests: tests/test_forecast_lab.py, 14 passed (three new: only an option record earns a buy statement; the commentary
  says only what is earned; a stale futures quote shows no forecast).
