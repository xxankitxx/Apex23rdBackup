import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, time
df=sim.load(); t=time.time(); r=sim.sim(df); print(time.time()-t, sim.summary(r))
t=time.time(); r=sim.sim(df); print('2nd',time.time()-t); print(sim.lot_size())
