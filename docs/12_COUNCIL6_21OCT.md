# Council 6 — Wed 21 Oct 2026: why the champion bled (10 members, 21 Oct + 19 Oct tapes)

## What happened
Live `spot_dc12_t12` (+ lock), weekly expiry 27 Oct (6 DTE), ₹1,00,000: 53 trades, net **−₹22,561**, 36 % wins. Replay of the tape on the same code: 54 trades, −₹24,443 (51 of 53 trades pair up; ~2–3k/day is replay noise). Nifty drifted 23,083 → 22,650 in small steps.

## Root cause (agreed across M01, M03, M06, M08, M09)
* The exits worked: premium give-back from the best was 3–6 %; 15 of 31 losers never moved 4 pts in favour. **The loss was made at entry.**
* The rule bought the first second of a break. 48 % of 21 Oct entries never moved 8 spot pts (19 % on 19 Oct). Each entry pays ~2.3 premium pts (≈₹900) for buying right after the burst; mean spot edge per trade was +2.5 pts against ~4.3 needed to break even.
* 18 CEs were bought into a falling day (22 % won, −34k); the PEs made +7k.
* Not the cause: option/strike/expiry choice (M04), fills/slippage (M10: ~13k of the loss is the cost of 53 round trips), noise level (M02: 21 Oct was no noisier than 19 Oct; the difference is trend vs mean-reversion, variance ratio 1.16 vs 0.88), volatility, lock.
* Separate defect (M10): the vendor index freezes ~15:15 and prints +500 pts garbage from 15:20 on both days; staleness checks never fired.

## What was changed
* D-131 retest entry, D-132 index guard (docs/02). Twin `spot_dc12_t12_first` keeps the old entry running beside the champion.
* Engine replay, honest fills: 19 Oct: first-touch +90.2k/32 trades → retest +131.2k/17. 21 Oct: −24.3k/54 → −1.9k/22 (CE trades 18 → 4). Council simulation (LTP, proxy strikes) had said +21.9k on 21 Oct; the engine number is the one to use.

## What the data cannot prove
39 trades on two days. 19 Oct's profit rests on a handful of trades (M09: without 3 trades it is −18k). The retest gain is morning-only; PM is ≈ 0 on 21 Oct and worse than first-touch on 19 Oct. It skips ~half the trades, including most clean runners (6 of 8 per day): on a one-way day with no pullback it trades little. Neighbourhood (±20 %): 19 Oct ≥ base in all cells except window 120 s; 21 Oct beats −28.6k in all, but ext 4 ≈ 0. Removing the largest 21 Oct winner leaves ≈ +1k in the simulation. Treat as a paper-trading candidate; the twin gives the live comparison.

## Rejected / not adopted (each cost 19 Oct most of its profit or flipped sign between days)
Trend filter (M05), basket/BankNifty/FinNifty/VIX gate (M07; `bk_up180` is a weak same-sign hint — log, don't gate), re-entry cool-down / swing margin / streak (M08), strike or expiry change (M04), wider fixed trail 14–24 (M02/M03), range-scaled trail 0.33×range (M02: +7k on 21 Oct but fits two days; M09 rejects), wider initial stop 24 pts (M03: fragile, losses 1.7× larger), 75-pt run cap (M01: reasonable, −1.5k on 21 Oct in simulation), 12-min range-width gate ≤ 40 (M09: both days positive but cuts 19 Oct 60 %; shadow candidate), hold-N-seconds / bar-close confirmation (M06: −70k…−140k on 19 Oct).

## Reports
/tmp reports M01–M10 were summarised here; keep this file as the record. Deployment note (M10): a restarted same-day book keeps its saved parameters; the new rules apply to the next trading day's fresh books.
