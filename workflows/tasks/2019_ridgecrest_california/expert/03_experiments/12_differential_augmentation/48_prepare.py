#!/usr/bin/env python3
"""Freeze a differential-only S control and an observation-aware graph refresh."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/48_differential_augmentation';SRC=HERE/'export/47_missing_s_observations';BASE=HERE/'export/45_added_station';GRAPH=HERE/'export/39_support_aware_pairs'
s=importlib.util.spec_from_file_location('base48',DIR.parent/'07_joint_location/33_joint_location.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
def freeze(path,value):
 if path.exists():assert json.loads(path.read_text())==value,f'Frozen identity changed: {path}'
 else:M.save(path,value)
def link(source,target):
 if not target.exists():target.symlink_to(source)
 assert target.resolve()==source.resolve()
def main():
 OUT.mkdir(exist_ok=True)
 files=list(DIR.glob('*.py'))+[SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv',SRC/'cc_measurements.csv',SRC/'run.json',BASE/'run.json',GRAPH/'inputs/pair_status.csv',HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'docs/optimization_reserved_events_v3.csv',HERE/'03_experiments/07_joint_location/39_prepare_graph.py']
 freeze(OUT/'design.json',{'round':27,'candidate':'Differential-only new EQTransformer S observations with the existing support-aware graph refreshed on augmented phase availability. The refreshed branch is the sole promotion candidate; fixed-graph branch is attribution only. No retrospective selection between branches.','control':'fixed: stage47 cohort and complete CC rows, but omit ALL eqs47_ observations from absolute objective only. Retain their prediction rows and CC measurements. Compare with stage45 original absolute observations and stage47 full S usage.','graph':'refreshed: same3D radius<=3km, at least6 shared eligible phases at4 stations, at least1 training phase, rank descending shared TRAINING stations then phases, increasing distance and eventID; retain top12 per target and union every old pair. Original PN eligibility>=0.5 and unique event/instrument/phase unchanged. Previously admitted qualified direct P/S observations supply new phase keys without equating their model scores to PN probability. Keep old supports, add selected supports, never drop scored targets or old CC rows. Exclude all original development/transfer/first-reserve IDs and unused reserve3 from new support pool.','absolute_policy':'All pre-stage47 observations remain absolute, with unchanged errors. Every eqs47_ S observation is relative-only in both branches; no event/station-specific exclusions. New support events keep all original absolute observations. Original1D fields and Huber CC0.05s remain.','validation':'16 matched solves per branch; original gates unchanged. Fixed575 and1408 held CC scored separately and RMS<=1.05 each of stage45 and47. Reference medians<=1.10 stage45,47 and39, plus original native/matched controls. Same300 targets and old auxiliary eligibility. Fresh reserve3 remains unused. Fixed control must reproduce stage45 absolute objective/Jacobian numerically. No weight, radius, cap or CC-threshold scan.','source_sha256':{str(p):M.sha(p) for p in files}})
 fixed=OUT/'fixed';fixed.mkdir(exist_ok=True)
 for name in ['inputs','cc_measurements.csv']:link(SRC/name,fixed/name)
 for branch in ['fixed','refreshed']:
  path=OUT/branch;path.mkdir(exist_ok=True);link(HERE/'export/35_cc_observation_selection/native_controls',path/'native_controls')
 dest=OUT/'refreshed';(dest/'inputs').mkdir(exist_ok=True)
 events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');original=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',low_memory=False);old=pd.read_csv(SRC/'inputs/events.csv');oldph=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);targets=old[old.role.eq('reserve')];assert len(targets)==300
 excluded=set()
 for f in [HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv',HERE/'docs/optimization_reserved_events_v3.csv']:excluded.update(pd.read_csv(f).event_id)
 assert not set(old.event_id)&set(pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv').event_id)
 pool=events[events.in_v1_working_catalog&~events.event_id.isin(excluded)].sort_values('event_id').reset_index(drop=True);held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'])
 good=original[original.probability.ge(.5)&original.event_id.isin(pool.event_id)].copy();good=good[~good.duplicated(['event_id','instrument_id','phase'],keep=False)]
 additional=oldph[~oldph.pick_id.isin(original.pick_id)].copy();assert additional.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_')).all();good=pd.concat([good,additional],ignore_index=True);assert not good.duplicated(['event_id','instrument_id','phase']).any();good['key']=good.instrument_id+':'+good.phase
 lookup={eid:g.set_index('key') for eid,g in good.groupby('event_id')};keys={eid:set(g.index) for eid,g in lookup.items()};train={eid:{k for k in v if k.split(':')[0] not in held} for eid,v in keys.items()}
 oldcc=pd.read_csv(SRC/'cc_measurements.csv');pairs=set(map(tuple,pd.read_csv(GRAPH/'inputs/pair_status.csv')[['event_id_a','event_id_b']].to_numpy()));pairs.update(map(tuple,oldcc[['event_id_a','event_id_b']].to_numpy()));previous=set(pairs);xyz=pool[M.XYZ].to_numpy();selections=[]
 for event in targets.itertuples():
  d=np.linalg.norm(xyz-np.array([getattr(event,k) for k in M.XYZ]),axis=1);rank=[]
  for i in np.flatnonzero((d<=3)&pool.event_id.ne(event.event_id).to_numpy()):
   eid=pool.event_id.iloc[i];shared=keys.get(event.event_id,set())&keys.get(eid,set());ct=train.get(event.event_id,set())&train.get(eid,set());stations={k.split(':')[0] for k in shared};ts={k.split(':')[0] for k in ct}
   if len(shared)>=6 and len(stations)>=4 and ct:rank.append((-len(ts),-len(ct),float(d[i]),eid))
  for ns,npick,distance,eid in sorted(rank)[:12]:
   pair=tuple(sorted([event.event_id,eid]));pairs.add(pair);selections.append({'target_event_id':event.event_id,'neighbor_event_id':eid,'shared_training_stations':-ns,'shared_training_phases':-npick,'distance_km':distance,'old_pair':pair in previous})
 ids=set(old.event_id)|{e for pair in pairs for e in pair};extra=pool[pool.event_id.isin(ids-set(old.event_id))].copy();extra['role']='support';extra_ph=original[original.event_id.isin(extra.event_id)].copy();counts=extra_ph[~extra_ph.instrument_id.isin(held)].assign(is_s=lambda d:d.phase.eq('S')).groupby('event_id').agg(n=('pick_id','size'),n_s=('is_s','sum')).reindex(extra.event_id,fill_value=0);extra['auxiliary_eligible']=(counts.n.ge(10)&counts.n_s.ge(3)).to_numpy();cohort=pd.concat([old,extra[old.columns]],ignore_index=True);allph=pd.concat([oldph,extra_ph],ignore_index=True);assert cohort.event_id.is_unique and allph.pick_id.is_unique and not set(cohort.event_id)&excluded
 existing=set(map(tuple,oldcc[['pick_id_a','pick_id_b']].to_numpy()));rows=[];pair_status=[]
 for a,b in sorted(pairs):
  common=sorted(keys.get(a,set())&keys.get(b,set()));eligible=len(common)>=6 and len({k.split(':')[0] for k in common})>=4;pair_status.append({'event_id_a':a,'event_id_b':b,'old_pair':(a,b) in previous,'eligible':eligible})
  if not eligible:continue
  for key in common:
   x,y=lookup[a].loc[key],lookup[b].loc[key]
   if (x.pick_id,y.pick_id) in existing:continue
   rows.append({'event_id_a':a,'event_id_b':b,'pick_id_a':x.pick_id,'pick_id_b':y.pick_id,'instrument_id':x.instrument_id,'phase':x.phase,'observed_dt_s':(pd.Timestamp(x.time_utc)-pd.Timestamp(y.time_utc)).total_seconds(),'training':x.instrument_id not in held})
 edges=pd.DataFrame(rows);used=set(edges.pick_id_a)|set(edges.pick_id_b)
 for name,table in [('events.csv',cohort),('all_phases.csv',allph),('picks.csv',allph[allph.pick_id.isin(used)]),('differential_times.csv',edges),('pair_status.csv',pd.DataFrame(pair_status)),('selected_neighbors.csv',pd.DataFrame(selections))]:
  path=dest/'inputs'/name;value=table.to_csv(index=False)
  if path.exists():assert path.read_text()==value
  else:path.write_text(value)
 M.save(OUT/'graph_summary.json',{'targets':len(targets),'old_events':len(old),'events':len(cohort),'new_support_events':len(extra),'old_pairs':len(previous),'all_pairs':len(pairs),'new_candidate_edges':len(edges),'new_candidate_P':int(edges.phase.eq('P').sum()),'new_candidate_S':int(edges.phase.eq('S').sum()),'reserve3_used':False})
 print((OUT/'graph_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
