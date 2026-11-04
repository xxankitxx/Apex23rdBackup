# Twenty-member panel C12 — losing trades, missed trades, loose exits (4 Nov 2026, night)

Owner: *"This code is either not taking trades or is still taking stupid loss making trades ... not trailing
tightly and gives away so many points ... sits like a stupid holding on to a non-working trade."* Asked for 20
members working alone, using advanced greeks, calculus and mathematical models.

Method: offline kit (ask fill 2 s after the signal, bid out), exact c20_9x class, 12 tapes 19 Oct – 4 Nov (expiry:
19 Oct, 27 Oct, 3 Nov). The kit reproduces 4 Nov live (-25,412) as -26,312. Each member one angle, a yes/no rule,
±20 % nudges, out-of-sample days (29 Oct – 4 Nov), leave-one-day-out. Red team re-ran the six best; a synthesis lead
stacked the survivors. Panel material: scratchpad `team4/`.

## Where c20_9x loses (kit, 12 days, +11,23,538)
| | trades | P&L |
|---|---:|---:|
| losers | 36 | -5,68,766 |
| dead losers (never above +5 %) | 18 | **-4,39,153** (77 % of all losses) |
| green-to-red (peaked >= +10 %, still lost) | 14 | -45,763 |
| stuck (>= 10 min, peak < +15 %) | 16 | -80,051 |
| give-back from peak (trades reaching +10 %) | 54 | avg 16.1 % of entry |
| big moves caught (15-min windows, forward range >= 40 pts) | | 68 of 175 |

The biggest dead losses are expiry stop-losses hit within 51–93 s (19 Oct -45k to -72k): no exit rule reaches them.

## The twenty angles
| Member | Mathematics | Kit vs c20_9x | Out-of-sample (base -22,480) | Outcome |
|---|---|---:|---:|---|
| gamma-theta | breakeven move sqrt(2·|Θ|·t/Γ), realized/implied variance | +9.6k | +5.7k | cliff (HOLD 240 s: -71k) |
| kalman | local-linear-trend Kalman velocity t-stat exit | +8.6k | +9.1k | cliff (T 240: -74k) |
| regime-vr | Lo-MacKinlay variance ratio, Hurst, efficiency ratio | +28.6k | -5.1k | loses out of sample |
| cusum-exit | CUSUM / Page-Hinkley drift change exit | +27.0k | -8.9k | loses out of sample |
| sprt-time | Wald SPRT on drift since entry | +14.9k | -7.6k | loses out of sample |
| vol-trail | σ·√t Chandelier trail with Δ+½Γ convexity | +32.3k | -7.3k | loses out of sample |
| **premium-efficiency** | Taylor model ΔF+½ΓF²+Θt+νΔσ; IV-rich entry veto | **+83.4k** | **+10.2k** | **accepted** |
| vanna-iv | dσ/dF, vega vs delta P&L | +55.5k | -34.1k | fails expiry check |
| charm-tod | charm, θ/premium by time of day | -239k | -6.4k | loses |
| breakeven-math | spread+θ cost-cover clock T* = ((s+θ)/(Δσ))² | -1.5k | +3.5k | no gain |
| mfe-mae | Sweeney excursion separation | +1.9k | -24.1k | no gain |
| breakeven-lock | noise-scaled break-even floor | +4.1k | 0 | no gain |
| chop-filter | flip-flop veto, choppiness | +39.4k | -5.2k | rejected: 4 trades, cliff at +27 % |
| ofi-micro | Cont-Kukanov-Stoikov order-flow imbalance | -10.1k | -26.1k | loses |
| **gex-walls** | dealer gamma / max-OI wall ahead of the breakout | **+25.2k** | -19.2k | **accepted** (no cliff, small) |
| re-entry | re-enter on resumed move | -45.3k | -33.1k | loses |
| missed-moves | extra entry type for missed big moves | +72.1k | +48.1k | rejected: cliff; losers 36 -> 57 |
| strike-select | greek-based strike choice | +1.5k | -19.3k | no gain |
| vol-regime | IV vs morning median (same 4 trades as premium-efficiency) | +83.4k | +10.2k | rejected: cliff on its own threshold |
| loser-autopsy | 25-feature autopsy of 36 losers vs 41 winners | +83.7k | +10.5k | rejected: not reproduced in time |

**Every exit idea failed.** Tight, noise-aware exits (Kalman, CUSUM, SPRT, σ-trail, breakeven clocks) all cut the
runners that are flat or red in their first 2–8 minutes — the same wall docs/21 and docs/22 hit. On these tapes the
early path of a runner and of a dead trade cannot be told apart by any causal price, greek or flow statistic the
panel tried. The money is in not entering the bad trades, not in exiting them faster.

## The result — c20_9y (shadow book)
c20_9x plus two entry vetoes; exits, picker and cooldowns unchanged.
1. **IV_RICH** — refuse a buy when the ATM IV (30-s mean of CE+PE IV at the strike nearest the forward) is more than
   3.5 vol pts above its median since 09:20. Fired only on expiry afternoons: 19 Oct 14:33 CE (-50.7k), 3 Nov
   13:54 / 14:18 / 14:24 PE (-13.4k, -16.4k, -2.8k).
2. **OI_WALL** — normal days: refuse a buy when the max-OI strike of the resisting type (call OI for a CE, put OI for
   a PE) within 250 pts lies ahead of the trade and within 25 pts.

| | c20_9x | c20_9y |
|---|---:|---:|
| Kit, 12 days | +11,23,538 | +12,32,085 (+1,08,547) |
| Losers | 36 / -5,68,766 | 28 / -4,68,299 |
| Dead losers | 18 / -4,39,153 | 15 / -3,58,569 |
| Green-to-red | 14 / -45,763 | 10 / -29,360 |
| Winners | 41 / +16,92,304 | 41 / +17,00,384 (none lost) |
| Out-of-sample (29 Oct – 4 Nov) | -22,480 | +13,419 |
| 3 Nov (expiry) | -38,428 | -5,775 |
| 4 Nov | -26,312 | -26,312 (untouched) |
| Big moves caught | 68 / 175 | 62 / 175 |

Nudges: IVR 2.8 / 4.2 keep 107 % / 88 % of the gain, 4.9 keeps 41 %; W and DMAX at ±20–40 % keep all of it. LODO
+1.09 L. The engine class (incremental IV series, IV in percent) gives the identical kit total. tests/test_c20_9y.py.

**Weaknesses.** Eight vetoed buys on five days make the whole gain; three expiry tapes. The IV veto may be a late
expiry-afternoon effect in IV clothing and would refuse a future runner that comes with a 3.5-pt IV spike. Below
IVR ≈ 2.2 it kills the 27 Oct 14:36 runner. Nothing fixes 4 Nov's chop or most dead losers; missed moves get
slightly worse. Kit numbers only — engine replay and live shadow days before any promotion.

## What the panel says to do next
* The leak is entries, not exits: 15 dead losers still cost -3.59 L. The cleanest remaining lead is the
  loser-autopsy veto (+83.7k claimed, not reproduced in time) — re-run its red team.
* Expiry stop-losses in the first 90 s (19 Oct) are the single biggest losers; an entry-confirmation study on
  expiry breakouts at the day's extreme is the open problem.
* Catching missed moves added more losers than profit every time it was tried (re-entry, missed-moves).
