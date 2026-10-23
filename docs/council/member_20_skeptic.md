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
