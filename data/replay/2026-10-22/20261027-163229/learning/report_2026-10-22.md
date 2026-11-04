# ApexOptions — learning report (2026-10-22)

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
| futures_only | 1 | +51.47 | 0.00 | inf | too few days |
| random_entry | 1 | +16.00 | 0.00 | inf | too few days |
| premium_momentum | 1 | +29.68 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| room | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| coherence | 4 | 2 | +5.21 | +20.45 | +15.24 | 0% | no | advisory |
| force | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| episode | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| book | 4 | 2 | +5.21 | +4.95 | -0.27 | 50% | no | advisory |
| premium | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| quiet | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| bank | 4 | 1 | +5.21 | +10.32 | +5.11 | 0% | no | advisory |
| event | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 0 | +5.21 | +5.21 | +0.00 | 0% | no | advisory |
| regime | 4 | 1 | +5.21 | +10.32 | +5.11 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| apex_edge | DIRECTIONAL | 3 | +10.32 | 67% |
| apex_edge | UNCERTAIN | 1 | -10.11 | 0% |
| RAW | DIRECTIONAL | 3 | +10.32 | 67% |
| RAW | UNCERTAIN | 1 | -10.11 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`apex_edge`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

402 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 402 | -0.225 | -0.25 | 0.017 |
| iv_atm | 402 | 14.7 | 14.6 | 0.00715 |
| iv_chg5 | 402 | 0.015 | -0.05 | 0.138 |
| rv15 | 402 | 11.2 | 11.7 | 0.0158 |
| iv_rv | 402 | 1.31 | 1.25 | -0.0184 |
| fut_imb5 | 402 | 0 | 0.056 | -0.0425 |
| fut_tot_imb | 402 | 0.081 | -0.057 | -0.0601 |
| wall_up | 402 | 320 | 287 | 0.118 |
| wall_dn | 402 | 122 | 101 | 0.0652 |
| pcr | 402 | 1.22 | 1.15 | 0.109 |
| imp_rng | 402 | 124 | 123 | 0.0601 |
| imp_d | 402 | 1 | 1 | -0.0152 |
| imp_f | 402 | 0.277 | 0.443 | -0.189 |
| fut_ofi60 | 402 | 4.01 | 6.22 | -0.0332 |
| syn_dev | 402 | 0.86 | 0.21 | 0.0523 |
| fut_micro | 402 | 0 | 0 | -0.0243 |
| v_min30 | 402 | 144 | 135 | 0.0326 |
| imp_with | 402 | 1 | 1 | 0.0153 |
| wall_room | 402 | 173 | 167 | 0.122 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
