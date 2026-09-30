#!/usr/bin/env python3
"""Execute the frozen stage33 objective on the frozen reserve/support graph."""
from pathlib import Path
import importlib.util,json,argparse
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
spec=importlib.util.spec_from_file_location('joint33',Path(__file__).with_name('33_joint_location.py'));M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
OUT=M.HERE/'export/34_joint_confirmation';INPUT=OUT/'inputs'
def problem(template,auxiliary):
 p=M.Problem.__new__(M.Problem)
 p.e=pd.read_csv(INPUT/'events.csv').sort_values('event_id').reset_index(drop=True)
 if auxiliary:p.e=p.e[p.e.auxiliary_eligible].reset_index(drop=True)
 e=p.e;index=pd.Series(np.arange(len(e)),index=e.event_id)
 p.p=pd.read_csv(INPUT/'all_phases.csv');p.p=p.p[p.p.event_id.isin(e.event_id)].reset_index(drop=True);ph=p.p
 p.st=template.st;p.ei=ph.event_id.map(index).to_numpy();p.t0=pd.to_datetime(e.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
 p.obs=pd.to_datetime(ph.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9-p.t0[p.ei];p.sigma=np.sqrt(.3**2+np.where(ph.phase.eq('P'),.1,.2)**2)
 held=json.loads((M.HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'];p.train=~ph.instrument_id.isin(held).to_numpy()
 cc=pd.read_csv(OUT/'cc_measurements.csv');p.c=cc[cc.accepted&cc.event_id_a.isin(e.event_id)&cc.event_id_b.isin(e.event_id)].reset_index(drop=True)
 idx=pd.Series(np.arange(len(ph)),index=ph.pick_id);p.a=p.c.pick_id_a.map(idx).to_numpy(int);p.b=p.c.pick_id_b.map(idx).to_numpy(int)
 assert ph.pick_id.is_unique and np.array_equal(p.train[p.a],p.c.training.to_numpy()) and np.array_equal(p.train[p.a],p.train[p.b])
 p.dt=p.c.cc_arrival_difference_s.to_numpy()-(p.t0[p.ei[p.a]]-p.t0[p.ei[p.b]])
 grids={}
 for ids,station,v,h,top in template.groups:
  row=template.p.iloc[ids[0]];grids[(row.instrument_id,row.phase)]=(station,v,h,top)
 p.groups=[];p.gridfiles=template.gridfiles
 for key,g in ph.groupby(['instrument_id','phase']):
  if key in grids:station,v,h,top=grids[key]
  else:
   sid,phase=key;hdr=M.BASE/'grids'/f'time.{phase}.{p.st.loc[sid,"nll_station"]}.time.hdr';f=hdr.read_text().splitlines()[0].split();ny,nz=int(f[1]),int(f[2]);h=float(f[7]);top=float(f[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float);station=p.st.loc[sid,['x(km)','y(km)']].to_numpy(float)
  p.groups.append((g.index.to_numpy(),station,v,h,top))
 p.start=np.column_stack([e[M.XYZ].to_numpy(),np.zeros(len(e))]);p.bounds=(np.tile([-54.639794,-60.855707,0.,-10.],len(e)),np.tile([54.639794,61.193307,25.,10.],len(e)))
 assert np.all(p.start.ravel()>=p.bounds[0]) and np.all(p.start.ravel()<=p.bounds[1])
 return p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');args=parser.parse_args()
 template=M.Problem();files=[Path(__file__),Path(M.__file__),OUT/'design.json',OUT/'cc_measurements.csv',OUT/'cc_processing/design.json',OUT/'cc_processing/cc_checks.json',INPUT/'events.csv',INPUT/'all_phases.csv']+template.gridfiles
 frozen=json.loads((M.HERE/'export/33_joint_location/frozen_candidate.json').read_text())
 for f,h in frozen['sha256'].items():assert M.sha(Path(f))==h
 design={'candidate':'Unchanged stage33 system/prediction and optimization options; new data only.','source_sha256':{str(f):M.sha(f) for f in files},'repeats':'All and withheld absolute/joint; common ±1 km starts on withheld solves. Record reserve and support separately. All reserve statuses retained.'}
 dest=OUT/'execution_design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 if args.stage=='prepare':
  for auxiliary in [False,True]:
   p=problem(template,auxiliary);print('Prepared', 'auxiliary' if auxiliary else 'primary',len(p.e),'events',len(p.p),'picks',len(p.c),'accepted edges',flush=True)
  return
 states=[]
 for auxiliary in [False,True]:
  p=problem(template,auxiliary);p.e[['event_id','role','auxiliary_eligible']].to_csv(OUT/('auxiliary_events.csv' if auxiliary else 'primary_events.csv'),index=False)
  for joint in [False,True]:
   branch=('joint' if joint else 'absolute')+('_withheld' if auxiliary else '_all');fun,jac=p.system(joint,auxiliary)
   for label,shift in (M.SHIFTS.items() if auxiliary else [('control',(0,0,0))]):
    file=OUT/(branch+'_'+label+'.npz');meta=file.with_suffix('.json')
    if not(file.exists() and meta.exists()):
     x=p.start.copy();x[:,:3]+=shift;x[:,2]=np.clip(x[:,2],.001,24.999)
     fit=least_squares(fun,x.ravel(),jac=jac,bounds=p.bounds,x_scale='jac',tr_solver='lsmr',max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-6,tr_options={'atol':1e-8,'btol':1e-8,'maxiter':2000})
     np.savez(file,x=fit.x.reshape(-1,4),event_id=p.e.event_id.to_numpy(str));M.save(meta,{'branch':branch,'start':label,'success':bool(fit.success),'status':int(fit.status),'nfev':fit.nfev,'cost':fit.cost,'optimality':fit.optimality,'message':fit.message})
    row=json.loads(meta.read_text());states.append(row);print(row,flush=True)
 pd.DataFrame(states).to_csv(OUT/'solver_status.csv',index=False)
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
