# ApexOptions — learning report (2026-10-19)

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
| futures_only | 1 | +96.76 | 0.00 | inf | too few days |
| random_entry | 1 | +58.56 | 0.00 | inf | too few days |
| premium_momentum | 1 | +178.29 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 3 | 2 | +11.44 | +16.24 | +4.80 | 50% | no | advisory |
| room | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| coherence | 3 | 3 | +11.44 | +0.00 | -11.44 | 100% | no | advisory |
| force | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| episode | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| book | 3 | 2 | +11.44 | +16.24 | +4.80 | 50% | no | advisory |
| premium | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| quiet | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| bank | 3 | 1 | +11.44 | +11.41 | -0.03 | 50% | no | advisory |
| event | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| gamma_leg | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |
| gex_room | 3 | 1 | +11.44 | +9.04 | -2.40 | 50% | no | advisory |
| regime | 3 | 0 | +11.44 | +11.44 | +0.00 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | DIRECTIONAL | 3 | +11.44 | 100% |
| RAW | DIRECTIONAL | 3 | +11.44 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

461 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 461 | 1.05 | 0.1 | 0.0878 |
| iv_atm | 461 | 31.8 | 31.5 | -0.152 |
| iv_chg5 | 445 | 0.24 | 0.2 | -0.00563 |
| rv15 | 461 | 12 | 11 | 0.108 |
| iv_rv | 461 | 2.45 | 2.92 | -0.196 |
| fut_imb5 | 461 | 0 | -0.111 | 0.203 |
| fut_tot_imb | 461 | 0.024 | 0.041 | -0.0365 |
| wall_up | 292 | 430 | 434 | 0.0386 |
| wall_dn | 108 | 478 | 480 | -0.0887 |
| pcr | 461 | 0.954 | 0.916 | 0.168 |
| imp_rng | 461 | 103 | 98 | 0.0605 |
| imp_d | 461 | -1 | -1 | 0.167 |
| imp_f | 461 | 0.431 | 0.286 | 0.203 |
| fut_ofi60 | 461 | 2.95 | 5.76 | 0.0353 |
| syn_dev | 461 | 0.57 | -0.07 | 0.0527 |
| fut_micro | 461 | -0.42 | -0.11 | -0.0898 |
| v_min30 | 461 | 85.1 | 60.9 | 0.0614 |
| imp_with | 461 | 1 | 1 | -0.106 |
| wall_room | 195 | 430 | 440 | -0.0282 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
