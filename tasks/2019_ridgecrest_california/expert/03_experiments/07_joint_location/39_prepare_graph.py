#!/usr/bin/env python3
"""Augment frozen nearest-neighbor pairs using training-station/phase overlap."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/39_support_aware_pairs';INPUT=OUT/'inputs';OLD=HERE/'export/34_joint_confirmation';PREV=HERE/'export/38_vector_s'
spec=importlib.util.spec_from_file_location('base39',Path(__file__).with_name('33_joint_location.py'));M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

def main():
 INPUT.mkdir(parents=True,exist_ok=True)
 events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');phases=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');old=pd.read_csv(OLD/'inputs/events.csv');targets=old[old.role.eq('reserve')].copy();assert len(targets)==300
 exclude=set()
 for f in [HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv']:exclude.update(pd.read_csv(f).event_id)
 pool=events[events.in_v1_working_catalog&~events.event_id.isin(exclude)].sort_values('event_id').reset_index(drop=True);held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'])
 good=phases[phases.event_id.isin(pool.event_id)&phases.probability.ge(.5)].copy();good=good[~good.duplicated(['event_id','instrument_id','phase'],keep=False)];good['key']=good.instrument_id+':'+good.phase
 lookup={eid:g.set_index('key') for eid,g in good.groupby('event_id')};keys={eid:set(g.index) for eid,g in lookup.items()};train={eid:{k for k in v if k.split(':')[0] not in held} for eid,v in keys.items()}
 oldpairs=pd.read_csv(OLD/'inputs/pair_status.csv');pairs=set(oldpairs[['event_id_a','event_id_b']].itertuples(index=False,name=None));original=set(pairs);selection=[]
 xyz=pool[M.XYZ].to_numpy()
 for event in targets.itertuples():
  point=np.array([getattr(event,k) for k in M.XYZ]);dist=np.linalg.norm(xyz-point,axis=1);rank=[]
  for i in np.flatnonzero((dist<=3)&pool.event_id.ne(event.event_id).to_numpy()):
   eid=pool.event_id.iloc[i];common=keys.get(event.event_id,set())&keys.get(eid,set())
   if len(common)<6 or len({k.split(':')[0] for k in common})<4:continue
   ct=train.get(event.event_id,set())&train.get(eid,set());ns=len({k.split(':')[0] for k in ct})
   if not ct:continue
   rank.append((-ns,-len(ct),float(dist[i]),eid))
  for ns,nphase,d,eid in sorted(rank)[:12]:
   a,b=sorted([event.event_id,eid]);pairs.add((a,b));selection.append({'target_event_id':event.event_id,'neighbor_event_id':eid,'shared_training_stations':-ns,'shared_training_phases':-nphase,'distance_km':d,'already_in_old_graph':(a,b) in original})
 ids=set(old.event_id)|{eid for pair in pairs for eid in pair};cohort=pool[pool.event_id.isin(ids)].copy();cohort['role']=np.where(cohort.event_id.isin(targets.event_id),'reserve','support');allp=phases[phases.event_id.isin(ids)].copy()
 counts=allp[~allp.instrument_id.isin(held)].assign(is_s=lambda f:f.phase.eq('S')).groupby('event_id').agg(n=('pick_id','size'),n_s=('is_s','sum')).reindex(cohort.event_id,fill_value=0);cohort['auxiliary_eligible']=(counts.n.ge(10)&counts.n_s.ge(3)).to_numpy()
 rows=[];pairinfo=[]
 for a,b in sorted(pairs):
  common=sorted(keys.get(a,set())&keys.get(b,set()));ok=len(common)>=6 and len({k.split(':')[0] for k in common})>=4;pairinfo.append({'event_id_a':a,'event_id_b':b,'old_pair':(a,b) in original,'eligible':ok,'n_common':len(common)})
  if not ok:continue
  for key in common:
   x,y=lookup[a].loc[key],lookup[b].loc[key];rows.append({'event_id_a':a,'event_id_b':b,'pick_id_a':x.pick_id,'pick_id_b':y.pick_id,'instrument_id':x.instrument_id,'phase':x.phase,'observed_dt_s':(pd.Timestamp(x.time_utc)-pd.Timestamp(y.time_utc)).total_seconds(),'training':x.instrument_id not in held})
 edges=pd.DataFrame(rows);oldedges=pd.read_csv(PREV/'cc_measurements.csv');assert set(zip(oldedges.pick_id_a,oldedges.pick_id_b))<=set(zip(edges.pick_id_a,edges.pick_id_b));used=set(edges.pick_id_a)|set(edges.pick_id_b)
 files=[Path(__file__),HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',OLD/'design.json',OLD/'inputs/events.csv',OLD/'inputs/pair_status.csv',PREV/'design.json',PREV/'cc_measurements.csv']
 design={'round':18,'cohort_role':'Same 300 exposed targets; retain all old support events, add selected support only. No fresh-confirmation claim.','rule':'Same eligible v1 pool/exclusions and original 3D radius <=3 km as stage34. For each target rank eligible neighbors by descending common TRAINING station count, descending common TRAINING P/S count, increasing distance, then event ID. Take at most 12; union with every original pair. Pair eligibility remains >=6 common phases at >=4 stations, probability>=0.5, no residual cutoff. No waveform outcome/reference/location update used to rank.','measurement_and_location':'Keep stage38 vector-S measurement, unchanged P measurement, and stage37 Huber locator. No waveform threshold or model change.','gates':'Keep stage34 gates. Score all original 575 held CC measurements regardless of new graph eligibility; RMS <=1.05 stage38 on that identical set. Score new held set separately. Compare new graph with matched absolute-only controls on the same enlarged event set; support events are never scored as target substitutes. No graph-parameter scan follows.','n_target':300,'n_old_events':len(old),'n_events':len(cohort),'n_new_support':len(cohort)-len(old),'n_old_pairs':len(original),'n_all_pairs':len(pairs),'n_candidate_edges':len(edges),'source_sha256':{str(f):M.sha(f) for f in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 for name,table in [('events.csv',cohort),('all_phases.csv',allp),('picks.csv',allp[allp.pick_id.isin(used)]),('differential_times.csv',edges),('pair_status.csv',pd.DataFrame(pairinfo)),('selected_neighbors.csv',pd.DataFrame(selection))]:
  f=INPUT/name;value=table.to_csv(index=False)
  if f.exists():assert f.read_text()==value
  else:f.write_text(value)
 print(json.dumps({k:v for k,v in design.items() if k!='source_sha256'},indent=2),flush=True)
if __name__=='__main__':main()
