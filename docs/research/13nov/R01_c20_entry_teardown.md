# R01. The c20 entry engine: why the account sits flat, and what could fill the gaps (13 Nov 2026)

Lens: owner points 1 and 3. Analyst R01. All scripts and outputs are in `data/research/13nov/work/R01/`.

## Findings first

1. **The pool is one entry signal, not five.** c20_9y, 9s, 9v, 9x and 9t share the same entry code. On the 17 days the
   five books produced 543 trades from only 140 distinct trigger seconds. On 76 of those seconds all five fired together,
   and on 30 more, four did. The live log for 12 Nov shows the same thing: at 11:12:39, 12:53:25 and 13:45:23 every pool
   book fired in the same second. The Conductor picks between them only by `ret_per_trade`. Adding another c20 variant
   to the pool adds no new entries.
2. **On normal days the signal fires about 5 times a day.** There were 58 distinct normal-day triggers on 12 normal
   days. 5 Nov had just one. The account was flat with no pool book busy for 3,957 of 5,768 entry-window minutes (69 %).
   On 12 Nov the log says "flat: no eligible trigger" 322 times.
3. **The main reason is that arms "age out" in trends.** I rebuilt the trigger second by second on 5 Nov, 6 Nov and
   30 Oct. Of 26 arms, 18 aged out because no 50 % pullback came within 15 minutes. Their deepest pullback was only 14 %
   to 48 % of the impulse (median about 36 %). 6 Nov 09:35 is a clear case: the system armed on a 240-point rally, the
   pullback reached only 33 %, and the arm was dropped. On 5 Nov (a +257-point trend day) five CE arms aged out, and the
   one trade it took was a PE against the trend, which lost 5 %.
4. **The code also cannot trade the opening.** A normal-day arm needs 20 minutes of smoothed history, so nothing can
   arm before about 09:35, and no normal-day entry ever came before 09:41. By its first trigger the market had already
   moved 147.9 points (6 Nov), 184.0 points (12 Nov) and −156.6 points (28 Oct). No existing book caught the 12 Nov
   rally from 09:15 to 10:02. Every book that fired before 10:15 that day lost.
5. **Adding other books as low-priority fillers does not hold up walk-forward.** I tested 100 books × 6 filters = 600
   variants, picked on 19 Oct to 4 Nov and tested on 5 to 12 Nov. 35 variants passed discovery and only 4 of them were
   positive on test (11 %), against 22 % of all 600. Choosing on discovery did worse than chance. The cost is
   crowd-out: a filler holds the account when a c20 trigger arrives. For example, 6 Nov loses 18.9 % on most retest
   fillers.
6. **A filler that steps aside (pre-emption) is the one idea that survived to test, but it fails the promotion
   standard.** In this variant, when a c20 book fires while the filler holds, the filler leaves and the c20 trade is
   taken. The retest family (lvl_trail_re, t28_bidpile) then did +51 % to +84 % on discovery and +72 % to +83 % on
   test, compared with the c20 pool alone. But the account's strike rate falls slightly, and the worst test day is
   worse (5 Nov −19 %). It also rests on an approximate exit price. It belongs in a shadow account only.
7. **The "noise boundary" momentum entry from the literature failed.** I tried the open-anchored band of Zarattini,
   Aziz and Barbon on this tape. It won 3 of 10 at k = 1.0, so on this market the signal fades rather than runs.

## Teardown: how a pool book decides an entry

The chain is c20_08 (core) → c20_20 (layers) → c20_8x (A8_10, FINAL parts) → c20_9x (round 9) → the pool variants.

### Normal day (NORM mode, `D.dte0` false)

| Step | Rule | Code |
|---|---|---|
| Smoothing | fs = 5-s EMA of the parity forward | `apex/engine/council/c20_08.py:92-94` |
| Window | 09:16 ≤ time < **15:00**, and 60 s since the book's last exit | `c20_08.py:40`, `:129` |
| Warm-up | no arm until fs exists 1,200 s back (about 09:35) | `c20_08.py:132` |
| Arm | fs above the 20-min max of fs (current row excluded) **and** fs − fs(20 min ago) ≥ 40; mirror for PE | `c20_08.py:134-140` |
| Arm record | [side, base = fs 20 min ago, extreme, pullback extreme, armed_at] | `c20_08.py:60`, `c20_8x.py:183-189` |
| Re-arm, same side | every new breakout second pushes the extreme and **resets the pullback extreme**; armed_at is kept | `c20_8x.py:187-188` |
| Opposite breakout | replaces the arm | `c20_8x.py:184-185` |
| Age-out | arm dropped once older than min(1,200, **900**) s. This is checked only on non-breakout seconds | `c20_8x.py:192`, `EXTRA PB_AMAX` `:29` |
| Pullback | retrace from the extreme ≥ 50 % of (extreme − base) | `c20_08.py:37`, `c20_8x.py:199-202` |
| Too deep | retrace > 75 % disarms (the V-turn is thrown away) | `c20_8x.py:203-205` (`PB_DMAX`) |
| Fire | 5-point resumption from the pullback extreme | `c20_8x.py:206-208` |
| Strike | \|delta\| target 0.52 (d52), at least 0.52, within ±150 points, quote age ≤ 5 s | `c20_8x.py:50-51`, `c20_08.py:62-83` |
| Vetoes | stale forward (5 s), seq/fy after a loser, and in 9t a rent-trail re-entry rule | `c20_9x.py:384-386`, `:276-308`, `:260-274` |

Not used on normal days: the ORB direction lock and the IV-pop guard. c20_20's `DEFAULT_PARTS` include them
(`c20_20.py:30`), but c20_8x's `FINAL` drops them (`c20_8x.py:295`). So no pool book has any direction lock or IV gate
on normal days.

### Expiry day (EXP mode)

The expiry-day entry is a breakout, not a pullback: fs breaks its 10-min range with ≥ 20 points in 150 s, at
\|delta\| 0.65 (`c20_08.py:21-36`). Entries stop at 14:40. Two vetoes apply: the IV-shock veto `ivz`
(`c20_9x.py:387-393`) and seq/fy. The tie-break strike picker is at `c20_9x.py:311-333`. Expiry days give 82 of the
140 distinct triggers.

### What each pool book changes

| Book | Entry difference | Exit difference | Code |
|---|---|---|---|
| c20_9x | the base | ramp floor, delta-scaled trail, expiry premium trail | `c20_9x.py:69` |
| c20_9y | vetoes a BUY when ATM IV is > 3.5 points over its median since 09:20; on normal days, vetoes when the max-OI resisting strike is 0 to 25 points ahead | none | `c20_9y.py:22`, `:83-97` |
| c20_9s | normal days: vetoes a pullback entry whose impulse first printed > 660 s earlier | none | `c20_9s.py:25`, `:41-42` |
| c20_9v | none | LVL_BOOK and PGB on normal days | `c20_9v.py:21-22`, `:55-101` |
| c20_9t | re-entry on the same side within 900 s of a RENT_TRAIL exit needs a faster trigger and ER ≥ 0.35 | rent trail | `c20_9x.py:260-274`, `c20_9t.py:20` |

The c20_9y and c20_9s vetoes can only remove entries; they never add any.

### The Conductor

* `apex/rules/pool.json`: all five entries have `rule: null` and `standing: low`. Same-tick priority is by
  `ret_per_trade`: 9y, then 9s, 9v, 9x, 9t (`conductor.py:95-98`).
* While holding, any pool trigger is only logged as "occupied" (`conductor.py:145-151`). There is no pre-emption and no
  upgrade.
* While flat with no pool trigger, the reason is "flat: no eligible trigger" (`conductor.py:174-176`). The log says
  nothing about the arm state: it does not say that c20 is armed, how far the pullback has gone, or how much is still
  needed.
* `config.LAST_ENTRY` is 15:15 (`apex/config.py:96`), but no c20 normal-day entry is possible after 15:00
  (`c20_08.py:40`), or after 14:40 on expiry days.

### Day shapes c20 cannot trade (from the code)

| Shape | Why the code stays out |
|---|---|
| Opening drive | warm-up: no arm before about 09:35 (`c20_08.py:132`) |
| Straight rally | every new high resets the pullback extreme; the needed pullback is 50 % of an impulse that keeps growing from a fixed base; the arm ages out after 900 s |
| Slow grind | fs − fs(20 min ago) never reaches 40, so it never arms |
| V turn | a retrace > 75 % disarms. The other side needs a fresh 20-min extreme plus 40 points, which means the V must fully complete, and then it still waits for a 50 % pullback |

## Evidence

### E1. The Conductor's day: holding, silent, and the market on the silent stretches

Source: `s04_timeline.py`. The futures path is rebuilt each minute from every book's entry and exit futures prints
(median gap 0.1 min). The account is from p44_sim / p44_simr, and the baseline reproduces docs/54 exactly (119 trades,
63 won, +₹10,92,458).

| Day | Holding (min) | Silent (min) | Silent % | Day % |
|---|---|---|---|---|
| 19 Oct (expiry) | 105 | 217 | 67 | +21.8 |
| 21 Oct | 163 | 181 | 53 | +48.1 |
| 22 Oct | 72 | 272 | 79 | +7.8 |
| 23 Oct | 117 | 210 | 61 | +25.2 |
| 26 Oct | 102 | 242 | 70 | +260.9 |
| 27 Oct (expiry) | 120 | 204 | 63 | +532.0 |
| 28 Oct | 181 | 163 | 47 | +56.2 |
| 29 Oct | 170 | 174 | 51 | +24.8 |
| 30 Oct | 56 | 288 | 84 | −5.6 |
| 2 Nov | 65 | 279 | 81 | +41.6 |
| 3 Nov (expiry) | 101 | 223 | 69 | −36.3 |
| 4 Nov | 49 | 295 | 86 | −26.7 |
| 5 Nov | 65 | 279 | 81 | −5.9 |
| 6 Nov | 96 | 248 | 72 | +100.2 |
| 9 Nov (expiry) | 116 | 206 | 64 | +43.2 |
| 11 Nov | 78 | 241 | 70 | +9.0 |
| 12 Nov | 109 | 235 | 68 | −4.0 |

The 87 silent stretches of 10 minutes or more fall into these shapes (classed on the minute path):

| Shape | Stretches | Minutes | Median best 15-min move (pts) |
|---|---|---|---|
| Two-way chop | 41 | 2,114 | 56 |
| V turn | 13 | 1,142 | 64 |
| Quiet range | 19 | 311 | 27 |
| Straight trend | 7 | 92 | 51 |
| Slow grind | 7 | 89 | 35 |

The long silent stretches had real moves in them: 5 Nov 11:21 for 219 min (+171 points), 6 Nov 11:24 for 165 min
(+200), 4 Nov 12:23 for 157 min (+188), and 30 Oct 09:55 for 236 min (a 199-point range).

Market state, from other books' weather photographs (one row per trigger minute):

| Median | At a c20 trigger | On a silent minute |
|---|---|---|
| \|5-min move\| | 16.8 | 11.8 |
| Day move | 33.6 | 20.0 |
| Range / straddle | 1.00 | 0.72 |
| Impulse depth | 0.36 | 0.25 |
| VWAP extension | 19.2 | 8.1 |
| 60-min efficiency | 0.11 | 0.12 |
| Minutes | 137 | 2,908 |

Silent minutes are quieter on average, but the efficiency is the same. On 1,745 silent minutes with full data, only
24 had 60-minute efficiency above 0.4.

### E2. Arm census, replayed second by second (`phaseB_c20_complements.py`, 3 day parts)

| Day | Arms | Aged out | Fired | Reversal (> 75 %) | Deepest retrace of aged-out arms |
|---|---|---|---|---|---|
| 5 Nov | 7 | 5 | 1 | 1 | 0.21 to 0.46 |
| 6 Nov | 11 | 6 | 4 | 1 | 0.14 to 0.47 |
| 30 Oct | 8 | 7 | 1 | 0 | 0.25 to 0.48 |

The replica runs on the futures mid with my own exits, so its trades are not the account's. The first FLAG prototype
(efficient impulse, shallow pause, new extreme) took 3 trades on these days: +29.8 % on 6 Nov, and +6.1 % then −11.1 %
on 5 Nov. That is far too few to judge: **untested**.

### E3. Low-priority fillers, walk-forward (`s06_fillers_fast.py`, `s07_sum.py`)

Each non-pool book was added to the pool at the lowest priority, with the account simulated exactly as the Conductor
runs it. Results below are the sum over days of log(account with filler / account without).

| Group | Variants | Positive on test |
|---|---|---|
| All books × filters | 600 | 133 (22 %) |
| Picked on discovery (sum > 0, more up days than down, worst day > −10 %) | 35 | 4 (11 %) |
| Breadth-with filter, all books | 100 | 47 % |

The retest family with no filter (t28_ts, t28_bidpile, lvl_trail_re and similar): discovery +0.4 to +1.0 (6 up days,
6 down); test −0.16 to +0.19 (2 up, 2 down). The 6 Nov loss of −0.209 appears on almost every retest book. That is a
displaced c20 winner.

Controls on test: premium_momentum with the breadth filter was the single best test variant (+1.63), and random_entry
was +0.30. So a 5-day test window ranks noise near the top.

### E4. Filler that steps aside (`s10_yield.py`, 144 variants; 24 books × hold cap {none, 300 s, 900 s} × pre-empt {no, yes})

In the pre-empt variant, when a pool book fires while the filler holds, the filler leaves at its latest hold mark (60,
300, 900 or 1,800 s) before that second. That exit price is an **approximation**. The c20 trade is then taken.

| Setting | Median discovery sum | Median test sum | Share positive on test |
|---|---|---|---|
| No cap, no pre-empt | −0.025 | −0.020 | 33 % |
| **No cap, pre-empt** | +0.038 | **+0.252** | **71 %** |
| 300-s cap, no pre-empt | +0.568 | −0.321 | 4 % |
| 300-s cap, pre-empt | +0.452 | +0.044 | 50 % |
| 900-s cap, pre-empt | +0.090 | +0.108 | 54 % |

The best retest books with pre-emption:

| Book | Disc. sum (% equiv) | Disc. days up/down | Test sum (% equiv) | Test days up/down | Worst test day | Account strike rate, test |
|---|---|---|---|---|---|---|
| lvl_trail_re | +0.411 (+51 %) | 7 / 5 | +0.577 (+78 %) | 3 / 1 | 5 Nov −0.213 (−19 %) | 50.0 % vs 51.4 % |
| t28_bidpile | +0.608 (+84 %) | 7 / 5 | +0.604 (+83 %) | 3 / 1 | 5 Nov −0.213 | 50.0 % vs 51.4 % |
| lvl_trail_rx_c10 | +0.471 | 7 / 5 | +0.544 | 3 / 1 | 5 Nov −0.213 | 50.0 % |

Test days for t28_bidpile, from 5 Nov to 12 Nov: −0.213, +0.100, +0.563, +0.154, 0.000.

Against the promotion standard: the strike rate is lower (fail), the worst day is worse (fail), and it passes in two
windows on return only. Under the strict selection rule, nothing passed: 3 variants were picked on discovery and 0 were
positive on test.

### E5. Opening drive and the noise boundary (`s11_open.py`, `s12_noise.py`)

| Day | First c20 trigger | Day move by then (pts) | Result |
|---|---|---|---|
| 28 Oct | 10:46 | −156.6 | CE +7.4 % |
| 2 Nov | 12:02 | −90.7 | PE −14.2 % |
| 4 Nov | 10:34 | −107.1 | PE −2.7 % |
| 6 Nov | 10:27 | +147.9 | CE +9.5 % |
| 12 Nov | 10:08 | +184.0 | CE −8.7 % |

The noise boundary from the 09:16 anchor (k = 1.0, checked every 30 min, walk-forward from the 6th day) gave 10
signals. 3 moved the right way at 60 minutes, with a median of −23.5 points. At k = 1.5 there were 4 signals, which is
too few. I tried 6 variants.

## Ideas

| # | Idea | Kind | Mechanism | Status | How to build | Risk |
|---|---|---|---|---|---|---|
| 1 | Arm-state commentary | display | The flat reason should say the arm side, impulse size, deepest pullback so far and points still needed, e.g. "armed CE on a 240-pt impulse, pullback 33 % of the 50 % needed, ages out 09:50". It answers "why silent" and takes a clear stand. | untested (display) | Expose `self.arm` from c20_08 through the adapter into `conductor.py:174-176` and the commentary row. | none to P&L; a little per-step cost |
| 2 | Pullback depth × arm age sweep | entry | A shallower pullback (25 to 40 %) or a longer arm life catches the arms that now age out in trends | untested; phase B ready | `phaseB_pb_sweep.py` (12 variants, walk-forward pick); then a shadow c20_9x clone with new `pb` / `PB_AMAX` | more entries at worse prices in chop |
| 3 | Age-out trend entry (AGE) | entry | When an arm ages out with deepest retrace < 35 %, the trend is real: buy its side | untested; phase B ready | `phaseB_pb_sweep.py` reports AGE trades and the futures continuation after age-out | buys late in mature trends |
| 4 | FLAG continuation | entry | Efficient impulse (ER ≥ 0.55), pause of 15 to 50 %, new extreme → buy | 3 trades only, untested | `phaseB_c20_complements.py ALL` | small sample |
| 5 | Yielding filler (retest family + pre-emption) | entry / guard | A filler trades the silent stretches but steps aside when c20 fires, which removes the crowd-out | tested approximately: test +78 % to +83 % vs pool; fails strike rate and worst day | Conductor change: in the `occupied` branch (`conductor.py:148-151`), if the holder is a `standing: filler` member and a c20 member fires, close the account at the held contract's bid and assign the new owner. Run it as a shadow account first. | pre-emption exit price not yet measured exactly; 5 Nov −19 % |
| 6 | Breadth-with gate for any filler | guard | Fillers on the side the heavyweights' breadth favours lose less | weak: 47 % of 100 positive on test vs 31 % ungated; not a selection | rule `breadth_dir` signed ≥ 0.5 on the pool entry | weak evidence |
| 7 | Stop adding c20 variants to the pool | selection | The five books are one signal; a new variant changes exits, not coverage | fact (140 distinct triggers / 543 trades) | pool policy | none |
| 8 | Opening-drive family | entry | No book trades 09:15 to 09:35 trends; c20 cannot | untested; the noise-boundary version failed 3/10 | a new shadow book with a short 5 to 10 min window and 09:20 to 10:00 only, judged walk-forward | opening reversals (12 Nov topped at 10:02) |
| 9 | V-turn reversal (REV) | entry | When an arm is dropped for > 75 % retrace and the forward crosses the impulse base, buy the other side | untested | `phaseB_c20_complements.py ALL` | catches false breaks |
| 10 | Align the entry end with LAST_ENTRY | other | Normal-day c20 stops at 15:00, but the engine allows 15:15 | untested, small | — | late theta; little room left |

Multiple testing: 600 (E3) + 144 (E4) + 6 (E5) = 750 account-level or signal variants were tried. Only the E4
pre-emption setting shows a consistent shift across books, and it rests on 5 test days.

## Phase B scripts (to run after 15:30; same rules: one at a time, low priority)

* `data/research/13nov/work/R01/phaseB_c20_complements.py ALL` runs every normal day in ds_v2 (12 Nov is not built).
  It gives the c20 replica arm census and the FLAG, GRIND and REV families with c20_9x normal-day exits.
* `data/research/13nov/work/R01/phaseB_pb_sweep.py` covers: the arm census with the futures continuation 15 and
  30 min after each age-out; the AGE entry; and the pullback depth {0.25, 0.33, 0.40, 0.50} × arm age {600, 900,
  1,200} sweep, picked walk-forward (discovery to 4 Nov, test from 5 Nov).
* Still to write: exact pre-emption exit prices from the per-second bids (ds_v2 `opt`), replacing the hold-mark
  approximation in E4.

## Files

Scratch scripts: `s04_timeline.py`, `s06_fillers_fast.py`, `s07_sum.py`, `s09_silent.py`, `s10_yield.py`,
`s11_open.py`, `s12_noise.py`.

Outputs: `minutes.pkl`, `silent_stretches.csv`, `conductor_days.csv`, `fillers_all.pkl`, `yield.pkl`,
`noise_signals.csv`, `phaseB_c20_complements_11-05_11-06_10-30.json`.

## Sources

- Kaufman efficiency-ratio gate (open script): https://www.tradingview.com/script/2Ghnhfqg-Kaufman-Efficiency-Ratio-Gate-NovaLens/
- Intraday regime classifier (trend → breakout or pullback, rotation → fade): https://jp.tradingview.com/script/bDi5IxpW-Intraday-Regime-Classifier
- Zarattini, Aziz, Barbon, "Beat the Market: an effective intraday momentum strategy for SPY", SFI 24-97: https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy
