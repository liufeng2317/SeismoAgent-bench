#!/usr/bin/env python3
"""Round 05: development-depth-gauge-constrained station corrections."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,sys,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('constrained_correction_helpers',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
S=importlib.util.module_from_spec(spec);sys.modules[spec.name]=S;spec.loader.exec_module(S)
OUT=HERE/'export/25_constrained_corrections';S.OUT=OUT


def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    cohort=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(cohort.event_id)].copy();picks['residual_s']=picks.residual_s_gamma
    stations=pd.read_csv(S.BASE/'stations.csv').set_index('id');aliases=stations.nll_station.to_dict()
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    c=pd.read_csv(HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv')
    dev=pd.read_csv(HERE/'export/16_diagnose_systematics/pick_diagnostics.csv')
    dev=dev[dev.cohort.eq('development')].reset_index(drop=True)
    reserved=set(pd.read_csv(HERE/'docs/optimization_reserved_events.csv').event_id)
    assert not set(dev.event_id)&set(cohort.event_id) and not reserved&(set(dev.event_id)|set(cohort.event_id))
    assert len(c)==61 and dev.event_id.nunique()==144 and len(cohort)==147
    keys=list(zip(c.instrument_id,c.phase));lookup={k:i for i,k in enumerate(keys)}
    _,grad=S.DIAG.predict(S.BASE/'grids',dev,stations)
    sensitivity=[]
    for eid,g in dev.groupby('event_id'):
        gg=grad[g.index];w=1/(cfg['model_error_s']**2+np.array([cfg['pick_error_s'][p]**2 for p in g.phase]))
        nuisance=np.column_stack([gg[:,:2],np.ones(len(g))]);root=np.sqrt(w)
        coeff=np.linalg.lstsq(nuisance*root[:,None],gg[:,2]*root,rcond=None)[0]
        zperp=gg[:,2]-nuisance@coeff;den=float(np.sum(w*zperp*zperp));assert den>1e-8
        kernel=-w*zperp/den
        assert abs(kernel.sum())<1e-8 and np.max(np.abs(kernel@nuisance))<1e-8
        row=np.zeros(len(c))
        for (_,p),k in zip(g.iterrows(),kernel):
            index=lookup.get((p.instrument_id,p.phase))
            if index is not None:row[index]+=k
        sensitivity.append(row)
    matrix=np.array(sensitivity);a=matrix.mean(axis=0);c0=c.proposed_tt_correction_s.to_numpy()
    # Minimum support-weighted change from the original correction vector, with a*c=0.
    support=c.development_n.to_numpy(float);direction=a/support
    projected=c0-direction*float(a@c0)/float(a@direction)
    assert abs(float(a@projected))<1e-10
    c['unconstrained_correction_s']=c0;c['mean_depth_sensitivity_km_per_s']=a
    c['proposed_tt_correction_s']=projected;c['nll_station']=c.instrument_id.map(aliases)
    c['status']='development_geometry_constrained_experimental_correction'
    c.to_csv(OUT/'tables/corrections.csv',index=False);cohort.to_csv(OUT/'tables/cohort.csv',index=False)
    constraints=dict(n_development=144,original_mean_linear_depth_shift_km=float(np.mean(matrix@c0)),constrained_mean_linear_depth_shift_km=float(np.mean(matrix@projected)),original_median_linear_depth_shift_km=float(np.median(matrix@c0)),constrained_median_linear_depth_shift_km=float(np.median(matrix@projected)),max_correction_change_s=float(np.max(np.abs(projected-c0))))
    files=[Path(__file__),Path(S.__file__),Path(S.NLL.__file__),Path(S.DIAG.__file__),HERE/'00_config/nonlinloc.yaml',HERE/'export/16_diagnose_systematics/pick_diagnostics.csv',HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',S.BASE/'stations.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'docs/optimization_reserved_events.csv',HERE/'export/20_velocity_model_qualification/tables/events.csv',HERE/'export/20_velocity_model_qualification/tables/fit_phases.csv',Path(cfg['binary_directory'])/'NLLoc']
    files+=list((S.BASE/'grids').glob('time.*.time.*'))
    for eid in cohort.event_id:files += [S.BASE/'events_raw'/eid/'input.obs',S.BASE/'events_raw'/eid/'control.in']
    design=dict(round=5,max_rounds=30,intervention='One mean-development-depth identifiability constraint on the frozen 61 correction cells; no reference fitting, damping scan, or velocity change.',estimator='A is mean development depth sensitivity to station corrections after projecting out x,y,origin. Minimize sum(n_dev*(c-c0)^2) subject to A*c=0. n_dev is a declared support weighting, not estimated precision.',limitation='Gauge anchored to original development depths, not true depths. Constraint is mean/linear/local, not a guarantee for individual events or transfer. Original 61-cell support was previously chosen using both cohorts; coefficients and new geometric constraint use only development values.',gates='Stage17 gates plus same fixed-omission median/P90 horizontal/depth displacement <=1.10 baseline. All must pass before fresh validation. No full adoption from this examined transfer cohort.',constraints=constraints,source_sha256={str(p):S.sha(p) for p in files})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==design
    else:S.write_json(path,design)
    print('Frozen constraint:',json.dumps(constraints),flush=True)
    corr=c.set_index(['instrument_id','phase']).proposed_tt_correction_s.to_dict()
    return cfg,cohort,picks,stations,c,corr,held,aliases


def run(data):
    cfg,cohort,picks,stations,c,corr,held,aliases=data
    S.checks(data)
    base=HERE/'export/20_velocity_model_qualification/tables'
    e=pd.read_csv(base/'events.csv');p=pd.read_csv(base/'fit_phases.csv')
    rows=e[e.branch.isin(['control','withheld_control'])].to_dict('records')
    p=p[p.branch.isin(['control','withheld_control'])].copy();p['tt_correction_s']=0.;p['corrected_predicted_travel_time_s']=p.predicted_travel_time_s
    phases=p.to_dict('records');failures=[];groups={eid:g.to_dict('records') for eid,g in picks.groupby('event_id')}
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs={pool.submit(S.solve,e,groups[e['event_id']],b,corr,aliases,cfg,held if b.startswith('withheld') else ()):(b,e['event_id']) for b in ['corrected','withheld_corrected'] for e in cohort.to_dict('records')}
        for i,f in enumerate(as_completed(jobs),1):
            try:r,pp=f.result();rows.append(r);phases.extend(pp)
            except Exception as exc:failures.append(dict(branch=jobs[f][0],event_id=jobs[f][1],error=repr(exc)));print(failures[-1],flush=True)
            if i%40==0 or i==len(jobs):print(f'[{i}/294] failed={len(failures)}',flush=True)
    pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(phases).to_csv(OUT/'tables/fit_phases.csv',index=False)
    assert not failures
    error=S.check_observations(rows,phases,picks,stations)
    check=json.loads((OUT/'checks.json').read_text());check.update(parsed_fits=len(rows),new_fits=294,reused_verified_controls=294,all_fit_max_residual_equation_error_s=error);S.write_json(OUT/'checks.json',check)


def report(data):
    S.report(data)
    result=json.loads((OUT/'run.json').read_text());events=pd.read_csv(OUT/'tables/events.csv');omission=[]
    for method in ['control','corrected']:
        a=events[events.branch.eq(method)].set_index('event_id');b=events[events.branch.eq('withheld_'+method)].set_index('event_id').loc[a.index]
        h=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km);z=(b.depth_km-a.depth_km).abs()
        omission.append(dict(method=method,median_horizontal_km=h.median(),p90_horizontal_km=h.quantile(.9),median_depth_km=z.median(),p90_depth_km=z.quantile(.9)))
    omission=pd.DataFrame(omission);oo=omission.set_index('method');ratios=(oo.loc['corrected']/oo.loc['control']).to_dict()
    result['round']=5;result['omission_ratios']=ratios;result['gates']['omission_stability']=bool(all(v<=1.10 for v in ratios.values()))
    result['decision']='eligible_for_fresh_validation' if all(result['gates'].values()) else 'do_not_promote'
    S.write_json(OUT/'run.json',result);omission.to_csv(OUT/'tables/omission_summary.csv',index=False)
    pd.DataFrame([dict(gate=k,passed=v) for k,v in result['gates'].items()]).to_csv(OUT/'tables/decision_gates.csv',index=False)
    table=lambda name:pd.read_csv(OUT/f'tables/{name}.csv').to_string(index=False,float_format=lambda v:f'{v:.5f}')
    constraint=json.loads((OUT/'design.json').read_text())['constraints']
    (OUT/'README.md').write_text(f'''# Round 05: development-depth-constrained station corrections

Decision: **{result['decision']}**. 294 new transfer fits plus 294 verified baseline controls; three additional zero/uniform-delay implementation checks. No full-catalog replacement.

## Physical question and estimator

Can the useful timing/horizontal component of station corrections be separated from the mean depth mode identified in stage 18? Keep the original 61 correction cells; use only the 144 development events to calculate the geometric constraint. At their original locations, project the depth travel-time derivative out of horizontal and origin-time nuisance directions using original inverse total variances. Aggregate the resulting station/phase sensitivities per event, then average over development events to form A.

Starting from original development corrections c0, minimize sum(n_dev*(c-c0)^2) subject to A*c=0. Closed form: c=c0-(A/n_dev)*(A*c0)/sum(A²/n_dev). Development counts express a fixed support preference, not estimated uncertainty. No multiplier scan, reference depths, velocity adjustment or post-result scaling. Original cell support was selected in earlier work on both cohorts; this is not blind validation. The 300 reserved events remain unused.

This fixes a local mean development depth gauge, not true depth or the individual events. Actual nonlinear transfer depth shifts remain free and must be evaluated. Original predicted mean development shift: {constraint['original_mean_linear_depth_shift_km']:.5f} km; constrained: {constraint['constrained_mean_linear_depth_shift_km']:.8f} km. Maximum correction change: {constraint['max_correction_change_s']:.5f} s.

Native LOCDELAY implements Tcorrected=Tgrid+c; original observations are unchanged. Unsupported cells remain zero. Positive uniform delay and zero-delay checks retain the established sign/origin semantics; independent grid checks verify every fitted residual. Exact corrections and geometric sensitivities are in tables/corrections.csv.

## Locations

```text
{table('metrics')}
```

Median paired transfer depth change: {result['median_depth_shift_km']:.5f} km.

## Withheld observations

Both auxiliary fits omit the same six instruments. Predict all 923 omitted arrivals at the corresponding fitted origins/locations with fixed development corrections; no held-out recentering.

```text
{table('heldout_metrics')}
```

## Fixed reference identities

```text
{table('reference_summary')}
```

Reference discrepancies are not truth errors. Depth comparisons retain the existing nominal Shelly convention; no coordinate alignment or rematching.

## Same station-omission perturbation

```text
{table('omission_summary')}
```

## Predeclared gates

```text
{table('decision_gates')}
```

A pass permits fresh validation only. A failure is retained without further correction-strength or projection-weight tuning on transfer results. Posterior widths remain conditional on the model; the omission comparison is one fixed perturbation, not a complete uncertainty calibration.

## Reproduction

Run `python -u 03_experiments/05_catalog_optimization/25_constrain_station_corrections.py` in seismoagent (eight CPU workers). This reuses stage-17 native execution/check/report helpers under this distinct output root; the final report replaces their historical narrative with this experiment's actual definition. Tables, figures and native files are local to this output. Previous sources/outputs are unchanged; design.json freezes their identities and the estimator before inversion. Logs are in run.log and each native event directory.
''')
    print('FINAL',json.dumps(result,indent=2),flush=True)


def main():
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare();run(data);report(data)

if __name__=='__main__':main()
