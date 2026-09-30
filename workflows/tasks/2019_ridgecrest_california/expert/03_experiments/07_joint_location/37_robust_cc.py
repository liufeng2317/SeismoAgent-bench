#!/usr/bin/env python3
"""Fixed CC-only Huber loss; absolute-arrival likelihood remains quadratic."""
from pathlib import Path
import importlib.util,json,types,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('shared37',DIR/'34_run_confirmation.py');M=C.M;HERE=M.HERE;SRC=HERE/'export/35_cc_observation_selection';OUT=HERE/'export/37_robust_cc';C.OUT=OUT;C.INPUT=OUT/'inputs'
ENGINE=load('engine37',DIR/'36_model_error.py');ENGINE.OUT=OUT
DELTA=1.345

def transform(r,n):
 value=r.copy();derivative=np.ones(len(r));mask=(np.arange(len(r))>=n)&(abs(r)>DELTA)
 z=np.sqrt(2*DELTA*abs(r[mask])-DELTA**2);value[mask]=np.sign(r[mask])*z;derivative[mask]=DELTA/z
 return value,derivative

def problem(template,auxiliary):
 p=C.problem(template,auxiliary)
 def system(self,joint,withheld):
  fun,jac=M.Problem.system(self,joint,withheld)
  if not joint:return fun,jac
  n=int(self.train.sum()) if withheld else len(self.p)
  def f(x):return transform(fun(x),n)[0]
  def j(x):return jac(x).multiply(transform(fun(x),n)[1][:,None]).tocsr()
  return f,j
 p.system=types.MethodType(system,p);return p

def prepare():
 OUT.mkdir(exist_ok=True)
 for name in ['inputs','cc_measurements.csv','native_controls']:ENGINE.link(SRC/name,OUT/name)
 files=[Path(__file__),Path(C.__file__),Path(M.__file__),Path(ENGINE.__file__),SRC/'design.json',SRC/'cc_measurements.csv',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv']+sorted((M.BASE/'grids').glob('time.*.time.*'))
 design={'round':16,'cohort_role':'Exposed development, fixed stage35 cohort/observations.','intervention':'CC-only Huber loss with delta=1.345 on residual/0.05 s; absolute-arrival objective stays quadratic with original errors. No model-contrast errors from stage36, no observation removal or hand-set depth constraints.','formula':'For CC standardized r, 0.5*r^2 when |r|<=delta; otherwise delta*|r|-0.5*delta^2. Implement as signed sqrt(2*Huber) pseudo-residual with exact sparse derivative.','delta':DELTA,'limits':'Fixed working loss, not a calibrated outlier probability or posterior model. Coverage remains 190/300 and fails regardless. Huber bounds residual influence, not geometric leverage or all model biases. No threshold or loss-family scan follows.','gates':'Retain stage34 prediction/reference/coverage/boundary/start-stability gates. Score the same 575 held CC and 1394 held absolute observations as stage35. Reuse exact absolute controls. This exposed test cannot authorize adoption or serve as fresh confirmation.','source_sha256':{str(p):M.sha(p) for p in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):
   for suffix in ['npz','json']:ENGINE.link(SRC/(branch+'_'+label+'.'+suffix),OUT/(branch+'_'+label+'.'+suffix))
 template=M.Problem();p=problem(template,True)
 r=np.array([-4.,-.5,0.,.5,4.]);f,_=transform(r,0);expected=np.where(abs(r)<=DELTA,.5*r*r,DELTA*abs(r)-.5*DELTA**2);assert np.allclose(.5*f*f,expected,atol=1e-14)
 rng=np.random.default_rng(37);x=p.start.copy();x[:,:3]+=.013;x=x.ravel();d=rng.normal(size=len(x));d/=np.linalg.norm(d);fun,jac=p.system(True,True);h=1e-4;err=float(np.max(abs((fun(x+h*d)-fun(x-h*d))/(2*h)-jac(x)@d)));assert err<1e-5
 M.save(OUT/'numerical_checks.json',{'huber_objective_identity':True,'sparse_derivative_error':err})
 return template

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();template=prepare()
 if args.stage=='prepare':return
 primary=problem(template,False);aux=problem(template,True);jobs=[(primary,'joint_all','control',(0,0,0))]+[(aux,'joint_withheld',label,shift) for label,shift in M.SHIFTS.items()]
 states=[]
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):states.append(json.loads((OUT/(branch+'_'+label+'.json')).read_text()))
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(ENGINE.solve,job) for job in jobs]):states.append(f.result())
 pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
