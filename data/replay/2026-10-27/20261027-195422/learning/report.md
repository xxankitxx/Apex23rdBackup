# ApexOptions — learning report (2026-10-27)

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0015 each, 34 challengers; 2 passing evenings in a row to promote)

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


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -75.79 | 0.00 | inf | too few days |
| random_entry | 1 | +64.34 | 0.00 | inf | too few days |
| premium_momentum | 1 | -144.13 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| room | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| coherence | 1 | 1 | +6.94 | +0.00 | -6.94 | 100% | no | advisory |
| force | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| episode | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| book | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| premium | 1 | 1 | +6.94 | +0.00 | -6.94 | 100% | no | advisory |
| quiet | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| bank | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| event | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| gamma_leg | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| gex_room | 1 | 0 | +6.94 | +6.94 | +0.00 | 0% | no | advisory |
| regime | 1 | 1 | +6.94 | +0.00 | -6.94 | 100% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | RANGE | 1 | +6.94 | 100% |
| RAW | RANGE | 1 | +6.94 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

443 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 443 | 1.7 | 1.43 | -0.0105 |
| iv_atm | 443 | 32.3 | 32.3 | -0.0254 |
| iv_chg5 | 443 | 0.13 | 0.145 | -0.0396 |
| rv15 | 443 | 11.2 | 9.81 | 0.106 |
| iv_rv | 443 | 2.87 | 3.05 | -0.177 |
| fut_imb5 | 443 | -0.088 | 0.04 | -0.114 |
| fut_tot_imb | 443 | 0.042 | 0.264 | -0.0843 |
| wall_up | 432 | 200 | 57.3 | 0.0986 |
| wall_dn | 317 | 46.9 | 51.7 | 0.0998 |
| pcr | 443 | 0.993 | 1.01 | -0.0588 |
| imp_rng | 443 | 88.1 | 93.5 | -0.117 |
| imp_d | 443 | 1 | -1 | 0.181 |
| imp_f | 443 | 0.359 | 0.219 | 0.143 |
| fut_ofi60 | 443 | 7.54 | 2.62 | 0.139 |
| syn_dev | 443 | 0.68 | -0.35 | 0.18 |
| fut_micro | 443 | -0.02 | 0 | -0.148 |
| v_min30 | 443 | 76.3 | 50.6 | 0.111 |
| imp_with | 443 | -1 | 1 | -0.189 |
| wall_room | 337 | 192 | 49.2 | 0.213 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
