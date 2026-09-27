#!/usr/bin/env python3
"""Matched solves with additional real vertical P observations."""
from pathlib import Path
import importlib.util,json,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('robust39',DIR.parent/'07_joint_location/37_robust_cc.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
M=R.M;HERE=M.HERE;OUT=HERE/'export/42_vertical_p_observations';SRC=HERE/'export/39_support_aware_pairs';OBS=HERE/'export/35_cc_observation_selection'
R.OUT=OUT;R.C.OUT=OUT;R.C.INPUT=OUT/'inputs';M.BASE=OUT/'base'

def problem(template,auxiliary):
 p=R.problem(template,auxiliary)
 new=p.p.pick_id.str.startswith('vp42_').to_numpy()
 p.sigma[new]=np.sqrt(.3**2+.2**2)
 assert p.p.loc[new,'phase'].eq('P').all() and p.train[new].all()
 return p

def solve(job):
 p,branch,label,shift=job;file=OUT/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
 if not(file.exists() and meta.exists()):
  fun,jac=p.system(branch.startswith('joint_'),branch.endswith('_withheld'))
  x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
  fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
  np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str))
  M.save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
 else:
  with np.load(file) as a:assert np.array_equal(a['event_id'],p.e.event_id.to_numpy(str))
 row=json.loads(meta.read_text());print(row,flush=True);return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--stage',choices=['prepare','run'],default='run');args=parser.parse_args()
 checks=json.loads((OUT/'measurement_checks.json').read_text());assert checks['old_acceptance_identical']
 for source,digest in json.loads((OUT/'cc_processing/design.json').read_text())['source_sha256'].items():assert M.sha(Path(source))==digest
 assert (OUT/'inputs/events.csv').read_bytes()==(SRC/'inputs/events.csv').read_bytes()
 oldph=pd.read_csv(SRC/'inputs/all_phases.csv');newph=pd.read_csv(OUT/'inputs/all_phases.csv')
 pd.testing.assert_frame_equal(oldph,newph.iloc[:len(oldph)][oldph.columns],check_dtype=False,rtol=1e-12,atol=1e-10)
 old=pd.read_csv(OBS/'inputs/events.csv');new=pd.read_csv(OUT/'inputs/events.csv')
 a=old[old.role.eq('reserve')].sort_values('event_id').reset_index(drop=True);b=new[new.role.eq('reserve')].sort_values('event_id').reset_index(drop=True)
 pd.testing.assert_frame_equal(a,b[a.columns],check_dtype=False)
 R.ENGINE.link(OBS/'native_controls',OUT/'native_controls')
 files=[Path(__file__),DIR/'42_evaluate_vertical.py',DIR/'42_measure_vertical_cc.py',DIR.parent/'07_joint_location/_joint_validation.py',Path(R.__file__),Path(R.C.__file__),Path(M.__file__),OUT/'target_design.json',OUT/'measurement_checks.json',OUT/'cc_measurements.csv',OUT/'inputs/events.csv',OUT/'inputs/all_phases.csv',OUT/'base/stations.csv',OUT/'new_grid_checks.json']+sorted((M.BASE/'grids').glob('time.*.time.*'))
 design={'round':21,'cohort_role':'exposed_development','intervention':'Add three real vertical P instruments to the fixed stage39 event cohort. Historical observations, model, scalar P/vector S CC and Huber optimizer stay fixed. New P pick error is 0.20 s, plus original 0.30 s model error; old errors unchanged. Recompute matched absolute controls. New instruments are training-only; held measurements and target eligibility unchanged.','source_sha256':{str(p):M.sha(p) for p in files}}
 f=OUT/'location_design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 template=M.Problem();primary=problem(template,False);aux=problem(template,True)
 rng=np.random.default_rng(39);x=aux.start.copy();x[:,:3]+=.013;x=x.ravel();d=rng.normal(size=len(x));d/=np.linalg.norm(d);errors={}
 for joint in [False,True]:
  fun,jac=aux.system(joint,True);h=1e-4;err=float(np.max(abs((fun(x+h*d)-fun(x-h*d))/(2*h)-jac(x)@d)));assert err<1e-5;errors[str(joint)]=err
 M.save(OUT/'numerical_checks.json',{'directional_jacobian_error':errors,'primary_events':len(primary.e),'auxiliary_events':len(aux.e),'accepted_edges':len(primary.c),'auxiliary_edges':len(aux.c)})
 print((OUT/'numerical_checks.json').read_text(),flush=True)
 if args.stage=='prepare':return
 jobs=[]
 for branch in ['absolute_all','joint_all']:jobs.append((primary,branch,'control',(0,0,0)))
 for branch in ['absolute_withheld','joint_withheld']:
  jobs.extend((aux,branch,label,shift) for label,shift in M.SHIFTS.items())
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(solve,job) for job in jobs]):
   states.append(f.result());pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 assert len(states)==16
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
