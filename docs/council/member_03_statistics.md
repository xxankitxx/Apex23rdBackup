# Member 03 — Statistics of the learning loop

## Lens
`apex/engine/learning.py` (405 lines) and its constants in `apex/config.py:120-128`. Question: does each test keep its stated error rates on small, clustered (several trades per day), fat-tailed option returns, and does it have enough power to decide anything in a reasonable number of sessions? Everything below marked "probe" was checked with `/tmp/council/03/probe.py` and `/tmp/council/03/adv.py`. Both import the real `learning.sprt_lines`, `_t`, `t_crit` and `_lodo_ok`. Tests pass (`python tests/test_core.py`).

## Teardown

**T1. The SPRT can call GO on a book that loses money under all-in compounding. HIGH (probe).**
`learning.py:252-258` runs the Wald SPRT on the *arithmetic* mean of per-trade ret% (H1 = +2.5 %). Under the owner's all-in sizing the account grows at E[ln(1+r)] ≈ μ − σ²/2, not μ. The probe used μ = +2.5 %/trade:

| true sd/trade | E[ln(1+r)] per trade |
|---|---|
| 10 % | +2.00 % |
| 20 % | +0.45 % |
| 30 % | **−2.78 %** |

A 0DTE book with sd near 30 % can therefore reach the GO line while the paper account it scores shrinks. The challenger test already uses log growth (`_day_ret`, l.61-66), so the scoreboard and the challenger test also judge two different quantities. Fix: run the SPRT on per-trade `ln(1+r)`, the same unit as `_day_ret`.

**T2. The SPRT's α depends entirely on the assumed σ = 10 %. HIGH (probe).**
`sprt_lines` (l.69-73) hard-codes σ² into the boundaries. The probe ran 2,000 runs per cell, up to 200 trades, with H0 μ = 0:

| true sd | P(GO \| H0), stated 0.05 | P(GO \| H1), stated 0.80 |
|---|---|---|
| 10 | 0.044 | 0.81 |
| 15 | 0.154 | 0.62 |
| 20 | 0.227 | 0.52 |
| 30 | 0.329 | 0.46 |

Results were similar with t3 tails and with a skewed lognormal shape. Clustering also hurts. With σ correct (10) but an intraday correlation of 0.3 (5 trades/day sharing the day's regime), P(GO | H0) = **0.162**. The SPRT treats trades as independent, and they are not. The remedy offered in the code (l.263-264: "re-register SPRT_SIGMA_PCT if this persists") changes the test after looking at the data, which is itself a sequential-validity problem. Fix: use an always-valid test that needs no σ (see G1), or at least use the day as the unit and compute σ from the data inside the test (t-SPRT). This is the most important finding: the main GO/KILL gate is calibrated on an assumption the code itself says is probably wrong (config.py:121, "0DTE trades swing far more").

**T3. Challenger promotion leaks α through repeated evening looks. MEDIUM-HIGH (probe).**
`learning.py:270-283`: Bonferroni α/12 (t ≥ 3.36 at 10 days) is applied *at each look*. The loop looks every evening from day 10 onward with no upper limit, and needs only `PROMOTE_STREAK = 2` passes in a row. Simulated family-wise error under the global null (12 challengers, ρ = 0.5 shared noise):

| horizon | FWER, normal | FWER, t3 |
|---|---|---|
| 30 days | 0.107 | 0.083 |
| 60 days | 0.135 | 0.125 |
| 120 days | 0.228 | 0.155 |

The real FWER is 2-4× the stated 0.05, and it keeps rising. The streak helps, but it is not a sequential correction.

**T4. Challenger power is low; only huge effects get detected. MEDIUM (probe).**
Power at Bonferroni α/12, effect measured as daily mean difference / daily sd of the difference:

| effect | n = 10 days | n = 20 | n = 40 |
|---|---|---|---|
| 0.25 sd | 0.03 | 0.05 | 0.13 |
| 0.5 sd | 0.09 | 0.27 | 0.66 |
| 1.0 sd | 0.47 | 0.90 | — |

Realistic grid neighbours (m1.5 vs m2.0) differ by well under 0.5 sd/day. So the champion stays in place mostly by default, which is safe, but the documents should say so. Combined with T3, the loop is low-power and leaky at the same time, because it tests the same null many times.

**T5. The LODO check is redundant in the paired test. LOW (probe + algebra).**
`_lodo_ok` (l.212-217) fails only if one day's difference exceeds the whole total. A sample with t ≥ 3.36 cannot contain such a day. Probe: 6,430 heavy-tailed samples passed the t threshold and **zero** failed LODO. It gives no protection there. It does add something in the advisor screen, which has no t-test. If a robustness check is wanted, use trimmed means, a sign/Wilcoxon test, or "drop the best 2 days".

**T6. The KILL-replacement step skips every test and picks the max. MEDIUM (read).**
`learning.py:289-298`: after a KILL, the new champion is `max(sum(x))` over all non-retired variants. `x` is taken across **all** recorded days, not `> registered` or `> champion_since`. The only filter is "not below its own kill line". That is a winner's-curse pick from 12 correlated records. Summing ret% (not log growth, not a mean) also favours the variants that trade most (m1.5). Fix: pick the variant with the best log-growth record by paired test against the retired champion, or restart with CHAMPION_DEFAULT's nearest neighbour as a pre-registered order.

**T7. The control comparison reuses the data that selected the champion. MEDIUM (read, l.323).**
The controls are compared "since registration" over the current champion's whole history. After a promotion, that history includes the days on which it won the promotion, so the comparison is biased towards "champion beats it". Also, "beats all three nulls" is an intersection-union claim, which is valid with each test at α. The Bonferroni α/3 at l.317 only costs power. Fix: compare against the controls since `champion_since`, at α each.

**T8. The advisor pipeline lets noise in cheaply and judges it unevenly. MEDIUM (probe + read).**
- The screen (l.337-350) has no variance term. With 13 null advisors (random 30 % vetoes, no effect), P(at least one becomes a CANDIDATE) was 0.55-0.83 and the mean was 0.8-1.8 false candidates (probe, 40-80 RAW trades, sd 10-20).
- The gated-book test then uses α / len(candidates) (l.352). With one candidate that is **α = 0.05**, against 0.0042 for variant challengers. It runs indefinitely with repeated looks (T3 again), and the count of advisors screened over time is never charged.
- Demotion (l.358) happens on any negative point estimate of the RAW gain, with no test. A real but small gate will bounce in and out.

Good design (gated book on fresh days after candidacy), weak thresholds. Fix: test gated books at α/13, one fixed family across all advisors ever screened, and require a significant reversal before demoting.

**T9. Minor issues (read).**
- `_day_ret` floors a −100 % trade at ln(1e-4) = −921 %/day. That is honest, but one such day dominates any t-test. Report it separately.
- `t_crit` bisects only up to 50. Fine for df ≥ 2, but at df = 1 (n = 2) the critical value at α/12 (~76) exceeds the cap, and 50 is returned. Harmless only because `CHALLENGER_MIN_DAYS = 10`.
- Under H1 the "undecided at 200 = KILL" branch almost never triggers, so it is not a real limit on run length.

## Good things
- **Pre-registered grid, nothing invented** (`config.py:89-113`, `learning.py:34`). That removes the biggest overfitting route.
- **Pairing on identical market days** (`paired_test`, l.220-232). Every book trades the same ticks, so the shared market noise cancels. This is the right design and is why T4 is not worse.
- **The gated book is judged out of sample** (l.364, `since = max(cands[a], champion_since)` with `d > since`). Screening data and decision data do not overlap. Good.
- **Log-growth day metric** (l.61-66), with a reason given for it. This is the correct quantity for all-in compounding; it just needs to reach the SPRT too (T1).
- **Exact Student t without scipy** (l.77-128). Matches scipy (audit doc) and avoids a normal approximation at df = 9.
- **Idempotent, once-per-evening state moves** (`first_look`, l.245; D-078); empty days recorded as 0 % (l.159-160), so there is no survivorship from missing days.
- **Controls as a first-class null** (D-065): rarely done, and it guards against "the exits do the work".
- **The report prints the observed sd** (l.263). The right instinct, but the fix it implies should come from the test itself (T2).

## Ideas from GitHub

1. **gostevehoward/confseq**, https://github.com/gostevehoward/confseq, MIT (opened: README, `src/confseq/betting.py`, `predmix.py`).
   - Idea: betting-martingale / predictable-mixture **confidence sequences** (Waudby-Smith & Ramdas). A one-sided test of "mean ≤ 0" for data bounded below needs no σ and stays valid under *any* number of looks.
   - Fit to Apex: per-trade r ≥ −100 %. The test wealth Πₜ(1 + λₜ·r) with predictable λₜ ∈ [0, 1) is the all-in paper account at fractional size. GO when wealth ≥ 1/α. That one change fixes T1, T2 and the repeated-look part of T3.
   - Where: replace `sprt_lines` in `learning.py`, numpy only (~40 lines, written from the paper's `lambda_predmix_eb` concept). Can be added first as an **observer** column in the report beside the Wald lines.

2. **bashtage/arch**, https://github.com/bashtage/arch, University of Illinois/NCSA (permissive) (opened: `arch/bootstrap/multiple_comparison.py`: `SPA`, `StepM`, `MCS`; stationary/circular block bootstrap).
   - Idea: Hansen's SPA / White's Reality Check and Romano-Wolf StepM. These test "is the best of k challengers really better than the benchmark", using a block bootstrap that respects the correlation between the 12 variants and serial correlation across days.
   - Fit to Apex: a less conservative and more powerful replacement for Bonferroni-over-12 (T3/T4) and for the T6 max-pick. Run StepM on the daily log-growth difference matrix (days × challengers) against the champion.
   - Where: `learning.py` §2, as an **observer** table first. The owner's PC lacks scipy and arch, so port the stationary bootstrap (~60 lines numpy) or run arch offline in `learn`.

## Top 3
1. **Make the scoreboard unit log growth and its boundary σ-free.** For now, switch the SPRT to per-trade ln(1+r) and print a predictable-mixture betting e-value beside it as an observer (G1). Pre-register that the e-value takes over if the observed sd is above 15 % after 30 trades. **S, before Monday.** It changes how the first sample is scored, and the current GO line has α ≈ 0.15-0.33 if sd is 15-30 %.
2. **Cap the looks.** Fix a look schedule for challengers and gated books (for example days 10, 20, 40, 80, with an O'Brien-Fleming-style spend), or use an e-value per challenger with e ≥ 12/α. Test gated books at α/13 across all advisors ever screened. Require a significant reversal before demoting. **S-M, before Monday** (constants and a few lines).
3. **Bootstrap multiple-comparison observer (StepM/SPA, G2) for challengers and the post-KILL pick.** Restrict the KILL pick and the control comparison to post-`champion_since` days (T6, T7). **M, later.**
