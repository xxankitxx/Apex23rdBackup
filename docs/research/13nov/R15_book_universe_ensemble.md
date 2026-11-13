# R15. The whole book universe, and whether a smarter way of choosing books beats the Conductor (13 Nov 2026)

Lens: owner points 1 and 3. All 107 books on the 17 replayed days, and meta-strategies that pick books under the
Conductor's one-position rule. Every number below is walk-forward unless it says "in sample".

## Findings first

1. **The pool is one signal, not five.** The five pool books fire on the same second. In the 17-day replay the
   Conductor logged 398 "lost priority" events (same-second ties) and only 26 "occupied" events. Of its 119 trades,
   95 came from c20_9y, 13 from c20_9s, 9 from c20_9t, 2 from c20_9v and none from c20_9x. Daily returns of the council
   books correlate 0.82 with each other.
2. **Pooling the c20 books added nothing.** Over 17 days the pool made +1,092 % (sum of daily returns), c20_9y alone
   +1,185 %, c20_9s alone +1,125 %, c20_9v alone +1,109 %. On the later days (5 to 12 Nov) the pool made +142.5 %,
   c20_9v alone +147.5 % with 1 losing day, c20_8x alone +161.5 %.
3. **No book ranking carries over from one day to the next.** Across the 106 books, the rank correlation of today's
   return with yesterday's averages 0.16. With the last 3 days it is 0.10. It was negative on 6 of the last 9 days.
   This is the hard reason why "rules that do not work every day" cannot be fixed by rotating to whatever worked
   recently.
4. **336 meta-strategy variants tested; none passes the owner's 7-test standard in both windows.** Best-of-recent,
   family rotation, ensemble votes, curated confirmations, veto rules, fill-in books, static additions and day stops
   all either lose the 26 to 27 Oct type big wins (window 1) or lose to the pool on 5 to 12 Nov (window 2). The
   variants that look best on 5 to 12 Nov are what you would expect by luck from 336 tries.
5. **Non-c20 books that held up on 5 to 12 Nov:** t28_fill, edge_bracket_only, t28_dur20, spot_ft_prem10,
   lvl_trail_rx_be, t28_tt8. The t28 and level-trail families correlate only about 0.2 with the council, so they are a
   genuinely different signal. But a non-council Conductor chosen on the early days lost to the pool on the later days
   in all 5 ways I chose it.
6. **The nearest miss is a confirmation filter.** Take a pool trigger only when at least one t28, level-trail, spot or
   edge book fired the same side in the previous 2 minutes. On 5 to 12 Nov it won 61 % of trades against the pool's
   51 %, made +154 % against +142.5 %, with no losing day. On 23 Oct to 4 Nov it dropped the big 26 and 27 Oct wins
   and made +336 % against +872 %. It fails test 7 (holds over time). It is worth a shadow book, not a promotion.

## Teardown

### What the code does

* `apex/conductor/account_sim.py:28-41` lists every pool book's trades by trigger time, ties broken by
  `apex/engine/conductor.py:95-98` `priority_key` (standing, then `ret_per_trade`, then book order).
* `account_sim.py:52-67`: while holding, a later trigger is "occupied", a same-second trigger is "lost priority".
* `account_sim.py:77-85`: all-in lots `capital // (entry * 65)`, P&L at the book's own fill and exit, capital
  compounds through the day. The engine does the same at `conductor.py:244`.
* `conductor.py:191`: the first eligible trigger in priority order takes the account. Nothing looks at the other
  books' state, the day's record, or agreement between families.
* `apex/rules/pool.json`: five c20 books, all `standing: low`, `rule: null`, ranked by `ret_per_trade` taken from the
  discovery days (`"ret_basis": "discovery days (in-sample)"`, written by `apex/conductor/pool_builder.py:71-72`).

I re-implemented the account rule on the trade table (`work/R15/simlib.py`, `sim_day` and `sim_fast`). It matches
`conductor_sim.json` on all 17 days to the trade count, win count and day return to two decimals.

### Where it fails

| # | Failure | Evidence | Where |
|---|---|---|---|
| T1 | Priority is decided by in-sample `ret_per_trade`, and only ever matters on a same-second tie. The ties are between near-copies, so the order just means "c20_9y wins". | 398 lost-priority ties versus 26 occupied; 95 of 119 trades from c20_9y | `conductor.py:95-98`, `pool.json` |
| T2 | The pool is one family. When the c20 pattern fails (a straight-line rally, a chop day), every member fails the same way. | Council daily-return correlation 0.82. On the pool's losing days (30 Oct, 3, 4, 5, 12 Nov) c20_9y, 9s and 9x lost on all five; 3 and 4 Nov were losses for every member. c20_9t was positive on 30 Oct (+19 %), 5 Nov (+4.8 %) and 12 Nov (+6.3 %), but the account took c20_9y's earlier trigger instead | `pool.json`, `conductor.py:191` |
| T3 | The Conductor has no view of the rest of the universe. 100 other books run in shadow; their triggers never inform the account. | `_fired` reads only pool members | `conductor.py:201-222` |
| T4 | `ret_per_trade` is never updated from forward days. The pool still ranks on the 14-day in-sample card. | `ret_basis` is "discovery days (in-sample)" on all five rows | `pool_builder.py:71-72, 92-93` |
| T5 | The near-copies produce identical trades: RAW equals c20_9x on every day; m1.5/m2.0/m2.5 at the same s give identical trades; rx_c20_9y and fr_c20_9y nearly match c20_9y on 5 to 12 Nov (+136.3 % and +136.8 % against +136.3 %). Any vote that counts books (not families) is fooled by this. | book_stats.csv | config.VARIANTS |

## Evidence

Days: early = 19 Oct to 4 Nov (12 days), later = 5 to 12 Nov (5 days). "Sum %" = sum of daily returns on a fresh
1 lakh a day (all-in, compounded within the day). Note that 5 and 6 Nov are also in sample for the c20 books, so only
9, 11 and 12 Nov are truly out of sample for the pool baseline. This makes the pool a harder bar to beat than it
should be.

### E1. Every book, the two halves (selected rows; all 107 in `work/R15/book_stats.csv`)

| Book | Family | Early trades | Early win % | Early sum % | Early losing days | Later trades | Later win % | Later sum % | Later losing days | Later worst day % | Later sum without best day % | Corr. with pool account |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Conductor (pool) | | 84 | 53.6 | +950 | 3 | 35 | 51.4 | +142.5 | 2 | -5.9 | +42.3 | 1.0 |
| c20_9y | council | 68 | 60.3 | +1,049 | 3 | 31 | 48.4 | +136.3 | 3 | -5.9 | +42.1 | 1.0 |
| c20_9v | council | 78 | 60.3 | +961 | 2 | 32 | 53.1 | +147.5 | 1 | -4.0 | +52.1 | 1.0 |
| c20_8x | council | 78 | 48.7 | +740 | 3 | 33 | 48.5 | +161.5 | 2 | -5.9 | +67.2 | 1.0 |
| c20_9t | council | 85 | 68.2 | +348 | 5 | 37 | 64.9 | +51.9 | 0 | +4.8 | +31.9 | 0.9 |
| c20_9e | council | 96 | 59.4 | +496 | 3 | 41 | 63.4 | +124.8 | 2 | -5.9 | +30.6 | 0.7 |
| spot_ft_prem10 | spot | 397 | 51.9 | +82 | 6 | 132 | 56.8 | +267.6 | 2 | -37.2 | +74.6 | 0.4 |
| t28_st20 | t28 | 85 | 54.1 | +320 | 3 | 35 | 57.1 | +171.6 | 2 | -21.1 | +4.6 | 0.2 |
| t28_fill | t28 | 166 | 48.2 | +303 | 6 | 60 | 53.3 | +161.5 | 1 | -3.0 | +60.5 | 0.1 |
| edge_bracket_only | edge | 94 | 39.4 | +28 | 6 | 40 | 52.5 | +156.6 | 1 | -15.4 | +54.6 | 0.0 |
| t28_tt8 | t28 | 90 | 58.9 | +214 | 3 | 34 | 58.8 | +146.3 | 2 | -9.6 | +29.5 | 0.0 |
| lvl_trail_rx_be | lvl | 89 | 50.6 | +304 | 4 | 34 | 58.8 | +140.4 | 2 | -12.3 | +40.4 | 0.2 |
| t28_dur20 | t28 | 73 | 52.1 | +298 | 4 | 31 | 54.8 | +134.3 | 1 | -9.6 | +33.2 | 0.3 |
| fade_switch | special | 642 | 51.9 | +145 | 4 | 313 | 42.8 | -156.8 | 5 | -77.6 | -155.2 | -0.4 |
| n01_ctl_flow | gen2_n | 178 | 44.4 | -83 | 9 | 121 | 36.4 | -112.9 | 5 | -50.6 | -102.7 | -0.1 |
| random_entry | control | 71 | 39.4 | -23 | 5 | 30 | 46.7 | -5.4 | 4 | -12.5 | -26.5 | 0.2 |

* 85 of 107 books were positive on 5 to 12 Nov; only 48 stayed positive without their best day.
* Books with early sum > 0, later sum > 0, later sum without best day > 0 and at most 1 later losing day: t28_fill,
  edge_bracket_only, c20_9v, t28_dur20, spot_dc12_t12, spot_dc12_t12_first_r002, spot_dc12_t12_nolock, c20_9t,
  t28_req, c20_9x_r004, and three identical m-grid books with 4 trades.
* Early-to-later rank stability across books (Spearman): sum 0.65, strike rate 0.52, median day 0.40, number of
  losing days 0.19, worst day 0.57. Families keep their level (good stays good), but this is mostly the gap between
  the good families and the broken ones (gen2_n, special); it does not pick a winner among the good ones.

### E2. Correlation between families (mean pairwise correlation of daily returns, 17 days)

| | council | t28 | lvl | spot | edge | mgrid | gen2_n | special |
|---|---|---|---|---|---|---|---|---|
| council | 0.82 | 0.20 | 0.16 | 0.18 | 0.06 | 0.62 | -0.10 | -0.12 |
| t28 | | 0.75 | 0.82 | 0.47 | 0.39 | 0.19 | -0.05 | 0.15 |
| lvl | | | 0.94 | 0.51 | 0.48 | 0.26 | -0.05 | 0.15 |
| spot | | | | 0.42 | 0.17 | 0.17 | -0.07 | 0.07 |

Mean pairwise correlation over all books 0.25. There are really three blocks: council plus m-grid; t28 plus level
trail plus spot plus edge; and the noisy rest.

### E3. The day decides, not the book

| Day | Best book that day | Its day % | Rank of c20_9y (of 106) | Median book % | Share of books > 0 |
|---|---|---|---|---|---|
| 19 Oct | t28_nohigh | +185 | 32 | +36 | 0.63 |
| 26 Oct | RAW (= c20_9x) | +217 | 9 | +2 | 0.60 |
| 27 Oct | RAW (= c20_9x) | +532 | 7 | +40 | 0.86 |
| 30 Oct | t28_fwd | +36 | 41 | -6 | 0.16 |
| 3 Nov | p02_clock | +146 | 26 | -10 | 0.15 |
| 4 Nov | spot_dual | +47 | 101 | 0 | 0.42 |
| 5 Nov | t28_fill | +46 | 57 | -5 | 0.21 |
| 9 Nov | spot_ft_prem10 | +193 | 34 | +28 | 0.75 |
| 11 Nov | t28_ts | +37 | 87 | +2 | 0.53 |
| 12 Nov | t28_fwd | +23 | 62 | -2 | 0.13 |

The best book of the day was a council book on 5 of 17 days. Picking the best book each day with hindsight would make
+2,114 % over 17 days (pool +1,092 %) and +394 % on 5 to 12 Nov (pool +142.5 %). That upside exists, but:

| Persistence test | Mean over days | Values on the last 6 days |
|---|---|---|
| Rank correlation of book returns, today vs yesterday | 0.16 | -0.08, 0.11, -0.28, -0.12, 0.45, 0.29, -0.27 (last 7) |
| Today vs the sum of the last 3 days | 0.10 | -0.45, -0.18, 0.30, 0.32, -0.36 (last 5) |
| Family level, today vs yesterday | 0.23 | -0.43, -0.12, 0.76, 0.56, -0.60 (last 5) |

There is no usable momentum in which book works. A regime classifier that sees the day as it unfolds (R03's lens)
is the only road to the hindsight upside; ranking books by their past cannot get there.

### E4. Meta-strategies, walk-forward (each day's choice uses only earlier days)

Window "later" = 5 to 12 Nov (5 days). Window "rolling" = 23 Oct to 12 Nov (14 days, the first 3 days are warm-up).
Pool baseline: later +142.5 %, 51.4 % won, 2 losing days, worst -5.9 %; rolling +1,015 %, 55.9 % won, 5 losing days.

| Family of meta-strategy | Variants | Beat pool on later sum | Beat pool on later win % | Beat pool on rolling sum | Best later variant (win %, sum %, losing days) | Same variant on rolling |
|---|---|---|---|---|---|---|
| Best-of-recent (top K books by last N days, 6 scores) | 96 | 19 | 24 | 2 | N3 logsum K10: 49.8 %, +403 %, 3, worst -32 | 51.4 %, +1,127 %, 6 losing days, worst -54 |
| Pool first, best recent non-council book fills idle time | 24 | 4 | 2 | 2 | N5 worst K1: 55.9 %, +200 %, 2 | 23 Oct to 4 Nov: +719 % vs pool +872 % |
| Family rotation (best family account by last N days) | 16 | 7 | 0 | 1 | N2 sum: 48.5 %, +496 %, 2, worst -38.7 | 49.5 %, +961 %, 6 losing days |
| Ensemble vote, any K families same side within W | 18 | 2 | 4 | 1 | K3 W300 pool-confirmed: 52.9 %, +150 %, 1 | 56.7 %, +1,025 %, 4 losing days |
| Vote among the 10/20/40 best recent books | 18 | 4 | 4 | 0 | M20 K3 W300: 64.0 %, +222 %, 1 | 23 Oct to 4 Nov: +264 % vs +872 % |
| Pool trigger confirmed / vetoed by other families (all books) | 36 | about 8 | about 10 | | see E5 | |
| Static addition of one non-council book, chosen on early days | 90 | 35 | 39 | | top early pick p05_adaptive: +66 % later | early-to-later rank corr of the gain 0.09 |
| Day stops (losses in a row, drawdown, profit lock, trade cap) | 15 | 2 | 4 | | profit lock at +100 %: +246 % later | early: +510 % vs +987 % |
| Curated confirmation / veto (t28, lvl, spot, edge only) | 12 distinct | 2 | 6 | | see E5 | |
| Non-council Conductor chosen on early days | 5 | 0 | 1 | | best: +99 % later | |
| **Total distinct variants** | **336** | | | | | |

With 336 variants, about 17 would beat the pool on any 5-day window by luck at a 5 % level. The counts above are in
that range.

### E5. The owner's standard on the strongest candidates (vs the pool; luck margin = exact sign-flip test on daily differences)

| Candidate | Window | Trades | Win % (pool) | Sum % (pool) | Without best day | Without best trade | Losing days (pool) | Worst day (pool) | Keeps top trades | p (return) | p (win %) | Pass? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Curated confirmation, 120 s, 1 family | 23 Oct to 4 Nov | 31 | 58.1 (58.6) | +336 (+872) | +28 | | 3 (3) | -42.3 (-36.3) | | | | no |
| | 5 to 12 Nov | 18 | 61.1 (51.4) | +154 (+142.5) | +78.5 | | 0 (2) | 0.0 (-5.9) | | | | no (window 1, luck) |
| Any-family confirmation, 300 s, 1 family (CONF_W300_K1) | 23 Oct to 4 Nov | 57 | 59.6 (58.6) | +895 (+872) | +363 | +752 | 3 (3) | -36.3 (-36.3) | 6/6 | 0.5 | 0.5 | no (luck) |
| | 5 to 12 Nov | 34 | 52.9 (51.4) | +150 (+142.5) | +49.9 | +75.6 | 1 (2) | -5.9 (-5.9) | 4/4 | 0.5 | 0.5 | no (luck) |
| Vote among the 20 best recent books, 3 families, 300 s | 23 Oct to 4 Nov | 39 | 53.8 (58.6) | +264 (+872) | +26 | | 3 (3) | -33 (-36.3) | 2/6 | 0.9 | 0.4 | no |
| | 5 to 12 Nov | 25 | 64.0 (51.4) | +222 (+142.5) | +70 | +155 | 1 (2) | -9.6 (-5.9) | 2/4 | 0.4 | 0.9 | no |
| Family rotation, last 2 days | 5 to 12 Nov | 204 | 48.5 (51.4) | +496 (+142.5) | +79 | +377 | 2 (2) | -38.7 (-5.9) | 4/4 | 0.3 | 0.4 | no |

CONF_W300_K1 is the only candidate that is never worse than the pool on any test in either window, but it only
drops 1 to 4 trades a window, so the gain is small and well inside luck. It is the safest shadow.

Day by day on 5 to 12 Nov (day %, wins/trades):

| Day | Pool | CONF_W300_K1 | Curated conf. 120 s | Vote top-20 K3 | Family rotation N2 |
|---|---|---|---|---|---|
| 5 Nov | -5.9 (0/1) | -5.9 (0/1) | 0 (0/0) | 0 (0/0) | -1.8 (13/33) |
| 6 Nov | +100.2 (4/4) | +100.2 (4/4) | +76 | +79.5 (3/4) | +89.1 (19/31) |
| 9 Nov | +43.2 (11/22) | +43.2 (11/22) | +62 | +151.9 (13/20) | +416.8 (40/68) |
| 11 Nov | +9.0 (2/4) | +9.0 (2/4) | +7 | 0 (0/0) | +30.3 (20/40) |
| 12 Nov | -4.0 (1/4) | +3.6 (1/3) | +9 | -9.6 (0/1) | -38.7 (7/32) |

On 12 Nov the confirmation filters skip the 10:08 CE that live never armed (-8.7 %), the one the replay took off the
top of the rally (docs/54).

## Ideas

| # | Idea | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|
| I1 | **Shadow Conductor "confirmed"** (CONF_W300_K1, and the curated 120 s version) | A c20 trigger is taken only if an independent family (t28, level trail, spot, edge) has fired the same side in the last 120 to 300 s. Two unrelated detectors agreeing is evidence the move is real; a lone c20 pullback-resumption in a choppy tape is not. | Tested. Never worse than the pool on any test; small gain; not significant (p 0.5). Curated 120 s: 0 losing days on 5 to 12 Nov but loses 26 to 27 Oct wins. | A second Conductor instance in shadow (its own book name, e.g. `conductor_conf`), the pool unchanged, plus a gate that reads the other books' `pending_entry` and recent trades in the same engine step (they are already in `books` at `conductor.py:137`). Score it with the 7 tests from 13 Nov. | Low. It only removes trades. Worst case it misses a big win when the other families are silent (26 Oct). |
| I2 | **Fix the pool's dead weight** | The five books are one signal; c20_9x never trades, c20_9v rarely. Ties are won by c20_9y by in-sample rank. | Tested: single books match or beat the pool (c20_9v alone later +147.5 %, 1 losing day; c20_8x +161.5 %). | Display change first: show on the dashboard which pool book owned each trade and the tie count. Then a shadow Conductor whose tie-break is the forward-scored strike rate (updated nightly from the dated record), not `ret_per_trade` from the discovery days. | Low. Differences are small; do not promote on 5 days. |
| I3 | **"Second family" shadow account (t28 / level trail)** | t28 and level-trail correlate 0.2 with the council and won on 19 Oct, 23 Oct, 4 Nov, 9 Nov, 11 Nov when the council was weak. | Tested negative as a Conductor replacement: every non-council pool chosen on early days lost to the pool on 5 to 12 Nov (best +99 % vs +142.5 %). Untested as a day-type-switched account. | Keep as shadow. Its value is in a day-type switch (see I4), not in rotation by recent results. | Medium if promoted: its worst days are -21 % to -29 %. |
| I4 | **Day-type switch instead of recent-results rotation** | The day decides which family wins (E3). Recent results do not (rank corr 0.16). A switch must read the day as it unfolds: trend efficiency, opening range, VWAP distance (R03, R04). | Untested here (R03's lens). The hindsight ceiling is +2,114 % over 17 days versus +1,092 %. | Phase B: join E3's daily winner family to the 10:30 weather photograph; fit a 3-way classifier (council day / t28-lvl day / stand aside) on the early days only. | High: 17 days is a tiny sample for a classifier. |
| I5 | **Commentary line from the universe** (owner point 4) | The system can say, in first person, "Three independent families agree on puts in the last two minutes; I would take the next c20 put trigger" or "Only the c20 family sees this; I am cautious." This is a stand built on facts already in the engine step. | Display only, untested as profit. | Add to the commentary writer: count of distinct families with a same-side trigger in the last 120 s and 300 s, and which side. | None to trading. |
| I6 | Rejected: best-of-recent, family rotation, static additions, day stops | | Tested; fail window 1 or window 2 (E4). Day stops: every stop chosen on the early days lowered later returns. | Do not build. | |

## Phase B scripts (written, not run; run after 15:30 with the same rules)

* `D:\ApexOptions\data\research\13nov\work\R15\phaseB_meta_of_meta.py`: second-level walk-forward. Each day it picks
  the meta-strategy itself from the 336 variants by its trailing record. Tests whether choosing the chooser helps.
* `D:\ApexOptions\data\research\13nov\work\R15\phaseB_dropped_trades_weather.py`: the pool trades the curated
  confirmation drops and keeps, joined to about 60 weather columns at the trigger; which weather items separate them on
  the early days, and whether the same gaps hold on 5 to 12 Nov.

## Files

Scratch and results in `D:\ApexOptions\data\research\13nov\work\R15\`: `simlib.py` (account rule, validated against
`conductor_sim.json` on all 17 days), `book_day.parquet` and `book_stats.csv` (every book, every day),
`meta_summary_A/B/C.csv` and `meta_days_*.json` (172 meta variants), `promo_tests.csv`, `conf_days.json`,
`curated_vote.csv`, `pool_additions.csv`, `family_account_day.csv`.

Caveats: day returns from `sim_fast` use integer lots; the day-stop test (s7) compounds trade returns without integer
lots, so its "none" row reads +153.8 % on the later days instead of +142.5 %. All books were designed with knowledge
of some early days, so even "walk-forward" selection sits on books that are partly in sample. Five later days are too
few for any luck margin below p = 1/32.
