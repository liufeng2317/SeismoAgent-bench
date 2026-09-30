#!/usr/bin/env python3
"""Keep all historical held measurements even when they are not current fit edges."""
from pathlib import Path
import json,importlib.util
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('run50',DIR/'50_run.py');M=C.M;OUT=C.OUT
def main():
 V=load('validation50',DIR.parent/'07_joint_location/_joint_validation.py');result=V.evaluate(C,OUT,round_id=29,cohort_role='exposed_development')
 for ext in ['png','pdf']:(OUT/('confirmation.'+ext)).replace(OUT/('development_comparison.'+ext))
 B=load('baseline48for50',DIR.parent/'12_differential_augmentation/48_run.py');B.configure('refreshed');template=B.M.Problem();old=B.problem(template,True);pick_index=pd.Series(np.arange(len(old.p)),index=old.p.pick_id)
 sets={}
 for name,path,n in [('old575',M.HERE/'export/35_cc_observation_selection',575),('fixed1408',M.HERE/'export/47_missing_s_observations',1408),('fixed1524',C.BASELINE,1524)]:
  cc=pd.read_csv(path/'cc_measurements.csv');cc=cc[cc.accepted&~cc.training&cc.event_id_a.isin(old.e.event_id)&cc.event_id_b.isin(old.e.event_id)];assert len(cc)==n;sets[name]=cc
 rows=[]
 for label,file in [('stage48',C.BASELINE/'joint_withheld_control.npz'),('candidate',OUT/'joint_withheld_control.npz'),('matched_absolute',OUT/'absolute_withheld_control.npz')]:
  with np.load(file) as z:ix=pd.Index(z['event_id']).get_indexer(old.e.event_id);assert (ix>=0).all();x=z['x'][ix]
  tt,_=old.prediction(x.ravel())
  for name,cc in sets.items():
   aa=cc.pick_id_a.map(pick_index);bb=cc.pick_id_b.map(pick_index);assert aa.notna().all() and bb.notna().all();aa=aa.to_numpy(int);bb=bb.to_numpy(int);dt=cc.cc_arrival_difference_s.to_numpy()-(old.t0[old.ei[aa]]-old.t0[old.ei[bb]]);res=tt[aa]-tt[bb]-dt
   for phase in ['all','P','S']:
    mask=np.ones(len(cc),bool) if phase=='all' else cc.phase.eq(phase).to_numpy();rows.append({'observations':name,'solution':label,'phase':phase,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(res[mask]**2)))})
 table=pd.DataFrame(rows);table.to_csv(OUT/'fixed_observation_scores.csv',index=False);idx=table.set_index(['observations','solution','phase']).rms_s
 for name in sets:
  ratio=float(idx.loc[(name,'candidate','all')]/idx.loc[(name,'stage48','all')]);result[name+'_stage48_ratio']=ratio;result['gates'][name+'_non_degradation']=ratio<=1.05
 current=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog'])
 for label,path in [('stage48',C.BASELINE),('stage45',M.HERE/'export/45_added_station')]:
  ref=pd.read_csv(path/'reference_summary.csv').set_index(['branch','catalog']);ok=all(current.loc[('joint_all',cat),'median_horizontal_km']<=1.1*ref.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']) and current.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*ref.loc[('joint_all','Shelly'),'median_abs_depth_km'];result['gates'][label+'_references']=bool(ok)
 e=pd.read_csv(OUT/'events.csv');target=e[e.branch.eq('joint_all')&e.role.eq('reserve')].copy();ref=pd.read_csv(C.BASELINE/'events.csv').query("branch=='joint_all'").set_index('event_id');target['previous_depth_km']=target.event_id.map(ref.depth_km);target['depth_change_km']=target.depth_km-target.previous_depth_km;target.to_csv(OUT/'target_changes.csv',index=False)
 result.update({'median_depth_change_from_stage48_km':float(target.depth_change_km.median()),'reserve3_used':False,'all_gates_passed':all(result['gates'].values())});result['decision']='development_passed_requires_fresh_confirmation' if result['all_gates_passed'] else 'do_not_promote';M.save(OUT/'run.json',result)
 (OUT/'RESULTS.md').write_text('# Depth-uncertainty-aware event pairing\n\nExposed development, not fresh confirmation or a new full catalog. Every old target, observation and gate remains. Moment envelopes only nominate waveform candidates; they do not establish actual hypocentral proximity. No model or uncertainty posterior is recalibrated.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n```text\n'+table.to_string(index=False)+'\n```\n')
 for f,h in json.loads((OUT/'location_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
