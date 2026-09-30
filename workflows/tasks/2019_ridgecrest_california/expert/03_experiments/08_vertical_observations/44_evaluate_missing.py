#!/usr/bin/env python3
"""Score fixed old observations and targets after adding vertical P data."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('run42',DIR/'44_run_missing.py');M=C.M;OUT=C.OUT
V=load('validation42',DIR.parent/'07_joint_location/_joint_validation.py')
def main():
 result=V.evaluate(C,OUT,round_id=23,cohort_role='exposed_development')
 for suffix in ['png','pdf']:(OUT/('confirmation.'+suffix)).replace(OUT/('development_comparison.'+suffix))
 template=M.Problem();rows=[];details=[]
 for name,source,expected in [('old575',C.OBS,575),('fixed1408',C.SRC,1408)]:
  B=load('old_'+name,DIR.parent/'07_joint_location/34_run_confirmation.py');B.OUT=source;B.INPUT=source/'inputs';B.M.BASE=M.BASE;p=B.problem(template,True);held=~p.c.training.to_numpy();assert held.sum()==expected
  for label,file in [('previous',C.SRC/'joint_withheld_control.npz'),('missing_P',OUT/'joint_withheld_control.npz'),('matched_absolute',OUT/'absolute_withheld_control.npz')]:
   with np.load(file) as f:
    indices=pd.Index(f['event_id']).get_indexer(p.e.event_id);assert (indices>=0).all();x=f['x'][indices]
   tt,_=p.prediction(x.ravel());residual=tt[p.a]-tt[p.b]-p.dt
   for phase in ['all','P','S']:
    mask=held if phase=='all' else held&p.c.phase.eq(phase).to_numpy();rows.append(dict(observations=name,solution=label,phase=phase,n=int(mask.sum()),rms_s=float(np.sqrt(np.mean(residual[mask]**2)))))
   q=p.c.loc[held,['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase']].copy();q['observations']=name;q['solution']=label;q['residual_s']=residual[held];details.append(q)
 table=pd.DataFrame(rows);table.to_csv(OUT/'fixed_observation_scores.csv',index=False);pd.concat(details).to_csv(OUT/'held_cc_predictions.csv',index=False);idx=table.set_index(['observations','solution','phase']).rms_s
 for name in ['old575','fixed1408']:
  ratio=float(idx.loc[(name,'missing_P','all')]/idx.loc[(name,'previous','all')]);result[name+'_rms_ratio']=ratio;result['gates'][name+'_non_degradation']=ratio<=1.05
 old=pd.read_csv(C.SRC/'reference_summary.csv').set_index(['branch','catalog']);new=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog']);refok=True
 for cat in ['Liu','Official','Shelly']:refok &= bool(new.loc[('joint_all',cat),'median_horizontal_km']<=1.1*old.loc[('joint_all',cat),'median_horizontal_km'])
 refok &= bool(new.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*old.loc[('joint_all','Shelly'),'median_abs_depth_km']);result['gates']['previous_reference_non_degradation']=refok
 historical=pd.read_csv(M.HERE/'export/39_support_aware_pairs/reference_summary.csv').set_index(['branch','catalog']);historical_ok=all(new.loc[('joint_all',cat),'median_horizontal_km']<=1.1*historical.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']) and new.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*historical.loc[('joint_all','Shelly'),'median_abs_depth_km'];result['gates']['stage39_reference_non_degradation']=bool(historical_ok)
 p=C.problem(template,True);oldcc=pd.read_csv(C.SRC/'cc_measurements.csv');oldcc=oldcc[oldcc.event_id_a.isin(p.e.event_id)&oldcc.event_id_b.isin(p.e.event_id)];assert set(p.c.loc[~p.c.training,'pick_id_a']+'|'+p.c.loc[~p.c.training,'pick_id_b'])==set(oldcc.loc[oldcc.accepted&~oldcc.training,'pick_id_a']+'|'+oldcc.loc[oldcc.accepted&~oldcc.training,'pick_id_b'])
 events=pd.read_csv(OUT/'events.csv');targets=events[events.branch.eq('joint_all')&events.role.eq('reserve')].copy();previous=pd.read_csv(C.SRC/'events.csv');previous=previous[previous.branch.eq('joint_all')].set_index('event_id');targets['previous_depth_km']=targets.event_id.map(previous.depth_km);targets['depth_change_km']=targets.depth_km-targets.previous_depth_km
 picks=pd.read_csv(OUT/'new_picks.csv');targets['new_P_stations']=targets.event_id.map(picks.groupby('event_id').instrument_id.nunique()).fillna(0).astype(int);targets.to_csv(OUT/'target_changes.csv',index=False)
 result['new_observations']=json.loads((OUT/'extraction_summary.json').read_text());result['new_cc']=json.loads((OUT/'measurement_checks.json').read_text());result['targets_with_new_P']=int(targets.new_P_stations.gt(0).sum());result['median_depth_change_km']=float(targets.depth_change_km.median());result['decision']='development_passed_requires_fresh_confirmation' if all(result['gates'].values()) else 'do_not_promote';M.save(OUT/'run.json',result)
 (OUT/'RESULTS.md').write_text('# Direct missing P observations: exposed development\n\nDecision: **'+result['decision']+'**. Conditional single-component picks add observations to existing events; they are not independent detections or a published-catalog reproduction. No full catalog is adopted.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n## Fixed held measurements\n\n```text\n'+table.to_string(index=False)+'\n```\n\nAll original targets, auxiliary eligibility, held stations and old CC observations remain fixed. New direct picks use training instruments only. Nominal reference depth differences are not ground-truth depth errors. See reference_summary.csv, target_changes.csv and anchor_metrics.csv. Both previous confirmation cohorts are exposed; any passing development result still needs genuinely fresh confirmation.\n')
 # Compact comparison with explicit baseline/candidate labels.
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,3,figsize=(10,3.2),layout='constrained')
 oldmetrics=pd.read_csv(C.SRC/'metrics.csv').set_index(['branch','kind']);newmetrics=pd.read_csv(OUT/'metrics.csv').set_index(['branch','kind'])
 baseline=[oldmetrics.loc[('joint_withheld','absolute'),'rms_s']]+[idx.loc[(name,'previous','all')] for name in ['old575','fixed1408']]
 candidate=[newmetrics.loc[('joint_withheld','absolute'),'rms_s']]+[idx.loc[(name,'missing_P','all')] for name in ['old575','fixed1408']]
 xx=np.arange(3)
 for ax,aa,bb,labels,ylabel in [(axes[0],baseline,candidate,['Arrivals','CC 575','CC 1408'],'Held-out RMS (s)'),(axes[1],[old.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']],[new.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']],['Liu','Official','Shelly'],'Median horizontal difference (km)')]:
  ax.bar(xx-.18,aa,.36,color='#666666',label='Baseline');ax.bar(xx+.18,bb,.36,color='#0072B2',label='Missing-P completion');ax.set_xticks(xx);ax.set_xticklabels(labels);ax.set_ylabel(ylabel)
 axes[0].set_yscale('log');axes[0].legend(frameon=False,fontsize=8)
 maximum=max(1,int(targets.new_P_stations.max()));scatter=axes[2].scatter(targets.previous_depth_km,targets.depth_km,c=targets.new_P_stations,cmap='viridis',vmin=0,vmax=maximum,s=12,alpha=.7);axes[2].plot([0,25],[0,25],color='black',lw=.8);axes[2].set(xlabel='Baseline depth (km)',ylabel='Missing-P completion depth (km)',xlim=(0,25),ylim=(0,25));fig.colorbar(scatter,ax=axes[2],label='Added P stations',ticks=np.unique(np.linspace(0,maximum,4).round().astype(int)))
 for ax,letter in zip(axes,'abc'):ax.text(0,1.03,letter,transform=ax.transAxes,fontweight='bold',fontsize=12)
 for suffix in ['png','pdf']:fig.savefig(OUT/('missing_p_comparison.'+suffix),dpi=220)
 plt.close(fig)
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
