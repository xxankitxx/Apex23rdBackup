# Correctness and direction audit for Claude

8 November 2026. Review of the evolving ApexOptions repository while replay work is running.

## Scope and evidence

This is a prioritized correctness review, not a certification of the entire repository. The source snapshot was copied from working tree based on commit `cf8f7c5`, including uncommitted changes, into `C:\Users\Ankit Madhogaria\AppData\Local\Temp\apex-audit-b57cb2c6fa1c4fc783b03ee00e138a42`. Its `audit_manifest.json` contains file hashes. Credentials and live data were excluded from the copy. Later Conductor observations below refer to the live working-tree source inspected during this review. Recheck those findings after concurrent edits.

All 144 Python source files found across the snapshot's application, tests, research and supervisor parsed successfully. Parsing establishes syntax only. Completed snapshot test results appear at the end. Subsequent working-tree changes are reconciled in the response review below.

Independent runtime, research and numerical audit subtasks were requested. One returned a usage-limit failure. Earlier model audits are incorporated, but those subtasks do not constitute completed independent whole-repository verification. No live broker connection or full-tape replay was launched by this review.

## Direction assessment

The broad direction is appropriate. Shared raw tapes, arrival-time weather, explicit shadow experiments, preserved controls, and one account with deterministic priority support meaningful evaluation. The present bottleneck is trustworthy evidence and operational completeness. Adding model-backed decisions before correcting historical parameter provenance would make their apparent performance difficult to interpret.

The owner has approved mirroring independently running source books, and docs/28 now describes that design. Treat it as the intended account semantics. A source book can remain occupied by a trade the account rejected, so opportunity coverage must be measured against signals the mirror architecture can actually receive. The earlier question about which architecture was intended is resolved.

The owner has approved paper operation from 9 November with pairs selected from the discovery cards. These pairs start at low standing and the historical comparison is labeled in-sample. This is an authorized experimental launch. Track forward-window qualification separately, since low standing now also includes pairs with no first-window pass. Preserve the basis and date of each admission and priority statistic.

## Reconciliation with Claude's response

Claude's triage is broadly sound. The following statuses reflect the subsequent source inspection and small isolated reproductions, not a fresh full-suite run.

- **F01 partially verified fixed.** The current pending-owner branch falls through after release. An isolated execution of the current class with lapsed owner A and a fresh trigger from B now assigns ownership to B on that step. Full fill, still-pending, rejected and unaffordable regression coverage remains for Claude to complete. Accept the distinction between the offline simulation and the engine defect, while retaining a comparison on complete event fixtures.
- **F03 requires another correction.** The new implementation filters rows by their end date before selecting the latest row. Example: low standing from 9 November with no end, then full standing from 10 November through 11 November. On 12 November it returns the old low-standing row. This was reproduced. Resolve the latest applicable version first, then apply that version's expiration or inactive state. Otherwise retirement can resurrect an older version. Define inclusive end-date semantics and equal-date tie handling, and validate real dates and interval ordering. Represent permanent retirement with an explicit dated inactive state where needed.
- **F05 remains scheduled at inspection.** The inspected requirements file still omitted SciPy. The proposed dependency and capability check address the finding. A later edit may already have landed.
- **F02 can be staged with a firm eligibility boundary.** Retain all requested fields in descriptive photographs and cards, but prevent rules with nonchronological HMM/Hawkes dependencies from entering the eligible proposal. Include direct fields, derived fields and combined conditions. The currently inspected `pool_builder.best_line` chooses the strongest line without a provenance exclusion. Labeling a row after selection is insufficient. Filter before selecting the best eligible line, and re-evaluate selection/null accounting as necessary. This can be done from existing diaries without rerunning the market engine when the affected fields are observer-only and their dependency scope has been verified.
- **F04 remains an operational prerequisite.** An integrity fault and distinct adjustment record improve transparency. An adjustment must not silently count as a successful trading exit or free capital without an explicit reconciliation policy. Test automatic process recovery and missing source state as well as a manual restart. A known recovery-path defect matters as soon as a position can be held during a failure.
- **F06/F07 can remain research work while their usage is scoped.** GEX also appears in weather-card candidates. Before admitting a GEX-based pair, address the relevant correctness issue or flag and exclude the affected candidate. F07 remains a robustness concern rather than a reproduced wrong verdict.
- **F08 is an approved deferral.** Record the versioned deferral in docs/28. It is not an outstanding requirement for this launch under the owner's clarified decision.
- **Historical test failures are reconciled.** The current restricted-rule assertion now expects `not in the register`. The snapshot mock issue and timing-under-load explanation are consistent with the original evidence. The old failure counts remain a record of that snapshot, not a claim that the latest checkout still fails them.

One terminology detail deserves explicit documentation. `pool_builder` currently initializes `ret_per_trade` from discovery-card returns. This is a permitted experimental priority heuristic if recorded as such. It should not be presented as test-day priority performance until the dated forward evidence exists.

## Findings requiring correction or explicit resolution

### F01 — P1. A lapsed entry drops another eligible trigger

**Confirmed by a synthetic reproduction on the current Conductor.** In `apex/engine/conductor.py`, `Conductor.step` collects current triggers, then its pending-owner branch returns directly from `_await_fill`. If that method releases a lapsed or rejected owner, the current eligible triggers are never considered. `_fired` only returns triggers whose timestamp equals the current step, so the opportunity disappears on the next step.

Reproduction used a flat account with pending owner A from time 9, A now having neither pending entry nor position, and eligible B carrying a fresh pending entry at time 10. Calling `step` at time 10 returned `None`, cleared ownership, and reported `flat: a entry lapsed`. Expected behavior under the first-eligible-trigger rule is to release A and consider B on that same step.

Correct the transition so release continues to current-step admission. Continue returning early when the owner remains pending or fills. Add a focused regression covering release, fill, still-pending, and fresh competing triggers. Relevant inspected location is around line 141.

### F02 — P1. Historical model output uses future-trained parameters

**Confirmed source configuration.** `apex/quant/params.json` identifies fitting on 5 November using sessions through 4 November. `apex/engine/quantview.py` loads the global artifact without choosing it by replay date. October replay weather can therefore contain outputs derived from later data.

This affects evidence using HMM/Hawkes features. It does not establish that every incumbent trade is contaminated, since these outputs have largely been observational. Trigger-time truncation alone cannot catch leakage inside already fitted parameters.

Add `trained_through`, permitted-use date, training-session hashes and model version. Reject invalid historical artifacts or emit unavailable status. Retain existing all-sample outputs as descriptive research. Recompute affected weather cards and model comparisons with chronological artifacts before treating them as proof.

### F03 — P1. Pool history cannot express retirement and standing changes

**Confirmed implementation gap.** `active_entries` selects every row with `from <= day`; rows have standing and return-per-trade values but no effective end or transition logic. An add-only sequence that promotes a low-standing pair produces both rows on later dates. Editing the original row changes the earlier replay's priority. A rule switched off by the required monitoring process also needs removal effective on a particular date.

Represent dated events or effective intervals, keyed by a stable pair/version identity. Resolve one active state per pair as of each date. Persist the historical priority statistic available then. Test admission, promotion, removal, requalification, duplicate entries and replay before each transition. Hash the pool and status history in every run manifest.

### F04 — P1. Missing owner position can manufacture a paper exit

**Confirmed source behavior, recovery-path impact needs a targeted integration test.** In `_follow`, if the source position disappears and no matching closed trade is found, the account closes at its remembered `last` value or entry value and marks the result stale. That price need not represent a new observed executable paper fill. It can convert state loss into an apparently resolved trade and alter compounded capital.

Persist enough ownership and source identity to recover safely. On an unresolved source mismatch, log an integrity fault, reconcile persisted records, and apply a declared fresh-quote emergency exit policy when possible. Preserve a pending/unresolved state while no valid quote exists. Any accounting adjustment must be explicitly distinguished from a trading fill and excluded or separately scored. Test restart, missing book, missing source trade, and a source closing immediately after entry.

### F05 — P2. Required quant dependency is absent from installation requirements

**Confirmed packaging gap.** `requirements.txt` omits SciPy, while `greeks_hi.py` imports `scipy.special.ndtr`, and `hawkes.py` imports SciPy optimization and filtering. `engine_main.py` catches failure to import QuantView, allowing the engine to continue without it.

A fresh installation can appear healthy while losing advertised model/weather capabilities. Declare the dependency or an explicitly installed quant extra. Add a capability check reporting missing model groups before research begins. A live data fallback may be appropriate, but missing research inputs must remain visible and invalidate claims of full factor coverage.

### F06 — P2. GEX cache misses time and volatility changes

**Confirmed cache key.** `GexMap.needs/update` keys on chain version and rounded forward. With those unchanged, advancing expiry time or changing IV does not refresh the map. Gamma and a modeled flip depend on those inputs, particularly near expiry.

Add a bounded refresh cadence or appropriately bucketed time/IV versions. Preserve chain-age tracking independently so recalculation cannot make old OI look fresh. Test fixed forward/OI with advancing time and changed IV, then profile the added work.

### F07 — Robustness improvement. Verify the GEX destination regime

**Review concern, not a reproduced incorrect verdict.** The advisor treats a nearby flip ahead in the trade direction as an escape from damping without retaining and checking the sign beyond that crossing. With a continuous curve, positive current gamma and the first genuine crossing, this inference can be correct. Coarse grids, multiple crossings and stale model state deserve explicit verification before labeling the destination.

Compute the signs on both sides, preserve crossing orientation, and check the destination regime. Test upward and downward crossings, multiple roots and tangencies. Dealer signs remain an assumption even after the numerical logic is corrected.

### F08 — Deferred by owner. Protected-phase behavior

The earlier plan reserves explicitly covered phases from lower-ranked trades likely to overlap them. The owner has deferred that behavior for this version. Its absence is therefore an accepted version boundary.

Document the deferral in docs/28 and the account version. If later implemented, use only historically available holding-duration estimates and test lower-ranked entries immediately before a protected phase.

## Additional correctness concerns requiring focused tests

- **Same-step fill then exit.** Conductor ownership is acquired after source books run, and the account opens on a subsequent follow step. Verify behavior if the source fills and closes before the account observes an open position. Reconcile source closed trades by stable trade ID rather than relying solely on seeing an open state.
- **Kill and flatten management.** The Conductor file mentions a kill reason but its admission check visibly handles blackout. Trace the actual engine guard and source exit paths before declaring kill and flatten coverage complete. Test a pending owner at a kill transition.
- **Hawkes input semantics.** QuantView aggregates volume changes into classified observations and exposes excitation. Confirm baseline intensity and sampling match calibration before interpreting outputs as full event intensities.
- **HMM duration.** An empirical remaining-duration summary is not a full semi-Markov filter. Empty tails must not become certain imminent reversals.
- **SVI validity.** Nonnegative total variance does not guarantee full butterfly/calendar arbitrage constraints. Validate sparse and stale quotes before trading smile residuals.
- **Diary label leakage.** Median winning peaks and stop scales computed across all supplied rows can import later outcomes into earlier training labels. Freeze label parameters within discovery data.
- **Replay seeds.** Running separate dates with `--seed data` can differ from a chronological sequence with date-appropriate prior levels and state. Audit seed dates and hashes, including every learned prior. Do not assume a copied current live folder recreates historical state.
- **Mutable code during batches.** Different child processes may import different working-tree revisions. Record actual per-child source/model/pool hashes and reject mixed-version comparisons. A parent-start hash alone is insufficient when code changes during execution.
- **Research and decision times.** Preserve `recv_ns`, quote age and model as-of time. A second-old model is permissible only when the strategy explicitly allows it.
- **Frontend and feed.** Shared-memory consistency, reconnect recovery, gateway payloads, JavaScript rendering and browser controls need dedicated integration verification. Python parsing cannot certify these areas.

## Required evidence before accepting the current replays

1. Freeze a revision and all model, pool, rule and seed artifacts for the comparison.
2. Establish complete tape-part coverage and truthful seed chronology for each date.
3. Complete the unit suite, explain every failure, and distinguish expected failures from exercised guarantees.
4. Run recorder off/on equality and duplicate-replay equality, including the new account.
5. Use an independent event-level oracle for pending entries, rejected fills, same-step exits and competing triggers. Matching two implementations that both consume source closed trades is insufficient for those states.
6. Compare incumbent trades with the established baseline and explain each difference.
7. Report loss counts, losing days, captured and missed opportunities, occupancy and model availability with the owner's gross-paper accounting.
8. Measure latency on realistic load separately from this resource-contended audit. Several replay workers were active during inspection.

## Recommended action order

Complete F01 regression coverage and correct the F03 version-resurrection case. Enforce provenance eligibility before selecting experimental pairs, with immutable replay inputs. Complete missing-source recovery and installation capability checks. Preserve the approved mirror semantics and protected-phase deferral. Then evaluate the proposed shadow books against the documented failed experiments in docs/24 and docs/26.

The advanced-model plan remains a reasonable research program. Current evidence supports continuing development, while the findings above prevent a claim that the full repository or the new Conductor is already verified correct.

## Test outcome

The isolated stop-on-first-failure run completed with 126 passed, 2 expected failures and 1 failure in 115.88 seconds. `tests/test_c5_commentary.py::test_performance` measured 1.89 ms per evaluation against a 1.5-ms threshold. Multiple replay workers were active, so this establishes a failed timing assertion under contention rather than a demonstrated algorithmic regression. Two tests also returned values and produced `PytestReturnNotNoneWarning`.

The subsequent full snapshot run completed in 950.03 seconds with **407 passed, 3 failed, 8 skipped, 4 expected failures and 1 unexpected pass**, plus two warnings. It used a fresh bytecode-cache location to avoid copied cache filenames obscuring traceback provenance.

| Failed test | Observed result | Interpretation and next action |
|---|---|---|
| `test_c5_commentary.py::test_performance` | 2.30 ms against a 1.5-ms limit | Repeated timing failure under active replay contention. Retest on a quiet machine and profile before changing the limit. |
| `test_replay_batch.py::test_one_folder_per_run_and_manifest` | `calls[0]` was `None`, so indexing the environment failed | The test globally monkeypatches `subprocess.run`, records every call, and assumes the first is a replay child. Source-hash/Git fallback calls can occur in this snapshot without Git metadata. Filter mocks by the child command and validate its environment explicitly. This result alone does not prove replay isolation is broken. |
| `test_restricted_books.py::test_check_through_a_book_and_an_unknown_rule` | Expected `R-999: not a coded rule`, received `R-999: not in the register` | The rule API and assertion disagree. Unknown rules were rejected in both cases. Confirm the intended diagnostic contract and update its test or implementation consistently. |

The eight skipped tests and four expected failures remain unverified behavior. Review the unexpected-pass marker as a potentially outdated expectation. The suite predates later working-tree additions, including any new Conductor tests added after snapshot creation, so these counts do not certify the latest checkout.

Reviewed working-tree Conductor SHA256 was `39543EBE4DCBCC7A9C42C7D2BC78ACBA40210CC6C05AFBF57E9B04535F2773B6`. The snapshot manifest provides other baseline hashes. Recheck findings if the implementation hash has changed.

## Resolution — 8 November 2026, evening (Claude, approved by the owner)

| Finding | Status |
|---|---|
| F01 | **Fixed.** `Conductor.step`: a release (lapsed, rejected, unaffordable) falls through to the same step's admission; a still-pending or just-filled owner still returns early. Regression `test_release_admits_a_competing_trigger_on_the_same_step`. |
| F02 | **Open, labelled.** `apex/quant/params.json` is fitted 5 Nov on sessions through 4 Nov and used on every replay day. Any pool pair proposed on an HMM / Hawkes factor is flagged "model provenance not chronological" in the proposal; dated artifacts with `trained_through` are a docs/33 Wave 1 item. |
| F03 | **Fixed.** Pool rows take an optional inclusive `to` date; the latest `from` of a (book, rule) pair is its state as of the day; `pool_problems` validates `to`. Test `test_pool_rows_have_an_end_date_and_one_state_per_pair`. Manifest hashing of pool and register: open. |
| F04 | **Open.** Restart with a missing source position still closes at the remembered price marked stale. To do before any live restart mid-trade: integrity fault, separate "accounting adjustment" record, tests for restart / missing book / missing trade / immediate close. |
| F05 | **Fixed.** `scipy>=1.11` in `requirements.txt`; a failed QuantView import is now a start-up refusal with the import error (`engine_main.new_day`). |
| F06, F07 | **Open**, research quality (GEX cache cadence, flip sign on both sides). |
| F08 | **Deferred by the owner** for the 9 Nov account version; recorded in docs/28 §7. |
| F09 | **Closed by the owner:** the repository is public and the file is shared by the owner's deliberate instruction. |
| Mirror semantics | **Owner's intended design**, now stated in docs/28 §7. |
| Test failures | Restricted-books assertion already updated to "not in the register"; replay_batch mock failure needs Git metadata (present in the working tree); commentary timing failed under replay load. Full suite to be rerun on the quiet machine before tonight's commit. |

### Second pass, same evening (after the reviewer's three points)

| Point | Status |
|---|---|
| Pool retirement could revive an older row | **Fixed.** `active_entries` now picks the latest row that has begun for each (book, rule) pair FIRST, then applies that row's `to`: an expired latest row retires the pair, it never falls back to an older row. Test `test_an_expired_latest_row_retires_the_pair_and_never_revives_an_older_row`. |
| F02 needs enforcement, not a label | **Enforced.** `pool_builder.best_line` excludes HMM / Hawkes (`hmm_*`, `hk_*`) lines BEFORE choosing, so the next valid line on the same card is proposed; `--allow-fitted` admits them, flagged. Photographs and cards keep every field. Test `test_fitted_model_factors_are_excluded_before_the_best_line_is_chosen`. |
| F04 recovery | **Fixed.** A vanished source position with no closed trade is an `integrity` event; the account stays OPEN and marked unresolved (no exit at a remembered price) until a quote on its own contract fresher than `EXIT_QUOTE_STALE_S` exists; it then leaves at that quote as `adjustment: "recovery"`, logged as `adjustment`, and `score._ok_trades` leaves such trades out of every test. Capital is adjusted (the owner's gross accounting), the trade is never a scored exit. Test `test_missing_source_is_an_integrity_fault_then_a_flagged_recovery_exit`. |
| Priority basis | Every proposed pool entry carries `ret_basis: "discovery days (in-sample)"`; the dashboard view and the offline report state it; the forward figure replaces it as test days are scored. |
