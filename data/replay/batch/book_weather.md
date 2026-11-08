# Each book's weather card (to the owner's spec)

14 replayed days (19 Oct - 6 Nov, today's code). Each book on its own trades plus missed signals. Searched only the spec's groups: time and calendar, shape of the day, realised volatility, breadth and leadership, room to the OI wall, straddle, option cost against the move, VIX. Left out: the book's own trigger measurements (index speed and moves, impulse), its own history, the contract and feed health. Day-type numbers (expiry, gap, VIX level, days to expiry) need 5 days on each side. Checks on every line: 15+ trades each side, kept side better on win rate and mean, neighbouring lines agree, two-thirds of big wins kept. Luck: the same search on 200 shuffles; 'beats luck' = better than luck's 95th percentile.

**57 books searched; 2 have a line that beats luck; about 2.9 would by chance alone.** Everything else below is a lead found by searching the past, not yet distinguishable from luck.

## fade_switch
702 trades on 13 days, 50% winners, mean -0.1 %. Losses: 346 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg_open >= 0.05 | 727, 53%, +0.2 % | 179.5, 39%, -1.8 % | 123 of 523 | VIX | **yes** |
| hi_age_min >= 8.932 | 721, 52%, -0.0 % | 185.5, 42%, -0.8 % | 118 of 523 | shape of the day | no |
| pos_dir >= 0.13882 | 724, 52%, -0.1 % | 182.5, 44%, -0.7 % | 116 of 523 | shape of the day | no |
| phase_bucket=open30 < 0.5 | 799.5, 51%, -0.1 % | 107, 43%, -0.7 % | 72 of 523 | time and calendar | no |
| pos_in_range < 0.88832 | 719, 51%, -0.1 % | 187.5, 45%, -0.6 % | 114 of 523 | shape of the day | no |

## spot_dc12_t12_first
571 trades on 13 days, 38% winners, mean +0.0 %. Losses: 311 never worked (weather), 44 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wall_dn >= 28.62 | 495, 41%, +0.5 % | 124.5, 29%, -2.1 % | 100 of 436 | room to the OI wall | no |
| breadth_dir < 0.84224 | 552.5, 40%, +0.3 % | 225.5, 29%, -0.8 % | 185 of 548 | breadth and leadership | no |
| vix_chg15 >= -0.05 | 553, 40%, +0.2 % | 225, 30%, -0.5 % | 175 of 548 | VIX | no |
| new_highs < 156 | 610, 39%, +0.2 % | 168, 30%, -0.9 % | 128 of 548 | shape of the day | no |
| er30 >= 0.0669 | 552.5, 39%, +0.4 % | 144, 31%, -1.2 % | 113 of 485 | shape of the day | no |

## spot_dc12_t12_first_r003
545 trades on 13 days, 37% winners, mean +0.0 %. Losses: 301 never worked (weather), 44 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wall_dn >= 28.92 | 470, 40%, +0.4 % | 116, 28%, -1.8 % | 95 of 416 | room to the OI wall | no |
| vix_chg15 >= -0.05 | 527.5, 39%, +0.2 % | 210.5, 28%, -0.5 % | 161 of 523 | VIX | no |
| breadth_dir < 0.808 | 448, 40%, +0.4 % | 290, 30%, -0.7 % | 235 of 523 | breadth and leadership | no |
| phase_bucket=open30 < 0.5 | 689, 37%, +0.1 % | 49, 28%, -1.4 % | 38 of 523 | time and calendar | no |
| wmove60_bank >= 0.25 | 611.5, 37%, +0.1 % | 126.5, 30%, -0.8 % | 116 of 523 | breadth and leadership | no |

## fade_switch_r002
414 trades on 13 days, 48% winners, mean -0.2 %. Losses: 208 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| er30 < 0.30968 | 347, 50%, +0.0 % | 88.5, 36%, -2.2 % | 60 of 251 | shape of the day | no |
| strad_chg5 < 1.978 | 352, 50%, +0.0 % | 87.5, 38%, -1.4 % | 56 of 249 | straddle | no |
| give >= 0.0572 | 394, 50%, -0.2 % | 102, 39%, -0.8 % | 65 of 282 | shape of the day | no |
| hi_age_min >= 11.42 | 396, 50%, -0.2 % | 100, 40%, -0.8 % | 65 of 282 | shape of the day | no |
| pos_in_range < 0.89178 | 395, 50%, -0.1 % | 101, 40%, -1.1 % | 67 of 282 | shape of the day | no |

## spot_ft_prem10
413 trades on 13 days, 54% winners, mean +1.0 %. Losses: 184 never worked (weather), 5 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| phase_bucket=open30 < 0.5 | 726, 56%, +1.3 % | 51.5, 32%, -3.8 % | 45 of 501 | time and calendar | **yes** |
| lo_age_min >= 26.18 | 618.5, 57%, +1.5 % | 159, 45%, -0.9 % | 120 of 501 | shape of the day | no |
| rv5 < 11.54 | 526, 57%, +1.6 % | 251.5, 48%, -0.4 % | 170 of 501 | realised volatility | no |
| vix_chg_open < 0.41 | 457.5, 58%, +1.7 % | 320, 49%, -0.1 % | 232 of 501 | VIX | no |
| mins_to_flat >= 93.77 | 621.5, 56%, +1.3 % | 156, 47%, -0.5 % | 120 of 501 | time and calendar | no |

## spot_dc12_t12
274 trades on 13 days, 35% winners, mean +0.3 %. Losses: 143 never worked (weather), 34 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| phase_bucket=afternoon < 0.5 | 261.5, 37%, +0.4 % | 60, 22%, -1.0 % | 39 of 195 | time and calendar | no |
| breadth_dir < 0.88688 | 226, 39%, +0.6 % | 95.5, 24%, -1.1 % | 68 of 195 | breadth and leadership | no |
| wmove60_energy >= -0.42 | 260, 37%, +0.8 % | 61.5, 23%, -2.5 % | 44 of 195 | breadth and leadership | no |
| vix_chg15 >= -0.05 | 230.5, 39%, +0.5 % | 91, 24%, -0.7 % | 59 of 195 | VIX | no |
| wall_room < 353.32 | 218, 38%, +0.6 % | 58, 25%, -0.5 % | 41 of 162 | room to the OI wall | no |

## spot_dc12_t12_nolock
274 trades on 13 days, 35% winners, mean +0.5 %. Losses: 143 never worked (weather), 34 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| phase_bucket=afternoon < 0.5 | 261.5, 37%, +0.6 % | 60, 22%, -1.1 % | 39 of 195 | time and calendar | no |
| breadth_dir < 0.88688 | 226, 39%, +0.6 % | 95.5, 24%, -0.5 % | 68 of 195 | breadth and leadership | no |
| wmove60_energy >= -0.42 | 260, 37%, +0.9 % | 61.5, 23%, -2.5 % | 44 of 195 | breadth and leadership | no |
| vix_chg15 >= -0.05 | 230.5, 39%, +0.7 % | 91, 24%, -0.7 % | 59 of 195 | VIX | no |
| wall_room < 353.32 | 218, 38%, +0.9 % | 58, 25%, -0.5 % | 41 of 162 | room to the OI wall | no |

## spot_dc12_t12_1130
254 trades on 13 days, 35% winners, mean +0.5 %. Losses: 132 never worked (weather), 32 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg15 >= -0.05 | 216, 39%, +0.5 % | 82, 23%, -0.1 % | 54 of 181 | VIX | no |
| breadth_dir < 0.8494 | 178, 41%, +1.2 % | 120, 25%, -1.0 % | 85 of 181 | breadth and leadership | no |
| phase_bucket=afternoon < 0.5 | 249, 37%, +0.3 % | 49, 22%, +0.0 % | 30 of 181 | time and calendar | no |
| mins_open < 268.082 | 238.5, 37%, +0.6 % | 59.5, 24%, -1.0 % | 41 of 181 | time and calendar | no |
| mins_to_flat >= 101.918 | 238.5, 37%, +0.6 % | 59.5, 24%, -1.0 % | 41 of 181 | time and calendar | no |

## t28_d46_fill
198 trades on 13 days, 45% winners, mean +1.1 %. Losses: 95 never worked (weather), 13 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| phase_bucket=afternoon < 0.5 | 228.5, 48%, +1.7 % | 40.5, 31%, -1.4 % | 32 of 163 | time and calendar | no |
| wall_dn >= 39.8 | 164.5, 52%, +2.6 % | 43.5, 34%, -1.7 % | 31 of 122 | room to the OI wall | no |
| to_pdh >= -155.17 | 214, 49%, +2.1 % | 55, 32%, -2.1 % | 42 of 163 | shape of the day | no |
| to_pdc >= -251.44 | 213.5, 49%, +2.0 % | 55.5, 33%, -1.8 % | 41 of 163 | shape of the day | no |
| breadth_dir < 0.7935 | 143, 52%, +2.4 % | 126, 38%, -0.1 % | 89 of 163 | breadth and leadership | no |

## t28_all
191 trades on 13 days, 46% winners, mean +1.1 %. Losses: 91 never worked (weather), 12 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| er_day < 0.1668 | 176, 50%, +2.3 % | 74.5, 36%, -1.2 % | 50 of 149 | shape of the day | no |
| vix_chg15 >= -0.04 | 183, 50%, +2.0 % | 70.5, 37%, -0.6 % | 49 of 150 | VIX | no |
| new_lows >= 9 | 187, 49%, +2.1 % | 66.5, 37%, -0.9 % | 44 of 150 | shape of the day | no |
| to_pdc >= -271.64 | 201, 49%, +1.9 % | 52.5, 36%, -1.2 % | 36 of 150 | shape of the day | no |
| to_pdh >= -165.91 | 201, 49%, +1.9 % | 52.5, 36%, -1.2 % | 36 of 150 | shape of the day | no |

## t28_core_fill
190 trades on 13 days, 45% winners, mean +1.0 %. Losses: 92 never worked (weather), 12 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| mins_to_flat >= 113.1 | 203.5, 49%, +1.7 % | 50.5, 34%, -1.0 % | 40 of 152 | time and calendar | no |
| er_day < 0.16584 | 176.5, 50%, +2.1 % | 74.5, 36%, -1.1 % | 50 of 151 | shape of the day | no |
| mins_open < 256.1 | 203.5, 48%, +1.7 % | 50.5, 35%, -0.8 % | 39 of 152 | time and calendar | no |
| vix_chg15 >= -0.04 | 184, 49%, +1.9 % | 70, 36%, -0.7 % | 49 of 152 | VIX | no |
| breadth_dir < 0.8048 | 132, 52%, +2.2 % | 122, 39%, +0.1 % | 82 of 152 | breadth and leadership | no |

## t28_fill
181 trades on 13 days, 49% winners, mean +1.3 %. Losses: 83 never worked (weather), 10 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wall_dn >= 56.5 | 136.5, 54%, +2.8 % | 64, 38%, -1.3 % | 45 of 119 | room to the OI wall | no |
| wall_up < 372.44 | 199, 50%, +2.1 % | 51.5, 36%, -1.5 % | 40 of 150 | room to the OI wall | no |
| wmove60_bank < 3.682 | 209, 50%, +1.8 % | 48.5, 36%, -1.3 % | 36 of 156 | breadth and leadership | no |
| vwap_ext >= -2.2 | 179.5, 51%, +1.7 % | 78, 38%, +0.0 % | 54 of 156 | shape of the day | no |
| breadth_dir < 0.8308 | 158.5, 52%, +2.0 % | 99, 39%, -0.0 % | 70 of 156 | breadth and leadership | no |

## spot_dc12_t12_first_r002
99 trades on 12 days, 41% winners, mean +0.7 %. Losses: 42 never worked (weather), 16 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg15 >= -0.1 | 122.5, 45%, +1.3 % | 23.5, 21%, -3.0 % | 23 of 88 | VIX | no |
| gap_pts >= -13.1 | 104, 48%, +2.0 % | 42, 26%, -3.0 % | 29 of 88 | shape of the day | no |
| er30 >= 0.0868 | 110, 46%, +1.5 % | 26.5, 25%, -3.2 % | 23 of 83 | shape of the day | no |
| wmove30 >= 0.596 | 120.5, 45%, +1.2 % | 25.5, 25%, -2.1 % | 22 of 88 | breadth and leadership | no |
| wmove10 >= 0.234 | 117, 45%, +1.3 % | 29, 28%, -2.4 % | 20 of 88 | breadth and leadership | no |

## lvl_trail_be
90 trades on 13 days, 47% winners, mean +1.6 %. Losses: 42 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| strad_excess < 5.528 | 74.5, 49%, +2.0 % | 17.5, 20%, -3.1 % | 16 of 52 | straddle | no |
| vix_chg30 >= -0.11 | 81, 51%, +3.0 % | 19, 24%, -3.7 % | 15 of 53 | VIX | no |
| lo_age_min < 217.308 | 79.5, 52%, +2.7 % | 20.5, 24%, -1.9 % | 17 of 53 | shape of the day | no |
| phase_bucket=afternoon < 0.5 | 80.5, 51%, +2.9 % | 19.5, 26%, -3.1 % | 15 of 53 | time and calendar | no |
| vix_chg15 >= -0.046 | 70, 53%, +3.0 % | 30, 30%, -1.3 % | 21 of 53 | VIX | no |

## edge_bracket_only
87 trades on 13 days, 40% winners, mean +0.5 %. Losses: 42 never worked (weather), 10 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.06 | 74, 49%, +2.5 % | 26, 15%, -5.2 % | 23 of 56 | VIX | no |
| strad_excess < 5.26 | 71.5, 43%, +1.3 % | 19, 11%, -7.0 % | 17 of 54 | straddle | no |
| theta_pct < 0.3563 | 71.5, 48%, +2.3 % | 28.5, 19%, -4.2 % | 25 of 56 | option cost against the move | no |
| vix_chg15 >= -0.044 | 71, 48%, +2.3 % | 29, 21%, -4.0 % | 21 of 56 | VIX | no |
| to_pdc >= -307 | 80.5, 45%, +2.0 % | 19.5, 21%, -5.9 % | 14 of 56 | shape of the day | no |

## lvl_trail
87 trades on 13 days, 46% winners, mean +1.7 %. Losses: 40 never worked (weather), 7 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.03 | 62.5, 55%, +4.5 % | 35.5, 28%, -2.8 % | 26 of 52 | VIX | no |
| strad_excess < 5.616 | 72.5, 47%, +2.0 % | 17.5, 20%, -3.1 % | 16 of 51 | straddle | no |
| lo_age_min < 217.332 | 77.5, 51%, +2.8 % | 20.5, 24%, -1.9 % | 17 of 52 | shape of the day | no |
| phase_bucket=afternoon < 0.5 | 78.5, 50%, +3.1 % | 19.5, 26%, -3.1 % | 15 of 52 | time and calendar | no |
| wall_up < 343.58 | 69, 53%, +4.4 % | 20, 30%, -3.4 % | 11 of 44 | room to the OI wall | no |

## t28_fwd
86 trades on 13 days, 50% winners, mean +1.4 %. Losses: 40 never worked (weather), 3 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| er_day < 0.1749 | 70, 57%, +3.1 % | 18.5, 19%, -4.0 % | 15 of 45 | shape of the day | no |
| bn300 < 0.052 | 66, 59%, +3.3 % | 27.5, 27%, -2.0 % | 21 of 47 | breadth and leadership | no |
| wmove60_other < 0.56 | 66.5, 58%, +3.1 % | 27, 30%, -1.6 % | 19 of 47 | breadth and leadership | no |
| breadth_dir < 0.7078 | 67, 57%, +2.9 % | 26.5, 30%, -1.1 % | 20 of 47 | breadth and leadership | no |
| dist_hi >= 30.89 | 76, 55%, +2.3 % | 17.5, 29%, -0.9 % | 13 of 47 | shape of the day | no |

## lvl_trail_rx_be
82 trades on 13 days, 50% winners, mean +2.5 %. Losses: 36 never worked (weather), 5 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| theta_pct >= 0.0218 | 74.5, 56%, +4.0 % | 17.5, 20%, -3.8 % | 13 of 47 | option cost against the move | no |
| vix_chg30 >= -0.11 | 74, 55%, +4.0 % | 18, 25%, -3.2 % | 14 of 47 | VIX | no |
| vix_chg15 >= -0.05 | 67.5, 56%, +4.1 % | 24.5, 31%, -1.6 % | 17 of 47 | VIX | no |
| vix >= 16.03 | 56, 56%, +5.2 % | 36, 38%, -1.6 % | 20 of 47 | VIX | no |
| bn300 < -0.01 | 48.5, 58%, +4.7 % | 43.5, 39%, +0.2 % | 30 of 47 | breadth and leadership | no |

## t28_d46
82 trades on 13 days, 48% winners, mean +2.2 %. Losses: 38 never worked (weather), 5 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 74, 52%, +3.7 % | 18, 25%, -3.4 % | 14 of 48 | VIX | no |
| wall_dn >= 34.88 | 55, 51%, +3.7 % | 15, 27%, -3.2 % | 11 of 39 | room to the OI wall | no |
| wmove10 < -0.38 | 66, 53%, +3.7 % | 26, 31%, -1.3 % | 18 of 48 | breadth and leadership | no |
| or_pos < 1.12876 | 54.5, 52%, +4.1 % | 21.5, 30%, -1.2 % | 17 of 41 | shape of the day | no |
| rv15_spot >= 10.55 | 49.5, 56%, +4.9 % | 42.5, 36%, -0.7 % | 28 of 48 | realised volatility | no |

## t28_tt8
82 trades on 13 days, 59% winners, mean +1.4 %. Losses: 33 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| lo_age_min < 214.25 | 73.5, 64%, +2.2 % | 18, 31%, -0.9 % | 14 of 43 | shape of the day | no |
| vix_chg30 >= -0.11 | 74, 64%, +2.5 % | 17.5, 31%, -2.3 % | 13 of 43 | VIX | no |
| vix_chg15 >= 0 | 41, 74%, +4.2 % | 50.5, 44%, -0.5 % | 31 of 43 | VIX | no |
| or_pos < 1.13141 | 55, 66%, +3.4 % | 20.5, 39%, -1.9 % | 16 of 36 | shape of the day | no |
| wall_dn >= 52.1 | 40.5, 67%, +2.7 % | 29, 40%, -1.5 % | 19 of 35 | room to the OI wall | no |

## t28_mh15
82 trades on 13 days, 52% winners, mean +2.1 %. Losses: 35 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.03 | 56, 64%, +4.8 % | 35, 30%, -1.9 % | 25 of 45 | VIX | no |
| or_pos < 1.13324 | 53.5, 60%, +3.3 % | 21.5, 30%, -0.5 % | 17 of 38 | shape of the day | no |
| lo_age_min < 122.638 | 55.5, 62%, +3.7 % | 35.5, 34%, -0.2 % | 26 of 45 | shape of the day | no |
| vix_chg15 >= -0.03 | 59.5, 60%, +4.3 % | 31.5, 35%, -1.7 % | 22 of 45 | VIX | no |
| mins_open < 246.672 | 72, 56%, +3.1 % | 19, 32%, -1.0 % | 13 of 45 | time and calendar | no |

## spot_dual
79 trades on 13 days, 48% winners, mean +1.4 %. Losses: 40 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| theta_ratio < 0.1266 | 63.5, 53%, +3.6 % | 27.5, 29%, -3.1 % | 24 of 58 | option cost against the move | no |
| strad_excess < 4.496 | 70.5, 47%, +0.7 % | 19, 24%, -3.4 % | 17 of 61 | straddle | no |
| vix_chg30 >= -0.128 | 78, 52%, +2.6 % | 20.5, 29%, -2.4 % | 17 of 61 | VIX | no |
| bn300 < -0.021 | 47, 59%, +5.4 % | 51.5, 37%, -1.9 % | 38 of 61 | breadth and leadership | no |
| rv15_spot >= 10.5 | 51, 57%, +4.7 % | 47.5, 37%, -1.8 % | 37 of 61 | realised volatility | no |

## lvl_trail_re
79 trades on 13 days, 49% winners, mean +2.7 %. Losses: 34 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.112 | 72, 54%, +4.3 % | 18, 25%, -3.8 % | 14 of 46 | VIX | no |
| wall_up < 343.58 | 65, 55%, +5.0 % | 19, 32%, -3.1 % | 10 of 41 | room to the OI wall | no |
| lo_age_min < 214.25 | 72, 53%, +3.4 % | 18, 31%, +0.1 % | 14 of 46 | shape of the day | no |
| dist_lo < 173.895 | 64, 54%, +3.8 % | 26, 35%, -0.0 % | 17 of 46 | shape of the day | no |
| rv15_spot >= 10.575 | 47.5, 57%, +5.7 % | 42.5, 39%, -0.6 % | 29 of 46 | realised volatility | no |

## lvl_trail_rx
79 trades on 13 days, 49% winners, mean +2.6 %. Losses: 34 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 73, 55%, +4.3 % | 17, 21%, -4.5 % | 14 of 46 | VIX | no |
| wall_up < 343.58 | 65, 55%, +4.9 % | 19, 32%, -3.1 % | 10 of 41 | room to the OI wall | no |
| lo_age_min < 214.25 | 72, 53%, +3.3 % | 18, 31%, +0.1 % | 14 of 46 | shape of the day | no |
| dist_lo < 173.895 | 64, 54%, +3.8 % | 26, 35%, -0.0 % | 17 of 46 | shape of the day | no |
| rv15_spot >= 10.575 | 47.5, 57%, +5.7 % | 42.5, 39%, -0.7 % | 29 of 46 | realised volatility | no |

## lvl_trail_rx_c10
79 trades on 13 days, 49% winners, mean +2.6 %. Losses: 34 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 73, 55%, +4.3 % | 17, 21%, -4.5 % | 14 of 46 | VIX | no |
| wall_up < 343.58 | 65, 55%, +4.9 % | 19, 32%, -3.1 % | 10 of 41 | room to the OI wall | no |
| lo_age_min < 214.25 | 72, 53%, +3.3 % | 18, 31%, +0.1 % | 14 of 46 | shape of the day | no |
| dist_lo < 173.895 | 64, 54%, +3.8 % | 26, 35%, -0.0 % | 17 of 46 | shape of the day | no |
| rv15_spot >= 10.575 | 47.5, 57%, +5.7 % | 42.5, 39%, -0.7 % | 29 of 46 | realised volatility | no |

## t28_ts
79 trades on 13 days, 48% winners, mean +3.0 %. Losses: 37 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.114 | 71.5, 52%, +4.5 % | 18, 25%, -3.8 % | 14 of 50 | VIX | no |
| wall_up < 344.04 | 64.5, 54%, +5.2 % | 19, 32%, -2.4 % | 10 of 44 | room to the OI wall | no |
| lo_age_min < 214.44 | 71.5, 51%, +3.4 % | 18, 31%, +0.7 % | 14 of 50 | shape of the day | no |
| wmove10 < -0.384 | 64, 52%, +4.5 % | 25.5, 33%, -1.2 % | 20 of 50 | breadth and leadership | no |
| er60 >= 0.07212 | 35.5, 55%, +4.8 % | 24.5, 37%, +1.0 % | 17 of 35 | shape of the day | no |

## edge_breakout
78 trades on 13 days, 37% winners, mean -0.6 %. Losses: 38 never worked (weather), 11 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| gap_pts < 57.25 | 95.5, 42%, +0.6 % | 24.5, 12%, -6.6 % | 25 of 83 | shape of the day | no |
| dist_lo < 180.48 | 93, 41%, +0.4 % | 27, 19%, -5.2 % | 24 of 83 | shape of the day | no |
| wmove60_bank < 3.728 | 81, 43%, +0.8 % | 39, 22%, -4.3 % | 28 of 83 | breadth and leadership | no |
| wall_up >= 94.63 | 82, 42%, +0.7 % | 38, 22%, -4.2 % | 27 of 83 | room to the OI wall | no |
| lo_age_min < 118.176 | 94.5, 40%, +0.2 % | 25.5, 22%, -4.6 % | 21 of 83 | shape of the day | no |

## t28_st20
77 trades on 13 days, 51% winners, mean +2.9 %. Losses: 32 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.114 | 70, 56%, +4.6 % | 18, 25%, -4.6 % | 14 of 42 | VIX | no |
| wall_up < 344.04 | 63, 56%, +5.5 % | 19, 32%, -4.0 % | 10 of 38 | room to the OI wall | no |
| lo_age_min < 126.404 | 52.5, 59%, +5.1 % | 35.5, 37%, -0.8 % | 24 of 42 | shape of the day | no |
| or_pos < 1.07404 | 45.5, 57%, +4.8 % | 26.5, 38%, -1.1 % | 19 of 35 | shape of the day | no |
| pos_in_range < 0.71 | 44.5, 58%, +5.8 % | 43.5, 41%, -0.4 % | 26 of 42 | shape of the day | no |

## t28_gap
77 trades on 13 days, 51% winners, mean +3.0 %. Losses: 32 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.116 | 70, 56%, +4.7 % | 18, 25%, -3.8 % | 14 of 44 | VIX | no |
| wall_up < 344.5 | 63, 56%, +5.5 % | 19, 32%, -3.1 % | 10 of 39 | room to the OI wall | no |
| lo_age_min < 214.63 | 70, 54%, +3.7 % | 18, 31%, +0.1 % | 14 of 44 | shape of the day | no |
| or_pos < 1.07852 | 45.5, 57%, +4.6 % | 26.5, 36%, -0.1 % | 21 of 37 | shape of the day | no |
| dist_lo < 174.585 | 62, 56%, +4.3 % | 26, 35%, -0.0 % | 17 of 44 | shape of the day | no |

## t28_gap_ts
77 trades on 13 days, 49% winners, mean +3.1 %. Losses: 35 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.118 | 69.5, 54%, +4.7 % | 18, 25%, -3.8 % | 14 of 48 | VIX | no |
| lo_age_min < 214.82 | 69.5, 53%, +3.5 % | 18, 31%, +0.7 % | 14 of 48 | shape of the day | no |
| wall_up < 344.76 | 63.5, 55%, +5.1 % | 18, 33%, -2.0 % | 9 of 42 | room to the OI wall | no |
| wmove10 < -0.776 | 54, 56%, +5.4 % | 33.5, 36%, -0.9 % | 25 of 48 | breadth and leadership | no |
| or_pos < 1.083 | 45, 54%, +4.2 % | 26.5, 36%, +0.3 % | 22 of 40 | shape of the day | no |

## spot_dual_lvl
76 trades on 13 days, 49% winners, mean +1.1 %. Losses: 37 never worked (weather), 2 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 73.5, 54%, +3.1 % | 18.5, 24%, -4.9 % | 16 of 54 | VIX | no |
| strad_excess < 5.704 | 66.5, 50%, +1.4 % | 17.5, 20%, -3.7 % | 16 of 54 | straddle | no |
| phase_bucket=afternoon < 0.5 | 74, 53%, +2.9 % | 18, 28%, -4.2 % | 15 of 54 | time and calendar | no |
| wall_up < 344.04 | 65.5, 56%, +4.5 % | 17.5, 31%, -5.9 % | 11 of 46 | room to the OI wall | no |
| bn300 < -0.005 | 45, 61%, +4.4 % | 47, 36%, -1.3 % | 35 of 54 | breadth and leadership | no |

## t28_cheapK
76 trades on 13 days, 51% winners, mean +3.3 %. Losses: 31 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wall_up < 343.12 | 62, 58%, +5.4 % | 18, 28%, -2.9 % | 10 of 38 | room to the OI wall | no |
| vix_chg30 >= -0.11 | 69.5, 55%, +4.7 % | 16.5, 27%, -3.6 % | 12 of 43 | VIX | no |
| lo_age_min < 215.01 | 68, 55%, +3.6 % | 18, 31%, +1.1 % | 14 of 43 | shape of the day | no |
| to_pdc >= -316.15 | 71, 54%, +4.1 % | 15, 33%, -1.7 % | 12 of 43 | shape of the day | no |
| to_pdh >= -245.6 | 71, 54%, +4.1 % | 15, 33%, -1.7 % | 12 of 43 | shape of the day | no |

## t28_bidpile
75 trades on 13 days, 51% winners, mean +2.9 %. Losses: 31 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.12 | 69.5, 56%, +4.4 % | 15.5, 19%, -4.3 % | 13 of 42 | VIX | no |
| wall_up < 344.04 | 61, 57%, +5.7 % | 18, 28%, -4.7 % | 10 of 37 | room to the OI wall | no |
| vwap_ext >= -6.48 | 59, 57%, +4.3 % | 26, 33%, -0.7 % | 16 of 42 | shape of the day | no |
| dist_lo < 174.755 | 61, 56%, +4.3 % | 24, 33%, -1.0 % | 16 of 42 | shape of the day | no |
| lo_age_min < 215.91 | 68, 54%, +3.3 % | 17, 32%, +0.7 % | 13 of 42 | shape of the day | no |

## c20_9e
74 trades on 13 days, 59% winners, mean +7.0 %. Losses: 20 never worked (weather), 10 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 15.77 | 66.5, 64%, +6.7 % | 16, 31%, +4.0 % | 8 of 30 | VIX | no |
| pos_in_range >= 0.2468 | 67, 63%, +7.2 % | 15.5, 35%, +1.4 % | 6 of 30 | shape of the day | no |
| theta_be >= 0.076 | 67, 63%, +6.5 % | 15.5, 35%, +4.6 % | 6 of 30 | option cost against the move | no |
| theta_be15 >= 1.14 | 67, 63%, +6.5 % | 15.5, 35%, +4.6 % | 6 of 30 | option cost against the move | no |
| wmove10 >= 2.37 | 42, 70%, +11.3 % | 40.5, 44%, +0.8 % | 19 of 30 | breadth and leadership | no |

## t28_nohigh
74 trades on 13 days, 50% winners, mean +3.2 %. Losses: 31 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 66, 57%, +5.2 % | 16, 22%, -3.4 % | 12 of 39 | VIX | no |
| wall_up < 342.76 | 59, 58%, +6.3 % | 17, 29%, -3.4 % | 9 of 34 | room to the OI wall | no |
| wall_dn >= 80.3 | 24, 67%, +7.3 % | 36, 39%, +1.7 % | 22 of 31 | room to the OI wall | no |
| to_pdc >= -295.81 | 66, 55%, +5.1 % | 16, 28%, -2.9 % | 12 of 39 | shape of the day | no |
| or_pos < 0.83888 | 27.5, 64%, +6.1 % | 39.5, 39%, +1.5 % | 26 of 33 | shape of the day | no |

## spot_dual_rg
72 trades on 13 days, 49% winners, mean +1.4 %. Losses: 36 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.11 | 71.5, 55%, +3.6 % | 18, 19%, -6.6 % | 17 of 55 | VIX | no |
| to_pdc >= -318.2 | 73.5, 52%, +2.7 % | 16, 25%, -3.8 % | 15 of 55 | shape of the day | no |
| to_pdh >= -247.65 | 73.5, 52%, +2.7 % | 16, 25%, -3.8 % | 15 of 55 | shape of the day | no |
| rv15_spot >= 10.53 | 46, 60%, +5.2 % | 43.5, 34%, -2.3 % | 35 of 55 | realised volatility | no |
| wall_up < 344.5 | 63.5, 57%, +5.0 % | 17, 32%, -6.1 % | 11 of 46 | room to the OI wall | no |

## c20_9h
71 trades on 13 days, 55% winners, mean +6.5 %. Losses: 21 never worked (weather), 11 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 15.96 | 49.5, 67%, +9.1 % | 31.5, 35%, +0.2 % | 16 of 31 | VIX | no |
| pos_in_range >= 0.2468 | 66, 60%, +6.8 % | 15, 30%, +0.8 % | 7 of 31 | shape of the day | no |
| theta_be >= 0.076 | 65.5, 59%, +5.9 % | 15.5, 35%, +4.6 % | 6 of 31 | option cost against the move | no |
| theta_be15 >= 1.14 | 65.5, 59%, +5.9 % | 15.5, 35%, +4.6 % | 6 of 31 | option cost against the move | no |
| new_highs < 132 | 59, 60%, +8.1 % | 22, 39%, -0.9 % | 12 of 31 | shape of the day | no |

## c20_9t
71 trades on 13 days, 73% winners, mean +4.4 %. Losses: 18 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| new_lows >= 12 | 48, 83%, +7.8 % | 28.5, 54%, -1.7 % | 13 of 21 | shape of the day | no |
| wmove60_other >= 0.404 | 45.5, 84%, +6.1 % | 31, 56%, +1.5 % | 15 of 21 | breadth and leadership | no |
| pos_dir >= 0.27152 | 59.5, 78%, +6.2 % | 17, 53%, -2.3 % | 7 of 21 | shape of the day | no |
| wmove60_energy >= -0.578 | 59.5, 78%, +4.7 % | 17, 53%, +2.6 % | 8 of 21 | breadth and leadership | no |
| vix >= 15.968 | 45, 82%, +7.3 % | 31.5, 59%, -0.0 % | 13 of 21 | VIX | no |

## t28_req
69 trades on 13 days, 54% winners, mean +3.9 %. Losses: 27 never worked (weather), 5 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.12 | 63.5, 61%, +6.0 % | 15.5, 19%, -4.3 % | 13 of 37 | VIX | no |
| wall_dn >= 63.8 | 29.5, 69%, +7.5 % | 29.5, 37%, +1.2 % | 20 of 30 | room to the OI wall | no |
| wall_up < 344.04 | 57, 61%, +6.6 % | 17, 29%, -2.9 % | 10 of 33 | room to the OI wall | no |
| or_pos < 0.84156 | 26, 67%, +7.0 % | 37, 43%, +2.0 % | 23 of 30 | shape of the day | no |

## c20_8x
67 trades on 13 days, 51% winners, mean +7.8 %. Losses: 18 never worked (weather), 15 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 16.36 | 41, 62%, +11.5 % | 43, 34%, -0.4 % | 22 of 35 | VIX | no |
| theta_be < 0.746 | 68.5, 53%, +6.7 % | 15.5, 26%, -0.6 % | 10 of 35 | option cost against the move | no |
| theta_be15 < 11.19 | 68.5, 53%, +6.7 % | 15.5, 26%, -0.6 % | 10 of 35 | option cost against the move | no |
| theta_pct < 0.6522 | 68.5, 53%, +6.7 % | 15.5, 26%, -0.6 % | 10 of 35 | option cost against the move | no |
| new_highs < 132 | 60.5, 55%, +8.2 % | 23.5, 30%, -1.9 % | 13 of 35 | shape of the day | no |

## t28_cheap
67 trades on 13 days, 52% winners, mean +4.0 %. Losses: 27 never worked (weather), 5 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.03 | 46, 67%, +8.1 % | 28, 29%, -1.5 % | 20 of 33 | VIX | no |
| wall_up < 339.28 | 54, 61%, +7.3 % | 15, 27%, -3.3 % | 9 of 29 | room to the OI wall | no |
| theta_ratio < 0.1242 | 47.5, 60%, +7.0 % | 19.5, 33%, -0.3 % | 15 of 31 | option cost against the move | no |
| or_pos < 1.08404 | 42, 60%, +5.8 % | 17, 35%, +1.5 % | 13 of 27 | shape of the day | no |
| or15_pos < 1.277 | 42.5, 60%, +6.2 % | 26.5, 36%, +1.6 % | 16 of 32 | shape of the day | no |

## c20_9v
66 trades on 13 days, 67% winners, mean +9.9 %. Losses: 16 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| theta_be < 0.704 | 63.5, 67%, +8.8 % | 15, 37%, +3.6 % | 9 of 31 | option cost against the move | no |
| theta_be15 < 10.56 | 63.5, 67%, +8.8 % | 15, 37%, +3.6 % | 9 of 31 | option cost against the move | no |
| vix >= 15.97 | 46, 73%, +12.7 % | 32.5, 45%, +0.9 % | 17 of 31 | VIX | no |
| new_highs < 132 | 57, 68%, +10.9 % | 21.5, 42%, -0.3 % | 11 of 31 | shape of the day | no |
| bn300 < 0.093 | 63.5, 65%, +9.2 % | 15, 43%, +2.1 % | 10 of 31 | breadth and leadership | no |

## c20_9x
65 trades on 13 days, 55% winners, mean +9.6 %. Losses: 17 never worked (weather), 12 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 15.966 | 45, 69%, +13.4 % | 32.5, 29%, -0.8 % | 17 of 31 | VIX | no |
| dte < 4 | 43.5, 64%, +9.8 % | 34, 37%, +4.5 % | 14 of 31 | time and calendar | no |
| theta_be >= 0.0758 | 62, 56%, +8.2 % | 15.5, 35%, +4.6 % | 6 of 31 | option cost against the move | no |
| theta_be15 >= 1.136 | 62, 56%, +8.2 % | 15.5, 35%, +4.6 % | 6 of 31 | option cost against the move | no |
| new_highs < 132.2 | 61, 57%, +9.4 % | 16.5, 36%, +0.4 % | 8 of 31 | shape of the day | no |

## t28_ivfall
65 trades on 13 days, 57% winners, mean +3.9 %. Losses: 27 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wall_dn >= 49.14 | 38, 64%, +6.2 % | 17, 29%, -1.6 % | 13 of 30 | room to the OI wall | no |
| vix_chg30 >= -0.061 | 54, 63%, +5.8 % | 21, 31%, -1.7 % | 18 of 40 | VIX | no |
| lo_age_min < 218.396 | 59, 60%, +4.5 % | 16, 31%, +0.6 % | 12 of 40 | shape of the day | no |
| mins_open < 256.836 | 59.5, 60%, +4.8 % | 15.5, 32%, -0.6 % | 12 of 40 | time and calendar | no |
| mins_to_flat >= 92.022 | 59.5, 60%, +4.8 % | 15.5, 32%, -0.6 % | 12 of 40 | time and calendar | no |

## t28_dur20
62 trades on 13 days, 50% winners, mean +3.3 %. Losses: 28 never worked (weather), 3 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.048 | 43, 64%, +7.1 % | 28, 25%, -3.0 % | 22 of 38 | VIX | no |
| or_pos < 1.085 | 40, 60%, +5.0 % | 23, 33%, +0.1 % | 19 of 34 | shape of the day | no |
| wmove10 < -0.234 | 51, 55%, +5.1 % | 20, 32%, -1.8 % | 15 of 38 | breadth and leadership | no |
| vix >= 15.83 | 58, 53%, +4.1 % | 13, 31%, -1.0 % | 9 of 38 | VIX | no |
| wall_up < 344.04 | 50, 55%, +5.5 % | 15, 33%, -2.0 % | 8 of 33 | room to the OI wall | no |

## t28_core
62 trades on 13 days, 50% winners, mean +2.8 %. Losses: 27 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix_chg30 >= -0.05 | 45, 63%, +6.3 % | 26, 23%, -3.3 % | 20 of 36 | VIX | no |
| wmove10 < -1.718 | 30.5, 67%, +7.6 % | 40.5, 35%, -0.9 % | 27 of 36 | breadth and leadership | no |
| or_pos < 1.085 | 40, 60%, +5.6 % | 23, 33%, -0.1 % | 17 of 32 | shape of the day | no |
| vix >= 15.826 | 57, 54%, +3.8 % | 14, 29%, -1.4 % | 8 of 36 | VIX | no |
| er60 >= 0.12676 | 22, 64%, +7.7 % | 32, 39%, +0.8 % | 21 of 28 | shape of the day | no |

## c20_9s
59 trades on 13 days, 61% winners, mean +11.4 %. Losses: 13 never worked (weather), 10 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 16 | 42.5, 67%, +13.9 % | 28.5, 40%, +1.4 % | 13 of 27 | VIX | no |
| new_highs < 132 | 52, 63%, +12.2 % | 19, 37%, -0.3 % | 10 of 27 | shape of the day | no |
| vwap_ext >= -4.8 | 48, 62%, +11.4 % | 23, 43%, +3.6 % | 10 of 27 | shape of the day | no |
| dist_hi < 96.39 | 50, 61%, +9.8 % | 21, 45%, +6.7 % | 10 of 27 | shape of the day | no |
| er_day < 0.1263 | 40, 61%, +13.8 % | 29, 47%, +2.6 % | 11 of 27 | shape of the day | no |

## c20_9y
58 trades on 13 days, 64% winners, mean +12.1 %. Losses: 14 never worked (weather), 7 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 15.98 | 42, 74%, +14.9 % | 28.5, 35%, +0.8 % | 16 of 30 | VIX | no |
| new_highs < 132 | 52.5, 65%, +11.9 % | 18, 39%, +1.2 % | 11 of 30 | shape of the day | no |
| theta_be >= 0.083 | 49.5, 65%, +10.2 % | 21, 43%, +6.8 % | 7 of 30 | option cost against the move | no |
| theta_be15 >= 1.25 | 49.5, 65%, +10.2 % | 21, 43%, +6.8 % | 7 of 30 | option cost against the move | no |
| theta_pct >= 0.02216 | 55.5, 62%, +9.8 % | 15, 43%, +6.6 % | 6 of 30 | option cost against the move | no |

## spot_pb45
52 trades on 13 days, 52% winners, mean -0.2 %. Losses: 20 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| bn300 < -0.0572 | 45, 60%, +3.4 % | 20, 30%, -8.5 % | 13 of 32 | breadth and leadership | no |
| rv5 >= 9.862 | 45, 58%, +2.1 % | 20, 35%, -5.5 % | 14 of 32 | realised volatility | no |
| strad_state=DECAYING < 0.5 | 19, 66%, +9.1 % | 46, 45%, -4.1 % | 26 of 32 | straddle | no |
| wmove60_it < -0.08 | 42.5, 58%, +3.3 % | 22.5, 38%, -7.0 % | 14 of 32 | breadth and leadership | no |
| wmove60_energy < -0.43 | 44, 57%, +4.1 % | 21, 38%, -9.4 % | 11 of 32 | breadth and leadership | no |

## c20_9x_r004
47 trades on 12 days, 55% winners, mean +9.7 %. Losses: 13 never worked (weather), 8 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 15.88 | 45.5, 58%, +9.0 % | 11, 18%, +0.9 % | 8 of 25 | VIX | no |
| new_highs < 132 | 41, 60%, +12.6 % | 15.5, 26%, -6.2 % | 10 of 25 | shape of the day | no |
| to_pdc >= -81.5 | 33, 62%, +15.7 % | 23.5, 34%, -4.2 % | 13 of 25 | shape of the day | no |
| new_lows >= 12 | 34.5, 61%, +13.9 % | 22, 34%, -2.8 % | 12 of 25 | shape of the day | no |
| to_pdh >= -28.075 | 39, 58%, +13.4 % | 17.5, 34%, -6.0 % | 11 of 25 | shape of the day | no |

## spot_dc12_t12_r002
43 trades on 7 days, 42% winners, mean -0.1 %. Losses: 19 never worked (weather), 6 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wmove60_energy >= 0.674 | 20.5, 61%, +5.3 % | 33.5, 28%, -2.7 % | 24 of 28 | breadth and leadership | no |
| wall_room >= 65.76 | 24, 54%, +3.5 % | 19, 26%, -3.5 % | 11 of 21 | room to the OI wall | no |
| hi_age_min < 44.13 | 26.5, 55%, +3.2 % | 27.5, 27%, -2.4 % | 17 of 28 | shape of the day | no |
| wmove60 >= 2.002 | 32, 52%, +2.0 % | 22, 25%, -2.0 % | 14 of 28 | breadth and leadership | no |
| rv15_spot >= 10.782 | 16.5, 58%, +3.8 % | 37.5, 33%, -1.2 % | 21 of 28 | realised volatility | no |

## edge_gate_trail
43 trades on 13 days, 53% winners, mean +3.3 %. Losses: 16 never worked (weather), 4 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| rv5 >= 11.068 | 27.5, 65%, +6.9 % | 18, 36%, -1.8 % | 10 of 18 | realised volatility | no |
| or15_pos < 0.94376 | 24.5, 61%, +6.5 % | 16, 34%, -1.6 % | 7 of 17 | shape of the day | no |
| lo_age_min < 29.75 | 23.5, 66%, +7.1 % | 22, 41%, -0.4 % | 10 of 18 | shape of the day | no |
| wmove60_other >= -2.736 | 26.5, 62%, +6.3 % | 19, 42%, -0.5 % | 9 of 18 | breadth and leadership | no |
| dist_lo < 84.2 | 27.5, 62%, +5.8 % | 18, 42%, -0.1 % | 7 of 18 | shape of the day | no |

## edge_gate_only
38 trades on 13 days, 58% winners, mean +2.7 %. Losses: 14 never worked (weather), 2 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| rv5 >= 11.068 | 26, 73%, +7.7 % | 17, 35%, -5.0 % | 10 of 18 | realised volatility | no |
| lo_age_min < 17.216 | 18, 78%, +8.9 % | 25, 44%, -1.8 % | 14 of 18 | shape of the day | no |
| phase_bucket=morning < 0.5 | 23.5, 70%, +6.0 % | 19.5, 44%, -1.3 % | 10 of 18 | time and calendar | no |
| or15_pos < 0.6475 | 18.5, 68%, +7.4 % | 19.5, 44%, -1.6 % | 10 of 17 | shape of the day | no |
| wall_up < 241.88 | 25, 66%, +7.1 % | 17, 44%, -3.6 % | 9 of 18 | room to the OI wall | no |

## apex_edge
37 trades on 13 days, 46% winners, mean +1.8 %. Losses: 17 never worked (weather), 3 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| theta_be >= 0.081 | 25, 60%, +5.3 % | 15, 27%, -2.7 % | 11 of 19 | option cost against the move | no |
| theta_be15 >= 1.22 | 25, 60%, +5.3 % | 15, 27%, -2.7 % | 11 of 19 | option cost against the move | no |
| new_lows < 32 | 23.5, 60%, +5.5 % | 16.5, 30%, -2.3 % | 9 of 19 | shape of the day | no |
| theta_pct >= 0.02508 | 24, 58%, +4.7 % | 16, 31%, -1.3 % | 11 of 19 | option cost against the move | no |
| vix >= 15.678 | 28, 55%, +4.3 % | 12, 29%, -2.4 % | 8 of 19 | VIX | no |

## straddle_spike
35 trades on 8 days, 31% winners, mean -1.8 %. Losses: 14 never worked (weather), 2 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wmove60_bank < 3.96 | 17, 56%, +4.2 % | 21, 14%, -6.0 % | 10 of 17 | breadth and leadership | no |
| vix_chg30 < -0.01 | 18.5, 51%, +3.2 % | 19.5, 15%, -5.8 % | 11 of 17 | VIX | no |
| vix_chg15 < 0.03 | 22.5, 47%, +2.1 % | 15.5, 13%, -6.5 % | 10 of 17 | VIX | no |
| wall_up < 290.44 | 20.5, 46%, +2.2 % | 15.5, 13%, -5.5 % | 6 of 17 | room to the OI wall | no |
| wmove60 < 7.88 | 17.5, 49%, +3.5 % | 20.5, 20%, -5.6 % | 9 of 17 | breadth and leadership | no |

## m2.0_s0.5_novol
33 trades on 11 days, 42% winners, mean +0.3 %. Losses: 16 never worked (weather), 1 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| vix >= 16.416 | 13, 73%, +4.2 % | 21, 24%, -2.0 % | 13 of 17 | VIX | no |
| gap_pts < 17.96 | 20.5, 56%, +1.8 % | 13.5, 22%, -1.9 % | 10 of 17 | shape of the day | no |
| new_highs < 86 | 19, 55%, +2.6 % | 15, 27%, -2.5 % | 9 of 17 | shape of the day | no |
| vix_chg_open < 0.242 | 10.5, 62%, +4.2 % | 23.5, 34%, -1.4 % | 13 of 17 | VIX | no |
| wmove60_energy >= 0.86 | 17, 56%, +2.2 % | 17, 29%, -1.5 % | 9 of 17 | breadth and leadership | no |

## c20_9x_r002
25 trades on 2 days, 64% winners, mean +7.4 %. Losses: 7 never worked (weather), 2 worked then gave it back (exits).

| Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Group | Beats luck |
|---|---|---|---|---|---|
| wmove60_energy >= 1.01 | 17, 71%, +12.5 % | 15, 40%, -4.2 % | 10 of 15 | breadth and leadership | no |
| bn300 < 0.064 | 16.5, 70%, +7.8 % | 15.5, 42%, +1.3 % | 10 of 15 | breadth and leadership | no |
| vix_chg5 >= -0.01 | 17, 68%, +7.9 % | 15, 43%, +1.0 % | 10 of 15 | VIX | no |
| wmove30 < 5.08 | 16.5, 64%, +8.3 % | 15.5, 48%, +0.9 % | 8 of 15 | breadth and leadership | no |

## Too few trades to search (under 30 rows)
m1.5_s0.4 (19), m2.0_s0.4 (19), m2.5_s0.4 (19), m1.5_s0.4_r003 (19), m2.0_s0.5_tvfast (18), m2.0_s0.5_bookexit (17), m1.5_s0.5 (16), m2.0_s0.5 (16), m2.5_s0.5 (16), m2.0_s0.5_ivinterp (16), m2.0_s0.5_d20 (16), spot_orb45 (16), spot_orb45_r005 (16), spot_orb45_r003 (15), m2.0_s0.5_trend (13), m1.5_s0.6 (13), m2.0_s0.6 (13), m2.5_s0.6 (13), spot_pb45_r002 (7), gap3_s0.4 (6), gap5_s0.4 (6), gap3_s0.4_r003 (6), m1.5_s0.4_r002 (5), spot_orb45_r002 (4), gap3_s0.4_r002 (2)