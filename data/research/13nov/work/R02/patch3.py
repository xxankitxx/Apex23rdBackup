import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
W = r"D:\ApexOptions\data\research\13nov\work\R02"
p = W + r"\a4_paths.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''    if os.environ.get("R02_COND"):
        T = [x for x in T if x.get("cond")]''', '''    if os.environ.get("R02_COND"):
        T = [x for x in T if x.get("cond")]
    if os.environ.get("R02_CHUNK"):                       # "k:size" -> the k-th block of `size` trades of this day
        k_, n_ = (int(v) for v in os.environ["R02_CHUNK"].split(":"))
        T = sorted(T, key=lambda x: (x["t_in"], x["book"]))[k_ * n_:(k_ + 1) * n_]''')
open(p, "w", encoding="utf-8").write(s)
