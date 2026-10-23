# Designer 3: colour, contrast and accessibility

All ratios below are WCAG 2.x, computed from the `:root` tokens in style.css. Sections sit on `rgba(10,37,50,.78)` over `--abyss`, which composites to **#09222e**. I call that "panel" below.

| token | on panel | on --shelf |
|---|---|---|
| --ink #dbeaf0 | 13.3 | 10.1 |
| --mist #7c9cab | 5.6 | 4.3 (fails 4.5 at 12–13 px) |
| --up #3ddc97 | 9.3 | 7.0 |
| --down #ff6b5e | 5.9 | 4.5 |
| --beacon #ffc24b | 10.2 | 7.7 |
| stale mist (grayscale, opacity .55) | **2.6 (fails)** | – |
| white on stale banner #b3261e | 6.5 | – |

`--up` against `--down` is only 1.58:1 in luminance. I simulated colour-blind vision (Machado model, full severity). Under deuteranopia, up becomes #c6bd9b and down becomes #b6a75a: two khaki shades, ΔE about 25, luminance contrast 1.29. Protanopia is similar (ΔE 26). Under deuteranopia, down (#b6a75a) also drifts towards beacon (#e9d250). So on the futures trace, the "stop" line and the "move began" line are hard to tell apart.

## 1. Critique (before_pos_fold.png, before_pos_panel.png)

1. **The colour of the instrument is fighting the colour of the result.** `renderPos` paints the contract line `.what` with `p.rr === "CE" ? "up" : "down"`. The page uses `--down` as the "puts" colour too (`/* puts / falling */`). So a PE always has a coral title. In before_pos_panel.png a *winning* PE shows a coral "Long 25 lots Nifty 25200 PE" above a green "₹2,925 +1.80 pts". A losing CE would show green above coral. Red and green carry two different meanings within 40 px of each other, and the eye can't tell which one is the verdict.
2. **The win/loss signal relies on hue alone.** Only the 1-character "−"/"+" and the hue show win versus loss, and for about 6% of men that hue is khaki versus khaki. The P&L sparkline (`drawPosLine`) has the same problem: same shape, only the stroke hue flips.
3. **Too many competing saturated numbers.** At the fold there are:
   - a green 30 px futures price;
   - ten 24 px ladder prices that `paintPx` flashes green/coral on *every tick* (320 ms);
   - a 22 px coral "Holding 25200 PE, −0.90 points" in `#verdict`, which duplicates the P&L;
   - the coral `−17.15` change;
   - green/coral advisor dots.

   The 34 px P&L is the largest number, but it isn't the loudest. Motion and repetition beat size.
4. **Stale mode makes the position unreadable.** `body.stale #pos {filter: grayscale(1); opacity:.55}` drops text to about 2.6:1. That happens at exactly the moment the user most needs the last known P&L and stop.
5. **How close the stop is never gets a colour.** "Stop at futures 25,232.0" is 13 px `--ink` inside `--mist` text. The user has to subtract it from the futures price in their head. "Trailing" is plain text.
6. **Flat is fine** (mist, 20 px), and it should stay that quiet.

## 2. Proposal

**Placement.** When a position is open, the panel moves to row 1, beside the triangle. The hero ladder drops below Straddle watch:

```
"vortex pos      trace"
"vortex straddle straddle"
"oimap  ladder   ladder"
"oimap  heavy    heavy"
"books  trades   trades"
"books  tape     tape"
```

When flat, the panel stays in the same cell but compresses: no hero number, `--mist` only. I'm not proposing a layout jump between states, because a layout jump is itself an attention event.

**Colour rule: inside the position card, red and green mean only P&L.**
- The contract identity becomes a neutral chip: `--ink` text on a `--shelf` fill (10.1:1), reading "25200 PE ▼ bearish" or "25200 CE ▲ bullish". The arrow and the word carry the side, so no hue is needed. The CE/PE colours stay as they are in the ladder, OI map and straddle panels, where they mean "calls/puts" and nothing else.
- The P&L hero number is **52 px Chakra Petch 700, tabular-nums**:
  - Format: sign glyph, then rupees, then points (`▼ −₹1,462 · −0.90 pts`), with the glyph always present (▲ for profit, ▼ for loss, ● for flat at 0).
  - Text colour is `--up` (9.3:1) or `--down` (5.9:1). Both pass AAA for large text.
  - Redundant cue 1: the card's left edge gets a 6 px solid bar for profit and a 6 px **diagonal-hatched** bar for loss (`repeating-linear-gradient`). That gives a shape difference with no hue.
  - Redundant cue 2: a 12 px label "IN PROFIT" or "IN LOSS" sits above the number.
  - Tint the card background only faintly (`--up`/`--down` at 6% alpha). Keep text contrast at 5.9 or better.
- Under the hero number, on one 15 px row in `--ink`: Bought 60.00 · Now 59.10 · Best +4.90 · Return −1.5% · In 4m 12s. Use "Now" rather than "Last".

**Stop / trail proximity, drawn as a bar rather than a number to subtract:**
- A 10 px horizontal track on `--shelf`, from the stop (left) through entry to best (right). A marker shows current futures.
- Caption: "**4.8 pts to stop** (25,232.0)" in 15 px `--ink`.
- Colour states:
  - more than 50% of the stop distance remaining: track and marker in `--mist`;
  - 25–50%: marker in `--beacon` ("trigger near" is exactly what that token is reserved for);
  - under 25%: the 1 px card border also turns `--beacon`, and the caption text changes to "**Near stop**".

  The change comes from text plus border, never from hue alone.
- When trail is on, the stop end of the track gets the word "TRAIL ▸" plus a solid notch. The notch moves rightwards as the trail ratchets.
- The trace's stop line should be **dashed `--down` plus the label "stop"**. The "move began" line should be **dotted `--beacon`**. Different dash patterns keep the two apart under deuteranopia.

**Calming the competition while in a position:**
- `#verdict`: replace the coloured duplicate with one `--mist` line, "In a trade. See position."
- `paintPx` flashes: keep them only on the held leg. For other legs, while `s.pos` is set, swap the colour flash for a 1 px ink underline.
- Header `#fut` stays `--ink`. Only `#futchg` carries colour.

**Entry:** the card border pulses `--beacon` twice over 1.2 s, then settles. Respect `prefers-reduced-motion` (no pulse; the border stays beacon for 5 s). **Exit:** for 60 s the card shows the result in neutral `--ink`: "Closed · TRAIL · +₹2,925". The reason appears as a word chip (STOP, TRAIL, THESIS-VOID, BOOK, TIME), and only the rupee figure is coloured. Then it fades to flat.

**Stale:** do not grayscale or fade the card. Instead:
- turn every number `--ink` (13.3:1), removing the green and red;
- set a 2 px dashed `--mist` border;
- prefix a 13 px label "FROZEN 7 s, last known".

The number stays readable. The missing colour and the dashed border say it is unreliable.

## 3. Constraints I would insist on

- Any text in the card at 4.5:1 or better. Hero numbers at 3:1 or better (they reach 5.9 or more). No `--mist` text on `--shelf` below 14 px (4.3:1).
- **No P&L state is carried by hue alone.** Each one has a glyph (▲▼), a word, and a pattern (hatched versus solid).
- Red and green mean one thing per panel. Beacon is for "stop near / entering" only.
- No looping animation during long holds. The only motion is a one-shot pulse on entry and on crossing a threshold, and `prefers-reduced-motion` is honoured.
- Fonts stay Chakra Petch for numbers and Barlow for words, with no new tokens apart from the 6% alpha tints.
- The stale banner (6.5:1) is kept, and staleness must never lower legibility.

## 4. Wireframe (open, losing)

```
┌▒─ Paper position ─────────────── exp 2026-10-19 · in 09:25:04 ┐
▒  [ 25200 PE ▼ bearish ]  25 lots                    IN LOSS     │
▒  ▼ −₹1,462   −0.90 pts                         (52px, --down)   │
▒  Bought 60.00 · Now 59.10 · Best +4.90 · −1.5% · 4m 12s         │
▒  STOP 25,232 |====●=======entry========best|   4.8 pts to stop  │
▒  ~~~ P&L sparkline (stroke + hatched fill below zero) ~~~       │
└▒────────────────────────────────────────────────────────────────┘
 ▒ = hatched loss bar; solid bar when in profit
```

Flat: `Flat · ₹1,00,000 ready` in 20 px `--mist`, with no bar, no tint and no chart.
