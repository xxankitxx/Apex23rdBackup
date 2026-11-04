# ApexOptions — learning report (2026-10-26)

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
| futures_only | 1 | +11.84 | 0.00 | inf | too few days |
| random_entry | 1 | +25.15 | 0.00 | inf | too few days |
| premium_momentum | 1 | +51.58 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| room | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| coherence | 7 | 4 | +1.23 | -4.18 | -5.41 | 67% | no | advisory |
| force | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| episode | 7 | 2 | +1.23 | +5.49 | +4.27 | 0% | no | advisory |
| book | 7 | 4 | +1.23 | +7.87 | +6.64 | 33% | no | advisory |
| premium | 7 | 2 | +1.23 | +0.95 | -0.28 | 33% | no | advisory |
| quiet | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| bank | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| event | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| gamma_leg | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| gex_room | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| regime | 7 | 4 | +1.23 | -4.01 | -5.24 | 67% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| t28_gap | COMPRESSION | 3 | +10.02 | 67% |
| t28_gap | DIRECTIONAL | 3 | -4.01 | 33% |
| t28_gap | WARMING | 1 | -9.42 | 0% |
| RAW | COMPRESSION | 3 | +10.02 | 67% |
| RAW | DIRECTIONAL | 3 | -4.01 | 33% |
| RAW | WARMING | 1 | -9.42 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12_first | 1 | -0.85 | 0% | -0.9 / -0.9 | 1 | CAS-ENTRY 1 |

Champion for the next session: **`t28_gap`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

606 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 606 | 3.75 | 1.55 | 0.229 |
| iv_atm | 606 | 23.2 | 23.6 | -0.198 |
| iv_chg5 | 606 | -0.07 | -0.08 | 0.0698 |
| rv15 | 606 | 12.5 | 13.5 | -0.194 |
| iv_rv | 606 | 1.83 | 1.77 | 0.18 |
| fut_imb5 | 606 | -0.245 | -0.111 | -0.0987 |
| fut_tot_imb | 606 | -0.205 | 0.192 | -0.205 |
| wall_up | 606 | 140 | 118 | -0.0212 |
| wall_dn | 413 | 107 | 101 | 0.025 |
| pcr | 606 | 1.31 | 1.31 | -0.116 |
| imp_rng | 606 | 88.8 | 98.7 | -0.133 |
| imp_d | 606 | 1 | -1 | 0.106 |
| imp_f | 606 | 0.471 | 0.469 | -0.0522 |
| fut_ofi60 | 606 | 5.78 | 2.58 | 0.152 |
| syn_dev | 606 | 0.42 | -0.58 | 0.0976 |
| fut_micro | 606 | 0 | 0 | -0.0112 |
| v_min30 | 606 | 95.3 | 117 | -0.119 |
| imp_with | 606 | 1 | 1 | -0.021 |
| wall_room | 533 | 107 | 99.6 | -0.016 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
