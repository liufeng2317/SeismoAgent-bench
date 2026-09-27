#!/usr/bin/env python3
"""Freeze reserve/support graph, then reuse the fixed historical CC measurement code."""
from pathlib import Path
import argparse,hashlib,json,importlib.util
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/34_joint_confirmation';INPUT=OUT/'inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 INPUT.mkdir(parents=True,exist_ok=True)
 frozen=HERE/'export/33_joint_location/frozen_candidate.json'
 for p,h in json.loads(frozen.read_text())['sha256'].items():assert sha(Path(p))==h
 reserve=pd.read_csv(HERE/'docs/optimization_reserved_events_v2.csv');assert len(reserve)==300 and reserve.event_id.is_unique
 all_e=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');reserve_e=all_e.set_index('event_id').loc[reserve.event_id].reset_index();assert reserve_e.in_v1_working_catalog.all()
 excluded=set()
 for p in [HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv']:excluded.update(pd.read_csv(p).event_id)
 assert not set(reserve.event_id)&excluded
 pool=all_e[all_e.in_v1_working_catalog&~all_e.event_id.isin(excluded)].sort_values('event_id').reset_index(drop=True)
 xyz=['x_km','y_km','depth_km'];pairs=set();geometry=[]
 for row in reserve_e.itertuples():
  point=np.array([getattr(row,k) for k in xyz]);dist=np.linalg.norm(pool[xyz].to_numpy()-point,axis=1)
  order=np.argsort(dist,kind='stable');use=[i for i in order if pool.event_id.iloc[i]!=row.event_id and dist[i]<=3][:12]
  for i in use:
   a,b=sorted([row.event_id,pool.event_id.iloc[i]]);pairs.add((a,b));geometry.append(dict(reserved_event_id=row.event_id,neighbor_event_id=pool.event_id.iloc[i],distance_km=float(dist[i])))
 p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');ids=set(reserve.event_id)|{v for pair in pairs for v in pair}
 events=pool[pool.event_id.isin(ids)].copy();events['role']=np.where(events.event_id.isin(reserve.event_id),'reserve','support')
 phases=p[p.event_id.isin(ids)].copy();eligible=phases[phases.probability.ge(.5)&phases.residual_s_nll.abs().le(.5)].copy();eligible=eligible[~eligible.duplicated(['event_id','instrument_id','phase'],keep=False)].copy();eligible['key']=eligible.instrument_id+':'+eligible.phase
 lookup={eid:g.set_index('key') for eid,g in eligible.groupby('event_id')};held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'];rows=[];pair_status=[]
 for a,b in sorted(pairs):
  aa=lookup.get(a);bb=lookup.get(b);keys=[] if aa is None or bb is None else sorted(set(aa.index)&set(bb.index));ok=len(keys)>=6 and len({k.split(':')[0] for k in keys})>=4
  pair_status.append(dict(event_id_a=a,event_id_b=b,n_common=len(keys),eligible=ok))
  if not ok:continue
  for k in keys:
   x,y=aa.loc[k],bb.loc[k];rows.append(dict(event_id_a=a,event_id_b=b,pick_id_a=x.pick_id,pick_id_b=y.pick_id,instrument_id=x.instrument_id,phase=x.phase,observed_dt_s=(pd.Timestamp(x.time_utc)-pd.Timestamp(y.time_utc)).total_seconds(),training=x.instrument_id not in held))
 edges=pd.DataFrame(rows);assert len(edges)>0
 used=set(edges.pick_id_a)|set(edges.pick_id_b);ccp=phases[phases.pick_id.isin(used)]
 counts=phases.assign(is_s=phases.phase.eq('S'),training=~phases.instrument_id.isin(held)).query('training').groupby('event_id').agg(n=('pick_id','size'),n_s=('is_s','sum')).reindex(events.event_id,fill_value=0)
 events['auxiliary_eligible']=(counts.n.ge(10)&counts.n_s.ge(3)).to_numpy()
 files=[Path(__file__),frozen,HERE/'docs/optimization_reserved_events_v2.csv',HERE/'docs/optimization_reserved_events_v2.json',HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py',HERE/'export/12_relative_location_pilot/run.json']
 design={'round':13,'stage':'confirmation_prepared_before_waveform_scores','candidate':'Frozen stage33 joint absolute/CC, 50 ms CC error, no tuning.','selection':'All 300 frozen reserve_v2 events. At most 12 nearest original 3D neighbors <=3 km per reserve event, event-ID tie break. Exclude earlier development/transfer/consumed reserve from support. Keep all reserve events, disconnected events and rejected pairs; do not select largest component. No reference data read.','support_role':'Only event pairs incident on at least one fixed reserve event; support chosen before waveform outcomes. Score reserve arrivals and edges incident on reserve. Shared supports make events dependent; report coverage, no independent-event confidence claim.','auxiliary':'At least 10 remaining absolute picks and 3 S per event after fixed six-station omission. Keep all primary events; exclude ineligible from auxiliary solve and its edges, list all statuses. Never replace reserve events.','gates':{'coverage':'All 300 primary reserve events retained. >=210 reserve events have accepted training CC, >=50 reserve events have held CC, >=100 held CC edges, >=240 reserve events auxiliary eligible; otherwise confirmation inconclusive.','prediction':'Held CC RMS <=0.95 absolute-only; held absolute RMS <=1.05 absolute-only and archived same-event original NLL omission (must compute if unavailable).','references':'Identical fixed unambiguous pairs; three horizontal and Shelly depth medians <=1.10 absolute-only and original NLL. No reference fitting.','stability':'Fixed +/-1 km common-start translations: joint mean <=0.10 km and individual P90 <=0.20 km for reserve events. Report omissions and numerical terminations.','boundary':'Reserve near-depth-boundary count no more than original+3.','adoption':'All gates needed before full production; no weights/graph changes based on confirmation scores.'},'n_reserve':300,'n_support':int(events.role.eq('support').sum()),'n_events':len(events),'n_absolute_picks':len(phases),'n_candidate_pairs':len(pairs),'n_eligible_edges':len(edges),'n_auxiliary_eligible_reserve':int((events.role.eq('reserve')&events.auxiliary_eligible).sum()),'source_sha256':{str(f):sha(f) for f in files}}
 path=OUT/'design.json'
 if path.exists():assert json.loads(path.read_text())==design
 else:path.write_text(json.dumps(design,indent=2)+'\n')
 for name,frame in [('events.csv',events),('all_phases.csv',phases),('picks.csv',ccp),('differential_times.csv',edges),('pair_status.csv',pd.DataFrame(pair_status)),('geometric_neighbors.csv',pd.DataFrame(geometry))]:
  target=INPUT/name;text=frame.to_csv(index=False)
  if target.exists():assert target.read_text()==text
  else:target.write_text(text)
 (OUT/'README.md').write_text('# Round13: frozen joint-location confirmation\n\nStatus: graph and eligibility frozen before waveform outcomes. No reference outcome or new location score has been read. All 300 reserve events remain included; their geometry is now used for preparation, so track exposure explicitly.\n\n```json\n'+json.dumps({k:v for k,v in design.items() if k!='source_sha256'},indent=2)+'\n```\n\nWaveform processing reuses stage13 unchanged. Absolute arrivals retain every associated pick; only CC candidates use the historical quality prefilter. Missing/failed CC windows remain recorded, with no replacement. No confirmed gain or full product is available yet.\n')
 print(json.dumps({k:v for k,v in design.items() if k not in ['source_sha256','gates']},indent=2),flush=True)
def cc():
 spec=importlib.util.spec_from_file_location('historical_cc34',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.PRE=INPUT;m.OUT=OUT;m.prepare_cc()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','cc','all'],default='prepare');a=parser.parse_args();prepare()
 if a.stage in ['cc','all']:cc()
