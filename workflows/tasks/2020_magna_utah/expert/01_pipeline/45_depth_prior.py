#!/usr/bin/env python3
"""Stage 45 -- depth prior for weakly constrained NLL locations.

Small events with few picks trade depth for origin time: NLL puts them
shallow and late (r7 known issue in PLAN.md). Their NLL posteriors usually
still carry probability at the sequence depth. For weakly constrained events
(n_phases < min_phases or posterior sigma_z > max_sigma_z_km) the posterior
scatter samples (2000 per event, stage-04 events_raw/<id>/last.scat) are
re-weighted by a Gaussian depth prior and the hypocenter is taken as the
weighted median of the samples; the origin time is shifted by the mean
change of the predicted pick travel times (same layered model, so tracer
bias cancels). The prior comes from this round's own well-constrained events
(no reference catalog): median depth of events with sigma_z <= 1.5 km,
n_phases >= 20, gap < 180, with a deliberately wider sigma. Events whose
re-weighted samples are too few to trust (effective sample size below
min_ess) keep their NLL location and get depth_unresolved = True.

Writes <export_root>/45_depth_prior/{events.csv, report.json}; events.csv has
the stage-04 columns (adjusted where the prior applies) plus nll_* originals
and prior bookkeeping. Stage 05 reads it instead of the raw stage-04 table
when it exists.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pyproj import Proj

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[3] / 'seismotools/match_and_locate/runtime/python/MatchLocatepy'))
from matchlocate_runner.traveltime import LayeredModel, first_arrival  # noqa: E402

CFG = yaml.safe_load((ROOT / '00_config/config.yaml').read_text())
ASSOC = yaml.safe_load((ROOT / '00_config/association.yaml').read_text())
PRIOR = CFG.get('depth_prior', {})
DATUM = float(ASSOC['reference_elevation_km'])
EXPORT = ROOT / CFG['export_root']


def weighted_median(values, weights):
    order = np.argsort(values)
    cum = np.cumsum(weights[order])
    return float(values[order][np.searchsorted(cum, 0.5 * cum[-1])])


def read_scat(path):
    raw = path.read_bytes()
    n = struct.unpack('<i', raw[:4])[0]
    return np.frombuffer(raw[16:16 + 16 * n], '<f4').reshape(n, 4).astype(float)


def main() -> int:
    t0 = time.time()
    min_phases = int(PRIOR.get('min_phases', 20))
    max_sigma = float(PRIOR.get('max_sigma_z_km', 2.0))
    prior_sigma = float(PRIOR.get('prior_sigma_km', 2.0))
    min_ess = float(PRIOR.get('min_ess', 30))
    nll = EXPORT / '04_locate_nonlinloc'
    ev = pd.read_csv(nll / 'full/events.csv')
    located = ev.status.eq('LOCATED')
    good = located & (ev.posterior_sigma_depth_km <= 1.5) & (ev.n_phases >= 20) & (ev.azimuth_gap_deg < 180)
    prior_mean_bsl = float(ev.loc[good, 'depth_below_sea_level_km'].median())
    prior_mean_model = prior_mean_bsl + DATUM

    proj = Proj(proj='aeqd', lon_0=ASSOC['projection_center'][0], lat_0=ASSOC['projection_center'][1],
                datum='WGS84', units='km')
    model = LayeredModel.from_rows(json.loads((EXPORT / '03_associate_gamma/full/inputs.json').read_text())
                                   ['model_source']['rows'])
    stations = pd.read_csv(nll / 'stations.csv').set_index('id')
    picks = pd.read_csv(nll / 'full/picks.csv')
    by_event = {k: g for k, g in picks.groupby('event_id')}

    def mean_tt(eid, x, y, z):
        g = by_event.get(eid)
        if g is None or not len(g):
            return np.nan
        tts = []
        for r in g.itertuples():
            if r.instrument_id not in stations.index:
                continue
            s = stations.loc[r.instrument_id]
            d = math.hypot(s['x(km)'] - x, s['y(km)'] - y)
            tts.append(first_arrival(model, r.phase, d, z, float(s['z(km)'])).travel_time_s)
        return float(np.mean(tts)) if tts else np.nan

    out = ev.copy()
    for col in ('origin_time', 'longitude', 'latitude', 'x_km', 'y_km', 'depth_km', 'depth_below_sea_level_km'):
        out[f'nll_{col}'] = ev[col]
    out['depth_prior_applied'] = False
    out['depth_unresolved'] = False
    out['prior_ess'] = np.nan
    out['prior_depth_shift_km'] = 0.0
    out['prior_origin_shift_s'] = 0.0
    weak = located & ((ev.n_phases < min_phases) | (ev.posterior_sigma_depth_km > max_sigma))
    for i in np.where(weak)[0]:
        r = ev.iloc[i]
        f = nll / 'events_raw' / r.event_id / 'last.scat'
        if not f.is_file():
            out.at[i, 'depth_unresolved'] = True
            continue
        s = read_scat(f)
        w = np.exp(-0.5 * ((s[:, 2] - prior_mean_model) / prior_sigma) ** 2)
        ess = float(w.sum() ** 2 / np.sum(w ** 2)) if w.sum() > 0 else 0.0
        out.at[i, 'prior_ess'] = ess
        if ess < min_ess:
            out.at[i, 'depth_unresolved'] = True
            continue
        x, y, z = (weighted_median(s[:, k], w) for k in range(3))
        dt = mean_tt(r.event_id, r.x_km, r.y_km, r.depth_km) - mean_tt(r.event_id, x, y, z)
        lon, lat = proj(x, y, inverse=True)
        origin = pd.Timestamp(r.origin_time) + pd.Timedelta(seconds=float(dt) if np.isfinite(dt) else 0.0)
        out.loc[i, ['x_km', 'y_km', 'depth_km', 'longitude', 'latitude']] = [x, y, z, lon, lat]
        out.at[i, 'depth_below_sea_level_km'] = z - DATUM
        out.at[i, 'origin_time'] = origin.isoformat()
        out.at[i, 'depth_prior_applied'] = True
        out.at[i, 'prior_depth_shift_km'] = z - r.depth_km
        out.at[i, 'prior_origin_shift_s'] = float(dt) if np.isfinite(dt) else 0.0
    dest = EXPORT / '45_depth_prior'
    dest.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest / 'events.csv', index=False)
    applied = out[out.depth_prior_applied]
    report = {
        'round': CFG['round'], 'events': int(located.sum()), 'weak_events': int(weak.sum()),
        'prior': {'mean_depth_bsl_km': round(prior_mean_bsl, 3), 'sigma_km': prior_sigma,
                  'from_well_constrained_events': int(good.sum()),
                  'weak_definition': f'n_phases < {min_phases} or posterior_sigma_z > {max_sigma} km',
                  'min_ess': min_ess},
        'applied': int(len(applied)), 'unresolved': int(out.depth_unresolved.sum()),
        'depth_shift_km_median': float(applied.prior_depth_shift_km.median()) if len(applied) else None,
        'origin_shift_s_median': float(applied.prior_origin_shift_s.median()) if len(applied) else None,
        'shallow_lt5km_bsl_before': int((ev.loc[located, 'depth_below_sea_level_km'] < 5).sum()),
        'shallow_lt5km_bsl_after': int((out.loc[located & ~out.depth_unresolved, 'depth_below_sea_level_km'] < 5).sum()),
        'seconds': round(time.time() - t0, 1)}
    (dest / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
