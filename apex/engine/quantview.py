"""Live quant evidence for the dashboard (5 Nov 2026, from reviews/). Display only: nothing here feeds a decision.

Updated once per second from the engine's own state (forward, ATM strike, option quotes, IVs), constant work per
update (~1-2 ms in all), so it never slows the 100-ms tick:

  * forward state   Kalman velocity (pts/s) and its t-stat, jump-robust bipower noise, Huang-Tauchen jump z,
                    CUSUM drift-change alarm
  * order flow      Hawkes buy / sell excitation on the ATM call and put (aggressive prints, shared kernel)
  * regime          hidden-Markov posterior on 60-s bars, current state, how long it has run, expected minutes left
  * premium outcome for buying the ATM call and the ATM put at the ask now: P(+10 % before -10 %) within 1, 3, 5,
                    10, 15 min, and the 30-s change of the 5-min figure (opportunity decay)
  * Greeks          third order (vanna, vomma, charm, speed, color, zomma) for the held option, else the ATM pair
  * smile           raw-SVI fit every 60 s and each ATM-band strike's residual (vol pts; + rich, - cheap)

Model parameters (Hawkes kernel, HMM) come from apex/quant/params.json, fitted offline on the taped days; without
the file the Hawkes kernel uses a 10-s default and the regime block stays empty.
"""
import json
import math
import os
from collections import deque

import numpy as np

from .. import config
from ..quant import greeks_hi, hawkes, micro, passage, regime, svi

PARAMS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quant", "params.json")
YEAR_S = 365.0 * 86400.0


def _f(x, nd=3):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if math.isfinite(x) else None


class QuantView:
    def __init__(self):
        p = {}
        try:
            with open(PARAMS, encoding="utf-8") as fh:
                p = json.load(fh)
        except (OSError, ValueError):
            p = {}
        mu, a, b = p.get("hawkes", [0.05, 0.05, 0.1])
        self.hk = (float(a), float(b))
        self.hmm = regime.GaussianHMM.from_dict(p["hmm"]) if p.get("hmm") else None
        self.reset()

    def reset(self):
        self.kf = micro.KalmanVelocity(q_v=1e-4, q_x=0.05, r=1.0)
        self.rv = micro.RollingVar(300)
        self.cu = micro.Cusum(k=0.5, h=5.0)
        self.prev_f, self.prev_t = None, None
        self.flow = {}                      # side -> dict(id, ttq, mid, hb, hs, t)
        self.bar = deque(maxlen=61)
        self.bar_n = 0
        self.post = None
        self.state, self.run = -1, 0
        if self.hmm:
            self.hmm.reset()
        self.po_hist = {"CE": deque(maxlen=31), "PE": deque(maxlen=31)}
        self.svi_p, self.svi_t = None, -1e9
        self.v = {}

    # ------------------------------------------------------------------ inputs
    def _flow(self, side, i, snap, now_s):
        """Hawkes excitation of aggressive buys / sells on one contract (prints since the last second)."""
        a, b = self.hk
        st = self.flow.get(side)
        ttq, ltp = float(snap["ttq"][i]), float(snap["ltp"][i])
        bid, ask = float(snap["bid"][i]), float(snap["ask"][i])
        mid = (bid + ask) / 2 if bid > 0 and ask >= bid else ltp
        if st is None or st["id"] != i:
            self.flow[side] = {"id": i, "ttq": ttq, "mid": mid, "hb": 0.0, "hs": 0.0, "t": now_s}
            return
        dec = math.exp(-b * max(now_s - st["t"], 0.0))
        st["hb"] *= dec
        st["hs"] *= dec
        if ttq > st["ttq"] and ltp > 0 and st["mid"] > 0:
            if ltp >= st["mid"]:
                st["hb"] += a
            else:
                st["hs"] += a
        st.update(ttq=ttq, mid=mid, t=now_s)

    def step(self, eng, snap):
        now_s = eng.now_s
        F = getattr(eng, "fwd", None)
        if F is None or not math.isfinite(F):
            return
        # forward state
        self.kf.add(F)
        if self.prev_f is not None and F != self.prev_f:
            d, gap = F - self.prev_f, max(now_s - self.prev_t, 1e-3)
            self.rv.add(d, gap)
            s = self.rv.sigma()
            if math.isfinite(s) and s > 0 and self.rv.count >= 60:
                self.cu.add(d / (s * math.sqrt(gap)))
        if self.prev_f is None or F != self.prev_f:
            self.prev_f, self.prev_t = F, now_s
        # regime bars
        self.bar.append(F)
        self.bar_n += 1
        if self.hmm and self.bar_n % 60 == 0 and len(self.bar) == 61 and max(self.bar) > min(self.bar):
            seg = np.array(self.bar)
            x = (seg[-1] - seg[0], math.log1p(seg.max() - seg.min()))
            self.post = self.hmm.filter(x)
            st = int(np.argmax(self.post))
            self.run = self.run + 1 if st == self.state else 1
            self.state = st
        # contracts: the ATM pair of the nearest weekly, the held option if any
        atm, w0 = getattr(eng, "atm", None), getattr(eng, "w0", None)
        if atm is None or not w0:
            return
        ids = {rr: eng.key.get(f"NIFTY|OPT|{w0}|{int(atm)}|{rr}") for rr in ("CE", "PE")}
        T = greeks_hi.real_years(w0, eng.now_dt)
        sig_f = self.rv.sigma() if self.rv.count >= 60 else float("nan")
        out = {"fwd": _f(F, 1), "kv": _f(self.kf.v, 3), "kvt": _f(self.kf.t_stat(), 2), "sig": _f(sig_f, 3),
               "jz": _f(self.rv.jump()[1], 2), "cusum": self.cu.state(), "atm": int(atm), "po": {}, "flow": {},
               "greeks": {}}
        for rr, i in ids.items():
            if i is None:
                continue
            self._flow(rr, i, snap, now_s)
            st = self.flow.get(rr)
            if st:
                out["flow"][rr] = {"buy": _f(st["hb"], 3), "sell": _f(st["hs"], 3),
                                   "ratio": _f((st["hb"] + 1e-3) / (st["hs"] + 1e-3), 2)}
            g = eng.greek.get(i) or {}
            iv = g.get("iv")
            ask = float(snap["ask"][i])
            if iv and ask > 0 and math.isfinite(sig_f) and sig_f > 0:
                o = passage.premium_outcome(F, float(atm), T, iv / 100.0, rr == "CE", ask, 0.10, 0.10,
                                            self.kf.v, sig_f)
                if o is not None:
                    h5 = float(o["up_by"][2])
                    hist = self.po_hist[rr]
                    hist.append(h5)
                    out["po"][rr] = {"up_by": [_f(x, 3) for x in o["up_by"]], "dn15": _f(o["dn_by"][-1], 3),
                                     "ever": _f(o["up_ever"], 3), "a": _f(o["a"], 1), "b": _f(o["b"], 1),
                                     "decay30": _f(hist[0] - h5, 3) if len(hist) == hist.maxlen else None,
                                     "mu_eff": _f(o["mu_eff"], 3)}
        # third-order Greeks: the held option if the champion holds one, else the ATM pair
        held = None
        champ = eng.books.get(eng.champion) if getattr(eng, "books", None) else None
        if champ and champ.pos:
            held = (champ.pos.get("id"), champ.pos.get("strike"), champ.pos.get("rr"))
        pairs = [held] if held and held[0] is not None else [(ids.get(rr), atm, rr) for rr in ("CE", "PE")]
        for i, K, rr in pairs:
            if i is None or K is None:
                continue
            iv = (eng.greek.get(i) or {}).get("iv")
            if not iv:
                continue
            g = greeks_hi.all_greeks(F, float(K), T, iv / 100.0, rr == "CE")
            out["greeks"][f"{int(K)}{rr}"] = {
                "delta": _f(g["delta"], 3), "gamma": _f(g["gamma"], 5),
                "theta_min": _f(g["theta"] / YEAR_S * 60, 3),          # premium per calendar minute
                "vega": _f(g["vega"] / 100, 3),                        # per vol point
                "vanna": _f(g["vanna"] / 100, 5),                      # delta change per vol point
                "vomma": _f(g["vomma"] / 1e4, 4),                      # vega change per vol point, per vol point
                "charm_min": _f(g["charm"] / YEAR_S * 60, 6),          # delta change per minute
                "speed": _f(g["speed"], 8), "color_min": _f(g["color"] / YEAR_S * 60, 8),
                "zomma": _f(g["zomma"] / 100, 7)}
        # smile every 60 s over the weekly's strikes that have an IV
        if now_s - self.svi_t >= 60.0:
            self.svi_t = now_s
            Ks, ivs = [], []
            for rr in ("CE", "PE"):
                for k in range(-config.HERO_BAND * 3, config.HERO_BAND * 3 + 1):
                    kk = int(atm + k * config.STRIKE_STEP)
                    i = eng.key.get(f"NIFTY|OPT|{w0}|{kk}|{rr}")
                    iv = (eng.greek.get(i) or {}).get("iv") if i is not None else None
                    otm = (rr == "CE" and kk >= atm) or (rr == "PE" and kk <= atm)    # OTM legs carry the smile
                    if iv and otm:
                        Ks.append(kk)
                        ivs.append(iv / 100.0)
            p = svi.fit(Ks, ivs, F, T, prev=self.svi_p) if len(Ks) >= 5 else None
            self.svi_p = p if p is not None else self.svi_p
            self._svi = {"K": Ks, "res": [_f(x, 2) for x in svi.residual(p, Ks, ivs, F, T)]} if p is not None else None
        out["smile"] = getattr(self, "_svi", None)
        if self.post is not None:
            mu = self.hmm.mu[:, 0]
            out["regime"] = {"post": [_f(x, 3) for x in self.post], "state": self.state, "run_min": self.run,
                             "left_min": _f(self.hmm.remaining(self.state, self.run), 1),
                             "drift": [_f(x, 1) for x in mu]}
        self.v = out

    def view(self):
        return self.v
