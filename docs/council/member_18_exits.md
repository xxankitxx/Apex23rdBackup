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
