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
| **Added 9 Nov (version 4)** | **Items 69–104** (groups L–Q below, about 140 more fields), `apex/engine/weather4.py`, on every position and every missed-signal row from 9 Nov. Owner: "67-68 items ... are not enough to identify a bad trade from a good trade ... add at least 30-40 more different kind of items". Photographs taken before 9 Nov do not carry them; the 14 replayed days would need a re-replay to have them. `tests/test_weather_v4.py` is the leak test and the definitions |
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

## L. The tape's structure (added 9 Nov, photo version 4)

| # | Factor | How it is measured |
|---|---|---|
| 69 | Yesterday's shape | yesterday's range; where yesterday closed inside it (for the trade); spot inside or outside yesterday's range; today's range ÷ yesterday's |
| 70 | Pivot levels | floor pivots from yesterday's high, low, close (S2, S1, P, R1, R2): distance from P for the trade; points to the next level ahead |
| 71 | Strike grid | points to the next 50-point strike ahead of spot; distance to the nearest strike (pinning) |
| 72 | The last bars | the last 5 min and 1 min as a bar: body for the trade, body ÷ range, the wick on the side ahead; the last minute's range ÷ the mean of the 15 before it |
| 73 | Bar runs | consecutive 1-min closes for the trade (negative = against); share of the last 30 one-minute moves for the trade; of the last five 5-min windows, how many made a higher high and higher low for the trade |
| 74 | Position in recent windows | spot inside the 5 / 15 / 60-min range (1 = at the extreme in the trade's direction) |
| 75 | Oscillators | RSI(14) on 1-min and on 5-min marks, for the trade; z-score of spot against its last 20 one-minute marks |
| 76 | Moving averages | spot minus the 5 / 20 / 60-min average, for the trade; how many of the three it is beyond; the 20-min average's 5-min slope |
| 77 | Compression | the 5 / 15 / 60-min range in points; 15-min ÷ 60-min range (squeeze); mean 1-min range over 15 min; 1-min ÷ 15-min realised vol |
| 78 | The day's net move | spot minus the first print, for the trade; that as a share of the day's range; minutes continuously on this side of the open |
| 79 | Persistence | lag-1 autocorrelation of 1-min moves over 30 min; variance ratio of 5-min to 1-min moves over 60 min (above 1 = trending, below = reverting) |
| 80 | The adverse path | the largest 1-min move against the trade in the last 15 min; how many of those 15 minutes went against it |

## M. Across markets (added 9 Nov)

| # | Factor | How it is measured |
|---|---|---|
| 81 | Sister divergence | Bank Nifty futures % minus Nifty % over 1 and 5 min, for the trade; correlation of their 10-s moves over 30 min |
| 82 | The VIX path | where VIX sits in its own range today; did VIX and spot move the same way over 5 min |
| 83 | Breadth at other horizons | share of heavyweight weight moving the trade's way over 1 min and 15 min (item 29 is 5 min); up minus down share; the change in 5-min breadth over the last 5 min |
| 84 | Dispersion and concentration | weighted spread of the heavyweights' 5-min returns; share of the weighted move from its three largest contributors; stocks moving the trade's way; share of weight at its 30-min extreme in the trade's direction |
| 85 | The leaders | the heaviest stock's move over 1 and 5 min, for the trade; how many of the three heaviest moved the trade's way over 1 min |

## N. The option and the chain (added 9 Nov)

| # | Factor | How it is measured |
|---|---|---|
| 86 | Moneyness | points and % in the money (forward against strike); intrinsic and time value; time value as % of the premium |
| 87 | Gearing | delta × forward ÷ premium; gamma per rupee of theta per minute; delta change for a 1 % move; spot points needed to earn back the spread |
| 88 | Implied move used | the ATM straddle now and against the day's first; today's range ÷ the opening straddle; the day's net move ÷ the opening straddle, for the trade |
| 89 | The opposite leg | the same strike's other option: premium change over 1 and 5 min, IV change over 1 min; both legs' 1-min change added (positive = both bid) |
| 90 | The premium's own path | the contract's premium change over 5 and 15 min; position in its own 15-min range; % below its 15-min high; its own 5-min volatility |
| 91 | Entry liquidity | rupees resting at the best ask; at five ask levels; at five bid levels; bid ÷ ask depth |
| 92 | The IV path | where ATM IV sits in its range today; correlation of 1-min IV and spot moves over 15 min; the contract's IV minus ATM IV |
| 93 | The wings | put IV 100 points below spot minus call IV 100 above; their mean minus ATM IV |
| 94 | Own-strike OI | the contract's OI; today's volume ÷ OI; its share of the hero band's OI on its side; against the other leg's OI |
| 95 | Futures OI build-up | futures OI change over 5 and 30 min; long build-up / short covering / short build-up / long unwinding (5-min price and OI together); fresh positions in the trade's direction, yes or no |

## O. Flow through time (added 9 Nov)

| # | Factor | How it is measured |
|---|---|---|
| 96 | Volume acceleration | last minute's volume ÷ the minute before: futures, heavyweights, the option band; futures volume over 5 min |
| 97 | Up-volume share | share of futures volume traded in the seconds the forward moved the trade's way, over 1 and 5 min |
| 98 | VWAP stretch | futures minus VWAP as a z-score of today's own stretch, for the trade; VWAP crossings today; the stretch now ÷ the furthest today on this side |
| 99 | Call/put flow tilt | the trade's side's share of option-band volume over the last minute; that minus its 5-min share |

## P. The books around this one (added 9 Nov)

| # | Factor | How it is measured |
|---|---|---|
| 100 | Other books' positions | books holding the same side / the other side now; share of the same-side holders in profit; the book's family (same name prefix): members, busy in a trade, free (docs/35 §7: a silent sibling that is busy is not a veto) |
| 101 | Other books' results today | closed trades and win share across all other books; seconds since the last closed trade on this side and whether it won; wins among the last five on this side |
| 102 | Trigger density | seconds with a trigger (any book, taken or not) in the last 5 and 30 min, same side and other side; direction flips among the last 15 minutes' triggers; seconds since the last opposite trigger |

## Q. This book's day (added 9 Nov)

| # | Factor | How it is measured |
|---|---|---|
| 103 | Re-entry context | trades on this side today; losses today; seconds since the last loss; the last trade's return, hold time and peak; same contract as the last trade, and the premium now against that trade's exit and entry |
| 104 | The day's P&L shape | best and worst trade today; the last three trades' return; win share; return below the day's high-water mark |

**Not recorded today:** GIFT Nifty, global markets, news. They would have to be added to the feed first.

104 items (68 to 8 Nov, 36 added 9 Nov), about 390 individual fields, per trade.

## R. The machine, the inputs and the trade's own path (added 10 Nov, photo version 5)

Detail, units and missing reasons are in docs/39 section 3.

| Item | Name |
|---|---|
| 105 | Engine service delay |
| 106 | Persistence health |
| 107 | Cross-input synchronisation |
| 108 | Fresh weighted coverage |
| 109 | Flow-sign uncertainty |
| 110 | Response-model reliability |
| 120 | Opportunity survival |
| 121 | Contract-path continuity |
| 122 | Fill evidence |
| 128 | Research lineage and support |

Items 123 to 126 are the continuation photograph (`weather_hold` on the trade), not entry items. Items 111 to 119
and 127 are not built. The millisecond fields of 105, all of 106 and three text fields of 128 are recorded but not
searched.
