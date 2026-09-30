#!/usr/bin/env python3
"""Freeze development-only nearest paired-station holdouts before model scoring."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/31_background_calibration'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    ep=HERE/'export/12_relative_location_pilot/events.csv';pp=HERE/'export/10_validate_catalog/phases.csv';sp=HERE/'export/04_locate_nonlinloc/stations.csv'
    e=pd.read_csv(ep,usecols=['event_id','x_km','y_km','depth_km']);p=pd.read_csv(pp,keep_default_na=False);p=p[p.event_id.isin(e.event_id)];st=pd.read_csv(sp).set_index('id')
    assert len(e)==144 and e.event_id.is_unique and not p.duplicated(['event_id','instrument_id','phase']).any()
    rows=[]
    for event in e.sort_values('event_id').itertuples():
        q=p[p.event_id.eq(event.event_id)];counts=q.groupby('instrument_id').phase.agg(set);ids=sorted(s for s,ph in counts.items() if ph=={'P','S'})
        if not ids:
            rows.append(dict(event_id=event.event_id,eligible=False,reason='no_paired_instrument'));continue
        distances=np.hypot(st.loc[ids,'x(km)'].to_numpy()-event.x_km,st.loc[ids,'y(km)'].to_numpy()-event.y_km)
        chosen=min(zip(distances,ids));dist,sid=chosen
        held=q[q.instrument_id.eq(sid)].set_index('phase');fit=q[~q.instrument_id.eq(sid)]
        interval=(pd.Timestamp(held.loc['S','time_utc'])-pd.Timestamp(held.loc['P','time_utc'])).total_seconds()
        eligible=len(fit)>=10 and int(fit.phase.eq('S').sum())>=3 and interval>0
        reason='eligible' if eligible else ('nonpositive_observed_SP' if interval<=0 else 'insufficient_fit_arrivals_or_S')
        rows.append(dict(event_id=event.event_id,held_instrument=sid,P_pick_id=held.loc['P','pick_id'],S_pick_id=held.loc['S','pick_id'],original_epicentral_distance_km=float(dist),observed_SP_s=interval,n_fit=len(fit),n_S_fit=int(fit.phase.eq('S').sum()),eligible=eligible,reason=reason))
    table=pd.DataFrame(rows);csv=OUT/'development_holdouts.csv';meta=OUT/'selection_design.json'
    design=dict(scope='144 previously examined development events only; transfer and second confirmation outcomes not used for candidate selection.',selection='Nearest instrument having both original P and S, from original NLL XY coordinates; ties by instrument ID. Do not update membership after relocation. Withhold both arrivals. Keep all 144 statuses.',eligibility='At least 10 remaining arrivals including 3 S, positive observed held-out S-P. No fallback/replacement for ineligible events.',candidates='Fixed physical velocity fields: alpha=0 local-background variant, alpha=1 raw-regional variant, alpha=0.5 arithmetic midpoint of their P and S VELOCITIES (not travel times), with identical full propagation domains. Original local 1D is a separate scoring control. No further alpha scan.',score='Untrimmed RMS of held-out S-P prediction errors on the same eligible events; no reference fitting, event exclusions after results or origin recentering.',decision='All fits/identities/checks must pass. Midpoint advances only if strictly lower S-P RMS than BOTH endpoint models and at least 5% lower than the original 1D control; otherwise close this bounded calibration. A qualifying midpoint must still pass existing transfer gates before opening the second reserve. Endpoint wins do not revive candidates already rejected on transfer.',n=len(table),n_eligible=int(table.eligible.sum()),source_sha256={str(f):sha(f) for f in [Path(__file__),ep,pp,sp]})
    if meta.exists():
        old=json.loads(meta.read_text());assert old['design']==design and old['csv_sha256']==sha(csv)
        pd.testing.assert_frame_equal(pd.read_csv(csv),table,check_dtype=False)
    else:
        table.to_csv(csv,index=False);meta.write_text(json.dumps(dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),design=design,csv_sha256=sha(csv)),indent=2,sort_keys=True)+'\n')
    print('Development eligibility:',table.reason.value_counts().to_dict());print('Nearest paired station distances (km):',table.original_epicentral_distance_km.quantile([0,.5,.9,1]).to_dict())
if __name__=='__main__':main()
