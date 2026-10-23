# Member 09: Dashboard, UX and decision support

## Lens
`apex/static/index.html`, `app.js`, `style.css`, `apex/gateway.py`. The question: does the screen help a trader decide quickly and correctly?

Method: I read all four files in full and the engine's `publish()` (`engine_main.py:595-683`). I ran the sim on a private copy (`/tmp/council/09/apex_copy`, with the port and shm names changed to avoid other members' runs; baseline untouched). Playwright/Chromium covered screenshots at 1600×1000 and 1366×768, DOM-churn checks, function timing, a WebSocket message counter, and fault drills where I SIGSTOP'd the engine or the gateway. Disclosure: an early `pgrep` also paused another member's sim engine (pid 1434) for 15 s before I resumed it.

## Teardown

**1. No staleness detection: a frozen engine looks healthy. HIGH.** Locations: `app.js:71-84`, `gateway.py:109-120`.
- `/ws/state` only pushes when the blob changes, and the browser never checks how old `S` is.
- The health dot is driven only by *tick* ages.
- *Verified* by SIGSTOP on my engine for 15 s. The clock stayed frozen at `09:52:24` and the verdict stayed "Push is 0.2 of the 2.0 needed." The dot stayed **green "live"** with "tick age 250 ms".
- If the gateway freezes, the dot only turns grey and says "no ticks". The whole page keeps showing the last verdict, position P&L and stop with no warning.
- Failure scenario: the engine hangs mid-trade (GC, disk, a numpy stall). The owner watches a "live" screen whose stop line and P&L are minutes old.
- `engine_hb_ns` and `gateway_hb_ns` already exist in the table (`table.py:44-45`) but are never sent to the browser. `gateway_hb_ns` is written only inside the per-client tick loop (`gateway.py:98-101`) and nothing reads it.

**2. The gold "fire" verdict is recomputed in the browser and ignores the engine's blocks. MEDIUM.** Locations: `app.js:114-123`, `157`.
- `corners()` decides `closed` from `domino.z / m_star`, `S / s_star` and `late`.
- `renderVerdict` sets `.verdict.fire` (gold glow; the CSS reserves gold for "trigger near or firing") whenever `closed` is true.
- It does this even when the engine's `reason` is "outside entry window", "already traded this episode", "DATA GAP…", "episode began in a data gap", or a gate veto (`paper.py:146-186`).
- The Triangle's eye and spiral (`drawTriangle`) also glow from the same browser-side maths.
- Result: you can get gold, glowing text reading "Already traded this move." or "Blocked by a learned rule". The visual says go while the words say no.
- If the champion becomes `straddle_spike` or a `gap*` variant, the Triangle shows the wrong trigger entirely.
- *Verified by reading* (not reproduced live). Fix: the engine should publish `fire_ready`/`blocked_by`, and the UI should render it instead of re-deriving it.

**3. The key seller-state signal is cut off at common laptop widths. MEDIUM.** Locations: `style.css:96` (`.leg .meta { white-space:nowrap; overflow:hidden }`), `app.js:203,206`.
- *Verified* in a 1366×768 screenshot: CE legs show "h", "re", "d" instead of hold/refill/drain, and "book→p…" is cut off.
- That is exactly the signal the panel legend calls "the run you are waiting for".
- At the same size, the Paper-position panel starts at y=710 of 768, so open-trade P&L and stop are below the fold.
- Document height is about 2,700 px, with about 470 numeric tokens in DOM text plus 5 canvases.

**4. Explanations are destroyed every 250-350 ms. MEDIUM.** Locations: `app.js:164-168` (advisors), `529-534` (heavyweights), `203/206` (ladder meta), `570` (tape).
- Each state message rebuilds these by `innerHTML`.
- *Verified*: the same `#advisors li` and `#ev li` node is not identical one second later.
- Each advisor's `why` exists only in a `title=` tooltip. Browser tooltips need about 0.5-1 s of stable hover, so they flicker away or never appear. The reason an advisor vetoed is effectively unreadable.
- Text selection and copying from the tape are also broken.

**5. Colour semantics are inconsistent and sometimes inverted. MEDIUM.**
- *Ladder and Straddle* (`style.css:131`): CE = green, PE = coral.
- *OI map* (`app.js:321-322`): **put OI is green and call OI is coral**.
- *Force line* (`app.js:345`): VACUUM/BREAK-IMMINENT/BROKE are always green ("up") and HOLD-STRONG is always coral. It ignores `force.dir`, which the engine publishes (`levels.py:199`). Breaking a *support* in a down move is painted green, the bullish colour.
- *Big price colours* (`app.js:63-68`): the flash class is re-added on every tick. Under steady ticks it becomes permanent, so the 30 px futures price is coloured by the last tick, not the day.
- *Verified* in a screenshot: futures shown green at 25,031.85 next to a coral "−207.20 (−0.82%)".
- Green/coral is also the only carrier of meaning in several places, which is risky for red-green colour blindness.

**6. Per-tick forced reflow; render cost on the main thread. MEDIUM in sim, probably LOW live.** Location: `app.js:66`.
- `void el.offsetWidth` forces a layout on every changed price.
- *Measured* (headless, software rendering, sim at 30×, about 1,600 ticks/s): `onTick` took **30-41 % of main-thread time** (3.0-4.1 s per 10 s).
- `render()` took about 48-69 ms per call at about 3 Hz, and there were 82 long tasks (>50 ms, worst 170 ms) in about 15 s.
- The Triangle's requestAnimationFrame loop fell to about **4.5 fps**.
- Live Breeze tick rates are far lower, so treat this as an upper bound. Still, a busy expiry morning on a laptop is where it would bite.
- Fixes:
  - Coalesce ticks per `requestAnimationFrame`, keeping the latest value per id.
  - Use the Web Animations API, or toggle between two classes, instead of reflow.
  - Diff state before using `innerHTML`.

**7. Silent failures in the gateway and the WebSocket client. LOW.**
- `gateway.py:103-106` swallows every exception and returns. A serialisation bug becomes a silent close-and-reconnect loop every second (`app.js:46,74`, with no backoff).
- `app.js:73` logs JSON errors only to the console.
- `StateBlob.write` silently drops a state larger than 2 MB (`table.py:165`). I measured 25 KB, and the series is capped at 720 points, so this is a latent issue, not a live one.

**8. Accessibility. LOW.**
- There are no `aria-live` regions (0 found), so entries and exits are not announced. The verdict is the obvious candidate.
- None of the 5 canvases has a text alternative.
- Contrast is fine: mist on panel is 5.4:1 and coral is 5.7:1.
- Fonts come from Google Fonts. If that fails (it was blocked in my sandbox), the canvas text falls back silently, which is acceptable.

**9. Smaller points. LOW.**
- "Together" means two things. The ladder header shows `K_up`/`K_dn` (hero coherence), while the Triangle shows `S_up`/`S_dn` (basket synchrony). I saw "together up 0% down 10%" next to "Together 0% of 50%".
- On the OI map, the "max pain" and "spot" labels overlap when they are at the same strike (seen in the screenshot).
- The Books panel sizes bars by points but labels them in rupees (`app.js:556-559`). Under compounding the two can disagree in sign.

## Good things
- **A sound process split.** The gateway computes nothing, and each WebSocket client gets its own diff loop driven by seqlock (`gateway.py:82-97`). A slow tab only slows itself, and reconnecting resends a full snapshot (`sent` is zeroed).
- **The `wsproto` choice is documented with its reason** (`gateway.py:139-146`).
- **Reasons are written in plain language.** `humanReason()` (`app.js:125-142`) turns engine reason strings into trader English ("Push is 0.8 of the 2.0 needed."), and blackout gaps are shown in the header (`app.js:94-97`).
- **Honest framing throughout.** The UI says "paper · simulated market", the GEX panel carries the caveat "Assumes dealers are long calls…; shown as evidence only", and the books panel says "Changes happen only after the close" (respects I-11).
- **The straddle watch is well thought through.** It uses a fixed strike rather than the jumping ATM, draws a theta-only reference path, marks ATM rolls, and lays out labels to avoid collisions (`app.js:436-521`).
- **Good canvas basics.** Canvas sizing respects DPR (`fit()`), and `prefers-reduced-motion` is honoured.
- **Controls and the lead book are visibly separated** from the lead book (`.book.ctl` in italics, champion in gold).

## Ideas from GitHub
1. **pladaria/reconnecting-websocket.** https://github.com/pladaria/reconnecting-websocket. Licence: MIT.
   - Source: `reconnecting-websocket.ts`, which provides jittered exponential backoff (`minReconnectionDelay` 1-5 s, growth ×1.3), a `connectionTimeout`, and open/close/error events you can listen to.
   - How it maps onto Apex: a **dashboard tool**. Replace the bare `setTimeout(connect,1000)` (`app.js:46,74`) and drive a "DISCONNECTED / STALE" banner from the close and timeout events.
   - Pair it with an `engine_age_ms` field (from `engine_hb_ns`) added by the gateway to every `/ws/state` frame, plus a 1 Hz heartbeat frame even when nothing changed.
2. **leeoniya/uPlot.** https://github.com/leeoniya/uPlot. Licence: MIT.
   - Source: `demos/sine-stream.html` and `sparklines.html`, a streaming time series in a few KB with a very low per-update cost.
   - How it maps onto Apex: **a dashboard tool**. Replace the hand-drawn `drawTrace`/`drawStraddle`/`drawPosLine`. You get a time axis, a hover cursor showing exact values, and much cheaper redraws than rebuilding the whole canvas on each state message.
3. **tradingview/lightweight-charts.** https://github.com/tradingview/lightweight-charts. Licence: Apache-2.0.
   - Source: `plugin-examples/src/plugins/` (`session-highlighting`, `user-price-lines`, `vertical-line`, `partial-price-line`) and the accessibility plugin (now the `lwc-plugin-accessibility` package).
   - How it maps onto Apex: **a dashboard tool**. The futures trace maps directly: episode shading becomes session-highlighting, entry/stop/"move began" become price lines, and ATM rolls become vertical lines. The accessibility plugin covers finding 8 for charts.

## Top 3
1. **Make staleness visible.** The gateway attaches `engine_age_ms` and `feed_age_ms` (from the existing `*_hb_ns`) and sends a heartbeat at least once a second. The browser shows a full-width red "ENGINE STALE n s / DISCONNECTED" banner and greys out the verdict, position and stop once the data is older than 2 s. Use reconnecting-websocket-style backoff. **Size S. Before Monday.**
2. **Make the engine the only source of "go" truth.** Publish `entry_ready` and `blocked_by` (the champion's `evaluate_entry` result *before* the time-window, blackout and fired checks, plus the actual blocker). Gold and glow happen only when the engine says entry is possible. The Force colours use `force.dir`, the OI map uses the CE/PE palette, and big prices are coloured by day change, not last tick. **Size S-M. Before Monday.**
3. **Cut churn and overload.**
   - Batch ticks per animation frame and drop the forced reflow.
   - Diff-render the advisors, tape and ladder, and move each advisor's `why` into visible text on the veto chip.
   - Stop the ladder from clipping its signal: wrap the meta row, or drop delta/IV first.
   - Add a compact "decision strip": verdict, position P&L, stop distance, staleness. It stays in the sticky header, so it is visible at 1366×768.
   - Move the deep-dive panels (GEX, books, straddle table) to a second tab.

   **Size M. Later.**
