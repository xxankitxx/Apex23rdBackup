# Agent 7 — spot retest family (spot_dc12_t12 and children)

Data: 14 replayed days 19 Oct – 6 Nov 2026. Discovery = first 10 days, holdout = last 4. Every search was re-run on 200 shufflings of the discovery outcomes (same features, same lines, same depth); p = share of shufflings scoring at least the real score. Score = share of discovery losers removed minus share of winners removed (rule_lab.score_masks), except S7 (kept win rate). Searches per book: S1 single clause on the ~195 base fields (5 quantile lines each); S2 pair on base; S3 single on ~180 derived features (ratios, differences, products, direction-signed fields, absolute values, within-day z-scores and ranks from the book's own earlier trades, time buckets, booleans, prior exited win share); S4 pair on all fields incl. text indicators (top 2500 masks); S5 pair with 9 lines; S6 greedy triple; S7 pair maximising kept win rate; S8 OR of two clauses; S9 single on all fields, 9 lines.

## spot_dc12_t12

Record — all 14 days: 291 trades, 36% win, mean +0.62 %, Rs +179,374, 185 losers. Discovery: 215 trades, 34% win, mean +0.61 %, Rs +127,481, 142 losers. Holdout: 76 trades, 43% win, mean +0.67 %, Rs +51,893, 43 losers.
Features searched: 195 base, 162 derived, 58 text indicators.

### Best rule (best attempt, rejected) — found by S7 pair maximising kept win rate (kept>=30), all fields, 5 lines

### spot_dc12_t12: `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4`

Shuffle test p = 0.370 (does NOT beat luck). Shuffle median 0.687, max 0.788; real score 0.700.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 215 | 34% | +0.6 | +127,481 | 142 |
| discovery | kept | 30 | 70% | +6.7 | +224,386 | 9 |
| discovery | removed | 185 | 28% | -0.4 | -96,905 | 133 |
| holdout | book | 76 | 43% | +0.7 | +51,893 | 43 |
| holdout | kept | 13 | 54% | +0.8 | +8,632 | 6 |
| holdout | removed | 63 | 41% | +0.6 | +43,261 | 37 |
| all | book | 291 | 36% | +0.6 | +179,374 | 185 |
| all | kept | 43 | 65% | +4.9 | +233,018 | 15 |
| all | removed | 248 | 31% | -0.1 | -53,644 | 170 |

Verdict on this rule: **REJECTED** — shuffle p=0.370 >= 0.05; holdout removed side is profitable.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `opt_iv_chg5 >= 0.08` | 69 / 49% / +187,704 / 35 | 146 / 107 | 0.410 | 23 / 52% / -3,068 / 11 | +54,961 | REJECTED: shuffle p=0.410 >= 0.05; holdout removed side is profitable |
| S2 pair | `absorb60 < 3.46e+07 AND fmv300 < 18.4` | 58 / 59% / +333,125 / 24 | 157 / 118 | 0.540 | 16 / 38% / -2,090 / 10 | +53,982 | REJECTED: shuffle p=0.540 >= 0.05; holdout kept win rate below the book's |
| S3 single | `s_bank_z < 0.478` | 150 / 41% / +232,141 / 89 | 65 / 53 | 0.510 | 42 / 50% / +71,591 / 21 | -19,698 | REJECTED: shuffle p=0.510 >= 0.05 |
| S4 pair | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219` | 70 / 56% / +160,768 / 31 | 145 / 111 | 0.505 | 23 / 57% / +89,992 / 10 | -38,100 | REJECTED: shuffle p=0.505 >= 0.05 |
| S5 pair | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219` | 70 / 56% / +160,768 / 31 | 145 / 111 | 0.740 | 23 / 57% / +89,992 / 10 | -38,100 | REJECTED: shuffle p=0.740 >= 0.05 |
| S6 greedy triple | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219 AND r_wmove60_mv60 < 0.9923` | 59 / 63% / +163,520 / 22 | 156 / 120 | 0.710 | 14 / 57% / +44,356 / 6 | +7,537 | REJECTED: shuffle p=0.710 >= 0.05; holdout removed side is profitable |
| S7 pair maximising kept win rate (kept>=30) | `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4` | 30 / 70% / +224,386 / 9 | 185 / 133 | 0.370 | 13 / 54% / +8,632 / 6 | +43,261 | REJECTED: shuffle p=0.370 >= 0.05; holdout removed side is profitable |
| S8 OR of two clauses | `p_vanna_mv60 >= 0.02028 OR fmv300 < 12.28` | 111 / 48% / +261,349 / 58 | 104 / 84 | 0.400 | 36 / 50% / -699 / 18 | +52,592 | REJECTED: shuffle p=0.400 >= 0.05; holdout removed side is profitable |
| S9 single | `opt_iv_chg5 >= 0.08` | 69 / 49% / +187,704 / 35 | 146 / 107 | 0.735 | 23 / 52% / -3,068 / 11 | +54,961 | REJECTED: shuffle p=0.735 >= 0.05; holdout removed side is profitable |

### Reading

The parent retest book: 291 trades, 36 % winners, Rs +179k over 14 days, but the money is one day (19 Oct, Rs +131k); the other 13 days net Rs +48k with 6 losing days. Nine searches, nothing beats luck: the best shuffle p is 0.40 (OR rule) and the typical single/pair score sits at the shuffle MEDIAN, i.e. exactly what random labels produce over ~400 features. The recurring picks (opt_iv_chg5 >= 0.08 — the contract's own IV rising over 5 min; s_bank_z — Bank Nifty z against our direction; absorb60; fmv300) read sensibly but each removes winners as fast as losers on holdout, and in every case the removed side was PROFITABLE on the last 4 days (Rs +43k to +55k), so the rule would have thrown away money. No rule honestly removes this book's losers. Transfer note: the oi_net_help5 >= 1.06e5 line found on the _first children, applied frozen here, keeps 47 % vs 39 % on holdout (Rs +72k vs -20k) — a mild tilt, not searched here, not proposed here.

**Verdict: NONE**

## spot_dc12_t12_1130

Record — all 14 days: 259 trades, 36% win, mean +0.72 %, Rs +177,401, 165 losers. Discovery: 191 trades, 33% win, mean +0.52 %, Rs +95,020, 128 losers. Holdout: 68 trades, 46% win, mean +1.28 %, Rs +82,381, 37 losers.
Features searched: 195 base, 162 derived, 57 text indicators.

### Best rule (best attempt, rejected) — found by S7 pair maximising kept win rate (kept>=30), all fields, 5 lines

### spot_dc12_t12_1130: `d_mv10_mv60 < -11.15 AND b_imp_with >= 1`

Shuffle test p = 0.220 (does NOT beat luck). Shuffle median 0.667, max 0.750; real score 0.700.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 191 | 33% | +0.5 | +95,020 | 128 |
| discovery | kept | 30 | 70% | +5.4 | +149,968 | 9 |
| discovery | removed | 161 | 26% | -0.4 | -54,948 | 119 |
| holdout | book | 68 | 46% | +1.3 | +82,381 | 37 |
| holdout | kept | 7 | 57% | +3.0 | +18,847 | 3 |
| holdout | removed | 61 | 44% | +1.1 | +63,534 | 34 |
| all | book | 259 | 36% | +0.7 | +177,401 | 165 |
| all | kept | 37 | 68% | +5.0 | +168,815 | 12 |
| all | removed | 222 | 31% | +0.0 | +8,586 | 153 |

Verdict on this rule: **REJECTED** — shuffle p=0.220 >= 0.05; holdout removed side is profitable.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `opt_iv_chg5 >= 0.06` | 59 / 49% / +197,038 / 30 | 132 / 98 | 0.505 | 21 / 62% / +22,578 / 8 | +59,803 | REJECTED: shuffle p=0.505 >= 0.05; holdout removed side is profitable |
| S2 pair | `basis_chg300 < 3.75 AND hw_vol_surge < 0.939` | 66 / 53% / +91,988 / 31 | 125 / 97 | 0.585 | 18 / 39% / -416 / 11 | +82,797 | REJECTED: shuffle p=0.585 >= 0.05; holdout kept win rate below the book's |
| S3 single | `d_mv10_mv60 < -11.15` | 57 / 49% / +149,926 / 29 | 134 / 99 | 0.570 | 14 / 43% / +12,249 / 8 | +70,132 | REJECTED: shuffle p=0.570 >= 0.05; holdout kept win rate below the book's |
| S4 pair | `s_bank_z < 0.37 AND basis_chg300 < 3.75` | 93 / 47% / +151,466 / 49 | 98 / 79 | 0.750 | 20 / 55% / +61,990 / 9 | +20,390 | REJECTED: shuffle p=0.750 >= 0.05; holdout removed side is profitable |
| S5 pair | `round_dist < 52.5 AND vol_ratio_with >= 0.935` | 57 / 60% / +107,754 / 23 | 134 / 105 | 0.340 | 29 / 41% / +23,140 / 17 | +59,241 | REJECTED: shuffle p=0.340 >= 0.05; holdout kept win rate below the book's |
| S6 greedy triple | `s_bank_z < 0.37 AND basis_chg300 < 3.75 AND r_gexwall_ahead_behind < 4.376` | 81 / 53% / +161,359 / 38 | 110 / 90 | 0.500 | 19 / 53% / +60,950 / 9 | +21,430 | REJECTED: shuffle p=0.500 >= 0.05; holdout removed side is profitable |
| S7 pair maximising kept win rate (kept>=30) | `d_mv10_mv60 < -11.15 AND b_imp_with >= 1` | 30 / 70% / +149,968 / 9 | 161 / 119 | 0.220 | 7 / 57% / +18,847 / 3 | +63,534 | REJECTED: shuffle p=0.220 >= 0.05; holdout removed side is profitable |
| S8 OR of two clauses | `opt_iv_chg5 >= 0.06 OR wmove60_it >= 1.24` | 73 / 52% / +242,245 / 35 | 118 / 93 | 0.560 | 22 / 64% / +31,886 / 8 | +50,495 | REJECTED: shuffle p=0.560 >= 0.05; holdout removed side is profitable |
| S9 single | `opt_iv_chg5 >= 0.06` | 59 / 49% / +197,038 / 30 | 132 / 98 | 0.815 | 21 / 62% / +22,578 / 8 | +59,803 | REJECTED: shuffle p=0.815 >= 0.05; holdout removed side is profitable |

### Reading

Same trades as the parent after 11:30 only (259 trades, Rs +177k). Discovery win rate is 33 %, holdout 46 % — the book itself got better in the last 4 days for reasons no photo field explains. No search beats luck (best p 0.22, the win-rate pair with 30 kept). Every candidate's removed side is profitable on holdout (Rs +20k to +83k): cutting any of them would have cost money. Verdict NONE.

**Verdict: NONE**

## spot_dc12_t12_nolock

Record — all 14 days: 291 trades, 36% win, mean +0.77 %, Rs +208,439, 185 losers. Discovery: 215 trades, 34% win, mean +0.81 %, Rs +156,367, 142 losers. Holdout: 76 trades, 43% win, mean +0.68 %, Rs +52,072, 43 losers.
Features searched: 195 base, 162 derived, 61 text indicators.

### Best rule (best attempt, rejected) — found by S7 pair maximising kept win rate (kept>=30), all fields, 5 lines

### spot_dc12_t12_nolock: `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4`

Shuffle test p = 0.370 (does NOT beat luck). Shuffle median 0.687, max 0.788; real score 0.700.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 215 | 34% | +0.8 | +156,367 | 142 |
| discovery | kept | 30 | 70% | +8.2 | +276,305 | 9 |
| discovery | removed | 185 | 28% | -0.4 | -119,938 | 133 |
| holdout | book | 76 | 43% | +0.7 | +52,072 | 43 |
| holdout | kept | 13 | 54% | +0.8 | +9,224 | 6 |
| holdout | removed | 63 | 41% | +0.6 | +42,848 | 37 |
| all | book | 291 | 36% | +0.8 | +208,439 | 185 |
| all | kept | 43 | 65% | +5.9 | +285,529 | 15 |
| all | removed | 248 | 31% | -0.1 | -77,090 | 170 |

Verdict on this rule: **REJECTED** — shuffle p=0.370 >= 0.05; holdout removed side is profitable.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `opt_iv_chg5 >= 0.08` | 69 / 49% / +224,838 / 35 | 146 / 107 | 0.410 | 23 / 52% / -2,476 / 11 | +54,548 | REJECTED: shuffle p=0.410 >= 0.05; holdout removed side is profitable |
| S2 pair | `absorb60 < 3.46e+07 AND fmv300 < 18.4` | 58 / 59% / +389,555 / 24 | 157 / 118 | 0.540 | 16 / 38% / -1,911 / 10 | +53,982 | REJECTED: shuffle p=0.540 >= 0.05; holdout kept win rate below the book's |
| S3 single | `s_bank_z < 0.478` | 150 / 41% / +237,981 / 89 | 65 / 53 | 0.510 | 42 / 50% / +71,770 / 21 | -19,698 | REJECTED: shuffle p=0.510 >= 0.05 |
| S4 pair | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219` | 70 / 56% / +153,654 / 31 | 145 / 111 | 0.505 | 23 / 57% / +90,584 / 10 | -38,512 | REJECTED: shuffle p=0.505 >= 0.05 |
| S5 pair | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219` | 70 / 56% / +153,654 / 31 | 145 / 111 | 0.740 | 23 / 57% / +90,584 / 10 | -38,512 | REJECTED: shuffle p=0.740 >= 0.05 |
| S6 greedy triple | `s_bank_z < 0.478 AND vol_ratio_with >= 1.219 AND r_wmove60_mv60 < 0.9923` | 59 / 63% / +156,406 / 22 | 156 / 120 | 0.715 | 14 / 57% / +44,356 / 6 | +7,716 | REJECTED: shuffle p=0.715 >= 0.05; holdout removed side is profitable |
| S7 pair maximising kept win rate (kept>=30) | `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4` | 30 / 70% / +276,305 / 9 | 185 / 133 | 0.370 | 13 / 54% / +9,224 / 6 | +42,848 | REJECTED: shuffle p=0.370 >= 0.05; holdout removed side is profitable |
| S8 OR of two clauses | `fmv300 < 12.28 OR p_vanna_mv60 >= 0.02028` | 111 / 48% / +304,518 / 58 | 104 / 84 | 0.400 | 36 / 50% / -1,112 / 18 | +53,183 | REJECTED: shuffle p=0.400 >= 0.05; holdout removed side is profitable |
| S9 single | `opt_iv_chg5 >= 0.08` | 69 / 49% / +224,838 / 35 | 146 / 107 | 0.735 | 23 / 52% / -2,476 / 11 | +54,548 | REJECTED: shuffle p=0.735 >= 0.05; holdout removed side is profitable |

### Reading

Same entries as the parent without the +18 % lock (291 trades, Rs +208k). The photographs are identical to the parent's, so the searches find the same clauses with the same p (0.40-0.74); only the rupees differ. Nothing beats luck; the removed sides are profitable on holdout. Verdict NONE.

**Verdict: NONE**

## spot_dc12_t12_r002

Record — all 14 days: 60 trades, 45% win, mean +1.69 %, Rs +116,304, 33 losers. Discovery: 44 trades, 48% win, mean +3.20 %, Rs +150,283, 23 losers. Holdout: 16 trades, 38% win, mean -2.47 %, Rs -33,979, 10 losers.
Features searched: 193 base, 161 derived, 54 text indicators.

### Best rule (PROPOSED) — found by S5 pair, all fields, 9 lines, top 1500 masks

### spot_dc12_t12_r002: `opt_lead < 0.0668 AND abs_e_fut_ofi60 >= 4.066`

Shuffle test p = 0.025 (beats luck). Shuffle median 0.640, max 0.822; real score 0.739.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 44 | 48% | +3.2 | +150,283 | 23 |
| discovery | kept | 27 | 78% | +9.1 | +318,084 | 6 |
| discovery | removed | 17 | 0% | -6.1 | -167,801 | 17 |
| holdout | book | 16 | 38% | -2.5 | -33,979 | 10 |
| holdout | kept | 8 | 50% | -2.1 | -15,730 | 4 |
| holdout | removed | 8 | 25% | -2.8 | -18,249 | 6 |
| all | book | 60 | 45% | +1.7 | +116,304 | 33 |
| all | kept | 35 | 71% | +6.5 | +302,354 | 10 |
| all | removed | 25 | 8% | -5.1 | -186,050 | 23 |

Verdict on this rule: **PROPOSE** — WEAK: passes 2-4 by the letter but the kept side LOST rupees on holdout.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `absorb60 < 2.97e+07` | 22 / 73% / +250,256 / 6 | 22 / 17 | 0.210 | 7 / 43% / -12,880 / 4 | -21,099 | REJECTED: shuffle p=0.210 >= 0.05 |
| S2 pair | `absorb60 < 2.97e+07 AND ret_today < 92.58` | 20 / 80% / +271,534 / 4 | 24 / 19 | 0.680 | 7 / 43% / -12,880 / 4 | -21,099 | REJECTED: shuffle p=0.680 >= 0.05 |
| S3 single | `abs_wmove60 >= 2.175` | 31 / 65% / +240,107 / 11 | 13 / 12 | 0.205 | 12 / 42% / -25,074 / 7 | -8,905 | REJECTED: shuffle p=0.205 >= 0.05 |
| S4 pair | `abs_wmove60 >= 2.175 AND opt_lead < 0.0561` | 21 / 81% / +259,448 / 4 | 23 / 19 | 0.410 | 8 / 50% / -15,730 / 4 | -18,249 | REJECTED: shuffle p=0.410 >= 0.05 |
| S5 pair | `opt_lead < 0.0668 AND abs_e_fut_ofi60 >= 4.066` | 27 / 78% / +318,084 / 6 | 17 / 17 | 0.025 | 8 / 50% / -15,730 / 4 | -18,249 | PROPOSE: WEAK: passes 2-4 by the letter but the kept side LOST rupees on holdout |
| S6 greedy triple | `abs_wmove60 >= 2.175 AND opt_lead < 0.0561 AND rest_opp_rs >= 1.477e+06` | 20 / 85% / +277,648 / 3 | 24 / 20 | 0.800 | 8 / 50% / -15,730 / 4 | -18,249 | REJECTED: shuffle p=0.800 >= 0.05 |
| S7 pair maximising kept win rate (kept>=30) | `abs_wmove60 >= 2.175 AND r_fmv60_mv60 >= 0.3171` | 30 / 67% / +244,371 / 10 | 14 / 13 | 0.325 | 12 / 42% / -25,074 / 7 | -8,905 | REJECTED: shuffle p=0.325 >= 0.05 |
| S8 OR of two clauses | `absorb60 < 2.97e+07 OR p_mv60_wmove60 >= 18.66` | 32 / 66% / +258,336 / 11 | 12 / 12 | 0.605 | 12 / 42% / -25,074 / 7 | -8,905 | REJECTED: shuffle p=0.605 >= 0.05 |
| S9 single | `p_mv60_wmove60 >= 12.59` | 26 / 69% / +240,087 / 8 | 18 / 15 | 0.250 | 12 / 42% / -25,074 / 7 | -8,905 | REJECTED: shuffle p=0.250 >= 0.05 |

### Reading

The parent gated by R-002 (er60): 60 trades on 8 days, 44 in discovery — thin. Its discovery record is flattered by 19 Oct (Rs +131k of +150k); holdout is a loser (16 trades, 38 % win, Rs -34k). Search S5 (pairs, 9 lines, all fields) returns opt_lead < 0.0668 AND abs_e_fut_ofi60 >= 4.066 with p = 0.025 — the only sub-0.05 p among nine searches on this book, which with nine tries is roughly what chance gives about a third of the time. On holdout its kept side has 8 trades, wins 50 % (book 38 %) and LOSES Rs 15.7k (mean -2.1 %); the removed side also loses, so it passes rules 2-4 by the letter and is marked PROPOSE-WEAK. My reading: do not register it. 44 discovery trades cannot support a two-clause rule with lines chosen from 9 quantiles over ~400 features; the holdout kept side lost money; and the same clauses at 5 lines (S4) had p = 0.41. Honest verdict: passes the written standard, fails common sense — treat as NONE in practice.

**Verdict: PROPOSE**

## spot_dc12_t12_first

Record — all 14 days: 603 trades, 38% win, mean +0.18 %, Rs +110,536, 371 losers. Discovery: 436 trades, 38% win, mean +0.25 %, Rs +105,297, 272 losers. Holdout: 167 trades, 41% win, mean +0.00 %, Rs +5,239, 99 losers.
Features searched: 195 base, 162 derived, 59 text indicators.

### Best rule (PROPOSED) — found by S1 single, base fields, 5 lines

### spot_dc12_t12_first: `oi_net_help5 >= 1.059e+05`

Shuffle test p = 0.020 (beats luck). Shuffle median 0.147, max 0.205; real score 0.189.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 436 | 38% | +0.2 | +105,297 | 272 |
| discovery | kept | 217 | 47% | +1.4 | +279,971 | 116 |
| discovery | removed | 219 | 29% | -0.9 | -174,674 | 156 |
| holdout | book | 167 | 41% | +0.0 | +5,239 | 99 |
| holdout | kept | 84 | 42% | +0.2 | +27,901 | 49 |
| holdout | removed | 83 | 40% | -0.2 | -22,662 | 50 |
| all | book | 603 | 38% | +0.2 | +110,536 | 371 |
| all | kept | 301 | 45% | +1.1 | +307,872 | 165 |
| all | removed | 302 | 32% | -0.7 | -197,337 | 206 |

Verdict on this rule: **PROPOSE** — passes 2-4.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `oi_net_help5 >= 1.059e+05` | 217 / 47% / +279,971 / 116 | 219 / 156 | 0.020 | 84 / 42% / +27,901 / 49 | -22,662 | PROPOSE: passes 2-4 |
| S2 pair | `oi_net_help5 >= 1.059e+05 AND fut_imb_t_chg30 >= -0.0106` | 195 / 50% / +295,236 / 98 | 241 / 174 | 0.075 | 79 / 42% / +32,994 / 46 | -27,755 | REJECTED: shuffle p=0.075 >= 0.05 |
| S3 single | `rk_spread_pct < 0.2857` | 121 / 52% / +153,624 / 58 | 315 / 214 | 0.100 | 52 / 46% / +76,180 / 28 | -70,941 | REJECTED: shuffle p=0.100 >= 0.05 |
| S4 pair | `z_spread_pct < 0.6033 AND new_highs < 98` | 180 / 51% / +241,140 / 88 | 256 / 184 | 0.105 | 21 / 38% / -7,319 / 13 | +12,558 | REJECTED: shuffle p=0.105 >= 0.05; holdout kept win rate below the book's |
| S5 pair | `rk_spread_pct < 0.5789 AND new_highs < 98` | 152 / 55% / +232,749 / 69 | 284 / 203 | 0.080 | 19 / 42% / +5,408 / 11 | -169 | REJECTED: shuffle p=0.080 >= 0.05 |
| S6 greedy triple | `z_spread_pct < 0.6033 AND new_highs < 98 AND fut_imb_t_chg30 >= -0.0106` | 163 / 55% / +289,302 / 74 | 273 / 198 | 0.130 | 17 / 41% / +1,235 / 10 | +4,004 | REJECTED: shuffle p=0.130 >= 0.05; holdout removed side is profitable |
| S7 pair maximising kept win rate (kept>=30) | `rk_spread_pct < 0.2857 AND s_basis_chg60 < -1.625` | 38 / 76% / +202,156 / 9 | 398 / 263 | 0.190 | 17 / 65% / +28,372 / 6 | -23,134 | REJECTED: shuffle p=0.190 >= 0.05 |
| S8 OR of two clauses | `z_spread_pct < -0.3837 OR sl_room_up_pct >= 1.45` | 262 / 47% / +252,518 / 138 | 174 / 134 | 0.065 | 108 / 42% / +38,665 / 63 | -33,426 | REJECTED: shuffle p=0.065 >= 0.05 |
| S9 single | `oi_net_help5 >= 1.059e+05` | 217 / 47% / +279,971 / 116 | 219 / 156 | 0.090 | 84 / 42% / +27,901 / 49 | -22,662 | REJECTED: shuffle p=0.090 >= 0.05 |

### Reading

First retest only (603 trades, Rs +111k; 38 % winners; 7 losing days of 14). One rule passes: oi_net_help5 >= 1.06e5 — option writers added at least ~Rs 1.06 lakh of OI on the side that helps us over the last 5 minutes. Found by S1 (single clause, 195 base fields x 5 lines), p = 0.020. Discovery: keeps 217 of 436, win 47 % vs 29 % removed, Rs +280k vs -175k; kept side beat removed side on 8 of 10 days. Holdout: kept 84, win 41.7 % vs book 40.7 % and removed 39.8 %, Rs +27.9k vs -22.7k; but kept beat removed on only 2 of the 4 days (3 and 4 Nov went the other way). The quintile gradient is clean on discovery (25/36/34/47/46 %) and muddled on holdout (35/47/38/47/37 %). The same clause found by the wider S9 search (all fields, 9 lines) has p = 0.09 — it does not survive the wider bar. Every 2- and 3-clause extension, the OR form and the win-rate objective FAIL the shuffle test (p 0.065-0.19) although they look better on discovery (55-76 % kept win): the extra clauses are memory of the tape. Reading: a real but small tilt — it halves the book and lifts the kept win rate by ~1 point out of sample. It does not come close to 'removing losses'; the kept side still carries 116 losers on discovery and 49 on holdout. PROPOSE by the standard, with that caveat stated.

**Verdict: PROPOSE**

## spot_dc12_t12_first_r002

Record — all 14 days: 131 trades, 44% win, mean +1.17 %, Rs +189,806, 74 losers. Discovery: 91 trades, 43% win, mean +1.80 %, Rs +184,132, 52 losers. Holdout: 40 trades, 45% win, mean -0.25 %, Rs +5,674, 22 losers.
Features searched: 194 base, 162 derived, 57 text indicators.

### Best rule (best attempt, rejected) — found by S3 single, derived fields (ratios/diffs/products/signed/z/bool), 5 lines

### spot_dc12_t12_first_r002: `rk_spread_pct < 1`

Shuffle test p = 0.090 (does NOT beat luck). Shuffle median 0.301, max 0.423; real score 0.359.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 91 | 43% | +1.8 | +184,132 | 52 |
| discovery | kept | 56 | 57% | +4.1 | +269,867 | 24 |
| discovery | removed | 35 | 20% | -2.0 | -85,735 | 28 |
| holdout | book | 40 | 45% | -0.2 | +5,674 | 22 |
| holdout | kept | 28 | 43% | -0.9 | -21,096 | 16 |
| holdout | removed | 12 | 50% | +1.3 | +26,770 | 6 |
| all | book | 131 | 44% | +1.2 | +189,806 | 74 |
| all | kept | 84 | 52% | +2.5 | +248,771 | 40 |
| all | removed | 47 | 28% | -1.1 | -58,965 | 34 |

Verdict on this rule: **REJECTED** — shuffle p=0.090 >= 0.05; holdout kept win rate below the book's.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `agree_same >= 2` | 66 / 53% / +261,258 / 31 | 25 / 21 | 0.550 | 31 / 39% / -49,507 / 19 | +55,182 | REJECTED: shuffle p=0.550 >= 0.05; holdout kept win rate below the book's |
| S2 pair | `quote_age >= 0.21 AND e_basis_dev < 2.45` | 42 / 67% / +256,354 / 14 | 49 / 38 | 0.375 | 17 / 35% / -5,168 / 11 | +10,842 | REJECTED: shuffle p=0.375 >= 0.05; holdout kept win rate below the book's |
| S3 single | `rk_spread_pct < 1` | 56 / 57% / +269,867 / 24 | 35 / 28 | 0.090 | 28 / 43% / -21,096 / 16 | +26,770 | REJECTED: shuffle p=0.090 >= 0.05; holdout kept win rate below the book's |
| S4 pair | `rk_spread_pct < 1 AND agree_same >= 2` | 47 / 66% / +322,319 / 16 | 44 / 36 | 0.180 | 24 / 42% / -26,351 / 14 | +32,026 | REJECTED: shuffle p=0.180 >= 0.05; holdout kept win rate below the book's |
| S5 pair | `rk_spread_pct < 1 AND agree_same >= 2` | 47 / 66% / +322,319 / 16 | 44 / 36 | 0.340 | 24 / 42% / -26,351 / 14 | +32,026 | REJECTED: shuffle p=0.340 >= 0.05; holdout kept win rate below the book's |
| S6 greedy triple | `rk_spread_pct < 1 AND agree_same >= 2 AND r_vix_rv15 < 1.934` | 39 / 74% / +300,098 / 10 | 52 / 42 | 0.205 | 22 / 41% / -17,300 / 13 | +22,974 | REJECTED: shuffle p=0.205 >= 0.05; holdout kept win rate below the book's |
| S7 pair maximising kept win rate (kept>=30) | `rk_spread_pct < 1 AND accel30 >= 3` | 31 / 74% / +337,893 / 8 | 60 / 44 | 0.365 | 13 / 38% / -31,457 / 8 | +37,131 | REJECTED: shuffle p=0.365 >= 0.05; holdout kept win rate below the book's |
| S8 OR of two clauses | `rk_spread_pct < 1 OR s_accel15 >= 2.13` | 64 / 58% / +297,570 / 27 | 27 / 25 | 0.670 | 32 / 44% / -13,023 / 18 | +18,697 | REJECTED: shuffle p=0.670 >= 0.05; holdout kept win rate below the book's |
| S9 single | `rk_spread_pct < 1` | 56 / 57% / +269,867 / 24 | 35 / 28 | 0.275 | 28 / 43% / -21,096 / 16 | +26,770 | REJECTED: shuffle p=0.275 >= 0.05; holdout kept win rate below the book's |

### Reading

First retest gated by R-002: 131 trades, 91 in discovery, concentrated on three days (19 Oct, 27 Oct, 3 Nov carry 104 of 131). Nothing beats luck (best p 0.09, rk_spread_pct < 1 — the spread is not the day's widest so far). On holdout the kept side of every candidate wins LESS than the book and the removed side is profitable. The rupees in discovery (Rs +184k) are two days. Verdict NONE.

**Verdict: NONE**

## spot_dc12_t12_first_r003

Record — all 14 days: 577 trades, 37% win, mean +0.15 %, Rs +37,284, 361 losers. Discovery: 418 trades, 37% win, mean +0.21 %, Rs +52,770, 262 losers. Holdout: 159 trades, 38% win, mean -0.01 %, Rs -15,486, 99 losers.
Features searched: 195 base, 162 derived, 60 text indicators.

### Best rule (PROPOSED) — found by S1 single, base fields, 5 lines

### spot_dc12_t12_first_r003: `oi_net_help5 >= 1.283e+05`

Shuffle test p = 0.005 (beats luck). Shuffle median 0.148, max 0.215; real score 0.198.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 418 | 37% | +0.2 | +52,770 | 262 |
| discovery | kept | 208 | 47% | +1.4 | +245,498 | 111 |
| discovery | removed | 210 | 28% | -1.0 | -192,728 | 151 |
| holdout | book | 159 | 38% | -0.0 | -15,486 | 99 |
| holdout | kept | 79 | 38% | +0.2 | +13,419 | 49 |
| holdout | removed | 80 | 38% | -0.2 | -28,906 | 50 |
| all | book | 577 | 37% | +0.1 | +37,284 | 361 |
| all | kept | 287 | 44% | +1.1 | +258,918 | 160 |
| all | removed | 290 | 31% | -0.8 | -221,634 | 201 |

Verdict on this rule: **PROPOSE** — passes 2-4.

### Every search (one line each)

| search | rule | disc kept n / win / Rs / losers | removed n / losers | p | hold kept n / win / Rs / losers | hold removed Rs | verdict |
|---|---|---|---|---|---|---|---|
| S1 single | `oi_net_help5 >= 1.283e+05` | 208 / 47% / +245,498 / 111 | 210 / 151 | 0.005 | 79 / 38% / +13,419 / 49 | -28,906 | PROPOSE: passes 2-4 |
| S2 pair | `oi_net_help5 >= 1.283e+05 AND fmv60 >= 2.582` | 192 / 49% / +297,382 / 98 | 226 / 164 | 0.150 | 69 / 36% / +28,636 / 44 | -44,122 | REJECTED: shuffle p=0.150 >= 0.05; holdout kept win rate below the book's |
| S3 single | `rk_mv60 >= 0.2312` | 271 / 43% / +194,266 / 154 | 147 / 108 | 0.155 | 100 / 35% / -36,858 / 65 | +21,372 | REJECTED: shuffle p=0.155 >= 0.05; holdout kept win rate below the book's |
| S4 pair | `oi_net_help5 >= 1.283e+05 AND s_fut_imb_o < 0.412` | 179 / 50% / +282,730 / 89 | 239 / 173 | 0.165 | 69 / 39% / +1,144 / 42 | -16,630 | REJECTED: shuffle p=0.165 >= 0.05 |
| S5 pair | `oi_net_help5 >= 1.283e+05 AND r_fmv60_mv60 >= 0.8724` | 170 / 52% / +338,760 / 82 | 248 / 180 | 0.110 | 58 / 34% / +36,420 / 38 | -51,906 | REJECTED: shuffle p=0.110 >= 0.05; holdout kept win rate below the book's |
| S6 greedy triple | `oi_net_help5 >= 1.283e+05 AND s_fut_imb_o < 0.412 AND fmv60 >= 2.582` | 163 / 53% / +334,614 / 76 | 255 / 186 | 0.260 | 59 / 37% / +16,360 / 37 | -31,847 | REJECTED: shuffle p=0.260 >= 0.05; holdout kept win rate below the book's |
| S7 pair maximising kept win rate (kept>=30) | `s_e_fut_ofi60 < -16.06 AND gaps_today < 6` | 32 / 75% / +106,291 / 8 | 386 / 254 | 0.265 | 2 / 0% / -5,626 / 2 | -9,860 | REJECTED: shuffle p=0.265 >= 0.05; holdout kept win rate below the book's |
| S8 OR of two clauses | `oi_net_help5 >= 1.283e+05 OR z_e_fut_ofi60 >= 0.3696` | 268 / 46% / +267,777 / 144 | 150 / 118 | 0.105 | 104 / 38% / -1,150 / 65 | -14,336 | REJECTED: shuffle p=0.105 >= 0.05; holdout kept win rate below the book's |
| S9 single | `oi_net_help5 >= 1.283e+05` | 208 / 47% / +245,498 / 111 | 210 / 151 | 0.020 | 79 / 38% / +13,419 / 49 | -28,906 | PROPOSE: passes 2-4 |

### Reading

First retest gated by R-003 breadth: 577 trades, Rs +37k over 14 days, 37 % winners, holdout a small loser (Rs -15k). Same single clause as _first: oi_net_help5 >= 1.28e5, p = 0.005 (S1) and p = 0.020 (S9, the wider search) — the strongest shuffle result in the family and it holds at the wider bar. Discovery: kept 208 of 418, win 47 % vs 28 %, Rs +245k vs -193k. Holdout: kept 79, win 38.0 % vs book 37.7 % and removed 37.5 %; Rs +13.4k vs -28.9k. The holdout win-rate edge is 0.3 of a point — essentially nil; the rupee edge is real but small. Every multi-clause extension fails the shuffle (p 0.11-0.27) and on holdout their kept sides win LESS than the book. Note _first and _first_r003 share ~95 % of their trades, so this is the same evidence seen twice, not a second confirmation. PROPOSE by the standard; honestly, a modest P&L tilt that halves the trade count and barely moves the win rate out of sample.

**Verdict: PROPOSE**

## Cross-check: the one surviving clause (oi_net_help5) applied FROZEN to every book, quintiles, day by day

No search was run here (fixed rule, so no shuffle is needed). Output of the cross-check script:

```
spot_dc12_t12                oi_net_help5>=1.06e+05: disc kept 104 win 38% Rs +192,166 | removed 111 win 30% Rs -64,685 || hold book win 43%; kept 45 win 47% Rs +72,078 | removed 31 win 39% Rs -20,186
spot_dc12_t12                oi_net_help5>=1.28e+05: disc kept 102 win 39% Rs +196,144 | removed 113 win 29% Rs -68,663 || hold book win 43%; kept 45 win 47% Rs +72,078 | removed 31 win 39% Rs -20,186
spot_dc12_t12_1130           oi_net_help5>=1.06e+05: disc kept 92 win 38% Rs +159,542 | removed 99 win 28% Rs -64,522 || hold book win 46%; kept 37 win 51% Rs +102,567 | removed 31 win 39% Rs -20,186
spot_dc12_t12_1130           oi_net_help5>=1.28e+05: disc kept 90 win 39% Rs +163,520 | removed 101 win 28% Rs -68,500 || hold book win 46%; kept 37 win 51% Rs +102,567 | removed 31 win 39% Rs -20,186
spot_dc12_t12_nolock         oi_net_help5>=1.06e+05: disc kept 104 win 38% Rs +237,530 | removed 111 win 30% Rs -81,162 || hold book win 43%; kept 45 win 47% Rs +72,257 | removed 31 win 39% Rs -20,186
spot_dc12_t12_nolock         oi_net_help5>=1.28e+05: disc kept 102 win 39% Rs +241,508 | removed 113 win 29% Rs -85,140 || hold book win 43%; kept 45 win 47% Rs +72,257 | removed 31 win 39% Rs -20,186
spot_dc12_t12_r002           oi_net_help5>=1.06e+05: disc kept 24 win 54% Rs +104,572 | removed 20 win 40% Rs +45,711 || hold book win 38%; kept 13 win 46% Rs -20,803 | removed 3 win 0% Rs -13,176
spot_dc12_t12_r002           oi_net_help5>=1.28e+05: disc kept 24 win 54% Rs +104,572 | removed 20 win 40% Rs +45,711 || hold book win 38%; kept 13 win 46% Rs -20,803 | removed 3 win 0% Rs -13,176
spot_dc12_t12_first          oi_net_help5>=1.06e+05: disc kept 217 win 47% Rs +279,971 | removed 219 win 29% Rs -174,674 || hold book win 41%; kept 84 win 42% Rs +27,901 | removed 83 win 40% Rs -22,662
spot_dc12_t12_first          oi_net_help5>=1.28e+05: disc kept 216 win 47% Rs +281,808 | removed 220 win 29% Rs -176,511 || hold book win 41%; kept 83 win 42% Rs +30,807 | removed 84 win 39% Rs -25,568
spot_dc12_t12_first_r002     oi_net_help5>=1.06e+05: disc kept 59 win 46% Rs +125,288 | removed 32 win 38% Rs +58,844 || hold book win 45%; kept 22 win 45% Rs +14,232 | removed 18 win 44% Rs -8,557
spot_dc12_t12_first_r002     oi_net_help5>=1.28e+05: disc kept 59 win 46% Rs +125,288 | removed 32 win 38% Rs +58,844 || hold book win 45%; kept 22 win 45% Rs +14,232 | removed 18 win 44% Rs -8,557
spot_dc12_t12_first_r003     oi_net_help5>=1.06e+05: disc kept 210 win 46% Rs +242,118 | removed 208 win 28% Rs -189,348 || hold book win 38%; kept 80 win 38% Rs +10,998 | removed 79 win 38% Rs -26,484
spot_dc12_t12_first_r003     oi_net_help5>=1.28e+05: disc kept 208 win 47% Rs +245,498 | removed 210 win 28% Rs -192,728 || hold book win 38%; kept 79 win 38% Rs +13,419 | removed 80 win 38% Rs -28,906

spot_dc12_t12_first: quintiles of oi_net_help5 (edges from discovery): ['-9.44e+06', '-1.06e+06', '-2.02e+05', '4.13e+05', '1.55e+06', '2.27e+07']
  disc: Q1 n=87 win=25% mean=-1.66 | Q2 n=87 win=36% mean=-0.09 | Q3 n=86 win=34% mean=-0.66 | Q4 n=87 win=47% mean=+1.47 | Q5 n=87 win=46% mean=+2.08
  hold: Q1 n=34 win=35% mean=-0.14 | Q2 n=32 win=47% mean=+0.56 | Q3 n=29 win=38% mean=-1.13 | Q4 n=34 win=47% mean=+2.01 | Q5 n=38 win=37% mean=-1.28
  day-by-day kept win - removed win (rule >= 1.059e5):
    2026-10-19 kept 19 win 58% Rs +17,251 | removed 13 win 38% Rs +72,910
    2026-10-21 kept 29 win 34% Rs -19,929 | removed 25 win 40% Rs -4,352
    2026-10-22 kept 27 win 41% Rs +12,948 | removed 25 win 40% Rs -11,505
    2026-10-23 kept 24 win 42% Rs +31,886 | removed 19 win 32% Rs -23,078
    2026-10-26 kept 19 win 47% Rs +43,527 | removed 32 win 22% Rs -57,840
    2026-10-27 kept 22 win 50% Rs +122,844 | removed 16 win 44% Rs -6,682
    2026-10-28 kept 25 win 60% Rs +19,607 | removed 16 win 31% Rs -16,175
    2026-10-29 kept 15 win 47% Rs +6,669 | removed 28 win 14% Rs -33,976
    2026-10-30 kept 16 win 50% Rs +6,149 | removed 28 win 21% Rs -49,758
    2026-11-02 kept 21 win 43% Rs +39,020 | removed 17 win 18% Rs -44,220
    2026-11-03 kept 16 win 31% Rs -47,330 | removed 18 win 44% Rs -8,557
    2026-11-04 kept 21 win 33% Rs -5,928 | removed 23 win 43% Rs +5,704
    2026-11-05 kept 18 win 50% Rs +28,568 | removed 24 win 38% Rs +598
    2026-11-06 kept 29 win 48% Rs +52,592 | removed 18 win 33% Rs -20,407

spot_dc12_t12: quintiles of oi_net_help5 (edges from discovery): ['-8.02e+06', '-1.21e+06', '-4.02e+05', '4.63e+05', '1.86e+06', '2.44e+07']
  disc: Q1 n=43 win=23% mean=-0.92 | Q2 n=43 win=28% mean=-0.69 | Q3 n=42 win=36% mean=-0.12 | Q4 n=43 win=37% mean=+2.17 | Q5 n=43 win=44% mean=+2.58
  hold: Q1 n=8 win=38% mean=-1.21 | Q2 n=13 win=46% mean=+0.14 | Q3 n=17 win=29% mean=-0.73 | Q4 n=15 win=53% mean=+5.56 | Q5 n=23 win=48% mean=-0.54
  day-by-day kept win - removed win (rule >= 1.059e5):
    2026-10-19 kept 8 win 62% Rs +86,590 | removed 9 win 44% Rs +44,603
    2026-10-21 kept 14 win 29% Rs +1,762 | removed 8 win 38% Rs -3,643
    2026-10-22 kept 10 win 40% Rs -8,531 | removed 17 win 29% Rs -15,987
    2026-10-23 kept 11 win 36% Rs +46,303 | removed 9 win 33% Rs -4,755
    2026-10-26 kept 9 win 44% Rs +60,898 | removed 13 win 31% Rs -39,006
    2026-10-27 kept 11 win 45% Rs -3,354 | removed 9 win 44% Rs +6,984
    2026-10-28 kept 13 win 38% Rs +14,212 | removed 13 win 23% Rs -14,300
    2026-10-29 kept 7 win 14% Rs -11,115 | removed 9 win 44% Rs +13,318
    2026-10-30 kept 10 win 40% Rs +663 | removed 13 win 15% Rs -25,126
    2026-11-02 kept 11 win 36% Rs +4,738 | removed 11 win 9% Rs -26,774
    2026-11-03 kept 11 win 45% Rs -22,935 | removed 3 win 0% Rs -13,176
    2026-11-04 kept 11 win 36% Rs +8,190 | removed 9 win 67% Rs +12,753
    2026-11-05 kept 9 win 33% Rs +21,109 | removed 9 win 22% Rs -3,998
    2026-11-06 kept 14 win 64% Rs +65,715 | removed 10 win 40% Rs -15,766
```

## What was tried and failed (family-wide)

* Pairs, greedy triples, OR-of-two and the kept-win-rate objective all score far better on discovery (kept win 55-85 %) and ALL fail the shuffle test on every book: with ~400 features x 5-9 lines, random labels produce the same scores (the shuffle medians equal the real scores).
* Derived mathematics (ratios mv/rv, premium/theta_be15, gamma x mv, er60-er30, breadth-0.5, direction-signed flow fields, within-day z-scores and ranks, time buckets, booleans, the prior exited trades' win share today) produced the best single clause on 4 of 7 books (abs_wmove60, rk_spread_pct, d_mv10_mv60, s_bank_z, rk_mv60) and none beat luck (p 0.09-0.57).
* opt_iv_chg5 >= 0.08 (parent, _1130, _nolock) and rk_spread_pct < 1 (the R-002 children) recur as the best single clause across sibling books, but siblings share the same photographs so recurrence is not confirmation; both have p >= 0.09 and profitable removed sides on holdout.
* Fitted-model fields (hmm_*, hk_*) were excluded by the toolkit as the brief requires.

## Verdicts

| book | verdict | best rule | p |
|---|---|---|---|
| spot_dc12_t12 | NONE | `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4` | 0.370 |
| spot_dc12_t12_1130 | NONE | `d_mv10_mv60 < -11.15 AND b_imp_with >= 1` | 0.220 |
| spot_dc12_t12_nolock | NONE | `opt_iv_chg5 >= 0.08 AND fmv300 < 18.4` | 0.370 |
| spot_dc12_t12_r002 | PROPOSE | `opt_lead < 0.0668 AND abs_e_fut_ofi60 >= 4.066` | 0.025 |
| spot_dc12_t12_first | PROPOSE | `oi_net_help5 >= 1.059e+05` | 0.020 |
| spot_dc12_t12_first_r002 | NONE | `rk_spread_pct < 1` | 0.090 |
| spot_dc12_t12_first_r003 | PROPOSE | `oi_net_help5 >= 1.283e+05` | 0.005 |