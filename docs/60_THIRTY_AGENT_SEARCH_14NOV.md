# 60. The 30-agent search for more trades and more profit (14 Nov 2026, while the owner is away)

Owner, 14 Nov: "Do not fucking stick to the idea of only using those pullback mechanisms to trade. If you want to run
replays run it during this time ... Ask 30 agents to work on improving the system, make it more profitable, test
their analogies, utilize the market hours to trade differently at different times. Use different mathematics, option
greeks, calculus, models and everything ... I want a more profitable system where more trades are taken ... Take a
best decision yourself."

## 1. The bar, written before any result was seen (pre-registration)

Written at the start of the run, before the agents were started. A new entry family joins the live Conductor's
pool (a dated row in `apex/rules/pool.json` from Mon 16 Nov, the champion's own books kept, so it only ADDS trades)
only if every test below holds. Anything that fails stays a shadow book.

1. **Both halves of the year.** Positive mean trade AND positive sum of daily results (account fresh every day,
   all-in within the day) on the half it was tuned on ("found", 7 May to 16 Oct 2026) AND on the half it was not
   ("judged", 14 Nov 2025 to 6 May 2026), for each day type it trades.
2. **An untouched year.** Positive sum of daily results on the holdout year (14 Nov 2024 to 13 Nov 2025), which no
   agent sees. A family that needs inputs the holdout year does not have (the option chain's open interest, the
   heavyweights) must instead show t >= 2 on the judged half and be positive on the recorded window.
3. **It adds to the account.** Pooled with the champion in one account (no pause between trades, the champion
   first on a tie), it raises the sum of daily results on found, judged and holdout, and the pooled winners % does
   not fall more than 2 points below the champion's alone.
4. **Real prices.** Priced on real option IV (the broker's minute bars) the sign does not flip.
5. **It runs.** Built as a real engine strategy class it reproduces at least 80 % of its harness entries on the
   recorded sessions, the engine replay on the recorded tapes shows no fault, and the median engine step stays
   under 25 ms with it loaded.
6. **Multiple testing.** Every variant an agent tries is logged; the finalist must show t >= 2 on judged + holdout
   together, not only on its best split.

The owner's earlier decisions stand: the champion keeps trading, expiry days included ("Keep it live", 14 Nov);
all-in on every trade, never position sizing; buy only, at the money or in the money; paper only.

## 2. The harness every agent used

`data/research/14nov/work/arena.py` (one scoring path for all ideas), validated in `arena_check.py` on the 18
recorded sessions against the tape's real per-second option quotes:

| Check | Normal days | Expiry days |
|---|---|---|
| Real-IV per-second price against the tape mid (mean absolute error) | 0.36 % | 0.93 % |
| Old model price against the tape mid | 23.4 % | 28.8 % |
| The champion's trades: correlation of results, real-IV against tape | 1.00 | 0.96 |
| Same, model against tape | 0.98 | 0.64 |
| Pooling the champion with nothing keeps every trade | 1,081 of 1,081 | |

Real-IV pricing: the broker's real 1-minute close of each contract gives its implied volatility each minute; the
price each second is Black-76 on the per-second Nifty future with that IV interpolated through the minute.

## 3. What ran (14 Nov evening to 15 Nov early morning)

- 84 agents in one workflow, about 12 hours, 0 errors: 30 round-1 themes, 23 adversarial verifiers, a planner,
  12 round-2 themes and their verifiers. **4,217 variants are logged** in `data/research/14nov/agents/*/trials.jsonl`
  (the multiple-testing count). With that many tries the largest t a pure-noise rule is expected to show is about 3.6.
- Data finished during the run: 246 sessions of real 1-minute option bars and captured inputs (`hist_wx`), minute
  features for all 246 (the recorded window included, after a fix), and 245 holdout sessions of 1-second futures
  (`hist1s`), 145 of them with real option bars from MYTHOS (`hist_wx_mythos`).

## 4. The live system's own baseline, repriced on real option IV

The five pool books' real strategy classes stepped per second on a real-IV option chain and merged as the Conductor
merges them (`work/s50_live_chain.py`; correlation 0.963 with the tape on the recorded sessions). Sum of daily results:

| Split | Normal days | Expiry days |
|---|---|---|
| Found (7 May to 16 Oct 2026) | -335 (176 trades) | -291 (195) |
| Judged (14 Nov 2025 to 6 May 2026) | +136 (240) | -521 (393) |
| Window (19 Oct to 13 Nov 2026) | +437 (58) | +437 (72) |

The recorded window is the system's best stretch. Outside it the live pool loses, and expiry days do the damage.

## 5. Harness faults found by the agents, and what was done

| Fault | Effect | Status |
|---|---|---|
| Champion cache built before the downloads finished | judged expiry pooled numbers treated the champion as flat | rebuilt (now incl. the holdout) |
| No minute features on the 18 recorded sessions | captured-data ideas had no window test | fixed in `s44_wxfeat.one` (forward from the tape, VWAP optional) |
| Real-IV price interpolated toward the CURRENT minute's close (up to 59 s ahead) | +0.22 % a trade on normal days, +1.35 % on expiry days, flattering every idea | `agents/r2_harness_fix/arena_fixed.py` holds the IV of the last completed minute; all verdicts below use it |
| First-come pooling: an idea's open trade blocks champion trades | pooled gain partly = displaced champion losers (found) or winners (judged) | champion-priority pool in `arena_fixed.py` |
| Signals silently dropped when the strike was outside the 13 downloaded strikes | 368 drops | model fallback in `arena_fixed.py` |
| Raw future levels (prior close, gap) mixed with the spot-like forward | gap off by up to 1.5 day-sigmas on roll days | spot-coordinate meta in `arena_fixed.py` |
| Whole-day median basis | strike differs on 17 % of trades | 09:20 basis in `arena_fixed.py` |

## 6. The verdict on the pre-registered bar

Round 1: 7 of 23 candidates were confirmed by their verifiers. Re-scored on the corrected data, two held on found,
judged and window: the late opening-range fade (`agents/opening/gen_orb_late.py`) and the three fades on expiry days
(`agents/_finalists/gen_fB_fade3x.py`). Round 2 (regime switching, a time-of-day fade council, new exits, signal
handover, timing-versus-side, the IV clock with greeks strikes, a four-year proof) produced no promotable book.

Final scoring on causal IV, every split, the holdout year opened once (`work/s53_fixed_verdict.py`,
`agents/_finalists/fixed_verdict.csv`). Sum of daily results, trades in brackets:

| Book | Day type | Found | Judged | Window | Holdout |
|---|---|---|---|---|---|
| Champion | normal | -438 (183) | +54 (246) | +330 (56) | -271 (442) |
| Champion | expiry | -926 (267) | -873 (444) | -82 (90) | +1,247 (344) |
| Late opening-range fade | normal | +125 (85) | +231 (87) | -1 (11) | -178 (180) |
| Three fades | expiry | +98 (48) | -46 (46) | +63 (6) | -164 (60) |
| Champion's seconds, 60-min fade side | normal | -119 | +279 | +175 | -431 |
| Champion's seconds, 60-min fade side | expiry | -347 | -8 | -66 | -165 |

**No candidate passes.** Every finalist loses on the untouched holdout year. The live pool is unchanged; nothing is
added on Monday.

## 7. The one lead worth building: switch the expiry style by recent results

Found after the agents finished, by the run owner, on all 83 real-IV expiry days (so it is selected, not
pre-registered). On each expiry day, trade the champion's expiry breakout if its last 6 expiry days summed at least
as much as the three fades' last 6, otherwise trade the fades. Causal IV:

| Expiry days | Found | Judged | Window | Holdout | All 83 |
|---|---|---|---|---|---|
| Champion | -926 | -873 | -82 | +1,247 | -634 |
| Three fades | +98 | -46 | +63 | -164 | -50 |
| Switch (last 6) | +98 | -233 | +63 | +1,259 | +1,186 |

Lookbacks of 4 and 8 give +1,178 and +1,153. The gain over the champion has t 4.23 on the daily difference, beats
99.9 % of random switches with the same share, and beats all 2,000 shuffles of the day order. That last test says the
edge is persistence: an expiry style that has been working keeps working for weeks. It still loses on judged, so it
fails test 1 as a standalone book, and it replaces rather than adds on expiry days, which the owner decided to keep
("Keep it live"). Recommendation: build it as a shadow account first (needs a three-fade expiry book and the switch
in the Conductor), and let the owner decide after it has run live.

## 8. What the search established

1. The price-only entry families (fades, breakouts, opening ranges, regimes, filters, models) do not carry a stable
   edge from one year to the next on these prices. Several looked strong on one or two splits; none survived four.
2. The system's result is decided by expiry days, and expiry-day style (breakout or fade) flips with the regime.
3. Time-of-day structure is real (09:15-09:45 loses for every entry; normal-day ATM IV falls 5-10 % over the day;
   expiry afternoons see IV rise 12-27 %), but no rule built on it made money out of sample.
4. Fade exits want a 25 % stop, no forward trail and a 45-minute clock; the champion's ladder costs about 1 % a trade
   on random entries. Useful for any future fade book.

## 9. The shadow is built (15 Nov, owner: "Yes, build the shadow")

| Piece | Where | What it does |
|---|---|---|
| fade3x | `apex/engine/council/fade3x.py`, `VARIANTS["fade3x"]` | the three fades (20 min / 0.6 sigma, 60 min / 0.7 sigma, first break of the 15-minute opening range until 11:45) on expiry days only; champion's picker; champion's expiry ladder with a 45-minute clock |
| conductor_xs | policy `xswitch` in `apex/engine/conductor.py`, `VARIANTS["conductor_xs"]` | its own all-in account: the live pool on normal days; on expiry days, at the first trigger, it reads the history and takes only the pool's triggers or only fade3x's for the rest of the day |
| history | `data/learning/expiry_switch.json` | 83 research expiry days (src "research", causal prices) seeded; each evening `learning.xswitch_record` adds the day's live Conductor and fade3x results when the day is an expiry day (src "live") |
| report | nightly report, shadow section | conductor_xs and fade3x appear beside the live Conductor from 16 Nov |

Both are shadows registered last (122 variants). The live Conductor and `apex/rules/pool.json` are unchanged.

Checks: on 52 expiry days (judged, found, window) the engine class stepped per second on the real-IV chain reproduced
97 of 98 research entries (99 %), with day sums +372 % against +376 %; its strategy step costs 0.42 ms a second
(`work/s54_fade3x_fidelity.py`). Tests: `tests/test_xswitch_15nov.py` (6), full suite passes.

On the next expiry day the switch starts in fade mode: over the last 6 research expiry days fade3x made +92 % and the
pool's champion pattern -169 %. Remove both shadows by deleting the two VARIANTS lines; nothing else depends on them.

## 10. Correction (15 Nov review, docs/61)

Two figures in this document were produced with the simulator's time decay in the wrong unit (per calendar minute; the
engine uses per trading minute, 3.84 times larger). They were not rerun and should not be quoted until they are:

* section 4, the expiry column of the live system's baseline repriced on real option IV;
* section 9, the +372 % day sum of the fade3x check. Its 97 of 98 entry times stand: entries do not read time decay.

The holdout verdict (sections 5 to 7) and the switch's seeded history do not use that value and stand as written.
