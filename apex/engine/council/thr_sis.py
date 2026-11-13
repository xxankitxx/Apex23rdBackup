"""thr_sis (14 Nov, shadow): the day before expiry, buy a 60-second thrust of BOTH sister indices (BANKNIFTY futures
and the FINNIFTY index, 8 Nifty-equivalent points each); the champion's exits. See thr_d1.py and docs/57."""
from .thr_d1 import SisStrategy as Strategy  # noqa: F401  (the adapter builds mod.Strategy())
