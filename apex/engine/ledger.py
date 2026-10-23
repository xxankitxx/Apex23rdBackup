"""
Candidate ledger (D-070) — every opportunity, taken or not, with what happened next.

External review (ChatGPT, "Apex v2"): a learning loop that only sees EXECUTED trades cannot tell
whether a filter removes bad opportunities or good ones. So every CANDIDATE is recorded:

  candidate = the first moment in an episode when the futures impulse reaches the champion's
              m* in the episode's direction (the "push" corner closes), whatever happens next.

At that moment the ledger stores the features (z, synchrony, basket gap, lateness, IV rise,
regime and its features, every advisor's verdict, episode type, time of day, DTE), the champion's
decision and reason, and the contract the champion WOULD buy. It then follows the next 15 min
and labels the outcome, with no reference to whether a trade was taken:

  label     TARGET  futures reach +d* (the champion's 1R, where the trail arms) before -d*
            STOP    futures reach -d* first
            NEITHER neither within 15 min
  t_label   seconds to TARGET / STOP
  opt_ret   the would-be contract's return on premium, % at +1 / +5 / +15 min, and its best and
            worst return inside the 15 min (on the LTP the engine saw at each step)

Written to data/paper/candidates_DAY.jsonl when resolved (or at the close). The learning
report turns the file into hit rates with confidence intervals by regime, by decision and by
rejection reason (engine/diagnostics.py) — the transparent statistical baseline that any
future predictive model must beat out of sample.
"""
import json
import os

from .. import config
from . import paper

FOLLOW_S = 15 * 60
OFFSETS = (60, 300, 900)


def _round(x, n=2):
    return None if x is None else round(float(x), n)


class Ledger:
    def __init__(self, day):
        self.day = day
        self.path = os.path.join(config.PAPER_DIR, f"candidates_{day}.jsonl")
        self.open = {}            # episode id -> record
        self.seen = set()
        self.n = 0

    def update(self, ctx, champ_book, champ_reason, regime_view):
        now = ctx["now_s"]
        ep = ctx.get("episode")
        p = champ_book.p
        if ep and ep["id"] not in self.seen and not p.get("spike") and not p.get("random") and not p.get("momentum") \
                and not p.get("spot_dc") and not p.get("fade_switch"):   # D-124: these books do not trade the domino cross
            dom = ctx["domino"]
            d = ep["dir"]
            z = dom["z"] * d
            if dom["dir"] == d and z >= p["m_star"]:
                self.seen.add(ep["id"])
                self.open[ep["id"]] = self._new(ctx, ep, champ_book, champ_reason, regime_view)
        for eid, r in list(self.open.items()):
            self._follow(r, ctx, champ_book)
            if now - r["t0"] >= FOLLOW_S:
                self._write(self.open.pop(eid))

    def _new(self, ctx, ep, book, reason, rv):
        p, dom, d = book.p, ctx["domino"], ep["dir"]
        opt, why = paper.choose_contract(ctx, d)
        sig = dom.get("sigma15") or 0.0
        moved = abs(ctx["fut"] - ep["fut0"])
        self.n += 1
        return {
            "day": self.day, "id": ep["id"], "t0": ctx["now_s"], "time": ctx["now_dt"].strftime("%H:%M:%S"),
            "dir": d, "fut0": ctx["fut"], "D": p["d_star"], "book": book.name,
            "z": _round(dom["z"] * d), "S": _round(dom["S_up"] if d > 0 else dom["S_dn"]),
            "gap": _round(dom.get("gap", 0.0) * d), "late": _round(moved / (p["L_star"] * sig) if sig else None),
            "iv_rise": _round(ctx.get("iv_rise_since_onset")), "ep_type": ep.get("type"), "ep_gap": bool(ep.get("gap")),
            "regime": rv.get("state"), "regime_dir": rv.get("dir"), "er5": rv.get("er5"), "breadth": rv.get("breadth"),
            "ext_pct": rv.get("ext_pct"), "rv_pct": rv.get("rv_pct"),
            "advisors": {k: bool(v.get("veto")) for k, v in (ctx.get("advisors") or {}).items()},
            "decision_at_cross": reason,
            "opt": ({"key": opt["key"], "strike": opt["strike"], "rr": opt["rr"], "px0": opt["ltp"],
                     "delta": opt.get("delta")} if opt else None),
            # D-101: exchange-stamp age of px0 (receive age can be refreshed by depth packets)
            "opt_age0": paper._trade_age(ctx["now_s"], opt) if opt else None,
            "opt_why": why or None,
            "fired": False, "label": None, "t_label": None,
            "opt_ret": {}, "opt_best": None, "opt_worst": None,
        }

    def _follow(self, r, ctx, book):
        el = ctx["now_s"] - r["t0"]
        if (ctx.get("blackout") or {}).get("on"):
            r["follow_gap"] = True                 # labelled on data that crossed a gap: filter in analysis
            return
        if not r["fired"]:
            pos = book.pos
            if (pos and pos.get("episode") == r["id"]) or any(t.get("episode") == r["id"] for t in book.trades[-3:]):
                r["fired"] = True
                r["fired_after_s"] = round(el, 1)
        if r["label"] is None:
            fav = (ctx["fut"] - r["fut0"]) * r["dir"]
            if fav >= r["D"]:
                r["label"], r["t_label"] = "TARGET", round(el, 1)
            elif fav <= -r["D"]:
                r["label"], r["t_label"] = "STOP", round(el, 1)
        o = r["opt"]
        if o and o["px0"]:
            q = ctx["by_key"].get(o["key"])
            xa = paper._trade_age(ctx["now_s"], q) if q else None
            if xa is not None and xa > config.QUOTE_DEFECT_AGE_S:
                r["opt_defect"] = True             # D-101: the quote's exchange stamp is stale
            if q and q["ltp"] and q.get("age", 0) < 15 and not r.get("opt_defect"):
                ret = 100.0 * (q["ltp"] - o["px0"]) / o["px0"]
                r["opt_best"] = ret if r["opt_best"] is None else max(r["opt_best"], ret)
                r["opt_worst"] = ret if r["opt_worst"] is None else min(r["opt_worst"], ret)
                for off in OFFSETS:
                    if el >= off and str(off) not in r["opt_ret"]:
                        r["opt_ret"][str(off)] = round(ret, 2)

    def _write(self, r):
        if r["label"] is None:
            r["label"] = "NEITHER"
        for k in ("opt_best", "opt_worst"):
            r[k] = _round(r[k])
        r.pop("t0", None)
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, default=str) + "\n")
        except OSError:
            pass

    def close(self):
        """At the close: write what is still being followed (labelled with what is known)."""
        for eid in list(self.open):
            r = self.open.pop(eid)
            r["truncated"] = True
            self._write(r)

    def view(self):
        return {"followed": len(self.open), "today": self.n}
