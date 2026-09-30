#!/usr/bin/env python3
"""Freeze an outcome-independent second confirmation cohort; never fit it here."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2]
CSV=HERE/'docs/optimization_reserved_events_v2.csv'
META=HERE/'docs/optimization_reserved_events_v2.json'
SALT='ridgecrest-confirmation-v2-300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'export/10_validate_catalog/events.csv'
    exclusions=[HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv',HERE/'export/19_s_arrival_review/selection.csv',HERE/'export/19_s_arrival_review/neighboring_picks.csv']
    excluded=set()
    for p in exclusions:excluded.update(pd.read_csv(p,usecols=['event_id']).event_id.dropna().astype(str))
    # Deliberately do not read reference matches, new locations, residuals or magnitudes.
    e=pd.read_csv(source,usecols=['event_id','in_v1_working_catalog','origin_time','x_km','y_km'])
    e=e[e.in_v1_working_catalog&~e.event_id.isin(excluded)].copy()
    t=pd.to_datetime(e.origin_time,utc=True,format='ISO8601')
    e['period']=np.select([t<pd.Timestamp('2019-07-04T17:33:49Z'),t<pd.Timestamp('2019-07-06T03:19:53Z')],['before_M6.4','between_mainshocks'],default='after_M7.1')
    e['x_10km_bin']=np.floor(e.x_km/10).astype(int);e['y_10km_bin']=np.floor(e.y_km/10).astype(int)
    e['selection_hash']=e.event_id.map(lambda x:hashlib.sha256((SALT+':'+x).encode()).hexdigest())
    strata=['period','x_10km_bin','y_10km_bin']
    groups=[g.sort_values(['selection_hash','event_id']).to_dict('records') for _,g in e.groupby(strata,sort=True)]
    selected=[];rank=0
    while len(selected)<300:
        available=[g[rank] for g in groups if rank<len(g)]
        assert available,'Not enough eligible events'
        selected.extend(available[:300-len(selected)]);rank+=1
    q=pd.DataFrame(selected)[['event_id']+strata+['selection_hash']]
    assert q.event_id.is_unique and not set(q.event_id)&excluded
    sources={str(p):sha(p) for p in [Path(__file__),source]+exclusions}
    if CSV.exists() or META.exists():
        assert CSV.exists() and META.exists()
        old=json.loads(META.read_text());assert old['source_sha256']==sources and old['csv_sha256']==sha(CSV)
        pd.testing.assert_frame_equal(pd.read_csv(CSV),q.reset_index(drop=True))
        print('Verified frozen second cohort; no locations run.');return
    assert not (HERE/'export/29_3d_velocity/transfer/run.json').exists(),'Selection must precede transfer results.'
    q.to_csv(CSV,index=False)
    meta=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),n=300,eligible_pool=len(e),excluded_unique_ids=len(excluded),status='reserved_not_used',selection='Deterministic SHA256 order within period/original-10km-XY strata; sorted-stratum round robin until 300. Not population-proportional. No result/reference-based screening.',salt=SALT,exposure='Disjoint from prior small experiment cohorts and consumed first confirmation cohort; also excludes reviewed S-window neighbors. Historical full-catalog comparisons exist, so not never-examined blind data. Event-disjoint, not guaranteed spatially or temporally independent.',use='Only open for confirmation after a fixed candidate passes transfer gates. Do not tune to this set. If stage29 fails, retain this set unused for a future independently frozen candidate.',source_sha256=sources,csv_sha256=sha(CSV),period_counts=q.period.value_counts().to_dict())
    META.write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:meta[k] for k in ['n','eligible_pool','excluded_unique_ids','period_counts','status']},indent=2))
if __name__=='__main__':main()
