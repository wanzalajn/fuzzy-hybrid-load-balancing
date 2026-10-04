import json
R=json.load(open('results/results.json')); names=list(R['nominal'])
f=lambda v,d=1: f"{v:.{d}f}"
rows=[('Tier-1 availability (\\%)','A1',1),('Tier-2 served (\\%)','A2',1),('Tier-3 served (\\%)','A3',1),('Total unserved energy (kWh)','Utot',2),
 ('Crit.-weighted unserved energy (weighted kWh)','CWUE_main',2),('Priority-reliability index PRI (\\%)','PRI_main',1),('Complete blackout (min)','blackout_min',0),
 ('Solar utilisation (\\%)','Usol',1),('Grid energy drawn (kWh)','Egrid',2),('Source-switching events','switch',0),('Minimum SOC (\\%)','minSOC',1)]
open('results/tab_nominal.tex','w').write('\n'.join(lab+' & '+' & '.join(f(R['nominal'][n][k],d) for n in names)+' \\\\' for lab,k,d in rows))
open('results/tab_stress.tex','w').write('\n'.join(s.replace('%','\\%')+' & '+' & '.join(f(v[n]['A1']) for n in names)+' & '+' & '.join(f(v[n]['PRI_main']) for n in names)+' & '+f(v[names[0]]['Usol'],0)+'/'+f(v[names[1]]['Usol'],0)+' \\\\' for s,v in R['stress'].items()))
mc=[lab+' & '+' & '.join(f"{R['mc'][n][k][0]:.{d}f}$\\pm${R['mc'][n][k][1]:.{d}f}" for n in names)+' \\\\' for lab,k,d in [('Tier-1 availability (\\%)','A1',1),('Priority-reliability index PRI (\\%)','PRI_main',1),('Complete blackout (min)','blackout_min',0),('Solar utilisation (\\%)','Usol',1),('Grid energy drawn (kWh)','Egrid',2),('Tier-3 served (\\%)','A3',1),('Source-switching events','switch',1)]]
mc.append('Runs with full Tier-1 service (\\%) & '+' & '.join(f(R['mc'][n]['frac_T1_full'],0) for n in names)+' \\\\')
mc.append('Runs with any Tier-1 blackout (\\%) & '+' & '.join(f(R['mc'][n]['frac_blackout'],0) for n in names)+' \\\\')
open('results/tab_mc.tex','w').write('\n'.join(mc))
print(open('results/tab_nominal.tex').read()); print(open('results/tab_stress.tex').read()); print(open('results/tab_mc.tex').read()); print(R['mc_win'])
