# Forecast correctness review during live-session preparation

11 November 2026. Codex follow-up. Scope: current forecast service, outcome labeling, artifact loading, engine entry integration and forecast UI. No trading settings or runtime source were changed, no service restarted, and no full suite/replay launched. This is not certification of the entire repository.

## Findings

### 1. P1: A stale signal remains actionable after current forecasts become unavailable

`apex/engine/pred.py`: `update` clears current forecasts but preserves `sig`; `_silent` updates explanations only. `apex/engine/paper.py:evaluate_gen` accepts a saved signal for 1.5 seconds without checking whether the current forecast update invalidated it.

Reproduced using the existing synthetic `tests/test_pred.py:Tape`, without ledger/files: warm the service, advance until p02_clock issues a signal, then advance one second with option quote age 9 seconds. Result:

```
reason: no contract with a fresh two-sided quote
current_forecasts: 0
evaluate_gen accepted: True
```

The whole-engine blackout gate protects against a global blackout. The option-quote reproduction does not require one: the forecaster's freshness criterion is stricter than the bound selector's 15-second quote limit. The reproduction proves evaluator acceptance, not that a particular live trade was filled. A fresh later print and other entry conditions still govern the actual fill.

Fix: give signals explicit validity tied to the current prediction snapshot; invalidate on unavailable/stale current inputs, and check the exact contract forecast at admission. Define whether an already-created pending order should cancel when its forecast becomes invalid; implement and test that policy separately. Preserve historical `fired` records for attribution. Add a regression where a signal is initially unconsumed, the next update has stale option data, and no new request is admitted.

### 2. P2: Chain-edge ATM suppresses otherwise valid executable and held forecasts

`apex/engine/pred.py:update` returns when ATM index is 0 or the last index, before considering explicitly requested contracts. This is the runtime counterpart of the previously identified builder boundary exclusion.

Reproduced on the five-strike synthetic chain with the future at the lowest strike:

```
ATM index: 0
Features.contract(0, CE) available: True
contracts scored: 0
reason: the at-the-money strike is at the edge of the recorded chain
```

Fix: enumerate only in-bounds optional nearby candidates, then union executable/pending/held candidates independently. Missing one neighboring strike must not disable all valid contracts. Add boundary tests for both ends, including held options and the case where the optional opposite-side neighbor is absent. Expose per-contract missing reasons.

### 3. P1: Incomplete terminal paths are labeled as a completed non-event

`apex/predict/targets.py:label` uses `data_end < h - max_gap` to identify right censoring. If the tape ends within ten seconds of a horizon, it labels no observed barrier as `N`, even though that horizon was not fully observed.

Reproduced with seconds 0..296, entry at second 1, flat quotes and no gaps. Only 295 seconds after entry are observed; `first[300]` is `N`. A barrier in the unobserved last five seconds remains unknown. The documented target explicitly describes an ended path as unobservable.

Fix: distinguish tolerated internal quote gaps from a terminal observation window that ends before the horizon. A non-event requires observation coverage through the horizon; otherwise label `U` unless the first event already resolved it. Define endpoint-return staleness separately from first-passage observability. Check analogous live end-of-session behavior and rebuild affected labels/calibration artifacts under a new target version. Quantify affected rows before comparing model scores.

### 4. P2: Validated chronological registry is not connected to engine startup

`apex/predict/registry.py:validated` exists and checks hashes/cutoffs, but current engine day initialization constructs `Pred(config.PREDICT_MODEL, ...)` directly. `config.PREDICT_MODEL` still points to `model_v2.json`; no runtime caller of `validated` was found in the inspected source.

Consequence: creating or testing the registry does not make engine replay use dated models. The current 11-Nov session is later than model_v2's 9-Nov cutoff, so this is not a claim that today's model contains today's future data. It is a disconnected enforcement path affecting historical replay and future artifact management.

Fix: introduce explicit chronological versus discovery loading modes, call validation from the actual startup path, and test the engine-selected hash for each session. Never silently fall back to the all-days model when no chronological artifact exists. Range artifacts need independent provenance too.

### 5. P2: Publication status is inferred from a truthy field, not its timestamp

`registry.validated` says "published before a live session" whenever `row['published']` is nonempty. It does not compare the timestamp with the decision/session boundary. A later publication can therefore receive a false availability label.

Fix: parse and validate publication/effective timestamps against an explicit as-of boundary, or label the field merely as a recorded publication timestamp without claiming prior availability. Include timezone and distinguish simulated historical artifacts from genuinely available ones. This does not supersede training/calibration cutoff validation.

## UI recheck

The previous headline and held-only cases are corrected: `forecastHeadline` compares favorable first-event probabilities, distinguishes zero executable sides and describes raw threshold crossing without claiming action. Range labels now identify estimated 10th–90th percentiles and describe current-ask conversion as approximate.

Ran `node tests/js/forecast_headline_test.js apex/static/app.js`: all five checks passed. `node --check apex/static/app.js` passed. The first invocation of the headline test omitted its required filename argument and failed; rerunning with the required argument passed. These checks do not measure browser rendering performance or certify the whole live engine.

## Next actions for Claude

Fix signal validity and right-censoring first, then chain-edge coverage. Wire registry validation into the engine with explicit discovery-mode behavior and fix publication labeling. Add focused regression tests and quantify historical effect; do not change live processes blindly or claim that these source findings explain a specific live loss without ledger evidence. After-session testing should include the full suite and matched replay manifests. Keep raw tapes and old artifacts intact.
