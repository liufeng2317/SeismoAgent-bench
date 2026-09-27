#!/usr/bin/env python3
"""Finalize existing EDT solutions, retaining native weights rounded to zero."""
from pathlib import Path
import importlib.util
import sys
import re
import json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('edt_execution',Path(__file__).with_name('22_test_edt.py'))
R=importlib.util.module_from_spec(spec);sys.modules[spec.name]=R;spec.loader.exec_module(R)
H=R.H;OUT=R.OUT
pairs=H.NLL.pairs;tokens=H.NLL.tokens

def parse_hyp_edt(path,event,observations,station_map,proj):
    body=path.read_text();status=re.match(r'NLLOC\s+"[^"]*"\s+"([^"]+)"',body).group(1)
    h=pairs(body,'HYPOCENTER');q=pairs(body,'QUALITY');stats=pairs(body,'STATISTICS')
    geo=tokens(body,'GEOGRAPHIC');year,month,day,hour,minute=map(int,geo[1:6]);sec=float(geo[6])
    origin=pd.Timestamp(year=year,month=month,day=day,hour=hour,minute=minute,tz='UTC')+pd.Timedelta(seconds=sec)
    x,y,z=[float(h[k]) for k in ['x','y','z']];lon,lat=proj(x,y,inverse=True)
    row=dict(event_id=event['event_id'],status=status,origin_time=origin.isoformat(),longitude=lon,latitude=lat,
             x_km=x,y_km=y,depth_km=z,depth_below_sea_level_km=z-.7,rms_residual_s=float(q['RMS']),
             n_phases=int(q['Nphs']),azimuth_gap_deg=float(q['Gap']),
             posterior_mean_x_km=float(stats['ExpectX']),posterior_mean_y_km=float(stats['Y']),posterior_mean_depth_km=float(stats['Z']),
             posterior_sigma_x_km=np.sqrt(max(0,float(stats['CovXX']))),posterior_sigma_y_km=np.sqrt(max(0,float(stats['YY']))),
             posterior_sigma_depth_km=np.sqrt(max(0,float(stats['ZZ']))),
             horizontal_shift_km=np.hypot(x-event['x_km'],y-event['y_km']),depth_shift_km=z-event['depth_km'],
             gamma_depth_km=event['depth_km'],gamma_rms_residual_s=event['rms_residual_s'])
    links=[];expected={(r['instrument_id'],r['phase']):r for r in observations}
    inside=False
    for line in body.splitlines():
        if line.startswith('PHASE '):inside=True;continue
        if line.startswith('END_PHASE'):inside=False
        if not inside or ' > ' not in line:continue
        before,after=line.split(' > ');a=before.split();b=after.split()
        instrument=station_map[a[0]];phase=a[4];p=expected[(instrument,phase)]
        # Verify the parser maps an unchanged arrival, not merely a station/phase label.
        stamp=pd.to_datetime(a[6],format='%Y%m%d',utc=True)+pd.Timedelta(hours=int(a[7])//100,minutes=int(a[7])%100,seconds=float(a[8]))
        assert abs((stamp-pd.Timestamp(p['time_utc'])).total_seconds())<.00011
        links.append(dict(event_id=row['event_id'],pick_id=p['pick_id'],instrument_id=instrument,phase=phase,
                          residual_s=float(b[1]),weight=float(b[2]),predicted_travel_time_s=float(b[0])))
    assert len(links)==len(expected)==row['n_phases'],f'Arrival count mismatch for {row["event_id"]}'
    assert len({r['pick_id'] for r in links})==len(links)
    # EDT consistency weights may round to zero; retain all matched input phases.
    assert all(r['weight']>=0 for r in links)
    assert abs(np.mean([r['weight'] for r in links])-1)<.0001
    row['rms_unweighted_s']=float(np.sqrt(np.mean([r['residual_s']**2 for r in links])))
    row['gamma_rms_unweighted_s']=float(np.sqrt(np.mean([float(r['residual_s'])**2 for r in observations])))
    row['origin_time_shift_s']=(origin-pd.Timestamp(event['origin_time'])).total_seconds()
    row['n_stations']=len({p['station_id'] for p in observations})
    assert len(observations)==len(expected)
    assert np.isfinite([x,y,z,row['rms_unweighted_s'],row['posterior_sigma_depth_km']]).all()
    assert 0<=z<=25, 'Depth outside the fixed search interval'
    row['quality_flags']=';'.join(x for x,condition in [('near_depth_bound',z<.5 or z>24.5),('azimuth_gap_gt_180',float(q['Gap'])>180),('not_located',status!='LOCATED')] if condition)
    return row,links


def main():
    import fcntl
    with (OUT/'run.lock').open('w') as lock:
        # Same lock as the execution script; never read partially written results.
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=R.prepare();cfg,cohort,picks,stations,held,_=data
        previous=json.loads((OUT/'design.json').read_text())
        assert all(H.sha(p)==v for p,v in previous['source_sha256'].items())
        aliases=stations.nll_station.to_dict();reverse={v:k for k,v in aliases.items()}
        baseline=HERE/'export/20_velocity_model_qualification/tables'
        e0=pd.read_csv(baseline/'events.csv');p0=pd.read_csv(baseline/'fit_phases.csv')
        rows=e0[e0.branch.isin(['control','withheld_control'])].to_dict('records')
        links=p0[p0.branch.isin(['control','withheld_control'])].to_dict('records')
        native_hashes={};maxweight=0.;zero_weights=0
        for branch in ['edt','withheld_edt']:
            for e in cohort.to_dict('records'):
                folder=OUT/'native'/branch/e['event_id'];src=R.BASE/'events_raw'/e['event_id']
                obs=picks[picks.event_id.eq(e['event_id'])].to_dict('records');text=(src/'input.obs').read_text()
                if branch.startswith('withheld'):
                    excluded={aliases[k] for k in held}
                    text='\n'.join(l for l in text.splitlines() if not l.split() or l.split()[0] not in excluded)+'\n'
                    obs=[p for p in obs if p['instrument_id'] not in held]
                assert (folder/'input.obs').read_text()==text
                ctl='\n'.join(l for l in (src/'control.in').read_text().splitlines() if not l.startswith('LOCFILES '))+'\n'
                ctl=ctl.replace('LOCMETH GAU_ANALYTIC ','LOCMETH EDT ')+f'LOCFILES input.obs NLLOC_OBS {R.BASE}/grids/time solution\n'
                assert (folder/'control.in').read_text()==ctl
                files=[p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name];assert len(files)==1
                row,pp=parse_hyp_edt(files[0],e,obs,reverse,H.PROJ)
                residual=np.array([p['residual_s'] for p in pp]);variance=np.array([cfg['model_error_s']**2+cfg['pick_error_s'][p['phase']]**2 for p in pp]);pv=variance[:,None]+variance[None,:]
                score=np.exp(-.5*(residual[:,None]-residual[None,:])**2/pv)/np.sqrt(pv);np.fill_diagonal(score,0.)
                expected=score.sum(axis=1);expected/=expected.mean()
                error=float(np.abs(expected-np.array([p['weight'] for p in pp])).max());assert error<.0005
                maxweight=max(maxweight,error);zero_weights+=sum(p['weight']==0 for p in pp)
                for k in ['gamma_depth_km','gamma_rms_residual_s','gamma_rms_unweighted_s']:row.pop(k)
                row['branch']=branch;row['native_weight_check_max']=error;rows.append(row)
                for p in pp:p['branch']=branch;p['weight_rounded_to_zero']=p['weight']==0
                links.extend(pp)
                for p in [files[0],folder/'input.obs',folder/'control.in']:native_hashes[str(p)]=H.sha(p)
        pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False)
        H.write_json(OUT/'parser_checks.json',dict(parser_sha256=H.sha(__file__),execution_design_sha256=H.sha(OUT/'design.json'),parsed_native_fits=294,weight_rounded_to_zero=zero_weights,max_native_weight_discrepancy=maxweight,native_sha256=native_hashes,semantics='EDT near-zero consistency weights are retained; no input removal or changes to computed native locations. Original failures.csv records GAU parser rejection, not failed NLLoc execution.'))
        R.report(data)
        print('EDT parser verification:',zero_weights,'rounded-zero weights; max discrepancy',maxweight,flush=True)
        path=OUT/'README.md';text=path.read_text();text+='\n## EDT-specific parser completion\n\nThe generic Gaussian parser rejected some valid native EDT rows because consistency weights rounded to zero. `22_finalize_edt.py` retains those rows, validates all input identities and reconstructs their pairwise weights; it does not rerun or change any native location. `parser_checks.json` records source/native hashes and checks; original `tables/failures.csv` records generic-parser failures, not failed native inversions. Reproduce with the execution command above, then `python -u 03_experiments/05_catalog_optimization/22_finalize_edt.py`. Use the finalizer for subsequent report generation. All final tables include the retained phases and explicit rounded-zero flags.\n'
        path.write_text(text)

if __name__=='__main__':main()
