# ApexOptions — learning report (2026-10-26)

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
| futures_only | 1 | -7.87 | 0.00 | inf | too few days |
| random_entry | 1 | +5.44 | 0.00 | inf | too few days |
| premium_momentum | 1 | +31.87 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| room | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| coherence | 4 | 2 | -3.70 | +2.04 | +5.74 | 0% | no | advisory |
| force | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| episode | 4 | 2 | -3.70 | +2.04 | +5.74 | 0% | no | advisory |
| book | 4 | 3 | -3.70 | +14.05 | +17.75 | 0% | no | advisory |
| premium | 4 | 1 | -3.70 | -1.61 | +2.09 | 0% | no | advisory |
| quiet | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| bank | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| event | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 0 | -3.70 | -3.70 | +0.00 | 0% | no | advisory |
| regime | 4 | 2 | -3.70 | +2.30 | +6.00 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| apex_edge | COMPRESSION | 1 | -9.96 | 0% |
| apex_edge | DIRECTIONAL | 2 | +2.30 | 50% |
| apex_edge | WARMING | 1 | -9.42 | 0% |
| RAW | COMPRESSION | 1 | -9.96 | 0% |
| RAW | DIRECTIONAL | 2 | +2.30 | 50% |
| RAW | WARMING | 1 | -9.42 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12_first | 1 | -0.85 | 0% | -0.9 / -0.9 | 1 | CAS-ENTRY 1 |

Champion for the next session: **`apex_edge`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

384 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 384 | 2.65 | 0.5 | 0.18 |
| iv_atm | 384 | 23.5 | 23.6 | -0.185 |
| iv_chg5 | 384 | -0.12 | -0.04 | -0.035 |
| rv15 | 384 | 12.6 | 13.2 | -0.131 |
| iv_rv | 384 | 1.82 | 1.75 | 0.102 |
| fut_imb5 | 384 | -0.172 | -0.024 | -0.183 |
| fut_tot_imb | 384 | -0.186 | 0.0205 | -0.171 |
| wall_up | 384 | 97 | 113 | -0.058 |
| wall_dn | 252 | 110 | 104 | 0.0372 |
| pcr | 384 | 1.23 | 1.32 | -0.15 |
| imp_rng | 384 | 91.5 | 98.7 | -0.0775 |
| imp_d | 384 | 1 | -1 | 0.00698 |
| imp_f | 384 | 0.238 | 0.307 | -0.0899 |
| fut_ofi60 | 384 | 10.6 | 5.33 | 0.114 |
| syn_dev | 384 | 1.58 | 0.28 | 0.00492 |
| fut_micro | 384 | -0.12 | 0 | -0.0737 |
| v_min30 | 384 | 114 | 128 | -0.0653 |
| imp_with | 384 | 1 | -1 | 0.0253 |
| wall_room | 328 | 98.2 | 100 | -0.106 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
