#!/usr/bin/env python3
"""Compare calibrated-model predictions on unchanged held observations and targets."""
from pathlib import Path
import json,importlib.util
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('run49',DIR/'49_run.py');M=C.M;OUT=C.OUT
def main():
 V=load('validation49',DIR.parent/'07_joint_location/_joint_validation.py');result=V.evaluate(C,OUT,round_id=28,cohort_role='exposed_development')
 for ext in ['png','pdf']:(OUT/('confirmation.'+ext)).replace(OUT/('development_comparison.'+ext))
 template=M.Problem();candidate=C.problem(template,True);B=load('old48_for49',DIR.parent/'12_differential_augmentation/48_run.py');B.configure('refreshed');previous=B.problem(template,True)
 assert np.array_equal(candidate.p.pick_id,previous.p.pick_id) and np.array_equal(candidate.c.pick_id_a,previous.c.pick_id_a)
 sets={'fixed1524':set(zip(previous.c.loc[~previous.c.training,'pick_id_a'],previous.c.loc[~previous.c.training,'pick_id_b']))}
 for name,source in [('old575',M.HERE/'export/35_cc_observation_selection'),('fixed1408',M.HERE/'export/47_missing_s_observations')]:
  c=pd.read_csv(source/'cc_measurements.csv');c=c[c.accepted&~c.training&c.event_id_a.isin(candidate.e.event_id)&c.event_id_b.isin(candidate.e.event_id)];sets[name]=set(zip(c.pick_id_a,c.pick_id_b))
 assert [len(sets[k]) for k in ['old575','fixed1408','fixed1524']]==[575,1408,1524]
 rows=[];keys=list(zip(candidate.c.pick_id_a,candidate.c.pick_id_b))
 # Own-model comparison is physical prediction skill; cross-model controls show model/location effects.
 for label,p,file in [('stage48',previous,C.BASELINE/'joint_withheld_control.npz'),('candidate',candidate,OUT/'joint_withheld_control.npz'),('new_model_old_locations',candidate,C.BASELINE/'joint_withheld_control.npz'),('old_model_new_locations',previous,OUT/'joint_withheld_control.npz')]:
  with np.load(file) as z:assert np.array_equal(z['event_id'],p.e.event_id);x=z['x']
  tt,_=p.prediction(x.ravel());res=tt[p.a]-tt[p.b]-p.dt
  for name,kk in sets.items():
   mask=np.array([k in kk for k in keys]);assert mask.sum()==len(kk)
   for phase in ['all','P','S']:
    mm=mask if phase=='all' else mask&p.c.phase.eq(phase).to_numpy();rows.append({'observations':name,'solution':label,'phase':phase,'n':int(mm.sum()),'rms_s':float(np.sqrt(np.mean(res[mm]**2)))})
 table=pd.DataFrame(rows);table.to_csv(OUT/'fixed_observation_scores.csv',index=False);idx=table.set_index(['observations','solution','phase']).rms_s
 for name in sets:
  ratio=float(idx.loc[(name,'candidate','all')]/idx.loc[(name,'stage48','all')]);result[name+'_stage48_ratio']=ratio;result['gates'][name+'_non_degradation']=ratio<=1.05
 current=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog'])
 for label,path in [('stage48',C.BASELINE),('stage45',M.HERE/'export/45_added_station')]:
  old=pd.read_csv(path/'reference_summary.csv').set_index(['branch','catalog']);ok=all(current.loc[('joint_all',cat),'median_horizontal_km']<=1.1*old.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']) and current.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*old.loc[('joint_all','Shelly'),'median_abs_depth_km'];result['gates'][label+'_references']=bool(ok)
 e=pd.read_csv(OUT/'events.csv');target=e[e.branch.eq('joint_all')&e.role.eq('reserve')].copy();old=pd.read_csv(C.BASELINE/'events.csv').query("branch=='joint_all'").set_index('event_id');target['previous_depth_km']=target.event_id.map(old.depth_km);target['depth_change_km']=target.depth_km-target.previous_depth_km;target.to_csv(OUT/'target_changes.csv',index=False)
 result.update({'vp_vs':json.loads((C.ROOT/'calibration.json').read_text())['vp_vs'],'median_depth_change_from_stage48_km':float(target.depth_change_km.median()),'reserve3_used':False,'all_gates_passed':all(result['gates'].values())});result['decision']='development_passed_requires_fresh_confirmation' if result['all_gates_passed'] else 'do_not_promote';M.save(OUT/'run.json',result)
 (OUT/'RESULTS.md').write_text('# Calibrated Vp/Vs location results\n\nExposed development evidence; no full catalog adoption. Candidate physical predictions are scored against unchanged observations using its own model. Both cross-model controls are retained separately. Original native controls are independently recomputed using the original model.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n```text\n'+table.to_string(index=False)+'\n```\n')
 for f,h in json.loads((OUT/'location_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
