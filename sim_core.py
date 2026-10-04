"""Re-implementation of the manuscript simulation (Appendix B/C controllers) with a
parametrised scenario generator, extra benchmarks and extra metrics."""
import numpy as np
CAP=4.8; DT=1/60; N=1440; EFF=0.90; CH_MAX=0.6; DIS_MAX=1.2; SOC_FLOOR=0.10; L_MAX=2.0
PEAK=1.5

def tri(x,a,b,c):
    x=np.asarray(x,dtype=float)
    left=(x-a)/(b-a) if b!=a else np.ones_like(x)
    right=(c-x)/(c-b) if c!=b else np.ones_like(x)
    return np.clip(np.minimum(left,right),0,1)
solar_low=lambda x:tri(x,-0.4,0,0.4); solar_med=lambda x:tri(x,0.2,0.5,0.8); solar_high=lambda x:tri(x,0.6,1.0,1.4)
soc_low=lambda x:tri(x,-0.4,0,0.45); soc_med=lambda x:tri(x,0.25,0.5,0.75); soc_high=lambda x:tri(x,0.55,1.0,1.4)
grid_absent=lambda x:tri(x,-0.4,0,0.4); grid_unstable=lambda x:tri(x,0.2,0.5,0.8); grid_stable=lambda x:tri(x,0.6,1.0,1.4)
load_low=lambda x:tri(x,-0.4,0,0.4); load_med=lambda x:tri(x,0.2,0.5,0.8); load_high=lambda x:tri(x,0.6,1.0,1.4)
P_UNIV=np.linspace(0,1,201); T_UNIV=np.linspace(0,3,301)
p_grid=lambda u:tri(u,-0.4,0,0.45); p_blend=lambda u:tri(u,0.25,0.5,0.75); p_solar=lambda u:tri(u,0.55,1.0,1.4)
t_t1=lambda u:tri(u,-0.6,0.5,1.2); t_t12=lambda u:tri(u,0.8,1.5,2.2); t_all=lambda u:tri(u,1.8,2.5,3.6)
# precompute output MFs on universes
_PM={f:f(P_UNIV) for f in (p_grid,p_blend,p_solar)}; _TM={f:f(T_UNIV) for f in (t_t1,t_t12,t_all)}
def centroid(univ,agg):
    s=agg.sum(); return float((univ*agg).sum()/s) if s>1e-9 else float(univ.mean())
def fuzzy_controller(S,B,G,L):
    sL,sM,sH=solar_low(S),solar_med(S),solar_high(S)
    bL,bM,bH=soc_low(B),soc_med(B),soc_high(B)
    gA,gU,gS=grid_absent(G),grid_unstable(G),grid_stable(G)
    lL,lM,lH=load_low(L),load_med(L),load_high(L)
    pr=[(min(sH,max(bM,bH)),p_solar),(bH,p_solar),(gA,p_solar),(min(bL,gS,sL),p_grid),
        (min(max(bL,bM),gS),p_grid),(min(sM,bM),p_blend),(min(gU,bM),p_blend),(min(sH,bL,gS),p_blend)]
    a=np.zeros_like(P_UNIV)
    for w,mf in pr:
        if w>0: a=np.maximum(a,np.minimum(w,_PM[mf]))
    P=centroid(P_UNIV,a)
    tr=[(min(sH,bH),t_all),(min(sH,bM),t_all),(bH,t_all),(min(gS,bM),t_all),(min(gS,bL),t_t12),
        (min(gU,bM),t_t12),(min(gA,bM),t_t12),(min(gA,bL),t_t1),(min(gU,bL),t_t1),(min(sL,bL,lH),t_t1)]
    a=np.zeros_like(T_UNIV)
    for w,mf in tr:
        if w>0: a=np.maximum(a,np.minimum(w,_TM[mf]))
    return P,centroid(T_UNIV,a)

def hrs(h): return int(round(h*60))
def build_scenario(peak=PEAK,sunrise=6.5,sunset=17.5,cloud=((13.0,14.5,0.3),),outages=((9.5,11.0),(18.5,22.5)),
                   brownouts=((15.0,15.5),),t1_scale=1.0,t2_scale=1.0,t3_scale=1.0,noise=0.05,seed=0,soc0=0.6):
    rng=np.random.default_rng(seed); t=np.arange(N)/60.0
    sol=np.where((t>=sunrise)&(t<=sunset),peak*np.sin(np.pi*(t-sunrise)/(sunset-sunrise)),0.0)
    for a,b,f in cloud: sol=np.where((t>=a)&(t<b),sol*f,sol)
    sol=np.clip(sol*(1+noise*rng.standard_normal(N)),0,None)*(sol>0)
    g=np.ones(N)
    for a,b in outages: g[(t>=a)&(t<b)]=0.0
    for a,b in brownouts: g[(t>=a)&(t<b)]=np.minimum(g[(t>=a)&(t<b)],0.5)
    t1=np.where((t>=17.5)&(t<23.0),0.45,0.30)*t1_scale
    t2=np.zeros(N)
    for a,b,p in ((6.5,8.5,0.8),(9.0,12.0,1.0),(12.0,16.0,0.5),(16.0,18.0,1.2),(18.5,22.5,0.3)):
        t2[(t>=a)&(t<b)]+=p
    t2*=t2_scale
    t3=np.where((t>=18.5)&(t<23.0),0.6,0.0)*t3_scale
    return dict(solar=sol,grid=g,t1=t1,t2=t2,t3=t3,soc0=soc0)

def _tier_alloc(d1,d2,d3,allowed,unserved):
    s3=d3 if (allowed>=3 and unserved<=1e-9) else (max(0.0,d3-unserved) if allowed>=3 else 0.0)
    rem=max(0.0,unserved-(d3 if allowed>=3 else 0.0)+s3) if allowed>=3 else unserved
    s2=d2 if (allowed>=2 and rem<=1e-9) else (max(0.0,d2-rem) if allowed>=2 else 0.0)
    rem2=max(0.0,rem-(d2 if allowed>=2 else 0.0)+s2) if allowed>=2 else rem
    return max(0.0,d1-rem2),s2,s3

def run_proposed(sc,mode='fuzzy'):
    """mode: 'fuzzy' (Appendix C loop) or 'crisp' (rule-based tiered controller, no fuzzy)"""
    soc=sc['soc0']; solar,grid=sc['solar'],sc['grid']; sigma=0
    H=dict(soc=[],served1=[],served2=[],served3=[],grid_kW=[],solar_used=[],src=[])
    for k in range(N):
        S=min(solar[k]/PEAK,1.0); G=grid[k]; d1,d2,d3=sc['t1'][k],sc['t2'][k],sc['t3'][k]
        if mode=='fuzzy':
            P,T=fuzzy_controller(S,soc,G,min((d1+d2+d3)/L_MAX,1.0))
            allowed=3 if T>=2.0 else (2 if T>=1.0 else 1)
        else:  # crisp analogue: same logic, hard thresholds
            if G<0.4: allowed=3 if soc>=0.70 else (2 if soc>=0.35 else 1)
            elif G<0.8: allowed=3 if soc>=0.70 else (2 if soc>=0.35 else 1)
            else: allowed=3 if soc>=0.35 else 2
            if G>=0.8 and soc<0.35: allowed=2
            if G<0.4 or soc>0.80: sigma=1
            elif soc<0.70: sigma=0
            P=1.0 if sigma==1 else 0.0
        demand=d1+(d2 if allowed>=2 else 0)+(d3 if allowed>=3 else 0)
        su=min(solar[k],demand); deficit=demand-su; g=0.0; bo=0.0; ok=G>=0.4
        can=min(DIS_MAX,max(0.0,(soc-SOC_FLOOR)*CAP/DT))
        if P>=0.5:
            bo=min(deficit,can); deficit-=bo
            if deficit>0 and ok: g=deficit; deficit=0.0
        else:
            if ok: g=deficit; deficit=0.0
            else: bo=min(deficit,can); deficit-=bo
        un=deficit; surplus=max(0.0,solar[k]-su); ch=min(surplus,CH_MAX,(1.0-soc)*CAP/DT); gch=0.0
        if P<0.55 and soc<0.8 and G>=0.9:
            gch=max(0.0,min(0.4,CH_MAX-ch,(1.0-soc)*CAP/DT-ch))
        soc=float(np.clip(soc+(ch+gch)*EFF*DT/CAP-bo*DT/(EFF*CAP),0,1)); g+=gch
        s1,s2,s3=_tier_alloc(d1,d2,d3,allowed,un)
        H['soc'].append(soc);H['served1'].append(s1);H['served2'].append(s2);H['served3'].append(s3)
        H['grid_kW'].append(g);H['solar_used'].append(su+ch);H['src'].append(1 if P>=0.5 else 0); H.setdefault('P',[]).append(P)
    R={k:np.array(v) for k,v in H.items()}; R['fuzzy']=(mode=='fuzzy'); return R

def run_baseline(sc):
    soc=sc['soc0']; solar,grid=sc['solar'],sc['grid']; lock=False
    H=dict(soc=[],served1=[],served2=[],served3=[],grid_kW=[],solar_used=[],src=[])
    for k in range(N):
        d1,d2,d3=sc['t1'][k],sc['t2'][k],sc['t3'][k]; dem=d1+d2+d3; ok=grid[k]>=0.4
        g=0.0;su=0.0;s1=s2=s3=0.0
        if ok:
            lock=False; g=dem; s1,s2,s3=d1,d2,d3
            ch=min(solar[k],CH_MAX,(1-soc)*CAP/DT); soc=float(np.clip(soc+ch*EFF*DT/CAP,0,1)); su=ch
        else:
            if soc<=0.20: lock=True
            if not lock:
                sd=min(solar[k],dem); de=dem-sd; can=min(DIS_MAX,max(0.0,(soc-SOC_FLOOR)*CAP/DT))
                bo=min(de,can); fr=(sd+bo)/dem if dem>0 else 1.0; s1,s2,s3=d1*fr,d2*fr,d3*fr
                ch=min(max(0.0,solar[k]-sd),CH_MAX,(1-soc)*CAP/DT)
                soc=float(np.clip(soc+ch*EFF*DT/CAP-bo*DT/(EFF*CAP),0,1)); su=sd+ch
            else:
                ch=min(solar[k],CH_MAX,(1-soc)*CAP/DT); soc=float(np.clip(soc+ch*EFF*DT/CAP,0,1)); su=ch
        H['soc'].append(soc);H['served1'].append(s1);H['served2'].append(s2);H['served3'].append(s3)
        H['grid_kW'].append(g);H['solar_used'].append(su);H['src'].append(0 if ok else 1)
    return {k:np.array(v) for k,v in H.items()}

def run_ats_priority(sc):
    """Benchmark B2: ATS with critical-load priority (no fuzzy, no reserve conservation).
    Grid serves all load when present; solar only charges the battery. During outage the inverter
    serves tiers in priority order, shedding Tier 3 below 50 % SOC and Tier 2 below 30 % SOC;
    Tier 1 is served down to the 10 % SOC floor."""
    soc=sc['soc0']; solar,grid=sc['solar'],sc['grid']
    H=dict(soc=[],served1=[],served2=[],served3=[],grid_kW=[],solar_used=[],src=[])
    for k in range(N):
        d1,d2,d3=sc['t1'][k],sc['t2'][k],sc['t3'][k]; ok=grid[k]>=0.4; g=0.0; s1=s2=s3=0.0
        if ok:
            g=d1+d2+d3; s1,s2,s3=d1,d2,d3
            ch=min(solar[k],CH_MAX,(1-soc)*CAP/DT); soc=float(np.clip(soc+ch*EFF*DT/CAP,0,1)); su=ch
        else:
            allowed=3 if soc>=0.5 else (2 if soc>=0.3 else 1)
            dem=d1+(d2 if allowed>=2 else 0)+(d3 if allowed>=3 else 0)
            sd=min(solar[k],dem); de=dem-sd; can=min(DIS_MAX,max(0.0,(soc-SOC_FLOOR)*CAP/DT))
            bo=min(de,can); un=de-bo
            s1,s2,s3=_tier_alloc(d1,d2,d3,allowed,un)
            ch=min(max(0.0,solar[k]-sd),CH_MAX,(1-soc)*CAP/DT)
            soc=float(np.clip(soc+ch*EFF*DT/CAP-bo*DT/(EFF*CAP),0,1)); su=sd+ch
        H['soc'].append(soc);H['served1'].append(s1);H['served2'].append(s2);H['served3'].append(s3)
        H['grid_kW'].append(g);H['solar_used'].append(su);H['src'].append(0 if ok else 1)
    return {k:np.array(v) for k,v in H.items()}

W_MAIN=(10.0,3.0,1.0); W_ALT=(5.0,2.0,1.0)
def metrics(sc,H):
    d=[sc['t1'],sc['t2'],sc['t3']]; s=[H['served1'],H['served2'],H['served3']]
    E_dem=[x.sum()*DT for x in d]; E_srv=[x.sum()*DT for x in s]; un=[a-b for a,b in zip(E_dem,E_srv)]
    out={}
    out['A1']=100*E_srv[0]/E_dem[0] if E_dem[0]>0 else 100.0
    out['U1']=un[0]; out['U2']=un[1]; out['U3']=un[2]; out['Utot']=sum(un)
    out['A2']=100*E_srv[1]/E_dem[1]; out['A3']=100*E_srv[2]/E_dem[2] if E_dem[2]>0 else 100.0
    sol=sc['solar'].sum()*DT; out['Usol']=100*H['solar_used'].sum()*DT/sol if sol>0 else float('nan')
    out['Egrid']=H['grid_kW'].sum()*DT
    out['blackout_min']=int(((sc['t1']>0)&(H['served1']<1e-6)).sum())
    out['degraded_min']=int(((sc['t1']>0)&(H['served1']<sc['t1']-1e-6)&(H['served1']>=1e-6)).sum())
    out['minSOC']=100*H['soc'].min()
    if 'P' in H and H.get('fuzzy',False):
        sg=0;n=0
        for p in H['P']:
            new=1 if p>0.55 else (0 if p<0.45 else sg)
            n+= (new!=sg); sg=new
        out['switch']=int(n)
    else: out['switch']=int((np.diff(H['src'])!=0).sum())
    for nm,w in (('main',W_MAIN),('alt',W_ALT)):
        cw=sum(wi*ui for wi,ui in zip(w,un)); cd=sum(wi*e for wi,e in zip(w,E_dem))
        out['CWUE_'+nm]=cw; out['PRI_'+nm]=100*(1-cw/cd)
    return out
CTRL={'Fuzzy (proposed)':lambda sc:run_proposed(sc,'fuzzy'),'Threshold ATS (baseline)':run_baseline,
      'ATS + critical priority':run_ats_priority,'Crisp tiered rule-based':lambda sc:run_proposed(sc,'crisp')}
