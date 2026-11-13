import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
D = r"D:\ApexOptions\data\research"
tr = pd.read_parquet(D + r"\13nov\trades_all_books.parquet", columns=["day", "book", "t_in", "t_out", "rr", "strike", "entry", "exit", "ret_pct"])
out = []
for part in ("2026-11-04", "2026-11-05", "2026-11-06"):
    z = np.load(fr"{D}\ds_v2\{part}.npz")
    t = z["t"]; opt = z["opt"]; K = z["strikes"]
    if part == "2026-11-04": print({k: z[k].shape for k in z.files if k in ("t", "opt", "strikes")})
    d = tr[tr.day == part]
    for r in d.itertuples():
        ki = np.where(np.isclose(K, r.strike))[0]
        if not len(ki): continue
        c = 0 if r.rr == "CE" else 1
        def px(ts, side):
            i = np.searchsorted(t, ts, side="right") - 1
            if i < 0 or i >= len(t): return np.nan
            return float(opt[i, ki[0], c, side])
        a0 = px(r.t_in, 1); b0 = px(r.t_out, 0)
        if not (a0 > 0 and b0 > 0): continue
        row = dict(day=part, book=r.book, c20=r.book.startswith("c20_9"), a0=a0, b0=b0)
        for dl in (0.5, 1, 2, 3, 5):
            row[f"in{dl}"] = (px(r.t_in + dl, 1) - a0) / a0 * 100      # extra paid for entering dl s late (pct of premium)
            row[f"out{dl}"] = (b0 - px(r.t_out + dl, 0)) / b0 * 100    # bid lost for exiting dl s late
        out.append(row)
df = pd.DataFrame(out)
df.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R13\latency_cost.parquet")
print("trades matched", len(df), "c20_9 pool", int(df.c20.sum()))
for name, g in (("all books", df), ("c20_9 pool books", df[df.c20])):
    print(name)
    for dl in (0.5, 1, 2, 3, 5):
        print(f"  delay {dl:>3} s: entry cost mean {g[f'in{dl}'].mean():+.3f}% median {g[f'in{dl}'].median():+.3f}%   exit cost mean {g[f'out{dl}'].mean():+.3f}% median {g[f'out{dl}'].median():+.3f}%   both {g[f'in{dl}'].mean()+g[f'out{dl}'].mean():+.3f}%")
    print("  per day 2 s both:", g.groupby("day").apply(lambda x: round(x["in2"].mean() + x["out2"].mean(), 3)).to_dict())
