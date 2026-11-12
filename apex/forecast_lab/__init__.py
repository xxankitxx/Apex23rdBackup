"""Forecast Lab (11 Nov 2026, owner's request): a path forecaster for the Nifty future and its weekly options that
runs OUTSIDE the engine, scores itself on every forecast that matures, and learns from those scores.

  core.py   the models: futures path (four drift experts, a calibrated volatility, online expert weights), option
            repricing along simulated paths with time decay and implied-volatility drift, the decay register, the
            self-scoring, and the plain-English commentary. Pure numpy; no shared memory, no files.
  live.py   the live runner: reads the feed's shared-memory table read-only once a second, writes the panel's JSON
            and its own learning state. Adds nothing to the engine's step.
  tape.py   the same core fed from the recorded sessions (data/research/ds_v2): warm start and offline tests.

Display and research only. Nothing here places, changes or blocks a trade."""
