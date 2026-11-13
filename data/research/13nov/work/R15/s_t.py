import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time; t=time.time(); x=0
for i in range(3_000_000): x+=i
print("3M loop", time.time()-t)
