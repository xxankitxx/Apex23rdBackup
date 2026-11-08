# Advanced models and new shadow books for Apex Conductor

8 November 2026. Detailed research and implementation proposal for Claude, supplementing `32_CLAUDE_IMPROVEMENT_HANDOFF.md`. This document proposes new work. It does not register or activate strategies. Historical results below are reported by the repository documents and have not been independently reproduced for this handoff.

## 1. Owner requirements

Aim for no losing trades, no losing days, and maximum capture of qualified opportunities. Stay flat when evidence is weak or the candidate option offers insufficient movement. Use all-in capital on every trade, buy-only Nifty weekly calls or puts, and the existing gross paper accounting. Brokerage and taxes are excluded. Impose no invented minimum daily trade count, loss allowance, or position-sizing scheme.

Investigate every loss and prevent verified repeatable defects. Trading corrections must be recognizable before the outcome and tested against winners they would also reject. Keep the recurrence register specified in document 32.

The owner wants more advanced mathematics integrated into decisions and more complementary shadow books eligible to join the Conductor. The aim is a larger set of demonstrated capabilities. Model sophistication by itself supplies no evidence of fewer losses. A finite successful sample cannot establish zero future losses. Report that limit precisely while pursuing the strongest measurable improvement.

## 2. What the system already uses

Verify these paths against the current checkout before editing. The weather v3 work and other source changes were uncommitted during this review.

| Component | Existing mathematics | Current decision role |
|---|---|---|
| `apex/greeks.py` | Black-76 pricing, IV inversion, Delta, Gamma, Theta and Vega | Contract selection, option diagnostics and strategy inputs |
| `apex/engine/council/c20_9x.py` | Delta-adjusted trails, gamma/theta rent, forward ranges, premium capture measures and calendar-time conversions | Several calculations already affect strike choice and exit behavior; audit the enabled flags and inherited strategy code |
| `apex/engine/paper.py`, `edge.py` | Realized variance, gamma benefit versus theta, premium response and reentry gates | Particular variants apply buyer-edge or cheapness gates; applicability differs by book |
| `apex/engine/domino.py`, `flow.py`, `impulse.py` | Normalized moves, weighted basket synchrony, book and trade-flow statistics | Entry evidence for impulse and related families |
| `apex/quant/greeks_hi.py` | Exact repricing, Vanna, Vomma, Charm, Speed, Color, Zomma and Ultima | Scenario library, dashboard and trigger-weather observations; higher-order Greeks do not collectively direct every book |
| `apex/quant/passage.py` | Two-barrier first-passage probabilities and horizon-dependent outcome probabilities | Quant evidence; historical scanner and gate experiments were unsuccessful |
| `apex/quant/micro.py` | Kalman local trend, bipower variation, jump statistic, CUSUM and Kyle lambda | Mainly observations and model inputs through QuantView |
| `apex/quant/hawkes.py` | Exponential event intensity, fitting and simulation | Activity/excitation observations; current display proxies require validation before directional trading use |
| `apex/quant/regime.py` | Gaussian HMM, causal state filter, empirical state-duration estimate | Quant observations; the duration summary should not be described as a full semi-Markov filter without implementing one |
| `apex/quant/svi.py` | Raw SVI smile fit and strike residuals | Smile observations; a raw fit needs explicit arbitrage and stability checks before selection decisions |
| `apex/engine/gex.py` | OI-weighted modeled gamma, flip and wall estimates | Advisory and weather evidence under assumed dealer signs |
| `apex/conductor/` | Diaries, search, permutation tests, window scoring and monitoring | Evidence selection and future eligibility; the shared-account selector remains work to complete |

The statement that all books fail to use models is too broad. Greek and statistical calculations already influence several strategies. The larger gap is the integration and validation of the newer quant library in decision-specific experiments.

## 3. Start with the failed experiments

`docs/24_REVIEWS_QUANT_LAYER_5NOV.md` reports the following historical experiments.

- The standalone premium-race scanner generated 604 trades, 318 losers, and a gross loss of ₹124,725 across its 12-day study.
- A related trail variant generated 551 trades, 292 losers, and a loss of ₹193,056.
- Among 17,484 probability samples, predictions of 0–10% success had about 17% realized success, while predictions of 90–100% had about 23%. The forecast ranking and calibration were weak despite verified probability mathematics.
- A regime-agreement filter removed substantial incumbent profit. A race-decay exit added 18 trades and 14 losers while reducing profit materially.

`docs/26_EVENT_STUDY_6NOV.md` reports modest discrimination from option premium momentum and volume, but a simple trading rule built from those features had approximately flat average returns. Most other individual features did little to separate runners from duds. Its leave-one-day-out results are research evidence; training on later dates to predict earlier dates is not a chronological deployment test.

Reproduce these controls before claiming a new variant fixes them. Any revival must specify the changed assumption, target, horizon, conditioning, data quality, or calibration method. A new threshold and name alone do not resolve the previous failure. Recalibration can correct probability levels but cannot create useful ranking from an uninformative score.

## 4. Correct model provenance before expanding decisions

`apex/quant/params.json` records fitting on 5 November using tapes through 4 November. `apex/engine/quantview.py` loads this global parameter file. Replaying earlier dates with those parameters introduces later-session information into learned model outputs. A trigger-time truncation test cannot detect this if the parameters themselves were already trained using future data.

Implement dated model artifacts with training cutoff, source-session hashes, preprocessing version, calibration cutoff, model version, and permitted use date. Historical runs must select artifacts available at that time. Where no valid artifact exists, report unavailable status or use an explicitly fixed prior. Keep the descriptive full-sample study separately labeled.

Audit Hawkes input reconstruction. The display currently treats a per-second volume increase as a classified event and exposes excitation values. Establish whether that input supports event-time, count, marked-volume, or simply activity-proxy modeling. Preserve baseline intensity and use correct normalization before interpreting buy/sell intensity ratios. Fit with the same observation process used live.

For regimes, use causal filtering at decision time. Historical Viterbi or smoothed states can see subsequent observations. Freeze semantic state mappings from training data, including how states are aligned across refits. A label called trend needs measured forecast relevance beyond describing the preceding minute.

Extend existing weather lineage and leakage checks to model fitting, probability calibration, feature normalization, chosen thresholds, and state warm-up. Every required input carries availability and age.

## 5. Separate the decisions that models can improve

Build experiments around four decisions.

1. **Opportunity detection.** Is there a new directional premium opportunity while the account is flat?
2. **Contract selection.** Given a direction and entry time, which permitted strike has the most favorable premium response?
3. **Continuation or exit.** Given the actual held contract and current state, is continued holding justified?
4. **Account admission.** Does this eligible setup get the shared capital given occupancy, standing, and protected phases?

A pricing model describes option value under assumptions. A physical forecasting model estimates actual future market outcomes. Calibrating an option surface under risk-neutral probabilities does not establish physical direction or trading success probability. Keep those quantities explicitly labeled in code, logs and documentation.

Use shared mathematical models to supply quantities such as expected premium response, uncertainty, or state duration. Express strategy decisions as dated yes/no rules under the existing Conductor design. Avoid an undocumented weighted score that quietly changes which rules get capital. A change to the official simple-rule or priority standard needs an explicit design decision.

For diagnosis, the local premium expansion is

```text
dV ≈ delta*dF + 0.5*gamma*dF² + vega*dSigma + theta*dt
     + vanna*dF*dSigma + 0.5*vomma*dSigma² + charm*dF*dt
```

This is a selected-term local diagnostic approximation. It omits volatility-time and time-time terms and is not the complete multivariable second-order expansion. Use consistent decimal-volatility and calendar-time units. Charm enters this expansion through a cross term. Use full repricing as the numerical reference for finite scenarios, especially near expiry. Under physical scenarios, integrate the joint distribution of forward movement, IV movement and time, preserving correlations. A plug-in repricing at mean inputs generally differs from expected repriced value.

The familiar `0.5*Gamma*realized variance - abs(Theta)` calculation describes one local component. A directional unhedged option also carries delta and volatility exposure. Positive gamma rent alone is insufficient to authorize a purchase.

## 6. Research-backed model additions and upgrades

The papers support the mathematical methods. The proposed Nifty uses below are adaptations requiring independent evidence. Keep source claims and strategy hypotheses distinct.

| Method | Proposed decision contribution | Implementation and proof requirement |
|---|---|---|
| Bayesian online changepoint detection | Identify a new segment or the end of the entry regime | Compare capped/pruned run-length posteriors against existing CUSUM on identical triggers. Freeze hazard and likelihood. Measure detection delay and false resets. A change supplies no direction by itself. |
| Multiscale realized-volatility regression | Estimate whether the next few minutes offer enough movement for a long option | Use a parsimonious HAR-inspired model with causal intraday windows and clock normalization. This adaptation differs from the original daily HAR specification. Compare to EWMA and recent realized variance. |
| Calibrated competing-risk survival model | Estimate target-first, stop-first and still-open probabilities by horizon, then reassess holding duration | Treat horizon expiry and quote gaps explicitly. Model the actual option path. Benchmark against empirical conditional rates and the existing Brownian passage model. |
| Constrained SVI/SSVI | Improve strike comparison and scenario consistency | Check butterfly constraints, quotes and fit stability. Calendar constraints require sufficient multi-expiry data. A residual must be assessed against spread, age and fit uncertainty. |
| Heston or SABR scenarios | Test whether contract ranking and premium vulnerability survive richer volatility dynamics | Calibrate offline or at a profiled low cadence. Evaluate parameter identifiability and perturbation stability. Begin with one alternative to Black-76 rather than assuming each adds independent evidence. |
| Multivariate marked Hawkes | Test whether directional event sequences improve timing after a qualified setup | Compare signed counts and EWMA first. Verify event definitions and stationarity conditions. Statistical cross-excitation does not establish causality. |
| Microprice and queue-state models | Refine short-horizon timing and detect absorption or depletion | Estimate on the exact observed feed. A weighted midpoint is a basic control. Broker snapshots may not support full order-event or queue-position models. |
| Adaptive conformal uncertainty | Quantify forecast uncertainty and study abstention | Evaluate coverage, interval width and selection effects with delayed labels. Marginal/time-average coverage is not per-trade loss protection. |
| Least-squares continuation value | Improve exit timing while preserving entry opportunities | Train a small offline continuation regression on physical data. Runtime inference can be cheap. Adapt the optimal-stopping method to selling the held European option. |
| Shrinkage and partial pooling | Stabilize sparse family estimates | Use a transparent penalized model or hierarchical estimates as research baselines. Retain independent-day accounting and held-out evaluation. Pooling cannot manufacture new independent sessions. |

Changepoint detection maintains a posterior over the time since the last distributional change. It can be updated as observations arrive. The Apex application would add explicit option-response confirmation and benchmark against its existing detectors. [Adams and MacKay](https://arxiv.org/abs/0710.3742)

HAR combines volatility estimates over several horizons in a parsimonious regression. The proposed intraday adaptation needs its own training and evaluation, especially because the current history spans few independent days. [Corsi](https://realvol.com/HVOLPaper.pdf)

Gatheral and Jacquier provide conditions and constructions for SVI surfaces without static arbitrage. That improves surface consistency; profitable strike selection still needs separate testing. [Gatheral and Jacquier](https://arxiv.org/abs/1204.0646)

Heston describes stochastic variance in option pricing, and SABR models correlated forward and volatility dynamics. Their potential role here is alternative repricing and smile sensitivity. Neither calibrated risk-neutral model supplies a verified Nifty entry forecast. [Heston](https://finance.martinsewell.com/stylized-facts/volatility/Heston1993.pdf) · [Hagan and coauthors](https://derivativesacademy.com/storage/uploads/files/modules/resources/1702213496_hagan_kumar_lesniewski_woodward_managing_smile_risk.pdf)

Hawkes methods model self-exciting and mutually exciting event processes. Use their directional variants only after validating recorded event semantics and comparing simple rates. [Bacry, Mastromatteo and Muzy](https://arxiv.org/abs/1502.04592)

Order-flow imbalance has been linked empirically to contemporaneous short-interval price changes. This does not establish prediction of later option returns. Microprice and queue-reactive research offer additional models of quote dynamics, whose feed and timescale requirements must be checked. [Cont, Kukanov and Stoikov](https://arxiv.org/abs/1011.6402) · [Stoikov](https://www.ma.imperial.ac.uk/~ajacquie/Gatheral60/Slides/Gatheral60%20-%20Stoikov.pdf) · [Huang, Lehalle and Rosenbaum](https://arxiv.org/abs/1312.0563)

Adaptive conformal methods study coverage under changing distributions. Test label delays, dependence and the selected subset of traded predictions explicitly. Preserve predictions for abstained cases. [Gibbs and Candès, 2021](https://arxiv.org/abs/2106.00170) · [Gibbs and Candès, 2022](https://arxiv.org/abs/2208.08401)

Longstaff–Schwartz estimates continuation value by regression for American exercise. The proposed adaptation estimates whether to continue holding an already purchased European option using a physical outcome model. This changes the objective and requires fresh validation. [Longstaff and Schwartz](https://people.math.ethz.ch/~hjfurrer/teaching/LongstaffSchwartzAmericanOptionsLeastSquareMonteCarlo.pdf)

Deep hedging addresses derivative-portfolio hedging with frictions. It is a later research reference with a different action space from this all-in, buy-only account. A reinforcement-learning controller would additionally require a validated simulator, extensive independent experience, reproducibility and a change to the current rule-based design. [Buehler and coauthors](https://arxiv.org/abs/1802.03042)

## 7. Twelve proposed shadow experiments

These are proposed experiment IDs, not registered book names. Use a small staged pilot rather than enabling every candidate simultaneously. Freeze actual thresholds, horizons, warm-up and parameters after discovery and before a test period. Reuse existing structural distances and clocks as controls. A parameter without an agreed value makes the experiment incomplete, not eligible for a favorable backtest.

All books use the common freshness, blackout, time, instrument and fill safeguards. Required model inputs becoming invalid must have explicit behavior. New entries abstain. Held positions retain their documented fallback exit management and clock exits.

### A01 — Premium resumption after a pause

**Purpose.** Capture a second leg of a directional option move that a long impulse/pullback setup might miss.

**Entry.** Detect a fresh rise in a fixed option contract's premium and activity, followed by a bounded pause and a renewed break of that pause's high. Require contemporaneous forward direction agreement. Normalize activity by earlier-day clock baselines. Compare a plain price-pattern version with one using changepoint or persistence evidence. A PE premium rise can qualify during a downward forward move.

**Exit.** In the first comparison, preserve a simple existing premium trail and clock. A separate exit twin can use cessation of the estimated continuation state.

**Controls and failure.** Compare with current premium_momentum, an identical pause/break trigger without the model, and the documented earlier premium scanner. Failure includes repeatedly buying the late peak, more losers per captured move, or no improvement beyond premium momentum.

**Implementation.** Reuse fixed-contract histories, event IDs and premium-momentum rearming. Compute each candidate state once per engine step. Maintain one entry per distinct setup and define a fresh reset. Inspect `ideas/i15_continuation.py` and existing continuation specifications before duplicating logic.

### A02 — Volatility expansion with direction confirmation

**Purpose.** Capture an emerging move after compression while avoiding long options during persistent stagnation.

**Entry.** Define compression using only the preceding window. Trigger on a completed directional range break and a forecast expansion of movement over the intended holding horizon. Evaluate the selected option under joint forward/IV scenarios and elapsed time. Direction comes from the break. Volatility magnitude alone does not choose CE or PE.

**Exit.** Initial control uses the existing breakout exit. The research twin exits on loss of expansion evidence or the structural break failing, plus its unchanged fallback.

**Controls and failure.** Compare range break alone, range break plus recent realized volatility, and range break plus HAR-inspired forecast. Reject an apparent gain caused entirely by one expiry day or thresholds that work only at a single setting.

**Implementation.** Reuse rolling variance and range history. Add only a small shared regression evaluation. Fit offline with earlier sessions. Preserve the one-leg buy-only rule.

### A03 — Failed breakout reversal

**Purpose.** Capture a new directional opportunity when an attempted breakout fails, including short moves within a broad range.

**Entry.** A previously defined level is crossed, then price returns through it and completes a causal reversal confirmation. Candidate CE/PE direction follows that reversal. Compare confirmation from price alone against order-flow reversal or a calibrated change-state posterior. Require enough room to the next observed level for the intended option move.

**Exit.** Exit if the failed-break thesis invalidates, at the next tested objective, or under the fixed clock and fallback. No short option position is needed.

**Controls and failure.** Compare with fade_switch, a simple failed-break baseline, and first-touch fading. Measure whether confirmation reduces false fades without making entries too late. Cluster repeated probes of the same level.

### A04 — Price-confirmed gamma-wall reversal

**Purpose.** Test whether modeled gamma concentration adds information to A03-style reversals.

**Entry.** Observe an approach to a fresh modeled wall and an actual rejection or reclaimed level. Choose the long option matching the confirmed reversal. Gamma location is context, with the dealer-sign assumption and chain age attached.

**Exit.** First use the same exit as the comparable ordinary-level reversal. Test a gamma-sensitive exit separately.

**Controls and failure.** Match against OI walls, recent price levels, and arbitrary levels with similar distances. Compare wall-only, reaction-only and combined versions. Reversing assumed inventory signs must be included in sensitivity checks. Reject if added value disappears after matching or fresh-chain filtering.

**Implementation.** Correct and test flip-side interpretation and cache invalidation before this book. Do not infer measured dealer Vanna/Charm flow from OI.

### A05 — Smile-aware contract-selection twin

**Purpose.** Improve the option chosen for an otherwise identical qualified entry.

**Entry.** Inherit the exact trigger and direction of a chosen base book. Among permitted ATM/ITM strikes, compare exact premium responses under the same frozen scenarios. Use constrained smile values, Greek exposure, quote age and fit uncertainty. Select by one declared economic criterion with deterministic ties.

**Exit.** Retain the base strategy's decision logic, evaluated on the actual selected contract. Differences due to premium-dependent exit behavior must be reported.

**Controls and failure.** Compare original strike choice, delta-nearest selection and simple premium-response ranking. Use a common-clock diagnostic to isolate selection, then complete account replays to capture occupancy effects. Reject unstable strike switching or gains concentrated in stale residuals.

**Implementation.** Reuse `greeks_hi.price` and the existing smile. Exclude or hold out the candidate quote when testing apparent relative cheapness to reduce self-fit circularity. A surface residual can represent noise or missing risk rather than a bargain.

### A06 — Calibrated premium-opportunity admission twin

**Purpose.** Test whether empirically supported premium probabilities improve admission to a base strategy.

**Entry.** Use an existing setup. Admit only when a causal model of target-first, stop-first and time-expiry outcomes passes the frozen criterion, with uncertainty and sufficient support. Estimate probabilities on a chronological training/calibration split. Account for the terminal return of trades that hit neither barrier.

**Exit.** Preserve the base exit initially. If the label models a fixed bracket while the book uses a trail, score that mismatch explicitly and train the policy-relevant outcome before claiming expected-return accuracy.

**Controls and failure.** Compare the old passage score, zero-drift passage, empirical conditional rates, and the unchanged base. Require calibration and useful ranking before choosing a gate. A flatter calibrated probability with no discrimination is insufficient.

**Implementation.** Use simple penalized logistic or discrete-time competing-risk models before a complex learner. Hard gates remain inspectable. Rejected setup logging must continue for missed-opportunity analysis.

### A07 — Calibrated holding-duration exit twin

**Purpose.** Release capital from stalled positions and preserve positions still likely to develop.

**Entry.** Identical to the base book.

**Exit.** At fixed decision opportunities, compare calibrated conditional continuation outcome with exit now. Include elapsed time, favorable/adverse excursions so far, premium state and current market evidence. The estimator must condition on survival to this point. Preserve fallback exits.

**Controls and failure.** Compare fixed clocks, current exits and the previously failed race-decay exit. Label training data as surviving state sequences with terminal outcomes and explicit censoring. Reject improvements that chiefly sacrifice the base book's largest winners.

**Implementation.** Begin with coarse discrete hazards and a few state variables. Use fixed model artifacts and cheap lookups. Replay subsequent entries because an early exit changes the rest of the account's day.

Construct continuation paths from the raw tapes beyond the original book's exit through a prespecified terminal horizon. Historical trade records alone end too early to evaluate longer holds. Define end-of-session liquidation and genuine data censoring explicitly. This requirement also applies to A09. A07 remains an offline Wave 1 experiment until its conditional estimator beats a simple age/progress baseline on chronological held-out data.

### A08 — Greek-aware premium giveback exit twin

**Purpose.** Respond to erosion of a profitable option position while the underlying thesis may still appear intact.

**Entry.** Identical to the base book.

**Exit.** Use exact repricing to describe recent premium loss, then evaluate continuation under fresh forward/IV scenarios. Define a frozen exit criterion for adverse expected premium response or a validated giveback condition scaled by current contract sensitivity. Separate observed attribution from prediction.

**Controls and failure.** Compare current premium locks, the delta-adjusted trail and a fixed giveback rule. Reproduce existing c20_9t/v/e/h and lvl_trail exit variants where relevant. A richer formula must outperform those controls on identical policy tests.

**Implementation.** Reuse Greek and IV values at the same timestamp. IV inferred from the observed premium mechanically explains part of that premium, so attribution alone cannot validate a predictive exit. Record interaction terms and residuals.

### A09 — Learned continuation-value exit twin

**Purpose.** Learn a small explicit sell/hold decision from historically available state.

**Entry.** Identical to the base book.

**Exit.** Fit a continuation regression offline with a declared time grid and regularized basis. At runtime compare immediate paper exit value with conditional continuation value, including the remaining session and fallback policy. Use nested training to generate continuation targets. Test on later sessions.

**Controls and failure.** Compare existing exits, A07 and simple clocks. The backward training algorithm may use future training outcomes, but test decisions may not use future prices or fitted test paths. Avoid future-maximum targets masquerading as realizable returns.

**Implementation.** Distill to a small interpretable basis or lookup table. Do not search over arbitrary retraining schedules. Consider only after enough independent sessions exist to estimate and validate the policy.

### A10 — Directional event-persistence timing twin

**Purpose.** Improve the timing of an already qualified short-horizon setup.

**Entry.** Inherit the base setup and require directional persistence from correctly specified signed count or marked Hawkes state within a frozen waiting window. Log the original opportunity and any delay. Baseline activity must be included.

**Exit.** Preserve the base initially. Test excitation exhaustion only as a separate exit hypothesis.

**Controls and failure.** Compare immediate entry, a fixed delay, signed recent counts and EWMA. Reject a Hawkes gain explained by the delay alone. Verify performance survives the broker feed's observation cadence and missing-packet behavior.

### A11 — Basket/forward convergence opportunity

**Purpose.** Test whether a validated temporary discrepancy creates an additional directional entry while other books are idle.

**Entry.** Estimate a causal dynamic relation between the available weighted basket and the forward, including time-of-day basis and uncertainty. Trigger only when prior tests establish which side tends to adjust and the option has sufficient modeled movement available. Shared market exposure alone creates correlated prices without a tradable lead.

**Exit.** Convergence, invalidation, or a fixed clock, plus fallback management.

**Controls and failure.** Compare existing basket-gap and domino books. The earlier event study found little simple lead/lag evidence. Retain this candidate only if a specific conditional hypothesis improves on those results. This is a directional long-option adaptation, with no short basket hedge.

**Implementation.** Partial heavyweight coverage and asynchronous updates need explicit uncertainty. Freeze hedge/loading estimation using past data. Remove observations crossing gaps rather than treating delayed prints as leadership.

### A12 — Uncertainty-aware abstention twin

**Purpose.** Test whether the base strategy can avoid uncertain situations while retaining its profitable opportunities.

**Entry.** Inherit the base setup and allow it only when a validated forecast interval or uncertainty diagnostic meets a frozen criterion. Study model disagreement and out-of-support detection as simple controls.

**Exit.** Preserve the base exit. Invalid forecast support must be logged separately from a bearish prediction.

**Controls and failure.** Compare the unchanged base, simple data-quality eligibility and a fixed weather restriction. Report selective coverage on traded cases and missed winners among abstentions. Update conformal state only after labels become available and distinguish overlapping horizons.

**Implementation.** Validate forecast quality first. An interval that includes all outcomes can have excellent coverage and no trading utility. Any online calibration update needs an explicit frozen update rule and reproducible state.

## 8. Register books and evidence at the right levels

An entry twin, contract-selection twin and exit twin answer different questions. Use a small factorial comparison where justified. Base/base, new-entry/base-exit, base-entry/new-exit, then combined. Contract selection is another independent axis and should not produce a combinatorial explosion.

The existing rule scorer principally compares restricted books to free books. A genuinely new entry generator is not automatically a restricted subset of an old family. Extend the registry to identify entry experiments, exit experiments, contract-selection experiments and genuine restrictions. Use chronological paired-day comparisons and an explicit comparator for new-entry experiments; do not apply subset-permutation assumptions where they fail.

Record each candidate's source family, eligible phase, complete parameters, model artifact, discovery dates, hypothesis, null comparator, frozen test schedule, and current standing. Define its family from actual entry mechanics and day type. An exit twin generally shares the entry family.

Running beside the live feed means a paper shadow receives real arriving data and maintains its own book. It does not confer eligibility for the shared Conductor account. Admission still needs the official evidence gates and versioned rule history. New family qualification must be reconciled explicitly with the official representative/restriction process before promotion.

Each qualified book-plus-rule pair can eventually enter the Conductor. One shared account still holds one position at a time. All eligible strategies can observe the market concurrently. Selected trades inherit their strategy's persisted exit policy. Measure collisions and occupied time before claiming that more books increase realized opportunity coverage.

## 9. Integration instructions for Claude

Read `Engine.run_books`, `_entry_choice`, `_entry`, `_council`, `paper.request_entry`, `try_fill_entry`, `check_exit`, and the council adapter before selecting an integration point. Council and non-council books have different decision paths. A generic gate added to one path may never affect the other.

The council adapter runs once per virtual second. Select and record each experiment's decision cadence explicitly. A 100-ms microstructure candidate and its comparator need an integration path that supports that cadence. Update the explicit variant-parameter whitelist in `config.validate` and the explicit `REPRESENTATIVES` list in `apex/conductor/search.py` when adding new parameters or entry families.

`apex/conductor/diary.py` computes loss-label medians from the supplied rows. Fit these labeling thresholds within discovery data and store them with the model artifact. Later outcomes must not alter labels used to train an earlier model.

1. Reuse the shared raw market state and factor computations. Avoid one model filter per book if its inputs are identical.
2. Separate model data from dashboard formatting. Decision consumers need timestamped full-precision values, validity and artifact IDs. Rounded strings and display-only failure defaults must not become trading inputs.
3. Establish an explicit step order. If a model updates once per second, a 100-ms decision must knowingly use the latest completed update or wait according to its frozen rule. Record the actual as-of timestamp.
4. Treat cross-book agreement as a potentially order-sensitive field. Adding shadows must not silently alter existing recorded agreement values or strategy decisions. Define whether agreement counts fixed baseline families, all active books, or unique setup episodes, and version that definition.
5. Store trigger state before requesting a fill. Preserve model snapshots and rule versions across pending fills, restarts and day transitions. A delayed fill may require a declared recheck rather than an accidental use of future state.
6. Use the existing next-print paper execution convention, capital accounting, cooldowns, persistence and data guards. Specify release of account ownership after rejected or expired pending entries.
7. Extend missed-signal observation and diary family mapping for new state machines. A book that runs but cannot produce correct counterfactuals is incompletely integrated.
8. Extend register eligibility, control exclusions, weather schema mapping, dashboard visibility and reports. Keep legacy books loadable with their saved parameters.
9. Unit-test new semantics and regressions. Run normal-entry-point integration on live-shaped fixtures, then tape acceptance under the authorized replay gate.
10. Prove existing books' trades are unchanged when the new shadows are enabled, subject only to explicitly versioned observer-schema changes. Measure timing perturbation separately because live sampling can be affected by added load.

## 10. Keep the full system fast

The engine has a nominal 100-ms step and several models already update at slower cadences. Docs/24 reports historical live p95 delays above a second on some busy minutes. Reprofile current code; those measurements are historical rather than a current benchmark.

Implement a shared computation schedule with dependencies, invalidation keys and per-module timing. Process genuinely necessary per-packet features incrementally. Compute per-second model state once. Fit smiles or expensive scenario grids at a measured lower cadence with freshness limits. Perform parameter fitting, resampling, broad scenario simulation and strategy search offline.

Runtime targets should be agreed from measurements on the owner's machine. Report p50/p95/p99/max latency, decision data age, step overruns, queue length, memory and throughput for baseline and each added wave. A cheap average model can still create long synchronized stalls. Stagger optional observation work deterministically and keep trade management serviced.

Cache by all material inputs, including time-to-expiry, quotes, volatility state, model version and selected contract. Precompute small grids where approximation errors are bounded against the exact calculation. Use vectorization and existing shared LiveDay state before adding threads or processes.

A microprice effect lasting less than broker delivery and decision latency is not usable here. Require measured signal persistence beyond the full decision delay. Validate fast-path output against reference calculations and deterministic replay. GPU training and huge ensembles have no automatic live-runtime advantage.

## 11. Evaluation that matches the ambition

Evaluate three layers separately.

- **Mathematical correctness.** Known limits, finite differences, numerical convergence, sign/unit checks, invalid-input behavior and model invariants.
- **Predictive usefulness.** Chronological held-out discrimination, calibration, interval coverage, proper scoring rules, conditional support and comparison with simple predictors.
- **Trading contribution.** Gross account outcomes under the same execution convention, losing trades/days, opportunity capture, large-winner preservation, occupancy and runtime.

Good mathematics does not imply good forecasts. Good forecasts do not necessarily produce profitable trades under a particular policy. Good individual books can displace better opportunities in the shared account.

Use expanding chronological training, a separate calibration interval, and untouched later test sessions. Purge overlapping outcome windows. Cluster trade evidence by session and market episode. Refit schedules and update rules are part of the frozen specification.

Run the whole search, including model and threshold selection, on null controls. Keep failed attempts in the register. Do not choose the best of many candidates and report an unadjusted single-test probability. Preserve the official two-window standard and its minimum observations. Added model families increase the research burden.

Measure opportunity capture using unique option moves and reachable entry opportunities under the account's constraints. Future best entries are research labels and an optimistic benchmark. They must not select trades or certify every missed excursion as achievable profit.

Track every loss using document 32. A regression test can establish that a reproduced software mistake is corrected. A trading restriction needs later matching cases to establish evidence of reduced recurrence, including the winners it discards.

## 12. Recommended build order

**Wave 0 — Evidence and shared infrastructure.** Complete model provenance, diary completeness, numerical conventions, factor age, calibration benchmarks and baseline timing. Reproduce the failed scanner and exit controls. Finish deterministic account-selector semantics.

**Wave 1 — Highest-information pilot.** Build A01, A02, A03, A05, A07 and A08 in small increments. These cover complementary entry styles, contract choice and exit behavior. Some may remain offline experiments if predictive prerequisites or runtime budgets fail. Live shadow admission requires structural correctness and acceptable added load, while Conductor admission requires performance evidence.

**Wave 2 — Conditional extensions.** Evaluate A04, A06, A10 and A12 after their input, calibration and comparison requirements pass. They must demonstrate added value over Wave 1 and simpler controls.

**Wave 3 — More data and richer policies.** Evaluate A09 and A11 after enough independent history accumulates. Test Heston or SABR scenario alternatives within A05/A08 first. Consider richer model families only when their added complexity addresses an observed residual failure.

This ordering is a recommendation for the research program. It leaves all 68 owner-mandated weather groups in the search. A lower-priority model remains recorded and available for future evidence.

## 13. Deliverables and release decision

Claude should deliver an inventory of actual model consumers, reproducible chronology-correct baselines, and executable specifications for every implemented candidate. Each specification must resolve its thresholds, horizon, warm-up, rearm, model version, missing-data behavior, fill policy and exit fallbacks.

For every wave, publish a compact matrix with candidate, comparator, additional unique opportunities, losing trades, losing days, gross return, largest-winner capture, occupancy impact, predictive calibration, latency change and eligibility status. Attach tape hashes, code version, model artifact versions and full trial history.

Show the owner a combined-account comparison against c20_9x and against the previous Conductor composition. Apply the required window reset after material pool or priority changes. Report unmet zero-loss objectives explicitly even if older profitability gates pass.

The intended result is a system with several independently justified ways to recognize, select, hold and exit opportunities, an exact record of why each trade occurred, and measured evidence for every model allowed to influence the account.
