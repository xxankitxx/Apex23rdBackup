# ApexOptions — learning report (2026-10-19)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `m2.0_s0.5`
2 trades since 2026-10-17, Σ +146.0 %. GO line 1000.6, KILL line -558.4 → **COLLECTING**. Observed sd 92.5 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #1 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 2).
- SPRT on per-trade 100·ln(1+r): Σ +94.2 (mean +47.08/trade) vs GO 1000.6 / KILL -558.4 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.47** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (1)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [x] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0038 each, 13 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | +14.29 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | -3.96 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | +14.29 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | -3.96 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | +17.37 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | -3.96 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | +107.86 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | +14.29 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | +0.00 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | +110.53 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -466.26 | 0.00 | inf | too few days |
| random_entry | 1 | +132.36 | 0.00 | inf | too few days |
| premium_momentum | 1 | -252.73 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| room | 2 | 1 | +72.98 | +7.57 | -65.41 | 50% | no | advisory |
| coherence | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| force | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| episode | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| book | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| premium | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| quiet | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| bank | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| event | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| gamma_leg | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| gex_room | 2 | 0 | +72.98 | +72.98 | +0.00 | 0% | no | advisory |
| regime | 2 | 2 | +72.98 | +0.00 | -72.98 | 100% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| m2.0_s0.5 | RANGE | 1 | +138.39 | 100% |
| m2.0_s0.5 | UNCERTAIN | 1 | +7.57 | 100% |
| RAW | RANGE | 1 | +138.39 | 100% |
| RAW | UNCERTAIN | 1 | +7.57 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

### Overall and by decision

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| all candidates | 139 | 62% | 54%–70% | +9.8 |
| taken | 2 | 100% | 34%–100% | +67.1 |
| rejected: already in a trade | 2 | 50% | 9%–91% | -10.1 |
| rejected: basket too thin | 126 | 62% | 53%–70% | +9.6 |
| rejected: outside window | 9 | 56% | 27%–81% | +2.4 |

### By regime at the candidate moment

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| BREAKOUT | 7 | 57% | 25%–84% | -2.0 |
| COMPRESSION | 23 | 70% | 49%–84% | +16.7 |
| DIRECTIONAL | 27 | 56% | 37%–72% | +11.0 |
| EXHAUSTION | 7 | 57% | 25%–84% | -7.5 |
| RANGE | 46 | 57% | 42%–70% | +15.4 |
| UNCERTAIN | 24 | 79% | 60%–91% | +2.2 |
| WARMING | 5 | 40% | 12%–77% | -0.1 |

### By impulse size (z at the crossing)

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| z 0–2.5 | 115 | 61% | 52%–69% | +8.7 |
| z 2.5–3.5 | 24 | 67% | 47%–82% | +16.0 |
| z 3.5–∞ | 0 | — | — | — |

### Does each advisor's veto separate good candidates from bad?

| advisor | vetoed: resolved | vetoed hit rate | passed: resolved | passed hit rate |
|---|---|---|---|---|
| bank | 2 | 50% | 137 | 62% |
| book | 29 | 52% | 110 | 65% |
| coherence | 81 | 54% | 58 | 72% |
| episode | 3 | 67% | 136 | 62% |
| event | 0 | — | 139 | 62% |
| force | 1 | 0% | 138 | 62% |
| gamma_leg | 8 | 50% | 131 | 63% |
| gex_room | 25 | 72% | 114 | 60% |
| iv_late | 22 | 64% | 117 | 62% |
| premium | 29 | 55% | 110 | 64% |
| quiet | 0 | — | 139 | 62% |
| regime | 123 | 61% | 16 | 69% |
| room | 6 | 50% | 133 | 62% |


Champion for the next session: **`m2.0_s0.5`** · gates: none · candidates: none
