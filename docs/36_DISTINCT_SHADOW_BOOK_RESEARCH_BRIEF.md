# Claude: build a new generation of independent shadow books

Owner-requested handoff, 9 November 2026. Read together with docs/33 and docs/35. This document proposes research and implementation work; none of these strategies is implemented or demonstrated profitable by this handoff.

## The correction to the earlier plan

Document 33 already proposed twelve experiments. Many are useful but remain modifications to familiar breakout/pullback entries, strike selection, entry filters, or exits. The owner now explicitly requests strategies with substantially different sources of opportunity. Do not fulfill this request by cloning c20, t28 or edge and adding another Greek threshold.

Build independent candidate generators with explicit market mechanisms, causal entry/exit state machines, realistic observation requirements, and full Conductor attribution. Sophisticated mathematics must change a decision in a demonstrable way. Mathematical terminology is not a source of edge.

Maintain the owner's all-in, one-long-option-at-a-time, buy-only Nifty weekly paper-account rules and gross accounting. No invented minimum trade quota or acceptable daily loss budget. Keep weak-evidence abstention. A range-bound index can still offer profitable short directional or volatility opportunities; flat is a decision about the option opportunity, not merely a sideways chart label. Report every loss and losing day. Neither this proposal nor a perfect historical subset guarantees zero future losses.

## First deliverable: prove novelty and feasibility

The inventory is changing: inspect current config, council, `apex/engine/ideas`, weather4, existing quant models and docs before implementing. The old 72-book guide is not a current exhaustive inventory.

For each proposal below, produce a nearest-existing-strategy comparison: source of edge, trigger, state variables, instrument selection, exit, reset, expected horizon and raw-feed dependencies. Explicitly identify overlap with doc33. If an existing book already implements the same mechanism, mark this proposal a duplicate and improve that experiment instead of adding another name.

Prepare a data matrix from actual tape schemas and sampled sessions: field, instrument coverage, exchange/receive timestamps, cadence, gaps, units, synchronization and retention. Trigger photographs alone are insufficient for most of these path-based ideas. Snapshot depth does not reveal individual order replenishment or cancellations reliably; inferred events must retain their proxy label. Do not backfill missing historical data with later observations.

Each book must discover entries independently of incumbent triggers. A model that only approves/rejects an existing book is a useful companion experiment, but does not count toward this new-book deliverable.

## N01 — Liquidity absorption and release

**Hypothesis:** persistent directional pressure can fail to move price while liquidity absorbs it; a subsequent change in that response can produce a tradeable release or reversal. The signal is the changing price response to pressure, not a range breakout.

**Model:** estimate a causal expected response `dF_hat = beta * flow / effective_depth`, using earlier observations only. Track pressure accumulation, actual response, residual, depth recovery, and uncertainty. Use a small sequential state model: neutral → absorption candidate → confirmed absorption → release/reversal → reset. Compare simple robust regression with a switching state-space version. Separate selling-pressure absorption from buying-pressure absorption.

**Entry:** after sustained selling pressure with unusually small downside response, require evidence that the absorbing side survives and price response turns upward; buy CE. Mirror for PE. A same-direction release is a separately frozen hypothesis with separate results, not a post-outcome direction choice. Require an executable option quote and movement beyond quote uncertainty.

**Exit:** absorption thesis fails, opposing pressure regains impact, the response normalizes, or the existing applicable clock/fallback exits. Reset only after pressure state clears, so repeated snapshots are not new opportunities.

**Data:** futures/underlying price, signed-flow observations or explicitly labelled proxies, bid/ask depth and timestamps. Full order events are not assumed available.

**Novelty/control:** unlike first-touch fades or failed-break reversals, no pre-existing chart level is required. Compare against the same price confirmation alone and a simple flow-imbalance rule. Reject if gains require hindsight cancellation labels, stale quotes, or repeat existing fade entries with no incremental opportunity.

## N02 — Transient-impact relaxation

**Hypothesis:** some price displacement reflects temporary flow pressure that decays after the pressure stops; other displacement reflects persistent repricing. Trade only a measured distinction between those cases.

**Model:** use a small propagator approximation, e.g. `impact_t = sum_j a_j z_j,t`, with `z_j,t = rho_j*z_j,t-1 + signed_flow_t`. Fit decay coefficients on prior sessions and estimate a separate slowly moving reference component. Residual uncertainty must include model error. This is a forecasting model, not a causal decomposition proved from observational data.

**Entry:** a temporary upward displacement is still present, new buy pressure has ceased, and confirmed decay implies sufficient downside premium opportunity: buy PE. Mirror after a downward displacement. Abstain if permanent-change diagnostics dominate or renewed flow supports continuation.

**Exit:** predicted displacement closes, impact begins rebuilding, permanent-change evidence invalidates the hypothesis, or horizon/clock exit. One event owns one relaxation episode.

**Data:** timestamped forward/futures prices and usable directional flow. If signing is weak, compare alternative definitions and reject unstable direction conclusions.

**Novelty/control:** generic fade_switch chooses follow/fade; this book estimates displacement and relaxation time before entry. Compare ordinary mean reversion, one-exponential decay and the multiscale model. N01 and N02 may overlap; merge them if their mechanisms and selected events are empirically indistinguishable.

## N03 — Sequence-order premium opportunities

**Hypothesis:** two market states with the same current momentum, IV and flow can have different outcomes because those variables arrived in a different order. Static trigger photographs discard that ordering.

**Model:** low-order path signatures or log-signatures over a strictly causal, small set of normalized channels: time, forward return, option premium response, IV innovation and flow. Degree two is a starting research restriction, not a claim that more degrees improve performance. Train a strongly regularized small predictor of forward executable premium outcomes, preserving CE/PE targets and label horizons. Fit all normalization on past data.

**Entry:** an independently monitored path enters a previously defined predictive sequence class with sufficient estimated premium movement and calibrated uncertainty. No existing breakout or pullback is required. Choose one permitted contract using a frozen rule. Use outcome-matured labels only.

**Exit:** sequence evidence reverses, forecast horizon expires, or fixed fallback exits. First compare exits on identical entries; do not jointly optimize many entry and exit parameters against 14 sessions.

**Novelty/control:** compare identical endpoint features, simple lag vectors and an ordinary linear model with comparable regularization. The decisive ablation removes event ordering while preserving endpoints; it is a diagnostic, not a substitute for forward validation. Reject if the benefit disappears against lagged linear features or is driven by data gaps. A large neural network is not justified by the current independent-day count.

## N04 — Cross-strike price-discovery propagation

**Hypothesis:** coherent innovations in liquid neighbouring options sometimes precede a still-fresh target contract's repricing. This is a conditional prediction of propagation, not an executable arbitrage claim.

**Model:** fit a compact dynamic factor/state-space model across simultaneously observable strikes and CE/PE quotes. Explain common forward, volatility-level and skew components. Estimate lagged innovations with receive-time causality; distinguish a real lead from asynchronous polling. Hold the target quote out of its own fair-value estimation where appropriate.

**Entry:** multiple independently observed neighbours imply upward repricing of an eligible CE or PE, the target quote is genuinely current, and a frozen predictive model supports buying that option after the actual request/fill delay. No incumbent direction trigger is inherited. Buy only one leg. Do not imply shorting the rich leg or hedging the basket.

**Exit:** innovation is realized, neighbouring evidence withdraws, model uncertainty rises, or time budget expires. Enforce episode reset after convergence.

**Data:** multi-strike fresh bid/ask history and timestamps. If the tape only contains ATM snapshots with inadequate coverage, this is observer-only pending collection. Never treat stale LTP as a fillable bargain.

**Novelty/control:** doc33 A05 changes strike selection after an existing entry. N04 generates an entry from cross-contract price discovery itself. Compare delta-adjusted single-contract momentum and simple cross-strike averages. Stress with measured feed/fill delays; reject an edge that vanishes before the current system could execute it.

## N05 — Volatility-surface migration

**Hypothesis:** a coherent rise or rotation in the implied-volatility surface can lift a long option's premium even without a conventional spot breakout. The opportunity is a forecast change in the surface, not merely a currently cheap strike.

**Model:** track robust low-dimensional innovations in IV level, skew and curvature from sufficiently fresh strikes. Forecast their short-horizon joint evolution with the forward; evaluate full option repricing under those physical scenarios. Use Delta/Gamma/Vega/Vanna/Vomma/Theta to explain the forecast and exposure, with correct units and exact-repricing checks. Do not insert a risk-neutral price distribution as a physical forecast.

**Entry:** a continuing upward premium opportunity survives joint forward/IV scenarios, quote uncertainty and elapsed time, with one long CE or PE chosen by the frozen criterion. A spot-directional break is unnecessary. If the forecast gives no defensible one-leg choice, abstain; do not silently turn it into a straddle.

**Exit:** the surface migration stalls/reverses, the expected remaining premium gain disappears, or time/clock controls fire. The observed price remains authoritative; model value is not a realizable exit price.

**Novelty/control:** differs from straddle_spike's trigger and doc33 A05's conditional strike-selection twin only if it independently forecasts surface dynamics. Compare simple IV momentum, premium momentum and the existing straddle mechanism. Run entry-overlap analysis before calling it a new source of opportunity.

**Data:** synchronized usable multi-strike quotes; calendar dynamics require multiple expiries actually recorded. Start within one expiry if that is all the feed supports. Fit uncertainty can make the entire book unavailable.

## N06 — Dispersion collapse and market leadership transfer

**Hypothesis:** constituent groups can disagree while the index is nearly stationary; a change in which group leads can produce an index move before an aggregate impulse threshold fires.

**Model:** decompose observed constituent returns into a weighted market component and residual components, using shrinkage and a small fixed grouping before considering dynamic graph estimation. Track residual dispersion, leader concentration and the direction in which disagreement resolves. A contraction of dispersion alone supplies no direction. Predict index motion from the observed transfer of leadership, not simply basket-minus-forward convergence.

**Entry:** a defined opposing group begins joining the leading direction while index displacement remains limited and the directional resolution model is confirmed. Buy CE/PE matching the predicted resolution. Reject stale constituent synchronization and mechanically overlapping evidence.

**Exit:** resolution fails, leadership fragments again, or predicted move has been realized; use frozen fallback exits.

**Data:** timestamped constituent prices, valid weights/coverage and index/futures observations. A small heavyweight subset is a partial basket and must be labelled accordingly.

**Novelty/control:** current domino synchrony, weather4 dispersion fields and doc33 A11 basket convergence already cover nearby ideas. This proposal counts as new only if an explicit transition model adds independent events beyond their thresholds. Compare the existing domino detector, breadth, dispersion alone and static convergence. Otherwise classify it as an extension, not a seventh independent discovery.

## N07 — Event-time pressure cycles (conditional candidate)

**Hypothesis:** repeated cycles of pressure build-up, diminishing impact and release have informative phase even when their duration in seconds changes sharply.

**Model:** reconstruct a causal event clock from actual observations, then use a compact hidden semi-Markov phase model or explicitly defined phase state machine. State duration is in observed event units, with wall-clock age retained. Model cycle completion and invalidation; do not smooth historical states using future data.

**Entry/exit:** buy the eligible option at a predeclared transition that predicts a premium advance; exit on phase termination, invalidation or clock expiry. One cycle supplies at most one entry unless a new cycle is established.

**Novelty condition:** doc33 A10 already proposes directional event-persistence timing. N07 must demonstrate that ordered cycle phases and duration change independent entries beyond Hawkes intensity/persistence. Otherwise merge it into A10. Compare wall-clock state models and simple event-count rules. Broker snapshots may support observation-event clocks, not true trade clocks; preserve that distinction.

## N08 — Matched-episode distribution forecasts (conditional candidate)

**Hypothesis:** the distribution of outcomes following similar *paths* may carry useful information that a single snapshot and a parametric passage model miss.

**Model:** retrieve only fully matured earlier episodes using a frozen, compact path representation. Compare ordinary nearest neighbours with a regularized optimal-transport distance between short empirical path distributions. Preserve temporal ordering through explicit time/channel features; a distribution distance alone can erase order. Estimate CE/PE premium outcome distributions, time to useful profit, adverse excursion and uncertainty using independent episode/day accounting.

**Entry/exit:** independently scan for a supported episode state; buy only when the past-episode forecast supports a fresh executable premium opportunity. Exit using a separately frozen continuation rule or matched horizon. Abstain for unsupported states. Future labels cannot enter the live retrieval store early.

**Novelty condition:** this is a separate modelling hypothesis, not automatically a separate economic mechanism. Count it as a new book only if it generates meaningful opportunities outside the existing triggers and N03, with a credible explanation. Otherwise use it as a diagnostic forecast or control. Compare simple nearest neighbours and the existing passage model before paying for optimal transport. Never retrieve the current episode's future or overlapping sibling duplicates as independent examples.

## Greeks: use them for economics, not decorative gates

For every proposed entry, attach a premium-response decomposition and uncertainty. Record whether anticipated gain comes from forward displacement, convexity, volatility change, or their interaction, and subtract modelled time decay consistently. Use exact repricing for finite shocks and expiry-sensitive scenarios. Higher-order terms must have documented derivatives and units.

No proposal may infer dealer positions, hedge direction, or forced buying from open interest alone. Dealer-signed GEX/Vanna/Charm are assumption-dependent unless inventory is observed. These new books do not require that unsupported inference.

## Implementation contract and speed

Use the current engine interfaces after inspection; suggested module names are proposals, not assertions of existing APIs. Factor shared path buffers, quote-age checks and rolling statistics into one computation per instrument/event. Each book owns explicit state, input availability, model artifact, episode ID, trigger reason and fallback exit. Preserve restart state and deterministic replay.

Keep training, graph estimation, surface calibration and expensive transport/retrieval-index construction outside the critical trading loop. Incremental inference must have bounded work. Cache using instrument/expiry, timestamp and model version, not a stale global result. Profile baseline and additions under actual tape load: p50/p95/p99 step time, worst observed pause, memory, data age, dropped events and throughput. Derive the permissible cost from the existing engine cadence; do not promise a fabricated latency figure.

If a model worker is late, stamp its result with the input cutoff and age. No blocking the trade loop waiting for research computation. No silent use of incomplete warm-up. Invalid inputs abstain from new entries; held trades retain deterministic fallback management.

## Proof package and Conductor experiments

1. Freeze hypotheses, features, thresholds, horizons, preprocessing, model dates and candidate-selection policy before evaluation. Use earlier training only and separate subsequent windows. Current 14 days are discovery material, not a large independent sample.
2. Supply a mechanism-only baseline, mathematical-model version and ablation per book. Compare matched execution and sample populations. Show enough evidence to distinguish added information from added parameters.
3. Report wins, losses, losing days, opportunities, abstentions, missed winners, episode concentration, feature failures, trade overlap and performance while incumbent books are idle. Low overlap alone is not merit.
4. Replay candidate alone, incumbent pool, pool+candidate, and pool-minus-member. Reconcile added, displaced and shared trades plus sizing effects exactly as docs/35. Standalone profit does not prove account benefit.
5. Run the existing approved mirror-Conductor track unchanged. If experimenting with a different admission or ownership policy, create a separately versioned shadow account; do not quietly rewrite mirror semantics.
6. Include executable-event simulation with pending/lapsed fills and concurrent triggers. Saved closed trades alone omit pending occupancy. Enforce truncation invariance, as-of artifact selection, restart/replay equivalence and quote/fill realism.
7. Preserve every loss with a pre-outcome-recognizable proposed explanation and its matched rejected winners. Do not add a bespoke veto after each loss and then score it on the same loss as proof of learning.
8. Separate implementation-correct, research-interesting, statistically supported, account-beneficial and owner-objective-met-on-observed-window. None implies invincibility or a guarantee of future profit.

## Build order and required Claude response

First return the current-code novelty audit and tape capability matrix. Pilot N01 and N02 where flow/depth are credible, and N03 where causal paths exist. N04/N05 depend on chain coverage; N06 depends on synchronized constituent data. N07/N08 remain conditional proposals, not promised extra books. Record all feasible observers alongside existing paper books before selecting which independent books to activate as shadows.

For each candidate deliver: mechanism card, actual code paths, state diagram, entry/exit/reset definition, parameter/artifact manifest, input availability, matched controls, correctness checks, speed measurements, trade-level report, and incremental Conductor attribution. State explicitly which proposals were duplicates or infeasible and why. Do not report a collection of renamed existing books as completion.

## Research anchors and limits

These papers motivate methods, not these specific strategies or a Nifty profit claim. The trading hypotheses above are proposed adaptations.

- [Cont, Kukanov and Stoikov: The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402) studies the relationship between order-flow imbalance, depth and short-interval price changes. It motivates N01's response diagnostics; contemporaneous explanation is not proof of future prediction or absorption identification.
- [Signature Trading: A Path-Dependent Extension of the Mean-Variance Framework with Exogenous Signals](https://arxiv.org/abs/2308.15135) motivates compact path-dependent representations for N03. Its portfolio framework differs from this one-leg all-in account; do not import its performance or guarantees.
- Document 33 provides primary-source references for state-space/changepoint, Hawkes, constrained surface, continuation-value and uncertainty methods. Recheck the original method assumptions before adapting them. Propagator, phase, cross-contract and transport proposals above require independent empirical identification; naming the mathematical family does not validate the mechanism.
