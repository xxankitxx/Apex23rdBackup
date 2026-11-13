import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
W = r"D:\ApexOptions\data\research\13nov\work\R02"
p = W + r"\a4_paths.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''    T = [x for x in trades if x["day"] == day]
''', '''    T = [x for x in trades if x["day"] == day]
    _man = json.load(open(os.path.join(r"D:\ApexOptions\data\research\ds_v2", part + ".manifest.json"), encoding="utf-8"))
    T = [x for x in T if _man["first"] <= x["t_in"] <= _man["last"]]      # only trades that start inside this part
''')
open(p, "w", encoding="utf-8").write(s)
