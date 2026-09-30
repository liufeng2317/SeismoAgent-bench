#!/usr/bin/env python3
"""Evaluate model-sensitivity errors on identical exposed observations."""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('model_error36',DIR/'36_model_error.py');V=load('validation36',DIR/'_joint_validation.py');M=C.M;OUT=C.OUT

def main():
 result=V.evaluate(C,OUT,round_id=15,cohort_role='exposed_development')
 for suffix in ['png','pdf']:(OUT/('confirmation.'+suffix)).replace(OUT/('development_comparison.'+suffix))
 p=C.problem(M.Problem(),True);held=~p.c.training.to_numpy();rows=[]
 for label,source in [('absolute',OUT/'absolute_withheld_control.npz'),('fixed_cc_error',C.SRC/'joint_withheld_control.npz'),('model_sensitivity_error',OUT/'joint_withheld_control.npz')]:
  f=np.load(source);assert np.array_equal(f['event_id'],p.e.event_id.to_numpy());tt,_=p.prediction(f['x'].ravel());res=tt[p.a]-tt[p.b]-p.dt
  rows.append({'method':label,'n_identical_held_CC':int(held.sum()),'rms_s':float(np.sqrt(np.mean(res[held]**2)))})
 pd.DataFrame(rows).to_csv(OUT/'same_observations.csv',index=False)
 events=pd.read_csv(OUT/'events.csv');current=events[events.branch.eq('joint_all')&events.role.eq('reserve')].copy();previous=pd.read_csv(C.SRC/'events.csv');previous=previous[previous.branch.eq('joint_all')].set_index('event_id');base=pd.read_csv(OUT/'inputs/events.csv').set_index('event_id');current['previous_joint_depth_km']=current.event_id.map(previous.depth_km);current['original_depth_km']=current.event_id.map(base.depth_km);current['near_boundary']=current.depth_km.lt(.5)|current.depth_km.gt(24.5);current.to_csv(OUT/'target_depth_changes.csv',index=False)
 report=OUT/'RESULTS.md';report.write_text(report.read_text()+'\n\n## Same-observation model-error comparison\n\n```text\n'+pd.DataFrame(rows).to_string(index=False)+'\n```\n\nThe working CC error includes an envelope of two archived physical-model contrasts at original locations. It is a sensitivity prescription, not an estimated standard deviation. Mean travel times and all observations are unchanged. Source-model/datum caveats and shared-edge correlations remain. The 190-event training coverage is unchanged and still fails the predeclared 210 requirement regardless of depth results.\n')
 print(pd.DataFrame(rows).to_string(index=False),flush=True)
if __name__=='__main__':main()
