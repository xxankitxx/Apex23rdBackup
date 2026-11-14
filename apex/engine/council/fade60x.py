"""fade60x (14 Nov, shadow): on EXPIRY days buy against a 60-minute move of 0.7 day-sigmas; the champion's expiry exits.
See fade.py, docs/59."""
from .fade import Fade60Expiry as Strategy  # noqa: F401  (the adapter builds mod.Strategy())
