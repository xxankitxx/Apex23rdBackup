"""tp_c20_9y (13 Nov, shadow twin): c20_9y with an EXPIRY-DAY premium take-profit at +60 % (EXP tp=0.60, the switch
the c20 core already has, c20_08.py). Normal days are c20_9y unchanged.

Evidence (docs/research/13nov/R02 and its Phase B run of 13 Nov, per-second bids from ds_v2, 523 rebuilt pool trades):
better in both windows (discovery +72.6 log pts, test +76.0), strike rate unchanged, positive without its best trade,
a plateau from 55 % to 70 %. Thin: the test gain is one expiry day (9 Nov) and only a few trades change. Shadow only,
judged on forward expiry days under the 7-test promotion standard; the Conductor never reads it.
"""
from . import c20_9y as _y

TP_EXPIRY = 0.60


class Strategy(_y.Strategy):
    def __init__(self, exp=None, **kw):
        super().__init__(exp=dict(exp or {}, tp=TP_EXPIRY), **kw)
