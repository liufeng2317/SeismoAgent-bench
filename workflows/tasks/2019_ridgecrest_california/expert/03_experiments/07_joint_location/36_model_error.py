#!/usr/bin/env python3
"""Fixed differential-model sensitivity errors; mean travel times unchanged."""
from pathlib import Path
import importlib.util,json,types,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('shared36',DIR/'34_run_confirmation.py');M=C.M;HERE=M.HERE;SRC=HERE/'export/35_cc_observation_selection';OUT=HERE/'export/36_differential_model_error';C.OUT=OUT;C.INPUT=OUT/'inputs'
D=load('diagnostic36',HERE/'02_diagnostics/16_diagnose_systematics.py');G=load('cropped36',HERE/'03_experiments/06_3d_velocity/_cropped_times.py')
REGIONAL=HERE/'export/31_background_calibration/crop_check/grids/regional';LAYER=HERE/'export/06_diagnose_depth/layered_grids'
def link(source,dest):
 if not dest.exists():dest.symlink_to(source,target_is_directory=source.is_dir())
 assert dest.resolve()==source.resolve()
def problem(template,auxiliary):
 p=C.problem(template,auxiliary);w=pd.read_csv(OUT/'edge_model_errors.csv').set_index(['pick_id_a','pick_id_b']);sigma=w.loc[list(zip(p.c.pick_id_a,p.c.pick_id_b)),'sigma_s'].to_numpy();assert np.all(sigma>=.05)
 original=M.Problem.system
 def system(self,joint,withheld):
  fun,jac=original(self,joint,withheld)
  n=int(self.train.sum()) if withheld else len(self.p);selected=self.c.training.to_numpy() if withheld else np.ones(len(self.c),bool)
  scales=np.r_[np.ones(n),.05/sigma[selected]] if joint else np.ones(n)
  def f(x):return fun(x)*scales
  def j(x):return jac(x).multiply(scales[:,None]).tocsr()
  return f,j
 p.system=types.MethodType(system,p);return p

def prepare():
 OUT.mkdir(exist_ok=True)
 for name in ['inputs','cc_measurements.csv','native_controls']:link(SRC/name,OUT/name)
 files=[Path(__file__),Path(C.__file__),Path(M.__file__),Path(D.__file__),Path(G.__file__),SRC/'design.json',SRC/'cc_measurements.csv',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv']
 for folder in [M.BASE/'grids',REGIONAL,LAYER]:files+=sorted(folder.glob('time.*.time.hdr'))+sorted(folder.glob('time.*.time.buf'))
 design={'round':15,'cohort_role':'Exposed development; fixed stage35 300 targets and 1970 supports.','intervention':'Replace only fixed 0.05-s CC working error with sqrt(0.05^2 + E^2). E is the maximum absolute difference between original and two alternative model differential travel times at frozen original NLL coordinates. Alternatives: archived layered local and raw regional 3D hybrid. No measured arrival, reference location, new fitted position or outcome sets this error.','mean_model':'Original linear elevated model remains the mean for absolute and differential times. No station corrections or coordinate blending.','limitations':'Model-contrast envelope is a working sensitivity error, not calibrated standard deviation or an independent ensemble. Alternatives share sources and have datum/provenance caveats. Shared CC-edge correlations remain; no formal posterior accuracy claim. No error multipliers or model subset scan follows.','gates':'Retain stage34 gates and all stage35 observations. Coverage is already below 210 and therefore blocks full promotion regardless. Test whether model-error treatment improves depth boundary behavior while preserving common held-out differential gains; a future complete candidate still requires fresh confirmation.','source_sha256':{str(f):M.sha(f) for f in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 template=M.Problem();p=C.problem(template,False)
 path=OUT/'edge_model_errors.csv'
 if not path.exists():
  points=p.p.copy();points[M.XYZ]=p.start[p.ei,:3]
  baseline,_=p.prediction(p.start.ravel());layered,_=D.predict(LAYER,points,p.st);regional=G.predict(REGIONAL,points,p.st)
  bd=baseline[p.a]-baseline[p.b];ld=layered[p.a]-layered[p.b]-bd;rd=regional[p.a]-regional[p.b]-bd;envelope=np.maximum(abs(ld),abs(rd))
  q=p.c.copy();q['layered_minus_original_dt_s']=ld;q['regional_minus_original_dt_s']=rd;q['model_envelope_s']=envelope;q['sigma_s']=np.sqrt(.05**2+envelope**2);q.to_csv(path,index=False)
  summary={'n_edges':len(q),'sigma_quantiles_s':{str(k):float(v) for k,v in q.sigma_s.quantile([0,.5,.9,.99,1]).items()},'n_above_0_1s':int(q.sigma_s.gt(.1).sum())};M.save(OUT/'model_error_summary.json',summary);print(summary,flush=True)
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):
   for suffix in ['npz','json']:link(SRC/(branch+'_'+label+'.'+suffix),OUT/(branch+'_'+label+'.'+suffix))
 pp=problem(template,True);fun,jac=pp.system(True,True);rng=np.random.default_rng(36);x=pp.start.copy();x[:,:3]+=.013;x=x.ravel();direction=rng.normal(size=len(x));direction/=np.linalg.norm(direction);h=1e-4;err=float(np.max(abs((fun(x+h*direction)-fun(x-h*direction))/(2*h)-jac(x)@direction)));assert err<1e-5
 M.save(OUT/'numerical_checks.json',{'weighted_jacobian_directional_error':err,'edge_error_table_sha256':M.sha(path)})
 return template

def solve(job):
 p,branch,label,shift=job;file=OUT/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
 if not(file.exists() and meta.exists()):
  fun,jac=p.system(True,branch.endswith('_withheld'));x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
  fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
  np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str));M.save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
 row=json.loads(meta.read_text());print(row,flush=True);return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();template=prepare()
 if args.stage=='prepare':return
 primary=problem(template,False);aux=problem(template,True);jobs=[(primary,'joint_all','control',(0,0,0))]+[(aux,'joint_withheld',label,shift) for label,shift in M.SHIFTS.items()]
 states=[]
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):states.append(json.loads((OUT/(branch+'_'+label+'.json')).read_text()))
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(solve,job) for job in jobs]):states.append(f.result())
 pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
