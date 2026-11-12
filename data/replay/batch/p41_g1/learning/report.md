# ApexOptions — learning report (2026-10-21)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `conductor`
0 trades since 2026-11-09, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #6 since registration (2026-10-17); evening looks: 0 for this champion, 14 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 0).
- SPRT on per-trade 100·ln(1+r): Σ +0.0 (mean +0.00/trade) vs GO 998.1 / KILL -560.9 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.00** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (0)
- [ ] ≥ 2 expiry days (0)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [ ] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0005 each, 101 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 0 | +0.00 | 0.00 | inf | no | 0 |
| straddle_spike | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_pb45 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual_rg | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual_lvl | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_absorb | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_release | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_ctl_price | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_ctl_flow | 0 | +0.00 | 0.00 | inf | no | 0 |
| n02_relax | 0 | +0.00 | 0.00 | inf | no | 0 |
| n02_ctl_mr | 0 | +0.00 | 0.00 | inf | no | 0 |
| n06_lead | 0 | +0.00 | 0.00 | inf | no | 0 |
| n06_ctl_breadth | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_ctl_price_ind | 0 | +0.00 | 0.00 | inf | no | 0 |
| s01_transmit | 0 | +0.00 | 0.00 | inf | no | 0 |
| s01_ctl_cash | 0 | +0.00 | 0.00 | inf | no | 0 |
| s01_ctl_sfut | 0 | +0.00 | 0.00 | inf | no | 0 |
| s03_recruit | 0 | +0.00 | 0.00 | inf | no | 0 |
| p02_clock | 0 | +0.00 | 0.00 | inf | no | 0 |
| p02_top1 | 0 | +0.00 | 0.00 | inf | no | 0 |
| p02_ctl_mom | 0 | +0.00 | 0.00 | inf | no | 0 |
| p05_adaptive | 0 | +0.00 | 0.00 | inf | no | 0 |
| apex_edge | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_bracket_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_breakout | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_re | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_d46 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_gap | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_dur20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_ts | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_fill | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_core | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_core_fill | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_all | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_d46_fill | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_gap_ts | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_ivfall | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_bidpile | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_st20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_nohigh | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_req | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_cheap | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_cheapK | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_fwd | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_mh15 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_tt8 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_8x | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9t | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9v | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9e | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9h | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9s | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9y | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_pb45_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.4_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.4_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x_r004 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r005 | 0 | +0.00 | 0.00 | inf | no | 0 |
| fx_c20_9y | 0 | +0.00 | 0.00 | inf | no | 0 |
| fr_c20_9y | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +27.37 | 0.00 | inf | too few days |
| random_entry | 1 | -0.29 | 0.00 | inf | too few days |
| premium_momentum | 1 | +13.41 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 72 | 0 | +1.51 | +1.51 | +0.00 | 0% | no | advisory |
| room | 72 | 4 | +1.51 | +1.24 | -0.27 | 5% | no | advisory |
| coherence | 72 | 52 | +1.51 | -1.59 | -3.10 | 79% | no | advisory |
| force | 72 | 2 | +1.51 | +1.58 | +0.07 | 5% | no | advisory |
| episode | 72 | 3 | +1.51 | +1.13 | -0.38 | 11% | no | advisory |
| book | 72 | 26 | +1.51 | +0.77 | -0.75 | 37% | no | advisory |
| premium | 72 | 9 | +1.51 | +2.52 | +1.00 | 0% | yes | → CANDIDATE (gated book from next session) |
| quiet | 72 | 0 | +1.51 | +1.51 | +0.00 | 0% | no | advisory |
| bank | 72 | 12 | +1.51 | -1.67 | -3.19 | 26% | no | advisory |
| event | 72 | 0 | +1.51 | +1.51 | +0.00 | 0% | no | advisory |
| gamma_leg | 72 | 1 | +1.51 | +1.77 | +0.26 | 0% | no | advisory |
| gex_room | 72 | 14 | +1.51 | +2.83 | +1.32 | 5% | yes | → CANDIDATE (gated book from next session) |
| regime | 72 | 39 | +1.51 | +0.78 | -0.73 | 47% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| RAW | BREAKOUT | 1 | -20.21 | 0% |
| RAW | COMPRESSION | 12 | +5.97 | 42% |
| RAW | DIRECTIONAL | 26 | +3.04 | 50% |
| RAW | EXHAUSTION | 2 | -5.07 | 0% |
| RAW | RANGE | 14 | +4.11 | 50% |
| RAW | UNCERTAIN | 11 | -5.90 | 36% |
| RAW | WARMING | 6 | -0.73 | 33% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:15, flatten 15:25. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 2 | +3.25 | 100% | +0.4 / +6.1 | 0 | CAS-ENTRY 2 |
| futures_only | 1 | +2.07 | 100% | +2.1 / +2.1 | 0 | CAS-ENTRY 1 |
| random_entry | 3 | +0.86 | 67% | -3.1 / +4.2 | 1 | CAS-ENTRY 3 |
| spot_dc12_t12 | 1 | +0.49 | 100% | +0.5 / +0.5 | 0 | CAS-ENTRY 1 |
| spot_dc12_t12_1130 | 1 | +0.49 | 100% | +0.5 / +0.5 | 0 | CAS-ENTRY 1 |
| spot_dc12_t12_first | 3 | -0.76 | 33% | -1.9 / +0.2 | 0 | CAS-ENTRY 3 |
| spot_dc12_t12_nolock | 1 | +0.49 | 100% | +0.5 / +0.5 | 0 | CAS-ENTRY 1 |
| spot_ft_prem10 | 3 | -1.38 | 33% | -4.2 / +0.0 | 1 | CAS-ENTRY 3 |

## Quarantined evidence (D-101) — kept on file, NOT counted anywhere above

- 2026-10-19: defect window(s) whole session (declared) — trades entered inside are excluded for every book.

| day | book | time in-out | contract | entry → exit | recorded ret % | why |
|---|---|---|---|---|---|---|
| 2026-10-19 | RAW | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | RAW | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | RAW | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | RAW | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | RAW | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | RAW | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | RAW | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | RAW | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | RAW | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | RAW | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | RAW | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | RAW | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | RAW | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | RAW | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | RAW | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | RAW | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | apex_edge | 09:27:47-09:28:51 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 168.3 | +23.98 | whole session declared defective |
| 2026-10-19 | apex_edge | 09:29:30-09:31:15 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 107.8 | -13.41 | whole session declared defective |
| 2026-10-19 | apex_edge | 09:36:30-09:37:40 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 183.8 | +18.66 | whole session declared defective |
| 2026-10-19 | c20_8x | 09:25:34-09:31:16 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 176.75 | +63.96 | whole session declared defective |
| 2026-10-19 | c20_8x | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_8x | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_8x | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_8x | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_8x | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_8x | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_8x | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_8x | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_8x | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_8x | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_8x | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_8x | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_8x | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_8x | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:25:34-09:25:57 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 121.0 | +12.24 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:27:05-09:27:19 | NIFTY|OPT|2026-10-19|23050|PE | 105.85 → 118.1 | +11.57 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:28:51-09:29:05 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 134.85 | +2.35 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:35:16-09:36:00 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 151.9 | +1.78 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:37:07-09:37:44 | NIFTY|OPT|2026-10-19|23050|CE | 132.25 → 142.25 | +7.56 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:55:07-09:57:32 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 125.4 | +25.71 | whole session declared defective |
| 2026-10-19 | c20_9e | 09:58:48-09:59:25 | NIFTY|OPT|2026-10-19|23100|PE | 102.55 → 109.9 | +7.17 | whole session declared defective |
| 2026-10-19 | c20_9e | 10:19:48-10:23:18 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 115.45 | +3.40 | whole session declared defective |
| 2026-10-19 | c20_9e | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9e | 10:34:15-10:37:00 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 114.9 | +6.93 | whole session declared defective |
| 2026-10-19 | c20_9e | 10:40:19-10:42:09 | NIFTY|OPT|2026-10-19|23100|PE | 95.7 → 113.85 | +18.97 | whole session declared defective |
| 2026-10-19 | c20_9e | 11:34:58-11:35:48 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 78.75 | +2.07 | whole session declared defective |
| 2026-10-19 | c20_9e | 11:38:29-11:40:01 | NIFTY|OPT|2026-10-19|23050|PE | 93.5 → 102.25 | +9.36 | whole session declared defective |
| 2026-10-19 | c20_9e | 11:51:14-11:53:01 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 94.2 | -4.66 | whole session declared defective |
| 2026-10-19 | c20_9e | 11:56:44-11:58:54 | NIFTY|OPT|2026-10-19|23050|PE | 105.4 → 102.5 | -2.75 | whole session declared defective |
| 2026-10-19 | c20_9e | 12:04:19-12:05:55 | NIFTY|OPT|2026-10-19|23000|PE | 94.7 → 85.5 | -9.71 | whole session declared defective |
| 2026-10-19 | c20_9e | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9e | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9e | 12:50:10-12:56:00 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 75.65 | +2.79 | whole session declared defective |
| 2026-10-19 | c20_9e | 13:03:21-13:04:29 | NIFTY|OPT|2026-10-19|22900|CE | 65.1 → 71.8 | +10.29 | whole session declared defective |
| 2026-10-19 | c20_9e | 13:10:36-13:20:14 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 88.35 | +21.36 | whole session declared defective |
| 2026-10-19 | c20_9e | 13:23:29-13:25:18 | NIFTY|OPT|2026-10-19|22900|PE | 67.45 → 68.4 | +1.41 | whole session declared defective |
| 2026-10-19 | c20_9e | 13:44:35-13:47:54 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 67.55 | -3.43 | whole session declared defective |
| 2026-10-19 | c20_9e | 14:02:58-14:03:39 | NIFTY|OPT|2026-10-19|22850|CE | 58.95 → 55.65 | -5.60 | whole session declared defective |
| 2026-10-19 | c20_9e | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:35:16-09:39:00 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 164.75 | +10.38 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:55:07-09:57:55 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 117.4 | +17.69 | whole session declared defective |
| 2026-10-19 | c20_9h | 09:58:55-10:00:49 | NIFTY|OPT|2026-10-19|23100|PE | 106.65 → 95.45 | -10.50 | whole session declared defective |
| 2026-10-19 | c20_9h | 10:19:48-10:24:19 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 121.85 | +9.14 | whole session declared defective |
| 2026-10-19 | c20_9h | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9h | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9h | 11:34:58-11:41:04 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 94.35 | +22.29 | whole session declared defective |
| 2026-10-19 | c20_9h | 11:51:14-12:05:58 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 120.7 | +22.17 | whole session declared defective |
| 2026-10-19 | c20_9h | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9h | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9h | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9h | 13:10:36-13:20:59 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 83.1 | +14.15 | whole session declared defective |
| 2026-10-19 | c20_9h | 13:23:29-13:30:19 | NIFTY|OPT|2026-10-19|22900|PE | 67.45 → 72.1 | +6.89 | whole session declared defective |
| 2026-10-19 | c20_9h | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9h | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9s | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9s | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9s | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9s | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9s | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9s | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9s | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9s | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9s | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9s | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9s | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9s | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9s | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9s | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9s | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9s | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:35:16-09:36:10 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 160.7 | +7.67 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:37:13-09:39:06 | NIFTY|OPT|2026-10-19|23100|CE | 99.45 → 92.8 | -6.69 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9t | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9t | 10:19:48-10:23:16 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 116.65 | +4.48 | whole session declared defective |
| 2026-10-19 | c20_9t | 10:30:09-10:31:43 | NIFTY|OPT|2026-10-19|23050|CE | 105.15 → 90.15 | -14.27 | whole session declared defective |
| 2026-10-19 | c20_9t | 10:34:15-10:37:00 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 114.9 | +6.93 | whole session declared defective |
| 2026-10-19 | c20_9t | 10:40:22-10:42:34 | NIFTY|OPT|2026-10-19|23100|PE | 96.6 → 98.0 | +1.45 | whole session declared defective |
| 2026-10-19 | c20_9t | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9t | 11:51:14-11:58:54 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 102.5 | +3.75 | whole session declared defective |
| 2026-10-19 | c20_9t | 12:04:19-12:05:58 | NIFTY|OPT|2026-10-19|23000|PE | 94.7 → 84.3 | -10.98 | whole session declared defective |
| 2026-10-19 | c20_9t | 12:26:31-12:40:55 | NIFTY|OPT|2026-10-19|22900|CE | 74.55 → 63.4 | -14.96 | whole session declared defective |
| 2026-10-19 | c20_9t | 13:03:21-13:03:43 | NIFTY|OPT|2026-10-19|22900|CE | 65.1 → 67.55 | +3.76 | whole session declared defective |
| 2026-10-19 | c20_9t | 13:10:36-13:20:52 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 86.4 | +18.68 | whole session declared defective |
| 2026-10-19 | c20_9t | 13:23:29-13:28:10 | NIFTY|OPT|2026-10-19|22900|PE | 67.45 → 72.05 | +6.82 | whole session declared defective |
| 2026-10-19 | c20_9t | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9t | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9v | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9v | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9v | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9v | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9v | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9v | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9v | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9v | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9v | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9v | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9v | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9v | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9v | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9v | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9v | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9v | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9x | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9x | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9x | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9x | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9x | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9x | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9x | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9x | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9x | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9x | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9x | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9x | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9x | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9x | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9x | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9x | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9x_r002 | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 09:28:51-09:31:16 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 107.25 | -18.60 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | c20_9x_r004 | 14:33:20-14:34:11 | NIFTY|OPT|2026-10-19|22850|CE | 41.6 → 34.9 | -16.11 | whole session declared defective |
| 2026-10-19 | c20_9y | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | c20_9y | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | c20_9y | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | c20_9y | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | c20_9y | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | c20_9y | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | c20_9y | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | c20_9y | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | c20_9y | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | c20_9y | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | c20_9y | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | c20_9y | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | c20_9y | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | c20_9y | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 09:27:47-09:28:51 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 168.3 | +23.98 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 09:29:30-09:31:15 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 107.8 | -13.41 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 09:36:30-09:37:40 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 183.8 | +18.66 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 10:38:01-10:39:30 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 129.35 | +20.72 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 10:42:33-10:56:11 | NIFTY|OPT|2026-10-19|23150|PE | 133.2 → 116.8 | -12.31 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 11:58:45-12:04:15 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 132.9 | +21.93 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 12:17:12-12:27:11 | NIFTY|OPT|2026-10-19|23000|PE | 100.3 → 88.45 | -11.81 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 12:28:20-12:40:53 | NIFTY|OPT|2026-10-19|22850|CE | 106.3 → 96.2 | -9.50 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 12:41:57-13:03:17 | NIFTY|OPT|2026-10-19|23000|PE | 102.25 → 90.55 | -11.44 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 13:04:49-13:06:03 | NIFTY|OPT|2026-10-19|22850|CE | 99.7 → 88.2 | -11.54 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 13:24:58-13:25:54 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 64.6 | -10.90 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.7 | -10.65 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 13:49:03-14:02:19 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 88.05 | -10.74 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 14:04:21-14:05:39 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 106.15 | +19.94 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 14:24:45-14:31:19 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 60.05 | -11.43 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 14:43:21-14:44:32 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 93.1 | +22.98 | whole session declared defective |
| 2026-10-19 | edge_bracket_only | 14:44:34-14:45:07 | NIFTY|OPT|2026-10-19|22850|CE | 54.9 → 51.35 | -6.47 | whole session declared defective |
| 2026-10-19 | edge_breakout | 09:27:47-09:28:51 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 168.3 | +23.98 | whole session declared defective |
| 2026-10-19 | edge_breakout | 09:29:30-09:31:15 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 107.8 | -13.41 | whole session declared defective |
| 2026-10-19 | edge_breakout | 09:36:30-09:37:40 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 183.8 | +18.66 | whole session declared defective |
| 2026-10-19 | edge_gate_only | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | edge_gate_only | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | edge_gate_only | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | edge_gate_trail | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | edge_gate_trail | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | edge_gate_trail | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:28:53-09:29:11 | NIFTY|OPT|2026-10-19|23050|PE | 134.4 → 141.4 | +5.21 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:30:27-09:31:15 | NIFTY|OPT|2026-10-19|22850|CE | 159.0 → 175.45 | +10.35 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:32:15-09:32:27 | NIFTY|OPT|2026-10-19|22950|CE | 125.65 → 134.0 | +6.64 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:33:31-09:33:48 | NIFTY|OPT|2026-10-19|23000|CE | 135.0 → 145.55 | +7.82 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:35:13-09:35:36 | NIFTY|OPT|2026-10-19|23000|CE | 140.7 → 146.8 | +4.33 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:36:37-09:37:01 | NIFTY|OPT|2026-10-19|23200|PE | 128.0 → 114.6 | -10.47 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:39:02-09:39:12 | NIFTY|OPT|2026-10-19|23250|PE | 145.75 → 156.8 | +7.58 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:40:12-09:41:05 | NIFTY|OPT|2026-10-19|23200|PE | 127.35 → 113.25 | -11.07 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:42:35-09:44:02 | NIFTY|OPT|2026-10-19|23200|PE | 122.2 → 110.9 | -9.25 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:46:21-09:47:24 | NIFTY|OPT|2026-10-19|23200|PE | 111.85 → 117.75 | +5.28 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:49:06-09:51:20 | NIFTY|OPT|2026-10-19|23050|CE | 128.6 → 112.75 | -12.32 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:52:26-09:52:44 | NIFTY|OPT|2026-10-19|23200|PE | 118.9 → 112.5 | -5.38 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:54:42-09:55:03 | NIFTY|OPT|2026-10-19|23000|CE | 139.5 → 129.65 | -7.06 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:56:03-09:57:06 | NIFTY|OPT|2026-10-19|23150|PE | 112.5 → 127.0 | +12.89 | whole session declared defective |
| 2026-10-19 | fade_switch | 09:58:48-09:59:12 | NIFTY|OPT|2026-10-19|23150|PE | 137.8 → 152.0 | +10.30 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:00:44-10:01:01 | NIFTY|OPT|2026-10-19|22950|CE | 142.35 → 152.8 | +7.34 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:04:02-10:05:15 | NIFTY|OPT|2026-10-19|23150|PE | 116.15 → 130.7 | +12.53 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:08:04-10:09:51 | NIFTY|OPT|2026-10-19|22950|CE | 136.95 → 148.0 | +8.07 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:11:17-10:13:07 | NIFTY|OPT|2026-10-19|23000|CE | 110.9 → 98.95 | -10.78 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:14:57-10:15:45 | NIFTY|OPT|2026-10-19|22950|CE | 132.25 → 141.2 | +6.77 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:17:01-10:17:53 | NIFTY|OPT|2026-10-19|22950|CE | 132.45 → 143.0 | +7.96 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:19:44-10:22:38 | NIFTY|OPT|2026-10-19|23150|PE | 106.8 → 96.3 | -9.83 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:23:39-10:25:08 | NIFTY|OPT|2026-10-19|23200|PE | 127.25 → 140.5 | +10.41 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:29:48-10:30:05 | NIFTY|OPT|2026-10-19|23200|PE | 125.9 → 111.35 | -11.56 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:31:39-10:32:42 | NIFTY|OPT|2026-10-19|23200|PE | 128.8 → 139.45 | +8.27 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:39:06-10:40:28 | NIFTY|OPT|2026-10-19|23150|PE | 123.35 → 138.65 | +12.40 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:42:15-10:42:31 | NIFTY|OPT|2026-10-19|22950|CE | 115.15 → 123.75 | +7.47 | whole session declared defective |
| 2026-10-19 | fade_switch | 10:46:23-10:48:56 | NIFTY|OPT|2026-10-19|23100|PE | 103.6 → 111.2 | +7.34 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:00:23-11:03:24 | NIFTY|OPT|2026-10-19|22950|CE | 127.0 → 123.5 | -2.76 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:06:24-11:07:41 | NIFTY|OPT|2026-10-19|22950|CE | 125.7 → 135.85 | +8.07 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:10:21-11:12:28 | NIFTY|OPT|2026-10-19|23150|PE | 100.0 → 110.05 | +10.05 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:16:21-11:19:21 | NIFTY|OPT|2026-10-19|23150|PE | 105.1 → 97.4 | -7.33 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:23:19-11:24:57 | NIFTY|OPT|2026-10-19|23150|PE | 104.6 → 116.5 | +11.38 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:35:09-11:38:10 | NIFTY|OPT|2026-10-19|22900|CE | 127.5 → 124.5 | -2.35 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:39:15-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 107.6 → 89.75 | -16.59 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:42:42-11:44:20 | NIFTY|OPT|2026-10-19|23050|PE | 96.65 → 86.75 | -10.24 | whole session declared defective |
| 2026-10-19 | fade_switch | 11:55:16-11:58:19 | NIFTY|OPT|2026-10-19|22900|CE | 104.4 → 97.6 | -6.51 | whole session declared defective |
| 2026-10-19 | fade_switch | 12:04:15-12:06:19 | NIFTY|OPT|2026-10-19|22900|CE | 78.55 → 85.1 | +8.34 | whole session declared defective |
| 2026-10-19 | fade_switch | 12:08:04-12:09:18 | NIFTY|OPT|2026-10-19|22900|CE | 90.65 → 78.45 | -13.46 | whole session declared defective |
| 2026-10-19 | fade_switch | 12:28:32-12:31:32 | NIFTY|OPT|2026-10-19|22850|CE | 104.8 → 109.8 | +4.77 | whole session declared defective |
| 2026-10-19 | fade_switch | 12:45:39-12:47:41 | NIFTY|OPT|2026-10-19|23000|PE | 99.25 → 109.55 | +10.38 | whole session declared defective |
| 2026-10-19 | fade_switch | 12:58:04-13:01:05 | NIFTY|OPT|2026-10-19|23000|PE | 109.7 → 107.8 | -1.73 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:03:29-13:05:32 | NIFTY|OPT|2026-10-19|23000|PE | 85.75 → 98.3 | +14.64 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:18:04-13:19:52 | NIFTY|OPT|2026-10-19|22800|CE | 102.75 → 95.45 | -7.11 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:22:30-13:22:58 | NIFTY|OPT|2026-10-19|22800|CE | 95.45 → 88.25 | -7.54 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:24:25-13:24:57 | NIFTY|OPT|2026-10-19|22950|PE | 99.95 → 110.6 | +10.65 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:27:20-13:30:20 | NIFTY|OPT|2026-10-19|22900|PE | 72.2 → 72.55 | +0.48 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:36:38-13:39:38 | NIFTY|OPT|2026-10-19|22950|PE | 95.75 → 92.35 | -3.55 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:41:33-13:43:58 | NIFTY|OPT|2026-10-19|22950|PE | 84.0 → 99.85 | +18.87 | whole session declared defective |
| 2026-10-19 | fade_switch | 13:49:03-13:52:03 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 100.5 | +1.88 | whole session declared defective |
| 2026-10-19 | fade_switch | 14:02:24-14:03:00 | NIFTY|OPT|2026-10-19|22950|PE | 84.05 → 83.0 | -1.25 | whole session declared defective |
| 2026-10-19 | fade_switch | 14:09:47-14:10:32 | NIFTY|OPT|2026-10-19|22800|CE | 80.5 → 90.3 | +12.17 | whole session declared defective |
| 2026-10-19 | fade_switch | 14:17:17-14:20:17 | NIFTY|OPT|2026-10-19|22800|CE | 70.95 → 67.5 | -4.86 | whole session declared defective |
| 2026-10-19 | fade_switch | 14:24:05-14:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 64.75 → 61.25 | -5.41 | whole session declared defective |
| 2026-10-19 | fade_switch | 14:31:22-14:34:22 | NIFTY|OPT|2026-10-19|22900|PE | 58.2 → 60.85 | +4.55 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:28:53-09:29:11 | NIFTY|OPT|2026-10-19|23050|PE | 134.4 → 141.4 | +5.21 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:30:27-09:31:15 | NIFTY|OPT|2026-10-19|22850|CE | 159.0 → 175.45 | +10.35 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:32:15-09:32:27 | NIFTY|OPT|2026-10-19|22950|CE | 125.65 → 134.0 | +6.64 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:33:31-09:33:48 | NIFTY|OPT|2026-10-19|23000|CE | 135.0 → 145.55 | +7.82 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:35:13-09:35:36 | NIFTY|OPT|2026-10-19|23000|CE | 140.7 → 146.8 | +4.33 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:36:37-09:37:01 | NIFTY|OPT|2026-10-19|23200|PE | 128.0 → 114.6 | -10.47 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:39:02-09:39:12 | NIFTY|OPT|2026-10-19|23250|PE | 145.75 → 156.8 | +7.58 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:40:12-09:41:05 | NIFTY|OPT|2026-10-19|23200|PE | 127.35 → 113.25 | -11.07 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:42:35-09:44:02 | NIFTY|OPT|2026-10-19|23200|PE | 122.2 → 110.9 | -9.25 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:46:21-09:47:24 | NIFTY|OPT|2026-10-19|23200|PE | 111.85 → 117.75 | +5.28 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:49:06-09:51:20 | NIFTY|OPT|2026-10-19|23050|CE | 128.6 → 112.75 | -12.32 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:52:26-09:52:44 | NIFTY|OPT|2026-10-19|23200|PE | 118.9 → 112.5 | -5.38 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:54:42-09:55:03 | NIFTY|OPT|2026-10-19|23000|CE | 139.5 → 129.65 | -7.06 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:56:03-09:57:06 | NIFTY|OPT|2026-10-19|23150|PE | 112.5 → 127.0 | +12.89 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 09:58:48-09:59:12 | NIFTY|OPT|2026-10-19|23150|PE | 137.8 → 152.0 | +10.30 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:00:44-10:01:01 | NIFTY|OPT|2026-10-19|22950|CE | 142.35 → 152.8 | +7.34 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:04:02-10:05:15 | NIFTY|OPT|2026-10-19|23150|PE | 116.15 → 130.7 | +12.53 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:08:04-10:09:51 | NIFTY|OPT|2026-10-19|22950|CE | 136.95 → 148.0 | +8.07 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:11:17-10:13:07 | NIFTY|OPT|2026-10-19|23000|CE | 110.9 → 98.95 | -10.78 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:14:57-10:15:45 | NIFTY|OPT|2026-10-19|22950|CE | 132.25 → 141.2 | +6.77 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:17:01-10:17:53 | NIFTY|OPT|2026-10-19|22950|CE | 132.45 → 143.0 | +7.96 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:19:44-10:22:38 | NIFTY|OPT|2026-10-19|23150|PE | 106.8 → 96.3 | -9.83 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:23:39-10:25:08 | NIFTY|OPT|2026-10-19|23200|PE | 127.25 → 140.5 | +10.41 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:29:48-10:30:05 | NIFTY|OPT|2026-10-19|23200|PE | 125.9 → 111.35 | -11.56 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:31:39-10:32:42 | NIFTY|OPT|2026-10-19|23200|PE | 128.8 → 139.45 | +8.27 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:39:06-10:40:28 | NIFTY|OPT|2026-10-19|23150|PE | 123.35 → 138.65 | +12.40 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:42:15-10:42:31 | NIFTY|OPT|2026-10-19|22950|CE | 115.15 → 123.75 | +7.47 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 10:46:23-10:48:56 | NIFTY|OPT|2026-10-19|23100|PE | 103.6 → 111.2 | +7.34 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:00:23-11:03:24 | NIFTY|OPT|2026-10-19|22950|CE | 127.0 → 123.5 | -2.76 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:06:24-11:07:41 | NIFTY|OPT|2026-10-19|22950|CE | 125.7 → 135.85 | +8.07 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:10:21-11:12:28 | NIFTY|OPT|2026-10-19|23150|PE | 100.0 → 110.05 | +10.05 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:16:21-11:19:21 | NIFTY|OPT|2026-10-19|23150|PE | 105.1 → 97.4 | -7.33 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:23:19-11:24:57 | NIFTY|OPT|2026-10-19|23150|PE | 104.6 → 116.5 | +11.38 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:35:09-11:38:10 | NIFTY|OPT|2026-10-19|22900|CE | 127.5 → 124.5 | -2.35 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:39:15-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 107.6 → 89.75 | -16.59 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:42:42-11:44:20 | NIFTY|OPT|2026-10-19|23050|PE | 96.65 → 86.75 | -10.24 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 11:55:16-11:58:19 | NIFTY|OPT|2026-10-19|22900|CE | 104.4 → 97.6 | -6.51 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 12:04:15-12:06:19 | NIFTY|OPT|2026-10-19|22900|CE | 78.55 → 85.1 | +8.34 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 12:08:04-12:09:18 | NIFTY|OPT|2026-10-19|22900|CE | 90.65 → 78.45 | -13.46 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 12:28:32-12:31:32 | NIFTY|OPT|2026-10-19|22850|CE | 104.8 → 109.8 | +4.77 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 12:45:39-12:47:41 | NIFTY|OPT|2026-10-19|23000|PE | 99.25 → 109.55 | +10.38 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 12:58:04-13:01:05 | NIFTY|OPT|2026-10-19|23000|PE | 109.7 → 107.8 | -1.73 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:03:29-13:05:32 | NIFTY|OPT|2026-10-19|23000|PE | 85.75 → 98.3 | +14.64 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:18:04-13:19:52 | NIFTY|OPT|2026-10-19|22800|CE | 102.75 → 95.45 | -7.11 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:22:30-13:22:58 | NIFTY|OPT|2026-10-19|22800|CE | 95.45 → 88.25 | -7.54 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:24:25-13:24:57 | NIFTY|OPT|2026-10-19|22950|PE | 99.95 → 110.6 | +10.65 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:27:20-13:30:20 | NIFTY|OPT|2026-10-19|22900|PE | 72.2 → 72.55 | +0.48 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:36:38-13:39:38 | NIFTY|OPT|2026-10-19|22950|PE | 95.75 → 92.35 | -3.55 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:41:33-13:43:58 | NIFTY|OPT|2026-10-19|22950|PE | 84.0 → 99.85 | +18.87 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 13:49:03-13:52:03 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 100.5 | +1.88 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 14:02:24-14:03:00 | NIFTY|OPT|2026-10-19|22950|PE | 84.05 → 83.0 | -1.25 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 14:09:47-14:10:32 | NIFTY|OPT|2026-10-19|22800|CE | 80.5 → 90.3 | +12.17 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 14:17:17-14:20:17 | NIFTY|OPT|2026-10-19|22800|CE | 70.95 → 67.5 | -4.86 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 14:24:05-14:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 64.75 → 61.25 | -5.41 | whole session declared defective |
| 2026-10-19 | fade_switch_r002 | 14:31:22-14:34:22 | NIFTY|OPT|2026-10-19|22900|PE | 58.2 → 60.85 | +4.55 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 09:25:34-09:26:35 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 160.45 | +48.84 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 12:50:10-13:03:07 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 62.1 | -15.62 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 13:10:36-13:25:36 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 109.55 | +50.48 | whole session declared defective |
| 2026-10-19 | fr_c20_9y | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | futures_only | 09:25:47-09:26:36 | NIFTY|OPT|2026-10-19|23150|PE | 119.85 → 165.6 | +38.17 | whole session declared defective |
| 2026-10-19 | futures_only | 09:27:49-09:28:13 | NIFTY|OPT|2026-10-19|22900|CE | 140.65 → 130.6 | -7.14 | whole session declared defective |
| 2026-10-19 | futures_only | 09:31:16-09:31:53 | NIFTY|OPT|2026-10-19|22900|CE | 134.75 → 129.8 | -3.67 | whole session declared defective |
| 2026-10-19 | futures_only | 09:39:14-09:41:12 | NIFTY|OPT|2026-10-19|23200|PE | 121.95 → 104.9 | -13.98 | whole session declared defective |
| 2026-10-19 | futures_only | 09:44:09-09:47:14 | NIFTY|OPT|2026-10-19|23050|CE | 133.55 → 114.25 | -14.45 | whole session declared defective |
| 2026-10-19 | futures_only | 09:52:11-09:52:28 | NIFTY|OPT|2026-10-19|23200|PE | 127.4 → 115.15 | -9.62 | whole session declared defective |
| 2026-10-19 | futures_only | 10:00:44-10:01:39 | NIFTY|OPT|2026-10-19|22950|CE | 142.35 → 143.55 | +0.84 | whole session declared defective |
| 2026-10-19 | futures_only | 10:08:07-10:10:28 | NIFTY|OPT|2026-10-19|22950|CE | 138.45 → 137.5 | -0.69 | whole session declared defective |
| 2026-10-19 | futures_only | 10:30:03-10:30:36 | NIFTY|OPT|2026-10-19|23000|CE | 138.9 → 132.75 | -4.43 | whole session declared defective |
| 2026-10-19 | futures_only | 10:31:39-10:38:20 | NIFTY|OPT|2026-10-19|23200|PE | 128.8 → 143.8 | +11.65 | whole session declared defective |
| 2026-10-19 | futures_only | 10:42:18-10:43:13 | NIFTY|OPT|2026-10-19|22950|CE | 116.9 → 116.0 | -0.77 | whole session declared defective |
| 2026-10-19 | futures_only | 11:16:27-11:22:11 | NIFTY|OPT|2026-10-19|23000|CE | 102.6 → 94.8 | -7.60 | whole session declared defective |
| 2026-10-19 | futures_only | 11:35:18-11:35:57 | NIFTY|OPT|2026-10-19|23100|PE | 119.8 → 106.75 | -10.89 | whole session declared defective |
| 2026-10-19 | futures_only | 11:41:18-11:46:34 | NIFTY|OPT|2026-10-19|22900|CE | 117.05 → 110.4 | -5.68 | whole session declared defective |
| 2026-10-19 | futures_only | 12:04:15-12:06:05 | NIFTY|OPT|2026-10-19|23050|PE | 132.9 → 119.05 | -10.42 | whole session declared defective |
| 2026-10-19 | futures_only | 13:41:33-13:43:58 | NIFTY|OPT|2026-10-19|22800|CE | 100.4 → 84.4 | -15.94 | whole session declared defective |
| 2026-10-19 | futures_only | 13:49:11-14:07:25 | NIFTY|OPT|2026-10-19|22800|CE | 79.95 → 92.3 | +15.45 | whole session declared defective |
| 2026-10-19 | futures_only | 14:09:51-14:10:33 | NIFTY|OPT|2026-10-19|22950|PE | 95.35 → 85.05 | -10.80 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 09:25:34-09:25:42 | NIFTY|OPT|2026-10-19|23150|PE | 107.8 → 116.25 | +7.84 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 09:25:44-09:27:45 | NIFTY|OPT|2026-10-19|23150|PE | 116.25 → 185.1 | +59.23 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 09:35:16-09:39:06 | NIFTY|OPT|2026-10-19|23000|CE | 149.25 → 162.55 | +8.91 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 09:52:13-09:53:02 | NIFTY|OPT|2026-10-19|23150|PE | 92.4 → 77.4 | -16.23 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 09:55:07-10:00:49 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 128.95 | +29.27 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 10:19:48-10:26:10 | NIFTY|OPT|2026-10-19|23000|CE | 111.65 → 110.8 | -0.76 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 10:30:06-10:31:40 | NIFTY|OPT|2026-10-19|23050|CE | 105.6 → 90.2 | -14.58 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 10:34:15-10:42:34 | NIFTY|OPT|2026-10-19|23150|PE | 107.45 → 133.2 | +23.96 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 11:34:58-11:41:31 | NIFTY|OPT|2026-10-19|23050|PE | 77.15 → 89.55 | +16.07 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 11:51:14-12:06:14 | NIFTY|OPT|2026-10-19|23050|PE | 98.8 → 118.6 | +20.04 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 12:16:20-12:17:21 | NIFTY|OPT|2026-10-19|22950|PE | 77.05 → 65.05 | -15.57 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 12:41:36-12:42:57 | NIFTY|OPT|2026-10-19|22950|PE | 73.8 → 63.5 | -13.96 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 12:50:10-12:54:27 | NIFTY|OPT|2026-10-19|22950|PE | 73.6 → 78.95 | +7.27 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 12:55:24-13:02:05 | NIFTY|OPT|2026-10-19|22950|PE | 79.35 → 67.25 | -15.25 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:10:36-13:17:31 | NIFTY|OPT|2026-10-19|22950|PE | 72.8 → 74.85 | +2.82 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:19:13-13:19:59 | NIFTY|OPT|2026-10-19|22950|PE | 87.8 → 92.85 | +5.75 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:20:01-13:20:05 | NIFTY|OPT|2026-10-19|22900|PE | 57.35 → 60.7 | +5.84 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:20:07-13:21:47 | NIFTY|OPT|2026-10-19|22900|PE | 58.7 → 48.5 | -17.38 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:23:29-13:24:07 | NIFTY|OPT|2026-10-19|22900|PE | 67.45 → 69.7 | +3.34 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:24:58-13:29:58 | NIFTY|OPT|2026-10-19|22900|PE | 73.0 → 78.0 | +6.85 | whole session declared defective |
| 2026-10-19 | fx_c20_9y | 13:44:35-13:49:35 | NIFTY|OPT|2026-10-19|22900|PE | 69.95 → 60.15 | -14.01 | whole session declared defective |
| 2026-10-19 | lvl_trail | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | lvl_trail | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | lvl_trail | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | lvl_trail | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail_be | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail_re | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_be | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 12:08:02-12:17:03 | NIFTY|OPT|2026-10-19|23000|PE | 75.45 → 102.35 | +35.65 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | lvl_trail_rx_c10 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 09:27:15-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 161.0 → 153.1 | -4.91 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4_r002 | 09:27:15-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 161.0 → 153.1 | -4.91 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4_r003 | 09:27:15-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 161.0 → 153.1 | -4.91 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 09:27:15-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 161.0 → 153.1 | -4.91 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 09:25:49-09:26:36 | NIFTY|OPT|2026-10-19|23150|PE | 121.95 → 165.6 | +35.79 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 09:28:56-09:31:11 | NIFTY|OPT|2026-10-19|23050|PE | 137.3 → 114.55 | -16.57 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 11:35:18-11:35:57 | NIFTY|OPT|2026-10-19|23100|PE | 119.8 → 106.75 | -10.89 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 14:09:57-14:10:28 | NIFTY|OPT|2026-10-19|22950|PE | 94.45 → 89.9 | -4.82 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 09:27:15-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 161.0 → 153.1 | -4.91 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 09:25:03-09:25:34 | NIFTY|OPT|2026-10-19|23200|PE | 130.85 → 144.05 | +10.09 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 09:29:01-09:30:28 | NIFTY|OPT|2026-10-19|23050|PE | 138.4 → 120.0 | -13.29 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 09:33:43-09:33:58 | NIFTY|OPT|2026-10-19|23000|CE | 134.7 → 126.9 | -5.79 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 09:37:08-09:37:33 | NIFTY|OPT|2026-10-19|23050|CE | 137.35 → 144.0 | +4.84 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 13:22:54-13:22:59 | NIFTY|OPT|2026-10-19|22950|PE | 94.6 → 100.6 | +6.34 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 14:19:54-14:21:20 | NIFTY|OPT|2026-10-19|22800|CE | 75.45 → 67.5 | -10.54 | whole session declared defective |
| 2026-10-19 | n01_ctl_flow | 14:25:06-14:30:06 | NIFTY|OPT|2026-10-19|22900|PE | 69.05 → 67.2 | -2.68 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:25:58-09:26:03 | NIFTY|OPT|2026-10-19|22950|CE | 140.3 → 130.65 | -6.88 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:27:16-09:27:45 | NIFTY|OPT|2026-10-19|22900|CE | 129.25 → 140.85 | +8.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:28:58-09:29:11 | NIFTY|OPT|2026-10-19|22850|CE | 148.5 → 142.75 | -3.87 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:30:43-09:31:11 | NIFTY|OPT|2026-10-19|23050|PE | 121.8 → 114.55 | -5.95 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:32:25-09:32:35 | NIFTY|OPT|2026-10-19|22950|CE | 132.4 → 140.3 | +5.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:33:45-09:35:15 | NIFTY|OPT|2026-10-19|23200|PE | 149.85 → 132.35 | -11.68 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:36:47-09:37:03 | NIFTY|OPT|2026-10-19|23000|CE | 149.05 → 166.85 | +11.94 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:38:32-09:38:55 | NIFTY|OPT|2026-10-19|23050|CE | 144.7 → 131.25 | -9.29 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:40:14-09:41:00 | NIFTY|OPT|2026-10-19|23200|PE | 123.45 → 113.45 | -8.10 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:42:15-09:42:35 | NIFTY|OPT|2026-10-19|23050|CE | 117.7 → 111.55 | -5.22 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:44:31-09:46:38 | NIFTY|OPT|2026-10-19|23250|PE | 142.4 → 145.45 | +2.14 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:48:23-09:49:06 | NIFTY|OPT|2026-10-19|23200|PE | 110.95 → 102.3 | -7.80 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:55:23-09:56:00 | NIFTY|OPT|2026-10-19|23000|CE | 135.1 → 119.0 | -11.92 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 09:57:16-09:58:49 | NIFTY|OPT|2026-10-19|22950|CE | 141.7 → 133.6 | -5.72 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 10:00:12-10:00:42 | NIFTY|OPT|2026-10-19|23150|PE | 148.5 → 132.7 | -10.64 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 10:02:01-10:03:08 | NIFTY|OPT|2026-10-19|23000|CE | 119.9 → 126.1 | +5.17 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 10:09:15-10:09:32 | NIFTY|OPT|2026-10-19|23150|PE | 124.75 → 117.4 | -5.89 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 10:10:52-10:15:52 | NIFTY|OPT|2026-10-19|22950|CE | 139.95 → 143.4 | +2.46 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:03:42-13:04:12 | NIFTY|OPT|2026-10-19|23000|PE | 87.85 → 80.5 | -8.37 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:05:49-13:07:27 | NIFTY|OPT|2026-10-19|22850|CE | 93.3 → 101.85 | +9.16 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:23:02-13:24:03 | NIFTY|OPT|2026-10-19|22800|CE | 86.75 → 80.7 | -6.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:31:39-13:36:38 | NIFTY|OPT|2026-10-19|22950|PE | 107.9 → 95.75 | -11.26 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:38:05-13:42:13 | NIFTY|OPT|2026-10-19|22800|CE | 91.5 → 96.95 | +5.96 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 13:44:01-13:44:33 | NIFTY|OPT|2026-10-19|22800|CE | 84.9 → 77.55 | -8.66 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:04:38-14:05:51 | NIFTY|OPT|2026-10-19|22800|CE | 91.85 → 103.25 | +12.41 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:10:17-14:15:13 | NIFTY|OPT|2026-10-19|22800|CE | 83.85 → 69.0 | -17.71 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:16:17-14:17:55 | NIFTY|OPT|2026-10-19|22900|PE | 56.95 → 62.15 | +9.13 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:25:11-14:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 62.6 → 61.25 | -2.16 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:27:42-14:31:52 | NIFTY|OPT|2026-10-19|22900|PE | 70.85 → 62.5 | -11.79 | whole session declared defective |
| 2026-10-19 | n01_ctl_price | 14:36:36-14:41:36 | NIFTY|OPT|2026-10-19|22800|CE | 64.2 → 64.55 | +0.55 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:25:58-09:26:03 | NIFTY|OPT|2026-10-19|22950|CE | 140.3 → 130.65 | -6.88 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:27:16-09:27:45 | NIFTY|OPT|2026-10-19|22900|CE | 129.25 → 140.85 | +8.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:28:58-09:29:11 | NIFTY|OPT|2026-10-19|22850|CE | 148.5 → 142.75 | -3.87 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:30:43-09:31:11 | NIFTY|OPT|2026-10-19|23050|PE | 121.8 → 114.55 | -5.95 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:32:25-09:32:35 | NIFTY|OPT|2026-10-19|22950|CE | 132.4 → 140.3 | +5.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:33:45-09:35:15 | NIFTY|OPT|2026-10-19|23200|PE | 149.85 → 132.35 | -11.68 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:36:47-09:37:03 | NIFTY|OPT|2026-10-19|23000|CE | 149.05 → 166.85 | +11.94 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:38:32-09:38:55 | NIFTY|OPT|2026-10-19|23050|CE | 144.7 → 131.25 | -9.29 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:40:14-09:41:00 | NIFTY|OPT|2026-10-19|23200|PE | 123.45 → 113.45 | -8.10 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:42:15-09:42:35 | NIFTY|OPT|2026-10-19|23050|CE | 117.7 → 111.55 | -5.22 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:44:31-09:46:38 | NIFTY|OPT|2026-10-19|23250|PE | 142.4 → 145.45 | +2.14 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:48:23-09:49:06 | NIFTY|OPT|2026-10-19|23200|PE | 110.95 → 102.3 | -7.80 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:55:23-09:56:00 | NIFTY|OPT|2026-10-19|23000|CE | 135.1 → 119.0 | -11.92 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 09:57:16-09:58:49 | NIFTY|OPT|2026-10-19|22950|CE | 141.7 → 133.6 | -5.72 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 10:00:12-10:00:42 | NIFTY|OPT|2026-10-19|23150|PE | 148.5 → 132.7 | -10.64 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 10:02:01-10:03:08 | NIFTY|OPT|2026-10-19|23000|CE | 119.9 → 126.1 | +5.17 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 10:09:15-10:09:32 | NIFTY|OPT|2026-10-19|23150|PE | 124.75 → 117.4 | -5.89 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 10:10:52-10:15:52 | NIFTY|OPT|2026-10-19|22950|CE | 139.95 → 143.4 | +2.46 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:03:42-13:04:12 | NIFTY|OPT|2026-10-19|23000|PE | 87.85 → 80.5 | -8.37 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:05:49-13:07:27 | NIFTY|OPT|2026-10-19|22850|CE | 93.3 → 101.85 | +9.16 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:23:02-13:24:03 | NIFTY|OPT|2026-10-19|22800|CE | 86.75 → 80.7 | -6.97 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:31:39-13:36:38 | NIFTY|OPT|2026-10-19|22950|PE | 107.9 → 95.75 | -11.26 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:38:05-13:42:13 | NIFTY|OPT|2026-10-19|22800|CE | 91.5 → 96.95 | +5.96 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 13:44:01-13:44:33 | NIFTY|OPT|2026-10-19|22800|CE | 84.9 → 77.55 | -8.66 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:04:38-14:05:51 | NIFTY|OPT|2026-10-19|22800|CE | 91.85 → 103.25 | +12.41 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:10:17-14:15:13 | NIFTY|OPT|2026-10-19|22800|CE | 83.85 → 69.0 | -17.71 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:16:17-14:17:55 | NIFTY|OPT|2026-10-19|22900|PE | 56.95 → 62.15 | +9.13 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:25:11-14:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 62.6 → 61.25 | -2.16 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:27:42-14:31:52 | NIFTY|OPT|2026-10-19|22900|PE | 70.85 → 62.5 | -11.79 | whole session declared defective |
| 2026-10-19 | n01_ctl_price_ind | 14:36:36-14:41:36 | NIFTY|OPT|2026-10-19|22800|CE | 64.2 → 64.55 | +0.55 | whole session declared defective |
| 2026-10-19 | n01_release | 14:26:43-14:26:59 | NIFTY|OPT|2026-10-19|22900|PE | 71.55 → 70.3 | -1.75 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:25:32-09:25:38 | NIFTY|OPT|2026-10-19|23000|CE | 117.95 → 113.7 | -3.60 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:27:16-09:27:19 | NIFTY|OPT|2026-10-19|22900|CE | 129.25 → 131.75 | +1.93 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:29:33-09:29:43 | NIFTY|OPT|2026-10-19|23050|PE | 126.45 → 136.85 | +8.22 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:31:17-09:31:25 | NIFTY|OPT|2026-10-19|23100|PE | 146.0 → 137.6 | -5.75 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:32:28-09:32:35 | NIFTY|OPT|2026-10-19|23150|PE | 146.4 → 139.1 | -4.99 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:34:25-09:34:31 | NIFTY|OPT|2026-10-19|23000|CE | 125.3 → 137.6 | +9.82 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:36:40-09:37:01 | NIFTY|OPT|2026-10-19|23000|CE | 146.8 → 160.0 | +8.99 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:38:20-09:38:55 | NIFTY|OPT|2026-10-19|23050|CE | 139.65 → 131.25 | -6.01 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:40:17-09:41:05 | NIFTY|OPT|2026-10-19|23000|CE | 148.6 → 158.35 | +6.56 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:42:50-09:44:01 | NIFTY|OPT|2026-10-19|23000|CE | 152.0 → 156.4 | +2.90 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:45:31-09:46:16 | NIFTY|OPT|2026-10-19|23250|PE | 133.65 → 146.85 | +9.88 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:47:27-09:48:17 | NIFTY|OPT|2026-10-19|23050|CE | 118.75 → 121.75 | +2.53 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:49:19-09:51:20 | NIFTY|OPT|2026-10-19|23200|PE | 110.85 → 111.4 | +0.50 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:55:20-09:55:35 | NIFTY|OPT|2026-10-19|23000|CE | 132.25 → 133.55 | +0.98 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:56:57-09:57:09 | NIFTY|OPT|2026-10-19|22950|CE | 146.95 → 141.35 | -3.81 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 09:58:33-09:58:49 | NIFTY|OPT|2026-10-19|22950|CE | 139.4 → 133.6 | -4.16 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 10:00:50-10:00:53 | NIFTY|OPT|2026-10-19|23150|PE | 129.0 → 126.15 | -2.21 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 10:03:15-10:04:00 | NIFTY|OPT|2026-10-19|23200|PE | 141.9 → 151.85 | +7.01 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 10:09:13-10:09:32 | NIFTY|OPT|2026-10-19|22950|CE | 140.0 → 145.75 | +4.11 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 10:10:35-10:11:08 | NIFTY|OPT|2026-10-19|22950|CE | 136.3 → 143.65 | +5.39 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:03:24-13:03:30 | NIFTY|OPT|2026-10-19|23000|PE | 90.65 → 86.05 | -5.07 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:04:57-13:05:32 | NIFTY|OPT|2026-10-19|22850|CE | 99.5 → 91.6 | -7.94 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:07:30-13:07:57 | NIFTY|OPT|2026-10-19|23000|PE | 90.6 → 94.25 | +4.03 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:09:34-13:10:51 | NIFTY|OPT|2026-10-19|22850|CE | 87.65 → 83.7 | -4.51 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:23:02-13:23:53 | NIFTY|OPT|2026-10-19|22800|CE | 86.75 → 81.3 | -6.28 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:32:05-13:35:05 | NIFTY|OPT|2026-10-19|22800|CE | 77.4 → 83.2 | +7.49 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:36:34-13:39:34 | NIFTY|OPT|2026-10-19|22950|PE | 95.0 → 92.55 | -2.58 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:40:36-13:41:25 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 93.05 | +9.21 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 13:43:06-13:44:21 | NIFTY|OPT|2026-10-19|22800|CE | 88.0 → 83.7 | -4.89 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:05:19-14:08:19 | NIFTY|OPT|2026-10-19|22950|PE | 81.65 → 81.15 | -0.61 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:10:02-14:10:31 | NIFTY|OPT|2026-10-19|22800|CE | 80.05 → 87.6 | +9.43 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:11:37-14:12:14 | NIFTY|OPT|2026-10-19|22950|PE | 88.7 → 95.75 | +7.95 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:15:30-14:16:10 | NIFTY|OPT|2026-10-19|22800|CE | 72.05 → 79.4 | +10.20 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:17:31-14:18:05 | NIFTY|OPT|2026-10-19|22800|CE | 72.3 → 70.8 | -2.08 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:25:21-14:28:22 | NIFTY|OPT|2026-10-19|22800|CE | 59.75 → 61.25 | +2.51 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:32:17-14:35:18 | NIFTY|OPT|2026-10-19|22900|PE | 57.45 → 62.35 | +8.53 | whole session declared defective |
| 2026-10-19 | n02_ctl_mr | 14:36:30-14:39:31 | NIFTY|OPT|2026-10-19|22800|CE | 63.1 → 64.55 | +2.30 | whole session declared defective |
| 2026-10-19 | n02_relax | 09:26:37-09:27:01 | NIFTY|OPT|2026-10-19|22900|CE | 150.9 → 138.6 | -8.15 | whole session declared defective |
| 2026-10-19 | n02_relax | 09:31:33-09:31:53 | NIFTY|OPT|2026-10-19|23100|PE | 142.75 → 151.2 | +5.92 | whole session declared defective |
| 2026-10-19 | n02_relax | 09:38:45-09:38:54 | NIFTY|OPT|2026-10-19|23250|PE | 129.75 → 138.65 | +6.86 | whole session declared defective |
| 2026-10-19 | n02_relax | 10:01:03-10:01:09 | NIFTY|OPT|2026-10-19|23150|PE | 118.45 → 116.35 | -1.77 | whole session declared defective |
| 2026-10-19 | n02_relax | 13:23:12-13:25:01 | NIFTY|OPT|2026-10-19|22800|CE | 86.55 → 76.0 | -12.19 | whole session declared defective |
| 2026-10-19 | n02_relax | 14:25:26-14:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 59.6 → 61.25 | +2.77 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:28:09-09:28:28 | NIFTY|OPT|2026-10-19|22900|CE | 135.05 → 125.3 | -7.22 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:30:02-09:30:28 | NIFTY|OPT|2026-10-19|23050|PE | 139.15 → 120.0 | -13.76 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:34:35-09:35:18 | NIFTY|OPT|2026-10-19|23000|CE | 136.4 → 151.35 | +10.96 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:36:37-09:37:01 | NIFTY|OPT|2026-10-19|23000|CE | 146.95 → 160.0 | +8.88 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:40:17-09:41:05 | NIFTY|OPT|2026-10-19|23200|PE | 122.5 → 113.25 | -7.55 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:45:22-09:46:38 | NIFTY|OPT|2026-10-19|23250|PE | 137.5 → 145.45 | +5.78 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:49:23-09:52:09 | NIFTY|OPT|2026-10-19|23200|PE | 111.85 → 125.95 | +12.61 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:57:54-09:58:30 | NIFTY|OPT|2026-10-19|23000|CE | 115.55 → 107.5 | -6.97 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 09:59:55-10:00:44 | NIFTY|OPT|2026-10-19|23150|PE | 147.2 → 129.45 | -12.06 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 10:02:10-10:03:08 | NIFTY|OPT|2026-10-19|23150|PE | 115.0 → 104.55 | -9.09 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 10:09:11-10:09:32 | NIFTY|OPT|2026-10-19|22950|CE | 136.95 → 145.75 | +6.43 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 10:11:12-10:13:19 | NIFTY|OPT|2026-10-19|23150|PE | 115.95 → 127.25 | +9.75 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 12:59:18-13:02:32 | NIFTY|OPT|2026-10-19|22950|PE | 76.55 → 67.3 | -12.08 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:04:41-13:05:32 | NIFTY|OPT|2026-10-19|23000|PE | 89.35 → 98.3 | +10.02 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:06:32-13:07:14 | NIFTY|OPT|2026-10-19|22850|CE | 88.8 → 98.2 | +10.59 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:08:50-13:09:27 | NIFTY|OPT|2026-10-19|22850|CE | 91.4 → 86.75 | -5.09 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:11:18-13:16:19 | NIFTY|OPT|2026-10-19|22850|CE | 84.0 → 78.55 | -6.49 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:28:29-13:33:30 | NIFTY|OPT|2026-10-19|22800|CE | 80.85 → 78.3 | -3.15 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:34:30-13:36:38 | NIFTY|OPT|2026-10-19|22800|CE | 83.0 → 90.9 | +9.52 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:38:18-13:41:33 | NIFTY|OPT|2026-10-19|22950|PE | 99.0 → 84.0 | -15.15 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 13:43:02-13:44:27 | NIFTY|OPT|2026-10-19|22950|PE | 95.2 → 106.0 | +11.35 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:05:06-14:09:46 | NIFTY|OPT|2026-10-19|22800|CE | 98.05 → 81.8 | -16.57 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:11:16-14:15:08 | NIFTY|OPT|2026-10-19|22800|CE | 87.65 → 72.15 | -17.68 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:17:16-14:21:47 | NIFTY|OPT|2026-10-19|22900|PE | 63.25 → 64.25 | +1.58 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:25:11-14:30:11 | NIFTY|OPT|2026-10-19|22900|PE | 68.8 → 66.95 | -2.69 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:31:21-14:36:21 | NIFTY|OPT|2026-10-19|22800|CE | 72.15 → 63.95 | -11.37 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:38:33-14:39:04 | NIFTY|OPT|2026-10-19|22900|PE | 65.45 → 60.45 | -7.64 | whole session declared defective |
| 2026-10-19 | n06_ctl_breadth | 14:40:26-14:43:14 | NIFTY|OPT|2026-10-19|22900|PE | 64.5 → 48.8 | -24.34 | whole session declared defective |
| 2026-10-19 | n06_lead | 09:48:51-09:49:06 | NIFTY|OPT|2026-10-19|23200|PE | 108.65 → 102.3 | -5.84 | whole session declared defective |
| 2026-10-19 | n06_lead | 09:54:51-09:55:53 | NIFTY|OPT|2026-10-19|23200|PE | 125.5 → 143.45 | +14.30 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:25:28-09:25:40 | NIFTY|OPT|2026-10-19|23000|CE | 121.25 → 110.15 | -9.15 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:27:28-09:27:46 | NIFTY|OPT|2026-10-19|22850|CE | 166.8 → 180.95 | +8.48 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:29:54-09:30:04 | NIFTY|OPT|2026-10-19|22850|CE | 150.95 → 141.45 | -6.29 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:31:58-09:32:07 | NIFTY|OPT|2026-10-19|22900|CE | 135.1 → 155.35 | +14.99 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:34:54-09:35:12 | NIFTY|OPT|2026-10-19|23200|PE | 147.2 → 138.4 | -5.98 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:37:07-09:37:24 | NIFTY|OPT|2026-10-19|23250|PE | 138.55 → 131.45 | -5.12 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:39:48-09:40:07 | NIFTY|OPT|2026-10-19|23250|PE | 146.75 → 152.55 | +3.95 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:42:04-09:42:35 | NIFTY|OPT|2026-10-19|23050|CE | 117.5 → 111.55 | -5.06 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:52:43-09:53:13 | NIFTY|OPT|2026-10-19|23200|PE | 112.3 → 118.95 | +5.92 | whole session declared defective |
| 2026-10-19 | p02_clock | 09:58:51-09:59:12 | NIFTY|OPT|2026-10-19|22950|CE | 133.75 → 122.45 | -8.45 | whole session declared defective |
| 2026-10-19 | p02_clock | 10:01:10-10:01:14 | NIFTY|OPT|2026-10-19|23150|PE | 113.85 → 112.15 | -1.49 | whole session declared defective |
| 2026-10-19 | p02_clock | 10:02:15-10:02:21 | NIFTY|OPT|2026-10-19|23000|CE | 120.05 → 115.95 | -3.42 | whole session declared defective |
| 2026-10-19 | p02_clock | 10:04:11-10:04:27 | NIFTY|OPT|2026-10-19|23150|PE | 114.25 → 121.1 | +6.00 | whole session declared defective |
| 2026-10-19 | p02_clock | 10:06:30-10:06:51 | NIFTY|OPT|2026-10-19|22950|CE | 132.05 → 122.85 | -6.97 | whole session declared defective |
| 2026-10-19 | p02_clock | 10:07:53-10:08:02 | NIFTY|OPT|2026-10-19|22950|CE | 127.2 → 134.2 | +5.50 | whole session declared defective |
| 2026-10-19 | p02_clock | 12:43:54-12:44:28 | NIFTY|OPT|2026-10-19|22850|CE | 96.5 → 91.45 | -5.23 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:03:06-13:03:19 | NIFTY|OPT|2026-10-19|22850|CE | 94.0 → 100.6 | +7.02 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:04:54-13:05:29 | NIFTY|OPT|2026-10-19|22850|CE | 100.9 → 91.55 | -9.27 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:07:19-13:07:40 | NIFTY|OPT|2026-10-19|22850|CE | 99.65 → 92.85 | -6.82 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:09:37-13:10:19 | NIFTY|OPT|2026-10-19|22850|CE | 87.1 → 81.4 | -6.54 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:19:59-13:20:36 | NIFTY|OPT|2026-10-19|22800|CE | 93.8 → 99.0 | +5.54 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:24:37-13:24:43 | NIFTY|OPT|2026-10-19|22950|PE | 104.95 → 105.55 | +0.57 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:27:21-13:29:48 | NIFTY|OPT|2026-10-19|22800|CE | 79.65 → 75.75 | -4.90 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:37:56-13:38:14 | NIFTY|OPT|2026-10-19|22800|CE | 92.1 → 87.35 | -5.16 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:40:17-13:40:47 | NIFTY|OPT|2026-10-19|22800|CE | 85.6 → 90.5 | +5.72 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:52:46-13:57:07 | NIFTY|OPT|2026-10-19|22800|CE | 82.4 → 78.75 | -4.43 | whole session declared defective |
| 2026-10-19 | p02_clock | 13:58:23-14:00:49 | NIFTY|OPT|2026-10-19|22800|CE | 80.3 → 75.1 | -6.48 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:02:28-14:02:59 | NIFTY|OPT|2026-10-19|22800|CE | 92.75 → 97.4 | +5.01 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:06:11-14:06:31 | NIFTY|OPT|2026-10-19|22850|CE | 62.25 → 58.8 | -5.54 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:07:39-14:08:44 | NIFTY|OPT|2026-10-19|22800|CE | 96.25 → 90.3 | -6.18 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:09:45-14:10:31 | NIFTY|OPT|2026-10-19|22800|CE | 82.4 → 87.6 | +6.31 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:11:58-14:12:11 | NIFTY|OPT|2026-10-19|22800|CE | 82.5 → 77.8 | -5.70 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:14:08-14:15:09 | NIFTY|OPT|2026-10-19|22800|CE | 77.45 → 71.8 | -7.29 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:21:23-14:21:33 | NIFTY|OPT|2026-10-19|22800|CE | 65.7 → 69.55 | +5.86 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:27:28-14:28:09 | NIFTY|OPT|2026-10-19|22800|CE | 62.3 → 59.55 | -4.41 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:30:14-14:30:33 | NIFTY|OPT|2026-10-19|22800|CE | 63.45 → 60.1 | -5.28 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:32:08-14:32:23 | NIFTY|OPT|2026-10-19|22800|CE | 74.3 → 70.7 | -4.84 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:35:11-14:36:19 | NIFTY|OPT|2026-10-19|22800|CE | 69.0 → 64.0 | -7.25 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:37:36-14:37:55 | NIFTY|OPT|2026-10-19|22800|CE | 65.5 → 61.5 | -6.11 | whole session declared defective |
| 2026-10-19 | p02_clock | 14:39:44-14:39:58 | NIFTY|OPT|2026-10-19|22800|CE | 62.2 → 59.1 | -4.98 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:25:27-09:25:39 | NIFTY|OPT|2026-10-19|23200|PE | 139.7 → 149.0 | +6.66 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:27:27-09:27:45 | NIFTY|OPT|2026-10-19|23100|PE | 157.6 → 145.1 | -7.93 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:30:04-09:30:07 | NIFTY|OPT|2026-10-19|23050|PE | 140.85 → 132.7 | -5.79 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:31:16-09:31:28 | NIFTY|OPT|2026-10-19|22900|CE | 134.75 → 142.45 | +5.71 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:33:15-09:33:29 | NIFTY|OPT|2026-10-19|22950|CE | 158.7 → 167.45 | +5.51 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:35:19-09:35:45 | NIFTY|OPT|2026-10-19|23000|CE | 147.4 → 159.0 | +7.87 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:37:37-09:38:14 | NIFTY|OPT|2026-10-19|23050|CE | 143.85 → 137.05 | -4.73 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:40:16-09:41:03 | NIFTY|OPT|2026-10-19|23200|PE | 120.35 → 112.9 | -6.19 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:44:06-09:44:15 | NIFTY|OPT|2026-10-19|23050|CE | 128.8 → 137.4 | +6.68 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:46:39-09:47:15 | NIFTY|OPT|2026-10-19|23250|PE | 145.2 → 153.9 | +5.99 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:52:11-09:52:20 | NIFTY|OPT|2026-10-19|23200|PE | 127.4 → 119.95 | -5.85 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:53:31-09:54:00 | NIFTY|OPT|2026-10-19|23200|PE | 120.7 → 115.35 | -4.43 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 09:58:50-09:59:08 | NIFTY|OPT|2026-10-19|23150|PE | 137.2 → 145.5 | +6.05 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 10:00:50-10:00:59 | NIFTY|OPT|2026-10-19|22950|CE | 142.8 → 152.65 | +6.90 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 10:03:12-10:03:42 | NIFTY|OPT|2026-10-19|23000|CE | 125.1 → 117.85 | -5.79 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 10:08:22-10:08:38 | NIFTY|OPT|2026-10-19|22950|CE | 135.0 → 141.6 | +4.89 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 10:09:57-10:10:18 | NIFTY|OPT|2026-10-19|23000|CE | 110.45 → 105.5 | -4.48 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 12:54:28-12:55:20 | NIFTY|OPT|2026-10-19|23000|PE | 112.7 → 118.4 | +5.06 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 13:03:29-13:04:05 | NIFTY|OPT|2026-10-19|22850|CE | 105.5 → 115.2 | +9.19 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 13:18:10-13:19:53 | NIFTY|OPT|2026-10-19|22950|PE | 85.25 → 89.75 | +5.28 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 13:22:38-13:22:56 | NIFTY|OPT|2026-10-19|22950|PE | 91.05 → 95.85 | +5.27 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 13:25:02-13:25:08 | NIFTY|OPT|2026-10-19|22900|PE | 75.4 → 70.65 | -6.30 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 13:27:19-13:28:14 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.95 | -6.41 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 14:02:36-14:03:11 | NIFTY|OPT|2026-10-19|22800|CE | 93.55 → 102.25 | +9.30 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 14:09:52-14:10:17 | NIFTY|OPT|2026-10-19|22950|PE | 95.75 → 91.35 | -4.59 | whole session declared defective |
| 2026-10-19 | p02_ctl_mom | 14:24:04-14:24:11 | NIFTY|OPT|2026-10-19|22900|PE | 68.9 → 65.35 | -5.15 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:26:11-09:26:23 | NIFTY|OPT|2026-10-19|22950|CE | 129.15 → 118.95 | -7.90 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:29:02-09:29:23 | NIFTY|OPT|2026-10-19|22850|CE | 147.55 → 152.8 | +3.56 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:33:17-09:33:32 | NIFTY|OPT|2026-10-19|23200|PE | 161.85 → 153.45 | -5.19 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:37:16-09:37:24 | NIFTY|OPT|2026-10-19|23250|PE | 138.6 → 131.45 | -5.16 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:42:10-09:42:35 | NIFTY|OPT|2026-10-19|23050|CE | 117.0 → 111.55 | -4.66 | whole session declared defective |
| 2026-10-19 | p02_top1 | 09:58:52-09:59:09 | NIFTY|OPT|2026-10-19|22950|CE | 134.3 → 126.95 | -5.47 | whole session declared defective |
| 2026-10-19 | p02_top1 | 10:00:20-10:00:42 | NIFTY|OPT|2026-10-19|22950|CE | 129.45 → 137.6 | +6.30 | whole session declared defective |
| 2026-10-19 | p02_top1 | 13:38:19-13:39:16 | NIFTY|OPT|2026-10-19|22800|CE | 86.1 → 91.35 | +6.10 | whole session declared defective |
| 2026-10-19 | p02_top1 | 13:58:04-14:00:13 | NIFTY|OPT|2026-10-19|22800|CE | 83.5 → 78.4 | -6.11 | whole session declared defective |
| 2026-10-19 | p02_top1 | 14:01:42-14:02:11 | NIFTY|OPT|2026-10-19|22800|CE | 78.35 → 83.55 | +6.64 | whole session declared defective |
| 2026-10-19 | p02_top1 | 14:06:28-14:06:33 | NIFTY|OPT|2026-10-19|22850|CE | 61.5 → 58.1 | -5.53 | whole session declared defective |
| 2026-10-19 | p02_top1 | 14:07:56-14:08:22 | NIFTY|OPT|2026-10-19|22850|CE | 61.0 → 57.25 | -6.15 | whole session declared defective |
| 2026-10-19 | p02_top1 | 14:11:02-14:11:44 | NIFTY|OPT|2026-10-19|22800|CE | 89.5 → 84.3 | -5.81 | whole session declared defective |
| 2026-10-19 | p02_top1 | 14:27:50-14:28:10 | NIFTY|OPT|2026-10-19|22800|CE | 61.45 → 60.6 | -1.38 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:26:19-09:26:24 | NIFTY|OPT|2026-10-19|22950|CE | 126.35 → 117.4 | -7.08 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:29:10-09:29:19 | NIFTY|OPT|2026-10-19|22850|CE | 143.5 → 153.55 | +7.00 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:33:22-09:33:32 | NIFTY|OPT|2026-10-19|23200|PE | 161.9 → 153.45 | -5.22 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:37:16-09:37:24 | NIFTY|OPT|2026-10-19|23250|PE | 138.6 → 131.45 | -5.16 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:42:11-09:42:13 | NIFTY|OPT|2026-10-19|23050|CE | 116.45 → 118.55 | +1.80 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 09:58:52-09:59:09 | NIFTY|OPT|2026-10-19|22950|CE | 134.3 → 126.95 | -5.47 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 10:00:37-10:00:44 | NIFTY|OPT|2026-10-19|22950|CE | 131.95 → 142.35 | +7.88 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 12:42:38-12:43:21 | NIFTY|OPT|2026-10-19|22850|CE | 97.15 → 102.15 | +5.15 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:00:56-13:01:39 | NIFTY|OPT|2026-10-19|22850|CE | 82.05 → 85.65 | +4.39 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:03:06-13:03:19 | NIFTY|OPT|2026-10-19|22850|CE | 94.0 → 100.6 | +7.02 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:18:52-13:19:11 | NIFTY|OPT|2026-10-19|22800|CE | 105.95 → 98.75 | -6.80 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:20:54-13:21:47 | NIFTY|OPT|2026-10-19|22800|CE | 100.9 → 106.8 | +5.85 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:29:34-13:29:48 | NIFTY|OPT|2026-10-19|22800|CE | 78.8 → 75.75 | -3.87 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:31:50-13:33:49 | NIFTY|OPT|2026-10-19|22800|CE | 77.95 → 82.75 | +6.16 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:54:31-13:56:14 | NIFTY|OPT|2026-10-19|22800|CE | 81.45 → 85.0 | +4.36 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 13:57:36-14:00:14 | NIFTY|OPT|2026-10-19|22800|CE | 81.7 → 77.5 | -5.14 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 14:01:47-14:02:14 | NIFTY|OPT|2026-10-19|22800|CE | 80.1 → 84.1 | +4.99 | whole session declared defective |
| 2026-10-19 | p05_adaptive | 14:07:57-14:08:22 | NIFTY|OPT|2026-10-19|22850|CE | 61.2 → 57.25 | -6.45 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:25:00-09:26:36 | NIFTY|OPT|2026-10-19|23150|PE | 98.75 → 165.6 | +67.70 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:42:09-09:44:09 | NIFTY|OPT|2026-10-19|23150|PE | 88.05 → 70.5 | -19.93 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:49:19-09:52:28 | NIFTY|OPT|2026-10-19|23150|PE | 80.25 → 83.7 | +4.30 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:53:30-09:57:50 | NIFTY|OPT|2026-10-19|23150|PE | 87.8 → 120.5 | +37.24 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:02:09-10:03:58 | NIFTY|OPT|2026-10-19|23050|CE | 85.3 → 82.65 | -3.11 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:04:58-10:06:18 | NIFTY|OPT|2026-10-19|23050|CE | 78.45 → 68.05 | -13.26 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:11:18-10:13:07 | NIFTY|OPT|2026-10-19|23050|CE | 79.6 → 69.65 | -12.50 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:19:46-10:24:49 | NIFTY|OPT|2026-10-19|23050|CE | 79.65 → 83.1 | +4.33 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:25:50-10:30:36 | NIFTY|OPT|2026-10-19|23050|CE | 82.6 → 96.8 | +17.19 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:45:09-10:49:42 | NIFTY|OPT|2026-10-19|23050|PE | 74.1 → 72.15 | -2.63 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:50:53-10:52:33 | NIFTY|OPT|2026-10-19|23050|PE | 75.2 → 61.3 | -18.48 | whole session declared defective |
| 2026-10-19 | premium_momentum | 10:59:23-11:03:18 | NIFTY|OPT|2026-10-19|23050|CE | 66.45 → 58.35 | -12.19 | whole session declared defective |
| 2026-10-19 | premium_momentum | 11:07:33-11:12:28 | NIFTY|OPT|2026-10-19|23050|CE | 65.6 → 67.3 | +2.59 | whole session declared defective |
| 2026-10-19 | premium_momentum | 11:20:32-11:22:11 | NIFTY|OPT|2026-10-19|23050|CE | 71.1 → 63.1 | -11.25 | whole session declared defective |
| 2026-10-19 | premium_momentum | 11:31:53-11:35:57 | NIFTY|OPT|2026-10-19|23050|PE | 64.95 → 74.6 | +14.86 | whole session declared defective |
| 2026-10-19 | premium_momentum | 11:44:20-11:46:34 | NIFTY|OPT|2026-10-19|22950|CE | 84.15 → 76.5 | -9.09 | whole session declared defective |
| 2026-10-19 | premium_momentum | 11:48:45-11:50:13 | NIFTY|OPT|2026-10-19|22950|CE | 88.65 → 74.15 | -16.36 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:32:21-12:43:07 | NIFTY|OPT|2026-10-19|22950|PE | 65.6 → 66.25 | +0.99 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:44:08-12:52:57 | NIFTY|OPT|2026-10-19|22950|PE | 69.2 → 65.65 | -5.13 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:54:20-13:02:35 | NIFTY|OPT|2026-10-19|22950|PE | 76.0 → 67.4 | -11.32 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:03:36-13:04:44 | NIFTY|OPT|2026-10-19|22900|CE | 69.25 → 66.1 | -4.55 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:06:49-13:07:57 | NIFTY|OPT|2026-10-19|22900|CE | 59.25 → 61.05 | +3.04 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:29:15-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 73.45 → 64.45 | -12.25 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:37:44-13:43:05 | NIFTY|OPT|2026-10-19|22850|CE | 56.05 → 53.95 | -3.75 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:51:44-14:07:25 | NIFTY|OPT|2026-10-19|22850|CE | 47.6 → 55.85 | +17.33 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:25:43-14:32:04 | NIFTY|OPT|2026-10-19|22850|PE | 38.05 → 27.85 | -26.81 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:33:04-14:36:33 | NIFTY|OPT|2026-10-19|22850|CE | 38.95 → 32.1 | -17.59 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:39:59-14:41:47 | NIFTY|OPT|2026-10-19|22850|PE | 33.35 → 28.9 | -13.34 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:42:49-14:45:44 | NIFTY|OPT|2026-10-19|22850|CE | 35.45 → 41.05 | +15.80 | whole session declared defective |
| 2026-10-19 | random_entry | 09:57:51-09:59:45 | NIFTY|OPT|2026-10-19|23150|PE | 117.15 → 144.75 | +23.56 | whole session declared defective |
| 2026-10-19 | random_entry | 10:41:28-10:42:26 | NIFTY|OPT|2026-10-19|23100|PE | 109.95 → 102.6 | -6.68 | whole session declared defective |
| 2026-10-19 | random_entry | 12:24:35-12:28:43 | NIFTY|OPT|2026-10-19|22850|CE | 93.7 → 101.75 | +8.59 | whole session declared defective |
| 2026-10-19 | random_entry | 12:51:43-12:52:57 | NIFTY|OPT|2026-10-19|23000|PE | 107.6 → 100.15 | -6.92 | whole session declared defective |
| 2026-10-19 | random_entry | 13:52:07-14:07:25 | NIFTY|OPT|2026-10-19|22800|CE | 81.65 → 92.3 | +13.04 | whole session declared defective |
| 2026-10-19 | random_entry | 14:14:26-14:17:50 | NIFTY|OPT|2026-10-19|22800|CE | 76.7 → 72.05 | -6.06 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:25:46-09:26:02 | NIFTY|OPT|2026-10-19|23150|PE | 119.35 → 134.9 | +13.03 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:27:09-09:27:14 | NIFTY|OPT|2026-10-19|23100|PE | 154.75 → 163.75 | +5.82 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:28:52-09:28:56 | NIFTY|OPT|2026-10-19|23050|PE | 133.2 → 137.3 | +3.08 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:30:04-09:30:27 | NIFTY|OPT|2026-10-19|23050|PE | 140.85 → 121.1 | -14.02 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:32:05-09:32:07 | NIFTY|OPT|2026-10-19|22900|CE | 154.75 → 156.0 | +0.81 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:33:12-09:33:34 | NIFTY|OPT|2026-10-19|22950|CE | 160.65 → 167.55 | +4.29 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:37:10-09:37:33 | NIFTY|OPT|2026-10-19|23050|CE | 138.4 → 144.0 | +4.05 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:39:13-09:39:47 | NIFTY|OPT|2026-10-19|23200|PE | 121.75 → 112.2 | -7.84 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:44:14-09:46:15 | NIFTY|OPT|2026-10-19|23050|CE | 136.5 → 123.4 | -9.60 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:56:02-09:57:00 | NIFTY|OPT|2026-10-19|23150|PE | 113.3 → 123.8 | +9.27 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 09:59:11-09:59:45 | NIFTY|OPT|2026-10-19|23150|PE | 154.5 → 144.75 | -6.31 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 10:01:02-10:03:02 | NIFTY|OPT|2026-10-19|23000|CE | 116.4 → 119.45 | +2.62 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 13:04:52-13:06:52 | NIFTY|OPT|2026-10-19|23000|PE | 91.1 → 96.3 | +5.71 | whole session declared defective |
| 2026-10-19 | s01_ctl_cash | 13:44:51-13:46:51 | NIFTY|OPT|2026-10-19|22900|PE | 72.1 → 74.25 | +2.98 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:25:43-09:25:53 | NIFTY|OPT|2026-10-19|23150|PE | 115.85 → 126.8 | +9.45 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:27:14-09:27:19 | NIFTY|OPT|2026-10-19|23100|PE | 163.75 → 153.1 | -6.50 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:29:00-09:30:05 | NIFTY|OPT|2026-10-19|23050|PE | 141.75 → 138.1 | -2.58 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:31:21-09:32:07 | NIFTY|OPT|2026-10-19|22900|CE | 135.05 → 156.0 | +15.51 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:33:10-09:33:17 | NIFTY|OPT|2026-10-19|22950|CE | 159.1 → 160.1 | +0.63 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:37:08-09:37:33 | NIFTY|OPT|2026-10-19|23050|CE | 137.35 → 144.0 | +4.84 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:39:12-09:40:10 | NIFTY|OPT|2026-10-19|23200|PE | 122.0 → 125.6 | +2.95 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:44:16-09:44:39 | NIFTY|OPT|2026-10-19|23050|CE | 138.15 → 126.25 | -8.61 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:53:31-09:54:01 | NIFTY|OPT|2026-10-19|23200|PE | 120.7 → 114.45 | -5.18 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:56:02-09:57:00 | NIFTY|OPT|2026-10-19|23150|PE | 113.3 → 123.8 | +9.27 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 09:59:11-09:59:45 | NIFTY|OPT|2026-10-19|23150|PE | 154.5 → 144.75 | -6.31 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 10:00:46-10:01:01 | NIFTY|OPT|2026-10-19|22950|CE | 142.05 → 152.8 | +7.57 | whole session declared defective |
| 2026-10-19 | s01_ctl_sfut | 13:04:52-13:06:52 | NIFTY|OPT|2026-10-19|23000|PE | 90.9 → 96.0 | +5.61 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:28:24-09:28:53 | NIFTY|OPT|2026-10-19|22900|CE | 130.4 → 116.95 | -10.31 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:30:08-09:30:27 | NIFTY|OPT|2026-10-19|23050|PE | 132.35 → 121.1 | -8.50 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:32:02-09:32:07 | NIFTY|OPT|2026-10-19|22900|CE | 142.2 → 156.0 | +9.71 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:34:46-09:35:07 | NIFTY|OPT|2026-10-19|23000|CE | 137.1 → 134.15 | -2.15 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:38:36-09:38:55 | NIFTY|OPT|2026-10-19|23050|CE | 141.5 → 131.25 | -7.24 | whole session declared defective |
| 2026-10-19 | s01_transmit | 09:45:44-09:46:15 | NIFTY|OPT|2026-10-19|23050|CE | 135.25 → 123.4 | -8.76 | whole session declared defective |
| 2026-10-19 | s01_transmit | 10:00:02-10:00:44 | NIFTY|OPT|2026-10-19|23150|PE | 149.2 → 129.45 | -13.24 | whole session declared defective |
| 2026-10-19 | s03_recruit | 09:30:01-09:30:28 | NIFTY|OPT|2026-10-19|23050|PE | 135.75 → 120.0 | -11.60 | whole session declared defective |
| 2026-10-19 | s03_recruit | 09:34:45-09:35:07 | NIFTY|OPT|2026-10-19|23000|CE | 136.95 → 135.3 | -1.21 | whole session declared defective |
| 2026-10-19 | s03_recruit | 09:38:16-09:38:31 | NIFTY|OPT|2026-10-19|23250|PE | 134.95 → 127.05 | -5.85 | whole session declared defective |
| 2026-10-19 | s03_recruit | 09:47:46-09:48:01 | NIFTY|OPT|2026-10-19|23050|CE | 121.6 → 119.85 | -1.44 | whole session declared defective |
| 2026-10-19 | s03_recruit | 09:59:44-09:59:58 | NIFTY|OPT|2026-10-19|22950|CE | 130.0 → 127.3 | -2.08 | whole session declared defective |
| 2026-10-19 | s03_recruit | 10:01:36-10:02:02 | NIFTY|OPT|2026-10-19|23150|PE | 126.65 → 114.0 | -9.99 | whole session declared defective |
| 2026-10-19 | s03_recruit | 10:07:22-10:07:31 | NIFTY|OPT|2026-10-19|22950|CE | 131.8 → 131.3 | -0.38 | whole session declared defective |
| 2026-10-19 | s03_recruit | 10:10:19-10:11:01 | NIFTY|OPT|2026-10-19|23150|PE | 122.65 → 122.2 | -0.37 | whole session declared defective |
| 2026-10-19 | s03_recruit | 10:50:52-10:51:20 | NIFTY|OPT|2026-10-19|23100|PE | 107.5 → 103.75 | -3.49 | whole session declared defective |
| 2026-10-19 | s03_recruit | 10:55:22-10:55:54 | NIFTY|OPT|2026-10-19|22950|CE | 128.95 → 125.5 | -2.67 | whole session declared defective |
| 2026-10-19 | s03_recruit | 11:09:50-11:10:15 | NIFTY|OPT|2026-10-19|23000|CE | 102.0 → 113.45 | +11.22 | whole session declared defective |
| 2026-10-19 | s03_recruit | 11:11:23-11:11:54 | NIFTY|OPT|2026-10-19|23000|CE | 110.05 → 105.45 | -4.18 | whole session declared defective |
| 2026-10-19 | s03_recruit | 11:19:52-11:21:30 | NIFTY|OPT|2026-10-19|23150|PE | 101.15 → 106.4 | +5.19 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:30:43-12:31:45 | NIFTY|OPT|2026-10-19|22850|CE | 103.1 → 103.85 | +0.73 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:35:31-12:36:12 | NIFTY|OPT|2026-10-19|23000|PE | 96.5 → 95.15 | -1.40 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:40:59-12:43:24 | NIFTY|OPT|2026-10-19|23000|PE | 104.3 → 95.3 | -8.63 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:53:11-12:53:38 | NIFTY|OPT|2026-10-19|23000|PE | 105.35 → 102.15 | -3.04 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:55:20-12:55:52 | NIFTY|OPT|2026-10-19|22950|PE | 80.9 → 78.7 | -2.72 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:57:08-12:57:34 | NIFTY|OPT|2026-10-19|22950|PE | 83.05 → 77.1 | -7.16 | whole session declared defective |
| 2026-10-19 | s03_recruit | 12:59:09-12:59:36 | NIFTY|OPT|2026-10-19|22950|PE | 78.45 → 75.8 | -3.38 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:04:41-13:05:32 | NIFTY|OPT|2026-10-19|23000|PE | 89.35 → 98.3 | +10.02 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:06:49-13:07:27 | NIFTY|OPT|2026-10-19|22850|CE | 93.55 → 101.85 | +8.87 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:09:23-13:09:59 | NIFTY|OPT|2026-10-19|23000|PE | 101.8 → 102.5 | +0.69 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:11:16-13:11:43 | NIFTY|OPT|2026-10-19|22850|CE | 84.25 → 83.0 | -1.48 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:17:17-13:17:40 | NIFTY|OPT|2026-10-19|22950|PE | 75.35 → 73.0 | -3.12 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:22:23-13:22:50 | NIFTY|OPT|2026-10-19|22950|PE | 86.65 → 94.4 | +8.94 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:27:16-13:27:46 | NIFTY|OPT|2026-10-19|22950|PE | 105.9 → 112.25 | +6.00 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:28:50-13:29:03 | NIFTY|OPT|2026-10-19|22900|PE | 73.65 → 73.55 | -0.14 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:34:03-13:34:33 | NIFTY|OPT|2026-10-19|22800|CE | 81.5 → 81.55 | +0.06 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:35:59-13:36:21 | NIFTY|OPT|2026-10-19|22950|PE | 106.45 → 102.25 | -3.95 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:38:00-13:38:13 | NIFTY|OPT|2026-10-19|22800|CE | 90.9 → 87.25 | -4.01 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:41:03-13:41:07 | NIFTY|OPT|2026-10-19|22800|CE | 88.6 → 85.4 | -3.61 | whole session declared defective |
| 2026-10-19 | s03_recruit | 13:53:14-13:53:42 | NIFTY|OPT|2026-10-19|22950|PE | 100.25 → 97.25 | -2.99 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:02:17-14:02:46 | NIFTY|OPT|2026-10-19|22800|CE | 86.7 → 92.1 | +6.23 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:05:06-14:06:13 | NIFTY|OPT|2026-10-19|22800|CE | 98.5 → 101.05 | +2.59 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:08:11-14:08:22 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 82.7 | +1.97 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:12:07-14:12:40 | NIFTY|OPT|2026-10-19|22950|PE | 93.55 → 96.0 | +2.62 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:18:15-14:18:24 | NIFTY|OPT|2026-10-19|22900|PE | 60.75 → 59.35 | -2.31 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:19:31-14:19:47 | NIFTY|OPT|2026-10-19|22800|CE | 79.15 → 74.2 | -6.25 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:24:54-14:25:14 | NIFTY|OPT|2026-10-19|22900|PE | 68.3 → 71.65 | +4.91 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:30:23-14:31:09 | NIFTY|OPT|2026-10-19|22900|PE | 68.85 → 67.6 | -1.82 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:34:04-14:34:36 | NIFTY|OPT|2026-10-19|22900|PE | 59.4 → 60.0 | +1.01 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:36:06-14:36:16 | NIFTY|OPT|2026-10-19|22800|CE | 70.4 → 67.2 | -4.54 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:40:13-14:40:28 | NIFTY|OPT|2026-10-19|22900|PE | 65.45 → 61.75 | -5.65 | whole session declared defective |
| 2026-10-19 | s03_recruit | 14:44:08-14:44:18 | NIFTY|OPT|2026-10-19|22950|PE | 88.05 → 86.2 | -2.10 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 14:24:45-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.5 | -6.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12 | 14:43:21-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 89.9 | +18.76 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_1130 | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_1130 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_1130 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_1130 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_1130 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:27:02-09:27:18 | NIFTY|OPT|2026-10-19|23100|PE | 139.8 → 151.4 | +8.30 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:28:50-09:29:20 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 127.75 | -3.04 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:36:03-09:36:36 | NIFTY|OPT|2026-10-19|23050|CE | 126.7 → 112.75 | -11.01 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:37:04-09:37:43 | NIFTY|OPT|2026-10-19|23050|CE | 129.5 → 141.7 | +9.42 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:52:09-09:52:29 | NIFTY|OPT|2026-10-19|23200|PE | 125.95 → 113.7 | -9.73 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:55:01-09:57:50 | NIFTY|OPT|2026-10-19|23200|PE | 131.4 → 155.7 | +18.49 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 09:58:47-09:59:24 | NIFTY|OPT|2026-10-19|23150|PE | 137.65 → 144.35 | +4.87 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 10:19:45-10:24:28 | NIFTY|OPT|2026-10-19|23000|CE | 111.85 → 119.7 | +7.02 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 10:30:03-10:30:34 | NIFTY|OPT|2026-10-19|23000|CE | 138.9 → 134.15 | -3.42 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 10:34:13-10:38:01 | NIFTY|OPT|2026-10-19|23150|PE | 108.05 → 107.7 | -0.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 10:39:04-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 123.85 → 145.8 | +17.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 10:52:27-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.05 → 123.65 | -2.68 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 11:08:53-11:12:28 | NIFTY|OPT|2026-10-19|23000|CE | 99.9 → 98.8 | -1.10 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 11:24:53-11:36:16 | NIFTY|OPT|2026-10-19|23150|PE | 115.5 → 146.25 | +26.62 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 11:37:52-11:41:04 | NIFTY|OPT|2026-10-19|23100|PE | 119.3 → 130.8 | +9.64 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 11:58:27-11:59:06 | NIFTY|OPT|2026-10-19|23050|PE | 111.8 → 101.65 | -9.08 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:04:02-12:05:53 | NIFTY|OPT|2026-10-19|23050|PE | 113.05 → 122.35 | +8.23 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:15:40-12:17:06 | NIFTY|OPT|2026-10-19|23000|PE | 102.5 → 102.7 | +0.20 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:23:24-12:24:54 | NIFTY|OPT|2026-10-19|23000|PE | 114.9 → 101.65 | -11.53 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:26:37-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 107.0 → 102.65 | -4.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:40:39-12:42:40 | NIFTY|OPT|2026-10-19|23000|PE | 101.65 → 100.65 | -0.98 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 12:46:34-12:57:54 | NIFTY|OPT|2026-10-19|23000|PE | 107.65 → 110.4 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:03:14-13:04:37 | NIFTY|OPT|2026-10-19|22850|CE | 96.7 → 103.2 | +6.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:12:33-13:20:54 | NIFTY|OPT|2026-10-19|22950|PE | 76.0 → 85.2 | +12.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:22:49-13:25:52 | NIFTY|OPT|2026-10-19|22950|PE | 95.0 → 101.75 | +7.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:29:57-13:30:30 | NIFTY|OPT|2026-10-19|22900|PE | 78.3 → 71.0 | -9.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:36:28-13:42:46 | NIFTY|OPT|2026-10-19|22800|CE | 91.1 → 89.2 | -2.09 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 13:44:34-13:47:53 | NIFTY|OPT|2026-10-19|22900|PE | 70.15 → 67.55 | -3.71 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 14:02:20-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 90.55 → 96.75 | +6.85 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 14:15:11-14:22:42 | NIFTY|OPT|2026-10-19|22900|PE | 63.4 → 61.55 | -2.92 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 14:24:37-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 68.55 → 63.5 | -7.37 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first | 14:43:07-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 76.7 → 89.9 | +17.21 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:27:02-09:27:18 | NIFTY|OPT|2026-10-19|23100|PE | 139.8 → 151.4 | +8.30 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:28:50-09:29:20 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 127.75 | -3.04 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:36:03-09:36:36 | NIFTY|OPT|2026-10-19|23050|CE | 126.7 → 112.75 | -11.01 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:37:04-09:37:43 | NIFTY|OPT|2026-10-19|23050|CE | 129.5 → 141.7 | +9.42 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:52:09-09:52:29 | NIFTY|OPT|2026-10-19|23200|PE | 125.95 → 113.7 | -9.73 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:55:01-09:57:50 | NIFTY|OPT|2026-10-19|23200|PE | 131.4 → 155.7 | +18.49 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 09:58:47-09:59:24 | NIFTY|OPT|2026-10-19|23150|PE | 137.65 → 144.35 | +4.87 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 10:19:45-10:24:28 | NIFTY|OPT|2026-10-19|23000|CE | 111.85 → 119.7 | +7.02 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 10:30:03-10:30:34 | NIFTY|OPT|2026-10-19|23000|CE | 138.9 → 134.15 | -3.42 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 10:34:13-10:38:01 | NIFTY|OPT|2026-10-19|23150|PE | 108.05 → 107.7 | -0.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 10:39:04-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 123.85 → 145.8 | +17.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 10:52:27-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.05 → 123.65 | -2.68 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 11:08:53-11:12:28 | NIFTY|OPT|2026-10-19|23000|CE | 99.9 → 98.8 | -1.10 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 11:24:53-11:36:16 | NIFTY|OPT|2026-10-19|23150|PE | 115.5 → 146.25 | +26.62 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 11:37:52-11:41:04 | NIFTY|OPT|2026-10-19|23100|PE | 119.3 → 130.8 | +9.64 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 11:58:27-11:59:06 | NIFTY|OPT|2026-10-19|23050|PE | 111.8 → 101.65 | -9.08 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:04:02-12:05:53 | NIFTY|OPT|2026-10-19|23050|PE | 113.05 → 122.35 | +8.23 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:15:40-12:17:06 | NIFTY|OPT|2026-10-19|23000|PE | 102.5 → 102.7 | +0.20 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:23:24-12:24:54 | NIFTY|OPT|2026-10-19|23000|PE | 114.9 → 101.65 | -11.53 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:26:37-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 107.0 → 102.65 | -4.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:40:39-12:42:40 | NIFTY|OPT|2026-10-19|23000|PE | 101.65 → 100.65 | -0.98 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 12:46:34-12:57:54 | NIFTY|OPT|2026-10-19|23000|PE | 107.65 → 110.4 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:03:14-13:04:37 | NIFTY|OPT|2026-10-19|22850|CE | 96.7 → 103.2 | +6.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:12:33-13:20:54 | NIFTY|OPT|2026-10-19|22950|PE | 76.0 → 85.2 | +12.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:22:49-13:25:52 | NIFTY|OPT|2026-10-19|22950|PE | 95.0 → 101.75 | +7.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:29:57-13:30:30 | NIFTY|OPT|2026-10-19|22900|PE | 78.3 → 71.0 | -9.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:36:28-13:42:46 | NIFTY|OPT|2026-10-19|22800|CE | 91.1 → 89.2 | -2.09 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 13:44:34-13:47:53 | NIFTY|OPT|2026-10-19|22900|PE | 70.15 → 67.55 | -3.71 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 14:02:20-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 90.55 → 96.75 | +6.85 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 14:15:11-14:22:42 | NIFTY|OPT|2026-10-19|22900|PE | 63.4 → 61.55 | -2.92 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 14:24:37-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 68.55 → 63.5 | -7.37 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r002 | 14:43:07-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 76.7 → 89.9 | +17.21 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:27:02-09:27:18 | NIFTY|OPT|2026-10-19|23100|PE | 139.8 → 151.4 | +8.30 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:28:50-09:29:20 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 127.75 | -3.04 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:36:03-09:36:36 | NIFTY|OPT|2026-10-19|23050|CE | 126.7 → 112.75 | -11.01 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:37:04-09:37:43 | NIFTY|OPT|2026-10-19|23050|CE | 129.5 → 141.7 | +9.42 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:52:09-09:52:29 | NIFTY|OPT|2026-10-19|23200|PE | 125.95 → 113.7 | -9.73 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:55:01-09:57:50 | NIFTY|OPT|2026-10-19|23200|PE | 131.4 → 155.7 | +18.49 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 09:58:47-09:59:24 | NIFTY|OPT|2026-10-19|23150|PE | 137.65 → 144.35 | +4.87 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 10:19:53-10:24:28 | NIFTY|OPT|2026-10-19|23000|CE | 110.45 → 119.7 | +8.38 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 10:30:04-10:30:34 | NIFTY|OPT|2026-10-19|23050|CE | 106.05 → 97.95 | -7.64 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 10:34:13-10:38:01 | NIFTY|OPT|2026-10-19|23150|PE | 108.05 → 107.7 | -0.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 10:39:04-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 123.85 → 145.8 | +17.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 10:52:27-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.05 → 123.65 | -2.68 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 11:08:53-11:12:28 | NIFTY|OPT|2026-10-19|23000|CE | 99.9 → 98.8 | -1.10 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 11:24:53-11:36:16 | NIFTY|OPT|2026-10-19|23150|PE | 115.5 → 146.25 | +26.62 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 11:37:52-11:41:04 | NIFTY|OPT|2026-10-19|23100|PE | 119.3 → 130.8 | +9.64 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 11:58:27-11:59:06 | NIFTY|OPT|2026-10-19|23050|PE | 111.8 → 101.65 | -9.08 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:04:02-12:05:53 | NIFTY|OPT|2026-10-19|23050|PE | 113.05 → 122.35 | +8.23 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:15:40-12:17:06 | NIFTY|OPT|2026-10-19|23000|PE | 102.5 → 102.7 | +0.20 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:23:24-12:24:54 | NIFTY|OPT|2026-10-19|23000|PE | 114.9 → 101.65 | -11.53 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:26:37-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 107.0 → 102.65 | -4.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:41:07-12:42:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.65 → 100.65 | -4.73 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 12:50:08-12:57:54 | NIFTY|OPT|2026-10-19|23000|PE | 110.25 → 110.4 | +0.14 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:03:14-13:04:37 | NIFTY|OPT|2026-10-19|22850|CE | 96.7 → 103.2 | +6.72 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:12:33-13:20:54 | NIFTY|OPT|2026-10-19|22950|PE | 76.0 → 85.2 | +12.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:22:49-13:25:52 | NIFTY|OPT|2026-10-19|22950|PE | 95.0 → 101.75 | +7.11 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:29:57-13:30:30 | NIFTY|OPT|2026-10-19|22900|PE | 78.3 → 71.0 | -9.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:36:28-13:42:46 | NIFTY|OPT|2026-10-19|22800|CE | 91.1 → 89.2 | -2.09 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 13:44:43-13:47:53 | NIFTY|OPT|2026-10-19|22900|PE | 70.0 → 67.55 | -3.50 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 14:02:20-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 90.55 → 96.75 | +6.85 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 14:15:18-14:22:42 | NIFTY|OPT|2026-10-19|22900|PE | 65.0 → 61.55 | -5.31 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 14:24:38-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 68.95 → 63.5 | -7.90 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_first_r003 | 14:43:07-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 76.7 → 89.9 | +17.21 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 11:31:13-11:36:16 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.9 | +20.45 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 14:04:21-14:06:51 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 92.6 | +4.63 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 14:24:45-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.5 | -6.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_nolock | 14:43:21-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 89.9 | +18.76 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 14:24:45-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.5 | -6.34 | whole session declared defective |
| 2026-10-19 | spot_dc12_t12_r002 | 14:43:21-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 89.9 | +18.76 | whole session declared defective |
| 2026-10-19 | spot_dual | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dual | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dual | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dual | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dual | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dual | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | spot_dual | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dual | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dual | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dual | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dual | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dual | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dual | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dual | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dual | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | spot_dual | 14:24:45-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.5 | -6.34 | whole session declared defective |
| 2026-10-19 | spot_dual | 14:43:21-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 89.9 | +18.76 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | spot_dual_lvl | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 09:27:47-09:29:20 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 163.85 | +20.70 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 14:24:45-14:29:17 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.5 | -6.34 | whole session declared defective |
| 2026-10-19 | spot_dual_rg | 14:43:21-14:44:56 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 89.9 | +18.76 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:27:02-09:27:10 | NIFTY|OPT|2026-10-19|23100|PE | 139.8 → 155.75 | +11.41 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:27:13-09:27:46 | NIFTY|OPT|2026-10-19|23100|PE | 159.6 → 143.0 | -10.40 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:28:50-09:31:12 | NIFTY|OPT|2026-10-19|23050|PE | 131.75 → 114.0 | -13.47 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:36:03-09:36:36 | NIFTY|OPT|2026-10-19|23050|CE | 126.7 → 113.6 | -10.34 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:37:04-09:37:28 | NIFTY|OPT|2026-10-19|23050|CE | 129.5 → 142.95 | +10.39 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:37:28-09:39:02 | NIFTY|OPT|2026-10-19|23050|CE | 141.25 → 125.55 | -11.12 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:52:09-09:52:30 | NIFTY|OPT|2026-10-19|23200|PE | 125.95 → 111.6 | -11.39 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:55:01-09:55:54 | NIFTY|OPT|2026-10-19|23200|PE | 131.4 → 146.0 | +11.11 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:55:55-09:57:00 | NIFTY|OPT|2026-10-19|23200|PE | 145.6 → 161.95 | +11.23 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:57:00-09:58:48 | NIFTY|OPT|2026-10-19|23150|PE | 123.8 → 137.8 | +11.31 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 09:58:55-10:00:44 | NIFTY|OPT|2026-10-19|23150|PE | 145.35 → 128.9 | -11.32 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:19:45-10:23:30 | NIFTY|OPT|2026-10-19|23000|CE | 111.85 → 124.05 | +10.91 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:23:37-10:25:26 | NIFTY|OPT|2026-10-19|23000|CE | 125.55 → 113.2 | -9.84 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:30:03-10:31:37 | NIFTY|OPT|2026-10-19|23000|CE | 138.9 → 124.25 | -10.55 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:34:13-10:36:42 | NIFTY|OPT|2026-10-19|23150|PE | 108.05 → 119.05 | +10.18 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:36:49-10:38:01 | NIFTY|OPT|2026-10-19|23150|PE | 120.15 → 107.15 | -10.82 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:39:04-10:40:28 | NIFTY|OPT|2026-10-19|23150|PE | 123.85 → 137.05 | +10.66 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:40:31-10:41:07 | NIFTY|OPT|2026-10-19|23100|PE | 104.7 → 113.4 | +8.31 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:41:41-10:42:16 | NIFTY|OPT|2026-10-19|23100|PE | 120.95 → 109.65 | -9.34 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 10:52:27-11:09:42 | NIFTY|OPT|2026-10-19|22950|CE | 127.05 → 139.5 | +9.80 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:09:47-11:16:06 | NIFTY|OPT|2026-10-19|23000|CE | 103.65 → 93.05 | -10.23 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:24:53-11:30:23 | NIFTY|OPT|2026-10-19|23150|PE | 115.5 → 129.45 | +12.08 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:30:25-11:33:22 | NIFTY|OPT|2026-10-19|23150|PE | 127.75 → 142.75 | +11.74 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:33:23-11:35:08 | NIFTY|OPT|2026-10-19|23100|PE | 103.45 → 118.0 | +14.06 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:35:09-11:38:31 | NIFTY|OPT|2026-10-19|23100|PE | 118.25 → 131.8 | +11.46 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:38:33-11:39:12 | NIFTY|OPT|2026-10-19|23050|PE | 94.75 → 106.25 | +12.14 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:39:13-11:41:04 | NIFTY|OPT|2026-10-19|23050|PE | 106.25 → 94.35 | -11.20 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 11:58:27-11:59:17 | NIFTY|OPT|2026-10-19|23050|PE | 111.8 → 99.8 | -10.73 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:04:02-12:04:15 | NIFTY|OPT|2026-10-19|23050|PE | 113.05 → 132.9 | +17.56 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:05:22-12:05:54 | NIFTY|OPT|2026-10-19|23000|PE | 101.05 → 85.5 | -15.39 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:15:40-12:16:13 | NIFTY|OPT|2026-10-19|23000|PE | 102.5 → 113.95 | +11.17 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:23:24-12:24:53 | NIFTY|OPT|2026-10-19|23000|PE | 114.9 → 102.7 | -10.62 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:26:37-12:40:52 | NIFTY|OPT|2026-10-19|22850|CE | 107.0 → 95.45 | -10.79 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:40:56-12:54:18 | NIFTY|OPT|2026-10-19|23000|PE | 102.5 → 112.2 | +9.46 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 12:54:19-13:02:37 | NIFTY|OPT|2026-10-19|23000|PE | 112.8 → 102.8 | -8.87 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:03:14-13:03:32 | NIFTY|OPT|2026-10-19|22850|CE | 96.7 → 105.8 | +9.41 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:03:34-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 107.35 → 93.8 | -12.62 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:12:33-13:13:07 | NIFTY|OPT|2026-10-19|22950|PE | 76.0 → 68.05 | -10.46 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:17:54-13:19:51 | NIFTY|OPT|2026-10-19|22950|PE | 80.95 → 89.8 | +10.93 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:19:52-13:21:22 | NIFTY|OPT|2026-10-19|22950|PE | 91.8 → 82.05 | -10.62 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:22:49-13:23:31 | NIFTY|OPT|2026-10-19|22950|PE | 95.0 → 105.6 | +11.16 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:23:43-13:30:01 | NIFTY|OPT|2026-10-19|22950|PE | 106.65 → 117.9 | +10.55 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:30:02-13:30:44 | NIFTY|OPT|2026-10-19|22900|PE | 77.55 → 69.65 | -10.19 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:36:28-13:41:33 | NIFTY|OPT|2026-10-19|22800|CE | 91.1 → 101.25 | +11.14 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:41:35-13:42:45 | NIFTY|OPT|2026-10-19|22800|CE | 99.8 → 89.85 | -9.97 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 13:44:34-13:49:03 | NIFTY|OPT|2026-10-19|22900|PE | 70.15 → 62.0 | -11.62 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:02:20-14:03:12 | NIFTY|OPT|2026-10-19|22800|CE | 90.55 → 101.6 | +12.20 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:05:38-14:06:31 | NIFTY|OPT|2026-10-19|22850|CE | 65.7 → 58.8 | -10.50 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:15:11-14:16:09 | NIFTY|OPT|2026-10-19|22900|PE | 63.4 → 56.45 | -10.96 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:18:03-14:19:29 | NIFTY|OPT|2026-10-19|22900|PE | 62.9 → 56.0 | -10.97 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:24:37-14:31:19 | NIFTY|OPT|2026-10-19|22900|PE | 68.55 → 60.05 | -12.40 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:43:07-14:43:29 | NIFTY|OPT|2026-10-19|22800|CE | 76.7 → 84.55 | +10.23 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:43:30-14:43:42 | NIFTY|OPT|2026-10-19|22800|CE | 85.45 → 76.65 | -10.30 | whole session declared defective |
| 2026-10-19 | spot_ft_prem10 | 14:44:29-14:44:46 | NIFTY|OPT|2026-10-19|22800|CE | 89.5 → 99.85 | +11.56 | whole session declared defective |
| 2026-10-19 | spot_orb45 | 12:04:14-12:55:19 | NIFTY|OPT|2026-10-19|23050|PE | 133.55 → 159.65 | +19.54 | whole session declared defective |
| 2026-10-19 | spot_orb45_r002 | 12:04:14-12:55:19 | NIFTY|OPT|2026-10-19|23050|PE | 133.55 → 159.65 | +19.54 | whole session declared defective |
| 2026-10-19 | spot_orb45_r003 | 12:04:14-12:55:19 | NIFTY|OPT|2026-10-19|23050|PE | 133.55 → 159.65 | +19.54 | whole session declared defective |
| 2026-10-19 | spot_orb45_r005 | 12:04:14-12:55:19 | NIFTY|OPT|2026-10-19|23050|PE | 133.55 → 159.65 | +19.54 | whole session declared defective |
| 2026-10-19 | spot_pb45 | 09:25:00-09:25:46 | NIFTY|OPT|2026-10-19|23000|CE | 125.65 → 106.65 | -15.12 | whole session declared defective |
| 2026-10-19 | spot_pb45 | 09:33:05-10:00:25 | NIFTY|OPT|2026-10-19|23150|PE | 128.05 → 138.2 | +7.93 | whole session declared defective |
| 2026-10-19 | spot_pb45 | 10:04:46-10:25:03 | NIFTY|OPT|2026-10-19|22950|CE | 143.15 → 155.05 | +8.31 | whole session declared defective |
| 2026-10-19 | spot_pb45 | 11:09:48-11:41:04 | NIFTY|OPT|2026-10-19|23150|PE | 105.3 → 172.5 | +63.82 | whole session declared defective |
| 2026-10-19 | spot_pb45 | 14:02:24-14:16:11 | NIFTY|OPT|2026-10-19|22950|PE | 84.05 → 94.0 | +11.84 | whole session declared defective |
| 2026-10-19 | spot_pb45_r002 | 09:25:00-09:25:46 | NIFTY|OPT|2026-10-19|23000|CE | 125.65 → 106.65 | -15.12 | whole session declared defective |
| 2026-10-19 | spot_pb45_r002 | 09:33:05-10:00:25 | NIFTY|OPT|2026-10-19|23150|PE | 128.05 → 138.2 | +7.93 | whole session declared defective |
| 2026-10-19 | spot_pb45_r002 | 10:04:46-10:25:03 | NIFTY|OPT|2026-10-19|22950|CE | 143.15 → 155.05 | +8.31 | whole session declared defective |
| 2026-10-19 | spot_pb45_r002 | 11:09:48-11:41:04 | NIFTY|OPT|2026-10-19|23150|PE | 105.3 → 172.5 | +63.82 | whole session declared defective |
| 2026-10-19 | spot_pb45_r002 | 14:02:24-14:16:11 | NIFTY|OPT|2026-10-19|22950|PE | 84.05 → 94.0 | +11.84 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:25:11-09:26:36 | NIFTY|OPT|2026-10-19|23150|PE | 101.4 → 165.6 | +63.31 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:55:06-09:57:50 | NIFTY|OPT|2026-10-19|23150|PE | 99.75 → 120.5 | +20.80 | whole session declared defective |
| 2026-10-19 | straddle_spike | 10:30:07-10:30:36 | NIFTY|OPT|2026-10-19|23050|CE | 104.95 → 96.8 | -7.77 | whole session declared defective |
| 2026-10-19 | straddle_spike | 10:40:27-10:42:15 | NIFTY|OPT|2026-10-19|23050|PE | 71.9 → 79.25 | +10.22 | whole session declared defective |
| 2026-10-19 | straddle_spike | 10:49:20-10:52:15 | NIFTY|OPT|2026-10-19|23050|PE | 76.7 → 65.05 | -15.19 | whole session declared defective |
| 2026-10-19 | straddle_spike | 11:10:16-11:13:49 | NIFTY|OPT|2026-10-19|23050|CE | 77.6 → 67.2 | -13.40 | whole session declared defective |
| 2026-10-19 | straddle_spike | 11:33:31-11:35:57 | NIFTY|OPT|2026-10-19|23050|PE | 68.35 → 74.6 | +9.14 | whole session declared defective |
| 2026-10-19 | straddle_spike | 12:41:34-12:43:16 | NIFTY|OPT|2026-10-19|22950|PE | 74.85 → 64.05 | -14.43 | whole session declared defective |
| 2026-10-19 | straddle_spike | 12:57:23-12:57:59 | NIFTY|OPT|2026-10-19|22950|PE | 78.6 → 73.2 | -6.87 | whole session declared defective |
| 2026-10-19 | straddle_spike | 13:03:54-13:04:44 | NIFTY|OPT|2026-10-19|22900|CE | 68.1 → 66.1 | -2.94 | whole session declared defective |
| 2026-10-19 | straddle_spike | 13:23:08-13:26:47 | NIFTY|OPT|2026-10-19|22900|PE | 68.15 → 62.95 | -7.63 | whole session declared defective |
| 2026-10-19 | straddle_spike | 14:03:29-14:09:42 | NIFTY|OPT|2026-10-19|22850|CE | 62.1 → 49.35 | -20.53 | whole session declared defective |
| 2026-10-19 | straddle_spike | 14:44:39-14:45:50 | NIFTY|OPT|2026-10-19|22850|CE | 53.2 → 43.75 | -17.76 | whole session declared defective |
| 2026-10-19 | t28_all | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_all | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_all | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_all | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_all | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_all | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_all | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_all | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_all | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_all | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_all | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_all | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_all | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_all | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_all | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_all | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_all | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_all | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_bidpile | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_cheap | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_cheap | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_cheap | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_cheap | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_cheap | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_cheap | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_cheap | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_cheap | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_cheap | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_cheap | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_cheap | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_cheap | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_cheap | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_cheap | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_cheap | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_cheap | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23050|PE | 104.75 → 115.8 | +10.55 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23000|PE | 94.3 → 101.2 | +7.32 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23100|PE | 76.15 → 109.35 | +43.60 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 10:57:02-11:01:27 | NIFTY|OPT|2026-10-19|23000|CE | 92.0 → 88.1 | -4.24 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 11:13:53-11:17:35 | NIFTY|OPT|2026-10-19|23050|CE | 66.5 → 67.75 | +1.88 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 11:31:14-11:35:50 | NIFTY|OPT|2026-10-19|23050|PE | 58.75 → 76.4 | +30.04 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 12:08:02-12:17:03 | NIFTY|OPT|2026-10-19|23000|PE | 75.45 → 102.35 | +35.65 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 12:42:02-12:43:01 | NIFTY|OPT|2026-10-19|22950|PE | 67.65 → 66.3 | -2.00 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22900|CE | 64.5 → 59.85 | -7.21 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22950|PE | 109.3 → 101.75 | -6.91 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_cheapK | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22750|CE | 120.45 → 137.75 | +14.36 | whole session declared defective |
| 2026-10-19 | t28_core | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_core | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_core | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_core | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_core | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_core | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_core | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_core | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_core | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_core | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_core | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_core | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_core | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_core | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_core | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_core | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_core | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_core | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_core_fill | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_d46 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_d46 | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_d46 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_d46 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_d46 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_d46 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_d46 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_d46 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_d46 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_d46 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_d46 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_d46 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_d46 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_d46 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_d46 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_d46 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_d46 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_d46 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_d46_fill | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_dur20 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_fill | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_fill | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_fill | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_fill | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_fill | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_fill | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_fill | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_fill | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_fill | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_fill | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_fill | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_fill | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_fill | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_fill | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_fill | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_fill | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_fill | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_fill | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_fwd | 09:29:22-09:29:57 | NIFTY|OPT|2026-10-19|23100|PE | 160.1 → 166.25 | +3.84 | whole session declared defective |
| 2026-10-19 | t28_fwd | 09:36:23-09:36:40 | NIFTY|OPT|2026-10-19|23000|CE | 154.65 → 146.2 | -5.46 | whole session declared defective |
| 2026-10-19 | t28_fwd | 09:38:59-09:39:12 | NIFTY|OPT|2026-10-19|23050|CE | 127.2 → 116.65 | -8.29 | whole session declared defective |
| 2026-10-19 | t28_fwd | 09:52:14-09:52:29 | NIFTY|OPT|2026-10-19|23200|PE | 122.4 → 113.7 | -7.11 | whole session declared defective |
| 2026-10-19 | t28_fwd | 09:55:23-09:57:38 | NIFTY|OPT|2026-10-19|23150|PE | 94.5 → 123.95 | +31.16 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:00:42-10:00:55 | NIFTY|OPT|2026-10-19|23100|PE | 99.25 → 94.05 | -5.24 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:20:25-10:20:46 | NIFTY|OPT|2026-10-19|23000|CE | 112.65 → 104.2 | -7.50 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:23:15-10:24:17 | NIFTY|OPT|2026-10-19|23050|CE | 82.95 → 87.8 | +5.85 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:38:05-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.0 → 145.8 | +36.26 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:52:47-10:54:45 | NIFTY|OPT|2026-10-19|22950|CE | 124.15 → 120.15 | -3.22 | whole session declared defective |
| 2026-10-19 | t28_fwd | 10:56:32-11:00:23 | NIFTY|OPT|2026-10-19|23000|CE | 94.55 → 91.25 | -3.49 | whole session declared defective |
| 2026-10-19 | t28_fwd | 11:10:50-11:12:28 | NIFTY|OPT|2026-10-19|23050|CE | 69.8 → 67.3 | -3.58 | whole session declared defective |
| 2026-10-19 | t28_fwd | 11:30:57-11:35:51 | NIFTY|OPT|2026-10-19|23100|PE | 90.65 → 108.95 | +20.19 | whole session declared defective |
| 2026-10-19 | t28_fwd | 11:58:41-11:59:15 | NIFTY|OPT|2026-10-19|23000|PE | 75.6 → 67.75 | -10.38 | whole session declared defective |
| 2026-10-19 | t28_fwd | 12:08:03-12:16:58 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 143.0 | +29.30 | whole session declared defective |
| 2026-10-19 | t28_fwd | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 107.65 → 102.65 | -4.64 | whole session declared defective |
| 2026-10-19 | t28_fwd | 12:41:55-12:42:54 | NIFTY|OPT|2026-10-19|23000|PE | 102.95 → 95.8 | -6.95 | whole session declared defective |
| 2026-10-19 | t28_fwd | 12:54:32-12:57:51 | NIFTY|OPT|2026-10-19|22950|PE | 73.7 → 74.0 | +0.41 | whole session declared defective |
| 2026-10-19 | t28_fwd | 13:05:29-13:06:24 | NIFTY|OPT|2026-10-19|22850|CE | 93.75 → 85.55 | -8.75 | whole session declared defective |
| 2026-10-19 | t28_fwd | 14:15:46-14:23:25 | NIFTY|OPT|2026-10-19|22900|PE | 59.15 → 58.55 | -1.01 | whole session declared defective |
| 2026-10-19 | t28_fwd | 14:43:17-14:44:58 | NIFTY|OPT|2026-10-19|22800|CE | 77.15 → 90.9 | +17.82 | whole session declared defective |
| 2026-10-19 | t28_gap | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_gap | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_gap | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_gap | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_gap | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_gap | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_gap | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_gap | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_gap | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_gap | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_gap | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_gap | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_gap | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_gap | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_gap | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_gap | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_gap | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_gap | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_gap_ts | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 11:35:52-11:41:04 | NIFTY|OPT|2026-10-19|23100|PE | 108.55 → 130.8 | +20.50 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23050|PE | 109.0 → 101.75 | -6.65 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 12:17:12-12:18:27 | NIFTY|OPT|2026-10-19|23000|PE | 100.3 → 95.8 | -4.49 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|22950|PE | 67.65 → 66.3 | -2.00 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 14:06:31-14:08:36 | NIFTY|OPT|2026-10-19|22850|CE | 59.1 → 55.05 | -6.85 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_ivfall | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_mh15 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_nohigh | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_req | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_req | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_req | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_req | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_req | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_req | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_req | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_req | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_req | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_req | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_req | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_req | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_req | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_req | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_req | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_req | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_req | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_req | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_st20 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_st20 | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_st20 | 09:36:30-09:38:51 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 170.05 | +9.78 | whole session declared defective |
| 2026-10-19 | t28_st20 | 10:38:01-10:42:17 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 144.05 | +34.44 | whole session declared defective |
| 2026-10-19 | t28_st20 | 10:57:02-11:07:02 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 131.0 | +2.46 | whole session declared defective |
| 2026-10-19 | t28_st20 | 11:13:54-11:23:54 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 97.5 | -0.36 | whole session declared defective |
| 2026-10-19 | t28_st20 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_st20 | 11:58:45-11:59:15 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 67.75 | -10.03 | whole session declared defective |
| 2026-10-19 | t28_st20 | 12:08:03-12:17:15 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 134.75 | +21.84 | whole session declared defective |
| 2026-10-19 | t28_st20 | 12:27:35-12:29:45 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 100.85 | -5.66 | whole session declared defective |
| 2026-10-19 | t28_st20 | 12:42:01-12:49:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 102.8 | +1.18 | whole session declared defective |
| 2026-10-19 | t28_st20 | 13:04:50-13:06:03 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 88.2 | -11.58 | whole session declared defective |
| 2026-10-19 | t28_st20 | 13:24:58-13:25:54 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 64.6 | -10.90 | whole session declared defective |
| 2026-10-19 | t28_st20 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.7 | -10.65 | whole session declared defective |
| 2026-10-19 | t28_st20 | 13:49:03-13:59:03 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 97.3 | -1.37 | whole session declared defective |
| 2026-10-19 | t28_st20 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_st20 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_st20 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_ts | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_ts | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_ts | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_ts | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_ts | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_ts | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_ts | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_ts | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_ts | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_ts | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_ts | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_ts | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_ts | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_ts | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_ts | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_ts | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_ts | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_ts | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 09:27:47-09:28:22 | NIFTY|OPT|2026-10-19|23100|PE | 135.75 → 151.35 | +11.49 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 09:29:30-09:29:53 | NIFTY|OPT|2026-10-19|23050|PE | 124.5 → 132.7 | +6.59 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 09:36:30-09:37:43 | NIFTY|OPT|2026-10-19|23000|CE | 154.9 → 180.05 | +16.24 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 10:38:01-10:42:12 | NIFTY|OPT|2026-10-19|23150|PE | 107.15 → 145.8 | +36.07 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 10:57:02-11:01:26 | NIFTY|OPT|2026-10-19|22950|CE | 127.85 → 123.65 | -3.29 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 11:13:54-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 97.85 → 100.35 | +2.56 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 11:31:13-11:35:56 | NIFTY|OPT|2026-10-19|23100|PE | 88.75 → 106.85 | +20.39 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 11:58:45-11:59:13 | NIFTY|OPT|2026-10-19|23000|PE | 75.3 → 69.0 | -8.37 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 12:08:03-12:17:05 | NIFTY|OPT|2026-10-19|23050|PE | 110.6 → 141.95 | +28.34 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 12:27:35-12:28:25 | NIFTY|OPT|2026-10-19|22850|CE | 106.9 → 102.65 | -3.98 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 12:42:01-12:43:01 | NIFTY|OPT|2026-10-19|23000|PE | 101.6 → 98.9 | -2.66 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 13:04:50-13:05:28 | NIFTY|OPT|2026-10-19|22850|CE | 99.75 → 93.8 | -5.96 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 13:24:58-13:25:52 | NIFTY|OPT|2026-10-19|22900|PE | 72.5 → 65.65 | -9.45 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 13:42:46-13:44:25 | NIFTY|OPT|2026-10-19|22800|CE | 89.2 → 79.85 | -10.48 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 13:49:03-13:52:01 | NIFTY|OPT|2026-10-19|22950|PE | 98.65 → 99.85 | +1.22 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 14:04:21-14:06:31 | NIFTY|OPT|2026-10-19|22800|CE | 88.5 → 96.75 | +9.32 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 14:24:45-14:29:16 | NIFTY|OPT|2026-10-19|22900|PE | 67.8 → 63.65 | -6.12 | whole session declared defective |
| 2026-10-19 | t28_tt8 | 14:43:21-14:44:53 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 92.45 | +22.13 | whole session declared defective |

Per book: RAW 16, apex_edge 3, c20_8x 15, c20_9e 26, c20_9h 18, c20_9s 16, c20_9t 19, c20_9v 16, c20_9x 16, c20_9x_r002 16, c20_9x_r004 16, c20_9y 14, edge_bracket_only 17, edge_breakout 3, edge_gate_only 3, edge_gate_trail 3, fade_switch 55, fade_switch_r002 55, fr_c20_9y 14, futures_only 18, fx_c20_9y 21, lvl_trail 18, lvl_trail_be 18, lvl_trail_re 18, lvl_trail_rx 17, lvl_trail_rx_be 17, lvl_trail_rx_c10 17, m1.5_s0.4 1, m1.5_s0.4_r002 1, m1.5_s0.4_r003 1, m2.0_s0.4 1, m2.0_s0.5_novol 4, m2.5_s0.4 1, n01_ctl_flow 7, n01_ctl_price 30, n01_ctl_price_ind 30, n01_release 1, n02_ctl_mr 37, n02_relax 6, n06_ctl_breadth 28, n06_lead 2, p02_clock 40, p02_ctl_mom 26, p02_top1 14, p05_adaptive 18, premium_momentum 29, random_entry 6, s01_ctl_cash 14, s01_ctl_sfut 13, s01_transmit 7, s03_recruit 45, spot_dc12_t12 17, spot_dc12_t12_1130 5, spot_dc12_t12_first 32, spot_dc12_t12_first_r002 32, spot_dc12_t12_first_r003 32, spot_dc12_t12_nolock 17, spot_dc12_t12_r002 17, spot_dual 17, spot_dual_lvl 18, spot_dual_rg 17, spot_ft_prem10 54, spot_orb45 1, spot_orb45_r002 1, spot_orb45_r003 1, spot_orb45_r005 1, spot_pb45 5, spot_pb45_r002 5, straddle_spike 13, t28_all 18, t28_bidpile 16, t28_cheap 16, t28_cheapK 18, t28_core 18, t28_core_fill 18, t28_d46 18, t28_d46_fill 18, t28_dur20 18, t28_fill 18, t28_fwd 21, t28_gap 18, t28_gap_ts 18, t28_ivfall 14, t28_mh15 18, t28_nohigh 16, t28_req 18, t28_st20 18, t28_ts 18, t28_tt8 18

## Record-only (config.LEARN_DECIDE = False)
The learning loop does not change books during the Conductor's forward tests. It would have made these changes, none applied: candidate+ premium; candidate+ gex_room.

Champion for the next session: **`conductor`** · gates: none · candidates: none

## Record integrity

- 1 recorded non-trading day(s) carry trades (special session, or sim/test data?): 2026-10-18

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

2758 trades over 2 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 2758 | -0.8 | 0.45 | -0.0558 |
| iv_atm | 2758 | 28.7 | 28.8 | -0.0533 |
| iv_chg5 | 2706 | 0.06 | 0.08 | -0.0816 |
| rv15 | 2758 | 10.8 | 10.8 | 0.00917 |
| iv_rv | 2758 | 1.51 | 1.59 | -0.0932 |
| fut_imb5 | 2758 | -0.057 | -0.111 | 0.125 |
| fut_tot_imb | 2758 | 0.0835 | 0.0155 | 0.0997 |
| wall_up | 2210 | 318 | 279 | 0.0552 |
| wall_dn | 1631 | 249 | 230 | 0.0727 |
| pcr | 2758 | 0.949 | 0.928 | 0.0726 |
| imp_rng | 2758 | 113 | 103 | 0.0241 |
| imp_d | 2758 | -1 | -1 | 0.0186 |
| imp_f | 2758 | 0.33 | 0.235 | 0.178 |
| fut_ofi60 | 2758 | 0.595 | 3.28 | 0.00898 |
| syn_dev | 2758 | 0.4 | -0.07 | 0.00792 |
| fut_micro | 2758 | -0.025 | 0 | -0.0571 |
| v_min30 | 2758 | 85.1 | 77.9 | 0.0562 |
| imp_with | 2758 | 1 | 1 | -0.00427 |
| wall_room | 1922 | 284 | 263 | 0.00154 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
