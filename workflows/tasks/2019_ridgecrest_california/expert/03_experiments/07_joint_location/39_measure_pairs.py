#!/usr/bin/env python3
"""Reuse identical cached windows; extract only newly needed pick windows."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/39_support_aware_pairs';INPUT=OUT/'inputs';WORK=OUT/'cc_processing';OLD=HERE/'export/35_cc_observation_selection/cc_processing'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=load('measurement_helper39',DIR/'_cc_measurements.py');M=H._V.M

def main():
 WORK.mkdir(exist_ok=True)
 files=[Path(__file__),Path(H.__file__),Path(H._V.__file__),OUT/'design.json',INPUT/'picks.csv',INPUT/'differential_times.csv',OLD/'cc_windows.npz',OLD/'waveform_windows.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py']
 design={'round':18,'measurement':'Exact historical scalar P and stage38 vector S. Shared implementation verified against all stage38 measurements. Cache reuse changes I/O only. Old waveform audit/arrays are reused unchanged for matching pick/channel keys, including old missing-window statuses; only unseen windows invoke the original extractor.','source_sha256':{str(f):M.sha(f) for f in files}}
 f=WORK/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 p=pd.read_csv(INPUT/'picks.csv');edges=pd.read_csv(INPUT/'differential_times.csv');times=pd.to_datetime(p.time_utc,utc=True,format='ISO8601');safe=(times>=pd.Timestamp('2019-07-04T00:00:10Z'))&(times<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(p.loc[~safe,'pick_id']);mask=~edges.pick_id_a.isin(bad)&~edges.pick_id_b.isin(bad)
 p[safe].to_csv(WORK/'picks.csv',index=False);edges[mask].to_csv(WORK/'differential_times.csv',index=False);p[~safe].to_csv(WORK/'boundary_picks.csv',index=False);pd.DataFrame({'cc_processing_edge_index':range(int(mask.sum())),'frozen_edge_index':edges.index[mask]}).to_csv(WORK/'edge_index_map.csv',index=False)
 old_windows=H.load_windows(OLD/'cc_windows.npz');old_audit=pd.read_csv(OLD/'waveform_windows.csv');assert not old_audit.duplicated(['pick_id','seed_id']).any();audit={(r['pick_id'],r['seed_id']):r for r in old_audit.to_dict('records')};print('Reusable cached windows',len(old_windows),flush=True)
 scalar=load('scalar39',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py');original=scalar.extract_file
 def cached_extract(job):
  path,rows=job;data={};records=[];missing=[]
  for row in rows:
   pid,seed,phase,time=row;key=(pid,seed)
   if key not in audit:missing.append(row);continue
   record=audit[key];assert record['path']==path;records.append(record.copy())
   if record['status']=='ok':assert pid+'|'+seed in old_windows;data[pid+'|'+seed]=old_windows[pid+'|'+seed]
  if missing:
   new,extra=original((path,missing));data.update(new);records.extend(extra)
  return data,records
 scalar.extract_file=cached_extract;scalar.PRE=WORK;scalar.OUT=WORK;scalar.prepare_cc()
 measured=pd.read_csv(WORK/'cc_measurements.csv');measured.index=edges.index[mask];excluded=edges[~mask].copy();excluded['accepted']=False;excluded['reason']='outside_historical_padded_window'
 for col in ['lag_s','cc','cc_arrival_difference_s']:excluded[col]=np.nan
 scalar_full=pd.concat([measured,excluded]).sort_index();assert len(scalar_full)==len(edges);scalar_full.to_csv(OUT/'scalar_measurements.csv',index=False)
 del old_windows,audit,old_audit
 windows=H.load_windows(WORK/'cc_windows.npz');meta=pd.read_csv(WORK/'waveform_windows.csv').set_index(['pick_id','seed_id']);result,vector_audit=H.measure_vector_s(scalar_full,p.set_index('pick_id'),meta,windows)
 result.to_csv(OUT/'cc_measurements.csv',index=False);vector_audit.to_csv(OUT/'vector_s_audit.csv',index=False)
 previous=pd.read_csv(HERE/'export/38_vector_s/cc_measurements.csv');keys=['pick_id_a','pick_id_b'];q=previous.merge(result,on=keys,suffixes=('_old','_new'),validate='one_to_one');assert len(q)==len(previous);assert q.accepted_old.equals(q.accepted_new)
 accepted=q[q.accepted_old];error=float(np.max(abs(accepted.cc_arrival_difference_s_old-accepted.cc_arrival_difference_s_new)));assert error<1e-8
 M.save(OUT/'measurement_checks.json',{'old_edges_preserved':len(q),'old_acceptance_identical':True,'old_accepted_difference_max_s':error,'accepted_P':int((result.accepted&result.phase.eq('P')).sum()),'accepted_S':int((result.accepted&result.phase.eq('S')).sum())})
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_checks.json').read_text(),flush=True)
if __name__=='__main__':main()
