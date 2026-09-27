#!/usr/bin/env python3
"""Report the fixed depth experiment; references never enter the fitting step."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Proj
import yaml

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
spec = importlib.util.spec_from_file_location('depth', HERE / '02_diagnostics/06_diagnose_depth.py')
depth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(depth)


def main():
    cfg, bounds, jobs = depth.setup()
    out = depth.OUT
    depth.initialize(depth.NLL / 'grids', cfg, bounds)
    job = next(j for j in jobs if j['event_id'] == 'gamma_0007346')
    problem = depth.Problem(job)
    point = np.array([3.127, 7.389, 4.137])
    step = 1e-5
    numeric = np.array([(problem.evaluate(point + axis * step)[0] -
                         problem.evaluate(point - axis * step)[0]) / (2 * step)
                        for axis in np.eye(3)])
    analytic = problem.evaluate(point)[1]
    assert np.allclose(analytic, numeric, rtol=1e-5, atol=1e-5)
    truth = np.array([5.123, 7.321, 8.137])
    synthetic = dict(job, observed=(problem.travel(truth)[0] - 3).tolist(), role='validation')
    result, _, _ = depth.solve(synthetic)
    error = np.linalg.norm(np.array([result['x_km'], result['y_km'], result['depth_km']]) - truth)
    assert error < .01 and result['refined_rms_s'] < .001
    checks = dict(gradient_max_absolute_difference=float(np.max(np.abs(analytic - numeric))),
                  synthetic_spatial_error_km=float(error),
                  synthetic_origin_error_s=float(result['origin_offset_s'] + 3),
                  synthetic_rms_s=float(result['refined_rms_s']))
    a = pd.read_csv(out / 'linear/picks.csv').sort_values('pick_id')
    b = pd.read_csv(out / 'layered/picks.csv').sort_values('pick_id')
    assert a[['event_id', 'pick_id', 'phase', 'weight']].equals(b[['event_id', 'pick_id', 'phase', 'weight']])
    assert set(a.pick_id) == {p for job in jobs for p in job['pick_ids']}
    checks['unchanged_pick_count'] = len(a)
    (out / 'numerical_checks.yaml').write_text(yaml.safe_dump(checks))
    depth.plot_and_compare()

    review = HERE / 'export/05_review_catalog'
    pairs = pd.read_csv(review / 'reference_matches.csv', dtype={'reference_id': str})
    refs = pd.read_csv(review / 'reference_events.csv', dtype={'reference_id': str})
    pairs = pairs[pairs.matched & ~pairs.ambiguous]
    pairs = pairs[['event_id', 'catalog', 'reference_id']].merge(
        refs, on=['catalog', 'reference_id'], validate='many_to_one')
    projection = Proj(proj='aeqd', lat_0=35.75, lon_0=-117.55, datum='WGS84', units='km')
    pairs['reference_x_km'], pairs['reference_y_km'] = projection(pairs.longitude.values, pairs.latitude.values)
    comparisons = pd.read_csv(out / 'comparison.csv')
    pairs = pairs.merge(comparisons, on='event_id', validate='many_to_one')
    for model in ['linear', 'layered']:
        pairs[f'horizontal_{model}_km'] = np.hypot(pairs[f'x_km_{model}'] - pairs.reference_x_km,
                                                  pairs[f'y_km_{model}'] - pairs.reference_y_km)
        origin = pd.to_datetime(pairs[f'origin_anchor_{model}'], utc=True, format='ISO8601') + pd.to_timedelta(pairs[f'origin_offset_s_{model}'], unit='s')
        pairs[f'dt_{model}_s'] = (origin - pd.to_datetime(pairs.time, utc=True, format='ISO8601')).dt.total_seconds()
        pairs[f'dz_{model}_km'] = (pairs[f'depth_km_{model}'] - pairs.depth_km).where(
            pairs.catalog.eq('Shelly') & pairs.depth_km.between(0, 40))
    keys = ['event_id', 'role', 'stratum', 'catalog', 'reference_id']
    columns = [f'{metric}_{model}_{unit}' for model in ['linear', 'layered']
               for metric, unit in [('horizontal', 'km'), ('dt', 's'), ('dz', 'km')]]
    pairs[keys + columns].to_csv(out / 'reference_comparison.csv', index=False)
    rows = []
    for (role, catalog), part in pairs.groupby(['role', 'catalog']):
        row = dict(role=role, catalog=catalog, n=len(part))
        for column in columns:
            row['median_abs_' + column] = float(part[column].abs().median()) if part[column].notna().any() else np.nan
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(out / 'reference_summary.csv', index=False)
    print(summary.to_string(index=False))
    print(checks)


if __name__ == '__main__':
    main()
