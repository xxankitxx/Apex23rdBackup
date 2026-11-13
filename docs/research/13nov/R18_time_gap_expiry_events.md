# R18: Time of day, gaps, expiry and events (owner point 2)

Analyst R18, 13 Nov 2026. Scope: when in the day, on which gap days and at which distance from expiry the Conductor and
its five c20 pool books make or lose money, and whether a time-window, gap, opening-range or expiry rule improves the
account walk-forward.

## Findings first

1. **No single time-window rule beats the Conductor out of sample when picked by a fixed procedure.** I tried 56 account
   rules (time windows, skip-a-bucket, opening range, gap, prior-day levels, expiry cut-offs, combinations). A rolling
   walk-forward that picks the best rule on the days so far and trades it on the next day made +176 % (sum of day
   returns) over 11 test days against +215 % for the plain Conductor, strike rate 44 % against 51 %. Time rules are not
   a free lunch on 17 days.
2. **Expiry afternoon is the clearest weak window.** On the 4 expiry days, pool-book trades from 13:30 won 29 % (58
   trades) against 63 % before 13:30 (254 trades); the win rate was lower on all 4 days. 10 of the Conductor's 14
   expiry-afternoon trades lost, mostly by the -14 to -20 % premium stop. Cutting new expiry entries at 13:30 improved
   3 of 4 expiry days and the worst day (-37.1 % to -28.5 %), but cost the 27 Oct 14:36 trade (+79.7 %). The code
   already has this switch (c20_20 "pm") and the pool books do not use it.
3. **Trading against a broken 30-minute opening range is the weakest entry type at trade level**, consistent in every
   book set: pool books 48 % won, mean -0.65 % per trade (90 trades) against 67 % and +12.7 % for the rest; worse on 10
   of 11 days. At account level the veto helped the early days and was slightly negative on the late days, because the
   account then takes a different trade. The c20_20 opening-range lock ("orb") that does this was dropped when c20_8x
   replaced the parts list.
4. **Trades in the direction of an unfilled opening gap are weak**: pool books 50 % won, mean -1.8 % (70 trades) against
   +7.9 % for the rest, worse on 4 of 5 days. Today (13 Nov, live, gap down 82 pts, not filled) the Conductor's 12:36 PE
   was exactly this case and lost 7.1 %.
5. **The first 30 minutes are the best window and the account is mostly absent from it.** Pool trades before 09:45 won
   74 % (54 trades, mean +11.6 %); the Conductor won 73 % of 11 such trades. The normal-day core needs 20 minutes of
   forward history (c20_08.py:41, W=1200 s), so normal-day entries cannot start before about 09:36.
6. **Opening-drive and last-half-hour momentum families fail walk-forward.** Every variant flipped sign between the
   early and late days. All 107 books lose after 15:00 on normal days (378 trades, 38 % won, mean -0.84 %). The pool
   books already stop new normal-day entries at 15:00. Keep it that way.
7. **Two data defects in this area.** (a) The event calendar holds only two future RBI dates (config.py:521-524), so
   `wx_event` was False for every one of the 20,817 trades: it carries no information. (b) 9 Nov is missing from
   `data/learning/day_levels.json`; `load_prior` (daystate.py:121-133) and c20_8x `_prior` (c20_8x.py:34-40) silently
   use 6 Nov instead, so on 11 Nov the prior-day high and low (to_pdh / to_pdl, and c20_9v's level booking) were wrong
   by up to about 340 points.

## Teardown

### What the code does in my area

| Item | Where | What it does |
|---|---|---|
| Engine entry window | config.py:91, 96, 97; paper.py:1063; engine_main.py:749 | No entry before 09:25 (SUPPRESS_UNTIL) or at/after 15:15 (LAST_ENTRY); flat at 15:25. |
| Expiry clock | config.py:103-104; paper.py:195, 261 | Expiry day: no entry from 14:45, flat by 15:00. |
| Expiry entry end | config.py:72 | `EXPIRY_ENTRY_END = None`: off. |
| Core windows of the pool books | c20_08.py:21-42, 129 | Expiry mode (EXP): 09:16 to 14:40. Normal mode (NORM): 09:16 to 15:00, but the 40-pt impulse needs W=1200 s of smoothed forward, so the first normal-day signal is about 09:36. |
| Opening-range lock (normal days) | c20_20.py:29-30, 115-124, 164 | "orb": after the forward breaks its 09:15-09:45 range by 5 pts, only that side. In DEFAULT_PARTS of c20_20. |
| Expiry afternoon cut | c20_20.py:18, 38, 162 | "pm": no expiry entry from 13:30. Never in any default. |
| Expiry opening-range lock | c20_8x.py:28, 222, 236-243 | "orbx": 09:16-09:31 range lock on expiry days. Not in FINAL. |
| Parts actually used by the pool | c20_8x.py:47-52, 295; c20_9x.py:69 | c20_8x passes `FINAL = (exp, norm, seq, pex, pbg, d52)` to c20_20, which REPLACES c20_20's default parts. So "orb" and "iv" from c20_20, and "pm", "orbx" are off in c20_9x, 9y, 9s, 9v and 9t. |
| Weather calendar items | weather.py:604-615, 676-701 | mins_open, dte, expiry_day, day_before_expiry, after_break, event, hrs_to_expiry, mins_to_flat, phase_bucket. |
| Gap and opening range items | weather.py:703-718 | gap_pts = first trusted print (within 600 s of open) minus prior close, signed by trade direction; gap_filled = day low (high) has touched the prior close; or15_pos / or30_pos = spot in the opening range (0 low, 1 high, outside = broken); to_pdh / to_pdl / to_pdc. |

### Where it fails

1. **The opening-range lock and the expiry afternoon cut were lost by inheritance, not by a decision on the account.**
   c20_20.py:30 says "orb" was chosen by ablation; c20_8x.py:48 then sets the parts to FINAL, which leaves it out. The
   pool books therefore fade a broken opening range freely (finding 3).
2. **`wx_event` is dead.** config.py:521-524 lists 2026-12-04 and 2027-02-05 only. Nothing in the 17 days could be
   marked, and weekly expiry, monthly expiry, US data nights and index rebalances are not events in the code.
3. **Silent stale prior-day levels.** daystate.py:132 takes the latest saved day before today with no check that it is
   the previous trading day. 9 Nov never got saved (the 9 Nov freeze is the likely cause), so 11 Nov ran on 6 Nov's
   high and low. The gap itself was nearly unaffected (the 9 Nov close, estimated from the futures less the 6 Nov basis,
   was about 24,920, close to 6 Nov's 24,932.7). c20_8x.py:34-40 has the same fallback for the "lvl" booking in c20_9v.
4. **`phase_bucket` does not match the entry clock on expiry days** (weather.py:700). "last_hour" starts at 14:30 but
   expiry entries stop at 14:40 (core) / 14:45 (engine), so the bucket holds 10-15 minutes there. Minor, but any rule
   on "last_hour" means two different things on the two day types.
5. **`gap_filled` is "ever touched"**, not "back across now". After a fill the price can be far back in the gap
   direction and the flag stays True. That is why the unfilled variant separates better than the filled one.
6. **Day-level fields carry 17 distinct values.** gap, dte and day_before_expiry are constant within a day, so any rule
   on them is a rule on 4 to 7 days, whatever the trade count says.

## Evidence

Data: `trades_all_books.parquet` (20,817 trades, 107 books, 17 days) and the Conductor's 119 replayed trades
(p44_sim, with p44_simr for 28 Oct, 30 Oct, 2 Nov, 3 Nov). My account simulator (`work/R18/sim.py`, the rule of
apex/conductor/account_sim.py) reproduces the Conductor exactly: 119 trades, every day to 0.1 %. Returns are in
percent per day, compounding inside the day from 1 lakh, as the account runs. "Sum" is the sum of day returns.
Early (discovery) = 19 Oct to 4 Nov (12 days); late (test) = 5 Nov to 12 Nov (5 days).

### Conductor trades by time bucket (119 trades)

| Bucket | Trades | Days | Won | Mean % | Median % |
|---|---|---|---|---|---|
| 09:15-09:45 | 11 | 7 | 73 % | +14.0 | +3.6 |
| 09:45-11:00 | 28 | 12 | 46 % | +4.8 | -1.2 |
| 11:00-13:00 | 42 | 14 | 55 % | +6.2 | +1.3 |
| 13:00-14:30 | 31 | 14 | 52 % | +6.5 | +0.6 |
| 14:30-15:15 | 7 | 7 | 43 % | +7.5 | -1.7 |

Pool books (543 trades) show the same shape: 74 % / 51 % / 58 % / 58 % / 54 % won. All 107 books: 52 % / 47 % / 48 % /
46 % / 46 %. First 30 minutes against the rest: Conductor 73 % vs 51 %, pool 74 % vs 56 %, all books 52 % vs 47 %.

### By gap, opening range, prior-day level and expiry (Conductor; pool in brackets)

| Group | Trades | Won | Mean % |
|---|---|---|---|
| Flat gap (<30 pts), 6 days | 49 (225) | 55 % (59 %) | +9.3 (+9.8) |
| Gap 30-150, 7 days | 48 (221) | 50 % (56 %) | +6.9 (+6.5) |
| Gap >150, 4 days | 22 (97) | 55 % (59 %) | +0.7 (+1.0) |
| Trade against the gap | 38 (176) | 55 % (61 %) | +9.5 (+8.4) |
| Trade with the gap | 32 (142) | 47 % (51 %) | -0.4 (+0.3) |
| OR30 broken against the trade | 24 (90) | 42 % (48 %) | -1.9 (-0.7) |
| OR30 broken with the trade | 27 (123) | 48 % (56 %) | +7.8 (+7.7) |
| Inside OR30 | 57 (276) | 56 % (59 %) | +8.5 (+8.0) |
| Already beyond PDH (CE) / PDL (PE) | 22 (107) | 45 % (55 %) | +2.4 (+2.6) |
| 50-150 pts short of the level | 25 (114) | 60 % (65 %) | +13.6 (+13.1) |
| Expiry day (dte 0), 4 days | 66 (312) | 55 % (56 %) | +5.0 (+5.1) |
| Day before expiry, 3 days | 14 (56) | 93 % (93 %) | +21.5 (+23.0) |
| dte 5-6, 7 days | 30 (133) | 43 % (52 %) | +4.7 (+5.1) |

`wx_event` was False on every trade (finding 7a), so there is no event result to report.

### Per-day paired tests (same day, flagged trades against the rest)

| Flag | Pool books: days flag worse / days | Pool won (flag vs rest) | All 107: days worse |
|---|---|---|---|
| OR30 broken against | 10 / 11 (early 8/9, late 2/2) | 48 % vs 67 % | 10 / 16 |
| OR15 broken against | 11 / 13 | 50 % vs 63 % | 11 / 16 |
| With gap >= 30 | 7 / 9 | 51 % vs 61 % | 8 / 11 |
| With gap, unfilled | 4 / 5 | 50 % vs 58 % | 8 / 10 |
| Expiry, from 13:30 | 3 / 4 (win lower on 4/4) | 29 % vs 63 % | 2 / 4 |
| 09:45-11:00 | 9 / 11 | 52 % vs 60 % | 9 / 17 |
| From 14:30 | 4 / 5 | 55 % vs 57 % | 13 / 17 |
| Beyond PDH/PDL | 6 / 10 | 55 % vs 50 % | 8 / 15 |

Expiry days, pool books, from 13:30, per day: 19 Oct 0 of 9 won (mean -14.9 %), 27 Oct 10 of 16 (+25.2 %), 3 Nov 2 of
13 (-12.9 %), 9 Nov 5 of 20 (-7.9 %). By half hour on expiry days the pool won 40 % at 13:30, 5 % at 14:00 (74 % of
those trades hit the premium stop) and 43 % at 14:30.

### Account walk-forward (56 rules; selected rows)

| Rule | Early trades / won / sum / losing days / worst / sum without best day | Late trades / won / sum / losing days / worst / without best day |
|---|---|---|
| Conductor as is | 84 / 53.6 % / +987 / 3 / -37.1 / +445 | 35 / 51.4 % / +154 / 2 / -6.0 / +45 |
| Expiry: no entry from 13:30 | 75 / 56.0 % / +759 / 3 / -28.5 / +481 | 30 / 56.7 % / +246 / 2 / -6.0 / +110 |
| Expiry: no entry from 14:00 | 78 / 55.1 % / +748 / 3 / -28.5 / +470 | 32 / 56.2 % / +251 / 2 / -6.0 / +110 |
| Veto OR30 broken against | 64 / 59.4 % / +867 / 2 / -28.5 / +482 | 32 / 50.0 % / +142 / 2 / -6.0 / +54 |
| Veto with-gap unfilled (>= 30) | 73 / 52.1 % / +1008 / 3 / -41.8 / +466 | 31 / 58.1 % / +179 / 1 / -6.0 / +70 |
| Veto with-gap (>= 30) | 69 / 53.6 % / +1047 / 3 / -41.8 / +506 | 18 / 61.1 % / +146 / 1 / -6.0 / +58 |
| Skip 09:45-11:00 | 66 / 54.5 % / +578 / 3 / -34.2 / +251 | 25 / 56.0 % / +168 / 0 / 0.0 / +87 |
| Window 10:30-14:00 only | 52 / 51.9 % / +356 / 6 / -28.5 / +165 | 20 / 70.0 % / +243 / 0 / 0.0 / +49 |
| Big-gap days (>150) off | 67 / 52.2 % / +982 / 2 / -28.5 / +440 | 30 / 53.3 % / +148 / 1 / -4.8 / +39 |
| Veto beyond PDH/PDL | 65 / 56.9 % / +1018 / 3 / -41.8 / +476 | 32 / 50.0 % / +66 / 2 / -6.0 / +22 |
| OR30 + with-gap + PDH/PDL | 44 / 68.2 % / +922 / 1 / -11.7 / +537 | 16 / 56.2 % / +58 / 1 / -6.0 / +26 |

All 56 rows: `data/research/13nov/work/R18/wf_rules.csv`. The rule that looks best on the early days by the owner's
standard (the three-way combination: 68 % won, 1 losing day, worst -11.7 %) lost most of its return on the late days.
The rules that look best on the late days (10:30-14:00 window, skip 09:45-11:00) are the worst on the early days.

Rolling walk-forward (pick, on all days so far, the rule with the highest sum among those with strike rate, sum without
best day and worst day no worse than the Conductor; trade it on the next day; 11 test days, 28 Oct to 12 Nov): base
+215 %, chosen +176 %; strike rate 50.7 % vs 44.4 %; losing days 5 vs 5. File: `work/R18/rolling_wf.csv`.

### Two best candidates over all 17 days (in sample for the choice, so not proof)

| | Conductor | Expiry cut 13:30 | Expiry cut 13:30 + with-gap-unfilled veto |
|---|---|---|---|
| Trades | 119 | 105 | 91 |
| Won | 52.9 % | 56.2 % | 58.2 % |
| Sum of day % | +1141 | +1004 | +1058 |
| Losing days | 5 | 5 | 4 |
| Worst day | -37.1 % | -28.5 % | -28.5 % |
| Without best trade | +961 | +824 | +878 |
| Without best day | +599 | +727 | +780 |

Per expiry day, cut at 13:30: 19 Oct +22.8 to +70.3 %; 27 Oct +541.9 to +231.5 %; 3 Nov -37.1 to -2.6 %; 9 Nov +43.4 to
+135.5 %. It passes strike rate, worst day and "without best day" in both windows; it fails return in the early window
(27 Oct) and "keeps the top trades" (it loses the 27 Oct 14:36 trade, +79.7 %).

### Opening-drive and last-half-hour families (16 variants, all 107 books as one account)

| Family | Early trades won / mean | Late trades won / mean | Verdict |
|---|---|---|---|
| Any trade before 09:45 | 55 % / +3.5 % | 43 % / -0.8 % | flips |
| Before 09:45, 5-min move with | 53 % / +1.8 % | 42 % / -0.8 % | flips |
| Before 09:45, OR15 broken with | 23 % / -2.5 % | 51 % / +0.6 % | flips |
| Before 09:45, against gap, day move with | 60 % / +9.9 % | 37 % / -1.9 % | flips |
| 14:45-15:15, day move with | 37 % / -1.2 % | 52 % / +1.5 % | flips |
| 14:45-15:15, OR30 broken with | 30 % / -1.8 % | 52 % / +1.6 % | flips |
| 14:45-15:15, all | 39 % / -1.3 % | 41 % / +0.3 % | weak both |

File: `work/R18/wf_family.csv`. Nothing here is worth a book.

### Today, 13 Nov (live, out of sample, partial)

Gap down 82 pts, not filled, dte 4. 10:53 CE (against gap, OR30 broken with): -12.4 %. 12:36 PE (with the unfilled gap,
spot already below PDL): -7.1 %; the with-gap-unfilled veto and the beyond-PDL veto would both have blocked it. 14:29
PE (with the unfilled gap) was still open when I read the log. One day; anecdote only.

### Multiple testing

Variants tried: 56 account rules, 16 family variants (3 returned no trades), 2 extra combinations, and the rolling
selection over the 56: about 74 distinct variants on 17 days, with 4 expiry days and 4 big-gap days. With that many tries
a difference of 50-100 % in the sum of day returns is noise. Only effects that are consistent per day in all three book
sets (OR30 against, expiry afternoon, with-gap unfilled) are worth a shadow book.

## Ideas

| # | Idea | Kind | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|---|
| 1 | Expiry afternoon cut at 13:30 | guard | 0-DTE theta and gamma after 13:30 make the 25-pt trail and 15 % stop a coin flip against decay; the pool's own trades won 29 % there | Walk-forward mixed: late +246 vs +154, 56.7 % vs 51.4 % won, early return -23 %; 4 expiry days | Shadow pool rule "dte==0 and time>=13:30: no entry", or a twin `c20_9y_pm` with parts FINAL_R9 + ("pm",) (c20_20.py:162 already codes it) | Loses rare big expiry afternoon runs (27 Oct +79.7 %). 4 days of evidence. |
| 2 | Opening-range direction veto (restore "orb") | guard | Fading a broken 09:15-09:45 range fights the day's order flow | Trade level strong (10 of 11 days); account early +win, late -8 % return | Shadow twin with FINAL_R9 + ("orb",) so the BOOK skips the fade (the book then keeps its own state, which a Conductor rule cannot) | Account substitution can erase the gain; must be judged on the twin's own book, then on the account. |
| 3 | With-gap-unfilled veto | guard | An unfilled gap means the overnight move is still being digested; chasing it buys at the extended side | Late +179 vs +154, 58 % vs 51 % won, 1 losing day vs 2; early worst day worse (-41.8 vs -37.1); rolling selection did not pick it | Shadow pool rule on wx_gap_pts > 30 and wx_gap_filled == False | 3 Nov (gap up 244 on expiry) the vetoed CE trades were mostly winners. |
| 4 | Time-of-day line in the forecaster and commentary | ui / commentary | The owner wants a stand, not a range. The system knows its own record per window | Untested (display) | Add one line to the Forecast panel and the Conductor commentary from a small table refreshed nightly: "It is expiry afternoon. My books won 29 % of 58 trades here. I would not buy now." / "First half hour: my books won 74 %. I am ready to take a clean pullback." | The table must be refreshed walk-forward each night, never fitted on today. |
| 5 | Prior-day levels with a staleness check | reliability / data | daystate.load_prior and c20_8x._prior take any older day silently | Defect confirmed (9 Nov missing; 11 Nov used 6 Nov) | Return the prior day's date with the levels; add `prior_day_ok` to the photo; when the saved day is not the previous trading day, rebuild H/L/C from the tick tape or leave the level fields None; alert in the log | None; a fix |
| 6 | A real event calendar | data | `wx_event` cannot help with an empty calendar | Untested; nothing to test on | Add RBI, Budget, US CPI and FOMC nights, monthly expiry, MSCI/FTSE rebalances to config.EVENT_DAYS, owner-maintained | Few days per year, so it will stay a display item for months |
| 7 | Earlier first normal-day entry | entry | Pool trades before 09:45 won 74 %; NORM cannot fire before about 09:36 (W=1200 s) | Untested | Replay twin with a 10-minute warm-up on the morning only (W=600 until 09:45). Needs a replay after the close with the owner's OK | More false impulses from the opening auction noise |
| 8 | Do not extend entries past 15:00 on normal days | guard (keep) | All 107 books lose after 15:00 (38 % won, mean -0.84 %) | Consistent in both windows | Nothing to build; keep NORM t1=15:00 (c20_08.py:41) even though LAST_ENTRY is 15:15 | None |
| 9 | Do not build opening-drive or last-half-hour momentum books | other | Every variant flipped sign between windows | Tested, failed | None | None |

Shadow-book plan for ideas 1 to 3: three pool-rule shadows scored by the official standard from 16 Nov, plus the two
twins (`c20_9y_pm`, `c20_9y_orb`) as books. Do not change the live Conductor on this evidence.

## Phase B scripts

* `D:\ApexOptions\data\research\13nov\work\R18\phaseB_tod_baseline.py` (ready, run after 15:30, about 35 s per day
  part, about 10 minutes for all 17 parts, one process). A book-independent time-of-day map from ds_v2: buying the
  nearest-the-money CE and PE every minute and selling 10 or 20 minutes later at the bid, by half hour and day type,
  momentum side against fade side; the follow-through of the first OR30 break (+5 to +60 minutes, worst adverse); gap
  size, fill time and the 09:15-09:45 move in the gap direction. Validated on 6 and 9 Nov only (it runs; the numbers
  on two days are not evidence). It answers whether the expiry-afternoon weakness belongs to the market (decay) or to
  the c20 entry.
* Not written as a script (needs a replay, which only the owner may start): twins `c20_9y_pm` and `c20_9y_orb`, and the
  morning warm-up twin of idea 7, on all 17 days plus 13 Nov.

## Scratch files

`D:\ApexOptions\data\research\13nov\work\R18\`: sim.py (account simulator, exact match), a4_out.txt (bucket tables),
wf_rules.csv, wf_family.csv, rolling_wf.csv, a1 to a10 scripts.
