# Why the replay combinations still lose — report for Claude

Audit date: 9 November 2026. Scope: the frozen reports and saved trades under `data/replay/batch/v3_cards_2026-11-08` and the 14 associated `v3_<day>` runs. This is an analysis of the reported experiment, not a certification of the entire engine. No trading code, registered rules, pool membership, or existing replay outputs were changed.

## 1. Direct answer to the owner

The rules did **not** select only profitable trades. They selected subsets with better average outcomes, sometimes with fewer than half the trades winning. The family pool also contains unrestricted books. Consequently, losses were present in the inputs before the Conductor combined anything.

The composition then changes which trades fit into the account and the capital available for later trades. This explains why adding individually profitable filtered books can reduce the combined account's profit.

All five published combinations made money **over the complete 14-day sample**. None eliminated losing trades or losing days. These are different statements and must be reported separately.

Under the stated gross paper mechanics, if every admitted source trade had `exit > entry`, with positive quantity and unchanged entry/exit prices, its P&L would necessarily be positive. Combining such trades could reduce opportunities, but could not manufacture a negative realized trade. The actual admitted source trades fail that premise. This is demonstrable directly from the saved records.

The owner's zero-loss objective has not been achieved. Do not quietly replace it with positive mean return or a better win rate. Conversely, do not claim that retrospective winner selection would prove that future trades cannot lose.

## 2. What I independently verified

I built a standard-library reconstruction of the offline closed-trade account. It reads saved trades, uses the published discovery priorities and two exact thresholds, follows the account's occupancy logic, and applies daily ₹100,000 starting capital, whole lots of 65, all-in sizing, and gross P&L. It does not rerun market tapes or import the live engine.

**Every A–E aggregate and all 70 pool/day trade counts and P&Ls match the published `sim_summary.json` to the paise.** Thus the headline losses are reproducible, not an arithmetic discrepancy in those tables.

Artifacts:

- `data/replay/batch/v3_cards_2026-11-08/codex_audit/reconcile.py` — reproduction and diagnostic ablations.
- `.../codex_audit/reconciliation.json` — selected trades, blocked candidates, exact daily attribution.
- `.../codex_audit/ablations.json` — additional in-sample configurations.

Run from repository root: `python data/replay/batch/v3_cards_2026-11-08/codex_audit/reconcile.py`.

This verifies the published **offline simulator's** calculation. It does not establish full parity with live event replay: `apex/conductor/account_sim.py` itself documents that lapsed pending entries leave no closed trade and are invisible to this simulation. Preserve this qualification.

## 3. The actual selection objective differs from the requested outcome

`apex/conductor/search.py` scores `kept win rate - other-side win rate`. Its better-side check requires a positive score and better mean return. Other checks cover sample size, retention of large winners, neighbouring thresholds, and the shuffle benchmark. None requires zero kept losses.

`apex/conductor/pool_builder.py::best_line` requires the luck flag, minimum retained evidence, and positive retained mean; it ranks score and retained return. It does not require a 100% win rate or zero losing days.

The actual proposal says:

| Pair | Exact entry filter | Retained discovery win rate | Retained mean return |
|---|---|---:|---:|
| edge_bracket_only / R-019 | `opt_vol1 < 2768805.0` | 49.06% | +2.8222% |
| edge_breakout / R-020 | `vomma >= 0.00646` | 46.43% | +1.7007% |

These are improvement filters that explicitly retain many losers. A positive average can coexist with a minority of winning trades when the winners are larger.

The fractional 79.5 retained observations in the first card are weighted discovery evidence, including counterfactual rows. They are not 79.5 executable trades. The card's cleaned 13-day real-trade sample, weighted search sample, full 14-day saved-trade sample, and account-selected sample have different denominators. Always show them separately.

Pool B is the unrestricted `c20_9y, c20_9s, c20_9v, c20_9x, c20_9t` family. Its constituents were not restricted to historical winning trades. The existing R-001–R-018 variants, new R-019/R-020 proposal, and subsequent team's exploratory rules are separate experiments. Do not imply the team’s rules produced the A–E results.

## 4. What the combinations actually achieved

| Configuration | Trades | Wins | Losses | Win rate | Gross P&L | Losing days |
|---|---:|---:|---:|---:|---:|---:|
| A: 9x alone | 81 | 43 | 38 | 53.09% | ₹1,004,809.00 | 4/14 |
| B: unrestricted family | 89 | 49 | 40 | 55.06% | ₹1,044,251.00 | 4/14 |
| C: B plus two filtered edge books | 149 | 74 | 75 | 49.66% | ₹865,081.75 | 3/14 |
| D: two filtered edge books alone | 111 | 56 | 55 | 50.45% | ₹351,656.50 | 3/14 |
| E: B plus 8x, 9e, 9h | 95 | 50 | 45 | 52.63% | ₹950,966.25 | 4/14 |

Adding the two pairs to B produced a **net 60 additional trades, 25 additional wins, 35 additional losses, and ₹179,169.25 less profit**. Losing days fell from four to three; that improvement does not erase the deterioration in trade losses and total profit.

These rupees are sums of 14 independently funded daily accounts. They are not the result of one ₹100,000 balance compounded continuously across all days.

## 5. Exact explanation of C's deterioration

Match B and C trades by day, source book, trigger, entry/exit timestamps, and contract. Of B's 89 trades, C retains 65 and displaces 24; C adds 84 edge trades.

| Contribution to C minus B | Amount |
|---|---:|
| P&L from 84 newly admitted trades, at C's sizes | +₹105,010.75 |
| Remove P&L of 24 displaced B trades, at B's sizes | −₹217,330.75 |
| Different sizing on the 65 shared trades | −₹66,849.25 |
| **Net change** | **−₹179,169.25** |

This is an exact accounting identity, not an assertion that deleting one trade leaves every later decision unchanged. The additional books make positive net contributions on their selected trades, yet occupy time slots that were worth more to the family and change later sizing. The standalone ₹351,656.50 from D cannot simply be added to B.

### Concrete collision: 6 November

In B, 9y buys the 24750 CE at 14:09:29 for 190.55 and exits at 15:20 for 327.00. Nine lots yield **₹79,823.25**.

In C, edge_bracket_only has already entered at **14:08:58** and holds until **14:30:57**. Its trade earns ₹19,682, but the account is occupied when the larger family opportunity triggers. Another family winner worth ₹5,564 in B is also displaced that morning. Along with sizing changes, the day falls from **₹100,233.25 to ₹20,475.00**.

This is the approved one-account mirror design operating as specified. A priority ranking at simultaneous triggers does not protect a high-priority trade that arrives after another book has entered. Improving this requires a separately tested admission/reservation or ownership policy; it is not a reason to silently change the owner's approved semantics or deferred protected phases.

### Concrete filter failures: 5 November

All five selected C trades come from the filtered edge books:

| Entry time | Book / rule | Actual feature value | Entry → exit | Account P&L |
|---|---|---:|---|---:|
| 09:36:46 | bracket / R-019 | volume 531,570 | 183.05 → 163.80 | −₹10,010.00 |
| 09:50:33 | breakout / R-020 | vomma 0.0176 | 184.85 → 166.25 | −₹8,463.00 |
| 10:03:16 | breakout / R-020 | vomma 0.0228 | 183.85 → 185.00 | +₹448.50 |
| 14:16:51 | bracket / R-019 | volume 605,930 | 183.05 → 166.80 | −₹6,337.50 |
| 14:33:26 | bracket / R-019 | volume 284,180 | 182.40 → 181.90 | −₹195.00 |

Every value satisfies its filter. Net: **−₹24,557.00**. The filters were applied; they did not distinguish these losses.

The 09:50 breakout has a recorded favourable peak of +14.6 premium points before closing at −18.6 points. That is worth an exit-path investigation. It does **not** justify choosing the retrospective peak as an attainable exit: a replacement exit must trigger using only observations available then and fill under the same execution rules. Other losers barely moved favourably, so a universal profit-taking change is not established by this example.

## 6. Additional finding: standalone strength hides bad residual trades

Pool B's selected contributions are:

| Source | Selected trades | Wins | Losses | P&L at B's sizes |
|---|---:|---:|---:|---:|
| c20_9y | 71 | 43 | 28 | +₹1,136,892.25 |
| c20_9s | 10 | 0 | 10 | −₹124,634.25 |
| c20_9t | 7 | 5 | 2 | +₹22,984.00 |
| c20_9v | 1 | 1 | 0 | +₹9,009.00 |
| c20_9x | 0 | 0 | 0 | ₹0.00 |

Most shared favourable opportunities are already owned by higher-priority books. What remains for a lower-priority book can be a very different distribution from its standalone history. Selecting books by their overall mean does not test this conditional contribution.

Diagnostic ablations, performed after seeing these results and therefore **strictly in-sample**:

| Configuration | Trades | Wins | Losses | P&L | Losing days |
|---|---:|---:|---:|---:|---:|
| 9y alone | 72 | 44 | 28 | ₹1,137,308.25 | 4 |
| B without 9s | 89 | 53 | 36 | ₹1,098,321.25 | 3 |
| B without 9x | 89 | 49 | 40 | ₹1,044,251.00 | 4 |

Removing 9s improves B by ₹54,070.25 while preserving trade count: replacement ownership matters. Its −₹124,634.25 contribution is not the exact removal benefit. Removing 9x changes nothing in this sample because it owns no trades. 9y alone earns ₹93,057.25 more than B, with 17 fewer trades and 12 fewer losses.

Therefore “B beats 9x” is an incomplete assessment. Compare with the strongest individual member, the account's marginal additions, and an opportunity/quality frontier. These diagnostics do not authorize removing a book or selecting the best hindsight configuration for deployment.

## 7. Assessment of the team report

The team correctly reports that none of its candidates removes losses to near nil. Rejecting attractive discovery fits after rechecking them is appropriate. Full-search shuffle checks and excluding chronologically invalid HMM/Hawkes inputs are improvements.

However, its written acceptance standard does not enforce the owner's objective. It allows discovery losses and requires only an improved/equal holdout win rate plus an unprofitable removed side. Four listed candidates have negative kept holdout P&L: **−₹7,312; −₹24,856; −₹15,730; −₹2,298**. They can pass that standard while losing money. “Passed statistical screen” must never be presented as “meets the no-loss requirement.”

The family agreement lead is potentially useful but limited:

- For 9y, `agree_same >= 7` keeps **57 trades, 41 winners and 16 losers** over all 14 days.
- The striking **12 trades / 12 losses** pattern is specifically `agree_same == 6`. The threshold `>= 7` also excludes three winners with agreement 5 or 1. These are different hypotheses.
- Its holdout benefit removes only one 9y loss; seven holdout losers remain. The 9s observations overlap heavily, so they are not independent replication.
- The value depends on book evaluation order and counts current/previous-step activity. A threshold usable by late-evaluated 9y cannot be transplanted to early-evaluated 9x.
- Log explicit per-member state: veto, busy, stale, unavailable, or affirmative. Do not treat every absence as an informed veto. A same-step simultaneous-vote design requires a separately versioned causal implementation and replay.

The full-width recheck p≈0.347 is appropriately less convincing than the single-feature p reported as 0.000. A zero exceedance count in a finite shuffle experiment is not a literal zero probability. Repeated nightly searches also need a recorded testing policy; “another 15–20 cases” is not by itself an automatic promotion criterion.

## 8. Reporting and evidence corrections

1. **Incorrect win-rate description:** REPORT says adding the pairs “roughly halve[s] the win rate.” B→C is 55.06%→49.66%, a 5.39 percentage-point decline, not a halving.
2. **Incorrect count:** C beats A's daily P&L on six dates (19, 22, 23, 30 Oct; 2, 4 Nov), not three.
3. **Discovery date typo:** `rule_lab.split_days` takes the first ten actual replay days, ending **2 November**, not 30 October. Holdout is 3–6 November.
4. **Overstated impossibility conclusion:** “not separable by anything recorded, nor any arithmetic” exceeds what finite threshold/combination searches establish. Correct wording: no tested rule demonstrated the required performance with convincing evidence under this experiment. This does not prove every sequence model, exit policy, or future hypothesis fails; it also does not imply more models will solve the problem.
5. **Experiment-level multiplicity:** 2 nominal card passes among 57 searched books, against 2.9 expected at 5%, is not strong evidence of a useful discovery. That expectation is not proof those particular two rules are false. Account for selection across books/search families as well as thresholds inside each search.
6. **Holdout qualification:** the last four dates are held out within the team's stated discovery split, but were already available to earlier full-sample analysis and family selection. Do not call them globally untouched prospective evidence.
7. **Different populations:** publish the exact exclusion reasons, missing-feature counts, weighted counterfactual counts, and real-trade counts for each stage. The card cleaning path and saved-trade/team paths do not share one identical population.
8. **Different accounting:** team's retained/removed source-rupee sums describe original book trades. They are not an all-in filtered-account replay. Recompute sizing and occupancy before making account-level claims.
9. **Mixed source versions:** REPORT discloses two source hashes and 86/87 books across the two batches. Establish that selected source-book behaviour and relevant features are invariant to these differences, or regenerate a homogeneous comparison. Do not assume either universal invalidity or equivalence.
10. **Actual versus hypothetical Conductor:** FULL_REPORT's Conductor row has zero trades. A–E are separate hypothetical offline accounts, not that row's live replay record.

## 9. Instructions for the next implementation/research pass

### A. Make the requirements visible in every result

Report losing trades, losing days, retained winners, rejected winners, opportunity coverage, P&L, and account occupancy together. Label the zero-loss objective **not met** whenever any evaluated trade/day loses. Report a zero-loss retrospective subset as an in-sample observation only. Do not introduce an arbitrary loss budget or trade quota on the owner's behalf.

Separate statuses: hypothesis, statistical screen passed, account benefit demonstrated, forward evidence, and owner objective achieved on a specified observed window. None is a synonym for a guarantee about unseen trades.

### B. Add a complete decision and loss ledger

For each candidate record the as-of feature snapshot and age, model training cutoff, book state, rule/version and result, arbitration decision, pending/fill/exit events, source prices, account quantity, realised outcome, and all competing triggers. Carry blocked and lapsed entries too.

For every loss, distinguish data/implementation error, admitted losing setup, adverse move before any useful profit, profit giveback, delayed execution, and composition displacement. These are diagnoses to test, not labels inferred solely from a future peak. Produce matched examples of winners with the same proposed rejection condition.

### C. Evaluate books where the account actually uses them

For each prospective addition run: baseline, candidate alone, baseline+candidate, baseline−candidate, fixed-priority alternatives, selected-versus-blocked performance, and the exact displaced/shared/sizing decomposition above. Keep source strategy state machines unchanged for this approved mirror experiment.

Freeze the configurations before the next evaluation window. Show a frontier of opportunities versus losses and profit rather than a single hindsight-maximised scalar. Specifically investigate the ten selected 9s losses and the 24 family trades displaced by C; do not promote a rule from those exact identities.

### D. Study entry, exit, and occupancy separately

Freeze entry sets while comparing causal exit policies. Then freeze exit policies while comparing entry gates. Finally replay full account interactions. Test adverse/favourable excursion timing from the tape, not just end-of-trade peak fields. Every proposed faster exit must also show which large winners it cuts short.

Model trajectories can be useful research inputs: persistence of flow, decay of momentum, IV/Greek changes, and deterioration after entry. The current evidence does not establish that another static Greek threshold will solve the losses. Keep new features causal, dated, and measured for compute cost; research search work need not run in the trading hot path.

### E. Strengthen validation without rewriting results

Freeze and hash input tapes, source tree, register, pool, parameters and search configuration. Use dated model artifacts. Separate discovery, validation and genuinely subsequent forward windows; retain the full candidate-search history. Consider day/episode dependence in shuffle or resampling tests rather than treating overlapping sibling trades as independent observations.

Require an event-level offline/live parity check covering pending lapses, competing triggers, fills, exits, and affordability before attributing live outcomes to a closed-trade simulator. Produce machine-readable trade-level simulations with every report so this reconciliation is routine.

### F. Preserve useful experiments without overstating them

Keep R-019/R-020 and agreement/veto hypotheses as separately identified research/shadow comparisons when desired. The observed C result does not support presenting the two edge additions as a proven improvement to B. B itself remains experimental and fails the zero-loss objective. The owner has already authorized experimental paper operation; this report adds no new approval gate.

The immediate priority is to fix the mismatch between the stated goal, selection criteria, and account evaluation. More sophisticated models should earn a place by improving a frozen account-level comparison, not by increasing the number of available indicators.
