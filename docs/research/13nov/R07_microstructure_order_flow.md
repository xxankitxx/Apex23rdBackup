# R07: Microstructure and order flow (13 Nov)

Lens: order-flow imbalance, depth imbalance, micro-price, spread, quote ages, and the futures-to-option lead and lag.
Owner points covered: 1 (teardown and ideas), 2 (every flow item of the weather tried), 4 (what the forecaster should
say), 6 (errors and speed in this code).

## Findings first

1. **The options market leads the Nifty future, not the other way round.** The parity forward of the weekly (built
   from option mids) moves first. Its 1-second change correlates 0.18 to 0.22 with the future's change one second
   LATER, against only 0.06 to 0.13 the other way. On the c20-style 5-point resumptions the forward got there first
   67% to 75% of the time, a median 3 to 4 seconds ahead. Same result on all three days studied (4, 5, 6 Nov).
2. **The futures mid catches up with the forward; the forward does not catch up with anything.** The gap between the
   forward and the futures mid, against its own 5-minute average, predicts the future's next 10 s to 2 min strongly
   (rank correlation +0.20 to +0.35 on every day). It predicts the forward's own next move not at all (-0.02 to +0.03).
3. **This undercuts the Forecast Lab's direction skill.** The Lab forecasts the futures mid (apex/forecast_lab/core.py:638).
   Walk-forward on its own 46 features, its skill on the futures mid is +0.15 to +0.35 at 10 s. On the forward, which
   is what option premiums follow, the same features score -0.03 to +0.03 at 10 s to 60 s. The skill it shows at
   short horizons is mostly "the future will catch up with the options". That is true and of no use to an option
   buyer. Its strongest single inputs (`dbasis`, `hwlead30`) predict the future and not the forward.
4. **No order-flow or book item at the trigger separates winning trades from losing ones out of sample.** I tried
   66 numeric and 9 class items on all 20,817 trades. 13 of 66 kept their early sign on at least 4 of the 5 late days.
   Chance alone gives 12.4. None of the 14 items with a real early effect (|rho| >= 0.05) held. As yes/no vetoes on
   the Conductor's own 119 trades (272 variants), 9 of the 55 early best picks beat the base on the late days. That
   is worse than a coin.
5. **Order-flow imbalance (Cont, Kukanov, Stoikov) and signed trade flow do predict the future, weakly:** +0.04 to
   +0.09 at 30 to 60 s, same sign on all three days. They add nothing to the Lab, which already carries `ofi30`.
   They do not predict the forward.
6. **Four code defects in this area** (details in the teardown). The biggest one: for the Nifty future, the
   aggressor test compares the bid/ask MID against the previous ask, not the last trade. So "buyer" and "seller"
   volume on the future is really a mid tick rule (flow.py:94-103 with market.py:46-52).

## Teardown

### What the code does

| File:line | What it computes | Where it fails |
|---|---|---|
| apex/engine/market.py:40-52 | D-110: replaces the Nifty future's `ltp` by the bid/ask mid in the engine's copy of the snapshot | Every reader of `m.snap["ltp"]` for the future gets the mid, including the flow classifier below |
| apex/engine/flow.py:92-103 | Aggressor split of each volume step: print >= previous ask = buyer, <= previous bid = seller, else tick test | `last = s["ltp"]` is the MID for the future. The mid can only be at or above the previous ask after a jump of half the spread or more within 0.1 s, so almost all futures volume falls to the tick test on mid changes or to "unclassified". `agg_b`, `agg_s`, `agg_net`, `agg_with_rs` and the Force detector's consumed volume (levels.py:211) inherit it |
| apex/engine/flow.py:110-114 | "Last 10 s" aggressive volume as a ring of `10 * HZ` = 100 slots | The ring counts steps, not seconds. 12 Nov perf log: median 564 steps a minute (9.4 Hz), 95th-percentile step 134 to 227 ms. In slow minutes the "10 s" window is 15 to 40 s |
| apex/engine/flow.py:147-163 | Book-leads-price score: correlation of the order imbalance 2 s ago with the price change since | Uses `m.ltp`, which for options is the last print with bid-ask bounce, and for the future is the mid that lags the forward (finding 1). In the weather `fut_lead` median is +0.03 to +0.07: the book almost never leads |
| apex/engine/flow.py:183-200 | REFILLING / HOLDING / DRAIN / PULLED classes from 10-s and 60-s log changes of the 5-level totals | Price-level blind: when the price ticks, a whole level leaves the 5-level window and another enters, so a move itself reads as a drain or a refill. Evidence: `fut_opp_q` classes give 40% to 49% winners in every class, both windows |
| apex/engine/levels.py:211-212 | Force detector: consumed volume `C += A * 0.1` per update | Assumes 0.1-s steps. With 9.4 Hz on average and slower minutes, C is under-counted, so `rho` and `pi` are biased. `BREAK-IMMINENT` was 74% winners early (n 43) and 20% late (n 25) |
| apex/engine/edge.py:127-149 | `fut_ofi60`: Cont OFI on the top of book once a second, summed over the last 60 entries | Count-based window (60 entries, not 60 s), 1 Hz sampling of a book that changes many times a second, so most queue events are netted away. A true event-level OFI needs the tick tape (Phase B script below) |
| apex/engine/edge.py:135 | `fut_micro` = size-weighted mid minus mid | This is exactly half the spread times the top-of-book imbalance. It is not Stoikov's micro-price (an empirical expected future mid). Median 0.00 for winners and losers |
| apex/forecast_lab/brain.py:136-138 | Lab `imb` and `micro` | `micro` is the imbalance's change over 10 samples, not a micro-price. In the data `LAB:imb` and my 5-level imbalance have identical rank correlation on every day, so the Lab's `imb` is the 5-level total imbalance |
| apex/forecast_lab/core.py:638 | The Lab's price `F` is the futures mid | The laggard of the three prices (forward, spot, future). See findings 2 and 3 |
| apex/engine/council/__init__.py:76-78 | The c20 books read the engine's parity forward `D.fwd` | Correct choice: the c20 entries already sit on the leading series. Other engine parts that run on the futures mid (D-110: impulse, sigma, episode, guard, exits, trace) run 1 to 4 s behind it |
| apex/engine/gex.py:143-160 | Gamma-wall advice compares the wall with the forward when it exists (engine_main.py:1521) | Correct. The weekly forward sits 37 to 44 points below the monthly future on these days, so any wall compared with the future directly would be off by that much |
| apex/conductor/search.py:61-67 | Clusters 21 to 27 put the flow items into the rule search | They are noise on this evidence (finding 4). Each extra item adds to the multiple-testing burden of the search |

### Errors and speed (owner point 6)

Nothing in flow.py, edge.py or levels.py raised in today's logs that I read. The defects above are wrong numbers,
not crashes. The cost: the flow update is fully vectorised. The edge snapshot is once a second. The new item I
propose (forward-minus-future gap against its 5-minute average) is one subtraction and one exponential average a
second: no measurable cost.

## Evidence

Data: ds_v2 parts 4 Nov (early), 5 Nov and 6 Nov (late), per second; the Lab's collected features for the same days;
the 20,817-trade table; the Conductor's 119 replayed trades. Scripts and outputs are in
`data/research/13nov/work/R07/` (s1 to s8).

### E1. The book on the Nifty future (per second)

| Day | Spread p10 / p50 / p90 (pts) | Quote age p50 / p90 (s) | Depth age p50 (s) | ATM CE quote age p50 (s) | Future minus weekly forward, median (pts) |
|---|---|---|---|---|---|
| 4 Nov | 0.6 / 3.8 / 9.0 | 0.49 / 1.20 | 0.83 | 0.35 | 42.3 |
| 5 Nov | 0.4 / 2.3 / 5.9 | 0.44 / 1.09 | 0.83 | 0.37 | 44.3 |
| 6 Nov | 0.9 / 4.8 / 10.5 | 0.45 / 1.14 | 0.83 | 0.37 | 37.1 |

The futures spread is often 4 to 10 points: its mid is a noisy price. The option quotes are fresher than the futures quote.

### E2. Who moves first (1-second changes, correlation)

| Day | Forward leads by 2 s | Forward leads by 1 s | Same second | Future leads by 1 s | 5-pt resumptions: forward first | Median lead of the forward |
|---|---|---|---|---|---|---|
| 4 Nov | 0.146 | 0.202 | 0.370 | 0.070 | 238 of 316 (75%) | 4 s |
| 5 Nov | 0.107 | 0.184 | 0.288 | 0.058 | 145 of 215 (67%) | 3 s |
| 6 Nov | 0.123 | 0.224 | 0.301 | 0.127 | 287 of 421 (68%) | 4 s |

Options against the future: the ATM option's mid did not change at all in 34% to 41% of the seconds in which the
future moved 2 points or more. With finding 2, most of that is the future's noise, not a stale option.

### E3. The gap predicts the future, not the forward (rank correlation with the next move)

`gap_dev` = (forward minus futures mid) minus its own 5-minute exponential average, sampled every 5 s.

| Day | Target | 5 s | 10 s | 30 s | 60 s | 120 s | 300 s |
|---|---|---|---|---|---|---|---|
| 4 Nov | future | +0.328 | +0.332 | +0.255 | +0.232 | +0.179 | +0.110 |
| 4 Nov | forward | -0.013 | -0.011 | -0.022 | +0.026 | +0.033 | +0.005 |
| 5 Nov | future | +0.349 | +0.342 | +0.272 | +0.218 | +0.167 | +0.125 |
| 5 Nov | forward | +0.006 | +0.008 | +0.007 | +0.012 | +0.021 | +0.018 |
| 6 Nov | future | +0.312 | +0.335 | +0.273 | +0.196 | +0.104 | +0.030 |
| 6 Nov | forward | -0.019 | -0.006 | -0.006 | -0.011 | -0.059 | -0.086 |

Size: in the top tenth of `gap_dev` the future rose 3.3 to 4.6 points on average over the next 60 s; the forward
rose 0.6 to 1.3. In the bottom tenth the forward rose 0.7 to 4.4 points: no pattern. The forward's own last 5-second
move also predicts the future (+0.19 to +0.24 at 10 s) and not itself (+0.01).

### E4. The Lab's skill, futures target against forward target (walk-forward ridge on the Lab's 46 features)

Correlation of the forecast with the outcome on the test day / share of right directions in its strongest fifth.

| Test day (trained on) | Horizon | Target: future | Target: forward | Future-model scored on the forward |
|---|---|---|---|---|
| 5 Nov (4 Nov) | 10 s | +0.160 / 60% | -0.026 / 51% | -0.010 / 50% |
| 5 Nov | 30 s | +0.065 / 61% | -0.017 / 53% | -0.024 / 56% |
| 5 Nov | 60 s | +0.029 / 59% | -0.001 / 55% | -0.019 / 57% |
| 5 Nov | 120 s | +0.029 / 55% | +0.011 / 54% | +0.003 / 54% |
| 5 Nov | 300 s | +0.072 / 58% | +0.051 / 56% | +0.053 / 57% |
| 6 Nov (4, 5 Nov) | 10 s | +0.350 / 67% | +0.016 / 46% | +0.064 / 50% |
| 6 Nov | 30 s | +0.231 / 56% | -0.006 / 40% | +0.038 / 46% |
| 6 Nov | 60 s | +0.146 / 48% | +0.029 / 40% | +0.059 / 45% |
| 6 Nov | 120 s | +0.075 / 36% | +0.035 / 34% | +0.033 / 35% |
| 6 Nov | 300 s | +0.024 / 27% | +0.029 / 30% | +0.008 / 27% |

Two test days only. The pattern is the same on both and matches E3. On 6 Nov the strongest fifth of the Lab's
2-to-5-minute calls was wrong two times in three, on both targets.

Single inputs (rank correlation at 10 s / 60 s, three days): `dbasis` on the future +0.26 to +0.31 / +0.15 to +0.20,
on the forward -0.00 to +0.04 / -0.01 to +0.04. `hwlead30` (heavyweights) on the future +0.14 to +0.19 / +0.05 to
+0.12, on the forward +0.01 to +0.06 / -0.00 to +0.05. The heavyweights lead the future; the options already know.

### E5. Do microstructure features add to the Lab? (futures target, walk-forward)

| Test day | Horizon | Lab | Lab + trade flow | Lab + gap | Lab + both |
|---|---|---|---|---|---|
| 5 Nov | 5 s | +0.220 / 64% | +0.223 / 64% | +0.339 / 74% | +0.342 / 74% |
| 5 Nov | 30 s | +0.065 / 61% | +0.066 / 62% | +0.108 / 61% | +0.108 / 62% |
| 5 Nov | 60 s | +0.029 / 59% | +0.030 / 59% | +0.058 / 59% | +0.058 / 59% |
| 6 Nov | 5 s | +0.357 / 69% | +0.357 / 70% | +0.397 / 74% | +0.397 / 75% |
| 6 Nov | 30 s | +0.231 / 56% | +0.230 / 57% | +0.286 / 60% | +0.286 / 60% |
| 6 Nov | 60 s | +0.146 / 48% | +0.144 / 47% | +0.206 / 51% | +0.204 / 51% |

The gap makes the futures forecast better, as expected from E3. Trade flow adds nothing. A pure microstructure
model (19 items: OFI at 5 to 120 s, depth change, trade flow, imbalance, spread, ages) scored +0.02 to +0.08 at
30 s, below the Lab. Stoikov's empirical micro-price (imbalance decile by spread state, learned on earlier days):
+0.05 and -0.02 at 30 s. Not useful at this data rate.

Univariate, same sign on all three days (future target, 60 s): OFI over 10 s +0.068 / +0.081 / +0.057; trade
flow over 10 s +0.091 / +0.063 / +0.039. Static 5-level imbalance changed sign: -0.100 / -0.055 / +0.029.

### E6. Trades at the trigger

All books, 17 days, 66 numeric flow items, rank correlation with the trade's return per day (s1):

| Test | Result | What chance gives |
|---|---|---|
| Items keeping their early-days sign on 4 or 5 of the 5 late days | 13 of 66 | 12.4 |
| Items with an early median effect of 0.05 or more | 14 | |
| Of those, keeping the sign on 4 or more late days | 0 | |

Conductor's own trades (s4): base early 84 trades, 53.6% won, +7,489% compounded, 3 losing days; late 35 trades,
51.4% won, +200.7%, 2 losing days (5 Nov -6.0%, 6 Nov +109.2%, 9 Nov +43.4%, 11 Nov +12.0%, 12 Nov -4.8%).
Variants: veto below or above the early 33rd or 67th percentile, 4 per item, 68 items, 272 variants.

| Early best pick | Early: won / return | Late: trades / won / return / losing days |
|---|---|---|
| Veto narrow futures spread (< 2.86) | 60.7% / +12,124% | 30 / 50.0% / +63.3% / 2 |
| Keep only far from a force level | 56.2% / +9,530% | 33 / 54.5% / +295.1% / 1 |
| Veto quote age > 0.54 s | 57.1% / +8,349% | 25 / 48.0% / +172.4% / 2 |
| Base | 53.6% / +7,489% | 35 / 51.4% / +200.7% / 2 |

Of 55 early picks, 9 beat the late base on return and 22 on strike rate. The force-level item is one lucky survivor
among 55: not promotable (it fails "passes in two windows" and the multiple-testing count).

Medians that kept their side in both windows (winners | losers): `e_fut_ofi60` early +5.5 | +4.0, late +7.6 | +3.4;
`quote_age` early 0.34 | 0.45 s, late 0.28 | 0.36 s. Neither survived as a yes/no veto (above).

Pool books on the three ds_v2 days (s8, only 45 trades, 4 Nov 24, 5 Nov 5, 6 Nov 16): at the trigger the forward had
moved a median 5.0 points with the trade in the last 5 s, the future only 2.85 (the future lags, E2). After the
fill the forward went against the trade: median -2.9 points at 60 s, only 31% of trades with the forward ahead.
Within a day, a faster forward move before the trigger went with a better return (rank correlation +0.35 on 4 Nov,
+0.61 on 6 Nov). Too few trades to claim anything: it is pre-registered for Phase B.

### Multiple testing, all of R07

s1: 75 items on all trades. s3: 27 items by 3 days, 19-item and 46-item models by 4 horizons by 2 folds, micro-price by
2 horizons by 2 folds. s4: 272 vetoes. s5: 4 model sets by 6 horizons by 2 folds. s6 and s7: diagnostics, 2 targets.
About 480 comparisons in all. The only result that holds on every day and every horizon is the lead of the forward
over the future (E2 to E4). It is a structural fact, not a found rule.

## Ideas

### I1. Forecast the forward, not the futures mid (owner points 4 and 1)

* Mechanism: option premiums follow the forward. The futures mid lags it by seconds and catches up over a minute.
  A forecaster of the future earns most of its score from that catch-up (E3, E4).
* Test: done, three days, two walk-forward folds (E4). The Lab's direction skill on the forward is about zero at
  10 s to 60 s and small (+0.03 to +0.05) at 3 to 5 minutes.
* Build: in the Lab, add a second target, the forward (core.py already holds `Fs` in `atm_hist`). Score both in the
  walk-forward report and show only the forward score on the dashboard. A display and scoring change, no trading
  change.
* Risk: honest scores will look much worse. That is the point: the owner should not read a stand into a number that
  only says "the future will catch up".

### I2. A first-person "futures are behind the options" line (owner point 4)

* Mechanism: E3. When the gap is large, the future's next minute is predictable; the premium's is not.
* Display: "Options already price Nifty 3 points higher than the future shows. I expect the future to catch up within
  a minute. That move is already in the premiums, so I would not buy for it." Show the gap and its 60-s expectation
  (the decile table of E3) next to the forecaster's call.
* Test: the forecast part is tested (E3). The wording is a display change.
* Risk: none to trading. It removes a false reason to act.

### I3. Fix the futures aggressor test (reliability)

* Mechanism: flow.py:96-97 should test the raw last print, not the mid copy made in market.py:46-52. Keep the raw
  `ltp` of the mid rows in the Market object (for example `m.raw_ltp`) and use it in Flow.update for the future.
* Effect: `agg_b`, `agg_s`, `agg_net`, `agg_with_rs` and the Force detector's consumed volume become true
  buyer-seller volume for the future. Today they are a mid tick rule.
* Test: untested for profit. The defect is certain from the code. The flow items have shown no value so far, but
  they were measured with this defect.
* Build: shadow first. Log both versions of `agg_net` for a week before any rule reads it.
* Risk: changes the inputs of commentary and of the Force verdicts; no book trades on them today.

### I4. Time-based windows in flow and force (reliability)

* Mechanism: flow.py:110-114 (100-slot ring) and levels.py:212 (`A * 0.1`) assume 10 steps a second. Use the true
  `dt` (already passed to Flow.update) and a time-stamped ring.
* Test: untested for profit. The step rate is measured (9.4 Hz median, slow minutes much worse).
* Risk: low. Speed: the same cost.

### I5. Pre-registered c20 veto on the forward's resumption speed (entry, Phase B)

* Mechanism: a resumption that the forward makes quickly (the 5 s before the trigger) should carry on more often
  than a slow one.
* Test: untested. Hint only (45 pool trades, E6). `phaseB_ms_gate.py` fixes four variants before it runs (veto when
  the forward's 5-s move is below the early 33rd percentile or median; veto when the future is ahead of, or far
  behind, the forward) and scores them on the pool books and the Conductor's trades, early against late, with the
  owner's checks.
* Build: as a pool rule in shadow on c20_9y only if it passes all of docs/28 section 2.
* Risk: the c20 trigger already needs a 5-point resumption, so the remaining spread of speeds is narrow.

### I6. Move engine timing from the futures mid to the forward (entry, exit, guard)

* Mechanism: D-110 moved the engine from the last print to the futures mid. The forward is one step better: no
  4-to-10-point spread noise and 1 to 4 s earlier (E1, E2).
* Test: untested. Needs a replay (not allowed now).
* Build: a shadow copy of the guard and of the futures-based exits that reads `eng.fwd`, falling back to the mid when
  the forward is older than 2 s.
* Risk: the forward is a median of three strikes from quotes up to 30 s old (council/__init__.py:76-78 accepts 2 s).
  In thin minutes it can freeze. E3 shows no sign of noise in it (its own 5-s move does not reverse: +0.01).

### I7. Take the flow items out of the rule search, or down-weight them (selection)

* Mechanism: clusters 21 to 27 in conductor/search.py:61-67 are noise on 17 days (E6). Every noise item in a search
  raises the chance of a lucky rule that fails live, which is the owner's point 3.
* Test: done (E6).
* Build: leave them in the weather and the display; drop them from the candidate factors until a corrected version
  (I3, I4, Phase B true OFI) shows a two-window effect.
* Risk: missing a real effect that appears later. The evening report (edge.py:166) keeps watching them.

### I8. True order-flow imbalance from the tick tape (data, Phase B)

* Mechanism: ds_v2 keeps only best prices and 5-level totals once a second. The tick tape has every quote and depth
  packet, so event-level L1 OFI (Cont, Kukanov, Stoikov) and multi-level OFI (Xu, Gould, Howison) can be built.
* Test: untested. `phaseB_l1_ofi_ticks.py` extracts them and scores them against the ds_v2 OFI. Score them on the
  FORWARD as well as the future (E3 says the future target flatters).
* Risk: on this evidence the futures book does not lead the options, so even a perfect futures OFI may only predict
  the future's catch-up.

Sources: Cont, Kukanov, Stoikov, "The price impact of order book events", https://arxiv.org/abs/1011.6402.
Stoikov, "The micro-price", https://ssrn.com/abstract=2970694, code at https://github.com/sstoikov/microprice.
Xu, Gould, Howison, "Multi-level order-flow imbalance in a limit order book", https://arxiv.org/abs/1907.06230.
Hasbrouck, "One security, many markets" (information share, the method behind E2), Journal of Finance 1995.

## Phase B scripts (after the 15:30 close, one at a time, each run under 3 minutes on an idle machine)

All in `D:\ApexOptions\data\research\13nov\work\R07\`.

| Script | What it does | How to run |
|---|---|---|
| phaseB_ms_alldays.py | Step 1: per-second features for each ds_v2 part still missing (20 parts). Step 2: s3, s5, s6, s7, s8 on every part, outputs to `phaseB_s*_out.txt` | `py -3.13 phaseB_ms_alldays.py todo`, then `... feat <part>` once per part (about 20 s each today), then `... eval` |
| phaseB_ms_gate.py | The four pre-registered vetoes of I5 on the pool books and the Conductor's trades, early against late, per day, strike rate, compounded return, losing days, without best trade and best day | `py -3.13 phaseB_ms_gate.py` (after eval) |
| phaseB_l1_ofi_ticks.py | Event-level L1 OFI, multi-level OFI and signed trade flow from the raw tick tape, per second, and their score against the ds_v2 OFI | `py -3.13 phaseB_l1_ofi_ticks.py <part>`, then `... eval <part> ...` |

Note: `eval` loads every part in one process. On 3 parts it took 89 s on today's loaded machine. On 23 parts it may
pass 3 minutes even when idle. If it does, ask the owner before running it (standing rule on long runs).
