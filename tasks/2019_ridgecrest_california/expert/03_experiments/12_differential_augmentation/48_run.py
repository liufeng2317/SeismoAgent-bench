#!/usr/bin/env python3
"""Differential-only EQ S; unchanged old absolute observations and robust CC objective."""
from pathlib import Path
import argparse,importlib.util,json,types
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=load('robust48',DIR.parent/'07_joint_location/37_robust_cc.py');M=R.M;HERE=M.HERE;ROOT=HERE/'export/48_differential_augmentation';SRC=HERE/'export/47_missing_s_observations';BASELINE=HERE/'export/45_added_station';OBS=HERE/'export/35_cc_observation_selection';OUT=ROOT/'refreshed'
def configure(branch):
 global OUT
 OUT=ROOT/branch;R.C.OUT=OUT;R.C.INPUT=OUT/'inputs';M.BASE=BASELINE/'base'
configure('refreshed')
def problem(template,auxiliary):
 p=R.C.problem(template,auxiliary);dpp=p.p.pick_id.str.startswith(('vp42_','mp44_')).to_numpy();p.sigma[dpp]=np.sqrt(.3**2+.2**2)
 eq=p.p.pick_id.str.startswith('eqs47_').to_numpy();assert p.p.loc[eq,'phase'].eq('S').all() and p.train[eq].all();p.absolute_used=~eq
 def system(self,joint,withheld):
  fun,jac=M.Problem.system(self,joint,withheld);scope=self.train if withheld else np.ones(len(self.p),bool);old_n=int(scope.sum());absolute=np.flatnonzero(self.absolute_used[scope]);ncc=int(self.c.training.sum()) if withheld else len(self.c);ncc=ncc if joint else 0;keep=np.r_[absolute,np.arange(old_n,old_n+ncc)]
  def f(x):return R.transform(fun(x)[keep],len(absolute))[0]
  def j(x):return jac(x)[keep].multiply(R.transform(fun(x)[keep],len(absolute))[1][:,None]).tocsr()
  return f,j
 p.system=types.MethodType(system,p);return p

def solve(job):
 p,branch,label,shift=job;file=OUT/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
 if not(file.exists() and meta.exists()):
  fun,jac=p.system(branch.startswith('joint_'),branch.endswith('_withheld'));x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
  fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
  np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str));M.save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
 else:
  with np.load(file) as f:assert np.array_equal(f['event_id'],p.e.event_id.to_numpy(str))
 row=json.loads(meta.read_text());print(row,flush=True);return row

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--branch',choices=['fixed','refreshed'],default='refreshed');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--stage',choices=['prepare','run'],default='run');args=ap.parse_args();configure(args.branch)
 for path,h in json.loads((ROOT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(path))==h
 olde=pd.read_csv(SRC/'inputs/events.csv');newe=pd.read_csv(OUT/'inputs/events.csv');pd.testing.assert_frame_equal(olde.sort_values('event_id').reset_index(drop=True),newe[newe.event_id.isin(olde.event_id)][olde.columns].sort_values('event_id').reset_index(drop=True),check_dtype=False)
 oldp=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);newp=pd.read_csv(OUT/'inputs/all_phases.csv',low_memory=False);pd.testing.assert_frame_equal(oldp,newp.iloc[:len(oldp)][oldp.columns],check_dtype=False,rtol=1e-12,atol=1e-10)
 oldc=pd.read_csv(SRC/'cc_measurements.csv');newc=pd.read_csv(OUT/'cc_measurements.csv');pd.testing.assert_frame_equal(oldc,newc.iloc[:len(oldc)][oldc.columns],check_dtype=False,rtol=1e-12,atol=1e-10)
 reserve=set(pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv').event_id);assert not set(newe.event_id)&reserve
 files=[Path(__file__),DIR/'48_evaluate.py',ROOT/'design.json',Path(R.__file__),Path(R.C.__file__),Path(M.__file__),OUT/'inputs/events.csv',OUT/'inputs/all_phases.csv',OUT/'cc_measurements.csv',M.BASE/'stations.csv',DIR.parent/'07_joint_location/_joint_validation.py']+sorted((M.BASE/'grids').glob('time.*.time.*'))
 design={'round':27,'branch':args.branch,'relative_only_pick_prefix':'eqs47_','source_sha256':{str(f):M.sha(f) for f in files}}
 f=OUT/'location_design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 template=M.Problem();primary=problem(template,False);aux=problem(template,True);u=primary.p[['pick_id','event_id','instrument_id','phase']].copy();u['absolute_used']=primary.absolute_used;u.to_csv(OUT/'observation_usage.csv',index=False)
 rng=np.random.default_rng(48);x=aux.start.copy();x[:,:3]+=.013;x=x.ravel();d=rng.normal(size=len(x));d/=np.linalg.norm(d);errors={}
 for joint in [False,True]:
  f,j=aux.system(joint,True);h=1e-4;err=float(np.max(abs((f(x+h*d)-f(x-h*d))/(2*h)-j(x)@d)));assert err<1e-5;errors[str(joint)]=err
 control={}
 if args.branch=='fixed':
  B=load('baseline45',DIR.parent/'10_added_station/45_run_station.py');oldtemplate=B.M.Problem()
  for auxiliary,p in [(False,primary),(True,aux)]:
   b=B.problem(oldtemplate,auxiliary);assert np.array_equal(b.e.event_id,p.e.event_id);z=p.start.copy();z[:,:3]+=.013;f,j=p.system(False,auxiliary);bf,bj=b.system(False,auxiliary);v=z.ravel();err=float(np.max(abs(f(v)-bf(v))));diff=j(v)-bj(v);je=float(np.max(abs(diff.data))) if diff.nnz else 0.;assert err<1e-10 and je<1e-10;control[str(auxiliary)]={'absolute_residual_error':err,'absolute_jacobian_error':je}
 M.save(OUT/'numerical_checks.json',{'directional_jacobian_error':errors,'stage45_absolute_control_equivalence':control,'primary_events':len(primary.e),'auxiliary_events':len(aux.e),'absolute_rows':int(primary.absolute_used.sum()),'relative_only_rows':int((~primary.absolute_used).sum()),'accepted_edges':len(primary.c)})
 print((OUT/'numerical_checks.json').read_text(),flush=True)
 if args.stage=='prepare':return
 jobs=[(primary,b,'control',(0,0,0)) for b in ['absolute_all','joint_all']]
 for branch in ['absolute_withheld','joint_withheld']:jobs.extend((aux,branch,label,shift) for label,shift in M.SHIFTS.items())
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for future in as_completed([pool.submit(solve,j) for j in jobs]):states.append(future.result());pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 assert len(states)==16
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
