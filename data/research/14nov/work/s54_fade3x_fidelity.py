"""docs/60 bar test 5 for fade3x: the engine class (apex/engine/council/fade3x.py) stepped per second on the real-IV
chain against the research generator's entries (agents/_finalists/gen_fB_fade3x.py through arena) on expiry days."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "D:/ApexOptions")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import arena, lab1s
from apex import fastlab as FL
import s50_live_chain as S

GEN = "D:/ApexOptions/data/research/14nov/agents/_finalists/gen_fB_fade3x.py"


def one(day):
    try:
        D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy()) if day in arena.REC else lab1s.session(day)
        L = S.realiv_live(D)
        from apex.engine.council import c20_8x, fade
        lv = S.levels_file(); c20_8x.LEVELS_PATH = lv; fade._FadeMixin.LEVELS = lv
        t0 = time.perf_counter()
        eng = FL.play(D, L, "fade3x")
        dt = (time.perf_counter() - t0) / max(1, len(D["fwd"]))
        res = arena.trades(arena.load_gen(GEN), [day])
        return dict(day=day, eng=[(int(t["i_in"]), t.get("side") or t.get("rr")) for t in eng],
                    res=[(int(r.i_in), r.side) for r in res.itertuples()] if len(res) else [], ms=1000 * dt,
                    eng_ret=[float(t["ret"]) for t in eng], res_ret=list(res.ret) if len(res) else [])
    except Exception as e:
        return dict(day=day, error=f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    days = [d for d in arena.sessions() if arena.is_expiry(d) and arena.has_wx(d) and not d < "2025-11-14"]
    with ProcessPoolExecutor(max_workers=4) as ex:
        R = list(ex.map(one, days))
    err = [r for r in R if "error" in r]
    R = [r for r in R if "error" not in r]
    n_res = sum(len(r["res"]) for r in R)
    hit = sum(sum(1 for (i, s) in r["res"] if any(abs(i - j) <= 2 and s == s2 for j, s2 in r["eng"])) for r in R)
    n_eng = sum(len(r["eng"]) for r in R)
    print(f"expiry days {len(R)} (errors {len(err)}): research entries {n_res}, engine entries {n_eng}, reproduced {hit} = {100 * hit / max(1, n_res):.0f} %")
    print(f"engine day sum {sum(100 * (np.prod(1 + np.array(r['eng_ret']) / 100) - 1) for r in R):+.0f} %, research {sum(100 * (np.prod(1 + np.array(r['res_ret']) / 100) - 1) for r in R):+.0f} %")
    print(f"fade3x step time on the simulator: median {np.median([r['ms'] for r in R]):.3f} ms a second")
    for e in err[:5]:
        print(e)
    pd.DataFrame(R).to_json("D:/ApexOptions/data/research/14nov/agents/_finalists/fade3x_fidelity.json", orient="records")
