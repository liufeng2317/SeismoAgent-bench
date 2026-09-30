#!/usr/bin/env python3
"""Same-observation scoring and influence audit for the fixed CC Huber trial."""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('robust37',DIR/'37_robust_cc.py');V=load('validation37',DIR/'_joint_validation.py');M=C.M;OUT=C.OUT

def main():
 V.evaluate(C,OUT,round_id=16,cohort_role='exposed_development')
 for suffix in ['png','pdf']:(OUT/('confirmation.'+suffix)).replace(OUT/('development_comparison.'+suffix))
 template=M.Problem();p=C.problem(template,True);held=~p.c.training.to_numpy();rows=[]
 for label,file in [('absolute',OUT/'absolute_withheld_control.npz'),('quadratic_cc',C.SRC/'joint_withheld_control.npz'),('huber_cc',OUT/'joint_withheld_control.npz')]:
  f=np.load(file);assert np.array_equal(f['event_id'],p.e.event_id.to_numpy());tt,_=p.prediction(f['x'].ravel());r=tt[p.a]-tt[p.b]-p.dt;rows.append({'method':label,'n_held_CC':int(held.sum()),'rms_s':float(np.sqrt(np.mean(r[held]**2)))})
 pd.DataFrame(rows).to_csv(OUT/'same_observations.csv',index=False)
 p=C.problem(template,False);file=np.load(OUT/'joint_all_control.npz');tt,_=p.prediction(file['x'].ravel());r=(tt[p.a]-tt[p.b]-p.dt)/.05;q=p.c.copy();q['standardized_residual']=r;q['huber_influence_ratio']=np.minimum(1.,C.DELTA/np.maximum(abs(r),1e-30));q.to_csv(OUT/'cc_influence.csv',index=False)
 events=pd.read_csv(OUT/'events.csv');targets=events[events.branch.eq('joint_all')&events.role.eq('reserve')].copy();previous=pd.read_csv(C.SRC/'events.csv');previous=previous[previous.branch.eq('joint_all')].set_index('event_id');targets['previous_joint_depth_km']=targets.event_id.map(previous.depth_km);targets['near_boundary']=targets.depth_km.lt(.5)|targets.depth_km.gt(24.5);targets.to_csv(OUT/'target_depth_changes.csv',index=False)
 report=OUT/'RESULTS.md';report.write_text(report.read_text()+'\n\n## Identical CC observations and influence\n\n```text\n'+pd.DataFrame(rows).to_string(index=False)+'\n```\n\nThe CC loss alone changes; delta=1.345 and the working error stays 0.05 s. Absolute errors and mean model remain unchanged. '+str(int(q.huber_influence_ratio.lt(1).sum()))+' of '+str(len(q))+' primary CC edges have reduced residual influence at the final solution. A small final residual does not establish a reliable phase association or constrain all spatial directions. Coverage remains 190/300 and blocks promotion. No threshold scan follows.\n')
 print(pd.DataFrame(rows).to_string(index=False),flush=True);print(targets[targets.event_id.eq('gamma_0007386')][['event_id','previous_joint_depth_km','depth_km']].to_string(index=False),flush=True)
if __name__=='__main__':main()
