# Forecast audit and champion improvement plan

11 November 2026. Codex review of revised documents 40/41, forecasting implementation, research scripts and the completed p41 replay outputs. Instructions for Claude; preserve the owner's main Conductor and book semantics while conducting the experiments below.

## 1. Verdict

The owner's concern is justified: the implemented system does not yet answer the forecasting questions needed to improve champion entries and exits. However, poor entries do not establish that forecasting is impossible, nor that a larger model would solve the problem. There are concrete implementation and experiment mismatches to fix before judging predictive power.

Claude built useful foundations: causal rolling features, frozen logistic models, multi-horizon first-barrier targets, forecast records, a maturity queue, calibration experiments, ranges and shadow integrations. Document 41 appropriately admits weak directional discrimination and in-sample replay status. These are useful baseline results, not the finished predictive conductor requested in document 40.

Three distinctions are essential:

1. The main champion's forecast is recorded at fill; it does not gate that champion's entry. Its bad entries therefore cannot demonstrate failure of an admission policy that was never deployed.
2. A forecast of +5% before -5% within five minutes is not a forecast of the champion's eventual result under its own exit policy. An entry model is also not automatically a continuation model for an existing position.
3. Many forecast-book trades buy a different contract from the one scored. Research thresholds and runtime scores also differ. Current results mix forecast quality, contract selection, execution and exit-policy changes.

The ambition should be a coherent, calibrated forecast of actionable alternatives, with measured incremental value to the champion. Neither additional mathematics nor selecting past winners can establish zero future losses. Retain the owner's gross paper accounting and all-in rules; do not introduce an arbitrary loss limit or trade quota as a substitute for solving this problem.

## 2. Audit scope and reproducible evidence

Read: documents 40/41; `apex/predict/{features,models,targets,ledger}.py`; `apex/engine/pred.py`; relevant integration in `paper.py`, `council/__init__.py` and `engine_main.py`; research `walk_forward.py`, `make_artefact.py`, `champ_separation.py`, `champ_forecast.py`, `contribution.py`; saved p41 trades and forecast ledgers.

Independent audit artifacts:

- `research/audit_forecast_p41.py`: reconstructs 15 unique session results, links forecast signals to purchased contracts, compares parent/runner trade identity and reconciles return-sign reporting.
- `research/audit_forecast_scores.py`: compares fitted raw scores with the deployed projection on 204,010 eligible saved origins; checks the vectorized calculation against actual `Forecaster.forecast` on 31 distributed rows.
- `data/research/codex_forecast_audit_2026-11-11/replay_audit.json` and `score_audit.json`: numerical evidence.

Reproduce from repository root:

```powershell
python research/audit_forecast_p41.py
py -3.13 research/audit_forecast_scores.py
py -3.13 -m pytest tests/test_predict.py tests/test_pred.py tests/test_ranges.py -q
```

The first script uses only the standard library. The score audit needs NumPy from Python 3.13 here; the default `python` environment lacks it.

Observed targeted test result: **25 passed, one teardown error**, not a clean suite pass. The session-wide data-tree fence detected changes under `data/replay/2026-11-09/20261111-011916-idle/paper/`. A separate Claude `plain_replay.py` process was running. The fence compares all non-log data files and cannot attribute writes to a process; this is consistent with concurrent replay interference, not proof that the last range test wrote those files. Rerun in an isolated checkout/data root. Do not disable the fence or stop someone else's replay. The full suite was not rerun by this audit.

No trading runtime, models, thresholds, pool or owner settings were changed. This is a forecasting-focused review, not certification of every repository line or of live performance.

## 3. What the completed replays actually show

These are **sums of saved per-trade rupee P&L across independent session books**, not one continuously funded account, not incremental Conductor contribution, and not an out-of-sample estimate. Positive/negative days use that saved P&L. Zero-P&L trades are separated from losses.

| Book | Trades | Wins / losses / zero | Aggregate saved P&L, Rs | Positive / negative days |
|---|---:|---:|---:|---:|
| c20_9y | 92 | 54 / 38 / 0 | 1,194,371.75 | 11 / 4 |
| fr_c20_9y | 92 | 54 / 38 / 0 | 1,194,371.75 | 11 / 4 |
| fx_c20_9y | 139 | 93 / 46 / 0 | 589,179.50 | 9 / 6 |
| p02_clock | 718 | 390 / 327 / 1 | 402,239.50 | 10 / 5 |
| p02_top1 | 294 | 155 / 139 / 0 | 77,821.25 | 6 / 9 |
| p05_adaptive | 795 | 417 / 368 / 10 | 385,996.00 | 10 / 5 |
| p02_ctl_mom | 558 | 252 / 305 / 1 | -105,384.50 | 6 / 9 |

The runner twin matches the parent's contract, entry/exit times and prices on every trade in all 15 sessions. No effective change occurred. Explain why before interpreting it as evidence against runner forecasting.

The exit twin raises the observed win rate from 58.7% to 66.9% but roughly halves aggregate saved P&L. It has 67 forecast exits. This illustrates why taking quick wins can destroy the economics of a runner-dependent strategy. Subsequent entry opportunities change when a position closes early; whole-book results are not a matched experiment on exit decisions alone.

Document 41's day counts use summed percentage returns in places. On 3 November, c20_9y's summed return is +0.9128%, but its saved P&L is **-Rs 2,356.25**. On 2 November p02_top1 sums to +2.9472%, while saved P&L is **-Rs 4,559.75**. Six book-day sign disagreements are recorded in the audit. Both statistics can be useful, but label them correctly; a positive sum of percentages does not establish a profitable paper-account day.

`contribution.py` compounds a synthetic starting 100 across returns and ranks standalone books. It does not simulate adding a book to the Conductor. Therefore “no forecast book adds to the account” is not established by that calculation. The correct conclusion is that the reported standalone comparison has not established incremental account benefit.

## 4. Verified mismatches to correct before further model search

### A. The model scores one contract and the book purchases another

`Pred._signals` selects a scored strike/right. `paper.evaluate_gen` transfers direction and signal episode, but does not bind that contract to the subsequent entry. The engine's independent selection then chooses the traded option.

Joining each p02/p05 trade to its recorded signal gives:

| Book | Linked trades | Different strike/right | Fraction |
|---|---:|---:|---:|
| p02_clock | 718 | 658 | 91.6% |
| p02_top1 | 294 | 276 | 93.9% |
| p05_adaptive | 795 | 679 | 85.4% |
| Momentum control | 558 | 476 | 85.3% |

Example: 19 October 09:25:28, p02_clock predicts `23100|CE` but buys `NIFTY|OPT|2026-10-19|23000|CE`. These are not interchangeable premium-return targets. The mismatch is also explicitly acknowledged qualitatively in document 41; this audit measures its prevalence. It does not prove every mismatch caused a loss.

**Required repair:** either select the actual executable contract first and score that contract, or carry the forecast's full contract identity through the pending request and fill. Include exchange/symbol/expiry/strike/right. If substitution is necessary, reforecast and rerun admission; record the new forecast and reason. Never silently transfer the probability to another strike. Test ATM changes, quote gaps, expiry rolls and delayed fills.

### B. Threshold training and runtime scoring are different functions

`make_artefact.py` computes thresholds from raw `T300 - A300`. `Forecaster.forecast` first applies a cumulative probability projection across all horizons and then computes the edge. `walk_forward.py` also evaluates raw scores.

On the same 204,010 eligible origins, projection changes 33,020 scores, with maximum absolute difference 0.4234. At the stored 95th-percentile line, raw scores admit 10,201 origins, deployed scores 9,557, with **1,424 membership changes**. At the 99th-percentile line: 2,041 versus 1,650, with **549 changes**. This is a deterministic parity defect, not sampling noise. These are origin-level comparisons, not counts of changed executed trades.

**Required repair:** one serialized prediction pipeline for fitting threshold policy, offline evaluation and runtime. Test identical probabilities, ranking and admission on the same feature matrix. Include all projection/calibration steps in the version. Fit thresholds on historical calibration data using the deployed score, not fitting-data percentiles of another score. The eventual competing-risk model below removes the need for this ad hoc projection.

### C. Forecast coverage does not follow the position

`Pred.update` scores four nearby contracts: ATM and first ITM on each side. `edge_of` accesses that current set. A held option falls outside coverage as the underlying moves. Only 46 of the parent's 92 trades have a non-null recorded fill forecast. Missingness can depend on exactly the market movement the system is intended to judge.

**Required repair:** the shared service must cover the union of entry candidates, pending requests, held contracts and contracts required for outstanding forecast outcomes. Compute shared market features once and contract features in a bounded batch. Record a reason for every missing forecast: warm-up, unavailable instrument, stale quote, unsupported expiry, invalid artifact or capacity. Missing is neither low confidence nor a negative prediction.

### D. Wrong learning target for champion admission and continuation

The current targets measure first passage of symmetric 5% premium barriers at 30/60/180/300 seconds. That is a legitimate question, but different from the c20_9y policy. A signal may hit +5% first and later lose under the champion; another may initially dip yet become a substantial runner.

`held_keep` and `held_exit` reuse a fresh-entry edge for the held option. They do not condition on position age, current gain, drawdown from peak, original thesis or impending parent exit. A fresh buyer pays an ask; an existing holder compares continued ownership with selling at the current bid. Those action values differ.

**Required repair:** retain the first-passage baseline, but train separate champion-policy admission and held-position continuation outputs. Do not attach “runner model” to an entry-score threshold without a matching target and validation.

### E. The champion-separation experiment is not a champion-specific test

`champ_separation.py` groups all `c20*` siblings by `(day, contract, round(trigger_t/5))`, takes the first sibling's weather, averages sibling returns and uses maximum sibling peak/best result for other targets. It computes `r9y` but does not use it as the win target. Rounding creates bins, not true within-five-second episodes. Adding/removing siblings can change the label even when the champion trade is unchanged.

**Required repair:** stable causal episode IDs, one explicitly named reference policy, its own trigger features, and labels from that policy. Keep sibling-policy outcomes in separate columns. Treat “profitable”, “developed 5%” and “runner” as separate outcomes, not one hierarchy that calls small positive trades failures. This old result rejects the tested family-average linear classifiers; it does not establish that champion losses cannot be distinguished by weather.

The documented champion-forecast analysis scores only 64 episodes; its weak results are evidence against using that score now, not enough data to rule out every nonlinear or sequence-based model.

### F. The replay does not provide chronological proof

The installed artifact was fitted on all 15 sessions through 9 November. The completed historical replay therefore tests a future-informed artifact on those same sessions. Document 41 acknowledges this. `Forecaster` validates schemas but does not enforce the artifact training cutoff against the current session.

**Required repair:** artifact registry with trained-through, label-mature-through, feature/code hashes, calibration interval and effective-from. Strict evaluation selects only artifacts available at that point in time; discovery mode may deliberately override, but must be visibly labeled and excluded from promotion evidence. Version fitted feature coefficients as well as model weights. Historical HMM/Hawkes/derived fields require their own provenance audit.

### G. Outcome and decision lifecycle needs parity tests

- Live `_mature` can fill an origin at a later fresh quote after the one-second delay; offline target construction requires the exact next-second fill. The live loop attempts filling before checking the unfilled lapse, so a sufficiently late fresh quote can defeat the intended deadline. Define one explicit fill deadline and event order.
- Offline calibration waits for a fixed terminal window; live calibration can update as soon as the first barrier resolves. Early resolution is legitimate for first-passage labels, but it is a different update schedule. A saved outcome's later peak/terminal return must not be inferred from a queue that stopped at first passage.
- Live calibration is a bin-based adjustment of frozen probabilities, not a model learning new feature relationships. Document 41 reports worse calibration in the tested adaptive experiment. Do not assume it improves merely because it updates.
- The maturity queue's capacity eviction can discard a filled outstanding origin. Emit an explicit censored/capacity outcome and monitor loss of coverage; do not silently alter the training population.
- `paper._gen_exit` uses `(o.get('age') or 9e9) < 15`. A legitimate age of zero is treated as unavailable, bypassing the premium barrier check that step. Use explicit missing-value validation and test age 0, stale, missing and invalid values.
- `Ledger` skips a torn JSON line on read but does not repair/quarantine its unterminated tail before appending. Restart does not reconstruct pending maturity/calibration state. Signal sequence restart also needs reconciliation with persisted fired episodes. Add deterministic restart and write-failure tests; do not interpret append-only as automatically crash-safe.
- Ledger flush runs synchronously from the engine prediction feed. The comment describing it as off the decision path is inaccurate. Bound writes and measure latency; use the existing writer architecture or a dedicated queue with explicit durability/backpressure semantics.

These lifecycle observations are source-review findings, not claims that each occurred in the 15-session batch. Add focused reproductions and measure incidence before assigning P&L impact.

## 5. The forecasting system to build

### 5.1 One decision contract, several useful answers

For each champion trigger, emit an immutable record containing: full contract identity; event and receive cutoffs; executable reference quote and its age; parent/episode/policy IDs; model/training/calibration versions; prediction validity duration; coverage/support; and the following separate outputs:

- probability of a favorable move, adverse move and neither by each horizon;
- conditional time-to-favorable/adverse-event distributions, plus unconditional survival probability;
- quantiles of premium return and expected policy return under the named exit policy;
- probability of becoming a runner versus failing before developing;
- admission or wait recommendation with uncertainty and the alternative being compared.

At held-position checkpoints emit incremental continuation value versus selling now. Always distinguish underlying direction, option premium direction and movement speed. A forecast of activity is not a forecast of profitable direction.

### 5.2 Coherent competing-risk movement and direction model

First implement a small discrete-time hazard model with intervals such as 0–30, 30–60, 60–180 and 180–300 seconds. Conditional on no barrier yet, a multinomial head predicts favorable hit, adverse hit or survival. Calculate cumulative incidence by summing prior survival times interval-specific hazards. The probabilities are coherent by construction. Handle observed first hits and censored paths in the likelihood.

Use an explicit activity component and a conditional directional component. Compare against an activity-only baseline using premium, DTE, spread and realized volatility. If the directional component cannot beat this baseline, do not advertise high short-horizon AUC as directional skill. Document 41's side AUC around 0.533 is an important warning.

Evaluate proper probability scores, reliability and direction conditional on movement; report hit-time accuracy on all eligible origins, including censored/no-hit cases. The existing winner-only speed ranking cannot alone establish usefulness for prospective trade selection.

### 5.3 Champion-specific residual model

Start with c20_9y as a named reference, while retaining any distinct current champion reference separately. Build one row per causal trigger, including missed/rejected triggers, and replay that reference policy independently for labels. Features must exist before entry. Predict policy-return distribution and failure-before-development; preserve the original first-passage outputs as supporting features.

Use strong regularization and partial pooling between genuinely related book policies, with explicit policy identity. Begin with logistic/generalized additive baselines, then a small gradient-boosted challenger. The effective sample is episodes and days, not the hundreds of thousands of correlated per-second observations. Fit model choice and thresholds inside earlier chronological windows.

Model weather interactions only where motivated: momentum persistence versus reversal, participation versus narrow leadership, option demand versus underlying move, volatility expansion versus decay, and spread/quote health. Compare blocks through ablations. Do not search hundreds of arbitrary indicator thresholds until the old tapes become perfectly classified.

### 5.4 Greek-aware premium forecasting

Build a causal local scenario model alongside the direct premium model. For small scenarios, decompose premium movement using delta times underlying change, one-half gamma times squared change, vega times IV change, theta times elapsed time, vanna cross effects and volga curvature. Define time/IV units and Greek conventions explicitly. Use full repricing for larger jumps or near-expiry instability; report residuals and quote quality.

Forecast joint underlying/IV/skew changes rather than feeding a perfect future underlying move into an options formula. This produces a scenario distribution, not a known future option price. Compare direct premium forecasting, scenario forecasting and their calibrated combination out of sample. Add IV age, smile-fit residual, Greek stability and model disagreement as confidence inputs.

Treat GEX, gamma flip, vanna and charm exposure as scenario features with uncertain positioning assumptions. Open interest does not reveal dealer inventory sign. In particular, dealers short puts generally sell more underlying as spot falls to hedge their increasing positive option delta; a put wall is not automatically a buying floor. Do not encode the earlier quoted narrative as a mechanical certainty.

### 5.5 Held-state continuation and giveback models

Create decision snapshots at parent exits and predeclared held checkpoints. Inputs include current bid-return, running peak, drawdown, time held, time since peak, current market/IV/flow state, thesis persistence, remaining session and forecast coverage. Labels compare explicit executable alternatives: sell now, follow the original parent, or hold under one predefined continuation policy.

Estimate incremental return versus the sell-now bid, not versus the old entry ask. A profitable trade can have negative continuation value; a currently losing trade can have positive continuation value. Avoid hindsight labels such as “best future exit”. Evaluate candidate trajectories from the same starting state, then separately replay the whole book to include changes to later entries.

### 5.6 Sequence and transition forecasts, after the baseline works

Weather at one instant can miss an absorption-release or leadership transition. Add a compact causal temporal model over pre-entry feature trajectories: slopes, acceleration, persistence, reversal count and changes in participation/IV/flow. Compare against a small causal convolution model only after data sufficiency and latency are established.

Do not train a large order-book neural network on 15 sessions and assume the paper's results transfer. First establish whether tapes contain the required depth, update order and coverage. Missing order-level history cannot be reconstructed honestly from sparse snapshots.

### 5.7 Learning from new evidence

Separate three mechanisms: probability calibration, detection of distribution change, and retraining feature relationships. Update only on mature observable outcomes; persist every version. Use day/episode weighting so many overlapping observations of one move do not dominate learning. Replay online updates in the exact event order used live.

Keep a frozen control beside every adaptive challenger. Track forecast residuals, probability reliability, interval coverage/width, missingness and regime support. Require recovery behavior for stale feeds and model failures. A model disagreement or novelty score can justify abstention or routing to a supported specialist; it is not proof that price will reverse.

Adaptive conformal intervals may help monitor and adjust uncertainty coverage. They are not guaranteed trade-profit bounds, and average coverage is not conditional coverage for every selected trade or regime. Evaluate them on the actual entry-selection population as well as broad origins.

## 6. Shadow books that answer distinct questions

Implement only after contract and score parity. Share one inference service. Each book changes one mechanism first; keep the untouched champion alongside it.

| Experiment | Mechanism | Required comparison |
|---|---|---|
| Champion policy admission | Reject only supported negative expected policy-value triggers | Parent; rejection loss saved versus winner/runner profit missed; accepted coverage |
| Champion wait-for-confirmation | At a trigger, choose enter now, bounded wait, or expire using updated causal state | Parent plus equally delayed nonforecast control; missed moves and worse entry prices |
| Champion contract selector | Preserve trigger/direction; rank executable contracts by policy-value distribution | Original contract selection with identical exit and sizing rules |
| Champion continuation | At a parent exit, continue only when incremental continuation value is supported | Same-state sell-now and original parent; intervention frequency and subsequent account path |
| Champion giveback defense | Exit when held-state deterioration predicts negative continuation value | Mechanical trailing control, with matched intervention opportunities |
| Opportunity scout | Independent hazard/sequence forecasts generate entries when parent is flat | Activity-matched and momentum controls; incremental combined-account opportunity coverage |

Do not combine all six before measuring each. A gate usually reduces trade count; complementary opportunity generation is the route to recovering useful opportunities, not lowering the gate until losses return. A book that never intervenes has not tested its claimed mechanism.

## 7. Proof package and promotion rules

1. **Parity fixtures:** same contract, quote policy, label definition, score transform, cutoff, threshold and decision between research and replay. Add no-future-data truncation tests and runtime/artifact mismatch rejection.
2. **Historical discovery:** preserve current results, rerun corrected pipelines under new manifests. Explicitly distinguish fixed-artifact in-sample engineering checks from rolling-origin historical evaluation. Repeatedly consulted historical days are not pristine holdouts.
3. **Chronological evaluation:** train/choose/calibrate only on past data with mature labels; group overlapping episodes and purge boundaries where labels overlap. Keep a trial registry. Reserve genuinely new sessions for confirmation; report all tried variants and failed hypotheses.
4. **Forecast evidence:** Brier/log loss, calibration, return-quantile pinball loss and coverage/width, conditional directional discrimination, censored time-to-event quality, and support by session/expiry/premium/regime. Compare with simple baselines and use paired day-block uncertainty estimates. Fifteen days cannot establish rare-loss safety.
5. **Entry attribution:** losses avoided, winners rejected, runner profit removed, opportunities missed, delay cost, acceptance rate and forecast availability. Analyze all predeclared triggers, not just trades surviving a filter.
6. **Exit attribution:** eligible decisions, actual interventions, same-start incremental value, foregone runner profit, reentry losses and occupancy changes. Zero interventions must be reported explicitly.
7. **Account evidence:** replay baseline Conductor and baseline-plus-candidate using identical inputs and actual ownership, pending/fill, lapsed-owner, whole-lot and all-in rules. Report rupee equity, drawdown, positive/negative days, trades, overlap/displacement and missed opportunities. Never sum standalone profits or rank synthetic accounts as a substitute.
8. **Operational evidence:** current engine p50/p95/p99/max stage latency, data age, held-contract coverage, write backlog, restart consistency and inference capacity. Batch shared computations and keep fitting off the live path. Do not attach a speed claim to an idle microbenchmark alone.

No promotion solely because win rate rises, an in-sample loss disappears, or one score has a high AUC. Require a reproducible improvement relevant to the account, with uncertainty and the performance cost stated. If no model beats the parent under these tests, keep the parent and retain the negative result.

## 8. Claude's implementation order and deliverables

**First:** acknowledge/correct the report's accounting and contribution claims; deliver exact-contract binding, shared scoring pipeline, held-contract coverage and provenance enforcement. Add the focused lifecycle tests from section 4. Reconcile the ineffective runner twin with explicit eligible/intervention counters.

**Second:** rebuild champion-specific episode labels and a reproducible train/calibrate/evaluate harness. Deliver `FORECAST_SPEC.md`, artifact manifests, contract/label parity fixtures and corrected baseline tables. Preserve old results; do not overwrite evidence.

**Third:** implement coherent hazards, champion admission and held-state continuation baselines. Deliver feature-block ablations and one-mechanism shadow comparisons. Add Greeks/scenario and sequence challengers only against these controls.

**Fourth:** run a frozen forward shadow package and actual combined-account comparisons. Deliver a report that explains whether improvement came from selection, contract choice, timing, continuation or independent opportunities. If the result is inconclusive, specify the evidence still missing instead of announcing completion.

For every milestone state: implemented behavior, exact code/artifact hashes, test results, measured results, failed hypotheses, remaining limitations and next experiment. Do not describe a recorded forecast as an active gate, calibration as structural learning, or historical fitting as forward proof.

## 9. Research references and applicability limits

- [scikit-survival: competing risks](https://scikit-survival.readthedocs.io/en/latest/user_guide/competing-risks.html): cumulative incidence accounts for competing events. Use the principle to construct coherent favorable/adverse first-passage outputs; it supplies no market alpha by itself.
- [Gibbs and Candes: Conformal Inference for Online Prediction with Arbitrary Distribution Shifts](https://www.jmlr.org/beta/papers/v25/22-1218.html): a basis for adaptive uncertainty calibration. Its coverage objective is not a profitability guarantee or automatic per-trade conditional protection.
- [DeepLOB](https://arxiv.org/abs/1808.03668): a sequence-model research reference using limit-order-book data. Feasibility here depends on actual tape information and independent sessions; do not assume its results transfer to weekly Nifty option premiums.

The practical next breakthrough is to ask the right predictive question about the exact trade the system can execute, then prove that its answer improves the champion. More model names cannot compensate for mismatched contracts, targets and decision policies.
