#!/usr/bin/env python3
"""Freeze a moment-envelope depth screen; preserve all stage48 observations."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/50_uncertain_depth_pairs';SRC=HERE/'export/48_differential_augmentation/refreshed';BASE=HERE/'export/45_added_station';GRAPH=SRC
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
 freeze(OUT/'design.json',{'round':29,'candidate':'Depth-uncertainty-aware candidate pairing on original NLL posterior moments; original stage48 model, data and relative-only new EQ S policy. No adoption of rejected stage49 ratio.','graph':'Horizontal center distance<=3km. Original posterior mean depth +/-2 posterior sigma, clipped to original [0,25] domain, supplies a moment envelope for each event. Candidate lower separation=sqrt(horizontal_distance^2 + minimum_gap_between_depth_envelopes^2)<=3km. Invalid moments fall back to the original point depth. This is an approximate candidate screen, not a calibrated joint95% probability or proof of true proximity. No horizontal uncertainty expansion. At least6 shared phases at4 instruments, at least1 training phase; rank by descending shared training instruments, phases, then ORIGINAL center3D distance and eventID; top12 each target. Union all historical pairs. No envelope-factor, radius or neighbor-cap scan.','data':'Original PN eligibility0.5, unique phase keys; admitted direct picks unchanged. Keep all old targets/supports/flags/absolute observations/CC candidate decisions. New supports retain original absolute observations. Six held stations unchanged. Exclude original development/transfer/first reserve and unused reserve3 from supports.','comparison':'Stage48 is the fixed historical control.16 matched solves, original gate set unchanged; all575/1408/1524 historical held CC RMS<=1.05 stage48; all reference medians<=1.10 stage48 and45. No rematching, target dropping or fresh confirmation unless every gate passes.','source_sha256':{str(p):M.sha(p) for p in files}})
 link(HERE/'export/35_cc_observation_selection/native_controls',OUT/'native_controls')
 dest=OUT;(dest/'inputs').mkdir(exist_ok=True)
 events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');original=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',low_memory=False);old=pd.read_csv(SRC/'inputs/events.csv');oldph=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);targets=old[old.role.eq('reserve')];assert len(targets)==300
 excluded=set()
 for f in [HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv',HERE/'docs/optimization_reserved_events_v3.csv']:excluded.update(pd.read_csv(f).event_id)
 assert not set(old.event_id)&set(pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv').event_id)
 pool=events[events.in_v1_working_catalog&~events.event_id.isin(excluded)].sort_values('event_id').reset_index(drop=True);held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'])
 good=original[original.probability.ge(.5)&original.event_id.isin(pool.event_id)].copy();good=good[~good.duplicated(['event_id','instrument_id','phase'],keep=False)]
 additional=oldph[~oldph.pick_id.isin(original.pick_id)].copy();assert additional.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_')).all();good=pd.concat([good,additional],ignore_index=True);assert not good.duplicated(['event_id','instrument_id','phase']).any();good['key']=good.instrument_id+':'+good.phase
 lookup={eid:g.set_index('key') for eid,g in good.groupby('event_id')};keys={eid:set(g.index) for eid,g in lookup.items()};train={eid:{k for k in v if k.split(':')[0] not in held} for eid,v in keys.items()}
 oldcc=pd.read_csv(SRC/'cc_measurements.csv');pairs=set(map(tuple,pd.read_csv(GRAPH/'inputs/pair_status.csv')[['event_id_a','event_id_b']].to_numpy()));pairs.update(map(tuple,oldcc[['event_id_a','event_id_b']].to_numpy()));previous=set(pairs);xyz=pool[M.XYZ].to_numpy();selections=[]
 mean=pool.posterior_mean_depth_km.to_numpy(float);sigma=pool.posterior_sigma_depth_km.to_numpy(float);valid=np.isfinite(mean)&np.isfinite(sigma)&(sigma>=0)&(mean>=0)&(mean<=25);lo=np.where(valid,np.maximum(0,mean-2*sigma),xyz[:,2]);hi=np.where(valid,np.minimum(25,mean+2*sigma),xyz[:,2]);envelope=dict(zip(pool.event_id,zip(lo,hi)))
 for event in targets.itertuples():
  d=np.linalg.norm(xyz-np.array([getattr(event,k) for k in M.XYZ]),axis=1);horizontal=np.linalg.norm(xyz[:,:2]-np.array([event.x_km,event.y_km]),axis=1);low,high=envelope[event.event_id];gap=np.maximum(np.maximum(lo-high,low-hi),0);lower=np.hypot(horizontal,gap);rank=[]
  for i in np.flatnonzero((lower<=3)&pool.event_id.ne(event.event_id).to_numpy()):
   eid=pool.event_id.iloc[i];shared=keys.get(event.event_id,set())&keys.get(eid,set());ct=train.get(event.event_id,set())&train.get(eid,set());stations={k.split(':')[0] for k in shared};ts={k.split(':')[0] for k in ct}
   if len(shared)>=6 and len(stations)>=4 and ct:rank.append((-len(ts),-len(ct),float(d[i]),eid))
  for ns,npick,distance,eid in sorted(rank)[:12]:
   pair=tuple(sorted([event.event_id,eid]));pairs.add(pair);selections.append({'target_event_id':event.event_id,'neighbor_event_id':eid,'shared_training_stations':-ns,'shared_training_phases':-npick,'distance_km':distance,'old_pair':pair in previous,'horizontal_km':float(horizontal[pool.index[pool.event_id.eq(eid)][0]]),'envelope_min_separation_km':float(lower[pool.index[pool.event_id.eq(eid)][0]]),'outside_old_3d_radius':distance>3})
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
