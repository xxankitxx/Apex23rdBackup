# A predictive Conductor that learns from evidence: implementation instructions for Claude

10 November 2026, Asia/Calcutta. Read after docs/39, not instead of it. Owner request: distinguish promising champion trades from avoidable losses, forecast direction and option speed before entry, improve forecasts as evidence matures, explore prediction-driven shadows, identify live bottlenecks, and reclaim unnecessary storage.

This is an implementation and validation programme, not a claim that the current data already contains a reliable winners-only separator. Preserve all-in, buy-only weekly-option paper trading, the owner's gross accounting convention, weak-evidence abstention and opportunity capture. Do not invent a minimum trade count or acceptable loss budget. No system can establish a guarantee of zero future losses from finite tape evidence; explicitly report the observed failure rate while working to reduce it.

## 1. The vision and the present gap

The system should answer five questions before risking its paper capital:

1. What distribution of underlying moves is plausible over the next few seconds and minutes?
2. How would each eligible option respond to those moves, IV changes and elapsed time?
3. How likely is useful premium appreciation to occur before an adverse excursion, and how long might it take?
4. How reliable is this forecast in comparable, genuinely subsequent episodes?
5. Is taking this opportunity better for the actual occupied/free account than the eligible alternatives?

Today many weather fields describe the market, and rule search partitions completed trades by their outcomes. That does not make the engine a calibrated forecaster. `QuantView` already publishes drift, regime, Hawkes and premium-passage estimates, but their presence is not evidence that the probabilities rank opportunities well or match observed frequencies. Earlier docs/24 and docs/33 record failed probability-based trading experiments. Do not resurrect those with a new name and unchanged assumptions.

The advance is a closed loop: **observe → issue immutable forecast → make a declared decision → wait for the outcome → score that original forecast → update only from matured evidence → compare with the frozen baseline**. The engine must also explain why it abstains. A forecast should be inspectable before the result, not a story attached after the trade.

## 2. What the latest evidence supports

The latest saved live session inspected in this review remains 9 November; no 10-November paper-book file was found. Docs/38 provides a reproducible 12-trade champion ledger. Six winners earned ₹116,467; six losers cost ₹56,803.50. The ₹54,756 runner contributed about 91.8% of net profit. Three losses first reached roughly 8–11.5% favourable premium movement, but the quick-exit sibling also cut the largest runner substantially.

Therefore there are at least three distinct problems: entering a setup that never develops, failing to exit a profitable but weakening setup, and cutting a genuine runner too early. One binary “good/bad trade” label conflates them. Day-direction and instantaneous-breadth filters did not neatly separate the examples; both winning calls were below the opening spot price too.

Docs/39 now reports corrected research, new instrumentation and operational fixes. Recognize this work: ClosedTrade caching/amendment handling, generation-aware persistence, model readiness, position brackets at fill, input ages and per-phase timing have been implemented according to that document. Their live validation is still pending. Do not tell the owner they remain wholly unaddressed.

The new S01 threshold signal did not beat its cash control. S03 has favourable overlapping futures-signal results but still 1,031 losing signals out of 2,186; it has not established single-position option-account benefit. Predictive accuracy, a favourable average and a usable trading strategy are separate claims.

## 3. Forecast targets: direction, magnitude, speed and path

Define a small fixed horizon grid tied to actual execution latency and plausible holding periods. For example, 30/60/180/300 seconds is a research starting grid, not an optimized recommendation. Avoid generating dozens of targets before determining sample support.

### Underlying forecast

Predict signed forward-return quantiles and probabilities of upward, downward and small movement. Define the small-movement band in advance in instrument units with a documented volatility/quote-noise scaling. A direction label that treats every tiny uptick as a successful call prediction is economically meaningless.

Predict a joint forward/IV scenario distribution, or an explicitly limited approximation with residual dependence preserved. Add conditional realised movement forecasts. A direction can be correct while the option loses because the move is too slow or IV falls.

### Fixed-contract premium forecast

At each forecast origin, identify the exact expiry/strike/right and the entry convention. Preserve that contract throughout the label horizon; never substitute the new ATM strike halfway through. Produce:

- Premium-return quantiles at each horizon, with the gross first-print accounting and quote-aware diagnostic labelled separately.
- Probability of reaching each predeclared useful-profit barrier before the adverse barrier and before horizon expiry.
- Probability of neither barrier occurring by the horizon.
- Time-to-profit distribution **conditional on reaching profit**, alongside the unconditional probability of doing so. Do not report a “fast expected win” by discarding the many paths that never win.
- Conditional adverse excursion, forecast decay and probability that the opportunity remains after the measured request/fill delay.

Use a competing-event/survival formulation for target-first, adverse-first and still-open outcomes. Gaps, close-of-day and absent future quotes require explicit censoring/unobservable status. A quote gap is neither an automatic stop nor a hidden win. The per-horizon event probabilities must form a consistent distribution.

### Strategy-policy and continuation forecasts

Separately label whether a **frozen entry/exit policy** profits. Do not train “best possible exit” outcomes and call them the probability that the actual strategy wins. Retrospective MFE is a potential-opportunity label, not an executable policy.

For held positions, forecast incremental return from continuing versus a specified exit convention, accounting for current state. The continuation photograph can include already observed peak, gain duration, giveback, changing flow and remaining time. None may be copied back into entry features. Compare continuation decisions with matched-entry controls before full account replay.

## 4. Greeks as the option-response translator

Greeks describe local sensitivity, not a standalone physical forecast of direction. Delta translates forward moves, Gamma changes that sensitivity, Vega translates volatility changes and Theta describes modelled time decay. Vanna, Vomma and other higher derivatives help explain joint/scenario sensitivity and approximation error.

Use full repricing as the reference for finite scenarios, particularly near expiry. Keep forward versus spot, decimal IV versus percentage-point IV, calendar time, discounting and derivative units explicit. Compute `E[V(F_future, IV_future, time_future)]` over joint scenarios; repricing only at mean F and mean IV is generally a different quantity.

Report predicted premium gain decomposed into forward, convexity, volatility, time and residual components. Unhedged long options are not pure gamma trades. Positive gamma-versus-theta arithmetic does not itself imply a profitable purchase. OI-based dealer-sign assumptions remain assumptions; do not infer actual dealer buying/selling pressure from unsigned OI.

Benchmark the scenario translator against a direct premium-return forecast. If the Greek-based model does not improve calibration or contract choice, retain it as an explanation/diagnostic rather than a compulsory gate.

## 5. Evidence architecture and forecast record

Create a versioned shared prediction service, not one independently trained model per book. Suggested modules are design proposals: `apex/predict/{schema,features,targets,models,calibration,registry,scoring}.py`. Inspect existing interfaces before choosing names.

Each immutable forecast record should carry:

```text
forecast_id, episode_id, market_snapshot_id, sequence
issued_receive_time, feature_cutoff_time, instrument_key
model_version, training_cutoff, calibration_version, feature_schema_hash
prediction_horizons, accounting_convention, entry_delay_assumption
forward_quantiles, premium_quantiles, target_first_probabilities
time_to_profit_distribution, unobservable_or_neither_probability
freshness, readiness, support_status, uncertainty_status
decision: enter / hold / exit / abstain, reason, policy_version
```

Actual request/fill/exit timestamps and matured outcomes belong in linked later records, never edits to the original prediction. Include forecasts for a bounded, predeclared sample of eligible non-traded opportunities, blocked candidates and abstentions. Training only on filled champion trades creates selection bias and misses exactly the opportunities the owner wants captured.

Sampling must be bounded: fixed-contract eligibility, event/episode origins, periodic comparison samples and all actual decisions. Recording every possible strike/horizon on every tick is not necessary. Keep a record of the sampling policy and weights if estimating population metrics from a sample.

Group siblings sharing an underlying episode. Hundreds of almost identical book rows do not create hundreds of independent market observations. Train chronological windows with episode-aware overlap handling and no future training/calibration artifacts. Signal-side fitting on all historical dates still makes those dates discovery material, even when future returns were not used.

## 6. Models and the staged learning loop

### Stage A: simple forecasts that can be falsified

Start with empirical conditional rates using shrinkage across related states, regularized logistic models for event probabilities, and regularized/quantile return models. Compare against base rates, recent momentum, actual premium_momentum, existing passage probabilities and no-model strategy controls. Small models are intentional: the history contains few independent sessions despite many rows.

Build features around hypotheses: multi-horizon participation and its persistence; cash/futures transmission; option response relative to forward/IV changes; signal age; expiry state; and data availability. Add the remaining doc38 weather items only when their measurement is reliable. Feature count is not information content.

### Stage B: probability and speed calibration

Score direction and event forecasts using proper scores such as Brier/log loss; score quantiles using pinball loss and interval coverage/width. Publish reliability diagrams and counts by probability bin, expiry class, horizon and selected versus all eligible cases. Score time-to-event with censoring-aware methods, not only successful events.

Use chronological calibration windows and small/regularized calibration models. A recalibrated score can fix probability levels but cannot create predictive ranking from an uninformative score. A high AUC alone does not establish profitable all-in trades or accurate event probabilities.

### Stage C: controlled intraday adaptation

Maintain a mature-label queue. A 300-second target cannot update the predictor at 30 seconds because the interim path looks favourable. Distinguish a terminal first-passage outcome from an unfinished horizon return. Log every training update's eligible sample cutoff.

Use fast bounded updates for residual scale or calibration only after the relevant outcomes mature. Keep structural model refits off the live decision process and deploy immutable artifacts atomically. Every forecast retains the version that produced it. Cache keys include model version, not just time and strike.

Run fast-adapting and slow/frozen predictors side by side. Drift alarms should widen uncertainty or reduce reliance on unsupported predictions; they should not cause an uncontrolled succession of new thresholds. Preserve old regimes in evaluation, and test recovery after shocks. Improvement is assessed over subsequent windows; it is not guaranteed after every update or loss.

Adaptive conformal methods are candidates for interval calibration under changing conditions. Their coverage properties are not a per-trade no-loss guarantee and need adaptation for delayed labels, dependence and selected trades. Keep the selected-subset coverage separate from overall coverage.

### Stage D: scheduled evidence-based promotion

Freeze evaluation rules and check dates before observing results. Report all attempted models and parameter choices. Compare paired subsequent episodes/days, confidence intervals under dependence, account outcomes and compute cost. Repeatedly inspecting the same holdout and trying variants turns it into discovery data.

Separate statuses: forecast implemented, calibration acceptable on a stated window, useful discrimination, executable policy benefit, incremental account benefit, and owner objective met on the observed window. None is a promise of zero future losses. Retain a reproducible fallback model/policy and a rollback path when drift or data failure appears.

## 7. Prediction-driven shadow books

These are roles built on the shared forecast system, not claims of five new independent market mechanisms. Keep their provenance distinct from N01–N08 and S01–S06.

| Proposed shadow | Decision hypothesis | Essential control |
|---|---|---|
| P01 `forecast_select` | On incumbent triggers, admit only where frozen calibrated premium-path evidence supports the trade | Same entries and exits without the forecast gate; record rejected winners |
| P02 `forecast_clock` | Independently enter a supported option opportunity whose predicted useful move should arrive before its opportunity decays | Same independent opportunity sampler with simple momentum/empirical timing |
| P03 `forecast_runner` | Identify persistence that justifies holding a potential runner | Matched entries, original trail, fixed-clock and simple persistence controls |
| P04 `forecast_exit` | Exit when remaining continuation value deteriorates after an observed gain or thesis failure | Matched-entry 9y/9e/9t exits, with exact runner opportunity cost |
| P05 `adaptive_calibration` | Improve P01/P02 reliability using only matured intraday labels | Identical frozen model/calibrator and identical opportunity stream |

P01 is a filter twin, P03/P04 are continuation experiments, and P05 tests learning dynamics. Only P02 is an independent opportunity generator, and its economic source must be identified. Do not inflate the book count by pretending all five are unrelated sources of edge.

Specify rearming, maximum inference age, missing inputs, entry/exit clocks, restart state, signal-to-fill opportunity decay, and deterministic fallback. Thresholds and horizons must be frozen before evaluation. Do not hard-code a confidence level merely because it sounds safe: calibration, expected movement and support matter.

First evaluate forecasts off-policy, then shadow policies, then the complete occupied account. Compare baseline, candidate alone, baseline+candidate and leave-one-out. Reconcile added, displaced and shared trades and sizing effects as docs/35 demonstrated. A profitable new book can lower the Conductor's profit by consuming time needed for a better opportunity.

Keep approved mirror-Conductor semantics unchanged in the baseline. Any predicted opportunity-cost admission policy is a separately named account experiment. Forecasts must not choose future winners with hindsight or silently pre-empt the current owner.

## 8. Performance investigation: evidence versus suspects

It is not possible to certify that *every* live bottleneck has been identified from source inspection and one older replay. The following inventory separates observed evidence, code costs and required measurements. Do not represent the profiler's books phase as proof that a particular unmeasured function consumed all its time.

### Confirmed measurements and current environment

Docs/39's named replay used **v4/gen2 VERSION 2**, not the latest v5/gen2 VERSION 3/gen3/99-book configuration. It reports 244,670 steps, 29.5 ms mean, four over one second, and 310 over 300 ms. Cached asynchronous save submission was measured near 12 ms median; full first serialization was hundreds of milliseconds. These are offline measurements from Claude's report, not a new live performance certification.

During this review, process inspection found multiple `apex.replay_batch` workers, several fast replays, cache builders and other research scripts running simultaneously. Basic inspection commands were unusually delayed. This establishes competing workloads, not their precise CPU utilization or their role in the 9-November incident. Do not kill someone else's work. Record per-process CPU deltas, memory pressure, disk latency/queue and task identity; isolate live trading from bulk replay/training jobs using an explicit scheduler or separate resources.

### Hot-path cost inventory

| Path | Evidence / concern | Required improvement or measurement |
|---|---|---|
| `run_books`, weather photo construction | Near-simultaneous entries repeatedly invoke photo work; docs/39 attributes remaining spikes to books but photo itself was not separately timed | Measure base, contract, direction, book-overlay and serialization timings separately |
| `weather4._p_books` | For each photograph, walks other books and their closed trades, then sorts same-side records | Maintain incremental aggregate indexes and subtract self; avoid repeated whole-history traversal |
| Trigger-density histories | Repeated filtering and set construction over fire history | Bounded rolling event indexes with correct episode/time semantics |
| `weather.photo` v2/v3/v4/v5 | Reconstructs large dictionaries and many derived values for each trigger | Share immutable base and contract features; retain lightweight per-book overlays |
| Option IV/Greeks and QuantView | Premium passage and higher Greeks run in the quant update; SVI fitting is synchronous every 60 seconds | Profile each block; bound iteration/work; background calibrations with stamped cutoffs and expiry |
| Persistence | Serialization fix exists, but new trades/hold snapshots, first save and final save still cost work | Measure cold/warm/update cases under latest schema; keep durable generation/error telemetry |
| Logging and decision/event files | `LOG.flush()` and event-file writes occur in engine code; root SDK log is large | Time writes, rotate verbose logs, bounded asynchronous observer writer; retain critical audit events |
| UI publication | `publish()` runs from `tick` on a 0.25-second cadence | Measure serialization and publication separately; send snapshots/deltas off critical decisions where safe |
| Warm-state checkpoint | `_save_warm()` runs from live `tick`, normally every 30 seconds | Time snapshot copy, serialization and disk; capture immutable state then persist off-loop if correct |
| Missed-signal recorder | Invoked for each book and advanced centrally | Bound active counterfactuals and expiry work; profile busy moments, not only idle seconds |
| Histories/arrays | Repeated windows, copies, allocation and sorting may drive burst latency | Incremental rolling stats where numerically equivalent; track allocation/GC separately |
| All books/exits | 99 books evaluated in shared processing | Share expensive observations, preserve independent strategy state and deterministic event order |
| External contention | Many concurrent research jobs observed | Separate live resource budget; benchmark under both isolated and representative contention |

### Correct caching is more subtle than “one photo per second”

Book-specific fields include current positions, completed trades and firing agreement. Their values can change within the same step as earlier books are evaluated. Reusing the first book's complete photograph for every other book silently changes semantics and may leak/erase same-step context.

Use market snapshot sequence plus contract, direction, schema/model versions for market-only caches; book-state sequence for overlays. Preserve the original order-dependent agreement definition unless creating a separately versioned simultaneous-vote experiment. Key freshness and as-of times correctly when multiple updates arrive within one second. Add semantic-equivalence tests on identical input sequences before accepting speedups.

### Performance acceptance package

Instrument receive→parse→state update→feature ready→forecast ready→decision→request→fill, and separate CPU service time from data age and scheduling delay. Report p50/p95/p99/max and per-stage cumulative time/call counts; attribute child timers without double-counting parents. Include publication/checkpoint work that happens after `step` so the measured critical cycle is complete.

Use a short representative burst fixture first: ten-plus simultaneous entries, full end-of-day histories, continuation photos, pending requests, writer backlog, unavailable model and reconnect. Then benchmark the full latest configuration under the agreed resource budget. This review does not start another full replay while the machine already runs many jobs.

Derive deadlines from the existing 100-ms loop ambition and three-second fill policy rather than treating “under three seconds” as fast enough. Exits and pending-fill checks need timely scheduling; expensive observers must not block them. If using background workers, immutable input cutoffs and bounded queues prevent future-state leakage and unlimited backlog. Coalesce replaceable display snapshots; never silently discard trades or required audit records.

No runtime model fitting, unbounded candidate search, disk compression or large directory cleanup in the decision process. Offline richness and online speed are compatible when the live artifact is small and inference work is bounded.

## 9. Storage audit and cleanup policy

A read-only inventory at review time found approximately **4.5665 GiB** under `D:\ApexOptions`:

| Area | GiB | Treatment |
|---|---:|---|
| Original market tapes (`data/ticks`) | 3.1636 | Preserve: irrecoverable training/replay evidence |
| Replay runs and reports | 0.7560 | Preserve referenced runs; manifest before pruning redundant generated outputs |
| Research artifacts | 0.2118 | Preserve fitted artifacts, forecasts and referenced datasets; assess rebuildable caches individually |
| Root SDK logs | 0.1832 | Rotate/archive closed logs after checking active writers; do not delete blindly |
| Git objects | 0.1333 | Preserve repository history; no destructive history cleanup |
| Saved paper records | 0.0825 | Preserve accounting, decisions and weather evidence |

The D drive had approximately **20.0 GiB free** at inspection, across the whole drive. That is not all space controlled by this repository. Root `logs/apiLogs.log` alone is 196,587,060 bytes, last modified 9 November; it is a concrete archive/rotation candidate, not proof it is unnecessary. Other processes may use the SDK logging path.

Inventory and cleanup evidence live under `data/replay/batch/codex_predictive_review_2026-11-10/`. `research/disk_inventory_codex.py` inventories without following links/junctions or deleting files. The completed cache cleanup removed **153 untracked regenerable files, 4,843,972 bytes (4.62 MiB)** from `__pycache__`/`.pytest_cache`, with canonical workspace checks and a deletion manifest. Read `cleanup_manifest.json` for the exact paths; source tapes, trade records, research conclusions, active outputs and Git history were excluded. A separate guarded SDK-log archive uses `research/archive_closed_sdk_log.ps1`; its observed outcome is recorded in `log_archive_manifest.json` when run.

**Completed log archive:** exclusive access against writers was acquired; the 196,587,060-byte log was compressed to `logs/apiLogs_2026-11-09_codex_archive.log.gz` (42,066,061 bytes). Full decompression SHA-256 matched the original before removal. This reclaimed **154,520,999 bytes**. Combined with caches, actual reclaimed space is **159,364,971 bytes, approximately 151.98 MiB**. This was lossless archival of evidence, not deletion of its contents. The SDK can create a new current `apiLogs.log` on its next run.

Larger savings should come from **avoiding duplicated representations**, not throwing away evidence: shared immutable weather snapshots, event logs plus periodic checkpoints, compact columnar closed research partitions, and explicit retention manifests for derived datasets. Do not adopt a new storage backend before measuring write latency and verifying replay/export compatibility.

For a closed log archive: confirm no writer, hash the original, compress to a new path, decompress and verify byte/hash equality, atomically commit the archive manifest, then remove the original only if it has not changed. For a rebuildable derived file: record its input hashes, code/artifact version and regeneration command first; preserve the outputs cited by reports. Never delete a raw tape because a replay result exists, and never delete an unfamiliar `.tmp` or scratchpad while another run may own it.

Introduce a registry of each run's producer, state (active/complete/failed), inputs, outputs, reference count and retention class. Cleanup should consume that registry and produce a reviewable dry-run list before deleting large artifacts. An automatic routine may remove explicitly unreferenced regenerable caches; originals and evidence need an archive/review policy. User authorization to clean unnecessary files is not evidence that unclassified research data is unnecessary.

## 10. Concrete Claude milestones

**M1: finish measuring the current system.** Reconcile docs/39 with current code, latest schema and active jobs. Deliver inclusive stage timings, a burst fixture, photo-cache dependency design and storage/producer manifest. Confirm what was actually fixed and what remains only hypothesized. Do not repeat already completed fixes as new work.

**M2: immutable forecast ledger and outcome queue.** Define schema, contract eligibility, fixed target policies, market-clock alignment and censoring. Deliver historical origin reconstruction and truncation checks, matured-only updates, snapshot references, deterministic restart and forecasts for abstentions. No capital-policy change yet.

**M3: baseline direction/premium/time forecasts.** Build parsimonious models and calibration with dated artifacts. Deliver proper scores, reliability, quantile width/coverage, time-to-event accuracy, model support and simple controls across chronological windows. Demonstrate whether Greeks/scenarios add anything beyond direct premium forecasting.

**M4: prediction shadows.** Implement P01 and P04 first to test discrimination and continuation on known entries; P02 then tests independent opportunity capture; P03/P05 follow with sufficient path and matured-label evidence. Record rejected winners and lost runners. Run frozen and adaptive versions together without changing the main account.

**M5: Conductor contribution and live readiness.** Complete event-level pool comparisons with pending occupancy, execution delay, model outages, fallback exits and all-in recalculation. Produce latency/staleness/capital attribution together. A strategy that only wins under an impossible fill or blocks more valuable opportunities is not an improvement.

Every milestone must include executable tests, actual measured results, known limits, failed hypotheses and exact artifact references. Build ambition into the breadth of questions and quality of evidence, not increasingly complicated scores. The desired outcome is an engine that makes useful, timely, calibrated forecasts, knows when evidence is weak, and can demonstrate whether each new capability improved the account.

## Research references

[Gibbs and Candès, Adaptive Conformal Inference Under Distribution Shift](https://arxiv.org/abs/2106.00170) and [Conformal Inference for Online Prediction with Arbitrary Distribution Shifts](https://www.jmlr.org/papers/volume25/22-1218/22-1218.pdf) motivate adaptive uncertainty calibration. Their coverage results are not a guarantee that a selected trade wins. Delayed outcome handling and trade-selection effects must be evaluated for this application.

[A Competing Risk Analysis of Executions and Cancellations in a Limit Order Market](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=934785) illustrates competing-event/time-to-event modelling in markets. Target-versus-adverse-barrier modelling proposed here is a different application requiring its own validation; no published execution result establishes an option-trading edge.
