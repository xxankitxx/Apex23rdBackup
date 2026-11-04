# ApexOptions — learning report (2026-11-03)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `c20_9x`
12 trades since 2026-10-30, Σ -46.3 %. GO line 1013.1, KILL line -545.9 → **COLLECTING**. Observed sd 11.1 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #2 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd 11.1 % (assumed 30 %): GO 152.3, KILL -62.2 → would be **COLLECTING**.
- SPRT on per-trade 100·ln(1+r): Σ -54.8 (mean -4.56/trade) vs GO 1013.1 / KILL -545.9 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **0.86** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (1)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [ ] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0008 each, 65 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | +42.55 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | +44.32 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | +42.09 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | +42.55 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 1 | +44.32 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | +42.09 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | +42.55 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | +44.32 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | +42.09 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | +54.76 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | +54.76 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | +46.84 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | -26.77 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | +44.32 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 1 | +39.52 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 1 | +54.76 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 1 | +8.80 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 1 | -32.51 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 1 | +48.74 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 1 | +9.43 | 0.00 | inf | no | 0 |
| spot_pb45 | 1 | +84.42 | 0.00 | inf | no | 0 |
| spot_dual | 1 | +8.80 | 0.00 | inf | no | 0 |
| spot_dual_rg | 1 | +8.80 | 0.00 | inf | no | 0 |
| spot_dual_lvl | 1 | +9.59 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 1 | +16.78 | 0.00 | inf | no | 0 |
| spot_orb45 | 1 | +66.15 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 1 | +37.42 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 1 | +48.40 | 0.00 | inf | no | 0 |
| fade_switch | 1 | +58.36 | 0.00 | inf | no | 0 |
| apex_edge | 1 | +44.12 | 0.00 | inf | no | 0 |
| edge_gate_only | 1 | +54.95 | 0.00 | inf | no | 0 |
| edge_bracket_only | 1 | -60.81 | 0.00 | inf | no | 0 |
| edge_breakout | 1 | +44.12 | 0.00 | inf | no | 0 |
| edge_gate_trail | 1 | +54.95 | 0.00 | inf | no | 0 |
| lvl_trail | 1 | +10.48 | 0.00 | inf | no | 0 |
| lvl_trail_re | 1 | +44.43 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 1 | +44.43 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 1 | +44.43 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 1 | +44.43 | 0.00 | inf | no | 0 |
| lvl_trail_be | 1 | +10.48 | 0.00 | inf | no | 0 |
| t28_d46 | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_gap | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_dur20 | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_ts | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_fill | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_core | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_core_fill | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_all | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_d46_fill | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_gap_ts | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_ivfall | 1 | +48.21 | 0.00 | inf | no | 0 |
| t28_bidpile | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_st20 | 1 | +20.66 | 0.00 | inf | no | 0 |
| t28_nohigh | 1 | +36.33 | 0.00 | inf | no | 0 |
| t28_req | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_cheap | 1 | +36.33 | 0.00 | inf | no | 0 |
| t28_cheapK | 1 | +54.16 | 0.00 | inf | no | 0 |
| t28_fwd | 1 | +26.62 | 0.00 | inf | no | 0 |
| t28_mh15 | 1 | +44.43 | 0.00 | inf | no | 0 |
| t28_tt8 | 1 | +45.78 | 0.00 | inf | no | 0 |
| c20_8x | 1 | -27.44 | 0.00 | inf | no | 0 |
| c20_9t | 1 | +29.82 | 0.00 | inf | no | 0 |
| c20_9v | 1 | +0.00 | 0.00 | inf | no | 0 |
| c20_9e | 1 | +40.48 | 0.00 | inf | no | 0 |
| c20_9h | 1 | +3.04 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -43.88 | 0.00 | inf | too few days |
| random_entry | 1 | -12.60 | 0.00 | inf | too few days |
| premium_momentum | 1 | +184.41 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| room | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| coherence | 12 | 6 | -3.86 | -1.54 | +2.32 | 50% | no | advisory |
| force | 12 | 1 | -3.86 | -4.74 | -0.88 | 25% | no | advisory |
| episode | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| book | 12 | 3 | -3.86 | -5.91 | -2.05 | 25% | no | advisory |
| premium | 12 | 3 | -3.86 | -2.47 | +1.40 | 25% | no | advisory |
| quiet | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| bank | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| event | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| gamma_leg | 12 | 0 | -3.86 | -3.86 | +0.00 | 0% | no | advisory |
| gex_room | 12 | 1 | -3.86 | -4.26 | -0.40 | 0% | no | advisory |
| regime | 12 | 7 | -3.86 | -3.55 | +0.31 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| c20_9x | BREAKOUT | 1 | -20.21 | 0% |
| c20_9x | DIRECTIONAL | 3 | +4.43 | 67% |
| c20_9x | RANGE | 3 | -7.33 | 33% |
| c20_9x | UNCERTAIN | 4 | -0.99 | 75% |
| c20_9x | WARMING | 1 | -13.48 | 0% |
| RAW | BREAKOUT | 1 | -20.21 | 0% |
| RAW | DIRECTIONAL | 3 | +4.43 | 67% |
| RAW | RANGE | 3 | -7.33 | 33% |
| RAW | UNCERTAIN | 4 | -0.99 | 75% |
| RAW | WARMING | 1 | -13.48 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`c20_9x`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

646 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 646 | 1.25 | 3 | 0.0127 |
| iv_atm | 646 | 27.1 | 28 | -0.395 |
| iv_chg5 | 646 | -0.23 | 0.34 | -0.274 |
| rv15 | 646 | 9.9 | 10.3 | -0.326 |
| iv_rv | 646 | 2.71 | 2.78 | -0.0447 |
| fut_imb5 | 646 | -0.474 | -0.067 | -0.159 |
| fut_tot_imb | 646 | 0.065 | -0.181 | 0.462 |
| wall_up | 445 | 347 | 359 | -0.345 |
| wall_dn | 529 | 64.3 | 33.2 | 0.465 |
| pcr | 646 | 1.09 | 1.13 | -0.197 |
| imp_rng | 646 | 59.8 | 63.6 | -0.193 |
| imp_d | 646 | 1 | 1 | 0.13 |
| imp_f | 646 | 0.149 | 0.299 | -0.158 |
| fut_ofi60 | 646 | 10.4 | 3.6 | -0.0315 |
| syn_dev | 646 | 1.11 | 1.44 | -0.12 |
| fut_micro | 646 | -0.11 | -0.22 | 0.0852 |
| v_min30 | 646 | 36 | 39.2 | -0.345 |
| imp_with | 646 | 1 | -1 | 0.194 |
| wall_room | 516 | 324 | 46.2 | 0.411 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
