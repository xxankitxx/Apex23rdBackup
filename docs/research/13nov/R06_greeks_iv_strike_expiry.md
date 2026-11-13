# R06: Greeks, implied volatility, strike and expiry choice

Analyst R06, 13 Nov 2026. Lens: owner point 1 (advanced mathematics and greeks), with points 2, 4 and 6 where the greeks touch them.

## Findings first

1. **The engine's theta clock is right on normal days and wrong on expiry day.** `apex/greeks.py:124` spreads a year of theta over 365 x 375 trading minutes, so its theta is 3.84 times the calendar rate. I asked the market which clock it uses: if premiums really decay on the trading-minute clock, the IV backed out with calendar time must drift down while a trade is held, by a predictable amount. It does, almost exactly, on normal days and the day before expiry. On expiry day the market uses the calendar clock (about 0.7 to 1.0 times calendar). So on expiry day every number built on `theta_min` is about 4 to 5 times too large: the weather's `theta_be` and `theta_ratio`, the commentary's "theta bill", the `req_move_veto` and the `buyer_edge_gate`. The c20 expiry picker and rent stop already correct for this (they multiply by 375/1440). Nothing else does.
2. **Theta is not why trades lose.** With the right clock, the median pool trade pays about 0.4 % of premium in theta on a normal day and about 0.5 to 0.6 % on expiry day. The half spread costs about 0.25 %. Gamma gives back part of the theta. The trade result depends on direction, and then on the IV change after entry.
3. **The IV change after entry is the second-biggest driver, and it can barely be predicted.** Conductor trades whose IV rose by more than 1 vol point won 93 % of the time. Those whose IV fell by more than 1 point won 36 %. But no ex-ante IV or greek item predicts that change well: the best Spearman correlation that kept its sign from the early days to the late days is 0.20.
4. **No greek or IV entry filter passed walk-forward.** I tried 30 items x 9 thresholds x 2 sides (538 variants per sample) on the Conductor, on c20_9y and on the five pool books. I chose on 19 Oct to 4 Nov and tested on 5 to 12 Nov. None improved the test days in a way that touched more than a single trade. `theta_ratio`, `theta_be`, the delta at entry, ITM depth, IV level and IV against the day's median all failed.
5. **One strike deeper ITM on expiry day only: promising, but only 3 days were repriced.** I repriced the same entry and exit seconds from the ds_v2 quotes. On both expiry days (3 and 9 Nov) the deeper strike was better: 3 Nov went from -40.0 % to -26.2 %, and 9 Nov from +31.0 % to +45.2 %. On the one normal day (6 Nov) it was worse: +107.6 % fell to +98.4 %. That is 2 days of evidence, so it is not proven. Phase B reprices all 16 days.
6. **The next weekly expiry is a shock absorber, not a profit source.** It has a third of the gearing (0.19 % of premium per Nifty point against 0.62 %). On 3 Nov it cut the loss from -40 % to -5 %, but on 9 Nov it cut the gain from +31 % to +6 %. Over 39 Conductor trades it lowered the strike rate from 53.8 % to 51.3 % and the compounded result from +63 % to +55 %.
7. **The Conductor's trouble is the normal day, not the greeks.** Normal days: 39 trades, 35.9 % won. Day before expiry: 14 trades, 92.9 % won. Expiry day: 66 trades, 54.5 % won. Its delta, IV and gearing on normal days look the same as on the good days. What differs is direction.

## Teardown

### What the code does

| Place | What it does | Problem |
|---|---|---|
| `apex/greeks.py:43-47` | Calendar years to 15:30 on expiry. Floor of 600 s on expiry day, 60 s otherwise. | Fine. The floor caps gamma in the last 10 minutes. |
| `apex/greeks.py:68-107` | IV by 40 steps of bisection on the Black-76 premium. Invalid when the premium is at or below intrinsic + 0.05. | 40 full erf passes per option per tick. A Newton step warm-started from the last second's IV needs 2 or 3 (see the speed idea). |
| `apex/greeks.py:124` | `theta_min = theta_year / 365 / 375` (the "kit" clock, 3.84 x calendar). | Right on normal days and the day before expiry. About 4 to 5 x too big on expiry day (Evidence B). |
| `apex/greeks.py:126-129` | Without an IV (deep ITM, or a premium at intrinsic), delta is forced to 0.99 and gamma, theta and vega to 0. | A two-strikes-ITM contract on expiry afternoon can show zero theta and zero gamma. Any picker that scores theta per rupee then prefers it for the wrong reason. |
| `apex/engine/weather.py:644-649` | `theta_be = abs(theta_min) / abs(delta)`, `theta_ratio = theta_be / speed15`. | Two errors. (a) It ignores gamma, which on normal days repays about 70 % of the theta. (b) It compares a needed drift (net points per minute) with `speed15`, the mean absolute one-minute move, which is mostly noise. The ratio is around 0.01 to 0.1 and does not sort trades (Evidence C). On expiry day it also carries the 4 to 5 x theta error. |
| `apex/engine/weather.py:152` and `apex/engine/edge.py:10` | Realised vol is annualised over 252 x 22,500 trading seconds. IV is annualised over calendar time. `e_iv_rv = iv / rv`. | It mixes two clocks, so the ratio is about 1.6 even when options are fairly priced. In the same per-minute units, realised is about 0.85 of implied on normal days (Evidence C). |
| `apex/engine/council/c20_08.py:62-82` | `_pick`: the strike whose abs(delta) is closest to `dt` (0.60 normal, 0.65 expiry), with abs(delta) >= 0.52, among ATM +-3 strikes. The expected-return score is computed and then overwritten when `dt > 0`. | The theta and gamma terms are dead code. Strike choice is a fixed delta target. |
| `apex/engine/council/c20_8x.py:50-51` | Part `d52` sets the normal-day target to 0.52, which is near ATM. | Normal-day pool trades sit at a median abs(delta) of 0.54. |
| `apex/engine/council/c20_9x.py:311-332` | Expiry picker `tie`: expected capture minus 5 x 100 x abs(abs(delta) - 0.65). It uses kit theta x 0.26 (= calendar). | It is the one place that already uses the right expiry clock. The median expiry abs(delta) is 0.65 to 0.67. |
| `apex/engine/council/c20_9x.py:435-441` | Expiry rent stop `uw`: gamma rent divided by `CAL` (375/1440). | Correct clock. |
| `apex/engine/paper.py:632` | `req_move_veto`: need = 10 % of ask minus 15 x `theta_min`. | Kit theta on expiry day: the needed move is overstated (affects the books that switch this on). |
| `apex/engine/paper.py:649-660` | `buyer_edge_gate`: 0.5 x gamma x v_min30 / abs(theta_min) >= gt_min. | Right on normal days. On expiry day the ratio is about 4 x too low, so it over-vetoes there. |
| `apex/engine/commentary.py:705-712` | Commentary "theta bill": spot must move theta / delta points a minute. | On expiry day it tells the owner the rent is 4 to 5 x what the market is charging. `apex/engine/cmt_hold.py:20-22` already knows this and corrects only its own display. |

### Where it fails, in one line each

* It has no single source of truth for "theta per minute right now". There are three: kit, kit x 0.26, and kit corrected for display only.
* `theta_be` and `theta_ratio` are on the photograph and in the Forecast Lab feature list (`apex/conductor/search.py:89`), but they measure the wrong thing.
* Strike choice is a fixed delta target that does not depend on the day type, the expected hold or IV, except for the expiry tie-breaker.

## Evidence

### A. The calculus of the break-even

The premium V(F, t, sigma) of a long option, over a short hold of h minutes, by Taylor (Ito) expansion:

dV = Delta dF + 1/2 Gamma dF^2 + Theta dt + Vega dsigma

Let the underlying drift be mu points per minute in the trade's direction, with per-minute noise s (points). Then E[dF] = mu h and E[dF^2] = s^2 h + mu^2 h^2. With sigma held fixed:

E[dV] / h = |Delta| mu + 1/2 Gamma (s^2 + mu^2 h) - theta

* **Drift break-even with no noise (s = 0, h small):** mu* = theta / |Delta|. This is the weather's `theta_be`.
* **Noise break-even with no drift (mu = 0):** s* = sqrt(2 theta / Gamma). Under Black-Scholes, theta = 1/2 Gamma F^2 sigma_imp^2 per unit time. So the noise term pays the theta exactly when realised variance equals implied variance on the same clock.
* **The honest break-even** puts both together: mu* = (theta - 1/2 Gamma s^2) / |Delta|. Gamma repays part of the rent, and only the rest has to come from drift.

So `theta_be` is an upper bound that drops the gamma credit. And `theta_ratio = theta_be / speed15` divides a drift by a noise level, which is not a break-even test.

Medians for the five pool books at entry (543 trades). "Kit" theta is the engine's number. "Calendar" is kit x 375/1440.

| Item | Normal | Day before | Expiry |
|---|---|---|---|
| Entry premium | 195.1 | 135.4 | 94.65 |
| abs(delta) | 0.542 | 0.564 | 0.653 |
| Kit theta, pts/min | 0.0458 | 0.1047 | 0.4833 |
| Calendar theta, pts/min | 0.0119 | 0.0273 | 0.1259 |
| Weather theta_be, pts/min | 0.081 | 0.193 | 0.740 |
| speed15 (mean abs 1-min move), pts | 6.34 | 8.22 | 6.14 |
| Gamma credit / calendar theta | 2.75 | 2.26 | 0.72 |
| Gamma credit / the theta the market charges (Evidence B) | about 0.72 | about 0.59 | about 0.7 to 0.9 |
| Honest drift break-even, pts/min | about 0.023 | about 0.08 | about 0.05 to 0.06 |
| Theta paid over the hold, kit, % of premium | 0.41 | 0.99 | 2.31 |
| Theta paid over the hold, right clock, % of premium | 0.41 | 0.99 | about 0.45 to 0.6 |
| Spread, % of premium | 0.22 | 0.24 | 0.26 |
| Median hold, min | 18.4 | 12.1 | 4.8 |

The weather's expiry `theta_be` of 0.74 points a minute should be about 0.13 to 0.19. The honest break-even drift is a few hundredths of a point a minute. That is far below the usual drift at a c20 entry: the median 5-minute move is 13 to 18 points.

### B. Which theta clock the market uses (a6_theta_clock.py, all 107 books, 17 days)

If premiums decay K times faster than calendar time, an IV computed with calendar time falls while the trade is held, at about d sigma / dt = -sigma (K - 1) / (2 T), with T in calendar hours (ATM, premium proportional to sigma sqrt T). I regressed (iv_out - iv_in) on hold hours and on the futures move, by day type and side.

| Day type | Side | Trades | T (hrs) | sigma | Measured slope, vol pts/hr (se) | Kit-clock prediction | Implied clock, x calendar |
|---|---|---|---|---|---|---|---|
| Normal | CE | 3,336 | 123 | 15.0 | -0.169 (0.019) | -0.172 | 3.79 |
| Normal | PE | 3,399 | 124 | 15.3 | -0.239 (0.016) | -0.175 | 4.89 |
| Day before | CE | 1,305 | 29 | 18.2 | -0.768 (0.040) | -0.890 | 3.45 |
| Day before | PE | 973 | 28 | 18.2 | -0.797 (0.042) | -0.911 | 3.48 |
| Expiry | CE | 2,315 | 3.9 | 32.7 | +1.140 (0.337) | -12.05 | 0.73 |
| Expiry | PE | 1,978 | 3.5 | 32.2 | +0.035 (0.304) | -13.11 | 0.99 |

The kit clock (3.84) fits normal days and the day before expiry. Calendar time fits expiry day. A direct check on 3 Nov agrees: the decay of the ATM straddle not explained by delta and gamma was 0.66 x calendar theta (se 0.13), over 345 five-minute windows. On 6 Nov (T = 3 days) the same test was too noisy to read (se 2.95). Caveat: an intraday IV seasonal could imitate this. But the fit to a zero-parameter prediction across three day types is close.

The same regression gives the spot-vol link: on expiry day IV rises with a move in the option's favour (CE +1.49 vol pts per 100 futures points up; PE +3.84 per 100 down). On normal days it is smaller (PE +0.31 per 100 down; CE +0.07).

### C. Results by greek and IV bucket (whole table, in sample)

Pool books (543 trades, 5 books, overlapping):

| abs(delta) at entry | n | Won % | Mean % |
|---|---|---|---|
| up to 0.55 | 143 | 56.6 | 7.90 |
| 0.55 to 0.60 | 113 | 59.3 | 11.94 |
| 0.60 to 0.65 | 120 | 51.7 | 2.37 |
| 0.65 to 0.70 | 128 | 60.9 | 5.66 |
| 0.70 to 0.80 | 39 | 66.7 | 5.81 |

| IV change entry to exit (after the fact) | n | Won % | Mean % |
|---|---|---|---|
| below -1 | 56 | 35.7 | -7.1 |
| -1 to -0.3 | 87 | 47.1 | -2.10 |
| -0.3 to +0.3 | 238 | 48.3 | 0.76 |
| +0.3 to +1 | 92 | 79.3 | 18.48 |
| +1 to +2 | 37 | 86.5 | 20.98 |
| above +2 | 33 | 100.0 | 49.58 |

Conductor (119 trades): IV vs the day's median above +1 vol point: 32 trades, 43.8 % won. Between -0.3 and +0.3: 29 trades, 58.6 % won. ATM IV up more than 0.5 in the last 5 minutes (pool): 66 trades, 39.4 % won, mean -1.47 %. These look like filters. They are not: see D.

The correlation of the IV change with the trade return is 0.21 on normal days, 0.38 on the day before and 0.34 on expiry day (all books). The best ex-ante predictors of the IV change that kept their sign from discovery to test (Spearman; 108 pairs tried) were all weak:

| Day type, side | Item | rho discovery | rho test |
|---|---|---|---|
| Day before, PE | iv_in | -0.198 | -0.276 |
| Expiry, PE | iv_spot_corr15 | +0.171 | +0.155 |
| Expiry, CE | iv_in | -0.154 | -0.149 |
| Day before, PE | term_atm | -0.143 | -0.227 |
| Expiry, PE | opt_iv_chg5 (IV mean-reverts) | -0.186 | -0.137 |

None of the honest break-even items sorted trades on the test days either: edge rate, gamma credit, realised-to-implied in the same units, drift over theta_be, or the weather's theta_ratio. The quintiles were set on the early days, and the test-day strike rates by quintile jump around with no order (a5_out.txt).

### D. Walk-forward filter search (a2_table.py section 6)

Discover on 19 Oct to 4 Nov, test on 5 to 12 Nov. The filter keeps at least 60 % of discovery trades. A dropped trade means staying flat (an approximation: the Conductor might have taken another book's trade). 30 greek and IV items, 9 thresholds, 2 sides: 538 variants per sample, 3 samples.

Conductor test days: 35 trades, 51.4 % won, log growth 1.101 (+200.7 %), 2 losing days out of 5.

| Item, chosen on discovery | Test trades kept | Test won % | Test log growth | Test days better / worse |
|---|---|---|---|---|
| atm_iv_day_pos < 0.888 (top discovery gain) | 34 of 35 | 52.9 | 1.283 | 1 / 0 |
| atm_iv_chg5 < 0.434 | 29 | 51.7 | 0.949 | 0 / 1 |
| iv_vs_med < 1.98 | 27 | 51.9 | 0.554 | 0 / 1 |
| theta_ratio < 0.21 | 34 | 50.0 | 1.072 | 0 / 1 |
| moneyness < 73 pts | 24 | 45.8 | 0.520 | 0 / 2 |
| abs(delta) < 0.689 | 32 | 56.2 | 1.500 | 1 / 0 (ranked last on discovery) |

The top discovery choice changes one test trade. With about 1,600 variants tried in all, that is noise. **Verdict: no greek or IV entry filter is supported.**

### E. Repricing other contracts at the same seconds (a3_reprice.py, ds_v2, 3 Nov, 6 Nov, 9 Nov)

The return is exit bid / entry ask - 1, at the trade's own entry and exit seconds. Quotes older than 10 s are not used. The repriced base trade matches the recorded return within a median of -0.26 percentage points. Conductor trades: 39 (13 on 3 Nov, an expiry day; 4 on 6 Nov, the day before the 9 Nov expiry; 22 on 9 Nov, an expiry day).

| Contract | Won % | Mean % | Compounded % | Median abs(delta) |
|---|---|---|---|---|
| As traded | 53.8 | 2.84 | 63.3 | 0.57 |
| One strike deeper ITM | 59.0 | 3.12 | 112.5 | 0.61 to 0.79 |
| Two deeper ITM | 53.8 | 2.57 | 90.7 | 0.66 to 0.88 |
| One strike toward OTM | 53.8 | 2.87 | 35.9 | 0.48 |
| Next weekly, same strike | 51.3 | 1.41 | 57.9 | 0.53 |
| Next weekly, delta-matched | 51.3 | 1.36 | 55.3 | 0.54 to 0.67 |

Per day, compounded %:

| Day | Trades | As traded | Deeper ITM | Two deeper | Toward OTM | Next weekly, delta-matched |
|---|---|---|---|---|---|---|
| 3 Nov (expiry) | 13 | -40.0 | -26.2 | -22.2 | -52.6 | -5.2 |
| 6 Nov (day before) | 4 | +107.6 | +98.4 | +89.8 | +113.6 | +54.9 |
| 9 Nov (expiry) | 22 | +31.0 | +45.2 | +29.2 | +34.4 | +5.7 |

On these trades the deeper strike works as a variance reducer. Losers averaged -8.96 % instead of -11.60 %, and winners +13.47 % instead of +15.21 %. On expiry day it also pays less theta per hour (4.8 % against 7.3 % of premium) and less vega (1.13 % against 1.80 % per vol point). On 6 Nov (DTE 3) it was worse on all 4 trades.

The five pool books on the same 3 days (181 trades) tell the same story. Deeper ITM won 58.6 % against 54.1 %. It was better on 52 % of 3 Nov trades, 12 % of 6 Nov trades and 60 % of 9 Nov trades.

Policy table (phaseB_strike_policy.py, run now on the 3 days; 37 variants): "deeper ITM on expiry day only" gave test days (6 and 9 Nov) +201.5 % against +172.0 %, a 61.5 % strike rate against 53.8 %, no losing day, and +76.1 % against +58.8 % without the best trade. The gain came on one test day (9 Nov). It needs the 16-day run.

Mid-to-mid attribution of the as-traded contract (Conductor, 39 trades, median hold 5.3 min), as % of entry mid: delta +3.12, gamma +0.84, calendar theta -0.93, vega +0.17, residual -0.10, half-spread cost 0.27. The engine's kit theta would have claimed -3.55.

### F. Gearing as leverage (a7_kelly_gearing.py)

Without position sizing, the strike is the only leverage dial. The option's elasticity Omega = abs(delta) x F / premium is the account's exposure to a 1 % Nifty move. The medians are 65 on normal days, 90 the day before expiry and 166 on expiry day. I scaled each Conductor trade's return by lambda, as a first-order stand-in for a different strike, and found the growth-best lambda.

| Sample | Kelly lambda, discovery | Kelly lambda, test |
|---|---|---|
| All trades | 2.0 (edge of grid) | 1.85 |
| Expiry day | 1.6 | 1.1 |
| Day before | 2.0 | 2.0 |
| Normal day | 1.9 | 0.5 |

Read it carefully. Linear scaling ignores that a nearer-the-money strike also changes theta and gamma, and the repricing in E (toward OTM was worse on 2 of 3 days) shows that. The robust messages: gearing is about right on expiry days. The day before expiry wants more. On normal days the edge is too thin and unstable to bear the present gearing (1.9 on discovery, 0.5 on test).

## Ideas

| # | Idea | Kind | Tested? | Confidence |
|---|---|---|---|---|
| 1 | One honest theta clock | data, guard, ui | Clock tested (B). Profit effect untested. | high |
| 2 | Expiry-day one-strike-deeper shadow book | selection | 3 days repriced, 2 expiry days both better | medium |
| 3 | Honest break-even card for the forecaster and commentary | ui, commentary | Display only | medium |
| 4 | IV-change watch as a hold and exit input | hold, exit | Untested | low |
| 5 | Next-weekly "low-conviction" mode | selection | 3 days, mixed | low |
| 6 | Warm-started Newton IV for speed | speed | Untested (operation count only) | high |
| 7 | Retire theta_ratio, theta_be and e_iv_rv as features, or rebuild them | data | Walk-forward shows no signal | medium |
| 8 | Day-before-expiry gearing up | selection | In sample only, 3 days | low |

### 1. One honest theta clock
* **Mechanism.** Add `theta_min_mkt` to `apex/greeks.py`: kit theta when DTE >= 1, kit x 375/1440 on expiry day. Evidence B says that is the clock the market charges.
* **Build.** Do not change `theta_min`, because books were fitted on it. Add the new field and switch only the observers to it first: the weather (`theta_be`, `theta_ratio`, `theta_be15`), the commentary "theta bill" and `cmt_hold`. Then a shadow copy of any book using `req_move_veto` or `buyer_edge_gate`, gated on the new field on expiry day.
* **Risk.** Low for the display. A gate change can alter expiry-day entries, so it goes through a shadow book first.
* **Speed.** One multiply.

### 2. Expiry-day one-strike-deeper (shadow book `c20_9y_x1`)
* **Mechanism.** On expiry day the next strike in (abs(delta) about 0.75 to 0.79) pays about a third less theta per hour and much less vega per rupee. It loses less on the losers and gives up a little on the winners. Under all-in compounding that lowers volatility drag.
* **Test.** 2 of 2 expiry days better (-40.0 to -26.2, +31.0 to +45.2). The normal day was worse.
* **Build.** Subclass the c20_9x `tie` picker with target 0.65 to 0.75 on `D.dte0` only. Exits stay the same: the forward trail is in futures points, so it is strike-free.
* **Risk.** Exits that depend on the premium path (premium trail `ptr`, `sl` at 15 % of the ask) fire at different times on a deeper strike. The repricing holds the exit second fixed. A shadow book is required. Run phaseB_reprice_all.py, then phaseB_strike_policy.py first.

### 3. Honest break-even card (owner point 4)
* **Mechanism.** The forecaster takes a stand in its own words, built from the calculus in A. For example: "I hold the 25,600 CE, delta 0.66. The market charges me 0.13 points a minute. Gamma is paying back 0.09 of that. Nifty needs only +0.04 points a minute my way, and it is doing +2.1. IV is up 0.4 since I bought, with the move, so vega is helping. I stay." On a flat book: "A 0.65-delta CE here needs 6 points in 10 minutes to clear the spread and the rent."
* **Build.** Display change in the Forecast Lab and `commentary.py`, using `theta_min_mkt`, gamma and realised per-minute sd from `rv5`.
* **Risk.** None to trading.

### 4. IV-change watch for holds and exits
* **Mechanism.** The IV change after entry is the second-biggest driver of the result, and on expiry day it moves with spot (+1.5 vol pts per 100 points for CE, +3.8 for PE). When IV falls while spot moves our way, the option underperforms its delta. That is a "the move is not being paid" signal for an earlier exit. A rise lets a trade breathe.
* **Build.** Shadow exit: on a trade up in futures points, tighten the trail when IV since entry is below -0.5 vol pt and premium gain is below delta x the move. Test it on the h<mark>_attr_iv_chg hold marks, walk-forward.
* **Risk.** It is fitted on after-the-fact IV. Weak ex-ante predictability (rho of 0.2 at best) is a warning.

### 5. Next-weekly low-conviction mode
* **Mechanism.** It has a third of the gearing and five times the vega per rupee. It halved the damage on 3 Nov and cut the gains on 9 Nov.
* **Build.** Use it only as an option for the Conductor on a signal it rates weak (for example an expiry-day trade after two losses). It is untested as a rule.
* **Risk.** It gives up the core edge of weekly gamma on good days.

### 6. Faster IV (owner point 6)
* **Mechanism.** `implied_vol` runs 40 bisection steps with 2 erf calls each, for every quoted option every tick. A Newton step on sigma with vega, warm-started from the same contract's IV one second earlier, converges in 2 or 3 steps to under 1e-6 vol, which is about 10 to 15 times fewer erf evaluations. Fall back to bisection when a step leaves [0.005, 5] or vega is under 1e-3. Jäckel's "Let's Be Rational" gives machine precision in 2 steps from a cold start. Open versions: https://github.com/vollib/lets_be_rational and https://github.com/vollib/py_vollib (paper: http://www.jaeckel.org/LetsBeRational.pdf). For a vectorised NumPy reference: https://github.com/vollib/py_vollib_vectorized. QuantLib (https://github.com/lballabio/QuantLib) is heavier and not needed.
* **Build.** A drop-in function behind a flag. Check it bit-for-bit against bisection to 1e-6 vol on a replay (phase B, outside market hours).
* **Risk.** Low if it is checked against the old values. No timing was measured today (the machine is loaded).

### 7. Retire or rebuild the theta items in the feature list
`theta_ratio`, `theta_be` and `e_iv_rv` are each a mismatch of units or clocks (Teardown). Replace them with: honest drift break-even = (theta_mkt - 1/2 Gamma s^2) / abs(delta); gamma credit = 1/2 Gamma s^2 / theta_mkt; and realised over implied on the same per-minute clock. Even rebuilt, they did not sort trades walk-forward (C). They are honest display items, not entry rules.

### 8. More gearing on the day before expiry
14 Conductor trades, 92.9 % won, and Kelly lambda about 2 in both windows. But that is 3 days, all in sample, and 6 Nov's 4 trades were better toward OTM (+113.6 % against +107.6 %). Watch it, do not promote it.

## Phase B scripts (ready, not run; run after 15:30, one at a time)

| Script | What it does | Expected run |
|---|---|---|
| `D:\ApexOptions\data\research\13nov\work\R06\phaseB_reprice_all.py` | Reprices every Conductor and pool-book trade on all 16 ds_v2 days (12 Nov has no ds_v2) at other strikes and the next weekly. Builds the straddle theta clock and the IV path per day, then aggregates. Skips days already done. | About 1 to 2 min per day on an idle machine, sequential. |
| `D:\ApexOptions\data\research\13nov\work\R06\phaseB_strike_policy.py` | Walk-forward test of 13 strike and expiry policies on the repriced Conductor trades: strike rate, compounded %, losing days, worst day, without the best trade, without the best day. | Seconds. Already run on 3 days (policy_3days.txt). |

## Scratch files

All in `D:\ApexOptions\data\research\13nov\work\R06\`: `a2_out.txt` (buckets, IV drift, walk-forward), `a4_out.txt` (repricing, attribution, theta clock), `a5_out.txt` (honest break-even, IV-change predictors), `a6_out.txt` (theta clock inference), `a7_out.txt` (gearing), `policy_3days.txt`, `reprice_11-03.csv`, `reprice_11-06.csv`, `reprice_11-09.csv`, `conductor_joined.csv`.

Multiple testing: about 1,600 filter variants (D), 108 predictor pairs (C), 37 strike policies (E), 34 gearing levels (F). Only finding B (the theta clock) and the "no filter works" result are robust. Idea 2 rests on 2 expiry days.
