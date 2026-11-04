# ApexOptions — learning report (2026-10-19)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `c20_9x`
0 trades since 2026-10-30, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #2 since registration (2026-10-17); evening looks: 0 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
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

## Challengers (daily return vs champion since it took over; one-sided α 0.0008 each, 65 challengers; 2 passing evenings in a row to promote)

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
| c20_9t | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9v | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9e | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9h | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +98.31 | 0.00 | inf | too few days |
| random_entry | 1 | +60.11 | 0.00 | inf | too few days |
| premium_momentum | 1 | +179.84 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 16 | 1 | +4.56 | +6.11 | +1.54 | 0% | no | advisory |
| room | 16 | 0 | +4.56 | +4.56 | +0.00 | 0% | no | advisory |
| coherence | 16 | 10 | +4.56 | +12.63 | +8.07 | 60% | no | advisory |
| force | 16 | 0 | +4.56 | +4.56 | +0.00 | 0% | no | advisory |
| episode | 16 | 1 | +4.56 | +5.84 | +1.28 | 0% | no | advisory |
| book | 16 | 5 | +4.56 | +0.51 | -4.05 | 60% | no | advisory |
| premium | 16 | 2 | +4.56 | +4.84 | +0.28 | 20% | no | advisory |
| quiet | 16 | 0 | +4.56 | +4.56 | +0.00 | 0% | no | advisory |
| bank | 16 | 4 | +4.56 | +3.99 | -0.57 | 20% | no | advisory |
| event | 16 | 0 | +4.56 | +4.56 | +0.00 | 0% | no | advisory |
| gamma_leg | 16 | 1 | +4.56 | +1.61 | -2.95 | 20% | no | advisory |
| gex_room | 16 | 3 | +4.56 | +7.30 | +2.74 | 0% | no | advisory |
| regime | 16 | 10 | +4.56 | +12.38 | +7.82 | 60% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| c20_9x | COMPRESSION | 4 | +20.48 | 50% |
| c20_9x | DIRECTIONAL | 5 | -2.10 | 40% |
| c20_9x | EXHAUSTION | 1 | +21.31 | 100% |
| c20_9x | RANGE | 1 | +23.96 | 100% |
| c20_9x | UNCERTAIN | 3 | -4.17 | 33% |
| c20_9x | WARMING | 2 | -15.60 | 0% |
| RAW | COMPRESSION | 4 | +20.48 | 50% |
| RAW | DIRECTIONAL | 5 | -2.10 | 40% |
| RAW | EXHAUSTION | 1 | +21.31 | 100% |
| RAW | RANGE | 1 | +23.96 | 100% |
| RAW | UNCERTAIN | 3 | -4.17 | 33% |
| RAW | WARMING | 2 | -15.60 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`c20_9x`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

937 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 937 | 1.4 | 0.8 | 0.0502 |
| iv_atm | 937 | 31.7 | 31.7 | -0.211 |
| iv_chg5 | 897 | 0.24 | 0.245 | -0.0732 |
| rv15 | 937 | 12 | 11 | 0.0983 |
| iv_rv | 937 | 2.43 | 2.93 | -0.216 |
| fut_imb5 | 937 | -0.067 | -0.154 | 0.254 |
| fut_tot_imb | 937 | 0.027 | 0.044 | -0.0467 |
| wall_up | 594 | 430 | 430 | 0.0365 |
| wall_dn | 242 | 478 | 480 | -0.148 |
| pcr | 937 | 0.954 | 0.903 | 0.216 |
| imp_rng | 937 | 103 | 92 | 0.0612 |
| imp_d | 937 | -1 | -1 | 0.149 |
| imp_f | 937 | 0.431 | 0.286 | 0.293 |
| fut_ofi60 | 937 | 2.39 | 6.06 | -0.00688 |
| syn_dev | 937 | 0.58 | -0.29 | 0.0712 |
| fut_micro | 937 | -0.42 | -0.11 | -0.163 |
| v_min30 | 937 | 85.1 | 57.1 | 0.056 |
| imp_with | 937 | 1 | 1 | -0.125 |
| wall_room | 413 | 430 | 440 | -0.0517 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
