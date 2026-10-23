# ApexOptions — learning report (2026-10-19)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `spot_dc12_t12`
0 trades since 2026-10-20, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0025 each, 20 challengers; 2 passing evenings in a row to promote)

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
| spot_dc12_t12_1130 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +127.81 | 0.00 | inf | too few days |
| random_entry | 1 | +146.47 | 0.00 | inf | too few days |
| premium_momentum | 1 | +155.95 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 17 | 3 | +9.39 | +10.32 | +0.93 | 0% | no | advisory |
| room | 17 | 0 | +9.39 | +9.39 | +0.00 | 0% | no | advisory |
| coherence | 17 | 11 | +9.39 | +14.66 | +5.27 | 40% | no | advisory |
| force | 17 | 0 | +9.39 | +9.39 | +0.00 | 0% | no | advisory |
| episode | 17 | 1 | +9.39 | +9.29 | -0.10 | 0% | no | advisory |
| book | 17 | 3 | +9.39 | +10.86 | +1.46 | 0% | no | advisory |
| premium | 17 | 1 | +9.39 | +10.03 | +0.64 | 0% | no | advisory |
| quiet | 17 | 0 | +9.39 | +9.39 | +0.00 | 0% | no | advisory |
| bank | 17 | 2 | +9.39 | +10.97 | +1.58 | 0% | no | advisory |
| event | 17 | 0 | +9.39 | +9.39 | +0.00 | 0% | no | advisory |
| gamma_leg | 17 | 0 | +9.39 | +9.39 | +0.00 | 0% | no | advisory |
| gex_room | 17 | 5 | +9.39 | +10.21 | +0.81 | 20% | no | advisory |
| regime | 17 | 11 | +9.39 | +15.08 | +5.68 | 40% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| spot_dc12_t12 | COMPRESSION | 6 | +6.52 | 50% |
| spot_dc12_t12 | DIRECTIONAL | 7 | +10.33 | 71% |
| spot_dc12_t12 | RANGE | 1 | +1.77 | 100% |
| spot_dc12_t12 | WARMING | 3 | +15.49 | 67% |
| RAW | COMPRESSION | 6 | +6.52 | 50% |
| RAW | DIRECTIONAL | 7 | +10.33 | 71% |
| RAW | RANGE | 1 | +1.77 | 100% |
| RAW | WARMING | 3 | +15.49 | 67% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`spot_dc12_t12`** · gates: none · candidates: none
