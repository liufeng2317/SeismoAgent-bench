#!/usr/bin/env python3
"""Prepare the committed third confirmation cohort without reading its reference outcomes."""
from pathlib import Path
import json
import pandas as pd
import _confirmation as C
def main():
 C.OUT.mkdir(exist_ok=True);C.verify_candidate();events,original,available=C.source_data()
 # Exact development geometry reproduction before preparing new-target observations.
 devpool=events[events.in_v1_working_catalog&~events.event_id.isin(C.exclusions(True))].sort_values('event_id').reset_index(drop=True);dev=pd.read_csv(C.SELECTED/'inputs/events.csv');dev=dev[dev.role.eq('reserve')];added,_=C.ranked_pairs(dev,devpool,available,envelope=True);prior=pd.read_csv(C.HERE/'export/48_differential_augmentation/refreshed/inputs/pair_status.csv');pairs=added|set(zip(prior.event_id_a,prior.event_id_b));expected=pd.read_csv(C.SELECTED/'inputs/pair_status.csv');assert pairs==set(zip(expected.event_id_a,expected.event_id_b))
 reserve=pd.read_csv(C.HERE/'docs/optimization_reserved_events_v3.csv');assert len(reserve)==300 and reserve.event_id.is_unique;previous=pd.read_csv(C.SELECTED/'inputs/events.csv');assert not set(reserve.event_id)&set(previous.event_id)
 files=[Path(__file__),Path(C.__file__),C.SELECTED/'frozen_candidate.json',C.HERE/'docs/optimization_reserved_events_v3.csv',C.HERE/'docs/optimization_reserved_events_v3.json',C.ORIGINAL/'events.csv',C.ORIGINAL/'phases.csv',C.SELECTED/'inputs/all_phases.csv']
 C.freeze(C.OUT/'design.json',{'round':30,'purpose':'Confirmation of the selected stage50 recipe, not another optimization. All300 reserve3 targets retained. No reference outcome read during preparation.','candidate':str(C.SELECTED/'frozen_candidate.json'),'development_selector_reproduced_exactly':True,'data_policy':'Retain all previously admitted observations as available input data. Initial nearest/support-ranked graph uses originalPN availability. Augment missing cells on its cohort with frozen methods; then union point-depth and depth-envelope refreshes. Prior supports may recur but are re-estimated as latent locations, never used as true anchors.','auxiliary':'Original PN training counts >=10 and S>=3, frozen before augmentation.','status':'Reserve3 committed to round30; no adaptive reuse even if confirmation fails.','source_sha256':{str(f):C.sha(f) for f in files}})
 pool=events[events.in_v1_working_catalog&~events.event_id.isin(C.exclusions())].sort_values('event_id').reset_index(drop=True);targets=pool[pool.event_id.isin(reserve.event_id)];assert len(targets)==300
 near,nearest=C.ranked_pairs(targets,pool,original,nearest=True);rank,support=C.ranked_pairs(targets,pool,original);pairs=near|rank;e=C.cohort(pool,set(reserve.event_id),pairs,original);ph=available[available.event_id.isin(e.event_id)].copy();edges,status=C.edges_for(pairs,original,set(pool.event_id))
 out=C.OUT/'initial';out.mkdir(exist_ok=True)
 for name,frame in [('events.csv',e),('all_phases.csv',ph),('pair_status.csv',status),('differential_times.csv',edges),('nearest_neighbors.csv',nearest),('support_neighbors.csv',support)]:
  f=out/name;t=frame.to_csv(index=False)
  if f.exists():assert f.read_text()==t
  else:f.write_text(t)
 result={'round':30,'targets':300,'initial_events':len(e),'supports':int(e.role.eq('support').sum()),'auxiliary_targets':int((e.role.eq('reserve')&e.auxiliary_eligible).sum()),'pairs':len(pairs),'initial_available_phases':len(ph),'previously_admitted_rows':int(ph.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_')).sum()),'reference_outcomes_read':False,'development_graph_reproduction':True};C.save(C.OUT/'preparation_summary.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
