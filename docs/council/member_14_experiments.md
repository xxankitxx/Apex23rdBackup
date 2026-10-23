# Member 14 — Experimental design & overfitting risk

## Lens
Whether the learning loop (apex/engine/learning.py), the variant/control set (apex/config.py:89-115), the candidate ledger (apex/engine/ledger.py) and diagnostics (apex/engine/diagnostics.py) can produce a conclusion you can trust, and how long that takes. Tests pass (`tests/test_core.py`, all ok). I checked the error rates with a Monte Carlo probe that calls the real `learning.paired_test` and `learning.sprt_lines` on synthetic null books. The script is at `/tmp/claude-0/-home-claude/a63e9fa2-7e12-5819-bed7-d06bfece2a8a/scratchpad/m14/probe.py`. The synthetic books are nested: the 9 grid variants take subsets of the same episodes with the same returns, plus 4 independent challengers. Each run has 60-300 trials, so every rate below is about ±5 percentage points.

## Teardown

**F1. CRITICAL: the SPRT's assumed sigma of 10 % makes GO and KILL close to coin flips. Settings at config.py:120-124, used in learning.py:69-73 and 252-258.**
All-in weekly option buys at LTP will almost certainly have a per-trade sd well above 10 %, because 0DTE trades swing ±30-60 %. With narrow lines (GO = 110.9 + 1.25n), a handful of large winners or losers crosses one of them. Probe results:
- True mean 0, sd 25 %: false GO in **25 %** of runs (nominal 5 %).
- True mean −3 % (a losing system), sd 25 %: false GO in **17 %** of runs.
- True edge +2.5 %, sd 25 %: KILL in **57 %** of runs.

Mitigation exists only on paper. The "re-register sigma" warning appears only after 30 trades (learning.py:264), and by then the SPRT has usually already decided. A KILL also retires the champion for good (learning.py:286-288).
Verified: probe.

**F2. HIGH: checking every evening with a 2-evening streak inflates false promotions about 3-5 times. Code at learning.py:277-283 and 365-370.**
Bonferroni at 0.05/12 controls a single look: probe = **6.7 %** family-wise at day 80, close to nominal. But `learn()` looks every evening from day 10. Consecutive evenings share n−1 days, so needing two passes in a row adds almost no protection. Probe over 80 sessions under a true null: a challenger is promoted in **15-18 %** of runs at sd 10-25 %, and **30 %** when the true per-trade mean is −3 %. D-066 fixed the per-look alpha (from about 19 %) but not the repeated looks. Gated books (learning.py:352-374) use the same machinery, so they share the problem.
Verified: probe (single look vs every evening).

**F3. HIGH: the `random_entry` null is not fair, because daily log growth mixes up edge with how many trades a book takes. Code at learning.py:61-66 and 220-232, config.py:114.**
Every comparison uses 100·Σln(1+r) per day. ln is concave, so each extra trade adds a variance drag (and with a negative mean, a negative drift). `random_entry` fires a fixed ~6 trades/day (Poisson, `RANDOM_ENTRIES_PER_DAY`, never matched to the champion's actual rate). A champion that trades less "beats" it just by being idle. Probe, where the champion takes ~1.7 trades/day and the control 3-9:
- No edge (mean 0, sd 25 %): the champion is declared to beat random in **28 %** of runs (nominal 1.7 %).
- True mean −3 %/trade: the champion is declared to beat random in **83 %** of runs. A losing trigger passes the null test.

The control also uses one random seed per day (paper.py:229), so its own noise is about the size of the effect being tested.
Verified: probe plus reading.

**F4. MEDIUM: two of the three controls stop matching the champion once the champion changes. Code at config.py:110-112 and learning.py:320-323.**
`futures_only` is hard-wired to m*=2.0 and `premium_momentum` is the null for `straddle_spike`. Yet the report always compares the current champion with all three, "since registration". If m1.5_s0.4 or gap3_s0.4 becomes champion, "futures_only" is no longer "the champion without the basket", and its verdict changes meaning without warning. For the m/s champions, `premium_momentum` tests a different hypothesis altogether.
Verified: read.

**F5. MEDIUM: the advisor screen pools RAW trades from different champions. Code at learning.py:330 and engine_main.py:141.**
RAW is rebuilt each morning with the then-current champion's parameters (engine_main.py:141). The screen, however, reads RAW "since registered" (learning.py:330), not since `champion_since`. After a champion change, each advisor's gain, top-quartile share and LODO mix trades from two different triggers. Gate demotion (learning.py:358) also reads this pooled screen.
Verified: read.

**F6. MEDIUM: the candidate ledger records nothing when the champion is `straddle_spike`. Code at ledger.py:53.**
`not p.get("spike")` skips every episode. If the loop promotes straddle_spike, D-070's "every opportunity, taken or not" evidence stops, along with every diagnostics table built from it (diagnostics.py:77-111). There is no warning.
Verified: read.

**F7. LOW-MEDIUM: diagnostics are many uncorrected splits of clustered data. Code at diagnostics.py:23-31 and 65-111.**
The diagnostics show Wilson intervals for 13 advisors × vetoed/passed, plus regimes, reasons and z buckets. Candidates within a day share the trend, and their 15-minute follow windows overlap, so the iid Wilson interval is too narrow. With about 40 splits, roughly 2 will look "significant" by chance. The tables are labelled "descriptive only", which is right, but the owner will still read them, so the header should say they are exploratory and the intervals are not adjusted. A candidate starts on +1R vs −1R in futures, so a 50 % hit rate is the right null. Good choice; it should be printed.
Verified: read.

**F8. LOW: KILL replacement picks the best raw sum over all history among 12 variants (learning.py:290-298).** This is a winner's-curse pick, partly offset because its SPRT restarts forward. The Bonferroni divisor for gates (learning.py:352) is computed before that evening's new candidates are added. Both minor.
Verified: read.

### How long until a conclusion is trustworthy
The closed form below is 80 % power for a one-sided test, with per-trade sd σ, edge δ per trade and k trades/day. Days needed ≈ (z_α+z_β)²·2σ²/(kδ²).

For champion vs random_entry (α = 0.05/3), with δ = 2.5 %:

| per-trade sd σ | trades/day k | days needed |
|---|---|---|
| 10 % | 2 | ~140 (≈ 7 months) |
| 25 % | 2 | ~880 (≈ 3.5 years) |
| 25 % | 4 | ~440 |

Champion vs 0 on per-trade returns needs about ((z_α+z_β)·σ/δ)² trades: ~140 at σ = 10 %, ~880 at σ = 25 %.

Probe check: with a true +2.5 % edge at σ 25 %, the champion beat random in only 3 % of 120-session runs.

Challengers differ from the champion by far less than 2.5 %/trade (they are nested grid neighbours). So a real promotion is essentially impossible inside the first year, and **any promotion in year 1 is more likely noise than signal** (F2). Realistically, no rule- or advisor-level conclusion is trustworthy for at least 6-12 months of sessions, and only if the observed sd turns out near 10 %. The first trustworthy number will be the observed per-trade sd itself, after about 30 trades.

## Good things
- **Pre-registration is real.** The variants are a finite fixed grid (config.py:89-115). The loop "never invents new numbers" (learning.py:34), and changes take effect only the next session (I-11). `validate()` (config.py:270-304) blocks a mis-typed registry.
- **Gated books (D-067) are a forward, out-of-sample test.** The screen is in-sample, but the decision uses only days after the advisor became a candidate (learning.py:364, `d > since`). This is the right way to stop 13 screened advisors from snooping their way into the trigger.
- **Controls can never be champion** (learning.py:236-237, 290-291), and their verdicts include "control is ahead" and "too few days" (learning.py:324-326).
- **The random control is reproducible**, seeded per day and book (paper.py:226-239), so replays match.
- **LODO plus `CHALLENGER_MIN_DAYS`** stop single-day promotions. The exact t-distribution is implemented with numpy only (learning.py:77-128).
- **The ledger labels outcomes without looking at the decision** (ledger.py:99-103), and records the would-be contract's returns at fixed times (+1, +5, +15 min). This is the right basis for "does a filter remove good or bad opportunities". Gap-crossed follows are flagged (ledger.py:90-92).
- **Empty days are recorded as 0 %** (learning.py:159-160). There is no survivorship gap.

## Ideas from GitHub
1. **bashtage/arch: White/Hansen SPA, StepM and MCS.** https://github.com/bashtage/arch, NCSA licence (permissive; cloned). `arch/bootstrap/multiple_comparison.py` has classes `SPA` (l.796), `StepM` (l.621) and `MCS` (l.286), all using a stationary block bootstrap. Mapping: add a `run_apex.py report --snoop` **offline tool** (arch needs scipy, so not in the engine). It takes the T × 13 matrix of daily log growth for every variant and asks: "Given we tried all of these, does the best beat the champion, or random_entry?" One test covers the whole correlated family, so per-look Bonferroni over nested books is no longer needed. Report-only (an observer), so it fits D-033.
2. **gostevehoward/confseq: anytime-valid confidence sequences.** https://github.com/gostevehoward/confseq, MIT (cloned). `src/confseq/betting.py` provides `betting_cs`, `hedged_cs` and `betting_lower_cs` for bounded means. Mapping: replace the SPRT (F1) and the evening t-tests (F2) with an always-valid lower confidence bound on per-trade return, with returns clipped to [−100 %, +X %]. You can look every evening without inflating error, no sigma has to be assumed, and `hedged_cs` is a small numpy port. Pre-register it as the scoreboard rule in learning.py.
3. **esvhd/pypbo: Probability of Backtest Overfitting (CSCV), MinTRL and Deflated Sharpe.** https://github.com/esvhd/pypbo, **AGPL-3.0, so borrow the concept, not the code**. Mapping: once there are ≥ 16 sessions, an observer section in report.md splits the days into combinatorial halves. It measures how often the in-sample best variant ranks below the median out of sample (PBO), and prints MinTRL ("days still needed"). That gives the owner an honest "how long until trustworthy" number every evening.

## Top 3
1. **Re-register `SPRT_SIGMA_PCT` at a conservative 30 % now, while there is still no live data.** That is still a valid pre-registration. Also block GO/KILL before 30 trades. (S, **before Monday**.)
2. **Stop deciding every evening.** Promotions for challengers and gates should be evaluated only at pre-registered checkpoints (e.g. sessions 20, 40, 60, with an O'Brien-Fleming / alpha-spending boundary). Later, replace this with confseq's anytime-valid bound or a `--snoop` SPA report. (S for checkpoints, **before Monday**; M for confseq/SPA, later.)
3. **Make the nulls fair.** Compare the champion with the controls on **per-trade** mean return (the D-064 unit), not daily log growth. Rate-match `random_entry`, or run 10-20 seeds and use their pooled distribution. Re-point `futures_only` to the current champion's m*, and compare `premium_momentum` only with `straddle_spike`. Fix the ledger skip (F6) and RAW `since` (F5) at the same time. (M, per-trade comparison and F5/F6 **before Monday**, the rest later.)
