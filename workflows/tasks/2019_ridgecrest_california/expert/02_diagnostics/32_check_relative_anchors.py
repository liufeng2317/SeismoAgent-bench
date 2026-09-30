#!/usr/bin/env python3
"""Fixed common-translation test of archived hypoDD configurations; no tuning."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,shutil
import numpy as np
import pandas as pd
from pyproj import Transformer,CRS
HERE=Path(__file__).resolve().parents[1]
SRC=HERE/'export/15_validate_transfer'
OUT=HERE/'export/32_relative_anchor_check'
CRSXY=CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km')
FWD=Transformer.from_crs(4326,CRSXY,always_xy=True)
REV=Transformer.from_crs(CRSXY,4326,always_xy=True)
SHIFTS={'control':(0,0,0),'east_minus':(-1,0,0),'east_plus':(1,0,0),'north_minus':(0,-1,0),'north_plus':(0,1,0),'depth_minus':(0,0,-1),'depth_plus':(0,0,1)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def coords(path):
 f=pd.read_csv(path,sep=r'\s+',header=None).set_index(0)
 x,y=FWD.transform(f[2].to_numpy(),f[1].to_numpy())
 return pd.DataFrame({'x':x,'y':y,'z':f[3].to_numpy()},index=f.index)
def run(job):
 method,label=job;source=SRC/method;dest=OUT/method/label;dest.mkdir(parents=True,exist_ok=True)
 for name in ['hypoDD.inp','dt.ct','dt.cc','station.dat']:shutil.copy2(source/name,dest/name)
 dx,dy,dz=SHIFTS[label]
 if label=='control':shutil.copy2(source/'event.dat',dest/'event.dat')
 else:
  lines=[]
  for line in (source/'event.dat').read_text().splitlines():
   a=line.split();x,y=FWD.transform(float(a[3]),float(a[2]));lon,lat=REV.transform(x+dx,y+dy)
   a[2]=f'{lat:.7f}';a[3]=f'{lon:.7f}';a[4]=f'{float(a[4])+dz:.5f}';lines.append(' '.join(a))
  (dest/'event.dat').write_text('\n'.join(lines)+'\n')
 with (dest/'console.log').open('w') as log:subprocess.run([str(SRC/'native/hypoDD'),'hypoDD.inp'],cwd=dest,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
 print(method,label,'complete',flush=True)
 return method,label

def main():
 OUT.mkdir(exist_ok=True)
 files=[Path(__file__),SRC/'native/hypoDD']+[SRC/m/n for m in ['hypodd','hypodd_cc'] for n in ['hypoDD.inp','dt.ct','dt.cc','station.dat','event.dat','hypoDD.reloc']]
 design={'purpose':'Diagnose dependence on a common initial-location translation; not an optimization round or independent accuracy test. No reference/confirmation outcomes read.','shifts_km':SHIFTS,'fixed_inputs':{str(p):sha(p) for p in files},'checks':'Exact native control reproduction required. Report all retention losses, common-event centroid response and centered deformation. No outcome-based selection or new shift sizes.'}
 design=json.loads(json.dumps(design));p=OUT/'design.json'
 if p.exists():assert json.loads(p.read_text())==design
 else:p.write_text(json.dumps(design,indent=2)+'\n')
 jobs=[(m,s) for m in ['hypodd','hypodd_cc'] for s in SHIFTS]
 with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,jobs))
 rows=[];all_delta=[]
 for m in ['hypodd','hypodd_cc']:
  archived=coords(SRC/m/'hypoDD.reloc');base=coords(OUT/m/'control/hypoDD.reloc')
  assert set(base.index)==set(archived.index)
  assert np.max(np.abs(base.loc[archived.index].to_numpy()-archived.to_numpy()))<1e-8
  for label,shift in SHIFTS.items():
   q=coords(OUT/m/label/'hypoDD.reloc');common=base.index.intersection(q.index);delta=q.loc[common]-base.loc[common]
   mean=delta.mean().to_numpy();centered=delta.to_numpy()-mean
   unit=np.array(shift,dtype=float);response=float(mean@unit) if np.any(unit) else 0.
   rows.append(dict(method=m,perturbation=label,n_baseline=len(base),n_retained=len(q),n_common=len(common),n_lost=len(base.index.difference(q.index)),n_gained=len(q.index.difference(base.index)),mean_dx_km=mean[0],mean_dy_km=mean[1],mean_dz_km=mean[2],response_along_shift_km=response,centered_displacement_rms_km=float(np.sqrt(np.mean(np.sum(centered**2,axis=1)))),p90_displacement_km=float(np.quantile(np.linalg.norm(delta,axis=1),.9))))
   delta=delta.rename(columns={'x':'dx_km','y':'dy_km','z':'dz_km'});delta['method']=m;delta['perturbation']=label;delta.index.name='native_id';all_delta.append(delta.reset_index())
 for p,h in design['fixed_inputs'].items():assert sha(Path(p))==h
 metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'metrics.csv',index=False);pd.concat(all_delta).to_csv(OUT/'event_displacements.csv',index=False)
 (OUT/'README.md').write_text('# Fixed relative-location anchor diagnostic\n\nFourteen native runs: two unchanged methods, each with an exact control and six common initial-location translations of ±1 km. Controls reproduce archived locations exactly. Observations, station positions, model and solver settings remain fixed. No reference or confirmation outcomes enter this check. This is a diagnostic, not an optimization round or a new catalog.\n\n'+metrics.to_string(index=False)+'\n\nThe response along the applied shift is in km per 1 km perturbation. Centered deformation removes the common mean translation on each paired retained cohort. Retention differences are reported explicitly. A low differential residual does not alone constrain a common cluster displacement. Do not interpret stability as true absolute accuracy.\n')
 print(metrics.to_string(index=False),flush=True)
if __name__=='__main__':main()
