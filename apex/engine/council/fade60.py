"""fade60 (14 Nov, shadow): buy against a 60-minute move of 0.7 day-sigmas; the champion's exits. See fade.py, docs/58."""
from .fade import Fade60 as Strategy  # noqa: F401  (the adapter builds mod.Strategy())
