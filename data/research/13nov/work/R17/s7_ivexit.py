import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, numpy as np, pandas as pd
full=sim.load(slim=False)
base_cols=['day','book','rr','entry','exit','trig','t_in','t_out','ret_pct','fut_in','fut_out','iv_in','iv_out','pri','wx_mins_open','wx_spread_pct']
def variant(M, th, gmax):
    d=full[base_cols].copy()
    hs=full[f'h{M}_hold_s']; iv=full[f'h{M}_attr_iv_chg']; gp=full[f'h{M}_gain_pct']
    still=(full.t_out-full.t_in)>M+1
    hit=still & hs.notna() & iv.notna() & gp.notna() & (iv<th) & (gp<gmax)
    spr=full.wx_spread_pct.fillna(0.25)
    newret=gp-spr      # ltp-based mark, pay roughly one spread to sell at the bid
    d.loc[hit,'exit']=d.loc[hit,'entry']*(1+newret[hit]/100)
    d.loc[hit,'ret_pct']=newret[hit]; d.loc[hit,'t_out']=d.loc[hit,'t_in']+M
    return d, hit
b,_=variant(60,-99,-999)
base=sim.sim(b)
def tot(res,days): 
    n=sum(res[x]['n'] for x in days); w=sum(res[x]['w'] for x in days)
    return round(sum(res[x]['ret_day'] for x in days),1), round(100*w/max(n,1),1), n, sum(res[x]['ret_day']<0 for x in days)
print('base E',tot(base,sim.EARLY),'L',tot(base,sim.LATE))
rows=[]
for M in (60,300):
    for th in (-1.0,-0.5,-0.3,0.0):
        for g in (-5.0,-2.0,0.0,999.0):
            d,hit=variant(M,th,g); r=sim.sim(d)
            # also: of hit trades, how many ended as winners originally
            hw=int(((full.ret_pct>0)&hit).sum()); hl=int(((full.ret_pct<=0)&hit).sum())
            e=tot(r,sim.EARLY); l=tot(r,sim.LATE)
            rows.append((M,th,g,hw,hl,*e,*l, [round(r[x]['ret_day']-base[x]['ret_day'],1) for x in sim.LATE]))
R=pd.DataFrame(rows,columns=['M','iv_lt','gain_lt','hitW','hitL','E_tot','E_sr','E_n','E_ld','L_tot','L_sr','L_n','L_ld','L_delta_by_day'])
pd.set_option('display.width',250); print(R.to_string())
