# Design council: resolved spec for the Paper position

## Agreed by all five (adopted)
- The position becomes the first row under the sticky bar.
- Red and green inside it mean P&L only.
- The stop is shown as a distance on a rail.
- `--beacon` means only "stop near" or "entry".
- The verdict stops repeating the P&L.
- No looping or per-tick motion during a hold.
- The exit receipt names its reason.
- Stale is stated in words.
- Existing tokens and fonts only.
- Hero contracts move below Straddle watch.

## Decisions on disagreements
- **Open placement:** a full-width row 1 (D1, D2, D4 over D3, D5). It is first in reading order and wide enough for one line.
- **Flat:** a quiet 44 px band in the same slot (D1, D3, D4 over D2, D5). The slot never moves, so an entry does not reshuffle the page.
- **P&L size:** 60 px (proposals were 44 to 64). That is 2× the next-largest number (30 px futures), which is D1's own rule.
- **Header while open:** "Equity" mark-to-market with `−₹1,462 open · ₹0 booked` (D1, D2, D5). One number, one truth.
- **Contract name:** a neutral ink chip with the side in words (D1, D3, D5). Coral meant both "put" and "loss".
- **Colour-blind safety:** sign glyph, ▲/▼, IN PROFIT/IN LOSS, and a 6 px edge that is solid for profit and hatched for loss (D3). Up and down collapse to khaki under deuteranopia.
- **Breakeven flicker:** D4's hysteresis is adopted. The band takes a colour after 3 s beyond ±0.5 pt, or at once beyond ±1.5 pt, so the headline does not flicker at breakeven and is never neutral on a real move.
- **Stop thresholds:** r ≤ .5 turns the segment beacon; r ≤ .25 turns the border beacon and shows "NEAR STOP". Two calm steps, with text carrying the state.
- **Receipt:** 60 s, or until the next entry (D1, D3, D5). The slot is reserved anyway.
- **Stale:** D3 + D4, meaning ink numbers, a dashed border, a FROZEN label, and frozen writes. Greyscale at .55 opacity measured 2.6:1.
- **Triangle while holding:** dimmed to 45%, with no full glow and no shock-wave; the entry moment belongs to the band. It cannot fire while a position is held.
- **Ladder while holding:** flashes only on the held leg, which gets a 2 px ink border and a HELD tag. The ATM chip becomes an outline.

**Rejected:**
- D4's breathing border: a loop at the most stressful moment.
- D4's reason-coloured receipt edge: colour belongs to P&L.
- D5's sticky chip: the header equity already covers it.
- D1's 20 px ladder prices: the ladder is now below the fold.
- D2's vanishing row: it reflows the page.

## Final spec
**Grid at ≥1281 px (the same open and flat):**
```
"pos pos pos" / "vortex trace trace" / "vortex straddle straddle" /
"oimap ladder ladder" / "oimap heavy heavy" / "books trades trades" / "books tape tape"
```
- At ≤1280 px: `pos pos`, then `vortex trace`, `straddle`, `ladder`, `oimap heavy`, `trades`, `books tape`.
- At ≤820 px: one column, with `pos` first.

**Flat band:** 44 px, transparent, with a 1 px `--line` border. 14 px `--mist` text: `FLAT · ₹1,00,000 ready · 2 trades today, 1 won`, with the last result on the right in mist. No saturated colour; nothing larger than 15 px.

**Open band:** about 150 px, `--deep` with a 6% tone tint and a 6 px left edge. Three columns:

| Column | Content |
|---|---|
| 1 | `LONG [25200 PE] puts ▼ · 25 lots · exp 19 Oct` with an `IN LOSS` tag. Below it, the **₹ P&L at 60/700**, signed, then `−0.90 pts −1.5%` at 24 px. |
| 2 | Stop rail with the caption `6.2 pts to STOP · 25,232.0` (15 px, ink). |
| 3 | `Bought · Now · Best · In 6m 12s · Time exit 15:25`, then a 44 px sparkline. |

**Stop rail:**
- Trail off: the track spans stop → entry → trail-arm (entry + d\*).
- Trail on: it spans TRAIL stop → best, and the caption adds `locks +x`.
- An ink tick marks now. The segment from the stop to now is mist, turning beacon at the thresholds above.
- r = (fut − stop)·dir / d\*.

**Type:** 60 / 24 / 18 / 15 / 13 / 12 px. Chakra Petch for numbers, Barlow for words.

**Tokens:**
- `--up` / `--down`: P&L only.
- `--beacon`: stop-near and entry.
- `--ink` / `--mist`: text.
- `--shelf`: the track.

**Chips (mist):**
- `EXIT PENDING · STOP, waiting for a fresh quote`
- `entries paused · data gap`

**Entry:** one beacon border glow fading over 1.2 s. The beep plays as today. aria-live announces `Bought 25 × 25200 PE at 60.00`.

**Exit:** for 60 s the band shows `CLOSED [TRAIL] +₹2,925 · +1.80 pts · 10:02 → 10:08` in ink, with only the rupee figure coloured. Then it returns to flat.

**Stale:**
- Numbers turn ink, and the band gets a 2 px dashed mist border and `FROZEN n s · last known`.
- Writes stop, and the rail's now-tick is hidden.
- No opacity change.

**Reduced motion:** no glow or transitions; instead the border stays beacon for 5 s. The ladder flash and the shock-wave are off, checked with `matchMedia`.

**Engine (additive, display only):** the published `pos` gains `d_star`, `fut_now`, `stop_pts`, `hold_s`, `ret_pct` and `time_exit`.
