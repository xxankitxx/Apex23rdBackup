# Designer 5: page layout and information architecture

## 1. Critique

**The position has no slot of its own in the grid.** In `style.css` it sits in the second row: `"vortex ladder ladder" / "vortex pos trace"`. It shares that row with the futures trace and gets 4/13 of the width. The ladder ("Ten hero contracts") takes the whole first row of the right side, which is about 560 px tall. In `before_pos_fold.png` the panel title starts at y≈760. The −₹1,462 sits at y≈826, below about 30 ladder numbers that are larger and brighter (premiums like 94.90 and 123.30 are set at about 26 px). The eye reaches the ladder, the triangle and the advisor chips before it reaches the position.

**The P&L appears in three places, and they disagree.** At the same moment the page shows:
- the header money block: `₹1,00,000` and `₹0 today, 0.00 points` (`app.js` l.144–145 shows only `s.book`, which is realised P&L);
- the triangle's verdict line: `Holding 25200 PE, −0.90 points` at 22 px (l.289, which overwrites the verdict);
- the panel itself: `−₹1,462 −0.90 pts` at 34 px.

So the biggest money number on the page says nothing is at risk, while the real figure is lower on the page and smaller. That is an IA error, not a styling one.

**The header bar wraps and costs height.** `.bar` is `flex-wrap: wrap`. In the position screenshot, "+1.72 in 5m" pushes "Sound off" onto a second line. The sticky bar grows from about 88 px to 125 px, and that height comes out of the fold exactly when a position is open.

**Flat and open use the same layout.** When flat, the "Paper position" box still takes a prime cell to say only "Flat" (`before_flat_fold.png`, y≈700). It is quiet but in the way, and the layout never changes when a position opens.

**Ladder vs straddle.** Straddle watch is the panel that produces the entries (the champion is `straddle_spike`), yet it sits at y≈1150 in `before_pos_full.png`, below the fold. The ladder, which is reference material, gets the top row.

## 2. Proposal: two grid states, switched by one body class

`renderPos` toggles `document.body.classList.toggle("holding", !!s.pos)`. The CSS swaps `grid-template-areas`. Panels never change their internals between the two states. Only their placement changes.

**FLAT (default).** The position is demoted, and the ladder moves below straddle as the owner asked:
```
"vortex   straddle straddle"
"vortex   ladder   ladder"
"pos      trace    trace"
"oimap    heavy    heavy"
"books    trades   trades"
"books    tape     tape"
```
The vortex column (about 1,000 px) now sits beside straddle plus ladder (about 1,080 px), which is a better height match than today. Above the fold at 1500×1000: the header, the triangle with its verdict, the full straddle chart and legs, and the top of the ladder. The flat `pos` card is one quiet line in `--mist` at 15 px: "Flat · ₹1,00,000 ready · 2 trades today, 1 won". It has no large type.

**HOLDING.** The position takes a full-width first row:
```
"pos      pos      trace"
"vortex   straddle straddle"
"vortex   ladder   ladder"
"oimap    heavy    heavy"
"books    trades   trades"
"books    tape     tape"
```
- **The `pos` card is 9/13 wide and about 230 px tall.** The trace stays beside it because it already draws the entry and stop lines (l.320); it is the position's chart.
- **Order of content, left to right:**
  1. Rupee P&L at 52 px in `--num`, coloured `--up` or `--down`, with points under it at 20 px.
  2. The contract ("Long 25 lots · 25200 PE · 19 Oct") at 17 px in `--ink`. The CE/PE colour moves to a small tag, so red no longer means both "put" and "loss".
  3. Bought 60.00 / Now 59.10 / Best +4.90 / Return −1.5% / In 3m 40s.
  4. A stop-distance track: the futures stop … futures entry … futures now, with "12.0 pts to STOP". The marker turns `--beacon` inside 3 pts. When `trail` is on, the track relabels to TRAIL.
- **Fold:** At 1500×1000 the whole strip, the trace, and about half of straddle watch are visible. On a 1366×768 laptop (still three columns) the strip and the top of straddle are visible. The P&L is the first large number under the header in both cases.
- **≤1280 px:**
  - holding: `"pos pos" "vortex trace" "straddle straddle" "ladder ladder" "oimap heavy" "trades trades" "books tape"`
  - flat: `"vortex trace" "straddle straddle" "ladder ladder" "pos heavy" "oimap trades" "books tape"`
- **≤820 px:** a single column with `pos` first only when holding.

**One P&L number, reconciled with the header.** The large P&L lives only in the strip. The header money block is driven by the same `ltp` in `livePos` and ticks with it:
- Holding: label "Equity", value `₹98,538` (capital + open) in `--ink`. The sub-line reads `−₹1,462 open · ₹0 realised · ₹97,500 in trade` (entry × qty), with only the open figure coloured.
- Flat: back to "Paper capital ₹1,00,000 / ₹0 today".

While holding, the vortex verdict stops repeating the P&L. It returns to the triangle's own sentence, prefixed in `--mist` with "Holding 25200 PE · ".

**Scrolling away.** An IntersectionObserver on `#pos` shows a compact chip in the sticky bar when the strip is off-screen: `25200 PE −₹1,462 · 12 pts to stop`. It sits in the slot freed by fixing the wrap. The bar gets `flex-wrap: nowrap`, fixed-width `dd`s, and "Sound off" moves into the brand group.

**Entry and exit.** On entry the grid reflows once, deliberately, with no animation (`prefers-reduced-motion` is already honoured). The page never scrolls on its own. If the user has scrolled down, the sticky chip shows the position instead. On exit, the strip stays in place for 60 s as a result card ("Closed · TRAIL · +₹3,120 · 4m 10s") in `--mist` with the result coloured, and then the grid returns to flat. That way the layout never jumps under a reading eye at the moment of exit.

**Stale.** The layout does not change. The strip keeps its slot and size and takes the existing `body.stale` greyscale. The strip adds "last good 09:25:44" so a frozen number cannot pass for a live one. The header Equity shows "—" and not a stale figure.

## 3. Constraints I insist on
- One large P&L figure on the page. Every other mention is smaller and derived from the same tick.
- The flat state never uses type larger than 20 px or any saturated colour in the `pos` cell.
- Reflow happens only on entry, on the deferred exit, and at breakpoints. It never happens on a tick or on stale.
- No new colours. Use `--up`, `--down`, `--beacon` (stop proximity only, per its own comment), `--ink` and `--mist`. Stay with Chakra Petch and Barlow.
- The text and markers carry the colour meaning, so it works without colour ("−", "to STOP").
- Nothing critical leaves the fold when holding. The stale banner stays as the first row of the sticky bar, above everything.

## 4. Wireframe (holding, 1500×1000)
```
┌ ApexOptions · Nifty fut 25,219.75 · Spot · VIX · IV · Clock │ Equity ₹98,538  −₹1,462 open · ₹0 realised │ ● Live ┐
├───────────────────────────────────────────────────────────┬─────────────────────────────┤
│ −₹1,462                  Long 25 lots · [PE] 25200 · 19 Oct │ Futures, last 5 min         │
│ −0.90 pts  (−1.5%)       Bought 60.00  Now 59.10  Best +4.90│  ---- stop 25,232           │
│                          In 3m 40s  · Trail off             │  ‥‥ entry 25,220            │
│ STOP 25,232 |=====●=========| entry 25,220   12.0 pts to stop│                             │
├──────────────────────┬────────────────────────────────────┴─────────────────────────────┤
│ triangle             │ Straddle watch  (chart + CE / PE legs)                            │
│ (verdict, advisors)  │ ─────────────── fold ────────────────────────────────────────────│
│                      │ Ten hero contracts                                                 │
```
