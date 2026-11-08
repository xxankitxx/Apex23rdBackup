# ApexOptions improvement instructions for Claude

Prepared 8 November 2026. This document is a proposed engineering and research handoff requested by the owner. Proposed additions below require evaluation against the existing official specification. They do not supersede dated owner decisions or constitute evidence of trading performance.

Read the companion [advanced-model and shadow-book plan](33_ADVANCED_MODELS_AND_SHADOW_BOOK_PLAN.md) for the current model-use audit, researched methods, twelve proposed experiments, implementation dependencies, and staged pilot. It incorporates the owner's all-in, gross-paper, opportunity-coverage requirements and identifies a model-training chronology issue to resolve before model-backed decisions.

## 1. The owner's objective and the acceptance problem

The owner wants a system that avoids losses, stays flat when appropriate, finds a good number of trades, combines the strengths of several trading styles and advanced mathematical and options models, and stays very fast throughout its operation.

Treat those requirements seriously and make each measurable. A promise of zero future trading losses cannot be established by a finite replay, a mathematical pricing model, or a period of profitable paper trading. A flat account can avoid trading losses while failing the frequency objective. A forced minimum trade count can require entering when no qualified opportunity exists. Surface this conflict before claiming compliance.

The owner clarified the following requirements on 8 November 2026. These answers replace the earlier requests for minimum trades and maximum loss. Carry them into implementation and evaluation.

| Requirement | Owner instruction or remaining measurement |
|---|---|
| Avoiding loss | Aim for no losing trades and no losing days. Every loss requires investigation and a recurrence review. |
| Allowed abstention | Stay flat when evidence is weak and buying an option offers insufficient movement, including sideways conditions. |
| Frequency | Capture as many qualified profitable opportunities as possible. The owner explicitly rejects an invented minimum trade count. |
| Loss tolerance | The owner explicitly rejects defining an acceptable maximum loss. Do not introduce a daily loss allowance or budget. Preserve existing exit behavior pending tested changes. |
| Confidence | Required uncertainty bounds, minimum independent sessions, and forward observation period. |
| Costs and capital | All-in on every entry. Evaluate this paper system on gross results. Brokerage and taxes are excluded by instruction. Preserve the documented paper-fill convention and honest timing. |
| Speed | Hardware, instruments and book count, maximum processing age, and acceptable p95/p99 latency. |

Retain the official statistical promotion gates as evidence requirements. Treat historical numerical frequency goals as comparisons rather than a newly imposed owner quota. Report losing trades and days explicitly even when a candidate passes the older profitability gates. Passing those gates alone does not establish the owner's zero-loss objective. No finite test establishes guaranteed zero future losses.

Translate “never make the same mistake again” into an auditable loss-review process. A distinguishable, repeatable defect can be prevented through a correction. Two losses with similar outcomes may have different causes, and apparently identical observable conditions may have different future outcomes. Preserve that distinction when deciding what can be prevented.

## 2. Establish the current baseline

Read the repository and its current working changes before implementing. Preserve unrelated work. The repository was changing during this review, including weather v3, per-book cards, and clock norms. File presence and documentation claims require verification against the actual source and outputs.

Read these documents in order, resolving later dated owner decisions explicitly.

1. `docs/28_APEX_CONDUCTOR_PLAN.md`, especially the 8 November replacement of section 11.
2. `docs/27_PRE_TRADE_FACTORS.md`, the complete 68-item catalogue.
3. `docs/29_MISSED_SIGNAL_RECORDER.md` and `docs/31_RULE_REGISTER.md`.
4. `docs/30_BOOK_GUIDE.md` and `docs/20_C20_9X_STRATEGY_SPEC.md`.
5. `docs/24_REVIEWS_QUANT_LAYER_5NOV.md`, `docs/26_EVENT_STUDY_6NOV.md`, and the current decision log.

Trace the following implementation paths.

| Area | Main source |
|---|---|
| Process supervision and isolation | `run_apex.py` |
| Live input, packet parsing, recording | `apex/feed_breeze.py`, `apex/feed_core.py` |
| Shared state | `apex/table.py` |
| Engine decisions and publishing | `apex/engine_main.py` |
| Paper fills and state persistence | `apex/engine/paper.py` |
| Active council strategy | `apex/engine/council/c20_9x.py` and its adapter |
| Trigger weather and missed signals | `apex/engine/weather.py`, `apex/engine/missed.py` |
| Research pipeline | `apex/conductor/` |
| Registered restrictions | `apex/engine/rules.py`, `apex/rules/register.json` |
| Greek calculations | `apex/greeks.py`, `apex/quant/greeks_hi.py` |
| Gamma map and model views | `apex/engine/gex.py`, `apex/engine/quantview.py` |
| Replay and acceptance | `apex/replay_batch.py`, `apex/replay_compare.py`, `apex/acceptance.py` |

The system uses buy-only Nifty weekly options and paper execution. The configured incumbent is c20_9x. Each book starts with ₹1,00,000 daily and compounds within the day. The Conductor will share one account and one position. Preserve the all-in sizing decision unless the owner explicitly changes it. Learning is currently record-only through `LEARN_DECIDE = False`.

Do not treat the README's original automatic learning description as the current authority. The existing docs also contain stale counts and conflicting summaries. Produce a concise discrepancy list with the applicable dated decision and source behavior.

## 3. Use the existing tapes correctly

Recorded sessions already exist in `data/ticks/`, including October through 6 November and multiple parts for restarted sessions. Inventory actual coverage, timestamps, packet types, gaps, and instrument changes. Establish which files are complete live sessions, partial sessions, or synthetic recordings before reporting a sample size.

The 68 items are groups of derived weather measurements. A raw tape does not necessarily contain a fully materialized weather photograph at every moment. Replay reconstructs available engine state and captures the photograph at every actual or qualifying missed trigger. Some values depend on the chosen contract, direction, model warm-up, or earlier sessions. Prove reconstructability per field and mark unavailable values explicitly.

Create a field lineage table with item ID, field, units, source packets, arrival timestamp, update cadence, warm-up, missing-value behavior, and all consumer locations. Include every item. Missing values must remain distinguishable from zero. The documents quote varying field totals, so compute the actual count from code and report it.

Replay sessions chronologically with all tape parts, declared starting state, prior levels, and earlier-day normalizers. A date's clock norms may use only earlier dates. A factor calculated at a trigger may use only information received by that trigger, even when an exchange timestamp is older.

Pin the code, configuration, dependencies, seed state, tape hashes, book order, and random seeds in the manifest. Use isolated directories and shared-memory names. Recheck existing running jobs before starting another expensive batch.

## 4. Preserve the Conductor's research design

Build one diary per book with trigger weather, fill weather, outcome, holding duration, favorable and adverse excursions, exit reason, and data-quality flags. Assign families per row from entry pattern and day type. Confirm the family loss-label threshold is derived only from its allowed discovery data and frozen for forward evaluation.

Separate losses that never developed favorably from trades that gained and subsequently gave back their profit. Route the latter into exit research. Preserve the recorder's deduplication and counterfactual weighting rules. Counterfactuals contribute to discovery and remain excluded from rule promotion scores.

Search every one of the 68 items for every book as the owner directed. Retain the family representative search for register proposals and dependence accounting. Do not interpret dozens of variants firing on the same underlying move as dozens of independent observations.

Freeze every proposed condition with a date, discovery sessions, formula, threshold, applicable family, and version. Start with one condition. Two-condition combinations require the documented individual passes and sufficient combined observations. Enforce the failed-rule near-duplicate block.

Restricted books must actually execute their own state machines. Removing a rejected trade can free capital for later signals, change cooldowns, and change subsequent positions. Filtering a historical trade table cannot reproduce that behavior.

Retain the official promotion standard, including both windows, luck margins, absolute positive returns, removal of the best trade and day, preservation of major winners, worst-day protection, and minimum observations. The first rule window requires both 30 restricted trades and 15 trading days, plus day-type coverage where applicable. First-window qualification earns low priority. Second-window qualification earns full standing. Resolve any disagreement between the rollout prose and worked example before implementing variant eligibility.

Use only sessions after the freeze date for proof. A rule discovered by examining all available tapes has used those tapes. Historical reconstruction does not turn them into unseen evidence. Earlier frozen rules can use later recorded sessions where eligibility and provenance are established.

## 5. Strengthen the statistical evidence

Audit the existing implementation before adding statistical machinery. Preserve the official standard and report any proposed stricter test as an additional requirement needing agreement.

The search spans books, fields, thresholds, directions, and potential combinations. Its null procedure should repeat the complete selection process, recording the best result found under each null run. Shuffling labels only after selecting the winning threshold understates selection bias. Report the number of trials and effective family dependence.

Use whole-session or appropriate clustered resampling where trades share a market move. Avoid random train/test splitting across overlapping triggers. Purge overlaps at discovery and test boundaries when outcome windows cross them. Keep all normalization, representative selection, threshold selection, and hyperparameter fitting inside the permitted discovery interval.

The existing restricted/free membership comparison is an approximate null because restricted paths can contain different trades. Retain the specified comparison, but examine paired daily return differences as a robustness check and disclose disagreements. Do not select whichever test gives the favorable verdict.

Inspect the mathematical assumptions of the betting e-value implementation before asserting validity under indefinite monitoring. Verify scaling, bounds or tail assumptions, predictability of the bet, and the daily observation process. Track all scheduled looks and changes to the rule. Preserve the documented switch-off threshold of 20 unless formally revised.

Report uncertainty with the results. As an illustration, zero failures in n independent observations gives an approximate 95% upper failure-probability bound of 3/n. Correlated trades provide less information than independent observations. Never present a zero-loss sample as proof of zero future loss.

## 6. Improve the use of option Greeks

Delta, Gamma, and Theta already affect strategy behavior. Vanna, Charm, and higher Greeks are calculated and captured in weather. The current gamma map assumes positive call inventory and negative put inventory for dealers, uses nearest-week OI, and falls back to ATM IV outside observed strike coverage. These assumptions must accompany any interpretation.

Open interest does not identify signed dealer inventory. Short-put delta hedging generally requires selling more underlying during a decline. A long OTM call losing delta through time generally requires buying back part of its short hedge. Do not copy reversed hedge signs from commentary or articles.

For a modeled dealer portfolio with signed inventory q, express the local hedge change as minus the portfolio delta change. Gamma times the forward change, Vanna times the volatility change, and Charm times elapsed time contribute under consistent units. State which variables are held fixed and which expiry and inventory assumptions apply. A single contract's Vanna does not determine aggregate dealer demand.

First verify analytic Greeks against finite differences across strikes, expiries, volatility levels, and both option rights. Verify per-volatility-point and per-calendar-minute conversions, the IV solver's time floor, the true contract clock, and forward consistency. Exercise near-expiry and stale-quote cases explicitly.

### 6.1 Premium attribution

Reuse exact repricing to explain observed premium movement through forward movement, IV change, and elapsed time. Choose and document an order-independent allocation or a fixed decomposition order, with interaction effects clearly accounted for. Preserve the residual and quote quality.

IV inferred from the same observed premium can mechanically explain that premium. This is an accounting decomposition. Any predictive exit feature must use only values available before the proposed exit and demonstrate incremental forward value.

Study giveback trades first. Identify whether repeated givebacks follow an underlying reversal, IV contraction, or time decay during a stall. Freeze a small set of exit candidates and evaluate them against existing exits, including their effect on the largest winners and on subsequent entries.

### 6.2 Gamma walls and flips

Audit the nearby-flip exception in `GexMap.advise`. Store the modeled sign on both sides of a crossing and verify the destination regime. Audit refresh behavior because the current cache key depends on chain version and rounded forward while IV and time can change independently. Benchmark any refresh adjustment.

Run a tape study of first encounters with fresh gamma walls. Compare with ordinary OI concentrations, recent price levels, and matched arbitrary levels. Match or stratify on distance, approach speed, time of day, and expiry status. Measure reversal, continuation, and option giveback over prespecified horizons. Cluster repeated contacts with the same level and session.

Test wall location alone, observed reaction alone, and their combination. Include coverage, age of OI, IV fallback share, and sensitivity to assumed dealer signs. A modeled wall should earn an incremental contribution beyond the simpler comparison.

### 6.3 Vanna and Charm scenarios

Only after the data and convention checks, evaluate chain-level scenarios using explicitly signed hypothetical inventories. Show sensitivity to opposite inventory assumptions, skew shifts, and expiry inclusion. Keep scenario-derived fields in research until dated rules pass the same forward standard. Avoid claiming measured dealer demand from OI alone.

## 7. Combine styles through actual account behavior

Implement the pool as eligible book-plus-rule pairs. Its history must be reproducible as of each date. Start empty, admit qualified rules, and retain the official priority order of full standing, test-day return per trade, then manifest book order.

One account gets the first eligible trigger while flat. Specify pending-entry ownership, rejected fills, competing triggers, cooldowns, partial operational failures, and restarts. A failed or timed-out entry must release ownership deterministically. Persist the chosen source strategy, frozen rule version, trigger context, and complete exit state.

Protected phases require an explicit calendar or clock condition and a historically available estimate of holding duration. Estimate the 75th-percentile hold only from allowed prior observations. Define behavior when that estimate is unavailable. Never use the completed future trade to decide whether it would collide.

Measure occupied time, rejected competing opportunities, idle time with no eligible signals, and idle time caused by operations. Attribute the Conductor's gains and losses to family and phase. Test whether added families improve the actual shared account after collisions. Standalone profitable books can crowd out better opportunities.

Trial opposite-direction switching separately using the future holding outcome only as a research label. The switching decision itself must use contemporaneous data. Retain the required choppy/trending evaluation. This paper study uses gross outcomes under the owner's clarified instruction, with brokerage and taxes excluded.

## 8. Execution, abstention, and loss control

Specify entry permission separately from exit management. An entry pause must leave existing positions under active management whenever executable quotes exist. Test reconnects, stale chains, frozen trade prices, stale depth, invalid IV, late starts, registry changes, and process restarts.

Use gross paper outcomes, with brokerage and taxes excluded. Verify the existing fill convention, quote freshness, trigger-to-fill ordering, and recorded delays. Retain bid/ask and depth as diagnostic evidence. Any proposed change to the fill convention must be separately versioned so comparisons retain the same accounting basis.

Evaluate abstention and exit rules as dated candidates. Measure avoided losses, missed winners, idle sessions, and resulting frequency. Follow the owner's all-in rule without adding sizing schemes or a daily loss budget. A sideways label should be tested against the available movement in the candidate option and the strategy's horizon. Some short opportunities can exist inside a broadly sideways session, while a directional index move can still produce a poor option purchase.

The Conductor may abstain because the pool is empty, no rule qualifies, data are unreliable, capital is occupied, or an approved account control is active. Record the exact reason and make it visible. Assess frequency over all market days as well as eligible days to prevent selective reporting.

### 8.1 Required review of every loss

Create a durable loss case with trade ID, source book and rule version, trigger weather, fill history, position path, exit state, and data-quality evidence. Reconstruct exactly what was available before entry and at each relevant exit decision.

Classify the supported cause as an implementation defect, invalid or stale input, execution-model issue, entry condition, exit behavior, collision with another opportunity, or unresolved market outcome. Allow multiple causes and explicit uncertainty. Do not manufacture a causal explanation simply because a trade lost.

For a verified software defect, reproduce it, add a focused regression test, correct it, and verify affected callers. For a proposed trading correction, define a condition recognizable before the decision, register it with a freeze date, replay its complete account path, and forward-test it. Evaluate all matching winners as well as losses. A rule that memorizes the losing date or excludes a losing trade using its future path fails the review.

Maintain a recurrence register containing the causal signature, correction, supporting evidence, affected versions, and future matched cases. Track recurrence counts, avoided losses, and good opportunities rejected by each correction. Mark a cause resolved only to the extent demonstrated. Continue logging unresolved losses transparently.

### 8.2 Opportunity coverage without a trade quota

Use the missed-signal machinery to account for eligible opportunities lost to occupancy, restrictions, data quality, pending fills, and priority. Group duplicate triggers from the same market episode to avoid inflating opportunity counts. Report coverage across all sessions and by family, expiry status, and phase.

Use future price paths only to label research outcomes. Define horizons and meaningful movement consistently with the strategy being evaluated and freeze those definitions before comparison. Report sensitivity to those definitions. An observed profitable excursion is an upper-bound opportunity diagnostic, since the ideal entry and exit were unknown at the time.

Compare each change on gross results, losing trades and days, opportunity coverage, idle time, and speed together. Explicitly show whether fewer losses came from excluding good opportunities. Seek additional qualified trades by combining complementary families and improving account occupancy. Any remaining trade-off goes back to the owner with concrete matched examples and uncertainty.

## 9. Make speed measurable

Benchmark the current system on the owner's hardware before changing the architecture. The configured engine cadence is 100 ms. The chain poll interval is 90 seconds. These are different freshness limits and must be reported separately.

Measure packet-receipt-to-table time, packet-to-decision age, engine step duration, scheduling backlog, Greek/model computation, state serialization, dashboard delivery, persistence, memory use, and replay throughput. Report p50, p95, p99, maximum, and missed deadlines on quiet and busy sessions with the full intended book count.

Agree numerical latency budgets before claiming speed compliance. Keep display throttling separate from decision timing. Reuse per-step shared calculations, precompute static values, and invalidate caches on every input that materially changes a result. Evaluate all 68 weather items at required triggers without repeating identical work across books.

Keep offline search and resampling outside the live decision path. Preserve determinism and identical outputs when optimizing. Use profiling evidence to select work. Any parallel computation needs a deterministic merge and explicit ownership of shared state. A faster replay that changes trade order fails acceptance.

Run endurance and fault tests with recording, dashboard clients, restricted books, and persistence enabled. Bound queues and expose overload. An average engine-step time below 100 ms does not establish acceptable tail latency.

## 10. Ordered implementation and release gates

1. **Baseline and contract.** Inventory source, tapes, running jobs, current variants, uncommitted work, and unresolved owner decisions. Produce a benchmark and reproducible baseline.
2. **Data and replay proof.** Establish field lineage, missingness, arrival-time leakage tests, recorder neutrality on busy and quiet full tapes, deterministic double replay, and anchors against live paper records.
3. **Research completion.** Produce all-book, all-item cards, frozen diaries, controls, full-search null results, and a register with explicit discovery/test boundaries.
4. **Account selector.** Implement deterministic pool admission, ordering, pending fills, exits, persistence, protected phases, and date-correct replay.
5. **Focused improvements.** Evaluate premium attribution, gamma-map corrections, wall studies, and a small registered set of exits and abstention rules. Give each change an independent comparison before combining it.
6. **Combined forward proof.** Apply the official Conductor comparison against c20_9x, including two 30-trading-day windows and a restart after material pool or priority changes. Separately report progress against no losing trades, no losing days, opportunity coverage, and repeat-failure prevention. Impose no invented frequency quota or loss allowance.
7. **Operational qualification.** Complete tail-latency, overload, restart, stale-data, and execution-sensitivity checks. Run the shadow with dated release criteria.

The official plan batches engine replays at the Conductor build and requires one tape for sign-off before the full replay. Check whether a later owner instruction has changed this sequencing. Follow the currently authorized gate and reuse completed, verified work.

## 11. Required evidence package

Deliver a compact implementation report and machine-readable supporting artifacts containing the following.

- Requirement matrix with target, measurement, result, uncertainty, and pass/fail/unresolved status.
- Source/configuration/tape manifest, actual coverage, dependencies, starting state, and reproduction commands.
- All 68 items mapped to fields and missingness, with leakage and observer test results.
- Per-book cards and family proposals, discovery boundaries, complete attempt history, and control-run outcomes.
- Restricted/free and Conductor/incumbent comparisons on the same gross paper accounting basis, excluding brokerage and taxes.
- Best-trade and best-day removal, major-winner capture, worst day, drawdown, losing-day rate, consecutive losses, trade frequency, and idle-time reasons.
- Pool composition through time, collisions, occupancy, frozen priorities, and switching status.
- Latency distributions and correctness comparisons before and after optimization.
- Explicit unresolved requirements and the additional evidence needed for each.

Use the words proven, observed, estimated, and assumed carefully. Distinguish deterministic software properties from statistical performance estimates. Report failed candidates and adverse results alongside successes.

## 12. Immediate instructions to Claude

Begin with the baseline and requirement matrix. Read the latest source and dated owner decisions. Verify current unit-test results rather than relying on earlier conversational claims. Complete existing replay gates before interpreting search output as evidence. Bring the owner concrete comparisons and a recommended next candidate with its expected benefit, implementation cost, and failure criteria.

The central deliverable is a reproducible account-level system whose measured behavior can be checked against the owner's agreed requirements, with a clear statement of the limits of the available evidence.
