"""The forecast service, the immutable ledger and the matured-label queue (docs/40 section 5 and 6, docs/41 M2).

  Forecaster   loads a frozen artefact (JSON, fitted offline) and turns one feature vector into a consistent set of
               probabilities. No fitting at run time.
  Ledger       append-only records. A forecast is written once with everything it was made from and is never edited.
               Fills, exits and outcomes are LATER records that point at it.
  Maturity     follows every open forecast's own contract second by second and emits an outcome only when the event
               has happened or the horizon has fully passed. Only those outcomes may reach a calibrator.

Lines are queued in memory by issue()/link() and written by flush(). The engine calls flush() every ten seconds
from its forecast feed, INSIDE the step (11 Nov, docs/42 G: the earlier text said "off the decision path", which was
wrong). It is an append of a few lines without fsync; its time is in the engine's "pred" timer."""
import hashlib
import json
import os

import numpy as np

from . import VERSION, features as F, hazard as Hz, models as Mo, targets as T


class Forecaster:
    def __init__(self, artefact=None, path=None):
        if artefact is None and path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                artefact = json.load(f)
        self.art = artefact
        self.why = None
        if artefact is None:
            self.why = "no model artefact"
        elif artefact.get("feature_schema") != F.SCHEMA:
            self.why = f"model was fitted on feature schema {artefact.get('feature_schema')}, the engine has {F.SCHEMA}"
        elif artefact.get("target_spec") != T.SPEC:
            self.why = "model was fitted on a different target specification"
        self.ok = self.why is None
        self.hash = (artefact or {}).get("hash")
        self.horizons = tuple(T.HORIZONS)
        self.kind = (artefact or {}).get("kind") or "logit8"
        if self.ok and self.kind == Hz.KIND:              # 11 Nov: the coherent competing-risk model (hazard.py)
            if len(artefact.get("W") or []) != len(self.horizons) or len(artefact.get("med") or []) != len(F.NAMES):
                self.ok, self.why = False, "hazard artefact has the wrong shape"
        elif self.ok:                                     # all models as three matrices: one pass per forecast
            order = [f"T{h}" for h in self.horizons] + [f"A{h}" for h in self.horizons]
            ms = [artefact["models"][k] for k in order]
            self._med = np.array([m["med"] for m in ms], float)
            self._sd = np.array([m["sd"] for m in ms], float)
            self._w0 = np.array([m["w"][0] for m in ms], float)
            self._w = np.array([m["w"][1:] for m in ms], float)

    def raw(self, X):
        """The eight fitted probabilities for each row of X, columns T(h...) then A(h...). Same as models.predict."""
        X = np.atleast_2d(np.asarray(X, float))
        z = np.clip(np.nan_to_num((X[:, None, :] - self._med[None]) / self._sd[None], nan=0.0, posinf=Mo.CLIP,
                                  neginf=-Mo.CLIP), -Mo.CLIP, Mo.CLIP)
        return 1.0 / (1.0 + np.exp(-np.clip(self._w0[None] + (z * self._w[None]).sum(2), -30.0, 30.0)))

    def score(self, X):
        """THE scoring pipeline (docs/42 finding B): fitted probabilities, then the projection that makes the horizons
        consistent. One function for the artefact's lines, offline evaluation and the engine. Returns (pT, pA), each
        (rows, horizons); the edge is pT[:, -1] - pA[:, -1]. A hazard artefact is coherent by construction."""
        if self.kind == Hz.KIND:
            return Hz.score(self.art, X)
        return project(self.raw(X), len(self.horizons))

    def edges(self, X):
        pT, pA = self.score(X)
        return pT[:, -1] - pA[:, -1]

    def forecast(self, x):
        """x: the feature vector (features.NAMES order). Returns None when there is no usable model, else
        dict(pT={h: p}, pA={h: p}, pN={h: p}, edge=pT300 - pA300). Per horizon the three probabilities sum to 1 and
        pT, pA never fall as the horizon grows. Computed by score(), the one pipeline."""
        if not self.ok or x is None:
            return None
        return self.forecast_many([x])[0]

    def forecast_many(self, X):
        """forecast() for several feature vectors in ONE pass of score(): what the engine calls once a second for
        every contract it scores (11 Nov: one row at a time cost about 1.7 ms a contract)."""
        if not self.ok:
            return [None] * len(X)
        t, a = self.score(np.asarray(X, float))
        hs, hmax, out = self.horizons, self.horizons[-1], []
        for i in range(len(t)):
            pT = {h: float(t[i, j]) for j, h in enumerate(hs)}
            pA = {h: float(a[i, j]) for j, h in enumerate(hs)}
            out.append(dict(pT=pT, pA=pA, pN={h: 1.0 - pT[h] - pA[h] for h in hs}, edge=pT[hmax] - pA[hmax]))
        return out


def project(P, nh):
    """Fitted per-horizon probabilities -> consistent ones: cumulative in the horizon (never falling), and the two
    events never take more than what is left. P: (rows, 2 * nh), columns T then A. Returns (pT, pA), (rows, nh)."""
    P = np.atleast_2d(np.asarray(P, float))
    n = len(P)
    pT, pA = np.zeros((n, nh)), np.zeros((n, nh))
    lt, la = np.zeros(n), np.zeros(n)
    for j in range(nh):
        dt, da = np.maximum(P[:, j] - lt, 0.0), np.maximum(P[:, nh + j] - la, 0.0)
        room, tot = 1.0 - lt - la, dt + da
        k = np.where(tot > room, np.divide(room, tot, out=np.zeros(n), where=tot > 0), 1.0)
        lt, la = lt + dt * k, la + da * k
        pT[:, j], pA[:, j] = lt, la
    return pT, pA


def _fid(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


class Ledger:
    """forecasts_<day>.jsonl and outcomes_<day>.jsonl in `folder`. Append only."""

    def __init__(self, folder, day):
        self.folder, self.day = folder, day
        self.fpath = os.path.join(folder, f"forecasts_{day}.jsonl")
        self.opath = os.path.join(folder, f"outcomes_{day}.jsonl")
        self.seq = 0
        self.ids = set()
        self._qf, self._qo = [], []
        self.written = 0
        self.errors = 0
        self.torn = 0                                     # unreadable lines found at a restart (left in place, skipped)
        self.max_signal = 0                               # the highest signal number already written (docs/42 G)
        self.unresolved = {}                              # forecast id -> role, written before a restart with no outcome
        if os.path.exists(self.fpath):                    # a restart continues the sequence, it never starts a new one
            with open(self.fpath, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        self.torn += 1                    # a torn last line of a killed run
                        continue
                    self.seq = max(self.seq, int(r.get("sequence", 0)))
                    self.ids.add(r.get("forecast_id"))
                    self.unresolved[r.get("forecast_id")] = r.get("role")
                    try:
                        self.max_signal = max(self.max_signal, int((r.get("extra") or {}).get("signal_id") or 0))
                    except (TypeError, ValueError):
                        pass
            if os.path.exists(self.opath):
                with open(self.opath, encoding="utf-8") as f:
                    for line in f:
                        try:
                            r = json.loads(line)
                        except ValueError:
                            self.torn += 1
                            continue
                        if r.get("kind") in ("outcome", "fill"):      # a filled order is not an orphan: its
                            self.unresolved.pop(r.get("forecast_id"), None)   # position carries it on (fc_sig)
        for path in (self.fpath, self.opath):             # 11 Nov (docs/42 G): a torn tail must not swallow the next
            self._end_line(path)                          # record: close it with a newline before anything is appended

    @staticmethod
    def _end_line(path):
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                with open(path, "rb+") as f:
                    f.seek(-1, os.SEEK_END)
                    if f.read(1) != b"\n":
                        f.write(b"\n")
        except OSError:
            pass

    def issue(self, t, instrument, x, fc, decision, reason, role, model_hash, training_cutoff, episode=None,
              ages=None, extra=None):
        """Record one forecast. Returns its id. `fc` is Forecaster.forecast()'s dict or None (an abstention because
        nothing could be forecast is still recorded, with the reason)."""
        self.seq += 1
        body = dict(sequence=self.seq, day=self.day, issued_t=float(t), feature_cutoff_t=float(int(t)),
                    instrument=instrument, role=role, service_version=VERSION, feature_schema=F.SCHEMA,
                    target_spec=T.SPEC, model=model_hash, training_cutoff=training_cutoff,
                    features=[None if not np.isfinite(v) else round(float(v), 6) for v in (x if x is not None else [])],
                    forecast=fc, decision=decision, reason=reason, episode=episode, ages=ages or {})
        if extra:
            body["extra"] = extra
        fid = _fid(body)
        if fid in self.ids:
            raise ValueError("this forecast is already in the ledger: a forecast is written once")
        body["forecast_id"] = fid
        self.ids.add(fid)
        self._qf.append(json.dumps(body, default=str))
        return fid

    def link(self, forecast_id, kind, t, **fields):
        """A later record about a forecast: kind = 'fill' | 'exit' | 'outcome' | 'lapse'. Never edits the forecast."""
        if forecast_id not in self.ids:
            raise KeyError(f"no forecast {forecast_id} in this ledger")
        self._qo.append(json.dumps(dict(forecast_id=forecast_id, kind=kind, t=float(t), **fields), default=str))

    def pending(self):
        return len(self._qf) + len(self._qo)

    def flush(self):
        """Append the queued lines. A failed write keeps them queued for the next call."""
        for path, q in ((self.fpath, self._qf), (self.opath, self._qo)):
            if not q:
                continue
            try:
                os.makedirs(self.folder, exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n".join(q) + "\n")
                self.written += len(q)
                del q[:]
            except OSError:
                self.errors += 1


class Maturity:
    """Open forecasts waiting for their outcome. add() at the forecast; fill() when the entry price is known (the
    ask `delay` seconds later, or the real fill); step() every second with that contract's bid. An outcome is
    returned exactly once: at the first barrier event, or when the longest horizon plus the gap allowance has passed.
    Bounded: at most `cap` open forecasts. When full, the oldest UNFILLED one goes first, else the oldest; add()
    returns the evicted record so the caller writes an explicit censored outcome (11 Nov, docs/42 G: never silent).
    fill_by: an origin not filled within this many seconds of its forecast lapses, as in targets.label (the fill is
    the ask at the next second, or there is none)."""

    def __init__(self, cap=400, barrier=T.BARRIER, horizons=T.HORIZONS, max_gap=T.MAX_GAP_S, fill_by=T.DELAY_S + 1.0):
        self.cap, self.barrier, self.horizons, self.max_gap = cap, barrier, tuple(horizons), max_gap
        self.fill_by = fill_by
        self.open = {}
        self.dropped = 0

    def add(self, fid, key, t, p=None):
        out = None
        if len(self.open) >= self.cap:
            unfilled = [k for k, o in self.open.items() if o["entry"] is None]
            old = min(unfilled or self.open, key=lambda k: self.open[k]["t"])
            o = self.open.pop(old)
            self.dropped += 1
            out = dict(forecast_id=old, status="C", key=o["key"], p=o["p"], entry=o["entry"])
        self.open[fid] = dict(key=key, t=float(t), p=p, entry=None, t_fill=None, last=None, blind=None, ev=None,
                              t_ev=None, peak=None, trough=None, ret={})
        return out

    def fill(self, fid, t, entry):
        o = self.open.get(fid)
        if o is not None and o["entry"] is None and entry and entry > 0 and float(t) - o["t"] < self.fill_by:
            o["entry"], o["t_fill"], o["last"] = float(entry), float(t), float(t)

    def lapse(self, fid):
        return self.open.pop(fid, None)

    def step(self, now, bid_of):
        """bid_of(key) -> the contract's current usable bid, or None. Returns the list of matured outcomes."""
        done = []
        hmax = self.horizons[-1]
        for fid in list(self.open):
            o = self.open[fid]
            if o["entry"] is None:
                if now - o["t"] >= self.fill_by:          # not filled at the next second: no path, as offline
                    done.append(dict(forecast_id=fid, status="L", p=o["p"], key=o["key"]))
                    del self.open[fid]
                continue
            s = now - o["t_fill"]
            if s <= 0:
                continue
            b = bid_of(o["key"])
            if b is not None and b > 0:
                if now - o["last"] > self.max_gap and o["blind"] is None:
                    o["blind"] = o["last"] - o["t_fill"]
                o["last"] = now
                if o["blind"] is None and s <= hmax:
                    r = b / o["entry"] - 1.0
                    o["peak"] = r if o["peak"] is None else max(o["peak"], r)
                    o["trough"] = r if o["trough"] is None else min(o["trough"], r)
                    for h in self.horizons:
                        if s <= h:
                            o["ret"][h] = r
                    if o["ev"] is None and r >= self.barrier:
                        o["ev"], o["t_ev"] = "T", s
                    elif o["ev"] is None and r <= -self.barrier:
                        o["ev"], o["t_ev"] = "A", s
            elif now - o["last"] > self.max_gap and o["blind"] is None:
                o["blind"] = o["last"] - o["t_fill"]
            if o["ev"] is not None or s >= hmax + self.max_gap:
                first = {}
                for h in self.horizons:
                    if o["ev"] is not None and o["t_ev"] <= h:
                        first[h] = o["ev"]
                    elif o["blind"] is not None and o["blind"] < h:
                        first[h] = "U"
                    else:
                        first[h] = "N" if s >= h else None    # None: this horizon had not passed when the event closed it
                done.append(dict(forecast_id=fid, status="ok", key=o["key"], p=o["p"], entry=o["entry"], first=first,
                                 t_hit=o["t_ev"], peak=o["peak"], trough=o["trough"], ret=dict(o["ret"]),
                                 matured_t=float(now)))
                del self.open[fid]
        return done
