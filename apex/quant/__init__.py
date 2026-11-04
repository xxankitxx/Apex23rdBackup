"""Quantitative evidence layer (5 Nov 2026, from the reviews in reviews/): models that SUPPLY EVIDENCE to the
strategies; none of them trades on its own. Every model here is streaming (constant work per update) so it can run
inside the 100-ms engine tick.

    greeks_hi   Black-76 to third order (vanna, vomma, charm, speed, color, zomma, ultima) and full repricing
    passage     first-passage / competing-risk probabilities: does the option's TARGET come before its STOP,
                and by when (premium outcome model; the reviews' "ultimate authority for entry")
    hawkes      self-exciting order-flow intensity (exponential kernel, O(1) update, MLE fit)
    regime      Gaussian hidden Markov model: Baum-Welch fit offline, online forward filter, semi-Markov
                expected remaining duration of the current state
    micro       jump-robust bipower variation, CUSUM change points, Kyle's lambda, Kalman velocity
    svi         raw-SVI smile fit per snapshot and each strike's residual against it

Conventions: Black-76 on the parity forward with r = 0 (the forward already carries the carry; pricing, IV and
parity all use the same undiscounted convention). Times in years for pricing, seconds for the streaming models.
"""
