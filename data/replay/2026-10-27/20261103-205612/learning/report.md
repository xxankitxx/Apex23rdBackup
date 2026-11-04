# ApexOptions — learning report (2026-10-27)

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
| futures_only | 1 | +102.51 | 0.00 | inf | too few days |
| random_entry | 1 | +242.63 | 0.00 | inf | too few days |
| premium_momentum | 1 | +34.16 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| room | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| coherence | 13 | 6 | +17.78 | +18.90 | +1.12 | 50% | no | advisory |
| force | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| episode | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| book | 13 | 7 | +17.78 | +14.00 | -3.78 | 75% | no | advisory |
| premium | 13 | 4 | +17.78 | +22.36 | +4.58 | 25% | no | advisory |
| quiet | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| bank | 13 | 1 | +17.78 | +17.07 | -0.71 | 0% | no | advisory |
| event | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| gamma_leg | 13 | 0 | +17.78 | +17.78 | +0.00 | 0% | no | advisory |
| gex_room | 13 | 3 | +17.78 | +15.59 | -2.19 | 25% | no | advisory |
| regime | 13 | 10 | +17.78 | +22.35 | +4.57 | 75% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| c20_9x | COMPRESSION | 3 | +20.80 | 100% |
| c20_9x | DIRECTIONAL | 3 | +22.35 | 67% |
| c20_9x | RANGE | 1 | +2.60 | 100% |
| c20_9x | UNCERTAIN | 6 | +16.51 | 67% |
| RAW | COMPRESSION | 3 | +20.80 | 100% |
| RAW | DIRECTIONAL | 3 | +22.35 | 67% |
| RAW | RANGE | 1 | +2.60 | 100% |
| RAW | UNCERTAIN | 6 | +16.51 | 67% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`c20_9x`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

994 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 994 | 1.5 | 1.3 | -0.0484 |
| iv_atm | 994 | 31.9 | 32.1 | -0.0347 |
| iv_chg5 | 993 | 0.14 | 0.17 | -0.0247 |
| rv15 | 994 | 11.1 | 9.32 | 0.127 |
| iv_rv | 994 | 2.87 | 3.13 | -0.202 |
| fut_imb5 | 994 | -0.034 | 0.04 | -0.0444 |
| fut_tot_imb | 994 | 0.007 | 0.286 | -0.0828 |
| wall_up | 961 | 66.3 | 52.5 | 0.0351 |
| wall_dn | 704 | 49.2 | 51.7 | 0.132 |
| pcr | 994 | 0.996 | 0.988 | -0.048 |
| imp_rng | 994 | 76.7 | 87 | -0.0949 |
| imp_d | 994 | 1 | -1 | 0.0832 |
| imp_f | 994 | 0.413 | 0.245 | 0.0585 |
| fut_ofi60 | 994 | 7.77 | 2.15 | 0.222 |
| syn_dev | 994 | 0.495 | -0.615 | 0.193 |
| fut_micro | 994 | 0 | 0 | -0.00225 |
| v_min30 | 994 | 62.4 | 39.5 | 0.12 |
| imp_with | 994 | -1 | 1 | -0.199 |
| wall_room | 735 | 89.3 | 49.2 | 0.208 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
