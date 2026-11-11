# Review of document 37, latest trades, and instructions for Claude

Prepared 10 November 2026, Asia/Calcutta. **Session analysed: 9 November 2026.** No `data/paper/2026-11-10.json` was available at review time. Do not describe these as 10-November trades. This report evaluates the latest saved session, current implementation and research artifacts. It does not change the champion, pool, parameters or trading code.

## 1. Assessment

Document 37 is a substantial improvement in research discipline: it inventories the actual feed, distinguishes snapshot proxies from real order events, builds controls, labels overlapping futures signals separately from option books, and reports negative findings. The overnight additions are **four hypothesis books and four controls**, not eight demonstrated independent edges. None traded in the saved 9-November live record.

The next step should combine operational correctness, better experiments and selective expansion. Do not respond to each failed model by adding another large collection of features. The session already contains hundreds of weather fields and clear opportunities; the account was unable to process later entries reliably. Extra computation without bounded persistence and event processing can make the system less capable of capturing opportunities.

Preserve the owner's requirements: all-in, long options only, gross paper accounting, no invented minimum trade quota or acceptable daily loss allowance. State explicitly when zero-loss aims are not met. Never infer guaranteed future profitability from finite observations.

## 2. Evidence and independent checks

Read: docs/37; saved books, Conductor events and decision records; `gen2.py`; its integration and exits; async persistence; weather4; the futures pilot and N03/N04/N05 dataset/research scripts and outputs.

The saved file contains **87 books and 608 trade records**, with no remaining open positions in that snapshot. None of the new n01/n02/n06 books appears. All 87 book totals and the detailed champion ledger are provided in:

- `data/replay/batch/codex_review_2026-11-10/ALL_BOOKS.md`
- `data/replay/batch/codex_review_2026-11-10/analysis.json`
- Reproduction: `python data/replay/batch/codex_review_2026-11-10/analyze.py`

The script records the source SHA-256, field completeness, entry/exit information, selected weather, releases and the serializer counterexample. It writes only its own audit artifacts.

Validation: `py -3.13 -m pytest tests/test_gen2.py tests/test_save_fast.py -q` — **23 passed**. Additional isolated probes reproduced the cache-mutation and pre-warm model-void cases below. This is targeted verification, not an exhaustive repository certification. The 22 research datasets' timestamp ranges were also checked: their file order is chronological with no overlapping segments detected; gaps remain real gaps.

## 3. The champion's complete trade ledger

| Entry | Leg | Source | Return | Best observed premium return | Gross P&L | Diagnosis lead |
|---|---|---|---:|---:|---:|---|
| 09:26:56 | 24850 CE | 9y | −12.528% | +1.24% | −₹11,518.00 | Little favourable movement; short bounce against larger decline |
| 09:35:29 | 25000 PE | 9y | +6.671% | +23.17% | +₹5,557.50 | Winner, substantial giveback |
| 09:45:30 | 24850 CE | 9y | −9.335% | +11.46% | −₹8,336.25 | Useful early gain lost |
| 09:55:09 | 25000 PE | 9y | −5.861% | +7.86% | −₹4,709.25 | Useful early gain lost |
| 10:20:18 | 24850 CE | 9y | −5.582% | +11.05% | −₹4,475.25 | Useful early gain lost |
| 10:26:14 | 25000 PE | 9t | +5.889% | +13.27% | +₹4,270.50 | Alternative source/exit contributes |
| 10:38:12 | 24950 PE | 9y | +14.386% | +35.79% | +₹10,660.00 | Winner, substantial giveback |
| 10:56:23 | 24850 CE | 9y | −14.847% | 0.00% | −₹13,562.25 | No favourable excursion; hard stop |
| 11:13:21 | 24800 CE | 9y | +16.018% | +40.35% | +₹11,895.00 | Reversal opportunity despite price below open |
| 11:33:18 | 24900 CE | 9y | +64.850% | +88.59% | +₹54,756.00 | Main profit contributor; preserve runners |
| 11:51:28 | 25050 PE | 9y | −9.837% | +5.05% | −₹14,202.50 | Largest rupee loss after capital expansion |
| 11:57:17 | 25050 PE | 9y | +23.364% | +44.49% | +₹29,328.00 | Re-entry in same contract succeeds |

Six wins add ₹116,467; six losses subtract ₹56,803.50; net **₹59,663.50**, ending capital ₹159,663.50. The largest loser in rupees is not the worst percentage loss: prior winnings increased its all-in quantity. This is expected accounting under the owner's sizing rule.

### A. Entry context matters, but a day-direction veto is not demonstrated

All four calls before 11:00 lost. However, the two later winning calls also entered below the day's first spot print. The direction-normalized `day_move` values on the winners were **−177.8 at 11:13** and **−108.15 at 11:33**. A blanket veto on negative `day_move` eliminates both winners as well as the losing calls.

Existing `breadth60_dir` was already high on losing calls: 0.7736, 0.9451, 0.7392 and 0.9454. The two winning calls were 1.0 and 0.8147. More instantaneous breadth thresholds will not cleanly separate these examples. Investigate *persistence and recruitment across horizons*, not a hindsight threshold at 11:00.

Important field semantics: weather4 defines `day_move = (spot - first_spot) * trade_direction`. Positive PE values mean a downward underlying move supports the put; they are not positive raw spot changes. Store raw and direction-normalized values with clear metadata.

### B. Exit improvement is plausible, but early exits cost runners

The three losses at 09:45, 09:55 and 10:20 total **−₹17,520.75**, after peaks of roughly 8–11.5%. The existing 9e sibling exited the same entries at +8.254%, +1.311% and +3.575%. Its 11:33 exit, however, captured only +17.09% versus +64.85% for 9y. These are real alternate strategy observations, not proof that an oracle can choose the better exit each time.

Build entry-matched exit studies with causal dynamic state, then rerun the complete strategy/account because earlier exits change occupancy, subsequent entries and capital. Retrospective peak price is a diagnostic, never a fill assumption. The 11:51 losing put and 11:57 winning put also show why blacklisting a contract or direction after one loss is unsound.

### C. Profit concentration is stronger than the simple subtraction suggests

The 11:33 trade contributes ₹54,756, about 91.8% of net P&L. Document 37's “without it +₹4,908” is the arithmetic sum with original quantities held fixed: exactly **₹4,907.50**.

If its entry is skipped and every other recorded entry/exit is held fixed while subsequent all-in quantities are recalculated in whole 65-unit lots, net becomes **−₹110.50**. This is a conditional sensitivity calculation, not a complete counterfactual replay; source state and newly available opportunities are deliberately unchanged. Label both quantities precisely.

### D. Agreement failed its first forward day

On 9y's own records `agree_same >= 7` retains five trades, two wins, with summed percentage returns −2.914%; excluded trades sum +54.215%. The analogous 9s threshold gives the same split. This confirms docs/37, but these sums are not compounded filtered-account P&L. Preserve R-019/R-020 as shadows, not proven gates. Their identifiers now refer to agreement rules; do not confuse them with the older unregistered edge proposals bearing those IDs in the 8-November proposal file. Cite immutable rule versions/hashes, not IDs alone.

### E. Rankings across books are useful but operationally confounded

Premium momentum: 33 trades, 18 wins, +₹238,615. 9e: 15 trades, 11 wins, +₹107,188. 8x: 19 trades, nine wins, +₹115,843. Fade switch: 63 trades, 22 wins, −₹76,661. The champion beats 9y alone by ₹29,120 on this recorded day.

The timing defect affected books differently. Premium momentum's winning live day does not contradict the failed N05 fixed-horizon premium-feature regression: they are different trigger, sample, holding, contract and fill policies. Reproduce the actual premium_momentum book under common execution before concluding that either experiment represents all premium-momentum strategies. Identical sibling trades are correlated copies, not independent evidence.

## 4. Operational diagnosis and repairs before expansion

### O1. Engine stalls prevented opportunities; widening the fill window is not the repair

The diary records **48 owner acquisitions, 12 entries and 36 lapsed releases**. **27** releases occur after the final 12:05:08 exit (document 37 says 26). Many are retries around the same setup; do not call them 27 independent missed profitable trades. One fixed-contract/time/episode matching policy is needed.

The log contains multi-second tick pauses and docs/37 attributes them to growing synchronous serialization and disk writes. I verified the count and inspected the implementation/log, but did not independently reconstruct every raw quote during every lapse. Reproduce the first available post-request quote from the tape to separate data absence from processing delay. Report missed outcomes as counterfactuals, not realised money.

The sum `(recorded_exit - exit_trigger_px) * recorded_qty` is **−₹3,383.25**, confirming the stated mark-to-fill difference. The trigger price is not necessarily the first fillable post-trigger observation; do not present this whole sum as proven recoverable profit from the persistence fix.

### O2. Cache validity is insufficient for mutable closed trades — reproduced

`paper._trade_text` keys validity on object identity and **top-level field count**. Changing an existing `exit`, replacing a value, or modifying nested weather without changing the count returns stale serialized text. Isolated reproduction: cache `{exit:10, weather:{x:1}}`, then change to `{exit:11, weather:{x:2}}`; serialization still gives the earlier values.

This demonstrates a conditional defect, not proof that today's saved trades were corrupted. Fix with enforced immutable finalized trade records plus a deliberate amendment/version API, or explicit revision-based invalidation. A full deep hash on every save would reintroduce the hot-path cost. Add tests for existing-field mutation, nested mutation, field replacement and correct amendment persistence.

### O3. Flush timeout is ignored and write success is conflated with idleness

`save_books` and `load_books` call `save_flush()` but ignore its Boolean result. If the worker exceeds the timeout, a synchronous save can proceed while a background write still uses the same `.tmp`; a load can return an older generation. `_Saver.flush` returns idle after a failed write as well; callers must distinguish drained, durable and failed.

Handle timeout explicitly, serialize writers to each path, track requested/completed/durable generation and surface errors. Never race a fallback writer against the outstanding writer. A “latest wins” queue is bounded in jobs, not in elapsed staleness or number of dropped generations. Replace “at most one write behind” with measurable persistence age/generation lag. Add blocked-writer, timeout, failed-final-write, shutdown and recovery tests.

### O4. Model-driven exits can fire before the documented warm-up — reproduced

`Gen2.void` lacks a `warm`/readiness check. N02 can regain coefficients after 120 observations, and N06 can form a 60-second group return, while the documented entry warm-up remains 600. Both REBUILD and FRAGMENT can therefore exit a held position before the stated post-restart readiness. Isolated cold-state probes returned both exits with `warm == False`.

Use mechanism-specific exit readiness and explicit restart/gap validity; a global `warm` that depends on N01 beta is not an appropriate readiness test for every mechanism. Persist the original bracket/thesis parameters with the position **at fill**, rather than first constructing `gx` during a later exit check. Restart between fill and that check can otherwise lose signal-specific settings. Add exact restart boundary tests and decide whether model state is restored or fallback-only until readiness.

### O5. Per-instrument freshness is missing from Gen2's interface

`_gen2_feed` passes prices, depth and constituent vectors but no per-instrument ages. `Gen2._hw_ret` treats finite positive prices as valid. A live overall feed can coexist with stale individual stocks or an old depth snapshot. The global blackout cannot certify every component. Coverage currently means valid numbers, not fresh weighted coverage.

Pass as-of timestamps and freshness masks; calculate freshness-weighted constituent coverage at both ends of each return window. Tag five-level versus best-level fallback depth to prevent discontinuous input scale being mistaken for liquidity release. Use real elapsed time for decay coefficients when update spacing varies; current EW decay assumes one second per accepted update even when two-to-five seconds pass.

### O6. Model interpretation and controls need tighter tests

N01 applies beta fitted on 10-second responses to 60-second pressure. That transfer requires validation; horizon-dependent impact/decay may invalidate it. Its response condition also accepts large moves against the pressure, not only a small response, and confirmation does not continuously enforce the original strength/sign condition. Specify and test what persistent absorption actually means.

N02's negative fast coefficient does **not alone prove non-identifiability**. Estimate condition numbers, uncertainty, coefficient stability and predictive residuals. Current positivity of the coefficient sum is weaker than a positive, monotone impact kernel. Compare unconstrained and economically constrained models against one-timescale and no-flow controls; do not force a coefficient sign merely to make the backtest look better.

The price-only N01 control is currently invoked inside the `beta is not None` branch. Decide whether that is deliberate matched-availability conditioning. Publish both that matched control and a truly independent price-only control; do not silently attribute the resulting availability restriction to price logic.

## 5. Research conclusions that need qualification or correction

1. **N01/N02/N06 pilot is not full strategy evaluation.** It scores overlapping futures signals, not options or capital. `pilot.py` applies target/stop/thesis/clock but does not replay dynamic `Gen2.void` exits. Some live and pilot inputs also differ in timestamp precision and blackout/freshness handling. Run the actual engine with these books before calling this a full rejection or validation of the implementation.
2. **The breadth control's 15 positive days are interesting, not proof of edge.** Thousands of overlapping observations and differing targets/stops invalidate naive independent-trade tests and raw sum comparisons. Compress into episodes and run single-position option accounts with identical clocks/execution. Avoid declaring information “real” from this pilot alone.
3. **N03 result is too concentrated to promote, but the whole method class is not disproved.** The degree-two representation, ridge predictor, 99th-percentile threshold and fixed 120-second horizon comprise one tested specification. Audit the +593% expiry observation at contract and quote level before any robustification; do not delete a legitimate tail merely because it dominates. The test does not establish that N08 retrieval would necessarily fail; it was not separately tested.
4. **N04's quoted 3-second lead versus 30-second trade is a horizon mismatch.** A negative 30-second label cannot by itself prove the 3-second signal was unbuyable. Decompose contemporaneous mid, delayed entry ask, and 1/3/5/10/30-second later values, using actual receive timestamps and a frozen latency grid based on measured engine behavior. This may still reject the strategy, but for a demonstrated reason. Repeatedly tuning latency until profit appears is not acceptable.
5. **N05's non-expiry table is a different experiment, not subtraction of expiry trades.** The code filters expiry samples *before* walk-forward fitting, changing training dates, first eligible test day, models and thresholds. This explains 287 non-expiry picks versus 149 overall. Show both (a) the original frozen predictions restricted to non-expiry dates and (b) a separately trained non-expiry model. Pair comparisons on common dates/availability. Full-sample surface mean +0.868% exceeds IV momentum +0.678%; the conclusion should be “no convincing incremental evidence,” not literal numerical underperformance in every comparison.
6. **Dataset timestamps are rounded after observing a packet.** `ds.py` updates state using a packet at fractional receive time, then stamps the row `int(t)`. A nominal 10:00:00 row can contain information received at 10:00:00.8. Keep actual cutoff/receive times or construct boundary snapshots from packets already received. One-row-ahead labels are not guaranteed to represent a full one-second executable delay. Option freshness up to three seconds is not a requirement for a new post-request quote.
7. **Fix one-second occupancy discrepancies.** `label` exits at `i+1+H`; selection sets `busy_until=t+H`. A later candidate can be admitted one second before the previous labelled position exits. The same pattern appears in N04. Use actual request, fill and exit timestamps.
8. **Protect against missing-outcome selection.** Current sample filtering requires future valid CE and PE labels. Report dropped/censored cases and entry availability separately; live entry cannot know a future quote will be missing. Do not train on unlabelled samples, but do not erase their operational impact from coverage metrics.
9. **Keep the accounting comparison explicit.** Main books use their current gross first-print convention; the new research uses delayed ask-to-bid labels. Preserve the owner's official convention and report quote-aware execution as a parallel diagnostic. Spreads and price availability are market observations, not brokerage/tax deductions. Never claim one result directly dominates another under different fill conventions.
10. **Make research reproducible.** `ds.py` and `research.py` hard-code a temporary scratchpad. Move dataset/manifests to configured durable research paths, record hashes and all picks, and use explicit IST rather than host-local `time.localtime`. Current chronology across part files was verified, but sorting and uniqueness should be assertions, not filename assumptions.

## 6. Additional weather: 24 proposed items, not 24 automatic trade gates

Proposed IDs 105–128 require checking the latest registry before allocation. Each item may contain several typed fields. Existing 69–104 already cover indicators, breadth, IV, depth, account context and day direction; do not duplicate them with new names.

Every field needs units, sign convention, raw versus direction-normalized form, source timestamps, cutoff, readiness, missing reason, parameter/model version and compute cadence. Model uncertainty fields are estimates, not calibrated probabilities unless tested. All entry features must exist before the trigger. Held-trade features below are a **separate continuation photograph** and cannot be backfilled into entry rows.

| Proposed item | Additional information | Implementation / use |
|---|---|---|
| 105 Engine service delay | receive→state-update→decision ages; max/p95 processing delay over completed prior window | Monotonic timestamps; distinguish live computation delay from market freshness |
| 106 Persistence health | pending generation, durable generation, durable age, last error, serialization/write duration | Observer telemetry; quantify the defect that stopped trading |
| 107 Cross-input synchronization | oldest/newest contributing receive time, temporal dispersion | Per quote set; distinguish lead-lag from delayed polling |
| 108 Fresh weighted coverage | fresh cash/futures weight, stale leaders, group coverage at both return endpoints | Extend existing breadth counts; stale finite prices are not valid evidence |
| 109 Flow-sign uncertainty | volume classified outside/inside previous spread, tick-rule share, unsigned share | Snapshot proxy provenance; no claim of recovered trade direction |
| 110 Response-model reliability | residual scale, conditioning, effective history, beta stability by horizon | N01 confidence and horizon compatibility, not just beta value |
| 111 Pressure decomposition | raw pressure, demeaned pressure, directional sign disagreement, duration | Separate negative absolute flow from positive deviation from its mean |
| 112 Impact-kernel diagnostics | fast/slow contributions, conditioning, sign/monotonicity checks, decay stability | N02 interpretation and abstention; keep model readiness explicit |
| 113 Absorption episode state | candidate/confirmed/spent, duration, observed/expected response, pressure continuity | New path information beyond instantaneous `absorb60` |
| 114 Breadth recruitment | weight newly joining, leaving or reversing over fixed elapsed windows | Distinguish broadening moves from a momentary high breadth reading |
| 115 Leadership persistence | leading-group tenure and turnover; concentration change rather than level alone | N06 and scale-transition diagnosis |
| 116 Cash–stock-futures transmission | fresh basis innovations by group, futures-leading-cash evidence | Supports proposed S01; requires paired-instrument clock alignment |
| 117 Cross-expiry innovation | near/next total-variance innovations at comparable moneyness, age and fit error | Supports S02; does not infer physical direction from IV alone |
| 118 Scale-transition state | agreement/transition among short and longer horizons, duration since change | Existing moves retained; add causal transition state rather than more thresholds |
| 119 Quote-response residual | observed option mid change minus repriced forward/time/IV contribution, uncertainty | Same fixed contract; separate stale marks and unexplained premium demand |
| 120 Opportunity survival | signal age, first versus retry, predicted remaining movement at actual fill | Cluster repeated lapsed requests, avoid treating retries as independent setups |
| 121 Contract-path continuity | fixed-contract path duration, ATM/strike-switch flag, missing segments | Prevent artificial momentum or IV changes from instrument substitution |
| 122 Fill evidence | request-to-next-observation gap, actual observation age and post-request eligibility | Outcomes logged after fill separately; entry uses only prior estimates |
| 123 Held gain maturity | elapsed time to gain thresholds, favourable duration, current known peak | Continuation-only; event-time history up to now, no final MFE leakage |
| 124 Held giveback dynamics | giveback magnitude/rate, time since observed peak, recent favourable/adverse variation | Continuation-only; compare early-exit behavior without choosing peaks retrospectively |
| 125 Held premium attribution | running forward/convexity/IV/time contributions plus repricing residual | Continuation-only; consistent units and scenario repricing near expiry |
| 126 Live thesis disagreement | price, breadth, flow and surface model agreement with missingness/readiness | Transparent vector, not a silently optimized weighted score |
| 127 Conditional book opportunity | incumbent occupancy, selected-source rank, eligibility/rejection reasons | Extend existing book counts with account decision context; future displaced P&L stays a label |
| 128 Research lineage/support | artifact cutoff, in-support flag, effective independent episodes, schema/rule hash | Makes model provenance and sparse support visible at each prediction |

First instrumentation batch: 105–110, 120–122, 128. First continuation batch: 123–126. Then 111–119 and 127 where models/feeds support them. Compute direction-free state once per appropriate event, share by snapshot ID, store immutable snapshots separately from every trade, and record references. Retain deterministic expansion/export for existing analysis tools. Profile total end-to-end load, not just individual feature functions.

## 7. Shadow-book expansion: two new mechanisms, two redesigns, two exit twins

Do not claim six novel independent economic edges. The classification below is deliberate. All remain hypotheses, use frozen parameter manifests, and require the same long-option/all-in rules. No proposal enters the main pool merely because it was built.

### S01 `cash_futures_transmission` — new independent candidate

Use paired stock futures and cash observations for the recorded heavyweights. Hypothesis: a sustained, fresh stock-futures innovation propagating into cash constituents forecasts an index movement not yet reflected in the Nifty future. This differs from N06's cash group disagreement and static basket synchrony.

Estimate a small, regularized lagged model or causal state-space residual using earlier sessions, with group-level shrinkage. Model intraday basis separately from raw returns. Entry requires coherent fresh futures→cash transmission across a predeclared coverage, a still-unrealized index response, and an eligible option's joint price/time response. CE/PE follows the predicted index move. Exit on propagation realization, basis reversal, loss of participating coverage or fixed horizon/fallback.

Controls: cash breadth alone, stock-futures return alone, existing gap/domino, and matched latency. Reject if apparent leadership disappears with receive-time alignment, stale-print exclusion or unchanged underlying momentum. Estimated weights and incomplete stock coverage remain explicit. Deep cross-impact estimation over all 23 stocks is unnecessary with this short history.

### S02 `cross_expiry_shock` — new independent candidate, related to N05

Use next-week and current-week quotes already recorded. Hypothesis: a persistent common volatility innovation seen in the next expiry forecasts a later near-week premium response after removing forward/moneyness/time effects. N05 tested within-expiry quadratic level/skew/curvature; this uses transmission across maturities and must demonstrate incremental information.

Track total variance `sigma²*T` and robust common-factor innovations at comparable moneyness; do not compare raw IV magnitudes without maturity context. Use a small causal regression with uncertainty, not a large surface neural net. Buy one permitted current-week CE or PE only when its *joint forward/IV* premium forecast supports the leg. If the model predicts volatility magnitude but no defensible one-leg opportunity, abstain. No calendar spread, short leg or claim of riskless arbitrage.

Exit on realized repricing, disappearance/reversal of the innovation or a frozen holding horizon. Controls: near-week IV momentum, near-week surface model, next-week direction alone. Stress chain age and expiry sensitivity. If transmission is below executable latency, reject rather than making the fill assumption faster.

### S03 `breadth_recruitment` — redesigned N06/control experiment

The breadth control merits proper option/account testing more than the currently unsupported leader/opposer complexity. Model persistence of weight joining a direction, departing weight and cash/futures agreement; avoid requiring an arbitrary named sector to oppose first. Independently trigger before a conventional index impulse only if option economics permit. Exit when recruitment reverses, predicted movement is realized or horizon/fallback expires.

Keep existing breadth-only control frozen. Compare recruitment against it at matched occupancy and episode count. This is a refinement of an existing idea, not an extraordinary new mechanism. Prove that added path state improves the baseline before retaining it.

### S04 `premium_response_residual` — redesigned N04/N05 experiment

Test whether a fresh option's sustained premium response beyond explained forward/IV/time changes forecasts further repricing over a horizon longer than observed system delay. This is option-specific demand/response, not an apparent instantaneous stale-strike bargain. Keep the contract fixed; use held-out fitting for the target when estimating common IV factors.

Independent entry requires repeated fresh residual innovations plus a forecast of absolute premium appreciation, not just cross-sectional cheapness. Exit on residual normalization, invalidation or horizon. Controls: actual premium_momentum, simple premium acceleration, repricing-residual-free model and the original short-horizon N04. This can fail; do not describe it as a discovery merely because the mathematical decomposition is richer.

### S05 `gain_maturity_exit` — matched-entry exit twin

Clone a frozen entry stream for research only. Compare continuation versus exit after an observed gain using favourable duration, giveback rate, elapsed option decay and weakening forward response. A small predeclared state machine is the first baseline; a continuation-value model comes later if independent episodes support it.

Entry is unchanged. Exit when a completed state transition indicates a failed continuation, with a separate persistent-runner state. Do not insert “protect 8% gains” because today's losers peaked near that figure. Evaluate the actual 11:33 runner and all earlier-window runners as costs of protection. First isolate matched-entry exits, then rerun full books with altered occupancy.

### S06 `scale_transition_entry` — context twin, not new entry family

Compare a base book with causal short-versus-long horizon transition evidence. Specifically test when a bounce remains a countertrend move versus when a reversal broadens and persists. Use 118, 114 and 115, and simple price-only controls. Do not use the eventual day's turning time or the rule “after 11:00 calls are good.” Exit policy stays unchanged initially.

Purpose: preserve both late winning calls while testing rejection of earlier weak bounces. That is a hypothesis to evaluate across dates, not a promised separator of these twelve observations.

## 8. Exact work order and acceptance evidence for Claude

**Phase 1 — correctness and measurement.** Address O2–O5 and archive reproducible failing cases. Verify durable final save, interrupted-write handling, restart position state, backfill of 9-November learning, and complete/censored tape status. Measure engine step and receive-to-decision latency with the actual new workload. “Zero lapsed entries” is not sufficient: distinguish legitimate quote absence, stale inputs and preventable processing lapse.

**Phase 2 — fair existing-model experiments.** Run actual Gen2 books and controls through the same event replay/fills. Include dynamic void exits and missingness, one position at a time, episode clustering and warm/restart rules. Fix timestamp/occupancy issues before interpreting revised N03–N05 numbers. Preserve old results and label corrected versions; do not silently overwrite history or tune parameters on the correction window.

**Phase 3 — focused additions.** Add the operational/lineage weather batch, then continuation observations. Implement S01 and S02 only after fresh-data capability checks; keep S03/S04 explicitly labelled redesigns and S05/S06 twins. Shared buffers, fixed work and background fitting preserve speed. Do not instantiate dozens of independently recomputing surface/regression objects.

**Phase 4 — account contribution.** For every candidate publish candidate alone, current pool, pool plus candidate and leave-one-out comparisons. Reconcile added trades, displaced trades and sizing effects as in docs/35. Include pending/lapsed occupancy, not only closed trades. Your approved mirror Conductor remains the baseline; alternate admission/ownership policies live in separately named shadow accounts.

**Required report tables:** per-day wins/losses/P&L; independently clustered opportunities; missed and rejected winners; source/exit comparison; continuation failures; freshness and readiness coverage; actual latency and persistence lag; all tried specifications; model training cutoffs; and trade-level account attribution. Separate expiry/non-expiry, morning/afternoon and interrupted/clean execution as declared strata. Use chronological validation and account for repeated searches; old 15-day tapes are now discovery material for these experiments.

The deliverable is improved evidence and working shadow implementations, not a guaranteed no-loss classifier. Mark owner requirements unmet wherever losses remain; do not quietly replace them with positive mean return. Equally, do not claim a finite unsuccessful threshold/regression study proves that every advanced model must fail.

## 9. Primary research references for the new proposals

The methods are research anchors, not evidence of profit in this repository. S01 is an adaptation: [Hoffmann, Rosenbaum and Yoshida, estimation of lead–lag from non-synchronous observations](https://arxiv.org/abs/1303.4871) addresses how sampling affects estimated lead/lag. Here, receive-time causality and actual execution delay remain essential.

S02 is a proposed cross-expiry application, not a reproduction of published strategy results. [A Two-Step Framework for Arbitrage-Free Prediction of the Implied Volatility Surface](https://arxiv.org/abs/2106.07177) studies surface representation, prediction and arbitrage-aware reconstruction. The repository's short history does not justify importing its larger-data learning architecture; start with low-dimensional controls and uncertainty.
