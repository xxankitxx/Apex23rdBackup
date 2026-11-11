"""10 Nov 2026 (docs/40 section 7, docs/41 section 6): the prediction-driven shadow signals. VERSION 1.

One shared forecaster (apex/predict), read every second for four contracts of the near week: the at-the-money call
and put and the first in-the-money call and put. Everything it says goes to the immutable forecast ledger first.

  p02_clock      independent entry: the forecast edge (P target first - P adverse first, 300 s) of one of the four
                 contracts is at or above the artefact's frozen entry line. Exit: +5 % / -5 % of the entry premium,
                 300 s, or the edge of the held contract falling to the artefact's exit line.
  p02_top1       the same book with the entry line at the artefact's 99th percentile instead of the 95th. Added
                 AFTER the walk-forward runs were seen (the top 1 % was positive in all three, the top 5 % was not
                 inside the engine's entry window): it is a post-hoc variant and is labelled so everywhere.
  p02_ctl_mom    its control: the same sampler, the same exit, entry on 30-s futures momentum at its own frozen line.
  p05_adaptive   the same entry as p02_clock but on the edge after the intraday calibrator, which learns ONLY from
                 forecasts whose 300 s have fully passed. p02_clock is its frozen twin.
  admit()/hold() P01 forecast_select and P03/P04 forecast_runner / forecast_exit read the same forecaster for a
                 contract another book wants to enter or is holding. They are filter and exit twins, not new sources.

Shadow only: never a pool member, never the champion. No fitting here: the artefact is a file fitted offline; if it is
missing, was fitted on another feature schema, or the inputs are stale, every signal is silent and says why."""
import os

import numpy as np

from ..predict import features as F, ledger as L, models as Mo, ranges as Rg, targets as T

VERSION = 2                  # 11 Nov (docs/42): the executable contract is scored and bought; held contracts are covered
NAMES = ("p02_clock", "p02_top1", "p02_ctl_mom", "p05_adaptive")
SAMPLE_S = 15                # every 15 s the four forecasts are written to the ledger, traded or not
REARM_S = 60                 # a signal name speaks again only after this long and after its score fell below the line
TP_PREM = SL_PREM = T.BARRIER
HOLD_S = max(T.HORIZONS)


class Pred:
    def __init__(self, artefact_path=None, ledger_dir=None, day=None, artefact=None, ranges_path=None, ranges=None):
        self.fc = L.Forecaster(artefact, artefact_path)
        self.rg = Rg.Ranger(ranges, ranges_path)      # premium-return ranges: a record only, nothing decides on them
        self.fs = F.Features()
        self.led = L.Ledger(ledger_dir, day) if ledger_dir and day else None
        self.mat = L.Maturity()
        self.cal_T, self.cal_A = Mo.Calibrator(prior=200.0), Mo.Calibrator(prior=200.0)
        art = self.fc.art or {}
        q = art.get("edge_quantiles") or {}
        self.line_in = q.get("0.95")                 # frozen in the artefact, from the training origins only
        self.line_top = q.get("0.99")
        self.line_out = q.get("0.5")
        self.mom_line = art.get("mom30_q95")
        self.sig, self.fired, self.why = {}, {}, {n: "not started" for n in NAMES}
        self.n_sig = 0
        self.expiry = None                           # the near week's expiry of the contracts scored (full identity)
        self.tags = {}                               # (strike, rr) -> "exe" | "held", as the engine asked this second
        self._panel = (None, None)                   # (second, dict): the dashboard view, built once a second
        if self.led is not None:                     # 11 Nov (docs/42 G): a restart of the same day
            self.n_sig = self.led.max_signal         # signal numbers never repeat: a book keys its fired set on them
            for fid in list(self.led.unresolved):    # forecasts the earlier process never resolved: say so, once
                self.led.link(fid, "outcome", 0.0, status="restart", first=None, t_hit=None, peak=None, trough=None)
            self.led.unresolved = {}
        self.armed = {n: True for n in NAMES}
        self.last_t = {n: -1e18 for n in NAMES}
        self.now = None
        self.cur = {}                                # (strike, rr) -> dict(x, f, edge, edge_cal) of this second
        self.keys = {}                               # ledger id -> (strike, rr)
        self.stats = dict(forecasts=0, matured=0, silent_s=0)
        self.exe = None                              # 11 Nov (docs/42 A): the contracts the engine would buy now, or None
        self.miss = {}                               # (strike, rr) -> why a wanted contract has no forecast this second
        cut = art.get("training_cutoff")
        self.in_sample = bool(day and cut and str(day) <= str(cut))   # docs/42 F: the model has seen this day

    # -- feed -------------------------------------------------------------------------------------------------------
    def update(self, now_s, fbid, fask, f_age, cash, cash_age, sf_bid, sf_ask, sf_age, w, K, obid, oask, oage, dte,
               expd, tod_s, ok=True, f_ltp=None, f_vol=None, bq=None, aq=None, d_age=None, extra=None, expiry=None):
        """Once per second. Arrays as apex.predict.features.Features.update. ok=False: a feed blackout (no forecast).
        extra (11 Nov, docs/42 A and C): [(strike, rr, tag)] of contracts that must be scored besides the four near
        the money. tag "exe" = the contract the engine would buy now on that side; "held" = a contract some book
        holds. When extra is given, the signals choose only among the "exe" contracts, so the contract scored is the
        contract bought. extra=None keeps the old behaviour (the four near contracts), for callers without an engine."""
        self.now = float(now_s)
        self.cur, self.miss = {}, {}
        self.expiry = expiry
        self.exe = None if extra is None else {(float(s), int(r)) for s, r, tag in extra if tag == "exe"}
        K = np.asarray(K, float)
        want = [] if extra is None else [(float(s), int(r), tag) for s, r, tag in extra]
        self.tags = {}
        for s, r, tag in want:                       # "exe" wins over "held" for the same contract
            if tag == "exe" or (s, r) not in self.tags:
                self.tags[(s, r)] = tag
        if not ok or not self.fc.ok:
            for s, r, _ in want:
                self.miss[(s, r)] = "the feed is not healthy" if not ok else str(self.fc.why)
        if not ok:
            self._silent("the feed is not healthy")
            return
        self.fs.update(now_s, fbid, fask, f_age, cash, cash_age, sf_bid, sf_ask, sf_age, w, K, obid, oask, oage, dte,
                       expd, tod_s, f_ltp=f_ltp, f_vol=f_vol, bq=bq, aq=aq, d_age=d_age)
        self._mature(K, np.asarray(obid, float), np.asarray(oask, float), np.asarray(oage, float))
        if not self.fc.ok:
            self._silent(self.fc.why)
            return
        if self.fs.market() is None:
            self._silent("warming up or the index future's quote is stale")
            for s, r, _ in want:
                self.miss[(s, r)] = "warming up or the index future's quote is stale"
            return
        k = self.fs.atm()
        if k is None:
            self._silent("no at-the-money strike yet")
            for s, r, _ in want:
                self.miss[(s, r)] = "no at-the-money strike yet"
            return
        sample = int(now_s) % SAMPLE_S == 0
        # 11 Nov (docs/46 finding 2): at the edge of the recorded chain only the neighbours that exist are taken;
        # a missing neighbour must not silence the contracts the engine could buy or holds
        cand = [(kk, rr, "near") for kk, rr in ((k, 0), (k, 1), (k - 1, 0), (k + 1, 1)) if 0 <= kk < len(K)]
        wanted = {(s, r) for s, r, _ in want}
        if want:
            idx = {float(s): j for j, s in enumerate(K)}
            near = {(c[0], c[1]) for c in cand}
            for s, r, tag in want:
                j = idx.get(s)
                if j is None:
                    self.miss[(s, r)] = "the strike is outside the forecaster's strike grid"
                elif (j, r) not in near:
                    near.add((j, r))
                    cand.append((j, r, tag))
        got = []
        for kk, rr, tag in cand:
            x = self.fs.contract(kk, rr)
            if x is None:
                if (float(K[kk]), rr) in wanted:
                    self.miss[(float(K[kk]), rr)] = "no fresh two-sided quote for this contract"
                continue
            got.append((kk, rr, tag, x))
        fcs = self.fc.forecast_many([g[3] for g in got]) if got else []      # every contract in one pass
        for (kk, rr, tag, x), f in zip(got, fcs):
            hm = T.HORIZONS[-1]
            ec = self.cal_T.one(f["pT"][hm]) - self.cal_A.one(f["pA"][hm])
            c = dict(x=x, f=f, edge=f["edge"], edge_cal=ec, k=kk, rr=rr, ask=float(np.asarray(oask, float)[kk, rr]))
            self.cur[(float(K[kk]), rr)] = c
            if sample and self.led is not None:
                fid = self.led.issue(now_s, f"{K[kk]:.0f}|{'CE' if rr == 0 else 'PE'}", x, self.rec(x, f), "sample", "periodic sample",
                                     "sample", self.fc.hash, (self.fc.art or {}).get("training_cutoff"),
                                     extra=(dict(tag="exe") if self.exe and (float(K[kk]), rr) in self.exe
                                            else None if tag == "near" else dict(tag=tag)))
                self._evicted(self.mat.add(fid, (float(K[kk]), rr), now_s, p=(f["pT"][hm], f["pA"][hm])))
                self.keys[fid] = (float(K[kk]), rr)
                self.stats["forecasts"] += 1
        self._signals()

    def rec(self, x, f):
        """What the ledger keeps of one forecast: the probabilities and, when a range artefact is loaded, the 10/50/90 %
        range of the premium return at 60 s and 300 s. Computed only when a record is written, not every second."""
        d = _plain(f)
        r = self.rg.ranges(x)
        if r is not None:
            d["range"] = {str(h): q for h, q in r.items()}
            d["range_model"] = self.rg.hash
        return d

    def _evicted(self, out):
        """docs/42 G: an origin pushed out of the full queue gets an explicit censored outcome. It teaches nothing."""
        if out is None:
            return
        self.keys.pop(out["forecast_id"], None)
        self.count("censored_capacity")
        if self.led is not None:
            self.led.link(out["forecast_id"], "outcome", self.now, status="censored_capacity", first=None, t_hit=None,
                          peak=None, trough=None)

    def _silent(self, why):
        self.stats["silent_s"] += 1
        self.sig = {}                                 # 11 Nov (docs/46 finding 1): no current forecast, no live signal
        for n in NAMES:
            self.why[n] = why

    def _mature(self, K, obid, oask, oage):
        """Fill waiting forecasts at the ask of a quote received after them, then collect matured outcomes."""
        idx = {float(s): i for i, s in enumerate(K)}

        def quote(key):
            i = idx.get(key[0])
            if i is None:
                return None, None
            b, a, g = obid[i, key[1]], oask[i, key[1]], oage[i, key[1]]
            return (b, a) if b > 0 and a > b and g <= F.Q_FRESH_S else (None, None)
        for fid, o in list(self.mat.open.items()):
            if o["entry"] is None and T.DELAY_S <= self.now - o["t"] < self.mat.fill_by:   # the next second only
                b, a = quote(o["key"])
                i = idx.get(o["key"][0])
                if a is not None and oage[i, o["key"][1]] <= self.now - o["t"]:
                    self.mat.fill(fid, self.now, a)
        for out in self.mat.step(self.now, lambda key: quote(key)[0]):
            self.keys.pop(out["forecast_id"], None)
            if out["status"] == "ok":
                first = out["first"][T.HORIZONS[-1]]
                if first in ("T", "A", "N") and out["p"] is not None:      # matured and observable: may teach
                    self.cal_T.update(out["p"][0], 1.0 if first == "T" else 0.0)
                    self.cal_A.update(out["p"][1], 1.0 if first == "A" else 0.0)
                    self.stats["matured"] += 1
            if self.led is not None:
                self.led.link(out["forecast_id"], "outcome", self.now, status=out["status"], first=out.get("first"),
                              t_hit=out.get("t_hit"), peak=out.get("peak"), trough=out.get("trough"))

    # -- signals ----------------------------------------------------------------------------------------------------
    def _signals(self):
        if not self.cur:
            self._silent("no contract with a fresh two-sided quote")
            return
        mom = self.fs.market()["mom30"]
        pool = list(self.cur.items()) if self.exe is None else [kv for kv in self.cur.items() if kv[0] in self.exe]
        if not pool:                                  # docs/42 A: never score one contract and buy another
            self._silent("no forecast for a contract the engine could buy now"
                         + (": " + "; ".join(sorted(set(self.miss.values()))) if self.miss else ""))
            return
        best = max(pool, key=lambda kv: kv[1]["edge"])
        best_c = max(pool, key=lambda kv: kv[1]["edge_cal"])
        atm = pool if self.exe is not None else [(k, c) for k, c in self.cur.items() if c["k"] == self.fs.atm()]
        plan = (("p02_clock", best[1]["edge"], self.line_in, best, "forecast edge"),
                ("p02_top1", best[1]["edge"], self.line_top, best, "forecast edge"),
                ("p05_adaptive", best_c[1]["edge_cal"], self.line_in, best_c, "calibrated forecast edge"))
        for name, score, line, (key, c), what in plan:
            self._one(name, score, line, key, c, f"{what} {score:+.3f} at or above the entry line {line:+.3f}"
                      if line is not None else None, what)
        if self.mom_line is not None and np.isfinite(mom) and atm:
            d = 1 if mom > 0 else -1
            pick = [kc for kc in atm if kc[1]["rr"] == (0 if d > 0 else 1)]
            if pick:
                self._one("p02_ctl_mom", abs(mom), self.mom_line, pick[0][0], pick[0][1],
                          f"30-s futures move {mom:+.1f} at or beyond {self.mom_line:.1f} points", "30-s momentum")
        else:
            self.why["p02_ctl_mom"] = "no momentum line in the artefact" if self.mom_line is None else "no quote on the momentum side"

    def _one(self, name, score, line, key, c, why, what):
        if line is None:
            self.why[name] = "the artefact carries no entry line"
            return
        if score < line:
            self.armed[name] = True
            self.why[name] = f"{what} {score:+.3f} below the line {line:+.3f}"
            return
        if not self.armed[name] or self.now - self.last_t[name] < REARM_S:
            self.why[name] = "already signalled; waiting to re-arm"
            return
        self.armed[name], self.last_t[name] = False, self.now
        self.n_sig += 1
        d = 1 if c["rr"] == 0 else -1
        s = dict(id=self.n_sig, t=self.now, dir=d, ep="P-" + name.upper().replace("_", "-"), why=why, tp=1e9, sl=1e9,
                 hold=HOLD_S, tp_prem=TP_PREM, sl_prem=SL_PREM, strike=key[0], rr=c["rr"], edge=float(c["edge"]),
                 edge_cal=float(c["edge_cal"]), stop_px=None, expiry=self.expiry,
                 key=(f"NIFTY|OPT|{self.expiry}|{int(key[0])}|{'CE' if c['rr'] == 0 else 'PE'}" if self.expiry else None))
        self.sig[name] = s
        self.fired[(name, s["id"])] = s
        self.why[name] = why
        if self.led is not None:
            s["forecast_id"] = self.led.issue(self.now, f"{key[0]:.0f}|{'CE' if c['rr'] == 0 else 'PE'}", c["x"], self.rec(c["x"], c["f"]),
                                              "enter", why, name, self.fc.hash, (self.fc.art or {}).get("training_cutoff"),
                                              extra=dict(signal_id=s["id"], edge_cal=s["edge_cal"], key=s["key"],
                                                         exe=bool(self.exe and key in self.exe)))

    # -- what the books ask -----------------------------------------------------------------------------------------
    def ready(self, name=None):
        return bool(self.fc.ok and self.fs.ready() and self.cur)

    def edge_of(self, strike, rr, calibrated=False):
        """The forecast edge of a contract this second, or None when it is not one of the four, or nothing is ready."""
        c = self.cur.get((float(strike), int(rr)))
        return None if c is None else (c["edge_cal"] if calibrated else c["edge"])

    def why_none(self, strike, rr):
        """docs/42 C: why a contract has no forecast this second. Missing is not a low score and not a veto."""
        if (float(strike), int(rr)) in self.cur:
            return None
        return self.miss.get((float(strike), int(rr))) or "not among the contracts scored this second"

    def count(self, key):
        self.stats[key] = self.stats.get(key, 0) + 1

    def admit(self, strike, rr):
        """P01 forecast_select: (admit?, edge, reason). No forecast = no opinion = admit (an absent vote is not a veto)."""
        e = self.edge_of(strike, rr)
        if e is None or self.line_out is None:
            return True, e, "no forecast for this contract: not vetoed"
        return (e >= self.line_out), e, f"forecast edge {e:+.3f} against the admission line {self.line_out:+.3f}"

    def void(self, name, gx, d):
        """Thesis exit for a held forecast position (P02/P05) and the P04 rule for any held contract: the edge of the
        held contract has fallen to the artefact's exit line. Silent when there is no forecast."""
        if name == "p02_ctl_mom" or not gx or gx.get("strike") is None or self.line_out is None:
            return None
        e = self.edge_of(gx["strike"], gx["rr"], calibrated=(name == "p05_adaptive"))
        if e is not None and e < self.line_out:
            return f"FORECAST GONE (edge {e:+.3f} below {self.line_out:+.3f})"
        return None

    def flush(self):
        if self.led is not None:
            self.led.flush()

    def panel(self):
        """11 Nov: the dashboard's forecast panel. DISPLAY ONLY: nothing reads it for a decision. One row for each
        contract the engine would buy now (call and put) and each held contract: the chance that its premium gains
        5 % before it loses 5 % within 5 minutes, the reverse, neither, and the 10 to 90 % range of its premium
        return at 60 s and 300 s. Built once a second."""
        if self._panel[0] == self.now and self.now is not None:
            return self._panel[1]
        hs = T.HORIZONS
        hm, h1 = hs[-1], (60 if 60 in hs else hs[0])
        rows = []
        for key, c in self.cur.items():
            tag = self.tags.get(key)
            if tag is None and self.exe is not None:
                continue
            f = c["f"]
            r = self.rg.ranges(c["x"]) or {}
            rows.append(dict(strike=float(key[0]), side="CE" if key[1] == 0 else "PE", tag=tag or "near",
                             ask=round(float(c["ask"]), 2) if np.isfinite(c["ask"]) else None,
                             up=round(float(f["pT"][hm]), 4), down=round(float(f["pA"][hm]), 4),
                             flat=round(max(0.0, 1.0 - float(f["pT"][hm]) - float(f["pA"][hm])), 4),
                             up60=round(float(f["pT"][h1]), 4), down60=round(float(f["pA"][h1]), 4),
                             edge=round(float(c["edge"]), 4),
                             above_line=bool(self.line_in is not None and c["edge"] >= self.line_in),
                             rng60=r.get(60), rng300=r.get(300)))
        rows.sort(key=lambda x: (0 if x["tag"] == "exe" else 1, x["side"], x["strike"]))
        missing = [dict(strike=k[0], side="CE" if k[1] == 0 else "PE", tag=self.tags.get(k), why=v)
                   for k, v in sorted(self.miss.items())][:8]
        last = None
        if self.fired:
            (nm, _), s = max(self.fired.items(), key=lambda kv: kv[1]["t"])
            last = dict(book=nm, t=float(s["t"]), strike=float(s["strike"]), side="CE" if s["rr"] == 0 else "PE", why=str(s["why"]))
        out = dict(ok=bool(self.fc.ok), ready=bool(self.ready()), why=None if rows else (self.why.get("p02_clock") or self.fc.why),
                   model=self.fc.hash, trained_through=(self.fc.art or {}).get("training_cutoff"), in_sample=self.in_sample,
                   horizon_s=int(hm), short_s=int(h1), barrier_pct=round(100 * T.BARRIER, 1), line_in=self.line_in,
                   line_out=self.line_out, expiry=self.expiry, rows=rows, missing=missing, signals=int(self.n_sig), last=last,
                   ranges=bool(self.rg.ok), t=self.now,
                   range_model=self.rg.hash if self.rg.ok else None,
                   range_trained_through=(self.rg.art or {}).get("training_cutoff") if self.rg.ok else None,
                   evaluation=(self.fc.art or {}).get("evaluation"),      # shown only when the artefact carries one
                   books={n: str(self.why.get(n)) for n in NAMES})        # each forecast book's own state, in its words
        self._panel = (self.now, out)
        return out

    def view(self):
        return dict(version=VERSION, ok=self.fc.ok, why=self.fc.why, model=self.fc.hash, ready=self.ready(),
                    in_sample=self.in_sample, scored=len(self.cur), missing=len(self.miss),
                    line_in=self.line_in, line_out=self.line_out, open=len(self.mat.open), dropped=self.mat.dropped,
                    calibrator_updates=self.cal_T.updates, stats=dict(self.stats), signals=self.n_sig,
                    now={f"{k[0]:.0f}{'CE' if k[1] == 0 else 'PE'}": round(c["edge"], 4) for k, c in self.cur.items()},
                    ledger_pending=self.led.pending() if self.led else None,
                    ledger_errors=self.led.errors if self.led else None)


def _held(ctx, pos):
    """(Pred, edge of the held contract) or (None, None) when there is no forecast for it this second."""
    p = (ctx or {}).get("pred")
    if p is None or pos.get("expiry") != ctx.get("w0") or pos.get("strike") is None:
        return None, None
    return p, p.edge_of(pos["strike"], 0 if pos.get("rr") == "CE" else 1)


def held_exit(ctx, pos, peak_bid):
    """P04 forecast_exit for a held position of another book: a reason, or None. Speaks only after an observed gain
    of at least the barrier (5 % of the entry premium on the bid) and only when a forecast exists and its edge is
    below the artefact's exit line. Never a stop: a position that never gained is left to its own rules."""
    p, e = _held(ctx, pos)
    if p is not None:                                 # docs/42: asked, could answer, eligible, spoke
        p.count("exit_asked")
        if e is None:
            p.count("exit_no_forecast")
    if p is None or e is None or p.line_out is None or not pos.get("entry") or not peak_bid:
        return None
    gain = peak_bid / pos["entry"] - 1.0
    if gain >= T.BARRIER:
        p.count("exit_eligible")
    if gain >= T.BARRIER and e < p.line_out:
        p.count("exit_spoke")
        return f"FORECAST EXIT (edge {e:+.3f} below {p.line_out:+.3f} after a gain of {100 * gain:.1f} %)"
    return None


def held_keep(ctx, pos, bid):
    """P03 forecast_runner: True when the strategy's own SELL should wait: the position is in profit on the bid and
    the forecast edge of the held contract is at or above the entry line. No forecast, or a loss, never holds."""
    p, e = _held(ctx, pos)
    if p is not None:                                 # docs/42: how often the runner twin was asked, could answer, held
        p.count("keep_asked")
        if e is None:
            p.count("keep_no_forecast")
        elif bid and pos.get("entry") and bid <= pos["entry"]:
            p.count("keep_not_in_profit")
        elif p.line_in is not None and e < p.line_in:
            p.count("keep_edge_below_line")
    if p is None or e is None or p.line_in is None or not bid or not pos.get("entry"):
        return False
    keep = bool(bid > pos["entry"] and e >= p.line_in)
    if keep:
        p.count("keep_held")
    return keep


def _plain(f):
    return dict(pT={str(h): round(v, 5) for h, v in f["pT"].items()}, pA={str(h): round(v, 5) for h, v in f["pA"].items()},
                edge=round(f["edge"], 5))
