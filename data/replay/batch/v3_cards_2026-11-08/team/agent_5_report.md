# Agent 5 — rule search report (8 Nov 2026)

Books: t28_d46, t28_d46_fill, t28_gap_ts, t28_mh15, t28_st20, t28_ts, t28_tt8, t28_cheapK

Method (same for every book; every search was run only on the 10 discovery days 19 Oct – 2 Nov; holdout = 3, 4, 5, 6 Nov, never looked at while searching):
* features: 196 numeric weather fields (hmm_*/hk_* excluded) + text indicators (regime=, ep_type=, phase_bucket=, strad_state=, force_verdict=, gex_regime=, fut/opt_opp_q/o=, sl_next_res=, trig_unit=) + ~110 derived features: direction-signed versions (x CE/PE), absolutes, ratios (mv60/rv15, premium/theta_be15, trig_str/sigma15, ...), differences (er_day-er30, speed15-theta_be, |mv60|-theta_be15, breadth_dir-0.5), products (gamma*mv30, vega*atm_iv_chg5, delta*mv60, vanna*iv_chg5), moneyness, hour bucket, advisor vetoes as 0/1, boolean flags as 0/1, within-day z-scores of premium/speed15/rv5/IV/vix/sigma15/fut_vol60 against the book's EARLIER trades that day (>= 3 earlier trades, else missing). Code: search.py in this folder.
* seven searches per book, each shuffle-tested with 200 shufflings of the discovery outcomes using the SAME search: single clause on base; pair on base; single on base+derived; pair on base+derived; greedy triple on base+derived; pair with min_keep 30; single on derived-only with 9 quantile lines.
* score = share of losers removed minus share of winners removed (rule_lab.score_masks), min kept 20 on discovery.
* verdict PROPOSE only if: discovery kept >= 20, profitable in mean and rupees, removed losers > winners; p < 0.05; holdout kept win% >= holdout book win%, kept rupees > 0, removed rupees <= 0.

## t28_d46

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 79 | 49% | +3.3 | +274,316 | 40 |
| holdout | 21 | 48% | +1.3 | +27,034 | 11 |
| all | 100 | 49% | +2.8 | +301,350 | 51 |

Best rule (best candidate, REJECTED), found by search `triple-greedy/all351(base+derived)/5 lines/min_keep 20`:

### t28_d46: `oi_own_chg15 >= -1.106e+06 AND swing_behind >= 23.48 AND fut_spread >= 1.08`

Shuffle test p = 0.180 (does NOT beat luck). Shuffle median best score 0.542, max 0.646; real score 0.570. shuffle p=0.180 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+6).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 79 | 49% | +3.3 | +274,316 | 40 |
| discovery | kept | 40 | 78% | +9.0 | +389,129 | 9 |
| discovery | removed | 39 | 21% | -2.7 | -114,813 | 31 |
| holdout | book | 21 | 48% | +1.3 | +27,034 | 11 |
| holdout | kept | 8 | 62% | +3.4 | +27,027 | 3 |
| holdout | removed | 13 | 38% | -0.0 | +6 | 8 |
| all | book | 100 | 49% | +2.8 | +301,350 | 51 |
| all | kept | 48 | 75% | +8.1 | +416,156 | 12 |
| all | removed | 52 | 25% | -2.0 | -114,806 | 39 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `fut_spread >= 2.54` — single/base253(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 55 (33W/22L, +334,851), p=0.810; holdout kept 13 win 46% +15,675, removed 8 win 50% +11,359, book win 48% — **REJECTED**: shuffle p=0.810 >= 0.05: the same search finds this in random labels; holdout kept win 46% < book 48%
* `oi_own_chg15 >= -1.106e+06 AND swing_behind >= 23.48` — pair/base253/5 lines/min_keep 20/no truncation — disc kept 45 (31W/14L, +345,904), p=0.610; holdout kept 10 win 50% +9,558, removed 11 win 45% +17,475, book win 48% — **REJECTED**: shuffle p=0.610 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+17,475)
* `fut_spread >= 2.54` — single/all351(base+derived)/5 lines/min_keep 20 — disc kept 55 (33W/22L, +334,851), p=0.880; holdout kept 13 win 46% +15,675, removed 8 win 50% +11,359, book win 48% — **REJECTED**: shuffle p=0.880 >= 0.05: the same search finds this in random labels; holdout kept win 46% < book 48%
* `oi_own_chg15 >= -1.106e+06 AND swing_behind >= 23.48` — pair/all351(base+derived)/5 lines/min_keep 20/no truncation — disc kept 45 (31W/14L, +345,904), p=0.700; holdout kept 10 win 50% +9,558, removed 11 win 45% +17,475, book win 48% — **REJECTED**: shuffle p=0.700 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+17,475)
* `oi_own_chg15 >= -1.106e+06 AND swing_behind >= 23.48 AND fut_spread >= 1.08` — triple-greedy/all351(base+derived)/5 lines/min_keep 20 — disc kept 40 (31W/9L, +389,129), p=0.180; holdout kept 8 win 62% +27,027, removed 13 win 38% +6, book win 48% — **REJECTED**: shuffle p=0.180 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+6)
* `oi_own_chg15 >= -1.106e+06 AND swing_behind >= 23.48` — pair/all351(base+derived)/5 lines/min_keep 30 — disc kept 45 (31W/14L, +345,904), p=0.675; holdout kept 10 win 50% +9,558, removed 11 win 45% +17,475, book win 48% — **REJECTED**: shuffle p=0.675 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+17,475)
* `spread_over_prem >= 0.0194` — single/derived-only98/9 lines/min_keep 20 — disc kept 55 (33W/22L, +355,794), p=0.585; holdout kept 14 win 50% +20,095, removed 7 win 43% +6,939, book win 48% — **REJECTED**: shuffle p=0.585 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+6,939)
* `OR: agg_net >= 0.0868 | OR: vixchg15_over_vix >= -0.00115` — OR-of-two-clauses/all351/5 lines/min_keep 20 — disc kept 52 (34W/18L, +409,110), p=0.900; holdout kept 14 win 50% +17,446, removed 7 win 43% +9,588, book win 48% — **REJECTED**: shuffle p=0.900 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+9,588)
* `IF regime=DIRECTIONAL: opt_imb_chg30 < -0.003 | IF NOT regime=DIRECTIONAL: e_basis_dev >= -1.51` — either/or by regime=DIRECTIONAL: best single clause per half/all351/5 lines — disc kept 54 (35W/19L, +421,652), p=0.895; holdout kept 14 win 36% -14,651, removed 7 win 71% +41,684, book win 48% — **REJECTED**: shuffle p=0.895 >= 0.05: the same search finds this in random labels; holdout kept win 36% < book 48%
* `IF is_CE: oi_net_help5 >= 8.84e+05 | IF NOT is_CE: depth_age_fut >= 0.9` — either/or by is_CE: best single clause per half/all351/5 lines — disc kept 37 (28W/9L, +364,624), p=0.440; holdout kept 9 win 56% -6,659, removed 12 win 42% +33,693, book win 48% — **REJECTED**: shuffle p=0.440 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF phase_bucket=open30: e_syn_dev >= -1.4 | IF NOT phase_bucket=open30: oi_net_help5 >= 8.84e+05` — either/or by phase_bucket=open30: best single clause per half/all351/5 lines — disc kept 40 (28W/12L, +290,553), p=0.310; holdout kept 9 win 56% -5,408, removed 12 win 42% +32,442, book win 48% — **REJECTED**: shuffle p=0.310 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF b_expiry_day: kv_x_dir >= -0.0916 | IF NOT b_expiry_day: oi_net_help5 >= 8.84e+05` — either/or by b_expiry_day: best single clause per half/all351/5 lines — disc kept 51 (34W/17L, +423,579), p=0.775; holdout kept 12 win 42% -17,628, removed 9 win 56% +44,662, book win 48% — **REJECTED**: shuffle p=0.775 >= 0.05: the same search finds this in random labels; holdout kept win 42% < book 48%
* `IF adv_regime_veto: swing_behind >= 23.48 | IF NOT adv_regime_veto: abs_delta < 0.739` — either/or by adv_regime_veto: best single clause per half/all351/5 lines — disc kept 57 (34W/23L, +331,012), p=0.845; holdout kept 12 win 50% +6,523, removed 9 win 44% +20,511, book win 48% — **REJECTED**: shuffle p=0.845 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+20,511)

Reading: Nothing here is more than a memory of the tape. The best single clause (fut_spread >= 2.54, i.e. a wider futures spread at the trigger) is what a random labelling produces 81 % of the time; the best pair (oi_own_chg15 / swing_behind) and the greedy triple keep 31 winners and 9 losers on discovery but the same search finds that or better in random labels 18 % of the time, and on the four holdout days the triple keeps only 8 trades. No rule honestly removes this book's losers; its 40 discovery losers are spread across every field we photographed in the same way its 39 winners are.

**Verdict: NONE**

## t28_d46_fill

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 167 | 49% | +2.1 | +436,192 | 86 |
| holdout | 49 | 39% | -0.9 | -47,398 | 30 |
| all | 216 | 46% | +1.4 | +388,794 | 116 |

Best rule (best candidate, REJECTED), found by search `either/or by regime=DIRECTIONAL: best single clause per half/all358/5 lines`:

### t28_d46_fill: `IF regime=DIRECTIONAL: skew_atm >= 0.022 | IF NOT regime=DIRECTIONAL: round_dist < 74.21`

Shuffle test p = 0.320 (does NOT beat luck). Shuffle median best score 0.329, max 0.409; real score 0.343. shuffle p=0.320 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 39%.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 167 | 49% | +2.1 | +436,192 | 86 |
| discovery | kept | 88 | 65% | +5.2 | +526,906 | 31 |
| discovery | removed | 79 | 30% | -1.3 | -90,714 | 55 |
| holdout | book | 49 | 39% | -0.9 | -47,398 | 30 |
| holdout | kept | 26 | 38% | -0.9 | -21,898 | 16 |
| holdout | removed | 23 | 39% | -0.9 | -25,500 | 14 |
| all | book | 216 | 46% | +1.4 | +388,794 | 116 |
| all | kept | 114 | 59% | +3.8 | +505,008 | 47 |
| all | removed | 102 | 32% | -1.2 | -116,214 | 69 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `oi_net_help5 >= 1.901e+06` — single/base256(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 50 (33W/17L, +252,756), p=0.795; holdout kept 17 win 65% +33,520, removed 32 win 25% -80,918, book win 39% — **REJECTED**: shuffle p=0.795 >= 0.05: the same search finds this in random labels
* `gap_pts < 17.5 AND oi_own_chg30 >= -9.279e+05` — pair/base256/5 lines/min_keep 20/no truncation — disc kept 93 (57W/36L, +545,772), p=0.965; holdout kept 24 win 33% -41,392, removed 25 win 44% -6,006, book win 39% — **REJECTED**: shuffle p=0.965 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 39%
* `oi_net_help5 >= 1.901e+06` — single/all358(base+derived)/5 lines/min_keep 20 — disc kept 50 (33W/17L, +252,756), p=0.870; holdout kept 17 win 65% +33,520, removed 32 win 25% -80,918, book win 39% — **REJECTED**: shuffle p=0.870 >= 0.05: the same search finds this in random labels
* `e_fut_tot_imb_x_dir < -0.0158 AND ep_n_cross < 14` — pair/all358(base+derived)/5 lines/min_keep 20/no truncation — disc kept 78 (50W/28L, +494,725), p=0.955; holdout kept 2 win 0% -10,660, removed 47 win 40% -36,738, book win 39% — **REJECTED**: shuffle p=0.955 >= 0.05: the same search finds this in random labels; holdout kept win 0% < book 39%
* `e_fut_tot_imb_x_dir < -0.0158 AND ep_n_cross < 14 AND oi_other_chg5 >= -1.864e+05` — triple-greedy/all358(base+derived)/5 lines/min_keep 20 — disc kept 69 (49W/20L, +583,144), p=0.680; holdout kept 2 win 0% -10,660, removed 47 win 40% -36,738, book win 39% — **REJECTED**: shuffle p=0.680 >= 0.05: the same search finds this in random labels; holdout kept win 0% < book 39%
* `e_fut_tot_imb_x_dir < -0.0158 AND ep_n_cross < 14` — pair/all358(base+derived)/5 lines/min_keep 30 — disc kept 78 (50W/28L, +494,725), p=0.955; holdout kept 2 win 0% -10,660, removed 47 win 40% -36,738, book win 39% — **REJECTED**: shuffle p=0.955 >= 0.05: the same search finds this in random labels; holdout kept win 0% < book 39%
* `optiv_minus_atmiv_chg5 < 0.01` — single/derived-only102/9 lines/min_keep 20 — disc kept 99 (57W/42L, +395,554), p=0.620; holdout kept 26 win 27% -57,606, removed 23 win 52% +10,208, book win 39% — **REJECTED**: shuffle p=0.620 >= 0.05: the same search finds this in random labels; holdout kept win 27% < book 39%
* `OR: mv60_over_speed15 >= 1.782 | OR: oi_net_help5 >= 1.901e+06` — OR-of-two-clauses/all358/5 lines/min_keep 20 — disc kept 59 (41W/18L, +365,196), p=0.935; holdout kept 22 win 59% +28,906, removed 27 win 22% -76,304, book win 39% — **REJECTED**: shuffle p=0.935 >= 0.05: the same search finds this in random labels
* `IF regime=DIRECTIONAL: skew_atm >= 0.022 | IF NOT regime=DIRECTIONAL: round_dist < 74.21` — either/or by regime=DIRECTIONAL: best single clause per half/all358/5 lines — disc kept 88 (57W/31L, +526,906), p=0.320; holdout kept 26 win 38% -21,898, removed 23 win 39% -25,500, book win 39% — **REJECTED**: shuffle p=0.320 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 39%
* `IF is_CE: e_fut_micro >= 0.45 | IF NOT is_CE: e_v_min30 >= 75.71` — either/or by is_CE: best single clause per half/all358/5 lines — disc kept 70 (47W/23L, +473,671), p=0.795; holdout kept 17 win 41% -14,592, removed 32 win 38% -32,806, book win 39% — **REJECTED**: shuffle p=0.795 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF phase_bucket=open30: depth_age_fut >= 0.48 | IF NOT phase_bucket=open30: gex_flip_ahead >= -14.1` — either/or by phase_bucket=open30: best single clause per half/all358/5 lines — disc kept 88 (55W/33L, +518,472), p=0.485; holdout kept 23 win 43% -1,904, removed 26 win 35% -45,494, book win 39% — **REJECTED**: shuffle p=0.485 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF b_expiry_day: accel30_x_dir >= -0.2 | IF NOT b_expiry_day: gap_pts < -55.55` — either/or by b_expiry_day: best single clause per half/all358/5 lines — disc kept 65 (43W/22L, +612,040), p=0.965; holdout kept 10 win 30% -25,844, removed 39 win 41% -21,554, book win 39% — **REJECTED**: shuffle p=0.965 >= 0.05: the same search finds this in random labels; holdout kept win 30% < book 39%
* `IF adv_regime_veto: e_fut_micro_x_dir >= 0 | IF NOT adv_regime_veto: gaps_today < 4` — either/or by adv_regime_veto: best single clause per half/all358/5 lines — disc kept 87 (56W/31L, +525,837), p=0.395; holdout kept 28 win 46% -6,939, removed 21 win 29% -40,459, book win 39% — **REJECTED**: shuffle p=0.395 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees

Reading: The one book of mine that LOSES on holdout (49 trades, 39 % win, -47k). Every search's best rule is a luck-level find (p 0.3-0.97). oi_net_help5 >= 1.9m looks pretty on holdout (17 kept, 65 % win, +33.5k, removed -81k) but it is p = 0.80 on discovery: the search finds a clause this good in four random labellings out of five, so the holdout picture is one coin toss, not evidence. No proposal; the fill variant's extra trades are the ones the parent would not take, and nothing in the photograph tells them apart in a way that survives shuffling.

**Verdict: NONE**

## t28_gap_ts

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 74 | 53% | +4.3 | +342,199 | 35 |
| holdout | 21 | 43% | +1.0 | +14,306 | 12 |
| all | 95 | 51% | +3.6 | +356,506 | 47 |

Best rule (best candidate, REJECTED), found by search `either/or by phase_bucket=open30: best single clause per half/all352/5 lines`:

### t28_gap_ts: `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.393`

Shuffle test p = 0.040 (beats luck). Shuffle median best score 0.404, max 0.646; real score 0.498. holdout removed side is profitable (+13,254).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 74 | 53% | +4.3 | +342,199 | 35 |
| discovery | kept | 30 | 83% | +12.0 | +431,961 | 5 |
| discovery | removed | 44 | 32% | -0.9 | -89,762 | 30 |
| holdout | book | 21 | 43% | +1.0 | +14,306 | 12 |
| holdout | kept | 7 | 57% | +0.3 | +1,053 | 3 |
| holdout | removed | 14 | 36% | +1.3 | +13,254 | 9 |
| all | book | 95 | 51% | +3.6 | +356,506 | 47 |
| all | kept | 37 | 78% | +9.8 | +433,014 | 8 |
| all | removed | 58 | 33% | -0.4 | -76,508 | 39 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `oi_own_chg30 >= 2.769e+04` — single/base254(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 34 (24W/10L, +353,486), p=0.605; holdout kept 5 win 40% -16,178, removed 16 win 44% +30,485, book win 43% — **REJECTED**: shuffle p=0.605 >= 0.05: the same search finds this in random labels; holdout kept win 40% < book 43%
* `e_syn_dev >= -1.44 AND oi_own_chg30 >= 2.769e+04` — pair/base254/5 lines/min_keep 20/no truncation — disc kept 27 (23W/4L, +366,223), p=0.480; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.480 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `oi_own_chg30 >= 2.769e+04` — single/all352(base+derived)/5 lines/min_keep 20 — disc kept 34 (24W/10L, +353,486), p=0.690; holdout kept 5 win 40% -16,178, removed 16 win 44% +30,485, book win 43% — **REJECTED**: shuffle p=0.690 >= 0.05: the same search finds this in random labels; holdout kept win 40% < book 43%
* `e_syn_dev >= -1.44 AND oi_own_chg30 >= 2.769e+04` — pair/all352(base+derived)/5 lines/min_keep 20/no truncation — disc kept 27 (23W/4L, +366,223), p=0.630; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.630 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `e_syn_dev >= -1.44 AND oi_own_chg30 >= 2.769e+04 AND bn300 >= -0.1778` — triple-greedy/all352(base+derived)/5 lines/min_keep 20 — disc kept 25 (23W/2L, +382,346), p=0.770; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.770 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `fut_spread >= 2.6 AND ret_today < 81.85` — pair/all352(base+derived)/5 lines/min_keep 30 — disc kept 48 (34W/14L, +460,730), p=0.585; holdout kept 13 win 38% -604, removed 8 win 50% +14,911, book win 43% — **REJECTED**: shuffle p=0.585 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `spread_over_prem >= 0.01379` — single/derived-only98/9 lines/min_keep 20 — disc kept 59 (38W/21L, +452,104), p=0.165; holdout kept 14 win 43% +3,816, removed 7 win 43% +10,491, book win 43% — **REJECTED**: shuffle p=0.165 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+10,491)
* `OR: e_fut_micro_x_dir >= 0.393 | OR: oi_own_chg30 >= 1.42e+06` — OR-of-two-clauses/all352/5 lines/min_keep 20 — disc kept 36 (28W/8L, +452,052), p=0.460; holdout kept 8 win 50% -5,889, removed 13 win 38% +20,196, book win 43% — **REJECTED**: shuffle p=0.460 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF regime=DIRECTIONAL: pos_dir >= 0.5665 | IF NOT regime=DIRECTIONAL: skew_chg5_x_dir < 0.02` — either/or by regime=DIRECTIONAL: best single clause per half/all352/5 lines — disc kept 36 (27W/9L, +368,784), p=0.960; holdout kept 12 win 42% -3,539, removed 9 win 44% +17,846, book win 43% — **REJECTED**: shuffle p=0.960 >= 0.05: the same search finds this in random labels; holdout kept win 42% < book 43%
* `IF is_CE: oi_net_help5 >= 8.743e+05 | IF NOT is_CE: e_v_min30 >= 81.02` — either/or by is_CE: best single clause per half/all352/5 lines — disc kept 36 (28W/8L, +399,432), p=0.685; holdout kept 7 win 71% +27,076, removed 14 win 29% -12,769, book win 43% — **REJECTED**: shuffle p=0.685 >= 0.05: the same search finds this in random labels
* `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.393` — either/or by phase_bucket=open30: best single clause per half/all352/5 lines — disc kept 30 (25W/5L, +431,961), p=0.040; holdout kept 7 win 57% +1,053, removed 14 win 36% +13,254, book win 43% — **REJECTED**: holdout removed side is profitable (+13,254)
* `IF b_expiry_day: rv1_over_rv5 < 0.9038 | IF NOT b_expiry_day: oi_net_help5 >= 8.743e+05` — either/or by b_expiry_day: best single clause per half/all352/5 lines — disc kept 35 (27W/8L, +381,082), p=0.855; holdout kept 3 win 67% +5,440, removed 18 win 39% +8,866, book win 43% — **REJECTED**: shuffle p=0.855 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+8,866)
* `IF adv_regime_veto: streak < 1 | IF NOT adv_regime_veto: abs_delta < 0.7415` — either/or by adv_regime_veto: best single clause per half/all352/5 lines — disc kept 43 (29W/14L, +287,046), p=0.580; holdout kept 14 win 43% +5,421, removed 7 win 43% +8,886, book win 43% — **REJECTED**: shuffle p=0.580 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+8,886)

Reading: Nearest miss of the whole set: the either/or rule 'open30 -> e_syn_dev >= -1.44, otherwise e_fut_micro_x_dir >= 0.39' (synthetic not below fair in the first half hour; futures microprice leaning our way later) keeps 25W/5L on discovery with p = 0.04, and on holdout its kept side wins 57 % against the book's 43 %. But the kept side makes only +1k on the four days and the REMOVED side makes +13k, so the rule throws away more money than it keeps; and p = 0.04 was found among 13 searches on this book, which is about what multiplicity alone would deliver. Rejected. All other rules p >= 0.17.

**Verdict: NONE**

## t28_mh15

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 79 | 53% | +3.1 | +263,276 | 37 |
| holdout | 21 | 52% | +1.4 | +21,265 | 10 |
| all | 100 | 53% | +2.8 | +284,541 | 47 |

Best rule (best candidate, REJECTED), found by search `single/derived-only98/9 lines/min_keep 20`:

### t28_mh15: `vixchg15_over_vix >= -0.00115`

Shuffle test p = 0.075 (does NOT beat luck). Shuffle median best score 0.306, max 0.465; real score 0.393. shuffle p=0.075 >= 0.05: the same search finds this in random labels.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 79 | 53% | +3.1 | +263,276 | 37 |
| discovery | kept | 40 | 72% | +6.7 | +280,742 | 11 |
| discovery | removed | 39 | 33% | -0.5 | -17,466 | 26 |
| holdout | book | 21 | 52% | +1.4 | +21,265 | 10 |
| holdout | kept | 11 | 64% | +3.3 | +29,929 | 4 |
| holdout | removed | 10 | 40% | -0.8 | -8,664 | 6 |
| all | book | 100 | 53% | +2.8 | +284,541 | 47 |
| all | kept | 51 | 71% | +6.0 | +310,671 | 15 |
| all | removed | 49 | 35% | -0.6 | -26,130 | 32 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `hw_book_chg30 < -0.0096` — single/base253(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 24 (19W/5L, +160,206), p=0.710; holdout kept 9 win 44% -11,420, removed 12 win 58% +32,685, book win 52% — **REJECTED**: shuffle p=0.710 >= 0.05: the same search finds this in random labels; holdout kept win 44% < book 52%
* `fut_spread >= 2.6 AND oi_own_chg5 < -1.299e+04` — pair/base253/5 lines/min_keep 20/no truncation — disc kept 43 (32W/11L, +324,682), p=0.430; holdout kept 10 win 60% +19,750, removed 11 win 45% +1,514, book win 52% — **REJECTED**: shuffle p=0.430 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+1,514)
* `vixchg15_over_vix >= -0.00115` — single/all351(base+derived)/5 lines/min_keep 20 — disc kept 40 (29W/11L, +280,742), p=0.145; holdout kept 11 win 64% +29,929, removed 10 win 40% -8,664, book win 52% — **REJECTED**: shuffle p=0.145 >= 0.05: the same search finds this in random labels
* `ret_today < 81.73 AND vixchg15_over_vix >= -0.00115` — pair/all351(base+derived)/5 lines/min_keep 20/no truncation — disc kept 35 (29W/6L, +348,264), p=0.120; holdout kept 11 win 64% +29,929, removed 10 win 40% -8,664, book win 52% — **REJECTED**: shuffle p=0.120 >= 0.05: the same search finds this in random labels
* `ret_today < 81.73 AND vixchg15_over_vix >= -0.00115 AND spread_pct >= 0.129` — triple-greedy/all351(base+derived)/5 lines/min_keep 20 — disc kept 31 (28W/3L, +331,172), p=0.170; holdout kept 9 win 67% +38,243, removed 12 win 42% -16,978, book win 52% — **REJECTED**: shuffle p=0.170 >= 0.05: the same search finds this in random labels
* `ret_today < 81.73 AND vixchg15_over_vix >= -0.00115` — pair/all351(base+derived)/5 lines/min_keep 30 — disc kept 35 (29W/6L, +348,264), p=0.110; holdout kept 11 win 64% +29,929, removed 10 win 40% -8,664, book win 52% — **REJECTED**: shuffle p=0.110 >= 0.05: the same search finds this in random labels
* `vixchg15_over_vix >= -0.00115` — single/derived-only98/9 lines/min_keep 20 — disc kept 40 (29W/11L, +280,742), p=0.075; holdout kept 11 win 64% +29,929, removed 10 win 40% -8,664, book win 52% — **REJECTED**: shuffle p=0.075 >= 0.05: the same search finds this in random labels
* `OR: basis_chg300 >= 6.77 | OR: vixchg15_over_vix >= -0.00115` — OR-of-two-clauses/all351/5 lines/min_keep 20 — disc kept 45 (34W/11L, +384,098), p=0.150; holdout kept 13 win 54% +19,269, removed 8 win 50% +1,996, book win 52% — **REJECTED**: shuffle p=0.150 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+1,996)
* `IF regime=DIRECTIONAL: pos_dir >= 0.5443 | IF NOT regime=DIRECTIONAL: moneyness_pts >= 51.57` — either/or by regime=DIRECTIONAL: best single clause per half/all351/5 lines — disc kept 48 (35W/13L, +371,530), p=0.490; holdout kept 15 win 47% -12,763, removed 6 win 67% +34,028, book win 52% — **REJECTED**: shuffle p=0.490 >= 0.05: the same search finds this in random labels; holdout kept win 47% < book 52%
* `IF is_CE: atm_iv_chg1 >= 0.03 | IF NOT is_CE: svi_res >= 0.01` — either/or by is_CE: best single clause per half/all351/5 lines — disc kept 39 (30W/9L, +378,320), p=0.630; holdout kept 8 win 38% -8,054, removed 13 win 62% +29,318, book win 52% — **REJECTED**: shuffle p=0.630 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 52%
* `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: vixchg15_over_vix >= -0.00115` — either/or by phase_bucket=open30: best single clause per half/all351/5 lines — disc kept 41 (31W/10L, +337,162), p=0.085; holdout kept 10 win 70% +39,939, removed 11 win 36% -18,674, book win 52% — **REJECTED**: shuffle p=0.085 >= 0.05: the same search finds this in random labels
* `IF b_expiry_day: rv1_over_rv5 < 0.9056 | IF NOT b_expiry_day: vixchg15_over_vix >= -0.00115` — either/or by b_expiry_day: best single clause per half/all351/5 lines — disc kept 36 (29W/7L, +315,536), p=0.365; holdout kept 10 win 60% +21,902, removed 11 win 45% -637, book win 52% — **REJECTED**: shuffle p=0.365 >= 0.05: the same search finds this in random labels
* `IF adv_regime_veto: vixchg15_over_vix >= -0.00115 | IF NOT adv_regime_veto: abs_delta < 0.739` — either/or by adv_regime_veto: best single clause per half/all351/5 lines — disc kept 42 (29W/13L, +254,550), p=0.520; holdout kept 12 win 58% +22,909, removed 9 win 44% -1,644, book win 52% — **REJECTED**: shuffle p=0.520 >= 0.05: the same search finds this in random labels

Reading: The recurring clause is vixchg15_over_vix >= -0.00115 (VIX not falling over the last 15 min, as a share of VIX). On discovery 29W/11L, holdout kept 11 trades at 64 % vs the book's 52 %, +29.9k kept, -8.7k removed: everything the owner would want, EXCEPT that the shuffle test gives p = 0.075-0.145 depending on the search width, and the either/or variant with e_syn_dev in the open30 bucket gives p = 0.085 (holdout 70 %, +39.9k). It fails the honesty bar by a small margin and with only 11 holdout trades; worth re-testing when more days exist, not proposing today.

**Verdict: NONE**

## t28_st20

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 74 | 54% | +4.2 | +318,766 | 34 |
| holdout | 21 | 43% | -0.1 | -5,359 | 12 |
| all | 95 | 52% | +3.3 | +313,407 | 46 |

Best rule (best candidate, REJECTED), found by search `either/or by phase_bucket=open30: best single clause per half/all352/5 lines`:

### t28_st20: `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.3`

Shuffle test p = 0.010 (beats luck). Shuffle median best score 0.416, max 0.540; real score 0.532. holdout kept side loses rupees.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 74 | 54% | +4.2 | +318,766 | 34 |
| discovery | kept | 30 | 87% | +11.8 | +392,298 | 4 |
| discovery | removed | 44 | 32% | -1.0 | -73,531 | 30 |
| holdout | book | 21 | 43% | -0.1 | -5,359 | 12 |
| holdout | kept | 7 | 57% | -0.2 | -3,351 | 3 |
| holdout | removed | 14 | 36% | -0.1 | -2,008 | 9 |
| all | book | 95 | 52% | +3.3 | +313,407 | 46 |
| all | kept | 37 | 81% | +9.6 | +388,947 | 7 |
| all | removed | 58 | 33% | -0.8 | -75,540 | 39 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `fut_spread >= 2.6` — single/base254(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 53 (37W/16L, +432,448), p=0.010; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: holdout kept win 38% < book 43%
* `fut_spread >= 2.6 AND fut_ttq60 >= 3120` — pair/base254/5 lines/min_keep 20/no truncation — disc kept 48 (36W/12L, +451,146), p=0.080; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: shuffle p=0.080 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `fut_spread >= 2.6` — single/all352(base+derived)/5 lines/min_keep 20 — disc kept 53 (37W/16L, +432,448), p=0.020; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: holdout kept win 38% < book 43%
* `abs_delta >= 0.53 AND fut_spread >= 2.6` — pair/all352(base+derived)/5 lines/min_keep 20/no truncation — disc kept 46 (35W/11L, +466,846), p=0.085; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: shuffle p=0.085 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `abs_delta >= 0.53 AND fut_spread >= 2.6 AND hw_book_imb_t >= -0.33` — triple-greedy/all352(base+derived)/5 lines/min_keep 20 — disc kept 40 (33W/7L, +470,863), p=0.120; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: shuffle p=0.120 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `abs_delta >= 0.53 AND fut_spread >= 2.6` — pair/all352(base+derived)/5 lines/min_keep 30 — disc kept 46 (35W/11L, +466,846), p=0.075; holdout kept 13 win 38% -14,654, removed 8 win 50% +9,295, book win 43% — **REJECTED**: shuffle p=0.075 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `spread_over_prem >= 0.01379` — single/derived-only98/9 lines/min_keep 20 — disc kept 59 (40W/19L, +466,820), p=0.040; holdout kept 14 win 43% -9,376, removed 7 win 43% +4,017, book win 43% — **REJECTED**: holdout kept side loses rupees
* `OR: b_ep_with >= 1 | OR: e_fut_micro_x_dir >= 0.3` — OR-of-two-clauses/all352/5 lines/min_keep 20 — disc kept 43 (33W/10L, +428,431), p=0.200; holdout kept 11 win 45% -21,453, removed 10 win 40% +16,094, book win 43% — **REJECTED**: shuffle p=0.200 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF regime=DIRECTIONAL: pos_dir >= 0.5665 | IF NOT regime=DIRECTIONAL: fut_spread >= 2.6` — either/or by regime=DIRECTIONAL: best single clause per half/all352/5 lines — disc kept 45 (34W/11L, +436,017), p=0.245; holdout kept 13 win 38% -15,028, removed 8 win 50% +9,669, book win 43% — **REJECTED**: shuffle p=0.245 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `IF is_CE: quote_age >= 0.44 | IF NOT is_CE: fut_spread >= 2.6` — either/or by is_CE: best single clause per half/all352/5 lines — disc kept 43 (34W/9L, +484,250), p=0.050; holdout kept 11 win 45% -10,075, removed 10 win 40% +4,716, book win 43% — **REJECTED**: shuffle p=0.050 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.3` — either/or by phase_bucket=open30: best single clause per half/all352/5 lines — disc kept 30 (26W/4L, +392,298), p=0.010; holdout kept 7 win 57% -3,351, removed 14 win 36% -2,008, book win 43% — **REJECTED**: holdout kept side loses rupees
* `IF b_expiry_day: fut_spread >= 2.6 | IF NOT b_expiry_day: oi_net_help5 >= 8.743e+05` — either/or by b_expiry_day: best single clause per half/all352/5 lines — disc kept 46 (34W/12L, +409,367), p=0.545; holdout kept 9 win 33% -26,627, removed 12 win 50% +21,268, book win 43% — **REJECTED**: shuffle p=0.545 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 43%
* `IF adv_regime_veto: fut_spread >= 2.6 | IF NOT adv_regime_veto: abs_delta < 0.7415` — either/or by adv_regime_veto: best single clause per half/all352/5 lines — disc kept 53 (37W/16L, +443,885), p=0.040; holdout kept 12 win 42% -4,631, removed 9 win 44% -728, book win 43% — **REJECTED**: holdout kept win 42% < book 43%

Reading: fut_spread >= 2.6 is the single clause that beats luck on discovery (p = 0.01-0.02; 37W/16L kept) and so does spread_over_prem (p = 0.04), and the either/or 'open30 -> e_syn_dev, else e_fut_micro_x_dir' (p = 0.01). Every one of them then LOSES on holdout: fut_spread's kept side wins 38 % against the book's 43 % and gives back -14.7k while the removed 8 trades make +9.3k; the either/or keeps 7 trades at 57 % but -3.4k. A clean textbook case of a discovery pattern that did not carry: the wide-spread trades of 19 Oct - 2 Nov were the winners, those of 3-6 Nov were not. Rejected on holdout.

**Verdict: NONE**

## t28_ts

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 76 | 51% | +4.2 | +339,563 | 37 |
| holdout | 21 | 43% | +1.0 | +14,306 | 12 |
| all | 97 | 49% | +3.5 | +353,870 | 49 |

Best rule (best candidate, REJECTED), found by search `either/or by phase_bucket=open30: best single clause per half/all349/5 lines`:

### t28_ts: `IF phase_bucket=open30: e_syn_dev >= -1.39 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.34`

Shuffle test p = 0.080 (does NOT beat luck). Shuffle median best score 0.400, max 0.581; real score 0.479. shuffle p=0.080 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+13,254).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 76 | 51% | +4.2 | +339,563 | 37 |
| discovery | kept | 31 | 81% | +11.3 | +411,034 | 6 |
| discovery | removed | 45 | 31% | -0.7 | -71,471 | 31 |
| holdout | book | 21 | 43% | +1.0 | +14,306 | 12 |
| holdout | kept | 7 | 57% | +0.3 | +1,053 | 3 |
| holdout | removed | 14 | 36% | +1.3 | +13,254 | 9 |
| all | book | 97 | 49% | +3.5 | +353,870 | 49 |
| all | kept | 38 | 76% | +9.3 | +412,087 | 9 |
| all | removed | 59 | 32% | -0.2 | -58,217 | 40 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `oi_own_chg30 >= -7605` — single/base252(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 35 (25W/10L, +363,334), p=0.200; holdout kept 5 win 40% -16,178, removed 16 win 44% +30,485, book win 43% — **REJECTED**: shuffle p=0.200 >= 0.05: the same search finds this in random labels; holdout kept win 40% < book 43%
* `e_syn_dev >= -1.39 AND oi_own_chg30 >= -7605` — pair/base252/5 lines/min_keep 20/no truncation — disc kept 27 (23W/4L, +366,223), p=0.285; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.285 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `oi_own_chg30 >= -7605` — single/all349(base+derived)/5 lines/min_keep 20 — disc kept 35 (25W/10L, +363,334), p=0.265; holdout kept 5 win 40% -16,178, removed 16 win 44% +30,485, book win 43% — **REJECTED**: shuffle p=0.265 >= 0.05: the same search finds this in random labels; holdout kept win 40% < book 43%
* `e_syn_dev >= -1.39 AND oi_own_chg30 >= -7605` — pair/all349(base+derived)/5 lines/min_keep 20/no truncation — disc kept 27 (23W/4L, +366,223), p=0.415; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.415 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `e_syn_dev >= -1.39 AND oi_own_chg30 >= -7605 AND bn300 >= -0.1825` — triple-greedy/all349(base+derived)/5 lines/min_keep 20 — disc kept 25 (23W/2L, +382,346), p=0.570; holdout kept 4 win 50% -9,236, removed 17 win 41% +23,543, book win 43% — **REJECTED**: shuffle p=0.570 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `fut_spread >= 2.6 AND ret_today < 81.8` — pair/all349(base+derived)/5 lines/min_keep 30 — disc kept 49 (34W/15L, +459,752), p=0.605; holdout kept 13 win 38% -604, removed 8 win 50% +14,911, book win 43% — **REJECTED**: shuffle p=0.605 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 43%
* `spread_over_prem >= 0.01301` — single/derived-only97/9 lines/min_keep 20 — disc kept 61 (38W/23L, +442,049), p=0.230; holdout kept 14 win 43% +3,816, removed 7 win 43% +10,491, book win 43% — **REJECTED**: shuffle p=0.230 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+10,491)
* `OR: e_fut_micro_x_dir >= 1.68 | OR: oi_own_chg30 >= -7605` — OR-of-two-clauses/all349/5 lines/min_keep 20 — disc kept 40 (30W/10L, +423,449), p=0.370; holdout kept 6 win 33% -24,252, removed 15 win 47% +38,558, book win 43% — **REJECTED**: shuffle p=0.370 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 43%
* `IF regime=DIRECTIONAL: oi_own_chg30 >= -7605 | IF NOT regime=DIRECTIONAL: skew_chg5_x_dir < 0.02` — either/or by regime=DIRECTIONAL: best single clause per half/all349/5 lines — disc kept 35 (26W/9L, +359,460), p=0.980; holdout kept 7 win 29% -34,508, removed 14 win 50% +48,815, book win 43% — **REJECTED**: shuffle p=0.980 >= 0.05: the same search finds this in random labels; holdout kept win 29% < book 43%
* `IF is_CE: oi_net_help5 >= 7.879e+05 | IF NOT is_CE: depth_age_fut >= 0.85` — either/or by is_CE: best single clause per half/all349/5 lines — disc kept 37 (28W/9L, +391,752), p=0.670; holdout kept 9 win 44% -17,264, removed 12 win 42% +31,570, book win 43% — **REJECTED**: shuffle p=0.670 >= 0.05: the same search finds this in random labels; holdout kept side loses rupees
* `IF phase_bucket=open30: e_syn_dev >= -1.39 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.34` — either/or by phase_bucket=open30: best single clause per half/all349/5 lines — disc kept 31 (25W/6L, +411,034), p=0.080; holdout kept 7 win 57% +1,053, removed 14 win 36% +13,254, book win 43% — **REJECTED**: shuffle p=0.080 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+13,254)
* `IF b_expiry_day: absmv60_minus_thetabe15 >= -3.915 | IF NOT b_expiry_day: oi_other_chg5 >= 1.088e+05` — either/or by b_expiry_day: best single clause per half/all349/5 lines — disc kept 32 (25W/7L, +365,632), p=0.860; holdout kept 9 win 33% -28,288, removed 12 win 50% +42,594, book win 43% — **REJECTED**: shuffle p=0.860 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 43%
* `IF adv_regime_veto: fut_spread >= 2.6 | IF NOT adv_regime_veto: abs_delta < 0.7405` — either/or by adv_regime_veto: best single clause per half/all349/5 lines — disc kept 54 (34W/20L, +393,464), p=0.690; holdout kept 12 win 42% +956, removed 9 win 44% +13,351, book win 43% — **REJECTED**: shuffle p=0.690 >= 0.05: the same search finds this in random labels; holdout kept win 42% < book 43%

Reading: Nothing beats luck (best p = 0.08 for the open30 either/or, which keeps 7 holdout trades for +1k while the removed 14 make +13k). oi_own_chg30 >= -7605 (own-strike OI not falling) keeps 25W/10L on discovery, p = 0.20, and on holdout keeps 5 trades at 40 % for -16k while the removed 16 make +30k: the opposite of what a rule should do. No proposal.

**Verdict: NONE**

## t28_tt8

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 79 | 59% | +2.3 | +195,358 | 32 |
| holdout | 21 | 52% | +1.7 | +27,264 | 10 |
| all | 100 | 58% | +2.2 | +222,622 | 42 |

Best rule (best candidate, REJECTED), found by search `either/or by phase_bucket=open30: best single clause per half/all352/5 lines`:

### t28_tt8: `IF phase_bucket=open30: e_syn_dev >= -1.47 | IF NOT phase_bucket=open30: ep_age_s >= 109.4`

Shuffle test p = 0.110 (does NOT beat luck). Shuffle median best score 0.410, max 0.536; real score 0.472. shuffle p=0.110 >= 0.05: the same search finds this in random labels; holdout kept win 44% < book 52%.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 79 | 59% | +2.3 | +195,358 | 32 |
| discovery | kept | 37 | 84% | +6.7 | +265,171 | 6 |
| discovery | removed | 42 | 38% | -1.5 | -69,813 | 26 |
| holdout | book | 21 | 52% | +1.7 | +27,264 | 10 |
| holdout | kept | 9 | 44% | +1.2 | +5,431 | 5 |
| holdout | removed | 12 | 58% | +2.1 | +21,834 | 5 |
| all | book | 100 | 58% | +2.2 | +222,622 | 42 |
| all | kept | 46 | 76% | +5.6 | +270,602 | 11 |
| all | removed | 54 | 43% | -0.7 | -47,980 | 31 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `hw_book_chg30 < -0.01` — single/base254(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 23 (20W/3L, +135,418), p=0.505; holdout kept 8 win 50% -1,046, removed 13 win 54% +28,311, book win 52% — **REJECTED**: shuffle p=0.505 >= 0.05: the same search finds this in random labels; holdout kept win 50% < book 52%
* `regime_ext_pct < 94.2 AND opt_opp_o=REFILLING < 1` — pair/base254/5 lines/min_keep 20/no truncation — disc kept 47 (36W/11L, +290,693), p=0.885; holdout kept 17 win 53% +24,856, removed 4 win 50% +2,408, book win 52% — **REJECTED**: shuffle p=0.885 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+2,408)
* `hw_book_chg30 < -0.01` — single/all352(base+derived)/5 lines/min_keep 20 — disc kept 23 (20W/3L, +135,418), p=0.590; holdout kept 8 win 50% -1,046, removed 13 win 54% +28,311, book win 52% — **REJECTED**: shuffle p=0.590 >= 0.05: the same search finds this in random labels; holdout kept win 50% < book 52%
* `iv_minus_rv < 19.08 AND opt_opp_o=REFILLING < 1` — pair/all352(base+derived)/5 lines/min_keep 20/no truncation — disc kept 35 (30W/5L, +241,267), p=0.500; holdout kept 15 win 60% +40,700, removed 6 win 33% -13,436, book win 52% — **REJECTED**: shuffle p=0.500 >= 0.05: the same search finds this in random labels
* `iv_minus_rv < 19.08 AND opt_opp_o=REFILLING < 1 AND po_b < 37.82` — triple-greedy/all352(base+derived)/5 lines/min_keep 20 — disc kept 32 (29W/3L, +256,019), p=0.730; holdout kept 14 win 57% +21,089, removed 7 win 43% +6,175, book win 52% — **REJECTED**: shuffle p=0.730 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+6,175)
* `iv_minus_rv < 19.08 AND opt_opp_o=REFILLING < 1` — pair/all352(base+derived)/5 lines/min_keep 30 — disc kept 35 (30W/5L, +241,267), p=0.490; holdout kept 15 win 60% +40,700, removed 6 win 33% -13,436, book win 52% — **REJECTED**: shuffle p=0.490 >= 0.05: the same search finds this in random labels
* `vixchg15_over_vix >= -0.00115` — single/derived-only98/9 lines/min_keep 20 — disc kept 40 (30W/10L, +239,577), p=0.400; holdout kept 11 win 64% +38,035, removed 10 win 40% -10,770, book win 52% — **REJECTED**: shuffle p=0.400 >= 0.05: the same search finds this in random labels
* `OR: e_fut_micro_x_dir >= 0.262 | OR: e_rv15 >= 12.11` — OR-of-two-clauses/all352/5 lines/min_keep 20 — disc kept 43 (35W/8L, +308,480), p=0.375; holdout kept 8 win 62% +5,483, removed 13 win 46% +21,782, book win 52% — **REJECTED**: shuffle p=0.375 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+21,782)
* `IF regime=DIRECTIONAL: pos_dir >= 0.5443 | IF NOT regime=DIRECTIONAL: e_basis_dev >= 0.85` — either/or by regime=DIRECTIONAL: best single clause per half/all352/5 lines — disc kept 43 (35W/8L, +321,097), p=0.465; holdout kept 13 win 54% +12,061, removed 8 win 50% +15,204, book win 52% — **REJECTED**: shuffle p=0.465 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+15,204)
* `IF is_CE: opt_opp_o=REFILLING < 1 | IF NOT is_CE: moneyness_pts >= 51.57` — either/or by is_CE: best single clause per half/all352/5 lines — disc kept 54 (41W/13L, +312,890), p=0.765; holdout kept 16 win 44% -2,857, removed 5 win 80% +30,121, book win 52% — **REJECTED**: shuffle p=0.765 >= 0.05: the same search finds this in random labels; holdout kept win 44% < book 52%
* `IF phase_bucket=open30: e_syn_dev >= -1.47 | IF NOT phase_bucket=open30: ep_age_s >= 109.4` — either/or by phase_bucket=open30: best single clause per half/all352/5 lines — disc kept 37 (31W/6L, +265,171), p=0.110; holdout kept 9 win 44% +5,431, removed 12 win 58% +21,834, book win 52% — **REJECTED**: shuffle p=0.110 >= 0.05: the same search finds this in random labels; holdout kept win 44% < book 52%
* `IF b_expiry_day: rv1_over_rv5 < 0.9056 | IF NOT b_expiry_day: opt_opp_o=REFILLING < 1` — either/or by b_expiry_day: best single clause per half/all352/5 lines — disc kept 40 (33W/7L, +273,621), p=0.520; holdout kept 11 win 73% +45,835, removed 10 win 30% -18,570, book win 52% — **REJECTED**: shuffle p=0.520 >= 0.05: the same search finds this in random labels
* `IF adv_regime_veto: hw_book_chg30 < -0.01 | IF NOT adv_regime_veto: abs_delta < 0.739` — either/or by adv_regime_veto: best single clause per half/all352/5 lines — disc kept 28 (23W/5L, +167,580), p=0.685; holdout kept 10 win 60% +3,175, removed 11 win 45% +24,089, book win 52% — **REJECTED**: shuffle p=0.685 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+24,089)

Reading: The best-winning book of mine (58 % overall) and the hardest to improve: its discovery losers (33 of 79) look like its winners in every field. Best p = 0.11 (open30 either/or), the AND rules all p >= 0.4. 'iv_minus_rv < 19 AND opt_opp_o != REFILLING' keeps 30W/5L on discovery and 60 % / +40.7k on holdout with the removed side -13.4k, but p = 0.49: half of all random labellings produce a pair this good. Holdout agreement after a p = 0.49 discovery is a coin that landed right, not a rule. No proposal.

**Verdict: NONE**

## t28_cheapK

Book record:

| window | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|
| discovery | 74 | 55% | +4.6 | +388,888 | 33 |
| holdout | 20 | 40% | +1.5 | +22,162 | 12 |
| all | 94 | 52% | +3.9 | +411,050 | 45 |

Best rule (best candidate, REJECTED), found by search `either/or by phase_bucket=open30: best single clause per half/all350/5 lines`:

### t28_cheapK: `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.3`

Shuffle test p = 0.240 (does NOT beat luck). Shuffle median best score 0.418, max 0.593; real score 0.458. shuffle p=0.240 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+16,559).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 74 | 55% | +4.6 | +388,888 | 33 |
| discovery | kept | 30 | 83% | +11.4 | +417,807 | 5 |
| discovery | removed | 44 | 36% | -0.1 | -28,918 | 28 |
| holdout | book | 20 | 40% | +1.5 | +22,162 | 12 |
| holdout | kept | 7 | 43% | +0.8 | +5,603 | 4 |
| holdout | removed | 13 | 38% | +1.9 | +16,559 | 8 |
| all | book | 94 | 52% | +3.9 | +411,050 | 45 |
| all | kept | 37 | 76% | +9.4 | +423,410 | 9 |
| all | removed | 57 | 37% | +0.4 | -12,360 | 36 |

Every search and its result (discovery kept W/L, p, holdout kept win% / rupees, verdict):

* `basis_chg300 >= 0.4` — single/base253(196 numeric+text indicators)/5 quantile lines/min_keep 20 — disc kept 37 (26W/11L, +414,576), p=0.900; holdout kept 10 win 30% -31,850, removed 10 win 50% +54,012, book win 40% — **REJECTED**: shuffle p=0.900 >= 0.05: the same search finds this in random labels; holdout kept win 30% < book 40%
* `fut_spread >= 2.6 AND ret_today < 104.8` — pair/base253/5 lines/min_keep 20/no truncation — disc kept 49 (35W/14L, +517,088), p=0.940; holdout kept 12 win 33% +6,536, removed 8 win 50% +15,626, book win 40% — **REJECTED**: shuffle p=0.940 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 40%
* `basis_chg300 >= 0.4` — single/all350(base+derived)/5 lines/min_keep 20 — disc kept 37 (26W/11L, +414,576), p=0.950; holdout kept 10 win 30% -31,850, removed 10 win 50% +54,012, book win 40% — **REJECTED**: shuffle p=0.950 >= 0.05: the same search finds this in random labels; holdout kept win 30% < book 40%
* `accel30_x_dir >= -1.055 AND swing_behind >= 25.09` — pair/all350(base+derived)/5 lines/min_keep 20/no truncation — disc kept 35 (28W/7L, +526,624), p=0.770; holdout kept 7 win 57% +24,118, removed 13 win 31% -1,956, book win 40% — **REJECTED**: shuffle p=0.770 >= 0.05: the same search finds this in random labels
* `accel30_x_dir >= -1.055 AND swing_behind >= 25.09 AND fut_imb_t_chg30 >= -0.0444` — triple-greedy/all350(base+derived)/5 lines/min_keep 20 — disc kept 29 (26W/3L, +490,682), p=0.730; holdout kept 7 win 57% +24,118, removed 13 win 31% -1,956, book win 40% — **REJECTED**: shuffle p=0.730 >= 0.05: the same search finds this in random labels
* `accel30_x_dir >= -1.055 AND swing_behind >= 25.09` — pair/all350(base+derived)/5 lines/min_keep 30 — disc kept 35 (28W/7L, +526,624), p=0.750; holdout kept 7 win 57% +24,118, removed 13 win 31% -1,956, book win 40% — **REJECTED**: shuffle p=0.750 >= 0.05: the same search finds this in random labels
* `spread_over_prem >= 0.01305` — single/derived-only97/9 lines/min_keep 20 — disc kept 59 (39W/20L, +518,216), p=0.465; holdout kept 13 win 38% +10,023, removed 7 win 43% +12,139, book win 40% — **REJECTED**: shuffle p=0.465 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 40%
* `OR: agg_net >= 0.0853 | OR: vixchg15_over_vix >= -0.001173` — OR-of-two-clauses/all350/5 lines/min_keep 20 — disc kept 48 (35W/13L, +466,434), p=0.845; holdout kept 13 win 38% +14,242, removed 7 win 43% +7,920, book win 40% — **REJECTED**: shuffle p=0.845 >= 0.05: the same search finds this in random labels; holdout kept win 38% < book 40%
* `IF regime=DIRECTIONAL: pos_dir >= 0.5665 | IF NOT regime=DIRECTIONAL: e_basis_dev >= 0.7` — either/or by regime=DIRECTIONAL: best single clause per half/all350/5 lines — disc kept 39 (31W/8L, +529,510), p=0.405; holdout kept 12 win 50% +32,165, removed 8 win 25% -10,004, book win 40% — **REJECTED**: shuffle p=0.405 >= 0.05: the same search finds this in random labels
* `IF is_CE: oi_net_help5 >= 8.743e+05 | IF NOT is_CE: depth_age_fut >= 0.9` — either/or by is_CE: best single clause per half/all350/5 lines — disc kept 37 (29W/8L, +456,982), p=0.855; holdout kept 9 win 33% -20,056, removed 11 win 45% +42,218, book win 40% — **REJECTED**: shuffle p=0.855 >= 0.05: the same search finds this in random labels; holdout kept win 33% < book 40%
* `IF phase_bucket=open30: e_syn_dev >= -1.44 | IF NOT phase_bucket=open30: e_fut_micro_x_dir >= 0.3` — either/or by phase_bucket=open30: best single clause per half/all350/5 lines — disc kept 30 (25W/5L, +417,807), p=0.240; holdout kept 7 win 43% +5,603, removed 13 win 38% +16,559, book win 40% — **REJECTED**: shuffle p=0.240 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+16,559)
* `IF b_expiry_day: kv_x_dir >= -0.1122 | IF NOT b_expiry_day: oi_net_help5 >= 8.743e+05` — either/or by b_expiry_day: best single clause per half/all350/5 lines — disc kept 51 (37W/14L, +531,654), p=0.765; holdout kept 11 win 36% -718, removed 9 win 44% +22,880, book win 40% — **REJECTED**: shuffle p=0.765 >= 0.05: the same search finds this in random labels; holdout kept win 36% < book 40%
* `IF adv_regime_veto: e_basis_dev >= 0.7 | IF NOT adv_regime_veto: abs_delta >= 0.5253` — either/or by adv_regime_veto: best single clause per half/all350/5 lines — disc kept 39 (28W/11L, +459,053), p=0.560; holdout kept 13 win 46% +21,086, removed 7 win 29% +1,076, book win 40% — **REJECTED**: shuffle p=0.560 >= 0.05: the same search finds this in random labels; holdout removed side is profitable (+1,076)

Reading: Nothing close. Best discovery rules are p 0.24-0.95; the pair accel30_x_dir >= -1.06 AND swing_behind >= 25 (p = 0.77) happens to hold 57 % on holdout but keeps only 7 trades. The book's holdout record (40 % win, +22k) is carried by a few large winners, and no photograph field separates them from the 12 holdout losers in a way that was also visible on discovery.

**Verdict: NONE**


## Across the eight books

* These eight are variants of one t28 strategy and share most of their trades (each has 94-100 trades on the 14 days except the _fill book's 216), so eight NONE verdicts are not eight independent pieces of evidence; they are one strategy photographed eight times.
* The same clauses recur as "best" in book after book: `fut_spread >= 2.6` / `spread_over_prem` (a wider futures spread at the trigger), `oi_own_chg15/30` not falling, and the piecewise rule `open30 -> e_syn_dev >= -1.44, else e_fut_micro_x_dir >= 0.3`. On discovery the spread clause beats luck on t28_st20 (p = 0.01) and the piecewise rule on t28_st20 (p = 0.01) and t28_gap_ts (p = 0.04); on the four holdout days neither carries: the spread clause's kept side wins LESS than the book and loses rupees on every book, and the piecewise rule keeps 7 trades per book for about zero rupees while the removed side is profitable. This is what a tape-memory looks like when the tape moves on.
* 13 searches per book were shuffle-tested; with that many looks a p of 0.04 on one of them is about what multiplicity alone delivers, which is a second reason not to take the gap_ts near-miss.
* What failed, in one line each: single clauses on 196 fields (p 0.2-0.9 everywhere except st20), AND pairs and greedy triples on ~350 base+derived features (p 0.08-0.97), pairs with a 30-trade floor, derived-only singles with finer lines, OR-of-two clauses (p 0.15-0.93), either/or by regime / CE-PE / open30 / expiry day / regime-advisor veto (one p = 0.01, one p = 0.04, both lose on holdout), direction-signed flow and Greeks, ratios of move to vol and premium to theta, within-day z-scores against the book's earlier trades.
* The honest conclusion for the owner: on these 14 days, nothing known at the trigger second separates these books' losers from their winners in a way that beats shuffling AND survives the four days it did not see. The t28_mh15 clause `vixchg15_over_vix >= -0.00115` (p 0.075-0.145, holdout 64 % vs 52 %, +29.9k kept / -8.7k removed) is the only one worth re-testing when more days exist.
