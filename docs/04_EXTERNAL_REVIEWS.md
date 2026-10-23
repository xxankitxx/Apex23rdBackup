# External teardowns of ApexOptions: what holds up, and what Claude missed

> **Status, 17 Oct night: F1–F6 and the no-order guard test are implemented** (D-063 … D-068 in the decision log), with tests for each. The F4 docstring is updated too.

*17 Oct 2026, night. Four reviews: ChatGPT, DeepSeek, Gemini, Grok. Each claim was checked against the code before it went in here, so line references are to the current tree.*

**Scope.** These are left out by design, because the owner has already decided them:
- **Already decided:** sizing (all-in, ₹1,00,000 fresh each day), fills at LTP, slippage, brokerage and charges.
- **Not in v1:** real-money readiness and everything that only matters for it: daily loss limits, static IP, exchange-held stops.

Most of what ChatGPT wrote is in this out-of-scope group. It is reasonable in general, but it does not apply to this system.

---

## 1. Verdict on the four reviews

| Reviewer | Did it read the code? | Useful to us |
|---|---|---|
| **ChatGPT** | Yes. It cites `learning.py`, `paper.py`, `RestLedger`, the test file. | **Most useful.** Its statistical points led to four of the six findings below. About half the review is out of scope (sizing, fills, costs). |
| **Grok** | Yes, plus the docs and decision log. It also found your other public repos and the MYTHOS track record. | Accurate summary, little new. Its main point: treat the learning loop's promotion rules as sacred. |
| **DeepSeek** | Only the GitHub page and README. | Nearly nothing. Licence, single commit, no stars: these matter for an open-source project, and this is a personal system. One side effect is worth knowing (see 4.3). |
| **Gemini** | **No.** | It describes a different program, one with Python threads running the signal loop, a terminal UI redrawing inside the engine, live hyper-parameter "auto-tuning", `list(deque)` copies and `except RuntimeError` in the hot path. None of these exist in Apex (checked: no matches). It reads like a review of MYTHOS/HAWK. **Ignore it.** |

---

## 2. What Claude missed: real findings, ranked by how much they matter

### F1. A feed reconnect can fake a Triangle *(bug; affects Monday)*
**Source:** ChatGPT, "prohibit new entries during feed recovery".

**What I verified:** `evaluate_entry` (`paper.py:125`) never looks at `feed_state`, and nothing in the engine checks quote age before an entry.

**The failure:**
1. The websocket drops for 40 s. Every price in the ring buffer freezes.
2. When it reconnects, the futures and all heavyweights jump to their current prices in the same tick.
3. The 15-s impulse (`Market.change`) sees the whole 40-s move as a 15-s move, so z is large.
4. Every stock "moved together", so synchrony is high.
5. The episode starts at the jump, so the Fresh corner says the move is fresh.

All three corners close on an artefact. The same jump is also fed into the 20-min σ scale (`domino.py`, `fut_sigma.add`), which dampens real signals for the next several minutes.

**Exits have the same blind spot.** `check_exit` prices the option at its last LTP, even if that quote is stale, and it falls back to `pos["last"]` or the entry price (`paper.py:230`, `:262`). After a reconnect, a futures-triggered STOP can book the option at a pre-gap price.

**Fix:** a data blackout. Block entries while `feed_state` ≠ LIVE, and keep blocking until 20 s of continuous fresh futures ticks have come in after recovery. Do not update σ during the blackout. Any exit taken in or just after a blackout is priced at the first fresh option quote and tagged `GAP`, so it can be excluded from the learning data. A recorded-tick test with a forced 40-s gap proves it.

**Why it matters now:** the live websocket is still the open problem. Monday is when reconnects are most likely.

### F2. The learning loop counts premium points, but under all-in sizing the account earns a percentage
**Source:** ChatGPT §5.3. Its reason (different lot counts) was close; the real reason is specific to our sizing rule.

**What I verified:** every statistical test in `learning.py` (SPRT on lines 129 and 169, the challenger t-test on line 144, advisor ablation on lines 193–205) uses `pnl_pts`, the premium points per unit.

**Why it's wrong:** the account buys as many lots as ₹1,00,000 allows, so the rupee result of a trade is (points ÷ entry premium) × capital. **The return on premium is the true unit, not points.** With entry premium written as P:
- A +4 point gain at P = ₹200 is a 2% day.
- A +4 point gain at P = ₹40 is a 10% day.

The learner currently scores those two as equal.

**Expiry days make it worse.** On 0DTE the chosen premiums are ₹20–60, so expiry-day trades produce small point values, while their percentage results are the largest of the week. Their weight in the statistics is close to nothing. Monday is an expiry day.

The SPRT constants (H1 = +1.5 pts, σ = 6 pts) were also set in points.

**Fix:** score in percent return per trade, `pnl_pts / entry × 100`, and a day's result as the compounded product, which is what the paper account itself does. Re-derive the SPRT constants in percent. Keep points in the report for readability.

### F3. Nothing tests the core idea against a null
**Source:** ChatGPT, "does the basket actually lead Nifty, or merely move with it?" and "compare against simple baselines".

**What I verified:** every registered variant has synchrony `s* ≥ 0.4`. No book trades on the futures impulse alone. RAW is the champion without advisor gates, so it is not a null either.

**Why it matters:** the domino thesis (heavyweights lead Nifty, so basket agreement adds an edge) is never tested on its own. If the futures-only book does as well, the basket is decoration. If the champion beats it, that is the first real evidence for the thesis.

**A second control is missing.** The four exits (12-pt stop, trail, flatten) can make or lose money regardless of how good the entry is. A random-entry book with the same exits separates entry skill from exit mechanics.

**Fix:** pre-register two control books.
- **`futures_only`:** `s* = 0`, everything else as the champion.
- **`random_entry`:** fires at uniformly random times inside the entry window, at about the champion's trade rate. The direction comes from the sign of the futures' last-minute move. It uses the same contract selection and the same exits.

Neither book can become champion; they exist to be compared against.

### F4. The champion test is no longer as strict as it says
**Source:** ChatGPT §5.2.

**What I verified:** the docstring says "t ≥ 2.5 (strict, because **eight** challengers are compared)". There are now 12 challengers: 9 grid variants, 2 gap variants, book-exit and straddle_spike, plus RAW. The test is also re-run every evening (repeated looks).

**The arithmetic:** with 10 days, t ≥ 2.5 is about p ≈ 0.017 one-sided. Across 12 independent challengers, the chance that at least one passes by luck at a single look is about 1 − 0.983¹² ≈ **19%**. The books are correlated because they share most entries, which lowers this. Daily re-testing raises it.

**Fix:**
- Scale the threshold with the number of challengers (Bonferroni: one-sided α = 0.05 / 12, about t ≥ 3.4 at 10 days).
- **Or** require the challenger to pass on 3 consecutive evenings before it takes over.
- Update the stale docstring. It still says "nine variants … a tenth book RAW", and its advisor list stops at episode-type.

### F5. Advisor promotion is judged on a fixed trade list, but the account is path-dependent
**Source:** ChatGPT §5.4.

**What I verified:** advisor ablation (`learning.py:193–205`) deletes vetoed trades from RAW's list and recomputes the mean.

**Why that isn't faithful:** we hold one position at a time, never re-enter an episode, and compound intraday. A vetoed trade is not simply a missing row. It frees the next 10–20 minutes for a different entry that RAW never took, and every later trade's rupee size changes.

**Fix:** once an advisor reaches candidate status (≥ 30 trades, ≥ 8 vetoes), spawn a shadow book "champion + this advisor as a hard gate". It trades the real alternative path, and promotion is decided on that book versus the champion, using the F4 rule. The infrastructure for parallel books already exists. Keep the current ablation as the cheap screen that picks candidates.

### F6. The straddle-spike book has no baseline without theta
**Source:** ChatGPT §3.4.

**The gap:** the spike detector measures the premium rise in excess of theta. Nothing tests whether the theta adjustment adds anything over plain premium momentum ("buy the leg that rose most in 5 min").

**Fix:** a pre-registered `premium_momentum` control book, with the same entry age, the same delta-rise filter and the same exits, and with no theta path and no excess threshold. If `straddle_spike` cannot beat it, the theta model is not the part that matters.

---

## 3. Points raised that are already covered (no action)

| Claim | Where it's already handled |
|---|---|
| "Signals must be evaluated including untraded ones, at fixed horizons" | `EpisodeLog` records a ±3-strike grid at +0/15/30/60/120/300 s for **every** episode, traded or not. Straddle spikes go to `straddle_DAY.jsonl` with +1/+5/+10 min outcomes. |
| "Is the basket early enough after latency?" | `LagMeter` measures the basket-to-futures lead each day and shows it on the dashboard. F3 is the stronger test. |
| "z = 2 is not a true 2σ event (fat tails)" | Correct but harmless. σ is an EWMA of \|r15\| (mean absolute, not standard deviation), and the thresholds are chosen empirically by the variant grid, not from a normal table. |
| "Zero-trade days must be recorded" | `record_day` writes every book every day, with empty trade lists included. The challenger test counts them as 0. |
| "The dealer-gamma sign may be wrong for Nifty" | Already stated in D-062. It is advisory only and promoted only through the learning loop (and F5 makes that fairer). |
| "A test that the paper version can't send orders" | `PAPER_ONLY` is checked by preflight, and there is no order call in the tree. A one-line test could grep for `place_order` / `modify_order` and fail if found. It is cheap and worth adding with F1. |
| Engine/UI coupling, GIL, live auto-tuning (Gemini) | Not applicable. Feed, engine and gateway are separate processes. Threads exist only for the REST poller, the tick recorder and audio. Parameters change only between sessions, chosen from pre-registered sets (invariant I-11). |

---

## 4. Minor items

1. **The REST per-minute window resets on restart** (`RestLedger.minute` is in memory; only the daily count is persisted). This is a real limitation, but negligible: we make about 3 REST calls a minute against a self-imposed cap of 60 and ICICI's 100. No action.
2. **`engine_main.py` (662 lines) and `app.js` (589 lines) are large.** Both reviewers flagged this. It is not urgent. Split if either grows past about 1,000 lines.
3. **The repository is public** (`xxankitxx/Apex`). Grok also found `xxankitxx/claude-code` and `vikash3rd`, read the MYTHOS track record (−355 pts / 361 trades) in them, and quoted it. If you did not intend the design, decision log and results to be public, make these repos private. `secrets/` is gitignored, so no credentials are exposed.
4. **The live Breeze path has never run end-to-end** (Grok). True, and still the number-one risk for Monday. The websocket preflight check is unresolved and waiting on your next preflight output.

---

## 5. What Claude should have caught, honestly

- **F1 is the one I should not have missed.** I wrote the reconnect logic and the impulse logic in the same week and never connected them. A frozen ring buffer followed by a jump is the textbook way a momentum trigger fires on nothing.
- **F2** came from me treating "points" as the natural unit, carried over from MYTHOS, without re-deriving it after you chose all-in sizing.
- **F3–F6** are experimental-design gaps. The pre-registration discipline was right, but I registered only treatments and no controls. Without a null, a positive champion result cannot be told apart from "the exits are good" or "any futures impulse works".

## 6. Proposed order of work

| # | Change | Size | Before Monday? |
|---|---|---|---|
| 1 | F1: data blackout for entries and σ, gap-aware exit pricing, gap test | small | **Yes**: it protects the first live sessions from artefacts |
| 2 | F2: learning in % return per trade, SPRT re-derived | small | **Yes**: changes how Monday's trades are scored, so it's best in place before the first sample |
| 3 | F3 + F6: `futures_only`, `random_entry`, `premium_momentum` control books | small | **Yes**: controls must run from day one to be comparable |
| 4 | F4: Bonferroni-scaled threshold or 3-evening persistence; docstring | tiny | Yes |
| 5 | F5: candidate advisors get a gated shadow book | medium | No: no advisor can reach candidate status before about 30 trades |
| 6 | No-order guard test | tiny | With #1 |

None of these adds a new signal. ChatGPT made the same point: the next milestone is evidence that the existing trigger works, not another indicator. Items 1–4 make that evidence trustworthy.
