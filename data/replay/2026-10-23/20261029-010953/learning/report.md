# ApexOptions — learning report (2026-10-23)

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
| futures_only | 1 | +127.81 | 0.00 | inf | too few days |
| random_entry | 1 | +92.40 | 0.00 | inf | too few days |
| premium_momentum | 1 | +105.51 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| room | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| coherence | 6 | 5 | +18.88 | +71.86 | +52.98 | 67% | no | advisory |
| force | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| episode | 6 | 1 | +18.88 | +19.21 | +0.33 | 33% | no | advisory |
| book | 6 | 2 | +18.88 | +16.73 | -2.14 | 67% | no | advisory |
| premium | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| quiet | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| bank | 6 | 1 | +18.88 | +19.21 | +0.33 | 33% | no | advisory |
| event | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| gamma_leg | 6 | 0 | +18.88 | +18.88 | +0.00 | 0% | no | advisory |
| gex_room | 6 | 1 | +18.88 | +24.88 | +6.00 | 0% | no | advisory |
| regime | 6 | 4 | +18.88 | +38.98 | +20.10 | 67% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| t28_gap | COMPRESSION | 1 | -11.12 | 0% |
| t28_gap | DIRECTIONAL | 2 | +38.98 | 100% |
| t28_gap | RANGE | 1 | +17.22 | 100% |
| t28_gap | UNCERTAIN | 1 | +29.11 | 100% |
| t28_gap | WARMING | 1 | +0.10 | 100% |
| RAW | COMPRESSION | 1 | -11.12 | 0% |
| RAW | DIRECTIONAL | 2 | +38.98 | 100% |
| RAW | RANGE | 1 | +17.22 | 100% |
| RAW | UNCERTAIN | 1 | +29.11 | 100% |
| RAW | WARMING | 1 | +0.10 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`t28_gap`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

534 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 534 | 0.7 | -1.4 | 0.396 |
| iv_atm | 534 | 15.5 | 15.8 | -0.149 |
| iv_chg5 | 533 | -0.025 | -0.03 | -0.081 |
| rv15 | 534 | 13 | 13 | 0.209 |
| iv_rv | 534 | 1.17 | 1.19 | -0.229 |
| fut_imb5 | 534 | 0.02 | -0.022 | -0.0309 |
| fut_tot_imb | 534 | 0.275 | 0.265 | -0.13 |
| wall_up | 495 | 72.2 | 89 | 0.0414 |
| wall_dn | 495 | 194 | 396 | -0.197 |
| pcr | 534 | 1.2 | 1.25 | -0.178 |
| imp_rng | 510 | 87.9 | 97.9 | -0.0909 |
| imp_d | 510 | -1 | -1 | 0.0551 |
| imp_f | 510 | 0.476 | 0.244 | 0.0652 |
| fut_ofi60 | 534 | -2.82 | 6.28 | -0.193 |
| syn_dev | 534 | 1.4 | 0.28 | 0.14 |
| fut_micro | 534 | 0 | 0 | -0.042 |
| v_min30 | 534 | 140 | 126 | 0.2 |
| imp_with | 510 | 1 | 1 | 0.269 |
| wall_room | 495 | 90.7 | 283 | -0.244 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
