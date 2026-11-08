# Agent 2 — rule search report (8 Nov 2026)

Books: c20_9e, c20_9h, c20_9x_r002, c20_9x_r004, apex_edge, futures_only. Discovery = first 10 replayed days (19 Oct – 2 Nov), holdout = last 4 (3 – 6 Nov). Every search ran on discovery only; the SAME search was re-run on 200 shufflings of the discovery outcomes for p; the frozen rule was then evaluated on holdout. Score = share of losers removed minus share of winners removed (rule_lab.score_masks). Standard: kept >= 20 on discovery, kept mean and rupees > 0, removed losers > winners, p < 0.05, holdout kept win rate >= the book's and removed side not profitable.

## c20_9e

### Record

* discovery: 77 trades, win 61%, mean +6.7%, Rs +534,576, losers 30
* holdout: 23 trades, win 57%, mean +1.9%, Rs +49,504, losers 10
* all 14 days: 100 trades, win 60%, mean +5.6%, Rs +584,080, losers 40

### Best rule (lowest shuffle p found; fails the standard) — search `pair_curated_fine`

Search: best 2-clause AND over the curated family, 9 lines; 23 features, 376 single masks; clauses combined by AND. Shuffle: median best score +0.375, max +0.530, real +0.538.

### c20_9e: `breadth_dir >= 0.2723 AND ret_today < 53.04`

Shuffle test p = 0.000 (beats luck). (AND of clauses) Verdict: REJECTED — fails holdout.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 77 | 61% | +6.7 | +534,576 | 30 |
| discovery | kept | 33 | 91% | +14.4 | +489,846 | 3 |
| discovery | removed | 44 | 39% | +0.9 | +44,730 | 27 |
| holdout | book | 23 | 57% | +1.9 | +49,504 | 10 |
| holdout | kept | 17 | 59% | -0.9 | -22,773 | 7 |
| holdout | removed | 6 | 50% | +10.1 | +72,277 | 3 |
| all | book | 100 | 60% | +5.6 | +584,080 | 40 |
| all | kept | 50 | 80% | +9.2 | +467,074 | 10 |
| all | removed | 50 | 40% | +2.0 | +117,006 | 30 |

Features:

* `breadth_dir`: raw weather field breadth_dir at the trigger second
* `ret_today`: raw weather field ret_today at the trigger second

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `bp_sig >= 1.225` | +0.380 | 0.215 | 23/91%/2 | 28/26 | 3/67%/1 | 20 / -33,504 | REJECTED | shuffle p=0.215 |
| pair_raw | `oi_net_help30 < 5.914e+06 AND new_lows < 128.2` | +0.533 | 0.060 | 43/84%/7 | 23/11 | 17/53%/8 | 6 / +54,135 | REJECTED | shuffle p=0.060; fails holdout |
| single_all | `abs_kv >= 0.163` | +0.393 | 0.235 | 39/79%/8 | 22/16 | 10/80%/2 | 13 / +23,972 | REJECTED | shuffle p=0.235; fails holdout |
| pair_all | `oi_net_help30 < 5.914e+06 AND to_pdh_over_to_pdl < -0.001323` | +0.548 | 0.100 | 36/89%/4 | 26/15 | 3/67%/1 | 20 / +51,766 | REJECTED | shuffle p=0.100; fails holdout |
| single_derived | `abs_kv >= 0.163` | +0.393 | 0.140 | 39/79%/8 | 22/16 | 10/80%/2 | 13 / +23,972 | REJECTED | shuffle p=0.140; fails holdout |
| pair_derived | `abs_mv30 >= 3.4 AND hw_book_imb_x_dir < 0.0304` | +0.523 | 0.095 | 40/85%/6 | 24/13 | 8/75%/2 | 15 / +37,044 | REJECTED | shuffle p=0.095; fails holdout |
| single_text | `last_reason=COUNCIL FWD_TRAIL < 1` | +0.272 | 0.235 | 59/69%/18 | 12/6 | 16/56%/7 | 7 / +63,196 | REJECTED | shuffle p=0.235; fails holdout |
| pair_text | `ep_type=CO-FIRST >= 1 AND last_reason=COUNCIL FWD_TRAIL < 1` | +0.344 | 0.420 | 29/83%/5 | 25/23 | 3/0%/3 | 20 / +63,037 | REJECTED | shuffle p=0.420; fails holdout |
| single_curated_fine | `ret_today < 53.04` | +0.323 | 0.190 | 46/74%/12 | 18/13 | 23/57%/10 | 0 / +0 | REJECTED | shuffle p=0.190 |
| pair_curated_fine | `breadth_dir >= 0.2723 AND ret_today < 53.04` | +0.538 | 0.000 | 33/91%/3 | 27/17 | 17/59%/7 | 6 / +72,277 | REJECTED | fails holdout |
| triple_all | `oi_net_help30 < 5.914e+06 AND dist_hi_minus_dist_lo < 261.2 AND mv300_minus_mv60 >= -17.25` | +0.633 | 0.090 | 40/90%/4 | 26/11 | 14/57%/6 | 9 / +46,182 | REJECTED | shuffle p=0.090; fails holdout |
| or_all | `abs_kv >= 0.163 OR bp_sig >= 0.988` | +0.503 | 0.370 | 57/77%/13 | 17/3 | 17/65%/6 | 6 / -43,258 | REJECTED | shuffle p=0.370 |
| narrow_daystate_single | `ret_today < 53.04` | +0.323 | 0.082 | 46/74%/12 | 18/13 | 23/57%/10 | 0 / +0 | REJECTED | shuffle p=0.082 |
| narrow_daystate_pair | `ret_today < 53.04 AND prior_pnl_today >= 0` | +0.360 | 0.152 | 40/78%/9 | 21/16 | 9/56%/4 | 14 / -15,698 | REJECTED | shuffle p=0.152; fails holdout |
| narrow_flow_single | `oi_net_help30 < 5.914e+06` | +0.366 | 0.052 | 48/75%/12 | 18/11 | 17/53%/8 | 6 / +54,135 | REJECTED | shuffle p=0.052; fails holdout |
| narrow_flow_pair | `breadth_edge >= -0.2277 AND oi_net_help30 < 5.914e+06` | +0.426 | 0.098 | 38/82%/7 | 23/16 | 12/58%/5 | 11 / +46,589 | REJECTED | shuffle p=0.098; fails holdout |
| narrow_trend_single | `mv30 >= 4.41` | +0.323 | 0.128 | 46/74%/12 | 18/13 | 9/67%/3 | 14 / +51,474 | REJECTED | shuffle p=0.128; fails holdout |
| narrow_trend_pair | `mv30 >= 3.1 AND wmove60 < 10.85` | +0.399 | 0.098 | 47/77%/11 | 19/11 | 12/67%/4 | 11 / +42,838 | REJECTED | shuffle p=0.098; fails holdout |
| narrow_option_single | `vega < 6.058` | +0.275 | 0.394 | 54/70%/16 | 14/9 | 14/64%/5 | 9 / +61,656 | REJECTED | shuffle p=0.394; fails holdout |
| narrow_option_pair | `vega < 6.058 AND vanna < 0.005608` | +0.433 | 0.086 | 46/78%/10 | 20/11 | 13/62%/5 | 10 / +66,303 | REJECTED | shuffle p=0.086; fails holdout |

### Reading

Twenty searches (12 broad + 8 narrow families). Nothing passes all of 2-4.

* The one rule that beats luck convincingly is `breadth_dir >= 0.27 AND ret_today < 53` (curated 23-feature family, 9 lines; p = 0.000 in 200 shufflings, shuffle max 0.53 vs real 0.54). On discovery it keeps 33 of 77 at 91 % (3 losers) and the 44 removed hold 27 losers. On holdout it fails: the 6 removed trades were WINNERS worth Rs +72,277 and the 17 kept trades lost Rs -22,773 (7 losers, 59 % vs the book's 57 %). The `ret_today < 53` half never fires on holdout (no holdout day reached +53 %), so all the holdout damage is the breadth clause removing good trades. Also seen unchanged on the sibling council books: same picture (c20_9h kept 50 %, removed +72k on holdout).
* `oi_net_help30 < 5.9e6` (writers adding on our side, less than ~5.9 M) appears in pair_raw / pair_all / triple_all / narrow_flow with p 0.05-0.10 — never below 0.05 and on holdout the removed side is profitable every time.
* `abs_kv >= 0.163` (Kalman velocity magnitude) is the best single everywhere (p 0.14-0.24): a wider search cannot distinguish it from luck.
* `ret_today < 53` alone (narrow 8-feature day-state family, p = 0.082): removes 31 discovery trades with 18 losers (Rs -27k), keeps 46 at 74 %. Sensible ("stop once the day is up 53 %") but no holdout day tested it and it does not beat luck in its own small family.

Honest reading: c20_9e's losers on 3-6 Nov are not the losers of 19 Oct-2 Nov. Every rule that cleans discovery removes the big winners of the holdout days. No rule honestly removes this book's losers.

### Verdict: NONE

## c20_9h

### Record

* discovery: 67 trades, win 55%, mean +7.4%, Rs +473,700, losers 30
* holdout: 22 trades, win 50%, mean +0.3%, Rs +21,785, losers 11
* all 14 days: 89 trades, win 54%, mean +5.7%, Rs +495,485, losers 41

### Best rule (lowest shuffle p found; fails the standard) — search `pair_text`

Search: best 2-indicator AND; 65 features, 208 single masks; clauses combined by AND. Shuffle: median best score +0.334, max +0.523, real +0.432.

### c20_9h: `opt_opp_o=DRAIN-FAST < 1 AND opt_opp_q=DRAIN-FAST < 1`

Shuffle test p = 0.030 (beats luck). (AND of clauses) Verdict: REJECTED — fails holdout.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 67 | 55% | +7.4 | +473,700 | 30 |
| discovery | kept | 45 | 71% | +14.0 | +674,732 | 13 |
| discovery | removed | 22 | 23% | -6.1 | -201,032 | 17 |
| holdout | book | 22 | 50% | +0.3 | +21,785 | 11 |
| holdout | kept | 14 | 36% | -5.2 | -62,215 | 9 |
| holdout | removed | 8 | 75% | +9.9 | +84,000 | 2 |
| all | book | 89 | 54% | +5.7 | +495,485 | 41 |
| all | kept | 59 | 63% | +9.4 | +612,518 | 22 |
| all | removed | 30 | 37% | -1.8 | -117,032 | 19 |

Features:

* `opt_opp_o=DRAIN-FAST`: indicator: 1 when weather field opt_opp_o == 'DRAIN-FAST', else 0
* `opt_opp_q=DRAIN-FAST`: indicator: 1 when weather field opt_opp_q == 'DRAIN-FAST', else 0

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `or45_pos >= -0.08592` | +0.336 | 0.720 | 37/70%/11 | 19/11 | 19/53%/9 | 3 / -21,554 | REJECTED | shuffle p=0.720 |
| pair_raw | `sl_room_dn_pct >= 0.88 AND agree_same >= 5` | +0.503 | 0.495 | 32/81%/6 | 24/11 | 18/56%/8 | 4 / -41,249 | REJECTED | shuffle p=0.495 |
| single_all | `vwap_ext_x_dir >= -54.36` | +0.365 | 0.610 | 47/68%/15 | 15/5 | 20/50%/10 | 2 / -7,826 | REJECTED | shuffle p=0.610 |
| pair_all | `vwap_ext_x_dir >= -54.36 AND e_iv_atm >= 14.08` | +0.505 | 0.660 | 41/76%/10 | 20/6 | 20/50%/10 | 2 / -7,826 | REJECTED | shuffle p=0.660 |
| single_derived | `vwap_ext_x_dir >= -54.36` | +0.365 | 0.365 | 47/68%/15 | 15/5 | 20/50%/10 | 2 / -7,826 | REJECTED | shuffle p=0.365 |
| pair_derived | `gamma_over_theta_min >= -0.02635 AND vwap_ext_x_dir >= -54.36` | +0.477 | 0.535 | 40/75%/10 | 20/7 | 20/50%/10 | 2 / -7,826 | REJECTED | shuffle p=0.535 |
| single_text | `opt_opp_q=DRAIN-FAST < 1` | +0.332 | 0.050 | 48/67%/16 | 14/5 | 15/40%/9 | 7 / +76,099 | REJECTED | shuffle p=0.050; fails holdout |
| pair_text | `opt_opp_o=DRAIN-FAST < 1 AND opt_opp_q=DRAIN-FAST < 1` | +0.432 | 0.030 | 45/71%/13 | 17/5 | 14/36%/9 | 8 / +84,000 | REJECTED | fails holdout |
| single_curated_fine | `agree_same >= 5` | +0.265 | 0.590 | 50/64%/18 | 12/5 | 19/58%/8 | 3 / -48,269 | REJECTED | shuffle p=0.590 |
| pair_curated_fine | `theta_be15 >= 3.184 AND agree_same >= 5` | +0.434 | 0.260 | 25/84%/4 | 26/16 | 10/70%/3 | 12 / +13,387 | REJECTED | shuffle p=0.260; fails holdout |
| triple_all | `vwap_ext_x_dir >= -54.36 AND e_iv_atm >= 14.08 AND last_reason=COUNCIL HALF_LOCK < 1` | +0.623 | 0.450 | 32/88%/4 | 26/9 | 15/47%/8 | 7 / -21,931 | REJECTED | shuffle p=0.450; fails holdout |
| or_all | `fut_lead >= 0.1304 OR give_over_range >= 0.002574` | +0.496 | 0.630 | 34/79%/7 | 23/10 | 2/50%/1 | 20 / +27,069 | REJECTED | shuffle p=0.630; fails holdout |
| narrow_daystate_single | `ret_today < 30.78` | +0.247 | 0.404 | 27/70%/8 | 22/18 | 22/50%/11 | 0 / +0 | REJECTED | shuffle p=0.404 |
| narrow_daystate_pair | `prior_pnl_today < 3.098e+04 AND mins_open < 300.7` | +0.295 | 0.558 | 31/71%/9 | 21/15 | 20/55%/9 | 2 / -28,434 | REJECTED | shuffle p=0.558 |
| narrow_flow_single | `agg_net_x_dir >= -0.045` | +0.315 | 0.204 | 34/71%/10 | 20/13 | 18/44%/10 | 4 / +4,336 | REJECTED | shuffle p=0.204; fails holdout |
| narrow_flow_pair | `agg_net_x_dir >= -0.045 AND hw_book_imb_x_dir < 0.06` | +0.415 | 0.248 | 31/77%/7 | 23/13 | 12/42%/7 | 10 / +72,898 | REJECTED | shuffle p=0.248; fails holdout |
| narrow_trend_single | `wmove60 >= 2.41` | +0.195 | 0.768 | 34/65%/12 | 18/15 | 10/60%/4 | 12 / +36,628 | REJECTED | shuffle p=0.768; fails holdout |
| narrow_trend_pair | `mv300 < 19.5 AND rv15_spot >= 11.3` | +0.353 | 0.416 | 22/82%/4 | 26/19 | 5/60%/2 | 17 / +19,682 | REJECTED | shuffle p=0.416; fails holdout |
| narrow_option_single | `iv_vs_med < -0.76` | +0.239 | 0.768 | 20/75%/5 | 25/22 | 0//0 | 22 / +21,785 | REJECTED | shuffle p=0.768; fails holdout |
| narrow_option_pair | `spread_pct >= 0.2224 AND iv_vs_med < 1.876` | +0.355 | 0.662 | 31/74%/8 | 22/14 | 6/50%/3 | 16 / +24,027 | REJECTED | shuffle p=0.662; fails holdout |

### Reading

Twenty searches. Nothing passes all of 2-4; only the text-indicator searches beat luck.

* `opt_opp_q = DRAIN-FAST` is false (the option's opposing-side quantity is NOT draining fast): single text search p = 0.050, pair with `opt_opp_o = DRAIN-FAST` false p = 0.030. Discovery: keeps 45 of 67 at 71 % and the 22 removed hold 17 losers (Rs -201k). Holdout: the 14 kept win 36 % (book 50 %, 9 losers, Rs -62k) and the 8 removed win 75 % (Rs +84k). It fails holdout outright. The same clause, unchanged, shows the identical reversal on c20_9e, c20_9x_r002 and c20_9x_r004: excellent on 19 Oct-2 Nov, harmful on 3-6 Nov. This is the clearest piece of evidence that the first-ten-day pattern of the council books was a memory of the tape (or that the regime changed on 3 Nov), not a rule.
* Everything numeric (vwap_ext_x_dir, e_iv_atm, sl_room_dn_pct, agree_same, theta_be15) has p 0.26-0.72: indistinguishable from random labels at this search width.
* Narrow families (day-state, flow, trend, option): best p 0.20; none is close.

Honest reading: no rule removes c20_9h's losers; the book is 50 % on holdout and nothing in the photograph at the trigger second separates its holdout winners from losers in a way that was also true on discovery.

### Verdict: NONE

## c20_9x_r002

### Record

* discovery: 29 trades, win 59%, mean +10.5%, Rs +572,471, losers 12
* holdout: 12 trades, win 50%, mean -4.0%, Rs -42,214, losers 6
* all 14 days: 41 trades, win 56%, mean +6.2%, Rs +530,257, losers 18

### Best rule (lowest shuffle p found; fails the standard) — search `single_text`

Search: best single indicator clause (field=VALUE); 57 features, 190 single masks; clauses combined by AND. Shuffle: median best score +0.299, max +0.583, real +0.525.

### c20_9x_r002: `opt_opp_q=DRAIN-FAST < 1`

Shuffle test p = 0.015 (beats luck). (AND of clauses) Verdict: REJECTED — fails holdout.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 29 | 59% | +10.5 | +572,471 | 12 |
| discovery | kept | 21 | 76% | +15.2 | +444,259 | 5 |
| discovery | removed | 8 | 12% | -1.8 | +128,212 | 7 |
| holdout | book | 12 | 50% | -4.0 | -42,214 | 6 |
| holdout | kept | 10 | 50% | -4.8 | -42,230 | 5 |
| holdout | removed | 2 | 50% | +0.0 | +16 | 1 |
| all | book | 41 | 56% | +6.2 | +530,257 | 18 |
| all | kept | 31 | 68% | +8.7 | +402,028 | 10 |
| all | removed | 10 | 20% | -1.4 | +128,229 | 8 |

Features:

* `opt_opp_q=DRAIN-FAST`: indicator: 1 when weather field opt_opp_q == 'DRAIN-FAST', else 0

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `dist_hi < 166.2` | +0.466 | 0.860 | 20/75%/5 | 7/2 | 12/50%/6 | 0 / +0 | REJECTED | shuffle p=0.860 |
| pair_raw | `vix_chg_open < 0.74 AND lo_age_min >= 5.16` | +0.583 | 0.585 | 22/77%/5 | 7/0 | 12/50%/6 | 0 / +0 | REJECTED | shuffle p=0.585 |
| single_all | `opt_opp_q=DRAIN-FAST < 1` | +0.525 | 0.300 | 21/76%/5 | 7/1 | 10/50%/5 | 2 / +16 | REJECTED | shuffle p=0.300; fails holdout |
| pair_all | `opt_opp_q=DRAIN-FAST < 1 AND max_pain_dist_x_dir < 34.14` | +0.608 | 0.640 | 20/80%/4 | 8/1 | 10/50%/5 | 2 / +16 | REJECTED | shuffle p=0.640; fails holdout |
| single_derived | `abs_vwap_ext < 64.52` | +0.466 | 0.805 | 20/75%/5 | 7/2 | 10/50%/5 | 2 / -8,164 | REJECTED | shuffle p=0.805 |
| pair_derived | `abs_accel15 >= 0.84 AND abs_vwap_ext < 64.52` | +0.466 | 0.985 | 20/75%/5 | 7/2 | 8/50%/4 | 4 / -17,570 | REJECTED | shuffle p=0.985 |
| single_text | `opt_opp_q=DRAIN-FAST < 1` | +0.525 | 0.015 | 21/76%/5 | 7/1 | 10/50%/5 | 2 / +16 | REJECTED | fails holdout |
| pair_text | `ep_type=BASKET-LED >= 0 AND opt_opp_q=DRAIN-FAST < 1` | +0.525 | 0.050 | 21/76%/5 | 7/1 | 10/50%/5 | 2 / +16 | REJECTED | shuffle p=0.050; fails holdout |
| single_curated_fine | `mv60_over_sigma15 < 2.859` | +0.324 | 0.850 | 20/70%/6 | 6/3 | 10/50%/5 | 2 / +4,436 | REJECTED | shuffle p=0.850; fails holdout |
| pair_curated_fine | `mv60 >= 3.66 AND n_today < 11` | +0.324 | 0.995 | 20/70%/6 | 6/3 | 8/62%/3 | 4 / -30,329 | REJECTED | shuffle p=0.995 |
| triple_all | `opt_opp_o=DRAIN-FAST < 1 AND dist_hi_over_dist_lo < 49 AND hw_book_imb_t < 0.4136` | +0.608 | 1.000 | 20/80%/4 | 8/1 | 9/44%/5 | 3 / +8,635 | REJECTED | shuffle p=1.000; fails holdout |
| or_all | `po_up5 < 0.9924 OR rv5 < 11.99` | +0.608 | 0.640 | 20/80%/4 | 8/1 | 11/45%/6 | 1 / +572 | REJECTED | shuffle p=0.640; fails holdout |
| narrow_daystate_single | `n_today < 9.6` | +0.324 | 0.350 | 20/70%/6 | 6/3 | 10/60%/4 | 2 / -26,702 | REJECTED | shuffle p=0.350 |
| narrow_daystate_pair | `n_today < 9.6 AND ret_today < 110.7` | +0.324 | 0.600 | 20/70%/6 | 6/3 | 10/60%/4 | 2 / -26,702 | REJECTED | shuffle p=0.600 |
| narrow_flow_single | `hw_book_imb_x_dir < 0.0476` | +0.216 | 0.994 | 23/65%/8 | 4/2 | 8/38%/5 | 4 / -6,896 | REJECTED | shuffle p=0.994; fails holdout |
| narrow_flow_pair | `agg_net_x_dir < 0.739 AND opt_lead_x_dir < 0.0248` | +0.382 | 0.824 | 21/71%/6 | 6/2 | 6/17%/5 | 6 / +13,942 | REJECTED | shuffle p=0.824; fails holdout |
| narrow_trend_single | `mv60_over_sigma15 < 2.859` | +0.324 | 0.696 | 20/70%/6 | 6/3 | 10/50%/5 | 2 / +4,436 | REJECTED | shuffle p=0.696; fails holdout |
| narrow_trend_pair | `mv30 < 18.15 AND mv60_over_sigma15 < 2.859` | +0.324 | 0.946 | 20/70%/6 | 6/3 | 10/50%/5 | 2 / +4,436 | REJECTED | shuffle p=0.946; fails holdout |
| narrow_option_single | `opt_iv_chg5 >= -0.552` | +0.358 | 0.558 | 23/70%/7 | 5/1 | 10/50%/5 | 2 / -10,855 | REJECTED | shuffle p=0.558 |
| narrow_option_pair | `gamma < 0.00357 AND opt_iv_chg5 >= -0.552` | +0.466 | 0.742 | 20/75%/5 | 7/2 | 7/71%/2 | 5 / -50,713 | REJECTED | shuffle p=0.742 |

### Reading

This book traded on only 3 of the 14 days (19 Oct, 27 Oct, 3 Nov): 29 discovery trades, 12 holdout trades. With a 20-trade
minimum, every "rule" keeps 20-23 of 29 — the search has almost no room, and the shuffle medians equal the real scores
(p 0.3-1.0) for every numeric search. The text indicator `opt_opp_q = DRAIN-FAST` false reaches p = 0.015 on discovery
(keeps 21 at 76 %, removes 8 with 7 losers) but on holdout removes 2 trades for Rs +16 and the kept 10 are 50 % = the
book: it does nothing there. Cross-book it is the same clause that reverses on every council sibling on 3-6 Nov.

Honest reading: 41 trades on 3 days is not enough to learn a rule, and nothing found survives. NONE.

### Verdict: NONE

## c20_9x_r004

### Record

* discovery: 44 trades, win 57%, mean +13.7%, Rs +862,384, losers 19
* holdout: 19 trades, win 42%, mean -3.8%, Rs -60,999, losers 11
* all 14 days: 63 trades, win 52%, mean +8.4%, Rs +801,385, losers 30

### Best rule (passes the standard) — search `triple_all`

Search: greedy 3-clause AND over raw + text + derived: top 12 pairs each extended by the best third clause; 369 features, 3230 single masks; clauses combined by AND. Shuffle: median best score +0.747, max +0.880, real +0.867.

### c20_9x_r004: `opt_opp_q=DRAIN-FAST < 1 AND hw_book_imb_t >= -0.2956 AND oi_other_chg5 >= -4.384e+04`

Shuffle test p = 0.010 (beats luck). (AND of clauses) Verdict: PROPOSE — passes 2-4 by the letter; WARNING holdout kept side loses Rs -24,856.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 44 | 57% | +13.7 | +862,384 | 19 |
| discovery | kept | 24 | 96% | +28.5 | +836,742 | 1 |
| discovery | removed | 20 | 10% | -4.2 | +25,642 | 18 |
| holdout | book | 19 | 42% | -3.8 | -60,999 | 11 |
| holdout | kept | 11 | 45% | -2.9 | -24,856 | 6 |
| holdout | removed | 8 | 38% | -5.0 | -36,143 | 5 |
| all | book | 63 | 52% | +8.4 | +801,385 | 30 |
| all | kept | 35 | 80% | +18.7 | +811,886 | 7 |
| all | removed | 28 | 18% | -4.4 | -10,501 | 23 |

Features:

* `opt_opp_q=DRAIN-FAST`: indicator: 1 when weather field opt_opp_q == 'DRAIN-FAST', else 0
* `hw_book_imb_t`: raw weather field hw_book_imb_t at the trigger second
* `oi_other_chg5`: raw weather field oi_other_chg5 at the trigger second

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `kyle_lambda < 0.001116` | +0.417 | 0.735 | 22/77%/5 | 14/8 | 11/55%/5 | 8 / -45,328 | REJECTED | shuffle p=0.735 |
| pair_raw | `vwap_side_min < 51.28 AND opt_run < 0.5512` | +0.617 | 0.370 | 27/81%/5 | 14/3 | 6/0%/6 | 13 / -15,210 | REJECTED | shuffle p=0.370; fails holdout |
| single_all | `opt_opp_q=DRAIN-FAST < 1` | +0.539 | 0.080 | 32/75%/8 | 11/1 | 15/40%/9 | 4 / -322 | REJECTED | shuffle p=0.080; fails holdout |
| pair_all | `opt_opp_q=DRAIN-FAST < 1 AND hw_book_imb_t >= -0.2956` | +0.749 | 0.015 | 28/86%/4 | 15/1 | 15/40%/9 | 4 / -322 | REJECTED | fails holdout |
| single_derived | `gex_wall_ahead_over_gex_wall_behind >= 0.7942` | +0.417 | 0.625 | 22/77%/5 | 14/8 | 12/33%/8 | 7 / -20,101 | REJECTED | shuffle p=0.625; fails holdout |
| pair_derived | `abs_vwap_ext < 66.25 AND mv10_over_mv60 < 1.412` | +0.617 | 0.225 | 27/81%/5 | 14/3 | 12/42%/7 | 7 / -28,665 | REJECTED | shuffle p=0.225; fails holdout |
| single_text | `opt_opp_q=DRAIN-FAST < 1` | +0.539 | 0.005 | 32/75%/8 | 11/1 | 15/40%/9 | 4 / -322 | REJECTED | fails holdout |
| pair_text | `opt_opp_o=DRAIN-FAST < 1 AND opt_opp_q=DRAIN-FAST < 1` | +0.592 | 0.010 | 31/77%/7 | 12/1 | 14/36%/9 | 5 / +8,297 | REJECTED | fails holdout |
| single_curated_fine | `vix >= 16.23` | +0.324 | 0.605 | 22/73%/6 | 13/9 | 2/100%/0 | 17 / -75,413 | REJECTED | shuffle p=0.605 |
| pair_curated_fine | `breadth_dir >= 0.1689 AND ret_today < 42.39` | +0.429 | 0.715 | 20/80%/4 | 15/9 | 17/47%/9 | 2 / -8,570 | REJECTED | shuffle p=0.715 |
| triple_all | `opt_opp_q=DRAIN-FAST < 1 AND hw_book_imb_t >= -0.2956 AND oi_other_chg5 >= -4.384e+04` | +0.867 | 0.010 | 24/96%/1 | 18/2 | 11/45%/6 | 8 / -36,143 | PROPOSE | passes 2-4 by the letter; WARNING holdout kept side loses Rs -24,856 |
| or_all | `kyle_lambda < 0.001116 OR oi_other_chg30 < 3.12e+06` | +0.539 | 0.680 | 32/75%/8 | 11/1 | 18/44%/10 | 1 / -16,478 | REJECTED | shuffle p=0.680 |
| narrow_daystate_single | `prior_pnl_today < 3.96e+04` | +0.417 | 0.048 | 22/77%/5 | 14/8 | 19/42%/11 | 0 / +0 | REJECTED | holdout vacuous: the rule removes no holdout trade (untested) |
| narrow_daystate_pair | `n_today >= 0 AND prior_pnl_today < 3.96e+04` | +0.417 | 0.208 | 22/77%/5 | 14/8 | 19/42%/11 | 0 / +0 | REJECTED | shuffle p=0.208 |
| narrow_flow_single | `oi_net_help30 < 3.523e+06` | +0.286 | 0.778 | 28/68%/9 | 10/6 | 12/42%/7 | 7 / -19,211 | REJECTED | shuffle p=0.778; fails holdout |
| narrow_flow_pair | `agg_net_x_dir >= -0.4371 AND oi_net_help15 < 2.417e+06` | +0.469 | 0.374 | 21/81%/4 | 15/8 | 8/50%/4 | 11 / -35,370 | REJECTED | shuffle p=0.374 |
| narrow_trend_single | `rv15_spot >= 11.76` | +0.232 | 0.800 | 22/68%/7 | 12/10 | 4/50%/2 | 15 / -52,166 | REJECTED | shuffle p=0.800 |
| narrow_trend_pair | `mv30 < 9.61 AND speed15_over_theta_be < 89.62` | +0.337 | 0.804 | 20/75%/5 | 14/10 | 13/46%/7 | 6 / -18,970 | REJECTED | shuffle p=0.804 |
| narrow_option_single | `iv_vs_med < -0.016` | +0.299 | 0.712 | 26/69%/8 | 11/7 | 7/29%/5 | 12 / -37,040 | REJECTED | shuffle p=0.712; fails holdout |
| narrow_option_pair | `spread_pct >= 0.1726 AND iv_vs_med < -0.016` | +0.429 | 0.620 | 20/80%/4 | 15/9 | 5/40%/3 | 14 / -45,321 | REJECTED | shuffle p=0.620; fails holdout |

### Reading

Two rules pass the letter of tests 2-4; neither honestly removes this book's losers, and I say so.

1. `opt_opp_q=DRAIN-FAST < 1 AND hw_book_imb_t >= -0.30 AND oi_other_chg5 >= -43,840` (greedy 3-clause over 369
   raw+text+derived features, 1500 masks, top-12 pairs extended; p = 0.010 — the shuffle max was 0.880 vs the real
   0.867, so 2 of 200 random labelings did as well). Discovery: keeps 24 of 44 at 96 % (1 loser), removes 20 with 18
   losers. Holdout: keeps 11 of 19 at 45 % (book 42 %) with 6 losers and Rs -24,856; removes 8 with Rs -36,143.
   It passes test 4 only because the book itself is 42 % on holdout: the kept side LOSES money there and keeps 6 of the
   11 losers. The first clause is the council-wide DRAIN-FAST indicator that reverses on every sibling on 3-6 Nov.
2. `prior_pnl_today < 39,600` (narrow 8-feature day-state family, 9 lines, p = 0.048 of 500): on discovery keeps 22
   at 77 %, removes 22 with 14 losers. On holdout it never fires (no holdout day had the book up Rs 39.6k before a
   trigger), so the holdout is vacuous — it was not tested, and I do not count it as passing.

Also: `opt_opp_q=DRAIN-FAST < 1` alone has p = 0.005 on discovery (keeps 32 at 75 %, removes 12 with 11 losers) and on
holdout keeps 15 at 40 % (book 42 %), removes 4 at Rs -322: fails. The pair with hw_book_imb_t (p = 0.015) fails the
same way.

Honest reading: the discovery days of c20_9x_r004 are cleanly separable by order-book state at the trigger and the
holdout days are not. Rule 1 is reported as PROPOSE because it passes the written standard, with the plain warning
that its holdout kept side lost Rs 24.9k and won 45 %. I would not run it.

### Verdict: PROPOSE

## apex_edge

### Record

* discovery: 33 trades, win 45%, mean +2.5%, Rs +82,998, losers 18
* holdout: 7 trades, win 57%, mean +2.0%, Rs +9,695, losers 3
* all 14 days: 40 trades, win 48%, mean +2.4%, Rs +92,693, losers 21

### Best rule (lowest shuffle p found; fails the standard) — search `narrow_daystate_pair`

Search: narrow_daystate_pair; 6 features, 82 single masks; clauses combined by AND. Shuffle: median best score +0.311, max +0.556, real +0.489.

### apex_edge: `ret_today >= -0.0402 AND prior_pnl_today < 2.621e+04`

Shuffle test p = 0.062 (does NOT beat luck). (AND of clauses) Verdict: REJECTED — shuffle p=0.062; fails holdout.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 33 | 45% | +2.5 | +82,998 | 18 |
| discovery | kept | 22 | 64% | +7.0 | +149,789 | 8 |
| discovery | removed | 11 | 9% | -6.7 | -66,791 | 10 |
| holdout | book | 7 | 57% | +2.0 | +9,695 | 3 |
| holdout | kept | 4 | 25% | -2.8 | -11,593 | 3 |
| holdout | removed | 3 | 100% | +8.4 | +21,288 | 0 |
| all | book | 40 | 48% | +2.4 | +92,693 | 21 |
| all | kept | 26 | 58% | +5.5 | +138,196 | 11 |
| all | removed | 14 | 29% | -3.5 | -45,503 | 10 |

Features:

* `ret_today`: raw weather field ret_today at the trigger second
* `prior_pnl_today`: sum of the book's own pnl_rs on EARLIER trades that day (0 for the first)

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `absorb60 >= 1.694e+07` | +0.433 | 0.830 | 23/61%/9 | 9/1 | 6/67%/2 | 1 / -9,568 | REJECTED | shuffle p=0.830 |
| pair_raw | `gex_wall_ahead >= 32.58 AND lo_age_min < 135.6` | +0.600 | 0.820 | 20/70%/6 | 12/1 | 6/50%/3 | 1 / +17,222 | REJECTED | shuffle p=0.820; fails holdout |
| single_all | `absorb60 >= 1.694e+07` | +0.433 | 0.935 | 23/61%/9 | 9/1 | 6/67%/2 | 1 / -9,568 | REJECTED | shuffle p=0.935 |
| pair_all | `gex_wall_ahead >= 32.58 AND absorb60 >= 1.241e+07` | +0.600 | 0.940 | 20/70%/6 | 12/1 | 6/67%/2 | 1 / -9,568 | REJECTED | shuffle p=0.940 |
| single_derived | `gamma_x_sigma15 >= 0.005142` | +0.433 | 0.755 | 23/61%/9 | 9/1 | 3/33%/2 | 4 / +27,098 | REJECTED | shuffle p=0.755; fails holdout |
| pair_derived | `abs_accel15 < 15.7 AND premium_over_theta_be15 < 170.5` | +0.600 | 0.755 | 20/70%/6 | 12/1 | 7/57%/3 | 0 / +0 | REJECTED | shuffle p=0.755 |
| single_text | `opt_opp_o=REFILLING < 1` | +0.300 | 0.520 | 21/57%/9 | 9/3 | 6/67%/2 | 1 / -9,646 | REJECTED | shuffle p=0.520 |
| pair_text | `ep_type=BASKET-LED >= 0 AND opt_opp_o=REFILLING < 1` | +0.300 | 0.890 | 21/57%/9 | 9/3 | 6/67%/2 | 1 / -9,646 | REJECTED | shuffle p=0.890 |
| single_curated_fine | `ret_today >= -0.0402` | +0.389 | 0.360 | 26/58%/11 | 7/0 | 4/25%/3 | 3 / +21,288 | REJECTED | shuffle p=0.360; fails holdout |
| pair_curated_fine | `theta_be15 >= 1.02 AND ret_today >= -0.0402` | +0.500 | 0.320 | 24/62%/9 | 9/0 | 4/25%/3 | 3 / +21,288 | REJECTED | shuffle p=0.320; fails holdout |
| triple_all | `gex_wall_ahead >= 32.58 AND absorb60 >= 1.241e+07 AND dte < 6` | +0.600 | 0.990 | 20/70%/6 | 12/1 | 6/67%/2 | 1 / -9,568 | REJECTED | shuffle p=0.990 |
| or_all | `sl_room_dn_pct >= 2.29 OR spread_pct >= 0.2402` | +0.556 | 0.585 | 23/65%/8 | 10/0 | 3/67%/1 | 4 / -133 | REJECTED | shuffle p=0.585 |
| narrow_daystate_single | `ret_today >= -0.0402` | +0.389 | 0.082 | 26/58%/11 | 7/0 | 4/25%/3 | 3 / +21,288 | REJECTED | shuffle p=0.082; fails holdout |
| narrow_daystate_pair | `ret_today >= -0.0402 AND prior_pnl_today < 2.621e+04` | +0.489 | 0.062 | 22/64%/8 | 10/1 | 4/25%/3 | 3 / +21,288 | REJECTED | shuffle p=0.062; fails holdout |
| narrow_flow_single | `oi_net_help30 < 8.441e+06` | +0.244 | 0.934 | 22/55%/10 | 8/3 | 3/67%/1 | 4 / -104 | REJECTED | shuffle p=0.934 |
| narrow_flow_pair | `breadth_edge >= -0.4918 AND oi_net_help30 < 9.006e+06` | +0.367 | 0.880 | 22/59%/9 | 9/2 | 4/50%/2 | 3 / +9,464 | REJECTED | shuffle p=0.880; fails holdout |
| narrow_trend_single | `rv15_spot >= 11.34` | +0.356 | 0.412 | 20/60%/8 | 10/3 | 4/50%/2 | 3 / +25,285 | REJECTED | shuffle p=0.412; fails holdout |
| narrow_trend_pair | `sigma15 >= 5 AND rv15_spot >= 11.34` | +0.356 | 0.714 | 20/60%/8 | 10/3 | 4/50%/2 | 3 / +25,285 | REJECTED | shuffle p=0.714; fails holdout |
| narrow_option_single | `theta_pct >= 0.02176` | +0.433 | 0.220 | 23/61%/9 | 9/1 | 7/57%/3 | 0 / +0 | REJECTED | shuffle p=0.220 |
| narrow_option_pair | `theta_pct >= 0.02176 AND iv_vs_med >= -0.872` | +0.600 | 0.120 | 20/70%/6 | 12/1 | 7/57%/3 | 0 / +0 | REJECTED | shuffle p=0.120 |

### Reading

33 discovery trades (45 % win), 7 holdout trades. With a 20-trade minimum there is hardly any room to remove, and the
shuffle test shows it: for every broad numeric search the shuffle MEDIAN equals the real score (p 0.75-0.99) — random
labels do just as well. The only searches near the bar are the day-state ones: `ret_today >= -0.04` (p = 0.082) and
`ret_today >= -0.04 AND prior_pnl_today < 26,210` (p = 0.062), i.e. "do not trade once the book is down on the day";
on discovery they remove 7-11 trades with 7-10 losers, but on holdout the 3 removed trades were worth Rs +21,288 and
the 4 kept won 25 %. Seven holdout trades cannot confirm or refute anything.

Honest reading: the book is too thin (40 trades) for any rule to be more than a memory of its own tape. NONE.

### Verdict: NONE

## futures_only

### Record

* discovery: 151 trades, win 36%, mean -0.3%, Rs -7,631, losers 96
* holdout: 36 trades, win 53%, mean +0.4%, Rs +13,588, losers 17
* all 14 days: 187 trades, win 40%, mean -0.2%, Rs +5,957, losers 113

### Best rule (lowest shuffle p found; fails the standard) — search `single_text`

Search: best single indicator clause (field=VALUE); 66 features, 214 single masks; clauses combined by AND. Shuffle: median best score +0.170, max +0.347, real +0.226.

### futures_only: `opt_opp_o=DRAIN-SLOW >= 1`

Shuffle test p = 0.095 (does NOT beat luck). (AND of clauses) Verdict: REJECTED — shuffle p=0.095; fails holdout.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 151 | 36% | -0.3 | -7,631 | 96 |
| discovery | kept | 25 | 68% | +4.6 | +90,571 | 8 |
| discovery | removed | 126 | 30% | -1.3 | -98,202 | 88 |
| holdout | book | 36 | 53% | +0.4 | +13,588 | 17 |
| holdout | kept | 7 | 43% | +0.4 | +1,817 | 4 |
| holdout | removed | 29 | 55% | +0.5 | +11,772 | 13 |
| all | book | 187 | 40% | -0.2 | +5,957 | 113 |
| all | kept | 32 | 62% | +3.7 | +92,388 | 12 |
| all | removed | 155 | 35% | -0.9 | -86,430 | 101 |

Features:

* `opt_opp_o=DRAIN-SLOW`: indicator: 1 when weather field opt_opp_o == 'DRAIN-SLOW', else 0

### Every search (one line each)

| search | rule | score | p | disc kept n/win/losers | disc removed L/W | hold kept n/win/losers | hold removed n / Rs | verdict | why |
|---|---|---|---|---|---|---|---|---|---|
| single_raw | `imp_rng < 122.8` | +0.259 | 0.440 | 74/49%/38 | 58/19 | 22/55%/10 | 14 / -439 | REJECTED | shuffle p=0.440 |
| pair_raw | `wall_up < 359.2 AND oi_own_chg30 < 1.307e+06` | +0.381 | 0.170 | 65/57%/28 | 68/18 | 19/53%/9 | 17 / +5,330 | REJECTED | shuffle p=0.170; fails holdout |
| single_all | `imp_rng < 122.8` | +0.259 | 0.575 | 74/49%/38 | 58/19 | 22/55%/10 | 14 / -439 | REJECTED | shuffle p=0.575 |
| pair_all | `wall_up < 359.2 AND oi_own_chg30 < 1.307e+06` | +0.381 | 0.355 | 65/57%/28 | 68/18 | 19/53%/9 | 17 / +5,330 | REJECTED | shuffle p=0.355; fails holdout |
| single_derived | `vix_over_e_rv15 >= 1.268` | +0.209 | 0.895 | 76/46%/41 | 55/20 | 28/46%/15 | 8 / +15,746 | REJECTED | shuffle p=0.895; fails holdout |
| pair_derived | `hour >= 10 AND speed15_over_theta_be < 169.4` | +0.303 | 0.885 | 89/48%/46 | 50/12 | 26/54%/12 | 10 / +796 | REJECTED | shuffle p=0.885; fails holdout |
| single_text | `opt_opp_o=DRAIN-SLOW >= 1` | +0.226 | 0.095 | 25/68%/8 | 88/38 | 7/43%/4 | 29 / +11,772 | REJECTED | shuffle p=0.095; fails holdout |
| pair_text | `fut_opp_q=HOLDING < 1 AND opt_opp_o=DRAIN-SLOW >= 1` | +0.228 | 0.545 | 22/73%/6 | 90/39 | 7/43%/4 | 29 / +11,772 | REJECTED | shuffle p=0.545; fails holdout |
| single_curated_fine | `mins_open >= 54.75` | +0.196 | 0.570 | 91/44%/51 | 45/15 | 27/52%/13 | 9 / +4,462 | REJECTED | shuffle p=0.570; fails holdout |
| pair_curated_fine | `vix >= 15.84 AND mins_open >= 54.75` | +0.306 | 0.250 | 64/53%/30 | 66/21 | 23/48%/12 | 13 / +19,780 | REJECTED | shuffle p=0.250; fails holdout |
| triple_all | `wall_up < 359.2 AND oi_own_chg30 < 1.307e+06 AND vega < 11.74` | +0.436 | 0.485 | 57/63%/21 | 75/19 | 19/53%/9 | 17 / +5,330 | REJECTED | shuffle p=0.485; fails holdout |
| or_all | `skew_atm >= 0.05 OR mv60_sq < 56.25` | +0.370 | 0.330 | 77/53%/36 | 60/14 | 21/48%/11 | 15 / +22,851 | REJECTED | shuffle p=0.330; fails holdout |
| narrow_daystate_single | `mins_to_flat < 307.8` | +0.206 | 0.178 | 90/44%/50 | 46/15 | 27/52%/13 | 9 / +4,462 | REJECTED | shuffle p=0.178; fails holdout |
| narrow_daystate_pair | `prior_winrate_today >= 0.1875 AND mins_open >= 54.75` | +0.227 | 0.398 | 77/47%/41 | 55/19 | 25/52%/12 | 11 / -5,024 | REJECTED | shuffle p=0.398; fails holdout |
| narrow_flow_single | `e_fut_ofi60_x_dir >= 10.12` | +0.163 | 0.732 | 31/55%/14 | 82/38 | 13/46%/7 | 23 / -1,534 | REJECTED | shuffle p=0.732; fails holdout |
| narrow_flow_pair | `opt_book_imb_x_dir >= 0.771 AND opt_lead_x_dir >= -0.008` | +0.199 | 0.954 | 44/52%/21 | 75/32 | 1/100%/0 | 35 / +8,356 | REJECTED | shuffle p=0.954; fails holdout |
| narrow_trend_single | `wmove60 < 6.15` | +0.191 | 0.440 | 75/45%/41 | 55/21 | 26/54%/12 | 10 / +12,116 | REJECTED | shuffle p=0.440; fails holdout |
| narrow_trend_pair | `speed15_over_theta_be < 143.7 AND sigma15 < 6.06` | +0.259 | 0.374 | 85/47%/45 | 51/15 | 29/52%/14 | 7 / +2,958 | REJECTED | shuffle p=0.374; fails holdout |
| narrow_option_single | `e_iv_rv >= 1.26` | +0.167 | 0.750 | 91/43%/52 | 44/16 | 29/48%/15 | 7 / +11,742 | REJECTED | fails discovery standard; shuffle p=0.750; fails holdout |
| narrow_option_pair | `e_iv_rv >= 1.26 AND prem_chg1_pct < 8.04` | +0.228 | 0.868 | 66/48%/34 | 62/23 | 28/46%/15 | 8 / +13,254 | REJECTED | shuffle p=0.868; fails holdout |

### Reading

The weakest book: 151 discovery trades at 36 % and Rs -7,631; 36 holdout trades at 53 % and Rs +13,588. Here "remove
the losers" needs a rule that finds a profitable subset, and with 96 discovery losers there is a lot to remove, so the
scores look large — yet nothing beats luck. Best broad rules: `wall_up < 359 AND oi_own_chg30 < 1.3 M` (pair, p 0.17-
0.36) keeps 65 at 57 %; the triple adds `vega < 11.7` (p 0.485). On holdout every one of them keeps 19-22 trades at
48-55 % (the book is 53 %) and the removed side is profitable (Rs +5k to +23k). The text indicator `opt_opp_o = DRAIN-
SLOW` (p 0.095) keeps 25 at 68 % on discovery and 7 at 43 % on holdout. The narrow families are all p > 0.17.

Honest reading: the photograph at the trigger second carries no stable signal for this book; its 14-day swing from
36 % to 53 % win rate between windows is larger than anything a rule separates. NONE — and the book itself has no edge
to protect (Rs +5,957 over 187 trades).

### Verdict: NONE

## Cross-book evidence (cross.py, pure evaluation of frozen rules on the sibling books; no search, so no p)

The council books share one theme: `opt_opp_q = DRAIN-FAST` false (the chosen option's opposing-side quantity is not
draining fast at the trigger). On the discovery days it cleans every council book (c20_9e 68 %, c20_9h 67 %, r002 76 %,
r004 75 % kept; the removed side 12/21, 14/19, 7/8, 11/12 losers). On the holdout days it reverses on every one of them:
kept 50 / 40 / 50 / 40 % against books of 57 / 50 / 50 / 42 %, and the trades it removes are the big winners of 3-6 Nov
(Rs +72,725 / +76,099 / +16 / -322). The same reversal for `breadth_dir >= 0.27 AND ret_today < 53` (c20_9e's p = 0.000
rule): holdout removed side Rs +72,277 on both c20_9e and c20_9h. `ret_today < 53` alone never fires on any holdout day.
Full numbers in cross.json.

## What failed, in one paragraph

120 search results across 6 books (12 broad searches at 200 shufflings + 8 narrow-family searches at 500 shufflings per
book, plus the greedy 3-clause and OR-of-two forms). Searches over the ~190 raw fields and ~370 raw+text+derived
features never beat luck below p = 0.05 except once (c20_9x_r004 pair_all p = 0.015, triple p = 0.010); the shuffle
medians sit at or above the real scores for the thin books (r002, apex_edge). The derived mathematics (direction
interactions, ratios such as mv60/sigma15 and speed15/theta_be, differences such as er60-er30, products such as
gamma*mv30, |kv|, within-day z-scores and ranks, prior day P&L, time buckets) produced the best singles on c20_9e
(`abs_kv >= 0.163`, p 0.14) and nothing that survived holdout anywhere. Scripts: load.py, search.py (broad), extra.py
(narrow families), cross.py, build_report.py; per-search cards in cards_<book>.md; raw results in results_<book>.json.
