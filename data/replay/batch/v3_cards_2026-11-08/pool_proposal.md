# Proposed Conductor pool — 2026-11-08

Every pair below is a lead found by searching the past (the 14 replayed days). Standing is **low** for all: no pair has a forward pass yet; `ret_per_trade` is the kept side's mean return per trade on the discovery days and is replaced by the forward figure as test days arrive. The owner admits, strikes or adds pairs; `--apply` then freezes the rules in the register and writes the pool.

## 2 proposed pairs

| Book | Rule | Condition at the trigger | Item | Kept: trades, win %, mean | Other side | Beats luck |
|---|---|---|---|---|---|---|
| edge_bracket_only | R-019 | `opt_vol1 < 2.7688e+06` | 50 Premium momentum | 79.5, 49%, +2.8 % | 20.5, 5%, -8.7 % | yes |
| edge_breakout | R-020 | `vomma >= 0.00646` | 47 Higher-order Greeks | 84, 46%, +1.7 % | 36, 11%, -6.8 % | yes |

## 55 books with no line beating luck (admit unrestricted, or leave out)

| Book | Trades | Days | Win % | Mean % | Never worked | Gave back |
|---|---|---|---|---|---|---|
| fade_switch | 702 | 13 | 50% | -0.1 | 343 | 7 |
| spot_dc12_t12_first | 571 | 13 | 38% | +0.0 | 285 | 70 |
| spot_dc12_t12_first_r003 | 545 | 13 | 37% | +0.0 | 277 | 68 |
| fade_switch_r002 | 414 | 13 | 48% | -0.2 | 207 | 7 |
| spot_ft_prem10 | 413 | 13 | 54% | +1.0 | 182 | 7 |
| spot_dc12_t12 | 274 | 13 | 35% | +0.3 | 145 | 32 |
| spot_dc12_t12_nolock | 274 | 13 | 35% | +0.5 | 145 | 32 |
| spot_dc12_t12_1130 | 254 | 13 | 35% | +0.5 | 134 | 30 |
| t28_d46_fill | 198 | 13 | 45% | +1.1 | 94 | 14 |
| t28_all | 191 | 13 | 46% | +1.1 | 90 | 13 |
| t28_core_fill | 190 | 13 | 45% | +1.0 | 91 | 13 |
| t28_fill | 181 | 13 | 49% | +1.3 | 82 | 11 |
| spot_dc12_t12_first_r002 | 99 | 12 | 41% | +0.7 | 39 | 19 |
| lvl_trail_be | 90 | 13 | 47% | +1.6 | 40 | 8 |
| lvl_trail | 87 | 13 | 46% | +1.7 | 38 | 9 |
| t28_fwd | 86 | 13 | 50% | +1.4 | 39 | 4 |
| lvl_trail_rx_be | 82 | 13 | 50% | +2.5 | 34 | 7 |
| t28_d46 | 82 | 13 | 48% | +2.2 | 36 | 7 |
| t28_tt8 | 82 | 13 | 59% | +1.4 | 30 | 4 |
| t28_mh15 | 82 | 13 | 52% | +2.1 | 33 | 6 |
| spot_dual | 79 | 13 | 48% | +1.4 | 35 | 6 |
| lvl_trail_re | 79 | 13 | 49% | +2.7 | 32 | 8 |
| lvl_trail_rx | 79 | 13 | 49% | +2.6 | 32 | 8 |
| lvl_trail_rx_c10 | 79 | 13 | 49% | +2.6 | 32 | 8 |
| t28_ts | 79 | 13 | 48% | +3.0 | 33 | 8 |
| t28_st20 | 77 | 13 | 51% | +2.9 | 31 | 7 |
| t28_gap | 77 | 13 | 51% | +3.0 | 30 | 8 |
| t28_gap_ts | 77 | 13 | 49% | +3.1 | 31 | 8 |
| spot_dual_lvl | 76 | 13 | 49% | +1.1 | 32 | 7 |
| t28_cheapK | 76 | 13 | 51% | +3.3 | 31 | 6 |
| t28_bidpile | 75 | 13 | 51% | +2.9 | 29 | 8 |
| c20_9e | 74 | 13 | 59% | +7.0 | 25 | 5 |
| t28_nohigh | 74 | 13 | 50% | +3.2 | 28 | 9 |
| spot_dual_rg | 72 | 13 | 49% | +1.4 | 31 | 6 |
| c20_9h | 71 | 13 | 55% | +6.5 | 26 | 6 |
| c20_9t | 71 | 13 | 73% | +4.4 | 18 | 1 |
| t28_req | 69 | 13 | 54% | +3.9 | 25 | 7 |
| c20_8x | 67 | 13 | 51% | +7.8 | 23 | 10 |
| t28_cheap | 67 | 13 | 52% | +4.0 | 24 | 8 |
| c20_9v | 66 | 13 | 67% | +9.9 | 18 | 4 |
| c20_9x | 65 | 13 | 55% | +9.6 | 22 | 7 |
| t28_ivfall | 65 | 13 | 57% | +3.9 | 23 | 5 |
| t28_dur20 | 62 | 13 | 50% | +3.3 | 25 | 6 |
| t28_core | 62 | 13 | 50% | +2.8 | 25 | 6 |
| c20_9s | 59 | 13 | 61% | +11.4 | 17 | 6 |
| c20_9y | 58 | 13 | 64% | +12.1 | 15 | 6 |
| spot_pb45 | 52 | 13 | 52% | -0.2 | 20 | 1 |
| c20_9x_r004 | 47 | 12 | 55% | +9.7 | 16 | 5 |
| spot_dc12_t12_r002 | 43 | 7 | 42% | -0.1 | 19 | 6 |
| edge_gate_trail | 43 | 13 | 53% | +3.3 | 16 | 4 |
| edge_gate_only | 38 | 13 | 58% | +2.7 | 14 | 2 |
| apex_edge | 37 | 13 | 46% | +1.8 | 17 | 3 |
| straddle_spike | 35 | 8 | 31% | -1.8 | 12 | 2 |
| m2.0_s0.5_novol | 33 | 11 | 42% | +0.3 | 16 | 1 |
| c20_9x_r002 | 25 | 2 | 64% | +7.4 | 7 | 2 |

## Not proposed

- m1.5_s0.4: too few rows
- m2.0_s0.4: too few rows
- m2.5_s0.4: too few rows
- m1.5_s0.4_r003: too few rows
- m2.0_s0.5_tvfast: too few rows
- m2.0_s0.5_bookexit: too few rows
- m1.5_s0.5: too few rows
- m2.0_s0.5: too few rows
- m2.5_s0.5: too few rows
- m2.0_s0.5_ivinterp: too few rows
- m2.0_s0.5_d20: too few rows
- spot_orb45: too few rows
- spot_orb45_r005: too few rows
- spot_orb45_r003: too few rows
- m2.0_s0.5_trend: too few rows
- m1.5_s0.6: too few rows
- m2.0_s0.6: too few rows
- m2.5_s0.6: too few rows
- spot_pb45_r002: too few rows
- gap3_s0.4: too few rows
- gap5_s0.4: too few rows
- gap3_s0.4_r003: too few rows
- m1.5_s0.4_r002: too few rows
- spot_orb45_r002: too few rows
- gap3_s0.4_r002: too few rows
