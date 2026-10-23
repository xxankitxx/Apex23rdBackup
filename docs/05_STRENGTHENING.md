# Strengthening ApexOptions: from weaknesses to strengths

*17–18 Oct 2026, before the first live paper session. Version 1.1.0 (see `CHANGELOG.md`).*

**The question:** how do we turn the weaknesses the reviews found into strengths?

**Out of scope, as agreed:** real money, slippage, brokerage, all-in sizing and trade frequency.

**Sources:** answers from ChatGPT, DeepSeek, Gemini and Grok, weighed against Apex's own rules:
- **D-033, the frozen four-number trigger:** the trigger stays as it is.
- **I-11, nothing changes intraday:** decisions take effect at the next session.
- **Pre-registration and evidence first:** a new idea starts as evidence and earns a vote only through the learning loop.

This document says what was taken from each answer, what was built tonight, what was deliberately left out, and what comes next.

---

## 1. The four answers, weighed

| Reviewer | What it understood | Verdict |
|---|---|---|
| **ChatGPT** ("Apex v2") | The real problem: Apex recognises *movement*, but not yet *opportunity*. It proposed a regime classifier, logging every candidate (not just trades), an outcome-based evaluation ("does this setup reach its target before its stop?"), and judging every feature by its added value. | **The backbone of tonight's work.** Two of its proposals were built in full, a third as its data foundation. Where it overlapped with what was already built (controls, ablation), the existing pieces were kept. |
| **Grok** | Engineering hygiene that fits this project: CI, replay fixtures, a decision log you can query, splitting the two large files, an advisor "plugin" contract. | **Partly built** (CI, config self-check, changelog). The file splits are deferred until after Monday (see §4). |
| **DeepSeek** | Open-source project hygiene: licence, contributor guides, Prometheus, Docker, branch protection, typed config. | **Mostly not applicable:** this is a personal research system, not a public framework. Two pieces were taken: a configuration self-check and CI. A licence is your call: the repo is public, so choose MIT or keep it private. |
| **Gemini** | Again describes a different program (thread-based, terminal UI, live auto-tuning). Its main proposal is to promote the best of 64 parameter sets *on every tick, per regime*. | **Rejected.** Intraday auto-promotion is exactly the overfitting whiplash that invariant I-11 forbids, and that the MYTHOS track record warns about. **One idea adapted:** a "zero-trust edge" bad-print check, now in the data guard (D-072). |

---

## 2. What was built, weakness → strength

### 2.1 "It sees movement, not opportunity" → a market regime label (D-069)

**Weakness:** a z = 2 impulse means one thing in a clean trend and another in a range or at the end of a stretched move. Until now the trigger couldn't tell them apart.

**Built:** `apex/engine/regime.py` labels the market every second, using only what is known at that second (no look-ahead). It uses five session-aware features:

| Feature | Measures |
|---|---|
| **Efficiency, 5 min** | Net move ÷ path length on 15-s samples (Kaufman's efficiency ratio). 1 = straight line, 0 = back-and-forth. |
| **Efficiency, 1 min** | The same on 5-s samples: is the move still making progress? |
| **Activity percentile** | Today's 5-min path length, ranked against earlier today. |
| **VWAP stretch percentile** | Distance of the futures from the session VWAP, ranked against earlier today. |
| **Breadth** | Share of heavyweight index weight moving with the futures over 5 min. |
| **Range break** | Futures beyond the high or low of the 30 minutes that ended 5 minutes ago. |

**Seven states, pre-registered tonight**, so they can't be tuned afterwards:

| State | Means | Rule (first match wins) |
|---|---|---|
| WARMING | Too early in the session | Less than 10 minutes of data |
| EXHAUSTION | Stretched and stalling: don't chase | VWAP stretch ≥ p90 and 1-min efficiency < 0.25 |
| BREAKOUT | Escaping the recent range with energy | Range break, efficiency ≥ 0.35, activity ≥ p60 |
| DIRECTIONAL | A clean move the basket confirms | Efficiency ≥ 0.35 and breadth ≥ 60% |
| COMPRESSION | Quiet and contracting | Activity ≤ p25 and efficiency < 0.35 |
| RANGE | Back-and-forth | Efficiency < 0.20 |
| UNCERTAIN | Progress without breadth, or mixed signals | Anything else |

**How it's used:**
- **Advisor `regime`:** it vetoes entries in every state except DIRECTIONAL and BREAKOUT, and vetoes those too when they point the other way. It becomes a rule only through its own gated book (D-067).
- **Every trade carries its regime,** and the report shows *results by regime* from day one.
- **The dashboard shows it** under the verdict, e.g. "Market: directional ↑ (efficiency 0.52, breadth 78%, VWAP stretch p40)".

**A calibration bug caught tonight:** the first version measured efficiency on 1-second prices. At that resolution the bid/ask bounce dominates the path, so even a random walk scored about 0.07, the market read RANGE all day, and the advisor vetoed 100% of the simulator's candidates. On 15-s samples a pure random walk scores about 0.22 on average. The thresholds are set against that baseline: ≥ 0.35 happens about 21% of the time by chance. Checked on a simulated random walk: DIRECTIONAL 18%, RANGE 37%, the rest spread across the other states.

### 2.2 "It only learns from trades it took" → the candidate ledger (D-070)

**Weakness:** if a filter rejects good opportunities, the learning loop can never see it, because rejected opportunities leave no trace.

**Built:** `apex/engine/ledger.py`. A **candidate** is the first moment in an episode when the futures impulse reaches the champion's m*. Every candidate is recorded, taken or not, with:
- **Features:** z, synchrony, basket gap, lateness, IV rise.
- **Market state:** regime and its features, episode type, time.
- **Decisions:** every advisor's verdict, and the champion's decision and reason.
- **The contract the champion would buy.**

Then it follows the next 15 minutes and labels what happened, independent of any trade:
- **TARGET / STOP / NEITHER:** did the futures reach +1R (d*, where the trail arms) before −1R?
- **Time to that outcome.**
- **The would-be contract's return on premium** at +1, +5 and +15 minutes, plus its best and worst point.

It is written to `data/paper/candidates_DAY.jsonl`.

### 2.3 "Confidence without calibration" → evidence tables in the learning report (D-071)

**Weakness:** an advisor or filter can look sensible without separating good candidates from bad ones.

**Built:** `apex/engine/diagnostics.py` adds two sections to the evening learning report.

**Candidates.** For each group: the hit rate (+1R before −1R) with a **Wilson 95% interval**, and the mean option return 5 minutes later. The groups are:
- taken vs rejected, and **each rejection reason** (basket too thin, late, gate, data gap, …);
- each regime;
- impulse size;
- **for each advisor:** the hit rate when it vetoed vs when it passed. An advisor whose vetoed candidates hit *as often* as the passed ones is adding nothing.

**Trades by regime:** the champion's and RAW's mean return and win rate per regime.

This is ChatGPT's "transparent statistical baseline". No predictive model is fitted until there are a few hundred labelled candidates. When one is, it must beat these tables on later days it has never seen.

**What the simulated day produced:** 113 candidates labelled, all seven regimes populated, every advisor scored, no errors. The simulator's synthetic market proves only that the pipeline works, not that any edge exists.

### 2.4 "A bad tick can look like a move" → bad-print guard (D-072)

Adapted from Gemini's "zero-trust edge". A futures price that jumps more than 1% within 2 seconds puts the engine into the existing data blackout (D-063): no entries, scales frozen. The blackout lifts after 20 s of clean data. Nifty does not move 250 points in two seconds outside a market-wide circuit event.

### 2.5 "Misconfiguration becomes a mystery" → configuration self-check (D-073)

`config.validate()` checks every variant's four numbers and ranges, that controls are never champion, the delta and premium bands, the order of the session clock, the statistics settings, the exit timers, and `PAPER_ONLY`. Preflight runs it as its first line, and so do the tests.

### 2.6 "No automated safety net" → CI and a changelog (D-074)

- **`.github/workflows/tests.yml`** runs the configuration self-check and all 20 offline tests on every push. It needs only numpy and never touches Breeze or `secrets/`.
- **`CHANGELOG.md`** has version 1.1.0, with each change mapped to its decision number.

The tests now cover the reconnect artefact, the bad-print guard, exits that wait for fresh quotes, the controls, the learning loop's statistics, the gated-book promotion, regime labelling, ledger labelling, the diagnostics and the no-order guard.

---

## 3. What was deliberately NOT done, and why

| Proposal | Why not |
|---|---|
| Per-regime parameter switching, intraday "best arm" promotion (Gemini) | Breaks I-11 (no intraday change) and pre-registration. It optimises for the regime that just ended. |
| A probability model ("68% chance of target") now (ChatGPT) | There is no data yet. Fitting it on zero live candidates would be fiction. The ledger collects the data first; the model must later beat the baseline tables out of sample. |
| Adding more indicators or agents | Every reviewer agreed: the next milestone is evidence that the existing trigger works. The regime label is a *description*, not a new trigger. |
| Splitting `engine_main.py` / `app.js` (Grok) | Worth doing, but not 36 hours before the first live session: a big refactor is the likeliest source of a new bug. Planned for the first weekend after a week of live data. |
| Licence, contributor guides, Prometheus, Docker, branch protection (DeepSeek) | For public frameworks with users. This is a personal research system. |
| Three feed processes behind a flag (Grok) | The single feed is not the bottleneck yet. Revisit if live tick age or drops say otherwise. |

---

## 4. What comes next, in order, each gated on evidence

1. **Monday:** first live paper session. The candidate ledger, regime labels, controls and gated-book machinery all start collecting. Record the ticks so the day can be replayed.
2. **After Monday:**
   - make a **replay fixture** from the recorded day;
   - add a test that replaying it twice gives the same decisions (not yet verified for the multi-process replay);
   - add a `replay --assert` mode that fails on broken invariants (stale hero rows, books not saved).
3. **After a week:**
   - split `engine_main.py` into trigger / advisors / exits / orchestrator;
   - split `app.js` into panels;
   - define the advisor contract (`advise(ctx) → (veto, why)`) in a short document;
   - add a "flight report" page that loads any past day's episodes, candidates and decisions on one timeline.
4. **After a few hundred labelled candidates:**
   - fit the first transparent outcome model (logistic regression on regime, z, breadth, lateness), trained on earlier days and tested on later ones;
   - it is adopted only if its predicted probabilities match observed hit rates and it beats the baseline tables;
   - it starts as an advisor, like everything else.
5. **Re-register thresholds only from evidence:** for example the SPRT σ once the observed spread is known, or the regime cut-offs if the per-regime tables show a state is never distinct.

---

## 5. One line

Tonight did not make the trigger cleverer. It made Apex able to tell a good moment from a busy one, to see every opportunity it passed up, and to show, with intervals, which of its own filters are worth keeping.
