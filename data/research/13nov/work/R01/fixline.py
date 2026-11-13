p = r"D:\ApexOptions\data\research\13nov\work\R01\s06_fillers_fast.py"
L = open(p, encoding="utf-8").read().split("\n")
L[65] = 'R = pd.DataFrame(res); R.to_pickle(W + "/fillers_" + str(A) + ".pkl")'
open(p, "w", encoding="utf-8").write("\n".join(L))
