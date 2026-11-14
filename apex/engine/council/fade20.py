"""fade20 (14 Nov, shadow): buy against a 20-minute move of 0.6 day-sigmas; the champion's exits. See fade.py, docs/58."""
from .fade import Fade20 as Strategy  # noqa: F401  (the adapter builds mod.Strategy())
