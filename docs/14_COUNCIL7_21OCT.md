# Council 7 — Wed 21 Oct evening: few trades, held, profitable on both tapes

## The owner's complaints
Way too many trades, none held; the same mistake again and again; entries after the rally in the contract is over.
Constraints kept: all-in lots (no risk sizing — refused), ₹1,00,000 a day, LTP fills, paper, no brakes or caps.

## Ideas harvested from public code (ideas only, no code copied)
smart-money-concepts (MIT): swing highs/lows, BOS / CHoCH, OTE 0.618–0.786 retracement, FVG · marketcalls SMC tutorial ·
Supertrend reversal and Choppiness-Index breakout (StockSharp catalogue) · chandelier / ATR trailing stops · Kaufman
efficiency ratio · option-chain OI / PCR / skew.

## Scoreboard (council simulator, LTP; 19 Oct / 21 Oct)
| Member | Idea | 19 Oct | 21 Oct | Verdict |
|---|---|---|---|---|
| — | champion first-touch (reference) | +151k / 33 tr | −28k / 48 tr | — |
| C06 | **pullback of a 45-min impulse** | **+124k / 5** | **+59k / 4** | every ±20 % neighbour positive on both days → **adopted** |
| C03 | 12-min entry + 2.5×ATR7 exit | +137k / 22 | +40k / 19 | cliff at k = 2.0; 3 trades carry 21 Oct |
| C02 | Supertrend 2-min pullback | +24k / 3 | +83k / 5 | narrow island; one trade carries 21 Oct |
| C07 | prove-then-hold | +39k / 21 | +66k / 15 | gives back 70 % of 19 Oct |
| C01 | structure bias, sell the rally | +20k / 24 | +27k / 11 | one trade carries 21 Oct |
| C04 | regime gates | ≤ 0 | ≤ +10k | not stable |
| C05 | option-chain lead | — | — | the chain moves WITH spot, not before it |
| C08 | red team | — | — | nothing else robust; random entries + a wide exit score similarly on 21 Oct |

## Engine replay (honest fills, all-in) — the numbers that count
| Book | 19 Oct | 21 Oct |
|---|---|---|
| **spot_pb45 (champion)** | **5 trades, +₹78,647** | **4 trades, +₹55,426** |
| spot_dc12_t12 (retest, shadow) | 17 trades, +₹1,31,193 | 22 trades, −₹1,882 |
| spot_dc12_t12_first (old live rule, shadow) | 32 trades, +₹90,162 | 54 trades, −₹24,281 |

21 Oct trades: CE 09:49→10:05 −15,083 (stop); **PE 10:35→12:02 +51,285 (target, 87 min)**; PE 12:33→13:57 +13,894 (lock);
PE 13:57→15:00 +5,330 (flat). 19 Oct: CE 09:25 −14,820 (stop, 1 min); PE 09:33 +6,598; CE 10:04 +6,962; PE 11:09 +61,152; PE 14:02 +18,756.

## Honest limits
* 9 trades on two days. 21 Oct is one held PE. The pullback entry is not better timed (median 10-min excursion after entry is
  no better than the breakout's); the profit is the structural stop that holds through 30–75-pt bounces plus one shot per
  impulse. On 21 Oct random-time entries with the same exit score similarly (C06's null: 40th percentile).
* All-in with a stop 30–70 pts away: a single stop costs ₹13–27k. Few trades means some days have none.
* Both tapes fell after 09:40: the CE side (an up-trend day) is untested. Cliff below a 30-min window; keep X ≥ 60.
* The shadows keep running on the same feed, so every new day adds an honest comparison.
