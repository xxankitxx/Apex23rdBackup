import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H, time
t=time.time(); df=H.load(); print("load",time.time()-t, len(df))
t=time.time(); c=H.conductor(df[df.book.isin(H.POOL)]); print("pool cond",time.time()-t)
t=time.time()
for b in sorted(df.book.unique())[:10]: H.conductor(df[df.book==b],[b])
print("10 books",time.time()-t)
