# Rule team brief — 8 Nov 2026 (ApexOptions, owner's instruction)

You are one of ten agents. Each has a set of BOOKS (paper-trading strategies of a buy-only Nifty weekly-options
system). Your job, in the owner's words: "apply rules to different books and make them only profitable and remove
losses completely. Attempt all kinds of permutation and combination and every kind of mathematics that can be applied
before a book actually triggers. Make each book more and more profitable and reduce the loss-making trades to almost nil."

## The data

14 replayed trading days (19 Oct – 6 Nov 2026). Every trade of every book carries the WEATHER PHOTOGRAPH taken at its
trigger second: ~270 numeric and text fields (trend over 30/60 min, speed, acceleration, Kalman velocity, realised vol,
every Greek incl. vanna/vomma/charm, IV and changes, order flow, OI, breadth, heavyweights, domino type, time of day,
other books firing, feed health...). A rule may use ONLY what is known at the trigger second: these fields and
anything computed from them. The outcome (ret_pct, pnl_rs, exit reason) is the label, never an input.

Toolkit (read its docstring first):
`C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team/rule_lab.py`
Run Python as `py -3.13` with `PYTHONIOENCODING=utf-8` (numpy is available there; the default `python` lacks it).
Loading the 14 days takes ~60 s; load once per script. Field meanings: `D:/ApexOptions/apex/engine/weather.py`
(the docstring at the top lists every item) and `D:/ApexOptions/docs/27_PRE_TRADE_FACTORS.md`.

## HARD CONSTRAINTS

* READ-ONLY on `D:/ApexOptions`. Write only under your own folder
  `C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team/agent_<N>/`.
* Never run a replay, the engine, or pytest. Never read `D:/ApexOptions/secrets`.
* Do not edit rule_lab.py (copy a function into your own script if you need a variant).
* Keep each script's run under ~15 minutes; use numpy (matrix tricks in rule_lab.best_pair) rather than Python loops
  over pairs. Nine other agents share this machine.

## THE STANDARD (a rule that fails it is reported as rejected, not hidden)

The owner's register admits a rule only when it is more than a memory of the tape. For every rule you propose:
1. Discovery = the first 10 days, holdout = the last 4 (`rule_lab.split_days`). Search ONLY on discovery.
2. On discovery: kept side >= 20 trades, profitable in mean return and in rupees; removed side's losers > winners.
3. Shuffle test: re-run the SAME search (same features, same width, same depth) on >= 200 shufflings of the discovery
   outcomes (`rule_lab.shuffle_p`). Report p. p < 0.05 = beats luck. The wider you search, the higher the bar — that is
   the point: a search over 190 fields x pairs finds "29 winners kept, 4 losers" in RANDOM labels about 28 % of the time.
4. Holdout: evaluate the frozen rule on the 4 held-out days and report kept/removed win rate, mean, rupees, losers —
   whatever they say. A rule whose kept side on holdout wins less than the book itself is rejected.
5. Report the book's own record, the rule, the three windows, p, and the exact search that found it (so it is
   reproducible). Also report what you tried that FAILED — that is evidence too.

"Every kind of mathematics" is encouraged, under the same standard: ratios (e.g. mv60/rv15, premium/theta_be15,
gamma*mv30), differences (er60-er30, breadth_dir-0.5 in the trade's direction), products, within-day z-scores and
ranks (compute from the book's own earlier trades that day only — nothing from later in the day), time-of-day buckets,
2- and 3-clause AND rules, OR of two rules, "either/or" by regime (text fields via indicators `regime=DIRECTIONAL`),
monotone transforms, interactions with direction (CE vs PE via `t['rr']`), hold-time-independent features only.
Fitted-model fields (hmm_*, hk_*) are excluded: their parameters were fitted on these very days.

## Deliverables (in your folder)

* `report.md`: for each of your books — its record (trades, winners, losers, rupees, by window); the best rule found
  with its full card (`rule_lab.card_markdown`), p, holdout; the rules that looked good on discovery but failed the
  shuffle test or holdout (one line each); your reading in plain words: does any rule honestly remove this book's
  losers? Close with a verdict per book: PROPOSE (passes all of 2-4) or NONE.
* `rules.json`: a list of objects {book, rule: [[feature, op, line], ...], features: {name: "how computed"},
  search: "...", discovery: {...}, holdout: {...}, p, verdict: "PROPOSE"|"REJECTED", why}. Include rejected ones.
* Your final message: a 10-line summary — per book: PROPOSE/NONE, rule, discovery kept win%/losers, holdout kept
  win%/losers, p.

Be exhaustive within the time, be honest about what fails, and never report a holdout you did not run.
