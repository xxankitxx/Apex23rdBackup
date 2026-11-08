# Agent 4 — rule search report (8 Nov 2026)

Books: t28_dur20, t28_core, t28_core_fill, t28_fill, t28_all, t28_fwd.

Method (identical for every book, script `s2_search.py`): discovery = first 10 replayed days, holdout = last 4 (`rule_lab.split_days`). ~195 raw numeric weather fields + ~50 derived features (ratios, differences, products, direction interactions `x * sgn(CE/PE)`, within-day z-scores from the book's own earlier trades, hour bucket) + ~60 text indicators. Eight searches per book, each the best rule by `rule_lab.score_masks` (share of losers removed minus share of winners removed, kept >= 20) or by kept-side mean rupees: single clause at 5 or 9 quantile lines, text indicator, pair (top-800 single masks paired), pair over numeric+text, greedy triple (top-600), pair over derived features only. Every rule that met the discovery bar (kept >= 20, kept mean > 0, kept rupees > 0, removed losers > winners) was shuffle-tested with the SAME search on 200 shufflings of the discovery outcomes (`rule_lab.shuffle_p`, seed 7), then frozen and evaluated on the 4 holdout days. The first book (t28_dur20) was run with a wider pair search (top-2500 masks, plus raw-only pair and single_all variants); it took 83 minutes, so the other five use the trimmed list above.

Second pass (`s4_hypo.py`, rows named `narrow:*`, `OR_of_two`, `by_direction`): hypothesis-first NARROW searches - eight named families of 4-7 features each (theta vs speed, order flow in the trade's direction, trend, time of day, crowd/own-day record, room to the next level, vol state, liquidity), best single clause at 5 lines with the shuffle run on the same narrow family (a narrow search has a lower luck bar - the honest way to test an idea); an OR-of-two-clauses search over the union; and an either/or by direction (best clause inside CE trades, inside PE trades).

Verdict rule: PROPOSE only if discovery bar AND p < 0.05 AND holdout kept win% >= book's holdout win% AND holdout removed side not profitable.

## t28_dur20

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 62 | 32 | 30 | 52% | +4.15 | +277,706 |
| holdout | 18 | 9 | 9 | 50% | +2.77 | +40,635 |
| all | 80 | 41 | 39 | 51% | +3.84 | +318,341 |

By day: 10-19 18t 10W +131,670; 10-21 4t 3W +39,455; 10-22 3t 1W +474; 10-23 4t 3W +47,834; 10-26 5t 4W +55,169; 10-27 18t 9W +46,426; 10-28 4t 1W -13,429; 10-29 2t 0W -18,434; 10-30 2t 0W -18,616; 11-02 2t 1W +7,156; 11-03 11t 5W -9,848; 11-04 1t 1W +22,409; 11-05 2t 1W +6,676; 11-06 4t 2W +21,398

Search space: 195 raw numeric + 50 derived + 61 text indicators. Run time 4986 s.

### Best rule found

### t28_dur20: `is_CE < 1 AND depth_age_fut >= 0.65`

Shuffle test p = 0.120 (does NOT beat luck). Search `by_direction:PE` (36 features, 5 lines). real score 0.463.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 62 | 52% | +4.2 | +277,706 | 30 |
| discovery | kept | 25 | 72% | +9.5 | +264,790 | 7 |
| discovery | removed | 37 | 38% | +0.6 | +12,916 | 23 |
| holdout | book | 18 | 50% | +2.8 | +40,635 | 9 |
| holdout | kept | 6 | 33% | -0.8 | -3,793 | 4 |
| holdout | removed | 12 | 58% | +4.6 | +44,428 | 5 |
| all | book | 80 | 51% | +3.8 | +318,341 | 39 |
| all | kept | 31 | 65% | +7.5 | +260,998 | 11 |
| all | removed | 49 | 43% | +1.5 | +57,343 | 28 |

Features used: `depth_age_fut` = raw weather field; `is_CE` = 1 if rr==CE else 0

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `agg_with_rs >= 9.419e+05` | 31 / 68% / +280,017 / 10 | 31 / 20 / -2,311 | yes | 0.910 | 11 / 64% / +59,686 / 4 | 7 / -19,052 | yes |
| single_raw_q9 | `bp_sig >= 1.022` | 25 / 72% / +266,139 / 7 | 37 / 23 / +11,567 | yes | 0.910 | 6 / 50% / +29,780 / 3 | 12 / +10,855 | NO |
| single_all_q5 | `agg_with_rs >= 9.419e+05` | 31 / 68% / +280,017 / 10 | 31 / 20 / -2,311 | yes | 0.935 | 11 / 64% / +59,686 / 4 | 7 / -19,052 | yes |
| single_all_q9 | `bp_sig >= 1.022` | 25 / 72% / +266,139 / 7 | 37 / 23 / +11,567 | yes | 0.930 | 6 / 50% / +29,780 / 3 | 12 / +10,855 | NO |
| single_text | `opt_opp_o=REFILLING < 1` | 39 / 62% / +237,624 / 15 | 23 / 15 / +40,082 | yes | 0.440 | 15 / 53% / +42,305 / 7 | 3 / -1,670 | yes |
| single_all_pnl_q5 | `dom_z_with >= 0.85` | 20 / 70% / +258,245 / 6 | 42 / 24 / +19,461 | yes | 0.200 | 5 / 20% / -7,595 / 4 | 13 / +48,230 | NO |
| pair_raw_q5 | `svi_res >= 0.01 AND vix_chg_open >= -0.127` | 24 / 83% / +360,906 / 4 | 38 / 26 / -83,200 | yes | 0.670 | 11 / 55% / +43,618 / 5 | 7 / -2,984 | yes |
| pair_all_q5 | `svi_res >= 0.01 AND vix_chg_open >= -0.127` | 24 / 83% / +360,906 / 4 | 38 / 26 / -83,200 | yes | 0.765 | 11 / 55% / +43,618 / 5 | 7 / -2,984 | yes |
| pair_all+text_q5 | `svi_res >= 0.01 AND vix_chg_open >= -0.127` | 24 / 83% / +360,906 / 4 | 38 / 26 / -83,200 | yes | 0.775 | 11 / 55% / +43,618 / 5 | 7 / -2,984 | yes |
| triple_all_q5 | `svi_res >= 0.01 AND vix_chg_open >= -0.127 AND ret_today < 87.37` | 21 / 95% / +404,261 / 1 | 41 / 29 / -126,555 | yes | 0.490 | 11 / 55% / +43,618 / 5 | 7 / -2,984 | yes |
| pair_derived_only_q5 | `prev_n_today >= 3 AND theta_be15_over_mv60 < 3.401` | 29 / 76% / +384,124 / 7 | 33 / 23 / -106,418 | yes | 0.370 | 7 / 57% / +1,664 / 3 | 11 / +38,971 | NO |
| narrow:theta_vs_speed | `theta_be15_over_mv60 < 1.962` | 43 / 58% / +246,490 / 18 | 19 / 12 / +31,216 | yes | 0.590 | 13 / 54% / +39,348 / 6 | 5 / +1,287 | NO |
| narrow:flow_with | `agg_with_rs >= 9.419e+05` | 31 / 68% / +280,017 / 10 | 31 / 20 / -2,311 | yes | 0.125 | 11 / 64% / +59,686 / 4 | 7 / -19,052 | yes |
| narrow:trend_with | `kv_with >= -0.0351` | 43 / 60% / +345,290 / 17 | 19 / 13 / -67,584 | yes | 0.125 | 14 / 43% / +4,196 / 8 | 4 / +36,439 | NO |
| narrow:time_of_day | `mins_to_flat >= 182.2` | 31 / 58% / +210,658 / 13 | 31 / 17 / +67,048 | yes | 0.845 | 12 / 50% / +12,893 / 6 | 6 / +27,742 | NO |
| narrow:crowd | `ret_today < 87.37` | 55 / 58% / +380,422 / 23 | 7 / 7 / -102,716 | yes | 0.320 | 18 / 50% / +40,635 / 9 | 0 / +0 | yes |
| narrow:room | `swing_ahead >= 3.965` | 55 / 56% / +345,033 / 24 | 7 / 6 / -67,327 | yes | 0.790 | 17 / 47% / +37,203 / 9 | 1 / +3,432 | NO |
| narrow:vol_state | `iv_minus_rv < 15.82` | 31 / 58% / +197,275 / 13 | 31 / 17 / +80,431 | yes | 0.820 | 11 / 64% / +54,259 / 4 | 7 / -13,624 | yes |
| narrow:liquidity | `quote_age >= 0.43` | 31 / 65% / +205,605 / 11 | 31 / 19 / +72,101 | yes | 0.390 | 8 / 62% / +22,620 / 3 | 10 / +18,015 | NO |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `agg_net >= 0.1609 AND depth_age_fut >= 1.5` | 26 / 77% / +324,470 / 6 | 36 / 24 / -46,764 | yes | 0.425 | 8 / 50% / +12,324 / 4 | 10 / +28,311 | NO |
| by_direction:CE | `is_CE >= 1 AND agg_with_rs >= 2.052e+05` | 23 / 52% / +53,222 / 11 | 39 / 19 / +224,484 | NO |  | 9 / 78% / +60,489 / 2 | 9 / -19,854 | yes |
| by_direction:PE | `is_CE < 1 AND depth_age_fut >= 0.65` | 25 / 72% / +264,790 / 7 | 37 / 23 / +12,916 | yes | 0.120 | 6 / 33% / -3,793 / 4 | 12 / +44,428 | NO |

### Reading

The book is a coin-flip (51% winners) carried by a few large winners (+3.2 lakh on 80 trades). Every search found a rule that looks superb on the discovery days: the pair `svi_res >= 0.01 AND vix_chg_open >= -0.127` keeps 24 of 62 with 83% winners and the greedy triple keeps 21 with ONE loser. But the shuffle test says random labels produce rules this good 67-78% of the time (pairs) and 49% (triple) - with 62 trades and ~250 fields the search can always memorise the tape. The most honest single, `agg_with_rs >= 9.4 lakh` (aggressive rupees in the trade's direction), had p=0.91 in the wide search and p=0.125 in the narrow 6-feature flow family, and on holdout it kept 11 of 18 at 64% (+59,686) and removed 7 at -19,052 - the right sign but far from a proof. No rule honestly removes this book's losers: every candidate is either luck by the shuffle or dies on the 4 held-out days (bp_sig, dom_z_with, the derived pair). Verdict NONE.

**Verdict: NONE**

## t28_core

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 62 | 31 | 31 | 50% | +3.56 | +248,758 |
| holdout | 18 | 10 | 8 | 56% | +3.23 | +53,410 |
| all | 80 | 41 | 39 | 51% | +3.48 | +302,169 |

By day: 10-19 18t 10W +131,670; 10-21 4t 3W +43,839; 10-22 3t 1W -127; 10-23 3t 2W +16,367; 10-26 5t 4W +68,149; 10-27 18t 9W +46,426; 10-28 4t 1W -14,710; 10-29 2t 0W -18,197; 10-30 2t 0W -18,522; 11-02 3t 1W -6,139; 11-03 11t 5W -9,848; 11-04 1t 1W +28,308; 11-05 2t 1W -2,580; 11-06 4t 3W +37,531

Search space: 195 raw numeric + 50 derived + 60 text indicators. Run time 1891 s.

### Best rule found

### t28_core: `kv_with >= -0.0351`

Shuffle test p = 0.210 (does NOT beat luck). Search `narrow:trend_with` (2 features, 5 lines). real score 0.226.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 62 | 50% | +3.6 | +248,758 | 31 |
| discovery | kept | 43 | 58% | +5.9 | +307,895 | 18 |
| discovery | removed | 19 | 32% | -1.8 | -59,137 | 13 |
| holdout | book | 18 | 56% | +3.2 | +53,410 | 8 |
| holdout | kept | 14 | 50% | +1.2 | +13,364 | 7 |
| holdout | removed | 4 | 75% | +10.3 | +40,046 | 1 |
| all | book | 80 | 51% | +3.5 | +302,169 | 39 |
| all | kept | 57 | 56% | +4.8 | +321,259 | 25 |
| all | removed | 23 | 39% | +0.3 | -19,090 | 14 |

Features used: `kv_with` = kv * sgn(dir)

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `basis_chg60 >= -2.975` | 43 / 60% / +315,572 / 17 | 19 / 14 / -66,814 | yes | 1.000 | 17 / 53% / +38,266 / 8 | 1 / +15,145 | NO |
| single_all_q9 | `zomma >= -6.528e-05` | 37 / 65% / +296,260 / 13 | 25 / 18 / -47,502 | yes | 0.835 | 12 / 50% / +49,582 / 6 | 6 / +3,828 | NO |
| single_text | `strad_state=DECAYING < 1` | 25 / 68% / +243,779 / 8 | 37 / 23 / +4,979 | yes | 0.215 | 8 / 50% / -9,425 / 4 | 10 / +62,836 | NO |
| single_all_pnl_q5 | `basis_chg60 >= 2` | 20 / 70% / +218,803 / 6 | 42 / 25 / +29,955 | yes | 0.455 | 5 / 80% / +6,292 / 1 | 13 / +47,118 | NO |
| pair_all_q5 | `opt_book_imb >= 0.7699 AND ret_today < 87.37` | 36 / 72% / +402,350 / 10 | 26 / 21 / -153,592 | yes | 0.715 | 11 / 45% / -9,848 / 6 | 7 / +63,258 | NO |
| pair_all+text_q5 | `opt_book_imb >= 0.7699 AND ret_today < 87.37` | 36 / 72% / +402,350 / 10 | 26 / 21 / -153,592 | yes | 0.725 | 11 / 45% / -9,848 / 6 | 7 / +63,258 | NO |
| triple_all_q5 | `opt_book_imb >= 0.7699 AND ret_today < 87.37 AND fut_spread >= 1.01` | 31 / 81% / +430,316 / 6 | 31 / 25 / -181,558 | yes | 0.480 | 9 / 44% / -7,962 / 5 | 9 / +61,373 | NO |
| pair_derived_only_q5 | `swing_ahead_over_behind < 1.397 AND swing_ahead_over_theta_be15 >= 0.3658` | 36 / 69% / +280,078 / 11 | 26 / 20 / -31,320 | yes | 0.495 | 13 / 38% / -18,232 / 8 | 5 / +71,643 | NO |
| narrow:theta_vs_speed | `theta_be15_over_mv60 < 1.962` | 43 / 56% / +217,542 / 19 | 19 / 12 / +31,216 | yes | 0.795 | 13 / 62% / +52,124 / 5 | 5 / +1,287 | NO |
| narrow:flow_with | `opt_book_imb >= 0.7699` | 43 / 60% / +299,634 / 17 | 19 / 14 / -50,876 | yes | 0.300 | 11 / 45% / -9,848 / 6 | 7 / +63,258 | NO |
| narrow:trend_with | `kv_with >= -0.0351` | 43 / 58% / +307,895 / 18 | 19 / 13 / -59,137 | yes | 0.210 | 14 / 50% / +13,364 / 7 | 4 / +40,046 | NO |
| narrow:time_of_day | `mins_open < 181.2` | 31 / 58% / +205,361 / 13 | 31 / 18 / +43,397 | yes | 0.680 | 12 / 58% / +32,812 / 5 | 6 / +20,598 | NO |
| narrow:crowd | `ret_today < 87.37` | 55 / 56% / +351,474 / 24 | 7 / 7 / -102,716 | yes | 0.400 | 18 / 56% / +53,410 / 8 | 0 / +0 | yes |
| narrow:room | `swing_ahead >= 3.965` | 55 / 55% / +316,085 / 25 | 7 / 6 / -67,327 | yes | 0.905 | 17 / 53% / +49,978 / 8 | 1 / +3,432 | NO |
| narrow:vol_state | `iv_minus_rv < 19.97` | 43 / 53% / +264,560 / 20 | 19 / 11 / -15,802 | yes | 0.960 | 15 / 60% / +64,415 / 6 | 3 / -11,004 | yes |
| narrow:liquidity | `fut_spread >= 2.6` | 44 / 59% / +264,404 / 18 | 18 / 13 / -15,646 | yes | 0.270 | 12 / 50% / +25,148 / 6 | 6 / +28,262 | NO |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `fut_spread >= 2.6 AND ofi60_with >= 8.361` | 51 / 61% / +348,130 / 20 | 11 / 11 / -99,372 | yes | 0.950 | 16 / 56% / +51,304 / 7 | 2 / +2,106 | NO |
| by_direction:CE | `is_CE >= 1 AND agg_with_rs >= 2.052e+05` | 23 / 52% / +61,165 / 11 | 39 / 20 / +187,593 | yes | 0.995 | 9 / 78% / +64,252 / 2 | 9 / -10,842 | yes |
| by_direction:PE | `is_CE < 1 AND depth_age_fut >= 0.6` | 25 / 68% / +223,798 / 8 | 37 / 23 / +24,960 | yes | 0.325 | 6 / 50% / +15,457 / 3 | 12 / +37,954 | NO |

### Reading

Same 80 trades as t28_dur20 up to exit handling (identical trigger set, CE 36 / PE 44), so the same picture: discovery-perfect pairs (`opt_book_imb >= 0.77 AND ret_today < 87`, 72% kept) with shuffle p 0.7, and this time they also fail holdout (kept 11 at 45%, removed side +63,258). Not one of the 19 searches passes the shuffle; the best p was the DECAYING-straddle exclusion at 0.215, which lost on holdout (8 kept, 50%, -9,425). The within-day `ret_today < 87` clause (don't fire after the book already made 87% today) keeps every holdout trade so it says nothing there. NONE.

**Verdict: NONE**

## t28_core_fill

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 160 | 76 | 84 | 48% | +1.90 | +435,263 |
| holdout | 48 | 20 | 28 | 42% | -0.17 | -16,825 |
| all | 208 | 96 | 112 | 46% | +1.42 | +418,438 |

By day: 10-19 18t 10W +131,670; 10-21 17t 13W +215,550; 10-22 9t 4W -5,577; 10-23 17t 12W +125,096; 10-26 16t 7W +22,308; 10-27 18t 9W +46,426; 10-28 14t 5W -15,405; 10-29 12t 5W -5,606; 10-30 18t 5W -41,710; 11-02 21t 6W -37,489; 11-03 11t 5W -9,848; 11-04 6t 1W -22,789; 11-05 12t 5W +3,019; 11-06 19t 9W +12,792

Search space: 195 raw numeric + 54 derived + 62 text indicators. Run time 1135 s.

### Best rule found

### t28_core_fill: `fut_tot_imb_with < -0.1175`

Shuffle test p = 0.030 (beats luck). Search `narrow:flow_with` (6 features, 5 lines). real score 0.251.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 160 | 48% | +1.9 | +435,263 | 84 |
| discovery | kept | 80 | 60% | +4.3 | +434,866 | 32 |
| discovery | removed | 80 | 35% | -0.5 | +396 | 52 |
| holdout | book | 48 | 42% | -0.2 | -16,825 | 28 |
| holdout | kept | 0 |  |  | +0 | 0 |
| holdout | removed | 48 | 42% | -0.2 | -16,825 | 28 |
| all | book | 208 | 46% | +1.4 | +418,438 | 112 |
| all | kept | 80 | 60% | +4.3 | +434,866 | 32 |
| all | removed | 128 | 38% | -0.4 | -16,429 | 80 |

Features used: `fut_tot_imb_with` = e_fut_tot_imb * sgn(dir)

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `oi_own_chg_open < 6.83e+06` | 112 / 56% / +526,350 / 49 | 48 / 35 / -91,088 | yes | 0.365 | 34 / 44% / +1,570 / 19 | 14 / -18,395 | yes |
| single_all_q9 | `fut_tot_imb_with < -0.1175` | 80 / 60% / +434,866 / 32 | 80 / 52 / +396 | yes | 0.485 | 0 /  / +0 / 0 | 48 / -16,825 | NO |
| single_text | `strad_state=WARMING >= 1` | 23 / 65% / +182,481 / 8 | 137 / 76 / +252,782 | yes | 0.990 | 3 / 67% / +7,326 / 1 | 45 / -24,151 | yes |
| single_all_pnl_q5 | `depth_age_fut >= 1.5` | 24 / 62% / +239,762 / 9 | 136 / 75 / +195,500 | yes | 0.050 | 4 / 75% / +20,000 / 1 | 44 / -36,826 | yes |
| pair_all_q5 | `oi_own_chg_open < 6.83e+06 AND fut_lead >= 0.0261` | 78 / 67% / +627,286 / 26 | 82 / 58 / -192,023 | yes | 0.100 | 12 / 25% / -38,214 / 9 | 36 / +21,388 | NO |
| pair_all+text_q5 | `oi_own_chg_open < 6.83e+06 AND fut_lead >= 0.0261` | 78 / 67% / +627,286 / 26 | 82 / 58 / -192,023 | yes | 0.105 | 12 / 25% / -38,214 / 9 | 36 / +21,388 | NO |
| triple_all_q5 | `oi_own_chg_open < 6.83e+06 AND fut_lead >= 0.0261 AND ep_age_s >= 9.54` | 64 / 75% / +632,180 / 16 | 96 / 68 / -196,918 | yes | 0.050 | 11 / 18% / -49,212 / 9 | 37 / +32,386 | NO |
| pair_derived_only_q5 | `fut_tot_imb_with < -0.1175 AND premium_zday >= 1.145` | 65 / 66% / +405,646 / 22 | 95 / 62 / +29,617 | yes | 0.235 | 0 /  / +0 / 0 | 48 / -16,825 | NO |
| narrow:theta_vs_speed | `absdelta_x_speed15_over_prem < 0.02213` | 46 / 63% / +260,162 / 17 | 114 / 67 / +175,100 | yes | 0.130 | 18 / 39% / +2,977 / 11 | 30 / -19,802 | NO |
| narrow:flow_with | `fut_tot_imb_with < -0.1175` | 80 / 60% / +434,866 / 32 | 80 / 52 / +396 | yes | 0.030 | 0 /  / +0 / 0 | 48 / -16,825 | NO |
| narrow:trend_with | `kv_with >= -0.114` | 114 / 50% / +443,914 / 57 | 46 / 27 / -8,652 | yes | 0.755 | 36 / 39% / -32,780 / 22 | 12 / +15,954 | NO |
| narrow:time_of_day | `hrs_to_expiry >= 98` | 80 / 52% / +255,886 / 38 | 80 / 46 / +179,377 | yes | 0.775 | 15 / 40% / -2,304 / 9 | 33 / -14,521 | NO |
| narrow:crowd | `ret_today >= 1.591` | 80 / 56% / +460,154 / 35 | 80 / 49 / -24,892 | yes | 0.225 | 19 / 32% / -36,826 / 13 | 29 / +20,000 | NO |
| narrow:room | `wall_room < 457.7` | 117 / 52% / +421,908 / 56 | 43 / 28 / +13,354 | yes | 0.550 | 38 / 45% / +12,337 / 21 | 10 / -29,162 | yes |
| narrow:vol_state | `iv_minus_rv < 5.205` | 80 / 54% / +292,575 / 37 | 80 / 47 / +142,688 | yes | 0.475 | 20 / 35% / -28,334 / 13 | 28 / +11,508 | NO |
| narrow:liquidity | `spread_pct < 0.2385` | 80 / 56% / +343,990 / 35 | 80 / 49 / +91,273 | yes | 0.310 | 27 / 37% / -35,714 / 17 | 21 / +18,889 | NO |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `fut_tot_imb_with < -0.2735 AND opt_book_imb >= 0.768` | 99 / 60% / +594,474 / 40 | 61 / 44 / -159,211 | yes | 0.175 | 14 / 43% / -13,306 / 8 | 34 / -3,520 | yes |
| by_direction:CE | `is_CE >= 1 AND hour_bucket >= 2` | 39 / 54% / +113,636 / 18 | 121 / 66 / +321,626 | yes | 0.800 | 12 / 67% / +55,048 / 4 | 36 / -71,874 | yes |
| by_direction:PE | `is_CE < 1 AND opt_book_imb >= 0.7575` | 45 / 62% / +366,967 / 17 | 115 / 67 / +68,296 | yes | 0.905 | 6 / 17% / -30,414 / 5 | 42 / +13,588 | NO |

### Reading

The largest book (208 trades) and the one where the holdout record is negative (48 trades, 42%, -16,825) - so a rule has a real target. The wide pair `oi_own_chg_open < 6.8m AND fut_lead >= 0.026` keeps 78 at 67% on discovery with p=0.10, then collapses on holdout (12 kept at 25%, -38,214) - the clearest memory-of-the-tape of the whole run. Two rules reach p~0.05: `depth_age_fut >= 1.5` (p=0.05, by kept-side rupees) keeps only 24 of 160 and 4 of 48 on holdout (3 wins, +20,000) - too thin to call; and in the narrow flow family `fut_tot_imb_with < -0.1175` (total futures book imbalance AGAINST the trade's direction) has p=0.03 on 80 kept at 60%, but on holdout it keeps ZERO of 48 trades, so there is nothing to judge it on and the rule would simply switch the book off. The by-direction split `is_CE AND hour_bucket >= 2` passes holdout (12 kept at 67%) but p=0.8. Nothing passes all three gates. NONE.

**Verdict: NONE**

## t28_fill

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 155 | 78 | 77 | 50% | +2.09 | +343,164 |
| holdout | 44 | 20 | 24 | 45% | +0.39 | +15,116 |
| all | 199 | 98 | 101 | 49% | +1.71 | +358,280 |

By day: 10-19 18t 10W +131,670; 10-21 16t 11W +118,921; 10-22 9t 5W +19,237; 10-23 16t 10W +61,945; 10-26 17t 7W -3,718; 10-27 18t 9W +46,426; 10-28 15t 7W +1,540; 10-29 12t 5W -7,482; 10-30 18t 8W -10,852; 11-02 16t 6W -14,524; 11-03 11t 5W -9,848; 11-04 6t 1W -20,407; 11-05 10t 7W +48,363; 11-06 17t 7W -2,993

Search space: 196 raw numeric + 53 derived + 63 text indicators. Run time 498 s.

### Best rule found

### t28_fill: `is_CE >= 1 AND prev_win_today < 0.5`

Shuffle test p = 0.080 (does NOT beat luck). Search `by_direction:CE` (37 features, 5 lines). real score 0.367.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 155 | 50% | +2.1 | +343,164 | 77 |
| discovery | kept | 39 | 64% | +3.6 | +141,784 | 14 |
| discovery | removed | 116 | 46% | +1.6 | +201,380 | 63 |
| holdout | book | 44 | 45% | +0.4 | +15,116 | 24 |
| holdout | kept | 14 | 64% | +4.1 | +39,855 | 5 |
| holdout | removed | 30 | 37% | -1.3 | -24,739 | 19 |
| all | book | 199 | 49% | +1.7 | +358,280 | 101 |
| all | kept | 53 | 64% | +3.8 | +181,639 | 19 |
| all | removed | 146 | 44% | +1.0 | +176,641 | 82 |

Features used: `is_CE` = 1 if rr==CE else 0; `prev_win_today` = win rate of this book's earlier trades today (None if first)

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `svi_res >= 0.01` | 80 / 61% / +368,166 / 31 | 75 / 46 / -25,002 | yes | 0.635 | 21 / 48% / +14,154 / 11 | 23 / +962 | NO |
| single_all_q9 | `pcr_chg30 >= -0.036` | 94 / 61% / +417,063 / 37 | 61 / 40 / -73,898 | yes | 0.540 | 35 / 54% / +57,622 / 16 | 9 / -42,507 | yes |
| single_text | `strad_state=WARMING >= 1` | 26 / 65% / +161,928 / 9 | 129 / 68 / +181,236 | yes | 0.985 | 4 / 75% / +13,380 / 1 | 40 / +1,736 | NO |
| single_all_pnl_q5 | `depth_age_fut >= 1.5` | 22 / 59% / +176,514 / 9 | 133 / 68 / +166,650 | yes | 0.360 | 4 / 50% / +7,150 / 2 | 40 / +7,966 | NO |
| pair_all_q5 | `svi_res >= 0.01 AND ep_age_s >= 8.66` | 61 / 70% / +402,022 / 18 | 94 / 59 / -58,858 | yes | 0.730 | 18 / 44% / +858 / 10 | 26 / +14,258 | NO |
| pair_all+text_q5 | `svi_res >= 0.01 AND ep_age_s >= 8.66` | 61 / 70% / +402,022 / 18 | 94 / 59 / -58,858 | yes | 0.765 | 18 / 44% / +858 / 10 | 26 / +14,258 | NO |
| triple_all_q5 | `svi_res >= 0.01 AND ep_age_s >= 8.66 AND sync_dir < 0.1822` | 51 / 78% / +405,379 / 11 | 104 / 66 / -62,215 | yes | 0.645 | 17 / 47% / +8,268 / 9 | 27 / +6,848 | NO |
| pair_derived_only_q5 | `fut_imb5_with < 0.4924 AND gamma_x_speed15 < 0.006809` | 38 / 74% / +218,907 / 10 | 117 / 67 / +124,257 | yes | 0.985 | 13 / 46% / +22,132 / 7 | 31 / -7,017 | yes |
| narrow:theta_vs_speed | `absdelta_x_speed15_over_prem < 0.02003` | 43 / 65% / +191,178 / 15 | 112 / 62 / +151,986 | yes | 0.270 | 14 / 50% / +33,358 / 7 | 30 / -18,242 | yes |
| narrow:flow_with | `fut_tot_imb_with < -0.0152` | 108 / 56% / +398,928 / 48 | 47 / 29 / -55,764 | yes | 0.620 | 2 / 0% / -10,660 / 2 | 42 / +25,776 | NO |
| narrow:trend_with | `kv_with < 0.016` | 77 / 55% / +167,622 / 35 | 78 / 42 / +175,542 | yes | 0.640 | 18 / 61% / +63,976 / 7 | 26 / -48,860 | yes |
| narrow:time_of_day | `hrs_to_expiry >= 98.72` | 78 / 54% / +161,740 / 36 | 77 / 41 / +181,425 | yes | 0.945 | 13 / 38% / -6,721 / 8 | 31 / +21,837 | NO |
| narrow:crowd | `prev_win_today < 0.5` | 70 / 59% / +320,369 / 29 | 85 / 48 / +22,796 | yes | 0.460 | 25 / 44% / +88 / 14 | 19 / +15,028 | NO |
| narrow:room | `wall_room < 446.9` | 117 / 54% / +319,683 / 54 | 38 / 23 / +23,481 | yes | 0.870 | 36 / 47% / +26,361 / 19 | 8 / -11,245 | yes |
| narrow:vol_state | `iv_minus_rv < 5.09` | 77 / 55% / +183,222 / 35 | 78 / 42 / +159,942 | yes | 0.885 | 15 / 47% / +1,076 / 8 | 29 / +14,040 | NO |
| narrow:liquidity | `quote_age >= 0.39` | 79 / 58% / +285,909 / 33 | 76 / 44 / +57,255 | yes | 0.395 | 21 / 52% / +26,994 / 10 | 23 / -11,879 | yes |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `gex_wall_ahead >= 258.7 AND prev_win_today < 0.5` | 83 / 61% / +429,959 / 32 | 72 / 45 / -86,794 | yes | 0.910 | 26 / 42% / -6,386 / 15 | 18 / +21,502 | NO |
| by_direction:CE | `is_CE >= 1 AND prev_win_today < 0.5` | 39 / 64% / +141,784 / 14 | 116 / 63 / +201,380 | yes | 0.080 | 14 / 64% / +39,855 / 5 | 30 / -24,739 | yes |
| by_direction:PE | `is_CE < 1 AND depth_age_fut >= 1` | 42 / 69% / +356,580 / 13 | 113 / 64 / -13,416 | yes | 0.135 | 7 / 14% / -35,080 / 6 | 37 / +50,196 | NO |

### Reading

199 trades, 49% winners, holdout flat (+15,116 on 44). Discovery favourites `svi_res >= 0.01` (SVI residual) and its pair with `ep_age_s >= 8.7` show p 0.63-0.77 - the shuffle median beats them - and on holdout the kept side wins 44-48%, below the book's 45%, so they fail twice. The one near-miss is the direction split `is_CE AND prev_win_today < 0.5` (CE trades only, when the book's earlier trades today were mostly losers): discovery 39 kept at 64%, holdout 14 kept at 64% (+39,855) with the removed side -24,739, but p=0.08 on the narrow search, so it is reported as rejected; it is the one idea on these six books worth re-testing when more days are recorded. `pcr_chg30 >= -0.036` passes holdout (35 kept, 54%, removed -42,507) but p=0.54. NONE.

**Verdict: NONE**

## t28_all

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 161 | 78 | 83 | 48% | +2.04 | +436,095 |
| holdout | 48 | 20 | 28 | 42% | -0.19 | -18,151 |
| all | 209 | 98 | 111 | 47% | +1.53 | +417,944 |

By day: 10-19 18t 10W +131,670; 10-21 17t 13W +215,550; 10-22 9t 4W -5,577; 10-23 17t 12W +104,176; 10-26 16t 7W +22,308; 10-27 18t 9W +46,426; 10-28 14t 5W -15,405; 10-29 12t 5W -5,606; 10-30 19t 7W -19,958; 11-02 21t 6W -37,489; 11-03 11t 5W -9,848; 11-04 6t 1W -22,789; 11-05 12t 5W +1,693; 11-06 19t 9W +12,792

Search space: 195 raw numeric + 54 derived + 62 text indicators. Run time 396 s.

### Best rule found

### t28_all: `fut_tot_imb_with < -0.117`

Shuffle test p = 0.040 (beats luck). Search `narrow:flow_with` (6 features, 5 lines). real score 0.230.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 161 | 48% | +2.0 | +436,095 | 83 |
| discovery | kept | 80 | 60% | +4.2 | +413,946 | 32 |
| discovery | removed | 81 | 37% | -0.1 | +22,149 | 51 |
| holdout | book | 48 | 42% | -0.2 | -18,151 | 28 |
| holdout | kept | 0 |  |  | +0 | 0 |
| holdout | removed | 48 | 42% | -0.2 | -18,151 | 28 |
| all | book | 209 | 47% | +1.5 | +417,944 | 111 |
| all | kept | 80 | 60% | +4.2 | +413,946 | 32 |
| all | removed | 129 | 39% | -0.1 | +3,998 | 79 |

Features used: `fut_tot_imb_with` = e_fut_tot_imb * sgn(dir)

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `fmv300 < 16.01` | 80 / 60% / +434,190 / 32 | 81 / 51 / +1,904 | yes | 0.565 | 19 / 53% / +38,197 / 9 | 29 / -56,348 | yes |
| single_all_q9 | `fmv300 < 16.01` | 80 / 60% / +434,190 / 32 | 81 / 51 / +1,904 | yes | 0.735 | 19 / 53% / +38,197 / 9 | 29 / -56,348 | yes |
| single_text | `regime=DIRECTIONAL < 1` | 111 / 52% / +393,159 / 53 | 50 / 30 / +42,936 | yes | 0.980 | 30 / 43% / -2,717 / 17 | 18 / -15,434 | yes |
| single_all_pnl_q5 | `depth_age_fut >= 1.5` | 23 / 65% / +227,341 / 8 | 138 / 75 / +208,754 | yes | 0.085 | 4 / 75% / +20,000 / 1 | 44 / -38,152 | yes |
| pair_all_q5 | `oi_own_chg_open < 6.821e+06 AND fut_lead >= 0.024` | 77 / 66% / +574,473 / 26 | 84 / 57 / -138,378 | yes | 0.325 | 12 / 25% / -38,214 / 9 | 36 / +20,062 | NO |
| pair_all+text_q5 | `oi_own_chg_open < 6.821e+06 AND fut_lead >= 0.024` | 77 / 66% / +574,473 / 26 | 84 / 57 / -138,378 | yes | 0.375 | 12 / 25% / -38,214 / 9 | 36 / +20,062 | NO |
| triple_all_q5 | `oi_own_chg_open < 6.821e+06 AND fut_lead >= 0.024 AND ep_age_s >= 9.61` | 63 / 75% / +579,368 / 16 | 98 / 67 / -143,273 | yes | 0.195 | 11 / 18% / -49,212 / 9 | 37 / +31,060 | NO |
| pair_derived_only_q5 | `fut_tot_imb_with < -0.117 AND theta_be15_over_mv60 < 2.411` | 69 / 65% / +419,104 / 24 | 92 / 59 / +16,991 | yes | 0.420 | 0 /  / +0 / 0 | 48 / -18,151 | NO |
| narrow:theta_vs_speed | `absdelta_x_speed15_over_prem < 0.02212` | 47 / 64% / +266,276 / 17 | 114 / 66 / +169,819 | yes | 0.120 | 18 / 39% / +1,651 / 11 | 30 / -19,802 | NO |
| narrow:flow_with | `fut_tot_imb_with < -0.117` | 80 / 60% / +413,946 / 32 | 81 / 51 / +22,149 | yes | 0.040 | 0 /  / +0 / 0 | 48 / -18,151 | NO |
| narrow:trend_with | `kv_with >= -0.114` | 114 / 51% / +438,578 / 56 | 47 / 27 / -2,483 | yes | 0.655 | 36 / 39% / -34,106 / 22 | 12 / +15,954 | NO |
| narrow:time_of_day | `hour_bucket >= 2` | 99 / 53% / +339,700 / 47 | 62 / 36 / +96,395 | yes | 0.670 | 19 / 42% / +6,958 / 11 | 29 / -25,110 | yes |
| narrow:crowd | `ret_today >= 1.474` | 81 / 57% / +452,550 / 35 | 80 / 48 / -16,455 | yes | 0.240 | 19 / 32% / -38,152 / 13 | 29 / +20,000 | NO |
| narrow:room | `wall_room < 457.8` | 118 / 53% / +427,928 / 56 | 43 / 27 / +8,167 | yes | 0.695 | 38 / 45% / +12,337 / 21 | 10 / -30,488 | yes |
| narrow:vol_state | `iv_minus_rv < 5.19` | 80 / 56% / +301,174 / 35 | 81 / 48 / +134,920 | yes | 0.275 | 20 / 35% / -29,660 / 13 | 28 / +11,508 | NO |
| narrow:liquidity | `spread_pct < 0.238` | 78 / 58% / +353,688 / 33 | 83 / 50 / +82,407 | yes | 0.300 | 26 / 35% / -47,018 / 17 | 22 / +28,866 | NO |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `depth_age_fut >= 1.5 AND fut_tot_imb_with < -0.117` | 92 / 61% / +559,894 / 36 | 69 / 47 / -123,799 | yes | 0.235 | 4 / 75% / +20,000 / 1 | 44 / -38,152 | yes |
| by_direction:CE | `is_CE >= 1 AND hour_bucket >= 2` | 40 / 57% / +122,941 / 17 | 121 / 66 / +313,154 | yes | 0.525 | 12 / 67% / +55,048 / 4 | 36 / -73,200 | yes |
| by_direction:PE | `is_CE < 1 AND opt_book_imb >= 0.7575` | 45 / 62% / +366,967 / 17 | 116 / 66 / +69,128 | yes | 0.900 | 6 / 17% / -30,414 / 5 | 42 / +12,262 | NO |

### Reading

209 trades, 47% winners, holdout negative (-18,151 on 48). Mirrors t28_core_fill (same pair `oi_own_chg_open < 6.8m AND fut_lead >= 0.024`, p=0.33, holdout kept 25%). `fmv300 < 16` (forward moved less than 16 pts in 5 min) passes holdout (19 kept at 53%, removed -56,348) with p 0.57-0.74 - a plausible 'don't chase' rule but indistinguishable from luck on 161 trades. `depth_age_fut >= 1.5` p=0.085 keeps 4 of 48 on holdout. The narrow flow-family clause `fut_tot_imb_with < -0.117` reaches p=0.04 (80 kept at 60% on discovery) but, exactly as on t28_core_fill, it keeps ZERO of the 48 holdout trades - a rule that switches the book off cannot be judged and is rejected. NONE.

**Verdict: NONE**

## t28_fwd

### Record

| window | trades | winners | losers | win % | mean % | P&L Rs |
|---|---|---|---|---|---|---|
| discovery | 83 | 40 | 43 | 48% | +2.58 | +218,845 |
| holdout | 24 | 11 | 13 | 46% | -1.04 | -23,462 |
| all | 107 | 51 | 56 | 48% | +1.77 | +195,384 |

By day: 10-19 21t 8W +62,068; 10-21 6t 4W +49,085; 10-22 3t 1W -10,946; 10-23 6t 5W +92,323; 10-26 9t 5W +52,120; 10-27 20t 8W -23,735; 10-28 5t 2W -17,820; 10-29 4t 1W -19,045; 10-30 6t 5W +35,825; 11-02 3t 1W -1,030; 11-03 12t 4W -24,089; 11-04 1t 1W +20,248; 11-05 5t 2W -22,028; 11-06 6t 4W +2,408

Search space: 188 raw numeric + 50 derived + 63 text indicators. Run time 357 s.

### Best rule found

### t28_fwd: `kv_with >= 0.2044`

Shuffle test p = 0.060 (does NOT beat luck). Search `narrow:trend_with` (2 features, 5 lines). real score 0.239.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 83 | 48% | +2.6 | +218,845 | 43 |
| discovery | kept | 25 | 68% | +8.3 | +201,367 | 8 |
| discovery | removed | 58 | 40% | +0.1 | +17,478 | 35 |
| holdout | book | 24 | 46% | -1.0 | -23,462 | 13 |
| holdout | kept | 5 | 40% | -3.8 | -18,184 | 3 |
| holdout | removed | 19 | 47% | -0.3 | -5,278 | 10 |
| all | book | 107 | 48% | +1.8 | +195,384 | 56 |
| all | kept | 30 | 63% | +6.3 | +183,183 | 11 |
| all | removed | 77 | 42% | -0.0 | +12,200 | 45 |

Features used: `kv_with` = kv * sgn(dir)

### Every search, one line each

| search | rule | disc kept n / win / Rs / losers | disc removed n / losers / Rs | disc bar | p | hold kept n / win / Rs / losers | hold removed n / Rs | hold bar |
|---|---|---|---|---|---|---|---|---|
| single_raw_q5 | `ep_max_s >= 0.5035` | 23 / 78% / +235,856 / 5 | 60 / 38 / -17,010 | yes | 0.420 | 6 / 67% / -536 / 2 | 18 / -22,926 | yes |
| single_all_q9 | `ep_max_s >= 0.479` | 31 / 71% / +307,427 / 9 | 52 / 34 / -88,582 | yes | 0.510 | 8 / 75% / +4,908 / 2 | 16 / -28,369 | yes |
| single_text | `opt_opp_q=HOLDING >= 1` | 28 / 64% / +177,343 / 10 | 55 / 33 / +41,502 | yes | 0.430 | 6 / 50% / -8,278 / 3 | 18 / -15,184 | yes |
| single_all_pnl_q5 | `ep_max_s >= 0.5035` | 23 / 78% / +235,856 / 5 | 60 / 38 / -17,010 | yes | 0.185 | 6 / 67% / -536 / 2 | 18 / -22,926 | yes |
| pair_all_q5 | `opt_imb_chg30 >= -0.006 AND opt_run < -0.1848` | 39 / 74% / +258,170 / 10 | 44 / 33 / -39,325 | yes | 0.150 | 11 / 45% / -10,494 / 6 | 13 / -12,968 | NO |
| pair_all+text_q5 | `opt_imb_chg30 >= -0.006 AND opt_run < -0.1848` | 39 / 74% / +258,170 / 10 | 44 / 33 / -39,325 | yes | 0.150 | 11 / 45% / -10,494 / 6 | 13 / -12,968 | NO |
| triple_all_q5 | `opt_imb_chg30 >= -0.006 AND opt_run < -0.1848 AND swing_behind < 89.37` | 35 / 83% / +286,341 / 6 | 48 / 37 / -67,496 | yes | 0.065 | 10 / 50% / -8,385 / 5 | 14 / -15,077 | yes |
| pair_derived_only_q5 | `vix_chg_open_with >= 0.13 AND wmove60_over_mv60 >= 0.4899` | 27 / 78% / +242,326 / 6 | 56 / 37 / -23,481 | yes | 0.465 | 6 / 50% / -22,354 / 3 | 18 / -1,108 | yes |
| narrow:theta_vs_speed | `theta_be15_over_mv60 < 0.2048` | 25 / 64% / +96,587 / 9 | 58 / 34 / +122,258 | yes | 0.320 | 8 / 62% / +6,828 / 3 | 16 / -30,290 | yes |
| narrow:flow_with | `agg_net < -0.264` | 41 / 56% / +210,616 / 18 | 42 / 25 / +8,229 | yes | 0.880 | 14 / 57% / +3,894 / 6 | 10 / -27,355 | yes |
| narrow:trend_with | `kv_with >= 0.2044` | 25 / 68% / +201,367 / 8 | 58 / 35 / +17,478 | yes | 0.060 | 5 / 40% / -18,184 / 3 | 19 / -5,278 | NO |
| narrow:time_of_day | `hrs_to_expiry >= 25.2` | 42 / 57% / +180,512 / 18 | 41 / 25 / +38,334 | yes | 0.475 | 12 / 58% / +627 / 5 | 12 / -24,089 | yes |
| narrow:crowd | `n_today >= 2` | 63 / 52% / +232,567 / 30 | 20 / 13 / -13,722 | yes | 0.925 | 17 / 41% / -38,441 / 10 | 7 / +14,979 | NO |
| narrow:room | `sl_room_up_pct < 1.14` | 25 / 68% / +140,108 / 8 | 58 / 35 / +78,738 | yes | 0.240 | 5 / 40% / -14,089 / 3 | 19 / -9,373 | NO |
| narrow:vol_state | `iv_minus_rv < 18.79` | 58 / 55% / +258,001 / 26 | 25 / 17 / -39,156 | yes | 0.355 | 21 / 48% / -8,450 / 11 | 3 / -15,012 | yes |
| narrow:liquidity | `spread_pct < 0.256` | 56 / 57% / +230,964 / 24 | 27 / 19 / -12,119 | yes | 0.225 | 14 / 50% / +3,045 / 7 | 10 / -26,507 | yes |
| OR_of_two:narrow_union [kept if EITHER clause holds] | `kv_with >= 0.2044 AND sl_room_up_pct < 0.37` | 32 / 75% / +286,322 / 8 | 51 / 35 / -67,476 | yes | 0.120 | 7 / 43% / -15,681 / 4 | 17 / -7,780 | NO |
| by_direction:CE | `is_CE >= 1 AND swing_ahead < 43.66` | 27 / 52% / +97,984 / 13 | 56 / 30 / +120,861 | yes | 0.390 | 10 / 30% / -9,474 / 7 | 14 / -13,988 | NO |
| by_direction:PE | `is_CE < 1 AND spread_pct < 0.24` | 21 / 76% / +166,007 / 5 | 62 / 38 / +52,838 | yes | 0.365 | 7 / 57% / +4,982 / 3 | 17 / -28,444 | yes |

### Reading

107 trades, 48% winners, the worst holdout (24 trades, 46%, -23,462). `ep_max_s >= 0.5` keeps 23 of 83 at 78% on discovery and on holdout 6 of 24 at 67% but -536 rupees; p 0.19-0.42. The greedy triple `opt_imb_chg30 >= -0.006 AND opt_run < -0.18 AND swing_behind < 89` reaches p=0.065 with 35 kept at 83% on discovery, and on holdout 10 kept at 50% (book 46%) but -8,385 rupees - it passes the formal holdout gate on win rate only, and misses the shuffle bar. The narrow trend clause `kv_with >= 0.2044` (Kalman velocity in the trade's direction) has p=0.06 and then loses on holdout (5 kept at 40%, -18,184). NONE.

**Verdict: NONE**

## Summary

- t28_dur20: NONE | best `is_CE < 1 AND depth_age_fut >= 0.65` | disc kept 72% win, 7 losers of 25 | hold kept 33% win, 4 losers of 6 (book 50%) | p=0.12
- t28_core: NONE | best `kv_with >= -0.0351` | disc kept 58% win, 18 losers of 43 | hold kept 50% win, 7 losers of 14 (book 56%) | p=0.21
- t28_core_fill: NONE | best `fut_tot_imb_with < -0.1175` | disc kept 60% win, 32 losers of 80 | hold kept  win, 0 losers of 0 (book 42%) | p=0.03
- t28_fill: NONE | best `is_CE >= 1 AND prev_win_today < 0.5` | disc kept 64% win, 14 losers of 39 | hold kept 64% win, 5 losers of 14 (book 45%) | p=0.08
- t28_all: NONE | best `fut_tot_imb_with < -0.117` | disc kept 60% win, 32 losers of 80 | hold kept  win, 0 losers of 0 (book 42%) | p=0.04
- t28_fwd: NONE | best `kv_with >= 0.2044` | disc kept 68% win, 8 losers of 25 | hold kept 40% win, 3 losers of 5 (book 46%) | p=0.06

Across six books, 100+ searches, every mathematics the brief lists (ratios, differences, products, direction interactions, within-day z-scores, hour buckets, 2- and 3-clause ANDs, OR-of-two, either/or by direction, text indicators, two objectives): not one rule passes all three gates. Two reach p <= 0.05 (t28_core_fill `fut_tot_imb_with < -0.1175` p=0.03 keeps 0 holdout trades; `depth_age_fut >= 1.5` p=0.05 keeps 4) and neither survives holdout in a usable form. The pattern is the one the brief warned of: on 62-161 discovery trades a search over ~250 fields finds an 80-95% kept side every time, and random labels do the same. The book-level fact that survives is simpler: all six t28 books are ~50% strike-rate books whose rupees come from a handful of large winners, and their last four days are flat to negative. Nothing here should be registered. The one idea worth carrying forward is 'CE only when the book's earlier trades today were losing' on t28_fill (p=0.08, holdout 64% vs 45%) - to be re-tested, not registered.