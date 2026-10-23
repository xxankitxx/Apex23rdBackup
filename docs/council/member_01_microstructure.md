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
