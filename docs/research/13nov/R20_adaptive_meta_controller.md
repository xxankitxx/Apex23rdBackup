# R20: An adaptive meta-controller for the Conductor (owner point 3: "not the same way every day")

Analyst R20, 13 Nov 2026. Data: `data/research/13nov/trades_all_books.parquet` (20,817 trades, 107 books, 17 days),
one ds_v2 part (6 Nov) as a check. Scratch and every script: `data/research/13nov/work/R20/`.
All returns are percent of the day's starting capital, all-in compounding inside the day, one position for the account.
"Sum" means the sum of the daily percent returns. Early = 19 Oct to 4 Nov (12 days). Late (test) = 5 to 12 Nov (5 days).

## Findings first

1. **The Conductor has no memory inside the day.** Its pool, its priorities and its rules are fixed when the day
   starts (`apex/engine/conductor.py:101-108`, `95-97`). At 14:00 it trades exactly as at 09:20, even when every c20
   put bought since 10:00 has lost. That is the "same way every day, then something stupid" the owner sees.
2. **This is not a bandit problem.** Every book runs in shadow, so the system sees the outcome of every arm, not only
   the one it played. Exploration costs nothing. Thompson sampling, as asked, gives the same answer as a plain
   posterior mean (tested: 12 seeds, median equal to the deterministic rule). The right tool is full-information
   learning from shadow outcomes, kept as yes/no rules.
3. **"Switch to whatever has been working" fails.** Which books do well does not carry over: day-to-day rank
   correlation of book returns is +0.15 on average and negative on 6 of the last 9 day pairs. Every family-switching
   design lost to the static Conductor: day-level expert switching 0 of 9 variants, intraday family switching 0 of 16,
   context gates on the HMM, the engine regime label or a change-point regime 0 of 90 (on total and on early sum).
   A rolling "pick the best variant so far" over all 154 variants made +500 % against +1,035 % for the static
   Conductor on the same 13 days, better on 4 days and worse on 7.
4. **One adaptive signal does hold: the losing side inside a day, for c20.** When today's c20-family shadow trades on
   one side (CE or PE) have lost more than they won (last 12 closed, at least 3), the next c20 trade on that side wins
   far less often. Pool trades on a "locked" side: early 49.6 % strike, +1.6 % mean (119); late 40.7 %, -1.6 % (59).
   Pool trades on an open side: early 64.2 %, +10.6 % (260); late 61.0 %, +8.1 % (105). Same sign in both windows.
5. **The side lock as an account rule** (one yes/no rule, nothing fitted beyond N): strike 59.3 % against 52.9 %,
   worst day -13.6 % against -37.1 %, test window 54.2 % against 51.4 % strike, +161.8 against +153.8, losing test days
   1 against 2. It costs 94 points over 17 days, all of it on 27 Oct (+542 % to +358 %). Of the 18 side-specific gate
   variants, 12 raised the strike rate in both windows and 17 improved the worst day. It is the most consistent rule I
   found, and it is a shadow candidate, not a promotion.
6. **The pullback families behave the opposite way.** For t28 and lvl_trail, trades on a side where their own family has
   been losing win MORE (lvl: early 63 % against 47 %, late 59 % against 49 %; t28: 58 % against 46 %, 55 % against 45 %).
   Handing the account to lvl_trail books on such sides, with the c20 side lock on, gave the best account in the study:
   strike 57.1 %, +1,373 against +1,141, without its best trade +1,139 against +961, test window +205.5 against +153.8,
   1 losing test day against 2. It misses the worst-day test by 1.3 points (-38.4 against -37.1), most of its test gain
   is 6 Nov, and the lvl trades themselves only win 50 %: much of the gain is path dependence (which c20 trade comes
   next). Low to medium confidence, shadow only.
7. **A change-point regime (BOCPD) is a good description and a weak gate.** Pool trades in a settled segment and in the
   direction of the segment's drift won 66.5 % (early, 185 trades, +11.0 % mean) and 66.7 % (late, 48, +12.0 %). Trades
   against a settled drift won 57 % early and 44 % late. But gating on it inside the one account cut the big early
   winners and lost money in all 36 variants. Use it for the display (owner point 4), not as a veto yet.

About 176 policy runs were scored (36 gate, 90 context, 16 switch, 9 day-level, 7 side lock, 12 hand-off, 6 robustness),
plus 12 Thompson seeds. With that many tries on 17 days, a single good variant proves little; the side-lock finding
is reported because it holds across most of its variants and in both windows, not because of its best variant.

## Teardown (what the code does in this area, and where it fails)

| Place | What it does | Where it fails for adaptation |
|---|---|---|
| `apex/engine/conductor.py:101-108` | Builds `members` once from the pool as of the day, sorted by `priority_key` | Fixed for the whole day; no state from outcomes |
| `apex/engine/conductor.py:95-97` | Same-tick priority: standing, then in-sample `ret_per_trade` from `pool.json`, then book order | `ret_per_trade` is a 14-day in-sample number (pool.json notes say "in-sample"); it never updates |
| `apex/engine/conductor.py:137-199` | `step`: follow the owner, await fill, else take the first eligible trigger | The only checks are occupancy and the pair's rule on the photograph (`177-190`); the shadow results of the day are never read, although `books[...]` with every book's `trades` list is passed in |
| `apex/engine/conductor.py:201-216` | `_fired` scans pool members only | No book outside the pool can ever be considered, whatever the day is doing |
| `apex/conductor/account_sim.py:44-90` | Offline twin of the same one-account rules | Same: no hook for an admission rule that depends on earlier closed trades. I reproduced it exactly on the parquet (119 trades, identical daily returns; `work/R20/s04_validate.py`) |
| `apex/rules/pool.json` | Five c20 books, all `rule: null`, `standing: low` | The pool cannot change inside a day; the owner's "adaptive" wish has no place to live |
| `apex/quant/regime.py:1-60` | Gaussian HMM with a semi-Markov layer, fitted offline, forward filter live | Used only by `apex/engine/quantview.py:50` and the photograph (`apex/engine/weather.py:1025`, `wx_hmm_state`). Never a decision input. As a context gate it did not help (E4) |
| `apex/engine/regime.py:43-45` | 5-minute micro regime labels | A 5-minute state; the label is noisy as a context (E4: 0 of 18 regime-label gates beat the Conductor on total) |
| `apex/engine_main.py:336-341` | One `self.conductor` object | No room for a second, shadow Conductor with another admission rule; it must be added (see Build) |
| `apex/engine_main.py:1677-1683` | Conductor step timed under `_ph_add("conductor")` after all books | Good place for an adaptive layer: the books have already run, their closed trades are known, and the cost is measured |
| `docs/25:147, 244` | "Contextual bandit over pre-registered entry methods, shadow only: NOT BUILT" | Still not built; this report says a bandit is the wrong framing (Finding 2) |

## Evidence

### E1. The simulator and the baseline

`work/R20/mc_lib.py` replays the account rules of `account_sim.py` on the parquet, with an `accept(trigger)` hook that
may only use shadow trades whose `t_out` is before the trigger (strictly causal). Static Conductor:

| Window | Trades | Strike | Sum % | Losing days | Worst day | Without best day | Without best trade |
|---|---|---|---|---|---|---|---|
| All 17 | 119 | 52.9 % | +1,140.7 | 5 | -37.1 | +598.9 | +960.8 |
| Early 12 | 84 | 53.6 % | +986.9 | 3 | -37.1 | | |
| Late 5 | 35 | 51.4 % | +153.8 | 2 | -6.0 | +44.6 | +153.8 |

(The sum is +1,140.7 here and +1,092.5 in docs/54 because this compounds `ret_pct` without lot rounding.)

### E2. Does success persist? (the precondition for any adaptive controller)

| Measure | Value |
|---|---|
| Book-day return rank, day d to d+1 (Spearman, 107 books) | mean +0.15; 6 of the last 9 pairs negative |
| Trailing 3-day mean to next day | mean +0.09 |
| All earlier days to next day | mean +0.17 |
| Morning (before 11:30) to afternoon, same book same day | pooled +0.19 (1,114 book-days); negative on 6 of 17 days |

Weak and unstable. A controller that chases recent winners will mostly chase noise. `s02_persist.py`.

### E3. Families and day-level switching (full information, walk-forward by construction)

Each family run alone as a one-position account (`arm_day_returns.csv`): no family is best on more than a few days,
and the best family of a day is rarely the best the next day (19 Oct: spot_dc12 +251 %, then -30 %).
Day-level switching (pick the arm with the best discounted past log return, median, or win rate, forgetting 0.6 / 0.8 / 1.0,
c20 pool for the first 3 days): 9 variants, **0 beat the Conductor on total**, best +774 against +1,141, worst days to -68 %.

### E4. Context gates and family switching inside the day (Beta posterior, cross-day prior with forgetting)

Rule: take a pool trigger if the posterior win rate of the c20 pool in the current context is at least a threshold.
Prior from earlier days discounted by gamma, weight w0, plus today's closed shadow trades.

| Context | Variants | Beat Conductor on total | On early sum | Late strike higher | Late sum higher |
|---|---|---|---|---|---|
| none | 18 | 0 | 0 | some | 0 |
| BOCPD 4 states (fresh/settled x with/against) | 18 | 0 | 0 | 11 of 36 with "none" | 0 |
| with / against the segment drift | 18 | 0 | 0 | 14 | 0 |
| HMM state (`wx_hmm_state`) | 18 | 0 | 0 | 10 | 10 |
| engine regime label (`wx_regime`) | 18 | 0 | 0 | 6 | 0 |
| Family switching (9 families, top-1 or top-2, contexts none / BOCPD) | 16 | 0 | 0 | 7 | 0 |

Family switching made the worst day much worse (-57 % to -67 %). Vetoes inside an all-in account shift the whole
sequence: skipping one trade lets a later, worse one in (several gates made the worst day -48.7 %).

### E5. Rolling meta-selection (choose the best variant so far each morning)

Over all 154 variants, from 26 Oct: picked by past sum, +499.5 against +1,034.7 static, 4 days better, 7 worse,
losing days 4 against 5. By past log return, +560.8. The controller of controllers loses half the money. `s14_rolling.py`.

### E6. The side-loss lock

Rule: refuse a c20 pool trigger on side s (CE or PE) when, among today's last 12 closed c20-family shadow trades on
side s (pool plus c20_9h, c20_9e, c20_8x, c20_9x_r002, c20_9x_r004, fr_/rx_/fx_c20_9y), at least 3 have closed and
losses exceed wins. Day start: empty. `s08_sidelock.py`.

| Version | Strike | Trades | Sum % | Losing days | Worst | w/o best day | w/o best trade | Late strike | Late n | Late sum | Late losing | Late worst | Top 12 kept |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Conductor | 52.9 | 119 | 1,140.7 | 5 | -37.1 | 598.9 | 960.8 | 51.4 | 35 | 153.8 | 2 | -6.0 | 12 |
| Side lock N=6 | 59.0 | 83 | 1,004.7 | 5 | -13.6 | 678.7 | 824.7 | 52.0 | 25 | 140.5 | 1 | -6.0 | 11 |
| **Side lock N=12** | **59.3** | 81 | 1,047.0 | 5 | **-13.6** | **688.8** | 867.0 | **54.2** | 24 | **161.8** | **1** | -6.0 | 11 |
| Side lock N=all day | 56.4 | 94 | 1,130.1 | 5 | -26.9 | 588.2 | 950.1 | 50.0 | 24 | 89.4 | 2 | -26.9 | 11 |
| Thompson twin, 12 seeds (median) | 59.0 | 83 | 1,032.9 | 5 | -13.6 | 674.7 | 853.0 | 54.2 | 24 | 161.8 | 1 | -6.0 | 11 |

Per day, N=12 against the Conductor: better on 9 days (19 Oct +41, 23 Oct +24, 3 Nov +29, 4 Nov +15, 29 Oct +18, 21 Oct +8,
12 Nov +6, 9 Nov +2, 30 Oct +1), worse on 3 (27 Oct -184, 2 Nov -41, 22 Oct -13), same on 5.
The 178 refused triggers, judged by their own result: early 119, 50 % won, +1.6 % mean; late 59, 41 % won, -1.6 %.

Gate family robustness (`s07_gate_an.py`), 18 side-specific against 18 side-blind variants:

| | Strike up in both windows | Worst day better | Total sum better | Without best day better |
|---|---|---|---|---|
| Side-specific (CE and PE tapes apart) | 12 of 18 | 17 of 18 | 1 of 18 | 7 of 18 |
| Side-blind (one tape) | 1 of 18 | 10 of 18 | 0 of 18 | 0 of 18 |

The side matters; a plain "the family is cold today" brake does not work.

### E7. The lock on every book alone (is it a market property or a c20 property?)

`s09_sidelock_books.py`: each book's trades split by whether its OWN family's last 12 closed same-side trades were losing.

| Family | Early locked | Early open | Late locked | Late open |
|---|---|---|---|---|
| c20 pool | 119, 49.6 %, +1.6 | 260, 64.2 %, +10.6 | 59, 40.7 %, -1.6 | 105, 61.0 %, +8.1 |
| c20 others | 178, 45.5 %, +1.1 | 409, 61.9 %, +9.8 | 102, 47.1 %, -0.5 | 180, 60.6 %, +5.5 |
| t28 | 872, 58.3 %, +3.9 | 1,178, 45.7 %, +2.2 | 332, 55.4 %, +2.2 | 470, 44.7 %, +2.1 |
| lvl_trail | 108, 63.0 %, +5.2 | 439, 47.2 %, +2.5 | 59, 59.3 %, +2.9 | 167, 49.1 %, +2.6 |
| spot_dc12 | 1,148, 38.4 % | 757, 35.3 % | 483, 31.5 % | 343, 45.5 % (sign flips) |

(cells: trades, strike, mean %). c20 has outcome momentum by side; the pullback families have outcome reversal by
side. Both signs hold in both windows. Reading: a c20 loss on a side means the market keeps moving against that side's
"resumption"; for a pullback buyer, the same run of losses means the pullback is stretched and close to turning.

### E8. Lock plus hand-off of the losing side to a pullback family

`s10_handoff.py`, `s11_final.py`. Pool first; helper books ranked by their early-days mean return only
(lvl: lvl_trail_rx_c10, lvl_trail_re, lvl_trail_rx, lvl_trail_rx_be, lvl_trail, lvl_trail_be). Modes: helper may trade a
side only while c20 is locked on it ("c20locked"), only while its own family is losing on it ("ownlosing"), both, or free.

| Variant | Strike | Trades | Sum % | Losing days | Worst | w/o best day | w/o best trade | Late strike | Late n | Late sum | Late losing | Late worst | Kept |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Conductor | 52.9 | 119 | 1,140.7 | 5 | -37.1 | 598.9 | 960.8 | 51.4 | 35 | 153.8 | 2 | -6.0 | 12 |
| lock + lvl ownlosing N=6 | 57.6 | 118 | 1,492.3 | 5 | -39.9 | 883.3 | 1,281.3 | 54.5 | 33 | 197.8 | 1 | -6.2 | 11 |
| **lock + lvl ownlosing N=12** | **57.1** | 105 | **1,373.3** | 5 | -38.4 | **822.2** | **1,139.3** | **53.1** | 32 | **205.5** | **1** | -6.2 | 11 |
| lock + lvl ownlosing N=all | 54.0 | 126 | 1,181.7 | 4 | -35.0 | 741.5 | 970.7 | 52.8 | 36 | 171.2 | 1 | -6.2 | 12 |
| lock + t28 both N=12 | 56.8 | 118 | 1,212.0 | 4 | -22.5 | 739.3 | 1,032.0 | 54.5 | 33 | 184.2 | 2 | -6.3 | 11 |
| lock + t28 both N=6 / all | 54.5 / 55.6 | | 1,208 / 1,238 | 6 / 3 | -25.5 / -16.0 | | | 47.2 / 48.6 | | 124.7 / 121.4 | 3 / 2 | | |
| free hand-off (t28 or lvl) | 45 to 52 | | 793 to 1,191 | | -36 to -52 | | | | | -2 to 136 | | | |

Test days, lock + lvl ownlosing N=12 against the Conductor:

| Day | Trades | Strike | Day % | Conductor trades | Strike | Day % |
|---|---|---|---|---|---|---|
| 5 Nov | 2 | 0 % | -6.2 | 1 | 0 % | -6.0 |
| 6 Nov | 5 | 100 % | +158.8 | 4 | 100 % | +109.2 |
| 9 Nov | 19 | 47 % | +39.8 | 22 | 50 % | +43.4 |
| 11 Nov | 4 | 50 % | +12.1 | 4 | 50 % | +12.1 |
| 12 Nov | 2 | 50 % | +1.1 | 4 | 25 % | -4.8 |

The lvl trades it took: 24, 50 % won, +2.2 % mean. So the extra profit comes mostly from which c20 trades follow.
Honest caveat: the hand-off direction was read from E7, which shows both windows; the early half alone gives the same rule.

### E9. The change-point regime (Bayesian online change-point detection)

Adams and MacKay (2007), Normal-Gamma prior, Student-t predictive, hazard 1/60 per minute, run length capped at 300,
on 1-minute futures returns. The futures path is rebuilt from every book's entry and exit futures prints (causal: a print
counts at its own time). Check against ds_v2 on 6 Nov (one part): median error 3.0 points, 90th percentile 8.9;
"fresh change" state agrees 80 % of minutes, segment direction 92 %. 5 to 31 change points a day.

| Pool trades | Early n | Strike | Mean % | Late n | Strike | Mean % |
|---|---|---|---|---|---|---|
| settled, with the drift | 185 | 66.5 % | +11.0 | 48 | 66.7 % | +12.0 |
| settled, against | 119 | 57.1 % | +7.6 | 93 | 44.1 % | +1.2 |
| fresh change, with | 49 | 42.9 % | -3.2 | 6 | 83 % | +3.9 |
| fresh change, against | 26 | 53.8 % | +7.2 | 17 | 58.8 % | +2.2 |

"With" beat "against" on 11 of 17 days. As a gate it lost money in every variant (E4), because 27 Oct's winners were
counter-drift.

## Ideas

### I1. Shadow book `conductor_sl`: the c20 side-loss lock (tested; medium confidence)
* Mechanism: c20 buys the resumption after a pullback. When the market keeps running against one side, each "resumption"
  on that side fails, and the shadow books show it first. The lock reads those shadow results and stops buying that side.
* Exact rule (yes/no, explainable): refuse a pool trigger on side s when today's last 12 closed c20-family shadow trades on
  side s number at least 3 and losses exceed wins. It lifts by itself as soon as wins catch up.
* Test: E6. Promotion standard against the Conductor: strike pass (59.3 against 52.9; late 54.2 against 51.4; luck margin
  not yet measured, Phase B); return fail on 17 days (-94), pass on the test days (+8); positive without best trade and day,
  pass; ahead without best day pass, without best trade fail (867 against 961); keeps 11 of 12 top trades, pass; worst day
  pass (-13.6 against -37.1); two windows: strike yes, return only late. Not promotable now.
* Build (no slowdown): a subclass `AdaptiveConductor(Conductor)` in `apex/engine/conductor.py` with a `SideTape`: for each
  tracked book keep a pointer into `book.trades`; each step append only new closed trades (O(new trades), a few per minute,
  well under 0.1 ms a step), keep two deques of 12 wins. Its `step` is the parent's with one extra check next to the rule
  check (`conductor.py:180-187`), logged as `rule_block` with "side lock: c20 PE today 2 won, 5 lost". `engine_main.py:336-341`
  holds one Conductor; add a list of shadow Conductors for VARIANTS entries such as `conductor_sl = dict(conductor="sidelock")`,
  stepped in the same timed block (`1677-1683`). Add the same `admit` hook to `account_sim.simulate_day` so the offline oracle
  still matches the engine trade for trade.
* Risk: it gives up the big counter-move day (27 Oct cost 184 points). One such day a month erases its gain.

### I2. Shadow book `conductor_slh`: lock plus hand-off to lvl_trail (tested; low to medium confidence)
* Mechanism: E7. When c20's side is cold, the pullback family on a side where it has been losing tends to turn.
* Rule: I1, plus lvl_trail books (order: rx_c10, re, rx, rx_be, trail, be) may own the account on side s only while their own
  last 12 closed same-side shadow trades show losses over wins (at least 3). Pool keeps priority.
* Test: E8. Beats the Conductor on strike, return, without best trade, without best day, test-window return and test losing
  days; fails the worst day by 1.3 points. Gain rests on 6 Nov and on path dependence. 18 variants of this kind tried.
* Build: as I1, with the helper books added to that shadow Conductor's members and a second tape per helper family.
* Risk: overfitting by sequence luck. It must run in shadow for at least two more windows before anyone believes it.

### I3. Do not build family switching, regime-gated pools or a bandit router (tested; high confidence as a guard)
* E3, E4, E5: 0 of 115 such designs beat the static Conductor on total; the rolling chooser halves the profit.
* Why: success does not persist across days (E2), and all-in one-position accounts amplify a wrong switch.
* Write this down in docs/28 so it is not rebuilt each week. If ever revisited, use full-information Hedge
  (exponential weights on all shadow outcomes), not Thompson exploration.

### I4. BOCPD segment on the forecaster card (display only; partly tested)
* Mechanism: owner point 4 wants a stand. BOCPD gives one in plain words: "The market turned up at 11:42 and has held
  that direction for 38 minutes, +1.1 points a minute. A c20 call here buys with the move; I would take it. A put
  here fights a settled up-move; those won 44 % on the test days."
* Test: E9 for the statistics; the display itself is untested.
* Build: in the Forecast Lab process (not the engine): run length vector capped at 300, one update a minute, about 0.3 ms.
  The side-lock state goes on the same card: "Puts are locked: today c20 puts 2 won, 5 lost. I am only buying calls."
* Risk: the 6 Nov check showed 80 % agreement on "fresh change" between the rebuilt path and ds_v2; use the live
  futures LTP, not trade prints.

### I5. First-person reason lines from the meta-controller (ui; untested)
* Every refusal and every hand-off already produces a sentence (I1, I2). Show the last one under the Conductor status, so
  the owner sees why it is flat: "Flat by choice: puts are cold today (1 of 5 won), calls have no trigger."

### I6. Keep the controller deterministic (tested)
* The Thompson twin of the lock (sample p from Beta(1+wins, 1+losses), trade if p >= 0.5) matched the deterministic rule
  (12 seeds: strike 57.1 to 60.2, sum 992 to 1,059). Randomness only makes the account harder to explain and to replay.

## Phase B scripts (ready, not run)

* `data/research/13nov/work/R20/phaseB_luck_margin.py`: random-refusal null (500 draws, same refusal rate per day) for the
  side lock, so the strike rate test of docs/28 section 2 gets its luck margin. About 10 to 20 minutes.
* `data/research/13nov/work/R20/phaseB_bocpd_ds2.py`: BOCPD from the per-second ds_v2 futures (one part at a time),
  hazards 1/30, 1/60, 1/120, re-scores E9; 12 Nov falls back to the trade-print path.

Scripts run today: `s02_persist.py`, `s03_cache.py`, `s04_validate.py`, `s05_bocpd.py`, `s06_policies.py` (gate, ctx, switch,
day), `s07_gate_an.py`, `s08_sidelock.py`, `s09_sidelock_books.py`, `s10_handoff.py`, `s11_final.py`, `s12_ds2check.py`,
`s13_prio.py`, `s14_rolling.py`; library `mc_lib.py`. Results: `policy_*.pkl`, `sidelock_*.pkl`, `handoff_results.pkl`,
`final_candidates.pkl`, `arm_day_returns.csv`, `ctx_bocpd.pkl`.
