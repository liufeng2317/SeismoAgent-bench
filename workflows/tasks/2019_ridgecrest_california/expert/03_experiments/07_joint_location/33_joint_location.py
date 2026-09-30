#!/usr/bin/env python3
"""Fixed absolute-arrival + waveform differential-time least-squares pilot."""
from pathlib import Path
import json,hashlib,argparse,importlib.util
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix
from pyproj import CRS,Transformer
from threadpoolctl import threadpool_limits
threadpool_limits(1)
HERE=Path(__file__).resolve().parents[2]
OUT=HERE/'export/33_joint_location'
BASE=HERE/'export/04_locate_nonlinloc'
XYZ=['x_km','y_km','depth_km']
SHIFTS={'control':(0,0,0),'east_minus':(-1,0,0),'east_plus':(1,0,0),'north_minus':(0,-1,0),'north_plus':(0,1,0),'depth_minus':(0,0,-1),'depth_plus':(0,0,1)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
class Problem:
 def __init__(self):
  self.e=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv').sort_values('event_id').reset_index(drop=True)
  e=self.e;index=pd.Series(np.arange(len(e)),index=e.event_id)
  p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');self.p=p[p.event_id.isin(e.event_id)].reset_index(drop=True);p=self.p
  assert p.pick_id.is_unique and len(e)==147 and len(p)==5413
  self.ei=p.event_id.map(index).to_numpy();self.st=pd.read_csv(BASE/'stations.csv').set_index('id')
  self.t0=pd.to_datetime(e.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
  self.obs=pd.to_datetime(p.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9-self.t0[self.ei]
  self.sigma=np.sqrt(.3**2+np.where(p.phase.eq('P'),.1,.2)**2)
  held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'];self.train=~p.instrument_id.isin(held).to_numpy()
  c=pd.read_csv(HERE/'export/15_validate_transfer/cc_measurements.csv');self.c=c[c.accepted].reset_index(drop=True);c=self.c
  idx=pd.Series(np.arange(len(p)),index=p.pick_id);self.a=c.pick_id_a.map(idx).to_numpy();self.b=c.pick_id_b.map(idx).to_numpy();assert not pd.isna(self.a).any() and not pd.isna(self.b).any()
  self.a=self.a.astype(int);self.b=self.b.astype(int)
  assert np.array_equal(self.train[self.a],c.training.to_numpy()) and np.array_equal(self.train[self.a],self.train[self.b])
  self.dt=c.cc_arrival_difference_s.to_numpy()-(self.t0[self.ei[self.a]]-self.t0[self.ei[self.b]])
  self.groups=[];self.gridfiles=[]
  for (station,phase),g in p.groupby(['instrument_id','phase']):
   hdr=BASE/'grids'/f'time.{phase}.{self.st.loc[station,"nll_station"]}.time.hdr';f=hdr.read_text().splitlines()[0].split();ny,nz=int(f[1]),int(f[2]);h=float(f[7]);top=float(f[5]);assert float(f[4])==0 and float(f[8])==h
   grid=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float)
   self.groups.append((g.index.to_numpy(),self.st.loc[station,['x(km)','y(km)']].to_numpy(float),grid,h,top));self.gridfiles.extend([hdr,hdr.with_suffix('.buf')])
  self.start=np.column_stack([e[XYZ].to_numpy(),np.zeros(len(e))]);self.bounds=(np.tile([-54.639794,-60.855707,0.,-10.],len(e)),np.tile([54.639794,61.193307,25.,10.],len(e)))
 def prediction(self,x):
  x=x.reshape(-1,4);tt=np.zeros(len(self.p));grad=np.zeros((len(tt),4));grad[:,3]=1.
  for ids,station,v,h,top in self.groups:
   d=x[self.ei[ids],:2]-station;r=np.linalg.norm(d,axis=1);ur=r/h;uz=(x[self.ei[ids],2]-top)/h;i=np.floor(ur).astype(int);j=np.floor(uz).astype(int);a=ur-i;b=uz-j
   assert np.all((i>=0)&(i<v.shape[0]-1)&(j>=0)&(j<v.shape[1]-1))
   v00=v[i,j];v10=v[i+1,j];v01=v[i,j+1];v11=v[i+1,j+1]
   tt[ids]=(1-a)*((1-b)*v00+b*v01)+a*((1-b)*v10+b*v11)
   dr=((1-b)*(v10-v00)+b*(v11-v01))/h;dz=((1-a)*(v01-v00)+a*(v11-v10))/h
   grad[ids,:2]=dr[:,None]*d/np.maximum(r[:,None],1e-12);grad[ids,2]=dz
  return tt+x[self.ei,3],grad
 def system(self,joint,withheld):
  ai=np.flatnonzero(self.train if withheld else np.ones(len(self.p),bool));ci=np.flatnonzero(self.c.training.to_numpy() if withheld else np.ones(len(self.c),bool)) if joint else np.array([],int)
  aa=self.a[ci];bb=self.b[ci];nr=len(ai)+len(ci);n=len(self.e)*4
  rows=np.concatenate([np.repeat(np.arange(len(ai)),4),np.repeat(len(ai)+np.arange(len(ci)),4),np.repeat(len(ai)+np.arange(len(ci)),4)])
  cols=np.concatenate([(self.ei[ai,None]*4+np.arange(4)).ravel(),(self.ei[aa,None]*4+np.arange(4)).ravel(),(self.ei[bb,None]*4+np.arange(4)).ravel()])
  def fun(x):
   t,_=self.prediction(x);return np.r_[(t[ai]-self.obs[ai])/self.sigma[ai],(t[aa]-t[bb]-self.dt[ci])/.05]
  def jac(x):
   _,g=self.prediction(x);values=np.r_[(g[ai]/self.sigma[ai,None]).ravel(),(g[aa]/.05).ravel(),(-g[bb]/.05).ravel()];return coo_matrix((values,(rows,cols)),shape=(nr,n)).tocsr()
  return fun,jac
 def prepare(self):
  OUT.mkdir(exist_ok=True)
  files=[Path(__file__),HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/15_validate_transfer/cc_measurements.csv',HERE/'export/12_relative_location_pilot/run.json',BASE/'stations.csv']+self.gridfiles
  design={'round':12,'intervention':'Joint absolute-arrival and accepted waveform CC differential times; no catalog differential times or coordinate blending. Original elevated linear 1D grids for both terms.','absolute_sigma_s':{'P':float(np.sqrt(.1**2+.3**2)),'S':float(np.sqrt(.2**2+.3**2))},'cc_sigma_s':.05,'weight_limitations':'Fixed conservative 50 ms working error, not an estimated uncertainty. CC edge correlations and shared absolute/CC waveform errors are not whitened. No formal posterior accuracy claim. No alternative weights after scores.','runs':'Absolute-only and joint, each all-station and fixed six-station-withheld; six common ±1 km starting shifts for each withheld branch. All associated absolute picks retained. Same upstream associations and CC eligibility as historical data; not blind independent observations.','gates':{'retention':'All 147 events; no silent exclusions; numerical convergence reported.','differential':'Withheld accepted CC RMS <=0.95 matched absolute-only.','absolute':'Withheld absolute RMS <=1.05 matched absolute-only AND <=1.05 archived NLL withheld control.','reference':'All three horizontal medians and Shelly depth median <=1.10 matched absolute-only AND original NLL on identical fixed pairs. References never fit.','anchor':'Each shifted withheld joint solution differs from its unshifted counterpart by <=0.10 km common mean and <=0.20 km P90 individual 3D displacement.','coverage':'Near-depth-boundary count cannot exceed original by >3.','limits':'Passing only qualifies for broader independent validation, not full catalog adoption. Original absolute-only gates are not a direct test of relative gains; report both types separately. Confirmation reserve remains unused.'},'source_sha256':{str(p):sha(p) for p in files}}
  p=OUT/'design.json'
  if p.exists():assert json.loads(p.read_text())==design
  else:save(p,design)
  # Native grid predictor equivalence and sparse-Jacobian directional derivative.
  spec=importlib.util.spec_from_file_location('diag',HERE/'02_diagnostics/16_diagnose_systematics.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
  p=self.p.copy();p[XYZ]=self.start[self.ei,:3];native,_=d.predict(BASE/'grids',p,self.st);pred,_=self.prediction(self.start.ravel());assert np.max(np.abs(native-pred))<1e-10
  rng=np.random.default_rng(33);x=self.start.copy();x[:,:3]+=.013;x=x.ravel();direction=rng.normal(size=len(x));direction/=np.linalg.norm(direction);fun,jac=self.system(True,True);h=1e-4;err=float(np.max(np.abs((fun(x+h*direction)-fun(x-h*direction))/(2*h)-jac(x)@direction)));assert err<1e-5
  save(OUT/'numerical_checks.json',{'native_predictor_max_error_s':float(np.max(np.abs(native-pred))),'sparse_jacobian_directional_max_error':err,'n_absolute':len(self.p),'n_cc':len(self.c),'held_absolute':int((~self.train).sum()),'held_cc':int((~self.c.training).sum())})
 def run(self):
  rows=[]
  for withheld in [False,True]:
   for joint in [False,True]:
    branch=('joint' if joint else 'absolute')+('_withheld' if withheld else '_all');fun,jac=self.system(joint,withheld)
    for label,shift in (SHIFTS.items() if withheld else [('control',(0,0,0))]):
     p=OUT/(branch+'_'+label+'.npz');meta=p.with_suffix('.json')
     if not (p.exists() and meta.exists()):
      x=self.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
      fit=least_squares(fun,x.ravel(),jac=jac,bounds=self.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
      np.savez(p,x=fit.x.reshape(-1,4));save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
     row=json.loads(meta.read_text());rows.append(row);print(row,flush=True)
  pd.DataFrame(rows).to_csv(OUT/'solver_status.csv',index=False)
  for p,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert sha(Path(p))==h
 def report(self):
  rows=[];positions=[];held=~self.train;hc=~self.c.training.to_numpy()
  for name in ['absolute_all','joint_all','absolute_withheld','joint_withheld']:
   x=np.load(OUT/(name+'_control.npz'))['x'];t,_=self.prediction(x.ravel());a=t-self.obs;cc=t[self.a]-t[self.b]-self.dt
   for kind,values,mask in [('absolute',a,held),('cc',cc,hc)]:
    rows.append({'branch':name,'kind':kind,'heldout':name.endswith('_withheld'),'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(values[mask]**2)))})
   e=self.e[['event_id']].copy();e[XYZ]=x[:,:3];e['origin_time']=pd.to_datetime(self.t0+x[:,3],unit='s',utc=True).astype(str);e['branch']=name;positions.append(e)
  pd.DataFrame(rows).to_csv(OUT/'metrics.csv',index=False);pd.concat(positions).to_csv(OUT/'events.csv',index=False)
  rows=[]
  for branch in ['absolute_withheld','joint_withheld']:
   base=np.load(OUT/(branch+'_control.npz'))['x']
   for label in list(SHIFTS)[1:]:
    x=np.load(OUT/(branch+'_'+label+'.npz'))['x'];delta=x[:,:3]-base[:,:3];rows.append({'branch':branch,'start':label,'mean_shift_km':float(np.linalg.norm(delta.mean(axis=0))),'p90_shift_km':float(np.quantile(np.linalg.norm(delta,axis=1),.9))})
  pd.DataFrame(rows).to_csv(OUT/'anchor_metrics.csv',index=False)
  print(pd.read_csv(OUT/'metrics.csv').to_string(index=False),flush=True);print(pd.DataFrame(rows).to_string(index=False),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run','report','all'],default='all');args=parser.parse_args();p=Problem();p.prepare()
 if args.stage in ['run','all']:p.run()
 if args.stage in ['report','all']:p.report()
