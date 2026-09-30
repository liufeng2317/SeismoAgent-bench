#!/usr/bin/env python3
"""One fixed point-depth refresh followed by the frozen moment-envelope refresh."""
import json
import pandas as pd
import _confirmation as C

def main():
 qualification=C.HERE/'export/46_alternative_picker/design.json';identities={f:h for f,h in json.loads(qualification.read_text())['source_sha256'].items() if '/pretrained/' in f or f.endswith('/model/eqtransformer.py')};assert len(identities)>=2
 for f,h in identities.items():assert C.sha(f)==h,f
 C.freeze(C.OUT/'observations/model_identity.json',{'source_sha256':identities,'qualification_design':str(qualification),'unchanged_qualified_EQ_weights':True})
 C.verify_candidate();events,original,_=C.source_data();available=pd.read_csv(C.OUT/'observations/available_phases.csv',low_memory=False);pool=events[events.in_v1_working_catalog&~events.event_id.isin(C.exclusions())].sort_values('event_id').reset_index(drop=True);targets=pool[pool.event_id.isin(pd.read_csv(C.HERE/'docs/optimization_reserved_events_v3.csv').event_id)];assert len(targets)==300
 pairs=set(map(tuple,pd.read_csv(C.OUT/'initial/pair_status.csv')[['event_id_a','event_id_b']].to_numpy()));initial=len(pairs);point,pointrows=C.ranked_pairs(targets,pool,available);pairs|=point;point_count=len(pairs);envelope,envrows=C.ranked_pairs(targets,pool,available,envelope=True);pairs|=envelope
 cohort=C.cohort(pool,set(targets.event_id),pairs,original);ph=available[available.event_id.isin(cohort.event_id)].copy();edges,status=C.edges_for(pairs,ph,set(cohort.event_id));used=set(edges.pick_id_a)|set(edges.pick_id_b);dest=C.OUT/'inputs';dest.mkdir(exist_ok=True)
 files=[__file__,C.__file__,C.HERE/'03_experiments/15_confirmation/51_continue.py',C.OUT/'design.json',C.OUT/'observations/design.json',C.OUT/'observations/available_phases.csv',C.OUT/'initial/pair_status.csv']
 C.freeze(C.OUT/'graph_design.json',{'round':30,'source_sha256':{str(f):C.sha(f) for f in files},'recipe':'Union initial nearest/support point graph, one support-ranked point refresh after augmentation, then one depth-moment envelope refresh. No outcome-dependent recursive augmentation.'})
 for name,df in [('events',cohort),('all_phases',ph),('picks',ph[ph.pick_id.isin(used)]),('differential_times',edges),('pair_status',status),('point_neighbors',pointrows),('envelope_neighbors',envrows)]:
  f=dest/(name+'.csv');value=df.to_csv(index=False)
  if f.exists():assert f.read_text()==value
  else:f.write_text(value)
 C.save(C.OUT/'graph_summary.json',{'targets':300,'events':len(cohort),'auxiliary_targets':int((cohort.role.eq('reserve')&cohort.auxiliary_eligible).sum()),'initial_pairs':initial,'point_pairs':point_count,'final_pairs':len(pairs),'candidate_edges':len(edges),'phases':len(ph),'reference_outcomes_read':False})
 print((C.OUT/'graph_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
