# R03: Day types and regimes (owner point 3: "not the same way every day")

Analyst R03, 13 Nov 2026. Data: `data/research/13nov/trades_all_books.parquet` (20,817 trades, 107 books, 17 days),
per-second Nifty futures mid for 16 days (forecast-lab collect, checked against ds_v2), the shipped Conductor sims.
Scratch and every script: `data/research/13nov/work/R03/`.

## Findings first

1. **The Conductor has no day-type brain at all.** It reads one fixed pool with fixed priorities every day
   (`apex/rules/pool.json`, `apex/engine/conductor.py:95-97`). The only "day type" anywhere in the c20 code is expiry
   versus not expiry (`apex/engine/council/c20_08.py:53`). The c20 opening-range direction lock exists
   (`apex/engine/council/c20_20.py:115-126, 164`) but **the pool books do not use it**: `c20_8x.py:295` FINAL drops "orb"
   and `c20_9x.py:69` builds on that. So on a clean trend-up day the pool still buys puts on every 40-point dip.
2. **The money is made on expiry and the day before.** Strike rate: day before expiry 9 of 10 trades (90 %), expiry
   36 of 66 (55 %), all other days 18 of 43 (42 %). Mean day: +151 %, +140 %, +21 %. Ordinary days are a coin toss.
3. **Where it does something stupid: clean one-way mornings.** On the 4 days that were a clean trend by 10:15
   (23 Oct, 2, 3, 4 Nov), the Conductor's trades after 10:15 lost on 3 of 4 days (mean -11 %, median -27 %). On 4 Nov
   (Nifty +265 points, closed at the high) it bought PE at 10:34, 11:11 and 12:04. On 3 Nov (gap up, trend up, expiry)
   three PE buys after 13:54 lost 14 %, 20 % and 15 %.
4. **A declared trend lock fixes most of that, on in-sample days.** "From 10:15, on a clean-trend morning, the pool may
   only buy in the morning's direction": strike 55.7 % vs 52.9 %, losing days 4 vs 5, worst day -17.7 % vs -36.3 %,
   +48.6 points of daily return over 17 days, all 12 top trades kept. The 11:00 version: +80.5 points, 2 days better,
   0 worse. **But no test day (5 to 12 Nov) was a clean-trend morning, so the late window cannot confirm it.** Shadow only.
5. **Picking book families by detected day type does not work on 17 days.** 108 adaptive-pool variants: 17 beat the
   Conductor, 53 lost to it, 38 changed nothing. Trade-level regime vetoes from the weather photograph chosen on the
   early days: of the 5 best, **0 of 5** helped on the test days; 24 of 136 helped at all. This is the clearest sign that
   "choose by regime" overfits at this sample size.
6. **Day types can be described but the rest of the day cannot be called.** A leave-one-day-out classifier of "will the
   rest of the day be one-way" scores 0.65 at 09:45 and 10:15 against a 0.53 majority guess, and 0.41 at 11:00 against
   0.65. Continuation of the morning move held on 10 of 17 days at every checkpoint (no edge over 59 %).
7. **Gap-and-go days hurt almost every family** (2, 3, 5 Nov): the c20 family averaged -2.9 % a book-day there, and only
   two small families were positive. Three days only.

## Teardown (what the code does in this area, and where it fails)

| Place | What it does | Where it fails for day types |
|---|---|---|
| `apex/engine/regime.py:1-35, 143-159` | 5-minute micro regime (ER5, breadth, VWAP stretch, activity) at 1 Hz, labels WARMING / EXHAUSTION / BREAKOUT / DIRECTIONAL / COMPRESSION / RANGE / UNCERTAIN | It is a 5-minute state, not a day type. Nothing remembers "today has been a trend since 09:15". |
| `apex/config.py:63-64`, `apex/engine/paper.py:973-990` | `base_gate` blocks entries in RANGE / UNCERTAIN / COMPRESSION / EXHAUSTION for impulse books | The c20 pool trades in every state (table E5): 31 Conductor trades in UNCERTAIN, 22 in RANGE, 20 in COMPRESSION. The gate does not bind the pool. |
| `apex/conductor/diary.py:51-57` | `day_type()` for the diary | Only EXP / NORM / UNK. |
| `apex/engine/council/c20_08.py:21, 37, 53` | Two modes: EXP (0 DTE breakout) and NORM (40-pt impulse, 50 % pullback, 5-pt resumption) | The mode is chosen by the calendar only. A NORM pullback buy is taken the same way on a trend day, a range day and a V day. |
| `apex/engine/council/c20_20.py:15-16, 30, 115-126, 164` | ORB direction lock: after a break of the 09:15-09:45 range only trade that side | Dropped from the pool: `c20_8x.py:295` FINAL = exp, norm, seq, pex, pbg, d52 (no "orb"); `c20_9x.py:69` FINAL_R9 adds exit and expiry parts only. |
| `apex/engine/council/c20_9y.py:3-6` | IV_RICH veto (both day types) | Only c20_9y has it. On 3 Nov afternoon the three PE losers it vetoed were taken by c20_9s through the pool. |
| `apex/engine/conductor.py:72-97`, `apex/rules/pool.json` | Pool as of the day; same-tick priority by standing, then in-sample `ret_per_trade` | Static all day. No market state changes who may trade. |

The Conductor's losing trades on the clean-trend mornings (shipped sims, p44_sim / p44_simr):

| Day | Morning | Trades after 10:15 (time, side, return) |
|---|---|---|
| 23 Oct | down, ER 0.39 | 11:02 PE -3, 11:22 CE -11, 11:44 PE -3, 12:23 CE -14 (whipsaw both ways after a +77 % PE at 09:41) |
| 3 Nov (expiry) | gap up, trend up | 13:54 PE -14, 14:18 PE -20, 14:24 PE -15 (all c20_9s, against the day) |
| 4 Nov | trend up all day | 10:34 PE -3, 10:54 CE -11, 11:11 PE -10, 11:27 CE -9, 12:04 PE +1 |
| 2 Nov | gap up, trend up | 12:02 PE -14, 12:58 PE +41, 13:20 PE +17, 14:36 CE +1 (the one day the counter-trend puts won) |

## Evidence

### E1. The 17 day labels (futures mid 09:15 to 15:25)

Rules declared before looking at results: trend if the close-minus-open is at least 55 % of the range and the close is
in the outer quarter; V if the first leg took at least 35 % of the range and the close recovered 65 % of it; gap overlay
at |gap| >= 0.30 % ("go" = moved with the gap and never filled it).

| Day | Calendar | Type | Net pts | Range | Gap % | Conductor % |
|---|---|---|---|---|---|---|
| 19 Oct | expiry | trend down | -251 | 309 | -0.02 | +21.8 |
| 21 Oct | | trend down (gap filled) | -262 | 470 | +0.57 | +48.1 |
| 22 Oct | | range | +75 | 256 | -0.25 | +7.8 |
| 23 Oct | | range (gap filled) | -232 | 407 | +0.31 | +25.2 |
| 26 Oct | day before | trend up | +202 | 338 | -0.08 | +260.9 |
| 27 Oct | expiry | range | +70 | 201 | -0.06 | +532.0 |
| 28 Oct | | V up (gap filled) | +82 | 297 | -0.32 | +56.2 |
| 29 Oct | | trend up | +306 | 344 | -0.08 | +24.8 |
| 30 Oct | | range | +91 | 214 | +0.11 | -5.6 |
| 2 Nov | day before | gap and go up | +151 | 180 | +0.93 | +41.6 |
| 3 Nov | expiry | gap and go up | +257 | 272 | +1.04 | -36.3 |
| 4 Nov | | trend up | +265 | 278 | +0.05 | -26.7 |
| 5 Nov | | gap and go up | +267 | 322 | +1.93 | -5.9 |
| 6 Nov | | trend up | +611 | 674 | -0.18 | +100.2 |
| 9 Nov | expiry | V up (gap filled) | -29 | 228 | +0.53 | +43.2 |
| 11 Nov | | V down (gap faded) | -106 | 292 | +1.30 | +9.0 |
| 12 Nov | | range | -20 | 183 | +0.22 | -4.0 |

12 Nov has no per-second file; its path is built from all books' entry and exit futures prints (checked on 11 Nov:
median error 1.7 pts, 90th percentile 5.9 pts). The forecast-lab futures mid equals the ds_v2 mid on 4 Nov
(4 marks, under 1 pt). Count: trend up 4, gap and go 3, range 5, trend down 2, V up 2, V down 1.

### E2. The Conductor by day type (shipped sims, each day from 1 lakh)

| Type | Days | Mean day % | Median | Days up | Trades | Strike |
|---|---|---|---|---|---|---|
| trend up | 4 | +89.8 | +62.5 | 3 | 19 | 68 % |
| gap and go | 3 | -0.2 | -5.9 | 1 | 18 | 56 % |
| range | 5 | +111.1 | +7.8 | 3 | 28 | 50 % |
| trend down | 2 | +34.9 | +34.9 | 2 | 23 | 39 % |
| V up | 2 | +49.7 | +49.7 | 2 | 27 | 56 % |
| V down | 1 | +9.0 | +9.0 | 1 | 4 | 50 % |
| **Calendar** | | | | | | |
| day before expiry | 2 | +151.3 | +151.3 | 2 | 10 | 90 % |
| expiry | 4 | +140.2 | +32.5 | 3 | 66 | 55 % |
| other | 11 | +20.8 | +9.0 | 7 | 43 | 42 % |

Range days look good only because of 27 Oct (+532 %). Without it the four range days average +5.9 % (8, 25, -6, -4).

### E3. Book families by day type (mean book-day return %, every book alone, all-in)

| Family | trend up (4) | gap go (3) | range (5) | trend down (2) | V up (2) | V down (1) |
|---|---|---|---|---|---|---|
| c20 council (pool family) | +66.3 | -2.9 | +85.3 | +44.6 | +38.2 | +13.9 |
| c20 exit / re-entry twins | +72.9 | +5.0 | +96.6 | +78.5 | +47.4 | -2.9 |
| t28 45-min pullback | +12.7 | -3.6 | +26.0 | +106.1 | +32.7 | +4.0 |
| lvl_trail pullback | +17.7 | -5.3 | +25.9 | +80.0 | +32.2 | +17.9 |
| spot 45-min pullback | +11.6 | -8.9 | -6.4 | +81.7 | +10.8 | +24.3 |
| spot retest | +20.2 | -11.1 | -1.0 | +62.2 | +19.4 | +3.7 |
| spot first-touch | +3.9 | -10.6 | +16.9 | +22.8 | +44.9 | -6.7 |
| opening range | +7.2 | -9.2 | +4.9 | +13.5 | +16.9 | +15.3 |
| burst fade | -13.1 | -0.1 | +0.3 | +73.9 | -35.3 | -33.0 |
| impulse + basket m-grid | +2.8 | -4.4 | +7.5 | -6.0 | +14.8 | -1.1 |
| edge | +2.7 | -2.9 | +14.5 | +19.7 | -5.1 | +20.1 |
| straddle spike | -1.8 | -21.5 | +0.5 | -12.5 | -27.0 | 0.0 |
| controls | +1.1 | -19.6 | -1.8 | -18.7 | +11.3 | +13.7 |

Full tables (strike rates, gap and calendar splits, family by day): `work/R03/fam_by_dtype.csv`, `fam_by_cal.csv`,
`fam_day.csv`. Reading: on the two trend-down days the pullback families beat c20; on gap-and-go days nearly
everything lost. Each cell is 1 to 5 days, so none of this is proof.

### E4. Early-day classifier, leave-one-day-out (17 days; LODO is the only honest scheme at this size)

Features at the checkpoint: move so far, range so far, efficiency so far, position in range, signed range share,
chop, last-15-min move, opening-range break, gap, range versus earlier days, plus the engine photograph (wx_er_day,
wx_range_vs_norm, VWAP stretch, VIX change). A one-split stump is refitted inside every fold (about 383 candidate
splits per fold), and a 3-nearest-neighbour vote on five core features.

| Checkpoint | Target | Majority guess | Declared rule | LODO stump | LODO 3-NN |
|---|---|---|---|---|---|
| 09:45 | whole day is a trend | 0.53 | 0.65 | 0.65 | 0.71 |
| 09:45 | rest of day one-way | 0.53 | 0.53 | 0.65 | 0.65 |
| 09:45 | rest continues the morning | 0.59 | 0.35 | 0.47 | 0.35 |
| 10:15 | whole day is a trend | 0.53 | 0.59 | 0.76 | 0.76 |
| 10:15 | rest of day one-way | 0.53 | 0.41 | 0.65 | 0.65 |
| 10:15 | rest continues the morning | 0.59 | 0.53 | 0.41 | 0.65 |
| 11:00 | whole day is a trend | 0.53 | 0.47 | 0.76 | 0.59 |
| 11:00 | rest of day one-way | 0.65 | 0.35 | 0.41 | 0.59 |
| 11:00 | rest continues the morning | 0.59 | 0.41 | 0.53 | 0.59 |

The whole-day label is easy late in the morning because the morning is part of it. What matters for trading (the rest
of the day) is at best 2 days in 17 better than a guess. The fixed split (fit 19 Oct to 4 Nov, test 5 to 12 Nov,
5 days) gives 0.6 / 0.6 / 0.8 for the whole-day label and 0.2 / 0.4 / 0.6 for the rest-of-day label.

### E5. Conductor trades by the engine's own regime label at the trigger

| Label | Trades | Strike | Mean % |
|---|---|---|---|
| DIRECTIONAL | 31 | 55 % | +7.9 |
| UNCERTAIN | 31 | 45 % | +1.9 |
| RANGE | 22 | 55 % | +7.9 |
| COMPRESSION | 20 | 55 % | +8.5 |
| WARMING | 11 | 64 % | +10.2 |
| BREAKOUT / EXHAUSTION | 2 / 2 | 50 % | small |

Pool-book trades (543) in UNCERTAIN: early days 57 % strike, test days 28 %, the one label that was weak in both
windows. Trades in the gap's direction: early 54 % / +3.7 %, test 45 % / +2.0 %; against the gap: 65 % / +12.1 % and
62 % / +7.0 %. Consistent in both windows, but vetoing either one in the account simulator still lost money (E7).

### E6. Adaptive pool, walk-forward

Simulator: the one-account rules of `account_sim` (one position, all-in, same-tick priority by pool order, a trigger
inside a held trade is skipped) on the parquet trades. It reproduces the shipped Conductor exactly: 119 trades,
sum of daily returns +1,092.5 % (= +10.92 lakh on 1 lakh a day).

Detectors at the checkpoint (all causal): **dec** = efficiency so far >= 0.30 and |move| >= 60 % of the range so far
(declared, not tuned); **gapgo** = |gap| >= 0.30 % and the move so far is with the gap; **cal** = expiry or day before;
**stump** = the LODO classifier; **oneway** = price in the outer 15 % of the range on the side of the move.
Policies, all learned only from training days of the same detected type: P1 / P1m go flat after the checkpoint if the
pool lost after it on such days (mean / median); P4 keep c20 first and add up to two books that won there on at least
60 % of days; P5 swap c20 for the best family representative there.

108 variants (4 policies x 3 checkpoints x 5 detectors x LODO or fixed split, less 4): **17 better, 53 worse,
38 no change.** The best ones:

| Variant | Scheme | Strike | Trades | Sum of daily % | vs Conductor | Losing days | Worst day | Without best day | Top trades kept | Better / worse days |
|---|---|---|---|---|---|---|---|---|---|---|
| Conductor | all 17 | 52.9 % | 119 | 1,092.5 | 0 | 5 | -36.3 | 560.4 | 12/12 | |
| P1 10:15 dec | LODO | 56.2 % | 96 | 1,156.7 | +64.2 | 4 | -5.9 | 624.6 | 12/12 | 3 / 1 |
| P1 10:15 dec | fixed (5 test days) | 51.4 % | 35 | 142.5 | 0 | 2 | -5.9 | 42.3 | 3/3 | 0 / 0 |
| P4 09:45 dec | LODO | 56.3 % | 135 | 1,154.0 | +61.5 | 4 | **-43.3** | 621.9 | 11/12 | 5 / 3 |
| P4 09:45 dec | fixed | 55.6 % | 36 | 165.6 | +23.1 | 1 | -7.7 | 65.3 | 3/3 | 2 / 1 |
| P4 09:45 oneway | fixed | 53.7 % | 41 | 202.9 | +60.4 | 2 | -5.9 | 99.4 | 2/3 | 1 / 0 |
| P5 10:15 stump | LODO | 45.9 % | 133 | 375.4 | -717.1 | 5 | -36.3 | 275.1 | 1/12 | 2 / 4 |

P1 10:15 dec per day: 23 Oct +25.2 to +71.5 (flat after the 09:41 winner), 2 Nov +41.6 to 0, 3 Nov -36.3 to -3.4,
4 Nov -26.7 to 0; all other days unchanged. P4 09:45 dec adds spot_pb45 on trend mornings: 21 Oct +48 to +97,
4 Nov -27 to +12, but 2 Nov +42 to -7 and 3 Nov -36 to -43, so the worst day gets worse and it fails the standard.
Full table: `work/R03/adaptive_summary.csv`; per-day: `adaptive_perday.pkl`.

### E7. Trade-level regime vetoes, discovered early, tested late

For 43 numeric photograph items and 10 labels, terciles were cut on 19 Oct to 4 Nov, each bucket became a veto, and the
veto was replayed in the account simulator. 136 variants. Ranked by early gain, **the top 5 all lost on the test days**
(range_vs_pd high: early +161, late -72; give low: +97 / -96; inside_pd false: +96 / -93; er_day high: +42 / -89;
hw_disp300 high: +24 / -67). 24 of 136 gained on the test days. Table: `work/R03/veto_walkforward.csv`.

### E8. Day-direction locks (declared rules, nothing fitted; 14 variants)

| Rule | Strike | Trades | Sum % | vs Conductor | Early / late change | Losing days | Worst | Without best day | Top kept | Better / worse |
|---|---|---|---|---|---|---|---|---|---|---|
| Conductor | 52.9 % | 119 | 1,092.5 | | | 5 | -36.3 | 560.4 | 12/12 | |
| L1 dec 10:15 | 55.7 % | 106 | 1,141.1 | +48.6 | +48.6 / 0 | 4 | -17.7 | 609.0 | 12/12 | 3 / 1 |
| L1 dec 11:00 | 55.4 % | 112 | 1,172.9 | +80.5 | +80.5 / 0 | 4 | -26.7 | 640.9 | 12/12 | 2 / 0 |
| L1 oneway 11:00 | 55.4 % | 112 | 1,172.9 | +80.5 | +80.5 / 0 | 4 | -26.7 | 640.9 | 12/12 | 2 / 0 |
| L1 dec 09:45 | 55.0 % | 100 | 1,023.6 | -68.9 | -49.7 / -19.2 | 5 | -17.7 | 491.5 | 11/12 | 3 / 4 |
| L1 gapgo 10:15 | 52.9 % | 104 | 1,028.9 | -63.5 | -52.9 / -10.7 | 5 | -26.7 | 496.9 | 12/12 | 2 / 3 |
| L2 every day, 10:15 | 55.1 % | 69 | 648.5 | -444.0 | | 5 | -17.7 | 466.6 | 10/12 | 8 / 8 |
| L3 with the day's move | 53.1 % | 64 | 430.6 | -661.8 | | 4 | -17.7 | 350.8 | 8/12 | 9 / 8 |
| L4 VWAP side only | **59.2 %** | 76 | 656.0 | -436.5 | -454.0 / **+17.5** | **3** | **-10.1** | 499.8 | 10/12 | 10 / 6 |

L1 dec 10:15 per day: 23 Oct 25 to 61, 2 Nov 42 to 1, 3 Nov -36 to 8, 4 Nov -27 to -18. L1 dec 11:00 touches only
23 Oct (25 to 61) and 3 Nov (-36 to 8). Applied to every book alone on the dec days (`work/R03/lock_allbooks.csv`):
the c20 family improves on 28 of 36 book-days at 10:15 (vetoed trades won only 34 %) and 19 of 19 at 11:00 (vetoed
trades won 22 %). The pullback families (t28, lvl_trail) get worse, so the lock belongs to c20 only. Locking every day
(L2, L3) destroys 26 and 27 Oct: the c20 edge on range and V days is exactly the counter-move.

L4 (only buy on the VWAP side) is the one rule that improves the owner's first measures in both windows: strike 59 % vs
53 %, losing days 3 vs 5, worst day -10 % vs -36 %, test window +17.5 points with 57 % vs 51 % strike. It costs
-436 points over 17 days because it cuts 27 Oct from +532 % to +107 % and 26 Oct from +261 % to +156 %.

### Multiple testing, in one place

Classifier: about 383 splits per fold x 9 targets. Adaptive pool: 108. Trade vetoes: 136. Locks: 14. Total policy
variants scored on returns: 258. The two L1 rules were written down before they were scored, but the "dec" detector
also appears in the 108, so treat L1 as one of roughly 20 rules of its kind, not a single pre-registered test.

## Ideas

### I1. c20 trend lock (shadow book `c20_tl`, or a Conductor shadow `conductor_tl`)
* Mechanism: c20 NORM buys the resumption after a 50 % pullback of a 40-pt impulse. On a clean one-way morning the
  counter-trend "impulses" are just pauses, so the counter-trend buys lose (vetoed trades won 22-34 %).
* Rule: at 10:15 (or 11:00), if efficiency since the open >= 0.30 and |futures minus open| >= 60 % of the range so far,
  pool books may only buy in the direction of futures minus open for the rest of the day. Expiry days included
  (3 Nov was one). Two numbers, both declared before scoring.
* Test: E8. +48.6 / +80.5 points, worst day better, all top trades kept, 3/1 and 2/0 days. In sample only (no trend
  morning on 5 to 12 Nov, nor on 9, 11 or 12 Nov live). Fails "passes in two windows" until a test day comes.
* Build: a 20-line layer in the Conductor (or c20_20 style part "tlock" reading rows <= i only), logged as
  `rule_block` with "trend lock: morning up, ER 0.35, PE refused". Shadow first.
* Risk: a trend morning that turns into a V. 2 Nov is the warning: the counter-trend puts won +41 % and +17 %. With 4
  trigger days, one bad day erases the gain.

### I2. Re-test the dropped ORB lock on the pool (untested here)
* `c20_20.py` has it, the pool does not (`c20_8x.py:295`). It is a cruder cousin of I1 (it locks on the 09:45 break and
  flips on the other edge). Needs an engine replay of a `c20_9y + orb` shadow; that is a long run, so it needs the
  owner's OK. Not run.

### I3. VWAP-side shadow for strike rate (shadow book `c20_vw`)
* Mechanism: only buy CE above session VWAP and PE below it. Removes the trades that fight the day's balance point.
* Test: E8 L4. Strike +6 points, losing days 5 to 3, worst day -36 % to -10 %, test window better (+17.5). Gives up the
  27 Oct runners. Owner rule says strike rate first, so it deserves a shadow, but it fails "keeps most top trades"
  in spirit (10/12 kept, but the biggest day shrinks by 80 %).
* Build: one veto in the Conductor on `wx_vwap_ext` signed by the trade (already in the photograph).

### I4. Show the day type and take a stand (display change, owner point 4)
* At 09:45, 10:15 and 11:00 the forecaster card prints one line in first person, from the E1 measures that are already
  live (efficiency since open, position in range, gap status, calendar):
  "Today so far: a clean trend up (efficiency 0.35, holding the top of its range, gap not filled). I buy only calls
  from here; dips that a pullback book would buy as puts I will skip." or "Today so far: two-way, no trend (efficiency
  0.05). The pool trades both sides as usual." or "Gap up 1.0 % and going: on such days every book family lost on
  average; I will be choosy."
* No numbers needed beyond what E1 uses; costs microseconds per minute.

### I5. Calendar honesty in the commentary (display only)
* Say plainly: expiry and the day before carry the edge (90 % and 55 % strike); ordinary days are 42 %. A gate on
  ordinary days is not proposed: their mean is still +21 % and the sample is 11 days.

### I6. Pullback family on trend-down mornings (watch only)
* t28, lvl_trail and spot_pb45 beat c20 on the two trend-down days. P4 09:45 dec (add spot_pb45 on trend mornings)
  was +61.5 LODO and +23.1 on the test days, but made the worst day worse (-43 % vs -36 %). Fails the standard. Keep
  the family-by-day-type table updating nightly; revisit at 30 days.

### Rejected (tested, do not build)
* Choosing families by detected day type (P2 to P5): 17 of 108 better, mostly tiny; the swap policy P5 is the worst.
* Single weather-item vetoes chosen on early days: 0 of the top 5 survive the test days.
* Locking direction every day (L2, L3): kills the range-day edge.
* Going flat after 09:45 on any detected type: every 09:45 policy lost.

## Phase B scripts (ready, not run in full; same rules, after 15:30)

| Script | What it does | Run |
|---|---|---|
| `data/research/13nov/work/R03/phaseB_daytypes_dsv2.py` | Rebuilds the day labels and checkpoint features from every ds_v2 part (multi-part days joined), adds Nifty-weighted heavyweight breadth, top-3 share, dispersion and lead versus futures at 09:45 / 10:15 / 11:00, compares labels with s03, re-runs the LODO stump with the heavyweight features | `py -3.13 phaseB_daytypes_dsv2.py` (smoke-tested now on 4 and 5 Nov with `R03_TEST=1`; labels agree) |

Scripts already run now (all under `work/R03/`): `s02b_paths.py` (futures paths), `s03_all.py` (labels, features,
book-day tables), `s03b_fam.py` (family tables, Conductor by day), `s04_classify_pool.py` (classifier),
`s05_adaptive.py` (108 adaptive variants), `s06_trade_regime.py` (136 vetoes), `s07_ds_check.py` (ds_v2 check, one part),
`s08_trend_lock.py` (14 locks), `s09_lock_allbooks.py` (lock on every book).

Limits: 17 days, 6 of them expiry or day before; 26 and 27 Oct dominate every sum; every day before 9 Nov is in sample
for the c20 books themselves; the simulator replays recorded trades, so a lock that frees the account cannot create the
new trades a live Conductor would then take (it can only skip). No web search was run in this attempt; the day-type
ideas follow the efficiency-ratio and opening-range literature already cited in `apex/engine/regime.py` and
`c20_20.py`.
