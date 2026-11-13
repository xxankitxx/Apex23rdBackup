import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R02")
import time, json; import pathlib_r02 as L
t0=time.time(); P=L.load_part("2026-11-06"); print("load", round(time.time()-t0,1))
T=[x for x in json.load(open("pool_trades.json")) if x["day"]=="2026-11-06"]
t0=time.time(); p=L.trade_path(P,T[0]); print("path", round(time.time()-t0,2), len(p["t"]))
t0=time.time(); L.add_theta(p,T[0]); r=L.sim(p,{},T[0]["book"]); print("sim", round(time.time()-t0,3))
print(sum(1 for x in json.load(open("pool_trades.json")) if x["day"]=="2026-11-09"), sum(1 for x in json.load(open("pool_trades.json")) if x["day"]=="2026-11-11"))
