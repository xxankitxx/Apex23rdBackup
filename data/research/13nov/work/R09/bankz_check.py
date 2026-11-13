import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, numpy as np, pandas as pd
R = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R09\trades_results.json"))
df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["day", "book", "t_in", "ret_pct", "wx_bank_z"])
days = sorted(df.day.unique()); E = [d for d in days if d <= "2026-11-04"]; L = [d for d in days if d > "2026-11-04"]
ct = []
for run in ("p44_sim", "p44_simr"):
    d = json.load(open(rf"D:\ApexOptions\data\replay\batch\{run}\conductor_sim.json"))
    for day, v in d["days"].items():
        if (run == "p44_sim") == (day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")):
            continue
        for t in v["trades"]:
            ct.append(dict(day=day, book=t["src"], t_in=float(t["t_in"]), ret=float(t["ret_pct"])))
ct = pd.DataFrame(ct); df["t_in"] = df.t_in.astype(float)
cj = ct.merge(df[["day", "book", "t_in", "wx_bank_z"]], on=["day", "book", "t_in"], how="left")


def sc(s, ds):
    dr = np.array([np.prod(1 + s.loc[s.day == d, "ret"].values / 100) - 1 for d in ds]) * 100
    lg = np.log1p(dr / 100)
    return dict(n=len(s), st=round((s.ret > 0).mean() * 100, 1), comp=round(np.expm1(lg.sum()) * 100, 1), ld=int((dr < 0).sum()),
                worst=round(dr.min(), 1), wo_best_day=round(np.expm1(lg.sum() - lg.max()) * 100, 1),
                wo_best_trade=round(float(s.ret.sum() - s.ret.max()), 1) if len(s) else 0)
print("CONDUCTOR (trades dropped, no replacement)")
for cut in (None, -1.0, -0.5, 0.0, 0.5):
    s = cj if cut is None else cj[~(cj.wx_bank_z < cut)]
    print(" cut", cut, "disc", sc(s[s.day.isin(E)], E), "test", sc(s[s.day.isin(L)], L))
# kept share of top 10 trades
top = cj.sort_values("ret", ascending=False).head(10)
print(" top10 bank_z", top.wx_bank_z.round(2).tolist())
print("POOL BOOKS")
P = df[df.book.isin(["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"])].rename(columns={"ret_pct": "ret"})
for cut in (None, -0.5, 0.0):
    for b in sorted(P.book.unique()):
        s = P[P.book == b]; s = s if cut is None else s[~(s.wx_bank_z < cut)]
        print(" cut", cut, b, "disc", sc(s[s.day.isin(E)], E), "test", sc(s[s.day.isin(L)], L))
