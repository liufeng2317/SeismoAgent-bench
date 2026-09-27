#!/usr/bin/env python3
"""Round 06: original development P corrections only; all S arrivals unchanged."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,sys,json
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('p_correction_runner',Path(__file__).with_name('25_constrain_station_corrections.py'))
R=importlib.util.module_from_spec(spec);sys.modules[spec.name]=R;spec.loader.exec_module(R)
S=R.S;OUT=HERE/'export/26_p_corrections';R.OUT=OUT;S.OUT=OUT


def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    cohort=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(cohort.event_id)].copy();picks['residual_s']=picks.residual_s_gamma
    stations=pd.read_csv(S.BASE/'stations.csv').set_index('id');aliases=stations.nll_station.to_dict()
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    c=pd.read_csv(HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv')
    c['original_development_correction_s']=c.proposed_tt_correction_s
    c['correction_active']=c.phase.eq('P');c.loc[~c.correction_active,'proposed_tt_correction_s']=0.
    c['nll_station']=c.instrument_id.map(aliases);c['status']='P_only_experiment_S_explicitly_zero'
    assert len(c)==61 and len(cohort)==147 and len(picks)==5413
    assert c.loc[c.phase.eq('P'),'proposed_tt_correction_s'].equals(c.loc[c.phase.eq('P'),'original_development_correction_s'])
    assert c.loc[c.phase.eq('S'),'proposed_tt_correction_s'].eq(0).all()
    reserved=set(pd.read_csv(HERE/'docs/optimization_reserved_events.csv').event_id);assert not reserved&set(cohort.event_id)
    c.to_csv(OUT/'tables/corrections.csv',index=False);cohort.to_csv(OUT/'tables/cohort.csv',index=False)
    files=[Path(__file__),Path(R.__file__),Path(S.__file__),Path(S.NLL.__file__),Path(S.DIAG.__file__),HERE/'00_config/nonlinloc.yaml',HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',S.BASE/'stations.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'docs/optimization_reserved_events.csv',HERE/'export/20_velocity_model_qualification/tables/events.csv',HERE/'export/20_velocity_model_qualification/tables/fit_phases.csv',Path(cfg['binary_directory'])/'NLLoc']
    files+=list((S.BASE/'grids').glob('time.*.time.*'))
    for eid in cohort.event_id:files += [S.BASE/'events_raw'/eid/'input.obs',S.BASE/'events_raw'/eid/'control.in']
    design=dict(round=6,max_rounds=30,intervention='Original stage16 development P corrections unchanged; S corrections exactly zero; retain all P/S observations, original errors, model, receiver elevations, search settings.',reason='Stage18 attributes dominant correction/depth shifts to S terms; no systematic S picking error established by stage19. Test P corrections without the S/depth component.',n_active_p=int(c.correction_active.sum()),gates='Stage17 gates plus median and P90 horizontal/absolute-depth station-omission displacement <=1.10 baseline. All pass: reserved-data validation only.',limitations='Model-specific empirical P terms, not established station clock errors. Original cell support was selected on both old cohorts; coefficient values were development-only. No reference fitting or correction-strength scan.',source_sha256={str(p):S.sha(p) for p in files})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==design
    else:S.write_json(path,design)
    print('Frozen P-only design:',int(c.correction_active.sum()),'P cells;',int((~c.correction_active).sum()),'S cells set to zero',flush=True)
    return cfg,cohort,picks,stations,c,c.set_index(['instrument_id','phase']).proposed_tt_correction_s.to_dict(),held,aliases


def report(data):
    S.report(data)
    result=json.loads((OUT/'run.json').read_text());e=pd.read_csv(OUT/'tables/events.csv');rows=[]
    for method in ['control','corrected']:
        a=e[e.branch.eq(method)].set_index('event_id');b=e[e.branch.eq('withheld_'+method)].set_index('event_id').loc[a.index]
        h=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km);z=(b.depth_km-a.depth_km).abs()
        rows.append(dict(method=method,median_horizontal_km=h.median(),p90_horizontal_km=h.quantile(.9),median_depth_km=z.median(),p90_depth_km=z.quantile(.9)))
    omission=pd.DataFrame(rows);o=omission.set_index('method');ratios=(o.loc['corrected']/o.loc['control']).to_dict()
    result['round']=6;result['omission_ratios']=ratios;result['gates']['omission_stability']=bool(all(v<=1.10 for v in ratios.values()))
    result['decision']='eligible_for_fresh_validation' if all(result['gates'].values()) else 'do_not_promote'
    S.write_json(OUT/'run.json',result);omission.to_csv(OUT/'tables/omission_summary.csv',index=False)
    pd.DataFrame([dict(gate=k,passed=v) for k,v in result['gates'].items()]).to_csv(OUT/'tables/decision_gates.csv',index=False)
    table=lambda name:pd.read_csv(OUT/f'tables/{name}.csv').to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text(f'''# Round 06: P-only station corrections

Decision: **{result['decision']}**. 294 new fits plus 294 verified controls, and three sign/zero-delay checks. The original full v1 is unchanged.

## Intervention

Retain original stage-16 development P corrections exactly; set every S correction to zero. All 5,413 P/S observations remain, with identical input times, errors, model grids, receiver elevations and search settings. There is no station/phase removal, magnitude adjustment, reference-based fitting, projection or scalar-strength tuning. Unsupported cells stay zero. Active P cells and explicitly inactive S cells are recorded in tables/corrections.csv; a table support flag does not imply an S correction was applied.

This follows the S-dominated depth-coupling evidence from stage 18 and the absence of a demonstrated systematic S picking error in stage 19. It does not prove P terms are physical clock errors. They are model-specific empirical corrections; source support was previously checked in both old cohorts, while coefficient values were fit on development events. The 300 reserved events are untouched.

Native prediction is Tgrid+c. Uniform positive delay and zero-delay checks verify sign and origin semantics; independent interpolation checks all fitted observations. Use explicit branch coordinates and paired shifts; legacy gamma_* fields in native helper tables refer to the supplied baseline cohort and do not describe a new GaMMA solution.

## Locations

```text
{table('metrics')}
```

Median paired depth change: {result['median_depth_shift_km']:.5f} km.

## Withheld prediction

All 923 withheld arrivals are predicted at auxiliary solutions and fitted origins; P uses frozen development corrections, S uses zero. No held-out recentering.

```text
{table('heldout_metrics')}
```

## Fixed reference pairs

```text
{table('reference_summary')}
```

Only Shelly uses the established nominal depth convention; other depth comparisons remain absent. References are not truth. No rematching or reference-derived coordinate shifts.

## Common station omission

```text
{table('omission_summary')}
```

## Frozen gates

```text
{table('decision_gates')}
```

A pass qualifies for reserved-data confirmation, not immediate full adoption. Preserve failed gates rather than tuning P strength or refitting using transfer/reference outcomes. Conditional posterior widths and this single omission test do not establish total accuracy.

## Reproduction

Run `python -u 03_experiments/05_catalog_optimization/26_test_p_corrections.py` in seismoagent. Eight CPU workers; prior verified baseline tables reused. The stage-25 execution helper and stage-17 native/report helpers are imported under this separate output root; the final report documents this actual P-only intervention. No previous files are modified. All sources and settings are frozen in design.json; tables, figures and native per-event controls/logs remain here.
''')
    print('FINAL',json.dumps(result,indent=2),flush=True)


def main():
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare();R.run(data);report(data)

if __name__=='__main__':main()
