import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import joblib, numpy as np
d = joblib.load(r"D:\ApexOptions\data\forecast_lab\collect\2026-11-11.joblib")
print(type(d))
if isinstance(d, dict):
    for k, v in d.items():
        print(k, type(v), getattr(v, 'shape', None) if hasattr(v,'shape') else (len(v) if hasattr(v,'__len__') else v))
