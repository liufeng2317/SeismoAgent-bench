#!/usr/bin/env python3
"""One fixed HK profile experiment under an explicit common depth datum."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]
OUT = HERE/'export/20_velocity_model_qualification'
BASE = HERE/'export/04_locate_nonlinloc'
XYZ = ['x_km', 'y_km', 'depth_km']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


HELP = load('hk_helpers', HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
NLL, DIAG, PROJ = HELP.NLL, HELP.DIAG, HELP.PROJ
sha, write_json, rms = HELP.sha, HELP.write_json, HELP.rms


def prepare():
    OUT.mkdir(exist_ok=True); (OUT/'tables').mkdir(exist_ok=True)
    cfg = yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    cohort = pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    picks = pd.read_csv(HERE/'export/10_validate_catalog/phases.csv', keep_default_na=False)
    picks = picks[picks.event_id.isin(cohort.event_id)].copy()
    picks['residual_s'] = picks.residual_s_gamma
    stations = pd.read_csv(BASE/'stations.csv').set_index('id')
    held = json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    assert len(cohort) == 147 and len(picks) == 5413 and len(held) == 6
    assert cohort.event_id.is_unique and picks.pick_id.is_unique
    sources = [Path(__file__), Path(HELP.__file__), Path(NLL.__file__), Path(DIAG.__file__),
               HERE/'00_config/nonlinloc.yaml', BASE/'stations.csv',
               HERE/'export/15_validate_transfer/inputs/events.csv', HERE/'export/10_validate_catalog/phases.csv',
               HERE/'export/12_relative_location_pilot/run.json', HERE/'export/10_validate_catalog/reference_matches.csv',
               HERE/'export/05_review_catalog/reference_events.csv',
               HERE.parents[2]/'data/2019_ridgecrest_california/references/AWR2025_CALTECHDATA/supplement/HUTTON2010__paper.pdf']
    sources += [Path(cfg['binary_directory'])/x for x in ['NLLoc','Vel2Grid','Grid2Time']]
    sources += sorted((BASE/'grids').glob('time.*.time.*')) + [BASE/'grids/P.in', BASE/'grids/S.in']
    for eid in cohort.event_id:
        sources += [BASE/'events_raw'/eid/'input.obs', BASE/'events_raw'/eid/'control.in']
    design = dict(
        intervention='HK constant layers, versus archived linear Shelly-derived baseline; no station corrections',
        model=dict(top_km=[0.,5.5,16.,32.], vp_km_s=[5.5,6.3,6.7,7.8], vp_vs=1.73,
                   source='Hutton et al. 2010 Table 5; https://scedc.caltech.edu/about/BSSA_2010_Hutton_SCSN_cat.pdf'),
        datum='Explicit experiment convention: layer depths below fixed +0.7 km ASL plane. Not a reconstruction of native SCSN datum. First layer extended to grid top -3 km; receivers unchanged.',
        fixed='147 events; original picks/order/errors/association/search/seed/receiver elevations; no fitted offsets or scanning',
        held_out_instruments=held,
        limitation='Previously examined transfer cohort; not fresh blind validation. Reference discrepancies are not truth errors.',
        gates=dict(execution='588 parsed fits; unchanged inputs; control reproduction and independent travel-time checks',
                   retention='No decrease in LOCATED count in either comparison',
                   boundaries='HK boundary count <= control +3',
                   uncertainty='HK p90 posterior depth sigma <=1.10 control',
                   heldout='All RMS <=0.95 control, P and S each <=1.05 control; no origin recentering',
                   reference='Each horizontal median and conventionally aligned Shelly absolute-depth median <=1.10 control'),
        decision='All pass: eligible for fresh-cohort validation, never immediate full adoption; otherwise close this fixed trial.',
        source_sha256={str(p):sha(p) for p in sources})
    dest = OUT/'design.json'
    if dest.exists():
        assert json.loads(dest.read_text()) == design, 'Frozen sources changed; do not overwrite this experiment.'
    else:
        write_json(dest, design)
    cohort.to_csv(OUT/'tables/cohort.csv', index=False)
    return cfg, cohort, picks, stations, held


def make_grids(cfg):
    folder = OUT/'hk_grids'; folder.mkdir(exist_ok=True)
    layers = '\n'.join(f'LAYER {z} {v} 0 {v/1.73:.10f} 0 2.7 0' for z,v in [(-3,5.5),(0,5.5),(5.5,6.3),(16,6.7),(32,7.8)])
    for phase in ['P','S']:
        original = (BASE/f'grids/{phase}.in').read_text().splitlines()
        first = next(i for i,line in enumerate(original) if line.startswith('LAYER '))
        lines = [line for line in original if not line.startswith('LAYER ')]
        lines.insert(first, layers)
        text = '\n'.join(lines)+'\n'
        control = folder/f'{phase}.in'
        marker = folder/f'{phase}_complete.json'
        if marker.exists():
            assert control.read_text() == text
            assert all(sha(folder/k) == v for k,v in json.loads(marker.read_text()).items())
            continue
        control.write_text(text)
        for binary in ['Vel2Grid','Grid2Time']:
            print(f'Grid {phase}: {binary}', flush=True)
            NLL.execute(Path(cfg['binary_directory'])/binary, control, folder, folder/f'{phase}_{binary}.log', 600)
        # Verify constant-layer velocity values in the generated slow-length grid.
        head = (folder/f'model.{phase}.mod.hdr').read_text().splitlines()[0].split()
        nx,ny,nz = map(int, head[:3]); step = float(head[8]); top = float(head[5])
        grid = np.fromfile(folder/f'model.{phase}.mod.buf', dtype=np.float32).reshape(nx,ny,nz)
        for z,v in [(1.,5.5),(8.,6.3),(20.,6.7),(34.,7.8)]:
            expected = v if phase == 'P' else v/1.73
            actual = step/grid[0,0,round((z-top)/step)]
            assert abs(actual-expected)<1e-5, (phase,z,actual,expected)
        files = sorted(folder.glob(f'time.{phase}.*.time.*'))
        assert len(files) == 74
        write_json(marker, {p.name:sha(p) for p in files})
    return folder


def solve(event, observations, branch, cfg, stations, held):
    folder = OUT/'native'/branch/event['event_id']; folder.mkdir(parents=True, exist_ok=True)
    aliases = stations.nll_station.to_dict()
    src = BASE/'events_raw'/event['event_id']
    text = (src/'input.obs').read_text()
    if branch.startswith('withheld_'):
        excluded = {aliases[k] for k in held}
        text = '\n'.join(l for l in text.splitlines() if not l.split() or l.split()[0] not in excluded)+'\n'
        observations = [p for p in observations if p['instrument_id'] not in held]
    grid = OUT/'hk_grids' if branch.endswith('hk') else BASE/'grids'
    control = '\n'.join(l for l in (src/'control.in').read_text().splitlines() if not l.startswith('LOCFILES '))+'\n'
    assert 'LOCDELAY ' not in control
    control += f'LOCFILES input.obs NLLOC_OBS {grid}/time solution\n'
    digest = hashlib.sha256((text+control).encode()).hexdigest()
    marker = folder/'complete.json'
    if marker.exists():
        previous = json.loads(marker.read_text())
        assert previous['input_sha256'] == digest and sha(folder/previous['hyp']) == previous['hyp_sha256']
        assert (folder/'input.obs').read_text() == text and (folder/'control.in').read_text() == control
    else:
        (folder/'input.obs').write_text(text); (folder/'control.in').write_text(control)
        NLL.execute(Path(cfg['binary_directory'])/'NLLoc', folder/'control.in', folder, folder/'run.log', cfg['per_event_timeout_s'])
    paths = [p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name]
    assert len(paths) == 1
    row, links = NLL.parse_hyp(paths[0],event,observations,{v:k for k,v in aliases.items()},PROJ)
    # These inherited parser fields refer to the supplied NLL cohort, not GaMMA; drop misleading names.
    for k in ['gamma_depth_km','gamma_rms_residual_s','gamma_rms_unweighted_s']:
        row.pop(k)
    row['branch'] = branch
    for p in links: p['branch'] = branch
    write_json(marker, dict(input_sha256=digest,hyp=paths[0].name,hyp_sha256=sha(paths[0])))
    return row, links


def run(data, workers):
    cfg, cohort, picks, stations, held = data
    make_grids(cfg)
    groups = {k:g.to_dict('records') for k,g in picks.groupby('event_id')}
    rows, phases, failures = [], [], []
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(solve,e,groups[e['event_id']],b,cfg,stations,held):(b,e['event_id'])
                   for b in ['control','hk','withheld_control','withheld_hk'] for e in cohort.to_dict('records')}
        for i,f in enumerate(as_completed(futures),1):
            try:
                row,pp = f.result(); rows.append(row); phases.extend(pp)
            except Exception as exc:
                failures.append(dict(branch=futures[f][0],event_id=futures[f][1],error=repr(exc)))
                print('FAILED',failures[-1],flush=True)
            if i%40 == 0 or i == len(futures):
                print(f'[{i}/588] parsed={len(rows)} failures={len(failures)} elapsed={time.monotonic()-start:.1f}s',flush=True)
    pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    pd.DataFrame(rows).sort_values(['branch','event_id']).to_csv(OUT/'tables/events.csv',index=False)
    pd.DataFrame(phases).sort_values(['branch','pick_id']).to_csv(OUT/'tables/fit_phases.csv',index=False)
    assert not failures, 'Incomplete experiment; inspect logs and resume unchanged inputs.'


def report(data):
    cfg, cohort, picks, stations, held = data
    events = pd.read_csv(OUT/'tables/events.csv'); fits = pd.read_csv(OUT/'tables/fit_phases.csv')
    assert len(events) == 588 and not events.duplicated(['branch','event_id']).any()
    a = events[events.branch.eq('control')].set_index('event_id').loc[cohort.event_id]
    xyz_error = float(np.abs(a[XYZ].to_numpy()-cohort[XYZ].to_numpy()).max())
    origin_error = float(np.abs((pd.to_datetime(a.origin_time.to_numpy(),utc=True,format='ISO8601')-pd.to_datetime(cohort.origin_time.to_numpy(),utc=True,format='ISO8601')).total_seconds()).max())
    assert xyz_error<.001 and origin_error<.001
    errors = []; held_rows = []; metrics = []
    for branch,e in events.groupby('branch'):
        grid = OUT/'hk_grids' if branch.endswith('hk') else BASE/'grids'
        fp = fits[fits.branch.eq(branch)]
        p = fp.merge(picks[['pick_id','time_utc']],on='pick_id',validate='one_to_one').merge(e[['event_id','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        tt,_ = DIAG.predict(grid,p,stations)
        elapsed = (pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()
        errors.extend([float(np.abs(tt-p.predicted_travel_time_s).max()),float(np.abs(elapsed-tt-p.residual_s).max())])
        assert max(errors)<.00035
        metrics.append(dict(branch=branch,n=len(e),located=int(e.status.eq('LOCATED').sum()),boundary=int(((e.depth_km<.5)|(e.depth_km>24.5)).sum()),median_depth_km=e.depth_km.median(),fit_rms_s=rms(fp.residual_s),p90_sigma_depth_km=e.posterior_sigma_depth_km.quantile(.9)))
        if branch.startswith('withheld_'):
            assert not set(fp.instrument_id)&set(held)
            p = picks[picks.instrument_id.isin(held)].merge(e[['event_id','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
            tt,_ = DIAG.predict(grid,p,stations)
            p['predicted_travel_time_s'] = tt
            p['residual_s'] = (pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt
            p['branch'] = branch; held_rows.append(p)
    held_rows = pd.concat(held_rows,ignore_index=True)
    hm = pd.DataFrame([dict(branch=b,phase=phase,n=len(q),rms_s=rms(q.residual_s)) for b,g in held_rows.groupby('branch') for phase,q in [('all',g),('P',g[g.phase.eq('P')]),('S',g[g.phase.eq('S')])]])
    assert hm[hm.phase.eq('all')].n.eq(923).all()
    matches = pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv')
    refs = pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    valid = set.intersection(*(set(events[(events.branch==b)&events.status.eq('LOCATED')].event_id) for b in ['control','hk']))
    m = matches[matches.event_id.isin(valid)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'],validate='many_to_one')
    vectors = []; summary = []
    for branch in ['control','hk']:
        e = events[events.branch.eq(branch)].set_index('event_id').loc[m.event_id]
        rx,ry = PROJ(m.longitude.to_numpy(),m.latitude.to_numpy())
        v = m[['event_id','catalog','reference_id','reference_depth_km']].copy()
        v['branch']=branch; v['reference_x_km']=rx; v['reference_y_km']=ry
        v['horizontal_km']=np.hypot(e.x_km.to_numpy()-rx,e.y_km.to_numpy()-ry)
        v['depth_difference_km']=np.where(m.catalog.eq('Shelly'),e.depth_km.to_numpy()-m.reference_depth_km,np.nan)
        vectors.append(v)
        for cat,q in v.groupby('catalog'):
            summary.append(dict(branch=branch,catalog=cat,n=len(q),median_horizontal_km=q.horizontal_km.median(),median_abs_depth_km=q.depth_difference_km.abs().median(),median_signed_depth_km=q.depth_difference_km.median()))
    vectors = pd.concat(vectors,ignore_index=True); summary = pd.DataFrame(summary); metrics = pd.DataFrame(metrics)
    b = events[events.branch.eq('hk')].set_index('event_id').loc[a.index]
    paired = pd.DataFrame(dict(event_id=a.index,control_depth_km=a.depth_km,hk_depth_km=b.depth_km,depth_shift_km=b.depth_km-a.depth_km,horizontal_shift_km=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km),control_rms_s=a.rms_unweighted_s,hk_rms_s=b.rms_unweighted_s))
    mt = metrics.set_index('branch'); hr = hm.pivot(index='phase',columns='branch',values='rms_s')
    rr = summary.pivot(index='catalog',columns='branch',values='median_horizontal_km')
    dr = summary[summary.catalog.eq('Shelly')].set_index('branch').median_abs_depth_km
    ratios = (rr.hk/rr.control).to_dict(); ratios['Shelly_depth'] = float(dr.hk/dr.control)
    gates = dict(execution=True,retention=bool(all(mt.loc[y,'located']>=mt.loc[x,'located'] for x,y in [('control','hk'),('withheld_control','withheld_hk')])),boundaries=bool(mt.loc['hk','boundary']<=mt.loc['control','boundary']+3),uncertainty=bool(mt.loc['hk','p90_sigma_depth_km']<=1.10*mt.loc['control','p90_sigma_depth_km']),heldout=bool(hr.loc['all','withheld_hk']<=.95*hr.loc['all','withheld_control'] and all(hr.loc[p,'withheld_hk']<=1.05*hr.loc[p,'withheld_control'] for p in ['P','S'])),reference=bool(all(v<=1.10 for v in ratios.values())))
    result = dict(decision='eligible_for_fresh_cohort_validation' if all(gates.values()) else 'do_not_promote',gates=gates,reference_ratios=ratios,heldout_rms_ratio=float(hr.loc['all','withheld_hk']/hr.loc['all','withheld_control']),median_depth_shift_km=float(paired.depth_shift_km.median()),median_horizontal_shift_km=float(paired.horizontal_shift_km.median()),checks=dict(parsed=588,control_xyz_error_km=xyz_error,control_origin_error_s=origin_error,max_tt_equation_error_s=max(errors)))
    for name,df in dict(events=events,fit_phases=fits,metrics=metrics,heldout_predictions=held_rows,heldout_metrics=hm,reference_pairs=vectors,reference_summary=summary,paired_events=paired).items():
        df.to_csv(OUT/f'tables/{name}.csv',index=False)
    write_json(OUT/'run.json',result)
    plot(events, paired, vectors, held_rows)
    print(json.dumps(result,indent=2),flush=True)
    print(metrics.to_string(index=False),flush=True); print(hm.to_string(index=False),flush=True); print(summary.to_string(index=False),flush=True)
    table = lambda df: df.to_string(index=False,float_format=lambda v:f'{v:.4f}')
    (OUT/'README.md').write_text(f'''# Controlled HK velocity-profile experiment

**Decision: {result['decision']}.** Completed 588 native NonLinLoc fits on 147 previously examined transfer events. This is a local model experiment, not a new full catalog or a reproduction of SCSN. The full provisional v1 remains at ../10_validate_catalog/.

## Physical intervention and fixed convention

Replace the archived linear Shelly-derived profile with the four constant HK layers in [Hutton et al. (2010), Table 5](https://scedc.caltech.edu/about/BSSA_2010_Hutton_SCSN_cat.pdf): layer tops 0, 5.5, 16, 32 km; Vp 5.5, 6.3, 6.7, 7.8 km/s; Vs=Vp/1.73. Extend the first layer upward to grid top -3 km without a gradient. Generated slow-length grid values are checked against these velocities.

Both models explicitly use the existing +0.7 km ASL plane as zero depth. Receivers retain elevation and burial, and sea-level depth equals reported depth minus 0.7 km. This is a declared common-datum experiment, not an assertion that the original HK author implementation used this plane. It compares complete profiles (including their interpolation), not an isolated layer-velocity coefficient. No datum offset was fitted. The earlier [qualification note](INPUT_MODEL_NOTES.md) is input documentation, not a completed optimization step.

The 5,413 original picks, associations, input order, pick/model errors, search bounds, seed and station coordinates are unchanged. No station corrections, repicking, hypoDD, model calibration or parameter scan. Design and source identities were frozen before new results in design.json. All 147 control locations and origins reproduce archived baseline within 0.001 km / 0.001 s; independent travel-time interpolation checks every fitted arrival. Maximum timing-equation/prediction discrepancy: {max(errors):.7f} s.

## Locations and uncertainty

```text
{table(metrics)}
```

Median paired HK-minus-control depth shift: {result['median_depth_shift_km']:.3f} km. Median horizontal movement: {result['median_horizontal_shift_km']:.3f} km. Posterior uncertainty is conditional on the selected velocity model and is not total location accuracy.

## Withheld prediction

Both auxiliary fits exclude the same six instruments: {', '.join(held)}. Evaluate all 923 omitted arrivals at each auxiliary solution and fitted origin, with no residual recentering. These observations do not enter either auxiliary location fit. This cohort has already informed earlier diagnostics and is not blind validation.

```text
{table(hm)}
```

## Frozen reference pairs

Keep previous identity matches and ambiguity exclusions; no rematching or coordinate alignment to improve agreement. Horizontal comparisons use common LOCATED events. Shelly depth differences retain the existing nominal alignment convention; the historical datum uncertainty remains. Reference differences do not establish true errors, and other reference depth metrics are intentionally absent.

```text
{table(summary)}
```

## Predeclared decision

```text
{table(pd.DataFrame([dict(gate=k,passed=v) for k,v in gates.items()]))}
```

Only a pass on every gate permits fresh-cohort validation; it does not authorize adoption. A failure closes this fixed trial without adjusting model, datum, station corrections or thresholds on this cohort. Do not promote a model solely because fit residuals decrease. Neither mainshock uncertainties nor the full v1 catalog are changed.

## Reproduction and outputs

Run in seismoagent from the expert root: `python -u 03_experiments/04_velocity_model/20_test_hk_model.py --stage all --workers 8`. `--stage report` only regenerates the report from completed solutions. Exact source identities and native output hashes guard resumption.

- tables/: all solutions, fitted and withheld predictions, fixed reference pairs, summary metrics and paired shifts.
- figures/: paired diagnostics and common-event maps/sections (PNG/PDF).
- hk_grids/: constant-layer controls, velocity and station travel-time grids, generator logs.
- native/: exact input observations, controls, per-event logs and native solutions.
- run.json: decision, gates and numerical implementation checks.
''')


def plot(events,paired,vectors,held):
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    colors={'control':'#2878B5','hk':'#D65F24'}
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.6),layout='constrained')
    ax=axes[0,0];limit=max(paired.control_rms_s.max(),paired.hk_rms_s.max())*1.05
    ax.scatter(paired.control_rms_s,paired.hk_rms_s,s=9,c=colors['hk'],alpha=.7,rasterized=True)
    ax.plot([0,limit],[0,limit],color='k',lw=.7);ax.set(xlabel='Baseline event RMS (s)',ylabel='HK event RMS (s)',xlim=(0,limit),ylim=(0,limit))
    ax=axes[0,1]
    ax.scatter(paired.control_depth_km,paired.hk_depth_km,s=9,c=colors['hk'],alpha=.7,rasterized=True)
    lim=max(paired.control_depth_km.max(),paired.hk_depth_km.max())+1
    ax.plot([0,lim],[0,lim],color='k',lw=.7);ax.set(xlabel='Baseline depth (km)',ylabel='HK depth (km)',xlim=(0,lim),ylim=(0,lim))
    ax=axes[1,0]
    for name,col in colors.items():
        vals=np.sort(np.abs(held.loc[held.branch.eq('withheld_'+name),'residual_s']))
        ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),color=col,label=('HK' if name == 'hk' else 'Baseline'))
    ax.set(xlabel='Withheld absolute residual (s)',ylabel='Cumulative fraction',xlim=(0,2));ax.legend(frameon=False)
    ax=axes[1,1]
    for name,col in colors.items():
        vals=np.sort(vectors.loc[vectors.branch.eq(name)&vectors.catalog.eq('Shelly'),'depth_difference_km'].abs())
        ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),color=col,label=('HK' if name == 'hk' else 'Baseline'))
    ax.set(xlabel='Absolute depth difference to Shelly (km)',ylabel='Cumulative fraction');ax.legend(frameon=False)
    for label,ax in zip('abcd',axes.flat):ax.set_title(label,loc='left',fontweight='bold')
    for ext in ['png','pdf']:fig.savefig(folder/f'01_paired_diagnostics.{ext}',dpi=240)
    plt.close(fig)
    sh=vectors[vectors.catalog.eq('Shelly')&vectors.branch.eq('control')]
    sources=[]
    for name in ['control','hk']:
        q=events[events.branch.eq(name)].set_index('event_id').loc[sh.event_id]
        sources.append((('HK' if name == 'hk' else 'Baseline'),q.x_km.to_numpy(),q.y_km.to_numpy(),q.depth_km.to_numpy()))
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['all','report'],default='all'); ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args()
    if args.workers<1: ap.error('workers must be positive')
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare()
        if args.stage=='all': run(data,args.workers)
        report(data)


if __name__=='__main__': main()
