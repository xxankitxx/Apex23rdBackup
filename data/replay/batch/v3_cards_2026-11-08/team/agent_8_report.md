# Agent 8 — rule search report (8 Nov 2026)

Books: spot_dual, spot_dual_lvl, spot_dual_rg, spot_pb45, spot_ft_prem10, m2.0_s0.5_novol.

Method (identical for every book): discovery = first 10 replayed days, holdout = last 4. Features = every numeric weather field (hmm_*/hk_* excluded) + derived mathematics (ratios, differences, products, direction interactions, absolute values, within-day z-scores and ranks from the book's earlier trades that day, time-of-day buckets, log premium, theta-cover minutes, gamma edge, entry slip) + text-field indicators. Clause lines at quantiles (5 or 9 per feature), both directions. Searches: best single, best 2-clause AND, greedy 3-clause AND, OR of two clauses, derived-only, and the same by a RUPEE score (share of loss-rupees removed minus share of profit-rupees removed). Every search was re-run unchanged on 200 shufflings of the discovery outcomes for p. The frozen rule was then evaluated once on the 4 holdout days. Verdict PROPOSE requires: discovery kept >= 20, profitable in mean and rupees, removed side losers > winners; p < 0.05; holdout kept win rate >= the book's, kept side profitable, removed side not profitable, and >= 5 holdout trades kept (fewer cannot be judged).

## spot_dual

Trades 96 (discovery 71, holdout 25); features searched: 191 raw, 149 derived, 43 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 71 | 36 | 35 | 51% | +2.68 | +190,638 |
| holdout | 25 | 11 | 14 | 44% | +1.00 | +17,124 |
| all | 96 | 47 | 49 | 49% | +2.24 | +207,763 |

### Best rule found (best of the rejected)

Search: best single clause, PRE-REGISTERED hypothesis set of 22 economically-motivated features (theta_ratio, er60, er30, breadth_dir, pos_dir, speed15, spread_pct, premium, mins_open, vix, rv15_spot, imp_depth, strad_excess, oi_net_help15, agree_same, trig_str, is_CE, hour_bucket, r_speed15_thetabe, theta_cover_min, gamma_edge, regime=DIRECTIONAL), 5 lines; min_keep 20; 204 clause masks over 22 features. Score 0.329; shuffle median 0.267, max 0.409 over 200 shufflings.

### spot_dual: `rv15_spot >= 11.95`

Shuffle test p = 0.105 (does NOT beat luck). Verdict REJECTED: shuffle p=0.105 (luck); holdout kept only 3 trades: cannot be judged; holdout removed side profitable (+32,399).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 71 | 51% | +2.7 | +190,638 | 35 |
| discovery | kept | 22 | 77% | +10.9 | +256,276 | 5 |
| discovery | removed | 49 | 39% | -1.0 | -65,637 | 30 |
| holdout | book | 25 | 44% | +1.0 | +17,124 | 14 |
| holdout | kept | 3 | 33% | -5.3 | -15,275 | 2 |
| holdout | removed | 22 | 45% | +1.9 | +32,399 | 12 |
| all | book | 96 | 49% | +2.2 | +207,763 | 49 |
| all | kept | 25 | 72% | +8.9 | +241,000 | 7 |
| all | removed | 71 | 41% | -0.1 | -33,238 | 42 |

Features: `rv15_spot` = raw weather field rv15_spot

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `n_today < 3` | 29 / 72% / 8 / +278,168 | 0.345 | 12 / 42% / 7 / +6,266 | 13 / +10,858 | REJECTED: shuffle p=0.345 (luck); holdout kept win 42% < book 44%; holdout removed side profitable (+10,858) |
| s_raw9 mk20 | `n_today < 3` | 29 / 72% / 8 / +278,168 | 0.530 | 12 / 42% / 7 / +6,266 | 13 / +10,858 | REJECTED: shuffle p=0.530 (luck); holdout kept win 42% < book 44%; holdout removed side profitable (+10,858) |
| p_raw mk20 | `zomma >= -7.03e-05 AND rest_with_rs >= 1.499e+06` | 32 / 75% / 8 / +226,223 | 0.915 | 18 / 44% / 10 / +32,864 | 7 / -15,740 | REJECTED: shuffle p=0.915 (luck) |
| s_all mk20 | `n_today < 3` | 29 / 72% / 8 / +278,168 | 0.535 | 12 / 42% / 7 / +6,266 | 13 / +10,858 | REJECTED: shuffle p=0.535 (luck); holdout kept win 42% < book 44%; holdout removed side profitable (+10,858) |
| s_all9 mk20 | `n_today < 3` | 29 / 72% / 8 / +278,168 | 0.735 | 12 / 42% / 7 / +6,266 | 13 / +10,858 | REJECTED: shuffle p=0.735 (luck); holdout kept win 42% < book 44%; holdout removed side profitable (+10,858) |
| p_all mk20 | `abs_e_fut_ofi60 >= 7.06 AND oi_own_chg30 >= -7.644e+04` | 23 / 87% / 3 / +319,020 | 0.775 | 4 / 50% / 2 / -15,242 | 21 / +32,367 | REJECTED: shuffle p=0.775 (luck); holdout kept only 4 trades: cannot be judged; holdout removed side profitable (+32,367) |
| t_all mk20 | `abs_e_fut_ofi60 >= 7.06 AND oi_own_chg30 >= -7.644e+04 AND bn60 >= -0.08` | 20 / 95% / 1 / +350,480 | 0.980 | 4 / 50% / 2 / -15,242 | 21 / +32,367 | REJECTED: shuffle p=0.980 (luck); holdout kept only 4 trades: cannot be judged; holdout removed side profitable (+32,367) |
| o_all mk20 | `e_rv15 >= 12 OR x_e_fut_micro_dir >= 0.4` | 38 / 74% / 10 / +393,689 | 0.610 | 10 / 40% / 6 / -34,964 | 15 / +52,088 | REJECTED: shuffle p=0.610 (luck); holdout kept win 40% < book 44%; holdout kept side loses money (-34,964); holdout removed side profitable (+52,088) |
| s_der mk20 | `halfhour_bucket < 2` | 22 / 73% / 6 / +233,412 | 0.955 | 7 / 43% / 4 / -22,964 | 18 / +40,089 | REJECTED: shuffle p=0.955 (luck); holdout kept win 43% < book 44%; holdout kept side loses money (-22,964); holdout removed side profitable (+40,089) |
| p_der mk20 | `x_opt_imb_chg30_dir < 0.003 AND r_wallroom_sigma15 < 85.64` | 32 / 75% / 8 / +331,194 | 0.795 | 12 / 67% / 4 / +67,038 | 13 / -49,914 | REJECTED: shuffle p=0.795 (luck) |
| s_pnl mk20 | `chain_age >= 44` | 36 / 64% / 13 / +298,662 | 0.985 | 11 / 45% / 6 / +19,074 | 14 / -1,950 | REJECTED: shuffle p=0.985 (luck) |
| p_pnl mk20 | `depth_age_fut >= 0.9 AND x_accel15_dir >= -1.6` | 26 / 73% / 7 / +411,128 | 0.880 | 10 / 30% / 7 / +6,308 | 15 / +10,816 | REJECTED: shuffle p=0.880 (luck); holdout kept win 30% < book 44%; holdout removed side profitable (+10,816) |
| s_all mk35 | `chain_age >= 44` | 36 / 64% / 13 / +298,662 | 0.995 | 11 / 45% / 6 / +19,074 | 14 / -1,950 | REJECTED: shuffle p=0.995 (luck) |
| p_all mk35 | `ret_today < 92.32 AND gap_pts < 13.1` | 38 / 71% / 11 / +429,673 | 0.890 | 16 / 38% / 10 / +20,127 | 9 / -3,003 | REJECTED: shuffle p=0.890 (luck); holdout kept win 38% < book 44% |
| t_all mk35 | `ret_today < 92.32 AND gap_pts < 13.1 AND opt_run < 0.017` | 35 / 74% / 9 / +435,282 | 0.965 | 14 / 43% / 8 / +37,424 | 11 / -20,300 | REJECTED: shuffle p=0.965 (luck); holdout kept win 43% < book 44% |
| o_all mk35 | `chain_age >= 44 OR pos_in_range >= 0.4946` | 53 / 64% / 19 / +424,739 | 0.790 | 22 / 45% / 12 / +18,050 | 3 / -926 | REJECTED: shuffle p=0.790 (luck) |
| s_hyp mk35 | `rv15_spot >= 10.73` | 36 / 64% / 13 / +244,052 | 0.345 | 9 / 33% / 6 / -38,363 | 16 / +55,487 | REJECTED: shuffle p=0.345 (luck); holdout kept win 33% < book 44%; holdout kept side loses money (-38,363); holdout removed side profitable (+55,487) |
| p_hyp mk35 | `premium >= 79.3 AND rv15_spot >= 10.73` | 35 / 66% / 12 / +262,252 | 0.690 | 8 / 38% / 5 / -28,672 | 17 / +45,796 | REJECTED: shuffle p=0.690 (luck); holdout kept win 38% < book 44%; holdout kept side loses money (-28,672); holdout removed side profitable (+45,796) |
| t_hyp mk35 | `premium >= 79.3 AND rv15_spot >= 10.73` | 35 / 66% / 12 / +262,252 | 0.850 | 8 / 38% / 5 / -28,672 | 17 / +45,796 | REJECTED: shuffle p=0.850 (luck); holdout kept win 38% < book 44%; holdout kept side loses money (-28,672); holdout removed side profitable (+45,796) |
| s_pnl mk35 | `chain_age >= 44` | 36 / 64% / 13 / +298,662 | 0.965 | 11 / 45% / 6 / +19,074 | 14 / -1,950 | REJECTED: shuffle p=0.965 (luck) |
| p_pnl mk35 | `ret_today < 92.32 AND gap_pts < 13.1` | 38 / 71% / 11 / +429,673 | 0.730 | 16 / 38% / 10 / +20,127 | 9 / -3,003 | REJECTED: shuffle p=0.730 (luck); holdout kept win 38% < book 44% |
| s_hyp mk20 | `rv15_spot >= 11.95` | 22 / 77% / 5 / +256,276 | 0.105 | 3 / 33% / 2 / -15,275 | 22 / +32,399 | REJECTED: shuffle p=0.105 (luck); holdout kept only 3 trades: cannot be judged; holdout removed side profitable (+32,399) |
| p_hyp mk20 | `spread_pct >= 0.123 AND rv15_spot >= 11.95` | 21 / 81% / 4 / +281,444 | 0.415 | 2 / 50% / 1 / -4,277 | 23 / +21,401 | REJECTED: shuffle p=0.415 (luck); holdout kept only 2 trades: cannot be judged; holdout removed side profitable (+21,401) |
| t_hyp mk20 | `spread_pct >= 0.123 AND rv15_spot >= 11.95` | 21 / 81% / 4 / +281,444 | 0.680 | 2 / 50% / 1 / -4,277 | 23 / +21,401 | REJECTED: shuffle p=0.680 (luck); holdout kept only 2 trades: cannot be judged; holdout removed side profitable (+21,401) |
| s_all mk33 | `abs_e_fut_ofi60 >= 6.908` | 47 / 64% / 17 / +220,230 | 0.830 | 16 / 56% / 7 / +39,221 | 6 / -50,498 | REJECTED: shuffle p=0.830 (luck) |
| p_all mk33 | `abs_e_fut_ofi60 >= 6.908 AND ret_today < 92.34` | 42 / 71% / 12 / +306,329 | 0.670 | 16 / 56% / 7 / +39,221 | 6 / -50,498 | REJECTED: shuffle p=0.670 (luck) |
| t_all mk33 | `abs_e_fut_ofi60 >= 6.908 AND ret_today < 92.34 AND e_iv_atm >= 14.32` | 37 / 78% / 8 / +350,230 | 0.435 | 15 / 53% / 7 / +32,350 | 7 / -43,628 | REJECTED: shuffle p=0.435 (luck) |
| o_all mk33 | `mins_open < 138.3 OR hw_book_imb < 0.005` | 49 / 67% / 16 / +379,015 | 0.395 | 17 / 47% / 9 / -1,908 | 5 / -9,370 | REJECTED: shuffle p=0.395 (luck); holdout kept side loses money (-1,908) |
| s_hyp mk33 | `mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.385 | 11 / 45% / 6 / -21,236 | 11 / +9,958 | REJECTED: shuffle p=0.385 (luck); holdout kept side loses money (-21,236); holdout removed side profitable (+9,958) |
| p_hyp mk33 | `pos_dir >= 0.2704 AND mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.835 | 8 / 50% / 4 / +1,014 | 14 / -12,292 | REJECTED: shuffle p=0.835 (luck) |
| t_hyp mk33 | `pos_dir >= 0.2704 AND mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.945 | 8 / 50% / 4 / +1,014 | 14 / -12,292 | REJECTED: shuffle p=0.945 (luck) |
| s_pnl mk33 | `mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.960 | 11 / 45% / 6 / -21,236 | 11 / +9,958 | REJECTED: shuffle p=0.960 (luck); holdout kept side loses money (-21,236); holdout removed side profitable (+9,958) |
| p_pnl mk33 | `ret_today < 92.34 AND r_gapts_sigma15 < 2.62` | 37 / 70% / 11 / +387,826 | 1.000 | 13 / 31% / 9 / -8,274 | 9 / -3,003 | REJECTED: shuffle p=1.000 (luck); holdout kept win 31% < book 41%; holdout kept side loses money (-8,274) |

### Reading

96 trades, 49 % winners, +2.08 L in all; the 4 holdout days were weak (44 %, +17 k). Every search's best discovery rule was a sliver (keep 20-38 of 71) and none beat the shuffle (lowest p 0.345 for `n_today < 3`, i.e. only the first two trades of the day; the pre-registered set gave `rv15_spot >= 11.95`, p 0.105, keeping 3 holdout trades). The only rules whose holdout kept side out-won the book (`x_opt_imb_chg30_dir < 0.003 AND r_wallroom_sigma15 < 85.6`, holdout 67 %, +67 k, removed -50 k) sit at p 0.795: random labels find a pair that good four times in five. With half-the-book min_keep (35) nothing changed. No rule honestly removes this book's losers.

**Verdict: NONE**

## spot_dual_lvl

Trades 94 (discovery 71, holdout 23); features searched: 190 raw, 149 derived, 43 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 71 | 38 | 33 | 54% | +2.92 | +246,987 |
| holdout | 23 | 9 | 14 | 39% | -0.75 | -25,760 |
| all | 94 | 47 | 47 | 50% | +2.02 | +221,228 |

### Best rule found (best of the rejected)

Search: OR of two single clauses, raw + derived + indicators, 5 lines, top-1000 singles; min_keep 35; 3464 clause masks over 382 features. Score 0.436; shuffle median 0.428, max 0.527 over 200 shufflings.

(OR rule: a trade is kept when EITHER clause holds.)

### spot_dual_lvl: `chain_age >= 44 AND to_pdh < 100.3`

Shuffle test p = 0.415 (does NOT beat luck). Verdict REJECTED: shuffle p=0.415 (luck); holdout kept side loses money (-25,760).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 71 | 54% | +2.9 | +246,987 | 33 |
| discovery | kept | 51 | 69% | +6.7 | +436,501 | 16 |
| discovery | removed | 20 | 15% | -6.8 | -189,514 | 17 |
| holdout | book | 23 | 39% | -0.8 | -25,760 | 14 |
| holdout | kept | 23 | 39% | -0.8 | -25,760 | 14 |
| holdout | removed | 0 |  |  | +0 | 0 |
| all | book | 94 | 50% | +2.0 | +221,228 | 47 |
| all | kept | 74 | 59% | +4.4 | +410,742 | 30 |
| all | removed | 20 | 15% | -6.8 | -189,514 | 17 |

Features: `chain_age` = raw weather field chain_age; `to_pdh` = raw weather field to_pdh

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `fut_spread >= 2.6` | 50 / 66% / 17 / +322,498 | 0.535 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.535 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| s_raw9 mk20 | `fut_spread >= 2.6` | 50 / 66% / 17 / +322,498 | 0.630 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.630 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| p_raw mk20 | `fut_spread >= 2.6 AND chain_age >= 44` | 27 / 85% / 4 / +366,707 | 0.525 | 9 / 33% / 6 / -15,574 | 14 / -10,186 | REJECTED: shuffle p=0.525 (luck); holdout kept win 33% < book 39%; holdout kept side loses money (-15,574) |
| s_all mk20 | `fut_spread >= 2.6` | 50 / 66% / 17 / +322,498 | 0.690 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.690 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| s_all9 mk20 | `fut_spread >= 2.6` | 50 / 66% / 17 / +322,498 | 0.750 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.750 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| p_all mk20 | `fut_spread >= 2.6 AND chain_age >= 44` | 27 / 85% / 4 / +366,707 | 0.755 | 9 / 33% / 6 / -15,574 | 14 / -10,186 | REJECTED: shuffle p=0.755 (luck); holdout kept win 33% < book 39%; holdout kept side loses money (-15,574) |
| t_all mk20 | `fut_spread >= 2.6 AND chain_age >= 44 AND fut_ttq60 >= 3120` | 24 / 96% / 1 / +408,645 | 0.540 | 9 / 33% / 6 / -15,574 | 14 / -10,186 | REJECTED: shuffle p=0.540 (luck); holdout kept win 33% < book 39%; holdout kept side loses money (-15,574) |
| o_all mk20 | `rv15_spot >= 12.12 OR x_e_fut_micro_dir >= 0.39` | 38 / 76% / 9 / +429,530 | 0.675 | 9 / 44% / 5 / -31,437 | 14 / +5,678 | REJECTED: shuffle p=0.675 (luck); holdout kept side loses money (-31,437); holdout removed side profitable (+5,678) |
| s_der mk20 | `abs_e_fut_ofi60 >= 7.04` | 50 / 64% / 18 / +288,334 | 0.900 | 17 / 53% / 8 / +24,739 | 6 / -50,498 | REJECTED: shuffle p=0.900 (luck) |
| p_der mk20 | `abs_e_fut_ofi60 >= 7.04 AND x_wmove60_bank_dir >= -4.26` | 45 / 71% / 13 / +336,378 | 0.715 | 10 / 60% / 4 / +11,973 | 13 / -37,732 | REJECTED: shuffle p=0.715 (luck) |
| s_pnl mk20 | `chain_age >= 44` | 37 / 68% / 12 / +347,659 | 0.715 | 12 / 42% / 7 / +6,416 | 11 / -32,175 | REJECTED: shuffle p=0.715 (luck) |
| p_pnl mk20 | `depth_age_fut >= 0.9 AND x_wmove30_dir >= 1.12` | 20 / 90% / 2 / +416,754 | 0.485 | 9 / 33% / 6 / -45,773 | 14 / +20,014 | REJECTED: shuffle p=0.485 (luck); holdout kept win 33% < book 39%; holdout kept side loses money (-45,773); holdout removed side profitable (+20,014) |
| s_all mk35 | `fut_spread >= 2.6` | 50 / 66% / 17 / +322,498 | 0.650 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.650 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| p_all mk35 | `fut_spread >= 2.6 AND ret_today < 86.11` | 44 / 73% / 12 / +333,460 | 0.595 | 16 / 31% / 11 / -41,580 | 7 / +15,821 | REJECTED: shuffle p=0.595 (luck); holdout kept win 31% < book 39%; holdout kept side loses money (-41,580); holdout removed side profitable (+15,821) |
| t_all mk35 | `fut_spread >= 2.6 AND ret_today < 86.11 AND r_gapts_sigma15 < 7.122` | 39 / 79% / 8 / +388,908 | 0.450 | 10 / 20% / 8 / -31,428 | 13 / +5,668 | REJECTED: shuffle p=0.450 (luck); holdout kept win 20% < book 39%; holdout kept side loses money (-31,428); holdout removed side profitable (+5,668) |
| o_all mk35 | `chain_age >= 44 OR to_pdh < 100.3` | 51 / 69% / 16 / +436,501 | 0.415 | 23 / 39% / 14 / -25,760 | 0 / +0 | REJECTED: shuffle p=0.415 (luck); holdout kept side loses money (-25,760) |
| s_hyp mk35 | `rv15_spot >= 10.73` | 36 / 64% / 13 / +267,199 | 0.845 | 9 / 33% / 6 / -37,976 | 14 / +12,217 | REJECTED: shuffle p=0.845 (luck); holdout kept win 33% < book 39%; holdout kept side loses money (-37,976); holdout removed side profitable (+12,217) |
| p_hyp mk35 | `spread_pct >= 0.196 AND trig_str >= 11.4` | 36 / 69% / 11 / +304,428 | 0.525 | 7 / 43% / 4 / +33,121 | 16 / -58,880 | REJECTED: shuffle p=0.525 (luck) |
| t_hyp mk35 | `spread_pct >= 0.196 AND trig_str >= 11.4 AND imp_depth >= 0.0862` | 35 / 71% / 10 / +315,412 | 0.590 | 7 / 43% / 4 / +33,121 | 16 / -58,880 | REJECTED: shuffle p=0.590 (luck) |
| s_pnl mk35 | `chain_age >= 44` | 37 / 68% / 12 / +347,659 | 0.600 | 12 / 42% / 7 / +6,416 | 11 / -32,175 | REJECTED: shuffle p=0.600 (luck) |
| p_pnl mk35 | `x_kv_dir >= -0.102 AND phase_bucket=afternoon < 1` | 39 / 67% / 13 / +421,512 | 0.925 | 12 / 42% / 7 / -28,984 | 11 / +3,224 | REJECTED: shuffle p=0.925 (luck); holdout kept side loses money (-28,984); holdout removed side profitable (+3,224) |
| s_hyp mk20 | `rv15_spot >= 12.12` | 21 / 76% / 5 / +248,157 | 0.525 | 2 / 50% / 1 / -10,816 | 21 / -14,944 | REJECTED: shuffle p=0.525 (luck); holdout kept only 2 trades: cannot be judged |
| p_hyp mk20 | `spread_pct >= 0.196 AND trig_str >= 11.4` | 36 / 69% / 11 / +304,428 | 0.720 | 7 / 43% / 4 / +33,121 | 16 / -58,880 | REJECTED: shuffle p=0.720 (luck) |
| t_hyp mk20 | `spread_pct >= 0.196 AND trig_str >= 11.4 AND premium < 203.6` | 30 / 77% / 7 / +323,921 | 0.525 | 7 / 43% / 4 / +33,121 | 16 / -58,880 | REJECTED: shuffle p=0.525 (luck) |

### Reading

94 trades, 50 % winners; the holdout lost money for the book itself (39 %, -25.8 k). The discovery favourite `fut_spread >= 2.6` (66 % of 50 kept) collapsed to 31 % on holdout. Derived-only `abs_e_fut_ofi60 >= 7.04` (+ bank wmove) held 60 % on holdout but p 0.715. The pre-registered pair `spread_pct >= 0.196 AND trig_str >= 11.4` kept 7 holdout trades at 43 %, +33 k with the removed side -59 k, but p 0.525-0.72. Nothing beats luck; nothing carries. The book's problem on 3-6 Nov is not visible in its trigger weather at this sample size.

**Verdict: NONE**

## spot_dual_rg

Trades 89 (discovery 67, holdout 22); features searched: 189 raw, 140 derived, 43 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 67 | 35 | 32 | 52% | +3.14 | +195,637 |
| holdout | 22 | 9 | 13 | 41% | -0.07 | -11,278 |
| all | 89 | 44 | 45 | 49% | +2.34 | +184,360 |

### Best rule found (best of the rejected)

Search: OR of two single clauses, raw + derived + indicators, 5 lines, top-1000 singles; min_keep 20; 3376 clause masks over 372 features. Score 0.550; shuffle median 0.508, max 0.646 over 200 shufflings.

(OR rule: a trade is kept when EITHER clause holds.)

### spot_dual_rg: `rv15_spot >= 12.06 AND x_e_fut_micro_dir >= 0.404`

Shuffle test p = 0.150 (does NOT beat luck). Verdict REJECTED: shuffle p=0.150 (luck); holdout kept win 40% < book 41%; holdout kept side loses money (-34,964); holdout removed side profitable (+23,686).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 67 | 52% | +3.1 | +195,637 | 32 |
| discovery | kept | 36 | 78% | +11.0 | +417,875 | 8 |
| discovery | removed | 31 | 23% | -6.0 | -222,238 | 24 |
| holdout | book | 22 | 41% | -0.1 | -11,278 | 13 |
| holdout | kept | 10 | 40% | -3.8 | -34,964 | 6 |
| holdout | removed | 12 | 42% | +3.1 | +23,686 | 7 |
| all | book | 89 | 49% | +2.3 | +184,360 | 45 |
| all | kept | 46 | 70% | +7.8 | +382,912 | 14 |
| all | removed | 43 | 28% | -3.4 | -198,552 | 31 |

Features: `rv15_spot` = raw weather field rv15_spot; `x_e_fut_micro_dir` = e_fut_micro * dir (+1 CE / -1 PE): the field in the trade's direction

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `e_rv15 >= 12.1` | 20 / 80% / 4 / +219,528 | 0.755 | 2 / 50% / 1 / -10,680 | 20 / -598 | REJECTED: shuffle p=0.755 (luck); holdout kept only 2 trades: cannot be judged |
| s_raw9 mk20 | `e_rv15 >= 12.1` | 20 / 80% / 4 / +219,528 | 0.855 | 2 / 50% / 1 / -10,680 | 20 / -598 | REJECTED: shuffle p=0.855 (luck); holdout kept only 2 trades: cannot be judged |
| p_raw mk20 | `oi_own_chg30 >= 1.097e+05 AND e_syn_dev >= -1.45` | 24 / 83% / 4 / +320,297 | 0.885 | 6 / 33% / 4 / -28,464 | 16 / +17,186 | REJECTED: shuffle p=0.885 (luck); holdout kept win 33% < book 41%; holdout kept side loses money (-28,464); holdout removed side profitable (+17,186) |
| s_all mk20 | `e_rv15 >= 12.1` | 20 / 80% / 4 / +219,528 | 0.870 | 2 / 50% / 1 / -10,680 | 20 / -598 | REJECTED: shuffle p=0.870 (luck); holdout kept only 2 trades: cannot be judged |
| s_all9 mk20 | `e_rv15 >= 12.1` | 20 / 80% / 4 / +219,528 | 0.955 | 2 / 50% / 1 / -10,680 | 20 / -598 | REJECTED: shuffle p=0.955 (luck); holdout kept only 2 trades: cannot be judged |
| p_all mk20 | `abs_e_fut_ofi60 >= 6.908 AND oi_own_chg30 >= 1.097e+05` | 22 / 91% / 2 / +332,748 | 0.555 | 4 / 50% / 2 / -15,242 | 18 / +3,965 | REJECTED: shuffle p=0.555 (luck); holdout kept only 4 trades: cannot be judged; holdout removed side profitable (+3,965) |
| t_all mk20 | `abs_e_fut_ofi60 >= 6.908 AND oi_own_chg30 >= 1.097e+05 AND breadth_dir >= 0.04512` | 20 / 100% / 0 / +377,806 | 0.605 | 4 / 50% / 2 / -15,242 | 18 / +3,965 | REJECTED: shuffle p=0.605 (luck); holdout kept only 4 trades: cannot be judged; holdout removed side profitable (+3,965) |
| o_all mk20 | `rv15_spot >= 12.06 OR x_e_fut_micro_dir >= 0.404` | 36 / 78% / 8 / +417,875 | 0.150 | 10 / 40% / 6 / -34,964 | 12 / +23,686 | REJECTED: shuffle p=0.150 (luck); holdout kept win 40% < book 41%; holdout kept side loses money (-34,964); holdout removed side profitable (+23,686) |
| s_der mk20 | `abs_e_fut_ofi60 >= 6.908` | 47 / 64% / 17 / +220,230 | 0.720 | 16 / 56% / 7 / +39,221 | 6 / -50,498 | REJECTED: shuffle p=0.720 (luck) |
| p_der mk20 | `r_wallroom_sigma15 < 86.59 AND x_opt_imb_chg30_dir < 0.003` | 31 / 77% / 7 / +315,776 | 0.535 | 11 / 64% / 4 / +48,708 | 11 / -59,985 | REJECTED: shuffle p=0.535 (luck) |
| s_pnl mk20 | `x_wmove30_dir >= 3.384` | 20 / 75% / 5 / +299,725 | 0.995 | 5 / 20% / 4 / -24,729 | 17 / +13,452 | REJECTED: shuffle p=0.995 (luck); holdout kept win 20% < book 41%; holdout kept side loses money (-24,729); holdout removed side profitable (+13,452) |
| p_pnl mk20 | `x_accel15_dir >= -1.66 AND depth_age_fut >= 0.9` | 25 / 72% / 7 / +374,137 | 0.995 | 9 / 22% / 7 / -19,754 | 13 / +8,476 | REJECTED: shuffle p=0.995 (luck); holdout kept win 22% < book 41%; holdout kept side loses money (-19,754); holdout removed side profitable (+8,476) |
| s_all mk33 | `abs_e_fut_ofi60 >= 6.908` | 47 / 64% / 17 / +220,230 | 0.830 | 16 / 56% / 7 / +39,221 | 6 / -50,498 | REJECTED: shuffle p=0.830 (luck) |
| p_all mk33 | `abs_e_fut_ofi60 >= 6.908 AND ret_today < 92.34` | 42 / 71% / 12 / +306,329 | 0.670 | 16 / 56% / 7 / +39,221 | 6 / -50,498 | REJECTED: shuffle p=0.670 (luck) |
| t_all mk33 | `abs_e_fut_ofi60 >= 6.908 AND ret_today < 92.34 AND e_iv_atm >= 14.32` | 37 / 78% / 8 / +350,230 | 0.435 | 15 / 53% / 7 / +32,350 | 7 / -43,628 | REJECTED: shuffle p=0.435 (luck) |
| o_all mk33 | `mins_open < 138.3 OR hw_book_imb < 0.005` | 49 / 67% / 16 / +379,015 | 0.395 | 17 / 47% / 9 / -1,908 | 5 / -9,370 | REJECTED: shuffle p=0.395 (luck); holdout kept side loses money (-1,908) |
| s_hyp mk33 | `mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.385 | 11 / 45% / 6 / -21,236 | 11 / +9,958 | REJECTED: shuffle p=0.385 (luck); holdout kept side loses money (-21,236); holdout removed side profitable (+9,958) |
| p_hyp mk33 | `pos_dir >= 0.2704 AND mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.835 | 8 / 50% / 4 / +1,014 | 14 / -12,292 | REJECTED: shuffle p=0.835 (luck) |
| t_hyp mk33 | `pos_dir >= 0.2704 AND mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.945 | 8 / 50% / 4 / +1,014 | 14 / -12,292 | REJECTED: shuffle p=0.945 (luck) |
| s_pnl mk33 | `mins_open < 138.3` | 33 / 67% / 11 / +294,986 | 0.960 | 11 / 45% / 6 / -21,236 | 11 / +9,958 | REJECTED: shuffle p=0.960 (luck); holdout kept side loses money (-21,236); holdout removed side profitable (+9,958) |
| p_pnl mk33 | `ret_today < 92.34 AND r_gapts_sigma15 < 2.62` | 37 / 70% / 11 / +387,826 | 1.000 | 13 / 31% / 9 / -8,274 | 9 / -3,003 | REJECTED: shuffle p=1.000 (luck); holdout kept win 31% < book 41%; holdout kept side loses money (-8,274) |
| s_hyp mk20 | `rv15_spot >= 12.06` | 20 / 80% / 4 / +219,528 | 0.200 | 3 / 33% / 2 / -15,275 | 19 / +3,998 | REJECTED: shuffle p=0.200 (luck); holdout kept only 3 trades: cannot be judged; holdout removed side profitable (+3,998) |
| p_hyp mk20 | `spread_pct >= 0.1262 AND mins_open < 138.3` | 31 / 71% / 9 / +334,396 | 0.675 | 9 / 56% / 4 / +8,794 | 13 / -20,072 | REJECTED: shuffle p=0.675 (luck) |
| t_hyp mk20 | `spread_pct >= 0.1262 AND mins_open < 138.3 AND rv15_spot >= 9.454` | 24 / 79% / 5 / +330,246 | 0.665 | 9 / 56% / 4 / +8,794 | 13 / -20,072 | REJECTED: shuffle p=0.665 (luck) |

### Reading

89 trades, 49 % winners, holdout 41 %, -11 k. One clause recurs across all three spot_dual variants: `abs_e_fut_ofi60 >= ~7` (strong 60-s futures order-flow imbalance of either sign at the trigger). Here it keeps 47 of 67 on discovery at 64 % and on holdout 16 of 22 at 56 %, +39 k, with the removed 6 trades losing -50 k — the only rule family whose holdout pointed the right way on every window. But its shuffle p is 0.72-0.83: a single clause this good appears in random labels most of the time, so it is a hint to re-test on the next 14 days, not a rule. Everything else (e_rv15 slivers, oi_own_chg30 pairs, 100 %-of-20 triples) is memory of the tape.

**Verdict: NONE**

## spot_pb45

Trades 57 (discovery 43, holdout 14); features searched: 189 raw, 127 derived, 36 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 43 | 22 | 21 | 51% | -0.77 | +44,184 |
| holdout | 14 | 9 | 5 | 64% | +7.01 | +86,164 |
| all | 57 | 31 | 26 | 54% | +1.14 | +130,348 |

### Best rule found (best of the rejected)

Search: best single clause, raw weather fields, 5 quantile lines (10..90 %), both directions; min_keep 20; 1832 clause masks over 189 features. Score 0.489; shuffle median 0.442, max 0.621 over 200 shufflings.

### spot_pb45: `bank_z < -0.49`

Shuffle test p = 0.265 (does NOT beat luck). Verdict REJECTED: shuffle p=0.265 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 43 | 51% | -0.8 | +44,184 | 21 |
| discovery | kept | 21 | 76% | +10.2 | +206,625 | 5 |
| discovery | removed | 22 | 27% | -11.3 | -162,442 | 16 |
| holdout | book | 14 | 64% | +7.0 | +86,164 | 5 |
| holdout | kept | 10 | 60% | +2.3 | +25,656 | 4 |
| holdout | removed | 4 | 75% | +18.9 | +60,508 | 1 |
| all | book | 57 | 54% | +1.1 | +130,348 | 26 |
| all | kept | 31 | 71% | +7.7 | +232,281 | 9 |
| all | removed | 26 | 35% | -6.6 | -101,933 | 17 |

Features: `bank_z` = raw weather field bank_z

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.265 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.265 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| s_raw9 mk20 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.295 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.295 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| p_raw mk20 | `bank_z < -0.49 AND streak >= -1` | 20 / 80% / 4 / +220,353 | 0.960 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.960 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| s_all mk20 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.350 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.350 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| s_all9 mk20 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.415 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.415 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| p_all mk20 | `bank_z < -0.49 AND streak >= -1` | 20 / 80% / 4 / +220,353 | 0.995 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.995 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| t_all mk20 | `bank_z < -0.49 AND streak >= -1` | 20 / 80% / 4 / +220,353 | 1.000 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=1.000 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| o_all mk20 | `adv_vetoes >= 4 OR lo_age_min < 26` | 28 / 71% / 8 / +217,496 | 0.500 | 9 / 67% / 3 / +52,890 | 5 / +33,274 | REJECTED: shuffle p=0.500 (luck); holdout removed side profitable (+33,274) |
| s_der mk20 | `abs_accel15 >= 3.65` | 22 / 68% / 7 / +136,289 | 0.925 | 8 / 62% / 3 / +24,492 | 6 / +61,672 | REJECTED: shuffle p=0.925 (luck); holdout kept win 62% < book 64%; holdout removed side profitable (+61,672) |
| p_der mk20 | `abs_mv300 >= 16.11 AND r_premchg1_spread >= -34.26` | 21 / 76% / 5 / +201,081 | 0.945 | 5 / 80% / 1 / +67,990 | 9 / +18,174 | REJECTED: shuffle p=0.945 (luck); holdout removed side profitable (+18,174) |
| s_pnl mk20 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.970 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.970 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| p_pnl mk20 | `wmove60_it < 0.022 AND term_atm >= -0.259` | 21 / 76% / 5 / +284,606 | 0.985 | 12 / 67% / 4 / +85,979 | 2 / +185 | REJECTED: shuffle p=0.985 (luck); holdout removed side profitable (+185) |
| s_all mk21 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.345 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.345 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| p_all mk21 | `zomma >= -7.204e-05 AND rv1 >= 9.68` | 22 / 77% / 5 / +225,521 | 0.965 | 7 / 57% / 3 / +19,588 | 7 / +66,576 | REJECTED: shuffle p=0.965 (luck); holdout kept win 57% < book 64%; holdout removed side profitable (+66,576) |
| t_all mk21 | `zomma >= -7.204e-05 AND rv1 >= 9.68 AND fut_spread >= 1.84` | 21 / 81% / 4 / +240,341 | 0.990 | 6 / 67% / 2 / +23,410 | 8 / +62,754 | REJECTED: shuffle p=0.990 (luck); holdout removed side profitable (+62,754) |
| o_all mk21 | `adv_vetoes >= 4 OR lo_age_min < 26` | 28 / 71% / 8 / +217,496 | 0.445 | 9 / 67% / 3 / +52,890 | 5 / +33,274 | REJECTED: shuffle p=0.445 (luck); holdout removed side profitable (+33,274) |
| s_hyp mk21 | `imp_depth >= 0.5026` | 31 / 61% / 12 / +77,500 | 0.670 | 9 / 56% / 4 / +41,405 | 5 / +44,759 | REJECTED: shuffle p=0.670 (luck); holdout kept win 56% < book 64%; holdout removed side profitable (+44,759) |
| p_hyp mk21 | `spread_pct >= 0.0796 AND imp_depth >= 0.5026` | 28 / 68% / 9 / +140,699 | 0.490 | 9 / 56% / 4 / +41,405 | 5 / +44,759 | REJECTED: shuffle p=0.490 (luck); holdout kept win 56% < book 64%; holdout removed side profitable (+44,759) |
| t_hyp mk21 | `spread_pct >= 0.0796 AND imp_depth >= 0.5026 AND vix < 17.02` | 23 / 74% / 6 / +202,394 | 0.440 | 8 / 62% / 3 / +60,437 | 6 / +25,727 | REJECTED: shuffle p=0.440 (luck); holdout kept win 62% < book 64%; holdout removed side profitable (+25,727) |
| s_pnl mk21 | `bank_z < -0.49` | 21 / 76% / 5 / +206,625 | 0.970 | 10 / 60% / 4 / +25,656 | 4 / +60,508 | REJECTED: shuffle p=0.970 (luck); holdout kept win 60% < book 64%; holdout removed side profitable (+60,508) |
| p_pnl mk21 | `wmove60_it < 0.022 AND term_atm >= -0.259` | 21 / 76% / 5 / +284,606 | 0.975 | 12 / 67% / 4 / +85,979 | 2 / +185 | REJECTED: shuffle p=0.975 (luck); holdout removed side profitable (+185) |
| s_hyp mk20 | `imp_depth >= 0.5026` | 31 / 61% / 12 / +77,500 | 0.680 | 9 / 56% / 4 / +41,405 | 5 / +44,759 | REJECTED: shuffle p=0.680 (luck); holdout kept win 56% < book 64%; holdout removed side profitable (+44,759) |
| p_hyp mk20 | `spread_pct >= 0.0796 AND imp_depth >= 0.5026` | 28 / 68% / 9 / +140,699 | 0.575 | 9 / 56% / 4 / +41,405 | 5 / +44,759 | REJECTED: shuffle p=0.575 (luck); holdout kept win 56% < book 64%; holdout removed side profitable (+44,759) |
| t_hyp mk20 | `spread_pct >= 0.0796 AND imp_depth >= 0.5026 AND vix < 17.02` | 23 / 74% / 6 / +202,394 | 0.430 | 8 / 62% / 3 / +60,437 | 6 / +25,727 | REJECTED: shuffle p=0.430 (luck); holdout kept win 62% < book 64%; holdout removed side profitable (+25,727) |

### Reading

57 trades, 54 % winners; the holdout was the book's BEST stretch (64 %, +86 k of its +130 k). No removal rule can improve on that, and none did: every search's removed side was profitable on holdout. Best discovery clause `bank_z < -0.49` (76 % of 21) is p 0.27-0.35 and 60 % on holdout. The pre-registered set gave `imp_depth >= 0.50` / `spread_pct >= 0.08`, p 0.43-0.68. This book does not need a filter on this evidence; it needs more days.

**Verdict: NONE**

## spot_ft_prem10

Trades 467 (discovery 350, holdout 117); features searched: 193 raw, 148 derived, 55 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 350 | 186 | 164 | 53% | +0.80 | +187,187 |
| holdout | 117 | 64 | 53 | 55% | +0.96 | +54,636 |
| all | 467 | 250 | 217 | 54% | +0.84 | +241,823 |

### Best rule found (best of the rejected)

Search: best 2-clause AND, raw weather fields, 5 lines; min_keep 20; 1876 clause masks over 193 features. Score 0.275; shuffle median 0.220, max 0.276 over 200 shufflings.

### spot_ft_prem10: `ep_n_cross < 14 AND chop30 >= 2.31`

Shuffle test p = 0.005 (beats luck). Verdict REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 350 | 53% | +0.8 | +187,187 | 164 |
| discovery | kept | 175 | 67% | +3.7 | +658,964 | 58 |
| discovery | removed | 175 | 39% | -2.1 | -471,776 | 106 |
| holdout | book | 117 | 55% | +1.0 | +54,636 | 53 |
| holdout | kept | 63 | 54% | +0.8 | +17,566 | 29 |
| holdout | removed | 54 | 56% | +1.1 | +37,070 | 24 |
| all | book | 467 | 54% | +0.8 | +241,823 | 217 |
| all | kept | 238 | 63% | +2.9 | +676,530 | 87 |
| all | removed | 229 | 43% | -1.3 | -434,707 | 130 |

Features: `ep_n_cross` = raw weather field ep_n_cross; `chop30` = raw weather field chop30

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.060 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.060 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| s_raw9 mk20 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.105 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.105 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| p_raw mk20 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.005 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| s_all mk20 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.115 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.115 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| s_all9 mk20 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.170 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.170 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| p_all mk20 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.025 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| t_all mk20 | `ep_n_cross < 14 AND chop30 >= 2.31 AND bank_z >= -0.306` | 156 / 71% / 46 / +708,451 | 0.030 | 57 / 54% / 26 / +18,044 | 60 / +36,592 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+36,592) |
| o_all mk20 | `ep_n_cross < 14 OR spot_age < 0.01` | 238 / 61% / 93 / +591,867 | 0.820 | 79 / 51% / 39 / -24,264 | 38 / +78,900 | REJECTED: shuffle p=0.820 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-24,264); holdout removed side profitable (+78,900) |
| s_der mk20 | `x_accel30_dir >= -4` | 245 / 58% / 103 / +408,522 | 0.840 | 90 / 57% / 39 / +58,386 | 27 / -3,750 | REJECTED: shuffle p=0.840 (luck) |
| p_der mk20 | `x_basis_chg60_dir < 2.95 AND x_e_syn_dev_dir >= -0.913` | 157 / 67% / 52 / +598,065 | 0.085 | 60 / 55% / 27 / +30,079 | 57 / +24,557 | REJECTED: shuffle p=0.085 (luck); holdout removed side profitable (+24,557) |
| s_pnl mk20 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.115 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.115 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| p_pnl mk20 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.045 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| s_all mk175 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.075 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.075 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| p_all mk175 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.010 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| t_all mk175 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.220 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: shuffle p=0.220 (luck); holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| o_all mk175 | `opt_lead >= 0.0215 OR opt_iv_chg1 >= 0.05` | 255 / 60% / 101 / +576,140 | 0.085 | 91 / 62% / 35 / +145,727 | 26 / -91,091 | REJECTED: shuffle p=0.085 (luck) |
| s_hyp mk175 | `er30 < 0.2995` | 209 / 59% / 86 / +428,110 | 0.150 | 77 / 56% / 34 / +45,584 | 40 / +9,051 | REJECTED: shuffle p=0.150 (luck); holdout removed side profitable (+9,051) |
| p_hyp mk175 | `er30 < 0.4324 AND breadth_dir < 0.9169` | 193 / 61% / 75 / +500,126 | 0.120 | 78 / 59% / 32 / +94,698 | 39 / -40,063 | REJECTED: shuffle p=0.120 (luck) |
| t_hyp mk175 | `er30 < 0.4324 AND breadth_dir < 0.9169 AND rv15_spot < 15.61` | 191 / 61% / 74 / +500,789 | 0.270 | 75 / 59% / 31 / +86,356 | 42 / -31,720 | REJECTED: shuffle p=0.270 (luck) |
| s_pnl mk175 | `ep_n_cross < 14` | 234 / 60% / 93 / +528,466 | 0.060 | 78 / 51% / 38 / -10,420 | 39 / +65,055 | REJECTED: shuffle p=0.060 (luck); holdout kept win 51% < book 55%; holdout kept side loses money (-10,420); holdout removed side profitable (+65,055) |
| p_pnl mk175 | `ep_n_cross < 14 AND chop30 >= 2.31` | 175 / 67% / 58 / +658,964 | 0.015 | 63 / 54% / 29 / +17,566 | 54 / +37,070 | REJECTED: holdout kept win 54% < book 55%; holdout removed side profitable (+37,070) |
| s_hyp mk20 | `er30 < 0.2995` | 209 / 59% / 86 / +428,110 | 0.220 | 77 / 56% / 34 / +45,584 | 40 / +9,051 | REJECTED: shuffle p=0.220 (luck); holdout removed side profitable (+9,051) |
| p_hyp mk20 | `er30 < 0.4324 AND breadth_dir < 0.9169` | 193 / 61% / 75 / +500,126 | 0.255 | 78 / 59% / 32 / +94,698 | 39 / -40,063 | REJECTED: shuffle p=0.255 (luck) |
| t_hyp mk20 | `er30 < 0.4324 AND breadth_dir < 0.9169 AND spread_pct < 0.281` | 174 / 63% / 65 / +501,430 | 0.335 | 67 / 60% / 27 / +91,689 | 50 / -37,053 | REJECTED: shuffle p=0.335 (luck) |

### Reading

467 trades (350 / 117), 54 % winners, +2.42 L. This is the one book where a search BEAT the shuffle: `ep_n_cross < 14 AND chop30 >= 2.31` was found independently by the win-rate pair search (p 0.005 raw, 0.025 all), the greedy triple (0.030) and the rupee pair (0.045); on discovery it keeps 175 of 350 at 67 % (+659 k, so the removed 175 lost -472 k). It then FAILED holdout: kept 63 at 54 % against the book's 55 %, +17.6 k, while the 54 removed trades won 46 % and made +37 k. A rule that removes profitable trades on the four unseen days is rejected whatever its p. Two further rules pointed the right way on holdout but did not clear p < 0.05: the pre-registered pair `er30 < 0.432 AND breadth_dir < 0.917` (holdout kept 78 at 59 %, +95 k; removed 39 at -40 k; p 0.12-0.26) and the OR rule `opt_lead >= 0.0215 OR opt_iv_chg1 >= 0.05` (holdout kept 91 at 62 %, +146 k; removed 26 at -91 k; p 0.085). Both are now pre-registered candidates for the next replay days; neither is proposed.

**Verdict: NONE**

## m2.0_s0.5_novol

Trades 37 (discovery 32, holdout 5); features searched: 189 raw, 130 derived, 36 text indicators.

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 32 | 14 | 18 | 44% | +1.20 | +32,315 |
| holdout | 5 | 1 | 4 | 20% | -5.04 | -24,122 |
| all | 37 | 15 | 22 | 41% | +0.35 | +8,193 |

### Best rule found (best of the rejected)

Search: best single clause by RUPEE score (share of loss-Rs removed minus share of profit-Rs removed), raw + derived + indicators, 5 lines; min_keep 20; 3252 clause masks over 355 features. Score 0.769; shuffle median 0.577, max 0.759 over 200 shufflings.

### m2.0_s0.5_novol: `fut_opp_o=HOLDING < 0.7`

Shuffle test p = 0.000 (beats luck). Verdict REJECTED: holdout kept only 3 trades: cannot be judged.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 32 | 44% | +1.2 | +32,315 | 18 |
| discovery | kept | 22 | 64% | +5.0 | +109,116 | 8 |
| discovery | removed | 10 | 0% | -7.2 | -76,801 | 10 |
| holdout | book | 5 | 20% | -5.0 | -24,122 | 4 |
| holdout | kept | 3 | 33% | -5.7 | -16,750 | 2 |
| holdout | removed | 2 | 0% | -4.0 | -7,371 | 2 |
| all | book | 37 | 41% | +0.4 | +8,193 | 22 |
| all | kept | 25 | 60% | +3.7 | +92,365 | 10 |
| all | removed | 12 | 0% | -6.6 | -84,172 | 12 |

Features: `fut_opp_o=HOLDING` = indicator: 1 when weather text field fut_opp_o == 'HOLDING', else 0

### Every search run (one line each)

| search | rule | disc kept n / win / losers / Rs | p | holdout kept n / win / losers / Rs | holdout removed n / Rs | verdict |
|---|---|---|---|---|---|---|
| s_raw mk20 | `absorb60 >= 1.797e+07` | 22 / 59% / 9 / +102,356 | 0.900 | 4 / 25% / 3 / -21,733 | 1 / -2,389 | REJECTED: shuffle p=0.900 (luck); holdout kept only 4 trades: cannot be judged |
| s_raw9 mk20 | `absorb60 >= 1.797e+07` | 22 / 59% / 9 / +102,356 | 0.905 | 4 / 25% / 3 / -21,733 | 1 / -2,389 | REJECTED: shuffle p=0.905 (luck); holdout kept only 4 trades: cannot be judged |
| p_raw mk20 | `absorb60 >= 1.797e+07 AND kvt >= 5.221` | 20 / 65% / 7 / +111,842 | 0.960 | 4 / 25% / 3 / -21,733 | 1 / -2,389 | REJECTED: shuffle p=0.960 (luck); holdout kept only 4 trades: cannot be judged |
| s_all mk20 | `fut_opp_o=HOLDING < 0.7` | 22 / 64% / 8 / +109,116 | 0.175 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: shuffle p=0.175 (luck); holdout kept only 3 trades: cannot be judged |
| s_all9 mk20 | `fut_opp_o=HOLDING < 0.7` | 22 / 64% / 8 / +109,116 | 0.175 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: shuffle p=0.175 (luck); holdout kept only 3 trades: cannot be judged |
| p_all mk20 | `fut_opp_o=HOLDING < 0.7 AND sl_next_res=swing low < 1` | 20 / 70% / 6 / +115,690 | 0.255 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: shuffle p=0.255 (luck); holdout kept only 3 trades: cannot be judged |
| t_all mk20 | `fut_opp_o=HOLDING < 0.7 AND sl_next_res=swing low < 1` | 20 / 70% / 6 / +115,690 | 0.510 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: shuffle p=0.510 (luck); holdout kept only 3 trades: cannot be judged |
| o_all mk20 | `e_rv15 >= 10.47 OR rv15_spot >= 10.47` | 22 / 59% / 9 / +70,180 | 0.645 | 2 / 0% / 2 / -8,590 | 3 / -15,532 | REJECTED: shuffle p=0.645 (luck); holdout kept only 2 trades: cannot be judged |
| s_der mk20 | `d_opt_iv_atm_iv5 >= -0.037` | 22 / 59% / 9 / +51,668 | 0.845 | 3 / 33% / 2 / -5,099 | 2 / -19,022 | REJECTED: shuffle p=0.845 (luck); holdout kept only 3 trades: cannot be judged |
| p_der mk20 | `d_opt_iv_atm_iv5 >= -0.037 AND x_e_syn_dev_dir < 5.179` | 20 / 65% / 7 / +60,385 | 0.900 | 3 / 33% / 2 / -5,099 | 2 / -19,022 | REJECTED: shuffle p=0.900 (luck); holdout kept only 3 trades: cannot be judged |
| s_pnl mk20 | `fut_opp_o=HOLDING < 0.7` | 22 / 64% / 8 / +109,116 | 0.000 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: holdout kept only 3 trades: cannot be judged |
| p_pnl mk20 | `fut_opp_o=HOLDING < 1 AND hw_book_imb_t < 0.3908` | 20 / 70% / 6 / +119,464 | 0.000 | 3 / 33% / 2 / -16,750 | 2 / -7,371 | REJECTED: holdout kept only 3 trades: cannot be judged |
| s_hyp mk20 | `vix >= 15.72` | 22 / 59% / 9 / +58,874 | 0.195 | 5 / 20% / 4 / -24,122 | 0 / +0 | REJECTED: shuffle p=0.195 (luck); holdout kept side loses money (-24,122) |
| p_hyp mk20 | `vix >= 15.72 AND rv15_spot >= 8.54` | 20 / 65% / 7 / +69,550 | 0.105 | 5 / 20% / 4 / -24,122 | 0 / +0 | REJECTED: shuffle p=0.105 (luck); holdout kept side loses money (-24,122) |
| t_hyp mk20 | `vix >= 15.72 AND rv15_spot >= 8.54` | 20 / 65% / 7 / +69,550 | 0.225 | 5 / 20% / 4 / -24,122 | 0 / +0 | REJECTED: shuffle p=0.225 (luck); holdout kept side loses money (-24,122) |

### Reading

37 trades (32 / 5), 41 % winners, +8 k in all; the 5 holdout trades lost 4 (-24 k). The rupee-score search found `fut_opp_o != HOLDING` (the opposing futures queue is not holding) with p = 0.000 by rupees (no shuffle reached 0.77), keeping 22 of 32 at 64 %, +109 k; by win-rate the same clause is p 0.175. It keeps only 3 holdout trades (1 winner): the holdout cannot judge it, and the brief's standard needs a judgment. With 5 holdout trades no rule on this book can be proposed from this data.

**Verdict: NONE**

## Closing reading

Verdict: NONE on all six books; 0 of 6 PROPOSE. 13 searches x 6 books at min_keep 20, plus 3 pre-registered-set searches and 9 half-the-book searches per book: 150 shuffle-tested rules, 200 shufflings each. Only four (all on spot_ft_prem10, all the same ep_n_cross/chop30 pair) beat luck, and that pair removed profitable trades on the unseen days. What the exercise shows in plain words: with 37-96 trades per book the win-rate score with a 20-trade floor can always carve out a 70-100 % sliver on the first ten days, and the shuffle test shows random labels do the same; the one book big enough to clear the shuffle (467 trades) did not carry to the next four days. The losers of these books are not separable from the winners by their trigger weather on 14 days of tape. Candidates pre-registered here for re-test when more days are recorded (not for the register now): spot_ft_prem10 `er30 < 0.432 AND breadth_dir < 0.917`; spot_ft_prem10 `opt_lead >= 0.0215 OR opt_iv_chg1 >= 0.05`; spot_dual family `abs(e_fut_ofi60) >= 7`.
