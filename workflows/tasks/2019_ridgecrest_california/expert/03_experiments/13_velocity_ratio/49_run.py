#!/usr/bin/env python3
"""Apply independently calibrated constant S-speed scale to stage48's fixed data."""
from pathlib import Path
import argparse,importlib.util,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('base48for49',DIR.parent/'12_differential_augmentation/48_run.py');M=C.M;HERE=M.HERE;ROOT=HERE/'export/49_velocity_ratio';OUT=ROOT/'location';BASELINE=HERE/'export/48_differential_augmentation/refreshed'
C.OUT=OUT;C.R.C.OUT=OUT;C.R.C.INPUT=BASELINE/'inputs'
def problem(template,auxiliary):
 p=C.problem(template,auxiliary);r=json.loads((ROOT/'calibration.json').read_text());assert all(r['gates'].values());factor=r['vp_vs']/r['original_vp_vs']
 p.groups=[(ids,st,v*factor if p.p.iloc[ids[0]].phase=='S' else v,h,top) for ids,st,v,h,top in p.groups]
 return p
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);args=ap.parse_args();OUT.mkdir(exist_ok=True)
 for name in ['cc_measurements.csv','inputs','native_controls']:
  link=OUT/name
  if not link.exists():link.symlink_to(BASELINE/name)
  assert link.resolve()==(BASELINE/name).resolve()
 cal=json.loads((ROOT/'calibration.json').read_text());assert all(cal['gates'].values())
 files=[Path(__file__),DIR/'49_evaluate.py',Path(C.__file__),Path(C.R.C.__file__),Path(M.__file__),Path(C.R.__file__),ROOT/'design.json',ROOT/'calibration.json',ROOT/'candidate_velocity_model.csv',BASELINE/'location_design.json',BASELINE/'inputs/events.csv',BASELINE/'inputs/all_phases.csv',BASELINE/'cc_measurements.csv',DIR.parent/'07_joint_location/_joint_validation.py']+list((M.BASE/'grids').glob('time.*.time.*'))
 design={'round':28,'intervention':'Single calibrated Vp/Vs, fitted only on disjoint event/station data, with fixed stage48 differential-only EQ S usage and graph. No further fit or ratio scan.','implementation':'Scale every original1D S travel-time table and its spatial gradient by calibrated_ratio/1.73. P fields and origin-time derivative unchanged. This corresponds to uniform Vs scaling for proportional isotropic1D media; original native table discretization is retained. All newly acquired receiver fields included.','vp_vs':cal['vp_vs'],'absolute_error_and_cc_objective':'Stage48 unchanged; no covariance tightening from calibration bootstrap.','gates':'All historical catalog gates including known coverage208<210. Fixed575/1408/1524 CC RMS<=1.05 stage48; reference medians<=1.10 stage48 and45 plus native/matched. No confirmation unless every gate passes.','source_sha256':{str(f):M.sha(f) for f in files}}
 f=OUT/'location_design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 template=M.Problem();primary=problem(template,False);aux=problem(template,True)
 # Check S-only scaling and origin-time derivative separately from location fitting.
 old=C.problem(template,True);x=aux.start.copy();x[:,:3]+=.013;x[:,3]=.12;t,g=aux.prediction(x.ravel());ot,og=old.prediction(x.ravel());s=aux.p.phase.eq('S').to_numpy();factor=cal['vp_vs']/1.73
 assert np.max(abs(t[~s]-ot[~s]))==0 and np.max(abs(t[s]-(ot[s]-.12)*factor-.12))<1e-10
 assert np.max(abs(g[s,:3]-og[s,:3]*factor))<1e-10 and np.array_equal(g[:,3],np.ones(len(g)))
 rng=np.random.default_rng(49);d=rng.normal(size=x.size);d/=np.linalg.norm(d);v=x.ravel();checks={}
 for joint in [False,True]:
  f,j=aux.system(joint,True);h=1e-4;err=float(np.max(abs((f(v+h*d)-f(v-h*d))/(2*h)-j(v)@d)));assert err<1e-5;checks[str(joint)]=err
 M.save(OUT/'numerical_checks.json',{'s_table_factor':factor,'P_unchanged':True,'origin_derivative_one':True,'directional_jacobian_error':checks,'primary_events':len(primary.e),'auxiliary_events':len(aux.e),'accepted_edges':len(primary.c)})
 print((OUT/'numerical_checks.json').read_text(),flush=True)
 jobs=[(primary,b,'control',(0,0,0)) for b in ['absolute_all','joint_all']]
 for branch in ['absolute_withheld','joint_withheld']:jobs.extend((aux,branch,label,shift) for label,shift in M.SHIFTS.items())
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for future in as_completed([pool.submit(C.solve,j) for j in jobs]):states.append(future.result());pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 assert len(states)==16
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
