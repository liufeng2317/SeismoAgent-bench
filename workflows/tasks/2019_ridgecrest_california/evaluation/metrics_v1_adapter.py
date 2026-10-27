"""Ridgecrest reference cohorts for metrics v1 (references_loader: adapter).

The case's references are not read by an expert stage-05 module but by the
audited five-source loader of the case data
(``data/2019_ridgecrest_california/scripts/figures/plot_catalog_comparison.py``),
which checks source hashes, the native comparison mask and the per-stage
audit counts.
"""
import importlib.util

import pandas as pd


def load_references(task_dir, config):
    case = task_dir.parents[2] / 'data' / task_dir.name
    spec = importlib.util.spec_from_file_location(
        'ridgecrest_reference_loader', case / 'scripts' / 'figures' / 'plot_catalog_comparison.py')
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    _, _, records, _ = loader.load_data(case)
    return {rec['key']: pd.DataFrame({field: [r[field] for r in rec['rows']]
                                      for field in ('time', 'latitude', 'longitude', 'depth_km', 'magnitude')})
            for rec in records}
