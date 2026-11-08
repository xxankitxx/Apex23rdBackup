# c20_9x: what the photograph recorded at the trigger — winners against losers

81 trades on the 14 days: 43 winners, 38 losers. For each field: the median and the middle half (25th to 75th percentile) of the winners, and the same for the losers. When the two middle halves overlap, no line on that field separates them.

## trend

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| er30 | 0.113 [0.0653, 0.218] | 0.134 [0.0562, 0.222] | yes |
| er60 | 0.107 [0.0521, 0.216] | 0.14 [0.103, 0.183] | yes |
| dir60 | 1 [-1, 1] | 1 [-1, 1] | yes |
| regime | 0 values | 0 values | text field: ['BREAKOUT', 'COMPRESSION', 'DIRECTIONAL', 'EXHAUSTION', 'RANGE', 'UNCERTAIN'] |
| regime_with | 1 [0, 1] | 1 [0, 1] | yes |
| regime_ext_pct | 68 [33, 87] | 48.5 [31, 81.5] | yes |
| hmm_state | 1 [1, 2] | 1 [1, 2] | yes |
| hmm_p | 0.896 [0.737, 0.95] | 0.871 [0.732, 0.956] | yes |
| hmm_run_min | 2 [1, 3] | 1 [1, 2] | yes |
| imp_with | 1 [0, 1] | 1 [0, 1] | yes |
| imp_age_min | 6.23 [3.39, 22.1] | 9.06 [4.22, 19.6] | yes |
| imp_depth | 0.36 [0.225, 0.516] | 0.331 [0.103, 0.462] | yes |
| vwap_ext | 26.6 [-8.1, 51.2] | 13.1 [-32.3, 86.5] | yes |
| chop60 | 9.31 [4.62, 19.2] | 7.15 [5.46, 9.74] | yes |
| reversals60 | 28 [26, 31] | 27 [24, 31] | yes |

## speed

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| mv5 | 2 [0.5, 4.1] | 2.53 [1.16, 5.6] | yes |
| mv30 | 4.5 [2.8, 8.7] | 3.73 [1.26, 10.6] | yes |
| mv60 | 5.3 [-3.6, 11.7] | 1.98 [-1.11, 12.6] | yes |
| mv300 | 7.25 [-13.5, 16.8] | 2.62 [-15.8, 19.5] | yes |
| accel15 | 6.05 [2.05, 8.7] | 4.62 [0.75, 10.3] | yes |
| accel30 | 5.05 [1.9, 12.4] | 6.7 [3.09, 10.7] | yes |
| kv | 0.141 [0.04, 0.26] | 0.128 [0.056, 0.229] | yes |
| kvt | 2.74 [0.77, 5.06] | 2.49 [1.09, 4.46] | yes |
| jump_z | 1.8 [0.58, 2.57] | 2.06 [0.73, 3.2] | yes |
| cusum | 0 [0, 0] | 0 [0, 0] | NO — a line exists here |
| rv1 | 10.9 [9.3, 12.8] | 11.2 [8.83, 13.4] | yes |
| rv5 | 10.9 [9.62, 14] | 10.9 [9.23, 12.2] | yes |
| rv15 | 0 values | 0 values | not enough values |
| fut_vol_surge | 0.741 [0.525, 1.61] | 0.96 [0.66, 2.23] | yes |
| hk_ratio | 1.18 [0.99, 1.33] | 1.07 [0.98, 1.25] | yes |
| dom_z | 1.04 [0.5, 1.55] | 0.81 [0.455, 1.55] | yes |

## greeks / IV

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| delta | 0.527 [-0.568, 0.61] | -0.548 [-0.607, 0.549] | yes |
| gamma | 0.00192 [0.00105, 0.00259] | 0.00156 [0.00102, 0.0028] | yes |
| theta_pct | 0.313 [0.0339, 0.481] | 0.0554 [0.0229, 0.628] | yes |
| vega | 2.27 [1.83, 9.14] | 7.24 [1.65, 10.7] | yes |
| vanna | -0.00131 [-0.00356, 0.00351] | 0.00303 [-0.00272, 0.00433] | yes |
| charm_min | 1e-06 [-0.000186, 0.000173] | -4e-06 [-0.000292, 3.25e-06] | yes |
| vomma | 0.0081 [0.0044, 0.0137] | 0.0082 [0.0052, 0.0151] | yes |
| speed_g | -1.8e-07 [-3.55e-06, 4.13e-06] | 2.35e-07 [-3.57e-07, 5.45e-06] | yes |
| iv | 0 values | 0 values | not enough values |
| iv_vs_med | -0.19 [-0.88, 0.52] | -0.08 [-0.615, 2.18] | yes |
| atm_iv_chg5 | -0.08 [-0.44, 0.11] | -0.03 [-0.16, 0.228] | yes |
| e_iv_rv | 1.84 [1.45, 2.71] | 1.71 [1.35, 2.94] | yes |
| skew_atm | -0.01 [-0.16, 0.06] | -0.025 [-0.08, 0.065] | yes |
| term_atm | 11.1 [1.39, 15.2] | 1.75 [-0.287, 18.1] | yes |
| gex_regime | 0 values | 0 values | text field: ['AMPLIFY', 'DAMPEN', 'MIXED'] |
| gex_flip_ahead | -7.4 [-39.8, 10] | -10.3 [-49.4, 19.1] | yes |

## flow / OI

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| e_fut_ofi60 | 4.59 [-5.85, 14.2] | 4.56 [-5.47, 9.87] | yes |
| e_fut_imb5 | 0 [-0.371, 0.364] | 0.0435 [-0.348, 0.31] | yes |
| fut_lead | 0.055 [-0.019, 0.166] | 0.035 [0.0113, 0.0902] | yes |
| agg_net | 0.431 [-0.062, 0.751] | 0.472 [0.033, 0.767] | yes |
| absorb60 | 27,011,631 [15,171,850, 47,198,132] | 25,818,802 [13,507,103, 48,263,610] | yes |
| kyle_lambda | 0.00105 [0.000598, 0.00165] | 0.00137 [0.000746, 0.00195] | yes |
| oi_net_help15 | 1,562,210 [-3,463,135, 4,653,285] | 1,854,710 [-2,561,699, 6,000,898] | yes |
| pcr | 0.981 [0.885, 1.15] | 0.976 [0.852, 1.13] | yes |
| breadth_dir | 0.539 [0.326, 0.802] | 0.415 [0.215, 0.696] | yes |
| wmove60 | 3.16 [-2.24, 7.17] | 1.96 [-1, 7.14] | yes |
| agree_same | 1 [1, 1] | 1 [1, 1] | NO — a line exists here |
| opt_book_imb | 0.847 [0.721, 0.933] | 0.806 [0.729, 0.886] | yes |
| vol_ratio_with | 1.19 [0.827, 1.69] | 1.13 [0.475, 1.49] | yes |

**regime** — winners: BREAKOUT 0, COMPRESSION 7, DIRECTIONAL 10, EXHAUSTION 1, RANGE 9, UNCERTAIN 11, WARMING 5; losers: BREAKOUT 1, COMPRESSION 5, DIRECTIONAL 8, EXHAUSTION 1, RANGE 7, UNCERTAIN 13, WARMING 3

**hmm_state** — winners: 0 7, 1 16, 2 16, 3 4; losers: 0 4, 1 19, 2 12, 3 3

**imp_with** — winners: False 17, True 26; losers: False 13, True 25

**regime_with** — winners: False 16, True 27; losers: False 18, True 20

**gex_regime** — winners: AMPLIFY 3, DAMPEN 7, MIXED 33; losers: AMPLIFY 7, DAMPEN 9, MIXED 22

**ep_type** — winners: BASKET-LED 15, CO-FIRST 23, FUTURES-LED 2, None 3; losers: BASKET-LED 16, CO-FIRST 16, FUTURES-LED 1, None 5

## Two factors at once (the cards searched one at a time)

Every pair of 191 numeric fields (1528 single lines: five quantile lines each, both directions), AND-combined, keeping at least 40 % of the trades. Score = share of losers removed minus share of winners removed.

Best found: `dist_hi < 166.4` AND `new_highs < 132` -> keeps 45 of 81 trades: 33 winners, 12 losers (from 43 winners, 38 losers). Score 0.452.

Shuffle test: the same two-factor search on 200 random re-labellings of the same trades (same number of winners and losers) reached a best score of median 0.459, max 0.650; 108 of 200 shuffles matched or beat the real score 0.452. The combination does NOT beat luck: a search this wide finds a line this good in random labels too.
