# Designer 1: Visual hierarchy and attention

## 1. Critique: the position loses the first glance

In `before_pos_fold.png` the eye goes through the page in this order:
1. **The glowing gold triangle** (canvas with a radial beacon glow, top-left, about 500 px square). It is the largest, brightest and warmest thing on the page.
2. **The solid white ATM chip "25150"** in the ladder (`.lad .k.atm { background: var(--ink) }`). It is the only light-filled block on a dark page, so it has the highest luminance contrast anywhere.
3. **Ten 24 px green/coral prices** in the hero ladder (`.leg .px 700 24px`), the 30 px Nifty futures price, and the 24 px ₹1,00,000 in the header.
4. Only after that comes **the position**: `#pos .big` at 34 px, sitting in grid row 2 (`"vortex pos trace"`) at y≈735 of a 1000 px viewport. Its sparkline is cut off by the fold.

Specific failures:
- **Size does not set it apart.** The P&L is 34 px against twelve other numbers of 24 to 30 px. A ratio of 1.15 to 1.4× is too small to register before attention. A hero number needs at least 2× the next number.
- **Position is wrong.** The position sits in the lower-middle of the screen, below a 570 px ladder. On an F-pattern scan the top band and the top-left corner are read first.
- **Colour means two things.** `.what` is coloured `down` because the contract is a PE (`p.rr === "CE" ? "up" : "down"`). In `before_pos_panel.png`, "Long … 25200 PE" is coral while the P&L is green. Coral means both "put" and "losing", so at a glance a winning PE looks like a loss.
- **It appears twice.** The verdict line ("Holding 25200 PE, −0.90 points", 22 px) repeats the P&L in a second location, and the two compete.
- **Risk is a bare number.** "Stop at futures 25,232.0" makes the trader do subtraction to see how close the stop is. The trail state is the word "Trailing" in mist. Proximity to an exit, the thing that matters most during a hold, has no visual form.
- **The header ignores the open trade.** The header shows "₹1,00,000 / ₹0 today" while the trade is down ₹1,462, so the top-right says "nothing is happening".
- **The ladder's held marker is weak.** `.leg.held` is only a 1 px ink border, the same weight as `.leg.hot` (and weaker than it, since hot also glows).

## 2. Proposal: one full-width position band, always in row 1

**Grid (≈1500 px).** Add a `pos` band across all three columns directly under the sticky bar, and move the hero ladder below Straddle watch:

```
"pos      pos      pos"
"vortex   straddle straddle"
"vortex   trace    trace"
"oimap    ladder   ladder"      <- hero contracts now below straddle
"oimap    heavy    heavy"
"books    trades   trades"
"books    tape     tape"
```

The band is always in this slot and only its height changes, so the page never rearranges itself on entry.

**FLAT (quiet):** a 44 px strip with `var(--mist)` text at 14 px and no fill colour. Content: `Flat · ₹1,00,000 ready · 0 trades today` on the left and the `blackout` text on the right if entries are paused. No large numbers and no tint. It reads as a status line.

**OPEN (dominant):** about 168 px tall. A 4 px left rule and a background tint of `rgba(up|down, .07)` follow the **sign of the P&L**, never the option type. Read order, left to right:

1. **Identity**, 18 px Chakra 600 in ink: `LONG 25200 PE` with an outlined CE/PE tag (a 1 px border in up or down; the text stays ink). Below it, in mist at 13 px: `25 lots · exp 19 Oct · in 09:25:04 · 6m 12s`.
2. **Rupee P&L, 64 px Chakra 700**, tabular, `--up`/`--down`, always with a sign glyph: `−₹1,462`. This is the only number on the page above 30 px.
3. **Points and return**, 26 px on the same baseline: `−0.90 pts  −1.5%`.
4. **Exit rail**, about 420 px wide. A horizontal track in futures points: stop on the left, entry tick, best tick, live dot. Above the track: `6.2 pts to STOP` (ink). When the trail is on, the stop marker becomes `TRAIL` and moves with it. The rail stays neutral (`--shelf`) until the live dot is within 30% of the stop distance. Then the gap segment and the label switch to `--beacon`, the one colour reserved for "something is about to fire".
5. **Detail column**, mist at 13 px with ink values: `Bought 60.00 · Now 59.10 · Best +4.90 · Fut in 25,220.0`. The P&L sparkline moves here at 40 px tall.

**Demote everything that competes while a position is open** (`body.inpos`):
- Hide the verdict's P&L. The verdict reads "In a trade." at 15 px in mist.
- Dim the triangle canvas to 45% opacity and drop its glow. No entry can fire, so it is background.
- Turn the ATM chip into an outline (`border: 1px solid var(--ink)`, transparent fill), on all pages.
- Ladder prices change from 24 px to 20 px. The held leg gets a 2 px border in the P&L-sign colour plus a "HELD" label.
- The header capital shows marked-to-market capital (`₹98,538 marked`). The day P&L includes the open MTM.

**Entry:** the band grows (200 ms height ease; instant under `prefers-reduced-motion`) and its border pulses `--beacon` once over 600 ms, then settles. That is the only motion the band ever makes. The P&L does **not** use `flash-up/down` per tick, and its text updates at most 4× a second.

**Exit:** for 60 s the band shows `CLOSED · TRAIL · +₹2,925 +1.80 pts` in ink with the reason as a chip (STOP, TRAIL, THESIS-VOID, BOOK, TIME), with no tint. It then collapses to the flat strip and the trade appears in Today's trades.

**Stale:** keep the existing grayscale/0.55 treatment. In addition, overlay a stamp at the P&L's top-right in 13 px white on `#b3261e`: `FROZEN 7 s · last 09:31:12`. Also replace "to STOP" with "stop unknown while frozen". The stale state is then readable in text, not only through loss of colour.

## 3. Constraints I would insist on

- **One loud thing.** At most one element above 30 px and at most one tinted panel at any time. Beacon is used only for near-stop/trigger.
- **Never colour alone.** Every P&L carries `+`/`−`. Stop proximity is stated in words and numbers. CE/PE is a text label, not a hue.
- **Contrast.** Ink on the tinted band stays ≥ 7:1, and mist detail stays ≥ 4.5:1 on `--deep`.
- **Long holds.** No looping animation, no blinking, no per-tick flashing on the band. A trader watches it for 30 minutes, and anything that moves continuously turns into noise.
- **Palette and fonts unchanged.** Use the existing tokens (`--up --down --beacon --mist --ink --shelf`), Chakra Petch for numbers, Barlow for text. No new hues.
- **Nothing hidden.** The futures trace (with its stop line) stays in the first viewport next to the band. The stale banner stays above the band. At 1280/820 px the band stays first in the grid order.
- The band has `aria-live="polite"` for entry/exit/stale changes only, never for tick updates.

## 4. Wireframe (OPEN, 1500 px, first viewport)

```
┌ bar: ApexOptions | Nifty fut 25,219.75 | Spot VIX IV Clock | ₹98,538 marked  −₹1,462 today | feed ┐
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│▌LONG [25200 PE]          −₹1,462   −0.90 pts −1.5%      STOP ●────────|entry──◆best         Bought 60.00│
│▌25 lots · exp 19 Oct                                       6.2 pts to STOP      [trail off]     Now 59.10   │
│▌in 09:25:04 · 6m 12s     (64px)    (26px)                                       Best +4.90  ~~~sparkline~~│
├──────────────────────────────┬─────────────────────────────────────────────────────────────────────┤
│ triangle (dimmed 45%)        │ Straddle watch                                                       │
│ "In a trade."  (15px mist)   ├─────────────────────────────────────────────────────────────────────┤
│ advisors                     │ Futures, last 5 min (stop / entry lines)                             │
├──────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
│ Where the walls are          │ Ten hero contracts (HELD leg outlined, ATM chip outlined)            │
```

FLAT: the band becomes `Flat · ₹1,00,000 ready · 0 trades today` (44 px, mist), and the triangle returns to full strength as the page's lead element.
