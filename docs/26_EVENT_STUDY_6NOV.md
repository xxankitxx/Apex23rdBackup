# Event study: what separates a real move from a fake one? (6 Nov 2026)

ChatGPT's 6 Nov proposal, after reading docs/25: stop adding models and study the data itself. Build an event-level
dataset with real option outcomes, compare the runners the champion caught with the ones it missed and with its
dead losers, look at path shape, rates of change and the order of events (heavyweights → futures → options), and
only then consider a trained model. All of it offline; nothing live was changed.

## 1. What was built (`research/event_study/`)

| Script | What it does |
|---|---|
| `extract_all.py` | Replays a raw tape through the engine's own parser into a private shared-memory table and samples every instrument once per second: Nifty, Bank Nifty, Fin Nifty and their futures, VIX, the **23 heavyweight stocks and their 23 futures** (61.4 % of Nifty's weight, 5-level depth on the futures), and the nearest-weekly Nifty options. |
| `events.py` | **Outcomes**: for every second and both sides, buy the nearest-ITM option at the ask 2 s later (the kit's fill) and follow its bid for 15 min — best and worst point, return at 30 s, 1, 3, 5, 10, 15 min, time to +10 % / +20 %, and whether +10 % / +20 % came before −10 %. **Runner** = +20 % before −10 % within 15 min. **Move starts** ("onsets"): the forward moved ≥ 8 pts in 60 s, at most one per direction per 5 min. **44 causal features** at any second (see §3). |
| `analyze.py` | The three comparisons below, every model judged on days it never saw. |
| `kit56.py` | c20_9x on the kit for 5 and 6 Nov (kit −6,055 / +93,529 vs live −5,486 / +93,821). |

Data: 14 full sessions, 19 Oct – 6 Nov (expiry: 19 Oct, 27 Oct, 3 Nov).

## 2. How many real opportunities are there?

ChatGPT's "107 missed runners" came from the 15-min windows with a 40-pt forward range; those count chop and the
same move several times. Measured on the option itself, merging same-side runner windows less than 5 min apart:

| | normal days: moves | c20_9x caught | expiry days: moves | caught |
|---|---:|---:|---:|---:|
| every runner (+20 % before −10 %) | 124 (11 days) | 13 (10 %) | 85 (3 days) | 23 (27 %) |
| best entry reached ≥ +40 % | 26 | 6 (23 %) | 46 | 21 (46 %) |
| best entry reached ≥ +80 % | 3 | 1 | 22 | 13 (59 %) |

About 15 distinct runner moves a day, but only **~2.4 big ones (≥ +40 %) on a normal day**; c20_9x takes about a
quarter of those and most of the very big expiry moves.

## 3. Real move or fake move? (988 move starts: 237 runners, 751 duds)

A **dud** is a move start where buying lost 10 % first or never got above +5 %. Each feature was measured at the
start, signed so that higher favours the trade, with AUC = 0.5 as a coin flip.

| Group (ChatGPT's hypothesis) | Features | AUC | Verdict |
|---|---|---:|---|
| The option itself is already moving | premium change over 60 s; option volume over 60 s | 0.63; 0.63 | the only consistent signal: same direction on 11 / 10 of 14 days, and in both halves of the period |
| Option book | option buyers vs sellers waiting | 0.59 | weak |
| Where in the day | position inside the day's range; points left to the day's extreme | 0.59; 0.41 | weak; mostly a trend-day effect |
| Volatility of the tape | realised vol over 5 min | 0.56 | weak |
| IV | IV level | 0.62 | but 0.52 within a single day: it marks high-IV days, not moments |
| IV rising after the move starts | IV change over 60 s; IV change per point moved | 0.51; 0.51 | **no signal** |
| Rates of change (derivatives) | forward acceleration 30 / 60 s; order-flow acceleration; depth-imbalance change; volume acceleration | 0.48–0.52 | **no signal** |
| Futures order flow (Cont–Kukanov–Stoikov) | 10 / 30 / 60 s | 0.50–0.54 | **no signal** |
| Order of events (heavyweights → futures → options) | heavyweight lead over the index; signed Lévy area of the two paths over 60 s; heavyweight breadth | 0.46–0.53 | **no signal** |
| Heavyweight book | weighted depth imbalance of the 23 stock futures | 0.46 | no signal |
| Premium lag | option change vs a 0.55-delta move | 0.50 | no signal |

**All 44 features together** (gradient boosting, trained leaving each day out, so every prediction is on an
unseen day): AUC **0.582**. The same procedure on labels shuffled within each day scores **0.552 ± 0.026** (the
day-level runner rate alone is worth that much), so the real edge is about one standard deviation: indistinguishable
from noise. Calibration on unseen days is nearly flat:

| Predicted runner chance | Actual |
|---|---:|
| 7 % | 21 % |
| 25 % | 27 % |
| 47 % | 34 % |
| 68 % (15 cases) | 47 % |

**Is the one consistent signal worth money?** A simple trade at each move start — +20 % target, −10 % stop,
15-min clock — by band of "premium already rising over 60 s", in both halves:

| Half | Lowest band → highest band (average return per trade) | All |
|---|---|---:|
| 19–28 Oct | +0.5 %, −0.1 %, −1.0 %, +1.0 %, −1.0 % | −0.1 % |
| 29 Oct – 6 Nov | −1.0 %, −1.2 %, +0.8 %, +0.5 %, −0.2 % | −0.2 % |

The top band has more runners (about 35 % against 24 %) but its failures cost as much, so every band averages about
zero. It would also mean ~21 trades a day.

## 4. Caught vs missed runners, and dead losers

* **Caught vs missed** (features at each runner's start): the largest differences are AUC 0.42–0.57 (heavyweight
  30-s move, time of day, position in the day). Nothing marks the missed ones out.
* **c20_9x dead losers (18) vs its winners (41)**, at the entry second: VIX 0.69, option book 0.67, realised vol
  0.62. With 44 features tried on 59 trades, the best of 44 random AUCs is about 0.65–0.70 by chance alone, so none
  of this can be told from noise.

## 5. Conclusion

On these 14 days the information Apex records — the index, its futures and order book, the 23 heavyweights and their
books, the option chain, IV, and the path, shape, rates of change and ordering of all of them — does not say, at the
moment a move starts, whether it will run. That is ChatGPT's own falsifiable test, and on this data the answer is
"not detectably". It is also why a trained "Model B" would not help yet: the best combined model is barely above the
shuffled-label baseline.

What the study does show:

* The opportunity is smaller than "107 missed runners": about two big runners per normal day, of which c20_9x takes
  about a quarter, and most of the very big expiry moves.
* The only signal that holds is option momentum — the premium and its volume already moving — and it does not turn
  into money with a fixed bracket.

What would change the answer: many more days (every new session adds about 70 move starts and 15 runner moves), or
information Apex does not record today. Rerun `research/event_study/analyze.py` as days accumulate; the dataset grows
by itself from the tapes.
