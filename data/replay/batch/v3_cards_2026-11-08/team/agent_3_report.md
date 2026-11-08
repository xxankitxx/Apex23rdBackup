# Agent 3 — t28 pullback books: t28_cheap, t28_nohigh, t28_bidpile, t28_req, t28_gap, t28_ivfall

Data: 14 replayed days 19 Oct – 6 Nov 2026; discovery = first 10 days, holdout = last 4 (`rule_lab.split_days`). Every search below was run on discovery only, then re-run on **300 shufflings** of the discovery outcomes (identical search: same features, same quantile lines, same depth; masks precomputed once in `s2_fast.py`, scoring = rule_lab.score_masks) and the frozen rule was evaluated on the holdout days. Scripts: `s0_cache.py` (load), `s1_search.py` (derived features + first run, too slow), `s2_fast.py` (the run reported), `s3_report.py` (this file). Raw search output: `fast_<book>.json`, `fast_log.txt`.

## Headline

**No rule passes the standard on any of the six books. Verdict: NONE × 6.** Across 96 searches (16 per book) the best shuffle p is 0.090 (t28_req, pair B) — and even that rule's removed side is profitable on holdout. The shuffle medians tell the story: a 2-clause search over ~1,900–2,700 clause masks reaches a score of ~0.50 (e.g. '36 kept, 78 % win, 8 losers' out of 65) on *random* labels half the time, and the real labels never do materially better. The ~270 photograph fields, ~70 derived features (62 with >= 80 % fill, the rest dropped) and 61 text indicators carry no detectable information about which t28 pullback entries will win.

The six books share 80–95 % of their trades (same t28 trigger, different admission filters), so the same clauses (`fut_spread >= 2.6`, `e_syn_dev >= ...`, `oi_own_chg5 < ...`, `oi_help30_minus_5 < ...`) surface in every book — one tape, not six confirmations.

## t28_cheap

Record (83 trades; 190 raw numeric fields, 62 derived features, 61 text indicators searched):

- discovery: 65 trades, win 57%, mean +5.5 %, Rs +432,432, 28 losers
- holdout: 18 trades, win 44%, mean +1.7 %, Rs +23,010, 10 losers
- all: 83 trades, win 54%, mean +4.7 %, Rs +455,442, 38 losers

### Best rule by shuffle p — search N text-only pair

Search: best AND-pair of text indicators only (61 features, 204 clause masks, 300 shufflings; shuffle median score 0.346, max 0.560, real 0.346).

### t28_cheap: `ep_type=None < 1 AND phase_bucket=morning < 1`

Shuffle test p = 0.503 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 65 | 57% | +5.5 | +432,432 | 28 |
| discovery | kept | 36 | 72% | +8.5 | +383,477 | 10 |
| discovery | removed | 29 | 38% | +1.8 | +48,955 | 18 |
| holdout | book | 18 | 44% | +1.7 | +23,010 | 10 |
| holdout | kept | 8 | 50% | +3.1 | +18,434 | 4 |
| holdout | removed | 10 | 40% | +0.7 | +4,576 | 6 |
| all | book | 83 | 54% | +4.7 | +455,442 | 38 |
| all | kept | 44 | 68% | +7.5 | +401,911 | 14 |
| all | removed | 39 | 38% | +1.5 | +53,531 | 24 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `e_syn_dev >= -0.69` | 33 / 73% / 9 | 0.903 | 10 / 40% / 6 | +42,426 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `fut_spread >= 2.9 AND oi_own_chg5 < -1.548e+04` | 36 / 78% / 8 | 0.840 | 8 / 50% / 4 | -1,368 | shuffle |
| C raw+derived single q5 | `e_syn_dev >= -0.69` | 33 / 73% / 9 | 0.967 | 10 / 40% / 6 | +42,426 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `e_syn_dev >= -1.664 AND oi_help30_minus_5 < 6.466e+06` | 32 / 81% / 6 | 0.870 | 7 / 29% / 5 | +39,127 | shuffle, holdout win < book, removed side profitable on holdout |
| E raw+text pair q5 | `fut_spread >= 2.9 AND oi_own_chg5 < -1.548e+04` | 36 / 78% / 8 | 0.867 | 8 / 50% / 4 | -1,368 | shuffle |
| F raw+derived greedy triple q5 | `e_syn_dev >= -1.664 AND oi_help30_minus_5 < 6.466e+06 AND e_iv_atm >= 14.42` | 29 / 90% / 3 | 0.550 | 7 / 29% / 5 | +39,127 | shuffle, holdout win < book, removed side profitable on holdout |
| G raw single q9 | `e_syn_dev >= -1.066` | 39 / 72% / 11 | 0.687 | 10 / 40% / 6 | +42,426 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `e_syn_dev >= -1.066 AND zomma >= -7.382e-05` | 33 / 82% / 6 | 0.677 | 8 / 38% / 5 | +39,052 | shuffle, holdout win < book, removed side profitable on holdout |
| I raw OR-pair q5 | `agg_net >= 0.0662 AND oi_net_help5 >= 1.031e+06` [OR] | 41 / 76% / 10 | 0.790 | 8 / 50% / 4 | +27,332 | shuffle, removed side profitable on holdout |
| J derived-only pair q5 | `oi_help30_minus_5 < 6.466e+06 AND dir_x_e_syn_dev < 2.908` | 38 / 74% / 10 | 0.903 | 6 / 17% / 5 | +39,309 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `e_syn_dev >= -1.664 AND oi_help30_minus_5 < 6.466e+06` | 32 / 81% / 6 | 0.817 | 7 / 29% / 5 | +39,127 | shuffle, holdout win < book, removed side profitable on holdout |
| L raw+derived+text pair q5 min_keep 25 | `e_syn_dev >= -1.664 AND oi_help30_minus_5 < 6.466e+06` | 32 / 81% / 6 | 0.890 | 7 / 29% / 5 | +39,127 | shuffle, holdout win < book, removed side profitable on holdout |
| M raw+derived triple q9 | `e_syn_dev >= -1.066 AND zomma >= -7.382e-05 AND sl_room_ahead >= 0.404` | 31 / 87% / 4 | 0.780 | 8 / 38% / 5 | +39,052 | shuffle, holdout win < book, removed side profitable on holdout |
| N text-only pair | `ep_type=None < 1 AND phase_bucket=morning < 1` | 36 / 72% / 10 | 0.503 | 8 / 50% / 4 | +4,576 | shuffle, removed side profitable on holdout |
| O raw pair by direction (CE | PE) | `depth_age_fut >= 0.7 AND svi_res >= -0.02 AND is_ce < 0.5` | 21 / 86% / 3 | 0.597 | 7 / 29% / 5 | +36,241 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 3.326e+06` | 36 / 69% / 11 | 0.913 | 5 / 40% / 3 | +33,586 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.503). On the holdout days the book itself wins 44% (10 losers of 18); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## t28_nohigh

Record (90 trades; 193 raw numeric fields, 62 derived features, 61 text indicators searched):

- discovery: 70 trades, win 56%, mean +5.0 %, Rs +415,217, 31 losers
- holdout: 20 trades, win 40%, mean +0.6 %, Rs +6,061, 12 losers
- all: 90 trades, win 52%, mean +4.0 %, Rs +421,278, 43 losers

### Best rule by shuffle p — search K raw+derived pair q5 min_keep 30

Search: best AND-pair, raw + derived, 5 lines, min 30 kept (255 features, 2496 clause masks, 300 shufflings; shuffle median score 0.492, max 0.666, real 0.492).

### t28_nohigh: `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06`

Shuffle test p = 0.503 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 70 | 56% | +5.0 | +415,217 | 31 |
| discovery | kept | 35 | 80% | +10.6 | +431,668 | 7 |
| discovery | removed | 35 | 31% | -0.7 | -16,452 | 24 |
| holdout | book | 20 | 40% | +0.6 | +6,061 | 12 |
| holdout | kept | 7 | 29% | -3.7 | -23,250 | 5 |
| holdout | removed | 13 | 46% | +2.9 | +29,312 | 7 |
| all | book | 90 | 52% | +4.0 | +421,278 | 43 |
| all | kept | 42 | 71% | +8.2 | +408,418 | 12 |
| all | removed | 48 | 35% | +0.3 | +12,860 | 31 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `fut_spread >= 2.81` | 49 / 67% / 16 | 0.733 | 11 / 36% / 7 | +6,396 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `e_pcr >= 0.9463 AND fut_spread >= 2.81` | 32 / 81% / 6 | 0.657 | 8 / 38% / 5 | -11,115 | shuffle, holdout win < book |
| C raw+derived single q5 | `fut_spread >= 2.81` | 49 / 67% / 16 | 0.797 | 11 / 36% / 7 | +6,396 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06` | 35 / 80% / 7 | 0.580 | 7 / 29% / 5 | +29,312 | shuffle, holdout win < book, removed side profitable on holdout |
| E raw+text pair q5 | `e_pcr >= 0.9463 AND fut_spread >= 2.81` | 32 / 81% / 6 | 0.690 | 8 / 38% / 5 | -11,115 | shuffle, holdout win < book |
| F raw+derived greedy triple q5 | `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06 AND breadth_dir >= 0.02709` | 33 / 85% / 5 | 0.627 | 7 / 29% / 5 | +29,312 | shuffle, holdout win < book, removed side profitable on holdout |
| G raw single q9 | `e_syn_dev >= -0.256` | 28 / 79% / 6 | 0.603 | 11 / 36% / 7 | +35,568 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `e_pcr >= 0.9463 AND fut_spread >= 2.81` | 32 / 81% / 6 | 0.900 | 8 / 38% / 5 | -11,115 | shuffle, holdout win < book |
| I raw OR-pair q5 | `depth_age_fut >= 1.5 AND e_syn_dev >= 0.386` [OR] | 30 / 83% / 5 | 0.583 | 10 / 30% / 7 | +25,906 | shuffle, holdout win < book, removed side profitable on holdout |
| J derived-only pair q5 | `oi_help30_minus_5 < 6.294e+06 AND dir_x_e_syn_dev < 2.843` | 41 / 73% / 11 | 0.697 | 7 / 14% / 6 | +29,689 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06` | 35 / 80% / 7 | 0.503 | 7 / 29% / 5 | +29,312 | shuffle, holdout win < book, removed side profitable on holdout |
| L raw+derived+text pair q5 min_keep 25 | `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06` | 35 / 80% / 7 | 0.580 | 7 / 29% / 5 | +29,312 | shuffle, holdout win < book, removed side profitable on holdout |
| M raw+derived triple q9 | `e_syn_dev >= -1.464 AND oi_help30_minus_5 < 8.688e+06 AND theta_pct_x_mins_to_flat >= 3.959` | 34 / 85% / 5 | 0.677 | 9 / 33% / 6 | +22,256 | shuffle, holdout win < book, removed side profitable on holdout |
| N text-only pair | `fut_opp_o=HOLDING < 1 AND opt_opp_o=REFILLING < 1` | 33 / 73% / 9 | 0.567 | 9 / 33% / 6 | +17,904 | shuffle, holdout win < book, removed side profitable on holdout |
| O raw pair by direction (CE | PE) | `ep_max_s < 0.6835 AND vix_chg15 >= -0.04 AND is_ce < 0.5` | 22 / 82% / 4 | 0.940 | 6 / 17% / 5 | +16,832 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 6.294e+06` | 45 / 67% / 15 | 0.843 | 9 / 33% / 6 | +7,098 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.503). On the holdout days the book itself wins 40% (12 losers of 20); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## t28_bidpile

Record (91 trades; 193 raw numeric fields, 62 derived features, 62 text indicators searched):

- discovery: 70 trades, win 56%, mean +4.6 %, Rs +405,126, 31 losers
- holdout: 21 trades, win 43%, mean +1.0 %, Rs +12,838, 12 losers
- all: 91 trades, win 53%, mean +3.7 %, Rs +417,963, 43 losers

### Best rule by shuffle p — search J derived-only pair q5

Search: best AND-pair over derived features only, 5 lines (62 features, 618 clause masks, 300 shufflings; shuffle median score 0.434, max 0.620, real 0.447).

### t28_bidpile: `oi_help30_minus_5 < 6.793e+06 AND dir_x_e_syn_dev < 2.968`

Shuffle test p = 0.397 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 70 | 56% | +4.6 | +405,126 | 31 |
| discovery | kept | 40 | 75% | +8.8 | +430,121 | 10 |
| discovery | removed | 30 | 30% | -1.1 | -24,996 | 21 |
| holdout | book | 21 | 43% | +1.0 | +12,838 | 12 |
| holdout | kept | 8 | 25% | -2.8 | -20,823 | 6 |
| holdout | removed | 13 | 54% | +3.3 | +33,660 | 6 |
| all | book | 91 | 53% | +3.7 | +417,963 | 43 |
| all | kept | 48 | 67% | +6.8 | +409,298 | 16 |
| all | removed | 43 | 37% | +0.3 | +8,664 | 27 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `oi_own_chg30 >= 2.769e+04` | 33 / 73% / 9 | 0.727 | 5 / 40% / 3 | +32,084 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917` | 39 / 77% / 9 | 0.610 | 10 / 50% / 5 | -5,291 | shuffle |
| C raw+derived single q5 | `oi_own_chg30 >= 2.769e+04` | 33 / 73% / 9 | 0.800 | 5 / 40% / 3 | +32,084 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917` | 39 / 77% / 9 | 0.673 | 10 / 50% / 5 | -5,291 | shuffle |
| E raw+text pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917` | 39 / 77% / 9 | 0.647 | 10 / 50% / 5 | -5,291 | shuffle |
| F raw+derived greedy triple q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917 AND po_a < 36.02` | 34 / 82% / 6 | 0.860 | 10 / 50% / 5 | -5,291 | shuffle |
| G raw single q9 | `oi_own_chg30 >= 2.769e+04` | 33 / 73% / 9 | 0.803 | 5 / 40% / 3 | +32,084 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `oi_own_chg30 >= 2.769e+04 AND opt_iv_chg5 >= -0.572` | 26 / 88% / 3 | 0.687 | 5 / 40% / 3 | +32,084 | shuffle, holdout win < book, removed side profitable on holdout |
| I raw OR-pair q5 | `new_lows >= 139 AND oi_net_help5 >= 1.732e+06` [OR] | 29 / 83% / 5 | 0.843 | 7 / 71% / 2 | +4,778 | shuffle, removed side profitable on holdout |
| J derived-only pair q5 | `oi_help30_minus_5 < 6.793e+06 AND dir_x_e_syn_dev < 2.968` | 40 / 75% / 10 | 0.397 | 8 / 25% / 6 | +33,660 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917` | 39 / 77% / 9 | 0.627 | 10 / 50% / 5 | -5,291 | shuffle |
| L raw+derived+text pair q5 min_keep 25 | `fut_spread >= 2.6 AND oi_own_chg5 < -7917` | 39 / 77% / 9 | 0.693 | 10 / 50% / 5 | -5,291 | shuffle |
| M raw+derived triple q9 | `oi_own_chg30 >= 2.769e+04 AND opt_iv_chg5 >= -0.572 AND basis_chg60 >= -4.26` | 24 / 96% / 1 | 0.827 | 5 / 40% / 3 | +32,084 | shuffle, holdout win < book, removed side profitable on holdout |
| N text-only pair | `fut_opp_o=HOLDING < 1 AND opt_opp_o=REFILLING < 1` | 31 / 74% / 8 | 0.550 | 10 / 40% / 6 | +17,960 | shuffle, holdout win < book, removed side profitable on holdout |
| O raw pair by direction (CE | PE) | `fut_spread >= 2.6 AND regime_ext_pct < 94.1 AND is_ce < 0.5` | 20 / 85% / 3 | 0.517 | 5 / 0% / 5 | +52,975 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 6.793e+06` | 45 / 67% / 15 | 0.817 | 10 / 40% / 6 | +11,070 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.397). On the holdout days the book itself wins 43% (12 losers of 21); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## t28_req

Record (87 trades; 190 raw numeric fields, 62 derived features, 61 text indicators searched):

- discovery: 68 trades, win 56%, mean +4.9 %, Rs +368,277, 30 losers
- holdout: 19 trades, win 47%, mean +2.1 %, Rs +29,786, 10 losers
- all: 87 trades, win 54%, mean +4.3 %, Rs +398,063, 40 losers

### Best rule by shuffle p — search B raw pair q5

Search: best AND-pair of clauses on different raw fields, 5 quantile lines, min 20 kept (rule_lab.best_pair) (190 features, 1856 clause masks, 300 shufflings; shuffle median score 0.486, max 0.661, real 0.556).

### t28_req: `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04`

Shuffle test p = 0.090 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 68 | 56% | +4.9 | +368,277 | 30 |
| discovery | kept | 37 | 81% | +10.4 | +439,293 | 7 |
| discovery | removed | 31 | 26% | -1.6 | -71,016 | 23 |
| holdout | book | 19 | 47% | +2.1 | +29,786 | 10 |
| holdout | kept | 9 | 56% | +4.1 | +27,748 | 4 |
| holdout | removed | 10 | 40% | +0.2 | +2,038 | 6 |
| all | book | 87 | 54% | +4.3 | +398,063 | 40 |
| all | kept | 46 | 76% | +9.2 | +467,041 | 11 |
| all | removed | 41 | 29% | -1.2 | -68,978 | 29 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `fut_spread >= 2.6` | 48 / 69% / 15 | 0.377 | 12 / 42% / 7 | +20,771 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.090 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| C raw+derived single q5 | `fut_spread >= 2.6` | 48 / 69% / 15 | 0.433 | 12 / 42% / 7 | +20,771 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.113 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| E raw+text pair q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.097 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| F raw+derived greedy triple q5 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04 AND agg_with_rs >= 2.039e+05` | 34 / 85% / 5 | 0.353 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| G raw single q9 | `fut_spread >= 2.6` | 48 / 69% / 15 | 0.480 | 12 / 42% / 7 | +20,771 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.203 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| I raw OR-pair q5 | `agg_net >= 0.0877 AND oi_net_help5 >= 9.974e+05` [OR] | 44 / 73% / 12 | 0.923 | 11 / 45% / 6 | +32,874 | shuffle, holdout win < book, removed side profitable on holdout |
| J derived-only pair q5 | `oi_help30_minus_5 < 6.789e+06 AND dir_x_e_syn_dev < 2.869` | 39 / 74% / 10 | 0.583 | 7 / 29% / 5 | +43,280 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.107 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| L raw+derived+text pair q5 min_keep 25 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04` | 37 / 81% / 7 | 0.123 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| M raw+derived triple q9 | `fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04 AND hw_vol_surge < 1.556` | 32 / 88% / 4 | 0.523 | 9 / 56% / 4 | +2,038 | shuffle, removed side profitable on holdout |
| N text-only pair | `ep_type=None < 1 AND phase_bucket=morning < 1` | 38 / 68% / 12 | 0.867 | 8 / 50% / 4 | +11,840 | shuffle, removed side profitable on holdout |
| O raw pair by direction (CE | PE) | `fut_spread >= 2.6 AND regime_ext_pct < 95.3 AND is_ce < 0.5` | 21 / 86% / 3 | 0.370 | 4 / 0% / 4 | +60,304 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 6.789e+06` | 43 / 67% / 14 | 0.857 | 9 / 44% / 5 | +20,690 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.090). On the holdout days the book itself wins 47% (10 losers of 19); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## t28_gap

Record (95 trades; 195 raw numeric fields, 62 derived features, 62 text indicators searched):

- discovery: 74 trades, win 54%, mean +4.2 %, Rs +345,579, 34 losers
- holdout: 21 trades, win 43%, mean +1.0 %, Rs +12,838, 12 losers
- all: 95 trades, win 52%, mean +3.5 %, Rs +358,416, 46 losers

### Best rule by shuffle p — search J derived-only pair q5

Search: best AND-pair over derived features only, 5 lines (62 features, 618 clause masks, 300 shufflings; shuffle median score 0.419, max 0.624, real 0.451).

### t28_gap: `oi_help30_minus_5 < 6.366e+06 AND dir_x_e_syn_dev < 2.921`

Shuffle test p = 0.280 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 74 | 54% | +4.2 | +345,579 | 34 |
| discovery | kept | 42 | 74% | +8.7 | +413,709 | 11 |
| discovery | removed | 32 | 28% | -1.6 | -68,130 | 23 |
| holdout | book | 21 | 43% | +1.0 | +12,838 | 12 |
| holdout | kept | 8 | 25% | -2.8 | -20,823 | 6 |
| holdout | removed | 13 | 54% | +3.3 | +33,660 | 6 |
| all | book | 95 | 52% | +3.5 | +358,416 | 46 |
| all | kept | 50 | 66% | +6.9 | +392,886 | 17 |
| all | removed | 45 | 36% | -0.2 | -34,470 | 29 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `fut_spread >= 2.6` | 53 / 66% / 18 | 0.407 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `fut_spread >= 2.6 AND ret_today < 81.85` | 48 / 73% / 13 | 0.323 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| C raw+derived single q5 | `fut_spread >= 2.6` | 53 / 66% / 18 | 0.473 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `fut_spread >= 2.6 AND ret_today < 81.85` | 48 / 73% / 13 | 0.443 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| E raw+text pair q5 | `fut_spread >= 2.6 AND ret_today < 81.85` | 48 / 73% / 13 | 0.357 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| F raw+derived greedy triple q5 | `fut_spread >= 2.6 AND ret_today < 81.85 AND fut_ttq60 >= 3120` | 43 / 79% / 9 | 0.300 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| G raw single q9 | `fut_spread >= 2.6` | 53 / 66% / 18 | 0.527 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `fut_spread >= 2.6 AND oi_net_help5 >= 4.611e+05` | 35 / 80% / 7 | 0.557 | 5 / 60% / 2 | +13,000 | shuffle, removed side profitable on holdout |
| I raw OR-pair q5 | `gap_pts < -76.72 AND oi_own_chg30 >= 2.769e+04` [OR] | 40 / 75% / 10 | 0.730 | 9 / 22% / 7 | +56,810 | shuffle, holdout win < book, removed side profitable on holdout |
| J derived-only pair q5 | `oi_help30_minus_5 < 6.366e+06 AND dir_x_e_syn_dev < 2.921` | 42 / 74% / 11 | 0.280 | 8 / 25% / 6 | +33,660 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `fut_spread >= 2.6 AND ret_today < 81.85` | 48 / 73% / 13 | 0.423 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| L raw+derived+text pair q5 min_keep 25 | `fut_spread >= 2.6 AND ret_today < 81.85` | 48 / 73% / 13 | 0.463 | 13 / 38% / 8 | +13,442 | shuffle, holdout win < book, removed side profitable on holdout |
| M raw+derived triple q9 | `e_syn_dev >= -2.35 AND oi_help30_minus_5 < 6.366e+06 AND lo_age_min < 220.8` | 35 / 86% / 5 | 0.323 | 6 / 50% / 3 | +19,688 | shuffle, removed side profitable on holdout |
| N text-only pair | `fut_opp_o=HOLDING < 1 AND opt_opp_o=REFILLING < 1` | 33 / 73% / 9 | 0.373 | 10 / 40% / 6 | +17,960 | shuffle, holdout win < book, removed side profitable on holdout |
| O raw pair by direction (CE | PE) | `fut_spread >= 2.6 AND regime_ext_pct < 94.7 AND is_ce < 0.5` | 21 / 86% / 3 | 0.387 | 5 / 0% / 5 | +52,975 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 6.366e+06` | 47 / 66% / 16 | 0.613 | 10 / 40% / 6 | +11,070 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.280). On the holdout days the book itself wins 43% (12 losers of 21); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## t28_ivfall

Record (79 trades; 195 raw numeric fields, 62 derived features, 62 text indicators searched):

- discovery: 61 trades, win 56%, mean +4.5 %, Rs +280,644, 27 losers
- holdout: 18 trades, win 50%, mean +2.5 %, Rs +38,552, 9 losers
- all: 79 trades, win 54%, mean +4.0 %, Rs +319,196, 36 losers

### Best rule by shuffle p — search A raw single q5

Search: best single clause, raw numeric photo fields, 5 quantile lines (10..90 %) both directions, min 20 kept (195 features, 1896 clause masks, 300 shufflings; shuffle median score 0.376, max 0.580, real 0.447).

### t28_ivfall: `e_syn_dev >= -0.51`

Shuffle test p = 0.103 (does NOT beat luck). 

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 61 | 56% | +4.5 | +280,644 | 27 |
| discovery | kept | 31 | 77% | +8.2 | +261,908 | 7 |
| discovery | removed | 30 | 33% | +0.7 | +18,736 | 20 |
| holdout | book | 18 | 50% | +2.5 | +38,552 | 9 |
| holdout | kept | 11 | 45% | -1.6 | -19,578 | 6 |
| holdout | removed | 7 | 57% | +8.8 | +58,130 | 3 |
| all | book | 79 | 54% | +4.0 | +319,196 | 36 |
| all | kept | 42 | 69% | +5.6 | +242,330 | 13 |
| all | removed | 37 | 38% | +2.2 | +76,866 | 23 |

### Everything tried (one line each; all REJECTED)

| search | rule | disc kept n / win / losers | p | hold kept n / win / losers | hold removed Rs | fails |
|---|---|---|---|---|---|---|
| A raw single q5 | `e_syn_dev >= -0.51` | 31 / 77% / 7 | 0.103 | 11 / 45% / 6 | +58,130 | shuffle, holdout win < book, removed side profitable on holdout |
| B raw pair q5 | `e_syn_dev >= -0.51 AND oi_net_help30 < 1.752e+07` | 28 / 86% / 4 | 0.220 | 8 / 38% / 5 | +65,663 | shuffle, holdout win < book, removed side profitable on holdout |
| C raw+derived single q5 | `e_syn_dev >= -0.51` | 31 / 77% / 7 | 0.133 | 11 / 45% / 6 | +58,130 | shuffle, holdout win < book, removed side profitable on holdout |
| D raw+derived pair q5 | `e_syn_dev >= -0.51 AND oi_net_help30 < 1.752e+07` | 28 / 86% / 4 | 0.287 | 8 / 38% / 5 | +65,663 | shuffle, holdout win < book, removed side profitable on holdout |
| E raw+text pair q5 | `e_syn_dev >= -0.51 AND oi_net_help30 < 1.752e+07` | 28 / 86% / 4 | 0.233 | 8 / 38% / 5 | +65,663 | shuffle, holdout win < book, removed side profitable on holdout |
| F raw+derived greedy triple q5 | `e_syn_dev >= -0.51 AND oi_net_help30 < 1.752e+07 AND gex_wall_ahead < 225.2` | 23 / 96% / 1 | 0.520 | 8 / 38% / 5 | +65,663 | shuffle, holdout win < book, removed side profitable on holdout |
| G raw single q9 | `e_syn_dev >= -0.51` | 31 / 77% / 7 | 0.153 | 11 / 45% / 6 | +58,130 | shuffle, holdout win < book, removed side profitable on holdout |
| H raw pair q9 | `chain_age >= 38 AND fut_spread >= 2.6` | 28 / 86% / 4 | 0.403 | 5 / 60% / 2 | +7,846 | shuffle, removed side profitable on holdout |
| I raw OR-pair q5 | `e_syn_dev >= -0.51 AND fut_imb_o < -0.167` [OR] | 42 / 76% / 10 | 0.157 | 12 / 50% / 6 | +51,162 | shuffle, removed side profitable on holdout |
| J derived-only pair q5 | `wmove60_minus_wmove30 >= -5.29 AND oi_help30_minus_5 < 1.438e+07` | 43 / 72% / 12 | 0.480 | 13 / 46% / 7 | +13,682 | shuffle, holdout win < book, removed side profitable on holdout |
| K raw+derived pair q5 min_keep 30 | `ep_age_s >= 9.26 AND fut_spread >= 2.6` | 36 / 78% / 8 | 0.413 | 10 / 50% / 5 | +21,414 | shuffle, removed side profitable on holdout |
| L raw+derived+text pair q5 min_keep 25 | `e_syn_dev >= -0.51 AND oi_net_help30 < 1.752e+07` | 28 / 86% / 4 | 0.287 | 8 / 38% / 5 | +65,663 | shuffle, holdout win < book, removed side profitable on holdout |
| M raw+derived triple q9 | `chain_age >= 38 AND fut_spread >= 2.6 AND ep_max_s < 0.7191` | 22 / 100% / 0 | 0.390 | 5 / 60% / 2 | +7,846 | shuffle, removed side profitable on holdout |
| N text-only pair | `ep_type=None < 1 AND opt_opp_o=REFILLING < 1` | 37 / 73% / 10 | 0.133 | 15 / 53% / 7 | -1,736 | shuffle |
| O raw pair by direction (CE | PE) | `fut_spread >= 2.6 AND regime_ext_pct < 96 AND is_ce < 0.5` | 20 / 85% / 3 | 0.153 | 4 / 0% / 4 | +72,582 | shuffle, holdout win < book, removed side profitable on holdout |
| P derived single q9 | `oi_help30_minus_5 < 7.864e+06` | 44 / 68% / 14 | 0.433 | 12 / 42% / 7 | +29,328 | shuffle, holdout win < book, removed side profitable on holdout |

### Reading

Does any rule honestly remove this book's losers? **No.** Every rule that looks clean on discovery (kept win 73–100 %, 0–11 losers) is matched or beaten by the same search on shuffled outcomes (best p = 0.103). On the holdout days the book itself wins 50% (9 losers of 18); the kept sides of the 'best' rules mostly win *less* than that and several lose money while the removed side makes it. The one recurring clause with a weak story — `fut_spread >= 2.6` (wider futures spread at the trigger) — carries p = 0.38–0.90 as a single and never passes as a pair. Nothing here is more than a memory of the tape.

**Verdict: NONE.**

## What was tried and failed (summary)

- Singles, AND-pairs, greedy AND-triples and OR-pairs over raw fields (5 and 9 quantile lines), 70 derived features (ratios such as mv60/rv15, premium/theta_be15, theta_be15/speed15; differences such as mv60-mv30, breadth_dir-0.5, oi_net_help30-oi_net_help5; products such as gamma*mv30, |delta|*mv60, vanna*vix_chg5, kv*kvt; 21 direction interactions dir*skew_atm, dir*pcr, dir*basis, dir*e_fut_ofi60 ...; |kvt|, |jump_z|, ln premium; hour / late_day buckets; within-day z-scores of premium, mv60, rv15, trig_str, vix, atm IV against the book's earlier trades that day; the book's win share so far today), 61 text indicators (regime, ep_type, gex_regime, fut/opt queue states, phase_bucket, strad_state ...), min_keep 20/25/30, and pair searches run separately on CE and PE trades.
- Every one of the 96 searches has p >= 0.09; 90 of 96 have p >= 0.15. Discovery-only 'perfect' rules exist (t28_ivfall M: 22 kept, 100 % win, p = 0.39) and are exactly what the shuffle test exists to catch.
- Not done: within-day ranks beyond z-scores, hold-time features (excluded by the brief), hmm_*/hk_* (excluded).

## Summary (10 lines)

1. t28_cheap: NONE — best ep_type=None < 1 AND phase_bucket=morning < 1 (search N); disc kept 72% / 10 losers; hold kept 50% / 4 losers (book 44%); p = 0.503
2. t28_nohigh: NONE — best e_syn_dev >= -1.464 AND oi_help30_minus_5 < 6.294e+06 (search K); disc kept 80% / 7 losers; hold kept 29% / 5 losers (book 40%); p = 0.503
3. t28_bidpile: NONE — best oi_help30_minus_5 < 6.793e+06 AND dir_x_e_syn_dev < 2.968 (search J); disc kept 75% / 10 losers; hold kept 25% / 6 losers (book 43%); p = 0.397
4. t28_req: NONE — best fut_spread >= 2.6 AND oi_own_chg5 < -1.109e+04 (search B); disc kept 81% / 7 losers; hold kept 56% / 4 losers (book 47%); p = 0.090
5. t28_gap: NONE — best oi_help30_minus_5 < 6.366e+06 AND dir_x_e_syn_dev < 2.921 (search J); disc kept 74% / 11 losers; hold kept 25% / 6 losers (book 43%); p = 0.280
6. t28_ivfall: NONE — best e_syn_dev >= -0.51 (search A); disc kept 77% / 7 losers; hold kept 45% / 6 losers (book 50%); p = 0.103
7. 96 searches, 300 shufflings each; minimum p = 0.090; no rule passes the shuffle test.
8. Books share 80–95 % of trades; the recurring clauses are one tape seen six times.
9. Holdout (3–6 Nov): the books themselves win 40–50 %; 'best' kept sides mostly win less and lose rupees.
10. Verdict: NONE for all six. No honest rule removes these books' losers from the trigger photograph.
