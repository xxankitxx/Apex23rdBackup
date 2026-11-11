# Forecasting that improves the champion: implementation mandate

11 November 2026. Owner-requested ambitious plan for Claude. Read after docs/42 and docs/43 section 7. This extends the predictive design; it does not replace outstanding correctness requirements or authorize a change to the main Conductor's ownership semantics.

## 1. The outcome to build

Build a forecasting service that can answer, before a decision:

1. Is a tradeable move developing, in which direction, and over what time scale?
2. Which eligible option best expresses that move under the owner's actual contract rules?
3. Should this champion trigger enter now, wait for a defined confirmation, or expire?
4. Once held, is continuing better than selling at the current executable bid?
5. When the champion is flat, is there an independently supported opportunity it misses?
6. Does adding this decision capability improve the actual combined paper account?

Treat these as different prediction and decision tasks. Do not answer all six with a threshold on P(+5% before -5% in 300 seconds).

Preserve long-option, gross paper accounting and all-in whole-lot sizing. Do not introduce an arbitrary minimum trade count or daily-loss cap. Optimize demonstrated profit and opportunity coverage together; report loss frequency, severity, missed runners and drawdown. Zero losses is the owner's aspiration, not an acceptance claim any finite replay can prove. Staying flat is appropriate when evidence is weak; sideways underlying movement alone does not establish that an option opportunity is absent.

## 2. Starting point and immediate corrections

Document 43 reports full-key binding, coverage priority, batched inference, next-second maturity fills and restart/orphan handling. These are foundations. This planning review read that document, the revised origins builder and registry; it did not independently certify the latest full suite, replay or live latency. Two matched trades are a smoke check, not a full-batch invariant proof.

Complete the end-to-end pending-order/restart test. Current documented policy drops pending orders at restart; test cancellation with no later fill, an explicit terminal record and no duplicate signal. Separately test restart of an already-filled position. A successful test must exercise engine requests/fills, not only call the contract selector in isolation.

### Sampling more strikes does not equal sampling executable contracts

`build_origins_v2.py` samples ATM plus four ITM strikes each side. It does not call the engine selector or tag actual eligibility. This broadens support but does not establish distribution alignment with traded contracts. Four strikes may still not cover every executable or held contract; quantify coverage rather than assume it.

The builder also skips an origin when ATM is fewer than four strikes from either recorded chain boundary. This can discard valid contracts on the other side and introduce market-location selection bias. Iterate available candidates independently, preserve valid ones, and record missing coverage rather than drop the whole timestamp.

Keep three labeled populations: broad market origins, engine-executable candidates, and champion decision episodes. Preserve all three; train/calibrate/evaluate each policy on its relevant population. Report candidate depth, delta, premium, DTE and coverage distributions. If historical delta/selector inputs cannot be reconstructed causally, label the approximation and exclude it from an exact-selector claim.

`registry.pick` is a useful start. It filters training dates, but selection alone is not artifact validation. At load verify file existence, content hash, embedded cutoff versus registry cutoff, feature/transformation versions, target policy, calibration cutoff and effective time. Missing/mismatched artifacts must produce an explicit unavailable state. Distinguish historical simulated availability from an artifact actually published before a live decision.

## 3. Build a decision dataset, not just a larger feature matrix

Store immutable, versioned tables linked by IDs:

| Table | Required content |
|---|---|
| Market snapshot | event/receive cutoffs, source ages, feature version, causal shared state |
| Candidate | full option key, eligibility, selector rank, bid/ask, quote age, Greeks/IV with provenance, support flag |
| Decision episode | trigger and parent policy ID, account occupancy, pending state, available alternatives, no-action reason |
| Forecast | artifact/calibration hashes, target definition, validity horizon, probabilities/quantiles, missingness, confidence diagnostics |
| Outcome | fill status/time, barrier events, policy returns, censoring reason, label maturity time |
| Action comparison | fixed counterfactual policy IDs, executable outcomes, comparison horizon, assumptions |

Retain rejected triggers and no-fill origins. Never train only on profitable trades. Keep a separate runner label, not a replacement for profit. Preserve sequence data preceding the trigger; never include features revised after the decision cutoff.

Use one episode ID across siblings, but retain separate policy labels. Do not average sibling outcomes into a synthetic champion. For generic pretraining weight each origin/episode so ten nearby strikes from one moment do not masquerade as ten independent market events. Normalize by episode/day where appropriate; estimate uncertainty in day blocks.

Build a data-quality report before fitting: usable sessions, unique episodes, maturity/censoring counts, coverage by candidate class, selector agreement, quote freshness, missing features and regime support. Larger row counts do not increase independent evidence in proportion.

## 4. Model architecture: shared market state, specialized decisions

### A. Activity and competing-event timing

First replace the eight unrelated binary heads with a small coherent discrete-time competing-risk model. At interval j, conditional on no prior event, output h_up(j), h_down(j), h_survive(j), summing to one. Then:

```
S(0) = 1
S(j) = S(j-1) * h_survive(j)
P(up by J) = sum_j<=J S(j-1) * h_up(j)
P(down by J) = sum_j<=J S(j-1) * h_down(j)
```

Use the existing horizons first to preserve comparisons. Add longer horizons only when motivated by the champion holding distribution and sufficient uncensored observations. Distinguish no event from missing observation; a feed gap is not a quiet market.

Expose activity probability and direction conditional on an event. Benchmark against activity-only predictors based on premium, expiry, spread and realized volatility. A model that predicts fast movement but cannot distinguish its sign must not be sold as accurate direction forecasting.

Keep the symmetric 5% baseline for continuity. Add policy-relevant event definitions in a small preregistered experiment, with barriers defined from information at origin. Do not tune dozens of barriers until one wins.

### B. Premium-return distributions

Predict conditional return quantiles at selected horizons, with ordered quantiles and calibrated coverage. Begin with regularized linear/GAM baselines and shallow gradient-boosted quantile challengers. Track pinball loss, interval width, coverage and selection-conditional performance. Do not infer an expected return from the median alone.

The desired output is a distribution describing both likely movement and uncertainty. A point prediction of “up” cannot distinguish a slow marginal move from a fast opportunity large enough to survive spread and delayed entry.

### C. Champion-policy admission

For each named parent, reconstruct its own trigger, actual eligible contract and counterfactual unchanged exit policy. Predict policy return and probability of failure before development. Include book-policy identity; use partial pooling across genuinely related policies rather than a large separate model for each sparse book.

Compare three targets: first-barrier outcome, unchanged-parent return and a return distribution including runner magnitude. Report where they disagree. Begin with a residual model: does weather add information beyond the fact that the champion triggered? This directly measures incremental predictive value.

An admission decision should use expected value and uncertainty under the named policy, not an arbitrary top-percentile threshold. Threshold selection belongs to earlier calibration windows and must report a coverage/profit/missed-runner frontier. Do not optimize win rate alone.

### D. Timing: enter versus wait

At a champion trigger evaluate enter now, wait a small predefined interval with a causal confirmation rule, or let the trigger expire. Waiting must have a deadline and a defined recheck policy. Label missed moves, worse prices and no-fill outcomes as part of the policy; do not keep only occasions where waiting improved entry.

Build a simple persistence/confirmation baseline before a learned timing policy. Compare with a nonforecast delay of the same duration so gains are not incorrectly attributed to model intelligence.

### E. Contract choice

Among contracts eligible under the owner rules, predict the return distribution under the same trigger and exit policy. Compare exact executable whole-lot rupee outcomes as well as percentage returns. Model spread, fill availability, premium sensitivity and IV exposure; a cheaper option with a larger percentage move is not automatically the best account choice.

Keep contract selection independent of timing initially. Use actual candidate states and a fixed fill convention. Any substitution or refreshed decision gets a new linked forecast; never transplant a probability to another option.

### F. Continuation and optimal stopping

At predefined holding checkpoints and original-parent exit events, compare sell-now with one or more fixed continuation policies. Inputs include current bid return, peak, drawdown from peak, age, time since peak, remaining session, thesis persistence, participation, IV trajectory and forecast support.

Estimate:

```
continuation_advantage(state, policy)
    = E[future executable exit value under policy - sell-now executable value | state]
```

For an existing position this is incremental value from now, not return from the entry ask. Include distributions and uncertainty. Separate runner preservation from giveback protection: their intervention opportunities and costs differ.

Start with fixed-horizon continuation labels and regularized regression. Only then investigate fitted value iteration/optimal stopping with cross-fitted targets and strict chronological policy evaluation. Never label the action using the best future price; that trains an oracle unavailable live. Include reentry and occupancy effects in subsequent whole-book/account replays.

## 5. Advanced models with specific jobs

### Joint underlying, IV and smile scenarios

Build a compact joint distribution of underlying changes, IV level changes and skew/smile changes. Translate scenarios into premium changes using causal Greeks and local Taylor terms for small moves, full repricing for large/unstable scenarios. Explicitly define time and volatility units, theta convention, vanna cross term and volga curvature. Verify against numerical perturbations.

Use this as a structural challenger to direct premium forecasting. Combine only if out-of-fold predictions demonstrate incremental value. Record the direct-versus-scenario disagreement as uncertainty. Fit the IV surface with no-arbitrage diagnostics and quote-quality weights; do not manufacture precise Greeks from stale/inconsistent quotes.

GEX/vanna/charm exposure features require inventory-sign assumptions; open interest alone does not identify dealer holdings. Keep scenario interpretations and confidence flags. A put wall must not become an unconditional floor rule. Require feature-block ablation before retaining expensive Greek calculations.

### Causal market transitions and sequences

Add a small temporal feature bank: directional persistence, acceleration, reversal count, participation broadening/narrowing, order-flow absorption, spread recovery, IV acceleration and lead/lag stability. Compute from bounded rolling buffers, shared across books.

Then compare a small causal temporal convolution model with tabular baselines, using identical data and chronological splits. This is a challenger, not the default architecture. Audit whether available tape depth and timestamps support the intended microstructure features. Do not use synthetic order-book reconstruction as observed evidence.

### Regime specialists with shrinkage

Use soft regime probabilities for trending, reverting, expanding-volatility and deteriorating-liquidity conditions. Begin with simple observable states; compare to a latent-state model only if its fitted artifacts are chronological. Specialists should share a global prior and fall back when support is thin.

The routing model must be trained on out-of-fold specialist predictions. Do not fit a gate to whichever specialist won each historical day and call it foresight. Keep specialist count small until independent session coverage justifies expansion.

### Historical analogs as a diagnostic and challenger

Retrieve comparable earlier episodes using a causal, normalized market/option state. Return empirical outcome distributions, effective neighbor count and distance, not just a predicted direction. Exclude the current episode/day and future data. Compare with global baselines; reject the approach when similarity is weak. This can make failure analysis understandable without claiming a past pattern must repeat.

### Adaptation without self-deception

Maintain a frozen control and an adaptive challenger. Separate probability recalibration, drift detection and structural retraining. Only mature labels can update any of them. Limit influence of overlapping observations and persist adaptation state/version.

Adaptive conformal methods are a candidate for interval-coverage monitoring and adjustment, not guarantees of per-trade profit or regime-conditional safety. Evaluate coverage on selected trades as well as broad origins. Broad coverage can conceal poor coverage on the subset the engine trades.

Do not use contextual bandits or reinforcement learning as a shortcut around evaluation. Logged deterministic actions lack overlap for many off-policy estimators. In this paper system, start with explicit tape-based alternate policies under stated execution/no-market-impact assumptions. These simulate possible outcomes, not observed real fills. Consider bandit routing later only with valid action/support logs and a narrowly specified objective.

## 6. New weather fields that serve decisions

Every field needs units, cutoff, availability, provenance, computation cost and a defined hypothesis. Add in blocks, not as a giant untested bundle.

| Block | Proposed fields | Decision served |
|---|---|---|
| Movement | favorable/adverse cumulative incidence; survival; activity and conditional direction | Whether and how quickly to act |
| Premium | return quantiles; expected policy value; spread-adjusted hurdle | Is the move economically meaningful? |
| Persistence | momentum persistence; acceleration; reversal density; participation trend | Enter now versus wait |
| Options | delta/gamma/vega exposure; IV/skew velocity; scenario residual; quote/surface confidence | Contract choice and premium behavior |
| Holding | continuation advantage; giveback probability; time since peak; parent-exit disagreement | Hold versus sell |
| Trust | support distance; effective episode support; model disagreement; calibration age; missingness | Which forecast can be relied on? |

Learned weather used to train another model must be generated out of fold, not fitted on its own outcome. Avoid feedback loops where a model uses its retrospectively revised prediction as an input.

## 7. Shadow experiments and combination design

Retain doc42's six roles: admission, timing, contract selection, continuation, giveback protection and independent opportunity scout. Give each a unique version, explicit hypothesis, matched baseline and intervention ledger. No twin is successful merely because it remains identical to its parent.

The scout should seek episodes the champion misses, such as a causally detected participation/flow transition with a supported premium path. Its aim is complementary opportunities, not more trades at any cost. Measure overlap, occupancy and displaced champion runners.

Run one-mechanism comparisons first. After identifying supported components, run a small preregistered interaction matrix: admission+timing, admission+continuation, and then the strongest candidate with the scout. Do not search all subsets of books on the same 15 sessions. Preserve the mirrored-source-book semantics; compare complete account paths with actual arbitration and sizing.

Promotion evidence must show both standalone mechanism value and account-level contribution. A useful admission model may reduce trade count; the scout can recover independent opportunities, but only the combined simulation can establish the resulting trade-off.

## 8. Evaluation that can reject our favorite ideas

Use chronological train/calibration/evaluation windows with mature labels and overlap-aware purging. All preprocessing, feature selection, model selection, calibration and thresholds fit within the allowed past. Repeatedly studied tapes remain historical research, even under walk-forward replay. Reserve future sessions for confirmation.

Freeze a small model roster: activity baseline, current corrected logistic baseline, coherent hazard baseline, champion-policy baseline, one nonlinear challenger. Add other architectures only when a measured error pattern motivates them. Keep an experiment registry including failures and all parameter searches.

Required scorecard:

- Forecast: log loss/Brier, reliability, conditional direction skill, return-quantile loss/coverage/width, time-to-event quality with censoring.
- Entry: accepted coverage, losses avoided, winner profit rejected, runner profit missed, delayed-entry cost, no-fill incidence.
- Holding: eligible interventions, interventions taken, matched incremental value, runners shortened, subsequent reentries.
- Account: rupee equity, gross profit/loss, drawdown, positive/negative days, opportunity displacement, whole-lot utilization, trade count.
- Robustness: results by day, expiry, premium, support, data quality; dependence on the best session/runner; paired day-block uncertainty and sensitivity to fill assumptions.
- Operations: decision latency, data age, queue capacity, contract coverage and restart consistency.

Compare against no-forecast controls. Include an activity-matched control so high-volatility selection is not mistaken for direction skill. Use predefined failure criteria: no directional improvement, no policy-value improvement, benefit disappears under executable fills, or unacceptable latency means no promotion. Report inconclusive evidence honestly; no fixed number of days guarantees rare-loss safety.

## 9. Speed and reliability are part of the model

Shared market features once per snapshot; contract features and inference in a batch. Cache only with full causal keys including contract/expiry, snapshot version, feature/model version and holding-state dependencies. A stale fast forecast is not an improvement.

Use separate fast decision, bounded audit-write and offline training paths. Account/exit forecasts take priority under capacity pressure. Skip optional research work explicitly; do not block the account or silently score a partial feature vector as if complete. Require defined fallback to the unchanged parent for unavailable shadow advice, with reason counts.

Measure full receive-to-decision latency and stage p50/p95/p99/max under normal and burst conditions, including 24 held contracts, pending orders, quote gaps, writer backlog and reconnect. Set operational budgets from measured engine cadence/headroom before adding models. Loaded-machine feed timing is useful, but does not certify live-step latency or isolate batching's causal improvement across different workloads.

Use bounded worker counts and an explicit research/live resource schedule. Do not launch another ten-way replay simply because ten cores exist. Cache shared causal snapshots and label paths where equivalence tests permit; candidate policies still need independent state transitions. Distill a complex offline model only after it earns its complexity; verify distilled prediction and policy fidelity.

## 10. Delivery stages, with gates

| Stage | Deliverables | Gate |
|---|---|---|
| M0: trustworthy plumbing | end-to-end lifecycle fixture; full-batch contract reconciliation; label parity; latest suite result; engine latency report | No unexplained mismatch; explicit coverage/censoring; measured runtime behavior |
| M1: aligned data | candidate/episode tables; exact-selector tags; chain-edge repair; data-quality/support report; validated registry | Reproducible causal population and provenance |
| M2: useful baseline forecasts | coherent hazards, return distributions, activity/direction separation; chronological controls | Proper-score and policy-relevance evidence, or explicit failure |
| M3: champion decisions | admission, timing and continuation models with their own labels and controls | Incremental matched value; runner/missed-opportunity accounting |
| M4: advanced challengers | Greek scenarios, temporal model, specialists/analogs where justified; feature ablations | Incremental evidence beyond M2/M3 at acceptable cost |
| M5: account integration | single-mechanism shadows, limited interaction tests, baseline-plus-candidate Conductor replay | Actual account contribution; no standalone-sum substitution |
| M6: forward operation | frozen prospective package, mature-only adaptive challenger, failure/drift monitoring | Forward evidence with uncertainty; controlled promotion decision |

Do not describe M0 completion as model improvement. Do not postpone data correctness until M4. Each stage delivers executable artifacts, versions/hashes, tests, metrics, failed hypotheses and remaining uncertainty.

Proposed module boundaries under `apex/predict/`: decision schema, candidate enumeration, artifact validation, competing-risk heads, policy-value heads, calibration and support diagnostics. Keep tape builders/trainers/evaluators outside the live engine, in a reusable research package rather than burying each new implementation in a dated run directory. Names are implementation choices; enforce interfaces and avoid duplicating existing components.

First reply requested from Claude: an implementation matrix mapping every stage to current status, concrete files, datasets available/missing, expected computation and acceptance tests. Then execute M0/M1 and the simplest M2/M3 models. No further broad plan is needed in place of those deliverables.

## 11. Research references

- [Competing-risk cumulative incidence, scikit-survival](https://scikit-survival.readthedocs.io/en/latest/user_guide/competing-risks.html): mathematical basis for mutually exclusive first-event probabilities; not evidence of market predictability.
- [Gibbs and Candes, online conformal inference under distribution shifts](https://www.jmlr.org/beta/papers/v25/22-1218.html): motivates adaptive uncertainty calibration; coverage is not a trading guarantee.
- [Dudik, Langford and Li, doubly robust policy evaluation](https://arxiv.org/abs/1103.4601): background for later policy-learning research. Applicability requires careful logging/support assumptions; it does not justify estimating unobserved deterministic actions without evidence.

The ambition is a system that predicts actionable alternatives, recognizes when its evidence is weak, learns from mature outcomes and demonstrates what each capability contributes. The destination is not a larger collection of scores; it is better decisions on the exact contracts and account paths the owner actually trades.
