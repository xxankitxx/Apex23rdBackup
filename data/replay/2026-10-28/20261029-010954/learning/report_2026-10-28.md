# ApexOptions — learning report (2026-10-28)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `t28_gap`
0 trades since 2026-10-28, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0009 each, 55 challengers; 2 passing evenings in a row to promote)

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


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -27.69 | 0.00 | inf | too few days |
| random_entry | 1 | -18.17 | 0.00 | inf | too few days |
| premium_momentum | 1 | -0.06 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| room | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| coherence | 5 | 4 | -4.80 | -9.16 | -4.36 | 100% | no | advisory |
| force | 5 | 1 | -4.80 | -5.81 | -1.01 | 0% | no | advisory |
| episode | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| book | 5 | 1 | -4.80 | -3.68 | +1.12 | 0% | no | advisory |
| premium | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| quiet | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| bank | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| event | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| gamma_leg | 5 | 0 | -4.80 | -4.80 | +0.00 | 0% | no | advisory |
| gex_room | 5 | 1 | -4.80 | -3.68 | +1.12 | 0% | no | advisory |
| regime | 5 | 1 | -4.80 | -3.68 | +1.12 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| t28_gap | COMPRESSION | 1 | -9.16 | 0% |
| t28_gap | DIRECTIONAL | 3 | -1.85 | 33% |
| t28_gap | EXHAUSTION | 1 | -9.29 | 0% |
| RAW | COMPRESSION | 1 | -9.16 | 0% |
| RAW | DIRECTIONAL | 3 | -1.85 | 33% |
| RAW | EXHAUSTION | 1 | -9.29 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12 | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_dc12_t12_1130 | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_dc12_t12_first | 4 | -0.52 | 25% | -1.1 / +0.2 | 0 | CAS-ENTRY 4 |
| spot_dc12_t12_nolock | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_ft_prem10 | 1 | +0.03 | 100% | +0.0 / +0.0 | 0 | CAS-ENTRY 1 |
| t28_all | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_core_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_d46_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |

Champion for the next session: **`t28_gap`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

454 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 452 | -0.8 | -0.7 | -0.064 |
| iv_atm | 454 | 16 | 15.8 | 0.00523 |
| iv_chg5 | 454 | -0.085 | -0.05 | -0.0628 |
| rv15 | 454 | 11.8 | 11.2 | 0.151 |
| iv_rv | 454 | 1.33 | 1.46 | -0.192 |
| fut_imb5 | 454 | -0.0335 | -0.077 | -0.0494 |
| fut_tot_imb | 454 | -0.083 | 0.076 | -0.364 |
| wall_up | 446 | 273 | 288 | -0.0549 |
| wall_dn | 414 | 83 | 51.5 | 0.101 |
| pcr | 452 | 0.925 | 0.965 | -0.199 |
| imp_rng | 452 | 98.9 | 91.2 | -0.0594 |
| imp_d | 452 | -1 | -1 | -0.0324 |
| imp_f | 452 | 0.284 | 0.506 | -0.151 |
| fut_ofi60 | 454 | 0.43 | 0.73 | -0.0221 |
| syn_dev | 452 | -0.17 | 0.23 | -0.219 |
| fut_micro | 454 | -0.5 | 0 | -0.0397 |
| v_min30 | 454 | 82.9 | 78 | -0.0126 |
| imp_with | 452 | 1 | 1 | -0.0907 |
| wall_room | 421 | 227 | 197 | -0.0194 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
