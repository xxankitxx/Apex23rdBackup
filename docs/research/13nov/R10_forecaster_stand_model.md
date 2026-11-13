# R10. The forecaster taking a clear stand (owner point 4, model side)

13 Nov 2026, during the session. Analyst R10. Display and research only: nothing here changes the Conductor, the pool
or any book. Scratch work: `data/research/13nov/work/R10/`.

## Findings first

1. **Why the page says WAIT all day.** The live verdict reads one number: the 2-minute pooled mean divided by its sd
   (`core.py:2506-2513`, thresholds 0.15 and 0.35 at `core.py:2575-2578`). In today's live file (13:50) that ratio is
   0.07. Two causes, both in the code: (a) the trained experts that carry the real skill (ridge, trees) hold only 4 to
   9 % of the pool weight at 1 to 5 minutes, so the pooled mean is diluted 5 to 10 times; (b) the variance calibration
   `kappa` has grown to 2.3 to 4.9 at 2 to 10 minutes, so the sd in the ratio is about twice the real size. The 80 %
   ranges still look right because the conformal factor shrank to about 0.5 to make up for it. Two calibrators are
   pulling against each other, and the lean pays for it. Today's feed shows one "TILT TO CALLS" in 4.5 hours. It
   lasted 35 seconds.
2. **There is real direction skill, and it can be stated honestly.** I fused the six horizon forecasts (1 to 15
   minutes) into one probability of "up over the next 2 minutes", then recalibrated it each day on earlier unseen
   days only. It is well calibrated: the error between stated and realised odds is about 2 points. When it says 60 to
   65 %, it was right 61 % (27 Oct to 4 Nov) and 60 % (5 to 11 Nov). When it says 56 % or more, it was right on 8 of
   9 test days.
3. **But almost all of that skill lives in the first 30 seconds.** If the move is measured from 30 seconds after the
   call, the 1-minute IC falls from +0.181 to +0.016, and the top fifth of calls falls from 65 % to 52 %. The model
   is reading the options' forward and the heavyweight stocks moving before the recorded futures quote. It is a
   nowcast of where the futures quote is being pulled, not foresight. Options already price it (docs/50).
4. **A stand that does not flicker has no edge on these days.** Every stable version I tried was close to a coin toss
   on the late days. That covers hysteresis capped at 12 changes an hour, a 30-second hold, a slow 10 to 15 minute
   model, and today's own follow-or-fade record. The live 30-second hold alone cuts the 2-minute hit from 55-60 % to
   51-53 %. So the stand needs two layers: a needle with no hold for the next 1 to 2 minutes (the part with skill),
   and a slower stance word with its own measured odds, which are near 51 to 53 %.
5. **"How the market is behaving" is a description, not a forecast.** Labels from fixed thresholds (trending,
   breaking out, reversing, chopping, drifting) flip their meaning between windows. "Trending up" carried on 33 to
   46 % of the time in the early window (the moves reverted) and 55 to 63 % in the late window. Raw labels change
   every 10 to 20 seconds. The label must be shown as a fact about the last 5 to 30 minutes, held for at least 60
   seconds, and never sold as a prediction.
6. **Heavyweights add a little, and only to the nowcast.** Taking the five breadth and lead inputs out lowers the
   1-minute IC from +0.181 to +0.165. With a 30-second delay they add nothing. The option-surface inputs matter most:
   without them the 1-minute IC is +0.115. A small model on heavyweights and order flow alone is the best of the
   delayed models (IC +0.027 at 1 to 3 minutes, positive on 8 or 9 of 11 days). That is still too weak to trade.
7. **Do not use the stand as a Conductor filter.** On 78 Conductor entries, those taken with a strong pull in the
   trade's direction did worst (49 % won). Those taken against it all won (10 of 10, but 9 of the 10 are in the early
   window). "Skip when the stand agrees" raises the early strike rate (57 % to 67 %) but lowers the return in both
   windows. It fails the promotion standard.

What the stand must say when its skill is weak: it still leans, it gives its odds in whole per cent, it says "close to
a coin toss" whenever those odds are under 55 %, and it quotes its own record for that odds bucket. It never says
"no call".

## Teardown (what the code does, where it fails)

| # | Where | What it does | Where it fails |
|---|---|---|---|
| T1 | `core.py:2506-2513` `_lean_of` | Lean = mean / sd at 2 minutes (1 minute near the close) | Uses only one horizon of the pooled forecast. Ignores the 1, 3, 5, 10 and 15 minute rows, the breadth and the flow it already has |
| T2 | `core.py:829` | `sd = sqrt(sig^2 + spread of the experts' means)` | The experts' disagreement makes sd bigger, so the lean shrinks exactly when the trained experts disagree with "no move". Live 13:50: the 10-minute sd (61.7) is larger than the 15-minute sd (41.2), so the ladder's 10-minute range is wider than its 15-minute range |
| T3 | `core.py:876` with `core.py:818` | `kappa` scales the variance by the mean of (move / sd) squared | With fat tails (kurtosis 4 to 6, walk_forward.json) the mean square is driven by a few jumps. Live: kappa 1.49, 2.28, 2.99, 3.91, 4.87, 1.48, 1.05 by horizon. The 5-minute sd shown is 39.7 points, but the 80 % range is only 50.6 points wide, which implies a typical sd near 20 |
| T4 | `core.py:878`, `core.py:834` | Adaptive conformal factor `z80` for the 80 % range | It compensates for T3 (live cf about 0.5), so the ranges stay on target. The lean ratio and the "I forecast 17.7 points a minute" sentence (`core.py:1573`, `core.py:2141-2146`) use the inflated sd, and they tell the owner "more movement than options price" when realised is 13.1 against 12.1 implied |
| T5 | `core.py:185-201` Hedge, `core.py:874` | Expert weights from CRPS with eta 2 and a 1 % share | Live weights at 1 to 5 minutes: ridge 0.045 / 0.09 / 0.069 / 0.051, trees 0.08 / 0.048 / 0.054 / 0.036. The walk-forward evidence that ridge has IC +0.18 at 1 minute is never used for the stance. CRPS is mostly about spread, not about direction |
| T6 | `core.py:2516-2523` `_conf` | Confidence = today's hit rate, if 10 independent clear calls exist | Clear calls need |mean| of at least 0.15 sd (`core.py:889`). With T2 and T3 they almost never happen: live at 13:50 there were 80 clear 2-minute calls, about 3 independent, so the page shows "confidence: untested today" for most of the day |
| T7 | `core.py:2330` `PAST_LEAN_HIT` | Hard-coded 67 / 60 / 59 / 55 % | These are for the ridge expert alone, top fifth, from walk_forward.json. The page applies them to the diluted pooled lean, which is a different signal |
| T8 | `core.py:2014-2034`, `BUY_MIN_DAYS = 5` (`core.py:84`) | Direction must be "earned": 20 independent calls, 60 % right, 5 forward days | Correct as a guard on claims, but it turns the commentary into "Direction: no call" (`core.py:2133`), which is exactly what the owner does not want. A stand with honest odds is a different statement from an earned claim. Both can be shown |
| T9 | `core.py:1556-1560` regime | trending if VR > 1.25 and ER > 0.3, choppy if VR < 0.8, else mixed | No direction ("trending" which way?), no breakout or reversal, no hold time. The feed holds the word 60 s (`core.py:1676-1685`), but the panel's own `regime` changes on every 5-second origin |
| T10 | `core.py:1790-1801` `_up_from_quantiles` | P(up) read off the five quantiles | It carries the training days' median drift in `qz[2]`, and it is not calibrated. Live: 15 minutes "59 % up", at a horizon with no skill (IC about 0) |
| T11 | `core.py:1648-1691` `_feed_step` | A new verdict word shows only after 30 s | Measured: a 30-second hold on the 2-minute signal cuts its hit from 55-60 % to 51-53 %. The skill is gone by the time the word appears |
| T12 | `apex/static/app.js:1792` | Shows `verdict.word` and "confidence: high / medium / low / untested today" | No probability, no horizon, no record. The owner cannot tell a 51 % lean from a 61 % one |

## Evidence

Data: `data/forecast_lab/collect/<day>.joblib`, 16 sessions from 19 Oct to 11 Nov (12 Nov is not collected).
Converted once to `work/R10/cache/*.npz`. Rows are 5 seconds apart, about 4,350 a day. Targets are the futures' move
over h, standardised by the 10-minute reference volatility. Walk-forward with an expanding window: for each test day
(27 Oct to 11 Nov, 11 days) the ridge models (alpha 3000, the brain's setting) are fitted on the earlier days only.
Inputs are scaled with the first five days' medians and sds. "Independent" counts = rows x 5 s / horizon. Hit = sign
right, zero moves dropped. Returns are not involved: this is a direction study.

### E1. Ablations (mean over 11 test days; IC, top-fifth hit, days with IC above 0)

| Model | 1 min | 2 min | 3 min | 5 min | 10 min | 15 min |
|---|---|---|---|---|---|---|
| all 46 inputs | +0.181, 64.8 %, 11 | +0.114, 59.3 %, 11 | +0.093, 58.2 %, 11 | +0.048, 55.7 %, 8 | +0.018, 54.7 %, 5 | -0.010, 51.3 %, 5 |
| without heavyweights | +0.165, 63.6 %, 11 | +0.103, 59.0 %, 11 | +0.083, 57.4 %, 10 | +0.042, 54.6 %, 9 | +0.017, 54.4 %, 6 | -0.012, 51.2 %, 5 |
| without order flow | +0.181, 65.4 %, 11 | +0.113, 59.6 %, 11 | +0.092, 58.5 %, 11 | +0.052, 56.4 %, 8 | +0.027, 56.1 %, 7 | +0.005, 54.1 %, 5 |
| without option surface | +0.115, 58.9 %, 11 | +0.072, 55.9 %, 11 | +0.057, 55.7 %, 10 | +0.020, 54.5 %, 6 | -0.001, 54.6 %, 4 | -0.024, 50.9 %, 5 |
| without the 5 lead inputs | +0.091, 56.4 %, 11 | +0.051, 54.4 %, 10 | +0.040, 54.8 %, 7 | +0.007, 53.0 %, 4 | 0.000, 53.6 %, 4 | -0.023, 50.0 %, 5 |
| price only | +0.023, 51.8 %, 8 | +0.003, 50.6 %, 6 | +0.006, 52.3 %, 6 | +0.001, 53.2 %, 6 | 0.000, 57.0 %, 4 | -0.017, 53.6 %, 5 |
| heavyweights + flow only | +0.120, 59.9 %, 11 | +0.088, 56.1 %, 11 | +0.073, 55.9 %, 11 | +0.025, 54.0 %, 11 | -0.024, 51.7 %, 3 | -0.044, 48.0 %, 4 |

Same models, move measured from 30 seconds after the call (the feed lead-lag removed):

| Model | 1 min | 2 min | 3 min | 5 min |
|---|---|---|---|---|
| all 46 inputs | +0.016, 52.0 %, 8 | +0.016, 52.3 %, 7 | +0.023, 53.0 %, 8 | +0.004, 53.3 %, 4 |
| without heavyweights | +0.013, 52.2 %, 7 | +0.015, 51.5 %, 7 | +0.022, 52.5 %, 8 | +0.003, 53.3 %, 4 |
| without order flow | +0.008, 51.3 %, 6 | +0.004, 51.9 %, 5 | +0.016, 53.2 %, 8 | +0.007, 53.8 %, 6 |
| heavyweights + flow only | **+0.027, 52.7 %, 9** | **+0.028, 53.4 %, 8** | +0.024, 53.8 %, 8 | -0.015, 51.3 %, 5 |

### E2. The fused stand, recalibrated (Platt fitted on earlier test days' unseen rows; scored 29 Oct to 11 Nov)

Fusion: the logistic `L = a0 + sum over h of a_h zhat_h` for "up over Hs", fitted on the training days. The raw
fused odds are too confident on unseen days (stated 0.62, realised 0.56 at 3 minutes). The Platt slope that fixes
this is 0.58 to 0.73, steady from day to day.

2-minute stand (Hs = 120 s):

| Stated odds | Early: share, realised (indep) | Late: share, realised (indep) |
|---|---|---|
| 50-53 % | 28.8 %, 50.9 % (259) | 34.7 %, 50.0 % (249) |
| 53-56 % | 27.2 %, 53.8 % (244) | 33.1 %, 52.3 % (238) |
| 56-60 % | 26.8 %, 54.9 % (241) | 23.1 %, 56.0 % (166) |
| 60-65 % | 13.5 %, **61.1 %** (122) | 7.2 %, **60.4 %** (52) |
| 65 % and up | 3.6 %, 67.6 % (33) | 1.8 %, 48.7 % (13) |
| Calibration error | 0.013 | 0.021 |

Hit at stated odds of 56 % or more, per test day: 29 Oct 57.5 %, 30 Oct 59.6 %, 2 Nov 60.7 %, 3 Nov 54.0 %, 4 Nov
55.1 %, 5 Nov 58.2 %, 6 Nov 64.6 %, 9 Nov 53.7 %, 11 Nov 52.1 %. 9 of 9 days above 50 %.

3-minute stand: same picture, a little weaker (56-60 %: 55.7 % early and 55.5 % late; at 56 % or more, 8 of 9 days
above 50 %, and 11 Nov at 48.0 %). With the 30-second delay, the recalibrated stand stays at 51 to 54 % in every
bucket. Its late hit of 53 % comes from the up-drift: the base rate of an up move was 57 % on 5 to 11 Nov.

### E3. Stability against skill (the flicker trade-off)

| Display rule (on the 3-minute fused odds) | Chosen on | Early hit / time shown / changes an hour | Late hit / shown / changes an hour |
|---|---|---|---|
| none (word = odds above 56 %) | | | 54.6 % / 32 % / 170 |
| Schmitt 0.62 / 0.54, no smoothing, no dwell (32-variant grid, best early) | early | 54.8 % / 37 % / 49 | 53.1 % / 13 % / 28 |
| Same grid, capped at 12 changes an hour (36 variants): EWMA 30 s, 0.58 / 0.53, 60-s dwell | early | 51.6 % / 47 % / 10.6 | **46.4 %** / 14 % / 6.1 |
| 5-minute version, same cap | early | 51.5 % / 62 % / 5.0 | **44.8 %** / 26 % / 2.2 |
| Frozen rule: 2-minute odds, 0.56 / 0.53, plus the live 30-second hold | fixed before the run | 53.0 % (2 min), 52.4 % (1 min) | 51.1 % (2 min), 52.4 % (1 min) |

Inside NEUTRAL, under the frozen rule, the lean (odds above or below 50 %) was right 54.0 % early and 53.5 % late at
2 minutes. That is better than the held word itself, because the lean is never stale. The frozen rule changes word
16 to 23 times an hour. The live words with the 30-second hold change about 7 times an hour (the ridge analogue).
Per day under the frozen rule, 2 minutes: 53.6, 54.4, 55.8, 47.0, 51.2, 55.8, 54.2, 50.7, 44.7 %.

### E4. Slow stands and today's persistence (all failed)

| Idea | Early | Late | Verdict |
|---|---|---|---|
| Slow 10-minute model (trend, VWAP, range, breadth), stable display | 49.0 % | 59.6 % | IC below 0 on 7 of 11 days. The late "hit" is the 57 % up base rate |
| Slow 15-minute model | 47.5 % | 59.4 % | IC below 0 on 7 of 11 days |
| Follow or fade the last 5-minute move by today's matured record, 3 minutes | 53.2 % (89 indep) | 44.7 % (28 indep) | fails |
| Same, 5 minutes | 32.4 % (10) | 38.4 % (8) | too few, fails |

### E5. Behaviour labels (fixed thresholds, one variant; follow rate = the next move goes the label's way)

| Label | Early share | Early follow 3 / 10 min | Late share | Late follow 3 / 10 min |
|---|---|---|---|---|
| breaking out up | 0.7 % | 43.7 / 58.4 % | 1.8 % | 58.4 / 62.2 % |
| breaking out down | 0.7 % | 54.8 / 66.0 % | 0.6 % | 56.5 / 13.0 % |
| reversing up | 0.2 % | 37.1 / 28.9 % | 0.4 % | 82.1 / 95.5 % |
| reversing down | 0.4 % | 42.4 / 56.9 % | 0.8 % | 46.2 / 39.8 % |
| trending up | 5.8 % | 32.5 / 45.9 % | 5.7 % | 54.9 / 62.7 % |
| trending down | 5.0 % | 45.2 / 47.9 % | 3.9 % | 43.7 / 36.5 % |
| chopping | 65.5 % | 52.2 / 51.6 % | 67.1 % | 51.2 / 49.8 % |
| drifting | 21.8 % | 49.4 / 51.9 % | 19.8 % | 50.2 / 50.9 % |

The rare labels hold 30 to 300 rows, which is only 2 to 20 independent events. Median run lengths of the raw labels
are 10 to 20 seconds.

### E6. Conductor entries against the 2-minute stand (78 entries, 27 Oct to 11 Nov, replay p44)

| Window | Stand with the trade (odds of 56 % or more) | Neutral | Against (44 % or less) |
|---|---|---|---|
| Early | 20 trades, 45 % won, +2.7 % mean | 18, 50 %, +5.6 % | 9, 100 %, +15.1 % |
| Late | 15, 53 %, +3.3 % | 15, 53 %, +5.5 % | 1, 100 %, +41.4 % |

"Skip when with": early 47 to 27 trades, won 57 % to 67 %, compounded +703 % to +504 %, without the best trade +347 %
to +236 %. Late 31 to 16 trades, won 55 % to 56 %, compounded +216 % to +160 %. The return is lower in both windows,
so it fails the standard. This matches docs/54. A plausible reason: c20 buys the pullback, and the pullback is when
the futures are being pulled against the trade.

Variants tried in total: 16 ablations, 6 fused stands, 32 + 32 + 36 + 36 hysteresis settings, 3 recalibrations, 8
persistence tests, 1 label set, 2 slow stands, 1 frozen display rule, 2 Conductor filters. That is about 175, so any
single good number in a grid is suspect. The calibration result (E2) involves no search: fixed horizons, a fixed
ridge strength, one Platt step.

## The STAND design (formulas)

Everything below runs on the 5-second origin in `Lab._origin` (`core.py:806`). It uses the brain's ridge output that
is already computed (`Brain.drift`, `brain.py:204`), so the extra cost is a few dot products, well under 0.1 ms.

**1. The pull: odds for the next 2 minutes (the part with skill).**
- `zhat_h` = the ridge expert's standardised mean for h in (60, 120, 180, 300, 600, 900) s (`bx[0]` in `_origin`).
- `L = a0 + sum_h a_h * zhat_h` (fusion weights fitted nightly on leave-one-day-out `zhat`; for the 3-minute version on 11 Nov the weights were
  about -0.005, 0.003, 0.67, 1.03, 0.24, -0.99, 0.72).
- `p_up = 1 / (1 + exp(-(c0 + c1 * L)))`, where `c0, c1` come from a Platt fit on every earlier day's unseen rows
  (c1 about 0.6, c0 about 0.14).
- `odds = round(100 * max(p_up, 1 - p_up))`. `lean = up if p_up >= 0.5 else down`.
- Shown every 5 seconds with no hold. It is a needle, not a word.

**2. The stance word (stable, with its own honest odds).**
- State machine on `p_up`: go BULLISH when `p_up >= 0.56`, or BEARISH when `p_up <= 0.44`. Back to NEUTRAL when
  `p_up` crosses 0.53 (or 0.47 for BEARISH). A new word is shown only after it has held 30 seconds, and stays at least
  60 seconds.
- Its odds are NOT `p_up`. They are the measured hit of the shown word in the nightly record (about 51 to 53 %), so the
  page never claims more for the word than it earned.

**3. Skill grade (decides the wording).**
- From the odds table for the current bucket: `real` if realised minus 0.5 is at least 0.05 and the bucket was above
  50 % on at least 70 % of days; `weak` if it is at least 0.02; `none` otherwise.
- Today's matured record (as `earned()` does now) can only downgrade the grade, never upgrade it.

**4. Behaviour label (a description, held).**
- Priority order: breaking out (at the day's high or low, 5-minute move of at least 1 sd, after 09:45), reversing
  (30-minute move of 1.5 sd or more one way, then 2 minutes of 1 sd or more the other way), trending (ER300 at least
  0.30, 5-minute move at least 0.7 sd, Kalman slope agreeing), chopping (ER300 under 0.15 or VR under 0.7),
  otherwise drifting with its sign. (`labels.py:label` has the exact code.)
- Shown only after it has held 60 seconds, kept at least 120 seconds. It always comes with its facts in points: the
  5- and 30-minute moves, the distance from VWAP, and the distance from the day's high and low.

**5. First-person commentary templates (no "no call").**
- Real: "I am BULLISH for the next 2 minutes: 61 % up. The futures are behind the options and the heavyweights, which
  are already higher. Calls like this were right 61 % of the time on 9 unseen days. Past 2 minutes I have no edge."
- Weak: "NEUTRAL, leaning up: 53 % up over the next 2 minutes. That is close to a coin toss. Calls this weak were
  right 52 to 53 % of the time. I would not act on direction now."
- Behaviour: "The market is trending up: +34 points in 15 minutes, 22 above VWAP, and moves are carrying through."
- What I would do, flat: "I would wait. A call needs +6 points in 5 minutes to pay for decay, and my edge does not
  reach 5 minutes." Holding a CE with the pull against it: "The pull is against your call for the next minute. This is
  often the pullback your entry bought (on past entries, 'against' was not a reason to exit)."

## Data contract (new key `stand` in the panel; `plain.verdict` stays for compatibility)

| Field | Type | Meaning |
|---|---|---|
| `stand.v` | int | contract version, 1 |
| `stand.word` | "BULLISH", "BEARISH", "NEUTRAL" | the held stance word |
| `stand.lean` | "up" or "down" | always present, also inside NEUTRAL |
| `stand.since`, `stand.held_s` | "HH:MM:SS", s | when the shown word began |
| `stand.word_odds` | int % | measured hit of the shown word (nightly record) |
| `stand.pull.p_up` | 0 to 1 | calibrated 2-minute odds, updated every 5 s, no hold |
| `stand.pull.odds` | int % | round(100 x max(p_up, 1 - p_up)) |
| `stand.pull.t` | epoch s | origin time of the odds (the page greys it out after 15 s) |
| `stand.skill` | "real", "weak", "none" | grade for the current odds bucket |
| `stand.record` | {said, got, indep, days_above_half, days} | the odds-table row for this bucket |
| `stand.horizons` | [{h, p_up, got}] | calibrated odds and record at 1, 2, 3, 5, 10 and 15 min (beyond 3 min it shows about 50 %) |
| `stand.drivers` | [{group, share, sign}] | the top three input groups in L: options forward, heavyweights, order flow, momentum, position |
| `stand.heavy` | {up_w, bank_minus_rest_pts, lead_pts} | weight-weighted share of heavyweights up over 60 s; bank against rest; lead over the futures |
| `stand.behaviour` | {label, since, held_s, r300_pts, r1800_pts, vwap_pts, to_high_pts, to_low_pts, er, vr} | the held label and its facts |
| `stand.say` | [str] | first-person sentences, in the order: stand, behaviour, what I would do, record |
| `stand.why_weak` | str or null | the reason when skill is not "real" |
| `stand.stale` | bool | the futures quote is more than 5 s old |
| `stand.model` | {built, trained_through, hash} | which `stand_model.json` is in use |

The UI shows the word big, the needle under it with "% up, next 2 min", and the record in one line. The behaviour
label goes beside it. Ranges move below as a secondary row.

## Ideas

| # | Idea | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|
| 1 | Calibrated fused pull needle | Six horizon forecasts into one logistic, Platt on unseen days | **Tested.** ECE 0.013 / 0.021. 60-65 % bucket right 61 % / 60 %. 9 of 9 days above 50 % at 56 % or more | `phaseB_stand_fit.py` writes `stand_model.json`; a `stand()` function in core next to `verdict()`; shadow key `stand` | It is a lead-lag nowcast. It must be labelled "next 1-2 minutes" and must never feed an entry |
| 2 | Stance word with measured odds | Schmitt 0.56 / 0.53, 30-s hold, odds from its own record | **Tested.** Hit 51-53 %, 16-23 changes an hour | Same function; the word's odds are read from the record, not from p_up | The owner may read the word as a call. The text must carry the odds |
| 3 | Fix the lean scale | Use calibrated p_up, or a robust sd = (q75 - q25) / 1.349, instead of mean / (mean-square sd) | Snapshot evidence only (kappa 3.9, cf 0.5, z = 0.07). **Untested on tapes** | Phase B tape replay of the lab with `_lean_of` reading p_up; compare how often each word shows | Changes what the old commentary says; keep `earned()` as the gate for claims |
| 4 | Stop kappa and z80 fighting | Calibrate kappa on a robust statistic (median of z squared / 0.455), or freeze it within [0.5, 2] while running | **Untested.** Snapshot: kappa up to 4.87 at runtime, against KAPPA_OK (0.5, 2.0) on load (`core.py:42`) | Shadow Lab instance on the 13 Nov tape after the close | Range coverage must stay 72-88 %. Check with `earned()` |
| 5 | Monotone ranges | Make sd non-decreasing in h (cumulative max) before the ladder | **Untested.** Live 10-minute sd 61.7 against 15-minute 41.2 | One line after `core.py:829` (display copy only) | None for scoring if applied to the display copy |
| 6 | Calibrated per-horizon odds instead of `_up_from_quantiles` | Platt per horizon; remove the training median drift | **Untested** for the quantile version. The fused version is tested (idea 1) | `stand.horizons` | Shows about 50 % beyond 3 minutes, which is honest but dull |
| 7 | Held behaviour label with facts | Fixed priority labels, 60-s enter, 120-s keep | Raw labels tested: descriptive only, follow-through flips between windows. **Held version untested** (`phaseB_behaviour_hyst.py`) | `stand.behaviour` | Must never be phrased as a forecast |
| 8 | Heavyweight and flow nowcast for the delayed horizon | Small model (10 inputs) is the best delayed model | **Tested.** IC +0.027 against +0.016 for all inputs; 52.7-53.8 % top fifth | A second needle, "after 30 s", shadow only | Too weak for trading; multiple-testing risk (16 ablations) |
| 9 | Skill decay map by delay | Where between 0 and 30 s the skill dies | **Untested** (`phaseB_lag_decay.py`) | Tells the owner how fast the needle goes stale; sets the 15-s grey-out | None |
| 10 | Conductor "skip when the stand agrees" | Pullback entries do better when the pull is against them | **Tested. Fails**: return lower in both windows | Do not build | |
| 11 | Today's follow-or-fade | Learn within the day whether moves continue | **Tested. Fails** (late 44.7 %) | Do not build | |
| 12 | Slow 10-15 minute stand | Trend, VWAP, range, breadth | **Tested. Fails** (IC below 0 on 7 of 11 days at both horizons) | Do not build | |

Sister indices (BANKNIFTY, FINNIFTY): the collected features have no sister-index inputs. Only `bank120`, from the
bank heavyweights, is there. The contract leaves room (`stand.drivers` group "sister indices") for the sister-index
analyst's inputs once they are collected into the tape.

## Phase B scripts (ready, not run; after 15:30, one at a time, `py -3.13`)

| Script | What it does | Run time |
|---|---|---|
| `data/research/13nov/work/R10/phaseB_lag_decay.py` | Walk-forward skill at delays 0, 5, 10, 15, 20, 30, 45 and 60 s for 1 to 3 minutes. Reads the 16 joblibs one at a time | about 3 min |
| `data/research/13nov/work/R10/phaseB_stand_fit.py` | Builds `work/R10/stand_model.json`: final ridge, fusion weights, Platt, odds table by bucket and day | about 1 min |
| `data/research/13nov/work/R10/phaseB_behaviour_hyst.py` | The held behaviour labels: run lengths, follow rates, early against late | under 1 min |

Scripts already run (light, under 3 min each): `cache.py`, `study2.py`, `sum1.py`, `sum2.py`, `recal.py`,
`labels.py`, `slow.py`, `final_rule.py`, `conductor_agree.py`. Results: `study2.json`, `sum2.json`, `recal.json`,
`labels.json`, `stand_rows.npz`. Live snapshot used for T2-T6: `work/R10/fl_snapshot.json` (copied at 13:50).

## Limits

- 16 sessions, all studied before by other work; 12 Nov and 13 Nov are not collected.
- My ridge uses the 10-minute reference sd as the scale, not the brain's volatility model. Signs and ranking are the
  same, but the weights differ a little.
- The fusion weights in E2 were fitted on the training days' in-sample `zhat`. The Platt step corrects the
  over-confidence that causes.
- E6 uses the probability at the entry second, from models fitted on earlier days. The Conductor's later trades would
  change if it skipped one, so E6 is approximate. A shadow book replay would settle it.
