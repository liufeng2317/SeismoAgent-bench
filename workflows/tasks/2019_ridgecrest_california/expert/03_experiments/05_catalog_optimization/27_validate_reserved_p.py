#!/usr/bin/env python3
"""Round 07: frozen P-only correction confirmation on 300 reserved events."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,sys,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('reserved_helpers',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
S=importlib.util.module_from_spec(spec);sys.modules[spec.name]=S;spec.loader.exec_module(S)
OUT=HERE/'export/27_reserved_p_corrections';S.OUT=OUT
BASE=S.BASE;DIAG=S.DIAG;PROJ=S.PROJ;XYZ=S.XYZ;rms=S.rms;plot=S.plot


def write_json(path,value):
    temp=path.with_name(path.name+'.tmp')
    with temp.open('w') as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)


def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    reserved=pd.read_csv(HERE/'docs/optimization_reserved_events.csv')
    all_events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv')
    cohort=all_events.set_index('event_id').loc[reserved.event_id].reset_index()
    assert len(cohort)==300 and cohort.in_v1_working_catalog.all()
    old=set(pd.read_csv(HERE/'export/12_relative_location_pilot/events.csv').event_id)|set(pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv').event_id)
    assert not set(cohort.event_id)&old
    picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(cohort.event_id)].copy();picks['residual_s']=picks.residual_s_gamma
    stations=pd.read_csv(BASE/'stations.csv').set_index('id');aliases=stations.nll_station.to_dict()
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    corrections=pd.read_csv(HERE/'export/26_p_corrections/tables/corrections.csv')
    assert corrections[corrections.phase.eq('S')].proposed_tt_correction_s.eq(0).all()
    assert int(corrections.correction_active.sum())==32
    counts=picks[~picks.instrument_id.isin(held)].groupby('event_id').size()
    cohort['aux_n_fit']=cohort.event_id.map(counts).fillna(0).astype(int)
    s_counts=picks[(~picks.instrument_id.isin(held))&picks.phase.eq('S')].groupby('event_id').size()
    cohort['aux_n_s']=cohort.event_id.map(s_counts).fillna(0).astype(int)
    cohort['aux_eligible']=cohort.aux_n_fit.ge(10)&cohort.aux_n_s.ge(3)
    cohort['aux_status']=np.where(cohort.aux_eligible,'eligible','not_run_insufficient_fit_arrivals_or_S')
    cohort.to_csv(OUT/'tables/cohort.csv',index=False);corrections.to_csv(OUT/'tables/corrections.csv',index=False)
    files=[Path(__file__),OUT/'auxiliary_input_audit.json',Path(S.__file__),Path(S.NLL.__file__),Path(S.DIAG.__file__),HERE/'00_config/nonlinloc.yaml',HERE/'docs/optimization_reserved_events.csv',HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',HERE/'export/26_p_corrections/tables/corrections.csv',HERE/'export/26_p_corrections/run.json',BASE/'stations.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',Path(cfg['binary_directory'])/'NLLoc']
    files+=list((BASE/'grids').glob('time.*.time.*'))
    for eid in cohort.event_id:files += [BASE/'events_raw'/eid/'input.obs',BASE/'events_raw'/eid/'control.in']
    design=dict(round=7,max_rounds=30,n_reserved=300,n_aux_eligible=int(cohort.aux_eligible.sum()),expected_fits=int(600+2*cohort.aux_eligible.sum()),candidate='Frozen stage26 P-only corrections. No refit/scaling/model/error/search changes.',scope='All pre-reserved 300 ordinary v1 events, no post-result exclusions. Auxiliary fits need >=10 input observations AND >=3 S arrivals (native LOCMETH minimums) after fixed six-instrument omission, determined before results. Primary fits include every event.',gates='Same stage17 reference/prediction/retention/depth-bound/posterior gates plus omission median and p90 horizontal/depth displacements <=1.10 baseline on identical aux-eligible events. Prediction all RMS <=.95 and P/S <=1.05 baseline. Bounds use the unchanged conservative absolute +3 count. Passing permits full production, not a claim of true accuracy.',limitation='Reserved from adaptive selection in this campaign; historical whole-catalog comparisons exist, so not never-before-examined blind data. No further tuning against these results.',source_sha256={str(p):S.sha(p) for p in files})
    p=OUT/'design.json'
    if p.exists():assert json.loads(p.read_text())==design
    else:write_json(p,design)
    print('Frozen reserved design:',300,'events,',design['n_aux_eligible'],'auxiliary-eligible,',design['expected_fits'],'fits',flush=True)
    return cfg,cohort,picks,stations,corrections,corrections.set_index(['instrument_id','phase']).proposed_tt_correction_s.to_dict(),held,aliases


def run(data):
    cfg,cohort,picks,stations,corrections,corr,held,aliases=data
    groups={k:g.to_dict('records') for k,g in picks.groupby('event_id')};rows=[];links=[];failures=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs={}
        for branch in ['control','corrected','withheld_control','withheld_corrected']:
            es=cohort[cohort.aux_eligible] if branch.startswith('withheld') else cohort
            for e in es.to_dict('records'):
                job=pool.submit(S.solve,e,groups[e['event_id']],branch,corr if branch.endswith('corrected') else {},aliases,cfg,held if branch.startswith('withheld') else ())
                jobs[job]=(branch,e['event_id'])
        for i,f in enumerate(as_completed(jobs),1):
            try:r,p=f.result();rows.append(r);links.extend(p)
            except Exception as exc:failures.append(dict(branch=jobs[f][0],event_id=jobs[f][1],error=repr(exc)));print(failures[-1],flush=True)
            if i%100==0 or i==len(jobs):print(f'[{i}/{len(jobs)}] failures={len(failures)}',flush=True)
    pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False)
    assert not failures
    err=S.check_observations(rows,links,picks,stations)
    base=pd.DataFrame(rows).query("branch=='control'").set_index('event_id').loc[cohort.event_id]
    dx=float(np.abs(base[XYZ].to_numpy()-cohort[XYZ].to_numpy()).max())
    dt=float(np.abs((pd.to_datetime(base.origin_time.to_numpy(),utc=True,format='ISO8601')-pd.to_datetime(cohort.origin_time.to_numpy(),utc=True,format='ISO8601')).total_seconds()).max())
    assert dx<.001 and dt<.001
    write_json(OUT/'checks.json',dict(parsed_fits=len(rows),control_xyz_max_km=dx,control_origin_max_s=dt,timing_equation_max_s=err))

def report(data):
    cfg, cohort, picks, stations, corrections, corr, held, aliases = data
    events = pd.read_csv(OUT/'tables/events.csv')
    expected = int(json.loads((OUT/'design.json').read_text())['expected_fits'])
    assert len(events) == expected and not events.duplicated(['branch','event_id']).any()
    fits = pd.read_csv(OUT/'tables/fit_phases.csv')
    # Predict withheld observations at auxiliary solutions; use fitted origin unchanged.
    withheld = []
    for branch in ['withheld_control','withheld_corrected']:
        e = events[events.branch.eq(branch)]
        p = picks[picks.instrument_id.isin(held)].merge(e[['event_id','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        tt,_ = DIAG.predict(BASE/'grids',p,stations)
        p['branch'] = branch
        p['tt_correction_s'] = [corr.get((r.instrument_id,r.phase),0.) if branch.endswith('corrected') else 0. for r in p.itertuples()]
        p['correction_supported'] = [(r.instrument_id,r.phase) in corr for r in p.itertuples()]
        p['predicted_travel_time_s'] = tt
        p['residual_s'] = (pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt-p.tt_correction_s
        withheld.append(p)
    withheld = pd.concat(withheld,ignore_index=True)
    withheld[['branch','event_id','pick_id','instrument_id','phase','time_utc','origin_time','predicted_travel_time_s','tt_correction_s','correction_supported','residual_s']].to_csv(OUT/'tables/heldout_predictions.csv',index=False)
    metrics=[]
    for branch,g in events.groupby('branch'):
        fp=fits[fits.branch.eq(branch)]
        metrics.append(dict(branch=branch,n=len(g),located=int(g.status.eq('LOCATED').sum()),near_depth_bound=int(((g.depth_km<.5)|(g.depth_km>24.5)).sum()),median_depth_km=g.depth_km.median(),median_event_rms_s=g.rms_unweighted_s.median(),all_pick_rms_s=rms(fp.residual_s),p90_posterior_depth_sigma_km=g.posterior_sigma_depth_km.quantile(.9)))
    metrics=pd.DataFrame(metrics);metrics.to_csv(OUT/'tables/metrics.csv',index=False)
    hm=[]
    for branch,g in withheld.groupby('branch'):
        for phase,q in [('all',g),('P',g[g.phase.eq('P')]),('S',g[g.phase.eq('S')])]:
            hm.append(dict(branch=branch,phase=phase,n=len(q),rms_s=rms(q.residual_s),median_abs_s=q.residual_s.abs().median()))
    hm=pd.DataFrame(hm);hm.to_csv(OUT/'tables/heldout_metrics.csv',index=False)
    station_rows=[]
    for kind,table,branches in [('fit',fits,['control','corrected']),('heldout',withheld,['withheld_control','withheld_corrected'])]:
        for (station,phase),q in table[table.branch.isin(branches)].groupby(['instrument_id','phase']):
            a=q[q.branch.eq(branches[0])];b=q[q.branch.eq(branches[1])]
            assert set(a.pick_id)==set(b.pick_id)
            station_rows.append(dict(kind=kind,instrument_id=station,phase=phase,n=len(a),correction_supported=(station,phase) in corr,control_rms_s=rms(a.residual_s),corrected_rms_s=rms(b.residual_s)))
    station_rows=pd.DataFrame(station_rows);station_rows.to_csv(OUT/'tables/station_phase_comparison.csv',index=False)
    # Fixed reference identities; no rematching, reference fitting or catalog shifts.
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv')
    refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    main=events[events.branch.isin(['control','corrected'])]
    valid=set.intersection(*(set(g[g.status.eq('LOCATED')].event_id) for _,g in main.groupby('branch')))
    m=matches[matches.event_id.isin(valid)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'],validate='many_to_one')
    vectors=[];ref_summary=[]
    for branch in ['control','corrected']:
        e=main[main.branch.eq(branch)].set_index('event_id')
        rx,ry=PROJ(m.longitude.to_numpy(),m.latitude.to_numpy())
        v=m[['event_id','catalog','reference_id','reference_depth_km']].copy()
        v['branch']=branch;v['reference_x_km']=rx;v['reference_y_km']=ry
        v['dx_km']=e.loc[m.event_id,'x_km'].to_numpy()-rx;v['dy_km']=e.loc[m.event_id,'y_km'].to_numpy()-ry
        v['horizontal_km']=np.hypot(v.dx_km,v.dy_km)
        v['depth_difference_km']=np.where(m.catalog.eq('Shelly'),e.loc[m.event_id,'depth_km'].to_numpy()-m.reference_depth_km,np.nan)
        vectors.append(v)
        for cat,q in v.groupby('catalog'):
            ref_summary.append(dict(branch=branch,catalog=cat,n=len(q),median_horizontal_km=q.horizontal_km.median(),median_dx_km=q.dx_km.median(),median_dy_km=q.dy_km.median(),median_abs_depth_km=q.depth_difference_km.abs().median(),median_signed_depth_km=q.depth_difference_km.median()))
    vectors=pd.concat(vectors,ignore_index=True);refsumm=pd.DataFrame(ref_summary)
    vectors.to_csv(OUT/'tables/reference_pairs.csv',index=False);refsumm.to_csv(OUT/'tables/reference_summary.csv',index=False)
    a=main[main.branch.eq('control')].set_index('event_id');b=main[main.branch.eq('corrected')].set_index('event_id').loc[a.index]
    paired=pd.DataFrame(dict(event_id=a.index,horizontal_shift_km=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km),depth_shift_km=b.depth_km-a.depth_km,control_depth_km=a.depth_km,corrected_depth_km=b.depth_km,control_rms_s=a.rms_unweighted_s,corrected_rms_s=b.rms_unweighted_s,control_sigma_depth_km=a.posterior_sigma_depth_km,corrected_sigma_depth_km=b.posterior_sigma_depth_km))
    paired['shift_3d_km']=np.hypot(paired.horizontal_shift_km,paired.depth_shift_km)
    paired['large_shift_review']=paired.shift_3d_km>3.
    paired.to_csv(OUT/'tables/paired_events.csv',index=False)
    # Apply frozen decision gates without revising their thresholds after inspection.
    mt=metrics.set_index('branch');hr=hm.pivot(index='phase',columns='branch',values='rms_s')
    rr=refsumm.pivot(index='catalog',columns='branch',values='median_horizontal_km')
    dr=refsumm[refsumm.catalog.eq('Shelly')].set_index('branch').median_abs_depth_km
    ratios=(rr.corrected/rr.control).to_dict();ratios['Shelly_depth']=float(dr['corrected']/dr['control'])
    tests={
        'execution':bool(json.loads((OUT/'checks.json').read_text())['parsed_fits']==expected),
        'retention':bool(all(mt.loc[y,'located']>=mt.loc[x,'located'] for x,y in [('control','corrected'),('withheld_control','withheld_corrected')])),
        'depth_bounds':bool(mt.loc['corrected','near_depth_bound']<=mt.loc['control','near_depth_bound']+3),
        'posterior_depth':bool(mt.loc['corrected','p90_posterior_depth_sigma_km']<=1.10*mt.loc['control','p90_posterior_depth_sigma_km']),
        'heldout_prediction':bool(hr.loc['all','withheld_corrected']<=.95*hr.loc['all','withheld_control'] and all(hr.loc[p,'withheld_corrected']<=1.05*hr.loc[p,'withheld_control'] for p in ['P','S'])),
        'reference_non_degradation':bool(all(v<=1.10 for v in ratios.values())),
        'reference_gain':bool(any(v<=.95 for v in ratios.values())),
    }
    decision='proceed_to_fresh_cohort_validation' if all(tests.values()) else 'do_not_promote'
    pd.DataFrame([dict(gate=k,passed=v) for k,v in tests.items()]).to_csv(OUT/'tables/decision_gates.csv',index=False)
    stats=dict(decision=decision,gates=tests,reference_ratios=ratios,heldout_rms_ratio=float(hr.loc['all','withheld_corrected']/hr.loc['all','withheld_control']),median_horizontal_shift_km=float(paired.horizontal_shift_km.median()),median_depth_shift_km=float(paired.depth_shift_km.median()),large_3d_shifts_over_3km=int(paired.large_shift_review.sum()),fit_station_phases_improved=int(((station_rows.kind=='fit')&(station_rows.corrected_rms_s<station_rows.control_rms_s)).sum()),fit_station_phases_total=int((station_rows.kind=='fit').sum()),no_prior_products_modified=True)
    write_json(OUT/'run.json',stats)
    plot(main,paired,vectors,withheld)

def finalize(data):
    report(data)
    cfg,cohort,picks,stations,corrections,corr,held,aliases=data
    result=json.loads((OUT/'run.json').read_text());e=pd.read_csv(OUT/'tables/events.csv');summary=[]
    for method in ['control','corrected']:
        b=e[e.branch.eq('withheld_'+method)].set_index('event_id');a=e[e.branch.eq(method)].set_index('event_id').loc[b.index]
        h=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km);z=(b.depth_km-a.depth_km).abs()
        summary.append(dict(method=method,n=len(a),median_horizontal_km=h.median(),p90_horizontal_km=h.quantile(.9),median_depth_km=z.median(),p90_depth_km=z.quantile(.9)))
    summary=pd.DataFrame(summary);o=summary.set_index('method').drop(columns=['n']);ratios=(o.loc['corrected']/o.loc['control']).to_dict()
    result['round']=7;result['omission_ratios']=ratios;result['gates']['omission_stability']=bool(all(v<=1.10 for v in ratios.values()))
    result['decision']='confirmed_for_full_production' if all(result['gates'].values()) else 'not_confirmed_do_not_promote'
    write_json(OUT/'run.json',result);summary.to_csv(OUT/'tables/omission_summary.csv',index=False)
    pd.DataFrame([dict(gate=k,passed=v) for k,v in result['gates'].items()]).to_csv(OUT/'tables/decision_gates.csv',index=False)
    # Descriptive coverage by original time/space strata; no stratum is selected after its outcome.
    strata=e.merge(cohort[['event_id','period','subregion']],on='event_id',validate='many_to_one')
    strata.groupby(['branch','period','subregion']).agg(n=('event_id','size'),located=('status',lambda x:int(x.eq('LOCATED').sum())),median_depth_km=('depth_km','median'),median_rms_s=('rms_unweighted_s','median')).reset_index().to_csv(OUT/'tables/coverage.csv',index=False)
    table=lambda name:pd.read_csv(OUT/f'tables/{name}.csv').to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text(f'''# Round 07: reserved confirmation of frozen P corrections

Decision: **{result['decision']}**. This is confirmation on the exact 300 events reserved before campaign selection, not another coefficient-fitting experiment. Full v1 remains unchanged.

## Fixed inputs and coverage

The original 32 P coefficients from round 06 are applied unchanged; S terms remain zero, all primary P/S picks are retained, and model/errors/search/receiver elevations are unchanged. Reference identities/ambiguity exclusions are fixed; reference coordinates do not enter fitting. No datum alignment, reference-based selection, strength fitting, or retraining is performed. The sample was reserved from this campaign's adaptive selection, but earlier full-catalog comparisons existed; it is not historically unseen blind data.

There are 300 primary events and {int(cohort.aux_eligible.sum())} auxiliary-eligible events. Auxiliary eligibility requires at least ten fitting observations and three S arrivals after the same six-instrument omission in both branches, determined from inputs before results. Ineligible events remain explicitly in tables/cohort.csv with a reason; all 300 receive primary fits. Coverage strata are descriptive only, not selected subgroups. Control xyz and origin reproduce original v1 within 0.001 km/0.001 s; all used timing equations are independently checked in checks.json.

## Locations

```text
{table('metrics')}
```

## Withheld prediction

Predict omitted observations at auxiliary locations and fitted origins, including fixed P terms and zero S terms, without recentering held-out residuals. Correction values were fit only on previous development events. These reserved arrivals do not enter the corresponding auxiliary fit.

```text
{table('heldout_metrics')}
```

## Fixed reference pairs

```text
{table('reference_summary')}
```

Shelly depth comparison uses the established nominal datum convention; other reference depths are absent. Reference discrepancies are not true errors.

## Identical station omission

```text
{table('omission_summary')}
```

## Frozen gates

```text
{table('decision_gates')}
```

A pass permits full production and whole-catalog verification only. A failure rejects confirmation; do not tune against this reserved sample or report it as still untouched in later selection. Native posterior uncertainty is conditional; the omission test is one observational perturbation, not a complete uncertainty calibration.

## Reproduction

Run `python -u 03_experiments/05_catalog_optimization/27_validate_reserved_p.py` in seismoagent (eight CPU workers). All four branches are executed for the eligible scope. Tables preserve corrections, all primary events and auxiliary statuses, phase predictions, fixed reference pairs, and coverage. Figures compare paired metrics and common-event geometry; native/ holds inputs/controls/logs. design.json fixes selection, gates and source hashes before inversion. Summary JSON uses atomic replacement and fsync for reliable record storage.
''')
    print('FINAL',json.dumps(result,indent=2),flush=True)


def main():
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        S.write_json=write_json
        data=prepare();run(data);finalize(data)

if __name__=='__main__':main()
