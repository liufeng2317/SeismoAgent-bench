#!/usr/bin/env python3
"""Account for every reserve target and frozen CC rejection without changing gates."""
from pathlib import Path
import json
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/34_joint_confirmation'
e=pd.read_csv(OUT/'inputs/events.csv');reserve=e[e.role.eq('reserve')].copy();ids=set(e.loc[e.auxiliary_eligible,'event_id']);g=pd.read_csv(OUT/'inputs/geometric_neighbors.csv');cc=pd.read_csv(OUT/'cc_measurements.csv');pairs=pd.read_csv(OUT/'inputs/pair_status.csv');rows=[]
for r in reserve.itertuples():
 q=cc[(cc.event_id_a.eq(r.event_id)|cc.event_id_b.eq(r.event_id))];a=q[q.accepted&q.training&q.event_id_a.isin(ids)&q.event_id_b.isin(ids)];n=int(g.reserved_event_id.eq(r.event_id).sum());ntrain=int(q.training.sum())
 reason='supported' if len(a) else ('auxiliary_ineligible' if not r.auxiliary_eligible else ('no_neighbor_within_3km' if n==0 else ('no_training_pick_edges' if ntrain==0 else 'no_accepted_training_CC')))
 rows.append({'event_id':r.event_id,'period':r.period,'n_geometric_neighbors':n,'n_candidate_edges':len(q),'n_training_candidates':ntrain,'n_accepted_training':len(a),'coverage_status':reason})
t=pd.DataFrame(rows);assert len(t)==300 and t.event_id.is_unique;t.to_csv(OUT/'coverage_diagnosis.csv',index=False)
components=pd.read_csv(OUT/'cc_processing/cc_components.csv');mapping=pd.read_csv(OUT/'cc_processing/edge_index_map.csv');components=components.merge(mapping,left_on='edge_index',right_on='cc_processing_edge_index',validate='many_to_one')
unsupported=set(t.loc[t.coverage_status.eq('no_accepted_training_CC'),'event_id']);mask=cc.training&(cc.event_id_a.isin(unsupported)|cc.event_id_b.isin(unsupported));comp=components[components.frozen_edge_index.isin(cc.index[mask])];counts=comp.status.str.split(';').explode().value_counts();counts.rename_axis('component_reason').rename('n').to_csv(OUT/'unsupported_component_reasons.csv')
result={'event_status_counts':{k:int(v) for k,v in t.coverage_status.value_counts().items()},'unsupported_training_component_reason_counts':{k:int(v) for k,v in counts.items()},'reason_counts_overlap':True,'gates_or_weights_changed':False};(OUT/'coverage_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'COVERAGE.md').write_text('# Frozen reserve CC coverage diagnosis\n\nEvery one of the 300 reserved events is retained. These counts describe the predeclared graph and measurement rules, not newly chosen criteria.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\nComponent rejection reasons overlap; counts are not independent rejected events. A low/ambiguous correlation may reflect distinct waveforms, noisy windows, or pick/association problems; the flag alone does not establish which cause applies. Do not lower thresholds to recover coverage. The fixed reserve is now exposed and cannot serve as untouched confirmation for a change chosen using these outcomes.\n')
print(json.dumps(result,indent=2),flush=True)
