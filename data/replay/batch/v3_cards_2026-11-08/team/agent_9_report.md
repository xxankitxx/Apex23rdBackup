# Agent 9 — rule search report (8 Nov 2026)

Books: edge_bracket_only, edge_breakout, edge_gate_only, edge_gate_trail, premium_momentum, straddle_spike.
Data: 14 replayed days 19 Oct – 6 Nov 2026; discovery = first 10 days, holdout = last 4 (`rule_lab.split_days`).
Score searched = share of discovery losers removed minus share of discovery winners removed (rule_lab.score_masks),
min 20 kept. Shuffle test: the SAME search re-run on 200 shufflings of the discovery outcomes (seed 7).
Searches run per book (each with its own shuffle test, so each has its own luck bar):

* `single/SMALL`: best single clause, 30 prior-chosen features, 5 quantile lines (10..90 %), both directions, min 20 kept
* `pair/SMALL`: best 2-clause AND over the 30 prior-chosen features, 5 lines each, different fields, min 20 kept
* `triple/SMALL`: best 2-clause AND over the 30 prior-chosen features, then the best third clause added to each of the top 40 pairs
* `or/SMALL`: best 2-clause OR (keep if either holds) over the 30 prior-chosen features, 5 lines
* `single/FULL`: best single clause over ALL numeric weather fields + derived features + text indicators (~300 features), 5 lines
* `pair/FULL`: best 2-clause AND over ~300 features x 5 lines x 2 directions (~3000 masks), different fields, min 20 kept
* `triple/FULL`: best 2-clause AND over ~300 features, then best third clause on each of the top 40 pairs
* `or/FULL`: best 2-clause OR over ~300 features, 5 lines
* `single/FULL/3lines`: best single clause over ~300 features, 3 quantile lines (10/50/90 %)
* `pair/FULL/3lines`: best 2-clause AND over ~300 features, 3 quantile lines

Derived features added to every search (`lab9.py`): ratios (mv60/rv15, premium/theta_be15, mv30/speed15, ...),
products (gamma*mv30, vega*vix_chg15, mv60*(breadth-0.5)), differences (er_day-er30, mv60-mv300, swing_ahead-swing_behind),
direction interactions (kv, kvt, cusum, order-flow and book-imbalance fields times +1 CE / -1 PE, is_ce), within-day
z-scores from the book's earlier trades that day (premium, speed15, mv60, theta_ratio, iv_vs_med, spread_pct), hour of day,
mean return of the book's earlier trades today. Fitted-model fields (hmm_*, hk_*) excluded.

Honesty notes. (1) Each search's p is for THAT search; I ran 10 searches per book, so across a book the chance that the
best of ten reaches p ~ 0.03-0.05 by luck alone is roughly 25-40 %. (2) For each book the card below is the rule with the
best DISCOVERY score among all searches (what one would have frozen before looking at holdout), not the rule that did
best on holdout. (3) The single passing rule (edge_breakout) was re-shuffled a second time with a different seed and
400 shufflings (s4_check.py, log_check.txt): p = 0.0175, pooled 16/600 = 0.027. (4) The three small books (33-38
discovery trades, 8 holdout) cannot support a rule: with min 20 kept there are at most 13-18 trades to remove, and the
shuffled labels match the real score 20-97 % of the time. (5) Holdout numbers are reported for every search, including
the ones that fail; none was run more than once.


## edge_bracket_only

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 80 | 34 | 46 | 42% | +1.5 | +67,840 |
| holdout | 24 | 7 | 17 | 29% | -2.9 | -30,566 |
| all | 104 | 41 | 63 | 39% | +0.5 | +37,274 |

**Verdict: NONE**  (0 of 10 searches passed all of 2-4)

Best rule found (search `triple/FULL`, 298 features; combine = AND):

### edge_bracket_only: `agree_same >= 5 AND fut_spread >= 2.6 AND hrs_to_expiry < 146`

Shuffle test p = 0.285 (does NOT beat luck). shuffle median best score 0.561, max 0.701; real 0.583.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 80 | 42% | +1.5 | +67,840 | 46 |
| discovery | kept | 32 | 78% | +10.7 | +328,185 | 7 |
| discovery | removed | 48 | 19% | -4.6 | -260,344 | 39 |
| holdout | book | 24 | 29% | -2.9 | -30,566 | 17 |
| holdout | kept | 14 | 29% | -3.8 | -26,523 | 10 |
| holdout | removed | 10 | 30% | -1.7 | -4,043 | 7 |
| all | book | 104 | 39% | +0.5 | +37,274 | 63 |
| all | kept | 46 | 63% | +6.3 | +301,662 | 17 |
| all | removed | 58 | 21% | -4.1 | -264,388 | 46 |

Features used: `agree_same` = weather field as recorded at the trigger second; `fut_spread` = weather field as recorded at the trigger second; `hrs_to_expiry` = weather field as recorded at the trigger second

Passes: discovery True, shuffle False, holdout False. shuffle p=0.285; holdout: kept win% below book or removed side profitable

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `speed15 >= 6.362` | 0.262 | 0.530 | 35 / 57% / 15 / +146,903 | 45 / 31 / -79,063 | 8 / 50% / 4 / +15,324 | 29% | 16 / -45,890 | Y / n / Y |
| pair/SMALL | `premium >= 107.3 AND vix_chg15 >= -0.005` | 0.400 | 0.240 | 31 / 68% / 10 / +246,769 | 49 / 36 / -178,929 | 7 / 57% / 3 / +13,637 | 29% | 17 / -44,203 | Y / n / Y |
| triple/SMALL | `premium >= 107.3 AND vix_chg15 >= -0.005 AND mean_ret_today < 15.53` | 0.436 | 0.380 | 27 / 74% / 7 / +265,002 | 53 / 39 / -197,161 | 7 / 57% / 3 / +13,637 | 29% | 17 / -44,203 | Y / n / Y |
| or/SMALL | `speed15 >= 6.362 OR rv15_spot >= 12.12` | 0.373 | 0.410 | 44 / 59% / 18 / +239,986 | 36 / 28 / -172,146 | 9 / 44% / 5 / +5,678 | 29% | 15 / -36,244 | Y / n / Y |
| single/FULL | `fut_spread >= 2.6` | 0.347 | 0.505 | 57 / 54% / 26 / +201,282 | 23 / 20 / -133,442 | 16 / 31% / 11 / -13,754 | 29% | 8 / -16,812 | Y / n / Y |
| pair/FULL | `agree_same >= 5 AND fut_spread >= 2.6` | 0.526 | 0.120 | 37 / 70% / 11 / +305,870 | 43 / 35 / -238,030 | 14 / 29% / 10 / -26,523 | 29% | 10 / -4,043 | Y / n / n |
| triple/FULL | `agree_same >= 5 AND fut_spread >= 2.6 AND hrs_to_expiry < 146` | 0.583 | 0.285 | 32 / 78% / 7 / +328,185 | 48 / 39 / -260,344 | 14 / 29% / 10 / -26,523 | 29% | 10 / -4,043 | Y / n / n |
| or/FULL | `chain_age >= 65 OR dist_hi < 54.8` | 0.446 | 0.790 | 43 / 63% / 16 / +224,448 | 37 / 30 / -156,608 | 21 / 24% / 16 / -46,589 | 29% | 3 / +16,022 | Y / n / n |
| single/FULL/3lines | `gex_wall_ahead >= 58.55` | 0.307 | 0.800 | 40 / 57% / 17 / +195,448 | 40 / 29 / -127,608 | 8 / 50% / 4 / +19,198 | 29% | 16 / -49,764 | Y / n / Y |
| pair/FULL/3lines | `fut_spread >= 1.27 AND ret_today < 10.69` | 0.437 | 0.530 | 34 / 68% / 11 / +262,431 | 46 / 35 / -194,590 | 17 / 29% / 12 / -38,844 | 29% | 7 / +8,278 | Y / n / n |

Reading: 80 discovery trades, 42 % winners, the holdout 4 days are bad for the book (29 %, -30,566 Rs). Every search finds a rule that looks good on discovery (the pair `agree_same >= 5 AND fut_spread >= 2.6` keeps 37 with 70 % winners) but none beats luck: p ranges 0.12-0.80; the shuffled labels produce rules just as good. The two FULL pair/triple rules with the lowest p also fail holdout outright (kept 29 %, -26,523 Rs, the same as the book). The SMALL-set rules that keep their holdout win rate (premium >= 107 AND vix_chg15 >= 0, 57 % on 7 kept) are p = 0.24-0.38 and keep only 7 holdout trades. Nothing here honestly removes this book's losers; the best honest statement is that higher-speed / larger-premium entries did better on both windows, with too little evidence to be a rule.


## edge_breakout

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 63 | 26 | 37 | 41% | +0.7 | +14,024 |
| holdout | 18 | 5 | 13 | 28% | -3.5 | -64,682 |
| all | 81 | 31 | 50 | 38% | -0.3 | -50,658 |

**Verdict: PROPOSE**  (1 of 10 searches passed all of 2-4)

Best rule found (search `triple/FULL`, 294 features; combine = AND):

### edge_breakout: `gaps_today < 6 AND vomma >= 0.00696 AND vix_chg30 < 0.608`

Shuffle test p = 0.045 (beats luck). shuffle median best score 0.624, max 0.742; real 0.722.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 63 | 41% | +0.7 | +14,024 | 37 |
| discovery | kept | 29 | 79% | +9.9 | +266,572 | 6 |
| discovery | removed | 34 | 9% | -7.3 | -252,548 | 31 |
| holdout | book | 18 | 28% | -3.5 | -64,682 | 13 |
| holdout | kept | 7 | 43% | +0.4 | -2,298 | 4 |
| holdout | removed | 11 | 18% | -5.9 | -62,384 | 9 |
| all | book | 81 | 38% | -0.3 | -50,658 | 50 |
| all | kept | 36 | 72% | +8.1 | +264,274 | 10 |
| all | removed | 45 | 11% | -6.9 | -314,932 | 40 |

Features used: `gaps_today` = weather field as recorded at the trigger second; `vomma` = weather field as recorded at the trigger second; `vix_chg30` = weather field as recorded at the trigger second

Passes: discovery True, shuffle True, holdout True. all three met.

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `abs_delta >= 0.5386` | 0.252 | 0.835 | 44 / 50% / 22 / +113,490 | 19 / 15 / -99,466 | 12 / 42% / 7 / -4,719 | 28% | 6 / -59,962 | Y / n / Y |
| pair/SMALL | `abs_delta >= 0.5386 AND n_today < 5.4` | 0.433 | 0.450 | 30 / 63% / 11 / +177,541 | 33 / 26 / -163,517 | 12 / 42% / 7 / -4,719 | 28% | 6 / -59,962 | Y / n / Y |
| triple/SMALL | `abs_delta >= 0.5386 AND n_today < 5.4 AND wmove60 < 13.19` | 0.515 | 0.290 | 27 / 70% / 8 / +207,015 | 36 / 29 / -192,992 | 11 / 36% / 7 / -20,849 | 28% | 7 / -43,833 | Y / n / Y |
| or/SMALL | `breadth_dir < 0.5932 OR vix < 16.23` | 0.375 | 0.825 | 37 / 57% / 16 / +114,013 | 26 / 21 / -99,990 | 14 / 36% / 9 / -25,230 | 28% | 4 / -39,452 | Y / n / Y |
| single/FULL | `gaps_today < 5` | 0.387 | 0.405 | 39 / 56% / 17 / +133,741 | 24 / 20 / -119,717 | 13 / 31% / 9 / -36,888 | 28% | 5 / -27,794 | Y / n / Y |
| pair/FULL | `gaps_today < 5 AND oi_own_chg5 < 1.408e+05` | 0.596 | 0.115 | 24 / 79% / 5 / +236,750 | 39 / 32 / -222,726 | 8 / 38% / 5 / -11,642 | 28% | 10 / -53,040 | Y / n / Y |
| triple/FULL | `gaps_today < 6 AND vomma >= 0.00696 AND vix_chg30 < 0.608` | 0.722 | 0.045 | 29 / 79% / 6 / +266,572 | 34 / 31 / -252,548 | 7 / 43% / 4 / -2,298 | 28% | 11 / -62,384 | Y / Y / Y |
| or/FULL | `jump_z < -0.16 OR vix_chg30 < -0.06` | 0.530 | 0.565 | 24 / 75% / 6 / +180,736 | 39 / 31 / -166,712 | 5 / 40% / 3 / -9,688 | 28% | 13 / -54,993 | Y / n / Y |
| single/FULL/3lines | `gaps_today < 6` | 0.286 | 0.960 | 50 / 50% / 25 / +95,267 | 13 / 12 / -81,244 | 15 / 27% / 11 / -52,630 | 28% | 3 / -12,051 | Y / n / n |
| pair/FULL/3lines | `gaps_today < 6 AND prem_ratio_with >= 1.002` | 0.492 | 0.535 | 23 / 74% / 6 / +186,404 | 40 / 31 / -172,380 | 9 / 33% / 6 / -19,045 | 28% | 9 / -45,636 | Y / n / Y |

Reading: 63 discovery trades, 41 % winners; holdout 28 %, -64,682 Rs. One rule passes all of 2-4 on the letter of the standard: `gaps_today < 6 AND vomma >= 0.00696 AND vix_chg30 < 0.608` (triple/FULL): discovery 29 kept, 79 % winners, +266,572 Rs, 6 losers; removed 34 with 31 losers; shuffle p = 0.045 (9 of 200 shufflings, seed 7); a second independent run of the same search with seed 11 and 400 shufflings gave p = 0.0175 (7 of 400), so the pooled estimate is 16/600 = 0.027 -- it does beat luck for its own search; holdout 7 kept, 43 % (book 28 %), -2,298 Rs, 4 losers, removed 11 trades -62,384 Rs. Why it must be read with suspicion: (a) p = 0.045 is at the bar, and it is the best of 10 searches on this book, so across the 10 searches on this book the chance that at least one reaches p ~ 0.03 by luck is roughly 25 %; (b) the kept side on holdout still loses money (3 winners, 4 losers); (c) `gaps_today` is the count of feed gaps so far today -- a feed-health / time-of-day proxy, not a market fact, and the clause alone does nothing on holdout (27 % kept); the lift on holdout comes from `vomma >= 0.007 AND vix_chg30 < 0.6` (8 kept, 50 %, +3,201 Rs), which did NOT itself pass the shuffle test when searched as a pair. Verdict on the letter: PROPOSE (marginal). My reading: a candidate to watch in the shadow book, not a rule to trust; it does not remove the losers, it removes a slice of them and keeps 7 of 18 holdout trades.


## edge_gate_only

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 33 | 21 | 12 | 64% | +4.8 | +192,205 |
| holdout | 8 | 4 | 4 | 50% | -2.5 | -22,812 |
| all | 41 | 25 | 16 | 61% | +3.3 | +169,393 |

**Verdict: NONE**  (0 of 10 searches passed all of 2-4)

Best rule found (search `triple/FULL`, 275 features; combine = AND):

### edge_gate_only: `e_iv_atm >= 14.02 AND fmv300 >= -52.08 AND gamma >= 0.000886`

Shuffle test p = 0.255 (does NOT beat luck). shuffle median best score 0.821, max 1.000; real 0.869.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 33 | 64% | +4.8 | +192,205 | 12 |
| discovery | kept | 21 | 95% | +14.1 | +321,708 | 1 |
| discovery | removed | 12 | 8% | -11.6 | -129,503 | 11 |
| holdout | book | 8 | 50% | -2.5 | -22,812 | 4 |
| holdout | kept | 6 | 33% | -9.6 | -52,169 | 4 |
| holdout | removed | 2 | 100% | +19.1 | +29,357 | 0 |
| all | book | 41 | 61% | +3.3 | +169,393 | 16 |
| all | kept | 27 | 81% | +8.8 | +269,539 | 5 |
| all | removed | 14 | 21% | -7.2 | -100,146 | 11 |

Features used: `e_iv_atm` = weather field as recorded at the trigger second; `fmv300` = weather field as recorded at the trigger second; `gamma` = weather field as recorded at the trigger second

Passes: discovery True, shuffle False, holdout False. shuffle p=0.255; holdout: kept win% below book or removed side profitable

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `premium < 196.4` | 0.310 | 0.950 | 23 / 74% / 6 / +209,560 | 10 / 6 / -17,355 | 6 / 50% / 3 / -22,298 | 50% | 2 / -514 | Y / n / Y |
| pair/SMALL | `mv300 >= -47.87 AND vwap_ext >= 2.6` | 0.476 | 0.780 | 21 / 81% / 4 / +212,859 | 12 / 8 / -20,654 | 4 / 75% / 1 / +6,146 | 50% | 4 / -28,958 | Y / n / Y |
| triple/SMALL | `iv_vs_med >= -0.872 AND mean_ret_today >= 0 AND mv300 >= -47.87` | 0.560 | 0.695 | 20 / 85% / 3 / +263,429 | 13 / 9 / -71,224 | 4 / 50% / 2 / -3,270 | 50% | 4 / -19,542 | Y / n / Y |
| or/SMALL | `mv60_over_rv15 >= -1.005 OR gamma_x_mv30 < -0.01204` | 0.571 | 0.470 | 23 / 83% / 4 / +268,921 | 10 / 8 / -76,716 | 4 / 25% / 3 / -47,294 | 50% | 4 / +24,482 | Y / n / n |
| single/FULL | `fut_spread >= 2.84` | 0.440 | 0.975 | 23 / 78% / 5 / +225,452 | 10 / 7 / -33,248 | 5 / 40% / 3 / -36,429 | 50% | 3 / +13,618 | Y / n / n |
| pair/FULL | `e_fut_tot_imb_dir < 0.0164 AND oi_own_chg5 < -2.664e+04` | 0.690 | 0.785 | 20 / 90% / 2 / +252,645 | 13 / 10 / -60,440 | 0 /  / 0 / +0 | 50% | 8 / -22,812 | Y / n / n |
| triple/FULL | `e_iv_atm >= 14.02 AND fmv300 >= -52.08 AND gamma >= 0.000886` | 0.869 | 0.255 | 21 / 95% / 1 / +321,708 | 12 / 11 / -129,503 | 6 / 33% / 4 / -52,169 | 50% | 2 / +29,357 | Y / n / n |
| or/FULL | `lo_age_min < 15.26 OR oi_net_help5 >= 8.386e+05` | 0.786 | 0.195 | 22 / 91% / 2 / +280,049 | 11 / 10 / -87,844 | 2 / 50% / 1 / -10,816 | 50% | 6 / -11,996 | Y / n / Y |
| single/FULL/3lines | `phase_bucket=morning < 1` | 0.345 | 0.595 | 21 / 76% / 5 / +186,384 | 12 / 7 / +5,821 | 3 / 67% / 1 / +23 | 50% | 5 / -22,834 | Y / n / Y |
| pair/FULL/3lines | `e_iv_atm >= 14.02 AND fmv300 >= -52.08` | 0.667 | 0.410 | 25 / 84% / 4 / +314,665 | 8 / 8 / -122,460 | 7 / 43% / 4 / -33,650 | 50% | 1 / +10,839 | Y / n / n |

Reading: 33 discovery trades (64 % winners, +192,205 Rs), 8 holdout trades (50 %, -22,812 Rs). With 33 trades and min 20 kept, a rule can only remove 13 trades; shuffled labels produce rules as good as the real ones in 20-97 % of runs. The pair/FULL rule keeps 0 holdout trades; the triple/FULL rule (95 % winners on discovery) wins 33 % on holdout. Nothing is distinguishable from luck. The book is already profitable; no rule should be applied on this evidence.


## edge_gate_trail

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 38 | 22 | 16 | 58% | +4.3 | +174,619 |
| holdout | 8 | 4 | 4 | 50% | +1.7 | +7,680 |
| all | 46 | 26 | 20 | 57% | +3.8 | +182,299 |

**Verdict: NONE**  (0 of 10 searches passed all of 2-4)

Best rule found (search `triple/FULL`, 275 features; combine = AND):

### edge_gate_trail: `ep_age_s < 327.4 AND gex_wall_ahead >= 44.58 AND fut_spread >= 1.94`

Shuffle test p = 0.750 (does NOT beat luck). shuffle median best score 0.739, max 0.847; real 0.739.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 38 | 58% | +4.3 | +174,619 | 16 |
| discovery | kept | 21 | 90% | +10.7 | +244,039 | 2 |
| discovery | removed | 17 | 18% | -3.7 | -69,420 | 14 |
| holdout | book | 8 | 50% | +1.7 | +7,680 | 4 |
| holdout | kept | 4 | 50% | +0.6 | -2,743 | 2 |
| holdout | removed | 4 | 50% | +2.8 | +10,423 | 2 |
| all | book | 46 | 57% | +3.8 | +182,299 | 20 |
| all | kept | 25 | 84% | +9.1 | +241,296 | 4 |
| all | removed | 21 | 24% | -2.5 | -58,997 | 16 |

Features used: `ep_age_s` = weather field as recorded at the trigger second; `gex_wall_ahead` = weather field as recorded at the trigger second; `fut_spread` = weather field as recorded at the trigger second

Passes: discovery True, shuffle False, holdout False. shuffle p=0.75; holdout: kept win% below book or removed side profitable

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `vix_chg15 >= -0` | 0.369 | 0.320 | 20 / 75% / 5 / +106,424 | 18 / 11 / +68,195 | 6 / 33% / 4 / -14,680 | 50% | 2 / +22,360 | Y / n / n |
| pair/SMALL | `mean_ret_today >= 0 AND vwap_ext >= -2.08` | 0.477 | 0.610 | 20 / 80% / 4 / +177,106 | 18 / 12 / -2,486 | 3 / 67% / 1 / +13,023 | 50% | 5 / -5,343 | Y / n / Y |
| triple/SMALL | `mv300 >= -47.17 AND vwap_ext >= -2.08 AND vix_chg15 >= -0.03` | 0.523 | 0.775 | 21 / 81% / 4 / +184,356 | 17 / 12 / -9,737 | 3 / 67% / 1 / +13,023 | 50% | 5 / -5,343 | Y / n / Y |
| or/SMALL | `gamma_x_mv30 >= -0.004394 OR vwap_ext >= 21.15` | 0.551 | 0.385 | 24 / 79% / 5 / +184,522 | 14 / 11 / -9,903 | 4 / 75% / 1 / +29,286 | 50% | 4 / -21,606 | Y / n / Y |
| single/FULL | `phase_bucket=morning < 1` | 0.443 | 0.365 | 24 / 75% / 6 / +213,236 | 14 / 10 / -38,616 | 3 / 67% / 1 / +6,435 | 50% | 5 / +1,245 | Y / n / n |
| pair/FULL | `ep_age_s < 327.4 AND fut_spread >= 2.64` | 0.614 | 0.810 | 23 / 83% / 4 / +245,713 | 15 / 12 / -71,094 | 4 / 50% / 2 / -2,743 | 50% | 4 / +10,423 | Y / n / n |
| triple/FULL | `ep_age_s < 327.4 AND gex_wall_ahead >= 44.58 AND fut_spread >= 1.94` | 0.739 | 0.750 | 21 / 90% / 2 / +244,039 | 17 / 14 / -69,420 | 4 / 50% / 2 / -2,743 | 50% | 4 / +10,423 | Y / n / n |
| or/FULL | `gap_pts < -55.55 OR swing_ahead_minus_behind < 1.87` | 0.676 | 0.510 | 22 / 86% / 3 / +252,684 | 16 / 13 / -78,065 | 3 / 33% / 2 / -19,448 | 50% | 5 / +27,128 | Y / n / n |
| single/FULL/3lines | `phase_bucket=morning < 1` | 0.443 | 0.180 | 24 / 75% / 6 / +213,236 | 14 / 10 / -38,616 | 3 / 67% / 1 / +6,435 | 50% | 5 / +1,245 | Y / n / n |
| pair/FULL/3lines | `e_fut_tot_imb_dir < 0.09 AND phase_bucket=morning < 1` | 0.585 | 0.270 | 20 / 85% / 3 / +229,352 | 18 / 13 / -54,733 | 2 / 50% / 1 / -9,828 | 50% | 6 / +17,508 | Y / n / n |

Reading: 38 discovery trades (58 %, +174,619 Rs), 8 holdout (50 %, +7,680 Rs). Same story as edge_gate_only: every rule is p = 0.18-0.81; the one recurring theme (`phase_bucket != morning`, i.e. the 10:00-12:00 entries lose) appears in three searches but its p is 0.18-0.37 and on holdout it keeps 3 trades while the removed 5 are mildly profitable. NONE.


## premium_momentum

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 184 | 67 | 117 | 36% | -0.5 | -175,198 |
| holdout | 57 | 23 | 34 | 40% | -2.9 | -100,662 |
| all | 241 | 90 | 151 | 37% | -1.1 | -275,860 |

**Verdict: NONE**  (0 of 10 searches passed all of 2-4)

Best rule found (search `triple/FULL`, 305 features; combine = AND):

### premium_momentum: `kv >= 0.102 AND sl_room_dn_pct < 3.39 AND e_basis_dev >= -5.705`

Shuffle test p = 0.730 (does NOT beat luck). shuffle median best score 0.381, max 0.469; real 0.366.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 184 | 36% | -0.5 | -175,198 | 117 |
| discovery | kept | 56 | 64% | +4.6 | +243,880 | 20 |
| discovery | removed | 128 | 24% | -2.8 | -419,078 | 97 |
| holdout | book | 57 | 40% | -2.9 | -100,662 | 34 |
| holdout | kept | 20 | 40% | -2.0 | -35,516 | 12 |
| holdout | removed | 37 | 41% | -3.4 | -65,146 | 22 |
| all | book | 241 | 37% | -1.1 | -275,860 | 151 |
| all | kept | 76 | 58% | +2.8 | +208,364 | 32 |
| all | removed | 165 | 28% | -2.9 | -484,224 | 119 |

Features used: `kv` = weather field as recorded at the trigger second; `sl_room_dn_pct` = weather field as recorded at the trigger second; `e_basis_dev` = weather field as recorded at the trigger second

Passes: discovery True, shuffle False, holdout False. shuffle p=0.73; holdout: kept win% below book or removed side profitable

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `breadth_dir < 0.7427` | 0.187 | 0.515 | 55 / 51% / 27 / +80,473 | 129 / 90 / -255,671 | 24 / 38% / 15 / -84,078 | 40% | 33 / -16,585 | Y / n / n |
| pair/SMALL | `abs_delta >= 0.534 AND e_fut_ofi60_dir >= -14.69` | 0.212 | 0.920 | 118 / 44% / 66 / +47,248 | 66 / 51 / -222,446 | 41 / 39% / 25 / -91,871 | 40% | 16 / -8,791 | Y / n / n |
| triple/SMALL | `e_fut_ofi60_dir >= -6.792 AND vwap_ext < 50.52 AND iv_vs_med < 0.032` | 0.277 | 0.705 | 72 / 53% / 34 / +152,926 | 112 / 83 / -328,123 | 12 / 58% / 5 / -5,450 | 40% | 45 / -95,212 | Y / n / Y |
| or/SMALL | `breadth_dir < 0.7427 OR spread_pct < 0.211` | 0.257 | 0.450 | 99 / 47% / 52 / +60,463 | 85 / 65 / -235,661 | 36 / 39% / 22 / -90,652 | 40% | 21 / -10,010 | Y / n / n |
| single/FULL | `sl_room_dn_pct < 3.39` | 0.246 | 0.335 | 92 / 48% / 48 / +141,700 | 92 / 69 / -316,898 | 26 / 50% / 13 / -20,650 | 40% | 31 / -80,012 | Y / n / Y |
| pair/FULL | `kyle_lambda >= 0.0001965 AND sl_room_dn_pct < 3.39` | 0.317 | 0.595 | 81 / 53% / 38 / +202,134 | 103 / 79 / -377,332 | 26 / 50% / 13 / -20,650 | 40% | 31 / -80,012 | Y / n / Y |
| triple/FULL | `kv >= 0.102 AND sl_room_dn_pct < 3.39 AND e_basis_dev >= -5.705` | 0.366 | 0.730 | 56 / 64% / 20 / +243,880 | 128 / 97 / -419,078 | 20 / 40% / 12 / -35,516 | 40% | 37 / -65,146 | Y / n / n |
| or/FULL | `hw_book_chg30 >= 0.02 OR sl_room_dn_pct < 3.39` | 0.317 | 0.640 | 103 / 50% / 52 / +186,641 | 81 / 65 / -361,839 | 30 / 47% / 16 / -32,740 | 40% | 27 / -67,922 | Y / n / Y |
| single/FULL/3lines | `sl_room_dn_pct < 3.39` | 0.246 | 0.255 | 92 / 48% / 48 / +141,700 | 92 / 69 / -316,898 | 26 / 50% / 13 / -20,650 | 40% | 31 / -80,012 | Y / n / Y |
| pair/FULL/3lines | `kyle_lambda >= 0.0001965 AND sl_room_dn_pct < 3.39` | 0.317 | 0.275 | 81 / 53% / 38 / +202,134 | 103 / 79 / -377,332 | 26 / 50% / 13 / -20,650 | 40% | 31 / -80,012 | Y / n / Y |

Reading: The largest book: 184 discovery trades, 36 % winners, -175,198 Rs; holdout 57 trades, 40 %, -100,662 Rs. Scores are low everywhere (best 0.37 with three clauses) and p = 0.26-0.92; the search over ~300 fields finds in shuffled labels exactly what it finds in the real ones. `sl_room_dn_pct < 3.39` (little room to the next support below) recurs as the best single and in every FULL rule and holds its holdout win rate (50 % on 26 kept vs 40 %) but still loses -20,650 Rs there and p = 0.26-0.34. The book's losses are not concentrated in any photograph slice we can see; they are spread across the day and across regimes. NONE. (The only thing that would make this book profitable is not a filter but a different exit: 115 of 241 exits are STOPs.)


## straddle_spike

Record (no rule):

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 37 | 14 | 23 | 38% | +0.3 | -32,890 |
| holdout | 11 | 1 | 10 | 9% | -7.3 | -57,684 |
| all | 48 | 15 | 33 | 31% | -1.4 | -90,574 |

**Verdict: NONE**  (0 of 10 searches passed all of 2-4)

Best rule found (search `or/FULL`, 291 features; combine = OR):

### straddle_spike: `e_fut_imb5_dir < -0.333 OR oi_own_chg30 >= 1.5e+06`

Shuffle test p = 0.605 (does NOT beat luck). shuffle median best score 0.652, max 0.739; real 0.652.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 37 | 38% | +0.3 | -32,890 | 23 |
| discovery | kept | 22 | 64% | +7.3 | +150,650 | 8 |
| discovery | removed | 15 | 0% | -9.9 | -183,540 | 15 |
| holdout | book | 11 | 9% | -7.3 | -57,684 | 10 |
| holdout | kept | 9 | 0% | -8.9 | -58,100 | 9 |
| holdout | removed | 2 | 50% | +0.1 | +416 | 1 |
| all | book | 48 | 31% | -1.4 | -90,574 | 33 |
| all | kept | 31 | 45% | +2.6 | +92,550 | 17 |
| all | removed | 17 | 6% | -8.7 | -183,124 | 16 |

Features used: `e_fut_imb5_dir` = e_fut_imb5 * (+1 for CE, -1 for PE); `oi_own_chg30` = weather field as recorded at the trigger second

Passes: discovery True, shuffle False, holdout False. shuffle p=0.605; holdout: kept win% below book or removed side profitable

All searches on this book (one line each):

| search | rule | score | p | disc kept n / win % / losers / Rs | removed n / losers / Rs | hold kept n / win % / losers / Rs | hold book win % | hold removed n / Rs | 2 / 3 / 4 |
|---|---|---|---|---|---|---|---|---|---|
| single/SMALL | `breadth_dir < 0.9611` | 0.363 | 0.530 | 26 / 50% / 13 / +37,060 | 11 / 10 / -69,950 | 8 / 12% / 7 / -44,564 | 9% | 3 / -13,120 | Y / n / Y |
| pair/SMALL | `er30 < 0.4987 AND vix_chg15 >= -0.06` | 0.509 | 0.455 | 20 / 60% / 8 / +98,995 | 17 / 15 / -131,885 | 7 / 0% / 7 / -41,828 | 9% | 4 / -15,857 | Y / n / n |
| triple/SMALL | `breadth_dir < 0.9611 AND premium >= 61.46 AND spread_pct >= 0.1678` | 0.581 | 0.480 | 21 / 62% / 8 / +115,661 | 16 / 15 / -148,551 | 7 / 14% / 6 / -29,120 | 9% | 4 / -28,564 | Y / n / Y |
| or/SMALL | `spread_pct < 0.247 OR mins_open >= 304.5` | 0.509 | 0.685 | 20 / 60% / 8 / +150,358 | 17 / 15 / -183,248 | 4 / 25% / 3 / -18,440 | 9% | 7 / -39,244 | Y / n / Y |
| single/FULL | `oi_other_chg30 < 3.595e+06` | 0.422 | 0.580 | 22 / 55% / 10 / +81,656 | 15 / 13 / -114,546 | 9 / 11% / 8 / -56,813 | 9% | 2 / -871 | Y / n / Y |
| pair/FULL | `breadth_dir < 0.9611 AND oi_net_help15_dir >= -1.429e+07` | 0.624 | 0.650 | 20 / 65% / 7 / +147,368 | 17 / 16 / -180,258 | 8 / 12% / 7 / -44,564 | 9% | 3 / -13,120 | Y / n / Y |
| triple/FULL | `swing_ahead_minus_behind >= -81.87 AND vix_chg_open < 0.496` | 0.624 | 0.695 | 20 / 65% / 7 / +166,992 | 17 / 16 / -199,882 | 6 / 0% / 6 / -39,673 | 9% | 5 / -18,012 | Y / n / n |
| or/FULL | `e_fut_imb5_dir < -0.333 OR oi_own_chg30 >= 1.5e+06` | 0.652 | 0.605 | 22 / 64% / 8 / +150,650 | 15 / 15 / -183,540 | 9 / 0% / 9 / -58,100 | 9% | 2 / +416 | Y / n / n |
| single/FULL/3lines | `opt_opp_q=REFILLING < 1` | 0.379 | 0.465 | 23 / 52% / 11 / +53,729 | 14 / 12 / -86,619 | 5 / 20% / 4 / -7,936 | 9% | 6 / -49,748 | Y / n / Y |
| pair/FULL/3lines | `breadth_dir < 1 AND oi_net_help15_dir >= -1.429e+07` | 0.581 | 0.215 | 21 / 62% / 8 / +144,242 | 16 / 15 / -177,132 | 8 / 12% / 7 / -44,564 | 9% | 3 / -13,120 | Y / n / Y |

Reading: 37 discovery trades (38 %, -32,890 Rs), 11 holdout (9 %, -57,684 Rs: 1 winner in 4 days). No rule survives: p = 0.22-0.70, and every rule's kept side loses on holdout (0-25 % winners) because the book itself won once in 11 trades. The `breadth_dir < 0.96` clause (do not buy when breadth is already unanimous) recurs and keeps 12 % on holdout vs 9 % -- not a rule. NONE; this book's problem is the strategy, not the entry filter.

