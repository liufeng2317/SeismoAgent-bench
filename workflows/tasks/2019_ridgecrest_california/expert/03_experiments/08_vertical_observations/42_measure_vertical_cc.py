#!/usr/bin/env python3
"""Append vertical P correlations without altering the historical pair graph."""
from pathlib import Path
import importlib.util,json
import pandas as pd
import numpy as np
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/42_vertical_p_observations';SRC=HERE/'export/39_support_aware_pairs';WORK=OUT/'cc_processing'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('engine42cc',HERE/'03_experiments/07_joint_location/33_joint_location.py')
def main():
 WORK.mkdir(exist_ok=True)
 for f,h in json.loads((OUT/'target_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 files=[Path(__file__),OUT/'target_design.json',OUT/'new_picks.csv',SRC/'cc_measurements.csv',SRC/'inputs/differential_times.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py']
 design={'round':21,'intervention':'New vertical P only, same historical event-pair graph and scalar CC rules; all historical measurements reused unchanged.','source_sha256':{str(f):M.sha(f) for f in files}}
 path=WORK/'design.json'
 if path.exists():assert json.loads(path.read_text())==design
 else:M.save(path,design)
 picks=pd.read_csv(OUT/'new_picks.csv');pairs=pd.read_csv(SRC/'inputs/differential_times.csv')[['event_id_a','event_id_b']].drop_duplicates();rows=[]
 for instrument,g in picks.groupby('instrument_id'):
  g=g.set_index('event_id');epochs=pd.to_datetime(g.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
  for r in pairs.itertuples():
   if r.event_id_a not in g.index or r.event_id_b not in g.index:continue
   rows.append(dict(event_id_a=r.event_id_a,event_id_b=r.event_id_b,pick_id_a=g.loc[r.event_id_a,'pick_id'],pick_id_b=g.loc[r.event_id_b,'pick_id'],instrument_id=instrument,phase='P',observed_dt_s=float(epochs[r.event_id_a]-epochs[r.event_id_b]),training=True))
 edges=pd.DataFrame(rows,columns=['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase','observed_dt_s','training']);edges.to_csv(OUT/'new_differential_times.csv',index=False)
 times=pd.to_datetime(picks.time_utc,utc=True,format='ISO8601');safe=(times>=pd.Timestamp('2019-07-04T00:00:10Z'))&(times<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(picks.loc[~safe,'pick_id']);mask=~edges.pick_id_a.isin(bad)&~edges.pick_id_b.isin(bad)
 picks[safe].to_csv(WORK/'picks.csv',index=False);edges[mask].to_csv(WORK/'differential_times.csv',index=False);picks[~safe].to_csv(WORK/'boundary_picks.csv',index=False)
 if mask.any():
  scalar=load('scalar42',files[-1]);scalar.PRE=WORK;scalar.OUT=WORK;scalar.prepare_cc();measured=pd.read_csv(WORK/'cc_measurements.csv');measured.index=edges.index[mask]
 else:measured=pd.DataFrame()
 excluded=edges[~mask].copy();excluded['accepted']=False;excluded['reason']='outside_historical_padded_window'
 for col in ['lag_s','cc','cc_arrival_difference_s']:excluded[col]=np.nan
 new=pd.concat([measured,excluded]).sort_index();assert len(new)==len(edges);new.to_csv(OUT/'new_cc_measurements.csv',index=False)
 old=pd.read_csv(SRC/'cc_measurements.csv');combined=pd.concat([old,new],ignore_index=True);combined.to_csv(OUT/'cc_measurements.csv',index=False)
 reread=pd.read_csv(OUT/'cc_measurements.csv');pd.testing.assert_frame_equal(old,reread.iloc[:len(old)][old.columns],check_dtype=False,rtol=1e-12,atol=1e-10)
 assert not combined.duplicated(['pick_id_a','pick_id_b']).any()
 M.save(OUT/'measurement_checks.json',{'old_acceptance_identical':True,'old_rows_preserved':len(old),'new_candidate_edges':len(new),'new_accepted_P':int(new.accepted.sum()),'new_accepted_S':0,'new_held_edges':0,'accepted_P':int((combined.accepted&combined.phase.eq('P')).sum()),'accepted_S':int((combined.accepted&combined.phase.eq('S')).sum())})
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_checks.json').read_text(),flush=True)
if __name__=='__main__':main()
