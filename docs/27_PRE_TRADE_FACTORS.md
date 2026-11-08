# Pre-trade factor catalogue — the market "weather" at the second a book takes a trade (6 Nov 2026)

Every factor below can be computed from what Apex already records, using only data up to the signal second (so it
can be used live as well as studied on the tapes). It is the specification for the per-book weather study
(docs/28).

**Data Apex records.** The tapes (`data/ticks/`) and the engine hold:

* Nifty spot, Nifty futures (best level and 5-level depth) and the put-call-parity forward;
* Bank Nifty and Fin Nifty with their futures, and India VIX;
* the 23 heavyweight stocks (61 % of Nifty's weight) and their futures, with 5-level depth;
* the weekly option chain: bid, ask, last price, quantities, total buy and sell quantity, volume, OI, exchange time;
* full-chain OI snapshots every 90 s.

**What the engine computes from them.** Implied volatility and Greeks, the regime label, the heavyweight "domino"
episodes, the gamma map, levels and their force verdicts, the straddle watch, the 13 advisors, and the quant models
(`apex/quant/`).

"For the trade" means signed so that a higher value favours the book's direction (CE up, PE down).

## Build status (7 Nov 2026, Conductor stage 2)

The photograph is taken at every entry trigger by `apex/engine/weather.py` (`weather_trig` on the position, `weather`
on each missed-signal row; field names in the module docstring). Every value uses only data that had **arrived** by
the trigger second; `tests/test_weather.py` is the leak test.

| Status | Groups |
|---|---|
| **In the photograph** (version 3, 8 Nov) | **All 68 items**, in the photo itself (about 230 fields), on every position and every missed-signal row. The field-to-item table is `apex/conductor/search.py` `ITEMS`; `tests/test_weather.py` fails if a photo field has no item. Version 2 (7 Nov) had 31 items in the photo, 9 recorded elsewhere on the trade and 25 unbuilt, and the 7–8 Nov search ran on a reduced set: withdrawn (docs/28 §11). |
| **Measured against earlier days** | B 7, C 17 "vs its normal", D 25 and E 34 "vs normal": the median of the EARLIER recorded days at the same clock minute (`apex/conductor/clock_norms.py`, `data/learning/clock_norms.json`); undefined until three earlier days exist (`norm_days`) |
| **From the engine's own per-second state** | C 18 (Kalman velocity, bipower noise, jump z, CUSUM), F 39 (gamma map), F 44 (SVI smile), G 54 (race odds, computed for the chosen contract at the trigger), H 57 (HMM), H 58 (Hawkes on every hero contract), I 62 (level force), I 61 (every advisor's verdict for both directions, once a second) |
| **Approximations, said plainly** | D 23 "next round level": depth levels at or beyond the next round 100 in the trade's direction (five levels, so the value is a floor) · D 25 "aggressor-side value": the flow module's 10-s EWMA of aggressive volume x price · J 67: the books that fired in this engine step and the one before it (not a whole second) · E 35 Fin Nifty: its futures when registered, else its spot |

## A. Calendar and clock

| # | Factor | How it is measured |
|---|---|---|
| 1 | Day type | expiry day; day before expiry; first day after a weekend or holiday; event day (`event_today`) |
| 2 | Time to expiry | hours to 15:30 on expiry — sets how fast theta and gamma act |
| 3 | Clock | minutes since 09:15; minutes to the forced flat (15:00 expiry, 15:20 otherwise) |
| 4 | Session phase | opening 30 min / morning / midday / afternoon / last hour |

## B. The day's shape so far

| # | Factor | How it is measured |
|---|---|---|
| 5 | Opening gap | open vs previous close: size, direction, filled or not |
| 6 | Opening range | high–low of the first 15 / 30 / 45 min; broken up, broken down or inside |
| 7 | Range so far | today's high–low vs the same clock time on earlier days |
| 8 | Position in the range | (price − low) / (high − low) |
| 9 | Trend or range day so far | efficiency (net move ÷ path length) over 30 / 60 min; number of new highs and new lows; number of reversals |
| 10 | VWAP | side of VWAP, distance in points, minutes on that side |
| 11 | Previous day's levels | distance to yesterday's high, low and close |
| 12 | Extremes' age | minutes since today's high and since today's low |

## C. Index price action right now

| # | Factor | How it is measured |
|---|---|---|
| 13 | Speed | forward change over 5 s, 10 s, 30 s, 1 min, 2 min, 5 min (for the trade) |
| 14 | Acceleration | change of speed over 15 s and 30 s |
| 15 | Current impulse | size, age, depth of the pullback from its extreme |
| 16 | Swing distance | points to the nearest swing high and swing low of the last 30 min |
| 17 | Realised volatility | 1 / 5 / 15 min, vs its normal at that time of day |
| 18 | Jump and drift change | bipower jump z of the last 5 min; CUSUM drift-change alarm |
| 19 | Choppiness | path length per point of net progress |
| 20 | Spot / futures / forward agreement | basis level and its change over 1 and 5 min |

## D. Nifty futures order book and money flow

| # | Factor | How it is measured |
|---|---|---|
| 21 | Order-flow imbalance | Cont–Kukanov–Stoikov OFI over 10 / 30 / 60 s, and its change |
| 22 | Depth imbalance | 5-level bid vs ask quantity, and its 30-s change |
| 23 | Resting value | rupees at the best bid and ask and at the next round level |
| 24 | Refill vs withdrawal | does the side being hit refill or pull (the level force detector's ρ and π) |
| 25 | Traded volume | volume rate vs normal; aggressor-side value in rupees |
| 26 | Absorption | rupees traded per point of progress (heavy volume, no progress = a defended level) |
| 27 | Price impact and spread | Kyle's λ (price change per unit of signed flow); bid–ask spread |

## E. Heavyweights (23 stocks, 61 % of Nifty)

| # | Factor | How it is measured |
|---|---|---|
| 28 | Weighted move | Σ weight × return of the 23 stock futures over 10 / 30 / 60 s, in Nifty points |
| 29 | Breadth | share of the 23 moving with the trade |
| 30 | Sector split | banks, IT, Reliance, others: which lead, which lag |
| 31 | Who moved first | heavyweights before or after the index (lead in seconds; path ordering) |
| 32 | Basket gap | basket-implied Nifty minus actual Nifty |
| 33 | Heavyweight books | weighted bid vs ask imbalance of the 23 futures books, and its change |
| 34 | Heavyweight volume | volume surge vs normal |
| 35 | Sister indices | Bank Nifty and Fin Nifty confirming or diverging |

## F. Option-chain positioning

| # | Factor | How it is measured |
|---|---|---|
| 36 | OI walls | largest call and put OI strikes; distance ahead of and behind the trade |
| 37 | OI change | over 5 / 15 / 30 min, by strike: where writers add or cover |
| 38 | Put/call ratio, max pain | level, change, distance to max pain |
| 39 | Gamma map | under three dealer assumptions (long calls, short calls, flow-inferred): flip level, gamma walls |
| 40 | Call vs put activity | volume ratio; premium ratio |
| 41 | Straddle | price vs its VWAP and vs its theta-expected decay (expanding or compressing) |
| 42 | IV skew | put IV vs call IV, and its change |
| 43 | IV term structure | this week's expiry vs next week's |
| 44 | Smile position | the chosen strike's IV vs the SVI smile (rich or cheap) |

## G. The chosen option itself

| # | Factor | How it is measured |
|---|---|---|
| 45 | Premium and quote | premium; spread as % of premium; quote age |
| 46 | First-order Greeks | delta, gamma, vega, theta per minute, theta as % of premium |
| 47 | Higher-order Greeks | vanna, charm, speed, color, vomma |
| 48 | Breakeven | index points needed to beat 15 min of theta |
| 49 | IV | level vs today's median; change over 1 and 5 min |
| 50 | Premium momentum | premium and volume change over the last minute |
| 51 | Premium response | actual premium change ÷ delta·ΔF + ½gamma·ΔF² + theta·Δt (over- or under-reacting) |
| 52 | Option book | total buy vs sell quantity waiting, and its change |
| 53 | Option's own levels | the option's day high/low; its own support and resistance (strike levels) |
| 54 | Premium race odds | P(+10 % before −10 %) within 1, 3, 5, 10, 15 min (`apex/quant/passage.py`) |

## H. Volatility environment

| # | Factor | How it is measured |
|---|---|---|
| 55 | VIX | level; change over 5 and 30 min |
| 56 | IV vs realised | ATM IV ÷ realised volatility (options cheap or dear relative to movement) |
| 57 | Hidden regime | HMM state, its probability, expected minutes left |
| 58 | Order-flow chain reaction | Hawkes buy vs sell excitation on the chosen option |

## I. What the engine already concludes

| # | Factor | How it is measured |
|---|---|---|
| 59 | Regime label | DIRECTIONAL / BREAKOUT / EXHAUSTION / RANGE / COMPRESSION / UNCERTAIN |
| 60 | Domino episode | type, first mover, synchrony of the basket |
| 61 | Advisors | each verdict: IV, room, coherence, force, episode, book, premium, quiet, bank, event, gamma leg, gamma room, regime |
| 62 | Level force | vacuum / about to break / holding / testing / rejected, at the nearest wall |

## J. The book's own situation

| # | Factor | How it is measured |
|---|---|---|
| 63 | Trigger | which rule fired, and its strength (impulse size, pullback depth, speed) |
| 64 | Last trade | seconds since exit; won or lost; exit reason |
| 65 | Direction history | same side as the last trade or a flip; re-entry after a stop |
| 66 | Today so far | trades taken, P&L, current streak |
| 67 | Agreement | how many other books are entering the same trade |

## K. Data quality

| # | Factor | How it is measured |
|---|---|---|
| 68 | Feed health | feed age, stale option legs, data gaps today, reconnects, abnormal spreads |

**Not recorded today:** GIFT Nifty, global markets, news. They would have to be added to the feed first.

About 68 groups, roughly 150 individual numbers, per trade.
