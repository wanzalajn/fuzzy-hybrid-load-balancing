import json, numpy as np
from sim_core import *
names=list(CTRL)
def run_all(sc): return {n:metrics(sc,CTRL[n](sc)) for n in names}
res={}
res['nominal']=run_all(build_scenario())
# deterministic stress cases
S={
 'Low-solar day (50% peak)':dict(peak=0.75),
 'High-load day (+30%)':dict(t1_scale=1.3,t2_scale=1.3,t3_scale=1.3),
 'Long evening outage (17:00-23:00)':dict(outages=((9.5,11.0),(17.0,23.0))),
 'Repeated short outages (6 x 30 min)':dict(outages=tuple((h,h+0.5) for h in (8,10.5,13,16,18.5,20.5))),
 'Evening outage, low initial SOC (20%)':dict(soc0=0.2,outages=((18.5,22.5),),brownouts=()),
 'Cloud during outage (13:00-17:00 at 20%)':dict(outages=((12.5,16.5),(18.5,22.5)),cloud=((13.0,17.0,0.2),)),
 'Critical-heavy tiers (T1 x1.8, T2 x0.6)':dict(t1_scale=1.8,t2_scale=0.6),
}
res['stress']={k:run_all(build_scenario(**v)) for k,v in S.items()}
# Monte Carlo
rng=np.random.default_rng(2026); M=100; mc={n:[] for n in names}
for i in range(M):
    peak=PEAK*rng.uniform(0.4,1.0)
    cs=rng.uniform(10,15); cloud=((cs,cs+rng.uniform(0.5,2.5),rng.uniform(0.2,0.6)),)
    outs=[]
    if rng.random()<0.8:
        a=rng.uniform(6,15); outs.append((a,a+rng.uniform(0.5,2.5)))
    a=rng.uniform(17,20); outs.append((a,min(a+rng.uniform(1.5,6.0),24)))
    brown=((15.0,15.5),) if rng.random()<0.5 else ()
    sc=build_scenario(peak=peak,cloud=cloud,outages=tuple(outs),brownouts=brown,
        t1_scale=rng.uniform(0.8,1.3),t2_scale=rng.uniform(0.7,1.3),t3_scale=rng.uniform(0.7,1.3),
        soc0=rng.uniform(0.2,1.0),seed=int(rng.integers(1e9)))
    for n in names: mc[n].append(metrics(sc,CTRL[n](sc)))
summ={}
for n in names:
    L=mc[n]; d={}
    for k in ('A1','Usol','Egrid','CWUE_main','PRI_main','PRI_alt','blackout_min','Utot','A3','switch','minSOC'):
        v=np.array([x[k] for x in L],float); d[k]=(float(np.nanmean(v)),float(np.nanstd(v)))
    d['frac_T1_full']=float(np.mean([x['A1']>=99.99 for x in L])*100)
    d['frac_blackout']=float(np.mean([x['blackout_min']>0 for x in L])*100)
    summ[n]=d
res['mc']=summ; res['mc_runs']=M
# paired win rate on PRI_main fuzzy vs others
f=np.array([x['PRI_main'] for x in mc[names[0]]])
res['mc_win']={n:float(np.mean(f>np.array([x['PRI_main'] for x in mc[n]])+1e-9)*100) for n in names[1:]}
res['mc_tie']={n:float(np.mean(np.abs(f-np.array([x['PRI_main'] for x in mc[n]]))<=1e-9)*100) for n in names[1:]}
json.dump(res,open('results/results.json','w'),indent=1,default=float)
print(json.dumps(res['mc'],indent=0)[:3000]); print(res['mc_win'],res['mc_tie'])
for k,v in res['stress'].items():
    print(k); 
    for n in names: print('  ',n[:22].ljust(22),{x:round(v[n][x],2) for x in ('A1','Usol','Egrid','blackout_min','PRI_main')})
json.dump({n:[{k:float(v) for k,v in x.items()} for x in mc[n]] for n in names},open('results/mc_raw.json','w'))
