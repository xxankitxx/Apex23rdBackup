# Designer 4 — Motion & state changes

## 1. Critique

- **The motion is in the wrong places.** In before_pos_fold.png, things move all the time, and none of them is the position:
  - `flash()` (app.js ~L75) recolours ten 24 px ladder prices on every tick.
  - The Triangle canvas orbits and glows on every frame.
  - The one "orchestrated moment", the entry shock-wave (`flashAt`, L441), is drawn on the Triangle.
- **The headline flickers between red and green.** `livePos` resets `"big " + tone(pts)` on every tick. Near breakeven, the 34 px P&L flips coral and green several times a minute.
- **Danger has no signal.** "Stop at futures 25,232.0" is a 13 px mist row (`#pos .row`). How close the stop is shows up only as a dashed line in another panel (Futures trace). "Trailing" is the same 13 px grey. ARMED makes a sound only if the sound toggle is on.
- **Exit is invisible.** When `s.pos` goes null, the panel turns into "Flat" in the same frame.
- **Stale is half-done.** `body.stale #pos` greys the panel, but `livePos` keeps writing ticks from `/ws/ticks`. The grey number keeps moving. A blackout or data gap shows up only in the header text.
- **Reduced motion is partial.** The CSS media query only removes transitions. The shock-wave, the orbit and the flash class swaps still run.

## 2. Proposal

**Placement.** The position takes a full-width row `"pos pos pos"` directly under the sticky bar.
- When flat, it collapses to a static 44 px mist strip in the same slot: `Flat · ₹1,00,000 ready · last +₹4,210 TRAIL`.
- The grid becomes `"pos pos pos" / "vortex trace trace" / "vortex straddle straddle" / "oimap ladder ladder" / "oimap heavy heavy" / …`. This puts the hero contracts below Straddle watch, as asked.

**Type (open).**
- Contract line: 17 px, CE in `--up`, PE in `--down`.
- P&L in rupees: 56 px/700, with points at 28 px.
- Return % and time-in: 15 px.
- The headline colour uses **hysteresis**. It turns `--up` or `--down` only after P&L has stayed past ±0.5 pt for 3 s. Otherwise it stays `--ink`.

**Stop-proximity rail.** A 10 px bar spans the panel from the stop (left) to the best price (right), with a 2 px `--ink` tick marking "now". The segment from the stop to now is coloured by how much of the stop distance is left, r = remaining ÷ initial distance:

| r | Rail segment | Panel left border |
|---|---|---|
| > 0.5 | `--line` (silent) | none |
| ≤ 0.5 | `--beacon` | none |
| ≤ 0.25 | `--beacon` | 4 px `--beacon`, static |
| ≤ 0.1 | `--beacon` | breathes, opacity .4 to 1, 2.4 s |

The breathing stops once r is above 0.15 again. `--beacon` already means "trigger near"; `--down` stays reserved for loss.

**Trail armed.** One 600 ms `--up` sweep runs along the rail. After that the left border stays 4 px `--up`, with the label "TRAIL ON · locks +x pts".

**Entry.**
- The strip expands to the panel (280 ms).
- The border gives one `--beacon` glow that fades over 1.2 s.
- The beep plays as today.
- An assertive aria-live announcement says "Bought 25 × 25200 PE at 60.00".
- The shock-wave moves off the Triangle.

**Exit.** A result card holds in place for 20 s: "SOLD · TRAIL · +₹4,210 +3.4 pts · held 12 m".
- The left border is `--down` for STOP, `--up` for TRAIL or BOOK, and `--ink` for THESIS-VOID or TIME.
- After 20 s it collapses to the flat strip, which keeps the last result.

**Stale / gap.**
- While `body.stale` is set, `livePos` stops writing, so the panel is frozen.
- A hatch overlay covers the panel (`repeating-linear-gradient`, `--shelf` at .5).
- "FROZEN 14 s — last known" replaces return %.
- The rail's now-tick is hidden.
- A blackout or data gap adds only a mist chip in the panel header: "entries paused · gap".

**Quiet the rest while a position is open.** Ladder flashes apply only to the held contract, and the Triangle stops orbiting and redraws at 1 Hz.

## 3. Constraints

- **At most two continuous animations:** the ≤10% stop breathing and the stale banner. Every other animation is one-shot and lasts ≤1.2 s.
- **`prefers-reduced-motion`, enforced in JS (`matchMedia`):**
  - one-shots become instant state changes
  - breathing becomes a static 6 px border
  - ladder flashes and the Triangle orbit are off
- **Never colour alone:** the rail carries text ("stop 11.8 pts away, 32%"), and the exit card names the reason.
- No breakeven flicker on the headline.
- **Nothing covers other critical information:** never the stale banner or the header capital. The flat strip uses no `--beacon`, `--up` or `--down`.
- **Existing tokens and fonts only;** `--ink` and `--beacon` on `--deep` meet AA.

## 4. Wireframe (open)

```
┌▌──────────────────────────────────────────────────────────────────────┐
│▌ LONG 25 × NIFTY 25200 PE · 19-Oct       in 09:25:04 · 6 m · TRAIL ON  │
│▌ −₹1,462   −0.90 pts   −1.5%      bought 60.00  now 59.10  best +4.90  │
│▌ stop 25,232 ├█████████░░░░░░░░░│░░░░░░░░░░┤ best    11.8 pts away 98% │
└▌──────────────────────────────────────────────────────────────────────┘
 ▌ = state edge: none / beacon ≤25% / breathing ≤10% / up when trail on
[ Triangle ][ Futures trace ........ ][ Straddle watch .............. ]
[ OI map   ][ Ten hero contracts ... ][ Heavyweights ................ ]
```
