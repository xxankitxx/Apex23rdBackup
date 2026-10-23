# Designer 2 — the trader's workflow

A buyer holding a weekly option asks five questions in a fixed order, every glance: **Am I up or down? How far is the stop? Is the trail armed? How long have I been in? What exits me next?** Pro terminals (the positions blotter in a broker terminal, a prop desk's "risk strip") answer them left to right on one line. They put the stop distance next to the P&L, because a P&L number with no distance to the stop doesn't tell you how much risk is left.

## 1. Critique

- **Placement buries it.** `grid-template-areas` puts `pos` in row 2, column 2 (`"vortex pos trace"`). In `before_pos_fold.png` the panel starts at y≈735 and is cut off by the fold. The ladder (`ladder ladder`, ~570 px tall, ten 24 px prices, coloured bars, a white ATM tile) and the 600 px triangle canvas take the whole first screen. The brightest object above the fold is the ATM strike tile, not my trade.
- **The P&L is the wrong size for what it is.** `#pos .big` is 34 px. `.q-px` (futures) is 30 px, and the ladder `.leg .px` prices are 24 px, ten of them. The P&L is one of a dozen large numbers.
- **The stop is a level, not a distance.** `renderPos` prints `Stop at futures 25,232.0` next to `Futures in 25,220.0`, so I have to do the subtraction myself while futures sit at 25,219.75. The futures trace has a dashed `stop` line, but it lives in a different panel.
- **Trail state is invisible when off.** `$("postrail").textContent = p.trail ? "Trailing" : ""`. A blank space can mean "not armed" or "not rendered", and I can't tell which.
- **No elapsed time.** `poshint` shows `in at 09:25:04`, a clock time, so I have to work out the duration in my head. There is also nothing about the TIME or THESIS-VOID exits.
- **The header contradicts the panel.** `#cap` says ₹1,00,000 and `#daypnl` says "₹0 today" while I'm −₹1,462 open (top right of `before_pos_fold.png`), so the most prominent money figure on the page ignores the trade.
- **The duplicate is in the wrong place.** The verdict line `Holding 25200 PE, −0.90 points` is the best-placed text, but it shows points only, in 22 px, under a decorative canvas.
- **When flat**, "Flat" at 20 px mist inside a full panel is fine in tone but takes up a prime slot for nothing.

## 2. Proposal

**A position strip spans the full width directly under the sticky bar** (new grid row `"pos pos pos"` at the top of `main`). It exists only when a position is open. The old `pos` cell is removed. In its place, `trace` widens (`"vortex trace trace"`), because the futures chart with its stop line is the natural companion.

**Grid (open):**
```
"pos pos pos"
"vortex trace trace"
"vortex straddle straddle"
"oimap ladder ladder"      <- hero contracts now BELOW straddle watch
"oimap heavy heavy" ...
```
**Grid (flat):** the same, without the `pos` row. The page jumps by about 96 px on entry, and that jump is itself the entry signal.

**Strip contents, left to right (order = the five questions):**
1. **Contract**: `LONG 25 × 25200 PE · 19 Oct`, 17 px `--num`, in `--down` for PE and `--up` for CE (as now).
2. **P&L**: `−₹1,462`, 44 px 700 `--num`, the largest number on the page (futures stays at 30). Beside it in 20 px: `−0.90 pts · −1.5 %`. Coloured by `tone()`.
3. **Stop distance meter**: a horizontal track 220 px wide. The left end is the stop, the right end is the futures entry or best, and a marker shows where futures is now. The label reads `12.3 pts to stop`. Track `--shelf`, fill `--mist`. The fill turns `--beacon` when less than 30 % of the initial distance remains, and that is the only use of beacon (consistent with the token's comment, "trigger near or firing"). Under 10 % it adds a 1 px beacon border on the whole strip, with no pulsing.
4. **Trail chip**: always rendered. `TRAIL off` (mist outline) or `TRAIL armed @ 25,214` (`--up` outline, plus the trailing level). It never disappears.
5. **Time in trade**: `in 04:12` as a running mm:ss counter, 16 px, with the entry clock in mist beneath. If the engine exposes a TIME deadline, it shows `time-exit 15:15` (or the countdown), mist by default and beacon in the last 2 minutes.
6. **Next exit**: one line in mist, `Next exit: STOP at 25,232.0 (12.3 pts)`, naming whichever exit is nearest (STOP / TRAIL / TIME). THESIS-VOID and BOOK appear only when they are armed or close.
7. **The small P&L sparkline** (`#posline`), 160×40, at the far right, showing shape, not detail. Best `+4.90` sits under it.

The strip background is `--deep` with a 4 px left border in the P&L tone, at 96 px height. No glow, no animation on tick: digits change and nothing else moves.

**Header capital while open:** `#cap` shows the live mark-to-market (`₹98,538`) with `open −₹1,462` underneath, so the header and the strip never disagree.

**Ladder:** keep `.leg.held`, but use a 2 px border in the position's tone so the held contract can be found among the ten.

**Entry:** the strip appears and the existing sound plays (if on). A one-time 600 ms background fade from beacon at 15 % alpha to `--deep` makes the entry noticeable without being loud.

**Exit:** the strip stays 20 s as a receipt (`CLOSED · TRAIL · +₹2,925 · held 06:40`, with the tone border at 50 %), then collapses. The trades table already holds the record.

**Stale:** the strip stays in place and is never hidden, because I still own the position. The numbers go mist, grayscale at .55 (extend the existing `body.stale #pos` rule to the strip), and the stop meter is hatched. A `PRICE STALE · last 09:31:02` label replaces the time counter. The P&L gets a `last known` prefix. Being greyed out is acceptable, but the strip must never show a confident number when the price is stale.

**Flat:** no strip. The header money block carries `Flat · ₹1,00,000 ready` in mist at its current size. The verdict line keeps its current job.

## 3. Constraints I insist on

- **Distance, not just level.** Every stop and trail value is shown as a distance in points with the level beside it.
- **Colour plus a word.** Every state has a text label (`TRAIL armed`, `12.3 pts to stop`, `STALE`), and the meter has a numeric label, so colour is never the only carrier. Contrast stays ≥ 4.5:1 on `--deep`.
- **Calm during long holds.** No blinking or pulsing, no tick flashes on the strip. Beacon appears only near a trigger.
- **The strip never covers the bar.** It sits in the scroll flow under the sticky bar and never overlaps the stale banner, the feed health or the clock.
- **Existing tokens and fonts only:** Chakra Petch for numbers (tabular), Barlow for words.
- **One number, one truth.** Header, strip, verdict and trades table must agree on the rupee P&L.

## 4. Wireframe (open, 1500 px)

```
[bar: Apex | Fut 25,219.75 | Spot VIX IV Clock | Capital ₹98,538 (open −₹1,462) | Feed]
+-------------------------------------------------------------------------------------+
|| LONG 25 x 25200 PE   −₹1,462        STOP |=====o------| ENTRY  [TRAIL off]  in 04:12 |
|| 19 Oct               −0.90 pts −1.5%  12.3 pts to stop           at 09:25:04 /\_/\  |
||  Next exit: STOP at 25,232.0 (12.3 pts) · time-exit 15:15                Best +4.90 |
+-------------------------------------------------------------------------------------+
| triangle / verdict      | Futures, last 5 min (stop, entry lines) ...               |
|                         +-----------------------------------------------------------+
|                         | Straddle watch                                            |
+-------------------------+-----------------------------------------------------------+
| Where the walls are     | Ten hero contracts (held leg outlined)                    |
```
