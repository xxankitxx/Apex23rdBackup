import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
W = r"D:\ApexOptions\data\research\13nov\work\R02"
for f in ("a2_teardown.py", "a3_marks.py", "a5_twins.py"):
    print("#####", f, flush=True)
    exec(compile(open(W + "\\" + f, encoding="utf-8").read(), f, "exec"), {"__name__": "__main__"})
