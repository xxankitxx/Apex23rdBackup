# The council's 20 individual reports

*18 Oct 2026. Twenty members, each alone, each with one lens, reviewing the same baseline (git `85b65ed`, v1.1.1). Every GitHub idea comes from a repository the member opened. The full reports follow the index, unedited.*

| # | Lens | Most important finding | Best GitHub idea |
|---|---|---|---|
| 01 | Market microstructure | Book advisor and BOOK exit read the wrong side of the book for every PE (engine_main book_state); Force ρ can never reach BREAK-IMMINENT | kayasolomon/order-flow-toxicity (MIT): Cont–Kukanov–Stoikov order-flow imbalance |
| 02 | Option pricing & Greeks | Theta per minute is ~3.8× too large (trading-minute vs calendar clock) → fake straddle 'spike' excess late on expiry day | vollib/lets_be_rational: IV at bid and ask (uncertainty band); py_vollib as test oracle |
| 03 | Statistics of the learning loop | SPRT false-GO 15–33 % when true sd is 15–30 % (assumed 10 %); tests arithmetic mean, not log growth; daily looks leak | gostevehoward/confseq (MIT): anytime-valid betting confidence sequence |
| 04 | Replay & reproducibility | Two replays of the same file give different trades (0/17 books match); re-replaying a day stacks on the previous run | nautilus_trader concept: lock-step replay clock |
| 05 | Breeze live feed | Feed crash + restart makes the rest of the day's recording unreadable; feed can report LIVE with 0 instruments | zerodha/pykiteconnect (MIT): ping/pong liveness, capped backoff |
| 06 | Shared memory & processes | Nobody reads the heartbeats: a hung engine with an open position looks normal; snapshot can mix two ticks | Supervisor/superlance httpok: restart on failed health check |
| 07 | Architecture | One advisor exception skips exits for every step with a live episode (position held 99 pts past a 12-pt stop) | nautilus_trader concept: RUNNING/DEGRADED/FAULTED guards; pluggy registry |
| 08 | Test quality | 27 one-line breaks to safety code → only 1 caught by the suite; weekend end_day promotes a challenger on an empty Saturday | HypothesisWorks/hypothesis: state-machine tests for the paper book |
| 09 | Dashboard & UX | No staleness detection: frozen engine shows green 'live' and stale P&L | pladaria/reconnecting-websocket (MIT) + engine-age banner |
| 10 | NSE / Indian F&O facts | TCS 2.70 and ITC 2.56 weights are impossible (top-10 ends at 2.52 %); calendar, lot, freeze qty all verified current | gerrymanoim/exchange_calendars (Apache-2.0): XBOM cross-check |
| 11 | Regime & volatility | ATM IV at a single strike jumps on strike change and rises on down-moves → PE entries rejected as LATE | Yang-Zhang / Rogers-Satchell realised vol → IV/RV observer (concept) |
| 12 | Domino thesis | Classifier calls ~14 % of no-lead episodes BASKET-LED — on the 15 % kill line; gap variants fire on stale stock prints | philipperemy/lead-lag (MIT): Hayashi-Yoshida lead-lag |
| 13 | OI, PCR & dealer gamma | gex_room compares weekly strikes with the MONTHLY futures (40–120 pt basis); a calls-only chain poll vetoes everything | Python-NSE-Option-Chain-Analyzer concept: wall-unwind observer |
| 14 | Experimental design | sd 10 % assumption too small: no-edge false GO 25 %, real edge killed 57 %; random_entry comparison favours trading less | bashtage/arch: SPA/StepM block-bootstrap over the variant family |
| 15 | Observability & audit | Same crashed-recording bug; event tape never written to disk; reruns double-count candidates | freqtrade concept: rejected-signal / tag-grouped analysis |
| 16 | Performance & latency | IV solve is ~47 % of each step; prototype 7× faster; sim above 10× under-samples | ijl/orjson for state publishing |
| 17 | Safety & paper-only | No-order test misses 5 real Breeze order methods; no runtime block; gateway accepts any websocket origin | Starlette TrustedHostMiddleware + origin check |
| 18 | Exits & trade management | Stops muted for 20 s after data returns (blackout fix too broad): stop fired at −12 % vs −4.8 % | QuantConnect/Lean: premium-based trailing stop as a shadow exit |
| 19 | Data storage & lifecycle | Live session stopped before 15:30 never reaches days.jsonl; non-atomic rewrite can kill learning permanently | python-atomicwrites (MIT) pattern; freqtrade schema migrations concept |
| 20 | The skeptic | GO can light on a no-edge strategy (64–89 % with serial champions); option 'age' is not trade age → fills at pre-impulse LTP | gostevehoward/confseq (MIT); lead-lag (MIT) |


---

# Member 01: Market microstructure and order-book flow

## Lens
I looked at the order-book layer: `apex/engine/flow.py` (the classes, the imbalances, the lead score, `run_score`), `apex/engine/market.py` (the 10 Hz rings), `apex/engine/levels.py` `Force`, the book advisor (`engine_main.py:426-436`), `book_state` (`engine_main.py:297-304`), the book exit (`paper.py:372-376`), and the depth parsing in `feed_core.py:180-194`. Everything here was checked against baseline 85b65ed. `tests/test_core.py` passes. The probe scripts are in `/tmp/council/01/probe.py` and `/tmp/council/01/probe2.py`. I ran both with synthetic snapshots through the real `Market`, `Flow` and `Force` classes.

## Teardown

### T1. The book advisor and the book exit read the wrong side of the book for every PE (HIGH, verified by probe)
- **Where:** `engine_main.py:301`. The code is `d = 1 if rr == "CE" else -1`, followed by `self.flow.side(i, d)`.
- **The bug:** `Flow.side(i, direction)` takes the direction of *the contract's own price* (see its docstring, "+1: the asks oppose a rising price"). We only ever *buy* options, so the side that opposes us is always the asks, for CE and PE alike. For a PE, `book_state` passes −1 and gets back the PE's bids, with the imbalance sign flipped.
- **The probe (P1):** the asks on a PE refill strongly (`cls_s`/`cls_so` = REFILLING). `side(i,-1)` reports HOLDING/HOLDING with an imbalance of −0.25, so there is no veto. Mirror the case so that PE buyers stack up, which is bullish for our PE: the advisor reports the "sellers" as REFILLING and vetoes. For a held PE, the BOOK exit (`paper.py:375`) fires when PE bids refill, which is a good sign for the position.
- **Impact:** half of the book advisor's verdicts are inverted. Those verdicts are logged, screened through RAW ablation and can be promoted (D-067). The same goes for the PE trades of `m2.0_s0.5_bookexit` (D-056). The learning loop will score a corrupted advisor and may drop an idea the owner called "very very important".
- **Not affected:** `coherence()`/`run_score` (`engine_main.py:400-401`) are correct. There the sign *does* mean contract direction under a market move.
- **Fix:** use `side(i, +1)` in `book_state`. This is a bug fix, not a rule change, but the evidence logged so far should be marked as pre-fix.

### T2. Force: ρ converges to 1 as the volume consumed grows, so a real drain never reads BREAK-IMMINENT (HIGH, verified by probe)
- **Where:** `levels.py:439-442`. The code computes `resid = S − (S0 − C)` and `ρ = resid/C`.
- **Why it fails:** S is the 5-level window total on the futures book, so S is bounded by a few thousand units. C, the cumulative aggressive volume, grows without bound. That gives ρ ≈ 1 + (S − S0)/C → 1, and π can only be positive while C < S0, which means the first seconds only.
- **The probe (P5):** the opposing side drains from 100 % to 25 % under steady buying. ρ goes 0.41 → 0.71 → 0.78 → 0.87, and the verdict moves from WEAKENING back to TESTING.
- **Consequences:**
  - BREAK-IMMINENT (ρ < 0.5 and S < 0.4·S0) can never happen.
  - VACUUM is reachable only in the first ~1–2 s.
  - With a static book, ρ is exactly 1.0 forever (P4). The `force` advisor's HOLD-STRONG veto then depends only on A fading below half its peak.
- **Root cause:** a stock-and-flow identity that assumes a fixed queue, applied to a 5-level window that moves with price. On a ₹0.05-tick futures book, as D-012/G3 note, the window is under a point wide. It is not the inventory "at the level", which can be up to 5 points away.
- **Fix:** compute ρ/π over a rolling 10–15 s window, with C and ΔS taken over the same window, instead of from the start of the test. Better still, use the OFI from Idea 1.

### T3. A refill after an earlier drain is classed DRAIN-SLOW, not REFILLING (MEDIUM, verified by probe)
- **Where:** `flow.py:165-166`. The DSLOW mask is applied *after* the REFILL mask and has no `r10 ≤ 0.15` guard.
- **The probe (P3b):** the asks rise 50 % in the last 10 s, after falling 70 % earlier in the minute. The result is `cls_s` = `cls_so` = DRAIN-SLOW.
- **Impact:** this is the "defenders came back" pattern the book advisor exists to catch, and it goes unseen. `run_score` also scores it as a drain (+1/3) instead of a refill (−1/3).
- **Fix:** add `& (r10 <= 0.15)` to the DSLOW mask.

### T4. Frozen depth reads HOLDING, and depth packets keep the quote "fresh" (MEDIUM)
- **Frozen depth (verified by probe P2):** `market.py:48` treats a row as having depth whenever `depth_ns > 0`, which stays true for the whole session. If the depth token goes silent, the last book is repeated forever. `_classify` then gives r10 = 0 and returns HOLDING. The `flow.py` docstring promises "a stale instrument gets no class", but nothing in `flow.py` checks age.
- **Fresh-looking quotes (verified by reading only):** `feed_core.py:193-194` calls `table.end(i, recv_ns)` on depth packets too. The guard's futures age (`engine_main.py:216`) and option `age` therefore get refreshed by depth-only traffic. If the "4.1!" quote stream dies while "4.2!" depth keeps flowing, LTP and ttq freeze but the guard (D-063) does not see a gap. Price exits then evaluate a frozen LTP.
- **Fix:** keep `quote_ns` and `depth_ns` separate. Use `quote_ns` for the guard and for exits. Give UNK when `now − depth_ns > 3 s`.

### T5. The lead score never takes the book's weight below half (LOW–MEDIUM, verified by reading)
- **Where:** `flow.py:196`. The code is `trust = 0.5 + 0.5·max(0, lead)`.
- **The problem:** the docstring says that with a lead near 0 the book "should carry no weight", yet the book terms keep 50 % weight at lead = 0. A *negative* lead also keeps 50 %. A negative lead means the book is contrarian, which is typical of quote fading or spoofing on NFO options.
- **A second weakness:** the estimator itself is a 100 ms-overlapping 2-s-horizon correlation on LTP, which is dominated by bid–ask bounce on options. Its effective sample is far below what the 3-min EW suggests. I did not quantify this (unverified).
- **Suggestion:** pre-register a variant with `trust = max(0, lead)` and log `lead` on every trade. Changing the live score itself would break I-11.

### T6. Force locks onto the session high or low during a breakout (LOW, verified by reading)
- **Where:** `levels.py:419-431`. The levels are built from the *previous* `sess_hi`.
- **What happens:** at a new high, the nearest level is the old high, just below. Its direction is −1 ("support attacked from above"). The test is sticky until it closes, so a CE wall 3 points above is ignored while price grinds up. During the most important breakouts, the `force` advisor (`dir == d`) is blind.

## Good things
- **D-013 window totals** (`market.py:49-52`). Totals are summed over the levels, never taken per level. This is the right defence against false per-level pulls from re-quoting, and the code is clean.
- **Order counts as their own series, explained in order units** (`flow.py:120-128`). Dividing consumed quantity by the average resting size, so that fills are separated from cancellations, is a genuinely good idea. On NSE depth, order counts are among the few hints about the queue that the feed carries (L2.5, so to speak). It is also cleanly separable for the learning loop.
- **Classes from time-based rings** (`market.ago`). This makes replay at any speed identical, and the probes reproduced deterministically.
- **The PULLED definition** (shrink ≥ 50 % in 10 s with trades explaining < 25 %). It is well posed, and `test_flow_orders_and_lead` pins it down.
- **The monotonic ttq guard** (`feed_core.py:152`) protects aggressor classification against SDK reordering.
- **Force and book are advisory, with verdicts logged on every trade** (D-033). This is why T1–T3 are fixable without contaminating the frozen trigger.

## Ideas from GitHub
1. **kayasolomon/order-flow-toxicity** (MIT): https://github.com/kayasolomon/order-flow-toxicity. I cloned it.
   - **What to borrow:** `src/order_flow_toxicity/ofi.py` `ofi_events()` implements the Cont–Kukanov–Stoikov four-branch OFI at the best quotes. It handles exactly the case T2 gets wrong: when the best price moves, the departed queue counts as full outflow rather than as a "residual". Add it as an **observer** next to `Force`, computed on the futures book from `bid/bqty/ask/aqty`. Fit `Δfut ~ β·OFI` per session, which gives the "book leads price" relationship in its standard, testable form. Then log OFI-over-15 s as a would-have **advisor** for the learning loop.
   - **Also worth borrowing:** its *labelled synthetic market* (`synth.py`), where the true informed intensity is known and "depth thins during toxic episodes". Copy that idea into `feed_sim.py` as a **tool**. With it, REFILL/PULLED/lead accuracy can be scored against ground truth. This is how T3 and T5 would have been caught.
2. **nkaz001/hftbacktest** (MIT): https://github.com/nkaz001/hftbacktest. I cloned it.
   - **What to borrow:** `examples/Market Making with Alpha - Order Book Imbalance.ipynb` computes imbalance over a *price range around mid* (`looking_depth`) and then *standardises it as a rolling z-score* before use. For Apex, the absolute `imb_o < −0.3` veto (`engine_main.py:430`) should become a per-contract z-score over the session. ATM and ±2 strikes have structurally different MM order counts, so one fixed threshold is wrong for most contracts. Register it as a **variant** of the book advisor.
   - **Also worth borrowing:** `Queue-Based Market Making in Large Tick Size Assets.ipynb` explains why queue dynamics dominate when the tick is large relative to the spread. Cheap Nifty options at ₹0.05 ticks are in exactly that regime. It supports a **tool** that buckets every logged trade by premium/tick ratio, to see where the book terms carry any information.

## Top 3
1. **Fix the PE side inversion in `book_state`** (`engine_main.py:301` → `side(i, +1)`), and tag the book/bookexit evidence logged so far as pre-fix. **S, before Monday.**
2. **Fix the DSLOW-over-REFILL ordering and add depth-staleness handling.** That means the `flow.py:166` guard, separate `quote_ns` vs `depth_ns`, the guard on `quote_ns`, and UNK on stale depth. **S–M, before Monday.**
3. **Replace Force's cumulative ρ/π with a rolling-window CKS-OFI observer and advisor** on the futures book, plus a ground-truth-labelled sim mode for scoring the classifiers. **M–L, later.**

---

# Member 02 — Option pricing, IV and Greeks

## Lens
`apex/greeks.py` (Black-76, bisection IV, synthetic forward, time convention, theta per minute), `compute_greeks` in `apex/engine_main.py:331-365`, delta-band contract choice in `apex/engine/paper.py:98-132`, and where the Greeks feed into decisions: `straddle_watch.py` (theta-expected path, spike measure), the `room` advisor (`engine_main.py:413-418`), `gex.py`. Baseline 85b65ed. Probes: `/tmp/council/02/probe.py` and `probe2.py`, checked against `scipy.special.ndtr`. `tests/test_core.py` passes.

**Context that matters:** Monday 19 Oct 2026 is an expiry day, because Tuesday 20 Oct is a holiday and `weekly_expiries` rolls the expiry back. The first live session is therefore a 0DTE session.

## Teardown

**T1. Theta per minute uses two clocks, so the straddle's expected decay is 3.8x too fast. On 0DTE this is plainly wrong. Severity: high (for Monday).**
- **Where:** `greeks.py:91` computes `theta_min = theta_year / 365 / 375`. But T is calendar time (`greeks.py:43-47`), and `straddle_watch.py:136` and `:185` add `theta_min` up per wall-clock minute.
- **Probe (constant IV, ATM straddle, F = 25,000).** Model change over the next 5 minutes, against `theta_min x 5`:

| Time | Model 5-min change | theta_min x 5 | Ratio |
|---|---|---|---|
| Thu, 5 DTE | -0.10 | -0.40 | 3.84 |
| Mon, 1 DTE | -0.21 | -0.81 | 3.84 |
| 0DTE 10:00 | -0.49 | -1.89 | 3.83 |
| 0DTE 13:00 | -0.74 | -2.80 | 3.81 |
| 0DTE 14:45 | -1.37 | -5.12 | 3.73 |

- **On non-expiry days**, dividing by 375 is a defensible guess: it assumes all overnight decay happens in the session. But it is the opposite extreme of the calendar clock that IV is solved on. D-032 says "one variance clock", and this is two.
- **On expiry day** there is no overnight. All remaining T is session time, so the only consistent wall-clock rate is `theta_year / (365 x 1440)`.
- **Failure scenario:** At 0DTE 14:45 a straddle that does not move at all shows `excess = 0 - (-5.1) = +5.1` points. That is above the `SPIKE_MIN_PTS = 4.0` floor (`config.py:136`). The quiet-time sigma EWMA (`straddle_watch.py:192-195`) absorbs part of this bias. But the bias grows through the afternoon (+1.4 at 10:00, +3.7 at 14:45 against the correct model), so the effective spike threshold drops exactly when gamma is highest.
- **Who is affected:** the `straddle_spike` variant, the `gamma_leg` advisor, the premium "DECAYING/FLAT" state and the `room` advisor (`theta x 5` term, small).
- **Verified:** probe, for the bias. **Not verified:** the actual change in Monday's spike count.

**T2. On 0DTE, delta is very sensitive to error in the synthetic forward, and the forward accepts stale LTPs. Severity: medium.**
- **Where:** `engine_main.py:345` falls back to `ltp` whenever bid or ask is missing, with no check on `recv_ns` age. `synthetic_forward` (`greeks.py:100-113`) averages parity at the two nearest strikes and rejects a result only if it is more than 150 points off spot.
- **Probe, 0DTE 12:00, IV 13%:**
  - The 24950 CE delta is 0.78 at F = 25,000, 0.86 at F = 25,020 and 0.92 at F = 25,040. So a 20-point forward error moves the contract out of the `zero_am` band (0.65-0.85).
  - One leg with an LTP 12 points stale shifts F by 6 points.
- **Why 150 is too loose:** it is roughly 2 standard deviations of the full day's move. The age filter in `choose_contract` (`paper.py:125`, `age < 15`) applies only to the chosen option, not to the legs that set F.
- **Fallback bias:** the fallback `ref` is spot (`engine_main.py:333`), not the forward. When parity fails, every delta carries the cost-of-carry bias, about 27 points at 6 DTE in my probe.
- **Verified:** probe and read.

**T3. D-020 is marked DECIDED, but three of its parts are not built. Severity: medium.**
- **What D-020 lists:** "mid-price IV with uncertainty band ... charm/vanna ... sticky-IV P&L attribution" (`docs/02_DECISION_LOG.md:28`).
- **What the code has:** `grep -i 'vanna|charm|attribution|iv_bid|uncertainty' apex` finds nothing. Only a single mid IV exists.
- **Why it matters:** without an IV band from bid and ask, `iv_late` (`engine_main.py:408`) cannot tell a real IV rise from a spread widening. Without attribution, the learning loop cannot say whether a trade lost to IV, theta or direction. That is the question D-019 claims is the buyer's real enemy.
- **Verified:** read and grep.

**T4. The 0DTE 14:45 "no entry" branch does nothing different from the 13:00 branch. Severity: low.**
- **Where:** `paper.py:114-117`. Both branches set `week, band = 1, nextweek`.
- **Docs disagree with each other:** `01_MASTER_DESIGN.md:162` and D-021 say "none after 14:45", while `:233` says only "no 0DTE entries".
- **The code:** still allows next-week entries from 14:45 to 15:15. It also never offers the "0DTE at delta ≥ 0.8" option discussed in OQ-8.
- **Owner decision needed:** confirm the intent and either delete the branch or `return None`.
- **Verified:** read.

**T5. The fallback in `choose_contract` has no upper delta bound. Severity: low.**
- **Where:** `paper.py:129-131`. If nothing is inside the band, the code takes the smallest delta at or above `lo`, which can be 0.95, or the forced 0.99 for invalid-IV deep ITM (`greeks.py:94`).
- **When it happens:** on 0DTE late morning. With strikes 50 apart and a 1-sigma remaining move of about 58 points at 12:45, the 0.65-0.85 band can contain zero strikes. The pick then jumps to a strike about 100 points ITM, under all-in sizing.
- **The cost:** under all-in sizing, strike choice is position size. It is not catastrophic, but the jump should be logged.
- **Verified:** read plus arithmetic.

**T6. An expired expiry is still priced, with T floored at 60 s. Severity: low.**
- **Where:** `greeks.py:46`. On any day after expiry, `years_to_expiry` returns 60 s instead of raising an error.
- **When it bites:** if a registry ever survives past 15:30 of expiry day (a long-running feed, or replay across days), `w0` becomes an expired chain. The ATM, the heroes and the deltas would then all come from dead contracts. `weekly_expiries` rolls off correctly at build time.
- **Verified:** the 60 s return is probed. That a stale registry can actually occur is unverified.

**Checked and correct** (verified against ndtr):
- The A&S erf price error is at most 0.001 points at F = 25,000.
- The IV round trip is exact to 0.001 vol points for 6 DTE, 3 h and 20 min, deep OTM to ATM.
- Delta matches to 1e-5.
- The bisection range [0.5%, 500%] covers 0DTE: a 20-minute OTM option at 3 points solves to 141%.
- The 600 s floor only matters after 15:20, by which time 0DTE positions are already flat at 15:00.

## Good things
- **Black-76 on a parity forward per expiry** (`greeks.py:100-113`; `engine_main.py:350`, solved separately for w0 and w1). This removes basis and carry bias. My carry probe recovered the true forward exactly.
- **Vectorised bisection, not Newton** (`greeks.py:61-75`). It does not blow up as vega goes to 0 near expiry, and 40 iterations give about 1e-11 precision.
- **Explicit validity test** at intrinsic + 0.05, with deep-ITM delta defaulting to ±0.99 and theta/gamma set to 0 (`greeks.py:67`, `:93-96`). This fixes the earlier ITM-put bug named in D-020.
- **`fnum` turns NaN into None** (`engine_main.py:50-55`), and `choose_contract` filters `delta is not None`, so a NaN delta can never enter the band test.
- **ATM IV averages the CE and PE IV at the strike nearest the forward** (`engine_main.py:359-363`). This is robust to one-sided quotes.
- **GEX falls back to ATM IV per strike when IV is missing** and sets NaN gamma to 0 (`gex.py:58-61`). The observer cannot crash the loop.
- **Holiday-aware 0DTE detection** uses the ISO expiry from the registry (`feed_breeze.py:333`; `paper.py:110`). Monday 19 Oct is correctly treated as 0DTE.

## Ideas from GitHub
1. **vollib/py_vollib** — https://github.com/vollib/py_vollib — MIT, with Peter Jäckel's permissive LetsBeRational notice.
   - **Borrow:** the `vollib.black` pricing and implied volatility, and the `vollib.ref_python` reference implementation.
   - **How it maps:** use it as a **test oracle** in `tests/test_core.py`, not in the runtime. Add a grid of 0DTE, deep-ITM and deep-OTM cases asserting that Apex's IV and delta match within tolerance.
   - **Why:** this locks in the numerics I checked by hand. It also adds the missing tests for theta convention and 0DTE: today only a 6-DTE round trip is tested (`test_core.py:51-59`).
   - **Kind:** tool, size S.
2. **vollib/lets_be_rational** — https://github.com/vollib/lets_be_rational — Jäckel's notice ("freely granted ... provided this notice is preserved").
   - **Borrow:** `implied_volatility_from_a_transformed_rational_guess`, which reaches machine precision in two iterations.
   - **How it maps:** use it to compute IV at bid and at ask for every row cheaply, giving the **IV uncertainty band** that D-020 promised (T3).
   - **Then:** log `iv_bid`/`iv_ask` beside `iv`, and add an **observer** that flags `iv_late` firings where `iv5` is smaller than the band width.
   - **Kind:** observer, size M.
3. **nautechsystems/nautilus_trader** — https://github.com/nautechsystems/nautilus_trader — LGPL-3.0, so concept only, no code.
   - **Concept 1:** its GreeksCalculator (`docs/concepts/greeks`) takes `spot_shock`, `vol_shock` and `time_to_expiry_shock`, revalues by full repricing, and raises an error on expired options instead of pricing them.
   - **How it maps, concept 1:** add a **sticky-IV P&L attribution observer** in `paper.py` exit logging. At exit, reprice the entry contract three ways: with only F moved, with only T moved, and with only IV moved. Split the trade's points into direction, theta and IV. This turns T3's missing attribution into data the learning loop can read.
   - **How it maps, concept 2:** make `years_to_expiry` refuse past expiries (T6).
   - **Kind:** observer, size M.

## Top 3
1. **Fix the theta clock for expiry day, as a logged correction (S, before Monday).**
   - **What:** on 0DTE use `theta_year / 365 / 1440`, or equivalently any day where `now.date() == expiry`. For other days, keep `/375` but log `drift_min / theta_min` from `straddle_watch` during quiet time, so D-032's clock gets calibrated from data.
   - **Rule question:** this is a measurement bug, not a trigger change. If the owner reads I-11 strictly, at least run the corrected `expected` path as a parallel observer series from Monday, so the spike variant's 0DTE results can be judged against it.
2. **Make the forward more robust (S, before Monday).**
   - Use mid-or-LTP only when `age < 15 s`.
   - Fall back to the futures-implied forward rather than spot.
   - Tighten the parity sanity check from 150 points to about 40, or to 0.5 x the remaining 1-sigma move.
   - Log F, its source, and the strikes used every second, so any band miss on Monday can be explained.
3. **Build what D-020 promised but is not in the code (M, later):**
   - an IV band from bid and ask (idea 2),
   - sticky-IV P&L attribution per trade (idea 3),
   - a py_vollib oracle test grid covering 0DTE and deep ITM/OTM (idea 1).

---

# Member 03 — Statistics of the learning loop

## Lens
`apex/engine/learning.py` (405 lines) and its constants in `apex/config.py:120-128`. Question: does each test keep its stated error rates on small, clustered (several trades per day), fat-tailed option returns, and does it have enough power to decide anything in a reasonable number of sessions? Everything below marked "probe" was checked with `/tmp/council/03/probe.py` and `/tmp/council/03/adv.py`. Both import the real `learning.sprt_lines`, `_t`, `t_crit` and `_lodo_ok`. Tests pass (`python tests/test_core.py`).

## Teardown

**T1. The SPRT can call GO on a book that loses money under all-in compounding. HIGH (probe).**
`learning.py:252-258` runs the Wald SPRT on the *arithmetic* mean of per-trade ret% (H1 = +2.5 %). Under the owner's all-in sizing the account grows at E[ln(1+r)] ≈ μ − σ²/2, not μ. The probe used μ = +2.5 %/trade:

| true sd/trade | E[ln(1+r)] per trade |
|---|---|
| 10 % | +2.00 % |
| 20 % | +0.45 % |
| 30 % | **−2.78 %** |

A 0DTE book with sd near 30 % can therefore reach the GO line while the paper account it scores shrinks. The challenger test already uses log growth (`_day_ret`, l.61-66), so the scoreboard and the challenger test also judge two different quantities. Fix: run the SPRT on per-trade `ln(1+r)`, the same unit as `_day_ret`.

**T2. The SPRT's α depends entirely on the assumed σ = 10 %. HIGH (probe).**
`sprt_lines` (l.69-73) hard-codes σ² into the boundaries. The probe ran 2,000 runs per cell, up to 200 trades, with H0 μ = 0:

| true sd | P(GO \| H0), stated 0.05 | P(GO \| H1), stated 0.80 |
|---|---|---|
| 10 | 0.044 | 0.81 |
| 15 | 0.154 | 0.62 |
| 20 | 0.227 | 0.52 |
| 30 | 0.329 | 0.46 |

Results were similar with t3 tails and with a skewed lognormal shape. Clustering also hurts. With σ correct (10) but an intraday correlation of 0.3 (5 trades/day sharing the day's regime), P(GO | H0) = **0.162**. The SPRT treats trades as independent, and they are not. The remedy offered in the code (l.263-264: "re-register SPRT_SIGMA_PCT if this persists") changes the test after looking at the data, which is itself a sequential-validity problem. Fix: use an always-valid test that needs no σ (see G1), or at least use the day as the unit and compute σ from the data inside the test (t-SPRT). This is the most important finding: the main GO/KILL gate is calibrated on an assumption the code itself says is probably wrong (config.py:121, "0DTE trades swing far more").

**T3. Challenger promotion leaks α through repeated evening looks. MEDIUM-HIGH (probe).**
`learning.py:270-283`: Bonferroni α/12 (t ≥ 3.36 at 10 days) is applied *at each look*. The loop looks every evening from day 10 onward with no upper limit, and needs only `PROMOTE_STREAK = 2` passes in a row. Simulated family-wise error under the global null (12 challengers, ρ = 0.5 shared noise):

| horizon | FWER, normal | FWER, t3 |
|---|---|---|
| 30 days | 0.107 | 0.083 |
| 60 days | 0.135 | 0.125 |
| 120 days | 0.228 | 0.155 |

The real FWER is 2-4× the stated 0.05, and it keeps rising. The streak helps, but it is not a sequential correction.

**T4. Challenger power is low; only huge effects get detected. MEDIUM (probe).**
Power at Bonferroni α/12, effect measured as daily mean difference / daily sd of the difference:

| effect | n = 10 days | n = 20 | n = 40 |
|---|---|---|---|
| 0.25 sd | 0.03 | 0.05 | 0.13 |
| 0.5 sd | 0.09 | 0.27 | 0.66 |
| 1.0 sd | 0.47 | 0.90 | — |

Realistic grid neighbours (m1.5 vs m2.0) differ by well under 0.5 sd/day. So the champion stays in place mostly by default, which is safe, but the documents should say so. Combined with T3, the loop is low-power and leaky at the same time, because it tests the same null many times.

**T5. The LODO check is redundant in the paired test. LOW (probe + algebra).**
`_lodo_ok` (l.212-217) fails only if one day's difference exceeds the whole total. A sample with t ≥ 3.36 cannot contain such a day. Probe: 6,430 heavy-tailed samples passed the t threshold and **zero** failed LODO. It gives no protection there. It does add something in the advisor screen, which has no t-test. If a robustness check is wanted, use trimmed means, a sign/Wilcoxon test, or "drop the best 2 days".

**T6. The KILL-replacement step skips every test and picks the max. MEDIUM (read).**
`learning.py:289-298`: after a KILL, the new champion is `max(sum(x))` over all non-retired variants. `x` is taken across **all** recorded days, not `> registered` or `> champion_since`. The only filter is "not below its own kill line". That is a winner's-curse pick from 12 correlated records. Summing ret% (not log growth, not a mean) also favours the variants that trade most (m1.5). Fix: pick the variant with the best log-growth record by paired test against the retired champion, or restart with CHAMPION_DEFAULT's nearest neighbour as a pre-registered order.

**T7. The control comparison reuses the data that selected the champion. MEDIUM (read, l.323).**
The controls are compared "since registration" over the current champion's whole history. After a promotion, that history includes the days on which it won the promotion, so the comparison is biased towards "champion beats it". Also, "beats all three nulls" is an intersection-union claim, which is valid with each test at α. The Bonferroni α/3 at l.317 only costs power. Fix: compare against the controls since `champion_since`, at α each.

**T8. The advisor pipeline lets noise in cheaply and judges it unevenly. MEDIUM (probe + read).**
- The screen (l.337-350) has no variance term. With 13 null advisors (random 30 % vetoes, no effect), P(at least one becomes a CANDIDATE) was 0.55-0.83 and the mean was 0.8-1.8 false candidates (probe, 40-80 RAW trades, sd 10-20).
- The gated-book test then uses α / len(candidates) (l.352). With one candidate that is **α = 0.05**, against 0.0042 for variant challengers. It runs indefinitely with repeated looks (T3 again), and the count of advisors screened over time is never charged.
- Demotion (l.358) happens on any negative point estimate of the RAW gain, with no test. A real but small gate will bounce in and out.

Good design (gated book on fresh days after candidacy), weak thresholds. Fix: test gated books at α/13, one fixed family across all advisors ever screened, and require a significant reversal before demoting.

**T9. Minor issues (read).**
- `_day_ret` floors a −100 % trade at ln(1e-4) = −921 %/day. That is honest, but one such day dominates any t-test. Report it separately.
- `t_crit` bisects only up to 50. Fine for df ≥ 2, but at df = 1 (n = 2) the critical value at α/12 (~76) exceeds the cap, and 50 is returned. Harmless only because `CHALLENGER_MIN_DAYS = 10`.
- Under H1 the "undecided at 200 = KILL" branch almost never triggers, so it is not a real limit on run length.

## Good things
- **Pre-registered grid, nothing invented** (`config.py:89-113`, `learning.py:34`). That removes the biggest overfitting route.
- **Pairing on identical market days** (`paired_test`, l.220-232). Every book trades the same ticks, so the shared market noise cancels. This is the right design and is why T4 is not worse.
- **The gated book is judged out of sample** (l.364, `since = max(cands[a], champion_since)` with `d > since`). Screening data and decision data do not overlap. Good.
- **Log-growth day metric** (l.61-66), with a reason given for it. This is the correct quantity for all-in compounding; it just needs to reach the SPRT too (T1).
- **Exact Student t without scipy** (l.77-128). Matches scipy (audit doc) and avoids a normal approximation at df = 9.
- **Idempotent, once-per-evening state moves** (`first_look`, l.245; D-078); empty days recorded as 0 % (l.159-160), so there is no survivorship from missing days.
- **Controls as a first-class null** (D-065): rarely done, and it guards against "the exits do the work".
- **The report prints the observed sd** (l.263). The right instinct, but the fix it implies should come from the test itself (T2).

## Ideas from GitHub

1. **gostevehoward/confseq**, https://github.com/gostevehoward/confseq, MIT (opened: README, `src/confseq/betting.py`, `predmix.py`).
   - Idea: betting-martingale / predictable-mixture **confidence sequences** (Waudby-Smith & Ramdas). A one-sided test of "mean ≤ 0" for data bounded below needs no σ and stays valid under *any* number of looks.
   - Fit to Apex: per-trade r ≥ −100 %. The test wealth Πₜ(1 + λₜ·r) with predictable λₜ ∈ [0, 1) is the all-in paper account at fractional size. GO when wealth ≥ 1/α. That one change fixes T1, T2 and the repeated-look part of T3.
   - Where: replace `sprt_lines` in `learning.py`, numpy only (~40 lines, written from the paper's `lambda_predmix_eb` concept). Can be added first as an **observer** column in the report beside the Wald lines.

2. **bashtage/arch**, https://github.com/bashtage/arch, University of Illinois/NCSA (permissive) (opened: `arch/bootstrap/multiple_comparison.py`: `SPA`, `StepM`, `MCS`; stationary/circular block bootstrap).
   - Idea: Hansen's SPA / White's Reality Check and Romano-Wolf StepM. These test "is the best of k challengers really better than the benchmark", using a block bootstrap that respects the correlation between the 12 variants and serial correlation across days.
   - Fit to Apex: a less conservative and more powerful replacement for Bonferroni-over-12 (T3/T4) and for the T6 max-pick. Run StepM on the daily log-growth difference matrix (days × challengers) against the champion.
   - Where: `learning.py` §2, as an **observer** table first. The owner's PC lacks scipy and arch, so port the stationary bootstrap (~60 lines numpy) or run arch offline in `learn`.

## Top 3
1. **Make the scoreboard unit log growth and its boundary σ-free.** For now, switch the SPRT to per-trade ln(1+r) and print a predictable-mixture betting e-value beside it as an observer (G1). Pre-register that the e-value takes over if the observed sd is above 15 % after 30 trades. **S, before Monday.** It changes how the first sample is scored, and the current GO line has α ≈ 0.15-0.33 if sd is 15-30 %.
2. **Cap the looks.** Fix a look schedule for challengers and gated books (for example days 10, 20, 40, 80, with an O'Brien-Fleming-style spend), or use an e-value per challenger with e ≥ 12/α. Test gated books at α/13 across all advisors ever screened. Require a significant reversal before demoting. **S-M, before Monday** (constants and a few lines).
3. **Bootstrap multiple-comparison observer (StepM/SPA, G2) for challengers and the post-KILL pick.** Restrict the KILL pick and the control comparison to post-`champion_since` days (T6, T7). **M, later.**

---

# Member 04: Replay and backtest reproducibility

## Lens
Can a recorded day be replayed with the same decisions every time, and the same as live? I read `feed_replay.py`, `feed_core.py` (`Recorder`, `apply_packet`), the recorder hooks in `feed_breeze.py`/`feed_sim.py`, `engine_main.py`, `guard.py`, persistence in `paper.py`/`learning.py`/`ledger.py`, and `run_apex.py`, and looked for look-ahead.

**Tests** (private copies in `/tmp/council/04/`, each with its own shared-memory names and port; a first run paused by another member was discarded and re-run):
1. Recorded one sim day (`--speed 40 --seed 7 --record`): 6,560,755 packets, 469 MB gzip.
2. Replayed it twice at speed 40 (R1, R2; run concurrently, so competing for CPU as on a real evening).
3. Replayed a 09:15–10:05 cut twice in one folder (R3).
4. Replayed a crash-then-restart file (R4).

## Teardown

**F1. The multi-process replay is not deterministic. Two replays of the same file give different trades. CRITICAL.** Verified with R1 against R2.
- **Where:** `engine_main.py:708-709`. The engine sleeps `0.1/speed − loop time` on the wall clock and reads whatever the feed has written by then. It is not locked to the recorded timeline.
- **Measured (my probe added to the copy):** at speed 40 the engine's median step was 0.75–1.0 virtual seconds, and the 90th percentile 1.25–1.5 s. Live runs at 100 ms. So replay samples the 15-second impulse and run-score windows about 10 times more coarsely than live, and the sampling grid changes with CPU load.
- **Result:** across the two replays, **0 of 17 books matched.**

  | Book | R1 | R2 |
  |---|---|---|
  | futures_only | 85 trades, +705.3 pts | 81 trades, +753.8 pts |
  | straddle_spike | 41 trades, +287.2 pts | 43 trades, +253.4 pts |
  | m2.0_s0.5 | +91.8 pts | +86.9 pts |

  The same entry (09:59:03 PE 25100) exits at different prices. The original sim run against a replay differs too: m2.5_s0.5 has 1 trade in one and 2 in the other.
- **Why it matters:** "check a changed rule against real sessions" (`feed_replay.py:6-7`) fails when two runs of the *same* rule differ by about 5–15 % of P&L; variants and controls would be judged partly on scheduling noise.
- **Context:** the design asked for "lockstep + timed" replay (`01_MASTER_DESIGN.md:274`); only timed exists, and `05_STRENGTHENING.md:135` flagged it "not yet verified".

**F2. Replaying the same day twice adds the second run on top of the first. HIGH.** Verified with R3.
- **Where:** `engine_main.py:133`. `paper.load_books(day)` reloads `data/replay/paper/<day>.json` from the previous replay. The observer files (`ledger.py:122`, `extras.py:192`, `straddle_watch.py:299`) open in append mode.
- **Result after the second replay:**
  - futures_only went from 9 to 19 trades, and its capital from ₹2,43,195 to ₹6,04,644. The second run compounded on top of the first.
  - candidates went from 16 to 32 lines, and episodes from 21 to 43.
  - Learning logged "already learned — decisions not repeated".
- **Also:** state carries over between *different* replay days through `data/replay/learning/state.json`, so the result of a replay depends on which replays were run before it (D-053 isolates replay from live, but not one replay from another).

**F3. A feed crash followed by a supervisor restart leaves a tick file that replay cannot read past the crash. Replay then hangs. HIGH.** Verified with a probe and R4.
- **Where:**
  - `feed_core.py:338` opens the day file in gzip append mode (`"at"`).
  - `feed_breeze.py:571-578` re-raises the error, so the Recorder's daemon thread is killed before the gzip trailer is written. Up to about 1 s of queued packets is lost as well.
  - The restarted feed appends a second gzip member after the truncated one.
- **Result:** reading fails with `zlib.error: invalid block type`. In my probe, 4,978 of 8,000 lines were readable, and the 3,000 lines written after the restart were lost even though they are intact on disk.
- **The replay side makes it worse:** `feed_replay.py:61` catches only `(EOFError, OSError)`, and `zlib.error` is not a subclass of either. The replay feed dies, `feed_state` never reaches 7, and the engine waits forever. R4 hung until `timeout` killed it (exit 124), with no end of day and no learning.
- **Why it matters:** feed-crash days are exactly the gap days D-063 exists to study.

**F4. Feed outages are not in the recording, so replay rebuilds them differently. MEDIUM.** Verified by reading.
- **Where:**
  - `feed_replay.py:47` sets `feed_state=6` for the whole replay. The live states 1, 3 and 4 (connecting, reconnecting, dead) are never recorded.
  - `feed_replay.py:80` advances `now_ns` only when a record arrives. During a live websocket stall, the replay clock freezes (only `vix`/`chain` REST records move it), so the futures quote never looks stale.
- **What happens instead:** the blackout appears late, as "engine paused" when the 30 s jump arrives (`guard.py:50`), instead of as "stale" after 3 s. Clock-driven TIME exits inside the gap fire at the resume price in replay but at the stale price live.
- **Smaller recording gaps:**
  - `Recorder.dropped` (`feed_core.py:335`) is counted but never logged or written, so packets lost to a full queue disappear silently.
  - Sim recordings contain no `vix` records (`feed_sim.py:419`).

**F5. Recording order is not application order. MEDIUM.** Verified by reading, not reproduced.
- **Where:** `feed_breeze.py:404-407`. `recv` is stamped before the lock, `apply_packet` runs under the lock, and `rec.put` runs after the lock is released. The SDK dispatches each packet on its own thread, so two packets can be applied as A then B but recorded as B then A.
- **Effect:** the recorded timestamps can go backwards. The `ttq` monotonic guard (`feed_core.py:266`) then drops a different packet in replay than it dropped live, so rows differ from the very first packet. Since `on_message` already holds the lock, moving `rec.put` inside it fixes this.

**F6. Nothing records which code and state produced a recording. MEDIUM.** Verified by reading.
- A tick file holds packets, registry, chain and VIX. It does not hold the git commit, a hash of `VARIANTS`/`CONTROLS`, or the live learning state at the open (champion, gates, candidates).
- So a replay of Monday runs with whatever champion `data/replay` happens to hold, and "the same decisions as live" cannot be reproduced even in principle. `cmd_learn --mode replay` also learns the *wall* date (`run_apex.py:305`), not the replayed day.

**Low:**
- Fixed shared-memory names (`config.py:38-39`) plus the port check mean yesterday cannot be replayed while live is running.
- A 469 MB gzip per sim day may not sustain high replay speeds (unverified for live-sized days).
- No look-ahead found: `now_ns` is set before each packet is applied, the chain is stamped on arrival, the random control is seeded per day and book, and learning reads only finished days. The only skew is the snapshot running up to (loop time × speed) ahead of `now_s`.

## Good things
- **One parser** (`apply_packet`, `feed_core.py:242`) for live, sim and replay, fed the raw Breeze list, so a parser fix can be replayed over old days.
- **Non-blocking hot path:** only `put_nowait` (`feed_core.py:329-335`).
- **Registry snapshots in the stream**, and `load_registry` resets history when row ids move (`engine_main.py:103`).
- **Deterministic random control:** `random.Random(f"{day}:{name}")` (`paper.py:229`).
- **Learning dedupes by day** (`learning.py:153-176`), which kept F2 out of the learning state.
- **The engine-pause guard** (`guard.py:50`) is the right defence against a sampling hole, and it is tested.
- **Sim `--gap` and `--record`** make fixtures possible without a broker login.

## Ideas from GitHub
1. **QuantConnect/Lean** (Apache-2.0), https://github.com/QuantConnect/Lean, file `Engine/DataFeeds/SubscriptionSynchronizer.cs` (opened). Frontier clock: consume data only while `EmitTimeUtc <= frontierUtc`, build one slice, then step the algorithm. **Apex mapping:** a **tool**, `apex/replay_lockstep.py`, running in one process. It builds `Table` and `Engine` in-process, applies packets with `t ≤ k·100 ms`, calls `Engine.step()` once per 100 ms of virtual time, and skips `publish()` and the sleeps. This fixes F1 and is the base for the twice-identical test.
2. **nautechsystems/nautilus_trader** (LGPL-3.0, concept only), https://github.com/nautechsystems/nautilus_trader, file `crates/common/src/clock/virtual.rs` (cloned). `VirtualClock.advance_time` returns due timers "in ascending order by event timestamp and timer name" and panics if time goes backwards. **Apex mapping:** in the lockstep tool, make the 4 Hz Greeks, the 1 Hz history and the 15:31 end of day ordered virtual timers, and add a **replay assertion** that recorded `t` never decreases (detects F5).
3. **databento/dbn** (Apache-2.0), https://github.com/databento/dbn, README (opened). A "self-describing metadata header" on every data file. **Apex mapping:** the `Recorder` writes a first `meta` record (schema version, git commit, a hash of `VARIANTS`/`CONTROLS`/guard constants, the learning state at the open) and a closing one with `dropped`. Replay seeds its run folder from the header and warns when the code hash differs (F6).

## Top 3
1. **Self-describing, crash-safe recordings** (S, **before Monday**: the first live file cannot be fixed after it is written). Add the `meta` header; open a new part file on every Recorder start instead of appending a gzip member; write `dropped`; add a 250 ms `hb` record with `feed_state` (F4); move `rec.put` inside the lock (F5); in replay, also catch `zlib.error` and still set `feed_state=7`.
2. **One folder per replay run** (S, **before Monday**): `data/replay/<file-stem>-<run-timestamp>/`, seeded from the `meta` learning state, so a replay never resumes another replay's books, ledger or learning (F2).
3. **Lockstep replay plus a twice-identical CI test** (M, **later**, but before any rule change or advisor is judged on replayed days). Use Monday's recording as the fixture, and assert byte-identical `paper/<day>.json` and `candidates_<day>.jsonl` across two runs (F1).

---

# Member 05: Live data feed and Breeze integration

## Lens
`apex/feed_breeze.py`, `apex/feed_core.py`, `apex/universe.py`, plus how `run_apex.py` (supervisor, preflight) and `feed_replay.py` handle what the feed writes. I checked every SDK assumption against the `breeze-connect` 1.0.69 sdist and the installed engineio 4.14 / socketio 5.17. Probe scripts are in `/tmp/council/05/probe/`. Monday 19 Oct is the **first live session**. It is also a **0DTE expiry**: Tuesday 20 Oct is a holiday, so the weekly expiry moves to Monday. `weekly_expiries` handles that correctly (19-Oct, 27-Oct). There is no `token_cache.json` yet, so the first build resolves everything from scratch. Tests: 28/28 pass.

## Teardown

**T1. A feed crash followed by a same-day restart corrupts the day's recording, and replay then crashes. HIGH. Verified by probe.**
`feed_core.py:209-236` opens `data/ticks/<day>.jsonl.gz` in append mode inside a *daemon* thread. When the feed dies:
- `main()` re-raises at `feed_breeze.py:575-577`. The `SystemExit` at `:359` is one example.
- The supervisor's `terminate()` fires after 12 s (`run_apex.py:105-113`). The feed can easily overrun 12 s while it sits in `connect()` backoff (`:433-446`, up to 30 s sleep plus a 15 s wait).

In both cases the gzip member is never closed. The supervisor then respawns the feed (`run_apex.py:92-98`), which appends a new member behind the broken one. Probe `w.py`: a crashed run followed by a clean run gives `zlib.error: invalid block type`. Every line from the restarted run is unreadable (771 of 1,771 read). `feed_replay.py:61` catches only `(EOFError, OSError)`, and `zlib.error` subclasses neither, so replay dies with a traceback. Effect: one mid-day feed restart loses the rest of the day's recording, and that recording is the input to the learning loop's replay. Fix (S): open a new file per feed process (`<day>.<pid or n>.jsonl.gz`) and have replay read them in order. Also catch `zlib.error`.

**T2. An empty security master gives "websocket LIVE" with zero instruments. HIGH. Verified by probe.**
The SDK's `get_stock_script_list` swallows every download error and leaves empty dicts (sdist `breeze_connect.py:892-967`). After that, every `get_stock_token_value` returns `'4.1!False'`. In that case `build()` (`feed_breeze.py:337-380`) still succeeds as long as the REST spot works. Probe `p1.py` case A: `0 instruments`, `subscribe_all()` returns `True` (`:419-429`, because `bad == 0`), so `connect()` sets `feed_state=2` and logs "websocket LIVE". The 30 s watchdog then reconnects forever while the dashboard says LIVE. Fix (S): `build()` should `SystemExit` when `NIFTY|FUT` or fewer than about 40 options resolved. The supervisor then retries, which re-downloads the master.

**T3. Hero contracts lose depth as soon as Nifty drifts, and re-centering never adds it back. MEDIUM. Verified by probe.**
Depth is requested only for strikes within ±3 of the *build-time* centre (`feed_breeze.py:387`). The engine's heroes are ATM ±2 of the *current* ATM (`engine_main.py:384-394`). After a 100-point move, the far-side heroes have no depth. Re-centering waits for 4 strikes (`config.RECENTER_STRIKES`), and even then `Registry.add` on an existing key only flips `depth=True`. It never stores the new `depth_token` (`feed_core.py:65-69`), so `subscribe_all` never joins it. Probe case B: after re-centering 25000→25200, strikes 25200 and 25250 show `depth=True, depth_token=None, subscribed=False`. `market.py:48-56` then falls back to best-level quantity with `sbo/sso = NaN`. The order-count classes (PULLED/REFILLING by orders) vanish on exactly the contracts the book exit and coherence read. On a 0DTE Monday, 100 to 200 point moves are normal. Fix (S): in `Registry.add`, set `it["depth_token"]` when an existing item gains depth. Re-centre depth on every 1-strike ATM change, or widen depth to ±5.

**T4. Packets are applied in arbitrary order; only quotes with a rising `ttq` are guarded. MEDIUM. Verified by reading.**
engineio runs every message in its own thread (`engineio/client.py:436`, `run_async=True`). `apply_packet` drops a quote only when `ttq` goes backwards (`feed_core.py:152`), which leaves three gaps:
- Depth packets (`:182-195`) have no ordering guard at all. An older 5-level snapshot can overwrite a newer one, which makes up a "drain" or "refill" in `flow.py`.
- Index quotes (NIFTY, VIX, and the BANKNIFTY and FINNIFTY indices) have `ttq` 0, so they are never guarded either.
- `rec.put` runs outside the lock (`feed_breeze.py:407`), so the recording order is not the order the packets were applied, and replay is not bit-identical to live.

Fix (S): guard depth on `raw[1]` (exchange epoch) and quotes on `ltt` as a tiebreak. Move `rec.put` inside the lock.

**T5. Login can hang with no timeout and no log line. MEDIUM. Verified by reading.**
The `requests` timeout patch (`feed_breeze.py:298-303`) does not cover the SDK's `urlopen(SECURITY_MASTER_URL)`. That call runs once at import (sdist line 32) and again in `generate_session` (line 898), with no timeout, and the same function then runs a third full `requests.get` of the zip. A slow `directlink.icicidirect.com` leaves the feed stuck in state 1 (connecting), with nothing written to `feed.log` between "starting" and "session established". Fix (S): set `socket.setdefaulttimeout(60)` before importing `breeze_connect`, and log before and after `generate_session` with elapsed seconds.

**T6. A feed restart re-numbers the instrument rows, and the engine throws away its warm state. MEDIUM. Verified by reading.**
`BreezeFeed.__init__` zeroes the whole table (`:235`). `build()` assigns ids in build order, and option ids depend on the *new* band centre. Any mid-day restart therefore makes `moved` true in `engine_main.py:104-109`. That resets `Market`, `Flow`, the greeks and the IV/OI history, which means another 10-minute warm-up (`WARMUP_S`) right after an outage. Fix (M): seed the registry from `instruments.json` when it is from today, keeping ids and appending only new keys.

**T7. Likely spurious reconnect at 09:15:00. LOW. Unverified: depends on whether Breeze streams pre-open data.**
`run()` checks silence only inside 09:15 to 15:30 (`:520-525`). If nothing arrived between about 09:08 and 09:14:30, the first loop pass at 09:15:00 sees more than 30 s of silence and tears the socket down just as the open prints. That costs `sleep(1)`, the handshake and three join batches, roughly 3 to 5 s. Fix (S): start the watchdog at 09:15:30, or reset `last_msg` when the session opens.

**T8. Small items. LOW. Verified by reading.**
- `HotStats.add` runs on many threads outside the lock (`:408`). Two threads can run the 1 s roll-up together, and `np.fromiter` over a deque being appended to raises "deque mutated". The stats glitch, but the packet is not lost.
- The poller spends REST calls outside market hours. The ledger never rolls its day (`:202`), so a feed left running overnight carries yesterday's count.
- On first run, `isec()` calls `get_names` (a pandas CSV parse of the master) for all 23 symbols, including the 14 that have hints. That is slow, but it only happens once.

## Good things
- `connect_stream` (`feed_breeze.py:148-181`) registers `connect_error` *before* connecting, waits 15 s and keeps the server's reason. `stream_probe` and `stream_hint` turn "Failed to connect to live stream" into an actionable cause. This is the right fix for the 16 Oct failure.
- `drop_stream` really tears the socket down, where the SDK's `ws_disconnect` only emits an event. The client is never reused (`:184-193`, `:435`).
- The hook replaces `SocketEventBreeze.on_message` *before* `watch()` binds `self.on_message` (SDK line 144). So the raw-array hot path works, and the SDK's `rewatch` on auto-reconnect still re-joins the tokens.
- One parser (`apply_packet`) feeds live, sim and replay. Segment disambiguation by length (21 vs 23) is correct against the SDK's `get_data_from_stock_token_value`. The `'4.1!False'` sentinel is handled (`:269`). The `breeze.interval = ""` workaround for the SDK's missing attribute is correct.
- `RestLedger` is persisted per day and gives a per-minute window. `rest_expiry` and `ws_expiry` are locale-independent.
- Preflight (`run_apex.py:233-300`) resolves NIFTY futures and today's ATM CE token from the actual master before the open. It would catch a strike or expiry format mismatch, a risk I could not check offline because the master download is blocked here.

## Ideas from GitHub
1. **zerodha/pykiteconnect**: https://github.com/zerodha/pykiteconnect, MIT. Cloned and read `kiteconnect/ticker.py`.
   - What it does: `_loop_pong_check` (lines 118-135) drops a "ghost" connection when the last pong is older than 2×`PING_INTERVAL`. Reconnects use exponential backoff capped by `reconnect_max_delay`, with an `on_noreconnect` callback, and `_on_connect` calls `resubscribe()`.
   - How it maps onto Apex: a **feed-side tool** in `feed_breeze.py`. Replace the single 30 s market-wide silence check with two signals: (a) transport liveness from `h.sio.eio` ping/pong age, which catches a dead socket within about 5 s even in quiet pre-open; (b) per-segment silence across futures, options and equities, which catches the server silently dropping one batch of joins. Publish both as observer fields in the control block. No trigger change.
2. **marketcalls/openalgo**: https://github.com/marketcalls/openalgo, **AGPL-3.0, concept only, no code copied**. Read `websocket_proxy/connection_manager.py`.
   - What it does: it pools several websockets per broker under a per-socket symbol cap (`MAX_SYMBOLS_PER_WEBSOCKET`). It classifies connect and subscribe failures by auth keywords (401/403/token-expiry) and forces a re-init that reads fresh credentials, separate from plain network retries.
   - How it maps onto Apex: (a) extend `stream_hint` into a typed outcome (AUTH / NETWORK / SERVER). On AUTH, `connect()` should stop the 7-attempt loop at once, set `feed_state=4`, and show "regenerate session token" on the dashboard rather than retrying for 2½ minutes. (b) Keep the option of splitting joins across two sockets if the Breeze per-socket cap turns out to be lower than the ~145 tokens (rising with each re-centre) Apex needs. That cap is unverified: ICICI's README does not state one.

## Top 3
1. **Make the recorder crash-safe:** a new file per feed process, and replay catches `zlib.error` (T1). Size S. **Before Monday.** Today, one mid-day feed restart silently destroys the rest of the first live recording.
2. **Fail loudly on an empty or partial registry and on a login hang** (T2 + T5): `SystemExit` if `NIFTY|FUT` or fewer than 40 options resolved, a socket default timeout, and timed log lines around `generate_session`. Size S. **Before Monday.**
3. **Fix hero depth** (T3): store `depth_token` on existing keys and re-centre depth with the ATM. Then add ordering guards on depth and index packets (T4). Size S to M. **Before Monday** for T3; later for T4.

---

# Member 06: Concurrency, shared memory and process supervision

## Lens
I looked at `apex/table.py` (the row seqlock, `snapshot()` and `StateBlob`), `run_apex.py supervise()`, how the feed, engine and gateway attach and restart, how shutdown works, and the Windows-specific behaviour of shared memory and files. I wrote and ran probe scripts in two real processes (`/tmp/council/06/probe*.py`, Python 3.13, numpy 2.5, 2 cores). `tests/test_core.py` passes.

## Teardown

**T1. `snapshot()` hands back torn rows, and its retry hardly ever fixes them. Severity: medium. Verified by probe.**
In `table.py:131-137`, the three re-reads run back to back with no pause. A Python-level row write (`apply_packet`, about 20 numpy scalar stores) takes tens of µs, so all three retries usually land inside the same write. After the loop the row is returned anyway, with no mask saying it is bad.
- Probe with one row written non-stop: **18 % of snapshots returned a torn row 0** (fields from two different ticks), and 24 % returned an odd `seq`.
- Probe with 200 rows round-robin and a 10 Hz reader: 1 torn row per 283 snapshots at a 50 ms writer gap, and 41 per 158 at zero gap.
- Failure scenario: the futures row mixes the new `ltp` with the old `bid`/`ask`/`ltt`. The result is a momentary fake spread or price that reaches Market, the Flow deltas and the DataGuard spike test.
- Fix, verified: put `time.sleep(0)` between retries, test `before & 1`, and return the indices that are still unresolved. The probe then gave **0 torn rows accepted** out of 195, with 1 row correctly flagged.
- `gateway.py:80-91` has the same flaw. It checks `seq` and then copies `rows[ch]` without checking again, so torn ticks reach the browser. That one is display only.

**T2. An exception between `begin()` and `end()` flips the row's parity for good. Severity: medium. Verified by probe.**
`feed_core.py:184-194` (the depth branch) calls `len(lv[k])` with no try/finally. A depth level of `None` raises `TypeError` while `seq` is odd.
- The probe confirmed it: `seq` is 1 after the exception and 3 after the next good quote. From then on every stable state of that row looks "mid-write" and every real mid-write looks stable.
- The gateway filters out odd rows (`gateway.py:82`), so that contract freezes on the dashboard. The engine's `snapshot()` accepts the real torn copies.
- The exception also escapes `on_message` into the SDK thread (`feed_breeze.py:406`).
- It only clears when a live feed restarts, because `feed_breeze.py:235` zeroes the rows. In sim and replay it never clears.

**T3. Nothing checks whether the processes are still alive and working. Severity: medium-high. Verified by read and grep.**
- `engine_hb_ns`, `feed_hb_ns` and `gateway_hb_ns` are written (`engine_main.py:705`, `feed_breeze.py:518`, `gateway.py:101`), but no code reads them: grep finds no reader in Python or in `app.js`.
- `supervise()` only calls `poll()` to see whether a process has exited (`run_apex.py:85-100`). A hung engine is never restarted.
- The dashboard keeps serving `LAST_STATE` with no age shown. `app.js:46,74` only reconnects when the websocket closes.
- Failure scenario: the engine hangs or wedges with an open paper position. The dashboard looks normal while the exits stop running.
- `StateBlob.write` silently throws away an oversized state (`table.py:165-166`), which produces the same symptom with nothing in the log.

**T4. An engine restart loses the trailing-stop state of an open trade. Severity: medium. Verified by read.**
- `pos["best"]`, `pos["trail"]` and `peak_pts` change on every step (`paper.py:353-362`).
- `save_books` only runs when an entry or exit happens (`engine_main.py:549-586`).
- `run_apex.py:87` says "books are on disk", but after a live restart `start_day` reloads `pos` as it was at entry. A trade that had already switched to the trailing stop drops back to the wide initial stop.

**T5. The shutdown kill window can truncate the whole learning history. Severity: medium. Verified by read.**
- `run_apex.py:105-117` gives feed and engine one shared 12 s deadline. It waits for the feed first, whose Recorder join can take up to 5 s, then for the engine. After that, `terminate()` runs, which is a hard `TerminateProcess` on Windows.
- After 15:30 the engine's stop path runs `end_day()`, which calls `learning.record_day`. That function rewrites **all of `days.jsonl` in place** with `open(DAYS, "w")` (`learning.py:175`), not tmp+replace.
- A kill in the middle of that write leaves the multi-day record truncated. Closing the console window has the same effect: Windows sends CTRL_CLOSE_EVENT and hard-kills after about 5 s.

**T6. Two save paths have no Windows retry. Severity: low-medium. Verified by read.**
- `feed_core.py:41` has a `replace_retry` helper, but `paper.save_books` (`paper.py:438`) and the learning state (`learning.py:150`) call plain `os.replace`.
- On Windows, antivirus, the search indexer or OneDrive can briefly hold the destination file, which raises `PermissionError`.
- Inside `run_books` that exception lands after the exit is already applied in memory. The `changed` flag is then lost, so the exit is not on disk until the next entry or exit.

**T7. The restart policies are crude. Severity: low. Verified by read.**
- The engine is respawned with no backoff and no limit (`run_apex.py:85-88`). A crash at import becomes a 1 Hz respawn loop that keeps appending to `engine.log`.
- The feed's `restarts` counter never resets. After about 12 restarts, every later death waits 60 s, and 90 s once it passes 20, even if the previous run was healthy for hours.
- In sim and replay a feed crash goes unnoticed. The engine waits forever for `feed_state == 7` (`engine_main.py:706`).

**T8. Linux only: a second instance can replace a segment that is still in use. Severity: low. Verified by read.**
`_open(create=True)` unlinks a live segment (`table.py:69-76`). On POSIX that lets a second instance start next to orphaned children, with two engines then writing the same paper files. The port check catches this only while the orphaned gateway is still running. Windows correctly raises `FileExistsError` here.

**T9. Possible but not observed: the `StateBlob` header may not be atomic. Severity: low, unverified.**
`seq` and `len` are written with one 12-byte `pack_into`, which is not guaranteed atomic, so a reader could pair a new `seq` with an old `len`. A probe hammering it read 3,067 frames with 0 invalid JSON.

## Good things
- **Clean single-writer layout.** There is one writer per segment, fixed-layout numpy rows, and a `u8` seq that cannot wrap round to an old value (no ABA). The gateway skips work when `gseq` has not changed (`gateway.py:76-78`). Every field is 8 bytes, so they all sit on 8-byte boundaries and x86 reads each one whole.
- **Windows shared-memory handling is right.** `track=False` keeps the 3.13 resource tracker from unlinking the segment (`table.py:77-84`). The Windows `FileExistsError` is turned into an actionable message (`run_apex.py:61-65`). The supervisor keeps a handle for the whole session, so the segment never disappears under the children.
- **Clean stop.** The children ignore SIGINT and stop through the `ctrl.stop` flag. The feed also handles engineio re-installing SIGINT (`feed_breeze.py:528`).
- **Row renumbering is handled.** Positions are tracked by contract key, not row id (`paper.py:343-348`). The engine detects renumbering and resets its price history (`engine_main.py:101-108`). A live feed restart zeroes the rows, which also resets their parity.
- **Atomic writes where they exist.** The registry and chain use atomic writes with a Windows retry (`feed_core.py:41-49, 94`). `record_day` and `learn` are idempotent per evening, and a test covers it.
- **The feed heals itself.** It reconnects after 30 s of silence in market hours and genuinely tears down the old stream (`feed_breeze.py:450-455, 520-523`).

## Ideas from GitHub
1. **rigtorp/Seqlock**, https://github.com/rigtorp/Seqlock, MIT (cloned).
   - What to borrow: in `include/rigtorp/Seqlock.h`, `load()` loops `while (seq0 != seq1 || seq0 & 1)` until it gets a clean copy, and `store()` is a single function that bumps `seq` on both sides of the write.
   - Where it goes (tool/infra, deployed between sessions): wrap `Table.begin/end` in one `write_row()` context manager (with `finally: end`). Give `snapshot()` a bounded, yielding retry that returns a `bad` mask; the engine reuses the previous frame's row for any masked row.
2. **Supervisor/superlance**, https://github.com/Supervisor/superlance, BSD-style repoze licence (cloned). This is a concept borrow.
   - What to borrow: `superlance/httpok.py`, which on a TICK event checks a process's health and restarts it if it is unhealthy, even though it never exited.
   - Where it goes (an observer plus the supervisor): `supervise()` reads `engine_hb_ns` and `feed_hb_ns` every second. If a heartbeat is older than 10 s in market hours, it logs, terminates and respawns that process. It also publishes `hb_age` for a red "ENGINE STALE" banner.
3. **untitaker/python-atomicwrites**, https://github.com/untitaker/python-atomicwrites, MIT (archived, cloned).
   - What to borrow: `atomicwrites/__init__.py`, which fsyncs the temp file and then calls `MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH)` on Windows.
   - Where it goes: one `atomic_write(path, text)` helper in `feed_core`, with `replace_retry`, used by `record_day`, `save_books`, the learning state and the report. That closes T5 and T6.
4. **tox-dev/filelock**, https://github.com/tox-dev/filelock, MIT (cloned).
   - What to borrow: the exclusive cross-platform lock file (`src/filelock/_windows.py` uses `msvcrt.locking`).
   - Where it goes: `supervise()` holds `data/<mode>/apex.lock` for the whole session. That guarantees one instance per data directory on any OS, whatever the shared-memory semantics (T8).

## Top 3
1. **A heartbeat watchdog in `supervise()` plus a dashboard staleness banner** (T3, with T7 backoff and reset). Size M, **before Monday**.
2. **Seqlock hardening**: a try/finally writer, a yielding snapshot retry that returns a bad mask, and a re-check in the gateway (T1, T2). Size S, **before Monday**. The fix has already been validated by probe.
3. **Durability** (T4, T5, T6):
   - Save books when `best` or `trail` changes, throttled to 1 Hz.
   - Make `days.jsonl` atomic.
   - Give the engine its own shutdown deadline and wait for it first.
   - Use `replace_retry` everywhere.

   Size S/M, **before Monday**. The `days.jsonl` part alone is S.

---

# Member 07: Software architecture & maintainability

## Lens
Module boundaries, `apex/engine_main.py` as orchestrator, coupling through the `ctx` dict, duplicated logic, error handling, `config.py` design, and how safely an advisor or variant can be added. Baseline 85b65ed; all 31 tests pass. Probes ran on a private copy (scratchpad `m07/repo`), with private shared-memory names `m07_tbl`/`m07_st`, the sim feed running in-process, and no gateway or port. The ApexOptions tree was not touched.

## Teardown

### T1. One failing advisor stops every exit while an episode is live, and the heartbeat says all is well. Severity: HIGH (verified, probe)
- `engine_main.py:283-287`: `advise()` runs before `run_books()` inside `step()`, with no guard of its own. Eleven of the thirteen advisor computations (`advise()`, lines 405-453) call sub-objects such as `self.watch.advise`, `self.gex.advise`, `self.regime.advise`, `self.straddle.view()` and `self.force.view()`. Any exception from them propagates up to the catch-all at `run()` lines 701-703, which logs, sleeps 0.5 s and loops.
- That makes the error policy inconsistent. regime (238), watch (255), gex (472) and ledger (290) are wrapped as "observers: never stop the loop", but the **advisors are observers too** (D-033: logged only, never voting unless promoted), and they sit unguarded in front of the code that manages positions. The same holds for `straddle.update`, `bank.update`, `lag.update` and `force.update` (250-262).
- Probe (scratchpad `m07/probe.py`): sim at 60x, seed 7. After the first paper entry, `advise()` was forced to raise. Result: 685 steps, `run_books` ran only 373 times, and **312 steps skipped all exits**. The `premium_momentum` position stayed open about 62 s of wall time (roughly an hour of sim time) while futures moved **99 points against it**, with `d_star = 12`. Exits only came back when no episode was live, because `advise()` is called only when `ctx["episode"]` exists. That is the worst case: exits are blocked exactly while price is moving.
- Compounding it, `engine_hb_ns` is written every loop, even right after the exception (705), and nothing reads it (`grep`: only `table.py:44` and `engine_main.py:705`). `run_apex.py:85` restarts the engine only on process exit. An engine stuck in this failure loop looks healthy to both the supervisor and the dashboard.
- In paper mode this corrupts the books and the learning record: the stop and trail never fire, and the learning loop then scores those trades.

### T2. Advisor names live in three hand-kept lists, and nothing cross-checks them. Severity: MEDIUM (verified, read + probe)
- They are produced as dict keys in `engine_main.py:405-453`, consumed in `learning.py:49` (`ADVISORS = [...]`), and labelled in `static/app.js:147`. If you add `a["new"]` in `advise()` and forget `learning.ADVISORS`, the advisor is logged on every trade but **silently never screened**. `config.validate()` cannot catch this; the probe confirmed `'my_new' in learning.ADVISORS` is False and no check fails.
- Related statistical flaw caused by the structure: there is one global `REGISTERED = "2026-10-17"` (`learning.py:50`), and the screen reads every RAW trade since then (330). Trades from before an advisor existed have no key for it, so `t["advisors"].get(a)` is falsy (338) and they count as "kept, not vetoed". A late-added advisor therefore reaches `n >= 30` on trades it never saw, and its `gain` and `top_v` are diluted by them. The repo has no per-advisor registration date. The D-033 "pre-registered" discipline is enforced for variants, but not for when an advisor started.

### T3. Variant behaviour is a set of loose flags read with `p.get(...)` in five functions, and the config check accepts typos. Severity: MEDIUM (verified, probe)
- The flags `spike`, `random`, `momentum`, `gap_star`, `exit_book` and `s_exit` are tested in `paper.py:69,102-105,142-156,169,313,370,372`. Adding a new kind of variant means editing `entry_dir`, `choose_contract`, `evaluate_entry`, `open_trade` and maybe `check_exit`. Precedence between flags is set only by the order of the `if` statements.
- `config.validate()` (270-304) checks that the four required keys exist and are in range, but never rejects unknown keys or conflicting flags. Probe: registering `{'exit_bok': True}` (a typo) and `{'spike': True, 'random': True}` both returned `validate() -> []`. The first silently becomes a clone of `m2.0_s0.5`, which spends a challenger slot and also inflates the Bonferroni divisor (`learning.py:271`) for every real challenger. That is a statistical cost, not only a code-style one.

### T4. `ctx` is an untyped bag of about 20 keys, and its contract is held only by convention. Severity: MEDIUM (read)
- It is built in `engine_main.py:265-278` and read through `ctx["..."]` and `ctx.get(...)` in paper, ledger (`ledger.py:79`), extras (`extras.py:177`) and the variant evaluators. Some keys are read with `[]` (`ctx["advisors"]`, `ctx["domino"]["dir"]`, `ctx["by_key"]`) and others with `.get` and a default, so a renamed key gives either a `KeyError` (which leads straight into T1) or a silent `None`. Nothing documents which module owns which key.
- `advise()` also reaches past `ctx` into engine state: `self.greek`, `self.pressure`, `self.domino.state`, `self.day`. So an advisor cannot be tested from a `ctx` snapshot or replayed from the ledger.

### T5. The orchestrator has no tests, and its state is created lazily. Severity: MEDIUM (verified, grep)
- `tests/test_core.py` never imports `engine_main`. All 31 tests exercise leaf modules, so the step ordering in T1 (the most safety-relevant sequence in the system) has no coverage.
- `Engine` creates many attributes on demand (`getattr(self, "atm"/"atm_iv"/"fwd"/"ledger"/"regime"/"_learned"/"_reg_err"…)`, and `self.key` and `self.opts` are never set in `__init__`). Each `getattr` default hides an ordering assumption. `compute_greeks` sets `self.atm_iv = getattr(...)` on every call (332), which is a sign the initialisation belongs in `__init__`.

### T6. Small duplications that will drift. Severity: LOW (read)
- The "for g in gates: veto → return" loop is copied three times (`paper.py:184,210,294`).
- The instrument key format `f"NIFTY|OPT|{w0}|{K}|{rr}"` is built in three places (`engine_main.py:391,482`, `paper.py:88`).
- The "log once a minute" error throttle is copied four times with four ad-hoc attributes (`_reg_err`, `_watch_err`, `_gex_err` using `time.time()` where the others use `now_s`, and `_led_err`).

## Good things
- **A clean process split.** feed → shared memory → engine → blob → gateway (`table.py`, `run_apex.py:57-61`). The engine can be restarted alone because the books are on disk (`run_apex.py:87`, `paper.save_books`, saved atomically via `os.replace` at 433-438).
- **`learning.py` is pure, file-in and file-out**, has no engine dependency, and writes its state atomically (146-150). It is idempotent per evening (`looked_day`/`learned_day`, with a test). This is the best-bounded module.
- **`config.validate()` plus preflight** (`run_apex.py:176`). The design is right; it just needs to check more (T3).
- **Exit logic matches contracts by key, not row id** (`paper.py:343-348`), which survives a feed restart that renumbers rows. Registry re-numbering resets history on purpose (`engine_main.py:102-108`).
- **Controls and gated books reuse the ordinary `Book`.** Champion, RAW, controls and `gate:<a>` books all go through one `run_books` path (548-586), so every null hypothesis is tested on identical code.
- The deterministic random-control schedule (`paper.py:226-239`) keeps replays reproducible.

## Ideas from GitHub (all opened or cloned into /tmp/council/07/)

1. **pytest-dev/pluggy** (https://github.com/pytest-dev/pluggy, MIT). Borrow the "hookspec plus registration-time verification" idea from `src/pluggy/_manager.py:_verify_hook` (lines 429+, which rejects implementations whose arguments are not in the spec) and `check_pending()` (479).
   - Map onto Apex as a small **advisor registry** (`apex/engine/advisors.py`). Each advisor is declared once with `name`, `registered` date, `label` and `fn(view) -> (veto, why)`. `learning.ADVISORS`, the `app.js` labels (served via the state blob) and the per-advisor screen start date are all derived from it.
   - That fixes T2 at the root. You don't need pluggy itself, only its "declare once, verify at load" pattern, which can be copied freely under MIT.

2. **nautechsystems/nautilus_trader** (https://github.com/nautechsystems/nautilus_trader, LGPL-3.0, so borrow the concept only and copy no code). From `docs/concepts/actors.md:83-102`, take the component state machine RUNNING → DEGRADED → FAULTED with `on_degrade`/`on_fault`.
   - Map onto Apex: each observer and advisor runs in its own guard. On an exception it becomes DEGRADED, and its output is replaced by `{"veto": False, "why": "advisor faulted", "faulted": True}`. That flag is stored with the trade, so learning can exclude faulted rows.
   - The engine itself goes FAULTED only when the core path fails (market, domino, books). This is the systematic fix for T1. Keep the "faulted" flag out of the trigger: it is a recorded state, not a vote (I-11 safe).

3. **pydantic/pydantic** (https://github.com/pydantic/pydantic, MIT). Use `ConfigDict(extra='forbid')` (`docs/concepts/models.md:267-272`) and discriminated unions (`docs/concepts/unions.md:174,217`).
   - Map onto Apex as a **tooling/preflight change only**. Describe each variant with a `kind` tag (`trigger | gap | bookexit | spike | random | momentum`) and a typed model per kind, validated in `config.validate()`.
   - Typos and conflicting flags then fail preflight (T3), and `paper.py` can dispatch on `kind` instead of a chain of `p.get`.
   - pydantic is already present wherever the gateway runs, because fastapi depends on it. If the owner wants the engine to stay numpy-only, a twenty-line hand-written allowed-keys table gives 80 % of the benefit.

## Top 3 (ranked)

1. **Guard advisors and observers individually, and give the heartbeat meaning.** Size **S**, **before Monday**.
   - Wrap each advisor in `advise()` and each update in 250-262 in a shared `safe(name, fn, default)` helper, so a fault yields `veto False, faulted True` and `run_books` always runs.
   - Move `run_books` exits before advisors, or into their own try block.
   - Set `engine_hb_ns` only after a step succeeds, and have `run_apex.py` (or the dashboard) flag a heartbeat older than 5 s.
   - Add one test that injects a raising advisor and asserts that a stop still fires. This is the T1 probe made into a test.

2. **One advisor registry with per-advisor registration dates.** Size **M**, **later** (the change touches learning and must not change the decisions already recorded).
   - Derive `learning.ADVISORS` and the dashboard labels from the registry.
   - Screen each advisor only on RAW trades dated after its own `registered` date and carrying its key.
   - Add a `validate()` check that every advisor key `advise()` produces is registered.

3. **Strict variant schema in `config.validate()`.** Size **S**, **before Monday**.
   - Keep an allowed-keys set per variant kind, reject unknown keys, and reject more than one behaviour flag.
   - Then refactor `paper.py` to dispatch on a `kind` field and drop the three copied gate loops (later, size M).

---

# Member 08: Test strategy and test quality

## Lens
`tests/test_core.py` (28 tests, all pass). I asked which tests pass for the wrong reason, which critical paths have no test, and which property-based or replay tests are missing. Methods:
- I read the code.
- I ran a **mutation run**: 27 one-line breaks to safety-critical logic, with the full suite run against each (`/tmp/council/m08/mutate.py`).
- I ran unit probes (`/tmp/council/m08/probes.py`).
- I ran a headless sim with shared-memory names and the tick directory isolated (`/tmp/council/m08/e2e.py`, `run_mod.py`).

## Teardown

**T1 (critical, verified by mutation): the suite kills 1 of 27 mutants.** Only "remove the ttq monotonic guard" fails a test. The suite stays green after each of these breaks:
- Exits: the futures-stale gate, THESIS-VOID, the 0DTE 15:00 flatten, and the BOOK exit (`paper.py:370-395`).
- Entries: the once-per-episode check, the L* LATE check, the IV-rise cap, the synchrony check, the 09:25–15:15 window, and promoted gates (`paper.py:146-186`).
- Contract choice: the 0DTE delta band, and the age-<15 s quote filter (`paper.py:113,125`).
- Restart: `fired_episodes` not restored (`paper.py:52`).
- Feed parsing: an OI-zero overwrite, cash tbq/tsq swapped, cash ltt/close swapped (`feed_core.py:163,170-171`).
- Table: the snapshot seqlock re-read removed (`table.py:133`).
- Learning: LODO dropped, `already_learned` always False, `record_day` not idempotent (`learning.py:155,165,231`).
- Every engine wiring change: guard-taints-episode, `learn_scales=not guard.on`, history reset on renumber, end_day idempotence (`engine_main.py:104,159,231,242`).
- The replay clock (`feed_replay.py:80`) and the gateway's odd-seq filter (`gateway.py:87`).

The v1 trigger is frozen (D-033), but the only thing that holds it frozen is the tests, and today they would not notice the trigger being changed.

**T2 (high, read): the tests check copies of the glue code, not the engine.** No test imports `engine_main`, `gateway`, `feed_replay`, `feed_sim`, `ledger` restart behaviour, or `run_apex`. `test_reconnect_jump_cannot_fire` (`test_core.py:250-254`) re-types `engine_main.py:231-243` by hand: guard, then `domino.update(learn_scales=...)`, then setting `episode["gap"]`. The mutation that removes those lines from the engine survives. `Engine.step` has no test at all, so neither do the day roll (`engine_main.py:187-193`), `end_day` (`:158`), restart mid-position (`start_day` → `load_books`, `:133`), or the shutdown learn (`:717`).

**T3 (high, verified by probe P1): learning runs on non-trading days, and a weekend evening promotes a challenger.** `Engine.step` calls `end_day()` at 15:31 every day with no `is_trading_day` check (`engine_main.py:192`). `record_day` stores empty books as 0 % days (`learning.py:158-177`). The live feed process keeps running over weekends (`feed_breeze.py:518`), so an engine left up from Friday learns on Saturday. Probe: a challenger reached streak 1 on Fri 13 Nov. Then `record_day`+`learn` for Sat 14 Nov (empty books) promoted it: `{'day': '2026-11-14', 'event': 'champion', 'from': 'm2.0_s0.5', 'to': 'm1.5_s0.4'}`. The "2 passing evenings" rule (PROMOTE_STREAK) was met with no new trading day. The zero-difference day also counts toward CHALLENGER_MIN_DAYS. No test covers this.

**T4 (medium, verified by probe and reading): tests that pass vacuously or for the wrong reason.**
- `test_gex_map_regime_walls_flip:185-187`: the flip-escape assert sits under `if both["regime"] == "DAMPEN"`. The real regime is `MIXED`, so it never runs.
- `test_exit_waits_for_fresh_quote...:312`: the "futures stale → no decision" assert also passes with the fut_age gate deleted (mutant survived), because the 8-second-old option quote defers the exit anyway.
- `test_learning_sprt:90`: "champion was replaced" is reached through the **KILL** path (log: champion retired 2026-11-05, status GO), not challenger promotion. It also uses legacy `pnl_pts` (no `ret_pct`), so it never tests the D-064 unit.
- `test_learning_sprt` does not call `_reset_learning()`. Its result depends on file order and on the shared `APEX_DATA` temp dir.

**T5 (medium, verified by probe P4): replay does not match live after a feed restart.** Live `BreezeFeed.__init__` zeroes all rows (`feed_breeze.py:235`). Replay's `install_registry` (`feed_replay.py:35-41`) does not. When a recorded day contains a second `reg` record (feed restart with a new band centre, so option ids get new strikes), the old occupant's `ttq` stays in each row. The monotonic guard (`feed_core.py:152`) then drops the new contract's quotes until its volume passes the old one. Probe: an option quote on a reused row returned `-1`, and ltp stayed at 25200. Replay is the owner's way of checking a rule (README), and this is where it diverges. The same guard also drops every next-day quote if a feed process survives midnight; that path is unverified live, because the Breeze session probably dies first.

**T6 (medium, read): replay and sim results depend on speed and CPU load.** The engine steps on wall-clock sleeps, `time.sleep(max(0.1/speed - elapsed, 0.005))` (`engine_main.py:708-709`). At `--speed 50` the 5 ms floor means one engine step per 0.25 virtual seconds, not 0.1. When the feed falls behind it rebases (`feed_sim.py:426`, `feed_replay.py:78`). The same file replayed at different speeds, or on a busy machine, gives different trades, so a golden-master replay test cannot be written today. Under load from other council runs, my isolated sim ran at about 25× instead of 50×. I did not finish a two-speed A/B run for lack of time; this is inferred from the code.

**T7 (medium, read and probe P6): restart mid-position fails silently.** `load_books` returns `None` on any parse error (`paper.py:441-450`). `start_day` then builds fresh books at ₹1,00,000 and flat, and the next `save_books` overwrites the evidence. Probe: a truncated JSON gave `None` with no log line. `Book.ctl` is not saved, so `premium_momentum` re-arms after a restart and can fire again on the same burst. `Ledger.seen` resets, so an episode still in progress is written twice to `candidates_*.jsonl`.

**T8 (low, read): `StateBlob.write` returns silently when the state exceeds 2 MB** (`table.py:165`). The dashboard would freeze with no error. Observed size at 09:25 sim was 19 KB, so this is a latent risk only.

**T9 (low, observed): test and sim isolation leaks.**
- `TICKS_DIR` and `TOKEN_CACHE_JSON` ignore `APEX_DATA` (`config.py:16,24`).
- The shared-memory names are fixed (`config.py:38-39`), and `Table.__init__` binds them as default arguments at import time.
- So `sim --record` always writes into the repository's `data/ticks`, and two sims on one machine share one table.

Disclosure: before I noticed this, my first un-isolated sim probe added data to `ApexOptions/data/ticks/2026-10-19_sim.jsonl.gz`. Another council member's process was writing to the same file at the same time. Treat that file as polluted and delete it. I left it in place because it is not only mine.

## Good things
- Several tests are scenario tests, not unit pokes. `test_reconnect_jump_cannot_fire` first shows the artefact really looks like a Triangle (`zmax>=2, smax>=0.5`) and only then shows the guard blocks it (`test_core.py:259-268`).
- Learning maths is checked against independent reference values: the t tail 0.0169, t_crit 3.364, SPRT lines 110.9/−62.3, Wilson bounds (`:355-359`, `:514`).
- `test_exit_never_prices_off_another_contract` and `test_exit_ignores_blackout_prints` encode real audit findings (R1, R2) as regression tests.
- `test_paper_only_no_order_calls` is a cheap structural guard for the paper-only rule.
- `apply_packet` tests a shared numeric token across the cash and F&O segments, plus out-of-order cumulative volume (`:28-48`). One parser for live, sim and replay (`feed_core.py`) is the right foundation for a replay test.
- `random_schedule` is seeded per day and per book, so it is reproducible (`paper.py:226`), and a test asserts that.
- The suite needs numpy only and runs in seconds.

## Ideas from GitHub
1. **HypothesisWorks/hypothesis**: https://github.com/HypothesisWorks/hypothesis, MPL-2.0 (LICENSE.txt read). Borrow `RuleBasedStateMachine` with `@rule`/`@invariant`/`@precondition` from the stateful-testing docs. Map it to a **test-only** `BookMachine`. Rules: open, tick(fut, opt quote, age, blackout), restart (`save_books`/`load_books`), clock jump. Invariants:
   - capital equals 1,00,000 plus the sum of `pnl_rs`;
   - at most one position;
   - no price exit while blackout is on;
   - an exit is priced only off the held key;
   - after a `pending` stop, a later exit is a STOP;
   - a round trip through restart is the identity.

   Add a separate `@given` property for `apply_packet`: any list of 21 or 23 strings, blanks or `None` never raises, and the seq counter stays even. Test dependency only (`pip install hypothesis`); engine code does not change.
2. **syrupy-project/syrupy**: https://github.com/syrupy-project/syrupy, MIT. Snapshot assertions (`assert x == snapshot`, `--snapshot-update`, and a test fails when its snapshot is missing). Map it to a **golden-replay tool**: commit one short recorded session (about 20 minutes, gzip) and replay it through `apply_packet` → `Engine.step`, driven by a stepped virtual clock (see idea 3). Snapshot every book's trades, ledger labels and advisor verdicts. Any change to frozen-trigger behaviour then shows up as a reviewed snapshot diff, which fits I-11 and D-033.
3. **nautechsystems/nautilus_trader**: https://github.com/nautechsystems/nautilus_trader, LGPL-3.0, so concept only and no code. Its README says "the same architecture, execution semantics, and time model operate across both" backtest and live, with a "deterministic event-driven runtime". Map it to a **replay mode where the engine owns the clock**: the feed applies all packets up to t, then the engine steps t+0.1 s in lock-step through a ctrl handshake, not wall-clock sleeps. This fixes T6, makes idea 2 possible, and turns replay into a real controlled experiment for variants.

## Top 3
1. **Mutation-driven safety tests (S, before Monday).** Add one small test per surviving mutant in the exit, entry and contract groups. Add a test for the `load_books` round trip, plus a loud warning when parsing fails. Add a test that `end_day` is skipped on non-trading days. Fix `end_day` with `if not config.is_trading_day(...)` (T3); it touches the learning loop, not the trigger. Re-run `/tmp/council/m08/mutate.py` until the 13 paper/learning mutants are killed.
2. **An Engine-level harness (M, before Monday for the day-roll subset).** Drive a real `Engine` from a fake `Table` and set `ctrl.now_ns`. Cover: 15:24 position → 15:25 TIME exit → 15:31 learn exactly once; a restart at 11:00 with an open position and pending stop; a renumbered registry; a date change at midnight. This kills the engine mutants and replaces the glue code copied into T2's tests.
3. **Deterministic lock-step replay plus a golden snapshot and Hypothesis machine (L, later).** Zero rows on every `reg` in replay (T5). Isolate `TICKS_DIR` and the shared-memory names per `APEX_DATA` (T9). Then build ideas 3, 2 and 1 in that order.

---

# Member 09: Dashboard, UX and decision support

## Lens
`apex/static/index.html`, `app.js`, `style.css`, `apex/gateway.py`. The question: does the screen help a trader decide quickly and correctly?

Method: I read all four files in full and the engine's `publish()` (`engine_main.py:595-683`). I ran the sim on a private copy (`/tmp/council/09/apex_copy`, with the port and shm names changed to avoid other members' runs; baseline untouched). Playwright/Chromium covered screenshots at 1600×1000 and 1366×768, DOM-churn checks, function timing, a WebSocket message counter, and fault drills where I SIGSTOP'd the engine or the gateway. Disclosure: an early `pgrep` also paused another member's sim engine (pid 1434) for 15 s before I resumed it.

## Teardown

**1. No staleness detection: a frozen engine looks healthy. HIGH.** Locations: `app.js:71-84`, `gateway.py:109-120`.
- `/ws/state` only pushes when the blob changes, and the browser never checks how old `S` is.
- The health dot is driven only by *tick* ages.
- *Verified* by SIGSTOP on my engine for 15 s. The clock stayed frozen at `09:52:24` and the verdict stayed "Push is 0.2 of the 2.0 needed." The dot stayed **green "live"** with "tick age 250 ms".
- If the gateway freezes, the dot only turns grey and says "no ticks". The whole page keeps showing the last verdict, position P&L and stop with no warning.
- Failure scenario: the engine hangs mid-trade (GC, disk, a numpy stall). The owner watches a "live" screen whose stop line and P&L are minutes old.
- `engine_hb_ns` and `gateway_hb_ns` already exist in the table (`table.py:44-45`) but are never sent to the browser. `gateway_hb_ns` is written only inside the per-client tick loop (`gateway.py:98-101`) and nothing reads it.

**2. The gold "fire" verdict is recomputed in the browser and ignores the engine's blocks. MEDIUM.** Locations: `app.js:114-123`, `157`.
- `corners()` decides `closed` from `domino.z / m_star`, `S / s_star` and `late`.
- `renderVerdict` sets `.verdict.fire` (gold glow; the CSS reserves gold for "trigger near or firing") whenever `closed` is true.
- It does this even when the engine's `reason` is "outside entry window", "already traded this episode", "DATA GAP…", "episode began in a data gap", or a gate veto (`paper.py:146-186`).
- The Triangle's eye and spiral (`drawTriangle`) also glow from the same browser-side maths.
- Result: you can get gold, glowing text reading "Already traded this move." or "Blocked by a learned rule". The visual says go while the words say no.
- If the champion becomes `straddle_spike` or a `gap*` variant, the Triangle shows the wrong trigger entirely.
- *Verified by reading* (not reproduced live). Fix: the engine should publish `fire_ready`/`blocked_by`, and the UI should render it instead of re-deriving it.

**3. The key seller-state signal is cut off at common laptop widths. MEDIUM.** Locations: `style.css:96` (`.leg .meta { white-space:nowrap; overflow:hidden }`), `app.js:203,206`.
- *Verified* in a 1366×768 screenshot: CE legs show "h", "re", "d" instead of hold/refill/drain, and "book→p…" is cut off.
- That is exactly the signal the panel legend calls "the run you are waiting for".
- At the same size, the Paper-position panel starts at y=710 of 768, so open-trade P&L and stop are below the fold.
- Document height is about 2,700 px, with about 470 numeric tokens in DOM text plus 5 canvases.

**4. Explanations are destroyed every 250-350 ms. MEDIUM.** Locations: `app.js:164-168` (advisors), `529-534` (heavyweights), `203/206` (ladder meta), `570` (tape).
- Each state message rebuilds these by `innerHTML`.
- *Verified*: the same `#advisors li` and `#ev li` node is not identical one second later.
- Each advisor's `why` exists only in a `title=` tooltip. Browser tooltips need about 0.5-1 s of stable hover, so they flicker away or never appear. The reason an advisor vetoed is effectively unreadable.
- Text selection and copying from the tape are also broken.

**5. Colour semantics are inconsistent and sometimes inverted. MEDIUM.**
- *Ladder and Straddle* (`style.css:131`): CE = green, PE = coral.
- *OI map* (`app.js:321-322`): **put OI is green and call OI is coral**.
- *Force line* (`app.js:345`): VACUUM/BREAK-IMMINENT/BROKE are always green ("up") and HOLD-STRONG is always coral. It ignores `force.dir`, which the engine publishes (`levels.py:199`). Breaking a *support* in a down move is painted green, the bullish colour.
- *Big price colours* (`app.js:63-68`): the flash class is re-added on every tick. Under steady ticks it becomes permanent, so the 30 px futures price is coloured by the last tick, not the day.
- *Verified* in a screenshot: futures shown green at 25,031.85 next to a coral "−207.20 (−0.82%)".
- Green/coral is also the only carrier of meaning in several places, which is risky for red-green colour blindness.

**6. Per-tick forced reflow; render cost on the main thread. MEDIUM in sim, probably LOW live.** Location: `app.js:66`.
- `void el.offsetWidth` forces a layout on every changed price.
- *Measured* (headless, software rendering, sim at 30×, about 1,600 ticks/s): `onTick` took **30-41 % of main-thread time** (3.0-4.1 s per 10 s).
- `render()` took about 48-69 ms per call at about 3 Hz, and there were 82 long tasks (>50 ms, worst 170 ms) in about 15 s.
- The Triangle's requestAnimationFrame loop fell to about **4.5 fps**.
- Live Breeze tick rates are far lower, so treat this as an upper bound. Still, a busy expiry morning on a laptop is where it would bite.
- Fixes:
  - Coalesce ticks per `requestAnimationFrame`, keeping the latest value per id.
  - Use the Web Animations API, or toggle between two classes, instead of reflow.
  - Diff state before using `innerHTML`.

**7. Silent failures in the gateway and the WebSocket client. LOW.**
- `gateway.py:103-106` swallows every exception and returns. A serialisation bug becomes a silent close-and-reconnect loop every second (`app.js:46,74`, with no backoff).
- `app.js:73` logs JSON errors only to the console.
- `StateBlob.write` silently drops a state larger than 2 MB (`table.py:165`). I measured 25 KB, and the series is capped at 720 points, so this is a latent issue, not a live one.

**8. Accessibility. LOW.**
- There are no `aria-live` regions (0 found), so entries and exits are not announced. The verdict is the obvious candidate.
- None of the 5 canvases has a text alternative.
- Contrast is fine: mist on panel is 5.4:1 and coral is 5.7:1.
- Fonts come from Google Fonts. If that fails (it was blocked in my sandbox), the canvas text falls back silently, which is acceptable.

**9. Smaller points. LOW.**
- "Together" means two things. The ladder header shows `K_up`/`K_dn` (hero coherence), while the Triangle shows `S_up`/`S_dn` (basket synchrony). I saw "together up 0% down 10%" next to "Together 0% of 50%".
- On the OI map, the "max pain" and "spot" labels overlap when they are at the same strike (seen in the screenshot).
- The Books panel sizes bars by points but labels them in rupees (`app.js:556-559`). Under compounding the two can disagree in sign.

## Good things
- **A sound process split.** The gateway computes nothing, and each WebSocket client gets its own diff loop driven by seqlock (`gateway.py:82-97`). A slow tab only slows itself, and reconnecting resends a full snapshot (`sent` is zeroed).
- **The `wsproto` choice is documented with its reason** (`gateway.py:139-146`).
- **Reasons are written in plain language.** `humanReason()` (`app.js:125-142`) turns engine reason strings into trader English ("Push is 0.8 of the 2.0 needed."), and blackout gaps are shown in the header (`app.js:94-97`).
- **Honest framing throughout.** The UI says "paper · simulated market", the GEX panel carries the caveat "Assumes dealers are long calls…; shown as evidence only", and the books panel says "Changes happen only after the close" (respects I-11).
- **The straddle watch is well thought through.** It uses a fixed strike rather than the jumping ATM, draws a theta-only reference path, marks ATM rolls, and lays out labels to avoid collisions (`app.js:436-521`).
- **Good canvas basics.** Canvas sizing respects DPR (`fit()`), and `prefers-reduced-motion` is honoured.
- **Controls and the lead book are visibly separated** from the lead book (`.book.ctl` in italics, champion in gold).

## Ideas from GitHub
1. **pladaria/reconnecting-websocket.** https://github.com/pladaria/reconnecting-websocket. Licence: MIT.
   - Source: `reconnecting-websocket.ts`, which provides jittered exponential backoff (`minReconnectionDelay` 1-5 s, growth ×1.3), a `connectionTimeout`, and open/close/error events you can listen to.
   - How it maps onto Apex: a **dashboard tool**. Replace the bare `setTimeout(connect,1000)` (`app.js:46,74`) and drive a "DISCONNECTED / STALE" banner from the close and timeout events.
   - Pair it with an `engine_age_ms` field (from `engine_hb_ns`) added by the gateway to every `/ws/state` frame, plus a 1 Hz heartbeat frame even when nothing changed.
2. **leeoniya/uPlot.** https://github.com/leeoniya/uPlot. Licence: MIT.
   - Source: `demos/sine-stream.html` and `sparklines.html`, a streaming time series in a few KB with a very low per-update cost.
   - How it maps onto Apex: **a dashboard tool**. Replace the hand-drawn `drawTrace`/`drawStraddle`/`drawPosLine`. You get a time axis, a hover cursor showing exact values, and much cheaper redraws than rebuilding the whole canvas on each state message.
3. **tradingview/lightweight-charts.** https://github.com/tradingview/lightweight-charts. Licence: Apache-2.0.
   - Source: `plugin-examples/src/plugins/` (`session-highlighting`, `user-price-lines`, `vertical-line`, `partial-price-line`) and the accessibility plugin (now the `lwc-plugin-accessibility` package).
   - How it maps onto Apex: **a dashboard tool**. The futures trace maps directly: episode shading becomes session-highlighting, entry/stop/"move began" become price lines, and ATM rolls become vertical lines. The accessibility plugin covers finding 8 for charts.

## Top 3
1. **Make staleness visible.** The gateway attaches `engine_age_ms` and `feed_age_ms` (from the existing `*_hb_ns`) and sends a heartbeat at least once a second. The browser shows a full-width red "ENGINE STALE n s / DISCONNECTED" banner and greys out the verdict, position and stop once the data is older than 2 s. Use reconnecting-websocket-style backoff. **Size S. Before Monday.**
2. **Make the engine the only source of "go" truth.** Publish `entry_ready` and `blocked_by` (the champion's `evaluate_entry` result *before* the time-window, blackout and fired checks, plus the actual blocker). Gold and glow happen only when the engine says entry is possible. The Force colours use `force.dir`, the OI map uses the CE/PE palette, and big prices are coloured by day change, not last tick. **Size S-M. Before Monday.**
3. **Cut churn and overload.**
   - Batch ticks per animation frame and drop the forced reflow.
   - Diff-render the advisors, tape and ladder, and move each advisor's `why` into visible text on the veto chip.
   - Stop the ladder from clipping its signal: wrap the meta row, or drop delta/IV first.
   - Add a compact "decision strip": verdict, position P&L, stop distance, staleness. It stays in the sticky header, so it is visible at 1366×768.
   - Move the deep-dive panels (GEX, books, straddle table) to a second tab.

   **Size M. Later.**

---

# Member 10: NSE F&O specifics

## Lens
I checked the parts of the code that depend on Indian market rules: `apex/config.py` (holidays, weekly and monthly expiry rules, lot size, freeze quantity, strike step, session clock, 0DTE rails, `EVENT_DAYS`) and `apex/universe.py` (index weights). I compared each against current public sources on 18 Oct 2026. Methods: reading the code, a probe script calling `weekly_expiries`, `monthly_expiry` and `monthly_expiry_candidates` on 9 dates, the test suite (all tests pass), and WebFetch of NSE, niftyindices and RBI documents.

**Facts that are current (verified):**
- **Holidays.** `NSE_HOLIDAYS` (config.py:167-172) matches the published 2026 list exactly: 16 weekday holidays (ClearTax copy of the NSE list). It also matches the independently maintained `exchange_calendars` XBOM list.
- **Expiry shifts.** Tue 20 Oct (Dussehra) gives a Mon 19 Oct weekly. After 15:30 on Mon 19 Oct the system rolls to 27 Oct (monthly) and 3 Nov. Tue 10 Nov gives Mon 9 Nov. Tue 24 Nov gives Mon 23 Nov for both weekly and monthly. 29 Dec is a normal monthly. All correct.
- **Freeze quantity.** `FREEZE_QTY = 3510` matches NSE/FAOP/76693, effective 5 Oct 2026 (BANKNIFTY 1440, FINNIFTY 3240).
- **Lot size.** `LOT_SIZE = 65` is current: 75 changed to 65 from the 6 Jan 2026 weekly. I found no newer revision.
- **Muhurat session.** It falls on Sun 8 Nov 2026, so `is_trading_day` returns False and nothing runs. That is correct.
- **Nifty 50 weights.** The ten "exact" weights match the 30 Sep 2026 factsheet. The Bank Nifty and FinNifty top-10 weights also match their factsheets.

## Teardown

**T1. Two "estimate" Nifty weights cannot be right (medium). Verified by logic plus the factsheet.**
- Where: `universe.py:26-27`, TCS 2.70 and ITC 2.56.
- What is wrong: the 30 Sep factsheet's top-10 table ends at M&M, #10, with 2.52%. Any stock outside the top 10 must therefore weigh 2.52% or less. TCS at 2.70 and ITC at 2.56 would both rank inside the top 10, yet neither appears there, so both estimates are too high.
- Effect: synchrony S_d is "share of tracked Nifty weight", and the basket-implied points feed the `gap3`/`gap5` variants. Both over-count the IT and FMCG legs. On an IT-only move, such as TCS or INFY results, the basket looks more "synchronous" than it is.
- Fix: cap every estimate at 2.52 or below. Better, derive the weights from the NSE constituent CSV (free-float market cap) or another dated source. Add a unit test: every "estimate" weight must be no larger than the smallest "exact" weight.

**T2. `EVENT_DAYS` is empty, and its one example date is a Saturday (medium). Verified against RBI.**
- Where: `config.py:146-148`.
- What is wrong: the commented example is `"2026-12-05": "RBI policy"`, which is a Saturday. The RBI's FY27 MPC schedule (press release 62422) puts the meeting on 2-4 Dec, so the decision comes on **Fri 4 Dec**. The October meeting (5-7 Oct) has already passed.
- Effect: with an empty dict, the "event" advisor logs zero would-vetoes, so the learning loop can never assess it.
- Dates to add, all checked: RBI 4 Dec 2026 and 5 Feb 2027.
- Dates to add, not checked by me (owner to confirm): FOMC decision about 29 Oct IST, US midterms 3-4 Nov, Union Budget 1 Feb 2027.
- Bigger gap for this system: Q2 results days of the tracked heavyweights. A single stock gapping on results breaks the "heavyweights lead the index" premise. Results days should be logged per stock, not per day.

**T3. No 2027 holidays, and the preflight check misses the gap (medium, hard date). Verified by reading.**
- Where: the preflight check at `run_apex.py:188` only asks whether *this* year's holidays are present. On 20 Dec 2026, `weekly_expiries` already looks into Jan 2027 and the check still passes.
- The concrete risk: **Tue 26 Jan 2027 is Republic Day**, and it is both the weekly and the monthly expiry date. Without a 2027 list, `weekly_expiries` and `monthly_expiry` return 26 Jan instead of Mon 25 Jan. From about Tue 19 Jan, w1 and the futures contract would point to a contract that does not exist. The token probe and the empty-chain guard would catch it, but only as a NO-GO on the morning.
- Fix: make preflight require holiday coverage for every date up to the furthest expiry it computes (w1 and mexp), not just the current year.

**T4. Days-to-expiry is counted in calendar days (low). Verified at `paper.py:120-121`.**
- `dte` counts calendar days, so on Fri 16 Oct, Fri 6 Nov and Fri 20 Nov (expiry on the following Monday) dte is 3. That selects the "ge3" delta band (0.52-0.70) when only one trading session remains.
- `greeks.years_to_expiry` (greeks.py:43) also uses calendar time over 365 days. Friday IVs therefore come out lower and deltas differ from a trading-time view.
- This is not a bug against D-021, which never says calendar or trading days. But the three Mondays in Oct and Nov 2026 hit this ambiguity, so the decision log should state which one is meant.

**T5. The comment on `SUPPRESS_UNTIL` predates the F&O pre-open session (low, informational). Verified the rule; the Breeze behaviour is not verified.**
- Since 8 Dec 2025, NSE runs a pre-open session for futures (not options): orders 9:00-9:08, matching 9:08-9:12, buffer to 9:15. The 9:15 futures price is now discovered in an auction.
- Effect: the comment's "overnight repricing" claim (`config.py:56`) and the domino's in-session sigma logic (`domino.py:84-89`) rest on a 9:15 jump that may now arrive at about 9:08. Options still open with a jump at 9:15.
- Check (unverified): Monday's recorder should log whether Breeze streams futures ticks between 9:08 and 9:15. If it does, those ticks land in `last_msg` but outside `fut_sigma`, which is fine.
- Separate effect: the first 10 minutes of the open feed the 20-minute EWMA. That inflates sigma at 9:25, when entries open (unverified size).

**T6. Lot size and freeze quantity are hard-coded constants that NSE changes (low). Verified by reading.**
- The freeze limit was revised on 1 Sep and again on 5 Oct 2026, so it now changes roughly monthly. Lot sizes are reviewed every six months.
- Effect today: none. Return-on-premium learning ignores lot size, and `slices` is informational only.
- Fix: preflight should read the NIFTY lot from the Breeze security master (or NSE `fo_mktlots.csv`) and fail on a mismatch with `LOT_SIZE`.

**T7. `monthly_expiry_candidates` probes a stale "last Thursday" rule (low). Verified with the probe script.**
- Stock futures moved to last Tuesday in Sep 2025, so the Thursday fallback (`config.py:235-245`) is dead code.
- In Mar 2026 it returns [30 Mar, **25 Mar**], so the fallback can sit *before* the primary. Harmless, because the cache and the first token lookup win, but it should be removed.

**T8. Nothing stops a live start on a holiday (low). Verified by reading.**
- If `run_apex live` is started on Tue 20 Oct, it builds normally from the REST previous close and then sits idle. Preflight never prints "today is an NSE holiday".
- Learning is unaffected, because only days on which both books traded count.

## Good things
- **Expiry calendar** (`config.py:186-232`): the holiday roll-back is shared by weekly and monthly expiries, the 15:30 roll-off is explicit, and `ws_expiry` uses its own month names, so it does not depend on the machine's locale (`%b`). All seven dates in the design's test plan come out right in my probe.
- **Freeze-quantity comment** (config.py:47): it cites the exact circular, which made verification a 30-second job. `universe.py` likewise tags each weight as exact or estimate and dates its source. That is good provenance practice.
- **0DTE rails** (`paper.py:112-118`, `paper.py:379-384`): they key on the contract's own expiry, not on the weekday, so holiday-shifted Monday expiries work without special cases.
- **Clock validation**: `config.validate()` (config.py:290-293) checks that the session clock is in order, and the preflight token probe of the computed weekly and futures expiries (run_apex.py:241-268) turns a calendar error into a morning NO-GO instead of a silent empty chain.
- **Pre-open handling** (`domino.py:84-89`): sigma learning is limited to in-session ticks, so pre-open zeros cannot shrink σ.

## Ideas from GitHub
1. **gerrymanoim/exchange_calendars** (https://github.com/gerrymanoim/exchange_calendars, Apache-2.0; cloned).
   - What to borrow: the `exchange_calendar_xbom.py` precomputed BSE/NSE holiday list. Its 2026 dates match Apex exactly.
   - How it maps onto Apex: a **preflight tool** that diffs `config.NSE_HOLIDAYS` against `xcals.get_calendar("XBOM")` for the current and next year. It warns on any difference and on a missing next year. Use it as a dev or preflight check only, not a runtime dependency. This covers T3 from a second source.
2. **BennyThadikaran/NseIndiaApi** (https://github.com/BennyThadikaran/NseIndiaApi, **GPL-3.0**: concept only, no code copied; cloned).
   - What to borrow: `NSE.holidays()` (calls NSE's `/api/holiday-master`), `fno_lots()` (parses `nsearchives.nseindia.com/content/fo/fo_mktlots.csv`) and `get_futures_expiry()` (NSE.py:1326-1360, 1568, 1769).
   - How it maps onto Apex: a small home-written preflight **observer**. Once a day it fetches the official NSE holiday master and the lot file, and asserts they agree with `NSE_HOLIDAYS`, `LOT_SIZE` and the computed expiries. This covers T3 and T6 straight from NSE, written clean-room.

## Top 3
1. **Fix the TCS and ITC weights, cap every estimate at or below the #10 weight, and add a unit test** (T1). Size S, before Monday. It directly affects the synchrony number that the frozen trigger and the gap variants read on Monday.
2. **Fill `EVENT_DAYS`** (T2). Add RBI 4 Dec 2026 and 5 Feb 2027 (correcting the 12-05 example), plus the owner-confirmed FOMC, US midterm and Budget dates. Add a per-stock results calendar for the 14 tracked Nifty heavyweights, logged as an advisor input. Size S, before Monday for the dict; later for the results calendar.
3. **Preflight calendar guard** (T3, T6): require holiday coverage up to max(w1, mexp), add the 2027 list once NSE publishes it (26 Jan 2027 is a Tuesday expiry), and cross-check `LOT_SIZE` against the security master, ideally through the exchange_calendars or NSE holiday-master diff above. Size M, later, but it must be done before about 19 Jan 2027.

---

# Council member 11 — Regime & volatility modelling

## Lens
`apex/engine/regime.py`, the VIX poll, ATM IV tracking (`engine_main.compute_greeks`, `iv_hist`, `iv_change`), the `iv_late` advisor, the frozen IV cap in `paper.py`, and the σ15 scales in `apex/engine/domino.py`. The question: are these features and thresholds sensible for intraday Nifty, and are any standard volatility estimators missing? I checked the work by reading the code, running three probe scripts against the real modules (in my scratchpad folder `p11/`), and running `tests/test_core.py`, which passes.

## Teardown

**F1 — HIGH: ATM IV is a floating-strike snapshot, so it saw-tooths at every strike roll and rises mechanically in sell-offs. That feeds the frozen trigger's IV cap and `iv_late`.**
- **Where:** `engine_main.py:359-363` takes the strike nearest F (`atm = min(strikes, key=|k-F|)`) and averages the CE/PE IV at that one strike. The result feeds `iv_rise_since_onset` (`:269`), which feeds the frozen `IV_RISE_CAP = 1.5` check (`paper.py:182`), the lateness score (`:533`) and `iv_late` (`:408`).
- **Probe `probe_iv.py`:** I used a smile fixed in moneyness, so true ATM-forward IV stays at 13.00 throughout. With a mild skew of −0.6 vol pts per 50-pt strike step, the measured `atm_iv` reads 13.32 at F = 25024 and 12.75 at F = 25026. That is a **0.57-pt jump with no change in volatility**, about 38 % of the 1.5-pt cap.
- **Probe `probe_iv2.py`:** I used a smile fixed in strike (sticky-strike). A 60-pt fall moves `atm_iv` by +1.40 pts at 1 day to expiry and +2.20 pts at 5 hours to expiry. That exceeds both the `iv_late` threshold (8 % of 13 = 1.04) and the 1.5-pt cap. The same 60-pt rally moves it by −1.0 / −1.8 pts.
- **Failure scenario:** On an expiry-week afternoon, a clean 60–100-pt down-impulse is rejected as "LATE: ATM IV +x since onset". Volatility did not move; the trigger simply started reading a higher-skew strike. CE entries are never blocked this way.
- **Why it matters:** The cap acts as a direction- and DTE-dependent filter. D-016 expects an IV tailwind for PE, but this effect is mostly a measurement artefact.
- **Fix:** Keep the number 1.5; change only the input.
  - Interpolate IV at F linearly in strike between the two strikes that bracket it, or read IV at fixed delta 0.5.
  - Or measure the rise at a fixed strike, namely the onset ATM strike (`ep["iv0_strike"]`).
  - Because this changes trigger behaviour, it needs the owner's sign-off, or it should run as a pre-registered variant first.

**F2 — MEDIUM: regime percentiles ignore time of day, so COMPRESSION is over-labelled in mid-morning and `rv_pct` thresholds mean different things by the clock.**
- **Where:** `regime.py:49,116` ranks `rv_pct` against *today's history so far*, which in the first hour is dominated by the opening burst. Nifty's intraday volatility is U-shaped: roughly 2× at 9:15–10:00 and again into 15:00.
- **Probe `probe_regime2.py`:** These are synthetic random walks run through the real `Regime` class. During 10:15–11:15, COMPRESSION was labelled **30–43 % of the time (mean 38 %) with U-shaped volatility vs 7–18 % (mean 14 %) with flat volatility**, over 3 seeds each.
- **Failure scenario:** The `regime` advisor vetoes most of late morning as "quiet and contracting" when the market is just ordinary. The per-regime report tables (D-069/D-071) then mix volatility state with clock time.
- **Fix:** Rank `rv5` against the same 15-minute bucket on previous sessions, i.e. a seasonal baseline built offline in the evening from recorder data. That should be a new pre-registered regime *variant*, not an edit.

**F3 — MEDIUM: EXHAUSTION fires heavily on trend days.**
- **Where:** `regime.py:150` fires EXHAUSTION when `ext_pct ≥ 90 and er1 < 0.25`. On a trending day, the distance to VWAP keeps setting new highs, so `ext_pct` sits near 100. `er1` is a 12-step efficiency ratio, which is below 0.25 about half the time for pure noise (≈ |Z|·0.36).
- **Probe `probe_regime.py` (single seed, so treat as indicative):** On a +150-pt drift day, EXHAUSTION took 30 % and 36 % of hours 2 and 4, against 12–14 % on a driftless walk. In practice the label vetoes every with-trend entry during the pauses inside a trend. The bar should be relative (e.g. `ext` in σ-units of the day's path) or require `er1 < 0.15` sustained for 60 s. Treat any of these as a variant.

**F4 — MEDIUM (verified by reading): a mid-session engine restart silently changes what the regime features mean.**
- **Where:** `start_day` builds `Regime()` from scratch (`engine_main.py:151`). `t0`, the VWAP accumulators (`regime.py:84,89`) and the percentile histories therefore start at restart time.
- **Failure scenario:** After a 13:00 restart, "VWAP" is VWAP since 13:00, and the percentiles rank only against the afternoon. Trades get labelled with a regime that is not comparable to other days' labels.
- **Fix:** On start, rebuild from the day's recorder file, which `feed_replay` already reads, or mark the labels `restarted=True` and exclude them from the per-regime tables.

**F5 — LOW: VIX is polled every 60 s but used nowhere in the engine.**
- **Where:** Polled at `feed_breeze.py:463`; the only consumer is the dashboard (`engine_main.py:648`).
- **Assessment:** Using one REST credit a minute just for display is fine. But the cheap, well-known signal next to it is missing: the weekly ATM IV minus India VIX (30-day), a term-structure / event-premium reading. See Idea 2.

**F6 — LOW: `iv_late` uses a single raw sample at each end.**
- **Where:** `iv_change` (`engine_main.py:538`) is the point difference between the current `atm_iv` (recomputed from mids every 0.25 s) and one sample from 5 minutes ago.
- **Failure scenario:** On 0DTE, ATM vega is small, so a one-tick widening of the spread moves IV by several tenths of a point.
- **Fix:** Take a 15–30 s median at both ends.
- `iv_hist` is also not cleared on a data gap, unlike the regime windows (D-075).
- The two IV rules use different units: `iv_late` is relative (8 %) while the cap is absolute (1.5 pts). That deserves a note in docs/03.

**Checked and not raised:**
- σ15 is a mean-absolute EWMA, not a standard deviation. This is already acknowledged in docs/04 line 116.
- The ER random-walk baseline in the docstring is correct. I re-derived it: mean ≈ 0.22, P(≥0.35) ≈ 21 %, P(<0.20) ≈ 52 %.
- Calendar-time `T` (`greeks.py:43`) produces only about 0.03 vol pts of drift per 5 minutes on the day before expiry, which is negligible for 5-minute and since-onset deltas.

## Good things
- **`regime.py` docstring:** The thresholds were set against an explicit random-walk baseline, and the docstring records the 1-s bid/ask-bounce failure and its fix (15-s sampling). This kind of pre-registration is rare and correct.
- **No look-ahead:** The current value is ranked *before* it is appended to the history (`regime.py:113-118`). The 30-minute range ends 5 minutes ago, so a breakout is never judged against its own move.
- **Gap handling:** `after_gap()` drops the price windows but keeps the session VWAP and histories. `learn_scales=False` during blackouts keeps a jump on resume from inflating σ15 or the volume baselines (`domino.py`). Stocks with no quote are treated as missing (NaN), not as a −100 % move (`regime.py:96`).
- **Scale estimators:** `EW` is a fast-start EWMA (`domino.py:23`) whose seed counts exactly once. σ15 updates only on in-session data, so pre-open zeros cannot shrink it.
- **Forward and IV:** F comes from a put-call-parity synthetic forward with a stale-quote guard (`greeks.py:100-113`), not from spot. IV is solved with Black-76 on that forward, which is the correct model for index options.
- **Advisory status:** The regime is an advisor with its own gated book (D-067). Every trade and candidate carries its regime label, so the learning loop can judge it without anyone touching the trigger.

## Ideas from GitHub (all cloned to /tmp/council/11/)

1. **jasonstrimpel/volatility-trading** — https://github.com/jasonstrimpel/volatility-trading — **GPL-3.0, so concept only, no code copied.**
   - **What it has:** `volatility/models/{Parkinson,GarmanKlass,RogersSatchell,YangZhang}.py`, range-based estimators from OHLC data. They are 5–8× more statistically efficient than close-to-close returns.
   - **Mapping:** Write a ~40-line observer `engine/rv.py` from scratch. It builds 1-minute OHLC bars of Nifty futures from the 1 Hz series already held in `regime.fut`.
     - Publish Rogers-Satchell RV over 15 minutes, and Yang-Zhang over the session including the overnight gap.
     - Annualise it so it sits on the same scale as ATM IV.
     - This gives the missing **IV/RV ratio (volatility risk premium)**, the most standard check for an options *buyer*. Log it as a new advisor `vrp` that vetoes when IV/RV is above 1.3, and judge it through a gated book.

2. **bashtage/arch** — https://github.com/bashtage/arch — **University of Illinois/NCSA licence (permissive, MIT-like).**
   - **What it has:** `arch/univariate/mean.py: class HARX` (the heterogeneous autoregressive model, the HAR-RV forecasting baseline) plus `arch.bootstrap` (stationary/block bootstrap).
   - **Mapping:** An *evening tool* in the learning loop, not anything intraday.
     - Fit HAR-RV on daily realised variance from the recorder files to forecast tomorrow's RV.
     - Store it in `lstate`. Tomorrow's `vrp` advisor then compares live ATM IV against a *forecast* rather than a trailing RV.
     - Also store India VIX minus the weekly ATM IV.
     - Separately, `StationaryBootstrap` gives honest confidence intervals for the per-regime P&L tables (D-071), where trades are autocorrelated within a day.

3. **vollib/py_vollib** — https://github.com/vollib/py_vollib — **MIT.**
   - **What it has:** `vollib/black/implied_volatility.py`, Jäckel's "Let's Be Rational" Black-76 implied-volatility solver, plus analytic greeks under `vollib/black/greeks`.
   - **Mapping:** Add it as a *test oracle* in `tests/test_core.py` (dev dependency only) to check `greeks.implied_vol` and `greeks.greeks` across 0DTE–7DTE and deep ITM/OTM, including near the `valid` cut-off at intrinsic + 0.05.
   - It also provides the reference values for the F1 fix: a test asserting that the ATM-IV estimate does not jump when F crosses a strike midpoint on a fixed smile.

## Top 3
1. **Fix the ATM IV measurement (F1)**, size **S**, **before Monday**, owner sign-off needed.
   - Interpolate IV at F between the two bracketing strikes (or measure at the onset strike) and median-filter it over 15 s.
   - Keep `IV_RISE_CAP = 1.5` and the 8 % rule unchanged; only their input changes.
   - If the owner says the trigger input is frozen too, run the fixed measure as a pre-registered variant and log both values on every candidate from Monday.
2. **Add an IV/RV observer and a `vrp` advisor** (Idea 1, plus Idea 2 later), size **M**, **later**. Log Rogers-Satchell RV, IV/RV and VIX minus the weekly ATM IV on every candidate from day one, even before the advisor is judged.
3. **Make the regime percentiles time-of-day aware and handle restarts (F2–F4)**, size **M**, **later**. Run it as a pre-registered `regime_v2` variant beside the current labels, with seasonal `rv` buckets, a relative EXHAUSTION bar, and labels rebuilt from the recorder after a restart. Compare the two sets of labels in the D-071 tables after about 10 sessions.

---

# Member 12 — The core domino / basket-leads-futures thesis

## Lens
`apex/engine/domino.py` (impulse z, synchrony, basket gap, episodes), `apex/engine/extras.py` (LagMeter, BankLead, EpisodeLog), `apex/universe.py` weights, plus `market.py`, `guard.py`, `paper.py:150-190`, `config.py:66-96`. Question: does the system actually measure "the basket leads the futures"?

**Method.** Besides reading the code, I wrote a null-model probe. It drives the real `Market` and `Domino` classes and `LagMeter`, using the 14 real Nifty weights, a one-factor model with idiosyncratic noise and vol bursts, 10 Hz, 180 simulated minutes. In the probe the futures price is the true index, so **no stock ever leads**. Run A: stocks are simultaneous with futures. Run B: stock LTPs lag futures by 1 s, so the *futures* lead. Script: `/tmp/claude-0/-home-claude/a63e9fa2-7e12-5819-bed7-d06bfece2a8a/scratchpad/probe_domino.py`, with `probe_preopen.py` next to it. Tests pass (`python tests/test_core.py`).

| Null run (no basket lead) | Episodes | BASKET-LED | CO-FIRST | FUTURES-LED | LagMeter median | P(gap·d ≥ 3) / ≥ 5 while z ≥ 1 |
|---|---|---|---|---|---|---|
| A: simultaneous | 130 | **14.6 %** | 85.4 % | 0 % | 0.0 s | 0.6 % / 0.0 % |
| B: futures lead by 1 s | 130 | **13.8 %** | 86.2 % | **0 %** | **0.0 s** | **23.1 % / 13.5 %** |

## Teardown

**F1 — CRITICAL. The episode classifier has a built-in BASKET-LED bias and cannot see futures leadership.** `domino.py:183-198`.
- A stock crossing is only recorded while an episode is open, and an episode opens on the *futures* reaching |z| ≥ 1.
- Fourteen stock clocks race one futures clock. The earliest of 14 noisy crossings is systematically early.
- Line 191 labels the episode BASKET-LED whenever `ft is None`, i.e. whenever futures z peaks between 1 and 2 and any one stock touches 2.
- Line 192 labels it BASKET-LED even when only one stock crossed, if concentration is below 0.6.
- Result: with no lead at all, 14.6 % of episodes come out BASKET-LED. That is right at the D-015 kill line ("Study F1: basket-led < 15 % → re-scope"), so the study can be passed or failed by noise. When futures truly lead by 1 s, FUTURES-LED is still 0 %, because the ±2 s CO-FIRST band and the onset censoring swallow it.
- Failure scenario: the owner reads "basket-led 18 %" after two weeks and treats the thesis as confirmed, when that rate is the null.
- Verified by probe.

**F2 — HIGH. LagMeter measures the futures' rise time, not a domino lag.** `extras.py:117-125` together with `domino.py:184`.
- A stock that crossed before onset gets timestamped at onset, so the lag is bounded by `fut_cross_t − t0`.
- Episodes where futures never reach z = 2 are dropped, which is a selection effect.
- With futures leading by 1 s, the day median still reads **0.0 s** (n = 127): the first-of-N bias cancels the real lead exactly.
- The published "domino lag" (D-057) therefore cannot reject anything.
- Verified by probe.

**F3 — HIGH. The basket gap is dominated by timestamp skew, and coverage extrapolation turns sector moves into fake "gap" signals.** `domino.py:127`, plus the variants at `config.py:95-96` and `paper.py:169-173`.
- *Timestamp skew.* `Mb` uses cash LTPs from the movers/rest sockets. `Mf` uses the hero-socket futures, Breeze `ltt` is truncated to 1 s, and illiquid stock LTPs sit stale between trades. With a 1 s skew in the futures' favour, gap·d ≥ 3 pts happens 23 % of the time while z ≥ 1, and ≥ 5 pts 13.5 % of the time (0.6 % / 0 % when synchronous). In other words, `gap3_s0.4` and `gap5_s0.4` fire mostly when the futures have **just paused or ticked back** while stale stock prints still show the move. They buy into the lull and label it "basket leads". Verified by probe.
- *Coverage extrapolation.* `Mb = Σmi · 100/wtot` scales the tracked ~61.6 % of weight up to the whole index. In a bank-only move with the untracked 38 % flat, Mb = 1.62 × Mf exactly, so gap = 0.62 × Mf. An 8-pt bank-news move gives a 5-pt "gap" although futures priced it fully. Verified by arithmetic from the code; not probed on live data.

**F4 — HIGH. Stock sigmas learn pre-open zeros; futures sigma does not.**
- `domino.py:89` gates `fut_sigma` on `in_session`, but the stock-scale block at `domino.py:91-105` has no such gate. `guard.py:73-74` keeps `learn_scales=True` outside session hours.
- If the engine starts at 09:00, the 15 pre-open minutes of zero moves drag `self.sig` down. Fast-start alpha (1/n) makes this worse, and then the 20-min half-life recovers it only slowly.
- Probe, same seed: median stock sigma at 09:25 is 0.19 when started at 09:00, against 0.47 when started at 09:15 (steady state ≈ 0.38). P(S ≥ 0.5) over 09:25-09:35 is **45.5 % vs 21.2 %**. Synchrony is doubled exactly when `SUPPRESS_UNTIL` (09:25) lifts.
- The same zeros push `vol15_base` towards 0, so `act = dv/base` becomes inf and passes the 1.2× activity filter.
- Verified by probe.

**F5 — MEDIUM. BankLead ignores the blackout and the session.** `extras.py:91-96`.
- Its sigma updates on every finite reading: it is never frozen in a data gap (D-063 freezes only the domino), and pre-open zeros shrink it to the 2-pt floor.
- A reconnect jump inflates `sig` for about 20 min, so the `bank_z` written to the episode log is biased low after every gap.
- Verified by read.

**F6 — MEDIUM. Cash, not stock futures, defines "the basket"; nothing measures index-arbitrage coupling.**
- `domino.py:56` uses `kind=="eq"` only. `sfut` rows are subscribed (`feed_breeze.py:373`) but never used here.
- Nifty futures and the cash basket are tied together by arbitrage desks within milliseconds. At a 15-s horizon, a genuine retail-visible "basket leads futures" signal has to survive that coupling. Most published Indian work finds futures lead cash (background knowledge, not verified here).
- The system never compares stock *futures* against Nifty futures, which is the like-for-like, same-segment comparison with no cash-session microstructure.
- Status: design gap, verified by read.

**F7 — LOW. Weights and z units.**
- Weights date from 30 Sep 2026 (`universe.py`). Four of them (TCS, ITC, BAJFINANCE, HINDUNILVR) are May-2026 estimates. Within a month, drift (wᵢ·Pᵢ/Pᵢ,ref ÷ N/N_ref) is a few percent: immaterial compared with F1-F3.
- "z" divides by an EWMA of |x| (the mean absolute move), not the sd. z = 2 is ≈ 1.6σ under normality, so thresholds read stricter than they are. This needs documenting, not fixing.

## Good things
- **Scales are time-based on a single 10 Hz ring** (`market.py:61-72`), so "15 s ago" means the same in live, sim and replay. That consistency is what made my probe trustworthy.
- **Blackout handling** (D-063): `learn_scales=False` freezes the futures and stock sigmas and the volume baselines (`domino.py:87`). Gap-born episodes are tainted (`engine_main.py:242`, `paper.py:159`), and a test reproduces the reconnect artefact (`tests/test_core.py:218-268`).
- **Synchrony is weight-normalised over *fresh* names only** (`domino.py:119-124`). It also requires both the move z and a volume confirmation, so it is not a vote count.
- **The weight tags are honest** (`universe.py:7-12`): exact vs estimate, with the source documented.
- **The counterfactual EpisodeLog** (`extras.py:136-201`) records the grid at +0/15/30/60/120/300 s for every episode, traded or not. That is exactly the dataset needed to fix F1-F3 offline without touching the frozen trigger.
- **The gap ideas enter as pre-registered variant books** (D-056), not as trigger edits. The process is right even though the measurement is flawed.

## Ideas from GitHub
1. **philipperemy/lead-lag** (https://github.com/philipperemy/lead-lag, MIT). Repo opened.
   - What it is: `lead_lag.lag(ts1, ts2, max_lag)` implements the Hoffmann-Rosenbaum-Yoshida contrast built on a modified Hayashi-Yoshida covariation. It is designed for non-synchronous ticks and resolves lags down to 100 µs.
   - Where it goes: an **EOD tool** (`tools/leadlag_eod.py`, not in the engine). Run it on the recorder's raw sequenced logs (D-026) for each heavyweight against Nifty futures, per episode window and per day.
   - Value: this is the statistically valid answer to "measure the lag" (D-057). It replaces LagMeter's crossing-clock race as the number that judges study F1. MIT, so it can be a dependency.
2. **bashtage/arch** (https://github.com/bashtage/arch; LICENSE.md is in the repo, and I believe it is NCSA, which is permissive, but the fetched page did not show the licence name). Repo opened.
   - What it is: `arch.bootstrap` provides Stationary and Circular Block bootstraps plus **SPA / StepM / MCS** multiple-comparison tests.
   - Where it goes: the **learning loop** (`engine/learning.py`), as an EOD report. With 12 variants plus RAW, the "winner" is selected from many candidates. SPA or StepM against the RAW/random-control books answers "is any variant better than chance after snooping". A block-bootstrapped null of the BASKET-LED rate also gives F1 a proper p-value.
3. **nkaz001/hftbacktest** (https://github.com/nkaz001/hftbacktest, MIT). Repo opened.
   - Idea: model **feed latency explicitly**, keeping an exchange timestamp and a local-receipt timestamp per feed.
   - Where it goes: a **replay variant** in `feed_replay.py` that injects per-socket delay (hero 0 ms, movers/rest +250/500/1000 ms). Run the same day through it and check whether the BASKET-LED rate and the gap-variant P&L survive.
   - Value: anything that flips sign under a 500 ms skew is an artefact (F3).

## Top 3
1. **Pre-register a null for every domino label and lag.** In the EOD report, compute the BASKET-LED rate and the lag median on a time-shuffled or phase-randomised copy of the day (or with stocks shifted ±1 s), and report observed minus null. Restate the D-015 bar as "basket-led rate significantly above the null rate", not "≥ 15 %". This is observer-only, so I-11 is untouched. **S — before Monday.**
2. **Gate stock-scale learning on `in_session`, like futures** (`domino.py:91`, and the same for `BankLead.update`, which should also respect `learn_scales`). This is a bug fix to scale estimation, not a trigger change. It stops the 09:25 synchrony inflation in every book from day one. **S — before Monday.**
3. **Make the gap variants measurable before trusting them.**
   - Log `gap_cov` (Σmi with no 1/coverage extrapolation) and the per-name quote age next to `gap`.
   - Run the EOD Hayashi-Yoshida lead-lag tool (idea 1) on the raw logs.
   - Add the latency-injection replay (idea 3).
   - Keep `gap3/gap5` as they are (pre-registered), but tag each of their trades with the futures' last-1 s move, so the learning loop can see whether they are buying pauses.
   - **M — later** (logging fields before Monday if cheap).

---

# Member 13: OI, PCR and dealer-gamma analytics

## Lens
I looked at the option-chain path for Nifty weeklies, end to end:
- `feed_breeze.poll_chain` / `write_chain` writes `data/chain_latest.json`.
- `engine/levels.Pressure` reads it to build the OI walls, PCR and destination/room.
- `engine/gex.GexMap` builds the dealer-gamma map from the same file.
- `engine_main.update_gex` feeds that map.
- Both advisors (`room` and `gex_room`) are in `engine_main.advise`, lines 410-450.

How I checked: I read all of the code above. I ran two probe scripts against the real modules (in my scratchpad as `m13/probe.py` and `probe2.py`). I ran `tests/test_core.py`, and all tests pass. I also checked Apex's Black gamma against py_vollib's reference value and it matches to 1e-12.

## Teardown

### F1 (HIGH): `gex_room` compares weekly strike levels to the monthly futures price
- **Where:** `engine_main.py:449` calls `self.gex.advise(d, ctx["fut"])`. But `ctx["fut"]` comes from `NIFTY|FUT`, which is the monthly contract (`feed_breeze.py:343`, `self.mexp`).
- **What is wrong:** The map is built at `F = self.fwd`, the w0 synthetic forward (`engine_main.py:364, 467`). Its walls and flip are strike levels in that weekly-forward space. `advise()` (`gex.py:125, 129`) then measures `wall - fut` and `flip - fut` against the monthly price. The docstring at `gex.py:116` treats "futures" and "forward" as the same thing, and they are not. The monthly-minus-weekly basis is often 40-120 pts, which is bigger than both of the advisor's thresholds (20 pts for the wall, 30 pts for the flip).
- **Failure scenario (probe2):** forward 25012, call wall 25100, monthly futures 25092.
  - The advisor vetoes the CE with "call gamma wall 25100 is only 8 pts ahead". The real distance is 88 pts.
  - With the same numbers it never vetoes PE entries near the put wall.
  - Once the monthly price is above the call wall, the wall counts as "behind", even though the weekly forward is still 80 pts below it.
- **Effect:** the `gex_room` verdicts logged to the learning loop are biased by the basis. The SPRT would then judge an advisor that is mis-measured, not the gamma idea itself.
- **Why the test misses it:** `test_gex_map_regime_walls_flip` passes `F` as the `fut` argument too, so the mismatch never appears.
- **Fix:** pass `self.fwd`, or `spot + (fwd - spot)`, to `advise`.
- **Contrast:** `Force.levels` (`levels.py:121`) maps walls into futures space with `+ (fut - spot)`. That is correct.

### F2 (HIGH): a half-failed chain poll is published as a valid chain
- **Where:** `feed_breeze.py:483-505`.
- **What is wrong:** If the put request comes back with no `Success` rows (a Breeze error payload, a throttle, or an empty response), the loop simply adds nothing. `out` still holds the calls, so the file is written and `chain_version` is bumped. The poll only gives up early when an exception is raised or the token ledger is empty.
- **Failure scenario (probe):** with a calls-only chain, the gamma map reports balance +1.00 and regime DAMPEN. `gex_room` then vetoes every CE and every PE entry for at least 90 s. PCR becomes 0.0, there are no put walls, so `room` on PE has "no wall data". The bad snapshot is also recorded into replays (`rec.put("chain")`).
- **Fix:** publish only when both legs returned rows and their strike counts are roughly equal. Otherwise keep the previous file and log the failure.

### F3 (MEDIUM): stale or foreign chain files are trusted, and nothing ever checks staleness
- **What is wrong:**
  - **At startup:** the shared table starts at `chain_version=0` and `Pressure.version=-1`. So `refresh` (`levels.py:54-65`) loads whatever `chain_latest.json` is already on disk. That can be yesterday's file, last week's expiry, or synthetic output from a `feed_sim` or `feed_replay` run, because all three feeds write to the same path in `DATA_DIR`.
  - **Expiry is never checked:** `pressure.expiry` is never compared with the engine's `w0`. For a past expiry (my probe used 2026-10-13), `years_to_expiry` drops to its 60-s floor, `T_days=0.0`, and the gamma map is computed on effectively infinite gamma.
  - **Age is never checked:** `chain_age` is computed but only displayed (`app.js:309`). If polling fails all day, for example because of a wrong `rest_expiry` format on a holiday-shifted week, `room` and `gex_room` keep producing verdicts from the last good chain.
- **Fix:** at load time, require `expiry == w0` and `chain_ns > 0`. In both advisors, return "no data" when `chain_age > 3 × CHAIN_POLL_S`.

### F4 (MEDIUM): the two "wall" definitions disagree, and the stricter one usually finds nothing
- **The two rules:**
  - `Pressure._walls` (`levels.py:81-93`) needs OI ≥ 2× the mean of the ±3 neighbouring strikes, and in the top quartile.
  - `GexMap.wall` needs OI ≥ 1.5× the mean of its side of the chain.
- **Failure scenario (probe):** I used a realistic Nifty chain where 100-point strikes carry about 1.6× the OI of 50-point strikes, with smooth peaks at 25200 CE and 24800 PE.
  - GEX finds walls at 25200 and 24800.
  - Pressure finds no walls at all. Only an isolated 2.5× spike was detected.
- **Why it matters:** the neighbour mean includes the other 100-point strikes, so the usual bulges in the chain cannot pass a 2× test. `room` treats "no wall" as "no veto" (`engine_main.py:416`), so the advisor is quietly biased toward permitting trades. The dashboard can also show a GEX wall where the OI panel shows none.
- **Fix:** record both definitions, and log on each trade which rule found which wall. Don't silently pick one.

### F5 (LOW-MEDIUM): `room` is measured from cash spot and judged against the weekly contracts
- `destination(ctx["spot"], d)` (`engine_main.py:410`, `levels.py:95`) measures from spot to a strike. Strikes live in forward space, which sits about 5-30 pts above spot early in the week.
- So upside room is overstated and downside room understated by the weekly carry. That is a sizeable error against a `1.3 × need` threshold that is typically 40-80 pts.
- After 13:00 on expiry day, `need` uses the delta of a w1 contract while the walls are still w0 (0DTE) walls.
- Verified by reading.

### F6 (LOW)
- **"Change since open" is not reliable:** `oi0` is "the first chain this process saw" (`levels.py:65`), so an engine restart at 11:00 resets the change-since-open figures. Breeze's REST chain may carry its own day-change OI field (UNVERIFIED: I could not hit the API). If it does, that field would be robust to restarts.
- **D-062 and the code describe the DAMPEN exception differently:** D-062 says the advisor vetoes in DAMPEN "unless price is already beyond the flip". `gex.py:124-125` instead escapes when the flip is less than 30 pts ahead. The code's version is the coherent one, because DAMPEN at F means F is on the positive side of the flip. The decision log should be updated to match.

## Good things
- **Honest framing of the gamma map** (`gex.py:12-21`):
  - The dealer-sign assumption is stated, along with the doubt about it on retail-heavy Nifty.
  - The outputs are unit-free (balance = net/gross, plus levels), which correctly avoids relying on Breeze's OI units.
  - It is an advisor only.
- **The flip is computed properly** (`gex.py:80-88`): gamma is recomputed on a ±3% grid of hypothetical forwards, not taken from a single cumulative-sum shortcut. It interpolates linearly and takes the sign change nearest the current forward.
- **The wall rule avoids a common trap** (`gex.py:68-77`): the strike must first stand out on OI, and only then is the largest exposure taken. Picking by largest exposure alone would always pick the ATM strike.
- **Per-strike IV:** live IV is used where the band has quotes, with ATM IV as the fallback. Gamma uses the Black-76 formula on the synthetic forward, which I cross-checked against py_vollib.
- **The map cannot crash the engine:** recompute is cached on (chain version, 10-pt forward bucket), and every failure path returns `ok: False` or is caught (`gex.py:104-112`, `engine_main.py:456-475`).
- **Atomic writes and replayability:** the chain file is written via a temp file and replace (`feed_breeze.py:555-561`). The snapshot is versioned through the shared table and recorded for replay, so chain-driven advisors replay exactly.
- **`Force.levels` gets the futures mapping right** with `K + (fut − spot)` (`levels.py:120-122`).

## Ideas from GitHub
1. **VarunS2002/Python-NSE-Option-Chain-Analyzer**
   - Link: https://github.com/VarunS2002/Python-NSE-Option-Chain-Analyzer
   - Licence: GPL-3.0, so I would borrow the concept only.
   - I cloned it. `NSE_Option_Chain_Analyzer.py`, lines ~1087-1367, tracks *change in OI* at the max-OI strikes ("Call/Put Boundary") and raises "Call Exits / Put Exits" when writers at the wall are unwinding.
   - **Apex mapping:** a new observer, `wall_unwind`, in `levels.py`. For the destination wall, log the OI change across the last N chains, which `Pressure` already keeps versioned. A wall losing OI as price approaches is a weakening wall: `room` should not veto, and `force` should lean toward BREAK.
   - It would be pre-registered as an advisor and judged by the SPRT. That turns static OI walls into a dynamic signal, which is the real information on Nifty weeklies.

2. **jensolson/SPX-Gamma-Exposure**
   - Link: https://github.com/jensolson/SPX-Gamma-Exposure
   - Licence: none found, so all rights reserved and concept only.
   - I cloned it. `GEX.py`, lines 225-261, drops contracts with |delta| > 0.95 or IV outside 1-200% before summing exposure, then plots exposure against a grid of forwards and reads the zero-GEX level.
   - **Apex mapping:** add the |delta| < 0.95 filter in `GexMap.compute`, because deep-ITM weekly OI with stale IV skews `gross`. Also publish the grid curve (`tot`) in the view, so the dashboard shows the gamma profile rather than a single flip number.
   - Size S. It's an observer change only, not a trigger change.

3. **vollib/py_vollib**
   - Link: https://github.com/vollib/py_vollib
   - Licence: MIT.
   - I cloned it. `vollib/ref_python/black/greeks/analytical.py:136` has reference Black-76 gamma with doctest values.
   - **Apex mapping:** test tooling only. Add a test that pins `greeks.greeks` gamma, delta and vega to these reference values; with r=0 Apex matches 0.065309. That guards GEX against a silent change to the Greeks. No runtime dependency is needed, just the constants.

## Top 3
1. **Fix F1:** feed `gex.advise` the weekly forward (`self.fwd`) instead of monthly `ctx["fut"]`, and add a test where `fut ≠ F`. Size S. Before Monday, because every `gex_room` verdict logged until then is biased by the basis and contaminates its SPRT record.
2. **Fix F2 and F3:** publish a chain only when both legs returned rows. At load time, require `expiry == w0` and a non-zero `chain_ns`. Make `room` and `gex_room` return "no data" when the chain is older than 270 s. Size S. Before Monday.
3. **Wall work:** reconcile and record the two wall definitions (F4), measure `room` in forward space (F5), and add the `wall_unwind` OI-change observer (idea 1). Size M. Later, as pre-registered advisors or variants after the weekend.

---

# Member 14 — Experimental design & overfitting risk

## Lens
Whether the learning loop (apex/engine/learning.py), the variant/control set (apex/config.py:89-115), the candidate ledger (apex/engine/ledger.py) and diagnostics (apex/engine/diagnostics.py) can produce a conclusion you can trust, and how long that takes. Tests pass (`tests/test_core.py`, all ok). I checked the error rates with a Monte Carlo probe that calls the real `learning.paired_test` and `learning.sprt_lines` on synthetic null books. The script is at `/tmp/claude-0/-home-claude/a63e9fa2-7e12-5819-bed7-d06bfece2a8a/scratchpad/m14/probe.py`. The synthetic books are nested: the 9 grid variants take subsets of the same episodes with the same returns, plus 4 independent challengers. Each run has 60-300 trials, so every rate below is about ±5 percentage points.

## Teardown

**F1. CRITICAL: the SPRT's assumed sigma of 10 % makes GO and KILL close to coin flips. Settings at config.py:120-124, used in learning.py:69-73 and 252-258.**
All-in weekly option buys at LTP will almost certainly have a per-trade sd well above 10 %, because 0DTE trades swing ±30-60 %. With narrow lines (GO = 110.9 + 1.25n), a handful of large winners or losers crosses one of them. Probe results:
- True mean 0, sd 25 %: false GO in **25 %** of runs (nominal 5 %).
- True mean −3 % (a losing system), sd 25 %: false GO in **17 %** of runs.
- True edge +2.5 %, sd 25 %: KILL in **57 %** of runs.

Mitigation exists only on paper. The "re-register sigma" warning appears only after 30 trades (learning.py:264), and by then the SPRT has usually already decided. A KILL also retires the champion for good (learning.py:286-288).
Verified: probe.

**F2. HIGH: checking every evening with a 2-evening streak inflates false promotions about 3-5 times. Code at learning.py:277-283 and 365-370.**
Bonferroni at 0.05/12 controls a single look: probe = **6.7 %** family-wise at day 80, close to nominal. But `learn()` looks every evening from day 10. Consecutive evenings share n−1 days, so needing two passes in a row adds almost no protection. Probe over 80 sessions under a true null: a challenger is promoted in **15-18 %** of runs at sd 10-25 %, and **30 %** when the true per-trade mean is −3 %. D-066 fixed the per-look alpha (from about 19 %) but not the repeated looks. Gated books (learning.py:352-374) use the same machinery, so they share the problem.
Verified: probe (single look vs every evening).

**F3. HIGH: the `random_entry` null is not fair, because daily log growth mixes up edge with how many trades a book takes. Code at learning.py:61-66 and 220-232, config.py:114.**
Every comparison uses 100·Σln(1+r) per day. ln is concave, so each extra trade adds a variance drag (and with a negative mean, a negative drift). `random_entry` fires a fixed ~6 trades/day (Poisson, `RANDOM_ENTRIES_PER_DAY`, never matched to the champion's actual rate). A champion that trades less "beats" it just by being idle. Probe, where the champion takes ~1.7 trades/day and the control 3-9:
- No edge (mean 0, sd 25 %): the champion is declared to beat random in **28 %** of runs (nominal 1.7 %).
- True mean −3 %/trade: the champion is declared to beat random in **83 %** of runs. A losing trigger passes the null test.

The control also uses one random seed per day (paper.py:229), so its own noise is about the size of the effect being tested.
Verified: probe plus reading.

**F4. MEDIUM: two of the three controls stop matching the champion once the champion changes. Code at config.py:110-112 and learning.py:320-323.**
`futures_only` is hard-wired to m*=2.0 and `premium_momentum` is the null for `straddle_spike`. Yet the report always compares the current champion with all three, "since registration". If m1.5_s0.4 or gap3_s0.4 becomes champion, "futures_only" is no longer "the champion without the basket", and its verdict changes meaning without warning. For the m/s champions, `premium_momentum` tests a different hypothesis altogether.
Verified: read.

**F5. MEDIUM: the advisor screen pools RAW trades from different champions. Code at learning.py:330 and engine_main.py:141.**
RAW is rebuilt each morning with the then-current champion's parameters (engine_main.py:141). The screen, however, reads RAW "since registered" (learning.py:330), not since `champion_since`. After a champion change, each advisor's gain, top-quartile share and LODO mix trades from two different triggers. Gate demotion (learning.py:358) also reads this pooled screen.
Verified: read.

**F6. MEDIUM: the candidate ledger records nothing when the champion is `straddle_spike`. Code at ledger.py:53.**
`not p.get("spike")` skips every episode. If the loop promotes straddle_spike, D-070's "every opportunity, taken or not" evidence stops, along with every diagnostics table built from it (diagnostics.py:77-111). There is no warning.
Verified: read.

**F7. LOW-MEDIUM: diagnostics are many uncorrected splits of clustered data. Code at diagnostics.py:23-31 and 65-111.**
The diagnostics show Wilson intervals for 13 advisors × vetoed/passed, plus regimes, reasons and z buckets. Candidates within a day share the trend, and their 15-minute follow windows overlap, so the iid Wilson interval is too narrow. With about 40 splits, roughly 2 will look "significant" by chance. The tables are labelled "descriptive only", which is right, but the owner will still read them, so the header should say they are exploratory and the intervals are not adjusted. A candidate starts on +1R vs −1R in futures, so a 50 % hit rate is the right null. Good choice; it should be printed.
Verified: read.

**F8. LOW: KILL replacement picks the best raw sum over all history among 12 variants (learning.py:290-298).** This is a winner's-curse pick, partly offset because its SPRT restarts forward. The Bonferroni divisor for gates (learning.py:352) is computed before that evening's new candidates are added. Both minor.
Verified: read.

### How long until a conclusion is trustworthy
The closed form below is 80 % power for a one-sided test, with per-trade sd σ, edge δ per trade and k trades/day. Days needed ≈ (z_α+z_β)²·2σ²/(kδ²).

For champion vs random_entry (α = 0.05/3), with δ = 2.5 %:

| per-trade sd σ | trades/day k | days needed |
|---|---|---|
| 10 % | 2 | ~140 (≈ 7 months) |
| 25 % | 2 | ~880 (≈ 3.5 years) |
| 25 % | 4 | ~440 |

Champion vs 0 on per-trade returns needs about ((z_α+z_β)·σ/δ)² trades: ~140 at σ = 10 %, ~880 at σ = 25 %.

Probe check: with a true +2.5 % edge at σ 25 %, the champion beat random in only 3 % of 120-session runs.

Challengers differ from the champion by far less than 2.5 %/trade (they are nested grid neighbours). So a real promotion is essentially impossible inside the first year, and **any promotion in year 1 is more likely noise than signal** (F2). Realistically, no rule- or advisor-level conclusion is trustworthy for at least 6-12 months of sessions, and only if the observed sd turns out near 10 %. The first trustworthy number will be the observed per-trade sd itself, after about 30 trades.

## Good things
- **Pre-registration is real.** The variants are a finite fixed grid (config.py:89-115). The loop "never invents new numbers" (learning.py:34), and changes take effect only the next session (I-11). `validate()` (config.py:270-304) blocks a mis-typed registry.
- **Gated books (D-067) are a forward, out-of-sample test.** The screen is in-sample, but the decision uses only days after the advisor became a candidate (learning.py:364, `d > since`). This is the right way to stop 13 screened advisors from snooping their way into the trigger.
- **Controls can never be champion** (learning.py:236-237, 290-291), and their verdicts include "control is ahead" and "too few days" (learning.py:324-326).
- **The random control is reproducible**, seeded per day and book (paper.py:226-239), so replays match.
- **LODO plus `CHALLENGER_MIN_DAYS`** stop single-day promotions. The exact t-distribution is implemented with numpy only (learning.py:77-128).
- **The ledger labels outcomes without looking at the decision** (ledger.py:99-103), and records the would-be contract's returns at fixed times (+1, +5, +15 min). This is the right basis for "does a filter remove good or bad opportunities". Gap-crossed follows are flagged (ledger.py:90-92).
- **Empty days are recorded as 0 %** (learning.py:159-160). There is no survivorship gap.

## Ideas from GitHub
1. **bashtage/arch: White/Hansen SPA, StepM and MCS.** https://github.com/bashtage/arch, NCSA licence (permissive; cloned). `arch/bootstrap/multiple_comparison.py` has classes `SPA` (l.796), `StepM` (l.621) and `MCS` (l.286), all using a stationary block bootstrap. Mapping: add a `run_apex.py report --snoop` **offline tool** (arch needs scipy, so not in the engine). It takes the T × 13 matrix of daily log growth for every variant and asks: "Given we tried all of these, does the best beat the champion, or random_entry?" One test covers the whole correlated family, so per-look Bonferroni over nested books is no longer needed. Report-only (an observer), so it fits D-033.
2. **gostevehoward/confseq: anytime-valid confidence sequences.** https://github.com/gostevehoward/confseq, MIT (cloned). `src/confseq/betting.py` provides `betting_cs`, `hedged_cs` and `betting_lower_cs` for bounded means. Mapping: replace the SPRT (F1) and the evening t-tests (F2) with an always-valid lower confidence bound on per-trade return, with returns clipped to [−100 %, +X %]. You can look every evening without inflating error, no sigma has to be assumed, and `hedged_cs` is a small numpy port. Pre-register it as the scoreboard rule in learning.py.
3. **esvhd/pypbo: Probability of Backtest Overfitting (CSCV), MinTRL and Deflated Sharpe.** https://github.com/esvhd/pypbo, **AGPL-3.0, so borrow the concept, not the code**. Mapping: once there are ≥ 16 sessions, an observer section in report.md splits the days into combinatorial halves. It measures how often the in-sample best variant ranks below the median out of sample (PBO), and prints MinTRL ("days still needed"). That gives the owner an honest "how long until trustworthy" number every evening.

## Top 3
1. **Re-register `SPRT_SIGMA_PCT` at a conservative 30 % now, while there is still no live data.** That is still a valid pre-registration. Also block GO/KILL before 30 trades. (S, **before Monday**.)
2. **Stop deciding every evening.** Promotions for challengers and gates should be evaluated only at pre-registered checkpoints (e.g. sessions 20, 40, 60, with an O'Brien-Fleming / alpha-spending boundary). Later, replace this with confseq's anytime-valid bound or a `--snoop` SPA report. (S for checkpoints, **before Monday**; M for confseq/SPA, later.)
3. **Make the nulls fair.** Compare the champion with the controls on **per-trade** mean return (the D-064 unit), not daily log growth. Rate-match `random_entry`, or run 10-20 seeds and use their pooled distribution. Re-point `futures_only` to the current champion's m*, and compare `premium_momentum` only with `straddle_spike`. Fix the ledger skip (F6) and RAW `since` (F5) at the same time. (M, per-trade comparison and F5/F6 **before Monday**, the rest later.)

---

# Member 15: Observability, logging and audit trail

## Lens
After a bad day, can the owner rebuild why each decision was made? I looked at the tick tape (`feed_core.Recorder`), engine/feed logs, the dashboard state blob, books JSON, trades CSV, the candidates/episodes/straddle jsonl files, `days.jsonl` and `report.md`. I ran the tests (they all pass) and wrote two probe scripts in `/tmp/council/15/`.

## Teardown

**1. CRITICAL: one feed crash corrupts the rest of the day's tick tape, and replay then crashes on it. Verified by probe.**
- `feed_breeze.py:507-530`: `run()` has no `try/finally`. Any exception that is not a KeyboardInterrupt skips `shutdown()`, so `rec.stop()` never runs. The recorder is a daemon thread (`feed_core.py:213`), so the gzip member is never closed. The same is true for a hard kill (supervisor `terminate()`/`kill()` at `run_apex.py:110-116`, console close, power loss).
- The supervisor restarts the feed (`run_apex.py:96-101`). The new `Recorder` opens the same `data/ticks/DAY.jsonl.gz` in `"at"` mode (`feed_core.py:225`) and appends a new member after the broken one.
- Probe (`/tmp/council/15/probe_gz.py`): process 1 writes and flushes 1,000 lines, then `os._exit`. Process 2 appends 1,000 more lines and closes cleanly. Reading the file back fails after 785 lines with `zlib.error: invalid block type`. Every line written after the restart is unreadable.
- `feed_replay.py:61` catches `(EOFError, OSError)`, but `zlib.error` is not an `OSError` (checked: `issubclass(zlib.error, OSError) == False`). I ran the replay loop's own except clause against the file and the exception escapes, so the replay feed dies with a traceback.
- Failure scenario: the feed throws once at 11:00 and is restarted. The tape for 11:00-15:30 is lost for good, and the very day you most need to replay is the one that cannot be replayed.
- Fix (size S): wrap the loop in `try/finally: self.shutdown()`. Give each process start its own file (`DAY.<pid or start_ns>.jsonl.gz`) and have replay merge the parts in order. Catch `zlib.error` and `gzip.BadGzipFile` in replay.

**2. HIGH: the champion's reason path is never saved, only one sample of it.**
- `engine_main.py:567-568`: `last_reason` is overwritten every 100 ms. It reaches disk only twice per episode: at the m* crossing (`ledger.py:80`, `decision_at_cross`) and at onset (`extras.py:177`, `verdict_at_onset`).
- `self.events` (`engine_main.py:69`, `deque(maxlen=120)`) holds ENTRY, EXIT, GAP, ARMED, SPIKE and LEARN events. It lives in memory and in the dashboard blob, and is never written to a file (verified by grep: no writer exists).
- Failure scenario: an episode shows "synchrony 0.42 < 0.5" at the cross, then 20 s later "LATE: futures already 31 pts". The owner sees only the first reason, so `diagnostics.reason_class` puts the miss in "basket too thin" when the real blocker was lateness. A restart in the middle of the day also wipes the event tape.
- Fix (size S): add `decisions_DAY.jsonl`. For every book, append a row whenever its reason class changes (dedupe on class), with `t`, book, reason, z, S, moved, iv_rise and episode id. Also append every `ev()` call to `events_DAY.jsonl`. This adds a few hundred lines a day.

**3. HIGH: the tick tape can drop data without telling anyone.**
- `feed_core.py:218-221`: when the queue is full, `Recorder.put` increments `self.dropped`. Nothing ever reads `dropped` (grep shows only the two lines that define and increment it). It is not in the table, the log or the dashboard.
- Replay would then differ from live with no warning. Fix (size S): publish `rec_dropped` as a table counter, log it at stop, and write a final `{"k":"meta","dropped":N}` line to the tape.

**4. MEDIUM: engine log timestamps use the wall clock, so sim/replay logs don't line up with market time.**
- `engine_main.py:42` uses `datetime.now(IST)`, but `ev()` and every jsonl record use the virtual `now_dt`. A replay at 20x speed logs "12:03:11 ENGINE ledger: KeyError" with no way to tie it to the 10:41 candidate. Fix: log both, `wall | mkt=HH:MM:SS`.

**5. MEDIUM: replay and sim reruns double-count in the diagnostics.**
- `Ledger._write` (`ledger.py:122`), `EpisodeLog._flush` (`extras.py:192`) and StraddleWatch all append, and `diagnostics.load_candidates` (`diagnostics.py:33-46`) does not dedupe. Replaying the same day twice into `data/replay` doubles that day's candidates, which narrows the Wilson intervals with fake data. `record_day` is idempotent; these files are not. Verified by reading only. Fix: dedupe on `(day, id)` in `load_candidates`, or truncate the per-day files in `start_day` when the books file does not exist yet.

**6. MEDIUM: no record says which code or config produced it.**
- No trade, candidate, `days.jsonl` row or report stamps `apex.__version__` or a hash of `config.VARIANTS`/thresholds. `learning._r` already has to guess "legacy rows: premium points" (`learning.py:57-60`). `report.md` is overwritten every evening (`learning.py:403`), so the report that justified yesterday's champion change is gone. Only one-line entries survive in `state.log`.
- Fix (size S): add `v` (version) and `cfg` (an 8-character sha of the frozen params plus advisor list) to every record, and also write `report_DAY.md`.

**7. MEDIUM: a stalled engine or an oversized state blob just looks like a frozen screen.**
- `StateBlob.write` (`table.py:165-166`) silently `return`s when the state is over 2 MB.
- `engine_hb_ns` is written (`engine_main.py:705`) but never read anywhere. The supervisor only checks for process exit, and `app.js` has no staleness check (grep for stale/hb finds nothing).
- Failure scenario: the engine hangs inside a Greeks solve. The dashboard keeps showing the last ENTRY with live-looking numbers, and no gap event is recorded because the guard runs inside the same stalled loop.
- Fix: the gateway compares `engine_hb_ns` with the current time and adds `engine_age_s`, and the UI shows a red banner when it exceeds 2 s. Log the oversize case once per minute.

**8. LOW: what survives in the analysis files is thinner than what was recorded.**
- `days.jsonl` stores advisors as booleans only (`learning.py:172`).
- The trades CSV (`paper.py:456-458`) is champion-only and drops `episode`, `delta_in`, `iv_in`, `stop_fut`, `peak_pts`, `exit_quote_age` and the advisors.
- The full detail is in `paper/DAY.json`, so nothing is lost, but the owner's spreadsheet view hides it.
- `run()` logs a full traceback on every failing step (`engine_main.py:702`) with no rotation.

## Good things
- **The position record is a real audit snapshot.** `paper.open_trade` (`paper.py:318-328`) freezes the reason string, every advisor's verdict *with its `why` text*, delta, IV, entry bid/ask, regime and episode id. `close_trade` adds exit bid/ask, quote age, `stale_exit` and `fut_out`.
- **Books are written atomically** (`paper.py:433-438`, tmp file plus `os.replace`) after every trade change (`engine_main.py:585`), so a crash loses no trades.
- **The candidate ledger** (`ledger.py`) is the strongest observability piece. It records every m* crossing, taken or not, labels it with no reference to whether it was taken, and marks `follow_gap`/`truncated` honestly. `diagnostics._row` excludes truncated NEITHER rows correctly.
- **Episode and spike ids come from the virtual clock** (`domino.py:166`, `straddle_watch.py:254`). They are deterministic in replay and do not collide after an engine restart.
- **The tape records raw packets with receive time, plus REST, chain and registry snapshots** (`feed_breeze.py:545`, `:504`), so replay can rebuild row re-numbering.
- `record_day` is idempotent per day and records empty days (`learning.py:158-180`), and `test_learn_is_idempotent_per_evening` tests it.
- Observers are wrapped in rate-limited try/log (`engine_main.py:238-241`, `255-258`, `290-293`), so a broken advisor cannot stop the loop.

## Ideas from GitHub
1. **freqtrade/freqtrade**, https://github.com/freqtrade/freqtrade, GPL-3.0 (concept only, no code).
   - `docs/advanced-backtesting.md` and `freqtrade/data/entryexitanalysis.py`: `backtesting-analysis --analysis-groups 0..5` gives profit by `enter_tag` × `exit_tag`, and `--rejected-signals` prints every signal that was suppressed.
   - Mapping: an `run_apex.py report --groups` tool that reads `paper/DAY.json` plus the new `decisions_DAY.jsonl`. It would show tables by entry reason class × exit reason (STOP, TRAIL, THESIS, TIME), and by rejection class over time, not just the reason at the cross.
   - This is an offline tool, so it does not touch the trigger.
2. **simonw/sqlite-utils**, https://github.com/simonw/sqlite-utils, Apache-2.0.
   - `sqlite-utils memory` (docs/cli.rst:464-496) loads CSV/JSON files into a temporary in-memory database and runs SQL on them in one command. `insert --nl` loads jsonl.
   - Mapping: a `run_apex.py autopsy DAY` tool. It loads `candidates_`, `episodes_`, `straddle_`, `decisions_` and the trades into one SQLite file keyed on episode id, so "why no trade at 10:41?" becomes a single join.
   - This is a dev tool only, with no runtime dependency.
3. **hynek/structlog**, https://github.com/hynek/structlog, MIT/Apache-2.0.
   - `contextvars.bind_contextvars`/`merge_contextvars` (`src/structlog/contextvars.py:82,119`) bind context once, and every later log line carries it as JSON.
   - Mapping: in `engine_main.step`, bind `mkt_t`, `episode`, `champion`, `cfg` and `v`. Then every `log()` line and decision row is machine-joinable to the ledger. This fixes findings 4 and 6 together.
   - Swapping the 6-line `log()` for a JSON formatter is enough; adding the dependency is optional.

## Top 3
1. **Make the tick tape survive a crash** (finding 1): `try/finally` shutdown, one file per process start, and replay catching `zlib.error`. Size S, **before Monday.**
2. **Persist the decision and event tape** (findings 2 and 3): `decisions_DAY.jsonl` written when a reason class changes, `events_DAY.jsonl`, and the recorder drop counter surfaced. Size S, **before Monday.**
3. **Provenance and liveness** (findings 6 and 7): stamp version and config hash on every record, write a dated `report_DAY.md`, and add an engine heartbeat staleness banner. Size S-M, **later** (the heartbeat banner part could go before Monday).

---

# Member 16 — Performance & latency

## Lens
The engine's 100 ms step, its numpy hot paths, how much it allocates, what `publish()` costs, and what the paper books cost.

**Method.** I copied the repo to `/tmp/council/16/ApexOptions` (the original was not touched). I wrote an in-process harness (`/tmp/council/16/harness.py`) that runs `feed_sim.Sim.step` and `Engine.step()`/`publish()` in lockstep: sim at 4 Hz virtual, engine at 10 Hz, publish at 4 Hz. Setup: seed 7, 121 instruments, 68 options, 17 books. All numbers below are **per-thread CPU time** (`time.thread_time`). The box had 2 cores and a load average of 18 (the other council members), so wall-clock was about 6x worse and is not reported. I also ran cProfile and a wrapper that times each component. Tests pass on the copy.

**Headline numbers (45 virtual minutes, 27,000 steps):**

| | mean | p50 | p99 | max |
|---|---|---|---|---|
| `Engine.step()` | 5.11 ms | 2.86 | 14.59 | 26.7 |
| `publish()` | 1.92 ms | 1.91 | 3.43 | 5.9 |
| sim step (feed) | 2.29 ms | 2.21 | 3.87 | 6.0 |

At 10 Hz live, the engine uses about 6 % of one core, so live has plenty of headroom. The state JSON is 19–31 kB, against a 2 MB limit. Step time is bimodal: steps that also compute Greeks take about 10–15 ms, the others about 3 ms.

**Per-component CPU (unprofiled wrapper, 2,400 steps):**

| component | per call | per step (amortised) |
|---|---|---|
| `compute_greeks` (4 Hz) | **7.04 ms** | **2.35 ms (~47 % of the step)** |
| `Flow.update` | 0.75 | 0.75 |
| `Pressure.refresh` | 0.34 | 0.34 |
| `coherence` | 0.27 | 0.27 |
| `Market.push` | 0.23 | 0.23 |
| `option_rows` / `Domino.update` / `update_gex` | ~0.18 each | |
| `run_books` (all 17 books) | **0.020** | 0.020 |
| `Regime.update` / `Ledger.update` / `EpisodeLog.update` | 0.013 / 0.009 / 0.005 | |

## Teardown

**F1 — Implied vol takes half the engine's CPU, and most of that is wasted. Severity: medium (headroom; it makes F2 worse).**
- **Where:** `apex/greeks.py:61-74` and `apex/engine_main.py:337-353`.
- **What is wrong:** each Greeks pass calls `implied_vol` twice, once per expiry (50 rows, then 18). Each call runs 40 bisection iterations. Each iteration prices both the call and the put through four `ncdf` calls, then keeps one with `np.where` (`b76_price`, lines 56-58). Forty iterations on [0.005, 5] give about 1e-12 precision; 20 already give 0.0002 vol points.
- **The cost is per call, not per row:** a 68-row call costs the same as an 18-row call (about 2.6 ms).
- **Prototype:** one merged call (array `T`), one priced leg via the sign trick, 20 iterations. Result: 5.49 ms down to 0.78 ms (**7.0x**), maximum difference 0.0002 vol points, no change in which rows come out NaN (probe script in this session).
- **Smaller extra cost:** the per-strike `nanmean` list comprehensions at lines 348-349 scan every row once per strike.
- **Verified by:** cProfile (`_erf` is the top function by self time, 403k calls in 6 minutes) and a microbenchmark.

**F2 — Replay and sim at `--speed` 10 or more cannot sample at 10 Hz, so they are not "identical at any speed". Severity: medium.**
- **Where:** `engine_main.py:709`, `time.sleep(max(0.1/speed - elapsed, 0.005))`. The sleep never goes below 5 ms, so each real cycle takes at least elapsed + 5 ms.
- **What follows:**
  - At `--speed 20` (the README's replay example) the engine can never step faster than 5 Hz virtual: a 0.2 s minimum, and about 0.38 s on Greeks steps.
  - At `--speed 10`, Greeks steps (10–15 ms) overrun the 10 ms budget, which is roughly 40 % of steps (derived from the measured distribution).
  - `market.py:5-6` claims "time-based, so replay at any speed is identical". That is not quite true. `Flow._rb`/`_rs` (`flow.py:66-67,103-106`) is a ring of 100 **samples** called "10 s", so at 5 Hz it covers 20 s. That `agg10` feeds the PULLED/DRAIN classification and the order-unit conversion. The EWMAs and the aggressor classification are also per-step.
- **Measured:** same sim, seed and minutes, engine cadence 0.1 s vs 0.2 s virtual.
  - Futures z correlation 0.99999.
  - Hero ask-class agreement 98.95 %.
  - 14 of 17 books had identical trades.
  - In `futures_only`, `premium_momentum` and `straddle_spike`, entry times moved by ±1 s and P&L by up to 0.5 pts.
  - One `premium_momentum` exit moved 55 s (09:27:50 vs 09:28:45).
  - Episode ids differ throughout, because `id = int(now_s*10)` depends on step phase.
- **Impact:** small in this sample, but replay-day learning records are not a faithful stand-in for live behaviour, and nothing on the dashboard reports the cadence actually achieved. The guard only reacts above a 10 s step gap (`guard.py:26`).
- **Verified by:** two harness runs, `run_0.1.pkl` vs `run_0.2.pkl`.

**F3 — `Pressure.refresh` rebuilds the OI arrays on every step, even when the chain has not changed. Severity: low.**
- **Where:** `apex/engine/levels.py:67-77`.
- **What is wrong:** it sorts the dict keys, builds two arrays through Python comprehensions and recomputes the walls and PCR at 10 Hz. Those only change when `chain_version` changes (every `CHAIN_POLL_S`) or when spot crosses a strike.
- **Cost:** 0.34 ms per step, measured, which is the third-largest item.

**F4 — `publish()` serialises the state twice in Python. Severity: low.**
- **Where:** `table.py:208` and `table.py:164`.
- **What is wrong:** `clean()` walks every value recursively (about 1,360 calls per publish under the profiler), and then `json.dumps` walks it all again. The 68 hero dicts are built with about 900 `fnum`/`round` calls per publish (1.22M `fnum` calls in 6 minutes).
- **Cost:** 1.9 ms mean. That is fine now, but it is the second-largest cost.

**F5 — All numpy work runs over 512 rows while 121 are used. Severity: low; the size of the saving is unverified.**
- **Where:** `config.MAX_ROWS = 512`, `market.py:20-28`.
- **What is wrong:** `Market.push`, `Flow.update` (eleven `ago()`-indexed 512-wide slices plus four `_classify` calls) and the 200 kB `snapshot()` copy all work on full-width rows.
- **Memory:** eight 512×600 float64 rings hold 19.7 MB, and each column write is strided by 4.8 kB.
- **Speed:** most of the per-call time here is numpy dispatch overhead, so I expect a modest gain (under 1.5x) from slicing to the used rows. I did not measure it.

**F6 — `Market.ago()` repeats an `arange` + `argmin` over 600 slots on every call. Severity: low.**
- **Where:** `market.py:61-69`.
- **What is wrong:** it runs 143k times in 6 minutes, about 40 times per step, because `run_score` → `m.change(m.ltp, 5)` computes a full 512-row difference to read a single element. That happens 44 times per step in `coherence` and again in `publish`.
- **Smaller repeat:** `ctx["fut_r60"]` computes `m.change(m.ltp, 60)` twice (`engine_main.py:272-273`).
- **Cost:** about 0.3 ms per step in total. A cache of slot per age per step would remove it.

**Not a problem (checked):**
- The 17 paper books cost 0.02 ms per step together.
- `Regime` (1 Hz, its percentile scan grows to about 22k samples by the close) costs 0.013 ms per step.
- The state blob is 1.5 % of `STATE_BYTES`.
- The `save_books` disk write happens only when a book changes.

## Good things
- **Shared memory between processes:** the seqlock with targeted re-reads of torn rows (`table.py:125-138`) costs only 0.065 ms per step for a full table copy. The feed hot path never waits on the engine.
- **Observers can't stop the loop:** each one (regime, watch, ledger, gex) is wrapped in its own try/except with a 60 s rate-limited log (`engine_main.py:232-241, 251-258, 288-293, 472-475`).
- **Loop timing is visible:** `loop_ms`, `hot_p50`/`hot_p99` and an engine heartbeat are all published, and an engine stall is treated as a data gap (`guard.py:44-56`, covered by a test). That is the right instinct.
- **Time-indexed rings:** `Market.ago()` looks up history by timestamp rather than by slot count, so most features already tolerate jitter in the step cadence.
- **Rate-limited heavy work:** Greeks run at 4 Hz, publish at 4 Hz and Regime/OI history at 1 Hz, all rate-limited on the virtual clock.
- **Cheap, isolated books:** each variant is pure Python dicts and costs about 1 µs, so adding pre-registered variants or controls is effectively free.

## Ideas from GitHub
1. **ijl/orjson** (https://github.com/ijl/orjson). Licence: MIT / Apache-2.0 (multi-licensed). It writes NaN/Inf as `null` and serialises numpy arrays natively with `OPT_SERIALIZE_NUMPY`, and it has Windows wheels.
   - **Maps to:** `StateBlob.write` (`table.py:163`). It could replace both the `clean()` walk and `json.dumps`. It is a tool-level change with no effect on trading logic.
   - **Caveat:** it adds one dependency, so it should be optional, falling back to the current path when it is not installed.
2. **benfred/py-spy** (https://github.com/benfred/py-spy). Licence: MIT. A sampling profiler that attaches to a running PID without a restart. It supports Windows, `top`, and flamegraph/speedscope output.
   - **Maps to:** a `run_apex.py profile` helper, or a documented runbook step, that records the live engine for 60 s during the first live week. It confirms on the owner's own machine (feed, gateway and browser all competing) the numbers I measured here. It is an observer tool with zero code in the hot path.
3. **marcdemers/py_vollib_vectorized** (https://github.com/marcdemers/py_vollib_vectorized, cloned). Licence: MIT. It has `vectorized_implied_volatility_black` (`implied_volatility.py:95`), based on Jäckel's "Let's Be Rational".
   - **Do not adopt it at runtime:** it needs numba, scipy and pandas.
   - **Use it offline:** a test that checks Apex's own Black-76 IV (after the F1 speed-up) against it on a grid of 0DTE and weekly strikes, so that cutting the iteration count is proven harmless.

## Top 3
1. **Make implied vol about 7x cheaper (F1).** One merged `implied_vol` call with an array `T`, price only the needed leg, 20 iterations, and vectorise the per-strike `nanmean`. The engine step should drop from about 5.1 to about 3 ms mean, and the p99 from about 14.6 to about 7 ms (estimated from the component split). Add the regression test from GitHub idea 3. The IV changes by at most 0.0002 vol points and the trigger numbers are untouched, so it can ship between sessions. **Size S, before Monday** (out of session only, per I-11).
2. **Make replay cadence honest (F2).**
   - Publish the achieved virtual step interval (p50/p99 of `step_gap`) next to `loop_ms`.
   - Warn when it goes above 0.12 s.
   - Change the floor sleep so the engine only sleeps when it has time to spare, instead of always sleeping 5 ms.
   - Fix the `market.py` docstring, which says replay at any speed is identical.
   - Later, make `Flow`'s "10 s" ring time-based.
   **Size S, before Monday** for the metric and the sleep; the ring is **later**.
3. **Cache `Pressure.refresh` on `chain_version`/ATM, memoise `Market.ago()` per step, and slice to the used rows (F3, F5, F6).** Together these save about 1 ms per step. **Size S–M, later.**

---

# Member 17 — Safety, secrets & paper-only guarantees

## Lens
Credential handling (`secrets/`, `run_apex.py session`), the preflight credential scanner, the no-order guard test, gateway exposure (host/port, Host/Origin, websockets), file writes, and anything that could leak a key or place an order. I checked against baseline 85b65ed and downloaded the real `breeze-connect==1.0.69` sdist (`/tmp/council/17/sdk`) to compare the guard with the SDK's actual method list. Probe scripts are in `/tmp/council/17/probe/`. All 60+ tests pass. The repo was not modified (`git status` is clean).

## Teardown

**F1 — The preflight credential scanner misses the file format the project itself writes. HIGH.**
`run_apex.py:162` `KEYLIKE` expects `api_key\s*[=:]\s*'…'`. In JSON the key is followed by a closing quote (`"api_key": "…"`), so the regex never matches. `cmd_session` writes exactly that format (`run_apex.py:155-156`, `json.dump(c, f)`).
- *Scenario:* the owner copies `secrets/breeze.json` to the root as a backup, or a notes file gets pasted JSON. Preflight still prints `[PASS] no credential-shaped strings`, and the next `git add .` commits the API secret.
- *Other misses (`probe/p.py`):* unquoted `.env` style (`BREEZE_API_KEY=…`), secrets containing `/ = .`, which fall outside the char class at `:162`, `apisession=` URLs, and real keys that happen to contain "sample"/"xxx". `PLACEHOLDER` (`:164`) is applied to the whole match, so the key's own text can whitelist it.
- *Extensions:* only `.py .md .json .js .html .txt .cfg .ini` are scanned. `.yml .toml .env .ps1 .bat .csv .ipynb` are not.
- *Verified:* probe script. 7 of 8 realistic leak shapes are MISSED, including the exact `cmd_session` output.

**F2 — Directory skips in the scanner are substring tests on the absolute path. MEDIUM.**
`run_apex.py:194` `any(x in dp for x in ("secrets", os.sep+"data", ".git", …))`:
- `.git` also skips `.github/`.
- Any folder whose name contains "secrets" (for example `notes_secrets_rotation/`) is skipped.
- Any folder starting "data" (`database/`) is skipped.
- If the checkout ever sits under a path with `\data…` (for example `C:\Users\ankit\data\ApexOptions`), **the whole scan is skipped and the check still PASSes**.
- *Verified:* probe script.
- The `.gitignore` check (`:206`) only greps for the word "secrets". It does not check that `data/` or `logs/` are ignored, and does not ask git (`git check-ignore`).

**F3 — The no-order guard names a method that doesn't exist and misses five that do. HIGH (for the paper-only promise).**
`tests/test_core.py:414` blocks `place_order|modify_order|cancel_order|square_off|place_gtt_order|limit_calculator`. In SDK 1.0.69 there is **no `place_gtt_order`**. The real order-capable methods it does not block are:
- `gtt_single_leg_place_order`, `gtt_three_leg_place_order`
- `gtt_*_modify_order`, `gtt_*_cancel_order`
- `aggressive_limit_order_placement`
- `set_funds`, `add_margin`

The leading `\.` means `.gtt_single_leg_place_order(` never matches. The test is also lexical only:
- `getattr(b, "place_order")(…)`, `fn = b.place_order` and `api_handler.make_request("POST", "order", …)` all pass (`probe/g.py`).
- It scans `apex/` only, not `run_apex.py`, which also builds a logged-in `BreezeConnect` (`run_apex.py:233-234`).
- Nothing enforces paper-only at **runtime**. `config.PAPER_ONLY` is read only by `validate()` (`config.py:302`).
- *Verified:* SDK source grep plus probe.

**F4 — The gateway accepts any Origin and any Host, including on websockets. MEDIUM.**
`apex/gateway.py` has no TrustedHost or Origin check. Probe `probe/ws.py` (FastAPI TestClient against the real `gateway.app`):
- `GET /api/state` with `Host: attacker.rebind.example` returns **200**.
- `/ws/state` from `Origin: https://evil.example` is **ACCEPTED**.

Browsers do not apply CORS to WebSockets. So any web page the owner has open while Apex runs can read the live position, the books, the trades and the learning state from `ws://127.0.0.1:8780`. DNS rebinding also reaches `/api/state` over HTTP.

`/ws/ticks` runs a 4 ms poll loop per connection (`gateway.py:74-102`) with no connection cap. A hostile tab that opens a few hundred sockets would steal CPU from the engine on the same box. That last part is *unverified* (read only).

No credentials are in the state blob, and the gateway has no write endpoints. So this is a privacy and availability problem, not an order risk.

**F5 — Credentials are stored in plaintext inside the project tree, with default permissions. MEDIUM.**
- `cmd_session` stores the **permanent** `api_secret` next to the daily token in `ROOT/secrets/breeze.json` (`run_apex.py:154-156`), with no restrictive mode or ACL.
- On a `D:\` root folder, the default Windows ACL usually gives *Authenticated Users* read/modify (*unverified on the owner's box*).
- Anything that zips, syncs (OneDrive), or hands the project folder to a reviewer or LLM carries `secrets/` with it. (This review copy's `secrets/` was empty, which is good.)
- The SDK also writes `logs/apiLogs.log` relative to CWD (= ROOT) at DEBUG level, including the customer-details response (name, user id; the SDK deletes `session_token` from it, per SDK `breeze_connect.py:1183-1185`). That file is gitignored but lives in the tree.

**F6 — Small items. LOW.**
- `cmd_session` prints the full login URL with the API key (`run_apex.py:145-146`). The app key is semi-public, but it lands in console scrollback.
- The session token is read with echoing `input()` (`:151`).
- A secret with stray whitespace from `getpass` is `.strip()`ed (fine).
- If an existing file has `api_key` but no `api_secret`, the secret is never asked for (`:142`). Preflight then FAILs with a confusing SDK error.
- `RestLedger`, the token cache and the trial counter use non-atomic `json.dump(…, open(p,"w"))` (`feed_breeze.py:206,223,251,257`). If the process dies mid-write, the ledger reads back corrupt and the REST budget resets. That is not money-unsafe, just rate-limit risk.
- `config.py:26-27` creates `secrets/` and `data/` dirs as an import side effect.

## Good things
- **No secret has ever been committed.** I checked `git ls-files` and grepped `git log --all -p`. `.gitignore` covers `secrets/ data/ logs/`.
- **Key and secret are typed through `getpass`** (`run_apex.py:143-144`), never passed as CLI args, so they don't show up in shell history or the process list.
- **The gateway is loopback-only** (`config.py:34`). `port_busy` binds 127.0.0.1 (`run_apex.py:122-130`).
- **The gateway is strictly read-only.** There is no POST route, so no browser path can steer the engine. Static serving is a fixed `FileResponse` plus `StaticFiles`. Path traversal `/static/../config.py` returns 404 (verified).
- **Error strings are bounded and contain no auth material.** `connect_stream` builds `auth` in-process and reports only `type(e)` plus 160 chars (`feed_breeze.py:161-178`). Preflight truncates every SDK error.
- **Global requests timeout patch** (`feed_breeze.py:298-303`). This is also the ideal hook for a runtime endpoint allowlist (see Top 3, item 1).
- **Defence in depth on paper-only, even if leaky:** `PAPER_ONLY` sits in `validate()`, CI runs `validate()` plus the guard on every push (`.github/workflows/tests.yml`), and sim/replay are isolated to `data/sim|replay` (`run_apex.py:37-48`).
- **The dashboard loads no third-party script.** Only Google Fonts CSS; `app.js` is local. There is no CDN JavaScript that could read state.

## Ideas from GitHub (all opened)

1. **gitleaks/gitleaks** — https://github.com/gitleaks/gitleaks — MIT.
   - *Borrow:* `gitleaks dir` plus a `.gitleaks.toml` with `[extend] useDefault = true` and one custom rule for Breeze (`(?i)"?(api_?secret|session_?token|api_?key)"?\s*[:=]\s*"?[^\s",]{8,}`).
   - *Map:* a **tool**. Add it as a pre-commit hook and a CI step, and have preflight shell out to it when it is installed (falling back to the fixed in-house regex). This closes F1 and F2 for every file type and for git history.

2. **Yelp/detect-secrets** — https://github.com/Yelp/detect-secrets — Apache-2.0.
   - *Borrow:* the `.secrets.baseline` concept (known, audited findings are recorded, and only *new* ones fail) plus the high-entropy detectors (Base64 above 4.5, Hex above 3.0).
   - *Map:* replace `PLACEHOLDER` whitelisting (F1's self-whitelisting bug) with an explicit baseline of the doc examples, and with `# pragma: allowlist secret` on deliberate stand-ins.

3. **encode/starlette** `starlette/middleware/trustedhost.py` — https://github.com/encode/starlette — BSD-3-Clause.
   - *Borrow:* `TrustedHostMiddleware(allowed_hosts=["127.0.0.1","localhost"])`, which checks **both http and websocket scopes** and returns 400 on a foreign Host.
   - *Map:* a one-line `app.add_middleware(...)` in `gateway.py`, plus a small Origin check in `ws_ticks`/`ws_state`: if `ws.headers.get("origin")` is not `http://127.0.0.1:8780` or `http://localhost:8780`, close with code 1008. Add a per-endpoint connection cap of about 4. This closes F4.

4. **jaraco/keyring** — https://github.com/jaraco/keyring — MIT (pyproject).
   - *Borrow:* `keyring.set_password("ApexOptions", "breeze_api_secret", s)` / `get_password(...)`, backed by Windows Credential Locker.
   - *Map:* `cmd_session` and `load_credentials`. The permanent `api_secret` goes to the OS vault, and only the daily `session_token` stays in a file (now harmless after 24 h). Keep the file fallback when keyring returns `None`. This closes most of F5.

## Top 3

1. **A runtime paper-only interlock plus a correct static guard. Size S, before Monday.**
   - In the existing `_req` patch (`feed_breeze.py:300`), refuse any URL whose last path segment is not in an allowlist `{customerdetails, quotes, optionchain}`. Raise `RuntimeError("PAPER_ONLY: blocked <endpoint>")` for `order`, `gttorder`, `squareoff`, `funds`, `margin` and the rest. Install the same patch in `cmd_preflight`.
   - After `BreezeConnect(...)`, rebind every attribute matching `order|square|gtt|funds|margin|limit_calc` on the instance and on `ApificationBreeze` to a raiser.
   - Fix the test: derive the forbidden set from `dir(BreezeConnect)` when the SDK is importable, otherwise use the full static list above. Drop the leading-dot requirement, catch `getattr(…, "<name>")`, and scan `run_apex.py` too.
   - Add a unit test that the interlock rejects a fake `.../order` request.

2. **Fix the credential scanner. Size S, before Monday.**
   - Allow an optional closing quote after the key name (`["']?\s*[:=]`), accept unquoted values, and widen the value char class to `[^\s"',]`.
   - Apply `PLACEHOLDER` to the *value* only.
   - Skip directories by `os.path.relpath(dp, ROOT).split(os.sep)[0]` in `{secrets, data, logs, .git, __pycache__}`.
   - Add `.yml .toml .env .ps1 .bat .csv`.
   - Replace the `.gitignore` grep with `git check-ignore -q secrets/breeze.json data/x logs/x`.
   - Add a regression test that feeds the exact `cmd_session` JSON and asserts it is CAUGHT. Later, add gitleaks in CI.

3. **Lock down the gateway and move the long-lived secret out of the tree. Size M, later** (the gateway part, about 10 lines, could go before Monday).
   - Gateway: TrustedHost middleware, a websocket Origin check, and a connection cap.
   - Secrets: the `api_secret` goes to keyring. Support an optional `APEX_SECRETS` directory outside the project (for example `%APPDATA%\ApexOptions`). Have the feed run with CWD in `data/logs` so the SDK's `logs/apiLogs.log` lands under the already-ignored data dir.

---

# Council member 18 — Exit logic & trade management

## Lens
`apex/engine/paper.py` `check_exit` / `close_trade` (stop, trail, thesis-void, book, TIME, 0DTE, deferred and committed exits, blackout), the exits of `straddle_spike` and the control books, and the guard that gates them (`apex/engine/guard.py`). Tests pass (`python tests/test_core.py`, all ok). Probes are in `/tmp/council/18/probe.py` and `/tmp/council/18/probe2.py`. They drive the real `paper.check_exit` and `guard.DataGuard`, and price options with the repo's own `apex/greeks.py` Black-76.

## Teardown

**F1. The 20-second resume window that protects entries also mutes stops on data that is fresh again. HIGH.**
`paper.py:389` drops every price exit while `blackout.on`. `guard.py:103` keeps `on` true until `RESUME_S = 20` s of *continuous fresh* futures quotes have arrived. The docstring (`guard.py:20`) says "exits wait for fresh quotes", but in practice they wait 20 s *after* fresh quotes come back. The 20-s rule exists so that no 15-s impulse window spans a gap. That is an entry concern only. A stop just compares the current fresh futures price with a level, and `paper.py:395` already guards exits against a stale futures quote (`EXIT_FUT_STALE_S = 3`).
*Scenario (probe2, verified):* a long CE, a 4-s websocket stall (common on Breeze), then fresh ticks with futures falling 1.5 pt/s. The futures crossed the stop at t=41.9 s, but the exit fired at t=54.0 s, a 12-s delay. Return was −12.1% against −4.8% at the stop level, so the loss was 2.5× the 1R. The same thing happens after every restart, because the guard starts with `on=True` (`guard.py:34`): an open position reloaded from `load_books` has no price exits for its first 20 s.
The same path applies to a genuine one-tick move above 1%, which `guard.py:66` classes as a bad print. Probe2 shows a 20-s delay there too. That case is rare and partly unavoidable, so I rate it low.
*Fix:* exits should look at `bad_print` and `fut_age` only, not at `on` during the resume phase. Expose `guard.view()["resuming"]` and block exits only when the guard is on *and* not resuming. Size S.

**F2. Every exit is blind to the option's own P&L, and the futures "break-even" trail is not break-even in premium. HIGH (design; affects what the learning loop learns).**
`paper.py:362-364`: when futures reach +d* (12 pts), the trail starts at `best − d*`, which is exactly `fut_in`. So the "worst" trail exit is futures break-even. But the trigger buys during an impulse with ATM IV up as much as 1.5 vol points (`IV_RISE_CAP`), and IV usually gives that back. Probe1 enters with IV +1.5, exits at the same futures level 30 min later with IV back at base, using the bands' typical contracts:

| bucket | premium | STOP (−12 fut) ret | "break-even" TRAIL ret | flat futures 3 h |
|---|---|---|---|---|
| ≥3 DTE, Δ .55 | 157 | −4.3% | **−10.0%** | −11.0% |
| 1 DTE, Δ .65 | 93 | −7.8% | −8.6% | −11.7% |
| 0DTE 10:00, Δ .75 | 64 | −13.0% | −6.5% | −15.7% |
| 0DTE pm next-week, Δ .55 | 200 | −3.3% | −10.5% | −11.0% |

On the ≥3-DTE bucket, a trade that went +1R and then came back loses *more* than a trade stopped out at once. These numbers are model results under stated assumptions, not market data. The direction matches the repo's own finding that the buyer's enemy is IV, not theta (D-019, `01_MASTER_DESIGN.md:77`).
The fixed 12-pt stop also produces an unequal R when measured in `ret_pct`, the unit the learning loop scores (`learning.py:57`, D-064). A stop costs −3.3% on one contract and −13% on another, and at `MIN_PREMIUM` 20 it costs about 12×0.6/20 = 36%. The repo already noted this for premium stops (`01_MASTER_DESIGN.md:208`) but not for the futures stop.
Nothing ends a trade that goes nowhere. If futures chop inside ±12 and synchrony never flips, the position bleeds until 15:25, at a cost of 11–16% in the probe. Under I-11 this cannot change intraday. It has to come in as pre-registered exit shadows (Top 3 #2).

**F3. Trades record no exit Greeks, so the vega share in F2 cannot be measured. MEDIUM.**
`close_trade` (`paper.py:423-427`) records `exit`, bid/ask and `fut_out`, but no `iv_out`, `delta_out` or exit DTE. `open_trade` stores `iv_in` and `delta_in` (`:324`). The master design promises "sticky-IV P&L attribution … for the open position" (`01_MASTER_DESIGN.md:156`), but grep finds no implementation in `apex/`. The learning loop cannot tell whether TRAIL/STOP losses come from delta, vega or theta, which is exactly the "vega exits → frames IV-path study" question (`01_MASTER_DESIGN.md:306`). Verified by reading the code and grepping.

**F4. Spike and momentum books exit on a different thesis than the one they entered on. MEDIUM.**
`straddle_spike` and `premium_momentum` enter on premium excess and a rising leg delta (`paper.py:192-214`, `276-301`). Their exits are the futures 12-pt stop/trail and the *heavyweight-synchrony* THESIS-VOID (`:368-371`). Spike entry does not require the domino to agree, so a book can enter while `S_opp ≥ s*` and `z·d ≤ −1` already hold, and THESIS-VOID would then fire on the next 100-ms tick with zero hold. That is possible from reading the code; I did not observe it in data. The defined end of a spike (the leg gives back half its move, D-060) is not used as the exit. For a control book, "same exits" is intended (D-065). For `straddle_spike`, which can become champion, the exit set means the experiment tests "spike entry + domino exits" rather than the owner's idea.

**F5. The BOOK exit is silently absent for contracts outside the hero band. LOW.**
`exit_book` reads `ctx["book_state"][o["id"]]` (`paper.py:373`), and `book_state` is built only for `heroes()`, which are w0 ATM±2 (`engine_main.py:297`, `384-394`). The 0DTE next-week entries (`choose_contract` week=1) and positions that drift more than 2 strikes from ATM never get a BOOK exit, so `m2.0_s0.5_bookexit` quietly runs as the plain variant on those trades. Verified by reading.

**F6. The 0DTE delta ≥ 0.9 exemption trusts a Greek computed from a stale quote. LOW.**
`paper.py:383` checks `o["delta"]` without checking `o["age"]`. If the held quote is stale, the delta comes from an old IV, and a 15:00 exit can be skipped until 15:25. Unverified in data; found by reading.

## Good things
- **Committed exits** (`paper.py:391-393`, `400-403`): once triggered, an exit stays pending until there is a fresh option quote (at most 10 s) and does not get un-triggered by a bounce. Tests cover it at `tests/test_core.py:300-312`.
- **TIME exits never wait** (`:388`, `:407-408`), and a stale TIME exit is still tagged `stale_exit`. This is correct priority.
- **The trail does not move on a frozen or implausible print** (`:358-359`), and the test proves no STOP fires on a bad print (`tests/test_core.py:583-585`).
- **Positions are matched by contract key, not row id** (`:343-348`), so the system survives a feed restart that renumbers rows. It is persisted atomically (`save_books`, `os.replace`).
- **0DTE logic uses the position's own expiry** (`:379`), so next-week contracts bought on expiry afternoon are not flattened at 15:00.
- **`ret_pct` is recorded** (D-064) and is the scoring unit. That makes F2's unequal-R problem measurable.

## Ideas from GitHub
1. **QuantConnect/Lean** (https://github.com/QuantConnect/Lean, Apache-2.0). File: `Algorithm.Framework/Risk/TrailingStopRiskManagementModel.cs`. It tracks the peak *holdings value* per position and liquidates when the drawdown from that peak exceeds a percentage. The neighbouring `MaximumDrawdownPercentPerSecurity` does the same from entry. **Maps to:** a `premium_trail` exit shadow in `paper.py`, run on every champion trade. It would compute a "would-have exited" at −X% from entry and −Y% from peak premium (`peak_pts` is already tracked, `:356`). This is an observer judged by the learning loop. The licence is permissive, so the logic can be ported.
2. **polakowo/vectorbt** (https://github.com/polakowo/vectorbt, Apache-2.0 + Commons Clause). File: `vectorbt/signals/generators.py`, `OHLCSTX`. It generates exits from entries for a grid of `sl_stop`, `sl_trail` and `tp_stop` at once, and labels each exit `StopLoss`/`TrailStop`/`TakeProfit`. **Maps to:** an evening tool in `learning.py` that replays the day's tick log with every book's entries held fixed and sweeps the exit parameters (d*, premium %, time stop), with output labelled by stop type. Commons Clause is acceptable for personal use, but I would reimplement the concept rather than add the dependency.
3. **nautechsystems/nautilus_trader** (https://github.com/nautechsystems/nautilus_trader, LGPL-3.0, cloned). File: `crates/execution/src/trailing.rs`. A trailing stop has an *offset type* (PRICE, BASIS_POINTS, TICKS, PRICE_TIER) and a separate *trigger reference* (LastPrice, BidAsk, MarkPrice, IndexPrice). **Concept only (LGPL):** split Apex's single "futures points" stop into two pre-registered dimensions, the reference (futures, or option premium/mid) and the unit (points, %, or delta-scaled `d*·|Δ_in|`). Each pair becomes a variant or exit shadow.

## Top 3
1. **F1: let exits run during the guard's resume phase.** Block exits only on a bad print or a stale futures quote. Add a test that copies probe2 (a stall, then a fresh fall through the stop) and asserts the exit happens within one tick of the cross. Size **S**, **before Monday.** This is a correctness bug, not a rule change, and it inflates losses beyond 1R today.
2. **Pre-registered exit shadows (F2 + F4).** For every champion and `straddle_spike` trade, log would-have exits for: premium −X% / trail −Y% from peak (Lean), a delta-scaled futures stop, a time stop (no +0.5R within N min), and the spike-end rule for `straddle_spike`. These are scored in `ret_pct` by the learning loop and nothing changes intraday. Size **M**, **later**, but register the shadows before Monday so the first week's data counts.
3. **F3: record exit Greeks and a sticky-IV attribution** (`iv_out`, `delta_out`, and the Δ/vega/θ split of `pnl_pts`) in `close_trade` and the CSV. Size **S**, **before Monday.** Without it, nobody can tell whether the losses on "break-even" trails are vega.

---

# Member 19 — Data storage, persistence & lifecycle

## Lens
What lands under `data/` (ticks, paper books, learning state, `days.jsonl`, candidates, episodes, straddle), and whether it holds up through crashes, mid-day restarts, months of growth and schema changes. Method: read `paper.py`, `learning.py`, `engine_main.py`, `ledger.py`, `extras.py`, `feed_core.py`, `feed_replay.py`, `feed_breeze.py`, `run_apex.py`, `table.py`, `diagnostics.py`. Wrote three probe scripts in `/tmp/council/19/` against a scratch `APEX_DATA`. The test suite passes at baseline.

## Teardown

**F1 — CRITICAL. A live session stopped before 15:30 is never recorded for learning.** `engine_main.py:717` runs `end_day()` on shutdown only when `mode != "live"` or the time is ≥ 15:30. `end_day()` is the only caller of `learning.record_day` (`engine_main.py:165`; grep finds no other caller outside the tests). On the next morning a fresh process starts with `self.day = None`, so `step()` (`:187`) goes straight to `start_day(today)` and the previous day is never closed. `run_apex.py learn` (`cmd_learn`, `:298`) runs `learn()` without calling `record_day`, and `learn()` reads only `days.jsonl` (`learning.py:180`).
*Scenario:* the owner presses Ctrl+C at 15:27, after the 15:25 flatten, which is the natural moment to stop. Or the PC sleeps or crashes at 15:29. That day's trades exist in `paper/<day>.json` but never reach `days.jsonl`. SPRT, challenger t-tests and advisor screens all run on a sample with days silently missing, and the missing days are not random: they are the days the owner or the machine stopped early. *Verified:* by reading the code path end to end.

**F2 — HIGH. `days.jsonl` is rewritten in place without an atomic swap, and its reader cannot survive one bad line.** `record_day` reads every row, then calls `open(DAYS, "w")` and rewrites the entire history (`learning.py:175-177`). It does not write to a temp file and swap it in, which `save_state` and `save_books` both do. A crash or power cut during that write truncates the only learning record. Neither reader (`learning.py:164`, `:187`) catches decode errors.
*Probe:* I appended one torn line. After that, `record_day` and `learn()` both raise `JSONDecodeError`. Every later evening then fails inside `end_day`: the exception is swallowed by the run loop at `:701`, and `_learned` is already set, so nothing retries. Learning stops permanently and silently. *Verified:* probe.

**F3 — HIGH. Open-position exit state is not saved between entry and exit, so a restart can revert an armed trail to the original stop.** `run_books` saves only when an entry or exit happened (`engine_main.py:585`). `check_exit` updates `pos["best"]`, `pos["trail"]`, `pos["peak_pts"]`, `pos["pending"]` (a committed exit) and `pos["last"]` on every step without saving (`paper.py:355-366, 400`). The supervisor restarts a dead engine with the message "books are on disk" (`run_apex.py:89`), but the books on disk are as they were at entry.
*Probe:* entry at futures 25000 with d*=12; futures run to 25040, so the trail arms and the stop sits at 25028. The engine "crashes" and reloads, and comes back with `trail=False`, `best=25000`. At 25025 the live book exits on TRAIL and the restarted book holds, with its stop back at 24988→25013 after re-arming. The record now depends on crash timing; a committed `pending` exit is also forgotten. *Verified:* probe.

**F4 — HIGH. A crashed feed leaves a tick file that replay cannot read past the crash.** The `Recorder` appends a gzip member per process (`feed_core.py:224`, mode `"at"`). In `feed_breeze.main()` (`:574-578`) the exception path re-raises without calling `rec.stop()`, and the writer is a daemon thread, so a crash leaves a member with no trailer and loses whatever was still queued. The supervisor then restarts the feed, which appends a new member to the same file.
*Probe:* 5,000 lines with a hard exit, then 3,000 lines appended. Reading back gives `zlib.error: invalid block type` after 4,987 lines. Every tick after the restart is unreadable. `feed_replay.py:61` catches `(EOFError, OSError)`, but `zlib.error` subclasses neither, so the replay process itself dies instead of logging "recording ends early". *Verified:* probe.

**F5 — MEDIUM. Corrupt state silently resets to defaults, and the next save overwrites the evidence.**
- `learning.load_state` (`:132-139`) catches every exception and returns the registered defaults: champion back to default, `retired`, `candidates`, streaks and `log` emptied. The next `save_state` writes those defaults over the file.
- `paper.load_books` (`:449`) returns `None` on any parse error, so every book restarts at ₹1,00,000 flat, and the first `save_books` replaces the corrupt file.
- None of `save_books`, `save_state` or `Registry.save` calls `fsync`. On Windows/NTFS a power loss after `os.replace` can leave a zero-length file, which then triggers exactly this silent reset.

*Verified:* by reading. The fsync and power-loss behaviour is not reproduced (unverified).

**F6 — MEDIUM. A restart throws away what the observers were following.** `Ledger.open`/`seen` (`ledger.py:45`), the open episodes in `EpisodeLog` and the straddle state live only in memory. A restart drops every candidate still inside its 15-minute follow, and those records are never written, not even as `truncated`. The candidate base rates (D-070) therefore under-count exactly the stretches around crashes. The `momentum` control's `armed` flags (`paper.py:268`) also reset on restart, which can re-fire.

*Verified:* by reading.

**F7 — LOW–MEDIUM. Nothing limits disk growth, and no file has a schema version.** OQ-18 decided 90-day tick retention, and G5 asks for a disk check at preflight and at 12:00. Neither exists in code: grep finds no prune, `disk_usage` or retention logic. `Recorder.dropped` is counted but never published. At the estimated 1–2.5 GB/day, a year of ticks is 250–600 GB. The logs (`engine.log`, `feed.log`) are append-only with no rotation, and a recurring exception logs a full traceback every 0.5 s (`engine_main.py:702`). No file carries a schema version: old rows are read through `t.get("ret_pct")` fallbacks (`learning.py:57`), which cannot tell a pre-D-064 row from a buggy one.

*Verified:* by reading and grep.

## Good things
- **Temp file then `os.replace`** is used for books (`paper.py:433-438`), learning state (`learning.py:146-150`), the registry, and the chain snapshot, which uses `replace_retry` for Windows sharing violations (`feed_core.py:41-49`).
- **Separate data roots for sim and replay**: `APEX_DATA` is set per mode (`run_apex.py:40-46`), so a simulator can never pollute the live paper record. - **Episode, spike and control ids are derived from time**: `int(now_s*10)`, `int(now_s)`, `-(1e7+sod)` (`domino.py:166`, `straddle_watch.py:254`, `paper.py:256`). Because of this, `fired_episodes` survives a restart without id reuse, and random-control schedules come from a fixed seed (`random_schedule`).
- **Positions are matched by contract key, not row id** (`paper.py:343`): a feed restart that renumbers rows cannot price an exit off another contract (covered by a test).
- **`record_day` is idempotent per day** and records empty days as 0 % days (`learning.py:158-165`). The candidate reader skips bad lines (`diagnostics.py:42-45`), and the StateBlob seqlock skips oversize states instead of tearing them (`table.py:163-182`).

## Ideas from GitHub
1. **untitaker/python-atomicwrites**, https://github.com/untitaker/python-atomicwrites, MIT (archived 2022). Its README sets out the protocol: temp file in the same directory, `fsync` on the file, rename, then `fsync` on the parent directory (`_commit` on Windows). *Map:* no dependency needed. Add a ~15-line `apex/fsio.py` with `atomic_write_json(path, obj)` (write tmp, flush, `os.fsync`, `replace_retry`) and an `atomic_write_lines(path, rows)`. Route `save_books`, `save_state`, `Registry.save`, `write_chain` and above all `record_day` through it.2. **freqtrade/freqtrade**, https://github.com/freqtrade/freqtrade, **GPL-3.0, so the concept only and no code copied**. In `freqtrade/persistence/migrations.py`, `check_migrate()` detects the shape of a stored record (whether a `record_version` column exists), migrates on startup with defaults for missing fields, renames legacy values (`sell_signal`→`exit_signal`), and refuses records too old to migrate. *Map:* add `"schema": N` to every row in `days.jsonl`, the candidates, the episodes and the books, plus a `migrate(row)` table in `learning.py` that upgrades old rows when they are loaded and refuses unknown versions loudly. That replaces the scattered `t.get(...)` fallbacks and makes "pre-D-064 row" explicit.
3. **wbolster/jsonlines**, https://github.com/wbolster/jsonlines, BSD-3-Clause. A JSON Lines reader and writer with an explicit invalid-line policy (`skip_invalid` / raise). *Map:* one shared reader for every `*.jsonl` under `data/`, with a policy decided per file: learning inputs skip and count bad lines, and the report prints "N corrupt rows skipped". This removes F2's permanent stall and makes the tolerance in `diagnostics.py` uniform.

## Top 3
1. **Make sure no day goes unrecorded (F1 + F2)** — S, **before Monday.**
   - In `start_day`, and in `cmd_learn`, scan `paper/*.json` for days after the last day in `days.jsonl` and `record_day` them. Flag a stale open `pos` as `unclosed`.
   - Make `record_day` write tmp, fsync and replace.
   - Make `_load_days` and `record_day` skip and count torn lines.
   - Add a test: engine stopped at 15:27, next-day start, and the previous day appears in `days.jsonl`.
2. **Persist exit state and make tick files survive a feed crash (F3 + F4)** — S/M, **before Monday.**
   - Save books once a second while any book has `pos` (or whenever `trail`, `best` or `pending` changes).
   - In `feed_breeze.main()`, wrap `run()` in `try/finally: rec.stop()`.
   - Give each feed process its own segment file (`DAY.partN.jsonl.gz`), have replay chain the segments, and catch `zlib.error` in replay.
   - Add tests for restart-with-armed-trail and truncated-segment replay.
3. **Lifecycle hygiene (F5 + F7)** — M, **later.**
   - On a parse failure, rename the bad state or books file to `.corrupt-<ts>` and show a red dashboard banner instead of silently resetting.
   - Add a `schema` field and migrate-on-load (idea 2).
   - Prune ticks after 90 days, and check free disk at preflight and at 12:00.
   - Publish `Recorder.dropped`, and use a `RotatingFileHandler`-style cap on the logs.

---

# Member 20 — THE SKEPTIC

## Lens
Can ApexOptions produce *trustworthy* evidence of an edge in Nifty option buying, and where is it most likely fooling itself? I read 01_MASTER_DESIGN, 02_DECISION_LOG, learning.py, paper.py, engine_main.py, domino.py, ledger.py, diagnostics.py, feed_core.py and config.py, ran the suite (all pass), and wrote three probes (in my scratchpad; the repo was not touched).

Verdict: the *architecture* of the evidence (pre-registered variants, controls, gated books, candidate ledger, KILL rule) is better than almost any retail system I have seen. The *statistics actually wired* are weaker than the design doc promises, and the measurement has one bias that points in the same direction as the hypothesis being tested.

## Teardown

**F1 — Serial champions plus an under-assumed sigma make "GO — edge looks real" likely under a true null. Severity: critical (for evidence).**
`learning.py:252-260, 286-313`; `config.py:120-124`. The SPRT is re-armed from zero every time a champion is replaced: either a KILL hands over to the "best surviving record" (`max(alive)`, which picks on noise), or a challenger wins. Each new champion gets a fresh α=0.05 shot at GO. The boundaries also assume a trade-return sd of 10%. With delta 0.6–0.85 and a 12-point futures stop, 0DTE and 1-DTE trades on ₹30–60 premiums move 20–40% per trade, so a pooled sd of 15–25% is realistic. The report only flags a mismatch after 30 trades, and only as advice. It also prints GO before then.
*Verified by Monte Carlo* (`p2_sprt.py`, using the repo's `sprt_lines`, true mean 0, 4 trades/day, 60 sessions):

| true sd | P(GO) one champion | P(GO) serial champions after KILL |
|---|---|---|
| 10 % | 0.04 | 0.14 |
| 15 % | 0.16 | 0.64 |
| 20 % | 0.24 | 0.89 |

Failure scenario: by early December the dashboard shows "edge looks real" (`app.js:562`) on a strategy with zero expectancy.

**F2 — GO ignores the design's own bar. Severity: high.**
`learning.py:255` declares GO on `tot >= go` alone. 01_MASTER_DESIGN §9.2 Phase 3 and §6.1 say GO also needs every leave-one-day-out mean > 0, a positive total with the best day dropped, no day > 40% of the total, ≥ 50% green days, ≥ 15 sessions, ≥ 2 expiry days, ≥ 1 trend day, and a win over the ignition-style null. None of these feed the status. The control comparison (lines 316-327) is reported only. *Verified by arithmetic:* `sprt_lines(8)` gives GO = 120.9, so 8 trades of +16% on **one** trend day print GO. GO is also not latched, so it can flicker on and off, and it is not treated as a terminal decision.

**F3 — The quote-freshness gate measures message age, not trade age. The bias points toward the hypothesis. Severity: high (unverified in magnitude).**
`engine_main.py:380` sets option `age` from `recv_ns`. `feed_core.py:193-194` refreshes `recv_ns` on every **depth** packet and every quote packet, even when no trade printed. *Verified by probe* (`p1_stale.py`): a depth packet 8 s after the last trade sets age to 0 and leaves LTP unchanged. `choose_contract` (`paper.py:125`) accepts age < 15 s, so the paper entry may be the **pre-impulse** last trade, while the trigger itself is a futures impulse. D-016 says this lag cannot be captured; the paper book captures it anyway.

The bias is asymmetric:
- Impulse-timed books (champion, variants, `futures_only`) get it.
- `random_entry` largely does not, so "champion beats random" is partly an artefact.
- STOP exits also tend to print the last trade before the adverse move.

This is not a request to change the LTP fill rule (that is the owner's call). The point is that the measurement cannot tell a fresh LTP from a stale one. `ltt` is already in the row (`table.py:25`), so trade age (now − ltt) and mid at fill could be logged at almost no cost. Magnitude depends on strike liquidity. It is probably small at the ATM and larger on next-week strikes after 13:00 on expiry day. Monday's data can measure it.

**F4 — "BASKET-LED" has a ~10% chance floor, and F1's kill bar is 15%. Severity: medium.**
`domino.py:183-196` labels an episode BASKET-LED when the first of 14 stocks crosses z ≥ 2 at least 2 s before futures. The minimum of 14 noisy crossing times beats a single series by order statistics alone. *Verified by probe* (`p3_domino.py`, which drives the real `Domino` on a synthetic market where futures are the contemporaneous weighted sum, i.e. no lead-lag at all): 8 of 77 episodes (10%) were labelled BASKET-LED. The pre-registered F1 kill rule ("basket-led < 15% → re-scope") is barely above noise. Real snapshot cadence (cash at 1–4/s) adds jitter on top. The `episode` advisor and the "lag" story inherit this.

**F5 — Synchrony may be nearly tautological with the impulse. Severity: medium (analysis, not verified on live data).**
The 14 tracked names are 61.6% of Nifty (`universe.py:57`). A 15-s futures move at z ≥ 2 mechanically needs most of that weight moving the same way, so P(S ≥ 0.5 | z ≥ 2) may be close to 1. The champion and `futures_only` would then take almost the same trades, and the "domino" hypothesis could never be told apart from plain momentum. That is exactly what lost −138.5 pts before (§6.1). This is cheap to check: the candidate ledger already stores S at every z ≥ m* crossing.

**F6 — Candidate hit rates have no stated null. Severity: low.**
`diagnostics.py:65-74` counts NEITHER as a miss. A symmetric ±1R race under a martingale gives TARGET ≈ STOP, so hit rates sit below 50% by construction, and the report gives no random-time baseline row to read them against. The table is also sliced 4 ways × many groups, which is a forking-paths risk for a human reader even though the automatic promotion is protected.

**F7 — RAW's parameters follow the champion. Severity: low.**
`engine_main.py:141` gives RAW the current champion's parameters, so after a champion change the advisor screen "since registration" (`learning.py:330`) mixes two parameter sets.

## Good things
- **One four-number trigger, with everything else an advisor** (D-033, `paper.py:135-189`). This is the single best defence against MYTHOS's failure mode, and the code really does it.
- **Gated-book promotion** (D-067, `learning.py:351-385`). Advisors are judged on the path they actually produce, forward from the day they became a candidate. That is honest out-of-sample evidence.
- **Pre-registered controls** (`config.py:107-113`), including `futures_only` as the direct test of the basket claim.
- **Bonferroni plus 2-evening persistence plus LODO for challengers** (`learning.py:270-283`). Exact t via the incomplete beta, no scipy.
- **Candidate ledger** (`ledger.py`). It labels every opportunity whether taken or not, which removes the survivorship that blinds most learning loops.
- **Blackout, settling and taint logic** (D-063/075/077) stops reconnect jumps from manufacturing impulses. The sim gap drill (D-079) proves it.
- **Log-growth day unit** (`learning.py:61-66`) is the right unit under all-in sizing.

## Ideas from GitHub (all opened)
1. **gostevehoward/confseq** — https://github.com/gostevehoward/confseq — MIT. Borrow `src/confseq/betting.py` (betting confidence sequences for bounded means) or the normal-mixture boundary. Map: a new **observer** in `learning.py` that shows an *always-valid* confidence sequence on champion trade returns (clipped to e.g. [−100, +300]%). It stays valid under daily looks, unknown sigma and champion swaps if the stream is pooled. It needs no assumed sd, so it fixes F1's root cause. Run it beside the SPRT, report-only, and later make it the GO criterion through a logged decision.
2. **esvhd/pypbo** — https://github.com/esvhd/pypbo — **AGPL-3.0, concept only.** The Probability of Backtest Overfitting (CSCV) and Deflated Sharpe ideas. Map: a nightly **observer** that treats the 13 non-control books' daily log-returns as the trial matrix and reports PBO, i.e. how often the in-sample best book ranks below median out of sample. If PBO > 0.5, champion swaps are chasing noise. Write it from the paper; do not copy code.
3. **philipperemy/lead-lag** — https://github.com/philipperemy/lead-lag — MIT. `lag(ts1, ts2, max_lag)` (Hayashi–Yoshida on asynchronous ticks). Map: an **evening tool** over `data/ticks/DAY.jsonl` that estimates the true basket→futures lag per heavyweight, with a shuffled-time null. That replaces F4's crossing-order label as evidence for or against the domino premise.
4. **skfolio/skfolio** — https://github.com/skfolio/skfolio — BSD-3. `skfolio.model_selection.CombinatorialPurgedCV`. Map: the validation harness for the **later ML advisor** described below.

**Where ML can help later, properly validated:** once there are ≥ 300 resolved candidates (D-071), train a *meta-label* model: given that v1 fired, predict TARGET vs STOP, or option +5-min return, from the ledger features. Use regularised logistic regression or a shallow gradient-boosted model, with purged and embargoed CV grouped by session, and calibrated probabilities. It must beat the Wilson tables out of sample. It then enters as **one** pre-registered advisor (`ml_meta`) and earns its gate only through its gated book, so no thresholds are re-fit intraday. Freeze each model version per session and hash it in the decision row (I-10). ML should replace the 13 hand-made vetoes with one composite, never add a 14th vote.

## Top 3
1. **Make GO honest: wire the §9.2 day-level conditions and "beats `futures_only`/`random_entry`" into the GO status. Latch the first crossing. Show the family-wise count ("champion #k, cumulative looks n") next to GO. Add the confseq observer.** — Size S/M — **before Monday** for the label and conditions (S), later for confseq (M).
2. **Log trade age (now − `ltt`) and mid with every entry, exit and candidate. Add a report row "ret% at mid" and "ret% excluding fills with trade age > 2 s".** This keeps the owner's LTP rule and makes F3's bias measurable. — S — **before Monday**, so day 1 is already instrumented.
3. **Evening "is the domino real?" tool:** the share of champion trades also taken by `futures_only`, the P(S ≥ s* | z ≥ m*) curve from the ledger, a shuffled-time null for the BASKET-LED rate, and Hayashi–Yoshida lags. If the overlap is above 90%, say plainly that synchrony is not being tested. — M — **later** (after 5 sessions).
