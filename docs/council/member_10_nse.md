# Member 10: NSE F&O specifics

## Lens
I checked the parts of the code that depend on Indian market rules: `apex/config.py` (holidays, weekly and monthly expiry rules, lot size, freeze quantity, strike step, session clock, 0DTE rails, `EVENT_DAYS`) and `apex/universe.py` (index weights). I compared each against current public sources on 18 Oct 2026. Methods: reading the code, a probe script calling `weekly_expiries`, `monthly_expiry` and `monthly_expiry_candidates` on 9 dates, the test suite (all tests pass), and WebFetch of NSE, niftyindices and RBI documents.

**Facts that are current (verified):**
- **Holidays.** `NSE_HOLIDAYS` (config.py:167-172) matches the published 2026 list exactly: 16 weekday holidays (ClearTax copy of the NSE list). It also matches the independently maintained `exchange_calendars` XBOM list.
- **Expiry shifts.** Tue 20 Oct (Dussehra) gives a Mon 19 Oct weekly. After 15:30 on Mon 19 Oct the system rolls to 27 Oct (monthly) and 3 Nov. Tue 10 Nov gives Mon 9 Nov. Tue 24 Nov gives Mon 23 Nov for both weekly and monthly. 29 Dec is a normal monthly. All correct.
- **Freeze quantity.** `FREEZE_QTY = 3510` matches NSE/FAOP/76693, effective 5 Oct 2026 (BANKNIFTY 1440, FINNIFTY 3240).
- **Lot size.** `LOT_SIZE = 65` is current: 75 changed to 65 from the 6 Jan 2026 weekly. I found no newer revision.
- **Muhurat session.** It falls on Sun 8 Nov 2026, so `is_trading_day` returns False and nothing runs. That is correct.
- **Nifty 50 weights.** The ten "exact" weights match the 30 Sep 2026 factsheet. The Bank Nifty and FinNifty top-10 weights also match their factsheets.

## Teardown

**T1. Two "estimate" Nifty weights cannot be right (medium). Verified by logic plus the factsheet.**
- Where: `universe.py:26-27`, TCS 2.70 and ITC 2.56.
- What is wrong: the 30 Sep factsheet's top-10 table ends at M&M, #10, with 2.52%. Any stock outside the top 10 must therefore weigh 2.52% or less. TCS at 2.70 and ITC at 2.56 would both rank inside the top 10, yet neither appears there, so both estimates are too high.
- Effect: synchrony S_d is "share of tracked Nifty weight", and the basket-implied points feed the `gap3`/`gap5` variants. Both over-count the IT and FMCG legs. On an IT-only move, such as TCS or INFY results, the basket looks more "synchronous" than it is.
- Fix: cap every estimate at 2.52 or below. Better, derive the weights from the NSE constituent CSV (free-float market cap) or another dated source. Add a unit test: every "estimate" weight must be no larger than the smallest "exact" weight.

**T2. `EVENT_DAYS` is empty, and its one example date is a Saturday (medium). Verified against RBI.**
- Where: `config.py:146-148`.
- What is wrong: the commented example is `"2026-12-05": "RBI policy"`, which is a Saturday. The RBI's FY27 MPC schedule (press release 62422) puts the meeting on 2-4 Dec, so the decision comes on **Fri 4 Dec**. The October meeting (5-7 Oct) has already passed.
- Effect: with an empty dict, the "event" advisor logs zero would-vetoes, so the learning loop can never assess it.
- Dates to add, all checked: RBI 4 Dec 2026 and 5 Feb 2027.
- Dates to add, not checked by me (owner to confirm): FOMC decision about 29 Oct IST, US midterms 3-4 Nov, Union Budget 1 Feb 2027.
- Bigger gap for this system: Q2 results days of the tracked heavyweights. A single stock gapping on results breaks the "heavyweights lead the index" premise. Results days should be logged per stock, not per day.

**T3. No 2027 holidays, and the preflight check misses the gap (medium, hard date). Verified by reading.**
- Where: the preflight check at `run_apex.py:188` only asks whether *this* year's holidays are present. On 20 Dec 2026, `weekly_expiries` already looks into Jan 2027 and the check still passes.
- The concrete risk: **Tue 26 Jan 2027 is Republic Day**, and it is both the weekly and the monthly expiry date. Without a 2027 list, `weekly_expiries` and `monthly_expiry` return 26 Jan instead of Mon 25 Jan. From about Tue 19 Jan, w1 and the futures contract would point to a contract that does not exist. The token probe and the empty-chain guard would catch it, but only as a NO-GO on the morning.
- Fix: make preflight require holiday coverage for every date up to the furthest expiry it computes (w1 and mexp), not just the current year.

**T4. Days-to-expiry is counted in calendar days (low). Verified at `paper.py:120-121`.**
- `dte` counts calendar days, so on Fri 16 Oct, Fri 6 Nov and Fri 20 Nov (expiry on the following Monday) dte is 3. That selects the "ge3" delta band (0.52-0.70) when only one trading session remains.
- `greeks.years_to_expiry` (greeks.py:43) also uses calendar time over 365 days. Friday IVs therefore come out lower and deltas differ from a trading-time view.
- This is not a bug against D-021, which never says calendar or trading days. But the three Mondays in Oct and Nov 2026 hit this ambiguity, so the decision log should state which one is meant.

**T5. The comment on `SUPPRESS_UNTIL` predates the F&O pre-open session (low, informational). Verified the rule; the Breeze behaviour is not verified.**
- Since 8 Dec 2025, NSE runs a pre-open session for futures (not options): orders 9:00-9:08, matching 9:08-9:12, buffer to 9:15. The 9:15 futures price is now discovered in an auction.
- Effect: the comment's "overnight repricing" claim (`config.py:56`) and the domino's in-session sigma logic (`domino.py:84-89`) rest on a 9:15 jump that may now arrive at about 9:08. Options still open with a jump at 9:15.
- Check (unverified): Monday's recorder should log whether Breeze streams futures ticks between 9:08 and 9:15. If it does, those ticks land in `last_msg` but outside `fut_sigma`, which is fine.
- Separate effect: the first 10 minutes of the open feed the 20-minute EWMA. That inflates sigma at 9:25, when entries open (unverified size).

**T6. Lot size and freeze quantity are hard-coded constants that NSE changes (low). Verified by reading.**
- The freeze limit was revised on 1 Sep and again on 5 Oct 2026, so it now changes roughly monthly. Lot sizes are reviewed every six months.
- Effect today: none. Return-on-premium learning ignores lot size, and `slices` is informational only.
- Fix: preflight should read the NIFTY lot from the Breeze security master (or NSE `fo_mktlots.csv`) and fail on a mismatch with `LOT_SIZE`.

**T7. `monthly_expiry_candidates` probes a stale "last Thursday" rule (low). Verified with the probe script.**
- Stock futures moved to last Tuesday in Sep 2025, so the Thursday fallback (`config.py:235-245`) is dead code.
- In Mar 2026 it returns [30 Mar, **25 Mar**], so the fallback can sit *before* the primary. Harmless, because the cache and the first token lookup win, but it should be removed.

**T8. Nothing stops a live start on a holiday (low). Verified by reading.**
- If `run_apex live` is started on Tue 20 Oct, it builds normally from the REST previous close and then sits idle. Preflight never prints "today is an NSE holiday".
- Learning is unaffected, because only days on which both books traded count.

## Good things
- **Expiry calendar** (`config.py:186-232`): the holiday roll-back is shared by weekly and monthly expiries, the 15:30 roll-off is explicit, and `ws_expiry` uses its own month names, so it does not depend on the machine's locale (`%b`). All seven dates in the design's test plan come out right in my probe.
- **Freeze-quantity comment** (config.py:47): it cites the exact circular, which made verification a 30-second job. `universe.py` likewise tags each weight as exact or estimate and dates its source. That is good provenance practice.
- **0DTE rails** (`paper.py:112-118`, `paper.py:379-384`): they key on the contract's own expiry, not on the weekday, so holiday-shifted Monday expiries work without special cases.
- **Clock validation**: `config.validate()` (config.py:290-293) checks that the session clock is in order, and the preflight token probe of the computed weekly and futures expiries (run_apex.py:241-268) turns a calendar error into a morning NO-GO instead of a silent empty chain.
- **Pre-open handling** (`domino.py:84-89`): sigma learning is limited to in-session ticks, so pre-open zeros cannot shrink σ.

## Ideas from GitHub
1. **gerrymanoim/exchange_calendars** (https://github.com/gerrymanoim/exchange_calendars, Apache-2.0; cloned).
   - What to borrow: the `exchange_calendar_xbom.py` precomputed BSE/NSE holiday list. Its 2026 dates match Apex exactly.
   - How it maps onto Apex: a **preflight tool** that diffs `config.NSE_HOLIDAYS` against `xcals.get_calendar("XBOM")` for the current and next year. It warns on any difference and on a missing next year. Use it as a dev or preflight check only, not a runtime dependency. This covers T3 from a second source.
2. **BennyThadikaran/NseIndiaApi** (https://github.com/BennyThadikaran/NseIndiaApi, **GPL-3.0**: concept only, no code copied; cloned).
   - What to borrow: `NSE.holidays()` (calls NSE's `/api/holiday-master`), `fno_lots()` (parses `nsearchives.nseindia.com/content/fo/fo_mktlots.csv`) and `get_futures_expiry()` (NSE.py:1326-1360, 1568, 1769).
   - How it maps onto Apex: a small home-written preflight **observer**. Once a day it fetches the official NSE holiday master and the lot file, and asserts they agree with `NSE_HOLIDAYS`, `LOT_SIZE` and the computed expiries. This covers T3 and T6 straight from NSE, written clean-room.

## Top 3
1. **Fix the TCS and ITC weights, cap every estimate at or below the #10 weight, and add a unit test** (T1). Size S, before Monday. It directly affects the synchrony number that the frozen trigger and the gap variants read on Monday.
2. **Fill `EVENT_DAYS`** (T2). Add RBI 4 Dec 2026 and 5 Feb 2027 (correcting the 12-05 example), plus the owner-confirmed FOMC, US midterm and Budget dates. Add a per-stock results calendar for the 14 tracked Nifty heavyweights, logged as an advisor input. Size S, before Monday for the dict; later for the results calendar.
3. **Preflight calendar guard** (T3, T6): require holiday coverage up to max(w1, mexp), add the 2027 list once NSE publishes it (26 Jan 2027 is a Tuesday expiry), and cross-check `LOT_SIZE` against the security master, ideally through the exchange_calendars or NSE holiday-master diff above. Size M, later, but it must be done before about 19 Jan 2027.
