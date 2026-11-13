import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
M=pd.read_pickle("cond.pkl"); d=np.where(M.rr=="CE",1,-1); late=M.day>="2026-11-05"
for nm,m in [("bank unsigned<-0.5",M.wx_bank_z<-0.5),("bank signed<-0.5",d*M.wx_bank_z<-0.5),
             ("gap unsigned>1.6",M.wx_basket_gap>1.6),("gap signed>1.6",d*M.wx_basket_gap>1.6)]:
    print(nm,"early cut",int(m[~late].sum()),"late cut",int(m[late].sum()))
print(M.groupby("rr")[["wx_bank_z","wx_basket_gap"]].median())
