"""Premium-return RANGES for the forecast record (docs/40 section 3, docs/41 section 12.3).

A frozen artefact (ranges_v1.json, fitted offline by make_ranges.py): per horizon a ridge model for the mean of the
quote-aware return of the fixed contract, a ridge model for its scale, and three standardised quantiles.
    quantile = mean(x) + max(scale(x), floor) * zq
No fitting at run time. A record only: nothing in the engine decides on a range."""
import json
import os

import numpy as np

from . import features as F, targets as T


class Ranger:
    def __init__(self, artefact=None, path=None):
        if artefact is None and path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                artefact = json.load(f)
        self.art = artefact
        self.why = None
        if artefact is None:
            self.why = "no range artefact"
        elif artefact.get("feature_schema") != F.SCHEMA:
            self.why = f"ranges were fitted on feature schema {artefact.get('feature_schema')}, the engine has {F.SCHEMA}"
        elif artefact.get("target_spec") != T.SPEC:
            self.why = "ranges were fitted on a different target specification"
        self.ok = self.why is None
        self.hash = (artefact or {}).get("hash")
        self.horizons = ()
        if self.ok:
            hs = sorted(artefact["horizons"], key=int)
            self.horizons = tuple(int(h) for h in hs)
            self.quantiles = tuple(artefact["quantiles"])
            self.clip = float(artefact.get("clip", 4.0))
            g = lambda k: np.array([artefact["horizons"][h][k] for h in hs], float)
            self._med, self._sd = g("med"), g("sd")
            self._mu0, self._mu = g("w_mu")[:, 0], g("w_mu")[:, 1:]
            self._sc0, self._sc = g("w_sc")[:, 0], g("w_sc")[:, 1:]
            self._floor, self._zq = g("floor"), g("zq")

    def ranges(self, x):
        """x: the feature vector (features.NAMES order). Returns None without a usable artefact, else
        {horizon: [q10, q50, q90]} as fractions of the entry premium (0.05 = +5 %). The quantiles never cross."""
        if not self.ok or x is None:
            return None
        z = np.clip(np.nan_to_num((np.asarray(x, float)[None, :] - self._med) / self._sd, nan=0.0, posinf=self.clip,
                                  neginf=-self.clip), -self.clip, self.clip)
        mu = self._mu0 + (z * self._mu).sum(1)
        s = np.maximum(self._sc0 + (z * self._sc).sum(1), self._floor)
        q = mu[:, None] + s[:, None] * self._zq
        return {h: [round(float(v), 5) for v in q[j]] for j, h in enumerate(self.horizons)}
