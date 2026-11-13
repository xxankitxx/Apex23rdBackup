import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd, json
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
B = r"D:\ApexOptions\data\replay\batch"
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
F = ["basket_gap", "wmove10", "wmove30", "wmove60", "wmove60_bank", "wmove60_other", "breadth_dir", "breadth60_dir",
     "breadth900_dir", "breadth_net", "breadth_chg5", "hw_n_with", "sync_dir", "hw_at_ext30", "hw_top3_share", "hw_disp300",
     "hw_book_imb_t", "hw_book_imb", "bank_z", "lead3_agree", "hw_vol_surge", "fn60", "fn300", "bn_minus_nifty300",
     "bn60", "mv10", "mv30", "mv60", "dom_z", "lead_s"]
cols = ["day", "book", "t_in", "ret_pct"] + ["wx_" + f for f in F]
df = pd.read_parquet(P, columns=cols)
df.columns = [c[3:] if c.startswith("wx_") else c for c in cols]
TW = 0.6142
for L in (10, 30, 60):
    df[f"div{L}"] = df[f"wmove{L}"] / TW - df[f"mv{L}"]
feats = F + ["div10", "div30", "div60"]
# Conductor trades
rows = []
for run, keep in (("p44_sim", None), ("p44_simr", {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"})):
    d = json.load(open(f"{B}\\{run}\\conductor_sim.json"))
    for day, v in d["days"].items():
        if run == "p44_sim" and day in {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}:
            continue
        if keep is not None and day not in keep:
            continue
        for t in v["trades"]:
            rows.append(dict(day=day, book=t["src"], t_in=float(t["t_in"]), cret=float(t["ret_pct"])))
C = pd.DataFrame(rows)
print("conductor trades", len(C), "days", C.day.nunique())
df["t_in"] = df["t_in"].astype(float)
M = C.merge(df.drop(columns=["ret_pct"]), on=["day", "book", "t_in"], how="left")
print("joined with photo:", int(M["basket_gap"].notna().sum()), "of", len(M))
M.to_parquet(OUT + r"\conductor_hw.parquet")
early = M.day <= "2026-11-04"; late = M.day >= "2026-11-05"


def stats(sub):
    if len(sub) == 0:
        return dict(n=0)
    g = sub.groupby("day")["cret"].apply(lambda r: (np.prod(1 + r.values / 100) - 1) * 100)
    return dict(n=int(len(sub)), sr=round(float((sub.cret > 0).mean()), 3), comp_sum=round(float(g.sum()), 1),
                lose_days=int((g < 0).sum()), days=int(len(g)))


base_e, base_l = stats(M[early]), stats(M[late])
print("base early", base_e, "late", base_l)
res = []
for f in feats:
    x = M[f].astype(float)
    for side in ("keep_ge", "keep_le"):
        best = None
        for q in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            th = float(np.nanquantile(x[early], q))
            keep = (x >= th) if side == "keep_ge" else (x <= th)
            keep = keep | x.isna()
            s = stats(M[early & keep])
            if s["n"] < 0.5 * base_e["n"]:
                continue
            score = s["sr"]
            if best is None or score > best[0]:
                best = (score, q, th, s)
        if best is None:
            continue
        _, q, th, se = best
        keep = ((x >= th) if side == "keep_ge" else (x <= th)) | x.isna()
        sl = stats(M[late & keep])
        res.append(dict(f=f, side=side, q=q, th=round(th, 3), e_n=se["n"], e_sr=se["sr"], e_ret=se["comp_sum"],
                        l_n=sl["n"], l_sr=sl["sr"], l_ret=sl["comp_sum"], l_lose=sl["lose_days"]))
R = pd.DataFrame(res).sort_values("e_sr", ascending=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
print(R.to_string())
R.to_csv(OUT + r"\s05_veto.csv", index=False)
print("variants tried:", len(feats) * 2 * 9)
# bins of the most interesting fields, both windows
for f in ("basket_gap", "div10", "div30", "breadth_dir", "breadth900_dir", "sync_dir", "hw_at_ext30", "wmove10"):
    x = M[f].astype(float)
    qs = np.nanquantile(x, [0, 1 / 3, 2 / 3, 1])
    b = pd.cut(x, np.unique(qs), include_lowest=True)
    t = M.assign(b=b, w=(M.cret > 0).astype(int), late=late).groupby(["b", "late"], observed=True).agg(
        n=("w", "size"), sr=("w", "mean"), mean_ret=("cret", "mean"))
    print("\n", f, "\n", t.round(3).to_string())
