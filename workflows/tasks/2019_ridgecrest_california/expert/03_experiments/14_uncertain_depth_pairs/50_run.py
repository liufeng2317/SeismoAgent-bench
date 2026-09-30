#!/usr/bin/env python3
"""Use the unchanged stage48 objective on the uncertainty-screened graph."""
from pathlib import Path
import importlib.util,json,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('engine48for50',DIR.parent/'12_differential_augmentation/48_run.py');M=C.M;HERE=M.HERE;OUT=HERE/'export/50_uncertain_depth_pairs';BASELINE=HERE/'export/48_differential_augmentation/refreshed'
C.OUT=OUT;C.R.C.OUT=OUT;C.R.C.INPUT=OUT/'inputs'
def problem(template,auxiliary):return C.problem(template,auxiliary)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);args=ap.parse_args()
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 olde=pd.read_csv(BASELINE/'inputs/events.csv');e=pd.read_csv(OUT/'inputs/events.csv');pd.testing.assert_frame_equal(olde,e.iloc[:len(olde)][olde.columns],check_dtype=False)
 for name in ['inputs/all_phases.csv','cc_measurements.csv']:
  a=pd.read_csv(BASELINE/name,low_memory=False);b=pd.read_csv(OUT/name,low_memory=False);pd.testing.assert_frame_equal(a,b.iloc[:len(a)][a.columns],check_dtype=False,rtol=1e-12,atol=1e-10)
 assert not set(e.event_id)&set(pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv').event_id)
 files=[Path(__file__),DIR/'50_evaluate.py',OUT/'design.json',OUT/'cc_processing/design.json',Path(C.__file__),Path(C.R.C.__file__),Path(C.R.__file__),Path(M.__file__),DIR.parent/'07_joint_location/_joint_validation.py',OUT/'inputs/events.csv',OUT/'inputs/all_phases.csv',OUT/'cc_measurements.csv',M.BASE/'stations.csv']+list((M.BASE/'grids').glob('time.*.time.*'))
 design={'round':29,'method':'Unchanged stage48 model, quadratic original absolute rows, differential-only EQ S, Huber CC delta1.345 and CCsigma0.05s. New observation-support graph only.16 matched solves with fixed bounds/start tests.','source_sha256':{str(f):M.sha(f) for f in files}}
 dest=OUT/'location_design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 template=M.Problem();primary=problem(template,False);aux=problem(template,True);u=primary.p[['pick_id','event_id','phase','instrument_id']].copy();u['absolute_used']=primary.absolute_used;u.to_csv(OUT/'observation_usage.csv',index=False)
 rng=np.random.default_rng(50);x=aux.start.copy();x[:,:3]+=.013;x=x.ravel();d=rng.normal(size=len(x));d/=np.linalg.norm(d);errors={}
 for joint in [False,True]:
  f,j=aux.system(joint,True);h=1e-4;err=float(np.max(abs((f(x+h*d)-f(x-h*d))/(2*h)-j(x)@d)));assert err<1e-5;errors[str(joint)]=err
 M.save(OUT/'numerical_checks.json',{'directional_jacobian_error':errors,'primary_events':len(primary.e),'auxiliary_events':len(aux.e),'absolute_rows':int(primary.absolute_used.sum()),'relative_only_rows':int((~primary.absolute_used).sum()),'accepted_edges':len(primary.c),'old_inputs_preserved':True,'reserve3_used':False});print((OUT/'numerical_checks.json').read_text(),flush=True)
 jobs=[(primary,b,'control',(0,0,0)) for b in ['absolute_all','joint_all']]
 for branch in ['absolute_withheld','joint_withheld']:jobs.extend((aux,branch,label,shift) for label,shift in M.SHIFTS.items())
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for future in as_completed([pool.submit(C.solve,j) for j in jobs]):states.append(future.result());pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 assert len(states)==16
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
