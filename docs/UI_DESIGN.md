# ApexOptions UI design brief: "Night instrument panel"

**Direction.** A high-end avionics/terminal panel at night: deep blue-black layered glass, 1 px hairlines, soft depth,
and crisp luminous tabular numerals that are the brightest thing on screen. Colour and glow appear only to carry
meaning (green = calls/rising, coral = puts/falling, gold beacon = trigger near/firing); everything else is calm ink and mist.

Fonts stay: **Chakra Petch** (`--num`: all numerals, labels, h2) and **Barlow** (`--txt`: prose). No new font links.

## Tokens (all on :root in base.css; never hard-code a hex that a token covers)
| Token | Use |
|---|---|
| `--abyss` `--s0` | page background only |
| `--deep` `--s1` | solid panel colour (canvas uses it) |
| `--panel-bg` | panel background (glass gradient). Already on every `section` |
| `--s2` / `--card-bg` | card or well inside a panel, table header row, chips |
| `--s3` | hover / active chip / selected row |
| `--shelf` | tracks, bar backgrounds, meters (canvas uses it) |
| `--line` axes/track borders (canvas) · `--hair` inner dividers · `--hair-2` panel border · `--line-strong` emphasised or stale dashes | |
| `--hi` | 1 px inset top highlight (inside `--shadow-1/2`) |
| `--ink` numerals, primary text · `--ink-2` h2, strong secondary · `--mist` labels, hints, units · `--ink-dim` axis ticks only, never a number | |
| `--up` `--up-tint` `--up-line` `--glow-up` | calls / rising: text, 10 % fill, 38 % border, glow |
| `--down` `--down-tint` `--down-line` `--glow-down` | puts / falling, same set |
| `--beacon` `--beacon-tint` `--beacon-line` `--glow-beacon` | trigger near/firing ONLY |
| `--refill`/`--ice`, `--gold`, `--amber`, `--violet` | existing state hues (refill, locked profit, near stop, exit pending) |
| `--c-*`, `--t-*`, `--v-*`, `--hn`, `--cmt-h-feed` | header tiles, commentary tones/verdicts: same names, keep using |
| `--frozen` the red FROZEN tag only · `--focus` focus ring | |
| `--r-xs 4` `--r-sm 8` `--r-md 12` `--r-lg 16` `--r-pill` | tags 4, chips/cards 8, inner cards 12, panels 14 (fixed), pills |
| `--sp-1..--sp-8` | 4 / 8 / 12 / 16 / 20 / 24 / 32 px. Use only these steps |
| `--shadow-1` panels · `--shadow-2` raised (open band, hot card) · `--shadow-in` wells/tracks | |
| `--fs-2xs 10` `--fs-xs 11` `--fs-sm 13` `--fs-md 15` `--fs-lg 18` `--fs-xl 24` `--fs-hero 52` | type scale |
| `--track-label .12em` | letter-spacing for UPPERCASE micro labels |
| `--ease` `--dur-fast 140ms` `--dur 220ms` `--dur-slow 420ms` | motion |

Canvas colours (`--up --down --beacon --ink --mist --shelf --line --deep --refill`) MUST stay 6-digit hex literals
(app.js `alpha()` parses them). Never set them to rgba() or var().

## Panel anatomy (grid.css owns it; do not restyle `section`, `.sec-head`, `h2`, `body`)
- `section`: `--panel-bg`, 1 px `--hair-2` border, radius 14, padding 16/18 (14/16 ≤1280, 14 ≤820), `--shadow-1`, position: relative.
- `.sec-head`: flex, baseline, wraps; 10 px bottom padding, 1 px `--hair` rule, 14 px gap to the body.
- `h2`: Chakra Petch 600 12.5 px UPPERCASE, `.12em`, `--ink-2`, led by a 6 px square marker (`::before`, `--line-strong`).
  A section MAY tint its own marker: `.ladder .sec-head h2::before { background: var(--up); }`. `h2 small` is not uppercased.
- `.sec-head > span` (hint at right): 13 px Barlow 500 `--mist`, tabular; `b` inside is `--ink-2`.
- `.legend` / `.small`: 13 px `--mist`, line-height 1.45; `.legend` has a `--hair` top rule.
- Inner cards: `--card-bg`, 1 px `--hair` border, radius 12 or 8, padding 10–12. No shadows on inner cards.
- Tables: head row 11 px UPPERCASE tracked `--mist` on `--s2`; rows split by `--hair`; numerals right (`td.r`).
- Vortex stays frameless by design. `.pos` and `.cmt` own their frames.

## Numeral sizes (Chakra Petch; base already gives `b`, `.num`, `td.r`, `.q-px` tabular lining figures)
| Level | Size / weight |
|---|---|
| Position-band P&L (hero) | `--fs-hero` 52 px 700 (48 ≤1500, 44 ≤820) |
| Futures quote `.q-px` | 36–40 px 600 |
| Header tile `.val` | `var(--hn)` (28–34 px) 600 |
| Panel key figure (verdict number, receipt, straddle total) | `--fs-xl` 24 px 600 |
| Emphasised in-panel number (ladder price, trade rupees) | 18–20 px 600–700 |
| Table cell / row value | `--fs-md` 15 px 500 |
| Sub-line, greeks, bid/ask | `--fs-sm` 13 px 500 `--mist`, values in `--ink-2` |
| Micro label / tag | `--fs-xs` 11 px 600 UPPERCASE `.12em`; tags `--fs-2xs` 10 px 700 |
Numbers are `--ink` unless direction makes them `--up`/`--down`. Units and labels `--mist`, lighter than the number.

## States (each must stay obvious)
- **body.stale (FROZEN)**: plain panels go dashed `--line-strong`, no shadow (grid.css). In your section: desaturate
  (`filter: saturate(.25)` or colour → `--mist`), kill glow and animation, keep numbers `--ink` and readable, keep the
  red `--frozen` FROZEN tag where it exists. Never hide a number when stale.
- **.nodata**: value and label `--mist`, accents 40 % opacity, em dash shown. No skeleton shimmer.
- **.hot**: `--beacon-tint` fill, 1 px `--beacon-line` border, `--glow-beacon` on the number only. Gold only for trigger meaning.
- **.held**: 1 px solid side-colour border (`--up` CE / `--down` PE) + HELD tag (`--fs-2xs` 700, side colour on 15 % tint).
- **.flash / .flash-up / .flash-down**: existing 300 ms change flash. Same duration; colour only, no size change, no movement.
- `.ph-*`, `.lv1-.lv4`, `.pop/.crush`, band states, commentary HOLD/WATCH/EXIT: keep each hue and meaning; you may
  refine tint/border/shade, never swap meaning.
- Hover (desktop only): `--s3` background or `--hair-2` border, `--dur-fast`. Never on numbers that update.

## Motion rules
- Allowed: the 300 ms flash; state changes (border/background/colour) at `--dur` `--ease`; the existing VIX lv4 and
  open-band pulses (slow ≥ 1.6 s, low amplitude); a one-time entrance for a new tape/commentary row (≤ 220 ms, opacity + ≤ 4 px).
- Not allowed: anything per tick besides the flash; moving or scaling a number; layout shift; looping shimmer; blur.
- Switch off every animation/transition you add inside your own `@media (prefers-reduced-motion: reduce) { }`.
- Fixed heights stay fixed (`--cmt-h-feed`). Reserve space (min-height) for things that appear; never push content.

## Layout guardrails
- Your @media rules live in your own block. Breakpoints in use: 1759, 1600, 1500, 1439, 1280, 820 px.
- 375 px: no horizontal page scroll; 16 px gutters (main has them); tables scroll inside (`overflow-x: auto`).
- `min-width: 0` on grid/flex children that hold numbers; `white-space: nowrap` on numerals, never on prose.
- Keep every id/class app.js and commentary.js use. Add classes freely. Grid areas stay rectangular.
- The responsive block must keep the same `main` grid-template-areas as today (grid.css only changes gap/padding).

## Do / Don't
- DO labels as `color: var(--mist); font: 600 var(--fs-xs)/1 var(--num); letter-spacing: var(--track-label); text-transform: uppercase;`
- DO a call-side chip as `background: var(--up-tint); border: 1px solid var(--up-line); color: var(--up);`
- DO `box-shadow: var(--glow-beacon)` only while the trigger is near/firing.
- DON'T glow neutral text, headings or borders "for looks".
- DON'T add decorative hues (teal/purple/blue gradients); decoration = ink, hairlines, depth.
- DON'T use gold for profit or warnings (locked profit = `--gold`, warnings = `--amber`, beacon = trigger only).
- DON'T use `--ink-dim` or opacity < .6 on a live number.
- DON'T use backdrop-filter or heavy blur (cost at 4 Hz redraws).
