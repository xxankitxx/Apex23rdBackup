# 48. The Forecast Lab: a path forecaster with decay, commentary and self-scoring

11 November 2026, built during the live session on the owner's request: "I hate the forecast model you have created.
It does not forecast shit. It does not even take and register the decay ... does not let us know what will happen
next and then next and then next ... add your commentaries ... keep improving yourself in retrospect ... no delay in
display and code running ... lightning fast."

The research behind it is in `docs/47_ADVANCED_FORECASTING_RESEARCH.md` (88 references). This document says what was
built, how it works, how fast it is, and what the evidence says so far. **Display and research only: nothing here
places, changes or blocks a trade.** "No losing trade" is unmet.

## 1. What it is

A separate process, `apex/forecast_lab/live.py`, started with:

```
py -3.13 -m apex.forecast_lab.live
```

- It reads the feed's shared-memory table **read only**, once a second, the same table the engine reads.
- It never writes to the shared table and never calls the engine. Every 5 s it reads `/api/state` once, for the
  account's state, the held contract, and the old model's numbers.
- It writes `apex/static/live/forecast_lab.json` once a second. The gateway serves the static folder from disk, so
  the dashboard picks it up with no restart of anything.
- It runs at below-normal priority on one thread, so the engine always wins the processor.
- It stops at 15:40, on Ctrl+C, or when `data/forecast_lab/STOP` exists. It saves its learning every minute and at
  exit to `data/forecast_lab/state.json`. Today's scoreboard survives a restart.

The dashboard's Forecast panel now sits directly under the position band. It polls that file once a second on its
own, separate from the engine's state stream.

## 2. What it forecasts, and how

Every 5 seconds:

| Output | Method |
|---|---|
| Nifty futures at +1, 2, 3, 5, 10, 15, 30 min | A distribution, not a point. Mean: five competing experts (no move, momentum, order flow, reversion, all signals), each a recursive least-squares regression with forgetting, combined by an exponentially weighted forecaster with fixed share that moves weight to whoever has actually been right. Spread: three realised-volatility clocks (2, 10, 30 min) and the options' implied volatility, rescaled by its own matured errors; the 80 % range width is tuned by adaptive conformal inference to catch 80 % |
| Each candidate option's premium at the same horizons | 600 simulated paths of the future; on each path the implied volatility moves by the measured spot-vol beta, today's measured volatility trend and a residual; each path is repriced with Black-76 as time to expiry runs down. So decay, volatility drift and the move are inside one number |
| Decay alone | The same option repriced with the future and volatility unchanged, only time passing: the dotted line on the chart |
| If bought now | Expected result after the spread (buy at the ask, sell at the bid), and the chance of a profit, at each horizon |
| Break-even move | How far the future must move by each horizon for that purchase to make money after decay and the spread |
| Which comes first, +5 % or −5 % of the premium within 5 min | From the simulated paths, on a 10-second grid. Kept for a head-to-head with the old model on the same cases |
| 5-minute change split | delta, gamma, vega and theta parts |
| Decay register | For the strikes around the money: decay on the trading clock (a day's decay over 375 minutes, the engine's and the champion's convention), on the calendar clock, the calendar clock with today's volatility trend, and the decay **measured from the quotes** (the premium change not explained by the future's move, last 30 minutes) |
| Gamma rent | The per-minute move that pays a trading minute's decay, `sqrt(2 x theta / gamma)`, against the movement actually delivered in the last 10 and 30 minutes. Below 1.00 buyers lose to time. This is why the champion has not traded today |
| Candidates | The call and put the engine would buy now (the engine's own pick when it reports one), the at-the-money pair, and the account's held contract |

## 3. Commentary: what I see, what I would do, what would change my mind

Built only from the numbers above, in sections: right now; next, then next, then next; time decay; what I would do;
what would change my mind; how my forecasts have done today; the account.

The "what I would do" rule:
- It recommends a buy only if the expected result after the spread is above +1 % with a profit chance above 55 %,
  **and** its own 5-minute futures forecasts have beaten "no move" today on at least 30 checked cases.
- Without that record it says the numbers favour a purchase but it would not act yet, and why.
- Otherwise it says to stay flat, with the break-even move each option needs against the move it expects.
- It is advice on the screen. It places no order. Each change of advice is logged to
  `data/forecast_lab/advice_<day>.jsonl` for later checking.

## 4. Self-scoring and learning

Every forecast is kept until each horizon has passed, then scored against what happened:
- futures: inside the 80 % range or not, CRPS against "no move", against the morning's frozen copy of itself,
  and direction on clear calls;
- options: middle forecast error against "no change" and "decay only", band coverage, profit-chance Brier score;
- the +5 % / −5 % race, against the old model on the same cases.

Each check teaches: expert coefficients, expert weights, the volatility scale, the range multiplier, the option band
bias and scale, and the spot-vol beta and volatility trend. Forecasts made 5 seconds apart over a 5-minute horizon
share most of their outcome, so each counts as a fraction of one observation (one unit per 5 minutes of new outcome).
A frozen copy of the morning's models is scored beside the learning one, so the panel shows whether learning helped.

## 5. Speed

| Measure | Value |
|---|---|
| Forecaster, live, average | about 21 ms of processor time a second (2 % of one core), below-normal priority |
| Its simulation | about 70 ms every 5 s |
| Engine step before and after it started, 11 Nov | median 42 and 39 ms, 95th percentile 136 and 137 ms: no measurable effect |
| Old forecast panel inside the engine | 0.3 to 0.5 ms a publish (still there, for the four forecast books) |

The engine's own slowness today comes mainly from its publish (40 to 65 ms per publish, 4 a second) and from a
machine at 90 to 96 % processor load from other running projects. A publish change is ready (section 7) and takes
effect only when the engine is restarted.

## 6. Evidence so far

- Warm start: learned on 14 recorded sessions, 19 Oct to 6 Nov (`data/forecast_lab/state_warm.json`).
- Test: 9 Nov, which the warm start did not see. Results in section 8, written when the run ends.
- Honest expectation from docs/45 and docs/47: the 80 % ranges should be well calibrated; the direction experts add
  little; the decay and break-even numbers are the most useful part. The panel says so when it is so.

## 7. Engine publish change, prepared, not live

`apex/engine_main.py` `_slow_parts`, `apex/table.py` `write_state(raw=...)`, `dumps_part`. The three big parts of the
published state that change slowly (the straddle chart's series 31 KB, the ideas board 11 KB, the per-book table
12 KB, of 80 KB) are rebuilt and encoded at most once a second instead of four times, and spliced in as text. Same keys
and shapes for the dashboard. Test: `tests/test_state_fastpath.py`. **Takes effect only at the next engine restart.**

## 8. Results of the 9 Nov test (unseen by the warm start)

Warm start on 19 Oct to 6 Nov, then 9 Nov second by second with learning on, as live. 16 ms a recorded second.

| Futures horizon | Checked | Inside the 80 % range | Against "no move" | Clear direction calls right |
|---|---|---|---|---|
| 1 min | 4,349 | 80.5 % | -0.4 % | 55.5 % of 618 |
| 5 min | 4,301 | 83.4 % | -0.7 % | 48.8 % of 82 |
| 15 min | 4,181 | 89.7 % | -1.6 % | 2 % of 50 |
| 30 min | 4,001 | 95.4 % | -2.3 % | 3 % of 38 |

| Premium horizon | Checked | Inside the 10-90 range | My error | "No change" error | "Decay only" error |
|---|---|---|---|---|---|
| 1 min | 2,553 | 80.5 % | 5.9 % | 5.8 % | 5.8 % |
| 5 min | 2,553 | 80.9 % | 12.8 % | 12.7 % | 12.7 % |
| 30 min | 2,552 | 84.2 % | 31.4 % | 31.0 % | 30.8 % |

What it says, plainly:
- **The ranges are right.** 80 % ranges caught 80 to 83 % up to 5 minutes, for the future and for the premiums.
  The longer horizons are too wide.
- **Direction is not forecastable with these experts.** The mean forecast is slightly worse than "no move" at every
  horizon, and the few clear calls at 15 and 30 minutes were almost all wrong on this expiry day. The learning moved
  weight to "no move" and reversion through the day, too slowly.
- The "+5 % or -5 % first" probabilities were no better than a coin (Brier 0.252 against 0.25).
- The useful parts are therefore the decay accounting, the break-even moves, the ranges and the gamma-rent ratio,
  not a direction call. The panel's "what I would do" never says buy until the forecaster has beaten "no move" on
  30 checked cases that day, so on a day like this it stays flat.

Live today (cold models 13:08 to 13:42, then the warm start): 5-minute futures 2 % worse than "no move", ranges 70 %
early in the session, the old model better on the +5 %/-5 % race (0.090 against 0.113 on 101 cases).
