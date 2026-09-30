#!/usr/bin/env python3
"""Reuse frozen joint equations; expanded CC candidates only, exposed cohort."""
from pathlib import Path
import importlib.util,json,argparse,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from scipy.optimize import least_squares
import numpy as np
import pandas as pd
spec=importlib.util.spec_from_file_location('shared34',Path(__file__).with_name('34_run_confirmation.py'));C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
M=C.M;SRC=M.HERE/'export/34_joint_confirmation';OUT=M.HERE/'export/35_cc_observation_selection';C.OUT=OUT;C.INPUT=OUT/'inputs'
problem=C.problem

def solve(job):
 p,branch,label,shift=job
 file=OUT/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
 if not(file.exists() and meta.exists()):
  fun,jac=p.system(True,branch.endswith('_withheld'));x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
  fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
  np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str));M.save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
 row=json.loads(meta.read_text());print(row,flush=True);return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();assert 1<=args.workers<=8
 for name in ['events.csv','all_phases.csv']:assert (OUT/'inputs'/name).read_bytes()==(SRC/'inputs'/name).read_bytes()
 old=pd.read_csv(SRC/'cc_measurements.csv');new=pd.read_csv(OUT/'cc_measurements.csv');keys=['pick_id_a','pick_id_b'];assert not new.duplicated(keys).any();q=old.merge(new,on=keys,suffixes=('_old','_new'),validate='one_to_one');assert len(q)==len(old);assert (q.accepted_old==q.accepted_new).all();accepted=q[q.accepted_old];err=float(np.max(abs(accepted.cc_arrival_difference_s_old-accepted.cc_arrival_difference_s_new)));assert err<1e-8
 files=[Path(__file__),Path(C.__file__),SRC/'execution_design.json',OUT/'design.json',SRC/'cc_measurements.csv',OUT/'cc_measurements.csv'];reused=[]
 for branch in ['absolute_all','absolute_withheld']:
  labels=['control'] if branch=='absolute_all' else list(M.SHIFTS)
  for label in labels:
   for suffix in ['npz','json']:
    name=branch+'_'+label+'.'+suffix;source=SRC/name;dest=OUT/name;files.append(source)
    if not dest.exists():dest.symlink_to(source)
    assert dest.resolve()==source.resolve()
   reused.append(branch+'_'+label)
 dest=OUT/'native_controls'
 if not dest.exists():dest.symlink_to(SRC/'native_controls',target_is_directory=True)
 assert dest.resolve()==(SRC/'native_controls').resolve()
 design={'round':14,'cohort_role':'Development after failed confirmation, not a fresh reserve.','only_intervention':'Remove absolute-model residual filtering of CC candidates.','reused_absolute_controls':reused,'old_edges_identical_acceptance':len(q),'old_accepted_difference_max_s':err,'source_sha256':{str(f):M.sha(f) for f in files}}
 p=OUT/'reuse_checks.json'
 if p.exists():assert json.loads(p.read_text())==design
 else:M.save(p,design)
 original_argv=sys.argv;sys.argv=[original_argv[0],'--stage','prepare']
 try:C.main()
 finally:sys.argv=original_argv
 if args.stage=='prepare':return
 # Only scheduling changes: immutable inputs/equations and solver options match stage34.
 template=M.Problem();primary=C.problem(template,False);aux=C.problem(template,True)
 jobs=[(primary,'joint_all','control',(0,0,0))]+[(aux,'joint_withheld',label,shift) for label,shift in M.SHIFTS.items()]
 states=[json.loads((OUT/(name+'.json')).read_text()) for name in reused]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  futures=[pool.submit(solve,job) for job in jobs]
  for future in as_completed(futures):states.append(future.result())
 assert len(states)==16
 pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 for source_design in [design,json.loads((OUT/'execution_design.json').read_text())]:
  for f,h in source_design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
