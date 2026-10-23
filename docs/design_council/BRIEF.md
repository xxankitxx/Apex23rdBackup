# Design council brief — the Paper position panel (identical for all 5 members)

You are ONE of five designers. Work ALONE: read nothing in /mnt/user-data/outputs/design_council/
except this BRIEF.md and the before_*.png screenshots. Do not coordinate.

## The owner's goal (his words)
"If a position is taken, that should be the most prominent thing that reaches my eye when I open
the browser." Also: the "Ten hero contracts" panel must move to sit BELOW the "Straddle watch" panel.

## The product
ApexOptions, a personal PAPER-trading dashboard for Nifty weekly options (buy CE/PE only), one
position at a time, ₹1,00,000 all-in, viewed on a desktop browser (~1500 px wide) during market
hours, dark theme. Code (read-only for you): /mnt/user-data/outputs/ApexOptions/apex/static/
index.html, app.js (see renderPos / the position rendering and the header capital), style.css
(grid areas, tokens). The position data available to the page: contract (strike, CE/PE, expiry),
lots, entry price, current price, best, P&L in points and rupees, return %, time in, futures entry,
stop level on futures, trail on/off, the exit reasons possible (STOP, TRAIL, THESIS-VOID, BOOK, TIME),
blackout/stale state. When flat: capital, today's P&L, "ready" text.

## Screenshots (1500x1000 viewport, simulated market)
- before_flat_fold.png / before_flat_full.png — no position
- before_pos_fold.png / before_pos_full.png — a position is open (Long 25 lots 25200 PE, −₹1,462)
- before_pos_panel.png — the current panel alone

## Your task
From YOUR lens (given in your instructions), write an individual critique and proposal:
1. Critique: what is wrong today with how a position presents itself, concretely (cite the screenshot
   and the CSS/JS you read). What competes with it for attention?
2. Proposal: what the position should look like and where it should live when OPEN and when FLAT
   (it must not shout when flat). Be concrete: placement in the grid, size, type scale, colour
   tokens, what numbers appear and in what order, how proximity to the stop / trail is shown, what
   changes on entry and exit, how it behaves when the engine is stale. Include the hero-contracts move.
3. Constraints you would insist on (accessibility, no distraction during long holds, consistency with
   the existing palette and fonts, nothing that hides other critical information).
4. A rough ASCII or bullet wireframe.
You may load the `frontend-design` skill for guidance. Do NOT modify any file under ApexOptions.

Write ≤ 900 words to /mnt/user-data/outputs/design_council/designer_<N>_<lens>.md and reply with
two lines: the path and your single strongest recommendation.
