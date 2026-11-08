# Each book's weather card

14 days (2026-10-19 to 2026-11-06). Every book on its own trades plus its missed signals; EVERY field of the weather photograph (all 68 docs/27 items) and every line. Checks: 15+ weighted trades each side (day-type fields: 5 days each side), kept side ahead on win rate and mean, neighbouring lines agree, two-thirds of big wins kept. Luck: the same search on 200 shuffles; 'beats luck' = better than luck's 95th percentile.

**57 of 82 books searched; 2 have a line that beats luck; about 2.9 would by chance alone.** Every line is a lead found by searching the past; a line that does not beat luck is not yet distinguishable from luck.

## fade_switch
702 trades on 13 days, 50% winners, mean -0.1 %. Losses: 343 never worked (weather), 7 worked then gave it back (exits). 337 fields, 3090 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 53 Option's own levels | sl_n_sup >= 2 | 791.5, 52%, +0.1 % | 115, 36%, -1.8 % | 80 of 519 | no |
| 59 Regime label | regime_broke < 1 | 793.5, 52%, -0.0 % | 113, 38%, -1.2 % | 76 of 519 | no |
| 55 VIX | vix_chg_open >= 0.05 | 727, 53%, +0.2 % | 179.5, 39%, -1.8 % | 121 of 519 | no |
| 52 Option book | opt_opp_q=PULLED < 0.5 | 891.5, 50%, -0.2 % | 15, 37%, -0.2 % | 10 of 519 | no |
| 20 Spot / futures / forward agreement | e_syn_dev >= -2.224 | 720.5, 52%, -0.0 % | 186, 41%, -0.8 % | 121 of 519 | no |
| 12 Extremes' age | hi_age_min >= 8.932 | 721, 52%, -0.0 % | 185.5, 42%, -0.8 % | 117 of 519 | no |
| 22 Depth imbalance | e_fut_tot_imb >= -0.2644 | 724.5, 52%, +0.0 % | 182, 41%, -1.0 % | 120 of 519 | no |
| 37 OI change | oi_own_chg5 < 125463 | 639, 53%, +0.1 % | 265.5, 43%, -0.9 % | 174 of 518 | no |

## spot_dc12_t12_first
571 trades on 13 days, 38% winners, mean +0.0 %. Losses: 285 never worked (weather), 70 worked then gave it back (exits). 372 fields, 3148 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 31 Who moved first | ep_first=INFY < 0.5 | 610, 39%, +0.2 % | 33.5, 21%, -1.7 % | 23 of 397 | no |
| 24 Refill vs withdrawal | fut_opp_q=PULLED < 0.5 | 756.5, 37%, +0.0 % | 21.5, 23%, -1.5 % | 19 of 503 | no |
| 36 OI walls | wall_dn >= 28.62 | 495, 41%, +0.5 % | 124.5, 29%, -2.1 % | 95 of 407 | no |
| 13 Speed | mv300 < 27.01 | 620.5, 40%, +0.2 % | 157.5, 27%, -0.9 % | 117 of 503 | no |
| 13 Speed | fmv300 < 30.102 | 621, 40%, +0.2 % | 157, 27%, -1.0 % | 116 of 503 | no |
| 37 OI change | oi_net_help5 >= -972725 | 618.5, 39%, +0.3 % | 158, 28%, -1.4 % | 120 of 501 | no |
| 37 OI change | oi_other_chg5 >= -77545 | 631.5, 39%, +0.4 % | 145, 28%, -1.8 % | 116 of 501 | no |
| 37 OI change | oi_own_chg5 < 40079 | 451, 42%, +0.6 % | 325.5, 31%, -0.9 % | 227 of 501 | no |

## spot_dc12_t12_first_r003
545 trades on 13 days, 37% winners, mean +0.0 %. Losses: 277 never worked (weather), 68 worked then gave it back (exits). 370 fields, 3150 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 31 Who moved first | ep_first=INFY < 0.5 | 585.5, 38%, +0.1 % | 34, 22%, -1.7 % | 25 of 385 | no |
| 24 Refill vs withdrawal | fut_opp_q=PULLED < 0.5 | 721.5, 36%, +0.0 % | 16.5, 21%, -1.7 % | 15 of 480 | no |
| 52 Option book | opt_opp_o=— < 0.5 | 717, 37%, +0.0 % | 21, 21%, -1.3 % | 14 of 480 | no |
| 37 OI change | oi_other_chg5 >= -93106 | 598.5, 39%, +0.4 % | 138.5, 25%, -1.9 % | 111 of 479 | no |
| 37 OI change | oi_net_help5 >= 171438 | 362, 43%, +1.0 % | 375, 30%, -1.0 % | 266 of 479 | no |
| 36 OI walls | wall_dn >= 28.92 | 470, 40%, +0.4 % | 116, 28%, -1.8 % | 91 of 388 | no |
| 13 Speed | mv300 < 27.85 | 586, 39%, +0.2 % | 152, 27%, -0.9 % | 111 of 480 | no |
| 13 Speed | fmv300 < 26.16 | 518, 39%, +0.3 % | 220, 28%, -0.8 % | 166 of 480 | no |

## fade_switch_r002
414 trades on 13 days, 48% winners, mean -0.2 %. Losses: 207 never worked (weather), 7 worked then gave it back (exits). 337 fields, 3054 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 53 Option's own levels | sl_next_res=OR low < 0.5 | 469.5, 49%, -0.3 % | 17, 32%, -0.7 % | 14 of 274 | no |
| 15 Current impulse | imp_depth >= 0.0631 | 393.5, 51%, +0.0 % | 101.5, 35%, -1.6 % | 69 of 280 | no |
| 53 Option's own levels | sl_n_res >= 2 | 476, 49%, -0.3 % | 20, 32%, -1.8 % | 13 of 281 | no |
| 53 Option's own levels | sl_next_res=OR high < 0.5 | 471.5, 49%, -0.2 % | 15, 33%, -3.7 % | 9 of 274 | no |
| 53 Option's own levels | sl_n_sup >= 2 | 431.5, 50%, -0.0 % | 64.5, 35%, -2.4 % | 45 of 281 | no |
| 15 Current impulse | imp_age_min >= 0.69 | 393, 51%, -0.0 % | 102, 36%, -1.4 % | 67 of 280 | no |
| 9 Trend or range day so far | er30 < 0.30968 | 347, 50%, +0.0 % | 88.5, 36%, -2.2 % | 59 of 250 | no |
| 22 Depth imbalance | e_fut_imb5 < 0.242 | 344.5, 52%, +0.2 % | 151.5, 38%, -1.5 % | 102 of 281 | no |

## spot_ft_prem10
413 trades on 13 days, 54% winners, mean +1.0 %. Losses: 182 never worked (weather), 7 worked then gave it back (exits). 386 fields, 3168 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 4 Session phase | phase_bucket=open30 < 0.5 | 726, 56%, +1.3 % | 51.5, 32%, -3.8 % | 44 of 509 | no |
| 39 Gamma map | gex_regime=AMPLIFY < 0.5 | 726.5, 56%, +1.3 % | 51, 33%, -3.2 % | 42 of 509 | no |
| 37 OI change | oi_own_chg30 < 1.62994e+06 | 598, 59%, +1.9 % | 166, 41%, -1.9 % | 133 of 495 | no |
| 57 Hidden regime | hmm_left_min >= 2.3 | 661, 57%, +1.5 % | 116.5, 40%, -1.8 % | 97 of 509 | no |
| 47 Higher-order Greeks | speed_g < 0 | 609, 58%, +1.6 % | 168.5, 42%, -1.3 % | 252 of 509 | no |
| 47 Higher-order Greeks | charm_min >= -3e-06 | 555.5, 58%, +1.7 % | 222, 44%, -0.9 % | 175 of 509 | no |
| 46 First-order Greeks | delta >= -0.558 | 613, 57%, +1.5 % | 164.5, 43%, -1.1 % | 126 of 509 | no |
| 37 OI change | oi_own_chg15 < 666003 | 608, 57%, +1.6 % | 164.5, 43%, -1.4 % | 127 of 504 | no |

## spot_dc12_t12
274 trades on 13 days, 35% winners, mean +0.3 %. Losses: 145 never worked (weather), 32 worked then gave it back (exits). 350 fields, 3128 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 59 Regime label | regime_broke >= 0 | 265, 38%, +0.7 % | 56.5, 17%, -2.4 % | 47 of 196 | no |
| 35 Sister indices | fn60 >= -0 | 305.5, 36%, +0.2 % | 16, 16%, -1.8 % | 11 of 196 | no |
| 37 OI change | oi_own_chg5 < 161252 | 254.5, 38%, +0.7 % | 67, 21%, -1.8 % | 45 of 196 | no |
| 24 Refill vs withdrawal | fut_pulled < 0.5 | 285.5, 36%, +0.4 % | 36, 19%, -1.8 % | 26 of 196 | no |
| 39 Gamma map | gex_regime=AMPLIFY < 0.5 | 305.5, 35%, +0.4 % | 16, 19%, -4.5 % | 14 of 196 | no |
| 24 Refill vs withdrawal | fut_opp_o=PULLED < 0.5 | 298.5, 36%, +0.3 % | 23, 20%, -1.7 % | 16 of 196 | no |
| 4 Session phase | phase_bucket=afternoon < 0.5 | 261.5, 37%, +0.4 % | 60, 22%, -1.0 % | 41 of 196 | no |
| 22 Depth imbalance | fut_imb_t_chg30 >= -0.026 | 257.5, 38%, +0.4 % | 64, 22%, -0.9 % | 47 of 196 | no |

## spot_dc12_t12_nolock
274 trades on 13 days, 35% winners, mean +0.5 %. Losses: 145 never worked (weather), 32 worked then gave it back (exits). 333 fields, 3096 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 59 Regime label | regime_broke >= 0 | 265, 38%, +0.9 % | 56.5, 17%, -2.4 % | 47 of 196 | no |
| 35 Sister indices | fn60 >= -0 | 305.5, 36%, +0.4 % | 16, 16%, -1.8 % | 11 of 196 | no |
| 37 OI change | oi_own_chg5 < 161252 | 254.5, 38%, +0.9 % | 67, 21%, -1.9 % | 45 of 196 | no |
| 24 Refill vs withdrawal | fut_pulled < 0.5 | 285.5, 36%, +0.5 % | 36, 19%, -1.8 % | 26 of 196 | no |
| 39 Gamma map | gex_regime=AMPLIFY < 0.5 | 305.5, 35%, +0.5 % | 16, 19%, -4.5 % | 14 of 196 | no |
| 24 Refill vs withdrawal | fut_opp_o=PULLED < 0.5 | 298.5, 36%, +0.4 % | 23, 20%, -1.7 % | 16 of 196 | no |
| 4 Session phase | phase_bucket=afternoon < 0.5 | 261.5, 37%, +0.6 % | 60, 22%, -1.1 % | 41 of 196 | no |
| 22 Depth imbalance | fut_imb_t_chg30 >= -0.026 | 257.5, 38%, +0.6 % | 64, 22%, -0.9 % | 47 of 196 | no |

## spot_dc12_t12_1130
254 trades on 13 days, 35% winners, mean +0.5 %. Losses: 134 never worked (weather), 30 worked then gave it back (exits). 345 fields, 3106 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 35 Sister indices | fn60 >= 0 | 282, 36%, +0.4 % | 16, 16%, -1.8 % | 11 of 182 | no |
| 22 Depth imbalance | fut_imb_t_chg30 >= -0.015 | 184.5, 41%, +0.5 % | 113.5, 23%, -0.1 % | 81 of 182 | no |
| 37 OI change | oi_own_chg5 < 162006 | 236, 38%, +0.8 % | 62, 21%, -1.8 % | 42 of 182 | no |
| 24 Refill vs withdrawal | fut_pulled < 0.5 | 262.5, 37%, +0.6 % | 35.5, 20%, -1.7 % | 25 of 182 | no |
| 24 Refill vs withdrawal | fut_opp_o=PULLED < 0.5 | 275.5, 36%, +0.5 % | 22.5, 20%, -1.7 % | 15 of 182 | no |
| 55 VIX | vix_chg15 >= -0.05 | 216, 39%, +0.5 % | 82, 23%, -0.1 % | 55 of 182 | no |
| 23 Resting value | rest_opp_rs >= 1.60585e+06 | 209.5, 39%, +0.6 % | 88.5, 24%, -0.5 % | 64 of 182 | no |
| 29 Breadth | breadth_dir < 0.8494 | 178, 41%, +1.2 % | 120, 25%, -1.0 % | 83 of 182 | no |

## t28_d46_fill
198 trades on 13 days, 45% winners, mean +1.1 %. Losses: 94 never worked (weather), 14 worked then gave it back (exits). 401 fields, 3244 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | agg_with_rs >= 739579 | 210.5, 50%, +2.2 % | 58.5, 29%, -2.5 % | 40 of 160 | no |
| 52 Option book | opt_imb_chg30 >= -0.014 | 219, 49%, +2.0 % | 50, 30%, -2.1 % | 40 of 160 | no |
| 37 OI change | oi_own_chg_open < 7.55702e+06 | 210.5, 50%, +2.0 % | 58.5, 31%, -1.5 % | 42 of 160 | no |
| 31 Who moved first | ep_first=INFY < 0.5 | 227, 49%, +1.7 % | 16.5, 30%, -1.2 % | 13 of 141 | no |
| 37 OI change | oi_other_chg5 >= -53209 | 217, 49%, +1.9 % | 52, 31%, -1.9 % | 41 of 160 | no |
| 52 Option book | opt_opp_o=DRAIN-SLOW < 0.5 | 240, 48%, +1.7 % | 29, 29%, -2.8 % | 24 of 160 | no |
| 4 Session phase | phase_bucket=afternoon < 0.5 | 228.5, 48%, +1.7 % | 40.5, 31%, -1.4 % | 33 of 160 | no |
| 36 OI walls | wall_dn >= 39.8 | 164.5, 52%, +2.6 % | 43.5, 34%, -1.7 % | 31 of 118 | no |

## t28_all
191 trades on 13 days, 46% winners, mean +1.1 %. Losses: 90 never worked (weather), 13 worked then gave it back (exits). 390 fields, 3222 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_own_chg_open < 6.0686e+06 | 172.5, 53%, +2.6 % | 81, 31%, -1.6 % | 57 of 148 | no |
| 24 Refill vs withdrawal | fut_opp_q=PULLED < 0.5 | 227, 48%, +1.6 % | 26.5, 28%, -1.4 % | 20 of 148 | no |
| 25 Traded volume | agg_with_rs >= 800608 | 199.5, 50%, +2.1 % | 54, 31%, -1.6 % | 36 of 148 | no |
| 39 Gamma map | gex_flip_ahead >= -15.1 | 126, 56%, +3.5 % | 127.5, 36%, -0.9 % | 88 of 148 | no |
| 24 Refill vs withdrawal | fut_opp_o=DRAIN-SLOW < 0.5 | 216.5, 49%, +1.8 % | 37, 30%, -1.8 % | 29 of 148 | no |
| 39 Gamma map | gex_balance >= -0.039 | 201.5, 50%, +1.8 % | 52, 32%, -0.8 % | 36 of 148 | no |
| 24 Refill vs withdrawal | fut_pulled < 0.5 | 219.5, 49%, +1.6 % | 34, 31%, -0.8 % | 23 of 148 | no |
| 52 Option book | opt_lead >= -0.018 | 201.5, 50%, +1.6 % | 52, 33%, +0.0 % | 36 of 148 | no |

## t28_core_fill
190 trades on 13 days, 45% winners, mean +1.0 %. Losses: 91 never worked (weather), 13 worked then gave it back (exits). 389 fields, 3220 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_own_chg_open < 7.65472e+06 | 198, 51%, +2.3 % | 56, 28%, -2.6 % | 42 of 150 | no |
| 25 Traded volume | agg_with_rs >= 788291 | 200.5, 50%, +2.0 % | 53.5, 30%, -2.0 % | 36 of 150 | no |
| 39 Gamma map | gex_flip_ahead >= -15.2 | 125, 56%, +3.5 % | 129, 36%, -1.1 % | 90 of 150 | no |
| 24 Refill vs withdrawal | fut_opp_q=PULLED < 0.5 | 227.5, 48%, +1.5 % | 26.5, 28%, -1.3 % | 20 of 150 | no |
| 24 Refill vs withdrawal | fut_opp_o=DRAIN-SLOW < 0.5 | 217, 48%, +1.7 % | 37, 30%, -2.1 % | 29 of 150 | no |
| 39 Gamma map | gex_balance >= -0.039 | 202, 49%, +1.7 % | 52, 32%, -0.8 % | 36 of 150 | no |
| 52 Option book | opt_lead >= -0.018 | 202, 49%, +1.6 % | 52, 32%, -0.4 % | 36 of 150 | no |
| 24 Refill vs withdrawal | fut_pulled < 0.5 | 220, 48%, +1.5 % | 34, 31%, -0.8 % | 23 of 150 | no |

## t28_fill
181 trades on 13 days, 49% winners, mean +1.3 %. Losses: 82 never worked (weather), 11 worked then gave it back (exits). 400 fields, 3238 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_net_help5 >= -809861 | 206.5, 50%, +1.8 % | 51, 33%, -1.2 % | 32 of 155 | no |
| 25 Traded volume | agg_with_rs >= 680704 | 204, 50%, +2.0 % | 53.5, 34%, -1.9 % | 37 of 155 | no |
| 7 Range so far vs earlier days | range_vs_norm < 1.4752 | 174, 48%, +1.3 % | 41.5, 31%, -1.6 % | 32 of 133 | no |
| 36 OI walls | wall_dn >= 56.5 | 136.5, 54%, +2.8 % | 64, 38%, -1.3 % | 44 of 119 | no |
| 31 Who moved first | ep_first=BHARTIARTL < 0.5 | 210, 50%, +1.8 % | 19, 34%, -1.5 % | 14 of 136 | no |
| 35 Sister indices | fn60 >= 0 | 239, 48%, +1.5 % | 18.5, 32%, -2.7 % | 14 of 155 | no |
| 24 Refill vs withdrawal | fut_opp_o=DRAIN-SLOW < 0.5 | 217.5, 49%, +1.8 % | 40, 34%, -1.9 % | 32 of 155 | no |
| 47 Higher-order Greeks | charm_min >= -4e-06 | 199.5, 50%, +1.4 % | 58, 35%, +0.4 % | 39 of 155 | no |

## spot_dc12_t12_first_r002
99 trades on 12 days, 41% winners, mean +0.7 %. Losses: 39 never worked (weather), 19 worked then gave it back (exits). 345 fields, 3100 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_net_help30 < 1.29219e+07 | 114, 46%, +1.6 % | 29, 21%, -4.0 % | 22 of 84 | no |
| 55 VIX | vix_chg15 >= -0.1 | 122.5, 45%, +1.3 % | 23.5, 21%, -3.0 % | 22 of 84 | no |
| 61 Advisors | adv_bank < 0.5 | 129, 44%, +1.1 % | 17, 21%, -3.6 % | 11 of 84 | no |
| 15 Current impulse | imp_rng < 116.4 | 114, 46%, +1.5 % | 32, 23%, -2.6 % | 21 of 84 | no |
| 14 Acceleration | accel30 >= -1.85 | 118, 46%, +1.6 % | 28, 23%, -3.8 % | 26 of 84 | no |
| 37 OI change | oi_other_chg30 < 2.90904e+06 | 97, 48%, +2.4 % | 46, 26%, -3.6 % | 36 of 84 | no |
| 13 Speed | mv300 < 22.16 | 116.5, 46%, +1.2 % | 29.5, 24%, -1.9 % | 22 of 84 | no |
| 45 Premium and quote | quote_age >= 0.24 | 89, 50%, +1.9 % | 57, 28%, -1.5 % | 36 of 84 | no |

## lvl_trail_be
90 trades on 13 days, 47% winners, mean +1.6 %. Losses: 40 never worked (weather), 8 worked then gave it back (exits). 376 fields, 3188 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | fut_vol_surge < 1.4748 | 81.5, 53%, +2.7 % | 18.5, 14%, -2.5 % | 13 of 50 | no |
| 37 OI change | oi_own_chg_open < 6.73536e+06 | 80, 52%, +3.1 % | 20, 20%, -3.9 % | 16 of 50 | no |
| 56 IV vs realised | e_v_min30 >= 51.0222 | 63, 57%, +4.5 % | 37, 27%, -3.0 % | 28 of 50 | no |
| 41 Straddle | strad_excess < 5.528 | 74.5, 49%, +2.0 % | 17.5, 20%, -3.1 % | 14 of 49 | no |
| 25 Traded volume | fut_vol60 >= 7566 | 70, 54%, +4.0 % | 30, 27%, -3.5 % | 22 of 50 | no |
| 55 VIX | vix_chg30 >= -0.11 | 81, 51%, +3.0 % | 19, 24%, -3.7 % | 12 of 50 | no |
| 39 Gamma map | gex_wall_ahead >= 53.8 | 51.5, 59%, +5.6 % | 48.5, 32%, -2.4 % | 32 of 50 | no |
| 48 Breakeven | speed15 >= 6.573 | 39, 60%, +7.1 % | 53, 33%, -2.0 % | 33 of 47 | no |

## edge_bracket_only
87 trades on 13 days, 40% winners, mean +0.5 %. Losses: 41 never worked (weather), 11 worked then gave it back (exits). 356 fields, 3146 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 50 Premium momentum | opt_vol1 < 2.7688e+06 | 79.5, 49%, +2.8 % | 20.5, 5%, -8.7 % | 16 of 52 | **yes** |
| 37 OI change | oi_own_chg_open < 5.06771e+06 | 71, 52%, +3.5 % | 29, 10%, -7.1 % | 22 of 52 | **yes** |
| 56 IV vs realised | e_v_min30 >= 52.0518 | 62.5, 54%, +4.2 % | 37.5, 16%, -5.8 % | 28 of 52 | no |
| 39 Gamma map | gex_wall_ahead >= 53.8 | 50, 59%, +5.1 % | 50, 21%, -4.2 % | 32 of 52 | no |
| 48 Breakeven | speed15 >= 5.893 | 48, 57%, +5.0 % | 44, 22%, -4.7 % | 27 of 48 | no |
| 56 IV vs realised | e_iv_rv < 3.07 | 80.5, 47%, +2.1 % | 19.5, 13%, -6.3 % | 14 of 52 | no |
| 27 Price impact and spread | fut_spread >= 2.56 | 70, 50%, +2.9 % | 30, 17%, -5.1 % | 17 of 52 | no |
| 55 VIX | vix_chg30 >= -0.06 | 74, 49%, +2.5 % | 26, 15%, -5.2 % | 20 of 52 | no |

## lvl_trail
87 trades on 13 days, 46% winners, mean +1.7 %. Losses: 38 never worked (weather), 9 worked then gave it back (exits). 370 fields, 3176 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | fut_vol_surge < 1.4832 | 79.5, 52%, +2.4 % | 18.5, 19%, -0.6 % | 13 of 49 | no |
| 37 OI change | oi_own_chg_open < 6.755e+06 | 78, 52%, +3.3 % | 20, 20%, -3.9 % | 16 of 49 | no |
| 37 OI change | oi_net_help5 >= 344532 | 66.5, 56%, +4.3 % | 31.5, 24%, -3.4 % | 18 of 49 | no |
| 56 IV vs realised | e_v_min30 >= 50.511 | 62, 56%, +4.7 % | 36, 28%, -3.0 % | 27 of 49 | no |
| 48 Breakeven | speed15 >= 4.481 | 66, 52%, +3.8 % | 24, 25%, -2.5 % | 18 of 46 | no |
| 55 VIX | vix_chg30 >= -0.03 | 62.5, 55%, +4.5 % | 35.5, 28%, -2.8 % | 21 of 49 | no |
| 41 Straddle | strad_excess < 5.616 | 72.5, 47%, +2.0 % | 17.5, 20%, -3.1 % | 14 of 48 | no |

## t28_fwd
86 trades on 13 days, 50% winners, mean +1.4 %. Losses: 39 never worked (weather), 4 worked then gave it back (exits). 375 fields, 3152 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 60 Domino episode | ep_max_s >= 0.475 | 34.5, 74%, +7.6 % | 50.5, 34%, -1.9 % | 33 of 40 | no |
| 9 Trend or range day so far | er_day < 0.1749 | 70, 57%, +3.1 % | 18.5, 19%, -4.0 % | 15 of 44 | no |
| 58 Order-flow chain reaction | hk_sell >= 0.2248 | 74, 57%, +3.2 % | 18.5, 24%, -3.9 % | 11 of 44 | no |
| 35 Sister indices | bn300 < 0.052 | 66, 59%, +3.3 % | 27.5, 27%, -2.0 % | 19 of 45 | no |
| 16 Swing distance | swing_ahead >= 20.57 | 67, 58%, +2.6 % | 26.5, 28%, -0.3 % | 18 of 45 | no |
| 23 Resting value | rest_opp_rs < 1.07737e+07 | 74.5, 56%, +2.7 % | 19, 26%, -2.2 % | 14 of 45 | no |
| 22 Depth imbalance | fut_imb_o < 0.091 | 65, 58%, +4.0 % | 28.5, 30%, -3.4 % | 21 of 45 | no |
| 30 Sector split | wmove60_other < 0.56 | 66.5, 58%, +3.1 % | 27, 30%, -1.6 % | 17 of 45 | no |

## lvl_trail_rx_be
82 trades on 13 days, 50% winners, mean +2.5 %. Losses: 34 never worked (weather), 7 worked then gave it back (exits). 373 fields, 3174 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | fut_vol_surge < 1.449 | 74.5, 57%, +3.6 % | 17.5, 14%, -1.9 % | 11 of 43 | no |
| 46 First-order Greeks | theta_pct >= 0.0218 | 74.5, 56%, +4.0 % | 17.5, 20%, -3.8 % | 13 of 43 | no |
| 25 Traded volume | fut_vol60 >= 7605 | 65, 58%, +5.1 % | 27, 26%, -3.6 % | 20 of 43 | no |
| 25 Traded volume | fut_ttq60 >= 7605 | 65.5, 58%, +5.0 % | 26.5, 26%, -3.5 % | 19 of 43 | no |
| 37 OI change | oi_other_chg5 >= 41990 | 55, 61%, +5.3 % | 37, 31%, -1.5 % | 22 of 43 | no |
| 55 VIX | vix_chg30 >= -0.11 | 74, 55%, +4.0 % | 18, 25%, -3.2 % | 11 of 43 | no |
| 56 IV vs realised | e_v_min30 >= 52.538 | 59, 59%, +5.3 % | 33, 30%, -2.3 % | 23 of 43 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 74.5, 54%, +3.5 % | 17.5, 26%, -1.5 % | 10 of 43 | no |

## t28_d46
82 trades on 13 days, 48% winners, mean +2.2 %. Losses: 36 never worked (weather), 7 worked then gave it back (exits). 368 fields, 3164 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 9 Trend or range day so far | reversals60 < 29 | 30, 63%, +8.8 % | 32, 31%, -2.1 % | 21 of 29 | no |
| 48 Breakeven | speed15 >= 5.863 | 44.5, 61%, +7.5 % | 39.5, 30%, -3.0 % | 24 of 41 | no |
| 56 IV vs realised | e_v_min30 >= 81.786 | 40, 64%, +7.0 % | 52, 34%, -1.3 % | 31 of 45 | no |
| 37 OI change | oi_net_help5 >= 310895 | 63.5, 56%, +4.7 % | 28.5, 26%, -3.0 % | 17 of 45 | no |
| 26 Absorption | absorb60 < 4.12805e+07 | 66.5, 55%, +4.3 % | 25.5, 25%, -2.9 % | 15 of 45 | no |
| 22 Depth imbalance | fut_lead >= 0.126 | 27.5, 67%, +9.8 % | 64.5, 38%, -0.9 % | 36 of 45 | no |
| 32 Basket gap | basket_gap < -1.324 | 37.5, 64%, +6.5 % | 54.5, 35%, -0.5 % | 31 of 45 | no |
| 25 Traded volume | agg_with_rs >= 752168 | 54, 58%, +5.9 % | 38, 30%, -2.8 % | 24 of 45 | no |

## t28_tt8
82 trades on 13 days, 59% winners, mean +1.4 %. Losses: 30 never worked (weather), 4 worked then gave it back (exits). 378 fields, 3182 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 56 IV vs realised | e_v_min30 >= 53.3048 | 58, 71%, +3.5 % | 33.5, 34%, -1.7 % | 22 of 38 | no |
| 12 Extremes' age | lo_age_min < 214.25 | 73.5, 64%, +2.2 % | 18, 31%, -0.9 % | 13 of 38 | no |
| 25 Traded volume | fut_vol_surge < 1.4508 | 75, 63%, +2.5 % | 16.5, 30%, -2.9 % | 10 of 38 | no |
| 55 VIX | vix_chg30 >= -0.11 | 74, 64%, +2.5 % | 17.5, 31%, -2.3 % | 10 of 38 | no |
| 48 Breakeven | speed15 >= 4.5098 | 62, 65%, +3.0 % | 22.5, 33%, -2.0 % | 14 of 36 | no |
| 55 VIX | vix_chg15 >= 0 | 41, 74%, +4.2 % | 50.5, 44%, -0.5 % | 25 of 38 | no |
| 56 IV vs realised | e_iv_rv < 2.94 | 73.5, 63%, +1.8 % | 18, 33%, +0.5 % | 11 of 38 | no |
| 37 OI change | oi_own_chg_open < 6.38538e+06 | 74, 63%, +2.2 % | 17.5, 34%, -1.3 % | 12 of 38 | no |

## t28_mh15
82 trades on 13 days, 52% winners, mean +2.1 %. Losses: 33 never worked (weather), 6 worked then gave it back (exits). 359 fields, 3148 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 26 Absorption | absorb60 < 4.39527e+07 | 66.5, 61%, +4.1 % | 24.5, 24%, -2.8 % | 15 of 41 | no |
| 27 Price impact and spread | fut_spread >= 1.68 | 73, 58%, +3.4 % | 18, 22%, -2.5 % | 10 of 41 | no |
| 55 VIX | vix_chg30 >= -0.03 | 56, 64%, +4.8 % | 35, 30%, -1.9 % | 20 of 41 | no |
| 48 Breakeven | speed15 >= 6.5718 | 35.5, 69%, +7.5 % | 48.5, 35%, -1.8 % | 29 of 39 | no |
| 32 Basket gap | basket_gap < -1.2782 | 37.5, 69%, +6.6 % | 53.5, 38%, -0.9 % | 28 of 41 | no |
| 6 Opening range | or45_pos < 1.13324 | 53.5, 60%, +3.3 % | 21.5, 30%, -0.5 % | 15 of 33 | no |
| 6 Opening range | or_pos < 1.13324 | 53.5, 60%, +3.3 % | 21.5, 30%, -0.5 % | 15 of 33 | no |

## spot_dual
79 trades on 13 days, 48% winners, mean +1.4 %. Losses: 35 never worked (weather), 6 worked then gave it back (exits). 368 fields, 3152 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 34 Heavyweight volume | hw_vol_surge < 1.2662 | 70, 56%, +3.8 % | 28.5, 25%, -3.9 % | 19 of 52 | no |
| 37 OI change | oi_own_chg_open < 6.4596e+06 | 77, 54%, +3.4 % | 21.5, 23%, -4.8 % | 16 of 52 | no |
| 56 IV vs realised | e_v_min30 >= 51.3654 | 60, 59%, +4.5 % | 38.5, 29%, -2.9 % | 27 of 52 | no |
| 56 IV vs realised | e_iv_rv < 2.964 | 77.5, 54%, +2.9 % | 21, 24%, -3.4 % | 14 of 52 | no |
| 47 Higher-order Greeks | zomma >= -7.3e-05 | 77.5, 54%, +4.1 % | 21, 24%, -7.6 % | 16 of 52 | no |
| 48 Breakeven | speed15 >= 3.773 | 73.5, 51%, +2.9 % | 17.5, 23%, -4.2 % | 14 of 49 | no |
| 25 Traded volume | fut_vol_surge < 1.4562 | 78.5, 53%, +1.7 % | 20, 25%, +1.1 % | 11 of 52 | no |
| 39 Gamma map | gex_balance >= -0.0616 | 77, 53%, +3.2 % | 21.5, 26%, -4.3 % | 16 of 52 | no |

## lvl_trail_re
79 trades on 13 days, 49% winners, mean +2.7 %. Losses: 32 never worked (weather), 8 worked then gave it back (exits). 367 fields, 3162 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | fut_vol_surge < 1.4508 | 73.5, 54%, +3.1 % | 16.5, 21%, +0.8 % | 10 of 42 | no |
| 37 OI change | oi_net_help5 >= 301594 | 61.5, 59%, +5.4 % | 28.5, 26%, -3.0 % | 15 of 42 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 73, 54%, +3.9 % | 17, 24%, -2.5 % | 10 of 42 | no |
| 25 Traded volume | agg_with_rs >= 743775 | 52.5, 61%, +6.7 % | 37.5, 31%, -2.9 % | 22 of 42 | no |
| 37 OI change | oi_other_chg5 >= 42926 | 54, 60%, +5.4 % | 36, 31%, -1.3 % | 22 of 42 | no |
| 55 VIX | vix_chg30 >= -0.112 | 72, 54%, +4.3 % | 18, 25%, -3.8 % | 11 of 42 | no |
| 48 Breakeven | speed15 >= 4.469 | 60, 56%, +5.0 % | 22, 27%, -2.2 % | 15 of 39 | no |
| 56 IV vs realised | e_v_min30 >= 52.4808 | 57, 59%, +5.6 % | 33, 30%, -2.3 % | 23 of 42 | no |

## lvl_trail_rx
79 trades on 13 days, 49% winners, mean +2.6 %. Losses: 32 never worked (weather), 8 worked then gave it back (exits). 367 fields, 3164 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.11 | 73, 55%, +4.3 % | 17, 21%, -4.5 % | 11 of 42 | no |
| 25 Traded volume | fut_vol_surge < 1.4508 | 73.5, 54%, +3.1 % | 16.5, 21%, +0.8 % | 10 of 42 | no |
| 34 Heavyweight volume | hw_vol_surge < 1.414 | 72, 55%, +4.4 % | 18, 22%, -4.1 % | 11 of 42 | no |
| 37 OI change | oi_net_help5 >= 301594 | 61.5, 59%, +5.3 % | 28.5, 26%, -3.0 % | 15 of 42 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 73, 54%, +3.9 % | 17, 24%, -2.5 % | 10 of 42 | no |
| 25 Traded volume | agg_with_rs >= 743775 | 52.5, 61%, +6.7 % | 37.5, 31%, -3.0 % | 22 of 42 | no |
| 37 OI change | oi_other_chg5 >= 42926 | 54, 60%, +5.3 % | 36, 31%, -1.3 % | 22 of 42 | no |
| 25 Traded volume | fut_vol60 >= 5785 | 73.5, 54%, +4.4 % | 16.5, 24%, -5.1 % | 14 of 42 | no |

## lvl_trail_rx_c10
79 trades on 13 days, 49% winners, mean +2.6 %. Losses: 32 never worked (weather), 8 worked then gave it back (exits). 367 fields, 3164 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.11 | 73, 55%, +4.3 % | 17, 21%, -4.5 % | 11 of 42 | no |
| 25 Traded volume | fut_vol_surge < 1.4508 | 73.5, 54%, +3.1 % | 16.5, 21%, +0.8 % | 10 of 42 | no |
| 34 Heavyweight volume | hw_vol_surge < 1.414 | 72, 55%, +4.4 % | 18, 22%, -4.1 % | 11 of 42 | no |
| 37 OI change | oi_net_help5 >= 301594 | 61.5, 59%, +5.3 % | 28.5, 26%, -3.0 % | 15 of 42 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 73, 54%, +3.9 % | 17, 24%, -2.5 % | 10 of 42 | no |
| 25 Traded volume | agg_with_rs >= 743775 | 52.5, 61%, +6.7 % | 37.5, 31%, -3.0 % | 22 of 42 | no |
| 37 OI change | oi_other_chg5 >= 42926 | 54, 60%, +5.3 % | 36, 31%, -1.3 % | 22 of 42 | no |
| 25 Traded volume | fut_vol60 >= 5785 | 73.5, 54%, +4.4 % | 16.5, 24%, -5.1 % | 14 of 42 | no |

## t28_ts
79 trades on 13 days, 48% winners, mean +3.0 %. Losses: 33 never worked (weather), 8 worked then gave it back (exits). 369 fields, 3170 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 32 Basket gap | basket_gap < -1.4248 | 37, 65%, +8.2 % | 52.5, 34%, -0.9 % | 29 of 43 | no |
| 37 OI change | oi_net_help5 >= 292292 | 61, 57%, +5.2 % | 28.5, 26%, -2.1 % | 15 of 43 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 72.5, 52%, +4.0 % | 17, 24%, -1.9 % | 10 of 43 | no |
| 26 Absorption | absorb60 < 3.17312e+07 | 55.5, 58%, +5.7 % | 34, 29%, -1.8 % | 21 of 43 | no |
| 25 Traded volume | agg_with_rs >= 735382 | 52, 59%, +6.5 % | 37.5, 31%, -2.2 % | 22 of 43 | no |
| 16 Swing distance | swing_behind >= 21.39 | 61, 56%, +4.8 % | 28.5, 28%, -1.4 % | 18 of 43 | no |
| 55 VIX | vix_chg30 >= -0.114 | 71.5, 52%, +4.5 % | 18, 25%, -3.8 % | 11 of 43 | no |
| 37 OI change | oi_other_chg5 >= 42302 | 53.5, 58%, +5.3 % | 36, 31%, -0.7 % | 22 of 43 | no |

## edge_breakout
78 trades on 13 days, 37% winners, mean -0.6 %. Losses: 39 never worked (weather), 10 worked then gave it back (exits). 354 fields, 3144 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 47 Higher-order Greeks | vomma >= 0.00646 | 84, 46%, +1.7 % | 36, 11%, -6.8 % | 35 of 85 | **yes** |
| 68 Feed health | gaps_today < 5 | 81.5, 45%, +1.4 % | 38.5, 16%, -5.7 % | 35 of 85 | no |
| 5 Opening gap | gap_pts < 55.55 | 95.5, 42%, +0.6 % | 24.5, 12%, -6.6 % | 25 of 85 | no |
| 13 Speed | fmv300 < 36.536 | 93.5, 42%, +0.4 % | 26.5, 15%, -5.3 % | 24 of 85 | no |
| 37 OI change | oi_own_chg5 < 217698 | 93.5, 42%, +0.9 % | 26.5, 15%, -7.1 % | 24 of 85 | no |
| 44 Smile position | svi_res >= -0.02 | 99.5, 41%, +0.4 % | 17.5, 14%, -6.4 % | 16 of 83 | no |
| 13 Speed | mv300 < 34.65 | 94, 41%, +0.4 % | 26, 15%, -5.3 % | 23 of 85 | no |
| 16 Swing distance | swing_ahead < 27.99 | 94, 41%, +0.7 % | 26, 15%, -6.4 % | 22 of 85 | no |

## t28_st20
77 trades on 13 days, 51% winners, mean +2.9 %. Losses: 31 never worked (weather), 7 worked then gave it back (exits). 370 fields, 3166 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 27 Price impact and spread | fut_spread >= 1.8 | 71, 57%, +4.4 % | 17, 21%, -4.0 % | 10 of 41 | no |
| 9 Trend or range day so far | reversals60 < 29 | 29.5, 68%, +9.2 % | 31, 34%, -2.8 % | 21 of 28 | no |
| 37 OI change | oi_net_help5 >= 305708 | 60, 60%, +5.0 % | 28, 29%, -2.1 % | 15 of 41 | no |
| 55 VIX | vix_chg30 >= -0.114 | 70, 56%, +4.6 % | 18, 25%, -4.6 % | 12 of 41 | no |
| 56 IV vs realised | e_v_min30 >= 61.984 | 47, 63%, +7.4 % | 41, 35%, -2.6 % | 27 of 41 | no |
| 48 Breakeven | speed15 >= 5.8165 | 42, 62%, +8.6 % | 39, 36%, -3.1 % | 24 of 39 | no |
| 26 Absorption | absorb60 >= 1.6082e+07 | 69.5, 55%, +4.1 % | 18.5, 30%, -2.5 % | 12 of 41 | no |

## t28_gap
77 trades on 13 days, 51% winners, mean +3.0 %. Losses: 30 never worked (weather), 8 worked then gave it back (exits). 367 fields, 3158 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 25 Traded volume | fut_vol_surge < 1.4544 | 71.5, 56%, +3.5 % | 16.5, 21%, +0.8 % | 10 of 40 | no |
| 37 OI change | oi_net_help5 >= 344532 | 59.5, 60%, +5.9 % | 28.5, 26%, -3.0 % | 15 of 40 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 71, 56%, +4.3 % | 17, 24%, -2.5 % | 10 of 40 | no |
| 55 VIX | vix_chg30 >= -0.116 | 70, 56%, +4.7 % | 18, 25%, -3.8 % | 11 of 40 | no |
| 25 Traded volume | agg_with_rs >= 798682 | 51.5, 62%, +7.0 % | 36.5, 32%, -2.6 % | 21 of 40 | no |
| 37 OI change | oi_other_chg5 >= 43238 | 53, 61%, +5.7 % | 35, 31%, -1.0 % | 21 of 40 | no |
| 48 Breakeven | speed15 >= 5.863 | 42.5, 62%, +8.4 % | 38.5, 34%, -2.5 % | 23 of 38 | no |
| 56 IV vs realised | e_v_min30 >= 52.0518 | 56, 60%, +5.9 % | 32, 31%, -2.1 % | 22 of 40 | no |

## t28_gap_ts
77 trades on 13 days, 49% winners, mean +3.1 %. Losses: 31 never worked (weather), 8 worked then gave it back (exits). 367 fields, 3170 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 32 Basket gap | basket_gap < -1.3996 | 36, 67%, +8.4 % | 51.5, 35%, -0.9 % | 28 of 41 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 70.5, 54%, +4.1 % | 17, 24%, -1.9 % | 10 of 41 | no |
| 37 OI change | oi_net_help5 >= 331526 | 60, 57%, +5.3 % | 27.5, 27%, -2.1 % | 14 of 41 | no |
| 55 VIX | vix_chg30 >= -0.118 | 69.5, 54%, +4.7 % | 18, 25%, -3.8 % | 11 of 41 | no |
| 26 Absorption | absorb60 < 3.27885e+07 | 54.5, 59%, +5.7 % | 33, 30%, -1.5 % | 20 of 41 | no |
| 25 Traded volume | agg_with_rs >= 775425 | 51, 60%, +6.8 % | 36.5, 32%, -2.3 % | 21 of 41 | no |
| 37 OI change | oi_other_chg5 >= 42614 | 52.5, 59%, +5.4 % | 35, 31%, -0.7 % | 21 of 41 | no |
| 16 Swing distance | swing_behind >= 21.53 | 60, 57%, +4.9 % | 27.5, 29%, -1.4 % | 17 of 41 | no |

## spot_dual_lvl
76 trades on 13 days, 49% winners, mean +1.1 %. Losses: 32 never worked (weather), 7 worked then gave it back (exits). 370 fields, 3162 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_own_chg_open < 6.77462e+06 | 72, 56%, +3.3 % | 20, 20%, -5.1 % | 16 of 46 | no |
| 56 IV vs realised | e_v_min30 >= 51.3654 | 56.5, 60%, +4.5 % | 35.5, 30%, -3.2 % | 24 of 46 | no |
| 48 Breakeven | speed15 >= 5.893 | 42, 63%, +6.9 % | 42.5, 33%, -3.3 % | 25 of 42 | no |
| 55 VIX | vix_chg30 >= -0.11 | 73.5, 54%, +3.1 % | 18.5, 24%, -4.9 % | 13 of 46 | no |
| 58 Order-flow chain reaction | hk_sell >= 0.229 | 73, 55%, +3.1 % | 18, 25%, -4.7 % | 12 of 45 | no |
| 37 OI change | oi_net_help5 >= 345215 | 62, 58%, +3.8 % | 30, 28%, -3.3 % | 18 of 46 | no |
| 41 Straddle | strad_excess < 5.704 | 66.5, 50%, +1.4 % | 17.5, 20%, -3.7 % | 13 of 46 | no |

## t28_cheapK
76 trades on 13 days, 51% winners, mean +3.3 %. Losses: 31 never worked (weather), 6 worked then gave it back (exits). 370 fields, 3164 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_other_chg5 >= 59410 | 52, 63%, +5.8 % | 34, 29%, -1.0 % | 20 of 39 | no |
| 36 OI walls | wall_up < 343.12 | 62, 58%, +5.4 % | 18, 28%, -2.9 % | 9 of 36 | no |
| 25 Traded volume | fut_vol_surge < 1.458 | 69.5, 55%, +3.6 % | 16.5, 27%, +0.9 % | 10 of 39 | no |
| 55 VIX | vix_chg30 >= -0.11 | 69.5, 55%, +4.7 % | 16.5, 27%, -3.6 % | 10 of 39 | no |
| 34 Heavyweight volume | hw_vol_surge < 1.43 | 68, 56%, +4.7 % | 18, 28%, -3.1 % | 11 of 39 | no |
| 37 OI change | oi_net_help5 >= 344922 | 58.5, 59%, +5.7 % | 27.5, 31%, -2.4 % | 14 of 39 | no |
| 48 Breakeven | speed15 >= 5.863 | 41, 63%, +8.2 % | 38, 37%, -1.8 % | 22 of 36 | no |
| 16 Swing distance | swing_behind >= 21.425 | 58.5, 58%, +5.1 % | 27.5, 33%, -1.1 % | 16 of 39 | no |

## t28_bidpile
75 trades on 13 days, 51% winners, mean +2.9 %. Losses: 29 never worked (weather), 8 worked then gave it back (exits). 365 fields, 3154 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.12 | 69.5, 56%, +4.4 % | 15.5, 19%, -4.3 % | 10 of 38 | no |
| 48 Breakeven | speed15 >= 6.5644 | 32.5, 68%, +8.9 % | 46.5, 34%, -1.4 % | 28 of 37 | no |
| 25 Traded volume | fut_vol_surge < 1.5288 | 69.5, 55%, +3.1 % | 15.5, 23%, +1.3 % | 9 of 38 | no |
| 27 Price impact and spread | fut_spread >= 1.64 | 68, 56%, +4.1 % | 17, 24%, -2.5 % | 10 of 38 | no |
| 37 OI change | oi_net_help5 >= 272604 | 58.5, 59%, +5.2 % | 26.5, 28%, -2.5 % | 13 of 38 | no |
| 36 OI walls | wall_up < 344.04 | 61, 57%, +5.7 % | 18, 28%, -4.7 % | 9 of 34 | no |
| 37 OI change | oi_own_chg_open < 4.99946e+06 | 60.5, 58%, +4.8 % | 24.5, 29%, -2.2 % | 17 of 38 | no |
| 56 IV vs realised | e_v_min30 >= 59.2405 | 45.5, 63%, +7.0 % | 39.5, 34%, -2.0 % | 26 of 38 | no |

## c20_9e
74 trades on 13 days, 59% winners, mean +7.0 %. Losses: 25 never worked (weather), 5 worked then gave it back (exits). 329 fields, 3080 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 53 Option's own levels | sl_room_dn_pct >= 0.83 | 66.5, 66%, +7.3 % | 16, 22%, +1.2 % | 12 of 34 | no |
| 49 IV | e_iv_atm >= 14.77 | 67, 65%, +6.8 % | 15.5, 26%, +3.2 % | 8 of 34 | no |
| 13 Speed | mv10 >= 2.8 | 51, 72%, +10.1 % | 31.5, 35%, -0.4 % | 20 of 34 | no |
| 52 Option book | opt_imb_chg30 >= 0.005 | 54.5, 70%, +8.9 % | 28, 34%, +0.7 % | 18 of 34 | no |
| 7 Range so far vs earlier days | range_vs_norm < 1.0076 | 51, 70%, +8.8 % | 22, 36%, -0.7 % | 14 of 28 | no |
| 61 Advisors | adv_vetoes < 4 | 62.5, 66%, +8.6 % | 20, 32%, -1.7 % | 12 of 34 | no |
| 37 OI change | oi_own_chg_open >= 2.56373e+06 | 59, 67%, +8.1 % | 23.5, 34%, +1.2 % | 16 of 34 | no |
| 55 VIX | vix >= 15.77 | 66.5, 64%, +6.7 % | 16, 31%, +4.0 % | 8 of 34 | no |

## t28_nohigh
74 trades on 13 days, 50% winners, mean +3.2 %. Losses: 28 never worked (weather), 9 worked then gave it back (exits). 364 fields, 3138 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 27 Price impact and spread | fut_spread >= 1.86 | 65.5, 57%, +5.0 % | 16.5, 21%, -2.4 % | 10 of 34 | no |
| 9 Trend or range day so far | reversals60 < 28.5 | 28.5, 67%, +9.5 % | 27, 31%, -1.7 % | 17 of 22 | no |
| 55 VIX | vix_chg30 >= -0.11 | 66, 57%, +5.2 % | 16, 22%, -3.4 % | 9 of 34 | no |
| 37 OI change | oi_net_help5 >= 346190 | 56, 60%, +5.8 % | 26, 29%, -1.4 % | 11 of 34 | no |
| 56 IV vs realised | e_v_min30 >= 54.9984 | 50.5, 61%, +6.5 % | 31.5, 32%, -1.4 % | 18 of 34 | no |
| 36 OI walls | wall_up < 342.76 | 59, 58%, +6.3 % | 17, 29%, -3.4 % | 8 of 30 | no |

## spot_dual_rg
72 trades on 13 days, 49% winners, mean +1.4 %. Losses: 31 never worked (weather), 6 worked then gave it back (exits). 361 fields, 3136 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_own_chg_open < 6.79426e+06 | 69.5, 55%, +3.5 % | 20, 20%, -5.4 % | 16 of 46 | no |
| 55 VIX | vix_chg30 >= -0.11 | 71.5, 55%, +3.6 % | 18, 19%, -6.6 % | 14 of 46 | no |
| 32 Basket gap | basket_gap < -1.095 | 36, 68%, +8.1 % | 53.5, 34%, -2.9 % | 34 of 46 | no |
| 56 IV vs realised | e_v_min30 >= 50.679 | 55.5, 60%, +5.1 % | 34, 26%, -4.3 % | 24 of 46 | no |
| 47 Higher-order Greeks | charm_min >= -0.000301 | 70, 54%, +2.6 % | 19.5, 23%, -2.4 % | 14 of 46 | no |
| 25 Traded volume | fut_vol60 >= 5785 | 74, 53%, +3.4 % | 15.5, 23%, -7.5 % | 14 of 46 | no |
| 48 Breakeven | speed15 >= 4.4933 | 58, 54%, +3.6 % | 24, 25%, -3.6 % | 16 of 43 | no |

## c20_9h
71 trades on 13 days, 55% winners, mean +6.5 %. Losses: 26 never worked (weather), 6 worked then gave it back (exits). 331 fields, 3092 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 49 IV | e_iv_atm >= 14.77 | 65.5, 61%, +6.2 % | 15.5, 26%, +3.2 % | 8 of 35 | no |
| 50 Premium momentum | opt_vol_chg1 >= 32175 | 42, 70%, +10.7 % | 39, 37%, +0.2 % | 23 of 35 | no |
| 55 VIX | vix >= 15.96 | 49.5, 67%, +9.1 % | 31.5, 35%, +0.2 % | 17 of 35 | no |
| 53 Option's own levels | sl_room_dn_pct >= 0.83 | 65.5, 60%, +6.4 % | 15.5, 29%, +2.3 % | 10 of 35 | no |
| 13 Speed | mv10 >= 2.75 | 49, 66%, +10.5 % | 32, 36%, -1.8 % | 19 of 35 | no |
| 8 Position in the range | pos_in_range >= 0.2468 | 66, 60%, +6.8 % | 15, 30%, +0.8 % | 12 of 35 | no |
| 61 Advisors | adv_vetoes < 4 | 61, 61%, +7.4 % | 20, 32%, +0.2 % | 12 of 35 | no |
| 7 Range so far vs earlier days | range_vs_norm < 1.0076 | 49.5, 65%, +8.2 % | 22, 36%, -0.7 % | 14 of 29 | no |

## c20_9t
71 trades on 13 days, 73% winners, mean +4.4 %. Losses: 18 never worked (weather), 1 worked then gave it back (exits). 327 fields, 3096 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 52 Option book | opt_opp_q=HOLDING < 0.5 | 55.5, 83%, +6.9 % | 21, 45%, -2.7 % | 12 of 21 | no |
| 9 Trend or range day so far | new_lows >= 12 | 48, 83%, +7.8 % | 28.5, 54%, -1.7 % | 13 of 21 | no |
| 49 IV | iv_vs_med < 1.078 | 61.5, 78%, +4.9 % | 15, 50%, +1.5 % | 7 of 21 | no |
| 23 Resting value | rest_with_rs < 2.96293e+06 | 37.5, 87%, +10.0 % | 39, 59%, -1.2 % | 16 of 21 | no |
| 50 Premium momentum | opt_vol_chg1 >= -34866 | 45.5, 84%, +8.3 % | 31, 56%, -1.6 % | 14 of 21 | no |
| 30 Sector split | wmove60_other >= 0.404 | 45.5, 84%, +6.1 % | 31, 56%, +1.5 % | 15 of 21 | no |
| 60 Domino episode | dom_z >= 0.888 | 45, 83%, +7.0 % | 31.5, 57%, +0.4 % | 14 of 21 | no |
| 8 Position in the range | pos_dir >= 0.27152 | 59.5, 78%, +6.2 % | 17, 53%, -2.3 % | 7 of 21 | no |

## t28_req
69 trades on 13 days, 54% winners, mean +3.9 %. Losses: 25 never worked (weather), 7 worked then gave it back (exits). 361 fields, 3128 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.12 | 63.5, 61%, +6.0 % | 15.5, 19%, -4.3 % | 10 of 33 | no |
| 25 Traded volume | fut_vol_surge < 1.4486 | 64, 59%, +4.5 % | 15, 23%, +1.8 % | 8 of 33 | no |
| 37 OI change | oi_own_chg_open < 5.12758e+06 | 55.5, 62%, +6.4 % | 23.5, 30%, -1.9 % | 17 of 33 | no |
| 36 OI walls | wall_dn >= 63.8 | 29.5, 69%, +7.5 % | 29.5, 37%, +1.2 % | 17 of 25 | no |
| 27 Price impact and spread | fut_spread >= 1.8 | 64, 59%, +5.3 % | 15, 27%, -1.7 % | 8 of 33 | no |
| 51 Premium response | prem_resp1 < 1.2352 | 64, 59%, +5.3 % | 15, 27%, -1.8 % | 10 of 33 | no |
| 36 OI walls | wall_up < 344.04 | 57, 61%, +6.6 % | 17, 29%, -2.9 % | 9 of 30 | no |
| 26 Absorption | absorb60 < 4.11728e+07 | 57.5, 61%, +6.1 % | 21.5, 30%, -1.8 % | 12 of 33 | no |

## c20_8x
67 trades on 13 days, 51% winners, mean +7.8 %. Losses: 23 never worked (weather), 10 worked then gave it back (exits). 330 fields, 3074 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 47 Higher-order Greeks | charm_min >= -0.000314 | 69, 55%, +8.2 % | 15, 13%, -7.3 % | 12 of 39 | no |
| 39 Gamma map | gex_regime=AMPLIFY < 0.5 | 69, 55%, +8.0 % | 15, 13%, -6.8 % | 11 of 39 | no |
| 39 Gamma map | gex_balance >= -0.095 | 68, 54%, +8.1 % | 16, 19%, -6.0 % | 11 of 39 | no |
| 47 Higher-order Greeks | speed_g < 7e-06 | 68, 54%, +8.3 % | 16, 19%, -6.8 % | 11 of 39 | no |
| 45 Premium and quote | premium >= 77.9 | 68.5, 54%, +6.9 % | 15.5, 19%, -1.4 % | 10 of 39 | no |
| 39 Gamma map | gex_regime=MIXED >= 0.5 | 51, 60%, +10.6 % | 33, 29%, -2.6 % | 19 of 39 | no |
| 39 Gamma map | gex_wall_ahead >= 28.9 | 68.5, 53%, +7.9 % | 15.5, 23%, -5.8 % | 12 of 39 | no |
| 46 First-order Greeks | delta >= -0.543 | 52.5, 59%, +10.4 % | 31.5, 29%, -3.0 % | 19 of 39 | no |

## t28_cheap
67 trades on 13 days, 52% winners, mean +4.0 %. Losses: 24 never worked (weather), 8 worked then gave it back (exits). 360 fields, 3132 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.03 | 46, 67%, +8.1 % | 28, 29%, -1.5 % | 14 of 28 | no |
| 37 OI change | oi_own_chg_open < 5.00399e+06 | 52, 63%, +7.1 % | 22, 27%, -1.8 % | 13 of 28 | no |
| 36 OI walls | wall_up < 339.28 | 54, 61%, +7.3 % | 15, 27%, -3.3 % | 8 of 25 | no |
| 56 IV vs realised | e_v_min30 >= 58.7234 | 45.5, 66%, +7.9 % | 28.5, 32%, -1.1 % | 15 of 28 | no |
| 27 Price impact and spread | fut_spread >= 2.5 | 53.5, 62%, +6.8 % | 20.5, 29%, -1.7 % | 11 of 28 | no |
| 48 Breakeven | speed15 >= 5.728 | 41, 65%, +8.7 % | 26, 33%, -1.2 % | 13 of 26 | no |
| 37 OI change | oi_net_help5 >= 378956 | 50.5, 62%, +6.5 % | 23.5, 32%, +0.1 % | 9 of 28 | no |

## c20_9v
66 trades on 13 days, 67% winners, mean +9.9 %. Losses: 18 never worked (weather), 4 worked then gave it back (exits). 333 fields, 3092 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 52 Option book | opt_opp_q=HOLDING < 0.5 | 56, 71%, +11.6 % | 22.5, 38%, -1.8 % | 14 of 32 | no |
| 47 Higher-order Greeks | speed_g < 2e-06 | 63, 67%, +9.7 % | 15.5, 35%, +0.0 % | 11 of 32 | no |
| 46 First-order Greeks | delta >= -0.568 | 63.5, 67%, +10.1 % | 15, 37%, -2.0 % | 10 of 32 | no |
| 48 Breakeven | theta_be < 0.704 | 63.5, 67%, +8.8 % | 15, 37%, +3.6 % | 9 of 32 | no |
| 48 Breakeven | theta_be15 < 10.56 | 63.5, 67%, +8.8 % | 15, 37%, +3.6 % | 9 of 32 | no |
| 47 Higher-order Greeks | vanna < 0.00414 | 61.5, 67%, +10.2 % | 17, 38%, -0.9 % | 10 of 32 | no |
| 67 Agreement | agree_same >= 3 | 58.5, 68%, +10.6 % | 20, 40%, -0.4 % | 16 of 32 | no |
| 55 VIX | vix >= 15.97 | 46, 73%, +12.7 % | 32.5, 45%, +0.9 % | 16 of 32 | no |

## c20_9x
65 trades on 13 days, 55% winners, mean +9.6 %. Losses: 22 never worked (weather), 7 worked then gave it back (exits). 331 fields, 3086 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix >= 15.966 | 45, 69%, +13.4 % | 32.5, 29%, -0.8 % | 18 of 35 | no |
| 49 IV | atm_iv_med >= 16.346 | 46.5, 67%, +10.3 % | 31, 31%, +3.3 % | 18 of 35 | no |
| 49 IV | e_iv_atm >= 14.724 | 62, 59%, +8.6 % | 15.5, 26%, +3.2 % | 8 of 35 | no |
| 53 Option's own levels | sl_room_dn_pct >= 0.826 | 62, 58%, +8.8 % | 15.5, 29%, +2.0 % | 10 of 35 | no |
| 39 Gamma map | gex_regime=MIXED >= 0.5 | 49.5, 63%, +11.7 % | 28, 34%, +0.0 % | 17 of 35 | no |
| 7 Range so far vs earlier days | range_now < 191.95 | 36.5, 67%, +11.9 % | 41, 39%, +3.5 % | 24 of 35 | no |
| 47 Higher-order Greeks | vanna < 0.003027 | 54.5, 61%, +10.0 % | 23, 33%, +1.4 % | 13 of 35 | no |

## t28_ivfall
65 trades on 13 days, 57% winners, mean +3.9 %. Losses: 23 never worked (weather), 5 worked then gave it back (exits). 363 fields, 3158 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 36 OI walls | wall_dn >= 49.14 | 38, 64%, +6.2 % | 17, 29%, -1.6 % | 12 of 24 | no |
| 56 IV vs realised | e_v_min30 >= 59.2405 | 40.5, 69%, +8.2 % | 34.5, 36%, -1.6 % | 22 of 33 | no |
| 55 VIX | vix_chg30 >= -0.061 | 54, 63%, +5.8 % | 21, 31%, -1.7 % | 14 of 33 | no |
| 48 Breakeven | speed15 >= 5.53 | 36.5, 67%, +8.8 % | 32.5, 37%, -1.8 % | 18 of 31 | no |
| 25 Traded volume | agg_with_rs >= 810484 | 43.5, 67%, +7.4 % | 31.5, 37%, -1.5 % | 19 of 33 | no |
| 12 Extremes' age | lo_age_min < 218.396 | 59, 60%, +4.5 % | 16, 31%, +0.6 % | 11 of 33 | no |

## t28_dur20
62 trades on 13 days, 50% winners, mean +3.3 %. Losses: 25 never worked (weather), 6 worked then gave it back (exits). 353 fields, 3120 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.048 | 43, 64%, +7.1 % | 28, 25%, -3.0 % | 18 of 33 | no |
| 25 Traded volume | agg_with_rs >= 680704 | 48.5, 60%, +6.0 % | 22.5, 24%, -2.9 % | 16 of 33 | no |
| 56 IV vs realised | e_v_min30 >= 55.741 | 39, 64%, +7.4 % | 32, 30%, -2.0 % | 22 of 33 | no |
| 68 Feed health | spot_age < 0.04 | 37.5, 64%, +7.0 % | 33.5, 31%, -1.1 % | 24 of 33 | no |
| 26 Absorption | absorb60 < 4.72857e+07 | 52, 57%, +5.3 % | 19, 26%, -2.7 % | 11 of 33 | no |
| 34 Heavyweight volume | hw_vol_surge < 1.1448 | 42, 61%, +5.3 % | 29, 31%, +0.1 % | 16 of 33 | no |
| 37 OI change | oi_other_chg30 < 2.39258e+06 | 49, 57%, +4.3 % | 20, 28%, -0.2 % | 14 of 32 | no |
| 37 OI change | oi_net_help5 >= 358592 | 48.5, 58%, +5.4 % | 22.5, 29%, -1.7 % | 12 of 33 | no |

## t28_core
62 trades on 13 days, 50% winners, mean +2.8 %. Losses: 25 never worked (weather), 6 worked then gave it back (exits). 353 fields, 3134 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix_chg30 >= -0.05 | 45, 63%, +6.3 % | 26, 23%, -3.3 % | 18 of 33 | no |
| 56 IV vs realised | e_v_min30 >= 63.4668 | 31, 71%, +8.5 % | 40, 31%, -1.7 % | 25 of 33 | no |
| 25 Traded volume | agg_with_rs >= 695198 | 48.5, 60%, +5.6 % | 22.5, 24%, -3.4 % | 15 of 33 | no |
| 26 Absorption | absorb60 < 3.45459e+07 | 45, 61%, +5.6 % | 26, 27%, -2.2 % | 16 of 33 | no |
| 28 Weighted move | wmove10 < -1.718 | 30.5, 67%, +7.6 % | 40.5, 35%, -0.9 % | 24 of 33 | no |
| 37 OI change | oi_own_chg_open < 6.81048e+06 | 49, 58%, +5.1 % | 22, 27%, -2.5 % | 15 of 33 | no |

## c20_9s
59 trades on 13 days, 61% winners, mean +11.4 %. Losses: 17 never worked (weather), 6 worked then gave it back (exits). 331 fields, 3084 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 67 Agreement | agree_same >= 6 | 52, 65%, +12.9 % | 19, 32%, -2.2 % | 17 of 30 | no |
| 61 Advisors | adv_vetoes < 4 | 53.5, 64%, +11.1 % | 17.5, 31%, +2.1 % | 10 of 30 | no |
| 39 Gamma map | gex_regime=MIXED >= 0.5 | 45.5, 68%, +13.7 % | 25.5, 35%, +0.2 % | 16 of 30 | no |
| 49 IV | iv_vs_med < -0.108 | 42, 69%, +12.7 % | 29, 38%, +3.3 % | 17 of 30 | no |
| 40 Call vs put activity | prem_ratio_with >= 0.9486 | 49, 65%, +11.4 % | 22, 36%, +3.3 % | 12 of 30 | no |
| 55 VIX | vix >= 16 | 42.5, 67%, +13.9 % | 28.5, 40%, +1.4 % | 13 of 30 | no |
| 9 Trend or range day so far | new_highs < 132 | 52, 63%, +12.2 % | 19, 37%, -0.3 % | 10 of 30 | no |
| 61 Advisors | adv_gex_room < 0.5 | 50, 64%, +12.3 % | 21, 38%, +0.6 % | 12 of 30 | no |

## c20_9y
58 trades on 13 days, 64% winners, mean +12.1 %. Losses: 15 never worked (weather), 6 worked then gave it back (exits). 330 fields, 3094 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 67 Agreement | agree_same >= 7 | 47, 72%, +14.9 % | 23.5, 30%, -2.3 % | 21 of 30 | no |
| 55 VIX | vix >= 15.98 | 42, 74%, +14.9 % | 28.5, 35%, +0.8 % | 15 of 30 | no |
| 47 Higher-order Greeks | vanna < 0.003134 | 49.5, 69%, +13.7 % | 21, 33%, -1.6 % | 13 of 30 | no |
| 50 Premium momentum | opt_vol_chg1 >= 8970 | 36.5, 73%, +16.2 % | 34, 43%, +1.6 % | 21 of 30 | no |
| 50 Premium momentum | opt_vol1 >= 569725 | 48.5, 67%, +13.7 % | 22, 39%, -0.8 % | 11 of 30 | no |
| 9 Trend or range day so far | new_highs < 132 | 52.5, 65%, +11.9 % | 18, 39%, +1.2 % | 10 of 30 | no |
| 49 IV | e_iv_atm >= 15.748 | 50.5, 65%, +11.1 % | 20, 40%, +4.2 % | 11 of 30 | no |

## spot_pb45
52 trades on 13 days, 52% winners, mean -0.2 %. Losses: 20 never worked (weather), 1 worked then gave it back (exits). 363 fields, 3102 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 60 Domino episode | ep_max_s >= 0.3119 | 42, 62%, +3.9 % | 20, 30%, -8.2 % | 12 of 27 | no |
| 35 Sister indices | bn300 < -0.0572 | 45, 60%, +3.4 % | 20, 30%, -8.5 % | 12 of 30 | no |
| 68 Feed health | fut_age < 0.395 | 34, 65%, +8.0 % | 31, 35%, -9.3 % | 19 of 30 | no |
| 68 Feed health | depth_age_fut >= 0.5 | 48.5, 58%, +2.1 % | 16.5, 30%, -7.0 % | 12 of 30 | no |
| 47 Higher-order Greeks | speed_g < 0 | 40, 61%, +5.4 % | 25, 34%, -9.2 % | 16 of 30 | no |
| 25 Traded volume | fut_vol_surge >= 0.6914 | 39, 62%, +6.7 % | 26, 35%, -10.6 % | 15 of 30 | no |
| 47 Higher-order Greeks | charm_min >= -2e-06 | 38, 62%, +5.8 % | 27, 35%, -8.7 % | 15 of 30 | no |
| 13 Speed | fmv300 < -17.487 | 45, 59%, +3.6 % | 20, 32%, -8.8 % | 13 of 30 | no |

## c20_9x_r004
47 trades on 12 days, 55% winners, mean +9.7 %. Losses: 16 never worked (weather), 5 worked then gave it back (exits). 330 fields, 3092 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 67 Agreement | agree_same >= 8 | 39, 64%, +12.1 % | 17.5, 20%, -3.0 % | 17 of 27 | no |
| 50 Premium momentum | opt_vol_chg1 >= 281450 | 24, 75%, +15.4 % | 32.5, 32%, +1.5 % | 22 of 27 | no |
| 55 VIX | vix >= 15.88 | 45.5, 58%, +9.0 % | 11, 18%, +0.9 % | 8 of 27 | no |
| 39 Gamma map | gex_regime=MIXED >= 0.5 | 34.5, 65%, +12.4 % | 22, 27%, -0.3 % | 15 of 27 | no |
| 23 Resting value | rest_with_rs < 3.03246e+06 | 28.5, 68%, +14.6 % | 28, 32%, +0.1 % | 18 of 27 | no |
| 37 OI change | oi_net_help30 < -733161 | 32.5, 65%, +12.9 % | 21.5, 30%, +0.6 % | 13 of 25 | no |

## spot_dc12_t12_r002
43 trades on 7 days, 42% winners, mean -0.1 %. Losses: 19 never worked (weather), 6 worked then gave it back (exits). 325 fields, 3068 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 39 Gamma map | gex_flip_ahead >= -15.5 | 32, 58%, +4.1 % | 22, 16%, -5.1 % | 17 of 28 | no |
| 13 Speed | mv5 < -1.865 | 16.5, 67%, +6.3 % | 37.5, 29%, -2.3 % | 22 of 28 | no |
| 32 Basket gap | basket_gap < -1.0888 | 22.5, 62%, +4.3 % | 31.5, 25%, -2.5 % | 21 of 28 | no |
| 52 Option book | opt_book_imb >= 0.9551 | 16, 66%, +6.6 % | 38, 30%, -2.3 % | 24 of 28 | no |
| 67 Agreement | agree_same >= 31 | 26.5, 58%, +4.3 % | 27.5, 24%, -3.5 % | 19 of 28 | no |
| 37 OI change | oi_own_chg_open < 6.79696e+06 | 37, 51%, +3.0 % | 17, 18%, -5.4 % | 15 of 28 | no |
| 20 Spot / futures / forward agreement | basis_chg300 >= 1.57 | 32.5, 54%, +3.1 % | 21.5, 21%, -3.8 % | 17 of 28 | no |
| 30 Sector split | wmove60_energy >= 0.674 | 20.5, 61%, +5.3 % | 33.5, 28%, -2.7 % | 24 of 28 | no |

## edge_gate_trail
43 trades on 13 days, 53% winners, mean +3.3 %. Losses: 16 never worked (weather), 4 worked then gave it back (exits). 343 fields, 3076 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_net_help5 >= 379041 | 26.5, 74%, +8.6 % | 19, 26%, -3.8 % | 10 of 18 | no |
| 53 Option's own levels | sl_room_dn_pct >= 1.666 | 28, 71%, +7.7 % | 17.5, 26%, -3.3 % | 11 of 18 | no |
| 37 OI change | oi_other_chg5 >= 63154 | 27.5, 69%, +6.6 % | 18, 31%, -1.3 % | 10 of 18 | no |
| 25 Traded volume | agg_with_rs >= 730158 | 23, 70%, +9.5 % | 22.5, 38%, -2.7 % | 12 of 18 | no |
| 37 OI change | oi_own_chg5 < -52325 | 27, 67%, +7.2 % | 18.5, 35%, -2.0 % | 10 of 18 | no |
| 13 Speed | mv60 >= -10.72 | 17, 74%, +7.2 % | 28.5, 42%, +1.2 % | 14 of 18 | no |
| 54 Premium race odds | po_dn15 < 1 | 17, 74%, +9.8 % | 28.5, 42%, -0.3 % | 13 of 18 | no |
| 25 Traded volume | fut_vol_vs_norm >= 0.8964 | 20.5, 63%, +6.7 % | 15, 33%, -2.9 % | 8 of 14 | no |

## edge_gate_only
38 trades on 13 days, 58% winners, mean +2.7 %. Losses: 14 never worked (weather), 2 worked then gave it back (exits). 345 fields, 3074 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 37 OI change | oi_net_help5 >= 1.03107e+06 | 16.5, 88%, +9.9 % | 26.5, 40%, -1.8 % | 16 of 18 | no |
| 53 Option's own levels | sl_room_dn_pct >= 1.666 | 26.5, 75%, +7.8 % | 16.5, 30%, -5.5 % | 11 of 18 | no |
| 37 OI change | oi_other_chg5 >= 63154 | 26.5, 74%, +6.2 % | 16.5, 33%, -3.0 % | 12 of 18 | no |
| 17 Realised volatility | rv1 >= 10.908 | 26, 73%, +7.6 % | 17, 35%, -4.9 % | 10 of 18 | no |
| 17 Realised volatility | rv5 >= 11.068 | 26, 73%, +7.7 % | 17, 35%, -5.0 % | 10 of 18 | no |
| 16 Swing distance | swing_behind >= 24.85 | 26, 73%, +5.9 % | 17, 35%, -2.3 % | 10 of 18 | no |
| 37 OI change | oi_net_help15 >= 2.13652e+06 | 25, 74%, +7.7 % | 17.5, 37%, -4.1 % | 11 of 17 | no |
| 12 Extremes' age | lo_age_min < 17.216 | 18, 78%, +8.9 % | 25, 44%, -1.8 % | 14 of 18 | no |

## apex_edge
37 trades on 13 days, 46% winners, mean +1.8 %. Losses: 17 never worked (weather), 3 worked then gave it back (exits). 336 fields, 3088 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 26 Absorption | absorb60 >= 1.84367e+07 | 24.5, 63%, +6.3 % | 15.5, 23%, -4.0 % | 11 of 19 | no |
| 25 Traded volume | agg_with_rs >= 693533 | 24.5, 63%, +6.6 % | 15.5, 23%, -4.5 % | 11 of 19 | no |
| 39 Gamma map | gex_wall_ahead >= 57.88 | 23.5, 64%, +5.9 % | 16.5, 24%, -2.9 % | 11 of 19 | no |
| 35 Sister indices | bank_z < -0.77 | 20.5, 66%, +6.3 % | 19.5, 28%, -1.9 % | 14 of 19 | no |
| 46 First-order Greeks | theta_min < -0.04388 | 24, 62%, +6.0 % | 16, 25%, -3.1 % | 12 of 19 | no |
| 37 OI change | oi_net_help5 >= 696293 | 15, 70%, +9.2 % | 25, 34%, -1.8 % | 14 of 19 | no |
| 33 Heavyweight books | hw_book_imb >= -0.0176 | 24.5, 61%, +5.1 % | 15.5, 26%, -2.0 % | 11 of 19 | no |
| 25 Traded volume | fut_ttq60 >= 10114 | 25, 60%, +5.4 % | 15, 27%, -2.9 % | 10 of 19 | no |

## straddle_spike
35 trades on 8 days, 31% winners, mean -1.8 %. Losses: 12 never worked (weather), 2 worked then gave it back (exits). 313 fields, 3010 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 30 Sector split | wmove60_bank < 3.96 | 17, 56%, +4.2 % | 21, 14%, -6.0 % | 7 of 15 | no |
| 13 Speed | fmv60 < 14.28 | 17.5, 54%, +4.4 % | 20.5, 15%, -6.4 % | 10 of 15 | no |
| 39 Gamma map | gex_flip_ahead >= -42.8 | 18, 53%, +4.7 % | 20, 15%, -6.9 % | 8 of 15 | no |
| 52 Option book | opt_opp_q=REFILLING < 0.5 | 21.5, 49%, +2.2 % | 16.5, 12%, -6.2 % | 6 of 15 | no |
| 38 Put/call ratio, max pain | e_pcr < 1.053 | 18.5, 51%, +5.7 % | 19.5, 15%, -8.2 % | 10 of 15 | no |
| 38 Put/call ratio, max pain | pcr < 1.053 | 18.5, 51%, +5.7 % | 19.5, 15%, -8.2 % | 10 of 15 | no |
| 55 VIX | vix_chg30 < -0.01 | 18.5, 51%, +3.2 % | 19.5, 15%, -5.8 % | 11 of 15 | no |

## m2.0_s0.5_novol
33 trades on 11 days, 42% winners, mean +0.3 %. Losses: 16 never worked (weather), 1 worked then gave it back (exits). 320 fields, 3086 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 55 VIX | vix >= 16.416 | 13, 73%, +4.2 % | 21, 24%, -2.0 % | 13 of 17 | no |
| 24 Refill vs withdrawal | fut_opp_o=REFILLING >= 0.5 | 16.5, 64%, +2.2 % | 17.5, 23%, -1.3 % | 12 of 17 | no |
| 60 Domino episode | ep_max_s >= 0.391 | 17.5, 60%, +2.9 % | 16.5, 24%, -2.4 % | 11 of 17 | no |
| 5 Opening gap | gap_pts < 17.96 | 20.5, 56%, +1.8 % | 13.5, 22%, -1.9 % | 10 of 17 | no |
| 21 Order-flow imbalance | e_fut_micro >= -0.04 | 18, 58%, +2.5 % | 16, 25%, -2.1 % | 12 of 17 | no |
| 5 Opening gap | gap_filled >= 0.5 | 24, 52%, +1.5 % | 10, 20%, -2.5 % | 6 of 17 | no |
| 46 First-order Greeks | theta_min < -0.0471 | 16, 59%, +2.1 % | 18, 28%, -1.2 % | 12 of 17 | no |

## c20_9x_r002
25 trades on 2 days, 64% winners, mean +7.4 %. Losses: 7 never worked (weather), 2 worked then gave it back (exits). 321 fields, 3006 lines tested.

| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |
|---|---|---|---|---|---|
| 34 Heavyweight volume | hw_vol_surge < 0.8522 | 15, 77%, +10.3 % | 17, 38%, -0.3 % | 11 of 15 | no |
| 39 Gamma map | gex_balance >= -0.023 | 17, 74%, +11.1 % | 15, 37%, -2.6 % | 10 of 15 | no |
| 38 Put/call ratio, max pain | e_pcr < 1.047 | 15, 73%, +12.8 % | 17, 41%, -2.5 % | 11 of 15 | no |
| 49 IV | iv_vs_med < 0.38 | 15, 73%, +9.8 % | 17, 41%, +0.1 % | 11 of 15 | no |
| 13 Speed | mv300 < 16.27 | 15, 73%, +7.6 % | 17, 41%, +2.2 % | 11 of 15 | no |
| 38 Put/call ratio, max pain | pcr < 1.047 | 15, 73%, +12.8 % | 17, 41%, -2.5 % | 11 of 15 | no |
| 54 Premium race odds | po_dn15 < 0.001 | 15, 73%, +9.0 % | 17, 41%, +0.9 % | 11 of 15 | no |
| 54 Premium race odds | po_ever >= 1 | 15, 73%, +9.0 % | 17, 41%, +0.9 % | 11 of 15 | no |

## Too few trades to search (under 30 rows)
m1.5_s0.4 (19), m2.0_s0.4 (19), m2.5_s0.4 (19), m1.5_s0.4_r003 (19), m2.0_s0.5_tvfast (18), m2.0_s0.5_bookexit (17), m1.5_s0.5 (16), m2.0_s0.5 (16), m2.5_s0.5 (16), m2.0_s0.5_ivinterp (16), m2.0_s0.5_d20 (16), spot_orb45 (16), spot_orb45_r005 (16), spot_orb45_r003 (15), m2.0_s0.5_trend (13), m1.5_s0.6 (13), m2.0_s0.6 (13), m2.5_s0.6 (13), spot_pb45_r002 (7), gap3_s0.4 (6), gap5_s0.4 (6), gap3_s0.4_r003 (6), m1.5_s0.4_r002 (5), spot_orb45_r002 (4), gap3_s0.4_r002 (2)
