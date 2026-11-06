# Apex — point-by-point response to the reviews (6 Nov 2026)

For the reviewers of `reviews/` (ChatGPT `chatgpt_5th_advanced.txt` / `Apex_Quantitative_Teardown.docx`, DeepSeek
`deepseek_5th.txt` and `deepseek_5th_advanced.txt`). Every recommendation is listed with what was done, where it
lives, how it was tested, the result, and why it is or is not used in trading decisions.

## How to read this

**Status labels**

* **DECIDES** — in the live decision path (the champion c20_9x or the shadow c20_9y).
* **REJECTED** — built and tested as a trading rule; it lost money or failed the robustness checks, so it does
  not decide. The code stays in `apex/quant/` for re-testing as days accumulate.
* **DISPLAY** — built and running live on the dashboard ("Quant evidence" panel, `apex/engine/quantview.py`),
  but never tested as a trading rule. These are open gaps, not verdicts.
* **NOT BUILT** — no code exists. The reason is given; where the reason is "omitted", the item should have been
  done and was not.
* **EXCLUDED** — left out on the owner's instruction.

**The owner's fixed rules, which constrain several recommendations.** Buy-only Nifty weekly options; paper
trading; **all-in on every trade, no position sizing ever**; ATM/ITM strikes only (|Δ| ≥ 0.52); **yes/no rules
only — no scores, composite indicators or weights**; no slippage or brokerage modelling (owner, 5 Nov); a new rule
enters decisions only if it beats the current book on days it was not tuned on.

**How everything was tested.** An offline kit (one row per second, 12 recorded days 19 Oct – 4 Nov 2026, three of
them expiry days) runs the exact strategy classes the engine runs. It fills at the ask two seconds after a signal
and sells at the bid. Each candidate rule was added to c20_9y alone, run over a grid of settings, and judged on
four things:

1. the 12-day total;
2. the five days no rule was ever fitted on (29 Oct – 4 Nov);
3. leave-one-day-out;
4. whether a ±20 % nudge of each setting keeps the gain (no "cliff").

For every model with fitted parameters (Hawkes, HMM), day *d* was scored by a model fitted on the other eleven days.

**Reference:** c20_9y on the kit: +12,32,085 over 12 days, 69 trades, 28 losers; never-fitted days +13,419.
(c20_9x: +11,23,538, 77 trades, 36 losers; never-fitted days −22,480.)

**The single most important finding.** The premium-outcome model — the reviews' central recommendation — was
built exactly as specified (full repricing, competing barriers, multi-horizon) but fed by a theoretical drift
(Kalman velocity of the 1-s forward). Its probabilities were not calibrated, as the reliability check on 17,484
samples shows:

| Predicted P(+10 % before −10 % within 5 min) | Actual |
|---|---:|
| 0–10 % | 17 % |
| 40–60 % | 22 % |
| 90–100 % | 23 % |

The mathematics is verified (closed forms, Monte Carlo); the drift input carries no information about the next
five minutes. The *trained* version the reviews also describe (meta-labelling, a fitted survival model, Bayesian
fusion, conformal calibration) was **not built** — see §B-4. That is the largest open item.

---

## Part A — ChatGPT teardown (`Apex_Quantitative_Teardown.docx` = `chatgpt_5th_advanced.txt`)

### A-0. Executive summary and "top five additions"

| # | Point | Status | Detail |
|---|---|---|---|
| 0.1 | Architecture is sound (multi-instrument impulse, futures book, premium tracking, candidate ledger, parallel books) | agreed | Unchanged. |
| 0.2 | Change the central question to "which option has the highest probability of an immediate premium gain before an adverse move" | **REJECTED** (analytic form) / **NOT BUILT** (trained form) | `apex/quant/passage.py` answers exactly this question for any option. As a filter it lost at every setting; as an entry engine it lost (see A-3.4). The trained version was not built (A-3.12). |
| 0.3 | More indicators are not the answer; measure incremental value | agreed, done | Every new model was tested one at a time against c20_9y (the "ablation lab", A-6.4). |
| 0.4 | 7–12 sessions are not enough to promote a strategy | agreed | c20_9y and c20_9s run as **shadow books**; c20_9x stays champion. |
| 0.5 | Data quality matters as much as mathematics | partly | Existing freshness guards only (A-8). |
| Top-5 #1 | Hawkes process | **REJECTED** | A-3.3. |
| Top-5 #2 | Hidden semi-Markov model | **REJECTED** (simplified form) | A-3.1. |
| Top-5 #3 | Competing-risk survival model | **REJECTED** (analytic) / **NOT BUILT** (fitted) | A-3.4. |
| Top-5 #4 | Higher-order Greeks and full repricing | **DISPLAY** (and inside the premium model) | A-2.3. |
| Top-5 #5 | Bayesian meta-labelling | **NOT BUILT** | A-3.12, A-3.13. |

### A-Intro. Three objectives: opportunity recall, entry precision, option profitability

Adopted as the scorecard every test reports (`card()` in the kit library):

* **Opportunity recall** — big moves caught: 15-min windows with a forward range ≥ 40 pts that had a trade open
  ≥ 5 min (c20_9x: 68 of 175).
* **Entry precision** — losing trades and "dead" losers that never got above +5 % (c20_9x: 18, costing −4.39 L,
  77 % of all losses).
* **Option profitability** — trades that were up +10 % and still lost, average give-back from the peak, and
  "stuck" trades held ≥ 10 min without reaching +15 %.

### A-1. What was found in the repository

| Point | Status | Detail |
|---|---|---|
| 1 / 1.1 Two layers (running engine vs specification documents); strongest components | agreed | The three specs (PCE, cheapness/regime, OI acceleration/VWAP) are still documents, not decision code. |
| 1.2 OI quadrants, OI walls, PCR, OI-acceleration+VWAP, queues, Greek timing, regime gates and dip-waiting failed as triggers (29 Oct) | agreed | Not re-introduced as triggers. **One exception:** c20_9y contains an OI-wall entry *veto* (A-2.2). |
| 1.2 Sixteen observer cards are not connected to decisions | agreed | Still true; the new quant panel is also display-only, by design (§How to read this). |
| 1.3 c20_9s, c20_9y, failed exit experiments; 7–12 days too few to promote | agreed | Neither shadow is promoted. |

### A-2. The biggest mathematical weaknesses

| Point | Status | Detail |
|---|---|---|
| 2.1 Predict three distributions: P(Nifty move), P(premium move), P(target before barrier) | partly | Only the third exists, analytically (`passage.py`). P(Nifty move) exists only as a drift estimate (Kalman velocity), not a distribution model. P(premium move) as its own distribution: **NOT BUILT** (omitted). |
| 2.1 The premium model must be the final authority for entry | not adopted | It failed calibration, so making it the authority would have lost money (A-3.4). |
| 2.2 GEX cannot identify dealer positioning | agreed | `apex/engine/gex.py` already states the long-call/short-put assumption and is display-only. |
| 2.2 Run three GEX scenarios (A, B, order-flow-inferred C) as features | **NOT BUILT** (omitted) | — |
| 2.2 Do not make one dealer-positioning scenario a hard veto | **partly contradicted** | c20_9y vetoes a normal-day buy when the maximum-OI strike of the resisting type is ≤ 25 pts ahead. Kit: +25,165 over 12 days, no cliff at ±40 %, from only 5 vetoed buys. It is raw OI, not GEX, and the book is a shadow. The reviewers' caution stands; the evidence is thin. |
| 2.3 Higher-order Greeks: vanna, vomma, charm, speed, color, ultima (+ zomma) | **DISPLAY** | `apex/quant/greeks_hi.py`, every Greek checked against a finite difference (tests/test_quant_greeks.py); shown live for the held option, else the ATM pair. Used inside the premium model. Not tested as stand-alone rules (A-2.3 note). |
| 2.3 Second-order cross Taylor (vanna·dF·dσ, ½vomma·dσ², charm·dF·dt) | built | `greeks_hi.taylor`; a test confirms it beats delta-gamma on a joint move. |
| 2.3 Full repricing engine: forecast F, forecast the vol surface, reprice by Black-76 on bid/ask, P(required premium) | partly | Full repricing of target and stop **is** built (`forward_for_premium`). Forecasting F: Kalman drift only. Forecasting the vol surface at a future time: **NOT BUILT** (IV scenario parameter exists, set to 0). Executable bid/ask: the model prices from the ask paid. |
| 2.3 Black-76 has no explicit discount factor e^(−rT) | decided, documented | The forward is the parity forward, so pricing, IV and parity all use r = 0 undiscounted (stated in `apex/quant/__init__.py`). For a ≤ 1-week horizon the difference is below the IV solver's tolerance. |
| 2.3 `years_to_expiry()` 600-s / 60-s floor misstates the clock | partly | The new module uses the real clock (`greeks_hi.real_years`, 1-s floor). The engine's own `greeks.py` keeps its floor: changing it changes live IVs and so the champion's decisions, which needs its own test. |
| *Note to 2.3* | — | The exact DeepSeek rule "no CE if charm < −X and vanna < 0" was **not run**. Related panel tests failed (charm/time-of-day −2.39 L; vanna/IV −34k out of sample). |
| 2.4 Upgrade lag-cheapness into a premium-dislocation detector: residual vs model, standardised against same strike/moneyness, expiry time, IV regime, spread and time of day, plus its convergence rate | **NOT BUILT** (omitted) | Nearest pieces: (a) the panel's "premium efficiency" member compared the realised premium change with the Taylor model — that became the IV-rich veto in c20_9y (DECIDES); (b) the SVI residual (A-3.6) is a cross-sectional cheapness measure. The standardised time-series residual and its convergence rate do not exist. |

### A-3. Advanced models

**Tier 1**

| Point | Status | Detail and result |
|---|---|---|
| 3.1 HMM / HSMM, six latent states, feed the posterior to the entry model | **REJECTED** | `apex/quant/regime.py`: Gaussian HMM, Baum-Welch with restarts, Viterbi, causal forward filter, plus a semi-Markov layer (expected remaining duration from empirical run lengths). **Four** states on 60-s bars (return, log range) — six would have ~70 % more parameters on ~4,000 bars; the number was not chosen by BIC (a gap). Not a full explicit-duration HSMM. Fitted states mostly separate quiet from busy tape (drifts −0.2, 0, +0.3, +2.2 pts/min); mean duration 2–3 min. Tests: "trade only in the most likely state's direction" −9.6 L; "skip regimes about to end" +7.3k at one setting (one trade) and −3.8 L at the next (a cliff). DISPLAY: posterior, state, minutes left. |
| 3.2 Kalman / UKF state model of the heavyweight-to-Nifty impulse and lead-lag | partly / **NOT BUILT** | Only a local-linear-trend Kalman on the Nifty forward exists (`micro.KalmanVelocity`). As a gate (velocity t-stat must agree): −1.7 to −3.0 L across settings. The heavyweight lead-lag state model and the UKF: **NOT BUILT** (omitted). The existing `domino.py` heavyweight model is unchanged. |
| 3.3 Multivariate Hawkes on seven event streams (aggressive futures buys/sells, ask/bid withdrawal, CE/PE buying, heavyweight impulses); P(intensity continues 30 s) | partly, **REJECTED** | `apex/quant/hawkes.py`: exponential kernel, O(1) live update, exact MLE on event times, binned MLE on per-second counts. Built for **two streams per option** (aggressive buy and sell prints on the CE and PE), one shared kernel — not cross-exciting, not the futures, liquidity or heavyweight streams. Fitted: branching ratio 0.86, half-life 84 s. Gate "buy-side excitation ≥ r × sell-side on the bought option": every setting lost (r = 1.0 −1.84 L; r = 1.25 −10.2 L). |
| 3.3 Estimate on true event timestamps, not snapshots | not met | The kit holds 1-s snapshots; live the engine samples every 100 ms. No exchange event stream is recorded, so the fit is a binned approximation (a test shows the bias: a 1-s kernel loses half its branching inside a bin). |
| 3.4 First-passage / competing-risk survival: P(target in 1, 3, 5, 10, 15 min), P(adverse first) | **REJECTED** (analytic) / **NOT BUILT** (fitted) | `apex/quant/passage.py`: full-repricing barriers, Brownian forward with drift and jump-robust noise, theta as a headwind, exact two-barrier exit densities (images for short times, eigen-series for long ones); verified against the scale function, the inverse-Gaussian limit and a Monte Carlo. As a filter on c20_9y: best +10,95,819 (−1.36 L); "eventually" version −1.8 L or worse. As an entry engine (A-4): −1.2 L to −6.0 L. Cause: uncalibrated (table at the top). A survival model **fitted to observed outcomes** was not built (A-3.12). DISPLAY: the race for the ATM call and put, every second. |

**Tier 2**

| Point | Status | Detail |
|---|---|---|
| 3.5 Heston / SABR; use a calibrated surface and short-horizon IV forecast, not as a signal | **NOT BUILT** | The reviewers rank these as valuation tools, not signals; no short-horizon IV forecast was built either (omitted). |
| 3.6 SVI surface, residuals; use the surface position for strike selection | **DISPLAY**; strike selection **NOT TESTED** (omitted) | `apex/quant/svi.py`: raw SVI by the quasi-explicit (Zeliade) calibration, ~1 ms per smile, admissibility constraints; residual per strike shown live. Nearest weekly only — no term structure, no calendar-arbitrage check. Choosing the cheapest admissible strike was never run on the kit. |
| 3.7 Rough volatility (behind HAR-RV and Heston benchmarks) | **NOT BUILT** | The reviewers themselves doubt the value at a 10–15-min horizon; HAR-RV also not built. |
| 3.8 Merton jump diffusion, bipower variation, realised jump variation, CUSUM, SPRT | mostly built, **REJECTED** | `micro.RollingVar`: RV, bipower BV, JV, Huang-Tauchen jump z (on real price changes only, time-scaled). Gate "no entry right after a jump": z ≤ 10 changes nothing; z ≤ 6 −5.4 L; z ≤ 4 −8.5 L. CUSUM built (`micro.Cusum`, live drift-change alarm); the 20-member panel's CUSUM exit lost out of sample. SPRT time-stop (panel): lost out of sample. Merton jump diffusion: **NOT BUILT**. |

**Tier 3**

| Point | Status | Detail |
|---|---|---|
| 3.9 Kyle's λ on futures, ATM CE, ATM PE, heavyweight futures, several horizons | built, **NOT WIRED** (omitted) | `micro.KyleLambda` exists and is unit-tested, but nothing calls it — not the strategies, not the dashboard. |
| 3.10 Liquidity resilience (replenished ÷ consumed, refill speed, cancellation intensity, queue lifetime) | **NOT BUILT** as specified | The existing level "force" detector already measures refill ρ and pull π at levels (`apex/engine/levels.py`); it was rejected as a trigger on 29 Oct. The full resilience model is not built. |
| 3.11 Lead-lag network (Granger, transfer entropy, partial correlation, sparse VAR, DCC) | **NOT BUILT** (omitted) | The existing heavyweight model uses weighted impulses and rolling correlations, unchanged. |

**Tier 4**

| Point | Status | Detail |
|---|---|---|
| 3.12 Meta-labelling: Model A high-recall detector, Model B high-precision classifier (gradient boosting, calibrated) | **NOT BUILT** (Model B) | Model A was tested in its analytic form (the scanner, A-4). Model B was not built. Reason: 12 days of labelled outcomes is very little (the reviewers say the same, Appendix A). It also produces a learned score, which needs the owner's agreement: it would be used as one calibrated probability with one threshold. **This is the largest open item.** |
| 3.13 Bayesian evidence accumulation with dependency handling (Bayesian network / hierarchical) | **NOT BUILT** | Same data limit; also a composite of evidence, which the owner's rules forbid unless it reduces to one calibrated probability. |
| 3.14 Conformal prediction, rolling and regime-conditional | **NOT BUILT** | Needs a trained model to calibrate; none exists. |
| 3.15 Contextual bandit over pre-registered entry methods, shadow only | **NOT BUILT** | Parallel shadow books exist (≈ 70 books on identical data); no learned policy picks among them. |
| 3.16 CUSUM on relationships breaking (heavyweights stop leading, OFI stops predicting, premium stops responding, walls stop holding) | **NOT BUILT** as specified | CUSUM runs only on the forward's own drift. |

**Tier 5 table** — each item listed in the review:

| Technique | Status |
|---|---|
| Fractional Brownian motion | NOT BUILT |
| Multivariate Hawkes | partly (two streams, shared kernel) — REJECTED |
| Hidden semi-Markov | partly (HMM + empirical durations) — REJECTED |
| Unscented Kalman filter | NOT BUILT |
| Transfer entropy | NOT BUILT |
| Neural SDE | NOT BUILT |
| Temporal convolutional networks | NOT BUILT |
| Transformers | NOT BUILT |
| Optimal stopping | tested as the opportunity-decay exit and the SPRT time-stop — REJECTED |
| Extreme value theory | NOT BUILT |
| Rough volatility | NOT BUILT |
| Particle filters | NOT BUILT |
| Dynamic Bayesian networks | NOT BUILT |

The review's own caution — establish simpler models before neural ones — was followed.

### A-4. Opportunity Decay Model (O_t = P(target before barrier), D_t = −dO/dt; five-stage lifecycle; diagnose the failure mechanism)

* **O_t and D_t** — **REJECTED**. O_t is the premium-race probability; the live panel shows its 30-s change
  ("fading" or "building"). As an exit — sell when the remaining race probability falls below p after the trade
  has been held a while — every setting lost 6.4–11.0 L: it sold trades that were still forming and then bought
  back in (+18 to +32 trades, +14 to +28 losers).
* **The five-stage lifecycle state machine** — **NOT BUILT**.
* **Classifying why an opportunity decays** (catalyst gone, premium repriced, liquidity returned, level near) —
  **NOT BUILT**.
* **The detector use ("Model A")** — **REJECTED**. Every 5 s the scanner computed the race for the nearest-ITM
  call and put and bought when P(+10 % first within 5 min) ≥ X. Exits: +10 % target, or a 5 % trail after
  +10 %; −10 % stop; 15-min clock.

  | Scanner | Trades | Losers | 12 days |
  |---|---:|---:|---:|
  | alone, X = 0.8, target | 604 | 318 | −1,24,725 |
  | alone, X = 0.8, trail | 551 | 292 | −1,93,056 |
  | filling gaps when c20_9y was flat, X = 0.8 | 506 | 272 | +73,639 (vs +12,32,085) |

### A-5. Seven-layer quantitative intelligence engine (models supply evidence, only layer 6 decides)

Partly. Layer 1 exists. Layer 2 (micro, derivatives, latent state) is now built as evidence in
`apex/engine/quantview.py` (2D cross-market is not). Layers 3–4 (probabilistic detection and fusion) are **not
built**. Layer 5 is the existing contract picker (|Δ| nearest 0.52). Layer 6 is the champion's yes/no rules.
Layer 7 is the shadow books plus the nightly learning loop.

### A-6. The learning engine

| Point | Status | Detail |
|---|---|---|
| 6.1 Event-level grouping, session clustering, purged walk-forward, embargo, effective sample size | partly | All tests split by **whole session** (leave-one-day-out, plus five never-fitted days), which is the coarsest grouping and immune to intraday overlap. Purging, embargo and effective-sample-size reporting: **NOT BUILT**. |
| 6.2 Deflated Sharpe, PBO, CSCV, White's Reality Check, Hansen SPA | **NOT BUILT** | Selection bias is handled only by nudge (cliff) tests, leave-one-day-out and never-fitted days. c20_9y was chosen from many candidates; its gain rests on 8 skipped trades, and it is not promoted for that reason. |
| 6.3 Metrics: target-first probability, MFE, MAE, time to MFE, time to target, initial adverse excursion, capture ratio, rejection cost, calibration error, incremental feature value | partly | Kit trades record peak (MFE %), hold time, exit reason; the scorecard reports give-back, missed moves and dead or stuck trades. Calibration error was measured once (the race). MAE, time to MFE/target, rejection cost and calibration in the nightly learning engine: **NOT BUILT**. |
| 6.4 Feature-ablation laboratory | done (single-feature form) | Each model added alone to c20_9y and compared. Conditional permutation importance: not done; no model reached the stage where it would matter. |

### A-7. Specific problems in the specifications

| Row | Status | Detail |
|---|---|---|
| OI falling ≠ writer covering | not addressed | The OI-acceleration spec is not in any decision. |
| Maximum OI ≠ resistance | partly contradicted | c20_9y's OI-wall veto (A-2.2). |
| Synthetic future leading spot: quote noise, stale legs | partly | The engine drops option legs older than 30 s from the parity forward (D-102). Executable-side parity checked against the actual future: **NOT BUILT**. |
| Delta/gamma premium forecast | built | Full repricing (A-2.3). |
| IV percentile misleads around expiry | partly | c20_9y's IV veto compares with *today's* median since 09:20, not a cross-day percentile; it still is not conditioned on moneyness or time to expiry. |
| Fixed 80 % probability threshold needs calibration | done | No such threshold is in any decision; the race probability was checked for calibration and failed. |
| 500 correlated candidate labels | not addressed | No model is trained on candidate labels. |
| OI updates are discontinuous | not addressed | OI acceleration is not used. |
| PE-on-support / CE-on-bounce IV hypothesis must not be a fixed rule | met | No such rule exists; the IV veto is symmetric for calls and puts. |
| 7.1 Scenario distribution (bullish/bearish/failure/sideways × IV paths); E[return], P(≥ +10 %), P(≤ −stop), EV = P(W)E[W] − P(L)E[L] − E[C] | **NOT BUILT** | The race uses one Brownian scenario with an optional IV shift (unused); no scenario mixture and no EV rule. The cost term E[C] is excluded on the owner's instruction. |

### A-8. Data quality

* **Exists.** Every row of the shared table carries the feed's receive time and the exchange's last-trade time,
  plus a depth timestamp. The engine leaves stale quotes out of the forward and IV (30 s). Exits wait for a quote
  fresher than 5 s. There is a spot staleness guard, and the dashboard shows a data-health card.
* **NOT BUILT:**
  * a formal per-instrument quality score Q_t;
  * all four clocks separated (exchange, broker, receipt, processing);
  * measures of out-of-order, duplicate or missing events and of crossed books;
  * passing quality metadata to every model.

### A-9. Implementation priority (ten steps) and the four survival tests

| Step | Upgrade | Status |
|---|---|---|
| 1 | Premium outcome prediction, full repricing, competing-risk labels | analytic model REJECTED; labels and trained model NOT BUILT |
| 2 | HSMM market state | simplified form REJECTED |
| 3 | Opportunity Decay Model | REJECTED as an exit and as a detector |
| 4 | Hawkes | two-stream form REJECTED |
| 5 | Kalman lead-lag | NOT BUILT (forward-only Kalman REJECTED) |
| 6 | Higher-order Greeks and surface | DISPLAY |
| 7 | Survival analysis | analytic only (step 1) |
| 8 | Bayesian aggregation | NOT BUILT |
| 9 | Conformal and change points | CUSUM built (DISPLAY); conformal NOT BUILT |
| 10 | Contextual bandit | NOT BUILT |

**Four survival tests** — all four were applied to every tested model:

* **A — recall:** big moves caught.
* **B — false entries without losing winners:** losers, dead losers, and whether the 27 Oct runners were kept.
* **C — incremental value:** each model compared against c20_9y alone.
* **D — out-of-sample:** the five never-fitted days and leave-one-day-out.

None of the new models passed.

**Execution caveat (LTP fills).** Correct for the live engine: a paper entry fills at the last traded price of the
first print after the trigger. The offline kit, where every number above comes from, buys at the ask and sells at
the bid. Slippage and charges beyond that: EXCLUDED (owner).

### A-10. Final assessment and the central question

Agreed. The one statement every test confirmed: *"no model can guarantee that it will never miss a winner or never
take a losing trade."* On these tapes every rule that cut losers also cut the runners that carry the profit, and
every engine that traded more often added more losers than profit.

### A-Appendix A. Reviewer notes and four immediate actions

| Action | Status |
|---|---|
| (1) Slippage and charges | EXCLUDED (owner) |
| (2) Group candidates by event, report effective sample size | NOT BUILT |
| (3) Separate exchange, broker, receipt and processing timestamps | partly (receipt and exchange times exist) |
| (4) Premium-outcome labels (target-first, MFE/MAE, time to target) in the candidate ledger | NOT BUILT — the prerequisite for the trained model (A-3.12) |

The data-budget and event-data cautions proved right (A-3.1, A-3.3).

---

## Part B — DeepSeek (`deepseek_5th.txt`)

| Point | Status | Detail |
|---|---|---|
| Strengths: event-driven 100 ms / 250 ms plumbing, Black-76 on the parity forward, flow.py, GEX honesty, SPRT/Bonferroni/LODO learning | agreed | Engine profiling on 5 Nov found the 250-ms publish was the single largest cost; fixed without changing any decision (72 of 72 books trade-for-trade identical on replay; 20.6 vs 23.7 ms per step). |
| Gap 1: Greeks stop at first order (vanna, charm, speed, color, zomma, ultima) | built — DISPLAY | A-2.3. |
| Gap 2: no arbitrage-free surface (SVI/SABR) | SVI built — DISPLAY | Butterfly admissibility only; one expiry, so no calendar check (A-3.6). |
| Gap 3: constant-vol Black-76 is biased near expiry; Heston / rough Heston | NOT BUILT | A-3.5, A-3.7. |
| Gap 4: entries are hand-set thresholds; no supervised layer | NOT BUILT | A-3.12. |
| Gap 5: options flow under-used (sweeps, large trades, opening/closing) | partly | Hawkes buy/sell excitation on each option's aggressive prints (REJECTED). Sweep and large-trade detection, and opening/closing classification: NOT BUILT. |
| Gap 6: no slippage model | EXCLUDED (owner) | The kit already buys at the ask and sells at the bid. |
| Higher-order Greeks as learning-loop features; gate "no CE if charm < −X and vanna < 0" | features DISPLAY; that exact gate NOT RUN | A-2.3 note. |
| SVI per expiry (voltorch / SciPy); surface fair value; skew and term residuals; Greeks from the surface; feed GEX and edge snapshot | partly | Own quasi-explicit calibration; residuals shown. Term structure, surface-differentiated Greeks and feeding GEX or the edge snapshot: NOT BUILT. |
| Heston calibration; model-consistent delta/gamma logged beside Black-76; rough Heston later | NOT BUILT | — |
| Gradient boosting / LSTM on `edge.py` features; RL for timing, sizing, strikes; start with a contextual bandit | NOT BUILT | Sizing: the owner's all-in rule makes it moot. Bandit: A-3.15. |
| Options flow features `opt_flow_imb_5m`, `sweep_count_1m`; VPIN on futures | NOT BUILT | — |
| Bayesian uncertainty, Bayesian change-point on the futures impulse | NOT BUILT | Frequentist CUSUM built instead (A-3.8). |
| Almgren-Chriss / spread-crossing slippage | EXCLUDED (owner) | — |
| Malliavin calculus for Greeks | NOT BUILT | Unnecessary under Black-76: the Greeks are closed-form and exact. Relevant only after stochastic-vol models. |

**DeepSeek roadmap**

| Phase | Item | Status |
|---|---|---|
| 1 | Higher-order Greeks | done |
| 2 | SVI | done (single slice) |
| 3 | Heston | not built |
| 4 | Gradient boosting gate | not built |
| 5 | Options flow + slippage | flow partly; slippage excluded |
| 6 | RL, rough Heston | not built |

---

## Part C — DeepSeek advanced (`deepseek_5th_advanced.txt`)

| Point | Status | Why |
|---|---|---|
| Quadratic Rough Heston / QRH+, regime-conditional on downside smile curvature | NOT BUILT | Valuation models; no stochastic-vol layer exists yet (A-3.5). The paper's own finding — a well-specified non-rough benchmark matches them on average — puts them behind Heston. |
| 4/2 rough-and-smooth model | NOT BUILT | Same. |
| Fast rough-Heston pricing (modified Adams + SINH Fourier); "ghost calibration" warning | NOT BUILT | Same; the warning is noted for any future calibration. |
| Signature-based optimal stopping (primal Longstaff-Schwartz / dual martingale) | NOT BUILT | Needs a learned policy and far more than 12 days. Optimal-stopping *rules* were tested and lost (A-4, A-3.8). |
| Deep signature features (depth-3/4 iterated integrals of the futures path) for a gradient-boosted model | NOT BUILT | No supervised model exists to consume them (A-3.12). |
| Signature methods for American options under rough vol | not applicable | Nifty index options are European. |
| Finance-Informed Neural Network (no-arbitrage loss) | NOT BUILT | Pricing research; Black-76 Greeks are exact for the model used. |
| DeepOption with transformer, no-arbitrage loss, transfer learning | NOT BUILT | Same, plus the data limit. |
| Arbitrage-free neural SDE market simulator (stress tests, augmentation, VaR) | NOT BUILT | Research-grade; the reviewer ranks it months 4–6. |
| Neural spline flows with signatures (market simulator) | NOT BUILT | Same. |
| RL deep hedging under frictions (TD3/SAC, CVaR) | not applicable as written | Buy-only, no hedging, no sizing (all-in). An exit policy minimising CVaR is the relevant part; exit rules tested so far all cut runners (A-4). |
| Deep hedging with IV-surface feedback | not applicable | Same. |
| Imitation-learning deep hedging (BSM delta warm start) | not applicable | Same. |
| Hawkes-based rough volatility, quadratic Hawkes, multivariate Hawkes LOB option pricing | NOT BUILT (theory) | The practical item is the next row. |
| Branching ratio as a toxicity feature (high = herding noise, low branching with high intensity = information) | partly | Branching ratio fitted offline (0.86) and stored in `apex/quant/params.json`; the live panel shows buy/sell excitation, not a rolling branching ratio. Excitation as a gate lost (A-3.3). A rolling branching-ratio gate: NOT TESTED (omitted). |
| VPIN, strike-specific, volume-time buckets | NOT BUILT | — |
| Stochastic local volatility (Heston SLV, Monte Carlo calibration) | NOT BUILT | Needs a full surface and stochastic-vol layer first. |
| Path-dependent volatility (running maximum) | NOT BUILT | — |
| Quantum amplitude estimation / quantum-inspired Monte Carlo | NOT BUILT | The reviewer marks it "watch"; Black-76 needs no Monte Carlo. |
| Roadmap A Hawkes | partly, REJECTED | — |
| Roadmap B QRH+/4-2 | not built | — |
| Roadmap C Signature features | not built | — |
| Roadmap D Deep hedging | not applicable | — |
| Roadmap E Neural SDE / FINN | not built | — |
| Roadmap F Quantum | not built | — |
| "The path is the primitive, not the point" | agreed in principle | The tested models are point-in-time; path representations (signatures) were not built. |

---

## Part D — What the system actually decides with today

**Champion c20_9x**

* **Forward and pricing.** Black-76 on the put-call-parity forward. Option legs older than 30 s are left out of
  the forward and IV.
* **Strike.** The CE or PE with |Δ| nearest 0.52; never below 0.52.
* **Normal-day entry.** A 40-pt forward impulse within 20 min, then a 50–75 % pullback within 15 min, then a
  5-pt resumption.
* **Expiry-day entry.** The forward breaks its 10-min range with ≥ 20 pts of velocity over 150 s.
* **Vetoes.**
  * The expiry IV-shock veto: no buy right after an IV jump.
  * The flip-after-loss gate.
  * A 60-s cooldown.
  * Entry windows.
* **Exits.**
  * A −15 % premium stop.
  * A forward trail of 25 pts on expiry days; 40 pts × a delta factor of 0.8–1.0 on normal days.
  * Premium floors: on expiry, break-even from +15 % and keep 70 % from +60 %; on normal days a continuous ramp
    from +15 %.
  * A +70 % premium trail (8 % off the peak bid) on expiry days.
  * Clocks of 15 min (expiry) and 90 min (normal); flat by 15:00 or 15:20.

**Shadow c20_9y** = c20_9x plus two vetoes:

* **IV-rich.** No buy when ATM IV is more than 3.5 vol pts above its median since 09:20.
* **OI wall.** On normal days, no buy when the maximum-OI resisting strike is ≤ 25 pts ahead.

Kit, 12 days: +12.32 L vs +11.24 L; 28 losers vs 36. Live since 5 Nov.

**Shadow c20_9s** = c20_9x plus a stale-impulse veto (normal days, impulse older than 660 s).

**Live record of c20_9x**

| Day | Result |
|---|---:|
| 30 Oct | −3,539 |
| 2 Nov | +43,183 |
| 3 Nov | −44,688 |
| 4 Nov | −25,412 |
| 5 Nov | −5,486 |
| 6 Nov | +93,821 |

On 5–6 Nov c20_9y and c20_9s made the same trades as c20_9x.

## Part E — Open items in order of value

1. **Premium-outcome labels and a trained, calibrated model (meta-labelling Model B).**
   * Labels: for every second, did +10 % come before −10 % within h, plus MFE, MAE and time to target.
   * Inputs: every model built (Hawkes excitation, regime posterior, jump z, CUSUM, Kalman velocity, SVI residual,
     Kyle λ, higher-order Greeks, the analytic race).
   * Validation: purged walk-forward by day, judged by calibration on unseen days.
   * In use: one probability, one threshold (owner's rule).
   * Expected obstacle: 12 days of data.
2. **SVI-residual strike selection** — never tested.
3. **Kyle's λ** — wire it, then test it.
4. **Three-scenario GEX** — to replace the single-assumption map.
5. **Rolling Hawkes branching ratio as a toxicity gate.**
6. **Selection-bias statistics** (deflated Sharpe, PBO) **and event grouping** before any promotion.
7. **Data-quality score and the four separated timestamps.**

Code: `apex/quant/` (models, 36 tests), `apex/engine/quantview.py` (live panel), docs/24 (test results),
docs/23 (the 20-member panel that produced c20_9y), docs/22 (stuck-trade panel), docs/20 (c20_9x specification).
