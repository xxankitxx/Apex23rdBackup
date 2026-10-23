# Council 8 — 21 Oct night: can the captured data take or ignore an entry? (7 members, both tapes)

## The owner's question
"Even if some stupid rules are asking the code to take a particular position, it must be in a position to take it or
ignore it based on the data it captures." Constraints kept: buy CE/PE only (arbitrage is information, not a trade), all-in
lots, LTP, no brakes, no risk sizing.

## Method
Every idea was scored as a VETO (refuse a proposed entry) or a CHOOSER (pick a different contract) on three candidate
sets — the pullback champion's entries (9), the retest book's (34–39), the first-touch book's (81–86) — on both days,
kept vs vetoed, ±20 % neighbours, against a random veto of the same rate (200–2000 draws). Pass bar: removes losers more
than winners on both days, on at least 2 of 3 sets, neighbours holding. Only data available at the decision second.

## Results
| Member | Data | Finding | Verdict |
|---|---|---|---|
| D01 | Put–call parity, synthetic future | Parity residuals 0.3–0.6 pt = the spread: no cheap/rich side. Synthetic−future "leads" the future only because the future's own quote is 2× noisier. Parity chooser no better than "one strike OTM". | no veto / chooser |
| D02 | Implied vs realised vol, VIX | Rich-IV vetoes removed the champion's biggest winners (+61k, +19k entered at IV/RV ≈ 4). "Vol falling" vetoes 7 of 9 champion trades (a pullback is a calm moment). 182 flags: 6 pass 2/3 sets, ≈ chance. | no veto |
| D03 | 5-level depth, order-flow imbalance | OFI genuinely LEADS the future and spot — corr +0.10…+0.15 at 5–10 s, both days — but the edge is ≈ 1 pt over 10 s, under one option spread. Opposing-OFI veto kills the champion's winners. Waiting for OFI to agree costs ₹12–20k. All-in size walks the book for only 0.01–0.07 pt. | real but too small; no veto |
| D04 | Heavyweight breadth, BankNifty/FinNifty | "Narrow move = fade" fails (vetoes champion winners). 360 rules: 4 pass 2 sets ≈ chance; the best just restates "the move already ran". | no veto |
| D05 | Futures basis vs carry | No consistent lead at 1–10 min; signs flip between days. The future moves 3–6 s before spot, and the option is priced off the future: the spot trigger reads a few seconds late. | no veto; a clock idea to test |
| D06 | OI walls, max pain, GEX, writing flow | Nothing passes; the one weak rule flips at ±20 %. The engine's old GEX "DAMPEN" advisor would have vetoed 8 of 9 champion trades (≈ ₹1.49 L): it cannot reach spot books (they return before the advisor gates), and must stay that way. Heavy-OI strikes were pierced 30 % vs 71 % for light ones — an exit hint, ~12 independent cases. | no veto; hint logged |
| D07 | Red team + ensemble | 11 flags × 4 thresholds: none passes. "Veto if ≥ 2 flags disagree" cleans the first-touch book but vetoes 8 of 9 champion entries incl. every winner. | do not gate the champion |

## What this means, plainly
On these two days, the extra data does not tell the pullback champion when to skip a trade. Every short-window flag
(1–5 min) disagrees with a pullback entry by construction, because a pullback is a move against the last few minutes.
The one thing that truly leads price — order-flow imbalance — leads it by seconds and by less than the option's spread,
which a buyer of options cannot capture. Nothing was gated. Two down-drift days cannot prove a negative either: every
member recommends logging these features on every decision so the learning loop can re-test them with more days,
including an up day.

## Logged for later (not wired as decisions)
basis_dev30, iv_pct / iv_chg5 / rv15, wbr_600 / breadth_600, 5-level book imbalance of NIFTY|FUT, distance to the nearest
heavy-OI strike and its 15-min OI change. Candidate shadow books if the owner wants them: retest + future-book-imbalance
veto (D03), first-touch + growing-OI-wall veto (D06). Untested idea: trigger on the future (minus its 30-min median basis)
instead of spot, a few seconds earlier (D05).
