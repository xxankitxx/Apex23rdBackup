# ApexOptions — learning report (2026-10-23)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `apex_edge`
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

## Challengers (daily return vs champion since it took over; one-sided α 0.0016 each, 32 challengers; 2 passing evenings in a row to promote)

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
| edge_gate_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_bracket_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_breakout | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +81.22 | 0.00 | inf | too few days |
| random_entry | 1 | +45.81 | 0.00 | inf | too few days |
| premium_momentum | 1 | +58.92 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| room | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| coherence | 7 | 6 | +7.19 | +20.97 | +13.78 | 67% | no | advisory |
| force | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| episode | 7 | 1 | +7.19 | +5.04 | -2.15 | 33% | no | advisory |
| book | 7 | 3 | +7.19 | +5.11 | -2.08 | 67% | no | advisory |
| premium | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| quiet | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| bank | 7 | 2 | +7.19 | +2.06 | -5.13 | 67% | no | advisory |
| event | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| gamma_leg | 7 | 0 | +7.19 | +7.19 | +0.00 | 0% | no | advisory |
| gex_room | 7 | 1 | +7.19 | +10.24 | +3.05 | 0% | no | advisory |
| regime | 7 | 5 | +7.19 | +15.20 | +8.01 | 67% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| apex_edge | COMPRESSION | 2 | +4.41 | 50% |
| apex_edge | DIRECTIONAL | 3 | +6.76 | 67% |
| apex_edge | RANGE | 1 | +20.09 | 100% |
| apex_edge | WARMING | 1 | +1.15 | 100% |
| RAW | COMPRESSION | 2 | +4.41 | 50% |
| RAW | DIRECTIONAL | 3 | +6.76 | 67% |
| RAW | RANGE | 1 | +20.09 | 100% |
| RAW | WARMING | 1 | +1.15 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`apex_edge`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

348 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 348 | -0.4 | -1.25 | 0.28 |
| iv_atm | 348 | 15.6 | 15.7 | -0.0101 |
| iv_chg5 | 347 | 0.005 | -0.02 | 0.0615 |
| rv15 | 348 | 13 | 13.2 | 0.0846 |
| iv_rv | 348 | 1.18 | 1.17 | -0.0911 |
| fut_imb5 | 348 | 0.045 | 0 | -0.0162 |
| fut_tot_imb | 348 | 0.275 | -0.227 | -0.0904 |
| wall_up | 332 | 89.3 | 101 | -0.0301 |
| wall_dn | 332 | 161 | 375 | -0.00929 |
| pcr | 348 | 1.21 | 1.22 | -0.0998 |
| imp_rng | 327 | 109 | 102 | 0.0228 |
| imp_d | 327 | -1 | -1 | 0.126 |
| imp_f | 327 | 0.129 | 0.134 | -0.0507 |
| fut_ofi60 | 348 | 2.56 | 7.68 | -0.159 |
| syn_dev | 348 | 0.45 | -0.31 | 0.103 |
| fut_micro | 348 | 0 | 0 | -0.085 |
| v_min30 | 348 | 153 | 131 | 0.141 |
| imp_with | 327 | 1 | 1 | 0.224 |
| wall_room | 332 | 111 | 271 | -0.188 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
