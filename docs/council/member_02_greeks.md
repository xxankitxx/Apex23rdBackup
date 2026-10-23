# Member 02 — Option pricing, IV and Greeks

## Lens
`apex/greeks.py` (Black-76, bisection IV, synthetic forward, time convention, theta per minute), `compute_greeks` in `apex/engine_main.py:331-365`, delta-band contract choice in `apex/engine/paper.py:98-132`, and where the Greeks feed into decisions: `straddle_watch.py` (theta-expected path, spike measure), the `room` advisor (`engine_main.py:413-418`), `gex.py`. Baseline 85b65ed. Probes: `/tmp/council/02/probe.py` and `probe2.py`, checked against `scipy.special.ndtr`. `tests/test_core.py` passes.

**Context that matters:** Monday 19 Oct 2026 is an expiry day, because Tuesday 20 Oct is a holiday and `weekly_expiries` rolls the expiry back. The first live session is therefore a 0DTE session.

## Teardown

**T1. Theta per minute uses two clocks, so the straddle's expected decay is 3.8x too fast. On 0DTE this is plainly wrong. Severity: high (for Monday).**
- **Where:** `greeks.py:91` computes `theta_min = theta_year / 365 / 375`. But T is calendar time (`greeks.py:43-47`), and `straddle_watch.py:136` and `:185` add `theta_min` up per wall-clock minute.
- **Probe (constant IV, ATM straddle, F = 25,000).** Model change over the next 5 minutes, against `theta_min x 5`:

| Time | Model 5-min change | theta_min x 5 | Ratio |
|---|---|---|---|
| Thu, 5 DTE | -0.10 | -0.40 | 3.84 |
| Mon, 1 DTE | -0.21 | -0.81 | 3.84 |
| 0DTE 10:00 | -0.49 | -1.89 | 3.83 |
| 0DTE 13:00 | -0.74 | -2.80 | 3.81 |
| 0DTE 14:45 | -1.37 | -5.12 | 3.73 |

- **On non-expiry days**, dividing by 375 is a defensible guess: it assumes all overnight decay happens in the session. But it is the opposite extreme of the calendar clock that IV is solved on. D-032 says "one variance clock", and this is two.
- **On expiry day** there is no overnight. All remaining T is session time, so the only consistent wall-clock rate is `theta_year / (365 x 1440)`.
- **Failure scenario:** At 0DTE 14:45 a straddle that does not move at all shows `excess = 0 - (-5.1) = +5.1` points. That is above the `SPIKE_MIN_PTS = 4.0` floor (`config.py:136`). The quiet-time sigma EWMA (`straddle_watch.py:192-195`) absorbs part of this bias. But the bias grows through the afternoon (+1.4 at 10:00, +3.7 at 14:45 against the correct model), so the effective spike threshold drops exactly when gamma is highest.
- **Who is affected:** the `straddle_spike` variant, the `gamma_leg` advisor, the premium "DECAYING/FLAT" state and the `room` advisor (`theta x 5` term, small).
- **Verified:** probe, for the bias. **Not verified:** the actual change in Monday's spike count.

**T2. On 0DTE, delta is very sensitive to error in the synthetic forward, and the forward accepts stale LTPs. Severity: medium.**
- **Where:** `engine_main.py:345` falls back to `ltp` whenever bid or ask is missing, with no check on `recv_ns` age. `synthetic_forward` (`greeks.py:100-113`) averages parity at the two nearest strikes and rejects a result only if it is more than 150 points off spot.
- **Probe, 0DTE 12:00, IV 13%:**
  - The 24950 CE delta is 0.78 at F = 25,000, 0.86 at F = 25,020 and 0.92 at F = 25,040. So a 20-point forward error moves the contract out of the `zero_am` band (0.65-0.85).
  - One leg with an LTP 12 points stale shifts F by 6 points.
- **Why 150 is too loose:** it is roughly 2 standard deviations of the full day's move. The age filter in `choose_contract` (`paper.py:125`, `age < 15`) applies only to the chosen option, not to the legs that set F.
- **Fallback bias:** the fallback `ref` is spot (`engine_main.py:333`), not the forward. When parity fails, every delta carries the cost-of-carry bias, about 27 points at 6 DTE in my probe.
- **Verified:** probe and read.

**T3. D-020 is marked DECIDED, but three of its parts are not built. Severity: medium.**
- **What D-020 lists:** "mid-price IV with uncertainty band ... charm/vanna ... sticky-IV P&L attribution" (`docs/02_DECISION_LOG.md:28`).
- **What the code has:** `grep -i 'vanna|charm|attribution|iv_bid|uncertainty' apex` finds nothing. Only a single mid IV exists.
- **Why it matters:** without an IV band from bid and ask, `iv_late` (`engine_main.py:408`) cannot tell a real IV rise from a spread widening. Without attribution, the learning loop cannot say whether a trade lost to IV, theta or direction. That is the question D-019 claims is the buyer's real enemy.
- **Verified:** read and grep.

**T4. The 0DTE 14:45 "no entry" branch does nothing different from the 13:00 branch. Severity: low.**
- **Where:** `paper.py:114-117`. Both branches set `week, band = 1, nextweek`.
- **Docs disagree with each other:** `01_MASTER_DESIGN.md:162` and D-021 say "none after 14:45", while `:233` says only "no 0DTE entries".
- **The code:** still allows next-week entries from 14:45 to 15:15. It also never offers the "0DTE at delta ≥ 0.8" option discussed in OQ-8.
- **Owner decision needed:** confirm the intent and either delete the branch or `return None`.
- **Verified:** read.

**T5. The fallback in `choose_contract` has no upper delta bound. Severity: low.**
- **Where:** `paper.py:129-131`. If nothing is inside the band, the code takes the smallest delta at or above `lo`, which can be 0.95, or the forced 0.99 for invalid-IV deep ITM (`greeks.py:94`).
- **When it happens:** on 0DTE late morning. With strikes 50 apart and a 1-sigma remaining move of about 58 points at 12:45, the 0.65-0.85 band can contain zero strikes. The pick then jumps to a strike about 100 points ITM, under all-in sizing.
- **The cost:** under all-in sizing, strike choice is position size. It is not catastrophic, but the jump should be logged.
- **Verified:** read plus arithmetic.

**T6. An expired expiry is still priced, with T floored at 60 s. Severity: low.**
- **Where:** `greeks.py:46`. On any day after expiry, `years_to_expiry` returns 60 s instead of raising an error.
- **When it bites:** if a registry ever survives past 15:30 of expiry day (a long-running feed, or replay across days), `w0` becomes an expired chain. The ATM, the heroes and the deltas would then all come from dead contracts. `weekly_expiries` rolls off correctly at build time.
- **Verified:** the 60 s return is probed. That a stale registry can actually occur is unverified.

**Checked and correct** (verified against ndtr):
- The A&S erf price error is at most 0.001 points at F = 25,000.
- The IV round trip is exact to 0.001 vol points for 6 DTE, 3 h and 20 min, deep OTM to ATM.
- Delta matches to 1e-5.
- The bisection range [0.5%, 500%] covers 0DTE: a 20-minute OTM option at 3 points solves to 141%.
- The 600 s floor only matters after 15:20, by which time 0DTE positions are already flat at 15:00.

## Good things
- **Black-76 on a parity forward per expiry** (`greeks.py:100-113`; `engine_main.py:350`, solved separately for w0 and w1). This removes basis and carry bias. My carry probe recovered the true forward exactly.
- **Vectorised bisection, not Newton** (`greeks.py:61-75`). It does not blow up as vega goes to 0 near expiry, and 40 iterations give about 1e-11 precision.
- **Explicit validity test** at intrinsic + 0.05, with deep-ITM delta defaulting to ±0.99 and theta/gamma set to 0 (`greeks.py:67`, `:93-96`). This fixes the earlier ITM-put bug named in D-020.
- **`fnum` turns NaN into None** (`engine_main.py:50-55`), and `choose_contract` filters `delta is not None`, so a NaN delta can never enter the band test.
- **ATM IV averages the CE and PE IV at the strike nearest the forward** (`engine_main.py:359-363`). This is robust to one-sided quotes.
- **GEX falls back to ATM IV per strike when IV is missing** and sets NaN gamma to 0 (`gex.py:58-61`). The observer cannot crash the loop.
- **Holiday-aware 0DTE detection** uses the ISO expiry from the registry (`feed_breeze.py:333`; `paper.py:110`). Monday 19 Oct is correctly treated as 0DTE.

## Ideas from GitHub
1. **vollib/py_vollib** — https://github.com/vollib/py_vollib — MIT, with Peter Jäckel's permissive LetsBeRational notice.
   - **Borrow:** the `vollib.black` pricing and implied volatility, and the `vollib.ref_python` reference implementation.
   - **How it maps:** use it as a **test oracle** in `tests/test_core.py`, not in the runtime. Add a grid of 0DTE, deep-ITM and deep-OTM cases asserting that Apex's IV and delta match within tolerance.
   - **Why:** this locks in the numerics I checked by hand. It also adds the missing tests for theta convention and 0DTE: today only a 6-DTE round trip is tested (`test_core.py:51-59`).
   - **Kind:** tool, size S.
2. **vollib/lets_be_rational** — https://github.com/vollib/lets_be_rational — Jäckel's notice ("freely granted ... provided this notice is preserved").
   - **Borrow:** `implied_volatility_from_a_transformed_rational_guess`, which reaches machine precision in two iterations.
   - **How it maps:** use it to compute IV at bid and at ask for every row cheaply, giving the **IV uncertainty band** that D-020 promised (T3).
   - **Then:** log `iv_bid`/`iv_ask` beside `iv`, and add an **observer** that flags `iv_late` firings where `iv5` is smaller than the band width.
   - **Kind:** observer, size M.
3. **nautechsystems/nautilus_trader** — https://github.com/nautechsystems/nautilus_trader — LGPL-3.0, so concept only, no code.
   - **Concept 1:** its GreeksCalculator (`docs/concepts/greeks`) takes `spot_shock`, `vol_shock` and `time_to_expiry_shock`, revalues by full repricing, and raises an error on expired options instead of pricing them.
   - **How it maps, concept 1:** add a **sticky-IV P&L attribution observer** in `paper.py` exit logging. At exit, reprice the entry contract three ways: with only F moved, with only T moved, and with only IV moved. Split the trade's points into direction, theta and IV. This turns T3's missing attribution into data the learning loop can read.
   - **How it maps, concept 2:** make `years_to_expiry` refuse past expiries (T6).
   - **Kind:** observer, size M.

## Top 3
1. **Fix the theta clock for expiry day, as a logged correction (S, before Monday).**
   - **What:** on 0DTE use `theta_year / 365 / 1440`, or equivalently any day where `now.date() == expiry`. For other days, keep `/375` but log `drift_min / theta_min` from `straddle_watch` during quiet time, so D-032's clock gets calibrated from data.
   - **Rule question:** this is a measurement bug, not a trigger change. If the owner reads I-11 strictly, at least run the corrected `expected` path as a parallel observer series from Monday, so the spike variant's 0DTE results can be judged against it.
2. **Make the forward more robust (S, before Monday).**
   - Use mid-or-LTP only when `age < 15 s`.
   - Fall back to the futures-implied forward rather than spot.
   - Tighten the parity sanity check from 150 points to about 40, or to 0.5 x the remaining 1-sigma move.
   - Log F, its source, and the strikes used every second, so any band miss on Monday can be explained.
3. **Build what D-020 promised but is not in the code (M, later):**
   - an IV band from bid and ask (idea 2),
   - sticky-IV P&L attribution per trade (idea 3),
   - a py_vollib oracle test grid covering 0DTE and deep ITM/OTM (idea 1).
