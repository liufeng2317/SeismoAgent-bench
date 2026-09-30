#!/usr/bin/env python3
"""Verify exact cropped buffers and native-location equivalence before calibration."""
from pathlib import Path
import importlib.util,sys,json
import numpy as np
import pandas as pd
import yaml
from concurrent.futures import ThreadPoolExecutor,as_completed
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/31_background_calibration/crop_check'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
C=load('crop31',Path(__file__).with_name('_cropped_times.py'))
S=load('native31',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
BASE=HERE/'export/04_locate_nonlinloc'
MODELS={'regional':HERE/'export/29_3d_velocity/h0250m/regional','local_background':HERE/'export/30_local_background/grids/regional'}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 import fcntl
 with (OUT/'run.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  dev=pd.read_csv(HERE/'export/12_relative_location_pilot/events.csv');transfer=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv');ids=sorted(set(dev.event_id)|set(transfer.event_id))
  controls=[BASE/'events_raw'/eid/'control.in' for eid in ids];bounds=C.search_bounds(controls)
  event=transfer.sort_values('event_id').iloc[0].to_dict();eid=event['event_id']
  picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);picks=picks[picks.event_id.eq(eid)].copy();picks['residual_s']=picks.residual_s_gamma
  st=pd.read_csv(BASE/'stations.csv').set_index('id');cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
  sources=[Path(__file__),Path(C.__file__),Path(S.__file__),Path(S.NLL.__file__),HERE/'00_config/nonlinloc.yaml',BASE/'stations.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/29_3d_velocity/transfer/tables/events.csv',HERE/'export/30_local_background/transfer/tables/events.csv']+controls
  design=dict(pilot=eid,search_events=len(ids),bounds=[v.tolist() for v in bounds],change='Exact aligned subset of TIME buffers; no resampling; unchanged station/transform header lines. All retained float32 values must match bitwise.',gates='Both native pilot xyz/origin within .001 km/.001 s of full grids; phase identities unchanged; independent native TT difference <.00035 s. Search-volume coverage required before any future use.',source_sha256={str(p):C.sha(p) for p in sources})
  d=OUT/'design.json'
  if d.exists():assert json.loads(d.read_text())==design
  else:C.write_json(d,design)
  tasks=[]
  for name,folder in MODELS.items():
   for sid in picks.instrument_id.unique():
    for phase in ['P','S']:
     filename=f'time.{phase}.{st.loc[sid,"nll_station"]}.time.buf';tasks.append((folder/filename,OUT/'grids'/name/filename))
  records=[]
  with ThreadPoolExecutor(max_workers=4) as pool:
   futures=[pool.submit(C.crop,a,b,bounds) for a,b in tasks]
   for i,f in enumerate(as_completed(futures),1):records.append(f.result());print(f'[{i}/{len(tasks)}] exact grid crop',flush=True)
  rows=[];phases=[];checks=[]
  for name in MODELS:
   proxy=OUT/('input_'+name);proxy.mkdir(exist_ok=True)
   for label,target in [('events_raw',BASE/'events_raw'),('grids',OUT/'grids'/name)]:
    dest=proxy/label
    if not dest.exists():dest.symlink_to(target,target_is_directory=True)
    assert dest.resolve()==target.resolve()
   S.OUT=OUT;S.BASE=proxy;S.write_json=C.write_json
   row,links=S.solve(event,picks.to_dict('records'),name,{},st.nll_station.to_dict(),cfg)
   oldroot=HERE/('export/29_3d_velocity/transfer' if name=='regional' else 'export/30_local_background/transfer')
   old=pd.read_csv(oldroot/'tables/events.csv');old=old[old.branch.eq('regional')&old.event_id.eq(eid)].iloc[0]
   dx=float(np.max(np.abs(np.array([row[k] for k in S.XYZ])-old[S.XYZ].to_numpy(float))));dt=abs((pd.Timestamp(row['origin_time'])-pd.Timestamp(old.origin_time)).total_seconds())
   q=pd.DataFrame(links).reset_index(drop=True)
   for col in S.XYZ:q[col]=row[col]
   err=float(np.max(np.abs(C.predict(OUT/'grids'/name,q,st)-q.predicted_travel_time_s)))
   assert dx<.001 and dt<.001 and err<.00035,(name,dx,dt,err)
   assert set(q.pick_id)==set(picks.pick_id)
   rows.append(row);phases.extend(links);checks.append(dict(model=name,max_xyz_difference_km=dx,origin_difference_s=dt,max_native_tt_difference_s=err))
   print('Native equivalence:',checks[-1],flush=True)
  pd.DataFrame(rows).to_csv(OUT/'events.csv',index=False);pd.DataFrame(phases).to_csv(OUT/'phases.csv',index=False)
  summary=dict(passed=True,checks=checks,n_buffers=len(records),source_bytes=sum(x['source_bytes'] for x in records),cropped_bytes=sum(x['cropped_bytes'] for x in records),round_counted=False)
  C.write_json(OUT/'run.json',summary);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
