# Four external reviews (DeepSeek, ChatGPT, Gemini, Grok) — what was adopted, tested, or set aside

Owner's instruction (21 Oct 19:53): look with an open mind, adopt what makes the system better at anticipating edges and
giving trades; Nifty options buying only; no risk management at all (ignore those ideas).

| Review idea | Source | Decision | Evidence / where |
|---|---|---|---|
| Log every data feature at every decision; feature-utility report (coverage, incremental value) | ChatGPT, Gemini, Grok | **Adopted** | D-136: `apex/engine/edge.py`, `edge_in` on every trade, evening table |
| Premium-outcome lab (MFE/MAE, forward premium per candidate) | ChatGPT | Partly existing | the candidate ledger follows every candidate 15 min; the edge table adds per-trade features |
| Dual mode: scalper on 0 DTE, trend-hold on other days | Gemini, Grok | **Shadow** `spot_dual` | D-137; the pullback champion already holds trends on both tapes |
| Bias object / structure exit / sell-the-rally | Gemini, Grok | Tested in council 7 (C01) | one trade carries 21 Oct; gives up 19 Oct — not adopted; the pullback book is the robust form |
| Trigger on futures minus basis (see moves seconds earlier) | Grok, council 8 | **Tested, rejected** | 19 Oct +75k vs +124k, 21 Oct +51k vs +59k (sim); the future's quote is noisier |
| Tier-1 fast order-flow pre-arm | DeepSeek | Rejected | council 8 D03: OFI leads ≈ 1 pt / 10 s, less than one spread; waiting for agreement costs ₹12–20k |
| Composite score with GEX / straddle-spike | DeepSeek | Rejected | council 8 D06: the GEX advisor vetoes 8 of 9 champion trades |
| Relative-value / dispersion signal | DeepSeek, ChatGPT | Tested (council 6 M07, council 8 D04) | no lead; logged |
| IV quote cleaning (mid, staleness) | DeepSeek | Already done | D-102: IV on mid-price, stale legs dropped |
| Protocol-shape canary, parser fuzz tests | DeepSeek | **Adopted** | D-138 |
| Fewer variants, 30-day evaluation, locked out-of-sample period | DeepSeek, ChatGPT | Owner's call | governance; the learning loop already needs 10+ days, LODO, two-evening persistence |
| Cost model, net P&L | all | Not adopted | owner's rule: LTP, gross (bid/ask recorded on every trade for later netting) |
| Risk sizing, loss limits, half-size, circuit breakers | all | **Ignored** | owner: no risk management |
| Split engine_main / dashboard JS, three feed processes, CAS index-freeze guard | Gemini | Index guard done (D-132); splits later | engineering |

## Gemini's second reply (21 Oct 19:59)
It says it could not read the repository's files and reviews components that do not exist in ApexOptions (TickProcessor,
SignalLoop, Strength Accumulator / RSI-VWAP-MACD voting, MomentumGear, AutoTuner, BgWriter, a threaded terminal UI) — so
its "bads" (GIL contention, AutoTuner overfitting, list(deque) churn, no tick journal) do not apply: ApexOptions is already
multi-process over shared memory (seqlock), never tunes live, records every packet and replays it lock-step, and solves IV
on mid-price with stale legs dropped. Adopted from it, as logged edge features (D-136, evidence only):
* `fut_ofi60` — Cont–Kukanov–Stoikov order-flow imbalance of the future's top of book over 60 s (net queue change, harder to
  spoof than static depth). Computed from 1-Hz snapshots, coarser than tick level; council 8 D03 measured the tick-level lead
  at ≈ 1 pt over 10 s.
* `syn_dev` — put-call-parity forward minus spot, minus its ~50-s average (its "synthetic basis dislocation").
* `fut_micro` — micro-price minus mid of the future.
Its sub-second (300–1,500 ms) lead claim cannot be tested on our 1-Hz evidence and, for an option BUYER, the option itself is
already repriced when the synthetic moves (council 8 D01/D05).
