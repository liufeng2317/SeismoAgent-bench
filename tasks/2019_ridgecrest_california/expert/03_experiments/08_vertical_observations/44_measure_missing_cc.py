#!/usr/bin/env python3
"""Append directly repicked missing-P correlations without altering the historical pair graph."""
from pathlib import Path
import importlib.util,json
import pandas as pd
import numpy as np
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/44_missing_p_observations';SRC=HERE/'export/42_vertical_p_observations';GRAPH=HERE/'export/39_support_aware_pairs';WORK=OUT/'cc_processing'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('engine42cc',HERE/'03_experiments/07_joint_location/33_joint_location.py')
def admit_against_existing():
 # Enforce the frozen different-event onset-uniqueness rule against old data too.
 raw=OUT/'extracted_picks.csv'
 if not raw.exists():raw.write_bytes((OUT/'new_picks.csv').read_bytes())
 new=pd.read_csv(raw);assert len(new)==json.loads((OUT/'extraction_summary.json').read_text())['admitted_after_association']
 existing=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',low_memory=False);prior=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);old=pd.concat([existing,prior],ignore_index=True).drop_duplicates('pick_id');old=old[old.phase.eq('P')&old.event_id.notna()].copy();old['epoch']=pd.to_datetime(old.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
 audit=new[['pick_id','event_id','instrument_id','time_utc']].copy();audit['admitted']=True;audit['conflicting_old_pick_ids']=''
 for instrument,g in new.groupby('instrument_id'):
  o=old[old.instrument_id.eq(instrument)].sort_values('epoch');times=o.epoch.to_numpy()
  for i,r in g.iterrows():
   time=float(pd.Timestamp(r.time_utc).timestamp());lo=np.searchsorted(times,time-.100001,side='left');hi=np.searchsorted(times,time+.100001,side='right');conflict=o.iloc[lo:hi];conflict=conflict[conflict.event_id.ne(r.event_id)]
   if len(conflict):audit.loc[i,['admitted','conflicting_old_pick_ids']]=[False,';'.join(conflict.pick_id)]
 audit.to_csv(OUT/'onset_admission.csv',index=False);admitted=new[audit.admitted];admitted.to_csv(OUT/'new_picks.csv',index=False);pd.concat([prior,admitted],ignore_index=True).to_csv(OUT/'inputs/all_phases.csv',index=False)
 return dict(extraction_admitted=len(new),old_onset_collisions=int((~audit.admitted).sum()),final_new_P=len(admitted))

def main():
 WORK.mkdir(exist_ok=True)
 for f,h in json.loads((OUT/'target_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 admission=admit_against_existing()
 files=[Path(__file__),OUT/'extracted_picks.csv',OUT/'onset_admission.csv',HERE/'export/10_validate_catalog/phases.csv',OUT/'target_design.json',OUT/'new_picks.csv',OUT/'inputs/all_phases.csv',SRC/'cc_measurements.csv',GRAPH/'inputs/differential_times.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py']
 design={'round':23,'intervention':'New directly estimated missing P only, same historical event-pair graph and scalar CC rules; all historical measurements reused unchanged.','source_sha256':{str(f):M.sha(f) for f in files}}
 path=WORK/'design.json'
 if path.exists():assert json.loads(path.read_text())==design
 else:M.save(path,design)
 allph=pd.read_csv(OUT/'inputs/all_phases.csv',low_memory=False);picks=allph[allph.phase.eq('P')&(allph.probability.ge(.7)|allph.pick_id.str.startswith('mp44_'))].sort_values('probability',ascending=False).drop_duplicates(['event_id','instrument_id']);pairs=pd.read_csv(GRAPH/'inputs/differential_times.csv')[['event_id_a','event_id_b']].drop_duplicates();rows=[]
 for instrument,g in picks.groupby('instrument_id'):
  g=g.set_index('event_id');epochs=pd.to_datetime(g.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
  for r in pairs.itertuples():
   if r.event_id_a not in g.index or r.event_id_b not in g.index:continue
   if not (g.loc[r.event_id_a,'pick_id'].startswith('mp44_') or g.loc[r.event_id_b,'pick_id'].startswith('mp44_')):continue
   rows.append(dict(event_id_a=r.event_id_a,event_id_b=r.event_id_b,pick_id_a=g.loc[r.event_id_a,'pick_id'],pick_id_b=g.loc[r.event_id_b,'pick_id'],instrument_id=instrument,phase='P',observed_dt_s=float(epochs[r.event_id_a]-epochs[r.event_id_b]),training=True))
 edges=pd.DataFrame(rows,columns=['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase','observed_dt_s','training']);edges.to_csv(OUT/'new_differential_times.csv',index=False)
 picks=picks[picks.pick_id.isin(set(edges.pick_id_a)|set(edges.pick_id_b))]
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
 M.save(OUT/'measurement_checks.json',dict(admission,**{'old_acceptance_identical':True,'old_rows_preserved':len(old),'new_candidate_edges':len(new),'new_accepted_P':int(new.accepted.sum()),'new_accepted_S':0,'new_held_edges':0,'accepted_P':int((combined.accepted&combined.phase.eq('P')).sum()),'accepted_S':int((combined.accepted&combined.phase.eq('S')).sum())}))
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_checks.json').read_text(),flush=True)
if __name__=='__main__':main()
