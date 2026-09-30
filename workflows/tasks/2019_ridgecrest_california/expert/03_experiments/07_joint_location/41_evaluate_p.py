#!/usr/bin/env python3
"""Disjoint-calibration P statics: fixed observation and reference comparisons."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('corrected41',DIR/'41_calibrate_p.py');V=load('validation41',DIR/'_joint_validation.py');B=load('uncorrected41',DIR/'40_joint_3d.py');OLD=load('original41',DIR/'39_run_pairs.py');M=C.M;OUT=C.OUT

def main():
 result=V.evaluate(C,OUT,round_id=20,cohort_role='exposed_development')
 for ext in ['png','pdf']:(OUT/('confirmation.'+ext)).replace(OUT/('development_comparison.'+ext))
 template=M.Problem();configs=[('previous_1d_joint',OLD.problem(template,True),OLD.OUT),('matched_3d_background_joint',B.problem(template,True,'background'),B.OUT/'matched_background'),('regional_3d_joint',B.problem(template,True),B.OUT),('corrected_regional_joint',C.problem(template,True),OUT)]
 old=pd.read_csv(M.HERE/'export/35_cc_observation_selection/cc_measurements.csv');old=old[old.accepted&~old.training];eligible=set(configs[0][1].e.event_id);old=old[old.event_id_a.isin(eligible)&old.event_id_b.isin(eligible)];assert len(old)==575
 scores=[];details=[];absolute=[]
 for label,p,folder in configs:
  with np.load(folder/'joint_withheld_control.npz') as f:assert np.array_equal(f['event_id'],p.e.event_id.to_numpy(str));x=f['x']
  tt,_=p.prediction(x.ravel());index=pd.Series(np.arange(len(p.p)),index=p.p.pick_id);targets=set(p.e[p.e.role.eq('reserve')].event_id);mask=p.p.event_id.isin(targets).to_numpy()&~p.train;residual=tt-p.obs
  for phase in ['all','P','S']:
   m=mask if phase=='all' else mask&p.p.phase.eq(phase).to_numpy();absolute.append({'solution':label,'phase':phase,'n':int(m.sum()),'rms_s':float(np.sqrt(np.mean(residual[m]**2)))})
  for obs,q in [('old_575',old),('fixed_1408',p.c[~p.c.training])]:
   a=index.loc[q.pick_id_a].to_numpy(int);b=index.loc[q.pick_id_b].to_numpy(int);dt=q.cc_arrival_difference_s.to_numpy()-(p.t0[p.ei[a]]-p.t0[p.ei[b]]);r=tt[a]-tt[b]-dt
   assert len(q)==(575 if obs=='old_575' else 1408)
   for phase in ['all','P','S']:
    m=np.ones(len(q),bool) if phase=='all' else q.phase.eq(phase).to_numpy();scores.append({'solution':label,'observations':obs,'phase':phase,'n':int(m.sum()),'rms_s':float(np.sqrt(np.mean(r[m]**2)))})
   d=q[['event_id_a','event_id_b','pick_id_a','pick_id_b','phase','instrument_id']].copy();d['solution']=label;d['observations']=obs;d['residual_s']=r;details.append(d)
 scores=pd.DataFrame(scores);absolute=pd.DataFrame(absolute);scores.to_csv(OUT/'control_cc_scores.csv',index=False);absolute.to_csv(OUT/'control_absolute_scores.csv',index=False);pd.concat(details).to_csv(OUT/'held_cc_predictions.csv',index=False)
 refs=pd.read_csv(OUT/'reference_comparison.csv');refs=refs[refs.branch.eq('joint_all')];reference=[];positions=[]
 for label,p,folder in configs:
  with np.load(folder/'joint_all_control.npz') as f:q=pd.DataFrame(f['x'][:,:3],columns=M.XYZ);q['event_id']=f['event_id']
  targets=set(p.e[p.e.role.eq('reserve')].event_id)
  # Include the 10 primary targets ineligible for omission by selecting from frozen inputs.
  full=pd.read_csv(OUT/'inputs/events.csv');targets=set(full[full.role.eq('reserve')].event_id);q=q[q.event_id.isin(targets)].copy();assert len(q)==300;q['solution']=label;positions.append(q)
  ref=refs[['event_id','catalog','reference_id','rx','ry','reference_depth_km']].merge(q,on='event_id',validate='many_to_one');ref['horizontal_km']=np.hypot(ref.x_km-ref.rx,ref.y_km-ref.ry);ref['absolute_depth_km']=abs(ref.depth_km-ref.reference_depth_km)
  for cat,g in ref.groupby('catalog'):reference.append({'solution':label,'catalog':cat,'n':len(g),'median_horizontal_km':float(g.horizontal_km.median()),'median_abs_depth_km':float(g.absolute_depth_km.median()) if cat=='Shelly' else np.nan})
 reference=pd.DataFrame(reference);reference.to_csv(OUT/'control_reference_summary.csv',index=False);positions=pd.concat(positions);positions.to_csv(OUT/'target_correction_comparison.csv',index=False)
 cc=scores.set_index(['solution','observations','phase']).rms_s;ref=reference.set_index(['solution','catalog']);absidx=absolute.set_index(['solution','phase']).rms_s;controls=[v[0] for v in configs[:-1]];new='corrected_regional_joint'
 result['gates']['old_measurement_non_degradation']=bool(cc.loc[(new,'old_575','all')]<=1.05*cc.loc[('regional_3d_joint','old_575','all')]);result['gates']['physical_control_cc']=all(cc.loc[(new,'fixed_1408','all')]<=1.05*cc.loc[(label,'fixed_1408','all')] for label in controls);result['gates']['uncorrected_held_absolute']=bool(absidx.loc[(new,'all')]<=1.05*absidx.loc[('regional_3d_joint','all')])
 ok=True
 for label in controls:
  for cat in ['Liu','Official','Shelly']:ok &= bool(ref.loc[(new,cat),'median_horizontal_km']<=1.10*ref.loc[(label,cat),'median_horizontal_km'])
  ok &= bool(ref.loc[(new,'Shelly'),'median_abs_depth_km']<=1.10*ref.loc[(label,'Shelly'),'median_abs_depth_km'])
 result['gates']['physical_control_references']=ok;result['decision']='development_passed_requires_fresh_confirmation' if all(result['gates'].values()) else 'do_not_promote'
 before=positions[positions.solution.eq('regional_3d_joint')].set_index('event_id');after=positions[positions.solution.eq(new)].set_index('event_id').loc[before.index];result['median_depth_shift_from_uncorrected_km']=float((after.depth_km-before.depth_km).median());M.save(OUT/'run.json',result)
 (OUT/'RESULTS.md').write_text('# Regional P-static correction experiment\n\nExposed development; corrections learned only from 147 events excluded from all 2,881 evaluation target/support events. No fresh confirmation or production adoption.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n## Identical held absolute arrivals\n\n```text\n'+absolute.to_string(index=False)+'\n```\n\n## Identical held CC observations\n\n```text\n'+scores.to_string(index=False)+'\n```\n\n## Fixed references\n\n```text\n'+reference.to_string(index=False)+'\n```\n\nThe station term cancels in same-station/phase differential times; any CC score change comes from the changed solution. Calibration split concordance is not evidence of physical clock errors. Zero calibration-weighted P mean does not guarantee zero depth shift on different station geometries. Earlier 1D and matched-background 3D reference/CC controls remain required, not replaced by the latest weaker depth result.\n')
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,2,figsize=(7.4,3.2),layout='constrained');coef=pd.read_csv(OUT/'p_corrections.csv');axes[0].scatter(coef.fold0_correction_s,coef.fold1_correction_s,s=18,color='#0072B2');lo=min(coef.fold0_correction_s.min(),coef.fold1_correction_s.min())-.05;hi=max(coef.fold0_correction_s.max(),coef.fold1_correction_s.max())+.05;axes[0].plot([lo,hi],[lo,hi],c='black',lw=.8);axes[0].set(xlabel='Calibration half 1 P correction (s)',ylabel='Calibration half 2 P correction (s)',xlim=(lo,hi),ylim=(lo,hi))
 axes[1].scatter(before.depth_km,after.depth_km,s=10,alpha=.6,color='#0072B2',linewidths=0);axes[1].plot([0,25],[0,25],c='black',lw=.8);axes[1].set(xlabel='Uncorrected 3D depth (km)',ylabel='P-corrected 3D depth (km)',xlim=(0,25),ylim=(0,25))
 for ax,label in zip(axes,'ab'):ax.text(0,1.03,label,transform=ax.transAxes,fontweight='bold',fontsize=12)
 fig.savefig(OUT/'station_correction_comparison.png',dpi=300);fig.savefig(OUT/'station_correction_comparison.pdf');plt.close(fig)
 print(json.dumps(result,indent=2),flush=True);print(absolute.to_string(index=False),flush=True);print(reference.to_string(index=False),flush=True)
if __name__=='__main__':main()
