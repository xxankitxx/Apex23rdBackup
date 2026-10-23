# Member 13: OI, PCR and dealer-gamma analytics

## Lens
I looked at the option-chain path for Nifty weeklies, end to end:
- `feed_breeze.poll_chain` / `write_chain` writes `data/chain_latest.json`.
- `engine/levels.Pressure` reads it to build the OI walls, PCR and destination/room.
- `engine/gex.GexMap` builds the dealer-gamma map from the same file.
- `engine_main.update_gex` feeds that map.
- Both advisors (`room` and `gex_room`) are in `engine_main.advise`, lines 410-450.

How I checked: I read all of the code above. I ran two probe scripts against the real modules (in my scratchpad as `m13/probe.py` and `probe2.py`). I ran `tests/test_core.py`, and all tests pass. I also checked Apex's Black gamma against py_vollib's reference value and it matches to 1e-12.

## Teardown

### F1 (HIGH): `gex_room` compares weekly strike levels to the monthly futures price
- **Where:** `engine_main.py:449` calls `self.gex.advise(d, ctx["fut"])`. But `ctx["fut"]` comes from `NIFTY|FUT`, which is the monthly contract (`feed_breeze.py:343`, `self.mexp`).
- **What is wrong:** The map is built at `F = self.fwd`, the w0 synthetic forward (`engine_main.py:364, 467`). Its walls and flip are strike levels in that weekly-forward space. `advise()` (`gex.py:125, 129`) then measures `wall - fut` and `flip - fut` against the monthly price. The docstring at `gex.py:116` treats "futures" and "forward" as the same thing, and they are not. The monthly-minus-weekly basis is often 40-120 pts, which is bigger than both of the advisor's thresholds (20 pts for the wall, 30 pts for the flip).
- **Failure scenario (probe2):** forward 25012, call wall 25100, monthly futures 25092.
  - The advisor vetoes the CE with "call gamma wall 25100 is only 8 pts ahead". The real distance is 88 pts.
  - With the same numbers it never vetoes PE entries near the put wall.
  - Once the monthly price is above the call wall, the wall counts as "behind", even though the weekly forward is still 80 pts below it.
- **Effect:** the `gex_room` verdicts logged to the learning loop are biased by the basis. The SPRT would then judge an advisor that is mis-measured, not the gamma idea itself.
- **Why the test misses it:** `test_gex_map_regime_walls_flip` passes `F` as the `fut` argument too, so the mismatch never appears.
- **Fix:** pass `self.fwd`, or `spot + (fwd - spot)`, to `advise`.
- **Contrast:** `Force.levels` (`levels.py:121`) maps walls into futures space with `+ (fut - spot)`. That is correct.

### F2 (HIGH): a half-failed chain poll is published as a valid chain
- **Where:** `feed_breeze.py:483-505`.
- **What is wrong:** If the put request comes back with no `Success` rows (a Breeze error payload, a throttle, or an empty response), the loop simply adds nothing. `out` still holds the calls, so the file is written and `chain_version` is bumped. The poll only gives up early when an exception is raised or the token ledger is empty.
- **Failure scenario (probe):** with a calls-only chain, the gamma map reports balance +1.00 and regime DAMPEN. `gex_room` then vetoes every CE and every PE entry for at least 90 s. PCR becomes 0.0, there are no put walls, so `room` on PE has "no wall data". The bad snapshot is also recorded into replays (`rec.put("chain")`).
- **Fix:** publish only when both legs returned rows and their strike counts are roughly equal. Otherwise keep the previous file and log the failure.

### F3 (MEDIUM): stale or foreign chain files are trusted, and nothing ever checks staleness
- **What is wrong:**
  - **At startup:** the shared table starts at `chain_version=0` and `Pressure.version=-1`. So `refresh` (`levels.py:54-65`) loads whatever `chain_latest.json` is already on disk. That can be yesterday's file, last week's expiry, or synthetic output from a `feed_sim` or `feed_replay` run, because all three feeds write to the same path in `DATA_DIR`.
  - **Expiry is never checked:** `pressure.expiry` is never compared with the engine's `w0`. For a past expiry (my probe used 2026-10-13), `years_to_expiry` drops to its 60-s floor, `T_days=0.0`, and the gamma map is computed on effectively infinite gamma.
  - **Age is never checked:** `chain_age` is computed but only displayed (`app.js:309`). If polling fails all day, for example because of a wrong `rest_expiry` format on a holiday-shifted week, `room` and `gex_room` keep producing verdicts from the last good chain.
- **Fix:** at load time, require `expiry == w0` and `chain_ns > 0`. In both advisors, return "no data" when `chain_age > 3 × CHAIN_POLL_S`.

### F4 (MEDIUM): the two "wall" definitions disagree, and the stricter one usually finds nothing
- **The two rules:**
  - `Pressure._walls` (`levels.py:81-93`) needs OI ≥ 2× the mean of the ±3 neighbouring strikes, and in the top quartile.
  - `GexMap.wall` needs OI ≥ 1.5× the mean of its side of the chain.
- **Failure scenario (probe):** I used a realistic Nifty chain where 100-point strikes carry about 1.6× the OI of 50-point strikes, with smooth peaks at 25200 CE and 24800 PE.
  - GEX finds walls at 25200 and 24800.
  - Pressure finds no walls at all. Only an isolated 2.5× spike was detected.
- **Why it matters:** the neighbour mean includes the other 100-point strikes, so the usual bulges in the chain cannot pass a 2× test. `room` treats "no wall" as "no veto" (`engine_main.py:416`), so the advisor is quietly biased toward permitting trades. The dashboard can also show a GEX wall where the OI panel shows none.
- **Fix:** record both definitions, and log on each trade which rule found which wall. Don't silently pick one.

### F5 (LOW-MEDIUM): `room` is measured from cash spot and judged against the weekly contracts
- `destination(ctx["spot"], d)` (`engine_main.py:410`, `levels.py:95`) measures from spot to a strike. Strikes live in forward space, which sits about 5-30 pts above spot early in the week.
- So upside room is overstated and downside room understated by the weekly carry. That is a sizeable error against a `1.3 × need` threshold that is typically 40-80 pts.
- After 13:00 on expiry day, `need` uses the delta of a w1 contract while the walls are still w0 (0DTE) walls.
- Verified by reading.

### F6 (LOW)
- **"Change since open" is not reliable:** `oi0` is "the first chain this process saw" (`levels.py:65`), so an engine restart at 11:00 resets the change-since-open figures. Breeze's REST chain may carry its own day-change OI field (UNVERIFIED: I could not hit the API). If it does, that field would be robust to restarts.
- **D-062 and the code describe the DAMPEN exception differently:** D-062 says the advisor vetoes in DAMPEN "unless price is already beyond the flip". `gex.py:124-125` instead escapes when the flip is less than 30 pts ahead. The code's version is the coherent one, because DAMPEN at F means F is on the positive side of the flip. The decision log should be updated to match.

## Good things
- **Honest framing of the gamma map** (`gex.py:12-21`):
  - The dealer-sign assumption is stated, along with the doubt about it on retail-heavy Nifty.
  - The outputs are unit-free (balance = net/gross, plus levels), which correctly avoids relying on Breeze's OI units.
  - It is an advisor only.
- **The flip is computed properly** (`gex.py:80-88`): gamma is recomputed on a ±3% grid of hypothetical forwards, not taken from a single cumulative-sum shortcut. It interpolates linearly and takes the sign change nearest the current forward.
- **The wall rule avoids a common trap** (`gex.py:68-77`): the strike must first stand out on OI, and only then is the largest exposure taken. Picking by largest exposure alone would always pick the ATM strike.
- **Per-strike IV:** live IV is used where the band has quotes, with ATM IV as the fallback. Gamma uses the Black-76 formula on the synthetic forward, which I cross-checked against py_vollib.
- **The map cannot crash the engine:** recompute is cached on (chain version, 10-pt forward bucket), and every failure path returns `ok: False` or is caught (`gex.py:104-112`, `engine_main.py:456-475`).
- **Atomic writes and replayability:** the chain file is written via a temp file and replace (`feed_breeze.py:555-561`). The snapshot is versioned through the shared table and recorded for replay, so chain-driven advisors replay exactly.
- **`Force.levels` gets the futures mapping right** with `K + (fut − spot)` (`levels.py:120-122`).

## Ideas from GitHub
1. **VarunS2002/Python-NSE-Option-Chain-Analyzer**
   - Link: https://github.com/VarunS2002/Python-NSE-Option-Chain-Analyzer
   - Licence: GPL-3.0, so I would borrow the concept only.
   - I cloned it. `NSE_Option_Chain_Analyzer.py`, lines ~1087-1367, tracks *change in OI* at the max-OI strikes ("Call/Put Boundary") and raises "Call Exits / Put Exits" when writers at the wall are unwinding.
   - **Apex mapping:** a new observer, `wall_unwind`, in `levels.py`. For the destination wall, log the OI change across the last N chains, which `Pressure` already keeps versioned. A wall losing OI as price approaches is a weakening wall: `room` should not veto, and `force` should lean toward BREAK.
   - It would be pre-registered as an advisor and judged by the SPRT. That turns static OI walls into a dynamic signal, which is the real information on Nifty weeklies.

2. **jensolson/SPX-Gamma-Exposure**
   - Link: https://github.com/jensolson/SPX-Gamma-Exposure
   - Licence: none found, so all rights reserved and concept only.
   - I cloned it. `GEX.py`, lines 225-261, drops contracts with |delta| > 0.95 or IV outside 1-200% before summing exposure, then plots exposure against a grid of forwards and reads the zero-GEX level.
   - **Apex mapping:** add the |delta| < 0.95 filter in `GexMap.compute`, because deep-ITM weekly OI with stale IV skews `gross`. Also publish the grid curve (`tot`) in the view, so the dashboard shows the gamma profile rather than a single flip number.
   - Size S. It's an observer change only, not a trigger change.

3. **vollib/py_vollib**
   - Link: https://github.com/vollib/py_vollib
   - Licence: MIT.
   - I cloned it. `vollib/ref_python/black/greeks/analytical.py:136` has reference Black-76 gamma with doctest values.
   - **Apex mapping:** test tooling only. Add a test that pins `greeks.greeks` gamma, delta and vega to these reference values; with r=0 Apex matches 0.065309. That guards GEX against a silent change to the Greeks. No runtime dependency is needed, just the constants.

## Top 3
1. **Fix F1:** feed `gex.advise` the weekly forward (`self.fwd`) instead of monthly `ctx["fut"]`, and add a test where `fut ≠ F`. Size S. Before Monday, because every `gex_room` verdict logged until then is biased by the basis and contaminates its SPRT record.
2. **Fix F2 and F3:** publish a chain only when both legs returned rows. At load time, require `expiry == w0` and a non-zero `chain_ns`. Make `room` and `gex_room` return "no data" when the chain is older than 270 s. Size S. Before Monday.
3. **Wall work:** reconcile and record the two wall definitions (F4), measure `room` in forward space (F5), and add the `wall_unwind` OI-change observer (idea 1). Size M. Later, as pre-registered advisors or variants after the weekend.
