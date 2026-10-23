# Council member 11 — Regime & volatility modelling

## Lens
`apex/engine/regime.py`, the VIX poll, ATM IV tracking (`engine_main.compute_greeks`, `iv_hist`, `iv_change`), the `iv_late` advisor, the frozen IV cap in `paper.py`, and the σ15 scales in `apex/engine/domino.py`. The question: are these features and thresholds sensible for intraday Nifty, and are any standard volatility estimators missing? I checked the work by reading the code, running three probe scripts against the real modules (in my scratchpad folder `p11/`), and running `tests/test_core.py`, which passes.

## Teardown

**F1 — HIGH: ATM IV is a floating-strike snapshot, so it saw-tooths at every strike roll and rises mechanically in sell-offs. That feeds the frozen trigger's IV cap and `iv_late`.**
- **Where:** `engine_main.py:359-363` takes the strike nearest F (`atm = min(strikes, key=|k-F|)`) and averages the CE/PE IV at that one strike. The result feeds `iv_rise_since_onset` (`:269`), which feeds the frozen `IV_RISE_CAP = 1.5` check (`paper.py:182`), the lateness score (`:533`) and `iv_late` (`:408`).
- **Probe `probe_iv.py`:** I used a smile fixed in moneyness, so true ATM-forward IV stays at 13.00 throughout. With a mild skew of −0.6 vol pts per 50-pt strike step, the measured `atm_iv` reads 13.32 at F = 25024 and 12.75 at F = 25026. That is a **0.57-pt jump with no change in volatility**, about 38 % of the 1.5-pt cap.
- **Probe `probe_iv2.py`:** I used a smile fixed in strike (sticky-strike). A 60-pt fall moves `atm_iv` by +1.40 pts at 1 day to expiry and +2.20 pts at 5 hours to expiry. That exceeds both the `iv_late` threshold (8 % of 13 = 1.04) and the 1.5-pt cap. The same 60-pt rally moves it by −1.0 / −1.8 pts.
- **Failure scenario:** On an expiry-week afternoon, a clean 60–100-pt down-impulse is rejected as "LATE: ATM IV +x since onset". Volatility did not move; the trigger simply started reading a higher-skew strike. CE entries are never blocked this way.
- **Why it matters:** The cap acts as a direction- and DTE-dependent filter. D-016 expects an IV tailwind for PE, but this effect is mostly a measurement artefact.
- **Fix:** Keep the number 1.5; change only the input.
  - Interpolate IV at F linearly in strike between the two strikes that bracket it, or read IV at fixed delta 0.5.
  - Or measure the rise at a fixed strike, namely the onset ATM strike (`ep["iv0_strike"]`).
  - Because this changes trigger behaviour, it needs the owner's sign-off, or it should run as a pre-registered variant first.

**F2 — MEDIUM: regime percentiles ignore time of day, so COMPRESSION is over-labelled in mid-morning and `rv_pct` thresholds mean different things by the clock.**
- **Where:** `regime.py:49,116` ranks `rv_pct` against *today's history so far*, which in the first hour is dominated by the opening burst. Nifty's intraday volatility is U-shaped: roughly 2× at 9:15–10:00 and again into 15:00.
- **Probe `probe_regime2.py`:** These are synthetic random walks run through the real `Regime` class. During 10:15–11:15, COMPRESSION was labelled **30–43 % of the time (mean 38 %) with U-shaped volatility vs 7–18 % (mean 14 %) with flat volatility**, over 3 seeds each.
- **Failure scenario:** The `regime` advisor vetoes most of late morning as "quiet and contracting" when the market is just ordinary. The per-regime report tables (D-069/D-071) then mix volatility state with clock time.
- **Fix:** Rank `rv5` against the same 15-minute bucket on previous sessions, i.e. a seasonal baseline built offline in the evening from recorder data. That should be a new pre-registered regime *variant*, not an edit.

**F3 — MEDIUM: EXHAUSTION fires heavily on trend days.**
- **Where:** `regime.py:150` fires EXHAUSTION when `ext_pct ≥ 90 and er1 < 0.25`. On a trending day, the distance to VWAP keeps setting new highs, so `ext_pct` sits near 100. `er1` is a 12-step efficiency ratio, which is below 0.25 about half the time for pure noise (≈ |Z|·0.36).
- **Probe `probe_regime.py` (single seed, so treat as indicative):** On a +150-pt drift day, EXHAUSTION took 30 % and 36 % of hours 2 and 4, against 12–14 % on a driftless walk. In practice the label vetoes every with-trend entry during the pauses inside a trend. The bar should be relative (e.g. `ext` in σ-units of the day's path) or require `er1 < 0.15` sustained for 60 s. Treat any of these as a variant.

**F4 — MEDIUM (verified by reading): a mid-session engine restart silently changes what the regime features mean.**
- **Where:** `start_day` builds `Regime()` from scratch (`engine_main.py:151`). `t0`, the VWAP accumulators (`regime.py:84,89`) and the percentile histories therefore start at restart time.
- **Failure scenario:** After a 13:00 restart, "VWAP" is VWAP since 13:00, and the percentiles rank only against the afternoon. Trades get labelled with a regime that is not comparable to other days' labels.
- **Fix:** On start, rebuild from the day's recorder file, which `feed_replay` already reads, or mark the labels `restarted=True` and exclude them from the per-regime tables.

**F5 — LOW: VIX is polled every 60 s but used nowhere in the engine.**
- **Where:** Polled at `feed_breeze.py:463`; the only consumer is the dashboard (`engine_main.py:648`).
- **Assessment:** Using one REST credit a minute just for display is fine. But the cheap, well-known signal next to it is missing: the weekly ATM IV minus India VIX (30-day), a term-structure / event-premium reading. See Idea 2.

**F6 — LOW: `iv_late` uses a single raw sample at each end.**
- **Where:** `iv_change` (`engine_main.py:538`) is the point difference between the current `atm_iv` (recomputed from mids every 0.25 s) and one sample from 5 minutes ago.
- **Failure scenario:** On 0DTE, ATM vega is small, so a one-tick widening of the spread moves IV by several tenths of a point.
- **Fix:** Take a 15–30 s median at both ends.
- `iv_hist` is also not cleared on a data gap, unlike the regime windows (D-075).
- The two IV rules use different units: `iv_late` is relative (8 %) while the cap is absolute (1.5 pts). That deserves a note in docs/03.

**Checked and not raised:**
- σ15 is a mean-absolute EWMA, not a standard deviation. This is already acknowledged in docs/04 line 116.
- The ER random-walk baseline in the docstring is correct. I re-derived it: mean ≈ 0.22, P(≥0.35) ≈ 21 %, P(<0.20) ≈ 52 %.
- Calendar-time `T` (`greeks.py:43`) produces only about 0.03 vol pts of drift per 5 minutes on the day before expiry, which is negligible for 5-minute and since-onset deltas.

## Good things
- **`regime.py` docstring:** The thresholds were set against an explicit random-walk baseline, and the docstring records the 1-s bid/ask-bounce failure and its fix (15-s sampling). This kind of pre-registration is rare and correct.
- **No look-ahead:** The current value is ranked *before* it is appended to the history (`regime.py:113-118`). The 30-minute range ends 5 minutes ago, so a breakout is never judged against its own move.
- **Gap handling:** `after_gap()` drops the price windows but keeps the session VWAP and histories. `learn_scales=False` during blackouts keeps a jump on resume from inflating σ15 or the volume baselines (`domino.py`). Stocks with no quote are treated as missing (NaN), not as a −100 % move (`regime.py:96`).
- **Scale estimators:** `EW` is a fast-start EWMA (`domino.py:23`) whose seed counts exactly once. σ15 updates only on in-session data, so pre-open zeros cannot shrink it.
- **Forward and IV:** F comes from a put-call-parity synthetic forward with a stale-quote guard (`greeks.py:100-113`), not from spot. IV is solved with Black-76 on that forward, which is the correct model for index options.
- **Advisory status:** The regime is an advisor with its own gated book (D-067). Every trade and candidate carries its regime label, so the learning loop can judge it without anyone touching the trigger.

## Ideas from GitHub (all cloned to /tmp/council/11/)

1. **jasonstrimpel/volatility-trading** — https://github.com/jasonstrimpel/volatility-trading — **GPL-3.0, so concept only, no code copied.**
   - **What it has:** `volatility/models/{Parkinson,GarmanKlass,RogersSatchell,YangZhang}.py`, range-based estimators from OHLC data. They are 5–8× more statistically efficient than close-to-close returns.
   - **Mapping:** Write a ~40-line observer `engine/rv.py` from scratch. It builds 1-minute OHLC bars of Nifty futures from the 1 Hz series already held in `regime.fut`.
     - Publish Rogers-Satchell RV over 15 minutes, and Yang-Zhang over the session including the overnight gap.
     - Annualise it so it sits on the same scale as ATM IV.
     - This gives the missing **IV/RV ratio (volatility risk premium)**, the most standard check for an options *buyer*. Log it as a new advisor `vrp` that vetoes when IV/RV is above 1.3, and judge it through a gated book.

2. **bashtage/arch** — https://github.com/bashtage/arch — **University of Illinois/NCSA licence (permissive, MIT-like).**
   - **What it has:** `arch/univariate/mean.py: class HARX` (the heterogeneous autoregressive model, the HAR-RV forecasting baseline) plus `arch.bootstrap` (stationary/block bootstrap).
   - **Mapping:** An *evening tool* in the learning loop, not anything intraday.
     - Fit HAR-RV on daily realised variance from the recorder files to forecast tomorrow's RV.
     - Store it in `lstate`. Tomorrow's `vrp` advisor then compares live ATM IV against a *forecast* rather than a trailing RV.
     - Also store India VIX minus the weekly ATM IV.
     - Separately, `StationaryBootstrap` gives honest confidence intervals for the per-regime P&L tables (D-071), where trades are autocorrelated within a day.

3. **vollib/py_vollib** — https://github.com/vollib/py_vollib — **MIT.**
   - **What it has:** `vollib/black/implied_volatility.py`, Jäckel's "Let's Be Rational" Black-76 implied-volatility solver, plus analytic greeks under `vollib/black/greeks`.
   - **Mapping:** Add it as a *test oracle* in `tests/test_core.py` (dev dependency only) to check `greeks.implied_vol` and `greeks.greeks` across 0DTE–7DTE and deep ITM/OTM, including near the `valid` cut-off at intrinsic + 0.05.
   - It also provides the reference values for the F1 fix: a test asserting that the ATM-IV estimate does not jump when F crosses a strike midpoint on a fixed smile.

## Top 3
1. **Fix the ATM IV measurement (F1)**, size **S**, **before Monday**, owner sign-off needed.
   - Interpolate IV at F between the two bracketing strikes (or measure at the onset strike) and median-filter it over 15 s.
   - Keep `IV_RISE_CAP = 1.5` and the 8 % rule unchanged; only their input changes.
   - If the owner says the trigger input is frozen too, run the fixed measure as a pre-registered variant and log both values on every candidate from Monday.
2. **Add an IV/RV observer and a `vrp` advisor** (Idea 1, plus Idea 2 later), size **M**, **later**. Log Rogers-Satchell RV, IV/RV and VIX minus the weekly ATM IV on every candidate from day one, even before the advisor is judged.
3. **Make the regime percentiles time-of-day aware and handle restarts (F2–F4)**, size **M**, **later**. Run it as a pre-registered `regime_v2` variant beside the current labels, with seasonal `rv` buckets, a relative EXHAUSTION bar, and labels rebuilt from the recorder after a restart. Compare the two sets of labels in the D-071 tables after about 10 sessions.
