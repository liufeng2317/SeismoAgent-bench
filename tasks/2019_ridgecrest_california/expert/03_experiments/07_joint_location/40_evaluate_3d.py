#!/usr/bin/env python3
"""Compare frozen observation sets using each solution's own physical model."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('candidate40',DIR/'40_joint_3d.py');V=load('validation40',DIR/'_joint_validation.py');M=C.M;OUT=C.OUT

def main():
 result=V.evaluate(C,OUT,round_id=19,cohort_role='exposed_development')
 for ext in ['png','pdf']:(OUT/('confirmation.'+ext)).replace(OUT/('development_comparison.'+ext))
 template=M.Problem();B=load('old39',DIR/'39_run_pairs.py')
 configs=[('previous_1d_joint',B.problem(template,True),C.SRC/'joint_withheld_control.npz'),('matched_3d_background_joint',C.problem(template,True,'background'),OUT/'matched_background/joint_withheld_control.npz'),('regional_3d_joint',C.problem(template,True),OUT/'joint_withheld_control.npz')]
 old=pd.read_csv(M.HERE/'export/35_cc_observation_selection/cc_measurements.csv');old=old[old.accepted&~old.training].copy()
 eligible=set(configs[0][1].e.event_id);old=old[old.event_id_a.isin(eligible)&old.event_id_b.isin(eligible)];assert len(old)==575
 tables=[];detail=[]
 for label,p,file in configs:
  with np.load(file) as f:assert np.array_equal(f['event_id'],p.e.event_id.to_numpy(str));x=f['x']
  tt,_=p.prediction(x.ravel());index=pd.Series(np.arange(len(p.p)),index=p.p.pick_id)
  for obs,q in [('common_old_575',old),('fixed_stage39_1408',p.c[~p.c.training])]:
   a=index.loc[q.pick_id_a].to_numpy(int);b=index.loc[q.pick_id_b].to_numpy(int);dt=q.cc_arrival_difference_s.to_numpy()-(p.t0[p.ei[a]]-p.t0[p.ei[b]]);r=tt[a]-tt[b]-dt
   if obs=='fixed_stage39_1408':assert len(q)==1408
   for phase in ['all','P','S']:
    mask=np.ones(len(q),bool) if phase=='all' else q.phase.eq(phase).to_numpy();tables.append({'solution':label,'observations':obs,'phase':phase,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(r[mask]**2)))})
   d=q[['event_id_a','event_id_b','pick_id_a','pick_id_b','phase','instrument_id']].copy();d['solution']=label;d['observations']=obs;d['residual_s']=r;detail.append(d)
 scores=pd.DataFrame(tables);scores.to_csv(OUT/'physical_model_scores.csv',index=False);pd.concat(detail).to_csv(OUT/'held_cc_predictions.csv',index=False)
 # Fixed reference identities and coordinates come only from the shared evaluator.
 refs=pd.read_csv(OUT/'reference_comparison.csv');refs=refs[refs.branch.eq('joint_all')].copy();reference=[];positions=[]
 for label,folder in [('previous_1d_joint',C.SRC),('matched_3d_background_joint',OUT/'matched_background'),('regional_3d_joint',OUT)]:
  with np.load(folder/'joint_all_control.npz') as f:pos=pd.DataFrame(f['x'][:,:3],columns=M.XYZ);pos['event_id']=f['event_id']
  target_ids=set(pd.read_csv(OUT/'inputs/events.csv').query("role == 'reserve'").event_id);pos=pos[pos.event_id.isin(target_ids)].copy();assert len(pos)==300;pos['solution']=label;positions.append(pos)
  q=refs[['event_id','catalog','reference_id','rx','ry','reference_depth_km']].merge(pos,on='event_id',validate='many_to_one');q['horizontal_km']=np.hypot(q.x_km-q.rx,q.y_km-q.ry);q['abs_depth_km']=abs(q.depth_km-q.reference_depth_km)
  for cat,g in q.groupby('catalog'):reference.append({'solution':label,'catalog':cat,'n':len(g),'median_horizontal_km':float(g.horizontal_km.median()),'median_abs_depth_km':float(g.abs_depth_km.median()) if cat=='Shelly' else np.nan})
 rs=pd.DataFrame(reference);rs.to_csv(OUT/'joint_control_reference_summary.csv',index=False);pd.concat(positions).to_csv(OUT/'target_model_comparison.csv',index=False)
 idx=scores.set_index(['solution','observations','phase']).rms_s
 ratio=float(idx.loc[('regional_3d_joint','common_old_575','all')]/idx.loc[('previous_1d_joint','common_old_575','all')]);result['old_measurement_rms_ratio']=ratio;result['gates']['old_measurement_non_degradation']=ratio<=1.05
 result['gates']['physical_control_cc']=all(idx.loc[('regional_3d_joint','fixed_stage39_1408','all')]<=1.05*idx.loc[(label,'fixed_stage39_1408','all')] for label in ['previous_1d_joint','matched_3d_background_joint'])
 refidx=rs.set_index(['solution','catalog']);ok=True
 for label in ['previous_1d_joint','matched_3d_background_joint']:
  for cat in ['Liu','Official','Shelly']:ok &= bool(refidx.loc[('regional_3d_joint',cat),'median_horizontal_km']<=1.10*refidx.loc[(label,cat),'median_horizontal_km'])
  ok &= bool(refidx.loc[('regional_3d_joint','Shelly'),'median_abs_depth_km']<=1.10*refidx.loc[(label,'Shelly'),'median_abs_depth_km'])
 result['gates']['physical_control_references']=ok
 status=pd.read_csv(OUT/'matched_background/solver_status.csv');assert len(status)==4;result['gates']['matched_background_termination']=bool(status.success.all())
 result['decision']='development_passed_requires_fresh_confirmation' if all(result['gates'].values()) else 'do_not_promote';M.save(OUT/'run.json',result)
 (OUT/'RESULTS.md').write_text('# Joint 3D physical-model comparison\n\nExposed development; no independent confirmation or full adoption. Both absolute and CC terms use the same archived 3D model, with a matched 3D-background control. Fixed observation identities, errors and Huber objective are preserved. Every prediction uses the solution own mean model.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n## Identical held observations\n\n```text\n'+scores.to_string(index=False)+'\n```\n\n## Fixed reference pairs\n\n```text\n'+rs.to_string(index=False)+'\n```\n\nCoverage is known to remain below the frozen gate. Reference coordinates are not fitted. Raw model schema/depth and hybrid boundary assumptions remain limitations, and interpolation derivatives are local, not formal uncertainty estimates. Native original-model controls remain an external baseline; they are not presented as regional-model native solves. See design.json, numerical_checks.json, verified_fields.json, anchor_metrics.csv and target_model_comparison.csv.\n')
 print(json.dumps(result,indent=2),flush=True);print(scores.to_string(index=False),flush=True);print(rs.to_string(index=False),flush=True)
if __name__=='__main__':main()
