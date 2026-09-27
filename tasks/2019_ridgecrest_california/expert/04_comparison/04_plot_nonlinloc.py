#!/usr/bin/env python3
"""Check fixed associations and plot the complete NonLinLoc/GaMMA comparison."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
BLUE, ORANGE = '#0072B2', '#D55E00'


def validate_numerics(root):
    """Check receiver depths, vertical times and a noiseless location round trip."""
    import importlib.util
    import json
    from pyproj import Proj
    from scipy.interpolate import RegularGridInterpolator
    spec = importlib.util.spec_from_file_location('nll_stage', HERE / '01_pipeline/04_locate_nonlinloc.py')
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    info = json.loads((root / 'inputs.json').read_text())
    model = info['association_inputs']['model_source']['rows']
    settings = info['association_inputs']['settings']
    stations = pd.read_csv(root / 'stations.csv')
    aliases = dict(zip(stations.id, stations.nll_station))
    proj = Proj(proj='aeqd', lon_0=settings['projection_center'][0],
                lat_0=settings['projection_center'][1], datum='WGS84', units='km')
    origin = pd.Timestamp('2019-07-05T12:00:00Z')
    event = dict(event_id='synthetic_validation', origin_time=origin.isoformat(),
                 x_km=5., y_km=5., depth_km=8., rms_residual_s=0.)
    observations, errors = [], []
    for phase in ['P', 'S']:
        for st in stations.to_dict('records'):
            path = root / 'grids' / f'time.{phase}.{st["nll_station"]}.time.buf'
            header = path.with_suffix('.hdr').read_text().splitlines()
            fields = header[0].split()
            ny, nz = int(fields[1]), int(fields[2])
            dy, dz, z0 = float(fields[7]), float(fields[8]), float(fields[5])
            # Grid2Time retains two sheets on disk; TIME2D reads the first.
            data = np.fromfile(path, dtype=np.float32).reshape(-1, ny, nz)[0]
            assert np.isfinite(data).all() and data.min() >= 0
            assert abs(float(header[1].split()[3]) - st['z(km)']) < 1e-5
            zaxis = z0 + np.arange(nz)*dz
            for depth in [2, 5, 10, 20, 25]:
                z = np.linspace(st['z(km)'], depth, 10001)
                v = np.interp(z, [r['top_of_layer_km'] for r in model],
                              [r['vp_km_s' if phase=='P' else 'vs_km_s'] for r in model])
                errors.append(abs(np.interp(depth, zaxis, data[0]) - np.trapz(1/v, z)))
            interpolator = RegularGridInterpolator((np.arange(ny)*dy, zaxis), data)
            distance = np.hypot(event['x_km']-st['x(km)'], event['y_km']-st['y(km)'])
            tt = float(interpolator([[distance, event['depth_km']]])[0])
            observations.append(dict(pick_id=f'synthetic_{st["nll_station"]}_{phase}',
                                     instrument_id=st['id'], station_id=st['station_id'], phase=phase,
                                     time_utc=(origin+pd.Timedelta(seconds=tt)).isoformat(), residual_s=0.))
    assert max(errors) < .003
    template = root / 'events_raw/gamma_0008401/control.in'
    common = template.read_text().split('LOCFILES ')[0]
    row, picks = stage.locate(event, observations, aliases, common, root, info['config'], proj)
    assert row['status']=='LOCATED' and len(picks)==74
    assert row['horizontal_shift_km'] < .3 and abs(row['depth_shift_km']) < .3
    assert abs(row['origin_time_shift_s']) < .05
    report = dict(vertical_max_error_s=float(max(errors)),
                  checked_station_phase_grids=74, synthetic_used_picks=len(picks),
                  synthetic_horizontal_error_km=float(row['horizontal_shift_km']),
                  synthetic_depth_error_km=float(row['depth_shift_km']),
                  synthetic_origin_error_s=float(row['origin_time_shift_s']))
    (root / 'numerical_checks.yaml').write_text(yaml.safe_dump(report, sort_keys=False))
    return report


def main():
    root = HERE / 'export/04_locate_nonlinloc'
    gamma = HERE / 'export/03_associate_gamma/full'
    validate_numerics(root)
    e = pd.read_csv(root / 'full/events.csv', keep_default_na=False)
    p = pd.read_csv(root / 'full/picks.csv')
    g = pd.read_csv(gamma / 'events.csv')
    gp = pd.read_csv(gamma / 'picks.csv', keep_default_na=False)
    gp = gp[gp.association_status.eq('associated')]
    assert e.event_id.is_unique and p.pick_id.is_unique
    assert set(e.event_id) == set(g.event_id)
    assert set(p.pick_id) == set(gp.pick_id)
    paired = p.merge(gp, on='pick_id', suffixes=('_nll', '_gamma'), validate='one_to_one')
    for key in ['event_id', 'instrument_id', 'phase']:
        assert paired[key + '_nll'].eq(paired[key + '_gamma']).all()
    assert e.depth_km.between(0, 25).all()
    assert np.isfinite(e[['longitude', 'latitude', 'depth_km', 'rms_residual_s',
                         'posterior_sigma_depth_km']]).all().all()
    assert p.weight.gt(0).all()
    counts = p.groupby('event_id').size().reindex(e.event_id).to_numpy()
    assert np.array_equal(counts, e.n_phases.to_numpy())
    unweighted = p.groupby('event_id').residual_s.apply(lambda a: np.sqrt(np.mean(a*a)))
    assert np.allclose(unweighted.reindex(e.event_id), e.rms_unweighted_s)
    comparison = e.merge(g[['event_id', 'longitude', 'latitude']], on='event_id', suffixes=('', '_gamma'))
    report = dict(events=len(e), unchanged_associated_picks=len(p),
                  located=int(e.status.eq('LOCATED').sum()), rejected=int(e.status.ne('LOCATED').sum()),
                  gamma_shallow_bound=int((e.gamma_depth_km < .5).sum()),
                  nll_shallow_bound=int((e.depth_km < .5).sum()),
                  gamma_deep_bound=int((e.gamma_depth_km > 24.5).sum()),
                  nll_deep_bound=int((e.depth_km > 24.5).sum()),
                  median_gamma_unweighted_rms_s=float(e.gamma_rms_unweighted_s.median()),
                  median_nll_unweighted_rms_s=float(e.rms_unweighted_s.median()),
                  median_horizontal_shift_km=float(e.horizontal_shift_km.median()),
                  p95_horizontal_shift_km=float(e.horizontal_shift_km.quantile(.95)),
                  median_absolute_depth_shift_km=float(e.depth_shift_km.abs().median()),
                  median_conditional_depth_sigma_km=float(e.posterior_sigma_depth_km.median()))
    (root / 'full/comparison.yaml').write_text(yaml.safe_dump(report, sort_keys=False))
    out = root / 'full/figures'
    out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.titlesize': 9,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.linewidth': .7, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.3), layout='constrained')
    for ax, letter in zip(axes.flat, 'abcdef'):
        ax.text(-.11, 1.03, letter, transform=ax.transAxes, weight='bold', fontsize=11)
    for ax, lon, lat, title in [(axes[0, 0], 'longitude_gamma', 'latitude_gamma', 'GaMMA'),
                                (axes[0, 1], 'longitude', 'latitude', 'NonLinLoc')]:
        sc = ax.scatter(comparison[lon], comparison[lat], c=e.depth_km if title=='NonLinLoc' else e.gamma_depth_km,
                        cmap='viridis', vmin=0, vmax=25, s=2, linewidths=0, rasterized=True)
        if title == 'NonLinLoc':
            rejected = comparison.status.ne('LOCATED')
            ax.scatter(comparison.loc[rejected, lon], comparison.loc[rejected, lat],
                       marker='x', c=ORANGE, s=10, linewidths=.6, label='Rejected')
            ax.legend(frameon=True, facecolor='white', edgecolor='none', framealpha=.95, loc='lower left', fontsize=7)
        ax.set(xlim=(-118.2, -116.9), ylim=(35.15, 36.35), xlabel='Longitude (°)', ylabel='Latitude (°)', title=title)
        ax.set_aspect(1 / np.cos(np.deg2rad(35.75)))
        ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    fig.colorbar(sc, ax=axes[0, :2], label='Depth (km)', fraction=.03, pad=.02)
    ax = axes[0, 2]
    ax.scatter(e.gamma_depth_km, e.depth_km, s=2, c=BLUE, alpha=.3, linewidths=0, rasterized=True)
    ax.plot([0, 25], [0, 25], 'k--', lw=.7)
    ax.set(xlabel='GaMMA depth (km)', ylabel='NonLinLoc depth (km)', xlim=(0,25), ylim=(0,25))
    ax = axes[1, 0]
    ax.hist([e.gamma_depth_km, e.depth_km], bins=np.arange(0,25.5,.5), histtype='step',
            color=[ORANGE, BLUE], label=['GaMMA', 'NonLinLoc'])
    ax.set(xlabel='Depth (km)', ylabel='Events'); ax.legend(frameon=False)
    ax = axes[1, 1]
    limit = max(e.rms_unweighted_s.max(), e.gamma_rms_unweighted_s.max()) * 1.03
    ax.scatter(e.gamma_rms_unweighted_s, e.rms_unweighted_s, s=2, c=BLUE, alpha=.3, linewidths=0, rasterized=True)
    ax.plot([0,limit], [0,limit], 'k--', lw=.7)
    ax.set(xlabel='GaMMA unweighted RMS (s)', ylabel='NonLinLoc unweighted RMS (s)', xlim=(0,limit), ylim=(0,limit))
    ax = axes[1, 2]
    ax.scatter(e.depth_km, e.posterior_sigma_depth_km, s=2, c=BLUE, alpha=.3, linewidths=0, rasterized=True)
    ax.set(xlabel='NonLinLoc depth (km)', ylabel='Conditional depth SD (km)', xlim=(0,25))
    fig.savefig(out/'01_location_comparison.png', dpi=240)
    fig.savefig(out/'01_location_comparison.pdf', dpi=300)
    plt.close(fig)
    (out/'README.md').write_text('''# Location comparison

All events are shown; no quality subset or reference catalog is selected. Panels a–b show the two location catalogs with the same depth/color and geographic axes; crosses in b mark NonLinLoc-rejected boundary solutions. Panel c compares paired depths; d shows depth distributions; e compares event RMS computed without weights on exactly the same arrivals; f shows NonLinLoc conditional posterior depth standard deviations.

Depth zero is the adopted plane 0.7 km above sea level. The 0–25 km search is bounded: near-boundary depths and posterior dispersions are truncated. Posterior dispersion assumes the fixed model and configured errors; it is not calibrated absolute accuracy. GaMMA and NonLinLoc use different travel-time/elevation implementations, weights and search methods. The fixed pick groups were selected by GaMMA, so residual comparisons are conditional on its association decisions. Location shifts or lower residuals alone do not establish better accuracy. See ../comparison.yaml for whole-catalog counts and statistics, including any NonLinLoc rejection statuses.
''')
    print(yaml.safe_dump(report, sort_keys=False))


if __name__ == '__main__':
    main()
