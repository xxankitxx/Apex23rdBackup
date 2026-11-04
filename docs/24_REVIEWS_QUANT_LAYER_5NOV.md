# The reviews' advanced models: built, tested, and what they are worth (5 Nov 2026)

Owner: *"Read all documents in reviews folder. Implement them in this code and further improve the code ... the most
advanced model in option which does not miss out on good opportunities and never takes in a loss-making trade nor
a non-mover trade ... the code should be superfast in displaying everything tick-by-tick."* Slippage and brokerage
items from the reviews are left out by the owner's instruction; all-in on every trade is unchanged.

Read: `reviews/Apex_Quantitative_Teardown.docx` (text and all 22 figures), `chatgpt_5th_advanced.txt` (the same
teardown as text), `deepseek_5th.txt`, `deepseek_5th_advanced.txt`.

## 1. What was built — `apex/quant/` (32 tests, all streaming)

| Review item | Module | What it computes |
|---|---|---|
| Higher-order Greeks, full repricing | `greeks_hi.py` | Black-76 to third order: vanna, vomma, charm, speed, color, zomma, ultima (each checked against a finite difference), exact repricing, the second-order cross Taylor expansion, the forward level where an option is worth a given premium. The real contract clock (`real_years`) is kept apart from the IV solver's 600-s floor; r = 0 throughout (the forward carries the carry), so pricing, IV and parity share one convention. |
| Premium outcome / competing-risk model | `passage.py` | P(target before stop) and P(by 1, 3, 5, 10, 15 min) for buying a given option now: barriers from full repricing, Brownian forward with drift and jump-robust noise, theta as a headwind, two-barrier exit densities (method of images for short times, eigenfunction series for long ones). Checked against the scale function, the inverse-Gaussian limit and a Monte Carlo. |
| Hawkes process | `hawkes.py` | Exponential-kernel intensity with an O(1) update, exact MLE on event times, binned MLE on per-second counts (linear IIR filter), Ogata simulation for tests. |
| Hidden (semi-)Markov regime | `regime.py` | Gaussian HMM, Baum-Welch with restarts, Viterbi, causal forward filter, and the semi-Markov layer: expected remaining duration of the current state from empirical run lengths. |
| Jumps, CUSUM, Kyle lambda, Kalman | `micro.py` | Bipower variation and the Huang-Tauchen jump z (on real price changes only), two-sided CUSUM, rolling Kyle lambda, local-linear-trend Kalman velocity. |
| SVI surface and residuals | `svi.py` | Raw SVI by the quasi-explicit (Zeliade) calibration, batched linear least squares, ~1 ms per smile; residual per strike in vol points. |

Live, display only: `apex/engine/quantview.py` runs once per second inside the engine's fault guard and the
dashboard's open-interest card shows a **Quant evidence** block: the premium race for the ATM call and put, Hawkes
buy/sell excitation, jump z and drift-change alarm, the regime posterior with minutes left, third-order Greeks for
the held option (else the ATM pair), and the smile residuals. Parameters: `apex/quant/params.json` (fitted on the
twelve taped days: Hawkes branching 0.86, half-life 84 s; four regimes lasting 2-3 min on average).

## 2. Every model as a yes/no rule on c20_9y (offline kit, 12 days, 19 Oct - 4 Nov)

Each day's Hawkes kernel and regime model were fitted on the OTHER eleven days. c20_9y: +12,32,085, 69 trades, 28
losers; the five never-fitted days (29 Oct - 4 Nov) +13,419.

| Rule (one quantity, one threshold) | Best setting | 12 days | Never-fitted days | Verdict |
|---|---|---:|---:|---|
| Premium race: P(+10 % before -10 % within h) >= p | 300 s, 0.10 | +10,95,819 | +34,635 | loses 1.36 L; every setting loses |
| Premium race, eventually | 0.50 | +9,45,103 | +208 | loses |
| Hawkes buy/sell excitation on the bought option | 0.75 | +11,31,897 | -5,213 | loses; 1.25 keeps only +2.1 L |
| Regime: most likely state's drift must agree | — | +2,68,700 | -23,904 | loses 9.6 L |
| Regime ageing: expected minutes left >= r | 2 | +12,39,407 | +20,741 | +7.3k from one trade; 3 -> +8.55 L: a cliff |
| Jump z of the last 5 min <= z | 10 | +12,28,650 | +13,419 | nothing; 6 -> +6.9 L |
| Kalman velocity t-stat agrees | 1.0 | +9,80,983 | +19,981 | loses 2.5 L |
| Exit when the remaining race P < p (opportunity decay) | 0.10, after 300 s | +5,95,654 | -38,110 | loses 6.4 L; adds 18 trades and 14 losers |

Premium race as an ENTRY engine (the reviews' opportunity detector, "Model A"), to trade more often:

| Book | Trades | Losers | 12 days |
|---|---:|---:|---:|
| Scanner alone, +10 % target, X = 0.8 | 604 | 318 | -1,24,725 |
| Scanner alone, 5 % trail after +10 %, X = 0.8 | 551 | 292 | -1,93,056 |
| c20_9y + scanner when c20_9y is flat, X = 0.8 | 506 | 272 | +73,639 |

**Why: the probabilities are not calibrated.** On 17,484 samples the option at the ask reached +10 % before -10 %
within 5 min 20 % of the time, and that rate barely moves with the model's prediction: predicted 0-10 % -> 17 %,
40-60 % -> 22 %, 90-100 % -> 23 %. The mathematics is right (it matches its closed forms and a Monte Carlo); its
drift input is not. A Kalman velocity on the one-second forward does not forecast the next five minutes, so a
premium-outcome model fed by it is a fair-odds calculator (strike, theta, vol), not a signal. Hawkes and regime
inputs hit the same wall: on these twelve days they do not separate the runners (the whole profit) from the duds.

No new trading book was registered. c20_9x stays champion, c20_9y the best shadow (docs/23). The reviews' own test
(teardown §9.1, "every technique must pass four tests") is what these models failed; the library stays so they can
be re-tested as days accumulate, and the live panel lets the owner watch them in real markets.

## 3. Bugs found and fixed on the way

* **c20_9y faulted on its first live second**: the engine's `LiveDay` had no `i_at` (the kit's `D` does), so the
  shadow book registered on 4 Nov would never have traded. `LiveDay.i_at` added; `tests/test_c20_9y.py` now runs
  the book on a real `LiveDay`.
* **NaN inside a published numpy array** crashed the state write (`_default` let plain NaN floats through).

## 4. Speed (tick-by-tick display)

Engine profile, 4 Nov 09:15-10:30 tape (cProfile): building and serialising the dashboard state was 25 % of engine
time, and its NaN scrub `clean()` alone made 69 million recursive calls (3,370 per publish); a kill-switch file stat
ran every 100-ms step at ~1.7 ms; every council book filled its own identical copy of the live day (~9 per second).
Fixed without changing any decision:

* `StateBlob.write_state`: serialise directly; only an output that holds a NaN/Infinity token is re-serialised from
  the cleaned copy. Byte-identical (tests/test_state_fastpath.py).
* Kill-switch file checked at most twice a second.
* One shared `LiveDay` per (day, expiry) for all council books (strategies only read it).

Live engine ticks on 4 Nov ran p50 50-75 ms with p95 up to 1.07 s against a 100-ms budget, so on busy minutes
only ~350 of 600 ticks ran.

## 5. Replay check (same tape slice, old code vs new code, each in its own shared memory)

| | old code (d8a3423) | new code |
|---|---:|---:|
| engine time per step (fast replay, 09:15-10:30, 66,647 steps) | 23.69 ms | 20.59 ms (-13 %) |
| books with identical trades | — | 72 of 72 (97 trades, 0 differences) |
| c20_9y | faulted at 09:14:59 (`i_at`) | runs |

The live quant view adds ~12 ms once per second and ~25 ms once a minute for the smile (measured on a loaded
machine), about 1 % of engine time.

## 6. What the owner asked for that mathematics cannot give

"Never takes a loss-making trade" and "never misses a good opportunity" pull against each other, and on these
tapes no causal model separates the runners from the losers early: every filter that cut losers cut the runners
that make the money, and every engine that traded more often added more losers than winners. The honest objective
is the reviews' own: more profit per day out of sample, measured on days no rule was fitted to.
