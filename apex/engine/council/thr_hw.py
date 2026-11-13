"""thr_hw (14 Nov, shadow): the day before expiry, buy a 60-second thrust of the Nifty-weighted heavyweight basket
(8 Nifty points with weighted breadth 0.5); the champion's exits. See thr_d1.py and docs/57."""
from .thr_d1 import HwStrategy as Strategy  # noqa: F401  (the adapter builds mod.Strategy())
