#!/usr/bin/env python3
"""Fixed-observation joint location in archived three-dimensional TIME fields."""
from pathlib import Path
import importlib.util,json,types,hashlib,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import least_squares
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=load('robust40',DIR/'37_robust_cc.py');M=R.M;HERE=M.HERE
G=load('grids40',HERE/'03_experiments/06_3d_velocity/_cropped_times.py')
SRC=HERE/'export/39_support_aware_pairs';OUT=HERE/'export/40_joint_3d_model'
REGIONAL=HERE/'export/31_background_calibration/crop_check/grids/regional'
BACKGROUND=HERE/'export/29_3d_velocity/h0250m/baseline'
R.C.OUT=OUT;R.C.INPUT=OUT/'inputs';FIELDS={}

def sha_stream(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while block:=f.read(8*1024*1024):h.update(block)
 return h.hexdigest()

def field(model,station,phase):
 key=(model,station,phase)
 if key not in FIELDS:
  base=(REGIONAL if model=='regional' else BACKGROUND)/f'time.{phase}.{station}.time.buf'
  _,shape,origin,step=G.header(base.with_suffix('.hdr'))
  v=np.memmap(base,mode='r',dtype=np.float32,shape=shape)
  FIELDS[key]=(v,origin,step,base)
 return FIELDS[key]

def interpolate(v,origin,step,points):
 u=(points-origin)/step;i=np.floor(u).astype(int);a=u-i
 assert np.all(i>=0) and np.all(i+1<np.array(v.shape))
 x,y,z=i.T;ax,ay,az=a.T
 v000=v[x,y,z].astype(float);v001=v[x,y,z+1].astype(float)
 v010=v[x,y+1,z].astype(float);v011=v[x,y+1,z+1].astype(float)
 v100=v[x+1,y,z].astype(float);v101=v[x+1,y,z+1].astype(float)
 v110=v[x+1,y+1,z].astype(float);v111=v[x+1,y+1,z+1].astype(float)
 z00=(1-az)*v000+az*v001;z01=(1-az)*v010+az*v011
 z10=(1-az)*v100+az*v101;z11=(1-az)*v110+az*v111
 y0=(1-ay)*z00+ay*z01;y1=(1-ay)*z10+ay*z11
 value=(1-ax)*y0+ax*y1
 dx=(y1-y0)/step[0]
 dy=((1-ax)*(z01-z00)+ax*(z11-z10))/step[1]
 dz=((1-ax)*((1-ay)*(v001-v000)+ay*(v011-v010))+ax*((1-ay)*(v101-v100)+ay*(v111-v110)))/step[2]
 return value,np.column_stack([dx,dy,dz])

def prediction(self,x):
 x=x.reshape(-1,4);tt=np.empty(len(self.p));grad=np.ones((len(self.p),4))
 for ids,v,origin,step in self.fields:
  values,derivatives=interpolate(v,origin,step,x[self.ei[ids],:3]);tt[ids]=values;grad[ids,:3]=derivatives
 return tt+x[self.ei,3],grad

def problem(template,auxiliary,model='regional'):
 p=R.problem(template,auxiliary);p.fields=[]
 for (sid,phase),q in p.p.groupby(['instrument_id','phase']):
  v,origin,step,_=field(model,p.st.loc[sid,'nll_station'],phase)
  lo=p.bounds[0].reshape(-1,4)[0,:3];hi=p.bounds[1].reshape(-1,4)[0,:3]
  assert np.all(lo>=origin) and np.all(hi<origin+(np.array(v.shape)-1)*step)
  p.fields.append((q.index.to_numpy(),v,origin,step))
 p.prediction=types.MethodType(prediction,p);return p

def verify_fields(template):
 verified=json.loads((HERE/'export/29_3d_velocity/transfer/verified_grid_inputs.json').read_text());jobs=[]
 for (model,station,phase),(v,origin,step,path) in FIELDS.items():
  if model=='regional':
   source=json.loads(path.with_suffix('.crop.json').read_text());expected=source['cropped_sha256'];header=source['cropped_header_sha256']
  else:expected=verified[str(path)]['time_sha256'];header=verified[str(path)]['header_sha256']
  assert M.sha(path.with_suffix('.hdr'))==header
  jobs.append((path,expected,header))
 def check(job):
  path,expected,header=job;before=path.stat();actual=sha_stream(path);after=path.stat();assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns;assert actual==expected,str(path)
  return str(path),{'sha256':actual,'header_sha256':header,'bytes':after.st_size,'mtime_ns':after.st_mtime_ns}
 rows={}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(check,j) for j in jobs]):
   path,info=f.result();rows[path]=info
   if len(rows)%20==0:print('Verified TIME fields',len(rows),'/',len(jobs),flush=True)
 M.save(OUT/'verified_fields.json',rows)

def prepare():
 OUT.mkdir(exist_ok=True);(OUT/'matched_background').mkdir(exist_ok=True)
 for name in ['inputs','cc_measurements.csv','native_controls']:R.ENGINE.link(SRC/name,OUT/name)
 files=[Path(__file__),Path(R.__file__),Path(R.C.__file__),Path(M.__file__),Path(G.__file__),DIR/'40_evaluate_3d.py',DIR/'_joint_validation.py',SRC/'design.json',SRC/'location_design.json',SRC/'cc_measurements.csv',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv',HERE/'export/29_3d_velocity/h0250m/grid_design.json',HERE/'export/29_3d_velocity/transfer/verified_grid_inputs.json']
 design={'round':19,'cohort_role':'Exposed development; unchanged 300 targets, 2581 supports and all stage39 absolute/CC observations.','intervention':'Replace original radial mean TIME predictions and derivatives by archived regional 3D hybrid TIME fields for BOTH absolute and CC terms. Native receiver elevations, model datum, search bounds, Huber loss, errors, starts, optimizer and measurements unchanged. No station corrections, coordinate blending, model-weight scan or reference fitting.','numerical_control':'Four matched primary/withheld absolute/joint solves on archived original-background 0.25-km 3D TIME fields; regional model gets all 16 solves. Trilinear predictions checked independently against scipy; analytic sparse derivatives checked numerically. Verify actual archived buffers before fitting. No regenerated grids.','limitations':'Archived regional hybrid is not a verified exact published model: block mapping and sea-level depth interpretation remain documented assumptions; fixed 15-km hull taper and shallow/deep constant extension retained. Original stage29 absolute-only regional model had improved horizontal results but worse depth; this tests the interaction with physically consistent differential constraints, not cancellation of coordinate offsets. Same exposed targets, no new confirmation.','gates':'Retain all stage34 gates, including coverage (known to fail at 206/300). Additionally all 575 common-old held CC RMS <=1.05 stage39 under each solution own mean model; all 1408 held CC RMS <=1.05 both stage39 joint and matched 3D-background joint. Reference medians <=1.10 both joint controls; do not relax boundary/reference criteria if residuals improve.','source_sha256':{str(p):M.sha(p) for p in files}}
 dest=OUT/'design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 template=M.Problem();cases={(model,aux):problem(template,aux,model) for model in ['background','regional'] for aux in [False,True]}
 verify_fields(template)
 checks={}
 for model in ['background','regional']:
  p=cases[(model,True)];x=p.start.copy();x[:,:3]+=.013;x=x.ravel();independent=np.empty(len(p.p))
  for ids,v,origin,step in p.fields:
   axes=tuple(o+np.arange(n)*d for o,n,d in zip(origin,v.shape,step));independent[ids]=RegularGridInterpolator(axes,v,bounds_error=True)(x.reshape(-1,4)[p.ei[ids],:3])
  pred,_=p.prediction(x);error=float(np.max(abs(pred-independent)));assert error<1e-10
  rng=np.random.default_rng(40);d=rng.normal(size=len(x));d/=np.linalg.norm(d);fun,jac=p.system(True,True);h=1e-4;derivative=float(np.max(abs((fun(x+h*d)-fun(x-h*d))/(2*h)-jac(x)@d)));assert derivative<1e-5
  checks[model]={'independent_interpolation_max_s':error,'sparse_derivative_error':derivative,'n_events':len(p.e),'n_picks':len(p.p),'n_cc':len(p.c)}
 M.save(OUT/'numerical_checks.json',checks);print(json.dumps(checks,indent=2),flush=True)
 return cases

def solve(job):
 p,model,branch,label,shift=job;folder=OUT if model=='regional' else OUT/'matched_background';file=folder/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
 if not(file.exists() and meta.exists()):
  fun,jac=p.system(branch.startswith('joint_'),branch.endswith('_withheld'));x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
  fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
  np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str));M.save(meta,{'model':model,'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
 else:
  with np.load(file) as f:assert np.array_equal(f['event_id'],p.e.event_id.to_numpy(str))
 row=json.loads(meta.read_text());print(row,flush=True);return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();cases=prepare()
 if args.stage=='prepare':return
 jobs=[]
 for model in ['background','regional']:
  for aux in [False,True]:
   for joint in [False,True]:
    branch=('joint' if joint else 'absolute')+('_withheld' if aux else '_all')
    for label,shift in (M.SHIFTS.items() if model=='regional' and aux else [('control',(0,0,0))]):jobs.append((cases[(model,aux)],model,branch,label,shift))
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(solve,j) for j in jobs]):
   states.append(f.result());table=pd.DataFrame(states)
   for model,folder in [('regional',OUT),('background',OUT/'matched_background')]:table[table.model.eq(model)].to_csv(folder/'solver_status.csv',index=False)
 assert len(states)==20
 for path,info in json.loads((OUT/'verified_fields.json').read_text()).items():
  s=Path(path).stat();assert s.st_size==info['bytes'] and s.st_mtime_ns==info['mtime_ns'];assert M.sha(Path(path).with_suffix('.hdr'))==info['header_sha256']
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
