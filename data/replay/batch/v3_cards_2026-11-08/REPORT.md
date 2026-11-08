# 14-day replay with the whole photograph (version 3, all 68 items) — 8 Nov 2026

**The complete per-book report is `FULL_REPORT.md` beside this file:** every one of the 87 books over the 14 days
(trades, wins, losses, win rate, mean return, rupees, losing days, best and worst day), then every restricted book
against its free parent trade by trade (kept / removed by the rule / extra), a one-line verdict per rule, and every
losing trade of every restricted book with its trigger, exit reason, hold and return.

Run dirs `data/replay/batch/v3_<day>`, 19 Oct – 6 Nov (14 trading days), 7 at a time, `--seed data`,
APEX_FAST, missed-signal recorder on. Every manifest `status: ok`, 0 cf_errors, 0 recorder faults, 0 engine faults.
Every trade's photograph is version 3 with 263–273 fields (the first seven days ran the tree before the `conductor`
book and the first-photo check were added, so they have 86 books and no "first photograph" log line; the last seven
have 87 and log "268 fields, version 3, not yet filled: 64 Last trade, 65 Direction history" at the first trigger,
the two items that need a prior trade). Code at `cf8f7c5` plus the uncommitted v3 tree (`source_hash` in each
manifest: first batch `50fc089e907c`, second `aab55fb1375b`).

## The cards (`book_cards.md`, `book_cards.json`)

82 books, 57 searched (the rest had too few evidence-clean rows), 200 shuffles per line, every one of the 68 items.
**2 books have a line that beats luck; about 2.9 would be expected by luck alone.** The search over all items
therefore does NOT find weather that separates winning from losing entries for any book beyond what chance
produces. The two:

| Book | Condition | Item | Kept side | Other side | Plain record (13 days) |
|---|---|---|---|---|---|
| edge_bracket_only | `opt_vol1 < 2.77e6` | 50 Premium momentum | 79.5 trades, 49 %, +2.8 % | 20.5, 5 %, −8.7 % | 87 trades, 40 %, +0.5 % |
| edge_breakout | `vomma >= 0.00646` | 47 Higher-order Greeks | 84, 46 %, +1.7 % | 36, 11 %, −6.8 % | 78, 37 %, −0.6 % |

Both kept sides win less than half the time with a small mean; the books themselves are flat. The strong books
(the c20 family) have NO line that beats luck: their best lines (VIX ≥ 16, ATM IV ≥ 16.3, agreement ≥ 7) raise the win
rate to 69–74 % on the kept side but do not clear the shuffle test with 58–65 trades.

HMM / Hawkes lines were excluded before choosing (docs/34 F02: parameters fitted 5 Nov on sessions through 4 Nov).

## The proposal (`pool_proposal.md`) and what the Conductor would have done (`sim_*.md`, in-sample)

Offline account (`apex/conductor/account_sim.py`, every pool entry on every day = in-sample, priority by the
discovery-day mean return per trade), ₹1,00,000 fresh each day, all-in, gross paper rupees, versus `c20_9x` alone on
the same run:

| Pool | Trades | Wins | Losses | P&L ₹ | Losing days /14 | Collisions (occupied + pending) |
|---|---|---|---|---|---|---|
| A: c20_9x alone (check: equals the book's own record) | 81 | 43 | 38 | +10,04,809 | 4 | 0 |
| B: c20 family unrestricted (9y, 9s, 9v, 9x, 9t) | 89 | 49 | 40 | +10,44,251 | 4 | 12 |
| C: B + the two rule pairs | 149 | 74 | 75 | +8,65,082 | 3 | 194 |
| D: the two rule pairs only | 111 | 56 | 55 | +3,51,656 | 3 | 28 |
| E: B + c20_8x, c20_9e, c20_9h | 95 | 50 | 45 | +9,50,966 | 4 | 41 |

Per day, A vs B vs C:

| day | c20_9x trades | c20_9x P&L | family trades | family P&L | family + 2 pairs trades | P&L |
|---|---|---|---|---|---|---|
| 2026-10-19 | 16 | +40,433 | 18 | +21,775 | 23 | +86,242 |
| 2026-10-21 | 5 | +48,074 | 5 | +48,074 | 11 | +26,266 |
| 2026-10-22 | 3 | +7,771 | 3 | +7,771 | 6 | +21,700 |
| 2026-10-23 | 5 | +25,226 | 5 | +25,226 | 9 | +63,476 |
| 2026-10-26 | 4 | +217,155 | 6 | +260,920 | 15 | +167,160 |
| 2026-10-27 | 13 | +532,038 | 13 | +532,038 | 15 | +470,054 |
| 2026-10-28 | 3 | +53,856 | 5 | +56,235 | 9 | +1,638 |
| 2026-10-29 | 4 | +24,788 | 4 | +24,788 | 5 | +23,663 |
| 2026-10-30 | 3 | −5,558 | 3 | −5,558 | 11 | +29,464 |
| 2026-11-02 | 4 | +41,584 | 4 | +41,584 | 9 | +51,035 |
| 2026-11-03 | 12 | −42,214 | 13 | −36,254 | 17 | −59,563 |
| 2026-11-04 | 5 | −26,679 | 5 | −26,679 | 7 | −11,973 |
| 2026-11-05 | 1 | −5,902 | 1 | −5,902 | 5 | −24,557 |
| 2026-11-06 | 3 | +94,237 | 4 | +100,233 | 7 | +20,475 |

Reading: the two rule pairs add trades (their books fire often) and roughly halve the win rate of the account; they
make money on the 3 days they beat c20_9x and give back more elsewhere. The c20 family unrestricted is c20_9x plus a
few trades its siblings take while 9x is idle (B differs from A on 5 days, 4 of them for the better). Nothing here is
a forward result: every figure is on the discovery days, and the c20 family was itself selected on most of these days.

## What was NOT found

No weather item, across all 68, gives any book a rule the shuffle test accepts beyond chance. "No losing trade"
cannot be approached by a factor-line rule on this evidence; the losing trades of the strong books are not separated
from their winning trades by anything the photograph records at the trigger second. The evidence stays (`book_cards.md`
has every book's full card, all items), the 9 Nov live day adds the first out-of-sample day, and the cards are rebuilt
each evening with one more day.
