# Agent 6 — lvl_trail family: rule search report (8 Nov 2026)

Books: lvl_trail, lvl_trail_be, lvl_trail_re, lvl_trail_rx, lvl_trail_rx_be, lvl_trail_rx_c10 (one level-trail
family: the six books share ~95 of ~100 trades; only the exit variant differs). Data: 14 replayed days, discovery =
first 10 (19 Oct - 2 Nov), holdout = last 4 (3 - 6 Nov). Search script: `s1_search.py` (this folder); every search
was re-run on 200 shufflings of the discovery labels with the same function (`rule_lab.shuffle_p`).

Feature pool per book: ~195 raw numeric weather fields + 88 derived (direction-signed moves, ratios, products,
differences, within-day z-scores/ranks from the book's earlier trades that day, time buckets) + ~62 text
indicators (`field=VALUE`). Fitted-model fields (hmm_*, hk_*) excluded. Searches: single clause on raw / hand-picked
24 / derived-only / text-only / all / all at 9 lines / all with >=30 kept; pair (AND) on raw / hand / all; greedy
triple on all; OR-of-two on all. Lines = quantiles 0.1..0.9 of each feature on discovery.

## lvl_trail

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 81 | 51% | +3.3 | +287,209 | 40 |
| holdout | 24 | 38% | -0.5 | -12,230 | 15 |
| all | 105 | 48% | +2.4 | +274,979 | 55 |

### Best rule found (search `triple_all`, 345 features, params default)

### lvl_trail: `fut_spread >= 2.6 AND imp_depth_with < 0.5124 AND ret_today < 83.4`

Shuffle test p = 0.235 (does NOT beat luck). Shuffle median best score 0.535, max 0.657, real 0.579.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 81 | 51% | +3.3 | +287,209 | 40 |
| discovery | kept | 44 | 77% | +8.5 | +406,812 | 10 |
| discovery | removed | 37 | 19% | -3.0 | -119,603 | 30 |
| holdout | book | 24 | 38% | -0.5 | -12,230 | 15 |
| holdout | kept | 15 | 27% | -3.4 | -43,027 | 11 |
| holdout | removed | 9 | 56% | +4.3 | +30,797 | 4 |
| all | book | 105 | 48% | +2.4 | +274,979 | 55 |
| all | kept | 59 | 64% | +5.5 | +363,786 | 21 |
| all | removed | 46 | 26% | -1.6 | -88,806 | 34 |

Verdict on this rule: **REJECTED** — shuffle p=0.23: the same search finds as good a rule in random labels; holdout kept wins 27% vs book 38% (worse than the book); holdout removed side is profitable (Rs +30,797).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `fut_spread >= 2.6` | 57 tr, win 63%, mean +6.0%, Rs +358,176, 21 losers | 24 tr, win 21%, mean -3.2%, Rs -70,967, 19 losers | 0.290 | 16 tr, win 31%, mean -1.7%, Rs -25,672, 11 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_hand | `rv15_spot >= 12.04` | 25 tr, win 68%, mean +8.4%, Rs +230,425, 8 losers | 56 tr, win 43%, mean +1.0%, Rs +56,784, 32 losers | 0.755 | 3 tr, win 33%, mean -4.7%, Rs -13,468, 2 losers | 21 tr, win 38%, mean +0.1%, Rs +1,238, 13 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.29` | 24 tr, win 75%, mean +8.0%, Rs +239,109, 6 losers | 57 tr, win 40%, mean +1.3%, Rs +48,100, 34 losers | 0.600 | 7 tr, win 43%, mean -1.2%, Rs -8,479, 4 losers | 17 tr, win 35%, mean -0.2%, Rs -3,750, 11 losers | REJECTED |
| single_text | `opt_opp_q=REFILLING < 1` | 47 tr, win 60%, mean +5.4%, Rs +293,020, 19 losers | 34 tr, win 38%, mean +0.4%, Rs -5,811, 21 losers | 0.570 | 18 tr, win 39%, mean +0.6%, Rs +10,189, 11 losers | 6 tr, win 33%, mean -3.9%, Rs -22,418, 4 losers | REJECTED |
| single_all | `fut_spread >= 2.6` | 57 tr, win 63%, mean +6.0%, Rs +358,176, 21 losers | 24 tr, win 21%, mean -3.2%, Rs -70,967, 19 losers | 0.340 | 16 tr, win 31%, mean -1.7%, Rs -25,672, 11 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_all_9lines | `fut_spread >= 2.6` | 57 tr, win 63%, mean +6.0%, Rs +358,176, 21 losers | 24 tr, win 21%, mean -3.2%, Rs -70,967, 19 losers | 0.490 | 16 tr, win 31%, mean -1.7%, Rs -25,672, 11 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_raw | `fut_spread >= 2.6 AND chain_age >= 45` | 29 tr, win 83%, mean +11.0%, Rs +365,641, 5 losers | 52 tr, win 33%, mean -1.0%, Rs -78,432, 35 losers | 0.365 | 9 tr, win 33%, mean -0.2%, Rs -2,135, 6 losers | 15 tr, win 40%, mean -0.7%, Rs -10,094, 9 losers | REJECTED |
| pair_hand | `rv15_spot >= 12.04 AND trig_str < 125.6` | 21 tr, win 81%, mean +11.8%, Rs +266,640, 4 losers | 60 tr, win 40%, mean +0.3%, Rs +20,569, 36 losers | 0.615 | 3 tr, win 33%, mean -4.7%, Rs -13,468, 2 losers | 21 tr, win 38%, mean +0.1%, Rs +1,238, 13 losers | REJECTED |
| pair_all | `fut_spread >= 2.6 AND imp_depth_with < 0.5124` | 50 tr, win 70%, mean +7.5%, Rs +396,653, 15 losers | 31 tr, win 19%, mean -3.5%, Rs -109,444, 25 losers | 0.500 | 15 tr, win 27%, mean -3.4%, Rs -43,027, 11 losers | 9 tr, win 56%, mean +4.3%, Rs +30,797, 4 losers | REJECTED |
| triple_all | `fut_spread >= 2.6 AND imp_depth_with < 0.5124 AND ret_today < 83.4` | 44 tr, win 77%, mean +8.5%, Rs +406,812, 10 losers | 37 tr, win 19%, mean -3.0%, Rs -119,603, 30 losers | 0.235 | 15 tr, win 27%, mean -3.4%, Rs -43,027, 11 losers | 9 tr, win 56%, mean +4.3%, Rs +30,797, 4 losers | REJECTED |
| or_all | `(oi_own_chg30 >= 1.245e+06) OR (e_fut_micro_with >= 0.29)` | 39 tr, win 74%, mean +8.8%, Rs +397,335, 10 losers | 42 tr, win 29%, mean -1.8%, Rs -110,126, 30 losers | 0.435 | 10 tr, win 40%, mean -2.9%, Rs -27,979, 6 losers | 14 tr, win 36%, mean +1.2%, Rs +15,750, 9 losers | REJECTED |
| single_all_keep30 | `fut_spread >= 2.6` | 57 tr, win 63%, mean +6.0%, Rs +358,176, 21 losers | 24 tr, win 21%, mean -3.2%, Rs -70,967, 19 losers | 0.315 | 16 tr, win 31%, mean -1.7%, Rs -25,672, 11 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## lvl_trail_be

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 84 | 49% | +2.8 | +259,454 | 43 |
| holdout | 24 | 46% | +0.4 | +11,160 | 13 |
| all | 108 | 48% | +2.3 | +270,614 | 56 |

### Best rule found (search `or_all`, 345 features, params default)

### lvl_trail_be: `(e_fut_micro_with >= 0.254) OR (rv15_spot >= 12.05)  (OR rule: kept if either clause holds)`

Shuffle test p = 0.055 (does NOT beat luck). Shuffle median best score 0.457, max 0.596, real 0.526.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 84 | 49% | +2.8 | +259,454 | 43 |
| discovery | kept | 45 | 73% | +8.5 | +430,612 | 12 |
| discovery | removed | 39 | 21% | -3.7 | -171,158 | 31 |
| holdout | book | 24 | 46% | +0.4 | +11,160 | 13 |
| holdout | kept | 10 | 50% | -1.2 | -12,977 | 5 |
| holdout | removed | 14 | 43% | +1.5 | +24,138 | 8 |
| all | book | 108 | 48% | +2.3 | +270,614 | 56 |
| all | kept | 55 | 69% | +6.7 | +417,635 | 17 |
| all | removed | 53 | 26% | -2.3 | -147,020 | 39 |

Verdict on this rule: **REJECTED** — shuffle p=0.06: the same search finds as good a rule in random labels; holdout removed side is profitable (Rs +24,138).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `e_rv15 >= 12.09` | 25 tr, win 76%, mean +10.1%, Rs +281,437, 6 losers | 59 tr, win 37%, mean -0.3%, Rs -21,983, 37 losers | 0.495 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 22 tr, win 45%, mean +0.9%, Rs +20,988, 12 losers | REJECTED |
| single_hand | `rv15_spot >= 12.05` | 25 tr, win 76%, mean +10.1%, Rs +281,437, 6 losers | 59 tr, win 37%, mean -0.3%, Rs -21,983, 37 losers | 0.070 | 3 tr, win 33%, mean -4.7%, Rs -13,468, 2 losers | 21 tr, win 48%, mean +1.1%, Rs +24,628, 11 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.254` | 25 tr, win 76%, mean +9.0%, Rs +277,911, 6 losers | 59 tr, win 37%, mean +0.2%, Rs -18,457, 37 losers | 0.285 | 7 tr, win 57%, mean +0.4%, Rs +491, 3 losers | 17 tr, win 41%, mean +0.4%, Rs +10,670, 10 losers | REJECTED |
| single_text | `opt_opp_q=REFILLING < 1` | 49 tr, win 57%, mean +4.6%, Rs +270,049, 21 losers | 35 tr, win 37%, mean +0.4%, Rs -10,595, 22 losers | 0.750 | 18 tr, win 44%, mean +1.3%, Rs +23,706, 10 losers | 6 tr, win 50%, mean -2.2%, Rs -12,545, 3 losers | REJECTED |
| single_all | `e_rv15 >= 12.09` | 25 tr, win 76%, mean +10.1%, Rs +281,437, 6 losers | 59 tr, win 37%, mean -0.3%, Rs -21,983, 37 losers | 0.630 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 22 tr, win 45%, mean +0.9%, Rs +20,988, 12 losers | REJECTED |
| single_all_9lines | `e_rv15 >= 12.09` | 25 tr, win 76%, mean +10.1%, Rs +281,437, 6 losers | 59 tr, win 37%, mean -0.3%, Rs -21,983, 37 losers | 0.715 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 22 tr, win 45%, mean +0.9%, Rs +20,988, 12 losers | REJECTED |
| pair_raw | `oi_own_chg30 >= -2.034e+04 AND e_syn_dev >= -1.493` | 28 tr, win 82%, mean +10.9%, Rs +351,972, 5 losers | 56 tr, win 32%, mean -1.2%, Rs -92,518, 38 losers | 0.560 | 6 tr, win 33%, mean -5.0%, Rs -28,259, 4 losers | 18 tr, win 50%, mean +2.2%, Rs +39,419, 9 losers | REJECTED |
| pair_hand | `rv15_spot >= 12.05 AND trig_str < 125.1` | 21 tr, win 86%, mean +13.3%, Rs +309,345, 3 losers | 63 tr, win 37%, mean -0.7%, Rs -49,891, 40 losers | 0.270 | 3 tr, win 33%, mean -4.7%, Rs -13,468, 2 losers | 21 tr, win 48%, mean +1.1%, Rs +24,628, 11 losers | REJECTED |
| pair_all | `oi_own_chg30 >= -2.034e+04 AND e_syn_dev >= -1.493` | 28 tr, win 82%, mean +10.9%, Rs +351,972, 5 losers | 56 tr, win 32%, mean -1.2%, Rs -92,518, 38 losers | 0.720 | 6 tr, win 33%, mean -5.0%, Rs -28,259, 4 losers | 18 tr, win 50%, mean +2.2%, Rs +39,419, 9 losers | REJECTED |
| triple_all | `oi_own_chg30 >= -2.034e+04 AND e_syn_dev >= -1.493 AND bn300 >= -0.1839` | 26 tr, win 88%, mean +12.5%, Rs +371,234, 3 losers | 58 tr, win 31%, mean -1.5%, Rs -111,780, 40 losers | 0.890 | 6 tr, win 33%, mean -5.0%, Rs -28,259, 4 losers | 18 tr, win 50%, mean +2.2%, Rs +39,419, 9 losers | REJECTED |
| or_all | `(e_fut_micro_with >= 0.254) OR (rv15_spot >= 12.05)` | 45 tr, win 73%, mean +8.5%, Rs +430,612, 12 losers | 39 tr, win 21%, mean -3.7%, Rs -171,158, 31 losers | 0.055 | 10 tr, win 50%, mean -1.2%, Rs -12,977, 5 losers | 14 tr, win 43%, mean +1.5%, Rs +24,138, 8 losers | REJECTED |
| single_all_keep30 | `oi_own_chg30 >= -2.034e+04` | 39 tr, win 64%, mean +7.0%, Rs +317,356, 14 losers | 45 tr, win 36%, mean -0.8%, Rs -57,902, 29 losers | 0.895 | 7 tr, win 29%, mean -5.8%, Rs -38,269, 5 losers | 17 tr, win 53%, mean +3.0%, Rs +49,429, 8 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## lvl_trail_re

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 76 | 53% | +3.9 | +317,570 | 36 |
| holdout | 21 | 43% | +1.0 | +12,838 | 12 |
| all | 97 | 51% | +3.2 | +330,408 | 48 |

### Best rule found (search `pair_raw`, 193 features, params default)

### lvl_trail_re: `fut_spread >= 2.6 AND oi_net_help5 >= 7.879e+05`

Shuffle test p = 0.300 (does NOT beat luck). Shuffle median best score 0.464, max 0.597, real 0.486.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 76 | 53% | +3.9 | +317,570 | 36 |
| discovery | kept | 30 | 83% | +9.9 | +340,525 | 5 |
| discovery | removed | 46 | 33% | -0.1 | -22,955 | 31 |
| holdout | book | 21 | 43% | +1.0 | +12,838 | 12 |
| holdout | kept | 5 | 60% | +0.5 | -162 | 2 |
| holdout | removed | 16 | 38% | +1.1 | +13,000 | 10 |
| all | book | 97 | 51% | +3.2 | +330,408 | 48 |
| all | kept | 35 | 80% | +8.6 | +340,363 | 7 |
| all | removed | 62 | 34% | +0.2 | -9,955 | 41 |

Verdict on this rule: **REJECTED** — shuffle p=0.30: the same search finds as good a rule in random labels; holdout removed side is profitable (Rs +13,000).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `fut_spread >= 2.6` | 54 tr, win 65%, mean +6.7%, Rs +378,999, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -61,428, 17 losers | 0.385 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_hand | `pos_dir >= 0.4631` | 53 tr, win 60%, mean +5.0%, Rs +287,342, 21 losers | 23 tr, win 35%, mean +1.3%, Rs +30,228, 15 losers | 0.775 | 12 tr, win 58%, mean +3.5%, Rs +32,646, 5 losers | 9 tr, win 22%, mean -2.4%, Rs -19,809, 7 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.27` | 23 tr, win 78%, mean +10.6%, Rs +294,076, 5 losers | 53 tr, win 42%, mean +0.9%, Rs +23,494, 31 losers | 0.600 | 6 tr, win 50%, mean +0.4%, Rs +871, 3 losers | 15 tr, win 40%, mean +1.2%, Rs +11,966, 9 losers | REJECTED |
| single_text | `opt_opp_o=REFILLING < 1` | 49 tr, win 61%, mean +4.6%, Rs +236,925, 19 losers | 27 tr, win 37%, mean +2.6%, Rs +80,646, 17 losers | 0.625 | 18 tr, win 44%, mean +1.2%, Rs +14,410, 10 losers | 3 tr, win 33%, mean -0.6%, Rs -1,573, 2 losers | REJECTED |
| single_all | `fut_spread >= 2.6` | 54 tr, win 65%, mean +6.7%, Rs +378,999, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -61,428, 17 losers | 0.485 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_all_9lines | `fut_spread >= 2.6` | 54 tr, win 65%, mean +6.7%, Rs +378,999, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -61,428, 17 losers | 0.620 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_raw | `fut_spread >= 2.6 AND oi_net_help5 >= 7.879e+05` | 30 tr, win 83%, mean +9.9%, Rs +340,525, 5 losers | 46 tr, win 33%, mean -0.1%, Rs -22,955, 31 losers | 0.300 | 5 tr, win 60%, mean +0.5%, Rs -162, 2 losers | 16 tr, win 38%, mean +1.1%, Rs +13,000, 10 losers | REJECTED |
| pair_hand | `pos_dir >= 0.4631 AND ret_today < 81.8` | 49 tr, win 65%, mean +5.9%, Rs +344,919, 17 losers | 27 tr, win 30%, mean +0.1%, Rs -27,349, 19 losers | 0.680 | 12 tr, win 58%, mean +3.5%, Rs +32,646, 5 losers | 9 tr, win 22%, mean -2.4%, Rs -19,809, 7 losers | REJECTED |
| pair_all | `fut_spread >= 2.6 AND oi_net_help5 >= 7.879e+05` | 30 tr, win 83%, mean +9.9%, Rs +340,525, 5 losers | 46 tr, win 33%, mean -0.1%, Rs -22,955, 31 losers | 0.440 | 5 tr, win 60%, mean +0.5%, Rs -162, 2 losers | 16 tr, win 38%, mean +1.1%, Rs +13,000, 10 losers | REJECTED |
| triple_all | `fut_spread >= 2.6 AND oi_net_help5 >= 7.879e+05 AND regime_ext_pct < 94.5` | 26 tr, win 92%, mean +11.5%, Rs +329,790, 2 losers | 50 tr, win 32%, mean -0.1%, Rs -12,220, 34 losers | 0.595 | 4 tr, win 50%, mean +0.6%, Rs -344, 2 losers | 17 tr, win 41%, mean +1.0%, Rs +13,182, 10 losers | REJECTED |
| or_all | `(e_fut_micro_with >= 0.27) OR (agg_net >= 0.0865)` | 40 tr, win 75%, mean +9.1%, Rs +425,503, 10 losers | 36 tr, win 28%, mean -1.9%, Rs -107,932, 26 losers | 0.555 | 10 tr, win 50%, mean +0.1%, Rs -715, 5 losers | 11 tr, win 36%, mean +1.7%, Rs +13,552, 7 losers | REJECTED |
| single_all_keep30 | `fut_spread >= 2.6` | 54 tr, win 65%, mean +6.7%, Rs +378,999, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -61,428, 17 losers | 0.405 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## lvl_trail_rx

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 75 | 52% | +3.8 | +301,398 | 36 |
| holdout | 21 | 43% | +1.0 | +12,838 | 12 |
| all | 96 | 50% | +3.2 | +314,236 | 48 |

### Best rule found (search `pair_raw`, 195 features, params default)

### lvl_trail_rx: `fut_spread >= 2.6 AND ret_today < 75.24`

Shuffle test p = 0.355 (does NOT beat luck). Shuffle median best score 0.470, max 0.658, real 0.483.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 75 | 52% | +3.8 | +301,398 | 36 |
| discovery | kept | 48 | 71% | +8.0 | +432,767 | 14 |
| discovery | removed | 27 | 19% | -3.6 | -131,368 | 22 |
| holdout | book | 21 | 43% | +1.0 | +12,838 | 12 |
| holdout | kept | 13 | 38% | +0.4 | -604 | 8 |
| holdout | removed | 8 | 50% | +1.8 | +13,442 | 4 |
| all | book | 96 | 50% | +3.2 | +314,236 | 48 |
| all | kept | 61 | 64% | +6.4 | +432,162 | 22 |
| all | removed | 35 | 26% | -2.4 | -117,926 | 26 |

Verdict on this rule: **REJECTED** — shuffle p=0.35: the same search finds as good a rule in random labels; holdout kept wins 38% vs book 43% (worse than the book); holdout removed side is profitable (Rs +13,442).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.6%, Rs +366,164, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,766, 17 losers | 0.380 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_hand | `streak < 1` | 42 tr, win 62%, mean +4.4%, Rs +187,012, 16 losers | 33 tr, win 39%, mean +3.0%, Rs +114,387, 20 losers | 0.770 | 14 tr, win 43%, mean +0.8%, Rs +3,952, 8 losers | 7 tr, win 43%, mean +1.3%, Rs +8,886, 4 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.37` | 23 tr, win 78%, mean +8.3%, Rs +231,455, 5 losers | 52 tr, win 40%, mean +1.8%, Rs +69,943, 31 losers | 0.455 | 6 tr, win 50%, mean +0.4%, Rs +871, 3 losers | 15 tr, win 40%, mean +1.2%, Rs +11,966, 9 losers | REJECTED |
| single_text | `opt_opp_o=REFILLING < 1` | 47 tr, win 60%, mean +4.5%, Rs +216,115, 19 losers | 28 tr, win 39%, mean +2.7%, Rs +85,283, 17 losers | 0.830 | 18 tr, win 44%, mean +1.2%, Rs +14,410, 10 losers | 3 tr, win 33%, mean -0.6%, Rs -1,573, 2 losers | REJECTED |
| single_all | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.6%, Rs +366,164, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,766, 17 losers | 0.520 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_all_9lines | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.6%, Rs +366,164, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,766, 17 losers | 0.680 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_raw | `fut_spread >= 2.6 AND ret_today < 75.24` | 48 tr, win 71%, mean +8.0%, Rs +432,767, 14 losers | 27 tr, win 19%, mean -3.6%, Rs -131,368, 22 losers | 0.355 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_hand | `pos_dir >= 0.4561 AND streak < 2` | 44 tr, win 66%, mean +5.9%, Rs +296,550, 15 losers | 31 tr, win 32%, mean +0.8%, Rs +4,849, 21 losers | 0.740 | 11 tr, win 64%, mean +3.9%, Rs +34,206, 4 losers | 10 tr, win 20%, mean -2.3%, Rs -21,369, 8 losers | REJECTED |
| pair_all | `fut_spread >= 2.6 AND ret_today < 75.24` | 48 tr, win 71%, mean +8.0%, Rs +432,767, 14 losers | 27 tr, win 19%, mean -3.6%, Rs -131,368, 22 losers | 0.540 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| triple_all | `fut_spread >= 2.6 AND ret_today < 75.24 AND imp_depth_with < 0.5105` | 41 tr, win 78%, mean +9.7%, Rs +454,659, 9 losers | 34 tr, win 21%, mean -3.3%, Rs -153,260, 27 losers | 0.445 | 12 tr, win 33%, mean -1.5%, Rs -17,960, 8 losers | 9 tr, win 56%, mean +4.3%, Rs +30,797, 4 losers | REJECTED |
| or_all | `(e_fut_micro_with >= 0.37) OR (e_rv15 >= 12.12)` | 42 tr, win 74%, mean +8.9%, Rs +409,994, 11 losers | 33 tr, win 24%, mean -2.7%, Rs -108,596, 25 losers | 0.415 | 8 tr, win 50%, mean -1.0%, Rs -8,957, 4 losers | 13 tr, win 38%, mean +2.2%, Rs +21,794, 8 losers | REJECTED |
| single_all_keep30 | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.6%, Rs +366,164, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,766, 17 losers | 0.465 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## lvl_trail_rx_be

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 78 | 50% | +3.3 | +284,554 | 39 |
| holdout | 21 | 52% | +2.0 | +36,228 | 10 |
| all | 99 | 51% | +3.0 | +320,782 | 49 |

### Best rule found (search `single_hand`, 22 features, params default)

### lvl_trail_rx_be: `rv15_spot >= 12.11`

Shuffle test p = 0.215 (does NOT beat luck). Shuffle median best score 0.256, max 0.487, real 0.308.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 78 | 50% | +3.3 | +284,554 | 39 |
| discovery | kept | 24 | 75% | +10.2 | +272,181 | 6 |
| discovery | removed | 54 | 39% | +0.2 | +12,373 | 33 |
| holdout | book | 21 | 52% | +2.0 | +36,228 | 10 |
| holdout | kept | 2 | 50% | -5.2 | -9,828 | 1 |
| holdout | removed | 19 | 53% | +2.7 | +46,056 | 9 |
| all | book | 99 | 51% | +3.0 | +320,782 | 49 |
| all | kept | 26 | 73% | +9.0 | +262,353 | 7 |
| all | removed | 73 | 42% | +0.9 | +58,428 | 42 |

Verdict on this rule: **REJECTED** — shuffle p=0.21: the same search finds as good a rule in random labels; holdout kept wins 50% vs book 52% (worse than the book); holdout removed side is profitable (Rs +46,056).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `e_rv15 >= 12.13` | 24 tr, win 75%, mean +10.2%, Rs +272,181, 6 losers | 54 tr, win 39%, mean +0.2%, Rs +12,373, 33 losers | 0.875 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 19 tr, win 53%, mean +2.7%, Rs +46,056, 9 losers | REJECTED |
| single_hand | `rv15_spot >= 12.11` | 24 tr, win 75%, mean +10.2%, Rs +272,181, 6 losers | 54 tr, win 39%, mean +0.2%, Rs +12,373, 33 losers | 0.215 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 19 tr, win 53%, mean +2.7%, Rs +46,056, 9 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.247` | 24 tr, win 75%, mean +8.9%, Rs +260,959, 6 losers | 54 tr, win 39%, mean +0.9%, Rs +23,595, 33 losers | 0.610 | 6 tr, win 67%, mean +2.2%, Rs +9,841, 2 losers | 15 tr, win 47%, mean +1.9%, Rs +26,387, 8 losers | REJECTED |
| single_text | `opt_opp_o=REFILLING < 1` | 51 tr, win 57%, mean +3.7%, Rs +204,068, 22 losers | 27 tr, win 37%, mean +2.6%, Rs +80,486, 17 losers | 0.890 | 18 tr, win 56%, mean +2.4%, Rs +37,833, 8 losers | 3 tr, win 33%, mean -0.6%, Rs -1,606, 2 losers | REJECTED |
| single_all | `e_rv15 >= 12.13` | 24 tr, win 75%, mean +10.2%, Rs +272,181, 6 losers | 54 tr, win 39%, mean +0.2%, Rs +12,373, 33 losers | 0.945 | 2 tr, win 50%, mean -5.2%, Rs -9,828, 1 losers | 19 tr, win 53%, mean +2.7%, Rs +46,056, 9 losers | REJECTED |
| single_all_9lines | `e_rv15 >= 11.53` | 31 tr, win 71%, mean +10.0%, Rs +350,942, 9 losers | 47 tr, win 36%, mean -1.1%, Rs -66,388, 30 losers | 0.775 | 6 tr, win 50%, mean -1.0%, Rs -6,702, 3 losers | 15 tr, win 53%, mean +3.2%, Rs +42,929, 7 losers | REJECTED |
| pair_raw | `oi_own_chg30 >= -9490 AND e_syn_dev >= -1.512` | 26 tr, win 85%, mean +11.7%, Rs +344,806, 4 losers | 52 tr, win 33%, mean -0.9%, Rs -60,252, 35 losers | 0.630 | 4 tr, win 50%, mean -2.3%, Rs -9,236, 2 losers | 17 tr, win 53%, mean +3.0%, Rs +45,464, 8 losers | REJECTED |
| pair_hand | `rv15_spot >= 10.92 AND ret_today < 75.17` | 36 tr, win 69%, mean +8.4%, Rs +341,172, 11 losers | 42 tr, win 33%, mean -1.1%, Rs -56,618, 28 losers | 0.580 | 7 tr, win 43%, mean -2.2%, Rs -16,270, 4 losers | 14 tr, win 57%, mean +4.1%, Rs +52,497, 6 losers | REJECTED |
| pair_all | `oi_own_chg30 >= -9490 AND e_syn_dev >= -1.512` | 26 tr, win 85%, mean +11.7%, Rs +344,806, 4 losers | 52 tr, win 33%, mean -0.9%, Rs -60,252, 35 losers | 0.860 | 4 tr, win 50%, mean -2.3%, Rs -9,236, 2 losers | 17 tr, win 53%, mean +3.0%, Rs +45,464, 8 losers | REJECTED |
| triple_all | `oi_own_chg30 >= -9490 AND e_syn_dev >= -1.512 AND hrs_to_expiry < 146.2` | 25 tr, win 88%, mean +12.5%, Rs +354,065, 3 losers | 53 tr, win 32%, mean -1.0%, Rs -69,511, 36 losers | 0.950 | 4 tr, win 50%, mean -2.3%, Rs -9,236, 2 losers | 17 tr, win 53%, mean +3.0%, Rs +45,464, 8 losers | REJECTED |
| or_all | `(e_fut_micro_with >= 0.247) OR (e_rv15 >= 12.13)` | 43 tr, win 72%, mean +8.4%, Rs +408,480, 12 losers | 35 tr, win 23%, mean -2.9%, Rs -123,926, 27 losers | 0.455 | 8 tr, win 62%, mean +0.4%, Rs +13, 3 losers | 13 tr, win 46%, mean +3.0%, Rs +36,215, 7 losers | REJECTED |
| single_all_keep30 | `oi_own_chg30 >= -9490` | 36 tr, win 67%, mean +7.8%, Rs +318,536, 12 losers | 42 tr, win 36%, mean -0.6%, Rs -33,982, 27 losers | 0.905 | 5 tr, win 40%, mean -4.0%, Rs -19,246, 3 losers | 16 tr, win 56%, mean +3.9%, Rs +55,474, 7 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## lvl_trail_rx_c10

### The book's own record

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 75 | 52% | +3.9 | +318,636 | 36 |
| holdout | 21 | 43% | +1.0 | +12,838 | 12 |
| all | 96 | 50% | +3.3 | +331,474 | 48 |

### Best rule found (search `pair_raw`, 195 features, params default)

### lvl_trail_rx_c10: `fut_spread >= 2.6 AND ret_today < 82.54`

Shuffle test p = 0.380 (does NOT beat luck). Shuffle median best score 0.471, max 0.658, real 0.483.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 75 | 52% | +3.9 | +318,636 | 36 |
| discovery | kept | 48 | 71% | +8.1 | +449,586 | 14 |
| discovery | removed | 27 | 19% | -3.6 | -130,949 | 22 |
| holdout | book | 21 | 43% | +1.0 | +12,838 | 12 |
| holdout | kept | 13 | 38% | +0.4 | -604 | 8 |
| holdout | removed | 8 | 50% | +1.8 | +13,442 | 4 |
| all | book | 96 | 50% | +3.3 | +331,474 | 48 |
| all | kept | 61 | 64% | +6.5 | +448,981 | 22 |
| all | removed | 35 | 26% | -2.3 | -117,507 | 26 |

Verdict on this rule: **REJECTED** — shuffle p=0.38: the same search finds as good a rule in random labels; holdout kept wins 38% vs book 43% (worse than the book); holdout removed side is profitable (Rs +13,442).

### Every search, one line each (discovery -> shuffle -> holdout)

| search | rule | disc kept | disc removed | p | holdout kept | holdout removed | verdict |
|---|---|---|---|---|---|---|---|
| single_raw | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.8%, Rs +382,840, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,204, 17 losers | 0.390 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_hand | `streak < 1` | 42 tr, win 62%, mean +4.6%, Rs +200,740, 16 losers | 33 tr, win 39%, mean +3.0%, Rs +117,897, 20 losers | 0.770 | 14 tr, win 43%, mean +0.8%, Rs +3,952, 8 losers | 7 tr, win 43%, mean +1.3%, Rs +8,886, 4 losers | REJECTED |
| single_derived | `e_fut_micro_with >= 0.37` | 23 tr, win 78%, mean +8.7%, Rs +245,957, 5 losers | 52 tr, win 40%, mean +1.8%, Rs +72,680, 31 losers | 0.440 | 6 tr, win 50%, mean +0.4%, Rs +871, 3 losers | 15 tr, win 40%, mean +1.2%, Rs +11,966, 9 losers | REJECTED |
| single_text | `opt_opp_q=REFILLING < 1` | 44 tr, win 61%, mean +6.7%, Rs +368,716, 17 losers | 31 tr, win 39%, mean -0.0%, Rs -50,079, 19 losers | 0.580 | 15 tr, win 47%, mean +2.9%, Rs +35,256, 8 losers | 6 tr, win 33%, mean -3.9%, Rs -22,418, 4 losers | REJECTED |
| single_all | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.8%, Rs +382,840, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,204, 17 losers | 0.530 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| single_all_9lines | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.8%, Rs +382,840, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,204, 17 losers | 0.680 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_raw | `fut_spread >= 2.6 AND ret_today < 82.54` | 48 tr, win 71%, mean +8.1%, Rs +449,586, 14 losers | 27 tr, win 19%, mean -3.6%, Rs -130,949, 22 losers | 0.380 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| pair_hand | `pos_dir >= 0.4561 AND streak < 2` | 44 tr, win 66%, mean +6.1%, Rs +309,608, 15 losers | 31 tr, win 32%, mean +0.8%, Rs +9,028, 21 losers | 0.740 | 11 tr, win 64%, mean +3.9%, Rs +34,206, 4 losers | 10 tr, win 20%, mean -2.3%, Rs -21,369, 8 losers | REJECTED |
| pair_all | `fut_spread >= 2.6 AND ret_today < 82.54` | 48 tr, win 71%, mean +8.1%, Rs +449,586, 14 losers | 27 tr, win 19%, mean -3.6%, Rs -130,949, 22 losers | 0.550 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| triple_all | `fut_spread >= 2.6 AND ret_today < 82.54 AND po_a < 36.12` | 41 tr, win 78%, mean +10.0%, Rs +464,870, 9 losers | 34 tr, win 21%, mean -3.5%, Rs -146,234, 27 losers | 0.435 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |
| or_all | `(e_fut_micro_with >= 0.37) OR (rv15_spot >= 12.1)` | 42 tr, win 74%, mean +9.1%, Rs +423,943, 11 losers | 33 tr, win 24%, mean -2.7%, Rs -105,306, 25 losers | 0.410 | 8 tr, win 50%, mean -1.0%, Rs -8,957, 4 losers | 13 tr, win 38%, mean +2.2%, Rs +21,794, 8 losers | REJECTED |
| single_all_keep30 | `fut_spread >= 2.6` | 53 tr, win 64%, mean +6.8%, Rs +382,840, 19 losers | 22 tr, win 23%, mean -3.0%, Rs -64,204, 17 losers | 0.490 | 13 tr, win 38%, mean +0.4%, Rs -604, 8 losers | 8 tr, win 50%, mean +1.8%, Rs +13,442, 4 losers | REJECTED |

### Reading

12 searches run. 12 rules passed the discovery standard, 0 of those also beat the shuffle test (p < 0.05), 0 survived the holdout. No rule honestly removes this book's losers: what fits the first ten days does not hold on the last four, or the same search finds it in random labels.

**Verdict: NONE**

## Reading across the family (plain words)

* 72 searches (12 per book x 6 books), every one rejected. Not one rule passed all three gates; most fail two.
* The shuffle test is the killer. The best real score of a single-clause search over the full pool (~345 features) was
  0.32-0.35; the same search on randomly shuffled labels reaches that or better 29-68 % of the time. Pairs and triples
  reach 0.45-0.58 real, and random labels match that 24-89 % of the time. The one near miss is the OR rule on
  lvl_trail_be (`e_fut_micro_with >= 0.254 OR rv15_spot >= 12.05`, p = 0.055), and it then loses on holdout (kept 50 %,
  removed side +Rs 24k). In other words, what looks like "77 % winners kept, 10 losers" on ten days is what any search
  this wide finds in coin-flip data.
* The clause that keeps surfacing, `fut_spread >= 2.6` (futures bid-ask spread in points at the trigger), is a
  memory of the tape: on discovery it keeps 63-65 % winners, on holdout 31-38 % — below the book — and the removed
  side turns profitable. The same is true of `rv15_spot >= 12` (realised vol): 25 kept trades at 68-76 % on discovery,
  2-3 trades on holdout. Realised vol fell in November, so the clause barely fires.
* The only clause whose holdout side looks right (`pos_dir >= 0.46`, position in the day's range in the trade's
  direction; alone on lvl_trail_re, paired with `streak < 2` on rx / rx_c10, hand-picked set: holdout kept 58-64 %, removed side negative) has
  p = 0.74-0.78 on discovery: it was the best of 24 hand-picked fields by luck, and its discovery edge (60 % vs 51 %)
  is small. It is a hypothesis to watch, not a rule to register.
* Why nothing works here: the lvl_trail family's edge is in the exit (level-trail, +18 % lock), not in the trigger.
  Winners average +13.6 %, losers -7.7 %, win rate ~50 %; the weather at the trigger second is about as informative as
  a coin for which side a trade ends on. Removing losers "completely" is not possible from these fields on this sample;
  any rule that did so on the ten days was fitted to them.
* What I did not do: hold-time-dependent features (excluded by the brief), fitted hmm_/hk_ fields (excluded),
  threshold searches finer than 9 quantile lines, 4+ clause rules (a 3-clause greedy rule already fails at p = 0.24-0.89,
  so more clauses would only fit harder).

## Verdicts

| book | verdict |
|---|---|
| lvl_trail | NONE |
| lvl_trail_be | NONE |
| lvl_trail_re | NONE |
| lvl_trail_rx | NONE |
| lvl_trail_rx_be | NONE |
| lvl_trail_rx_c10 | NONE |
