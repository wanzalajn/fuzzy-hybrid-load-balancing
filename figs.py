import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from sim_core import *
plt.rcParams.update({'font.size':11,'axes.titlesize':12,'axes.labelsize':11,'legend.fontsize':10,'font.family':'DejaVu Sans'})
# ---- Fig 2 high-res membership functions (exact parameters of Appendix B)
x=np.linspace(0,1,401); u=np.linspace(0,3,601)
fig,ax=plt.subplots(2,3,figsize=(13,7.2),dpi=300)
def panel(a,t,xs,fs,lab,xl,cols=('#1f77b4','#ff7f0e','#2ca02c')):
    for f,l,c in zip(fs,lab,cols): a.plot(xs,f(xs),lw=2.2,label=l,color=c)
    a.set_title(t); a.set_xlabel(xl); a.set_ylabel(r'Membership $\mu$'); a.set_ylim(-0.02,1.05); a.grid(alpha=.3); a.legend(loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(0.5,-0.2))
panel(ax[0,0],'(a) Solar output',x,[solar_low,solar_med,solar_high],['Low','Medium','High'],'Normalised solar output $S$')
panel(ax[0,1],'(b) Battery SOC',x,[soc_low,soc_med,soc_high],['Low','Medium','High'],'Battery SOC $B$')
panel(ax[0,2],'(c) Grid status',x,[grid_absent,grid_unstable,grid_stable],['Absent','Unstable','Stable'],'Grid-status index $G$')
panel(ax[1,0],'(d) Load demand',x,[load_low,load_med,load_high],['Low','Medium','High'],'Normalised load demand $L$')
panel(ax[1,1],'(e) Output: source priority',x,[p_grid,p_blend,p_solar],['Grid','Blend','Solar/Battery'],'Source priority $P$')
panel(ax[1,2],'(f) Output: tier permission',u,[t_t1,t_t12,t_all],['Tier 1 only','Tiers 1–2','All tiers'],'Tier permission $T$')
plt.tight_layout(); plt.savefig('figures/fig2_membership_hr.png'); plt.close()
# ---- Fig 4 split panels (published Table 3 values)
fig,ax=plt.subplots(1,3,figsize=(12,4.2),dpi=300); c=['#d62728','#7f7f7f']
def bars(a,vals,title,yl,fmt):
    b=a.bar(['Fuzzy','Baseline'],vals,color=['#1f77b4','#7f7f7f'],width=.55); a.set_title(title); a.set_ylabel(yl); a.grid(axis='y',alpha=.3)
    for r,v in zip(b,vals): a.text(r.get_x()+r.get_width()/2,v,fmt%v,ha='center',va='bottom',fontsize=11)
    a.set_ylim(0,max(vals)*1.18)
bars(ax[0],[100.0,91.9],'(a) Tier-1 availability','Availability (%)','%.1f')
ax[0].set_ylim(80,104)
bars(ax[1],[7.95,13.43],'(b) Grid energy drawn','Energy (kWh)','%.2f')
bars(ax[2],[2,4],'(c) Source-switching events','Number of events','%d')
ax[2].set_yticks([0,1,2,3,4])
plt.tight_layout(); plt.savefig('figures/fig4_comparison_hr.png'); plt.close()
# ---- Fig 5 Monte Carlo
R=json.load(open('results/mc_raw.json')); names=list(R); short=['Fuzzy\n(proposed)','Threshold\nATS','ATS +\ncrit. priority','Crisp tiered\nrule-based']
fig,ax=plt.subplots(1,3,figsize=(13,4.4),dpi=300)
for a,key,t,yl in zip(ax,['A1','Usol','Egrid'],['(a) Tier-1 availability','(b) Solar utilisation','(c) Grid energy drawn'],['%','%','kWh']):
    d=[[x[key] for x in R[n]] for n in names]
    bp=a.boxplot(d,tick_labels=short,patch_artist=True,showmeans=True,meanprops=dict(marker='D',markerfacecolor='k',markeredgecolor='k',markersize=4))
    for p,cc in zip(bp['boxes'],['#1f77b4','#7f7f7f','#ff7f0e','#2ca02c']): p.set_facecolor(cc); p.set_alpha(.7)
    a.set_title(t); a.set_ylabel(yl); a.grid(axis='y',alpha=.3); a.tick_params(axis='x',labelsize=9)
plt.tight_layout(); plt.savefig('figures/fig5_montecarlo.png'); plt.close()
print('ok')
