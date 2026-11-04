# ApexOptions — learning report (2026-10-23)

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
| futures_only | 1 | +117.14 | 0.00 | inf | too few days |
| random_entry | 1 | +81.74 | 0.00 | inf | too few days |
| premium_momentum | 1 | +94.85 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| room | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| coherence | 7 | 6 | +14.74 | +71.86 | +57.12 | 67% | no | advisory |
| force | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| episode | 7 | 1 | +14.74 | +14.32 | -0.41 | 33% | no | advisory |
| book | 7 | 3 | +14.74 | +16.73 | +2.00 | 67% | no | advisory |
| premium | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| quiet | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| bank | 7 | 1 | +14.74 | +14.32 | -0.41 | 33% | no | advisory |
| event | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| gamma_leg | 7 | 0 | +14.74 | +14.74 | +0.00 | 0% | no | advisory |
| gex_room | 7 | 1 | +14.74 | +19.04 | +4.31 | 0% | no | advisory |
| regime | 7 | 5 | +14.74 | +38.98 | +24.24 | 67% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | COMPRESSION | 1 | -11.12 | 0% |
| edge_gate_trail | DIRECTIONAL | 3 | +22.61 | 67% |
| edge_gate_trail | RANGE | 1 | +17.22 | 100% |
| edge_gate_trail | UNCERTAIN | 1 | +29.11 | 100% |
| edge_gate_trail | WARMING | 1 | +0.10 | 100% |
| RAW | COMPRESSION | 1 | -11.12 | 0% |
| RAW | DIRECTIONAL | 3 | +22.61 | 67% |
| RAW | RANGE | 1 | +17.22 | 100% |
| RAW | UNCERTAIN | 1 | +29.11 | 100% |
| RAW | WARMING | 1 | +0.10 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

392 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 392 | 0.65 | -1.4 | 0.365 |
| iv_atm | 392 | 15.5 | 15.7 | -0.118 |
| iv_chg5 | 391 | -0.02 | -0.03 | -0.0316 |
| rv15 | 392 | 13 | 13.1 | 0.155 |
| iv_rv | 392 | 1.17 | 1.19 | -0.177 |
| fut_imb5 | 392 | 0.032 | 0 | -0.0527 |
| fut_tot_imb | 392 | 0.275 | -0.227 | -0.0954 |
| wall_up | 369 | 85.3 | 94.2 | 0.021 |
| wall_dn | 369 | 159 | 388 | -0.128 |
| pcr | 392 | 1.2 | 1.22 | -0.156 |
| imp_rng | 372 | 97 | 104 | -0.0344 |
| imp_d | 372 | -1 | -1 | 0.0685 |
| imp_f | 372 | 0.282 | 0.182 | 0.0182 |
| fut_ofi60 | 392 | 0.99 | 6.28 | -0.172 |
| syn_dev | 392 | 0.85 | 0.13 | 0.121 |
| fut_micro | 392 | 0 | 0 | -0.0835 |
| v_min30 | 392 | 147 | 134 | 0.172 |
| imp_with | 372 | 1 | 1 | 0.224 |
| wall_room | 369 | 103 | 270 | -0.217 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
