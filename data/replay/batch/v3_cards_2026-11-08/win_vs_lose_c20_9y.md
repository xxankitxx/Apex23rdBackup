# c20_9y: what the photograph recorded at the trigger — winners against losers

72 trades on the 14 days: 44 winners, 28 losers. For each field: the median and the middle half (25th to 75th percentile) of the winners, and the same for the losers. When the two middle halves overlap, no line on that field separates them.

## trend

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| er30 | 0.116 [0.0658, 0.207] | 0.134 [0.084, 0.234] | yes |
| er60 | 0.107 [0.0521, 0.216] | 0.123 [0.0717, 0.186] | yes |
| dir60 | 1 [-1, 1] | 1 [-1, 1] | yes |
| regime | 0 values | 0 values | text field: ['COMPRESSION', 'DIRECTIONAL', 'EXHAUSTION', 'RANGE', 'UNCERTAIN', 'WARMING'] |
| regime_with | 1 [0, 1] | 1 [0, 1] | yes |
| regime_ext_pct | 66.5 [34, 86.8] | 48.5 [24.2, 89.8] | yes |
| hmm_state | 1 [1, 2] | 1 [1, 2] | yes |
| hmm_p | 0.895 [0.733, 0.95] | 0.899 [0.736, 0.958] | yes |
| hmm_run_min | 2 [1, 3] | 1 [1, 2] | yes |
| imp_with | 1 [0, 1] | 1 [0, 1] | yes |
| imp_age_min | 6.14 [3.41, 21.4] | 9.71 [5.21, 21.1] | yes |
| imp_depth | 0.358 [0.229, 0.515] | 0.333 [0.14, 0.469] | yes |
| vwap_ext | 29.1 [-6.75, 51.6] | 29.6 [-16.9, 78] | yes |
| chop60 | 9.31 [4.62, 19.2] | 8.11 [5.37, 13.9] | yes |
| reversals60 | 28 [26, 31] | 27 [24, 31] | yes |

## speed

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| mv5 | 1.98 [0.575, 4.01] | 3.15 [1.25, 5.89] | yes |
| mv30 | 4.45 [2.24, 8.56] | 5.4 [1.21, 10.9] | yes |
| mv60 | 4.55 [-3.58, 11.4] | 2.67 [-1.03, 14.9] | yes |
| mv300 | 6.97 [-13.5, 16.6] | 2.62 [-17, 20.1] | yes |
| accel15 | 6.2 [2.38, 8.61] | 6.07 [1.2, 10.9] | yes |
| accel30 | 4.97 [1.41, 12] | 6.7 [2.7, 10.9] | yes |
| kv | 0.139 [0.044, 0.257] | 0.123 [0.0665, 0.328] | yes |
| kvt | 2.69 [0.85, 4.99] | 2.4 [1.3, 6.36] | yes |
| jump_z | 1.85 [0.602, 2.98] | 1.98 [0.73, 3.1] | yes |
| cusum | 0 [0, 0] | 0 [0, 0] | NO — a line exists here |
| rv1 | 10.9 [9.2, 12.7] | 11.2 [8.79, 13.1] | yes |
| rv5 | 10.9 [9.67, 13.9] | 10.9 [9.18, 12.4] | yes |
| rv15 | 0 values | 0 values | not enough values |
| fut_vol_surge | 0.73 [0.526, 1.61] | 1.31 [0.748, 2.6] | yes |
| hk_ratio | 1.18 [0.982, 1.33] | 1.06 [0.982, 1.2] | yes |
| dom_z | 1.02 [0.47, 1.55] | 0.93 [0.527, 1.63] | yes |

## greeks / IV

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| delta | 0.526 [-0.567, 0.608] | -0.551 [-0.609, 0.559] | yes |
| gamma | 0.00186 [0.00105, 0.00259] | 0.00156 [0.000965, 0.00274] | yes |
| theta_pct | 0.288 [0.0288, 0.473] | 0.0554 [0.0216, 0.495] | yes |
| vega | 2.33 [1.84, 9.36] | 7.29 [1.7, 11.1] | yes |
| vanna | -0.00111 [-0.00355, 0.00398] | 0.00352 [-0.00302, 0.00439] | yes |
| charm_min | 1e-06 [-0.000145, 0.000163] | -4e-06 [-0.000247, 3.75e-06] | yes |
| vomma | 0.00825 [0.00445, 0.0145] | 0.0119 [0.00532, 0.0168] | yes |
| speed_g | -1.55e-07 [-3.37e-06, 3.3e-06] | 2.35e-07 [-4.45e-07, 4.78e-06] | yes |
| iv | 0 values | 0 values | not enough values |
| iv_vs_med | -0.21 [-0.875, 0.503] | -0.14 [-0.63, 1.06] | yes |
| atm_iv_chg5 | -0.06 [-0.422, 0.103] | -0.035 [-0.232, 0.0475] | yes |
| e_iv_rv | 1.78 [1.45, 2.7] | 1.85 [1.39, 2.85] | yes |
| skew_atm | -0.01 [-0.16, 0.055] | -0.03 [-0.0875, 0.02] | yes |
| term_atm | 11.1 [1.29, 15.1] | 1.75 [-0.22, 16.3] | yes |
| gex_regime | 0 values | 0 values | text field: ['AMPLIFY', 'DAMPEN', 'MIXED'] |
| gex_flip_ahead | -7 [-39.7, 11.3] | -8.2 [-47.6, 21.1] | yes |

## flow / OI

| field | winners: median [25–75 %] | losers: median [25–75 %] | overlap of the middle halves |
|---|---|---|---|
| e_fut_ofi60 | 3.96 [-5.74, 13.9] | 5.73 [-4.9, 11.8] | yes |
| e_fut_imb5 | 0.01 [-0.365, 0.372] | 0.017 [-0.325, 0.301] | yes |
| fut_lead | 0.061 [-0.0172, 0.162] | 0.0385 [0.0148, 0.0932] | yes |
| agg_net | 0.402 [-0.14, 0.736] | 0.656 [0.244, 0.859] | yes |
| absorb60 | 28,711,328 [15,368,220, 58,754,995] | 26,330,794 [12,876,489, 97,275,772] | yes |
| kyle_lambda | 0.00104 [0.000573, 0.00161] | 0.00143 [0.00091, 0.00205] | yes |
| oi_net_help15 | 1,668,550 [-3,011,336, 4,748,250] | 1,854,710 [-2,532,026, 5,622,598] | yes |
| pcr | 1.01 [0.89, 1.16] | 0.921 [0.832, 1.05] | yes |
| breadth_dir | 0.524 [0.328, 0.799] | 0.39 [0.163, 0.685] | yes |
| wmove60 | 2.99 [-2.11, 7.05] | 1.96 [-0.645, 8.24] | yes |
| agree_same | 7 [7, 7] | 7 [6, 7] | NO — a line exists here |
| opt_book_imb | 0.861 [0.733, 0.933] | 0.821 [0.736, 0.887] | yes |
| vol_ratio_with | 1.2 [0.828, 1.67] | 1.04 [0.184, 1.56] | yes |

**regime** — winners: COMPRESSION 8, DIRECTIONAL 10, EXHAUSTION 1, RANGE 9, UNCERTAIN 11, WARMING 5; losers: COMPRESSION 4, DIRECTIONAL 6, EXHAUSTION 1, RANGE 3, UNCERTAIN 11, WARMING 3

**hmm_state** — winners: 0 7, 1 17, 2 16, 3 4; losers: 0 3, 1 14, 2 11, 3 0

**imp_with** — winners: False 17, True 27; losers: False 8, True 20

**regime_with** — winners: False 17, True 27; losers: False 13, True 15

**gex_regime** — winners: AMPLIFY 3, DAMPEN 7, MIXED 34; losers: AMPLIFY 3, DAMPEN 8, MIXED 17

**ep_type** — winners: BASKET-LED 16, CO-FIRST 23, FUTURES-LED 2, None 3; losers: BASKET-LED 12, CO-FIRST 11, FUTURES-LED 1, None 4

## Two factors at once (the cards searched one at a time)

Every pair of 192 numeric fields (1536 single lines: five quantile lines each, both directions), AND-combined, keeping at least 40 % of the trades. Score = share of losers removed minus share of winners removed.

Best found: `agree_same >= 7` AND `sl_room_dn_pct >= 1.808` -> keeps 33 of 72 trades: 29 winners, 4 losers (from 44 winners, 28 losers). Score 0.516.

Shuffle test: the same two-factor search on 200 random re-labellings of the same trades (same number of winners and losers) reached a best score of median 0.489, max 0.607; 56 of 200 shuffles matched or beat the real score 0.516. The combination does NOT beat luck: a search this wide finds a line this good in random labels too.
