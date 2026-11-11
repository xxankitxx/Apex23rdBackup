# Forecast implementation matrix: reply to docs/44

11 November 2026, 02:40. Claude's first reply to `docs/44_AMBITIOUS_FORECASTING_MODEL_ROADMAP.md`, as it asks: every
stage mapped to its status, files, data, computation and acceptance tests. Then the work itself, in sections 3 on.

**Nothing here is a model improvement yet.** M0 and M1 are plumbing and data. "No losing trade" is unmet.

## 1. Accepted corrections

| Point in docs/44 | Reply |
|---|---|
| Sampling more strikes is not sampling executable contracts | Correct. `build_origins_v2.py` is superseded by `research/predict/build_candidates.py`, which reconstructs the engine's selector and tags its pick. See section 3 |
| v2 dropped a whole timestamp near the chain edge | Correct. The new builder takes each candidate on its own and counts what is missing |
| Two matched trades are a smoke check | Correct. Full-batch reconciliation is an M0 item, done when the replay ends |
| Registry selection is not validation | Correct. `registry.pick` only filters by date today. Validation at load is an M1 item, not done |
| Do not launch another ten-way replay because the cores exist | Accepted. The ten-way run of this night was mine, was started before docs/44, and is starving the other work. No further wide replay will be started without a stated resource plan |
| Research code in dated run folders | New research code goes to `research/predict/`. Older scripts stay where they are as evidence |

## 2. The matrix

Status words: **done** (tested), **partial**, **running**, **not started**. Computation is on this machine, 8 cores.

| Stage | Deliverable | Status | Files | Data | Computation | Acceptance test |
|---|---|---|---|---|---|---|
| M0 | Exact-contract binding, full key through pending and fill | done in parts | `apex/engine/paper.py` (`bound_contract`, `fc_sig`), `apex/engine/pred.py` v2 | none | none | 13 tests in `tests/test_forecast_repairs.py` |
| M0 | End-to-end fixture: engine request, delayed fill, restart with a pending order, restart with a filled position | **not started** | to add: `tests/test_forecast_lifecycle.py` on the engine test rig | synthetic tape | minutes | pending order cancelled at restart, terminal record written, no later fill, no repeated signal number; filled position keeps `fc_sig` |
| M0 | Full-batch contract reconciliation | running | `research/audit_forecast_p41.py` logic on `p42_*` | `data/replay/batch/p42_*` | replay ends about 07:00 | every linked forecast-book trade on the scored contract, or each exception listed |
| M0 | Label parity live against offline | partial | `apex/predict/ledger.py` (`fill_by`), `targets.label` | one tape | about 15 min | live outcomes of sampled forecasts equal `targets.label` on the same seconds, or each difference explained |
| M0 | Latest full suite | running | `tests/` | none | 5 to 15 min | no failure, no error |
| M0 | Engine latency report | partial | feed timing in docs/43 section 7.2 | one tape | one idle day replay, 2.6 h | p50, p95, p99, max of the step and of the forecast feed on an idle machine, with 24 held contracts |
| M1 | Candidate table with executable tags, chain-edge repair | running | `research/predict/build_candidates.py` | `data/research/ds_v2` (15 sessions, have), output `origins_v3.npz` | about 25 min, 2 workers | manifest reports coverage, depth, delta and premium of the executable rows; selector agreement measured against real fills |
| M1 | Selector agreement | not started | to add: `research/predict/selector_agreement.py` | `p41_*` trades of default-selector books | minutes | share of real fills whose contract equals the reconstructed pick at the trigger second; quoted with every claim that uses the tag |
| M1 | Champion decision episodes | not started | to add: `research/predict/build_episodes.py` | `p41_*` and `p42_*` trades and `decisions_*.jsonl` of `c20_9y`; missed and rejected triggers need a replay with the recorder ON, **missing** | minutes for fills; one recorder-on replay for the rest | one row per causal trigger of the named policy, its own features at the trigger second, its own result under its own exits; sibling results in separate columns |
| M1 | Data-quality and support report | not started | `research/predict/data_quality.py` | the tables above | minutes | sessions, unique episodes, censoring, coverage by class, quote freshness |
| M1 | Validated registry | partial | `apex/predict/registry.py` | `apex/predict/registry.json` | none | at load: file exists, content hash, embedded cut-off equals the registry's, schema, target; a mismatch gives an explicit unavailable state. Live-published and historically simulated artefacts told apart |
| M2 | Chronological logistic baseline | running, on v2 data | `data/replay/batch/predict_2026-11-10/fit_chrono.py` | `origins_v2.npz` now, `origins_v3.npz` next | about 20 min | each session scored by a model fitted on earlier sessions only |
| M2 | Activity-only baseline | not started | `research/predict/` | `origins_v3` | minutes | premium, expiry, spread, realised volatility only |
| M2 | Coherent competing-risk hazards | not started | `apex/predict/hazard.py`, trainer in `research/predict/` | `origins_v3` | minutes | probabilities coherent by construction; proper scores against the logistic and the activity baselines, chronological |
| M2 | Premium-return quantiles | partial | `apex/predict/ranges.py`, `ranges_v1.json` | `origins_v3` | minutes | ordered quantiles, coverage and width by day type, chronological |
| M3 | Champion admission | not started | after episodes | episodes | minutes | residual question first: does weather add anything beyond "the champion triggered"; frontier of coverage, profit and missed runners |
| M3 | Enter or wait | not started | after episodes | episodes plus tape paths | minutes | against a same-length delay with no forecast |
| M3 | Continuation | not started | to add: held-state snapshots | `c20_9y` positions second by second from the tapes | about 30 min | incremental value against selling at the bid now; never the best future price |
| M4 | Greek scenarios, sequences, specialists, analogs | not started, except `ranges_greeks2.py` | | | | only against M2 and M3 baselines |
| M5 | Single-mechanism shadows; Conductor with and without a candidate | not started | | | one Conductor replay pair per candidate | rupee equity, drawdown, displacement. Never a stand-alone sum |
| M6 | Forward package | not started | | sessions after 11 Nov | | frozen control beside any adaptive challenger |

## 3. M1 finding: where the executable contract sits. Corrected after the full build

**Correction.** The first version of this section reported one recorded part of one day (29 Oct, part 4): 853 of 890
executable picks outside the depths the old model was fitted on. That does not generalise. The full build says:

| Depth of the engine's pick, from the forecaster's at-the-money strike | Share of 103,995 executable picks, 15 sessions |
|---|---|
| One strike out of the money | 6.1 % |
| At the money | 21.2 % |
| One strike in | 31.3 % |
| Two strikes in | 32.5 % |
| Three strikes in | 8.6 % |
| Four strikes in | 0.4 % |
| Deeper | none |

- **52.4 % of executable picks are at the depths `model_v1` and `model_v2` were fitted on. 47.6 % are not.**
- It varies a great deal by session: 99 % at the old depths on 21, 22 and 23 Oct; 11 % on 26 Oct; 17 % on 29 Oct.
- **Feature overlap, not only depth.** Against the middle 99 % range of each feature in the old training data:
  of the picks at other depths, 97 % have their moneyness outside that range, and **no other feature** is outside
  it for more than 2 % of rows. Of the picks at the old depths, 11 % have some feature outside, which is the
  reference level (the old data against its own range gives 14 %). So the gap is real, it is about moneyness, and
  it is about half the picks, not nearly all.
- The cause stands: the forecaster's "at the money" follows the index future, the engine's delta follows the parity
  forward of the weekly options.
- Evidence: `data/research/predict/origins_v3.manifest.json`, `data/research/predict/support_overlap.json`.

## 4. Order of work from here

1. Finish M0: full suite result, batch reconciliation, the end-to-end fixture, label parity on a tape.
2. Finish M1: candidate table, selector agreement, episodes of `c20_9y`, data-quality report, registry validation.
3. M2 on `origins_v3`: activity baseline, chronological logistic, hazards, quantiles. Report or reject.
4. M3: admission residual model and continuation labels for `c20_9y`.

Sections are added below as each item lands, with files, hashes, tests, numbers and failures.

---

## 5. M0 evidence (11 Nov, 03:20)

| Item | Result | Evidence |
|---|---|---|
| Full suite, idle machine, latest code | **537 passed, 8 skipped, 4 expected failures, 1 unexpected pass, no failure, no error**, 4 min 20 s | run at 03:16. An earlier run beside ten replays had one timing failure and one fence error; both were load |
| End-to-end order fixture | 3 tests through the real `evaluate_entry`, `choose_contract`, `request_entry`, `try_fill_entry`: a delayed fill on the scored contract; a restart with the order pending (order gone, nothing fills later, one terminal record, the next signal has a new number); a restart with the position open (forecast identity and bracket kept) | `tests/test_forecast_lifecycle.py` |
| Fault the fixture found | After a restart a forecast whose order had filled was marked as an orphan. Fixed: a fill resolves it | `apex/predict/ledger.py` |
| Batch contract reconciliation | The ten-day replay was stopped on the owner's instruction after about one market hour per day. On its trades: **111 linked forecast-book trades, 0 on another contract** (before the repair: 86 to 94 % on another contract). One market hour of ten days, not full sessions | `data/replay/batch/p42_*` |
| Label parity live against offline | Rule aligned (fill at the next second or none). **Not checked on a tape** | open |
| Engine latency, idle | Partial. One process alone, 9 Nov tape, 25 min wall, to 10:24 market. Logged minutes 09:16 to 10:05: median step 28 ms, 95th percentile 97 ms, 6 steps over 300 ms, one step of 1,241 ms. The idle run before the repairs, same tape and hour: 30 ms, 128 ms, 33 steps over 300 ms. **No slowdown seen from the repairs in the first market hour.** Only 5 minute-lines were logged, the afternoon is not covered, and the forecast feed's own percentiles are not separated | scratch logs, not kept in the repo |

## 6. M1 evidence

### 6.1 Candidate table `origins_v3`

`research/predict/build_candidates.py`, 20 min with 2 workers. 648,026 rows over 54,018 moments in 15 sessions;
103,995 rows are executable picks. No moment was dropped at the chain edge (0 missing). 4,038 side-moments had no
executable contract (cut-off or nothing in band). The out-of-band fallback fired 5 times. Executable delta: 5th to
95th percentile 0.52 to 0.74, median 0.56. Executable premium: 85 to 213, median 169.

### 6.2 Selector agreement, stage by stage

`research/predict/selector_agreement.py` against the 17 signal books of the 15-day replay, which used the default
rule at the trigger and carried that contract's key through the pending order to the fill.

| Stage | Result on 8,796 fills |
|---|---|
| Reconstructed pick at the trigger second equals the traded contract | 8,649, **98.3 %** |
| Equal at the trigger second or one second either side | 8,749, 99.5 % |
| Off by one strike at the trigger second | 147 |
| Off by more than one strike | 0 |
| No reconstructed pick | 0 |
| Delta of the traded contract, reconstruction against the engine's value at the fill | median difference 0.0007, 95th percentile 0.006 |

By session the agreement is 97.5 % to 99.2 %. Four fills had a trigger second outside the recorded set. The tag is
a close reconstruction, not an exact replay; claims that rest on it carry this 1.7 %.

### 6.3 Champion episodes, executed only

`research/predict/build_episodes.py c20_9y`: 92 fills on 15 sessions, each with its own trigger second, contract and
result under its own exits. 69 have the forecaster's features at the trigger second (23 fell in the warm-up or had
no two-sided quote). 54 profitable, 70 gained 5 % at some point, 20 runners (20 % or more).

**The champion does not use the default delta rule.** Its strategy names its own strike: depth one out 1, at the
money 13, one in 33, two in 20, three in 2. Delta 0.53 to 0.71.

The forecast-style label against the champion's own result, same 89 labelled trades:

| First event within 300 s of the trigger | Trades | Profitable | Runners | Rupees | Mean return |
|---|---|---|---|---|---|
| +5 % first | 35 | 25 | 12 | +8,84,449 | +18.5 % |
| -5 % first | 49 | 23 | 6 | +2,31,962 | +3.4 % |
| Neither | 3 | 2 | 1 | +40,388 | |
| Unobservable | 2 | 2 | 0 | +5,896 | |

- **"+5 % before -5 %" is the wrong target for this policy.** 49 of 89 trades dipped 5 % first; that group still
  made money and held 6 of the 20 runners. A gate on that label would have removed them.
- The label is informative all the same: the +5 %-first group earned about four times as much on fewer trades.
- In-sample, executed trades only. **Missing: every trigger the policy did not trade.** No admission model is fitted
  until a recorder-on replay supplies them. That replay is not started; it needs the owner's go-ahead and a size.

### 6.4 Registry

`apex/predict/registry.py` `validated()`: file present, content hash equals the file's and the registry's, embedded
cut-off equals the registry's and is before the session, else an explicit unavailable state. One test. The 11
artefacts written tonight by `fit_chrono.py` are on the **superseded v2 data** and are interim; the engine does not
load them. Their availability on past days is simulated, and the registry says so.

## 7. M2: three baseline forecasters on unseen sessions

`research/predict/m2_compare.py`, output `data/research/predict/m2_compare.json`. Roster and protocol fixed in the
script before the run. Ten test sessions (27 Oct to 9 Nov); for each, standardisation, fit and the top-5 % line come
from earlier sessions only. One l2, no feature selection, no threshold search. The contracts of one moment share
one unit of weight. These 15 sessions have been studied before; this is historical research, not forward proof.

Executable population, means over the 10 sessions. The difference is against the activity-only baseline, with a
paired day-block 90 % interval.

| Measure | Activity only | Hazard | Deployed logistic method |
|---|---|---|---|
| Three-way log loss at 300 s, lower is better | 0.9694 | 0.9704, +0.0011 [-0.003, +0.005], better on 4 of 10 | 1.0245, **+0.055 [+0.009, +0.110]**, better on 1 of 10 |
| Three-way Brier | 0.6021 | 0.6029, better on 3 | 0.6071, worse, better on 2 |
| Activity AUC, any 5 % event | 0.605 | 0.612, +0.007 [-0.005, +0.020] | 0.611 |
| Direction AUC given an event | 0.5005 | **0.5385, +0.038 [+0.008, +0.071]**, better on 8 of 10 | **0.5426, +0.042 [+0.012, +0.075]**, better on 9 of 10 |
| Top 5 % by edge: origins | 3,098 | 4,601 | 5,054 |
| Top 5 %: up first against down first | | 45.1 % against 43.2 % | 40.3 % against 40.8 % |
| Top 5 %: mean 300-s return, ask in, bid out | -0.48 % | +0.22 % | +0.20 % |
| Top 5 %: sessions with a positive mean | | 6 of 10 | 5 of 10 |

What it says:

1. **Knowing that a move is coming is not skill beyond the obvious.** Premium, spread, expiry, time of day and
   realised volatility already give it. Neither full model beats that baseline on a proper score.
2. **There is a small, repeatable direction signal.** Given that a 5 % event happens, both full models rank the
   side at 0.54 against 0.50, with the interval clear of zero, on 8 or 9 of 10 sessions. It is small.
3. **The deployed method is badly calibrated out of sample.** Eight separate models and a projection lose to the
   activity baseline on log loss on 9 of 10 sessions. The coherent hazard model has the same direction skill
   without that damage. **The hazard model replaces it as the baseline.** `model_v2` should not be trusted for
   probabilities.
4. **The top-edge slice is weak.** Up-first leads down-first by two points and the mean 300-s return is +0.22 %,
   positive on 6 of 10 sessions. That is not a trading result. The activity baseline's own top slice is negative,
   so the gain is from direction, not from picking busy moments.
5. On the broad population the picture is the same, and the direction interval there includes zero.

Failed or not shown: no model improves proper scores; the deployed logistic method is rejected as a probability
model. Not done in M2: return quantiles on v3, and scores by expiry, premium and support.

## 8. Freeze

`research/predict/freeze.py` appends the time and the content hashes of every file that decides a forecast or a
forecast-book trade to `apex/predict/freeze_log.jsonl`; `--check` lists what changed since. A session is forward
evidence for a package only if it opened after the freeze and the check is clean at its end. The package frozen
before the 11 Nov open is the repaired one with `model_v2`: its weights saw all 15 sessions to 9 Nov, so 11 Nov is
its first unseen session. It is the **old** probability model; the hazard baseline is not in the engine.

## 9. Next

1. With the owner's go-ahead: one recorder-on replay to capture the champion's untraded triggers, sized in advance.
2. Continuation snapshots for `c20_9y` from the tapes (no replay needed): held state against selling at the bid.
3. Hazard model as a frozen artefact behind the forecaster interface, chronological, then shadow-only.
4. Idle latency and label parity on one tape.

---

## 10. Reply to docs/46 (11 Nov, 08:30, before the open)

All five findings were checked and hold. Three are fixed and tested now. Two are deliberately left until after the
session, with the reason.

| # | Finding | Status | What was done, or why not |
|---|---|---|---|
| 1 | A stale signal stays actionable after the current forecasts are gone | **Fixed** | Two guards. The forecaster withdraws every live signal in any second it has no current forecast (`Pred._silent`). And `paper.evaluate_gen` accepts a forecast-book signal only if the forecaster updated within 1.5 s and still has a forecast for that exact contract; otherwise "signal dropped" with the reason. A pending order that already exists is unchanged: it fills on the first print after its trigger or lapses, as every book's does |
| 2 | At-the-money at the chain edge silences everything | **Fixed** | Only the neighbours that exist are taken; buyable and held contracts are scored independently. Tested at both ends, including the panel |
| 5 | "Published" inferred from a truthy field | **Fixed** | `published` must be a time `YYYY-MM-DD HH:MM:SS` before that session's 09:15 open. Anything else, including a later time, is reported as simulated availability |
| 3 | A path that ends before the horizon is labelled "neither" | **Not fixed today** | It is real: `targets.label` gives "neither" when the recording ends inside the horizon. The fix changes the target specification, and the engine refuses a model fitted on another specification. Changing it 45 minutes before the open would silence the forecaster for the day. After the session: new target version, rebuild `origins`, refit, and count the affected rows (origins in the last 300 s of each recorded part) |
| 4 | The validated registry is not wired into engine start | **Not fixed today** | True: the engine loads `config.PREDICT_MODEL` directly. Today that is `model_v2`, fitted through 9 Nov, so today is unseen for it. Wiring needs the two loading modes docs/46 asks for (chronological, discovery) and a test of the hash chosen per session. Not a change for the last hour before a session |

Tests: 3 more in `tests/test_forecast_repairs.py`. Full suite on the idle machine at 08:30: **543 passed, 8 skipped,
no failure, no error.** Freeze re-recorded after these changes; finding 1 and 2 touch the forecast books' entry
path and the forecaster, shadow only. The champion, the pool and the Conductor are untouched.

Effect of finding 3 on what is already reported: the "neither" share in `origins_v1` to `v3`, and so every M2 score
in section 7, includes rows from the last 300 s of a recorded part that should be unobservable. Not yet counted.
