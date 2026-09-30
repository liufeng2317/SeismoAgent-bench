#!/usr/bin/env python3
"""Append new-station scalar P / vector S correlations on the unchanged pair graph."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/45_added_station';SRC=HERE/'export/44_missing_p_observations';GRAPH=HERE/'export/39_support_aware_pairs';WORK=OUT/'cc_processing'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=load('measure45helper',DIR.parent/'07_joint_location/_cc_measurements.py');M=H._V.M
class ManifestAdapter:
 """Only redirect the frozen extractor's manifest read; leave global pandas alone."""
 def __getattr__(self,name):return getattr(pd,name)
 def read_csv(self,path,*a,**kw):
  original=HERE/'export/01_prepare_inputs/full/waveform_inputs.csv'
  if Path(path).resolve()==original.resolve():path=OUT/'waveform_inputs.csv'
  return pd.read_csv(path,*a,**kw)
def main():
 WORK.mkdir(exist_ok=True)
 files=[Path(__file__),Path(H.__file__),Path(H._V.__file__),OUT/'target_design.json',OUT/'new_picks.csv',OUT/'waveform_inputs.csv',OUT/'inputs/all_phases.csv',SRC/'cc_measurements.csv',GRAPH/'inputs/differential_times.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py']
 design={'round':24,'intervention':'New LB.DAC observations only; original scalar P and frozen two-horizontal vector S. Manifest read adapter only; native250Hz filtered by existing extractor before100Hz CC interpolation. No old observation or decision changes.','source_sha256':{str(f):M.sha(f) for f in files}}
 path=WORK/'design.json'
 if path.exists():assert json.loads(path.read_text())==design
 else:M.save(path,design)
 picks=pd.read_csv(OUT/'new_picks.csv');pairs=pd.read_csv(GRAPH/'inputs/differential_times.csv')[['event_id_a','event_id_b']].drop_duplicates();rows=[]
 for phase,g in picks.groupby('phase'):
  g=g.set_index('event_id');epochs=pd.to_datetime(g.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
  for r in pairs.itertuples():
   if r.event_id_a not in g.index or r.event_id_b not in g.index:continue
   rows.append(dict(event_id_a=r.event_id_a,event_id_b=r.event_id_b,pick_id_a=g.loc[r.event_id_a,'pick_id'],pick_id_b=g.loc[r.event_id_b,'pick_id'],instrument_id='LB.DAC..HH',phase=phase,observed_dt_s=float(epochs[r.event_id_a]-epochs[r.event_id_b]),training=True))
 edges=pd.DataFrame(rows,columns=['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase','observed_dt_s','training']);edges.to_csv(OUT/'new_differential_times.csv',index=False)
 picks=picks[picks.pick_id.isin(set(edges.pick_id_a)|set(edges.pick_id_b))];times=pd.to_datetime(picks.time_utc,utc=True,format='ISO8601');safe=(times>=pd.Timestamp('2019-07-04T00:00:10Z'))&(times<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(picks.loc[~safe,'pick_id']);mask=~edges.pick_id_a.isin(bad)&~edges.pick_id_b.isin(bad)
 picks[safe].to_csv(WORK/'picks.csv',index=False);edges[mask].to_csv(WORK/'differential_times.csv',index=False);picks[~safe].to_csv(WORK/'boundary_picks.csv',index=False)
 assert mask.any(),'No new CC candidates; stop without claiming an optimization.'
 scalar=load('scalar45',files[-1]);scalar.pd=ManifestAdapter();scalar.PRE=WORK;scalar.OUT=WORK;scalar.prepare_cc();measured=pd.read_csv(WORK/'cc_measurements.csv');measured.index=edges.index[mask]
 excluded=edges[~mask].copy();excluded['accepted']=False;excluded['reason']='outside_historical_padded_window'
 for col in ['lag_s','cc','cc_arrival_difference_s']:excluded[col]=np.nan
 scalar_full=pd.concat([measured,excluded]).sort_index();assert len(scalar_full)==len(edges);scalar_full.to_csv(OUT/'new_scalar_measurements.csv',index=False)
 windows=H.load_windows(WORK/'cc_windows.npz');meta=pd.read_csv(WORK/'waveform_windows.csv').set_index(['pick_id','seed_id']);new,audit=H.measure_vector_s(scalar_full,picks.set_index('pick_id'),meta,windows);audit.to_csv(OUT/'vector_s_audit.csv',index=False);new.to_csv(OUT/'new_cc_measurements.csv',index=False)
 old=pd.read_csv(SRC/'cc_measurements.csv');combined=pd.concat([old,new],ignore_index=True);combined.to_csv(OUT/'cc_measurements.csv',index=False);reread=pd.read_csv(OUT/'cc_measurements.csv');pd.testing.assert_frame_equal(old,reread.iloc[:len(old)][old.columns],check_dtype=False,rtol=1e-12,atol=1e-10);assert not combined.duplicated(['pick_id_a','pick_id_b']).any()
 M.save(OUT/'measurement_checks.json',{'old_acceptance_identical':True,'old_rows_preserved':len(old),'new_candidate_edges':len(new),'new_accepted_P':int((new.accepted&new.phase.eq('P')).sum()),'new_accepted_S':int((new.accepted&new.phase.eq('S')).sum()),'new_held_edges':0,'accepted_P':int((combined.accepted&combined.phase.eq('P')).sum()),'accepted_S':int((combined.accepted&combined.phase.eq('S')).sum())})
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_checks.json').read_text(),flush=True)
if __name__=='__main__':main()
