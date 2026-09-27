#!/usr/bin/env python3
"""Build one fixed velocity midpoint and cache exact cropped endpoint travel times."""
from pathlib import Path
import importlib.util,json,subprocess,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/31_background_calibration'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('cache31',Path(__file__).with_name('_cropped_times.py'))
G=load('full31',Path(__file__).with_name('29_build_3d_grids.py'));G.configure(.25)
ENDPOINTS={'regional':G.OUT/'regional','local_background':HERE/'export/30_local_background/grids/regional'}
CACHE=OUT/'crop_check/grids';MID=OUT/'midpoint';FULL=MID/'full'

def prepare():
 assert json.loads((OUT/'crop_check/run.json').read_text())['passed']
 selection=json.loads((OUT/'selection_design.json').read_text());assert selection['design']['n_eligible']==138
 bounds=[np.array(v) for v in json.loads((OUT/'crop_check/design.json').read_text())['bounds']]
 sources=[Path(__file__),Path(C.__file__),Path(G.__file__),OUT/'selection_design.json',OUT/'development_holdouts.csv',OUT/'crop_check/design.json',G.BASE/'stations.csv',G.BINDIR/'Grid2Time']
 for folder in ENDPOINTS.values():
  for phase in ['P','S']:sources.extend([folder/f'model.{phase}.mod.buf',folder/f'model.{phase}.mod.hdr'])
 design=dict(intervention='Single predeclared alpha=.5 arithmetic mean of endpoint VELOCITIES, separately P/S. Not interpolation of travel times. Full-domain Grid2Time propagation then exact crop. No reference fitting or additional weights.',bounds=[x.tolist() for x in bounds],spacing_km=.25,source_sha256={str(p):C.sha(p) for p in sources})
 d=OUT/'grid_design.json'
 if d.exists():assert json.loads(d.read_text())==design
 else:C.write_json(d,design)
 FULL.mkdir(parents=True,exist_ok=True);shape=tuple(len(a) for a in G.AXES)
 for phase in ['P','S']:
  paths=[folder/f'model.{phase}.mod.buf' for folder in ENDPOINTS.values()];a,b=[np.memmap(p,dtype=np.float32,mode='r',shape=shape) for p in paths]
  output=FULL/f'model.{phase}.mod.buf';exists=output.exists();target=np.memmap(output,dtype=np.float32,mode='r' if exists else 'w+',shape=shape)
  for i in range(shape[0]):
   expected=(2/(1/a[i].astype(float)+1/b[i].astype(float))).astype(np.float32)
   assert np.isfinite(expected).all() and expected.min()>0
   if exists:assert np.array_equal(target[i],expected)
   else:target[i]=expected
  if not exists:
   target.flush();(FULL/f'model.{phase}.mod.hdr').write_bytes(paths[0].with_suffix('.hdr').read_bytes())
  del a,b,target
  print('Verified physical velocity midpoint',phase,flush=True)
 return bounds,pd.read_csv(G.BASE/'stations.csv')

def midpoint_job(station,phase,bounds,model_hashes):
 sid=station['nll_station'];name=f'time.{phase}.{sid}.time.buf';destination=CACHE/'midpoint'/name;destination.parent.mkdir(exist_ok=True)
 control=f'CONTROL 1 54321\nTRANS NONE\nGTFILES model time {phase}\nGTMODE GRID3D ANGLES_NO\nGT_PLFD 1.e-3 0\nGTSRCE {sid} XYZ {station["x(km)"]:.8f} {station["y(km)"]:.8f} {station["z(km)"]:.8f} 0\n'
 done=destination.with_suffix('.complete.json');identity=dict(control=control,model_sha256=model_hashes[phase],bounds=[v.tolist() for v in bounds])
 if done.exists():
  m=json.loads(done.read_text());assert m['input']==identity and C.sha(destination)==m['cropped_sha256'] and C.sha(destination.with_suffix('.hdr'))==m['cropped_header_sha256'];return
 path=FULL/f'{phase}_{sid}.in';path.write_text(control)
 with (FULL/f'{phase}_{sid}.log').open('w') as log:subprocess.run([str(G.BINDIR/'Grid2Time'),path.name],cwd=FULL,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
 source=FULL/name;_,shape,_,_=C.header(source.with_suffix('.hdr'));v=np.memmap(source,dtype=np.float32,mode='r',shape=shape);assert np.isfinite(v).all() and v.min()>=0 and v.max()<200;del v
 cropped=C.crop(source,destination,bounds)
 C.write_json(done,dict(input=identity,full_time_sha256=cropped['input']['source_sha256'],cropped_sha256=cropped['cropped_sha256'],cropped_header_sha256=cropped['cropped_header_sha256']))
 # Regenerable scratch output only; controls/logs, full hashes and cropped data remain.
 source.unlink();source.with_suffix('.hdr').unlink()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
 import fcntl
 OUT.mkdir(exist_ok=True)
 with (OUT/'grid.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);bounds,st=prepare()
  endpoint_jobs=[]
  for label,folder in ENDPOINTS.items():
   for sid in st.nll_station:
    for phase in ['P','S']:
     name=f'time.{phase}.{sid}.time.buf';endpoint_jobs.append((folder/name,CACHE/label/name))
  with ThreadPoolExecutor(max_workers=4) as pool:
   fs=[pool.submit(C.crop,s,d,bounds) for s,d in endpoint_jobs]
   for i,f in enumerate(as_completed(fs),1):
    f.result()
    if i%20==0 or i==len(fs):print('Endpoint cache',i,len(fs),flush=True)
  hashes={p:C.sha(FULL/f'model.{p}.mod.buf') for p in ['P','S']}
  with ThreadPoolExecutor(max_workers=a.workers) as pool:
   fs=[pool.submit(midpoint_job,s,p,bounds,hashes) for s in st.to_dict('records') for p in ['P','S']]
   for i,f in enumerate(as_completed(fs),1):f.result();print('Midpoint grids',i,len(fs),flush=True)
  C.write_json(OUT/'grid_run.json',dict(complete=True,n_endpoint_grids=len(endpoint_jobs),n_midpoint_grids=len(st)*2,scratch_full_buffers_removed_after_verified_crop=True))
if __name__=='__main__':main()
