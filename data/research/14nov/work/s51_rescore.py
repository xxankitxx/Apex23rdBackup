"""Re-score every round-1 verified candidate on the corrected harness (fresh champion cache, minute history on every
split, recorded-day features) in one consistent pass. Writes agents/_rescore_<tag>.csv.

    py -3.13 s51_rescore.py [splits ...]
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, arena
from concurrent.futures import ProcessPoolExecutor

J = r"C:/Users/Ankit Madhogaria/.claude/projects/D--ApexOptions/4fc710fd-915d-4b6c-be6c-118168a8b13b/subagents/workflows/wf_60379da3-d68/journal.jsonl"


def candidates():
    rows = [json.loads(l) for l in open(J, encoding="utf-8")]
    lab = {j["key"]: j["label"] for j in rows if j["type"] == "started"}
    out = {}
    for j in rows:
        if j.get("type") == "result" and lab.get(j["key"], "").startswith("Verify"):
            r = j["result"]
            if isinstance(r, dict) and r.get("generator_path") and os.path.exists(r["generator_path"]):
                out[r["generator_path"]] = dict(name=lab[j["key"]][7:], confirmed=r.get("confirmed"))
    return out


def one(a):
    path, name, splits = a
    try:
        R = arena.evaluate(path, name=name, splits=splits)
        R["gen"] = path
        return R
    except Exception as e:
        return pd.DataFrame([dict(idea=name, gen=path, error=f"{type(e).__name__}: {e}")])


if __name__ == "__main__":
    splits = tuple(sys.argv[1:]) or ("found", "judged", "window")
    C = candidates()
    print(len(C), "candidates")
    with ProcessPoolExecutor(max_workers=4) as ex:
        R = pd.concat(list(ex.map(one, [(p, v["name"], splits) for p, v in C.items()])), ignore_index=True)
    R["confirmed"] = R.gen.map(lambda p: C[p]["confirmed"])
    tag = "_".join(splits)
    R.to_csv(os.path.join(arena.AGENTS, f"_rescore_{tag}.csv"), index=False)
    print(R.to_string(max_cols=30))
