#!/usr/bin/env python3
"""Score expanded CC on old common and expanded sets; exposed development only."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=load('selection35',DIR/'35_run_selection.py');V=load('joint_validation35',DIR/'_joint_validation.py');M=C.M;OUT=C.OUT;OLD=C.SRC

def main():
 frozen=json.loads((OUT/'evaluation_design.json').read_text())
 for path,digest in frozen['source_sha256'].items():assert M.sha(Path(path))==digest
 result=V.evaluate(C,OUT,round_id=14,cohort_role='exposed_development')
 for suffix in ['png','pdf']:
  (OUT/('confirmation.'+suffix)).replace(OUT/('development_comparison.'+suffix))
 p=C.problem(M.Problem(),True);oldcc=pd.read_csv(OLD/'cc_measurements.csv');oldcc=oldcc[oldcc.accepted&~oldcc.training];oldkeys=set(zip(oldcc.pick_id_a,oldcc.pick_id_b));keys=list(zip(p.c.pick_id_a,p.c.pick_id_b));common=np.array([key in oldkeys for key in keys])&~p.c.training.to_numpy();expanded=~p.c.training.to_numpy();assert common.sum()==526
 rows=[];detail=[]
 for branch,path in [('absolute',OUT/'absolute_withheld_control.npz'),('previous_joint',OLD/'joint_withheld_control.npz'),('expanded_joint',OUT/'joint_withheld_control.npz')]:
  f=np.load(path);assert np.array_equal(f['event_id'],p.e.event_id.to_numpy());tt,_=p.prediction(f['x'].ravel());residual=tt[p.a]-tt[p.b]-p.dt
  for label,mask in [('old_common',common),('expanded',expanded),('new_only',expanded&~common)]:
   rows.append({'branch':branch,'scoring_set':label,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(residual[mask]**2))) if mask.any() else None})
  q=p.c.loc[expanded,['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase']].copy();q['branch']=branch;q['residual_s']=residual[expanded];q['in_old_common']=common[expanded];detail.append(q)
 table=pd.DataFrame(rows);table.to_csv(OUT/'common_cc_comparison.csv',index=False);pd.concat(detail).to_csv(OUT/'held_cc_predictions.csv',index=False)
 (OUT/'RESULTS.md').write_text((OUT/'RESULTS.md').read_text()+'\n\n## Identical-observation comparison\n\n```text\n'+table.to_string(index=False)+'\n```\n\nOld common edges are identical measurements with unchanged acceptance, independently verified before fitting. Both joint solutions are also scored on the expanded set; new observations must not be confused with improvement on the original set. This exposed cohort cannot establish independent confirmation.\n')
 print(table.to_string(index=False),flush=True)
if __name__=='__main__':main()
