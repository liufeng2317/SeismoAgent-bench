#!/usr/bin/env python3
"""Count frozen-neighbor pair support lost to absolute-model residual screening."""
from pathlib import Path
import pandas as pd,json
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/34_joint_confirmation'
p=pd.read_csv(OUT/'inputs/all_phases.csv');pairs=pd.read_csv(OUT/'inputs/pair_status.csv');status=pd.read_csv(OUT/'coverage_diagnosis.csv');events=pd.read_csv(OUT/'inputs/events.csv');held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'])
rows=[]
for label,q in [('historical',p[p.probability.ge(.5)&p.residual_s_nll.abs().le(.5)]),('probability_only',p[p.probability.ge(.5)])]:
 q=q[~q.duplicated(['event_id','instrument_id','phase'],keep=False)].copy();q['key']=q.instrument_id+':'+q.phase;lookup={eid:set(g.key) for eid,g in q.groupby('event_id')};support=set();nrows=0;npairs=0
 for a,b in pairs[['event_id_a','event_id_b']].itertuples(index=False,name=None):
  keys=lookup.get(a,set())&lookup.get(b,set())
  if len(keys)<6 or len({k.split(':')[0] for k in keys})<4:continue
  train=[k for k in keys if k.split(':')[0] not in held]
  if train:support.update([a,b]);npairs+=1;nrows+=len(train)
 for r in status.itertuples():rows.append({'event_id':r.event_id,'current_status':r.coverage_status,'filter':label,'has_candidate_training_pair':r.event_id in support})
 print(label,'pairs',npairs,'training edges',nrows,flush=True)
t=pd.DataFrame(rows);t.to_csv(OUT/'prefilter_support.csv',index=False);summary=t.groupby(['filter','current_status']).has_candidate_training_pair.agg(['size','sum']);summary.to_csv(OUT/'prefilter_support_summary.csv');print(summary.to_string(),flush=True)
