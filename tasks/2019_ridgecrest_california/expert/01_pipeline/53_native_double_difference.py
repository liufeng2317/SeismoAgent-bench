#!/usr/bin/env python3
"""Fixed full-cohort native hypoDD comparison; never replace the stage 52 product."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'export/06_full_catalog/52_full_catalog'
OUT = ROOT / 'export/06_full_catalog/53_native_double_difference'
HIST = ROOT / 'export/03_location_experiments/01_relative_location'
LABELS = {'nll_baseline': 'NLL baseline (ours)',
          'joint_dd_candidate': 'Joint DD candidate (ours)',
          'hypodd_ct': 'hypoDD CT (ours)', 'hypodd_cc': 'hypoDD CT+CC (ours)'}
COLORS = {'nll_baseline':'#777777', 'joint_dd_candidate':'#0072B2',
          'hypodd_ct':'#E69F00', 'hypodd_cc':'#009E73'}
PROJ = Transformer.from_crs(4326, CRS.from_proj4(
    '+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'), always_xy=True)


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'design.json').exists():
        design = json.loads((OUT / 'design.json').read_text())
        for name, digest in design['input_sha256'].items():
            assert sha(Path(name)) == digest, name
        print('Prepared inputs verified; reuse unchanged design.', flush=True)
        return
    e = pd.read_csv(SRC / 'inputs/events.csv').sort_values('event_id').reset_index(drop=True)
    assert len(e) == 6520 and e.event_id.is_unique
    e['native_id'] = np.arange(1, len(e) + 1)
    times = pd.to_datetime(e.origin_time, utc=True, format='ISO8601').dt.round('10ms')
    e['native_origin'] = times.astype(str)
    e['native_origin_rounding_s'] = (times - pd.to_datetime(e.origin_time, utc=True, format='ISO8601')).dt.total_seconds()
    e.to_csv(OUT / 'input_events.csv', index=False)
    picks = pd.read_csv(SRC / 'inputs/all_phases.csv', low_memory=False).set_index('pick_id')
    usage = pd.read_csv(SRC / 'observation_usage.csv').set_index('pick_id')
    assert picks.index.is_unique and usage.index.is_unique
    stpath = ROOT / 'export/45_added_station/base/stations.csv'
    stations = pd.read_csv(stpath).set_index('id')
    edges = pd.read_csv(SRC / 'inputs/differential_times.csv')
    cc = pd.read_csv(SRC / 'cc_measurements.csv')
    cc = cc[cc.accepted].copy()
    # Relative-only EQ S picks must never become catalog absolute-arrival picks.
    keep = edges.pick_id_a.map(usage.absolute_used).fillna(False) & edges.pick_id_b.map(usage.absolute_used).fillna(False)
    ct = edges[keep].copy()
    assert ct.event_id_a.isin(e.event_id).all() and ct.event_id_b.isin(e.event_id).all()
    assert cc.event_id_a.isin(e.event_id).all() and cc.event_id_b.isin(e.event_id).all()
    for frame in [ct, cc]:
        a, b = picks.loc[frame.pick_id_a], picks.loc[frame.pick_id_b]
        assert np.array_equal(a.event_id.to_numpy(), frame.event_id_a.to_numpy())
        assert np.array_equal(b.event_id.to_numpy(), frame.event_id_b.to_numpy())
        assert np.array_equal(a.instrument_id.to_numpy(), frame.instrument_id.to_numpy())
        assert np.array_equal(b.instrument_id.to_numpy(), frame.instrument_id.to_numpy())
        assert np.array_equal(a.phase.to_numpy(), frame.phase.to_numpy())
        assert np.array_equal(b.phase.to_numpy(), frame.phase.to_numpy())
        assert frame.instrument_id.isin(stations.index).all()
    idx = e.set_index('event_id')
    origin = pd.to_datetime(idx.native_origin, utc=True, format='ISO8601').astype('int64') / 1e9
    picktime = pd.to_datetime(picks.time_utc, utc=True, format='ISO8601').astype('int64') / 1e9
    travel = picktime - picks.event_id.map(origin)
    inputs = OUT / 'inputs'; inputs.mkdir(exist_ok=True)
    with (inputs / 'event.dat').open('w') as f:
        for row, t in zip(e.itertuples(), times):
            stamp = t.strftime('%H%M%S') + f'{t.microsecond // 10000:02d}'
            f.write(f'{t:%Y%m%d} {stamp} {row.latitude:.7f} {row.longitude:.7f} {row.depth_km:.5f} 0 0 0 0 {row.native_id}\n')
    with (inputs / 'station.dat').open('w') as f:
        for r in stations.itertuples():
            f.write(f'{r.nll_station} {r.latitude:.7f} {r.longitude:.7f}\n')
    # OTC=0: CC input is the travel-time difference, NOT the raw waveform lag.
    for frame, filename in [(ct, 'dt.ct'), (cc, 'dt.cc')]:
        with (inputs / filename).open('w') as f:
            for (a, b), g in frame.groupby(['event_id_a', 'event_id_b'], sort=True):
                f.write(f'# {idx.loc[a,"native_id"]} {idx.loc[b,"native_id"]}' + (' 0\n' if filename == 'dt.cc' else '\n'))
                names = g.instrument_id.map(stations.nll_station)
                if filename == 'dt.ct':
                    ta, tb = g.pick_id_a.map(travel), g.pick_id_b.map(travel)
                    assert np.isfinite(ta).all() and np.isfinite(tb).all()
                    f.writelines(f'{s} {x:.6f} {y:.6f} 1 {p}\n' for s, x, y, p in zip(names, ta, tb, g.phase))
                else:
                    dt = g.cc_arrival_difference_s - (origin[a] - origin[b])
                    assert np.isfinite(dt).all() and g.cc.between(.75, 1.000001).all()
                    f.writelines(f'{s} {d:.6f} {q*q:.6f} {p}\n' for s, d, q, p in zip(names, dt, g.cc, g.phase))
        print(f'Wrote {filename}: {len(frame):,} observations', flush=True)
    audit = {'events': len(e), 'ct_rows': len(ct), 'cc_rows': len(cc),
             'excluded_relative_only_ct_rows': int((~keep).sum()),
             'ct_supported_events': len(set(ct.event_id_a) | set(ct.event_id_b)),
             'cc_supported_events': len(set(cc.event_id_a) | set(cc.event_id_b)),
             'max_origin_rounding_s': float(e.native_origin_rounding_s.abs().max()),
             'cc_convention': 'dt.cc = CC absolute arrival difference - rounded input origin difference; OTC=0',
             'scope': 'All 6520 working IDs; all stations. No held-out accuracy claim; no new picking, CC measurement, pair selection or tuning.',
             'initial_locations': 'Original NLL, not the stage 52 joint solution.',
             'native_model': 'Historical constant Shelly layers; Vp/Vs=1.73; station elevation omitted; nominal +0.7 km datum. Different from joint linear interpolation and receiver elevations.',
             'controls': {'hypodd_ct': 'cc0_d1', 'hypodd_cc': 'cc3_d1'}}
    paths = [SRC / 'inputs/events.csv', SRC / 'inputs/all_phases.csv', SRC / 'inputs/differential_times.csv',
             SRC / 'cc_measurements.csv', SRC / 'observation_usage.csv', stpath]
    paths += sorted(inputs.iterdir())
    paths += [HIST / '14_tune_hypodd/runs' / c / 'hypoDD.inp' for c in audit['controls'].values()]
    audit['input_sha256'] = {str(p): sha(p) for p in paths}
    save(OUT / 'design.json', audit)


def build():
    design = json.loads((OUT / 'design.json').read_text())
    dest = OUT / 'native'
    for part in ['include', 'src/hypoDD']:
        shutil.copytree(HIST / '13_hypodd_cc_pilot/native' / part, dest / part, dirs_exist_ok=True)
    capacity = design['ct_rows'] + design['cc_rows'] + 1000
    (dest / 'include/hypoDD.inc').write_text(
        '      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,\n'
        '     & MAXDATA0, MAXCL\n'
        f'      parameter(MAXEVE=7000, MAXLAY=15, MAXDATA={capacity},\n'
        '     & MAXSTA=100, MAXEVE0=2, MAXDATA0=1, MAXCL=7000)\n')
    cwd = dest / 'src/hypoDD'
    with (dest / 'build.log').open('w') as log:
        subprocess.run(['make', 'clean'], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(['make', '-j4', 'FC=gfortran',
                        'FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch'],
                       cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
    save(dest / 'build.json', {'max_events': 7000, 'max_data': capacity,
                              'scientific_changes': 'None; array capacities only.',
                              'binary_sha256': sha(cwd / 'hypoDD')})
    return cwd / 'hypoDD'


def locate(branch_selection='both'):
    binary = OUT / 'native/src/hypoDD/hypoDD'
    build_record = OUT / 'native/build.json'
    if not (binary.exists() and build_record.exists()):
        binary = build()
    else:
        assert sha(binary) == json.loads(build_record.read_text())['binary_sha256']
    def run_branch(job):
        branch, config = job
        run = OUT / branch; run.mkdir(exist_ok=True)
        for name in ['event.dat', 'station.dat', 'dt.ct', 'dt.cc']:
            p = run / name
            if not p.exists(): p.symlink_to(Path('../inputs') / name)
        control = HIST / '14_tune_hypodd/runs' / config / 'hypoDD.inp'
        shutil.copy2(control, run / 'hypoDD.inp')
        print(f'Starting {branch}; native progress: {run / "console.log"}', flush=True)
        with (run / 'console.log').open('w') as log:
            subprocess.run([str(binary), 'hypoDD.inp'], cwd=run, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=3600)
        assert (run / 'hypoDD.reloc').stat().st_size > 0
        print(f'Finished {branch}', flush=True)
    jobs = [('hypodd_ct','cc0_d1'),('hypodd_cc','cc3_d1')]
    if branch_selection != 'both':
        jobs = [job for job in jobs if job[0] == branch_selection]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(run_branch, jobs))


def report():
    events = pd.read_csv(OUT / 'input_events.csv')
    columns = ['native_id','latitude','longitude','depth_km','x_m','y_m','z_m','ex_m','ey_m','ez_m',
               'year','month','day','hour','minute','second','magnitude_placeholder','nccp','nccs','nctp','ncts','rmscc','rmsct','cluster']
    products = {'nll_baseline': events.set_index('event_id'),
                'joint_dd_candidate': pd.read_csv(SRC / 'working_catalog.csv').set_index('event_id')}
    cohort = events[['event_id', 'native_id']].set_index('event_id')
    for branch in ['hypodd_ct', 'hypodd_cc']:
        assert (OUT / branch / 'hypoDD.reloc.001.012').is_file(), 'Twelve configured iterations have not completed'
        assert 'writing out results' in (OUT / branch / 'console.log').read_text(errors='replace')
        f = pd.read_csv(OUT / branch / 'hypoDD.reloc', sep=r'\s+', header=None, names=columns)
        last = pd.read_csv(OUT / branch / 'hypoDD.reloc.001.012', sep=r'\s+', header=None)
        assert set(last[0]) == set(f.native_id), 'Final export is incomplete'
        assert f.native_id.is_unique
        assert np.isfinite(f[['latitude','longitude','depth_km']].to_numpy()).all()
        if branch == 'hypodd_cc':
            assert (f.nccp + f.nccs).gt(0).any(), 'Native CC was not used'
        f['origin_time'] = [(pd.Timestamp(year=int(r.year), month=int(r.month), day=int(r.day),
            hour=int(r.hour), minute=int(r.minute), tz='UTC') + pd.Timedelta(seconds=r.second)).isoformat() for r in f.itertuples()]
        f = f.merge(events[['native_id', 'event_id']], on='native_id', validate='one_to_one').set_index('event_id')
        f['x_km'], f['y_km'] = PROJ.transform(f.longitude.to_numpy(), f.latitude.to_numpy())
        f['depth_below_sea_level_km'] = f.depth_km - .7
        f['working_depth_range_flag'] = f.depth_km.lt(.5) | f.depth_km.gt(24.5)
        f['catalog_id'] = branch
        f['location_status'] = 'native_relocated'
        # No placeholder magnitude or inherited NLL posterior is presented as a new measurement.
        f.drop(columns=['magnitude_placeholder']).rename(columns={
            'x_m':'native_local_x_m', 'y_m':'native_local_y_m', 'z_m':'native_local_z_m',
            'ex_m':'native_formal_ex_m', 'ey_m':'native_formal_ey_m', 'ez_m':'native_formal_ez_m',
            'rmscc':'cc_rms_s', 'rmsct':'ct_rms_s', 'cluster':'native_cluster'
        }).to_csv(OUT / branch / 'catalog.csv')
        products[branch] = f
        cohort[branch + '_retained'] = cohort.index.isin(f.index)
        loaded = pd.read_csv(OUT / branch / 'hypoDD.loc', sep=r'\s+', header=None, usecols=[0])[0]
        cohort[branch + '_loaded_by_native'] = cohort.native_id.isin(loaded)
        negatives = set(map(int, re.findall(r'negative depth -\s+(\d+)', (OUT / branch / 'hypoDD.log').read_text(errors='replace'))))
        cohort[branch + '_negative_depth_rejection'] = cohort.native_id.isin(negatives)
        cohort[branch + '_status'] = np.select(
            [cohort[branch + '_retained'], cohort[branch + '_negative_depth_rejection'],
             ~cohort[branch + '_loaded_by_native']],
            ['relocated', 'negative_depth_rejection', 'no_loaded_differential_data'],
            default='other_native_exclusion')
    common = sorted(set.intersection(*(set(f.index) for f in products.values())))
    cohort['common_four_catalogs'] = cohort.index.isin(common)
    cohort.to_csv(OUT / 'event_membership.csv')
    reference = pd.read_csv(SRC / 'reference_comparison.csv')
    reference = reference[reference.branch.eq('original_nll')].copy()
    assert not reference.duplicated(['event_id','catalog']).any()
    rows = []; comparisons = []
    for scope in ['common_four_catalogs', 'each_retained_catalog']:
        for branch, f in products.items():
            r = reference[reference.event_id.isin(common if scope == 'common_four_catalogs' else f.index)].copy()
            loc = f.loc[r.event_id]
            x, y = PROJ.transform(loc.longitude.to_numpy(), loc.latitude.to_numpy())
            r['horizontal_km'] = np.hypot(x - r.rx.to_numpy(), y - r.ry.to_numpy())
            r['absolute_depth_km'] = np.where(r.depth_comparison_eligible,
                abs(loc.depth_km.to_numpy() - r.reference_depth_km.to_numpy()), np.nan)
            r['absolute_origin_s'] = abs((pd.to_datetime(loc.origin_time.to_numpy(), utc=True, format='ISO8601') -
                pd.to_datetime(r.reference_time.to_numpy(), utc=True, format='ISO8601')).total_seconds())
            r['catalog_id'] = branch; r['scope'] = scope
            comparisons.append(r[['event_id','catalog','reference_id','catalog_id','scope',
                                  'horizontal_km','absolute_depth_km','absolute_origin_s',
                                  'depth_comparison_eligible']])
            for ref, g in r.groupby('catalog'):
                rows.append(dict(scope=scope, catalog_id=branch, reference=ref, n=len(g),
                    horizontal_median_km=g.horizontal_km.median(), horizontal_p90_km=g.horizontal_km.quantile(.9),
                    depth_n=int(g.absolute_depth_km.notna().sum()), depth_median_km=g.absolute_depth_km.median(),
                    origin_median_s=g.absolute_origin_s.median()))
    metrics = pd.DataFrame(rows); metrics.to_csv(OUT / 'reference_metrics.csv', index=False)
    pd.concat(comparisons).to_csv(OUT / 'reference_comparison.csv', index=False)
    figdir = OUT / 'figures'; figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 4, figsize=(14, 7), layout='constrained')
    coords = []
    for branch, f in products.items():
        g = f.loc[common]
        x, y = PROJ.transform(g.longitude.to_numpy(), g.latitude.to_numpy())
        coords.append((x, y, g.depth_km.to_numpy()))
    allxyz = np.concatenate([np.column_stack(v) for v in coords])
    lo, hi = allxyz.min(axis=0)-.5, allxyz.max(axis=0)+.5
    for k, ((branch, f), (x, y, z)) in enumerate(zip(products.items(), coords)):
        axes[0,k].scatter(x,y,s=.8,c='black',alpha=.35,rasterized=True)
        axes[1,k].scatter(x,z,s=.8,c='black',alpha=.35,rasterized=True)
        axes[0,k].set(title=LABELS[branch],xlabel='East (km)',ylabel='North (km)',xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),aspect='equal')
        axes[1,k].set(xlabel='East (km)',ylabel='Depth (km)',xlim=(lo[0],hi[0]),ylim=(hi[2],min(0,lo[2])),aspect='equal')
    for ext in ['png','pdf']: fig.savefig(figdir / ('01_same_event_locations.'+ext),dpi=220)
    plt.close(fig)
    fig, axes = plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    for ax, ref in zip(axes,['Liu','Official','Shelly']):
        r = pd.concat(comparisons); r = r[r.scope.eq('common_four_catalogs') & r.catalog.eq(ref)]
        for branch in products:
            v = np.sort(r.loc[r.catalog_id.eq(branch),'horizontal_km'].to_numpy())
            ax.plot(v,np.arange(1,len(v)+1)/len(v),label=LABELS[branch],color=COLORS[branch])
        ax.set(title='Reference: '+ref,xlabel='Horizontal discrepancy (km)',ylabel='Cumulative fraction',ylim=(0,1))
    axes[0].legend(frameon=False,fontsize=8)
    for ext in ['png','pdf']: fig.savefig(figdir / ('02_reference_discrepancies.'+ext),dpi=220)
    plt.close(fig)
    summary = {'attempted_events': len(events), 'retained_events': {k:len(f) for k,f in products.items()},
               'common_events': len(common), 'working_depth_range_flag_counts': {k:int((f.depth_km.lt(.5)|f.depth_km.gt(24.5)).sum()) for k,f in products.items()},
               'native_membership': {k:cohort[k + '_status'].value_counts().to_dict() for k in ['hypodd_ct','hypodd_cc']},
               'decision': 'Comparison branches only; stage 52 remains the retained candidate. No automatic promotion.'}
    save(OUT / 'summary.json', summary)
    table = metrics[metrics.scope.eq('common_four_catalogs')].drop(columns='scope').to_string(index=False,float_format=lambda v:f'{v:.4f}')
    markdown = ['| Catalog | Reference | Pairs | Median horizontal km | P90 horizontal km | Median absolute depth difference km | Median absolute time difference s |',
                '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in metrics[metrics.scope.eq('common_four_catalogs')].itertuples():
        depth = f'{r.depth_median_km:.3f}' if r.depth_n else '—'
        markdown.append(f'| {LABELS[r.catalog_id]} | {r.reference} | {r.n} | {r.horizontal_median_km:.3f} | {r.horizontal_p90_km:.3f} | {depth} | {r.origin_median_s:.3f} |')
    markdown = '\n'.join(markdown)
    shelly = metrics[metrics.scope.eq('common_four_catalogs') & metrics.reference.eq('Shelly')].set_index('catalog_id')
    (OUT / 'README.md').write_text(f'''# Full-cohort native double-difference comparison

Run `bash 01_pipeline/run_53_native_double_difference.sh` from the expert root.
Individual stages: `python 01_pipeline/53_native_double_difference.py --stage prepare|locate|report`.
The two independent native branches run concurrently (one CPU process each).
The original 6,520 NLL working events initialize both native branches; neither is
a second relocation applied on top of the joint candidate. Stage 52 is preserved.

## Fixed design

Reuse the stage 52 graph and measured CC; no new waveform processing, pair search,
reference rematching or parameter tuning. Catalog differences use only picks marked
`absolute_used`; added relative-only EQ S remains CC-only. All stations are fitted;
these are production-scope comparisons, not a held-out validation experiment.
Exact historical native controls: CT=cc0_d1, CT+CC=cc3_d1; LSQR 4+8 iterations,
damping 80/40, CT P/S=1/0.5, CC P/S=3/1.5 with quality CC squared. Native
negative-depth removal can repeat a configured iteration; logs preserve those extra
internal passes. The 4+8 configured iteration schedule is unchanged. Native constant
Shelly layers and Vp/Vs=1.73 are unchanged. Unlike the joint model, native hypoDD
omits receiver elevation and uses constant layers. Thus NLL/joint versus native
differences include a forward-model change. All nominal depths retain the +0.7 km
datum; native origin times are rounded to 0.01 s. No new absolute anchoring is added.
`design.json` records input counts, checksums and the audited CC time convention.

## Retention and fixed-reference comparison

```json
{json.dumps(summary,indent=2)}
```

All rows below use the same {len(common)} retained IDs, and frozen reference pairs.
Shelly depth eligibility follows the existing stage 52 rule. Reference discrepancy
is not ground-truth error. Per-method retained-population metrics are also saved,
but should not be confused with a paired comparison.

{markdown}

## Interpretation and delivery decision

On the common-event Shelly matches, horizontal medians are
{shelly.loc['joint_dd_candidate','horizontal_median_km']:.3f} km for the joint DD candidate,
{shelly.loc['hypodd_ct','horizontal_median_km']:.3f} km for native CT and
{shelly.loc['hypodd_cc','horizontal_median_km']:.3f} km for native CT+CC. Their nominal
depth medians are {shelly.loc['joint_dd_candidate','depth_median_km']:.3f},
{shelly.loc['hypodd_ct','depth_median_km']:.3f} and
{shelly.loc['hypodd_cc','depth_median_km']:.3f} km; absolute origin-time medians are
{shelly.loc['joint_dd_candidate','origin_median_s']:.3f},
{shelly.loc['hypodd_ct','origin_median_s']:.3f} and
{shelly.loc['hypodd_cc','origin_median_s']:.3f} s, respectively.

Retain the joint DD candidate as the current delivery and both native products as
named comparisons. Adding CC improves the native branch's reference agreement here,
but does not establish a better replacement for the full joint catalog. Its timing
benefit is retained as a separate observation; do not transplant native times into
joint coordinates. Lower retained depth-range flag counts are not evidence of fewer
problems when negative-depth events have already been excluded. Model/elevation
differences and event attrition prevent attributing all differences to the algorithm.

![Same events and axes](figures/01_same_event_locations.png)
![Fixed reference pairs](figures/02_reference_discrepancies.png)

## Products and limits

- `hypodd_ct/catalog.csv`: native catalog-difference relocation, retained events only.
- `hypodd_cc/catalog.csv`: native catalog plus CC relocation, retained events only.
- `event_membership.csv`: all input IDs, retention, negative-depth rejection and common cohort.
- `reference_metrics.csv`, `reference_comparison.csv`: quantitative comparisons, without rematching.
- `inputs/`, `native/`, and branch inputs/logs: exact replay materials and original native outputs.

Missing events are not silently filled with NLL coordinates. Native placeholder
magnitudes are omitted from exported catalogs; magnitudes require separate joining
and retain their earlier geometry caveat. NLL uncertainty columns are not copied
as native uncertainty. `native_formal_*_m` are native formal outputs, not calibrated
total uncertainty. `native_local_*_m` use the native cluster coordinate origin;
`x_km/y_km` use the common AEQD origin. `nccp/nccs/nctp/ncts` count differential
constraint rows, not unique picked arrivals or stations. `cc_rms_s/ct_rms_s` are
native per-event residual summaries in seconds. Completing 12 configured iterations
does not itself establish convergence or accuracy. Existing joint depth/time and
mainshock limitations remain.
`working_depth_range_flag` reuses the baseline thresholds below 0.5 or above 24.5 km;
these are comparison safeguards, not upper/lower bounds imposed on the native solver.
Do not select a winner from image sharpness alone or call these branches ground truth.
''')
    print(json.dumps(summary,indent=2),flush=True)
    print(table,flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['all','prepare','locate','report'],default='all')
    parser.add_argument('--branch',choices=['both','hypodd_ct','hypodd_cc'],default='both',
                        help='Native execution only; default runs the independent branches concurrently.')
    args = parser.parse_args()
    if args.stage in ['all','prepare','locate']: prepare()
    if args.stage in ['all','locate']: locate(args.branch)
    if args.stage in ['all','report']: report()


if __name__ == '__main__':
    main()
