"""The final verdict on the untouched holdout year for the finalists (docs/60 tests 1, 2, 3, 6)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, arena
FIN = "D:/ApexOptions/data/research/14nov/agents/_finalists"
if __name__ == "__main__":
    C = arena.champion_trades(rebuild="--rebuild" in sys.argv)
    print("champion cache", len(C), C.day.nunique(), "holdout days in it", C.day.between(*arena.SPLITS["holdout"]).sum())
    gens = [a for a in sys.argv[1:] if not a.startswith("--")] or ["fA_orblate", "fB_fade3x"]
    out = []
    for g in gens:
        R = arena.evaluate(f"{FIN}/gen_{g}.py", name=g, splits=("found", "judged", "window", "holdout"),
                           save=f"{FIN}/trades_{g}.parquet")
        out.append(R)
        arena.record("_finalists", g, R, "final verdict incl. holdout")
    R = pd.concat(out)
    R.to_csv(f"{FIN}/verdict.csv", index=False)
    pd.set_option("display.width", 250)
    print(R[["idea", "split", "days", "sessions", "trades", "winners", "per_trade", "day_sum", "t", "champ_day_sum", "champ_winners",
             "pooled_day_sum", "pooled_winners", "pooled_gain"]].to_string())
