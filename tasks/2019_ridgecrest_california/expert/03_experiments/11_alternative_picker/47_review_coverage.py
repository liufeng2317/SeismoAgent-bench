#!/usr/bin/env python3
"""Count unmeasured pair opportunities with unchanged geometric/overlap rules; no CC or fit."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/47_missing_s_observations'
def main():
 original=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',low_memory=False);current=pd.read_csv(OUT/'inputs/all_phases.csv',low_memory=False);events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');cohort=pd.read_csv(OUT/'inputs/events.csv');targets=cohort[cohort.role.eq('reserve')]
 excluded=set()
 for f in [HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv',HERE/'docs/optimization_reserved_events_v3.csv']:excluded.update(pd.read_csv(f).event_id)
 pool=events[events.in_v1_working_catalog&~events.event_id.isin(excluded)].sort_values('event_id');held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']);old=original[original.probability.ge(.5)].copy();old=old[~old.duplicated(['event_id','instrument_id','phase'],keep=False)]
 additional=current[~current.pick_id.isin(original.pick_id)].copy();aug=pd.concat([old,additional],ignore_index=True);assert not aug.duplicated(['event_id','instrument_id','phase']).any()
 def keys(table):
  table=table.copy();table['key']=table.instrument_id+':'+table.phase;return {eid:set(g.key) for eid,g in table.groupby('event_id')}
 lookups={'old':keys(old),'augmented':keys(aug)};xyz=pool[['x_km','y_km','depth_km']].to_numpy();graph=pd.read_csv(HERE/'export/39_support_aware_pairs/inputs/differential_times.csv');pairs=set(map(tuple,graph[['event_id_a','event_id_b']].drop_duplicates().to_numpy()));cc=pd.read_csv(OUT/'cc_measurements.csv');eligible=set(cohort[cohort.auxiliary_eligible].event_id);cc=cc[cc.accepted&cc.training&cc.event_id_a.isin(eligible)&cc.event_id_b.isin(eligible)];supported=set(cc.event_id_a)|set(cc.event_id_b);rows=[]
 for r in targets.itertuples():
  d=np.linalg.norm(xyz-np.array([r.x_km,r.y_km,r.depth_km]),axis=1);neighbors=pool.event_id.to_numpy()[(d<=3)&pool.event_id.ne(r.event_id).to_numpy()];row={'event_id':r.event_id,'auxiliary_eligible':bool(r.auxiliary_eligible),'has_training_cc':r.event_id in supported,'neighbors_within_3d_3km':len(neighbors)}
  for name,lookup in lookups.items():
   count=0;unmeasured=0
   for eid in neighbors:
    shared=lookup.get(r.event_id,set())&lookup.get(eid,set());stations={k.split(':')[0] for k in shared};training=stations-held
    if len(shared)>=6 and len(stations)>=4 and training:
     count+=1;unmeasured+=tuple(sorted([r.event_id,eid])) not in pairs
   row[name+'_eligible_neighbors']=count;row[name+'_unmeasured_neighbors']=unmeasured
  rows.append(row)
 result=pd.DataFrame(rows);result.to_csv(OUT/'coverage_geometry_audit.csv',index=False);weak=result[result.auxiliary_eligible&~result.has_training_cc]
 print(json.dumps({'all_targets':len(result),'unsupported_eligible_targets':len(weak),'unsupported_with_zero_geometric_neighbors':int(weak.neighbors_within_3d_3km.eq(0).sum()),'unsupported_with_no_old_eligible_neighbor':int(weak.old_eligible_neighbors.eq(0).sum()),'unsupported_with_no_augmented_eligible_neighbor':int(weak.augmented_eligible_neighbors.eq(0).sum()),'unsupported_with_unmeasured_augmented_neighbors':int(weak.augmented_unmeasured_neighbors.gt(0).sum()),'unsupported_with_more_unmeasured_after_augmentation':int(weak.augmented_unmeasured_neighbors.gt(weak.old_unmeasured_neighbors).sum())},indent=2))
if __name__=='__main__':main()
