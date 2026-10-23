# Council brief (identical for all 20 members)

You are ONE member of a 20-member review council. You work ALONE: do not read anything under
/mnt/user-data/outputs/council/ except this BRIEF.md, and do not coordinate with anyone. Your
independence is the point.

## The system
ApexOptions, at /mnt/user-data/outputs/ApexOptions (read-only for you; git baseline commit 85b65ed).
A personal PAPER-TRADING system for Nifty weekly options (buy CE/PE only), on ICICI Breeze data.
Processes: feed (apex/feed_breeze.py | feed_sim.py | feed_replay.py) -> shared-memory table
(apex/table.py) -> engine (apex/engine_main.py + apex/engine/*) -> gateway/dashboard
(apex/gateway.py, apex/static/). Supervisor/CLI: run_apex.py. Tests: tests/test_core.py
(run: cd /mnt/user-data/outputs/ApexOptions && python tests/test_core.py — needs numpy only).
Design history and the owner's rules: docs/ (01_MASTER_DESIGN.md, 02_DECISION_LOG.md,
03_OPEN_QUESTIONS.md, 04-06 review/strengthening/audit docs), README.md, CHANGELOG.md.

## Owner's fixed rules — do NOT spend findings on these
- Paper trading only; never sends orders. Real-money readiness is out of scope.
- Slippage, brokerage, charges, fills at LTP: out of scope.
- Sizing (all-in ₹1,00,000 fresh daily) and trade frequency: owner decisions, out of scope.
- The v1 trigger is frozen at four numbers (D-033); new ideas must enter as logged ADVISORS,
  pre-registered VARIANTS/controls, or observers, judged by the learning loop. Nothing changes
  intraday (invariant I-11).

## Your task
1. Read the code relevant to your lens (and anything else you need). Run the tests if useful.
2. TEARDOWN: concrete weaknesses. For each: file:line, what is wrong, a failure scenario,
   severity (critical/high/medium/low), and how you verified it (read, probe script, test).
   Prefer a few verified findings over many speculative ones. Mark anything unverified as such.
3. GOOD THINGS: what is genuinely well done, with file references. Be specific.
4. NEW IDEAS FROM PUBLIC GITHUB REPOSITORIES (2-4): each must be a REAL repository you actually
   opened (WebFetch the GitHub page or README, or `git clone --depth 1` into /tmp/council/<your-id>/).
   Give: owner/repo, URL, licence, the specific file/idea you would borrow, and exactly how it maps
   onto Apex (which module, as an advisor/variant/observer/tool). Never cite a repo you did not
   open; never copy code from a non-permissive licence (describe the concept instead).
   Repos the owner has already reviewed (do not re-propose): anthonyjohn17/ai-trading-agents-stack,
   ygwyg/MAHORAGA, TauricResearch/TradingAgents, himself65/trade-skills, staskh/trading_skills,
   mphinance/alpha-skills, Iman/agent-driven-options-desk-and-skills, schroejahr2/deribit-mcp,
   zer0dte/zer0dte, lenko-d/LLM_Trader.
5. Your top 3 recommendations, ranked, each sized (S/M/L) and marked "before Monday" or "later".

## Output
Write your report to /mnt/user-data/outputs/council/member_<NN>_<lens>.md (≤ 1,500 words,
markdown, sections: Lens · Teardown · Good things · Ideas from GitHub · Top 3).
Do NOT modify anything under /mnt/user-data/outputs/ApexOptions. Then reply with 3 lines:
the report path, your single most important finding, your single best GitHub idea.
