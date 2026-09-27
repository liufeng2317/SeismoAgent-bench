#!/usr/bin/env python3
"""Measure all confirmation edges using the frozen scalar P and vector S rules."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];ROOT=HERE/'export/51_confirmation';OUT=ROOT;SRC=HERE/'export/48_differential_augmentation/refreshed';WORK=OUT/'cc_processing'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=load('helper48',DIR.parent/'07_joint_location/_cc_measurements.py');M=H._V.M
class ManifestAdapter:
 def __getattr__(self,key):return getattr(pd,key)
 def read_csv(self,path,*args,**kw):
  if Path(path).resolve()==(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv').resolve():path=HERE/'export/45_added_station/waveform_inputs.csv'
  return pd.read_csv(path,*args,**kw)
def main():
 WORK.mkdir(exist_ok=True)
 for p,h in json.loads((ROOT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(p))==h
 files=[Path(__file__),Path(H.__file__),Path(H._V.__file__),ROOT/'design.json',OUT/'inputs/differential_times.csv',OUT/'inputs/picks.csv',ROOT/'graph_design.json',HERE/'export/45_added_station/waveform_inputs.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py'];design={'round':30,'method':'Unchanged scalar P and vector S, direct extraction of new edge windows; original manifest read redirected only to the verified augmented351+9 manifest. Fresh confirmation edge measurements; no location outcomes used.','source_sha256':{str(f):M.sha(f) for f in files}}
 dest=WORK/'design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 p=pd.read_csv(OUT/'inputs/picks.csv',low_memory=False);edges=pd.read_csv(OUT/'inputs/differential_times.csv');t=pd.to_datetime(p.time_utc,utc=True,format='ISO8601');safe=(t>=pd.Timestamp('2019-07-04T00:00:10Z'))&(t<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(p.loc[~safe,'pick_id']);mask=~edges.pick_id_a.isin(bad)&~edges.pick_id_b.isin(bad);p[safe].to_csv(WORK/'picks.csv',index=False);edges[mask].to_csv(WORK/'differential_times.csv',index=False);p[~safe].to_csv(WORK/'boundary_picks.csv',index=False)
 scalar=load('scalar48',files[-1]);scalar.pd=ManifestAdapter();scalar.PRE=WORK;scalar.OUT=WORK;scalar.prepare_cc();measured=pd.read_csv(WORK/'cc_measurements.csv');measured.index=edges.index[mask];excluded=edges[~mask].copy();excluded['accepted']=False;excluded['reason']='outside_historical_padded_window'
 for col in ['lag_s','cc','cc_arrival_difference_s']:excluded[col]=np.nan
 full=pd.concat([measured,excluded]).sort_index();full.to_csv(OUT/'new_scalar_measurements.csv',index=False);windows=H.load_windows(WORK/'cc_windows.npz');meta=pd.read_csv(WORK/'waveform_windows.csv').set_index(['pick_id','seed_id']);new,audit=H.measure_vector_s(full,p.set_index('pick_id'),meta,windows);new.to_csv(OUT/'new_cc_measurements.csv',index=False);audit.to_csv(OUT/'vector_s_audit.csv',index=False)
 new.to_csv(OUT/'cc_measurements.csv',index=False);assert not new.duplicated(['pick_id_a','pick_id_b']).any()
 M.save(OUT/'measurement_checks.json',{'candidates':len(new),'accepted_P':int((new.accepted&new.phase.eq('P')).sum()),'accepted_S':int((new.accepted&new.phase.eq('S')).sum()),'held_edges':int((new.accepted&~new.training).sum()),'reserve3_used':True})
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_checks.json').read_text(),flush=True)
if __name__=='__main__':main()
