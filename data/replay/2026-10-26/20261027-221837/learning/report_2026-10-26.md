# ApexOptions — learning report (2026-10-26)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `edge_gate_trail`
0 trades since 2026-10-27, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0013 each, 39 challengers; 2 passing evenings in a row to promote)

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
| lvl_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_re | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_be | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -14.01 | 0.00 | inf | too few days |
| random_entry | 1 | -0.71 | 0.00 | inf | too few days |
| premium_momentum | 1 | +25.72 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| room | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| coherence | 4 | 2 | -5.39 | -1.35 | +4.04 | 0% | no | advisory |
| force | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| episode | 4 | 2 | -5.39 | -1.35 | +4.04 | 0% | no | advisory |
| book | 4 | 3 | -5.39 | +7.25 | +12.65 | 0% | no | advisory |
| premium | 4 | 1 | -5.39 | -3.87 | +1.52 | 0% | no | advisory |
| quiet | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| bank | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| event | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 0 | -5.39 | -5.39 | +0.00 | 0% | no | advisory |
| regime | 4 | 2 | -5.39 | -1.10 | +4.30 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | COMPRESSION | 1 | -9.96 | 0% |
| edge_gate_trail | DIRECTIONAL | 2 | -1.10 | 50% |
| edge_gate_trail | WARMING | 1 | -9.42 | 0% |
| RAW | COMPRESSION | 1 | -9.96 | 0% |
| RAW | DIRECTIONAL | 2 | -1.10 | 50% |
| RAW | WARMING | 1 | -9.42 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12_first | 1 | -0.85 | 0% | -0.9 / -0.9 | 1 | CAS-ENTRY 1 |

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

433 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 433 | 2.67 | 0.5 | 0.225 |
| iv_atm | 433 | 23.4 | 23.6 | -0.19 |
| iv_chg5 | 433 | -0.07 | -0.04 | 0.0139 |
| rv15 | 433 | 12.6 | 13.5 | -0.153 |
| iv_rv | 433 | 1.82 | 1.75 | 0.123 |
| fut_imb5 | 433 | -0.196 | -0.043 | -0.151 |
| fut_tot_imb | 433 | -0.186 | 0.121 | -0.195 |
| wall_up | 433 | 98.8 | 118 | -0.0514 |
| wall_dn | 288 | 107 | 101 | 0.013 |
| pcr | 433 | 1.28 | 1.32 | -0.138 |
| imp_rng | 433 | 89.5 | 98.7 | -0.0858 |
| imp_d | 433 | 1 | -1 | 0.067 |
| imp_f | 433 | 0.348 | 0.385 | -0.102 |
| fut_ofi60 | 433 | 7.44 | 3.86 | 0.132 |
| syn_dev | 433 | 1.41 | -0.01 | 0.0543 |
| fut_micro | 433 | -0.05 | 0 | -0.0489 |
| v_min30 | 433 | 103 | 123 | -0.0833 |
| imp_with | 433 | 1 | 1 | 0.0142 |
| wall_room | 377 | 105 | 101 | -0.098 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
