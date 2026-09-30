#!/usr/bin/env python3
"""Score all old held measurements, even when the new S estimator rejects them."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('vector38',DIR/'39_run_pairs.py');V=load('validation38',DIR/'_joint_validation.py');M=C.M;OUT=C.OUT

def main():
 result=V.evaluate(C,OUT,round_id=18,cohort_role='exposed_development')
 for suffix in ['png','pdf']:(OUT/('confirmation.'+suffix)).replace(OUT/('development_comparison.'+suffix))
 template=M.Problem();new=C.problem(template,True);B=load('oldobs38',DIR/'34_run_confirmation.py');B.OUT=C.OBS;B.INPUT=C.OBS/'inputs';old=B.problem(template,True);rows=[];details=[]
 for obs,p in [('all_old_measurements',old),('new_measurements',new)]:
  held=~p.c.training.to_numpy()
  if obs=='all_old_measurements':assert held.sum()==575
  for label,file in [('absolute',OUT/'absolute_withheld_control.npz'),('previous_vector_S',C.SRC/'joint_withheld_control.npz'),('augmented_graph',OUT/'joint_withheld_control.npz')]:
   if obs=='new_measurements' and label=='previous_vector_S':continue
   with np.load(file) as f:
    indices=pd.Index(f['event_id']).get_indexer(p.e.event_id);assert (indices>=0).all();x=f['x'][indices]
   tt,_=p.prediction(x.ravel());r=tt[p.a]-tt[p.b]-p.dt
   for phase in ['all','P','S']:
    mask=held if phase=='all' else held&p.c.phase.eq(phase).to_numpy();rows.append({'observations':obs,'solution':label,'phase':phase,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(r[mask]**2)))})
   q=p.c.loc[held,['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase']].copy();q['observations']=obs;q['solution']=label;q['residual_s']=r[held];details.append(q)
 table=pd.DataFrame(rows);table.to_csv(OUT/'old_and_new_observation_scores.csv',index=False);pd.concat(details).to_csv(OUT/'held_cc_predictions.csv',index=False)
 idx=table.set_index(['observations','solution','phase']).rms_s;ratio=float(idx.loc[('all_old_measurements','augmented_graph','all')]/idx.loc[('all_old_measurements','previous_vector_S','all')]);result['old_measurement_rms_ratio']=ratio;result['gates']['old_measurement_non_degradation']=ratio<=1.05;result['decision']='development_passed_requires_fresh_confirmation' if all(result['gates'].values()) else 'do_not_promote';M.save(OUT/'run.json',result)
 e=pd.read_csv(OUT/'events.csv');targets=e[e.branch.eq('joint_all')&e.role.eq('reserve')].copy();prev=pd.read_csv(C.SRC/'events.csv');prev=prev[prev.branch.eq('joint_all')].set_index('event_id');targets['previous_depth_km']=targets.event_id.map(prev.depth_km);targets.to_csv(OUT/'target_depth_changes.csv',index=False)
 (OUT/'RESULTS.md').write_text('# Support-aware graph augmentation: exposed development\n\nDecision: **'+result['decision']+'**. This is not independent confirmation. All targets and fixed gates remain.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n## Identical and new observations\n\n```text\n'+table.to_string(index=False)+'\n```\n\nAll 575 historical held measurements are scored with event-ID-aligned coordinates, including observations rejected by the vector-S estimator. The old-set RMS must remain <=1.05 times the previous vector-S solution. New held observations are scored against matched absolute controls on the enlarged cohort; the previous solution lacks new support events and is not scored on that enlarged domain. The original model, measurement rules, 50 ms error and CC Huber loss remain fixed. See reference_summary.csv, anchor_metrics.csv, reserve_status.csv and target_depth_changes.csv for other checks. No full product is adopted.\n')
 print(json.dumps(result,indent=2),flush=True);print(table.to_string(index=False),flush=True)
if __name__=='__main__':main()
