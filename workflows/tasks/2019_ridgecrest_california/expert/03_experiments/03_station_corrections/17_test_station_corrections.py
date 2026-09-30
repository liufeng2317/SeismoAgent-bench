#!/usr/bin/env python3
"""Fixed station-phase correction experiment; no tuning and no full-catalog replacement."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import pandas as pd
from pyproj import Proj
import yaml
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]
OUT = HERE / 'export/17_station_corrections'
BASE = HERE / 'export/04_locate_nonlinloc'
XYZ = ['x_km', 'y_km', 'depth_km']
PROJ = Proj(proj='aeqd', lon_0=-117.55, lat_0=35.75, datum='WGS84', units='km')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


NLL = load('station_correction_nll', HERE/'01_pipeline/04_locate_nonlinloc.py')
DIAG = load('station_correction_grids', HERE/'02_diagnostics/16_diagnose_systematics.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n')


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'tables').mkdir(exist_ok=True)
    cfg = yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    cohort = pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    assert len(cohort) == 147 and cohort.event_id.is_unique
    allp = pd.read_csv(HERE/'export/10_validate_catalog/phases.csv', keep_default_na=False)
    picks = allp[allp.event_id.isin(cohort.event_id)].copy()
    # stage04 parser uses this only for inherited diagnostics; not for selection.
    picks['residual_s'] = picks.residual_s_gamma
    assert len(picks) == 5413 and picks.pick_id.is_unique
    assert not picks.duplicated(['event_id', 'instrument_id', 'phase']).any()
    stations = pd.read_csv(BASE/'stations.csv').set_index('id')
    corrections = pd.read_csv(HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv')
    assert len(corrections) == 61 and not corrections.duplicated(['instrument_id', 'phase']).any()
    corr = corrections.set_index(['instrument_id', 'phase']).proposed_tt_correction_s.to_dict()
    held = json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    assert len(held) == 6
    aliases = stations.nll_station.to_dict()
    corrections['nll_station'] = corrections.instrument_id.map(aliases)
    assert corrections.nll_station.notna().all()
    design = dict(
        intervention='Fixed stage16 development station-phase corrections; Tcorrected=Tgrid+c',
        cohort='All 147 connected stage15 transfer events; already-examined development validation',
        primary_branches=['control', 'corrected'],
        auxiliary_branches=['withheld_control', 'withheld_corrected'],
        held_out_instruments=held,
        correction_fit='Frozen stage16 development estimates; none estimated from transfer/reference coordinates',
        support='61 cells supported in both prior cohorts; all other cells unchanged',
        fixed='Original observations, order, model grids, errors, search, random seed and associations',
        auxiliary='Same fixed six instruments excluded in BOTH auxiliary fits; evaluate their unchanged arrivals afterward',
        gates={
            'execution': 'All 4 x 147 fits parse; all identity, delay-sign, zero-delay and baseline reproduction checks pass',
            'retention': 'Corrected LOCATED count >= control in primary and withheld branches',
            'depth_bounds': 'Primary corrected near-bound events increase by no more than 3/147 (within 0.5 km of 0/25)',
            'posterior_depth': 'Primary corrected p90 conditional posterior depth sigma <= 1.10 x control',
            'heldout_prediction': 'Auxiliary held-out arrival RMS <= 0.95 x control overall, and <= 1.05 x control separately for P and S; no held-out recentering',
            'reference_non_degradation': 'Each frozen reference median horizontal distance and compatible Shelly median absolute depth difference <= 1.10 x control',
            'reference_gain': 'At least one reference median horizontal or compatible Shelly depth difference <= 0.95 x control',
        },
        decision='All gates pass: proceed to fresh cohort validation, not adoption; otherwise do not promote and do not tune on this cohort',
        uncertainty='Posterior sigmas assume the fixed model; corrections can absorb location/path/picker bias and are not clock calibration',
        verification_event=sorted(cohort.event_id)[0],
        verification='No-delay vs zero-delay, and +0.2 s at every observed station/phase must keep xyz and shift origin by -0.2 s',
    )
    sources = [Path(__file__), HERE/'01_pipeline/04_locate_nonlinloc.py', HERE/'02_diagnostics/16_diagnose_systematics.py',
               HERE/'00_config/nonlinloc.yaml', HERE/'export/15_validate_transfer/inputs/events.csv',
               HERE/'export/10_validate_catalog/phases.csv', BASE/'stations.csv',
               HERE/'export/16_diagnose_systematics/proposed_station_corrections.csv',
               HERE/'export/12_relative_location_pilot/run.json',
               HERE/'export/10_validate_catalog/reference_matches.csv', HERE/'export/05_review_catalog/reference_events.csv',
               Path(cfg['binary_directory'])/'NLLoc', Path(cfg['binary_directory'])/'NLLocLib.c']
    sources += sorted((BASE/'grids').glob('time.*.time.*'))
    for eid in cohort.event_id:
        sources += [BASE/'events_raw'/eid/'input.obs', BASE/'events_raw'/eid/'control.in']
    frozen = dict(design=design, source_sha256={str(p):sha(p) for p in sources})
    path = OUT/'design.json'
    if path.exists():
        assert json.loads(path.read_text()) == frozen, 'Frozen design/input/code changed; use a new export destination.'
    else:
        write_json(path, frozen)
    cohort.to_csv(OUT/'tables/cohort.csv', index=False)
    corrections.to_csv(OUT/'tables/corrections.csv', index=False)
    (OUT/'README.md').write_text('''# Fixed station-phase correction experiment

Status: design frozen before new location results. See design.json for gates and input/code identities.
All 147 transfer events are retained. Run control/corrected and auxiliary six-instrument-withheld comparisons.
No picking, association or model tuning. Original observations and previous catalogs remain unchanged.
A successful experiment permits a fresh-cohort check, not immediate full-catalog adoption.
''')
    return cfg, cohort, picks, stations, corrections, corr, held, aliases


def solve(event, observations, branch, delay_map, aliases, cfg, held=()):
    eid = event['event_id']
    folder = OUT/'native'/branch/eid
    folder.mkdir(parents=True, exist_ok=True)
    source = BASE/'events_raw'/eid
    original = (source/'input.obs').read_text()
    if held:
        excluded = {aliases[x] for x in held}
        text = '\n'.join(line for line in original.splitlines() if not line.split() or line.split()[0] not in excluded)+'\n'
        observations = [r for r in observations if r['instrument_id'] not in held]
    else:
        text = original
    assert len(observations) >= 10
    control = '\n'.join(line for line in (source/'control.in').read_text().splitlines() if not line.startswith('LOCFILES '))+'\n'
    assert 'LOCDELAY ' not in control
    for (instrument, phase), delay in sorted(delay_map.items()):
        # Fifth numeric field is std_dev=0; source does not activate error rescaling.
        control += f'LOCDELAY {aliases[instrument]} {phase} 1 {delay:.10f} 0\n'
    control += f'LOCFILES input.obs NLLOC_OBS {BASE}/grids/time solution\n'
    digest = hashlib.sha256((text+control).encode()).hexdigest()
    done = folder/'complete.json'
    if done.exists():
        previous = json.loads(done.read_text())
        assert previous['input_sha256'] == digest
        assert sha(folder/previous['hyp']) == previous['hyp_sha256']
    else:
        (folder/'input.obs').write_text(text)
        (folder/'control.in').write_text(control)
        NLL.execute(Path(cfg['binary_directory'])/'NLLoc', folder/'control.in', folder, folder/'run.log', cfg['per_event_timeout_s'])
    paths = [p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name]
    assert len(paths) == 1, (branch, eid, 'Missing or multiple native solutions')
    row, links = NLL.parse_hyp(paths[0], event, observations, {v:k for k,v in aliases.items()}, PROJ)
    phase_lines = [line for line in paths[0].read_text().splitlines() if ' > ' in line and not line.startswith('PHASE ')]
    for line in phase_lines:
        left, right = line.split(' > ')
        a, b = left.split(), right.split()
        key = ({v:k for k,v in aliases.items()}[a[0]], a[4])
        assert abs(float(b[-1])-delay_map.get(key, 0)) < .00006
    for p in links:
        p['branch'] = branch
        p['tt_correction_s'] = delay_map.get((p['instrument_id'], p['phase']), 0.)
        # NLL's TTpred excludes the delay, explicitly preserve both semantics.
        p['corrected_predicted_travel_time_s'] = p['predicted_travel_time_s']+p['tt_correction_s']
    row['branch'] = branch
    write_json(done, dict(input_sha256=digest, hyp=paths[0].name, hyp_sha256=sha(paths[0])))
    return row, links


def check_observations(events, links, picks, stations):
    """Independent grid interpolation checks timing equation and correction sign."""
    p = pd.DataFrame(links).merge(picks[['pick_id', 'time_utc']], on='pick_id', validate='many_to_one')
    e = pd.DataFrame(events)
    p = p.merge(e[['branch', 'event_id', 'origin_time']+XYZ], on=['branch', 'event_id'], validate='many_to_one').reset_index(drop=True)
    tt, _ = DIAG.predict(BASE/'grids', p, stations)
    elapsed = (pd.to_datetime(p.time_utc, utc=True, format='ISO8601')-pd.to_datetime(p.origin_time, utc=True, format='ISO8601')).dt.total_seconds()
    errors = elapsed-tt-p.tt_correction_s-p.residual_s
    assert errors.abs().max() < .00035, errors.abs().max()
    assert np.max(np.abs(tt-p.predicted_travel_time_s)) < .00035
    return float(errors.abs().max())


def checks(data):
    cfg, cohort, picks, stations, corrections, corr, held, aliases = data
    event = cohort.sort_values('event_id').iloc[0].to_dict()
    obs = picks[picks.event_id.eq(event['event_id'])].to_dict('records')
    keys = [(p['instrument_id'], p['phase']) for p in obs]
    variants = {'check_no_delay':{}, 'check_zero_delay':{k:0. for k in keys}, 'check_uniform_positive':{k:.2 for k in keys}}
    results, phases = [], []
    for branch, delays in variants.items():
        row, links = solve(event, obs, branch, delays, aliases, cfg)
        results.append(row); phases.extend(links)
    r = pd.DataFrame(results).set_index('branch'); base = r.loc['check_no_delay']
    for name, offset in [('check_zero_delay', 0.), ('check_uniform_positive', -.2)]:
        other = r.loc[name]
        assert np.max(np.abs(other[XYZ].to_numpy(float)-base[XYZ].to_numpy(float))) < .001
        assert abs((pd.Timestamp(other.origin_time)-pd.Timestamp(base.origin_time)).total_seconds()-offset) < .001
    assert np.max(np.abs(base[XYZ].to_numpy(float)-np.array([event[x] for x in XYZ]))) < .001
    max_error = check_observations(results, phases, picks, stations)
    result = dict(zero_delay_pass=True, uniform_positive_02_origin_shift_s=float((pd.Timestamp(r.loc['check_uniform_positive','origin_time'])-pd.Timestamp(base.origin_time)).total_seconds()), max_residual_equation_error_s=max_error)
    write_json(OUT/'checks.json', result)
    print('Implementation checks:', result, flush=True)


def run(data, workers):
    cfg, cohort, picks, stations, corrections, corr, held, aliases = data
    groups = {eid:g.to_dict('records') for eid,g in picks.groupby('event_id')}
    results, links, failures = [], [], []
    began = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for branch in ['control', 'corrected', 'withheld_control', 'withheld_corrected']:
            delays = corr if branch.endswith('corrected') else {}
            for event in cohort.to_dict('records'):
                f = pool.submit(solve, event, groups[event['event_id']], branch, delays, aliases, cfg, held if branch.startswith('withheld_') else ())
                futures[f] = (branch, event['event_id'])
        for i,f in enumerate(as_completed(futures), 1):
            try:
                row, pp = f.result();results.append(row);links.extend(pp)
            except Exception as exc:
                failures.append(dict(branch=futures[f][0], event_id=futures[f][1], error=repr(exc)))
                print('FAILED', failures[-1], flush=True)
            if i % 40 == 0 or i == len(futures):
                print(f'[{i}/{len(futures)}] parsed={len(results)} failed={len(failures)} elapsed={time.monotonic()-began:.1f}s', flush=True)
    pd.DataFrame(failures, columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv', index=False)
    pd.DataFrame(results).sort_values(['branch','event_id']).to_csv(OUT/'tables/events.csv', index=False)
    pd.DataFrame(links).sort_values(['branch','pick_id']).to_csv(OUT/'tables/fit_phases.csv', index=False)
    if failures:
        raise RuntimeError('Fits incomplete; retain failures and do not issue an adoption decision.')
    error = check_observations(results, links, picks, stations)
    baseline = pd.DataFrame(results).query("branch == 'control'").set_index('event_id').loc[cohort.event_id]
    delta = np.max(np.abs(baseline[XYZ].to_numpy()-cohort[XYZ].to_numpy()))
    dt = np.max(np.abs((pd.to_datetime(baseline.origin_time.to_numpy(), utc=True, format='ISO8601')-pd.to_datetime(cohort.origin_time.to_numpy(), utc=True, format='ISO8601')).total_seconds()))
    assert delta < .001 and dt < .001, (delta,dt)
    check = json.loads((OUT/'checks.json').read_text())
    check.update(all_control_max_xyz_difference_km=float(delta),all_control_max_origin_difference_s=float(dt),all_fit_max_residual_equation_error_s=error,parsed_fits=len(results))
    write_json(OUT/'checks.json',check)


def rms(values):
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float)**2)))


def report(data):
    cfg, cohort, picks, stations, corrections, corr, held, aliases = data
    events = pd.read_csv(OUT/'tables/events.csv')
    assert len(events) == 588 and not events.duplicated(['branch','event_id']).any()
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
        'execution':bool(json.loads((OUT/'checks.json').read_text())['parsed_fits']==588),
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
    table=lambda df:df.to_string(index=False,float_format=lambda x:f'{x:.4f}')
    text=f'''# Fixed station-phase correction experiment

**Decision: {decision}.** This is a 147-event development-validation experiment,
not a full catalog or a new v1/v2 release. No previous catalog, picks or waveforms changed.

## Design and implementation

Run from the expert root in seismoagent:
`python -u 03_experiments/03_station_corrections/17_test_station_corrections.py --stage all --workers 8`.
Separate `check`, `locate`, `report` stages are available; identical inputs are resumable.
`design.json` froze decision gates and source identities before new inversions.

The 61 station-phase corrections are exactly the stage-16 development estimates.
Support was assessed on both previously examined cohorts; correction values were not
estimated on this transfer cohort or from reference coordinates. Unsupported phases
retain zero correction and explicit support flags. No correction scaling or rejection
was fitted after outcomes. Original 147 event identities and all 5,413 associated picks
are retained in the primary branches. Neither association nor pick errors changed.

Controls and observation files come directly from stage 04. Only grid-path resolution
and LOCDELAY statements differ. LOCDELAY subtracts c internally from observed time,
which is equivalent to Tcorrected=Tgrid+c; original input timestamps are unchanged.
NLL's output TTpred excludes c; fit_phases.csv preserves both predictions explicitly.
Local NLLocLib.c ApplyTimeDelays/GetTimeDelays and archived source hashes document the
implementation. The [official NonLinLoc source](https://github.com/ut-beg-texnet/NonLinLoc)
provides the upstream implementation. No receiver-height or velocity-grid change occurred.

A zero-delay run reproduces the control. Uniform +0.2-s delays preserve location and
shift origin by -0.2 s. Independent grid interpolation checks the residual equation
for every used observation. All 147 control locations/origin times reproduce the
archived baseline within 0.001 km / 0.001 s. Checks are in checks.json.

## Paired locations

```text
{table(metrics)}
```

Median horizontal shift: {stats['median_horizontal_shift_km']:.3f} km; median signed
depth shift: {stats['median_depth_shift_km']:.3f} km. There are
{stats['large_3d_shifts_over_3km']} events with >3-km 3D change; retain these for review,
not automatic rejection. Conditional posterior sigmas omit structural/model errors
and cannot establish absolute accuracy. Station-phase fit RMS improves in
{stats['fit_station_phases_improved']}/{stats['fit_station_phases_total']} observed groups;
all adverse groups are retained in station_phase_comparison.csv.

## Withheld observations

Both auxiliary branches omit the same six instruments used in the earlier DD checks:
{', '.join(held)}. Their arrival residuals are evaluated at auxiliary locations and
fitted origins, without recentering or reference-derived origin shifts. The fixed
correction may be estimated for these instruments from DEVELOPMENT events; their
TRANSFER arrivals never enter the corresponding auxiliary location fit. This is
prediction on held-out observations, but not a fresh blind benchmark, because the
cohort, stations and stage-16 diagnostic results have already been examined.

```text
{table(hm)}
```

## Frozen reference pairs

Reference identities and ambiguity exclusions are inherited unchanged. Primary
comparisons use identical events located in both branches. Only Shelly has the
compatible depth datum used here; other depth metrics remain blank. These are
reference discrepancies, not errors relative to known truth.

```text
{table(refsumm)}
```

## Decision gates

```text
{table(pd.DataFrame([dict(gate=k,passed=v) for k,v in tests.items()]))}
```

All gates must pass to proceed to a new independent cohort; passing does not authorize
full adoption. If any gate fails, retain v1 and the frozen hypoDD/CC comparisons and
do not tune correction strength on this cohort. Reduced residuals or posterior
sigmas alone are insufficient evidence of improved absolute locations. Mainshock
uncertainties remain outside this ordinary-event experiment.

## Files

- tables/events.csv and fit_phases.csv: all four branches, explicit status and pick identities.
- tables/cohort.csv and corrections.csv: frozen cohort and correction values.
- tables/heldout_predictions.csv: every withheld prediction, including unsupported phases.
- tables/paired_events.csv: event shifts, depth, RMS, uncertainty and large-shift flags.
- tables/reference_pairs.csv and reference_summary.csv: fixed-pair comparisons.
- tables/station_phase_comparison.csv and decision_gates.csv: adverse effects and decision.
- figures/: residual/depth comparisons and common-axis locations.
- native/: exact controls, unchanged or explicitly withheld observations, logs and results.

No full-catalog processing or new parameter scan was performed.
'''
    (OUT/'README.md').write_text(text)
    print('DECISION',json.dumps(stats,indent=2),flush=True)
    print(table(refsumm),flush=True)


def plot(events,paired,vectors,held):
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    colors={'control':'#2878B5','corrected':'#D65F24'}
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.6),layout='constrained')
    ax=axes[0,0];limit=max(paired.control_rms_s.max(),paired.corrected_rms_s.max())*1.05
    ax.scatter(paired.control_rms_s,paired.corrected_rms_s,s=9,c=colors['corrected'],alpha=.7,rasterized=True)
    ax.plot([0,limit],[0,limit],color='k',lw=.7);ax.set(xlabel='Control event RMS (s)',ylabel='Corrected event RMS (s)',xlim=(0,limit),ylim=(0,limit))
    ax=axes[0,1]
    ax.scatter(paired.control_depth_km,paired.corrected_depth_km,s=9,c=colors['corrected'],alpha=.7,rasterized=True)
    lim=max(paired.control_depth_km.max(),paired.corrected_depth_km.max())+1
    ax.plot([0,lim],[0,lim],color='k',lw=.7);ax.set(xlabel='Control depth (km)',ylabel='Corrected depth (km)',xlim=(0,lim),ylim=(0,lim))
    ax=axes[1,0]
    for name,col in colors.items():
        vals=np.sort(np.abs(held.loc[held.branch.eq('withheld_'+name),'residual_s']))
        ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),color=col,label=name.capitalize())
    ax.set(xlabel='Withheld absolute residual (s)',ylabel='Cumulative fraction',xlim=(0,2));ax.legend(frameon=False)
    ax=axes[1,1]
    for name,col in colors.items():
        vals=np.sort(vectors.loc[vectors.branch.eq(name)&vectors.catalog.eq('Shelly'),'depth_difference_km'].abs())
        ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),color=col,label=name.capitalize())
    ax.set(xlabel='Absolute depth difference to Shelly (km)',ylabel='Cumulative fraction');ax.legend(frameon=False)
    for label,ax in zip('abcd',axes.flat):ax.set_title(label,loc='left',fontweight='bold')
    for ext in ['png','pdf']:fig.savefig(folder/f'01_paired_diagnostics.{ext}',dpi=240)
    plt.close(fig)
    sh=vectors[vectors.catalog.eq('Shelly')&vectors.branch.eq('control')]
    sources=[]
    for name in ['control','corrected']:
        q=events[events.branch.eq(name)].set_index('event_id').loc[sh.event_id]
        sources.append((name.capitalize(),q.x_km.to_numpy(),q.y_km.to_numpy(),q.depth_km.to_numpy()))
    sources.append(('Shelly',sh.reference_x_km.to_numpy(),sh.reference_y_km.to_numpy(),sh.reference_depth_km.to_numpy()))
    fig,axes=plt.subplots(2,3,figsize=(8,5),sharex=True,sharey='row',layout='constrained')
    for i,(name,x,y,z) in enumerate(sources):
        axes[0,i].scatter(x,y,s=7,c='black',alpha=.5,rasterized=True);axes[0,i].set_title(name)
        axes[1,i].scatter(x,z,s=7,c='black',alpha=.5,rasterized=True);axes[1,i].set_xlabel('East (km)')
        axes[0,i].set_aspect('equal',adjustable='box')
    axes[0,0].set_ylabel('North (km)');axes[1,0].set_ylabel('Depth (km)');axes[1,0].invert_yaxis()
    for ext in ['png','pdf']:fig.savefig(folder/f'02_common_event_locations.{ext}',dpi=240)
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['all','check','locate','report'],default='all')
    ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args()
    if args.workers<1:ap.error('workers must be positive')
    import fcntl
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare()
        if args.stage in ['all','check','locate']:checks(data)
        if args.stage in ['all','locate']:run(data,args.workers)
        if args.stage in ['all','report']:report(data)


if __name__=='__main__':
    main()
