"""Move clock (owner, 29 Oct: "Big and good moves don't last more than 10-15 minutes").

How long the current Nifty leg has been running. A leg starts at the last swing extreme that spot has since moved
>= 0.12 % away from (zig-zag on the 1-Hz spot, last 60 minutes)."""
import numpy as np

NAME = "move_clock"
TITLE = "Move clock (10-15 min rule)"
IDEA = "Big moves last 10-15 minutes: how old is the current leg, and is it still young enough to buy?"
VERDICT = "Research 28-29 Oct: max-hold / time exits cut the best winners; shown here as a clock, not a rule."
EVERY_S = 2

SWING = 0.0012      # a 0.12 % reversal (~30 Nifty pts) starts a new leg


def zigzag(S, sw=SWING):
    """-> (direction +1/-1/0, start index, extreme index) of the current leg."""
    d, start, ext, hi, lo = 0, 0, 0, 0, 0
    for i in range(1, len(S)):
        x = S[i]
        if d == 0:
            if x > S[hi]:
                hi = i
            if x < S[lo]:
                lo = i
            if x >= S[lo] * (1 + sw):
                d, start, ext = 1, lo, i
            elif x <= S[hi] * (1 - sw):
                d, start, ext = -1, hi, i
        elif d > 0:
            if x > S[ext]:
                ext = i
            elif x <= S[ext] * (1 - sw):
                d, start, ext = -1, ext, i
        else:
            if x < S[ext]:
                ext = i
            elif x >= S[ext] * (1 + sw):
                d, start, ext = 1, ext, i
    return d, start, ext


class Idea:
    def update(self, env):
        T, S = env.hist.series("SPOT", secs=3600)
        ok = np.isfinite(S)
        T, S = T[ok], S[ok]
        if len(S) < 60:
            return {"state": "WARMING", "text": "needs a minute of spot"}
        d, start, ext = zigzag(S.tolist())
        if d == 0:
            return {"state": "NO LEG", "text": f"spot inside {SWING * 100:.2f} % for {len(S) // 60} min"}
        age = (T[-1] - T[start]) / 60.0
        pts = S[-1] - S[start]
        off_ext = S[-1] - S[ext]
        st = "YOUNG" if age < 10 else "MATURE" if age <= 15 else "OLD"
        return {"state": f"{st} LEG {'UP' if d > 0 else 'DOWN'}",
                "side": ("CE" if d > 0 else "PE") if age <= 15 else None,
                "value": age, "unit": "min",
                "text": f"{'up' if d > 0 else 'down'} {abs(pts):.0f} pts in {age:.1f} min; {abs(off_ext):.0f} pts off its "
                        f"{'high' if d > 0 else 'low'}",
                "plan": "" if age > 15 else f"{15 - age:.0f} min left by the 15-min rule"}
