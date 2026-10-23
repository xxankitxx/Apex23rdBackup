# 11 — The live-trade commentary (council 5, 20 Oct 2026)

The owner asked (20 Oct 19:22): *"After taking a trade, sometimes you may realize that you have either done a stupidity
or you entered costly. When holding a trade, you may anticipate higher price for selling. I want a commentary panel to
pop up during a live trade … tell me which stocks are going in my favor or which stock ruined my current trade … it
should have a huge number of possibilities … if you can instil more and more confidence in me to hold, I will keep
holding."*

This document is the whole catalogue: every fact the commentary can see, every remark it can make, and the evidence
each one rests on. It is generated from the modules, so what is written here is what the engine says.

## 11.0 How it works (apex/engine/commentary.py)

* While the champion holds a position the engine evaluates the commentary **once per market second** (an observer:
  it never changes when or whether the system trades).
* **Facts** — 115 base facts (`FACT_KEYS`: premium, give-back, spot vs stop, lock, Greeks and their rupee shares,
  heavyweight attribution since entry, order-book classes on the held strike, straddle, regime, walls, the clock, the
  day) plus the three content modules' own: 89 `entry` facts, 112 `eq_*` basket facts, 115 `hold_*` facts.
* **Templates** — 209 in all, 685 phrasings. Each has a predicate over the facts, a tone (warning / caution /
  confidence / praise / lesson / information), a priority, a cool-down, a "step" (a watched number moving by this much
  re-fires it), a minimum hold time, and 2–6 phrasings chosen deterministically per trade (so a replay reproduces the
  commentary to the word).
* **Selection** — at most one new remark per second and three per ten seconds; a warning jumps the budget but keeps
  its own cool-down; ties go to the higher priority.
* **Verdict** — a persistent HOLD / WATCH / EXIT-SOON line with its single strongest reason, derived only from named
  evidence (stop distance, give-back, basket synchrony, order book, the clock, data health). A HOLD is never justified
  by mood. A stricter verdict replaces a milder one at once; a milder one needs 3 s.
* **Cards** — an entry card at the fill (grade A–E, three lines) and a review card at the exit (what the trade did,
  what made it, what ruined it, the day's tally).
* **Honesty rules, enforced by tests** — no instruction words ("hold", "sell", "exit" as imperatives); a confidence
  remark must cite a number and is silenced when spot is within a quarter-trail of the stop, when the sellable bid shows
  a loss while the last print shows a gain, or when data is bad; warnings only when evidence has turned; every number
  in a sentence is a fact, never typed in.
* **Where it goes** — the state blob (`commentary`: verdict, the latest 12 remarks, the cards) for the dashboard
  panel, and the tape `data/paper/commentary_<day>.jsonl`.
* **Evidence** — the thresholds come from the 19 Oct replay (32 champion trades). They are labelled "19 Oct" wherever
  they appear in a sentence, and they must be re-measured after ten sessions (the modules carry a `REF`/`HOLD_REF`
  table for that).

## 11.1 Entry quality and the price paid — `apex/engine/cmt_entry.py` (team T06)



The question this module answers, once per trade, at the fill: **did I do a stupidity, or did I enter costly?**
*Costly* means the right idea at a rich price — the spread, the IV, a premium that already ran, a straddle that
expanded before you. *Stupid* means the wrong contract or the wrong moment — a near-the-money strike on an expiry
afternoon, a break with no 5-minute push behind it, a stop that sits inside the noise. The entry card grades both
(A–E) and pins itself above the commentary for the life of the trade; the templates say which one it is, with numbers.
The grade sorts the **entry**, never the outcome: the biggest ₹ loss of 19 Oct was an E, the second biggest was an A
that simply failed, and `entry.second_look_60s` says so a minute later.

## Evidence (19 Oct 2026, 32 champion trades; `work_T06/trades32_graded.csv`)

| Dimension | Fact | What the day said | Threshold |
|---|---|---|---|
| Spread paid | `over_mid` | ≤ 0: **13 trades, 10 wins, +₹2,80,000, +10.3 %**; 0.5–1.0: 5/2; > 1.0: 3/2 (2.97, 2.88, 1.67 pts). Day's over-mid tax ₹24,963 (median 0.07 % of premium) | clean ≤ 0.05 · fair ≤ 0.30 · costly ≤ 1.0 · chased > 1.0 |
| Premium vs its own path | `pos_in_range` | < 0.80: **4/4, +₹1,91,770, +23.0 %**; ≥ 0.95: **11/5, −₹20,787, +0.4 %**. The strongest single fill-quality discriminator | top ≥ 0.97 · retest < 0.80 |
| Premium run-up | `rise5` | ≥ 50 %: 4 trades (all pre-09:40), 3 wins, mean +4.9 % vs +7.3 % for 10–20 % | ran ≥ 50 · some 20–50 · fresh < 10 |
| IV paid | `iv_run_pct`, `iv_vs30` | percentile ≤ 33: **5/5, +₹1,96,437, +21.9 %**; `iv_vs30` > +3: 10/5, +2.9 %; < −1: 14/10, +6.6 %. Expiry ramp 27 % → 45 % — compare to the day so far, not the whole day | low ≤ 33 · high ≥ 90 and +3 · falling ≤ −1 |
| Strike (vs **spot**) | `money`, `extr_pct` | < 40 ITM: **5 trades, 1 win, −₹49,933** (13:12–14:24, all PE, 29–39 ITM, 44–59 % extrinsic, delta 0.66–0.73); 60–90: 20/13, +₹2.77 L; **90–130: 7/5, +₹1.41 L, +13.2 %**. Measured vs the future it is nonsense (PM basis 18–30 pts) | sweet 60–130 and extr ≤ 40 · lottery < 40 or extr ≥ 45 · heavy > 150 |
| Chase / impulse | `chase_pts`, `s60`, `s300` | chase 3–10 pts past the level: 4/3, **+10.8 %** (not a sin); `s60` ≥ 20: 4/2, +3.3 %; **`s300` < 10: 6/3, −₹28,629**; 10–50: 21/13, +₹3.77 L | no push < 10 · sprint ≥ 20 |
| 30-min trend | `s1800` | ≤ −20: 7/3, ≈ 0; −20..0: 5/4, +₹1.85 L; ≥ 20: 12/7, +5.4 %. Not monotonic → caution, never lesson | against ≤ −20 · with ≥ +20 |
| Regime | `regime` | DIRECTIONAL 9/7, +9.8 %; RANGE+UNCERTAIN+EXHAUSTION 8/3, −₹5.4k; against the regime 3/2 | — |
| Hour | `hour` | AM 20/12, +7.4 %, 19.9 pts peak; PM 12/7, +2.6 %, 12.7 pts; after 14:15 3/1 | PM ≥ 12:30 · opening < 09:40 · last ≥ 14:15 |
| Size | `qty_vs_vol`, `qty_vs_ss` | max 0.2 % of 5-min volume, 0.4–4 % of the visible ask — never a concern on Nifty weekly ATM. Thresholds are market-maker practice, **not data** | 2 % / 50 % |
| Straddle | `strad_5` | ≤ −2: **13/9, +₹2.38 L, +7.8 %**; ≥ +5: 6/4 (mixed) | priced ≥ +5 · compressing ≤ −2 |
| Room | `room_in` | nearest wall 360–521 pts on every logged trade; 25 pts = 2 × stop + the advisor's "need ~19" | ≤ 25 · ≥ 100 |
| Stale quote | `trade_age_in` | 5–30 s: 7/6, +₹2.36 L — **no direction signal**; fill honesty only | ≥ 5 s |
| Noise | `sigma15`, `range5` | 5–7: **5/5, +12.0 %**; 7–9: 5/2, +₹1,388. `range5` ≥ 40: 7/5 | inside ≥ 8 · well-sized 5–7 · wide ≥ 40 |

**Score** (grade.py, every term above): over_mid ≤ 0.05 / ≤ 0.30 / ≥ 1.0 → +2 / +1 / −2 · pos_in_range < 0.80 / ≥ 0.97 → +2 / −1 ·
money 60–130 with extr ≤ 40 / < 40 or extr ≥ 45 / > 150 → +2 / **−3** / −1 · s300 < 10 / 10–50 → **−2** / +1 · s60 > 20 → −1 ·
sigma15 > 8 / 5–7 → **−2** / +1 · hour ≥ 13 → −1 · strad_5 > 5 / < −2 → −1 / +1 · iv_vs30 > 3 → −1 · trade_age_in > 5 → 0 (named on the card as fill uncertainty).
**Grade:** A ≥ 4 · B 2–3 · C 0–1 · D −2..−1 · E ≤ −3. Verdicts: clean / good (or "good, but you paid up" when > 0.30 over mid) / fair / costly / poor entry.
A missing fact skips its term; the grade is never guessed from a default.

**In-sample result** (the weights were designed on these trades — a sanity check, not a validation): A 16/11, +₹2,77,739, +9.2 %, peak 21.6 pts ·
B 5/4, +₹1,01,794 · C 3/2, +₹37,912 · D 4/2, +₹6,806 · E 4/0, −₹55,591, peak 6.2 pts. **Validation rule:** replay 21 and 22 Oct, print the grade
table untouched; if E is not the worst bin and A not the best, the weights go back to the owner and the panel keeps the facts without the letter.

## The entry card

Three lines, built by `entry_card(f)` on the entry tick, pinned by the core (`state["commentary"]["entry_card"]`):

1. `Grade A — clean` (the letter and the verdict word)
2. the two or three facts that decided it, always with numbers (`entry_reasons[:3]`, e.g. `fill −0.53 vs mid · 90 pts ITM vs spot, 27 % extrinsic · spot +27 / 5 min`); a fill on a quote ≥ 5 s stale is named here as fill uncertainty
3. the base rate from the last replayed day, **labelled** — `On 19 Oct, A-entries: 11/16 won, mean +9.2 %, best excursion 22 pts. Your part is done; now the hold.` — read from `REFS["grades"]`, never a prediction.

`REFS` in the module is the first `commentary_refs` table (19 Oct). Every `{ref_day}` in a phrasing prints `REFS["day"]`; the hour table
and the grade table are slots too. When the lead regenerates the refs after a replay, the literal 19 Oct clauses in the phrasings are the
next thing to move into REFS (they are kept literal for now so the owner can read the evidence in the sentence).

## Facts added (`cmt_entry.FACTS`, 89 keys; all computed once at the fill in `extend_memo`, copied into `f` every second)

| Fact | Meaning | Source |
|---|---|---|
| `over_mid`, `over_mid_pct`, `over_mid_rs` | entry − mid at the fill, as % of premium, in ₹ (× qty) | `pos.entry`, `pos.mid_in` (paper._entry_observers), `pos.qty` |
| `mid_in`, `entry_bid`, `entry_ask`, `spread_pct`, `roundtrip_rs` | the book at the fill; spread as % of premium; ask−bid × qty | `pos.entry_bid/ask`, `pos.mid_in` |
| `prem_win_s`, `lo5`, `hi5`, `p5`, `pos_in_range`, `rise5` | the held contract's premium window before the fill: its length in seconds, low, high, first price, (entry−lo)/(hi−lo), entry/p5 − 1 in % | `eng.m.ltp` ring (60 s @ 10 Hz) merged with this module's own 1-Hz history of the contract (fed while a trade is held, 600 s) — **the window is 5 min only when the contract was held in the last 5 min; the phrasings print the real window** (`{prem_win_txt}`) |
| `vwap5`, `vwap_kind`, `vs_vwap`, `vs_vwap_pct` | Σ(Δttq × price)/ΣΔttq over the window (`vwap_kind` = "VWAP"), else the 1-Hz mean ("mean"); entry minus it | `eng.m.ttq` and `ltp` over the same window |
| `iv_run_pct`, `iv_day_lo/hi/med`, `iv_cover_min` | percentile of `iv_in` (the contract's IV) within the ATM IV history so far, that history's low / high / median and its length in minutes | `eng.iv_hist` (900 s @ 1 Hz) folded into a per-day, per-30-s list kept by this module (bounded 800) |
| `iv_vs30` | `iv_in` minus the ATM IV 30 min earlier (None until 25–40 min of history exist) | same list |
| `iv_rise` | ATM IV change over the last 5 min (pts) | `eng.iv_change(300)`, else `ctx.iv_rise_since_onset` |
| `iv_other`, `skew` | the other leg's IV at the same strike; own − other | `eng.greek[eng.key[...]]` |
| `iv_late_why`, `regime_why`, `room_why` | the advisors' sentences at entry | `pos.advisors` |
| `money`, `money_fut`, `extr_pct`, `intr_pct` | (spot_in − K)·dir in pts — **vs spot**; the same vs the future (for the basis remark); extrinsic / intrinsic share of the premium | `pos.spot_in`, `pos.fut_in`, `pos.strike`, `pos.dir` |
| `band_fallback`, `lot_cost` | the band had no contract; premium × LOT_SIZE | `pos.band_fallback`, `config.LOT_SIZE` |
| `break_level`, `chase_pts` | the 12-min level the trigger broke (ctx spot_hi for calls, spot_lo for puts) and how far past it spot was at the fill | `ctx.spot_hi/lo`, `pos.spot_in` |
| `s60`, `s300` | spot change in the trade's direction over the 60 / 300 s before the fill | `eng.spot_hist` (1 Hz, 12 min) |
| `s1800` | futures move over 30 min in the trade's direction | `ctx.trend30` × dir (D-114), else `eng.fut_hist` |
| `sigma15`, `range5` | the trigger's noise measure and the futures 5-min range at entry | `ctx.domino.sigma15`, `ctx.range5` |
| `hour`, `time_in`, `trail_pts` | clock at entry; the champion's spot trail (12) | `ctx.now_dt`, `pos.time_in`, `book.p.spot_trail` |
| `stop_rs`, `stop_prem`, `rs_per_pt` | trail × |delta_in| × qty; trail × |delta|; |delta| × qty | `pos.delta_in` |
| `vol_win`, `vol_win_s`, `qty_vs_vol` | traded quantity over the premium window and qty / it | `eng.m.ttq` (cumulative) |
| `ss_in`, `sso_in`, `qty_vs_ss`, `slices` | visible sell-side quantity and order count at the fill; qty / ss; the order's freeze slices | `eng.m.ss/sso[row, k]`, `pos.slices` |
| `prev_lots`, `prev_ret`, `prev_reason`, `prev_key`, `same_key`, `since_exit`, `prev_stop_rs` | the previous closed trade: size, return, exit reason, contract, same contract?, seconds since its exit, its ₹ stop | `book.trades[-1]` |
| `strad_5`, `strad_state_in`, `strad_px_in`, `strad_vwap_in` | ATM straddle: 5-min change, state, price, VWAP at the fill | `eng.straddle.view()` |
| `room_in`, `wall_in`, `wall_oi_in`, `chain_age_in` | next OI wall in the trade's direction, its distance and OI, and the chain's age | `eng.pressure.destination()`, `.walls_up/dn`, `.chain_age` |
| `trade_age_in`, `lag_s_in` | seconds since the contract's last exchange print at the fill; feed delivery lag on the index | `pos.trade_age_in`, `eng.data_health(snap).lag_s` |
| `vix`, `vix_lo`, `vix_hi` | India VIX at entry and the range this module has seen today | `eng.t.c("vix")` |
| `day_over_mid_rs`, `day_trades`, `day_over_mid_pct` | the day's spread tax so far (closed trades + this one), count, mean % of premium | `book.trades`, this fill |
| `entry_score`, `entry_grade`, `entry_verdict`, `entry_reasons`, `entry_fired` | the score, the letter, the verdict word, the reasons in card order | `_score(q)` |
| `ret_now`, `spot_vs_in`, `best_vs_in`, `entry_look`, `cost_status` | the five dynamic keys for the 60-s second look: return now, spot vs entry, best spot vs entry, "vindicated / unproven / expensive" (≥ +2 % / between / ≤ −2 %), whether the over-mid has been earned back | base facts `ret_pct`, `spot_fav`, `best_spot_fav`, `pnl_pts` |

Honesty of the windows: the engine keeps 60 s of contract prices, so on the first trade of a contract the "5-min" premium facts are 60-s facts.
The module keeps its own 1-Hz history of the held contract and merges it at the next entry, so a re-entry within 5 minutes sees the full window.
Every phrasing prints the window it really used (`{prem_win_txt}` = "5-min" / "58-s"; `{vol_win_txt}` likewise) and the IV percentile names its coverage.
`None` facts render as "—" and a template whose facts are missing simply does not fire.

## Template catalogue — 59 templates, 198 phrasings
Every template fires **at most once per trade** (the entry facts do not change); `min_hold_s` spreads the groups over the first minute so the panel is not a wall at the fill (composite with the card at 0 s → fill 1 s → strike 2 s → chase 3 s → premium 4 s → rs-per-point 5 s → IV 6 s → noise 8 s → hour 10 s → trend 12 s → straddle 14 s → time 16 s → size 18 s → room 20 s → quote 22 s → VIX 25 s → what-it-cost 30 s → second look and day tally 60 s). The core still allows one remark a second and three per ten seconds, so lower-priority remarks slide later. `{ref_day}` prints REFS['day'] (19 Oct).

### A fill

#### `fill.clean`
- **tone / prio / kind:** praise / 70 / entry · **fires:** once per trade, from 1 s into the trade
- **when:** fill at or under the mid: `over_mid` ≤ +0.05 pts
- **evidence:** over_mid ≤ 0.05: 13/32 on 19 Oct, 10 wins, +₹2,80,000, mean +10.3 %
- **phrasings:**
  - Clean fill: {over_mid:+.2f} over the mid, spread was {spread_in:.2f}. Nothing given away at the door.
  - You bought at {entry:.2f} against a {entry_bid:.2f}/{entry_ask:.2f} book — at the mid. That is as good as a fill gets.
  - Filled {over_mid:+.2f} vs mid. On {ref_day} the 13 fills at or under the mid went 10-3 for ₹2.80 L; the entry cost you nothing.
  - No spread tax here: entry {entry:.2f}, mid {mid_in:.2f}. Start the trade at zero, not minus.

#### `fill.fair`
- **tone / prio / kind:** information / 40 / entry · **fires:** once per trade, from 1 s into the trade
- **when:** 0.05 < `over_mid` ≤ 0.30 pts and `over_mid_pct` ≤ 0.4 %
- **evidence:** 0.05-0.30: 11 trades, 5 wins, −₹29k on 19 Oct; not a loss driver by itself
- **phrasings:**
  - Fill {over_mid:+.2f} over the mid ({over_mid_pct:.2f} % of premium) — normal for a market order on this contract.
  - You paid {over_mid:.2f} pts of spread: {over_mid_rs_txt} on {qty} qty. Small, but it is the first thing the trade has to earn back.
  - Ordinary fill: {over_mid:.2f} over mid, within the {spread_in:.2f} spread. Fine.
  - Spread paid {over_mid:.2f} — about what the book charges anyone who crosses it.

#### `fill.costly`
- **tone / prio / kind:** lesson / 70 / entry · **fires:** once per trade, from 1 s into the trade
- **when:** 0.30 < `over_mid` ≤ 1.0 pts, or `over_mid_pct` > 0.4 % (still ≤ 1.0 pt)
- **evidence:** 19 Oct median over-mid 0.07 % of premium; 0.30-1.0 pts: 5 trades, 2 wins
- **phrasings:**
  - You paid {over_mid:.2f} over the mid — {over_mid_pct:.2f} % of the premium, {over_mid_rs_txt} on this size. The market moved while you were deciding.
  - Costly fill: {over_mid:.2f} pts above mid. A limit at the mid would have saved {over_mid_rs_txt} or missed the trade — on {ref_day} it would have missed 2 of 32.
  - {over_mid:.2f} over the mid ({over_mid_pct:.2f} % of premium). Not a disaster, but it is {x_median:.0f}× the {ref_day} median of {ref_median_over_mid_pct:.2f} %.
  - The ask ran away from you: entry {entry:.2f}, mid {mid_in:.2f}. That is {over_mid_rs_txt} you need the trade to earn first.

#### `fill.chased_ask`
- **tone / prio / kind:** lesson / 85 / entry · **fires:** once per trade, from 1 s into the trade
- **when:** `over_mid` > 1.0 pt: filled through the ask, the premium jumped between signal and fill
- **evidence:** over_mid > 1.0: 3 trades on 19 Oct (2.97, 2.88, 1.67 pts), ₹7,700 combined
- **phrasings:**
  - You were filled {over_mid:.1f} pts above the mid ({over_mid_pct:.1f} % of premium). That is not spread — the premium jumped as you hit it. On {ref_day} this happened twice: 09:36 (−5.0 %) and 10:19 (+8.7 %).
  - Ouch: {over_mid:.1f} over mid. The quote was {entry_bid:.2f}/{entry_ask:.2f} and you printed {entry:.2f}. Someone got there a second before you.
  - Entry {entry:.2f} vs a mid of {mid_in:.2f}. You chased the premium, not the spot. {over_mid_rs_txt} given to the seller.
  - This fill cost {over_mid:.1f} pts more than a patient one. It is the single most expensive thing you did on this trade so far.

#### `fill.spread_wide`
- **tone / prio / kind:** caution / 55 / entry · **fires:** once per trade, from 2 s into the trade
- **when:** `spread_in` ≥ 0.35 pts or `spread_pct` ≥ 0.3 % of premium
- **evidence:** 19 Oct spreads 0.15-0.35 pts; ≥ 0.35 in 4 trades (all 09:27-09:58); round-trip on 32 trades ₹21,900
- **phrasings:**
  - Wide book at entry: {spread_in:.2f} between bid and ask ({spread_pct:.2f} %). Expect the exit to cost the same again.
  - Spread {spread_in:.2f} — the widest third of the {ref_day} day. Round-trip cost on this size ≈ {roundtrip_rs_txt}.
  - The bid/ask was {entry_bid:.2f}/{entry_ask:.2f}. Wide for an ATM weekly; the market-maker is nervous, which also means fast moves.

#### `fill.day_tally`
- **tone / prio / kind:** information / 40 / day · **fires:** once per trade, from 60 s into the trade
- **when:** once, 60 s after entry: `day_over_mid_rs`, `day_trades` (closed trades + this one)
- **evidence:** 19 Oct: Σ(entry − mid)·qty = ₹24,963; mean 0.32 %, median 0.07 % of premium
- **phrasings:**
  - Spread paid so far today: {day_over_mid_rs_txt} across {day_trades} entries ({day_over_mid_pct:.2f} % of premium on average). On {ref_day} the full day came to {ref_day_over_mid_rs}.
  - Entry costs today: {day_over_mid_rs_txt}. Small per trade, real by 15:00.
  - Running tab for crossing the spread: {day_over_mid_rs_txt} in {day_trades} trades.

### B premium path

#### `prem.top_of_range`
- **tone / prio / kind:** caution / 70 / premium · **fires:** once per trade, from 4 s into the trade
- **when:** `pos_in_range` ≥ 0.97: the fill is at the top of the premium's window (`lo5`–`hi5`, window `prem_win_s`)
- **evidence:** pos_in_range ≥ 0.97: 11 trades, 5 wins, −₹20.8k; < 0.80: 4 trades, 4 wins, +₹1.92 L (mean +23 %)
- **phrasings:**
  - You bought the premium at its {prem_win_txt} high ({entry:.2f}; range {lo5:.2f}–{hi5:.2f}). On {ref_day} the 11 entries at the 5-min high went 5-6 for −₹20,787; the 4 bought below 80 % of the range went 4-0 for +₹1.92 L.
  - Premium at the very top of its last {prem_win_long}. A breakout buyer always does this — just know the first pullback is now against you by up to {range5_prem:.1f} pts.
  - Paid the high of the last {prem_win_long}. The spot break is real; the premium is simply fully priced for it.
  - Top-tick of the {prem_win_txt} range ({lo5:.2f}–{hi5:.2f}). The trade has to make a NEW premium high to pay.

#### `prem.retest_entry`
- **tone / prio / kind:** confidence / 70 / premium · **fires:** once per trade, from 4 s into the trade
- **when:** `pos_in_range` < 0.80: bought below the top fifth of the window
- **evidence:** see prem.top_of_range
- **phrasings:**
  - Good price: {entry:.2f} is only {pos_in_range_pct:.0f} % up the last-{prem_win_long} range ({lo5:.2f}–{hi5:.2f}). You bought the retest, not the spike.
  - You did not pay the top: premium is {hi5_minus:.1f} pts under its {prem_win_txt} high. All four such entries on {ref_day} were winners (+30.6 %, +11.0 %, +23.7 %, +26.8 %).
  - Entry {pos_in_range_pct:.0f} % up the premium's {prem_win_txt} range. The breakout came without a premium spike — cheap by {ref_day}'s standards.
  - Below the {prem_win_txt} high by {hi5_minus:.1f}. That is the kind of fill that makes holding easy.

#### `prem.ran_already`
- **tone / prio / kind:** lesson / 85 / premium · **fires:** once per trade, from 4 s into the trade
- **when:** `rise5` ≥ 50 %: the premium rose ≥ 50 % over the window before the fill
- **evidence:** rise5 ≥ 50 %: 4 trades (all before 09:40), 3 wins but mean +4.9 % vs +7.3 % for 10-20 %
- **phrasings:**
  - This premium was {p5:.2f} {prem_win_long} ago and you paid {entry:.2f} (+{rise5:.0f} %). The option already made the move you are hoping for.
  - +{rise5:.0f} % in {prem_win_long} before you entered. You are buying the second half of a spike: on {ref_day} 09:27 and 09:28 did this (+7.9 %, −0.8 %).
  - The premium ran {rise5:.0f} % into your entry. Expect theta and IV-fade to fight you if the spot pauses.
  - Late to the premium: +{rise5:.0f} % in {prem_win_long}. The spot level may be fresh; the price you paid is not.

#### `prem.ran_some`
- **tone / prio / kind:** caution / 55 / premium · **fires:** once per trade, from 4 s into the trade
- **when:** 20 ≤ `rise5` < 50 %
- **evidence:** 20-50 %: 3 trades, 2 wins, +₹64k
- **phrasings:**
  - Premium +{rise5:.0f} % in the last {prem_win_long}. Some of the move is already in the price.
  - You paid {entry:.2f}; {prem_win_long} ago it was {p5:.2f}. Fair warning: the easy part is in.
  - +{rise5:.0f} % premium run-up before entry. Normal on a breakout — just not cheap.

#### `prem.fresh`
- **tone / prio / kind:** praise / 55 / premium · **fires:** once per trade, from 4 s into the trade
- **when:** `rise5` < 10 % and `pos_in_range` < 0.95
- **evidence:** rise5 < 10 %: 7 trades, 4 wins; position in range is the better discriminator
- **phrasings:**
  - The premium has barely moved before your entry (+{rise5:.0f} % in {prem_win_long}). You are early, not late.
  - Quiet premium into the break: +{rise5:.0f} % over {prem_win_long}. If the spot follows through, the option still has to re-price — that is your edge.
  - Fresh entry: the option did not run ahead of the spot (+{rise5:.0f} % in {prem_win_long}).

#### `prem.vs_vwap`
- **tone / prio / kind:** information / 40 / premium · **fires:** once per trade, from 6 s into the trade
- **when:** always (when `vwap5` exists): entry vs the contract's window VWAP (or 1-Hz mean when ttq is missing — `vwap_kind` says which)
- **evidence:** informational; on 19 Oct all 32 were above the 5-min VWAP (breakout buying), 3 % to 236 %
- **phrasings:**
  - Entry {entry:.2f} vs the contract's {prem_win_txt} {vwap_kind} {vwap5:.2f} ({vs_vwap:+.1f}). Everyone who traded it in the last {prem_win_long} paid {vs_vwap_word} than you.
  - {vs_vwap_pct:+.1f} % vs the {prem_win_txt} {vwap_kind}. {vs_vwap_word_cap} than the crowd.
  - You paid {vs_vwap:+.1f} pts vs the recent {vwap_kind} of this strike.

### C IV paid

#### `iv.low_third`
- **tone / prio / kind:** confidence / 70 / greeks · **fires:** once per trade, from 6 s into the trade
- **when:** `iv_run_pct` ≤ 33 with ≥ 10 min of ATM IV history (`iv_cover_min`)
- **evidence:** iv_run_pct ≤ 33: 5 trades, 5 wins, +₹1.96 L, mean +21.9 %, mean peak 37 pts
- **phrasings:**
  - IV paid {iv_in:.1f} % — in the lower third of the ATM range seen so far ({iv_day_lo:.1f}–{iv_day_hi:.1f}, {iv_cover_min:.0f} min of history). On {ref_day} all five such entries won, mean +21.9 %.
  - Cheap vol: {iv_in:.1f} % is the {iv_run_pct:.0f}th percentile of the ATM IV so far. If the move comes, IV expansion works for you, not against you.
  - You bought this option at {iv_in:.1f} % IV, under the running ATM median {iv_day_med:.1f}. Good — the premium is not inflated.
  - IV {iv_in:.1f} %, bottom third of the day so far. One of the three cleanest things an option buyer can do.

#### `iv.high_vs_day`
- **tone / prio / kind:** lesson / 70 / greeks · **fires:** once per trade, from 6 s into the trade
- **when:** `iv_run_pct` ≥ 90 and `iv_vs30` > +3 pts
- **evidence:** iv_vs30 > +3: 10 trades, 5 wins, +2.9 %; < −1: 14 trades, 10 wins, +6.6 %
- **phrasings:**
  - You paid {iv_in:.1f} % IV — the {iv_run_pct:.0f}th percentile of the day so far, and {iv_vs30:+.1f} pts above 30 minutes ago. Vol is expensive here; a stall costs you twice (theta + IV fade).
  - IV {iv_in:.1f} %, up {iv_vs30:.1f} pts in half an hour. You bought fear. It must turn into movement quickly.
  - Expensive vol: {iv_in:.1f} % vs a running ATM median of {iv_day_med:.1f}. On {ref_day}, +3 pts-vs-30-min entries averaged +2.9 % against +6.6 % for falling-IV entries.
  - Top-decile IV for the day so far ({iv_run_pct:.0f}th percentile). Not stupid — but costly, and the premium leaks if the spot goes sideways.

#### `iv.rising_fast`
- **tone / prio / kind:** caution / 70 / greeks · **fires:** once per trade, from 6 s into the trade
- **when:** `iv_rise` ≥ 3 pts (ATM IV change over 5 min, `eng.iv_change(300)`)
- **evidence:** 19 Oct: the two trades with +4.4 / +6.3 IV in 5 min: +7.9 % and −0.8 %; both exited within 30 s
- **phrasings:**
  - ATM IV jumped {iv_rise:+.1f} pts in the last 5 minutes. The straddle re-priced before you got in; this is the 'late' tax.
  - IV +{iv_rise:.1f} in 5 min. Both {ref_day} entries with this flag (09:27, 09:28) saw the premium give back IV within a minute — one won small, one lost.
  - Fast-rising IV into your entry (+{iv_rise:.1f} pts / 5 min). If spot keeps going you are fine; if it pauses, the premium falls even with spot unchanged.
  - The iv_late advisor read: {iv_late_why} (ATM IV {iv_rise:+.1f} in 5 min). It is an advisor, not a gate — but it is right more often than not.

#### `iv.falling`
- **tone / prio / kind:** confidence / 55 / greeks · **fires:** once per trade, from 6 s into the trade
- **when:** `iv_vs30` ≤ −1 pt
- **evidence:** see iv.high_vs_day
- **phrasings:**
  - IV {iv_in:.1f} %, {iv_vs30:.1f} pts below 30 minutes ago. You bought the option while vol was deflating — the cheapest way to own gamma.
  - Vol is cooling ({iv_vs30:+.1f} pts / 30 min). Your premium has less air in it.
  - Falling-IV entry ({iv_vs30:+.1f} pts vs 30 min). 14 of these on {ref_day}: 10 winners, +₹2.06 L.

#### `iv.skew_tax`
- **tone / prio / kind:** information / 55 / greeks · **fires:** once per trade, from 6 s into the trade
- **when:** `skew` = own-leg IV − other-leg IV at the same strike ≥ +8 pts
- **evidence:** skew ≥ +3: 14 trades, 10 wins, +7.5 % — a cost, not a verdict
- **phrasings:**
  - This {rr} is priced at {iv_in:.1f} % IV while the {other_rr} at the same strike trades at {iv_other:.1f} %. You are paying {skew:+.1f} pts of skew — the insurance premium everyone wants on expiry afternoon.
  - Skew tax: {skew:+.1f} IV pts over the other leg. Not a reason to avoid the trade (14 of these went 10-4 on {ref_day}), but it is why the premium looks fat.
  - The {rr} carries {skew:+.1f} pts more IV than its twin. If the move fails, this skew unwinds against you faster than theta does.

#### `iv.after_1330`
- **tone / prio / kind:** caution / 55 / time · **fires:** once per trade, from 16 s into the trade
- **when:** expiry day (`zero_dte`) and `time_in` ≥ 13:30
- **evidence:** 19 Oct 13:00-14:45: 10 trades, 5 wins, mean +2.8 %, mean peak 12.6 pts (AM: 19.9)
- **phrasings:**
  - Expiry afternoon: IV {iv_in:.1f} % and climbing. This is pure gamma now — the option pays only if spot moves, and the premium melts every minute it does not.
  - 0DTE after 13:30. On {ref_day} the ATM IV went from 31 % to 45 % into the close; extrinsic value evaporates at {theta_rs_abs:,.0f} ₹/min on your size.
  - Late-expiry entry ({time_in}). Nothing wrong with it — but understand the clock is the opponent now, not the spread.

### D strike

#### `strike.sweet`
- **tone / prio / kind:** confidence / 70 / entry · **fires:** once per trade, from 2 s into the trade
- **when:** 60 ≤ `money` ≤ 130 pts ITM vs SPOT and `extr_pct` ≤ 40 %
- **evidence:** money vs spot 60-90: 20/13 +₹2.77 L; 90-130: 7/5 +₹1.41 L, mean +13.2 %; extrinsic ≤ 30 %: 13/9 +11.0 %
- **phrasings:**
  - {strike} {rr}: {money:.0f} pts in the money vs spot, delta {delta_in:.2f}, {extr_pct:.0f} % extrinsic. This is the sweet spot — on {ref_day} 60–130 ITM went 18-9 for +₹4.19 L.
  - Right strike: {money:.0f} ITM. Enough delta to track the spot (≈ {delta_pts_per_12:.0f} pts of premium per {trail_pts:.0f} of spot), not so deep that you are paying for intrinsic you cannot lever.
  - Delta {delta_in:.2f}. Each {trail_pts:.0f}-pt spot move is worth ≈ {rs_per_12_txt} to you. Clean.
  - Strike choice is textbook: {money:.0f} ITM vs spot, extrinsic only {extr_pct:.0f} %.

#### `strike.lottery`
- **tone / prio / kind:** lesson / 85 / entry · **fires:** once per trade, from 2 s into the trade
- **when:** `money` < 40 pts ITM vs SPOT or `extr_pct` ≥ 45 %
- **evidence:** money vs spot < 40: 5 trades (13:12, 13:29, 13:44, 14:15, 14:24), 1 win, −₹49.9k, mean peak 6.9 pts
- **phrasings:**
  - {strike} {rr} is only {money:.0f} pts in the money vs spot — {extr_pct:.0f} % of what you paid is time value. On {ref_day} the five such entries went 1-4 for −₹49,933 while the engine's delta read {delta_in:.2f}; delta flattered them.
  - This is a lottery ticket, not a delta trade: {extr_pct:.0f} % extrinsic, {money:.0f} ITM. It needs the spot to move AND move fast.
  - Near-ATM at expiry: delta {delta_in:.2f} now, but it will be 0.5 or 0.95 within the hour. The {trail_pts:.0f}-pt stop does not protect a premium that is mostly air.
  - Strike choice is the weak point of this entry: {money:.0f} ITM vs spot. The band picked the lowest delta ≥ 0.65; on a skewed expiry afternoon that is a near-the-money {rr}.
  - Caution on the contract, not the direction: {extr_pct:.0f} % of {entry:.2f} is extrinsic. Theta here is ≈ {theta_rs_abs:,.0f} ₹/min on your size.

#### `strike.heavy`
- **tone / prio / kind:** caution / 55 / entry · **fires:** once per trade, from 2 s into the trade
- **when:** `money` > 150 or `extr_pct` < 5 %
- **evidence:** no 19 Oct trade was > 130 pts ITM vs spot; 90-130 was the best bin — a cost statement, not an outcome one
- **phrasings:**
  - {strike} {rr} is {money:.0f} pts deep. You are buying mostly intrinsic ({intr_pct:.0f} %), so lots are {lots} instead of ≈ {lots_atm_est} at 75 ITM — less leverage for the same spot move.
  - Deep ITM: delta {delta_in:.2f} is great, but each lot costs {lot_cost_txt}. The trade can still work; it will work slower in % terms.
  - Heavy strike ({money:.0f} ITM). Fewer lots, fatter spread in ₹ — a {trail_pts:.0f}-pt spot move is ≈ {ret_per_12:.1f} % here vs ≈ {ret_per_12_sweet:.1f} % at 75 ITM.

#### `strike.band_fallback`
- **tone / prio / kind:** caution / 70 / entry · **fires:** once per trade, from 2 s into the trade
- **when:** `band_fallback` true (pos.band_fallback from paper._entry_observers)
- **evidence:** never fired on 19 Oct
- **phrasings:**
  - No strike sat inside the delta band; the engine took the nearest one above it (delta {delta_in:.2f}). Expect a deeper, pricier contract than usual.
  - Band fallback: the usual 0.65–0.85 window had nothing live, so you own a {delta_in:.2f}-delta option. Fine for direction, heavier in ₹.
  - Fallback contract (delta {delta_in:.2f}). Did not happen once in 32 trades on {ref_day} — worth a look at the chain if it repeats.

#### `strike.delta_vs_money`
- **tone / prio / kind:** information / 55 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** |`delta_in`| ≥ 0.65 while `money` < 40, or `basis_in` ≥ 15 pts
- **evidence:** all 5 lottery entries on 19 Oct carried delta 0.66-0.73 while 29-39 pts ITM vs spot (basis 24-30 pts)
- **phrasings:**
  - Delta {delta_in:.2f} on a strike only {money:.0f} ITM vs spot — the delta flatters it. Treat this as a near-0.55 option for sizing your expectations.
  - Basis check: future {fut_in:.0f}, spot {spot_in:.0f} ({basis_in:+.0f}). The option settles on spot; it is {money:.0f} ITM, not {money_fut:.0f}.
  - Quoted delta {delta_in:.2f}, real moneyness {money:.0f} vs spot. This is how the band chose a near-the-money strike on an expiry afternoon; worth the owner's review.

#### `strike.rs_per_point`
- **tone / prio / kind:** information / 55 / entry · **fires:** once per trade, from 5 s into the trade
- **when:** always, 5 s after entry: `stop_rs`, `stop_prem` from `trail_pts` × |delta_in| × qty
- **evidence:** informational
- **phrasings:**
  - Your stop ({trail_pts:.0f} pts of spot) is ≈ {stop_prem:.1f} pts of premium ≈ {stop_rs_txt} ({stop_pct:.1f} % of capital). A +{trail_pts:.0f} move is worth about the same the other way.
  - Translation: 1 pt of Nifty ≈ {delta_abs:.2f} pts of premium ≈ {rs_per_pt_txt} on {qty} qty.
  - Risk on this entry: {trail_pts:.0f} spot pts × delta {delta_abs:.2f} × {qty} = {stop_rs_txt}. Know the number before the screen shows it.

### E chase / impulse

#### `chase.late_entry`
- **tone / prio / kind:** information / 55 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** `chase_pts` ≥ 3: spot was ≥ 3 pts past the 12-min level (`break_level` = ctx spot_hi/lo at entry)
- **evidence:** chase ≥ 3: 4 trades, 3 wins, +₹71.5k, mean +10.8 %; 0-0.5: 16 trades, 9 wins, +3.9 %
- **phrasings:**
  - Spot was {chase_pts:.1f} pts past the breakout level ({break_level:.1f}) when you were filled. On {ref_day} that was not a sin — the 4 entries ≥ 3 pts past the level went 3-1, mean +10.8 %. Momentum, not chasing.
  - You entered {chase_pts:.1f} pts beyond the break. Your stop is still {trail_pts:.0f} from the best, so the late entry costs you premium, not safety.
  - Filled {chase_pts:.1f} pts past the level. A little late is fine; the data says the breaks that ran 3+ pts immediately were the real ones.

#### `chase.spot_sprint`
- **tone / prio / kind:** caution / 70 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** `s60` ≥ 20 pts in the trade's direction in the 60 s before the fill
- **evidence:** s60 ≥ 20: 4 trades, 2 wins, +3.3 %; 5-10: 11 trades, 8 wins, +7.7 %
- **phrasings:**
  - Spot sprinted {s60:.0f} pts in the last minute. You are buying into an air-pocket: on {ref_day} the four ≥ 20-pt-in-60-s entries averaged +3.3 % vs +7.7 % for 5–10 pt breaks.
  - {s60:.0f} pts in 60 seconds before your fill. Fast breaks snap back fast — the {trail_pts:.0f}-pt trail will be tested in the first minute.
  - Entered after a {s60:.0f}-pt spot sprint. Not wrong, but the premium you paid already contains it.
  - A one-minute {s60:.0f}-pt move preceded this entry. Expect the first pullback to be sharp; the plan, not the tick, is the thing to watch.

#### `chase.no_push`
- **tone / prio / kind:** caution / 85 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** `s300` < 10 pts in the trade's direction over the 5 min before the fill
- **evidence:** s300 < 10: 6 trades, 3 wins, −₹28.6k, mean −0.9 %; 10-50: 21 trades, 13 wins, +₹3.77 L
- **phrasings:**
  - The break came with no push behind it: spot only {s300:+.0f} pts in 5 minutes. On {ref_day} the six such entries went 3-3 for −₹28,629 — the weakest group of the day.
  - Flat 5-minute tape ({s300:+.0f} pts) into a breakout. It can still work; it usually needs a second impulse. The confidence is not there yet.
  - No momentum behind this entry ({s300:+.0f} pts / 5 min). The level broke on a tick, not on a wave.
  - Breakout on a quiet tape ({s300:+.0f} pts / 5 min). Half of these fail quickly; the stop is doing its job if it does.

#### `chase.good_push`
- **tone / prio / kind:** confidence / 55 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** 10 ≤ `s300` ≤ 50 and 5 ≤ `s60` ≤ 20
- **evidence:** see chase.no_push
- **phrasings:**
  - Good impulse: spot {s300:+.0f} pts over 5 min, {s60:+.0f} in the last minute. The break has a wave behind it, not a single tick.
  - This is what a breakout should look like underneath: {s300:+.0f} / 5 min, steady, not a sprint. 13 of 21 such entries won on {ref_day}.
  - Momentum is right-sized ({s60:+.0f} pts in 60 s, {s300:+.0f} in 5 min). Not chasing, not early.

#### `chase.second_try`
- **tone / prio / kind:** information / 70 / entry · **fires:** once per trade, from 3 s into the trade
- **when:** `same_key` (same contract as the last closed trade), `since_exit` < 600 s, `prev_reason` STOP or TRAIL
- **evidence:** 19 Oct re-entries < 10 min: 09:37 +8.8, 09:55 +30.6, 10:39 +25.3, 12:04 +26.8, 12:23 −7.8, 12:46 +1.9 → 5-1
- **phrasings:**
  - Re-entry on {strike} {rr}, {since_exit:.0f} s after the last exit ({prev_reason}, {prev_ret:+.1f} %). On {ref_day} re-entries within 10 min went {reentry_record}; the second attempt at 09:55 was the day's +30 %.
  - Second attempt at the same break, {since_exit:.0f} s after the last exit. The rule allows it; just notice you are paying the spread twice for one idea.
  - Back in after {since_exit:.0f} s. The level is now tested twice — if it holds this time it tends to run.

### F trend / regime

#### `trend.against_30`
- **tone / prio / kind:** caution / 70 / structure · **fires:** once per trade, from 12 s into the trade
- **when:** `s1800` ≤ −20 (futures 30-min move in the trade's direction, ctx trend30 × dir)
- **evidence:** s1800 ≤ −20: 7 trades, 3 wins, −₹1.2k, +1.8 %; −20..0: 5 trades, 4 wins, +₹1.85 L; not monotonic → CAUTION
- **phrasings:**
  - You are trading against the last 30 minutes ({s1800:+.0f} pts the other way). On {ref_day}, 7 such entries went 3-4 for ≈ 0 — coin-flip territory.
  - Counter-trend on the 30-min: the future has moved {abs_s1800:.0f} pts against your direction since {t_minus30}. The break may be the turn, or a pullback inside the trend.
  - This entry fades the 30-minute move ({s1800:+.0f} pts). Not stupid — the {trail_pts:.0f}-pt stop makes it cheap to be wrong — but expect no help from the wider tape.
  - Against the half-hour trend ({s1800:+.0f} pts). The {ref_day} replay had the engine's trend30 field null on every trade; this one is read live from the futures history.

#### `trend.with_30`
- **tone / prio / kind:** confidence / 40 / structure · **fires:** once per trade, from 12 s into the trade
- **when:** `s1800` ≥ +20
- **evidence:** s1800 ≥ 20: 12 trades, 7 wins, +₹1.51 L, mean +5.4 %
- **phrasings:**
  - With the 30-min trend ({s1800:+.0f} pts). Continuation entries went 7-5 on {ref_day} — not magic, but the wind is at your back.
  - Trend-aligned: the last half-hour already moved {s1800:.0f} pts your way.
  - The wider tape agrees with you ({s1800:+.0f} over 30 min).

#### `trend.regime_against`
- **tone / prio / kind:** caution / 70 / structure · **fires:** once per trade, from 12 s into the trade
- **when:** base fact `regime_with` == −1 (DIRECTIONAL/BREAKOUT regime the other way)
- **evidence:** regime_align False: 3 trades, 2 wins, +₹59k (small n)
- **phrasings:**
  - The regime read is directional the other way ({regime_why}). You are buying a counter-move. 3 of these on {ref_day}: 2 wins, so it is not a veto — but it is a reason to let the trail decide, not hope.
  - Regime says {regime} {regime_arrow}; you are {dir_word}. A short leash is what the trail gives this one.
  - Against the regime direction ({regime} {regime_arrow}). Fine on a {trail_pts:.0f}-pt stop; just do not expect a trend day to turn for you.

#### `trend.regime_range`
- **tone / prio / kind:** caution / 55 / structure · **fires:** once per trade, from 12 s into the trade
- **when:** base fact `regime` ∈ {RANGE, UNCERTAIN, EXHAUSTION}
- **evidence:** RANGE/UNCERTAIN/EXHAUSTION: 8 trades, 3 wins, −₹5.4k; DIRECTIONAL: 9 trades, 7 wins, +₹1.86 L
- **phrasings:**
  - Regime: {regime}. Breakouts in a range regime went 3-5 on {ref_day} (mean +0.3 %) against 7-2 in DIRECTIONAL. Expect a smaller peak — median 11 pts, not 23.
  - Range regime ({regime}). The break may be the edge of the box, not a trend start. Your trail will probably decide this one, not your target.
  - {regime} tape. Half of these entries fail; the other half pay 5–20 %. Nothing to do but let the rule work.

### G time of day

#### `time.hour_stats`
- **tone / prio / kind:** information / 55 / time · **fires:** once per trade, from 10 s into the trade
- **when:** always, 10 s after entry, when `hour` has a row in REFS['hours']
- **evidence:** 9h 7/4 +5.9 %; 10h 5/4 +8.9 %; 11h 4/2 +11.7 %; 12h 6/4 +3.1 %; 13h 6/3 +2.3 %; 14h 4/2 +3.6 %
- **phrasings:**
  - Entries in the {hour:02d}:00 hour: {hour_n} trades, {hour_wins} wins, mean {hour_mean_ret:+.1f} %, mean best excursion {hour_peak:.0f} pts ({ref_day}). That is your base rate right now.
  - Base rate for this hour on {ref_day}: {hour_wins}/{hour_n}, {hour_mean_ret:+.1f} %. Not a prediction — a prior.
  - The {hour:02d}:xx hour paid {hour_pnl_txt} on {ref_day} across {hour_n} entries.

#### `time.pm_entry`
- **tone / prio / kind:** caution / 55 / time · **fires:** once per trade, from 16 s into the trade
- **when:** `time_in` ≥ 12:30:00
- **evidence:** AM: 20 trades, 12 wins, +₹2.55 L, +7.4 %; PM: 12 trades, 7 wins, +₹1.13 L, +2.6 %
- **phrasings:**
  - Afternoon entry ({time_in}). On {ref_day} PM entries averaged +2.6 % with a mean best excursion of 12.7 pts; the morning gave +7.4 % and 19.9 pts. Smaller moves — expect the trail to do the exiting.
  - PM half ({time_in}). Fewer points per move after 12:30 on {ref_day}; the trade is worth taking, the expectation should be half the morning's.
  - After 12:30. The tape gets narrower and IV ramps on expiry; good entries still pay (+20 % at 14:43 on {ref_day}), but the median was +1.7 %.

#### `time.opening_burst`
- **tone / prio / kind:** caution / 55 / time · **fires:** once per trade, from 16 s into the trade
- **when:** `time_in` < 09:40:00
- **evidence:** pre-09:40: 4 trades, 2 wins, +₹9.9k, median hold 31 s
- **phrasings:**
  - Opening burst: σ15 is {sigma15:.1f} pts, spreads are widest and premiums move 50 % in minutes. On {ref_day} the four pre-09:40 entries held a median 31 s and went 2-2.
  - First 15 minutes of the window. Expect to be trailed out in under a minute either way — the {trail_pts:.0f}-pt trail is tiny against a {sigma15:.1f}-pt σ15.
  - Early entry ({time_in}). On {ref_day} these fills were 0.35-pt spreads and premiums at their 5-min highs — the market charges most for the first move.

#### `time.last_window`
- **tone / prio / kind:** caution / 70 / time · **fires:** once per trade, from 16 s into the trade
- **when:** expiry day and `time_in` ≥ 14:15:00
- **evidence:** after 14:15: 3 trades, 1 win, +₹38.8k (one +20 %)
- **phrasings:**
  - {mins_to_flat:.0f} minutes to the forced flat. The trade cannot be a long one; the trail is your only exit besides the clock.
  - Late window: entries stop at 14:45 and you are flat at 15:00. Three {ref_day} entries after 14:15: −2.3 %, −7.0 %, +20.1 %.
  - Clock risk on top of price risk now — {mins_to_flat:.0f} minutes left.

### H size vs liquidity

#### `size.vs_volume`
- **tone / prio / kind:** caution / 70 / book · **fires:** once per trade, from 18 s into the trade
- **when:** `qty_vs_vol` ≥ 2 % of the contract's traded quantity over the window (`vol_win`, `vol_win_s`)
- **evidence:** 19 Oct max qty/vol5 = 0.2 %; threshold 2 % (caution), 5 % (lesson) from market-maker practice, not data
- **phrasings:**
  - Your {qty} qty is {qty_vs_vol5_pct:.1f} % of what this strike traded in the last {vol_win_txt}. Big for the book; the exit will move the price against you.
  - Size warning: {lots} lots on a strike that traded {vol5_lots:,.0f} lots in {vol_win_txt}. On {ref_day} the largest entry was 0.2 % of 5-min volume — you are at {qty_vs_vol5_pct:.1f} %.
  - Liquidity is thinner than your order ({qty_vs_vol5_pct:.1f} % of the last {vol_win_txt}). Expect slippage on the way out, not just on the way in.

#### `size.vs_book`
- **tone / prio / kind:** caution / 70 / book · **fires:** once per trade, from 18 s into the trade
- **when:** `qty_vs_ss` ≥ 50 % of the visible sell-side quantity at entry (`ss_in`)
- **evidence:** 19 Oct sizes 650-6,825 qty → 0.4-4 % of a typical 170k visible book; practice threshold
- **phrasings:**
  - You lifted {qty_vs_ss_pct:.0f} % of the visible ask size ({ss_lots:,.0f} lots across {sso} orders). The book will refill, but the next trader pays more — and so will you on exit.
  - Order larger than half the top-of-book ({qty_vs_ss_pct:.0f} %). Fill was {over_mid:+.2f} over mid — that is where the size shows.
  - Big relative to the visible book ({qty_vs_ss_pct:.0f} % of ask size). Slices are the engine's answer (slices={slices}).

#### `size.all_in_ok`
- **tone / prio / kind:** confidence / 40 / book · **fires:** once per trade, from 18 s into the trade
- **when:** `qty_vs_vol` < 0.5 % and `qty_vs_ss` < 20 %
- **evidence:** all 32 trades on 19 Oct
- **phrasings:**
  - {lots} lots ({qty} qty) is {qty_vs_vol5_pct:.2f} % of the last {vol_win_txt} of volume and {qty_vs_ss_pct:.0f} % of the visible ask. Size is invisible to the market. All-in is fine here.
  - Liquidity check passed: your order is noise against {vol5_lots:,.0f} lots traded in the last {vol_win_txt}.
  - Size is not your problem on this contract ({qty_vs_vol5_pct:.2f} % of recent volume).

#### `size.capital_jump`
- **tone / prio / kind:** information / 55 / day · **fires:** once per trade, from 18 s into the trade
- **when:** `lots` ≥ 1.5 × `prev_lots`, or `capital_deployed` ≥ 90 % of `capital`
- **evidence:** 19 Oct lots 10 → 105; the 13:29 trade (93 lots) lost ₹39.6k — largest size on a lottery strike
- **phrasings:**
  - {lots} lots this time, up from {prev_lots} — the last win is now at risk on this entry. Same {trail_pts:.0f}-pt stop, {stop_rs_txt} at stake instead of {prev_stop_rs_txt}.
  - Capital deployed {capital_deployed_txt} of {capital_txt} ({deployed_pct:.0f} %). All-in by design; just see the number.
  - Size stepped up to {lots} lots after the {prev_ret:+.0f} % trade. The rule compounds; the stop in rupees compounds with it ({stop_rs_txt}).

### I straddle

#### `strad.priced_in`
- **tone / prio / kind:** caution / 70 / structure · **fires:** once per trade, from 14 s into the trade
- **when:** `strad_5` ≥ +5 or `strad_state_in` == EXPANDING
- **evidence:** strad_5 ≥ +5: 6 trades, 4 wins, +₹92.9k (mixed); ≤ −2: 13 trades, 9 wins, +₹2.38 L
- **phrasings:**
  - The ATM straddle went from {strad_5ago:.1f} to {strad_px_in:.1f} in 5 min ({strad_5:+.1f}). The market is paying up for a move — you are buying after it was priced. {ref_day} 09:27 / 09:28 (+21, +32): +7.9 %, −0.8 %.
  - Straddle expanding ({strad_5:+.1f} / 5 min). Your option is dearer than it was; if spot delivers, the expansion helps, if not it reverses on you.
  - Move priced: straddle {strad_px_in:.1f} vs VWAP {strad_vwap_in:.1f}. You need spot to beat what the straddle already implies — about {implied_move:.0f} pts to the close.
  - The straddle re-priced before you ({strad_5:+.1f} in 5 min). Not a stupid entry — an expensive one.

#### `strad.compressing`
- **tone / prio / kind:** confidence / 55 / structure · **fires:** once per trade, from 14 s into the trade
- **when:** `strad_5` ≤ −2
- **evidence:** see strad.priced_in
- **phrasings:**
  - Straddle compressing ({strad_5:+.1f} in 5 min, {strad_state_in}). You bought the option while the market was giving vol away — the cheapest state. 13 such entries on {ref_day}: 9 winners, mean +7.8 %.
  - Vol was deflating into your entry (straddle {strad_px_in:.1f}, VWAP {strad_vwap_in:.1f}). A real move from here gets paid twice: delta and re-expansion.
  - Straddle {strad_5:+.1f} in 5 min and below VWAP {strad_vwap_in:.1f}. Good moment to own gamma.

#### `strad.flat`
- **tone / prio / kind:** information / 25 / structure · **fires:** once per trade, from 14 s into the trade
- **when:** −2 < `strad_5` < 2
- **evidence:** −2..2: 7 trades, 4 wins, +₹10k, mean +1.0 %
- **phrasings:**
  - Straddle flat ({strad_5:+.1f} / 5 min). The option market has no opinion on this break yet — the 7 flat-straddle entries on {ref_day} averaged +1.0 %.
  - No vol signal either way (straddle {strad_px_in:.1f}, {strad_5:+.1f} in 5 min). Spot has to do all the work.
  - The straddle ({strad_5:+.1f} / 5 min) is not confirming or denying the break.

### J room

#### `room.into_wall`
- **tone / prio / kind:** caution / 70 / structure · **fires:** once per trade, from 20 s into the trade
- **when:** `room_in` ≤ 25 pts to the next OI wall in the trade's direction (`wall_in`)
- **evidence:** 19 Oct: room advisor never vetoed (nearest wall 360-521 pts); threshold 25 = 2× stop + the 'need ~19'
- **phrasings:**
  - Entering {room_in:.0f} pts from the {wall_in:.0f} wall ({wall_oi_lots:,.0f} lots OI). You need ≈ 19 pts to pay; the wall is closer than that. If it holds, you are trailed out at the wall.
  - The next OI wall is at {wall_in:.0f} — {room_in:.0f} pts away. The room advisor said '{room_why}'. Tight.
  - Little room: {room_in:.0f} pts to {wall_in:.0f}. Walls break on expiry day, but they break after a fight; the first touch usually rejects.
  - Wall ahead at {wall_in:.0f}. Your best case before it is ≈ {room_in:.0f} pts × delta {delta_abs:.2f} = {room_prem:.0f} pts of premium.

#### `room.open_road`
- **tone / prio / kind:** confidence / 40 / structure · **fires:** once per trade, from 20 s into the trade
- **when:** `room_in` ≥ 100 pts
- **evidence:** all 11 logged on 19 Oct
- **phrasings:**
  - Open road: next wall {wall_in:.0f} is {room_in:.0f} pts away. Nothing on the chain stands between you and a full run.
  - {room_in:.0f} pts of room to {wall_in:.0f}. The trail, not a wall, will decide this one.
  - No OI wall within {room_in:.0f} pts. Good.

#### `room.stale_chain`
- **tone / prio / kind:** information / 25 / data · **fires:** once per trade, from 20 s into the trade
- **when:** `chain_age_in` ≥ 180 s
- **evidence:** informational
- **phrasings:**
  - The wall map is {chain_age_in:.0f} s old (chain polls every 90 s). Treat room numbers as approximate.
  - OI data is {chain_age_in:.0f} s stale; walls may have moved.

### K quote

#### `quote.stale_trade`
- **tone / prio / kind:** caution / 55 / data · **fires:** once per trade, from 22 s into the trade
- **when:** `trade_age_in` ≥ 5 s (now − exchange last-trade time at the fill)
- **evidence:** trade_age 1-5 s: 10/3 (−₹27k); 5-30 s: 7/6 (+₹2.36 L): no direction signal — fill honesty only
- **phrasings:**
  - The contract had not traded for {trade_age_in:.0f} s when you were filled at {entry:.2f}. In paper you got the LTP; live you would have paid the ask ({entry_ask:.2f}) — {ask_minus:+.2f}.
  - Stale last-trade ({trade_age_in:.0f} s). The paper fill is optimistic by up to the spread. On {ref_day} the two 10 s+ stale entries were the two best trades of the day (+23.7 %, +26.8 %) — so stale is not bad, just uncertain.
  - No print for {trade_age_in:.0f} s before entry. Your 'entry' is a quote, not a trade — judge this one by the bid/ask ({entry_bid:.2f}/{entry_ask:.2f}), not the LTP.
  - Quiet contract at entry ({trade_age_in:.0f} s since last trade). The engine refuses quotes ≥ 15 s old; this one was fine, just slow.

#### `quote.wide_or_crossed`
- **tone / prio / kind:** caution / 70 / data · **fires:** once per trade, from 22 s into the trade
- **when:** `entry_bid` ≤ 0, or `entry_ask` < `entry_bid`, or `spread_pct` > 2 %
- **evidence:** never on 19 Oct (all spreads 0.15-0.35, two-sided)
- **phrasings:**
  - The book was {entry_bid:.2f}/{entry_ask:.2f} at your fill — not a healthy two-sided quote. The entry price is less certain than it looks.
  - Crossed or one-sided quote at entry. Paper filled you at LTP {entry:.2f}; a live order could have printed anywhere in {entry_bid:.2f}–{entry_ask:.2f}.
  - Quote quality was poor at the fill ({entry_bid:.2f}/{entry_ask:.2f}). The exit quote age deserves the same look.

#### `quote.feed_lag`
- **tone / prio / kind:** caution / 70 / data · **fires:** once per trade, from 22 s into the trade
- **when:** `lag_s_in` ≥ 1.0 s (eng.data_health lag on the Nifty index at entry)
- **evidence:** informational; 19 Oct replay lag n/a
- **phrasings:**
  - Feed lag was {lag_s_in:.1f} s at entry. The spot break you traded was {lag_s_in:.1f} s old by the time the order went — the premium may already reflect it.
  - Your fill came on a laggy feed ({lag_s_in:.1f} s). Everything you see is slightly behind; the trail will be slightly late too.
  - Lag {lag_s_in:.1f} s. Not your fault; it is still your cost.

### L noise vs stop

#### `noise.stop_inside_sigma`
- **tone / prio / kind:** caution / 85 / structure · **fires:** once per trade, from 8 s into the trade
- **when:** `sigma15` ≥ 8 pts
- **evidence:** sigma15 7-9: 5 trades, 2 wins, +₹1.4k, +0.5 %; 5-7: 5 trades, 5 wins, +12.0 %
- **phrasings:**
  - σ15 is {sigma15:.1f} pts; your stop is {trail_pts:.0f}. The noise alone can take you out. On {ref_day} the five σ15 > 7 entries went 2-3 for +₹1,388 — a wash.
  - Noisy tape ({sigma15:.1f} pts σ15). A {trail_pts:.0f}-pt trail here is a coin, not a stop. Expect a quick exit either way.
  - Stop is inside the noise band (σ15 {sigma15:.1f}). This is the structural weakness of a fixed {trail_pts:.0f}-pt trail at the open.
  - σ15 {sigma15:.1f} vs stop {trail_pts:.0f}: the market can hit your stop without changing its mind.

#### `noise.stop_well_sized`
- **tone / prio / kind:** confidence / 40 / structure · **fires:** once per trade, from 8 s into the trade
- **when:** 5 ≤ `sigma15` < 7
- **evidence:** see noise.stop_inside_sigma
- **phrasings:**
  - σ15 {sigma15:.1f} pts: the {trail_pts:.0f}-pt stop is about 2σ of the 15-min noise — sized right. All five such entries won on {ref_day} (mean +12 %).
  - Noise is {sigma15:.1f} pts; the stop ({trail_pts:.0f}) is comfortably outside it. The trade will be decided by direction, not by jitter.
  - Stop vs noise: {trail_pts:.0f} vs {sigma15:.1f}. Good ratio.

#### `noise.range5_wide`
- **tone / prio / kind:** caution / 55 / structure · **fires:** once per trade, from 8 s into the trade
- **when:** `range5` ≥ 40 pts (futures 5-min high−low at entry)
- **evidence:** range5 ≥ 40: 7 trades, 5 wins, +₹68k; 15-25: 13 trades, 6 wins, +₹18k
- **phrasings:**
  - The last 5 minutes spanned {range5:.0f} pts — three stops' worth. The break is inside a violent bar, not after a tight base.
  - 5-min range {range5:.0f} pts. Big bars give big peaks (mean 17 pts on {ref_day}) and big whips; both are coming.
  - Wide 5-min range ({range5:.0f}). The rule, not the breath, is the thing to hold.

### M composite

#### `entry.stupid`
- **tone / prio / kind:** lesson / 85 / entry · **fires:** once per trade, from 0 s into the trade
- **when:** `entry_grade` == E (score ≤ −3)
- **evidence:** E: 4 trades, 0 wins, −₹55.6k (in-sample)
- **phrasings:**
  - Honest read: this was a poor entry — {reason_1}; {reason_2}. On {ref_day} the four grade-E entries went 0-4 for −₹55,591. The rule still gets its {trail_pts:.0f} pts; expect to need luck.
  - Grade E. Not the direction — the price and the contract: {reason_1}, {reason_2}. The trail does its work; nothing to add to it in your head.
  - You know what this is: {reason_1}. Take the lesson now, the result later.
  - This entry paid for everything at once: {reason_list}. The stop is cheap; the discipline is to let it be cheap.

#### `entry.costly_not_stupid`
- **tone / prio / kind:** lesson / 70 / entry · **fires:** once per trade, from 0 s into the trade
- **when:** `entry_grade` C or D, not a lottery strike, `s300` ≥ 10, and at least one of: fill > 0.30 over mid / IV ≥ p90 and +3 vs 30 min / `rise5` ≥ 50 / `strad_5` ≥ 5
- **evidence:** C: 3/2 +₹38k; D: 4/2 +₹7k on 19 Oct
- **phrasings:**
  - Right idea, expensive ticket: {reason_1}. Direction is fine; you simply paid up. Each extra point paid is a point the trail must earn before you see green.
  - Costly, not stupid — {reason_1}. The {ref_day} grade-C/D entries still went 4-3 (+₹44.7k); the price you paid lowers the average, it does not kill the trade.
  - The entry is sound, the price is rich ({reason_1}). The edge is smaller, not gone.

#### `entry.clean`
- **tone / prio / kind:** confidence / 85 / entry · **fires:** once per trade, from 0 s into the trade
- **when:** `entry_grade` == A (score ≥ 4)
- **evidence:** A: 16 trades, 11 wins, +₹2,77,739, mean +9.2 %, mean peak 21.6 pts (in-sample)
- **phrasings:**
  - Clean entry, grade A: {reason_1}; {reason_2}; {reason_3}. On {ref_day} grade-A entries went 11-5 for +₹2.78 L, mean +9 %, mean best excursion 22 pts. You have done your part — now the holding.
  - Grade A (score {entry_score:+d}). Nothing to fix about this entry: {reason_list}. If it loses, it loses honestly.
  - This is what a good entry looks like in numbers (score {entry_score:+d}): {reason_list}. The plan is the thing to hold.
  - A-grade fill and contract ({reason_1}; {reason_2}). On {ref_day} 11 of 16 A-entries won. The market still decides, but you are not starting from behind.

#### `entry.what_it_cost`
- **tone / prio / kind:** information / 55 / entry · **fires:** once per trade, from 30 s into the trade
- **when:** once, 30 s after entry: `over_mid_rs`, `day_over_mid_rs`, `extr_pct` (≥ 45 % adds the extrinsic clause)
- **evidence:** 19 Oct: Σ over-mid ₹24,963; Σ full-spread round trip ₹21,899; buy@ask/sell@bid would have made ₹3.83 L vs ₹3.69 L
- **phrasings:**
  - This entry's price tag vs ideal: spread {over_mid_rs_txt}{extr_clause}. Day so far: {day_over_mid_rs_txt} of spread. On {ref_day} the whole day's entry tax was ₹24,963 against ₹3.69 L of profit — 6.8 %.
  - Cost of entering: {over_mid_rs_txt} on the spread. Running total today {day_over_mid_rs_txt}.
  - Entry tax {over_mid_rs_txt}. Small; the strike and the timing are where the real money is made or lost.

#### `entry.second_look_60s`
- **tone / prio / kind:** information / 55 / entry · **fires:** once per trade, from 60 s into the trade
- **when:** once, 60 s after entry: `ret_now`, `spot_vs_in`, `best_vs_in`, `entry_look`, `cost_status`
- **evidence:** 19 Oct median hold 144 s; 5 of 13 losers were out inside 40 s, the other 8 bled 89-540 s
- **phrasings:**
  - One minute in: premium {ret_now:+.1f} %, spot {spot_vs_in:+.0f} from entry, best {best_vs_in:+.0f}. The entry price now looks {entry_look} — the market, not the grade, says so.
  - 60-s check: you are {ret_now:+.1f} % from your fill. The entry cost ({over_mid:.2f} over mid) is {cost_status}.
  - After a minute the fill reads as {entry_look}: spot {spot_vs_in:+.0f}, premium {ret_now:+.1f} %.

#### `entry.vix_context`
- **tone / prio / kind:** information / 25 / structure · **fires:** once per trade, from 25 s into the trade
- **when:** once, 25 s after entry, when `vix` is available
- **evidence:** VIX ≤ 14.7: 17 trades, 11 wins, +₹3.0 L; > 14.7: 15 trades, 8 wins, +₹68.6k
- **phrasings:**
  - VIX {vix:.2f} (seen {vix_lo:.2f}–{vix_hi:.2f} today). On {ref_day} entries with VIX ≤ 14.7 averaged +9.4 %; above it +1.3 % — mostly a time-of-day effect, but it is the air you are breathing.
  - VIX {vix:.2f}. Low and steady on {ref_day}; moves were short. Higher VIX days pay more per break and whip more.
  - Vol context: VIX {vix:.2f}.


## 11.2 The heavyweight basket — `apex/engine/cmt_basket.py` (team T07)

*"Which stocks are with me, which stock ruined it."* While the champion holds, this module watches the 14 tracked
Nifty heavyweights (61.4 % of the index) and speaks only from ONE new computation — each stock's Nifty-point
contribution **since your entry** — plus facts the engine already had (domino 15-s z and activity tiles, the flow
classes and aggressive flow per stock, the episode's first mover). 71 templates, 188 phrasings (T07 wrote 185; three
single-phrasing keys got a second line because the core requires two). The core's own `contrib / helpers / hurters`
facts are untouched; everything this module adds is prefixed `eq_`.

### Evidence (19 Oct 2026, pack.npz, the 32 champion trades — one day, so every claim below is a description)

* **The core fact works as a story-teller.** Entry / +60 s / best / exit facts for all 32 trades are in
  `work_T07/facts_32_trades.txt`. The +37.9-pt 09:55 PE was ICICIBANK +8.2 and HDFCBANK +3.2 with 11 of 14 names with
  it at the best; the −10.1-pt 09:52 PE was reversed by RELIANCE (−2.0) and ICICIBANK (−1.6) with 2 of 14 left; the
  12:04 PE was trailed out on the index print while the basket was still rising (+31.0 vs +24.0 at the best, 14/14);
  the 13:30 PE never had a single name with it (0/14 at the best, 9 against at the exit).
* **Breadth has no monotone edge.** Every second with a ≥ 8-pt 60-s move, continuation over the next 60 s by the
  number of names with the move: 0–3 → −4.0 pts (n = 11) · 4–6 → −0.0 (548) · 7–9 → −1.5 (2 565) · 10–14 → +0.6
  (3 067). So breadth remarks *describe what is carrying the move*; they never argue a hold, and any warning ≥ 75
  silences every cheer in the same second (`eq_hot`).
* **Trade level (partly mechanical):** at +30 s winners had breadth 6.9/14 and basket +8.0 pts, losers 2.7/14 and
  +0.2; basket ≥ +5 at +30 s → +160.9 pts over 15 trades vs +46.1 over 17. A trade whose basket is +5 is already in
  profit, so this supports describing, not acting.
* **AIR at entry** (print ≥ 5 pts with ≤ 3 names, or concentration ≥ 0.5, or basket < 40 % of the print) was 16 % of
  winners and 15 % of losers → `breakout_on_air` is a warning, not a veto. Live AIR with ≤ 3 names was 11 seconds of
  6 191 and reverted −4 pts in the next minute: too few to call an edge, so `thin_move` says "a count, not a forecast".
* **Stock futures do not lead cash at 1 Hz.** Cross-correlation of 5-s returns, lags −8…+8 s: best lag 0 s for 11 of
  14 names, +1 s for KOTAKBANK / ITC / HINDUNILVR; after a futures lead ≥ +3 pts the next 30 s of spot was +0.16 vs
  −0.14 unconditional (noise). The G templates are therefore `information` at prio 15–20, fire only at ≥ 5 pts, and
  say "running ahead", never "leading".
* **Aggressive flow does not forecast.** The 30-s weight-averaged flow imbalance correlates 0.70 with the *current*
  30-s spot move and 0.00 with the *next* 30 s. The H templates are present tense ("is being pressed"), prio ≤ 70.

### The facts this module adds (all signed in the trade's favour: + = helping a CE that needs a rise, a PE that needs a fall)

Notation: `d` = ±1, `N0` = spot at entry, `w_i` = index weight / 100, `EQ_i(t)` cash LTP. `th_i = w_i · 0.0003 · N0`
is "meaningful" (0.03 % of the stock: HDFCBANK ≈ 0.7 pts, HINDUNILVR ≈ 0.13 pts at 23 000). Source for all of them:
`eng.m.ltp[row, eng.m.k]` for rows `eng.key["<SYM>|EQ"]` / `"|FUT"`, `eng.domino.eq_ids / eq_w / eq_sym / state.tiles`,
`eng.flow.agg_b / agg_s / cls_b / cls_s`, `ctx["episode"]`, `eng.m.snap["close"]`, plus the module's own 1-Hz ring
(960 s of eq ltp, stock-future ltp, net aggressive flow per name).

| fact | meaning |
|---|---|
| `eq_n`, `eq_syms_fresh` | names with a usable entry print (a NaN at entry with no fresh print ≤ 5 s old is excluded: "of 13") |
| `eq_rows` | per stock: `sym w grp pct pts help th help60 help30 run_with run_against z act cls_b cls_s` |
| `eq_breadth_with / _against / _flat`, `eq_wpct_with` | `#{help > th}`, `#{help < −th}`, the rest; weight-breadth in % of tracked weight |
| `eq_with60`, `eq_breadth_chg60`, `eq_leavers`, `eq_max_with` | breadth a minute ago, its change, the names that were with and no longer are, the trade's peak breadth |
| `eq_spot_pts` | `d · (spot − N0)` (the core's `spot_fav`) |
| `eq_basket_pts_scaled` | `d · Σ pts_i · 100 / Σ w` — what the tracked 61 % implies for Nifty |
| `eq_gap_vs_print`, `eq_ratio` | basket − print (+ = stocks ahead), basket / max(print, 1) |
| `eq_basket60`, `eq_abs_sum` | basket a minute ago; `Σ|pts_i|` |
| `eq_concentration`, `eq_conc_sym`, `eq_air` | `max|pts| / Σ|pts|`, that name, and AIR = print ≥ 5 and (with ≤ 3 or conc ≥ 0.5 or ratio < 0.4) |
| `eq_help_pos`, `eq_help_neg` | `Σ help>0`, `Σ |help<0|` |
| `eq_top_sym/_help/_pct/_share/_run_with/_run_against`, `eq_top2_*`, `eq_top3_*`, `eq_top60_sym`, `eq_top_help60` | the three biggest helpers; the top helper's share of the positive help, its flow runs, who led 60 s ago |
| `eq_bot_sym/_help/_pct/_run_against` | the biggest hurter |
| `eq_flips`, `eq_flip_against`, `eq_flip_with`, `eq_pair_flip_banks` | names whose help changed sign vs 60 s ago with both sides > th; the largest each way; HDFCBANK and ICICIBANK both flipped against within 60 s |
| `eq_turn`, `eq_new_helper` | 30-s change of help per name; a name whose turn ≥ max(1, 3 th) that was not a helper 30 s ago |
| `eq_new_best`, `eq_best_t`, `eq_best_hms`, `eq_with_at_best`, `eq_basket_at_best` | the book's `best_spot` improved this second; what the basket looked like then |
| `eq_print_giveback`, `eq_basket_giveback` | print retrace from the best (`spot_retrace`); basket(best) − basket(now) |
| `eq_swing_sym/_giveback/_at_best/_now` | the stock that gave back the most since the best, if ≥ max(1, 25 % of the print's give-back) |
| `eq_giveback_n/_max/_max_sym`, `eq_giveback_top` | how many names gave back, the largest, the top two (sym, pts) |
| `eq_made` | `help_i` at the best, descending — "who built the best" |
| `eq_sector_banks/_banks_with/_it/_it_with/_ril/_other/_rest`, `eq_sector_against`, `eq_all_sectors_on`, `eq_lone_sector`, `eq_opposite_pair`, `eq_infy`, `eq_tcs`, `eq_hdfc_help`, `eq_big_bank_against` | sector sums and with-counts; a sector of ≥ 2 names with none with and sum ≤ −1; every sector ≥ 0; one sector ≥ 70 % of the help; one name ≥ +1 and another ≤ −1 in the same sector; HDFCBANK / ICICIBANK at ≤ −1 |
| `eq_fut_lead`, `eq_basis_bps` | 15-s stock-futures basket move minus cash basket move (pts, in favour); weight-averaged basis change since entry (bp, in favour) |
| `eq_flow_with / _against`, `eq_flow_with_wpct / _against_wpct`, `eq_pressed_name`, `eq_fought_name`, `eq_top_pulled`, `eq_refilling` | names whose 10-s net aggressive flow has run with / against the trade for ≥ 30 s (≤ 120), their weight; a helper pressed ≥ 40 s, a hurter fought ≥ 40 s; the top helper's holding side PULLED; helpers whose breaking side is REFILLING |
| `eq_first_mover`, `eq_first_mover_t`, `eq_ep_type`, `eq_ep_age`, `eq_ep_ncross`, `eq_ep_with` | `episode.first` etc. when the episode is in the trade's direction and began ≤ 120 s before entry |
| `eq_pre_ref_s`, `eq_pre_rows`, `eq_pre_with/_against/_basket/_spot/_ratio/_top/_bot/_bank_with/_makers` | the breakout before entry: reference 90 s back from the module ring when it has it, else the market ring's 60-s slot (`eq_pre_ref_s` says which) |
| `eq_day_with`, `eq_day_leader/_chg`, `eq_day_laggard/_chg` | % vs previous close at entry |
| `eq_wave_with / _against`, `eq_vol_dry_n` | names with domino 15-s z ≥ 2 in / against the trade's direction; names with activity < 0.5 |
| `eq_hot` | a T07 warning with prio ≥ 75 holds this second → every `confidence` template in this module is silent |

Tone mapping (T07 → core): `confident` → **confidence**, `warning` ≥ 75 → **warning** (bypasses the budget, wins the
second), `warning` < 75 → **caution**, `descriptive` and `colour` → **information**, `review` → **lesson** (kind
`review`, never fired live; `cmt_basket.review_lines(trade, last_facts)` renders up to two for the review card).
Phrasing choice is the core's `crc32(trade_id:key:n)`. Stock names are plain symbols so the panel can chip them.
Slot values are strings built by `cmt_basket.S(f)`: `{pts}`-style numbers carry their sign and one decimal, `{pct}` two
decimals, counts are integers, "of 14" is `{n}` (the fresh count).

### The templates

### A. Helpers

**`lead_helper`** · tone **confidence** · prio 60 · cool-down 90 s, re-fires when `eq_top_help` moves ≥ 2  
when: A1: top helper >= max(2, 35 % of the positive help) with the print >= 6 in favour.  
- "{sym} alone has given you {pts} of your {tot} basket points."
- "The engine room is {sym}: {pts} points of the {tot} the basket has moved for you."
- "{sym} is carrying this — {pct} % since your entry, worth {pts} Nifty points."
- "If you want to know who is paying for this trade: {sym}, {pts} points."
- "{sym} is doing the heavy lifting ({pts} of {tot}). The rest are passengers so far."

**`two_helpers`** · tone **confidence** · prio 55 · cool-down 120 s, re-fires when `eq_top2_share` moves ≥ 0.15  
when: A2: the top two helpers are >= 60 % of the positive help, both meaningful.  
- "{sym1} and {sym2} are your trade: {pts1} and {pts2} points between them."
- "Two engines running — {sym1} ({pts1}) and {sym2} ({pts2}). Everyone else is a rounding error."
- "This is a {sym1}–{sym2} move: {share2} % of the basket's help is those two names."
- "{sym1} started it, {sym2} is finishing it: {pts1} + {pts2} points."

**`helper_pressed`** · tone **confidence** · prio 50 · cool-down 90 s, re-fires when `eq_top_run_with` moves ≥ 30  
when: A3: top helper with net aggressive flow in the trade's direction for >= 30 s (present tense: flow describes, it does not forecast).  
- "{sym} is your best name ({pts}) and {side} have been pressing it for {secs} s."
- "{sym}: {pts} points for you, and the aggressive flow there has been on your side for {secs} seconds."
- "Not just drifting — {sym} is being hit by {side} for {secs} s straight, and it is your top contributor."

**`new_helper`** · tone **confidence** · prio 45 · cool-down 60 s, re-fires when `eq_breadth_with` moves ≥ 1; not before 30 s in the trade  
when: A4: 30-s turn >= max(1, 3 th), now meaningful, was not a helper 30 s ago.  
- "{nsym} just joined the move: {nturn} points in the last 30 s."
- "A new recruit — {nsym} has come across to your side ({npts} now)."
- "{nsym} woke up: {nturn} points for you in half a minute."
- "Add {nsym} to the list of names working for you ({npts})."

**`helper_share_small`** · tone **confidence** · prio 40 · cool-down 180 s  
when: A5: top helper < 25 % of the positive help and breadth >= 8.  
- "No single star — the biggest helper is {sym} at only {pts}; this is {with} names pulling together."
- "Help is spread thin and wide: {with} names, none above {pts}. A crowd, not a hero."
- "Nobody owns this move; {with} heavyweights are each giving a little."


### B. Hurters

**`lead_hurter`** · tone **caution** · prio 65 · cool-down 90 s, re-fires when `eq_bot_help` moves ≥ 1  
when: B1: bottom hurter <= -max(1, 2 th) while the print is >= 3 in favour.  
- "{hsym} is the one fighting you: {hpct} % while the rest of the basket {dirword_s}."
- "Your drag is {hsym} — {hpts} points against, the biggest in the basket."
- "{hsym} has not read the memo: {hpct} % against your {opt}."
- "One name is leaning the other way: {hsym}, costing you {hpts} points."
- "{hsym} is the anchor on this trade ({hpts})."

**`big_bank_against`** · tone **caution** · prio 70 · cool-down 120 s, re-fires when `eq_hdfc_help` moves ≥ 1  
when: B2: HDFCBANK or ICICIBANK at help <= -1.0 pt.  
- "{bbsym} is against you, and it is {bbw} % of the index — the heaviest name you track is on the other side."
- "Note the weight: {bbsym} ({bbw} % of Nifty) is {bbpct} % the wrong way. It does not take much from it to undo the rest."
- "The biggest bank is not with you: {bbsym} {bbpts}. The trade is winning in spite of it, not because of it."

**`hurter_pressed`** · tone **caution** · prio 60 · cool-down 90 s, re-fires when `eq_bot_run_against` moves ≥ 30  
when: B3: bottom hurter with aggressive flow against the trade for >= 30 s.  
- "{hsym} is being pressed against you — aggressive {oside} for {hsecs} s and {hpts} points lost there."
- "The fight is in {hsym}: {oside} hitting it for {hsecs} seconds, {hpts} against you."
- "{hsym}: {oside} have been in control for {hsecs} s. That is where your trade is being contested."

**`hurters_outnumber_helpers_pts`** · tone **warning** · prio 75 · cool-down 60 s, re-fires when `eq_help_neg` moves ≥ 1  
when: B4: Σ|help<0| > Σ help>0 while the print is still in favour.  
- "The stocks against you now outweigh the stocks with you ({neg} vs {pos} pts); the index is up on names we do not track."
- "Basket says {tot}, print says {spot}. The heavyweights have stopped paying for this."
- "More weight is leaning against the trade than for it. The profit on screen is not coming from the basket."

**`sector_against`** · tone **caution** · prio 50 · cool-down 150 s  
when: B5: a sector with >= 2 names, none with, sum <= -1.0.  
- "{sector_a} is not playing: {sector_a_n} of {sector_a_n} against you, {sector_a_pts} points."
- "The whole {sector_a} block is on the other side ({sector_a_pts})."
- "{sector_a} has decided this is not a {dirword}: {sector_a_list}."


### C. Breadth

**`broad_move`** · tone **confidence** · prio 70 · cool-down 120 s, re-fires when `eq_breadth_with` moves ≥ 2  
when: C1: with >= 10, against <= 1, print >= 8. Descriptive confidence: no 60-s edge was found on 19 Oct.  
- "{with} of {n} heavyweights are with you — this is a real move, not an index print."
- "Breadth {with}/{n}, {against} against. The whole basket is leaning your way."
- "You are not fighting anyone: {with} names with you, {against} meaningfully against."
- "This has weight behind it — {with} of the {n} names we track, {wpct} % of tracked weight."
- "Count them: {with} heavyweights {dirword_ing} with your {opt}."

**`full_house`** · tone **confidence** · prio 80 · cool-down 180 s  
when: C2: with >= 13.  
- "{with} of {n}. Every sector, every bank. As broad as a move gets."
- "{with}/{n} — the entire basket is on your side right now."
- "Full house: {with} of {n}, nobody meaningful against."

**`half_breadth`** · tone **information** · prio 40 · cool-down 150 s  
when: C3: 5 <= with <= 8, against <= 3.  
- "A split basket: {with} with you, {against} against, the rest flat."
- "Half the heavyweights are in ({with}/{n}). Enough to move the index, not enough to call it a stampede."
- "{with} names are doing the work; {flat} have not chosen a side yet."

**`thin_move`** · tone **warning** · prio 85 · cool-down 60 s, re-fires when `eq_breadth_with` moves ≥ 1  
when: C4: AIR with breadth <= 3 and print >= 5. On 19 Oct n = 11 seconds: a warning, never a forecast.  
- "Only {with} names are moving; the index is being dragged by {sym} — a reversal there would undo this."
- "Thin: {with} of {n}. The print says {spot} but the basket says {tot}. This is {csym}'s move, not the market's."
- "The index is moving on air — {with} heavyweights with you, {against} against. That is the count, not the print."
- "You are {spot} up on the print and the stocks have not come: basket {tot}, {with} names."

**`concentrated`** · tone **caution** · prio 65 · cool-down 120 s, re-fires when `eq_concentration` moves ≥ 0.1  
when: C5: max|pts| / Σ|pts| >= 0.5 with the print >= 5.  
- "{csym} is {cshare} % of everything the basket has done. One name. If it turns, the trade turns."
- "Concentration {cshare} % in {csym}. Not a basket move — a single-name move wearing an index costume."
- "Everything is riding on {csym} ({cshare} % of the basket's net move)."

**`breadth_rising`** · tone **confidence** · prio 55 · cool-down 90 s, re-fires when `eq_breadth_with` moves ≥ 2; not before 60 s in the trade  
when: C6: with(t) - with(t-60) >= 3.  
- "The move is spreading: {with} names now, {with60} a minute ago."
- "Recruitment — {gain} more heavyweights joined in the last minute ({with}/{n})."
- "Breadth is building, {with60} → {with}. The basket is catching up with the print."

**`breadth_falling`** · tone **warning** · prio 80 · cool-down 60 s, re-fires when `eq_breadth_with` moves ≥ 1; not before 60 s in the trade  
when: C7: with(t) - with(t-60) <= -3 with the print >= 3.  
- "Names are leaving: {with60} with you a minute ago, {with} now. {leavers} let go."
- "The basket is thinning out — {with}/{n}, down from {with60}. The print is holding; the stocks are not."
- "You have lost {loss} heavyweights in a minute ({leavers}). That is how reversals start — not a forecast, a count."

**`basket_zero`** · tone **warning** · prio 90 · cool-down 60 s  
when: C8: with = 0 after 15 s with the print not against.  
- "No heavyweight is past its entry print. The breakout you bought is not in the stocks."
- "Zero of {n}. Whatever moved the index, it was not these names."
- "The basket has not moved at all ({tot}). You are long an index print."


### D. Basket vs print

**`basket_confirms`** · tone **confidence** · prio 60 · cool-down 150 s, re-fires when `eq_basket_pts_scaled` moves ≥ 5  
when: D1: basket/print >= 0.8, print >= 8, with >= 7.  
- "Basket {tot}, print {spot}: the stocks confirm the breakout."
- "This is not a futures-only move — the cash names account for {ratio} % of what Nifty printed."
- "The index says {spot}, the heavyweights say {tot}. They agree."

**`basket_ahead`** · tone **confidence** · prio 65 · cool-down 120 s, re-fires when `eq_gap_vs_print` moves ≥ 3  
when: D2: gap = basket - print >= max(4, 30 % of the print), with >= 7.  
- "The stocks are AHEAD of the index: basket {tot} vs print {spot}. The print has {gap} points of catching up to do."
- "Nifty has not caught up with its own constituents — basket {tot}, spot {spot}."
- "There is {gap} points of basket move that the index has not printed yet."

**`basket_behind`** · tone **warning** · prio 75 · cool-down 90 s, re-fires when `eq_gap_vs_print` moves ≥ 3  
when: D3: print - basket >= max(4, 40 % of the print), print >= 6.  
- "The index is ahead of its stocks: print {spot}, basket only {tot}. {gap} points of this is not in the heavyweights."
- "Spot {spot}, basket {tot}. The names we track explain less than half of this print."
- "This profit rests on the print — the basket is {tot} and the index is {spot}; the difference is names we cannot see, or air."

**`trailing_on_air`** · tone **information** · prio 70 · cool-down 60 s, re-fires when `eq_print_giveback` moves ≥ 3  
when: D4: print retrace >= 8 while the basket is within 1 pt of its value at the best and with >= 10 (19 Oct 12:04 PE). Colour: the exit rule is the owner's.  
- "The print has pulled back {pb} from the best but the basket has not — still {tot}, {with} names with you. The stocks did not reverse."
- "Index pull-back {pb}; basket pull-back {bpb}. This retrace is in the index, not in the heavyweights."
- "Your trail is being tested by the print, not by the stocks: basket {tot}, {with}/{n} still on side."

**`basket_reversed`** · tone **warning** · prio 85 · cool-down 60 s, re-fires when `eq_basket_giveback` moves ≥ 3  
when: D5: basket(best) - basket(now) >= 8 and with <= 6.  
- "The basket has given back {bpb} points since your best and {with} names remain. The move is over in the stocks."
- "Stocks have reversed: basket from {bbest} at the best to {tot} now. The index is following them."
- "This is a real reversal, not noise — the basket lost {bpb} and {leavers} led it."


### E. Flips and the swing stock

**`flip_against`** · tone **warning** · prio 80 · cool-down 60 s, re-fires when `eq_breadth_against` moves ≥ 1; not before 60 s in the trade  
when: E1: sign of help changed vs 60 s ago, both sides meaningful, was >= +1.0.  
- "{fsym} just turned: it was helping ({fwas}), now it is against you ({fnow})."
- "{fsym} flipped sides — {fwas} a minute ago, {fnow} now."
- "Lost one: {fsym} crossed from helper to hurter ({fwas} → {fnow})."
- "{fsym} changed its mind. It gave you {fwas}; it has taken that back and more ({fnow})."

**`flip_with`** · tone **confidence** · prio 50 · cool-down 60 s, re-fires when `eq_breadth_with` moves ≥ 1; not before 60 s in the trade  
when: E2: flip the other way, was <= -0.7.  
- "{gsym} has come over: it was against you ({gwas}), now it is with you ({gnow})."
- "{gsym} stopped fighting and joined ({gwas} → {gnow})."
- "A convert — {gsym}, from {gwas} to {gnow}."

**`swing_stock`** · tone **warning** · prio 85 · cool-down 90 s, re-fires when `eq_swing_giveback` moves ≥ 1  
when: E3: the stock with the largest give-back since the best, >= max(1, 25 % of the print's give-back), print give-back >= 3.  
- "{ssym} is the one that turned this: {satbest} at your best, {snow} now — {sgb} points given back from one name."
- "The swing stock is {ssym}: it took back {sgb} of the {pb} points the print has lost since the best."
- "Your best was built with {ssym} at {satbest}. It is {snow} now. That is the trade's story in one name."
- "{ssym} reversed the trade: {sgb} points back since {besttime}."

**`swing_spread`** · tone **information** · prio 55 · cool-down 120 s, re-fires when `eq_print_giveback` moves ≥ 3  
when: E4: print give-back >= 8 and no stock gave back more than 20 % of it.  
- "No single name took this back — the give-back is spread across {gbn} stocks, biggest {gbsym} at {gbmax}."
- "The whole basket breathed out together: {gbmax} max from any one name."
- "Not a reversal in one stock; a general exhale. {with} still with you."

**`flip_pair_banks`** · tone **warning** · prio 90 · cool-down once per trade  
when: E5: HDFCBANK and ICICIBANK both flipped against within 60 s of each other.  
- "Both big banks turned inside a minute — HDFCBANK {hflip} and ICICIBANK {iflip}. That is 19 % of the index changing sides."
- "HDFCBANK and ICICIBANK have gone the other way together. On a {opt} that is the worst pair to lose."


### F. Sector reads

**`bank_move`** · tone **information** · prio 55 · cool-down 180 s  
when: F1: the banks are >= 60 % of the positive help with >= 3 of 5 meaningful.  
- "This is a bank move: {bpts} of your {tot} basket points are the five banks ({bwith}/5)."
- "Banks are the whole story ({bwith} of 5, {bpts} pts). IT and RIL and the rest are {rest}."
- "Financials are driving — {bpts} points from the banks; the rest of the basket is along for the ride."

**`banks_vs_rest`** · tone **caution** · prio 60 · cool-down 150 s  
when: F2: bank help and non-bank help have opposite signs, both |.| >= 2.  
- "Banks and the rest disagree: banks {bpts}, everything else {rpts}. Somebody is wrong."
- "A split market — financials {bpts}, non-financials {rpts}. The index is the net of that split."
- "Banks {bpts}, RIL+IT+rest {rpts}. The index is the net of a tug-of-war."

**`it_against`** · tone **information** · prio 40 · cool-down 180 s  
when: F3: INFY + TCS <= -1.0 with neither meaningful with.  
- "IT is fighting you: INFY {infy}, TCS {tcs}. Small weight, but both of them."
- "The two IT names are the other way ({itpts}). Not enough to matter unless the banks join them."

**`ril_alone`** · tone **caution** · prio 70 · cool-down 120 s  
when: F4: RELIANCE >= 50 % of the positive help with breadth <= 5.  
- "RELIANCE is the move: {rilpts} of {tot}. One stock, 7.6 % of the index, and {with} names with it."
- "This is RIL and little else ({rilshare} % of the basket's help). It can carry an index for a while, not forever — a count, not a forecast."

**`all_sectors`** · tone **confidence** · prio 75 · cool-down 180 s  
when: F5: every sector's net help >= 0 and with >= 10.  
- "Every sector we track is on your side: banks, IT, RIL, FMCG, autos."
- "Banks ✓ IT ✓ RIL ✓ FMCG ✓ autos ✓ — no sector is dissenting."
- "Across the board: {with} of {n}, not one sector against."

**`defensives_lead`** · tone **information** · prio 35 · cool-down 240 s  
when: F6: top helper is ITC or HINDUNILVR on a PE.  
- "FMCG is leading a fall — {sym} is your top name. Defensives falling first is unusual; note it."
- "Odd leader: {sym}, a defensive, is the biggest help on a PE."


### G. Stock futures vs cash (colour only)

**`stock_futs_ahead`** · tone **information** · prio 15 · cool-down 300 s  
when: G1: 15-s stock-futures basket move minus cash basket move >= +5 in favour. Colour: best cross-corr lag 0 s.  
- "Stock futures are running ahead of cash by {lead} basket points right now. (On 19 Oct this had no edge; colour only.)"
- "The stock-futures basket moved {lead} points more than cash in the last 15 s."

**`stock_futs_behind`** · tone **information** · prio 15 · cool-down 300 s  
when: G2: the mirror of G1.  
- "Cash is ahead of the stock futures by {lead} points — the futures have not followed yet."
- "Stock futures are lagging the cash names by {lead} basket points."

**`basis_widening`** · tone **information** · prio 20 · cool-down 300 s; not before 120 s in the trade  
when: G3: weight-averaged basis change since entry >= 0.05 % in favour after 120 s.  
- "The stock-futures basis has widened {bps} bp in your direction since entry — futures traders leaning your way."
- "Since entry the stock futures have moved {bps} bp more than their cash names, your way."


### H. Flow (present tense only)

**`pressed_name`** · tone **information** · prio 45 · cool-down 90 s  
when: H1: a helper with aggressive flow in the trade's direction for >= 40 s.  
- "Aggressive {side} in {psym} for {psecs} s — the move is being pressed."
- "{psym}: {psecs} seconds of {side} hitting the {olevel}. Someone wants it {dirword_er}."
- "{side} are leaning on {psym} ({psecs} s and counting)."

**`fought_name`** · tone **caution** · prio 55 · cool-down 90 s  
when: H2: a hurter with aggressive flow against the trade for >= 40 s.  
- "{qsym} is being hit against you for {qsecs} s — that is where the other side is working."
- "Aggressive {oside} in {qsym} for {qsecs} s ({qpts}). That is the name where a reversal would show first."

**`flow_broad_with`** · tone **information** · prio 50 · cool-down 120 s  
when: H3: names with run_with >= 30 s are >= 40 % of tracked weight.  
- "The aggressive flow is with you across {fwn} names ({fwpct} % of tracked weight)."
- "{side} are pressing {fwn} heavyweights at once."

**`flow_broad_against`** · tone **caution** · prio 70 · cool-down 90 s  
when: H4: names with run_against >= 30 s are >= 40 % of tracked weight.  
- "Aggressive {oside} across {fan} names ({fapct} % of weight) while the print is still {spot}. The flow has turned before the price."
- "The other side is now pressing {fan} heavyweights. Price has not followed yet; the count has."

**`book_pulled`** · tone **caution** · prio 60 · cool-down 120 s  
when: H5: the side the trade needs to hold (bids for a CE, asks for a PE) is PULLED on the top helper.  
- "The {level} in {sym} was pulled, not eaten — the resting orders walked away."
- "{sym}'s {level} side: PULLED. Liquidity left; it was not consumed."

**`book_refilling_against`** · tone **information** · prio 40 · cool-down 120 s  
when: H6: the side the trade must break is REFILLING in >= 2 helpers.  
- "{refill_list} are refilling the {olevel} — the move is being absorbed in the book, not running away."
- "The {olevel} keeps refilling in {refill_list}: the helpers are being met with fresh orders."

**`flow_vs_price`** · tone **caution** · prio 65 · cool-down 90 s  
when: H7: top helper on price, aggressive flow against for >= 40 s.  
- "{sym} is still your best name ({pts}) but the aggressive flow there has been against you for {asecs} s. Price and flow disagree."
- "{sym} is helping on price and being {oside}-hit on flow ({asecs} s)."


### I. First mover / episode

**`first_mover`** · tone **information** · prio 45 · cool-down once per trade  
when: I1: episode.first when the episode's direction is the trade's and it began <= 120 s before entry.  
- "{fm} moved first — it crossed its 2σ line at {ft}, before the index."
- "First mover: {fm}. The episode is {eptype}; {ncross} names have crossed since."
- "This leg started in {fm} ({eptype}). Everyone else followed."

**`futures_led`** · tone **caution** · prio 60 · cool-down once per trade; not before 30 s in the trade  
when: I2: FUTURES-LED episode and with <= 5 at 30 s.  
- "This was a FUTURES-LED episode and the stocks have not followed: {with}/{n} after {age} s."
- "Futures moved first; the cash names are still thinking about it ({with} with you)."

**`single_name`** · tone **caution** · prio 65 · cool-down once per trade  
when: I3: episode type SINGLE-NAME.  
- "Single-name episode: {fm} is the whole move. The index is {fm} in disguise."
- "The episode is SINGLE-NAME — {fm} started it and nobody meaningful has joined."

**`basket_led`** · tone **confidence** · prio 50 · cool-down once per trade  
when: I4: BASKET-LED episode with with >= 7.  
- "BASKET-LED: the stocks moved before the futures, and {with} of them are still with you."
- "The heavyweights started this one ({fm} first), the index followed. The right way round."


### J. The entry moment

**`breakout_made_by`** · tone **information** · prio 60 · cool-down once per trade  
when: J1: top pre-entry helper >= 2 pts.  
- "This breakout was made by {jsym1} ({jpts1}) and {jsym2} ({jpts2}); {jwith} of {n} moved with it."
- "The last {jref} s: {jsym1} {jpts1}, {jsym2} {jpts2}, {jsym3} {jpts3}. That is what you just bought."
- "Who broke the range: {jsym1}, then {jsym2}. {jagainst} names fought it."

**`breakout_fought_by`** · tone **caution** · prio 55 · cool-down once per trade  
when: J2: bottom pre-entry hurter <= -2 pts.  
- "{jhsym} fought this breakout the whole way ({jhpts}). It will have to give up for the move to extend."
- "Note {jhsym}: {jhpts} against the breakout you just bought."

**`breakout_on_air`** · tone **warning** · prio 75 · cool-down once per trade  
when: J3: the print moved >= 3 in favour before entry and basket/print < 0.4 or with <= 4. On 19 Oct: 16 % of winners, 15 % of losers — a warning, not a veto.  
- "This breakout is an index print: the basket we track moved {jtot} vs the index's {jspot}. {jwith} names with it. Needs the stocks to catch up."
- "Thin breakout — {jwith} heavyweights took part. You are early or you are wrong; the next minute tells which."

**`breakout_broad`** · tone **confidence** · prio 65 · cool-down once per trade  
when: J4: pre-entry with >= 9 and ratio >= 0.8.  
- "A proper breakout: {jwith} of {n} moved with it, basket {jtot} vs print {jspot}."
- "The stocks broke out with the index — {jwith} names, {jbwith} of 5 banks."

**`late_to_it`** · tone **caution** · prio 60 · cool-down once per trade  
when: J5: the print moved >= 20 pts in favour over the pre-entry window.  
- "The move you bought is already {jspot} points old — {jsym1} and {jsym2} did most of it before your fill."
- "You are buying after a {jspot}-point run in {jref} s. The basket made it; what you need is a second leg."

**`day_context`** · tone **information** · prio 30 · cool-down once per trade  
when: J6: % vs previous close from snap['close'] at entry.  
- "On the day the heavyweights are {daywith}/{n} your way; the day's leader your way is {leader} ({chg} %)."
- "Day picture: {leader} {chg} %, {laggard} {lchg} %. Your {opt} is {with_or_against} the day's drift."


### K. Holding reassurance (only when the facts hold)

**`still_broad_after`** · tone **confidence** · prio 55 · cool-down 120 s, re-fires when `hold_s` moves ≥ 120; not before 120 s in the trade  
when: K1: age >= 120 s, with >= 9 and not below a minute ago.  
- "{min} minutes in and still {with} names with you. The basket has not thinned."
- "Breadth is holding at {with}/{n} after {min} min — the names that started this are still in it."

**`helper_holding_at_best`** · tone **confidence** · prio 50 · cool-down 90 s; not before 60 s in the trade  
when: K2: at a new best, the top helper is the same as 60 s ago and its help is rising.  
- "New best, and {sym} is still the one making it ({pts}, rising)."
- "{sym} pushed the trade to a new best — {pts} and climbing."

**`best_without_basket`** · tone **warning** · prio 75 · cool-down 60 s; not before 60 s in the trade  
when: K3: at a new best, basket below its value 60 s ago.  
- "New best on the print, but the basket is LOWER than a minute ago ({tot} vs {tot60}). The stocks did not make this high."
- "The index made a new best without its heavyweights — basket {tot}, down from {tot60}."

**`nothing_meaningful`** · tone **information** · prio 50 · cool-down 90 s  
when: K4: with = 0 and against = 0 after 20 s.  
- "Nothing meaningful is carrying this yet: the biggest helper is {csym} at {abs} pts total either way."
- "The basket is asleep — no name has moved 0.03 % either way since your entry."


### L. Exit review (kind `review`, rendered by `review_lines()`)

**`made_and_ruined`** · tone **lesson** · prio 100 · cool-down once per trade  
when: L1: winner, the two names that built the best >= 1 each, some stock gave back >= 1.  
- "This trade was made by {m1} ({mp1}) and {m2} ({mp2}); {r1} ruined the last {gbmax} points."
- "Credit: {m1}, {m2}. Blame for the give-back: {r1} ({rp1}), {r2} ({rp2})."
- "Built by {m1} and {m2}, trimmed by {r1}. Net: {pnl} on the print."

**`ruined_by`** · tone **lesson** · prio 100 · cool-down once per trade  
when: L2: loser with a hurter <= -1 at the exit.  
- "Ruined by {r1} ({rp1}) and {r2} ({rp2}): {rshare} % of the give-back came from those two."
- "{ssym} reversed this trade. It was {ratbest} at your best and {rnow} at the exit."
- "The loser's name is {hsym}: {hpts} points against from one stock, {against} names against in all."

**`nobody_made_it`** · tone **lesson** · prio 100 · cool-down once per trade  
when: L3: loser and no stock ever contributed >= 1 pt at the best.  
- "Nobody made this trade. The basket never confirmed ({maxwith} names at most); it was an index wobble."
- "No heavyweight ever got going — peak breadth {maxwith}/{n}. There was nothing carrying it."

**`spread_exhale`** · tone **lesson** · prio 100 · cool-down once per trade  
when: L4: winner, no stock gave back more than 20 % of the print's give-back.  
- "No single name ruined this; the whole basket breathed out together ({gbn} names, max {gbmax})."
- "The give-back was collective — {gbmax} from {gbsym} at most. A good trade that ran out of {side} everywhere at once."

**`exit_basket_still_with`** · tone **lesson** · prio 95 · cool-down once per trade  
when: L5: at the exit with >= 10 and the basket within 2 pts of its value at the best.  
- "You were trailed out by the index print while {with} of {n} names were still with you (basket {tot}). The rule is the rule; the stocks had not turned."
- "Out on the print, not on the stocks: basket {tot} at the close, {with}/{n} on side."

**`exit_breadth_collapsed`** · tone **lesson** · prio 95 · cool-down once per trade  
when: L6: with(exit) <= with(best) - 5.  
- "Breadth went from {bwith_best} at your best to {with} at the exit. The basket left before the price did."
- "From {bwith_best} names to {with}. The stocks had already said it before the print did."


### M. Rare / colour

**`heaviest_flat`** · tone **information** · prio 35 · cool-down 240 s  
when: M1: |HDFCBANK help| < its threshold with the print >= 10.  
- "HDFCBANK has not moved at all — the 10 % of the index that matters most is sitting this out."
- "{spot} points of print and HDFCBANK is flat ({hdfc}). Whatever this is, it is not a bank move."

**`opposite_pair`** · tone **information** · prio 30 · cool-down 240 s  
when: M2: one name of a sector >= +1, another <= -1.  
- "{osector} is split down the middle: {oa} {opa} vs {ob} {opb}."
- "Within {osector}, {oa} and {ob} are pulling opposite ways."

**`unanimous_against`** · tone **warning** · prio 95 · cool-down 60 s, re-fires when `eq_breadth_against` moves ≥ 1  
when: M3: against >= 10.  
- "{against} of {n} heavyweights are against you. The index print is the only thing on your side."
- "The basket has voted: {against} names the other way."

**`basket_quiet`** · tone **information** · prio 35 · cool-down 180 s; not before 60 s in the trade  
when: M4: Σ|pts| < 2 after 60 s.  
- "Quiet basket — the {n} names have barely moved (total {abs} pts either way) in {min} min."
- "Nothing is happening in the stocks. The trade is marking time."

**`volume_dry`** · tone **information** · prio 30 · cool-down 240 s  
when: M5: domino tiles act < 0.5 for >= 10 names.  
- "Volume has dried up in {dryn} of {n} names (under half their 15-s baseline)."
- "The heavyweights are trading thin — {dryn} names below half their normal pace."

**`recruit_wave`** · tone **confidence** · prio 60 · cool-down 60 s  
when: M6: >= 3 names with 15-s z >= 2 in the trade's direction.  
- "A wave: {wlist} all crossed 2σ in the same 15 s, your way."
- "{wn} names just jumped together ({wlist})."

**`recruit_wave_against`** · tone **warning** · prio 85 · cool-down 60 s  
when: M7: >= 3 names with 15-s z <= -2 against the trade.  
- "{an} names just jumped the other way together: {alist}. The print has not reacted yet."
- "A counter-wave in {alist}. The next 30 s of the print will show whether it matters."


### What 19 Oct would have heard (from `facts_32_trades.txt`)

* **09:55:01 PE (+37.9)** — entry: "This breakout was made by HDFCBANK (+5.7) and ICICIBANK (+1.2); 6 of 14 moved with
  it." then "RELIANCE fought this breakout the whole way (−4.2)." · +60 s: "ICICIBANK alone has given you +8.5 of your
  +27.9 basket points." / "The stocks are AHEAD of the index: basket +27.9 vs print +25.5." · best: "11/14 — the entire
  basket is on your side right now." · review: "This trade was made by ICICIBANK (+8.2) and HDFCBANK (+3.2); AXISBANK
  ruined the last 1.8 points."
* **09:52:08 PE (−10.1)** — +10 s: "Nothing meaningful is carrying this yet." · +20 s: "RELIANCE is the one that turned
  this: +0.0 at your best, −2.0 now — 2.0 points given back from one name." / "Only 2 names are moving …" · review:
  "Ruined by RELIANCE (−2.0) and ICICIBANK (−1.8): 31 % of the give-back came from those two."
* **12:04:01 PE (+29.2)** — entry: "This breakout is an index print: the basket we track moved −0.1 vs the index's +4.0.
  4 names with it." · exit: "The print has pulled back 18.6 from the best but the basket has not — still +31.0, 14 names
  with you. The stocks did not reverse." (`trailing_on_air`, information: the exit rule is the owner's).
* **13:29:56 PE (−6.6)** — "No heavyweight is past its entry print. The breakout you bought is not in the stocks." ·
  review: "Nobody made this trade. The basket never confirmed (0 names at most); it was an index wobble."

### Tests — `tests/test_c5_cmt_basket.py`

71 templates, unique keys, ≥ 2 phrasings, valid kind/tone, no instruction verbs; every predicate and phrasing on the
all-None dict and on a populated one; the facts on a hand-built bank-led PE (helper maths to ±0.05 pt, breadth, flips
both ways, the swing stock, review lines); the T07 honesty guard (with = 2, against = 9, print +12 → no confidence line,
`thin_move` and `hurters_outnumber_helpers_pts` fire, the core selector shows the warning); a NaN entry print lowers
the denominator to 13 and no phrasing prints "nan"; flow runs and z-waves; a broken engine never raises; 1 000
`extend_facts` calls in ~0.23 ms each.


## 11.3 Holding, anticipating, and knowing when it has turned — `apex/engine/cmt_hold.py` (team T08)

The owner said: *"if you can instil more and more confidence in me to hold, I will keep holding."* This module's answer
is the one it can honestly give: confidence is evidence that has not changed yet. Every few seconds it says what the
evidence is, in numbers the owner can check on the same screen, and the moment the evidence turns it says that first.
It never tells the owner what to do — the verdict line (core) and the rule (the spot trail, the profit lock, the clock)
do that. A false "stay" is the one output this module must never produce, so every confidence remark is wrapped in an
honesty guard (below).

Module facts: **69 templates / 276 phrasings** (CONFIDENCE 13 · ANTICIPATION 11 · CAUTION 12 · WARNING 12 · TIME 7 ·
DISCIPLINE 7 · EXIT REVIEW 7), **115 `hold_*` facts**, `review_card(t, f)` for the receipt. Test:
`python3 tests/test_c5_cmt_hold.py` (10 tests: shape, predicates on empty and full facts, formatting, no instruction
words, no literal digits, the honesty guard, a fake engine through `extend_facts`, the review card, loading through
the core, 1,000 `extend_facts` calls in ≈ 100 ms).

### The evidence (19 Oct 2026, 32 champion trades, `spot_dc12_t12`, expiry day, 1-Hz pack; bid = the sellable return)

Measured by `work_T08/analyse.py` / `analyse2.py`; the full tables are in the T08 report. One day of evidence is one
day: every rate below is quoted in the phrasings **with its date** ("on 19 Oct") from the `HOLD_REF` constants at
the top of the module, never as a law. When the harness is re-run on a new day, `HOLD_REF` is the one place to update.

| question | measured on 19 Oct |
|---|---|
| how far winners ran before the trail took them | best unrealised **+15.6 %** mean; realised **+5.6 %**; give-back **9.9 %** mean (median 10.0) — the price of a 12-pt spot trail at δ≈0.65 |
| how fast a winner declares itself | +10 % (bid) at a median **44 s**; 13 of 21 within 60 s |
| the ladder (bid return, later in the same trade) | +5→+10 21/28 (75 %) · +10→+15 13/21 (62 %) · **+10→+20 8/21 (38 %)** · +15→+25 7/13 (54 %) · **+20→+25 7/8 (88 %)** · +20→+30 5/8 (62 %) · +25→+30 5/7 (71 %) |
| a 5 % give-back — recovered to a new high? | **23 of 49 = 47 %** → caution, not alarm |
| more than half the best gone (best ≥ 10 %) | 4 of 21 ex-+10 % trades ended near flat this way → warning |
| stall (no new best SPOT) ≥ 60 / 90 / 120 / 180 s → a new best later | 65 % / 75 % / **73 %** / **50 %**; nothing survived a 5-min stall (longest before exit 272 s) → caution at 120 s, warning at 180 s |
| theta on expiry day | the engine's `theta_min` spreads year-theta/365 over 375 trading minutes; with the session itself as the remaining time the calendar clock (/1440) is right: **×3.84 overstated**. Measured flat-window decay −0.1…−0.3 pts/min matches `theta × 375/1440`. The panel shows `hold_theta_cal` labelled "expiry-day clock"; the engine's number is untouched |
| spot speed to stay flat | `theta_cal / |delta|` = 0.15–0.4 pts/min; three idle minutes = THETA_IDLE (warning) |
| IV during moves | held PE on a fall ΔIV **+1.4** mean, vega share 61 % / 63 % on 11:37 and 12:04; held CE on a rally ΔIV **−1.1**, vega share −20 % |
| "spot moved my way and I still lost" | **13:44 PE**: +13.4 spot pts, delta +₹47 k, **IV −8.3 pts = vega −₹63.5 k**, net −₹16.6 k; also 14:24 PE and 13:36 CE → `warn.vega_eating` at ΔIV ≤ −3 with spot in favour, `cau.premium_lag` when spot makes a new best and the bid does not |
| basket synchrony (cash, since entry, > 0.03 %) | winners **10.0 with / 1.3 against** of 14; losers 4.2 / 5.2 → with−against ≥ 6 confident, against ≥ 4 caution, against ≥ with+3 warning |
| 30-min trend | with (n=9) mean **+12.0 %**, median +8.1; against (n=19) +3.2 %, median −0.9 |
| regime at entry | DIRECTIONAL +9.8 % · COMPRESSION +6.5 · WARMING +5.3 · RANGE **+1.3** |
| liquidity | exit spread 0.10–0.45 pts (≤ 0.5 %); the position ≤ 3 % of one minute's volume; ltp-vs-bid fill gap ≤ 0.5 pt → SPREAD_WIDE > 1 % or 3× entry, THIN > 10 % of 1-min volume |
| the lull | median 1-min \|Δspot\| 8–10 pts before 10:30, **3.4–6.3 pts 11:00–14:30** → LULL σ15 ≤ 5 and speed < 4 |
| the profit lock (owner's D-127: +18 % arms, 10 % off the best) | on the 32 bid paths P ≤ 12 lost money (47 % of 5 % give-backs recover); P ≥ 15 with a 4–6 % gap helped a little and never cut a winner. The module reads whatever the book publishes (`pos['lock_armed']`, `pos['lock_floor']`, `pos['best_prem']`, `book.p['lock_pct']`, `['lock_trail_pct']`) and treats a missing lock as "no lock" |

Thresholds (named constants in the module): GB_CAUTION 5 % · GB_WARN best ≥ 10 % and > half gone · STALL_WATCH 120 s ·
STALL_WARN 180 s · STOP_NEAR ≤ 4 pts · STOP_IMMINENT ≤ 2 · IV_OFF ≤ −3 · IV_WITH ≥ +2 · PREM_LAG > 3 % · BASKET_WITH ≥ 6 ·
BASKET_SPLIT ≥ 4 · BASKET_TURNED against ≥ with+3 · THETA_IDLE 180 s · TIME_NEAR 15 min / IMMINENT 5 · LULL σ ≤ 5 & speed < 4 ·
THIN > 10 % · LONG_HOLD 600 s · STOCK_MOVE 0.03 % · LUNCH 12:00–13:15 · LAST_HOUR 14:30 (14:00 on expiry).

### The honesty guard

Every CONFIDENCE template's predicate is `_honest(f) and when(f)`. `_honest` is False when spot is within a quarter of
the trail of the stop (`stop_dist ≤ 0.25 × hold_trail_pts`), when the bid shows a loss while the last print shows a
gain (`hold_bid_loss_ltp_gain`), or when the held quote is stale / an exit is pending (`hold_data_bad`). In those
states the warnings still speak (`warn.stop_near`, `warn.data`), the confidence does not. The test
`test_confidence_honesty_guard` asserts all four cases over all 13 confidence templates. The ladder anticipation
(`ant.ladder`) carries the same guard. Beyond that: no phrasing contains a literal digit (every number is a `{slot}`,
so nothing can go stale inside a sentence); "hold", "sell" and "buy" never appear as words; "exit" only as a noun and
never at the head of a clause — the test checks all three.

### The facts this module adds (`FACTS`, 115 keys; None where the data is missing, never a guess)

| fact | meaning | source |
|---|---|---|
| `hold_trail_pts` | the spot trail in points | `book.p['spot_trail']` (else `d_star`, else 12) |
| `hold_stall_s`, `hold_stall_m` | seconds / minutes since `best_spot_fav` last improved | kept in the memo: `hold_best_t` is reset whenever the core's `best_spot_fav` rises |
| `hold_new_best_recent` | the best spot improved within the last 3 s | derived |
| `hold_theta_cal`, `hold_theta_cal_abs` | theta per minute on the calendar clock: `theta_min × 375/1440` on a 0-DTE contract, else `theta_min` (display only) | `greek[id]['theta_min']`, `zero_dte` |
| `hold_flat_speed` | spot pts/min needed to pay theta = `|theta_cal| / |delta|` | derived |
| `hold_theta_rs_min`, `hold_theta_3m_rs` | `|theta_cal| × qty`, ×3 | derived |
| `hold_spot_speed_1m` | `|spot − spot 60 s ago|` | core `spot_r60` (eng.spot_hist) |
| `hold_theta_idle`, `hold_idle_s` | speed below the flat speed for ≥ 180 s; how long | memo clock `hold_idle_since` |
| `hold_bid_sellable`, `hold_ret_bid`, `hold_bid_rs` | bid − entry in pts, %, ₹: the P&L you can actually realise | `by_key[key]['bid']` |
| `hold_giveback_bid`, `hold_prem_lag` | best return − bid return (%) | derived |
| `hold_bid_loss_ltp_gain` | the bid is below entry while the last print is above it | derived (honesty flag) |
| `hold_best_ret_bid`, `hold_ladder_rung`, `hold_fast_start` | best bid return seen; highest rung of 10/15/20/25 % reached on the bid; +10 % within 60 s | memo |
| `hold_ladder_p5_10 … p25_30`, `hold_ref_date` | the 19 Oct ladder rates (0.75, 0.62, 0.38, 0.54, 0.88, 0.62, 0.71) and the date — REF constants, labelled | `HOLD_REF` |
| `hold_lock_on`, `hold_lock_floor`, `hold_lock_q`, `hold_lock_rs`, `hold_lock_gap`, `hold_lock_pct`, `hold_lock_trail_pct`, `hold_best_prem` | the profit lock: armed?; the floor price; the floor as a % of entry; the rupees it keeps; bid return − floor return; P and R; the best premium | `pos['lock_armed']`, `pos['lock_floor']`, `pos['best_prem']`, `book.p` (all via `.get`; None → no lock) |
| `hold_room_pct`, `hold_wall_rs`, `hold_wall_prem` | what reaching the next OI wall is worth: `wall_room × |delta| / ltp × 100`, in ₹, as a premium | core `wall_room` (pressure.destination) |
| `hold_round_next`, `hold_round_dist` | the next 100-multiple of spot in the trade direction and the distance | derived from `spot` |
| `hold_day_level`, `hold_day_room`, `hold_hi_lo` | the day's futures high (CE) / low (PE) and the room to it from the futures mid (≤ 0 = beyond it); "high"/"low" | `eng._day_hi` / `eng._day_lo`, `ctx['fut']` |
| `hold_vol_1m`, `hold_pos_vs_vol`, `hold_thin` | units traded on the held strike in the last 60 s (Δttq from a 90-s 1-Hz deque in the memo); qty as % of it; > 10 % | `eng.m.ttq[id, k]` |
| `hold_agg_b`, `hold_agg_s` | aggressive buy / sell volume EWMA on the held contract | `eng.flow.agg_b/agg_s[id]` |
| `hold_spread_pct`, `hold_spread_x`, `hold_spread_wide` | spread as % of premium; vs the entry spread; > 1 % or > 3× | core `spread_now`, `spread_in` |
| `hold_delta_rs`, `hold_vega_rs`, `hold_resid_rs`, `hold_delta_only_pct` | attribution: `delta_in × (spot − spot_in) × qty`; `Δiv × vega × qty`; the rest (theta, spread, noise); the move alone in % | core `delta_in`, `iv_rs` |
| `hold_iv_off`, `hold_iv_with` | ΔIV ≤ −3 with spot in favour; ΔIV ≥ +2 | core `iv_chg` |
| `hold_n_with`, `hold_n_against`, `hold_n_eq`, `hold_best_stock`, `hold_worst_stock`, `hold_worst_move` | heavyweights moved > 0.03 % with / against since entry (T08's measure, finer than the core's 0.5-pt `n_helping`); names; the worst move in % | `eng.m.ltp[eq_ids, k]` vs the core memo's `eq_px_in` |
| `hold_basket_with`, `hold_basket_split`, `hold_basket_turned` | with−against ≥ 6; against ≥ 4 (not turned); against ≥ with+3 | derived |
| `hold_trend30`, `hold_with_trend` | the futures 30-min move signed in the trade direction; 1 / 0 / −1 at ± 5 pts | `ctx['trend30']` |
| `hold_regime_in`, `hold_regime_dir_in`, `hold_regime_flipped`, `hold_regime_text` | regime at entry; direction flipped against or state fell into RANGE / EXHAUSTION; the engine's text | `pos['signal']`, `ctx['regime']` |
| `hold_r15_in`, `hold_sigma15_in`, `hold_sigma15`, `hold_late_entry`, `hold_lull` | 15-min return and σ at entry; σ now; entered after a > 2σ move; the lull | `pos['signal']`, `ctx['domino']['sigma15']` |
| `hold_costly_entry`, `hold_mid_in` | entry > 0.5 pt over the mid or entry spread > 1 %; the mid at entry | core `entry_over_mid`, `spread_in` |
| `hold_straddle_state`, `hold_straddle_leg`, `hold_straddle_slope`, `hold_straddle_px`, `hold_move_vs_straddle`, `hold_straddle_spike_with` | the fixed-strike straddle watch: state, spiking leg, 5-min change, price; spot move ÷ straddle; True / False / None for a spike on our leg / the other / none | `eng.watch.view(series=False)`, core `straddle_px` |
| `hold_gex_ok`, `hold_gex_flip`, `hold_gex_call`, `hold_gex_put`, `hold_gex_regime`, `hold_gex_wall`, `hold_gex_room`, `hold_gex_tendency` | the dealer-gamma map; its wall in the trade direction and the room; "damp" / "accelerate" / "do either" | `eng.gex.v` |
| `hold_fut_confirm`, `hold_fut_best_fav` | futures made a new extreme within 10 s of the new spot extreme; the best futures excursion | memo clocks, `ctx['fut']`, `pos['fut_in']` |
| `hold_basis_chg_dir` | basis change since entry signed in the trade direction | core `basis_chg` |
| `hold_lunch`, `hold_last_hour`, `hold_no_reentry`, `hold_last_entry_hms` | 12:00–13:15; ≥ 14:30 (14:00 on expiry); past the last entry; that time as text | `ctx['now_dt']`, `config.LAST_ENTRY` / `ZERO_DTE_NO_ENTRY` |
| `hold_time_room_pts`, `hold_exit_est_rs` | speed × minutes to the flatten; what a trail hit from here is worth `(ltp − trail×|delta| − entry) × qty` | derived |
| `hold_stop_rs`, `hold_rs_per_spot`, `hold_stop_rs_entry`, `hold_giveback_rs`, `hold_trail_prem_pts`, `hold_delta_abs` | rupees the trail can still take; ₹ per spot point; the trail in ₹ at the entry delta; give-back in ₹; the trail in premium points; \|delta\| | derived |
| `hold_stop_near`, `hold_stop_imminent` | stop ≤ 4 pts / ≤ 2 pts | core `stop_dist` |
| `hold_biggest_today`, `hold_day_best_rs` | the open gain beats the day's best realised; that best | `book.trades` |
| `hold_data_bad` | data gap, exit pending, or the held quote > 5 s old | core `gap_on`, `exit_pending`, `quote_age` |

The memo (`extend_memo`) snapshots at entry: the stall and futures clocks, the idle clock, the best bid return and
ladder rung, the 90-s ttq deque, and `pos['signal']` (r15, sigma15, regime, regime_dir).

### The exit review — `review_card(t, f)` → `{"grade", "lines": [3]}`

Three lines from the closed trade record and the last facts: (1) `exit.summary`; (2) the line that fits the exit —
`exit.winning_move_lost` when the trade lost with a best spot excursion ≥ 10 pts (the 13:44 lesson), else
`exit.stop_review` for a STOP or a return < −3 %, else `exit.time_review` for a TIME exit, else `exit.trail_cost` for a
TRAIL with a best ≥ 10 % (its second phrasing for a LOCK), else a second `exit.summary` phrasing; (3) `exit.day_tally`
with the day's count, wins, realised and capital including this trade. Slots the card adds: `{exit}` (the fill),
`{reason}` (the first word), `{vega_share_pct}` (the share of the give-back that was IV coming off, 0–100, only when
IV came off). Phrasings are chosen by the core's crc32 of the trade id, so a replay reproduces the receipt.

The grade is the outcome against the trade's own best, stated so the owner can disagree with the rule, not the letter:
**A** realised ≥ 15 % · **B** ≥ 5 % · **C** a scratch (−3 … 5 %) · **D** lost ≥ 3 % after a best ≥ 10 % (a winner
given back or taken by vol) · **E** lost ≥ 3 % and never saw +10 %.

Example (the 11:24 PE of 19 Oct, +28.1 %, ₹58,331, 683 s, TRAIL):
> TRAIL at 146.25. Attribution: delta ₹48,048, vega ₹8,900, theta and spread −₹9,992.
> A trail is paid for at the end. This one cost ₹25,025.
> Day: 14 trades, 9 won, ₹2,73,331. Capital ₹3,73,331. Biggest ₹58,331.

### Not ported, and why

- **`exit.what_followed` as a 60-s-later line** ("a minute later the 23150 PE is 148.10 — the trail was early by 2
  pts"): the core calls `review_card` once, at the close, and gives no hook a minute later; the held contract's later
  price is not in the last facts. The template exists with honest stand-in phrasings (no post-exit price, no
  verdict on the rule) but the card does not use it. It belongs to the dashboard (which sees the tick stream) or to a
  later core hook; the T08 text and the "runs both ways" rule are in the T08 doc §5.7.
- **The HOLD / WATCH / EXIT-SOON scoring table** (T08 §4, ±1/±2 rows summed, DATA chip): the core's `verdict_of`
  (rule list in trail units) is kept as instructed; it is not replaced. The facts the table needs are all in `f`
  now (`hold_stall_s`, `hold_lock_gap`, `hold_basket_*`, `hold_with_trend`, `hold_theta_idle`, `hold_iv_off`,
  `hold_prem_lag`, `hold_data_bad`), so the lead can add rows to `verdict_of` or a `DATA` level later without a new fact.
- **The basket at 0.03 % in `conf.basket_with` vs the core's `basket_carry` at 0.5 Nifty pts**: both exist; the T08
  thresholds (with−against ≥ 6 / against ≥ 4 / turned) use the finer cash measure, as measured.
- **"No phrasing twice in a trade until all are used"** (T08 composition rule 4): the core picks by crc32 of
  `trade:key:n`, which varies the text but does not guarantee round-robin; the test asserts determinism and variety,
  not strict rotation.
- **Cadence 8 s / 3 s / 0 s and the chip colours** are the core's (1 per s, 3 per 10 s, warnings bypass) and the
  dashboard's; nothing to port here.
- Stats JSON (`commentary_stats.json`, regenerated per replay) → `HOLD_REF` in the module instead, with the date in
  every quoted rate; `tools/commentary_stats.py` is still to be written from `work_T08/analyse*.py`.

### The templates (key · kind · tone · prio · cool-down · when · evidence · all phrasings)

Tone mapping from T08's groups to the core's tones: CONFIDENCE → `confidence`; ANTICIPATION → `information`;
CAUTION → `caution`; WARNING → `warning`; TIME → `information` (`time.flatten_countdown` → `caution`, `time.imminent`
→ `warning`); DISCIPLINE → `lesson` (`disc.entered_well` → `praise`); EXIT → `lesson`, kind `review`. In the core a
warning bypasses the cool-down and the 3-per-10-s budget, so the cool-downs on warnings below are documentary; a
warning re-fires every second while its evidence holds (lead: that is the core's rule, worth a look).

### CONFIDENCE — staying, because here is why

**conf.trail_room_sellers** · kind `book` · tone confidence (honesty-guarded) · prio 60 · cool-down 45 s; re-fires when `stop_dist` moves ≥ 3; not before 10 s in the trade  
*when:* spot is ≥ 8 pts from the stop (`stop_dist`), the sellers' ORDERS on the held contract read PULLED or DRAIN-FAST (`sellers_o`) and the trade is up (`ret_pct`).  
*evidence:* stop_dist from the book's stop_spot; sellers_o = flow.side(id,+1) orders class on the held contract.
- The trail is {stop_pts} points away and sellers on your {strike} {rr} are pulling their orders ({cls_so}) — the evidence favours staying.
- {stop_pts} points of room to the stop, and the sellers' order count on {strike} {rr} reads {cls_so}. Nothing here argues for leaving.
- Room: {stop_pts} pts. Sellers on your strike: {cls_so}. Both on your side.
- Your stop sits at {stop_spot}, {stop_pts} points behind the action, while the other side of your book is walking away ({cls_so}).

**conf.basket_with** · kind `basket` · tone confidence (honesty-guarded) · prio 55 · cool-down 60 s; re-fires when `hold_n_with` moves ≥ 2; not before 20 s in the trade  
*when:* breadth with − against ≥ 6 of the 14 cash heavyweights since entry (`hold_basket_with`, 0.03 % stock threshold).  
*evidence:* n_with/n_against: cash stocks moved > 0.03 % since entry, signed in the trade's direction (memo.eq_px_in).
- {n_with} of {n_eq} heavyweights are moving with you since entry — {best_stock} leads. On {ref_date} winners averaged {ref_bw} with, losers {ref_bl}.
- The basket agrees: {n_with} with, {n_against} against. {best_stock} is doing the pulling.
- This is not one index tick; {n_with} of the {n_eq} big names moved your way since {time_in}.
- Breadth is with you — {n_with} stocks in step, only {n_against} leaning the other way ({worst_stock}).

**conf.with_trend** · kind `structure` · tone confidence (honesty-guarded) · prio 45 · cool-down 120 s; not before 5 s in the trade  
*when:* the 30-min futures drift is ≥ 5 pts in the trade's direction (`hold_with_trend` = 1) and the regime is DIRECTIONAL.  
*evidence:* trend30 = ctx['trend30'] (futures 30-min move) signed in the trade direction; regime from ctx.
- You are riding the half-hour trend ({trend30} pts) in a {regime} regime. Trades entered this way averaged {ref_with_mean} on {ref_date}; against the trend, {ref_against_mean}.
- Trend and trade point the same way: half-hour drift {trend30} pts, regime {regime}. The odds you started with are the good ones.
- The regime is {regime} and the half-hour drift is {trend30} pts your way. The rule is doing its work.
- With-trend entries: median {ref_with_median} on {ref_date}. That is the pool this trade is drawn from ({trend30} pts of drift).

**conf.iv_with** · kind `greeks` · tone confidence (honesty-guarded) · prio 50 · cool-down 90 s; re-fires when `iv_chg` moves ≥ 1  
*when:* IV on the held contract is ≥ +2 pts since entry (`hold_iv_with`).  
*evidence:* iv_chg on the held contract; vega_rs = Δiv × vega × qty.
- IV on your strike is up {d_iv} points since entry — vega has added {vega_rs} on top of the move itself.
- The market is paying up for your side: IV {iv_in} → {iv_now}. That is {vega_rs} of your P&L that spot did not have to earn.
- Fear is being bid into your leg ({d_iv} IV pts). It came off fast on {ref_date} too, so the lock matters — but right now it is a tailwind.
- Vega is working for you: {vega_rs} from IV, {delta_rs} from the move.

**conf.new_best** · kind `trail` · tone confidence (honesty-guarded) · prio 65 · cool-down 20 s; re-fires when `best_spot_fav` moves ≥ 3  
*when:* the best spot improved within the last 3 s (`hold_new_best_recent`) and the sellable return is ≥ 5 % (`hold_ret_bid`).  
*evidence:* hold_stall_s <= 3 s and the sellable return >= 5 %.
- New high: spot {spot_txt}, your best so far — the trail steps to {stop_spot}.
- Fresh best. The stop moves with it: {stop_spot}, locking more of the {pnl_rs}.
- {fav_pts} points of excursion now; the trail follows at {trail}.
- Another new best at {spot_txt}. The rule is doing the holding for you.

**conf.fast_start** · kind `premium` · tone confidence (honesty-guarded) · prio 50 · cool-down once per trade  
*when:* the bid return reached +10 % within 60 s of entry (`hold_fast_start`); said once, within the first 90 s.  
*evidence:* bid return >= 10 % within 60 s of entry (memo flag).
- +{ten} % on the bid inside {hold_s_txt} s. {ref_first10_fast} of the trades that got here on {ref_date} did it this fast, and {ref_l10_20} went on to +{twenty} %.
- A quick start: +{ten} % in {hold_s_txt} s. Fast starts were the rule on the winning trades of {ref_date} (median {ref_first10}).
- The premium answered immediately — {ret_pct} in {hold_s_txt} s. That is what a real break looks like.
- You are +{ten} % at {hold_s_txt} s. Median on {ref_date} was {ref_first10}; you are in the good half.

**conf.straddle_with** · kind `structure` · tone confidence (honesty-guarded) · prio 45 · cool-down 120 s  
*when:* the straddle watch reads SPIKE on the held leg (`hold_straddle_spike_with` is True).  
*evidence:* straddle_watch.state SPIKE <leg> with leg == the held rr.
- The ATM straddle ({straddle}) is spiking and your leg is carrying it — the market is buying the move, not fading it.
- Straddle {straddle}, up on the {rr} side: the move is being priced as it happens, not after.
- Expansion on your leg ({straddle_state}). On {ref_date} the two biggest winners both had IV rising into the move.
- The straddle agrees with you: {straddle_state}, led by the {rr}, {straddle} on the ATM.

**conf.fresh_ground** · kind `structure` · tone confidence (honesty-guarded) · prio 40 · cool-down 180 s  
*when:* the futures are beyond the day's high/low in the trade direction (`hold_day_room` ≤ 0) and the next OI wall is ≥ 40 pts away (`wall_room`).  
*evidence:* day high/low = the engine's futures high-water marks (eng._day_hi/_day_lo) vs the futures mid.
- You are on fresh ground — the day {hi_lo} ({day_level}) is behind the price and the next OI wall is {wall_room} points away.
- Nothing on today's chart stands between here and {wall_level}; the day's {hi_lo} at {day_level} is behind you.
- Beyond the day's {hi_lo} ({day_level}): whoever sold there is under water, and the next wall is {wall_room} pts off.
- Open air: day {hi_lo} broken, wall at {wall_level}, {wall_room} pts of room.

**conf.lock_armed** · kind `trail` · tone confidence (honesty-guarded) · prio 55 · cool-down 120 s; re-fires when `hold_lock_q` moves ≥ 2  
*when:* the profit lock is armed with a floor above entry (`hold_lock_on`, `hold_lock_q` > 0).  
*evidence:* pos['lock_armed'], pos['lock_floor'] (D-127): lock_q = floor over entry in %.
- The lock is on: whatever happens now, {lock_q} ({lock_rs}) is kept. Everything above it is free to run.
- You cannot give it all back from here — the lock holds {lock_rs}. That stays in your pocket whatever follows.
- Locked: {lock_q}. The trail sits at {stop_spot}, {stop_pts} pts away; the worst case is a paid trade.
- {lock_rs} is banked by rule (floor {lock_floor}). The rest is upside you do not have to protect by hand.

**conf.book_leads** · kind `book` · tone confidence (honesty-guarded) · prio 40 · cool-down 90 s  
*when:* the held contract's book lead is ≥ 0.3 (`book_lead`) and its imbalance leans to buyers by > 0.1 (`book_imb`).  
*evidence:* book_lead / book_imb from book_state (flow.lead, imbalance for the bought side).
- The order book on {strike} {rr} has been predicting its next tick (lead {lead}) and it leans your way ({imb_o}).
- The standing orders on your strike are ahead of the price (lead {lead}), and they are on your side ({imb_o}).
- Book-leads-price {lead}, imbalance {imb_o} toward buyers — the people queuing on your contract want it.
- The queue agrees: buyers heavier by {imb_o}, and this book has been right lately (lead {lead}).

**conf.futures_confirm** · kind `structure` · tone confidence (honesty-guarded) · prio 40 · cool-down 120 s  
*when:* the futures made a new extreme in the trade direction within 10 s of the new spot extreme (`hold_fut_confirm`).  
*evidence:* a new futures extreme since entry within 10 s of the new spot extreme (memo clocks).
- Futures confirmed the new spot {hi_lo}: {fut_txt}, basis {basis}. Not a cash-only flicker.
- Spot ({spot_txt}) and futures ({fut_txt}) printed the new {hi_lo} together. The move is in both markets.
- The futures are leading now (basis {basis}); the index is being pulled, not pushed.
- Both legs of the market agree: fut {fut_txt}, spot {spot_txt}.

**conf.volume_with** · kind `book` · tone confidence (honesty-guarded) · prio 35 · cool-down 120 s; not before 30 s in the trade  
*when:* ≥ 1,000,000 units traded on the held strike in the last minute (`hold_vol_1m`) with aggressive buyers above sellers (`hold_agg_b` > `hold_agg_s`).  
*evidence:* hold_vol_1m = Δttq over 60 s on the held row; agg_b/agg_s = flow aggressor EWMA.
- {vol_1m} units traded on your strike in the last minute, more at the ask than the bid. Buyers are chasing it.
- Heavy and one-sided: {vol_1m} units a minute, aggressors buying. Your {qty} is {pos_vs_vol} % of that.
- The contract is liquid ({vol_1m} units/min) and being bought. Nobody is forcing anything.
- Volume {vol_1m}/min on {strike} {rr}, buyers in control.

**conf.capital_small_risk** · kind `trail` · tone confidence (honesty-guarded) · prio 35 · cool-down 300 s  
*when:* the rupees the trail can still take (`hold_stop_rs`) are under 40 % of the open gain (`pnl_rs` > 0).  
*evidence:* hold_stop_rs = stop_dist × |delta| × qty.
- The trail can only cost {stop_rs} of the {pnl_rs} on the table. The risk is a fraction of the reward now.
- Worst case at the stop: give back {stop_rs}, keep the rest of {pnl_rs}. That is the shape of a trade worth staying in.
- Risk to the trail {stop_rs}; unrealised {pnl_rs}. The ratio is on your side.
- The stop is {stop_pts} pts × {delta_abs} × {qty} = {stop_rs}. Measured against {pnl_rs}, that is a cheap wait.


### ANTICIPATION — what more there could be, without promising it

**ant.next_wall** · kind `structure` · tone information · prio 45 · cool-down 180 s; re-fires when `wall_room` moves ≥ 15  
*when:* the next OI wall is ≥ 20 pts away (`wall_room`) and its premium value is known (`hold_room_pct`).  
*evidence:* pressure.destination in the trade direction; room × |delta| / premium.
- The next wall is {wall_level}, {wall_room} points away; at your delta that is about +{wall_prem_pct} % on the premium. The rule will trail it — you don't have to decide.
- Room to {wall_level}: {wall_room} pts, worth roughly {wall_rs} if it gets there. Nothing to do but let the trail follow.
- If spot reaches the {wall_level} wall your premium is near {wall_prem}. That is the size of the "what if"; the trail keeps the "what is".
- {wall_room} pts to the OI wall. The arithmetic: × {delta_abs} × {qty} = {wall_rs}. The decision: none, the rule carries it.

**ant.round_number** · kind `structure` · tone information · prio 40 · cool-down 180 s; re-fires when `hold_round_dist` moves ≥ 20  
*when:* the next 100-multiple in the trade direction is 10–60 pts away (`hold_round_dist`).  
*evidence:* next 100-multiple of spot in the trade direction.
- {round_next} is {round_room} points away. Round numbers draw stops and targets; expect a fight there, not a wall.
- Next round level {round_next}, {round_room} pts. On {ref_date} a round line was tested {ref_round_tests} times before it gave.
- {round_room} pts to {round_next}. If it breaks, the trail follows; if it holds, the trail decides.
- The crowd watches {round_next}. You are {round_room} away with a stop {stop_pts} behind.

**ant.day_extreme** · kind `structure` · tone information · prio 40 · cool-down 180 s; re-fires when `hold_day_room` moves ≥ 15  
*when:* the day's high/low in the trade direction is 0–60 pts ahead (`hold_day_room`).  
*evidence:* engine futures day high/low vs the futures mid, in the trade direction.
- The day's {hi_lo} is {day_room} pts ahead. Breaking it would put everyone who sold there under water.
- {day_room} points to the day {hi_lo} at {day_level}. Beyond it is open air.
- Target of record: the session {hi_lo}, {day_room} pts off. Not a promise, a landmark.
- Between here and the day's {hi_lo}: {day_room} pts. Between here and your stop: {stop_pts}.

**ant.ladder** · kind `premium` · tone information · prio 50 · cool-down never on time; re-fires when `hold_ladder_rung` moves ≥ 5  
*when:* the bid return has crossed a rung of 10 / 15 / 20 / 25 % (`hold_ladder_rung`); re-fires only on a new rung (step 5), never on time; silent inside the honesty guard.  
*evidence:* hold_ladder_rung = highest of 10/15/20/25 % reached on the BID; re-fires on each new rung (step), not on time.
- +{ladder_rung} % on the bid. On {ref_date}: from +{ten} %, {ref_l10_20} trades went on to +{twenty} % and {ref_l10_15} to +{fifteen} %; from +{twenty} %, {ref_l20_25} reached +{twentyfive} %. The rule holds for the ones that run; the lock protects you from the rest.
- +{ladder_rung} % now. The {ref_date} ladder: +{fifteen} → +{twentyfive} {ref_l15_25}, +{twenty} → +{thirty} {ref_l20_30}. Better than a coin above +{twenty}, worse than a certainty below.
- Rung +{ladder_rung} %. +{twenty} → +{twentyfive} was {ref_l20_25} on {ref_date}; +{twentyfive} → +{thirty} was {ref_l25_30}. Momentum in the premium was real above +{twenty} %.
- +{ladder_rung} % reached. The trail is now {stop_pts} pts away: that is the whole cost of finding out whether the next rung comes ({ref_p10_20} did from +{ten} %).

**ant.straddle_room** · kind `structure` · tone information · prio 35 · cool-down 240 s; not before 30 s in the trade  
*when:* spot's move since entry is under half the ATM straddle (`hold_move_vs_straddle` < 0.5) and spot is in favour.  
*evidence:* |spot − spot_in| / ATM straddle premium.
- Spot has moved {now_pts} pts since entry against a straddle of {straddle}: the market priced more than this for the day.
- The move so far is {move_vs_straddle_pct} % of the straddle ({straddle}). The expected range has not been used up.
- {now_pts} pts done; the straddle says the day is worth {straddle}. Plenty of range unspent.
- Against an ATM straddle of {straddle}, this {now_pts}-pt move is still small.

**ant.vega_tailwind** · kind `greeks` · tone information · prio 35 · cool-down 240 s  
*when:* a held PE while the fixed-strike straddle's 5-min change is positive (`hold_straddle_slope` > 0).  
*evidence:* straddle_watch.chg5 > 0 on a held PE.
- Puts gain twice on a fall: delta and the IV that comes with fear. The straddle is rising ({straddle_slope} over five minutes) — if it keeps going, vega adds {vega} pts per IV point, {vega_rs_per_pt} per point.
- Each IV point is worth {vega_rs_per_pt} to you at vega {vega}. The straddle is drifting up ({straddle_slope}).
- A fall that frightens pays twice. Vega {vega} pts per vol point, {qty} units.
- If IV runs another three points the premium gains about {vega_3pt} pts before spot moves at all.

**ant.gex_room** · kind `structure` · tone information · prio 30 · cool-down 300 s  
*when:* the dealer-gamma map is valid (`hold_gex_ok`) and its wall in the trade direction is ahead (`hold_gex_room` > 0).  
*evidence:* eng.gex.v: ok / flip / call_wall / put_wall / regime (DAMPEN | AMPLIFY | MIXED).
- Dealer gamma: flip {gex_flip}, call wall {gex_call}, put wall {gex_put}. In {gex_regime} gamma, moves tend to {gex_tendency}.
- The gamma map says {gex_regime}: hedging flows {gex_tendency}. The next dealer wall in your direction is {gex_wall}.
- {gex_room} pts to the dealers' {gex_wall}. Expect hedging to {gex_tendency} until then.
- Gamma regime {gex_regime} (flip {gex_flip}). That is the weather, not the trade.

**ant.time_room** · kind `time` · tone information · prio 35 · cool-down 300 s; not before 60 s in the trade  
*when:* more than 30 min to the flatten (`min_to_flatten`) and spot moved in the last minute (`hold_spot_speed_1m` > 0).  
*evidence:* speed × minutes to the flatten.
- At the last minute's pace ({speed} pts/min) the flatten at {time_exit} leaves room for another {time_room_pts} pts. The trail will decide long before the clock does.
- Clock: {mins_to_exit} min. Pace: {speed} pts/min. Time is not what ends this trade; the trail is.
- {mins_to_exit} minutes of session left — a lot of trail steps.
- The clock is generous today: {mins_to_exit} min to the flatten at {time_exit}.

**ant.rule_holds** · kind `trail` · tone information · prio 40 · cool-down 180 s; not before 15 s in the trade  
*when:* the trade is up (`ret_pct` > 0) and the stop is ≥ 6 pts away (`stop_dist`).  
*evidence:* plain description of the trail; no number is a forecast.
- You do not have to call the top. The trail is {stop_pts} pts back and will follow every new high at {trail}.
- The rule does the selling, at {stop_spot} or wherever the trail is by then. Your job is to let it.
- Anticipate all you like — the exit is already placed, at {stop_spot}, and it only moves one way.
- The hardest part of holding is already automated: the stop at {stop_spot}, {stop_pts} away, rising with the price.

**ant.basis_lead** · kind `structure` · tone information · prio 30 · cool-down 300 s; re-fires when `hold_basis_chg_dir` moves ≥ 5  
*when:* the futures basis moved ≥ 5 pts in the trade direction since entry (`hold_basis_chg_dir`).  
*evidence:* basis_chg (core) × dir.
- The futures basis has moved {basis_chg} pts your way since entry ({basis_in} → {basis}): the futures crowd is leaning in before cash.
- Basis {basis} now, {basis_in} at entry. Futures are running ahead of the index.
- The futures are pricing more of this move than spot has delivered yet: basis {basis}.
- Basis widening in your direction ({basis_chg} pts) — the derivative crowd expects spot to catch up.

**ant.bigger_than_best** · kind `day` · tone information · prio 35 · cool-down 300 s  
*when:* the open gain is above 80 % of the day's best realised trade (`hold_day_best_rs`) but not yet above it.  
*evidence:* book.trades pnl_rs max vs the open P&L.
- This trade is within reach of the day's best ({day_best}). The rule does not care; the number is for you.
- Open {pnl_rs}; best realised today {day_best}. Close.
- If the trail takes it here it is nearly the biggest trade of the day ({pnl_rs} vs {day_best}). If it runs, more so. Either way the rule carries it.
- {pnl_rs} on the table against a day best of {day_best}.


### CAUTION — still a stay, but the picture has a flaw

**cau.giveback** · kind `premium` · tone caution · prio 60 · cool-down 60 s; re-fires when `giveback_pct` moves ≥ 3  
*when:* give-back ≥ 5 % of entry (`giveback_pct`) and NOT the warning case (best ≥ 10 % with more than half gone).  
*evidence:* giveback_pct (core) >= 5 and not GB_WARN.
- You are {ret_pct} but have given back {giveback} % from the best; the lock {lock_status}. On {ref_date} {ref_gb5} of {five} % give-backs recovered to a new high.
- Off the best by {giveback} %. About half of these ({ref_gb5_n}) came back on {ref_date}; half did not. The stop is {stop_pts} pts away either way.
- {giveback} % given back from {best_ret}. Not a signal, a cost — the trail is paid for in exactly this currency.
- Best was {best_ret}, now {ret_pct}. The lock {lock_status}; the trail keeps the decision.

**cau.stall** · kind `trail` · tone caution · prio 55 · cool-down 90 s; re-fires when `hold_stall_s` moves ≥ 60  
*when:* 120 s ≤ seconds since the best spot < 180 s (`hold_stall_s`).  
*evidence:* hold_stall_s: seconds since best_spot_fav last improved.
- No new high for {stall_m} minutes. {ref_stall_120} of two-minute stalls on {ref_date} still made a new best — but the clock is now charging {theta_cal} pts/min ({dte_clock}).
- {stall_m} min since the last best. Spot needs {flat_speed} pts/min just to pay theta. Watching, not flinching.
- The move has paused for {stall_m} min at {now_pts} pts. Most pauses resumed; the stop is {stop_pts} pts back if this one doesn't.
- Quiet for {stall_m} min. The trail has not moved; neither has the risk.

**cau.basket_split** · kind `basket` · tone caution · prio 55 · cool-down 90 s; re-fires when `hold_n_against` moves ≥ 2; not before 20 s in the trade  
*when:* ≥ 4 heavyweights against since entry and the basket has not turned (`hold_basket_split`).  
*evidence:* n_against >= 4 and not turned.
- The basket is split: {n_with} with you, {n_against} against — {worst_stock} is the one pulling the other way.
- {n_against} heavyweights leaning against you ({worst_stock} {worst_move}). Losers on {ref_date} averaged {ref_bl_against} against.
- Not everyone agrees: {worst_stock} and {n_against_minus1} others are going the other way.
- The index is being carried by {n_with} names while {n_against} fight it. Thinner than it looks.

**cau.iv_easing** · kind `greeks` · tone caution · prio 50 · cool-down 120 s; re-fires when `iv_chg` moves ≥ 1  
*when:* −3 < `iv_chg` ≤ −1.5 pts while spot is in favour (`spot_fav` > 0).  
*evidence:* −3 < iv_chg <= −1.5 with spot in favour.
- IV has eased {d_iv} points since entry; vega has taken {vega_rs} off a move that is otherwise yours.
- The premium is lagging the index a little: IV {iv_in} → {iv_now}. Delta gave {delta_rs}, vega took {vega_rs}.
- Vol is coming off ({d_iv}) as the move matures. Expect the premium to track spot less than one-for-one from here.
- IV off {d_iv}. Not a turn — a tax.

**cau.against_trend** · kind `structure` · tone caution · prio 45 · cool-down 300 s; not before 5 s in the trade  
*when:* the 30-min drift is ≥ 5 pts against the trade (`hold_with_trend` = −1) and the regime is not DIRECTIONAL.  
*evidence:* trend30 against by >= 5 pts and the regime not DIRECTIONAL.
- This is a counter-trend trade (half-hour drift {trend30} pts the other way) in a {regime} regime. Such entries averaged {ref_against_mean} on {ref_date}, median {ref_against_median}. The rule is the same; expect less.
- You are fighting the half-hour drift ({trend30} pts). It can work — {ref_against_winners} did on {ref_date} — but the base rate is thin.
- Against the half-hour trend ({trend30}), regime {regime}. The trail is the same; the odds are not.
- Counter-trend ({trend30} pts): the median outcome on {ref_date} was a scratch ({ref_against_median}). The trail stays strict.

**cau.sellers_refilling** · kind `book` · tone caution · prio 50 · cool-down 90 s  
*when:* the sellers' orders on the held contract read REFILLING (`sellers_o`), imbalance against by > 0.1 (`book_imb`) and the book lead is ≥ 0.2 (`book_lead`).  
*evidence:* sellers_o REFILLING, imbalance against, lead >= 0.2.
- Sellers are refilling on your {strike} {rr} (orders {cls_so}, imbalance {imb_o}) and this book has been leading price (lead {lead}). Supply is coming back.
- The other side of your contract is restocking ({cls_so}). On a book with lead {lead}, that has been meaning something.
- Seller orders {cls_so}, imbalance {imb_o}. The queue is turning against you.
- Fresh offers stacking on {strike} {rr} ({cls_so}). The trail is {stop_pts} pts away; the book is the early warning.

**cau.premium_lag** · kind `premium` · tone caution · prio 60 · cool-down 60 s; re-fires when `hold_prem_lag` moves ≥ 2  
*when:* a new spot best within the last 60 s (`hold_stall_s` ≤ 60) while the bid return trails the best return by > 3 % (`hold_prem_lag`) on a best ≥ 5 %.  
*evidence:* a new spot best within 60 s while the bid return trails the best return by > 3 %.
- Spot just made a new best but your premium on the bid is {prem_lag} % below its own best. IV {d_iv} pts — the option is not following the index.
- New spot high, no new premium high ({prem_lag} % off). Something in the vol surface is leaning against you ({d_iv} IV pts).
- The index moved; the option didn't ({prem_lag} % behind its best). On {ref_date} the {ref_lesson} trade lost on a {ref_lesson_pts}-point winning move this way.
- Divergence: spot best {fav_pts} pts, premium {prem_lag} % off its best. Watch the IV ({d_iv}).

**cau.near_wall** · kind `structure` · tone caution · prio 45 · cool-down 180 s; re-fires when `wall_room` moves ≥ 5  
*when:* the next OI wall is 1–15 pts ahead (`wall_room`).  
*evidence:* pressure.destination room <= 15.
- The {wall_level} OI wall is {wall_room} pts ahead. Walls stall moves more often than they stop them, but expect the trail to be tested here.
- Into the wall: {wall_level}, {wall_room} pts. Give-backs cluster at levels like this.
- {wall_room} pts to {wall_level}. If spot stalls here for {stall_warn_min} min, the odds drop to even ({ref_stall_180}).
- Approaching the wall at {wall_level}. The stop is {stop_pts} behind: a {trail}-pt rejection takes it.

**cau.spread_wide** · kind `data` · tone caution · prio 50 · cool-down 120 s  
*when:* the spread is > 1 % of the premium or > 3× the entry spread (`hold_spread_wide`).  
*evidence:* spread > 1 % of premium or > 3× the entry spread.
- The spread on {strike} {rr} has widened to {spread} ({spread_pct} % of premium). The bid, not the last, is what can actually be realised: {bid}.
- Can you actually get out at this? The bid is {bid}, {spread} below the ask. Your real return is {ret_bid}.
- Wide market: {bid} / {ask}. The engine fills at last; a live order would get the bid ({ret_bid}).
- Spread {spread} pts, {spread_x}× what it was at entry. Liquidity is thinning on this strike.

**cau.lull** · kind `time` · tone caution · prio 40 · cool-down 300 s; not before 60 s in the trade  
*when:* 15-min σ ≤ 5 and 1-min speed < 4 pts (`hold_lull`) while the trade is up; not before 60 s in the trade.  
*evidence:* sigma15 <= 5 and 1-min speed < 4.
- The lull: fifteen-minute σ {sigma15} pts, last minute {speed}. Between late morning and mid-afternoon the median minute moved {ref_lull} pts on {ref_date}. Theta runs; spot idles.
- Midday pace ({speed} pts/min). The trail is safe at {stop_pts} pts, but every idle minute costs {theta_cal} pts.
- Quiet tape ({speed} pts/min, σ {sigma15}). Nothing wrong, nothing happening.
- The market has gone quiet ({speed} pts/min). Your stop ({stop_spot}) has not.

**cau.costly_entry** · kind `entry` · tone caution · prio 45 · cool-down once per trade  
*when:* entry > 0.5 pt over the mid or the entry spread > 1 % of the premium (`hold_costly_entry`); once, in the first 30 s.  
*evidence:* entry − mid_in > 0.5 pt or entry spread > 1 % of the premium; first 30 s only.
- You paid {entry} against a mid of {mid_in} — {entry_vs_mid} pts above fair. Not a stupidity, a cost; the trade needs {entry_vs_mid_pct} % just to be flat on the mid.
- Entered {entry_vs_mid} pts over the mid on a {entry_spread} spread. Remember it when you read the P&L.
- The fill was on the costly side of the quote ({entry} vs mid {mid_in}). The first {entry_vs_mid_pct} % of this trade is paying for that.
- Entry at the ask on a {entry_spread} spread: that is where the first part of the give-back went before the trade began.

**cau.late_entry_wave** · kind `entry` · tone caution · prio 45 · cool-down once per trade  
*when:* |15-min return at entry| > 2 × σ15 at entry (`hold_late_entry`, from pos['signal']); once, in the first 60 s.  
*evidence:* |r15 at entry| > 2 × sigma15 at entry (pos['signal']).
- You entered after a {r15}-pt fifteen-minute move (σ {sigma15_in}). Late entries on {ref_date} ran less: the fuel was partly spent.
- This break came at the end of a {r15}-pt run. Expect a shorter leg and a quicker trail.
- The fifteen-minute return before entry was {r15} pts against a σ of {sigma15_in}. Some of the move happened before you.
- Entered into an extended move ({r15} pts). The trail is the same; the runway may be shorter.


### WARNING — the evidence has turned

**warn.theta_stall** · kind `greeks` · tone warning (bypasses cool-down and budget in the core) · prio 75 · cool-down 60 s; re-fires when `hold_idle_s` moves ≥ 120  
*when:* spot's 1-min speed below the theta flat speed for ≥ 180 s (`hold_theta_idle`).  
*evidence:* 1-min spot speed below |theta_cal|/|delta| for 3 consecutive minutes.
- Theta is now eating {theta_cal} pts a minute ({dte_clock}) and spot has not outrun it for {idle_min} minutes — the clock is against you.
- {idle_min} idle minutes. At {theta_cal} pts/min that is {theta_3m_rs} gone with the index flat. The stop is {stop_pts} pts away.
- Spot needs {flat_speed} pts/min in your favour to stand still; it is giving {speed}. The premium is bleeding.
- Idle index, running clock: {theta_cal} pts/min × {qty} = {theta_rs_min}/min.

**warn.vega_eating** · kind `greeks` · tone warning (bypasses cool-down and budget in the core) · prio 80 · cool-down 60 s; re-fires when `iv_chg` moves ≥ 1  
*when:* IV ≤ −3 pts since entry while spot is in favour (`hold_iv_off`) — the 13:44 / 14:24 / 13:36 pattern.  
*evidence:* iv_chg <= −3 with spot in favour — the 13:44 / 14:24 / 13:36 pattern of 19 Oct.
- Spot has moved {now_pts} pts your way but IV is off {d_iv} points: vega has taken {vega_rs} against delta's {delta_rs}. The premium is not following the index.
- This is the {ref_lesson} pattern from {ref_date}: a winning move in spot, a losing option. IV {iv_in} → {iv_now} ({vega_rs}).
- Vol crush on your leg: {d_iv} IV pts = {vega_rs}. The move has to keep going just to stand still.
- IV has come off {d_iv}. Your premium is {ret_pct} on a {now_pts}-pt move that should have been worth {delta_only_pct}.

**warn.basket_turned** · kind `basket` · tone warning (bypasses cool-down and budget in the core) · prio 75 · cool-down 60 s; re-fires when `hold_n_against` moves ≥ 2; not before 20 s in the trade  
*when:* heavyweights against ≥ with + 3 (`hold_basket_turned`).  
*evidence:* n_against >= n_with + 3.
- The basket has turned: {n_against} heavyweights against you, {n_with} with. {worst_stock} ({worst_move}) is the one ruining this trade.
- Breadth has flipped. {worst_stock} led the turn; {n_against} of {n_eq} now lean the other way.
- The index is being held up by {n_with} names only. The rest — {worst_stock} first — are leaving.
- {n_against} against, {n_with} with. On {ref_date} that was the loser's profile ({ref_bl} with, {ref_bl_against} against).

**warn.stop_near** · kind `trail` · tone warning (bypasses cool-down and budget in the core) · prio 85 · cool-down 20 s; re-fires when `stop_dist` moves ≥ 1  
*when:* 2 < `stop_dist` ≤ 4 pts (`hold_stop_near` and not `hold_stop_imminent`).  
*evidence:* 2 < stop_dist <= 4 pts.
- The stop is {stop_pts} pts away at {stop_spot}. One ordinary minute of this tape ({speed} pts) can reach it.
- {stop_pts} points of trail left. If it goes, it goes at {stop_spot} for about {exit_est_rs}.
- Close to the trail: {stop_pts} pts. The rule is about to speak.
- Spot {spot_txt}, stop {stop_spot}. The gap is {stop_pts}.

**warn.lock_near** · kind `trail` · tone warning (bypasses cool-down and budget in the core) · prio 85 · cool-down 20 s; re-fires when `hold_lock_gap` moves ≥ 1  
*when:* the lock is armed and the bid return is within 3 % of the lock floor's return (`hold_lock_gap` ≤ 3).  
*evidence:* bid return within 3 % of the lock floor's return.
- You are {ret_bid} on the bid; the lock fires at {lock_q}. {lock_gap} % of give-back left before the rule takes {lock_rs}.
- The lock is {lock_gap} % away. It would close this at about {lock_floor} for {lock_rs}.
- Near the lock: {ret_bid} vs {lock_q}. Nothing to do; it is the rule's exit, not yours.
- {lock_gap} % between you and the lock. It protects {lock_rs} either way.

**warn.giveback_half** · kind `premium` · tone warning (bypasses cool-down and budget in the core) · prio 80 · cool-down 60 s; re-fires when `giveback_frac` moves ≥ 0.1  
*when:* best ≥ 10 % and more than half of it gone (`best_pct`, `giveback_frac` > 0.5).  
*evidence:* best >= 10 % and more than half of it gone.
- You have given back more than half of the best: {best_ret} → {ret_pct}. On {ref_date} {ref_gb_half_flat} trades that saw +{ten} % ended near flat this way.
- Half the gain is gone ({giveback} % of {best_ret}). The shape of this trade has changed.
- Best {best_ret}, now {ret_pct}. This is where "it will come back" costs the most.
- More than half the best has been returned ({giveback} %). The trail at {stop_spot} is the floor; the lock {lock_status}.

**warn.regime_flip** · kind `structure` · tone warning (bypasses cool-down and budget in the core) · prio 70 · cool-down 120 s  
*when:* the regime direction flipped against the trade since entry, or the state fell into RANGE / EXHAUSTION (`hold_regime_flipped`).  
*evidence:* regime dir flipped to −dir, or state fell into RANGE / EXHAUSTION since entry.
- The regime has changed since entry: {regime_in} → {regime}, direction {regime_dir}. Range-regime trades averaged {ref_range_mean} on {ref_date}.
- The engine now reads the market as {regime} ({regime_text}). The thesis you entered on is weaker.
- Regime turned {regime} (was {regime_in}). It does not exit you; it tells you what the trail is likely to meet.
- {regime_in} at entry, {regime} now. The tape has changed character.

**warn.straddle_against** · kind `structure` · tone warning (bypasses cool-down and budget in the core) · prio 70 · cool-down 120 s  
*when:* the straddle watch reads SPIKE on the other leg (`hold_straddle_spike_with` is False).  
*evidence:* straddle_watch SPIKE on the leg that is not the held rr.
- The ATM straddle ({straddle}) is spiking on the other leg ({straddle_leg}) — the market is buying protection against your direction.
- Vol is being bought on the {straddle_leg} side ({straddle_state}). That is money betting the other way.
- Straddle spike, wrong leg: {straddle_leg}. Your {rr} is not the one being chased.
- The straddle expansion is against you ({straddle_leg}, {straddle}).

**warn.stall_long** · kind `trail` · tone warning (bypasses cool-down and budget in the core) · prio 70 · cool-down 60 s; re-fires when `hold_stall_s` moves ≥ 60  
*when:* ≥ 180 s since the best spot (`hold_stall_s`).  
*evidence:* hold_stall_s >= 180.
- No new high for {stall_m} minutes. On {ref_date} the odds of another best from here were even ({ref_stall_180}), and no trade survived a {no_survive_min}-minute stall.
- {stall_m} min since the best. The trail took every stalled trade within {ref_stall_max} on {ref_date}.
- {stall_m} minutes flat at {now_pts} pts. The stop is {stop_pts} away; theta is {theta_cal}/min.
- Stalled {stall_m} min. Even odds now ({ref_stall_180}). The rule is close to deciding.

**warn.data** · kind `data` · tone warning (bypasses cool-down and budget in the core) · prio 90 · cool-down 10 s; re-fires when `quote_age` moves ≥ 5  
*when:* data gap, exit pending, or the held quote older than 5 s (`hold_data_bad`).  
*evidence:* gap_on, exit_pending, or the held quote older than 5 s.
- Data: the held quote is {quote_age} s old{pending_text}. No verdict on a frozen number — the rule is waiting for a fresh print.
- Feed gap ({quote_age} s). The trail does not move on stale data and neither does this panel.
- An exit is pending ({pending_reason}) — waiting for a quote fresher than {five} s (this one is {quote_age} s).
- The engine is in blackout ({blackout_why}, quote {quote_age} s). Decisions resume when the data does.

**warn.thin** · kind `data` · tone warning (bypasses cool-down and budget in the core) · prio 65 · cool-down 120 s; not before 30 s in the trade  
*when:* the position is > 10 % of the last minute's volume on the held strike (`hold_thin`).  
*evidence:* qty > 10 % of the last minute's volume on the held strike.
- Your {qty} units are {pos_vs_vol} % of the last minute's volume on {strike} {rr}. A market exit would move the price.
- Thin strike: {vol_1m} units/min against your {qty}. The rule's fill at last is optimistic here.
- Liquidity warning. The exchange traded {vol_1m} on this contract in the last minute; your position is {qty}.
- {pos_vs_vol} % of a minute's volume — expect slippage beyond the {spread} spread.

**warn.spot_fut_split** · kind `structure` · tone warning (bypasses cool-down and budget in the core) · prio 65 · cool-down 120 s; re-fires when `hold_basis_chg_dir` moves ≥ 4  
*when:* the basis moved ≥ 8 pts against the trade since entry (`hold_basis_chg_dir` ≤ −8).  
*evidence:* basis moved >= 8 pts against the trade since entry.
- The futures have stopped confirming: basis {basis_in} → {basis}. Spot is making the move alone.
- Futures are leaning the other way (basis {basis_chg} pts against you). Cash moves that futures do not follow tend to fade.
- Spot moving, futures not ({basis_chg} pts of basis against) — the derivative crowd is not buying this leg.
- Basis divergence {basis_chg} pts against the trade.


### TIME — the clock is a fact like any other

**time.flatten_countdown** · kind `time` · tone caution · prio 70 · cool-down 60 s; re-fires when `min_to_flatten` moves ≥ 5  
*when:* 5 < minutes to the flatten ≤ 15 (`min_to_flatten`).  
*evidence:* 5 < min_to_flatten <= 15.
- {mins_to_exit} minutes to the flatten at {time_exit}; a timed exit is coming whatever spot does.
- The clock closes this at {time_exit}. {mins_to_exit} min left; after that the rule takes the last print.
- {mins_to_exit} min. On expiry the engine flattens at {flat_0dte} unless delta ≥ {delta_run} (yours: {delta}).
- Time, not price, may end this one: {mins_to_exit} min to {time_exit}.

**time.imminent** · kind `time` · tone warning (bypasses cool-down and budget in the core) · prio 94 · cool-down 15 s; re-fires when `min_to_flatten` moves ≥ 1  
*when:* minutes to the flatten ≤ 5 (`min_to_flatten`); the core's own `flatten_soon` (prio 95) usually speaks first.  
*evidence:* min_to_flatten <= 5; the core's flatten_soon says the same from the config clock.
- {mins_to_exit} min. The timed exit will take this at the next print after {time_exit}.
- Under {five} minutes ({mins_to_exit}). Expect a TIME exit at about {last} for {pnl_rs}.
- The session is ending for this trade: {mins_to_exit} min to {time_exit}.
- {time_exit} is {mins_to_exit} min away. The rule does not wait for a better price.

**time.first_minute** · kind `time` · tone information · prio 40 · cool-down once per trade  
*when:* the first 60 s of the trade, once (`hold_s` < 60).  
*evidence:* fires once in the first minute.
- First minute. Winners on {ref_date} reached +{ten} % at a median {ref_first10}; the stop is at {stop_spot}, {trail} pts from your entry.
- Just in at {entry}, {lots} lots, {cap_deployed} deployed. The break gets a minute to prove itself.
- {hold_s_txt} s in. Every winner of {ref_date} was already moving by {ref_first10} — but so were some losers.
- Entry done. Stop {stop_spot}. The next sixty seconds usually tell.

**time.long_hold** · kind `time` · tone information · prio 45 · cool-down 300 s  
*when:* held more than 600 s (`hold_s`).  
*evidence:* hold_s > 600.
- Held {hold_m} min. The longest winner on {ref_date} ran {ref_longest_winner}; long holds that were not already paid tended to end as scratches.
- {hold_m} minutes in at {ret_pct}. Slow trades were the thin ones on {ref_date}.
- {hold_m} min. The trail is {stop_pts} pts away; the clock is {theta_cal} pts/min against you.
- A long one: {hold_m} min. Not wrong, just rarer than it feels.

**time.last_hour** · kind `time` · tone information · prio 45 · cool-down 600 s  
*when:* clock ≥ 14:30, or ≥ 14:00 on expiry (`hold_last_hour`).  
*evidence:* now >= 14:30 (14:00 on expiry).
- Last hour. Entries close at {last_entry}; this is the last swing you can be in today. Gamma is highest, theta too ({theta_cal} pts/min).
- The final hour: your delta is {delta}; on expiry, above {delta_run} the engine lets it run past {flat_0dte}.
- Late session. On {ref_date} the last-hour trade made {ref_last_hour_trade} — the last hour moves, it just moves fast both ways.
- Clock: {mins_to_exit} min to {time_exit}. Pace picks up late; the flatten comes first.

**time.lunch** · kind `time` · tone information · prio 35 · cool-down 900 s  
*when:* 12:00–13:15 and the lull facts true (`hold_lunch`, `hold_lull`).  
*evidence:* 12:00–13:15 and the lull facts true.
- Lunch tape: median minute {ref_lull} pts on {ref_date}; right now {speed}. Trails survive; premiums leak.
- Midday ({speed} pts/min). Expect stalls to run longer and mean less.
- The market thins over lunch. Patience is cheaper now, but not free: {theta_cal} pts/min.
- Lull hours. The stop is {stop_pts} away and nothing ({speed} pts/min) is pushing toward it.

**time.no_reentry** · kind `time` · tone information · prio 50 · cool-down once per trade  
*when:* clock past the last-entry time (`hold_no_reentry`: 14:45 on expiry, else LAST_ENTRY); once.  
*evidence:* now past LAST_ENTRY (ZERO_DTE_NO_ENTRY on expiry).
- Entries are closed for the day ({last_entry}). Whatever this trade becomes, there is no next one.
- This is the last trade of the day by rule (no entries after {last_entry}). The same rule carries it.
- No re-entry after {last_entry}. The trail is the only decision left today.
- Final position of the session (entries closed at {last_entry}).


### DISCIPLINE — the rule, the size, the day

**disc.rule_exits** · kind `trail` · tone lesson · prio 50 · cool-down 240 s; not before 45 s in the trade  
*when:* any trade with a stop (`stop_spot`, `stop_dist`); low priority, after 45 s.  
*evidence:* always true in a trade; low priority.
- The rule exits at the trail, not at a feeling — the stop is at {stop_spot}, {stop_pts} points away.
- Your exit is already placed: {stop_spot}. The only way out is spot coming {trail} pts off its best.
- Nothing on this panel is a button. The trail at {stop_spot} is.
- The decision was made at entry: {trail} pts behind the best. Everything since ({stop_pts} pts of room now) is bookkeeping.

**disc.no_target** · kind `premium` · tone lesson · prio 45 · cool-down 300 s  
*when:* `ret_pct` ≥ 15.  
*evidence:* ret_pct >= 15.
- There is no target. On {ref_date} the three biggest trades ({ref_big3}) all ran past the point where a target would have closed them.
- Anticipating a price is fine; closing at one is not the rule. The trail took {ref_top_trade} by waiting.
- Targets cap winners; the trail caps give-backs. Only one of those pays for the losers. You are {ret_pct}.
- You are {ret_pct}. The rule does not know that number; it knows {stop_spot}.

**disc.biggest** · kind `day` · tone lesson · prio 45 · cool-down 300 s  
*when:* the open gain exceeds the day's best realised trade (`hold_biggest_today`).  
*evidence:* open pnl_rs > the day's best realised trade.
- This is already the biggest trade of the day ({pnl_rs} vs {day_best} realised). Size does not change the rule.
- Day's largest open P&L ({pnl_rs}). The stop is still {stop_pts} pts away; the number does not move it.
- {pnl_rs} on {qty} units — larger than anything booked today. The trail is doing the holding.
- Big one ({pnl_rs}). Same rule.

**disc.swings** · kind `day` · tone lesson · prio 35 · cool-down 600 s; not before 120 s in the trade  
*when:* any trade, after 120 s (`trades_today` known).  
*evidence:* book.trades count + the open one.
- Swing {swings_used} of the day. One trade per swing: when this closes, the next needs a new break.
- Trade {swings_used} today; realised {day_pnl}. This one is {pnl_rs} on top.
- Day so far: {swings_used} trades counting this one, {wins} won, {day_pnl}. This is the open one.
- {swings_used} swings used. Capital now {capital}; deployed in this trade {cap_deployed}.

**disc.size** · kind `entry` · tone lesson · prio 40 · cool-down once per trade  
*when:* the first 30 s, once.  
*evidence:* fires once in the first 30 s.
- {lots} lots = {qty} units; every premium point is {rs_per_pt}. The {trail}-pt trail is about {stop_rs_entry} at your delta.
- Capital deployed {cap_deployed} of {capital}. At {delta} delta, one spot point ≈ {rs_per_spot}.
- All-in: {lots} lots at {entry}. One premium point = {rs_per_pt}; one spot point ≈ {rs_per_spot}.
- Size: {qty} units ({lots} lots). The arithmetic of the day is set; only the price moves now.

**disc.day_context** · kind `day` · tone lesson · prio 35 · cool-down 600 s; not before 30 s in the trade  
*when:* the day's realised P&L is negative (`realised_rs` < 0) while this trade is up.  
*evidence:* realised_rs < 0 with an open gain.
- The day is {day_pnl} realised; this trade is {pnl_rs}. Do not ask it to repair the day — ask it to follow the rule.
- Down on the day ({day_pnl}), up on the trade ({pnl_rs}). The trail does not know either number.
- {pnl_rs} open against {day_pnl} booked. Staying in to "get back to flat" is the feeling the rule exists to replace.
- Day context: {day_pnl}. Trade context: {stop_pts} pts to the stop.

**disc.entered_well** · kind `entry` · tone praise · prio 35 · cool-down once per trade  
*when:* not a costly entry (`hold_costly_entry` False) with the entry-vs-mid known; once, in the first 30 s.  
*evidence:* the praise twin of cau.costly_entry.
- Entered at {entry} on a {entry_spread} spread, {entry_vs_mid} from the mid. Clean fill.
- No "entered costly" today: {entry} vs mid {mid_in}.
- The fill was fair ({entry_vs_mid} vs the mid). Whatever happens next is the market, not the entry.
- Good entry price ({entry}, mid {mid_in}). The rest is the rule's.


### EXIT REVIEW — the receipt (kind `review`: composed by `review_card`, never selected live)

**exit.summary** · kind `review` · tone lesson · prio 100 · cool-down once per trade  
*when:* review line 1, always.  
*evidence:* line 1 of the review card.
- Closed {ret_pct} ({pnl_rs}) at {exit}: best was {best_ret} — {giveback} % given back, {vega_share_pct} % of it IV coming off, the rest the trail's {trail} points.
- Closed {lots} lots at {exit} on {reason}. Peak {best_ret}, realised {ret_pct}. Held {hold_m} min.
- {reason} at {exit}. Attribution: delta {delta_rs}, vega {vega_rs}, theta and spread {resid_rs}.
- Out: {pnl_rs}. Best seen {best_ret}; the trail cost {giveback} %, which on {ref_date} was about the average price ({ref_gb_mean}) of letting winners run.

**exit.trail_cost** · kind `review` · tone lesson · prio 60 · cool-down once per trade  
*when:* review line 2 when the exit was TRAIL with a best ≥ 10 % (phrasing 2 for a LOCK exit).  
*evidence:* TRAIL exit with best >= 10 %.
- The trail took {giveback} % from the best. The same trail gave {ref_date}'s {ref_big3}. It is one rule, both ways.
- Give-back {giveback} %: {trail} spot pts × {delta_abs} ≈ {trail_pts_prem} premium pts. That is the rule working, not failing.
- From best to exit: {giveback} %. The average on {ref_date} was {ref_gb_mean}.
- A trail is paid for at the end. This one cost {giveback_rs}.

**exit.stop_review** · kind `review` · tone lesson · prio 60 · cool-down once per trade  
*when:* review line 2 when the exit was STOP or the return < −3 %.  
*evidence:* STOP exit or ret < −3 %.
- Stopped at {exit} for {pnl_rs}. Best was only {best_ret}: the break did not travel. On {ref_date} {ref_losers_no10} losers never saw +{ten} spot pts.
- A loser that never worked: best {fav_pts} spot pts, trail at {trail}. Nothing to learn except that it was a losing break.
- {pnl_rs}. Entry {entry}, exit {exit}, {hold_m} min. The basket was {n_with} with / {n_against} against — {worst_stock} led the other way.
- Loss {pnl_rs}. The entry was {entry_quality}; the move was not there.

**exit.time_review** · kind `review` · tone lesson · prio 60 · cool-down once per trade  
*when:* review line 2 when the reason starts with TIME.  
*evidence:* reason starts with TIME.
- Flattened by the clock at {exit} for {pnl_rs}. The trail was {stop_pts} pts away; time got there first.
- TIME exit. Best {best_ret}, closed {ret_pct}. No price decision was made — the session ended.
- The clock closed this one. {pnl_rs}.
- Timed out at {time_exit} with {ret_pct}.

**exit.winning_move_lost** · kind `review` · tone lesson · prio 70 · cool-down once per trade  
*when:* review line 2 when the trade lost with a best spot excursion ≥ 10 pts (takes precedence).  
*evidence:* pnl < 0 with a best spot excursion >= 10 pts.
- Spot moved {fav_pts} pts your way and the trade still lost {pnl_rs}: IV came off {d_iv} pts (vega {vega_rs}) and the trail gave back the rest. A right call, a wrong instrument today.
- The index did what you said ({fav_pts} pts); the premium did not. Vega {vega_rs} against delta {delta_rs}.
- Lost on a winning move ({fav_pts} pts, {pnl_rs}). {ref_lesson} on {ref_date} was the same: {ref_lesson_pts} pts in favour, {ref_lesson_rs}.
- Direction right, vol wrong. {d_iv} IV pts cost {vega_rs}.

**exit.what_followed** · kind `review` · tone lesson · prio 50 · cool-down once per trade  
*when:* NOT used by the card (see 'not ported'); the phrasings are the honest stand-in without a 60-s-later price.  
*evidence:* the core gives no 60-s-later hook; this is the honest stand-in (see docs).
- Where it went after the exit is for the tape to say: the rule is judged over a season, not a minute. Closed at {exit}.
- Hindsight is allowed later, not now. Out at {exit}; the next minute will show whether the trail was early or right.
- The receipt stops at {exit}. What the {strike} {rr} does next is noted on the tape, not acted on.
- Closed at {exit}. The minute after is information, not a verdict on the rule.

**exit.day_tally** · kind `review` · tone lesson · prio 40 · cool-down once per trade  
*when:* review line 3, always.  
*evidence:* line 3 of the review card.
- Day: {swings_used} trades, {wins} won, {day_pnl}. Capital {capital}. Biggest {day_best}.
- Booked. Running total {day_pnl} on {swings_used} swings.
- {day_pnl} for the day ({wins} of {swings_used} won). The next entry needs a new break.
- Tally: {wins}/{swings_used}, {day_pnl}.

