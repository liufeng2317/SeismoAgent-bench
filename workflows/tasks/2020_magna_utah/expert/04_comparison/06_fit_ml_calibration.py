#!/usr/bin/env python3
"""Fit the Utah ML calibration on a completed round's provisional magnitudes.

Anchors accepted station magnitudes of events unambiguously matched to UUSS ML
(the regional standard local-magnitude scale) and fits the residual structure

    station ML(HB87) - UUSS ML  ~  a*log10(r/100 km) + c

The recalibration is the negative of that fit: ml_station(new) =
ml_station(HB87) - a*log10(r/100 km) - c, i.e. the geometric-spreading
coefficient and the constant are adjusted while the HB87 anelastic term
(0.00189/km) is kept. Refitting the anelastic term as well is deliberately
excluded: 95% of anchor measurements are within ~35 km, where log10(r) and r
are collinear, and a free fit produces non-monotonic, unphysical corrections.
Model selection keeps the smallest form whose extra coefficient is significant
(cluster-robust SE, clustered on events, MAD sigma-clipped residuals). Pang
Mc, UUSS MD and the Baker mixed scales are different magnitude scales: they
are reported before/after as independent validation only, never fitted. The
absolute coefficients (A*log10(r) + B*r + C) in fit.yaml go into the
magnitude.ml_calibration block of the next round's config.yaml.
"""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((HERE / '00_config/config.yaml').read_text())
# Stage 09's HB87 code form: 1.11*log10(r/100) + 0.00189*(r-100) + 3.
HB_A, HB_B, HB_C = 1.11, 0.00189, 3. - 1.11 * np.log10(100.) - 0.00189 * 100.

MODELS = {  # name -> column builders on r (km); a constant column is appended last
    'constant': lambda r: [],
    'geometric_spread': lambda r: [np.log10(r / 100.)],
}
PARAMS = {  # fitted coefficient names, in model order, constant last
    'constant': ['c'],
    'geometric_spread': ['a_log10_r100', 'c'],
}

def cluster_ols(X, y, clusters):
    """OLS with cluster-robust (CR0) standard errors."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    for group in np.unique(clusters):
        mask = clusters == group
        score = X[mask].T @ resid[mask]
        meat += np.outer(score, score)
    se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
    return beta, se, resid

def fit_model(name, r, y, clusters, clip_z=3.0, max_iter=10):
    keep = np.ones(len(y), bool)
    beta = se = None
    for _ in range(max_iter):
        beta, se, resid = cluster_ols(np.column_stack(MODELS[name](r) + [np.ones(len(r))])[keep],
                                      y[keep], clusters[keep])
        full_resid = y - np.column_stack(MODELS[name](r) + [np.ones(len(r))]) @ beta
        med = np.median(full_resid[keep])
        mad = 1.4826 * np.median(np.abs(full_resid[keep] - med))
        new = np.abs(full_resid - med) <= clip_z * max(mad, 1e-9)
        if (new == keep).all():
            break
        keep = new
    t = beta / se
    return dict(name=name, beta=dict(zip(PARAMS[name], beta)), se=dict(zip(PARAMS[name], se)),
                t=dict(zip(PARAMS[name], t)), clipped=int((~keep).sum()),
                measurements=int(keep.sum()), events=int(pd.unique(clusters[keep]).size))

def select_model(fits):
    """Smallest form first; add a term only when its |t| >= 2."""
    spread = fits['geometric_spread']
    if abs(spread['t'].get('a_log10_r100', 0.)) >= 2.:
        return 'geometric_spread'
    return 'constant'

def native(obj):
    """PyYAML safe_dump only accepts exact built-in types, not numpy scalars."""
    if isinstance(obj, dict):
        return {str(k): native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [native(v) for v in obj]
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--round', default=CFG['round'], help='round export to fit against')
    ap.add_argument('--anchor-catalog', default='uuss')
    ap.add_argument('--anchor-type', default='ML',
                    help='reference magnitude type to anchor on (default ML)')
    args = ap.parse_args()
    exp = HERE / 'export' / args.round
    out = exp / '06_fit_ml_calibration'
    out.mkdir(parents=True, exist_ok=True)

    station = pd.read_csv(exp / '09_estimate_magnitude/station_magnitudes.csv')
    catalog = pd.read_csv(exp / '09_estimate_magnitude/catalog.csv',
                          usecols=['event_id', 'origin_time', 'ml_provisional', 'magnitude_status'])
    matches = pd.read_csv(exp / '05_match_references/reference_matches.csv')
    provisional = catalog[catalog.magnitude_status.eq('provisional')]

    anchor = matches[matches.catalog.eq(args.anchor_catalog) & matches.matched & ~matches.ambiguous
                     & matches.reference_magnitude.notna()
                     & matches.reference_magnitude_type.str.upper().eq(args.anchor_type.upper())]
    # base: every accepted station measurement behind a provisional event magnitude;
    # the fit anchors on the subset of base that matched the anchor scale.
    base = station[station.accepted & station.ml_station.notna() & station.hypocentral_km.notna()
                   & station.event_id.isin(provisional.event_id)].copy()
    m = base.merge(anchor[['event_id', 'reference_magnitude']], on='event_id')
    if m.event_id.nunique() < 30:
        raise ValueError(f'anchor sample too small: {m.event_id.nunique()} events')
    m['residual'] = m.ml_station - m.reference_magnitude

    r = m.hypocentral_km.to_numpy(float)
    y = m.residual.to_numpy(float)
    clusters = m.event_id.to_numpy()
    fits = {name: fit_model(name, r, y, clusters) for name in MODELS}
    selected = select_model(fits)
    # The fitted structure describes the residual; the correction is its negative.
    delta = {key: -value for key, value in fits[selected]['beta'].items()}

    def correction_delta(distance_km):
        return (delta.get('a_log10_r100', 0.) * np.log10(np.asarray(distance_km, float) / 100.)
                + delta.get('b_r_minus_100_km', 0.) * (np.asarray(distance_km, float) - 100.) + delta['c'])

    # Event-level new magnitudes under the selected correction, per matched scale.
    m['new_correction_delta'] = correction_delta(m.hypocentral_km)
    new_ml = base.assign(station_new_ml=base.ml_station + correction_delta(base.hypocentral_km)) \
                 .groupby('event_id').station_new_ml.median()
    origin = pd.to_datetime(provisional.set_index('event_id').origin_time, format='ISO8601', utc=True)
    t1 = pd.Timestamp(CFG['mainshock']['time_utc'])

    def scale_report():
        rows = []
        pairs = matches[matches.matched & ~matches.ambiguous & matches.reference_magnitude.notna()
                        & matches.event_id.isin(provisional.event_id)]
        provisioned = provisional.set_index('event_id')
        for (cat, typ), group in pairs.groupby(['catalog', 'reference_magnitude_type']):
            if len(group) < 10:
                continue
            before = provisioned.loc[group.event_id, 'ml_provisional'].to_numpy(float)
            after = group.event_id.map(new_ml).to_numpy(float)
            ref = group.reference_magnitude.to_numpy(float)

            def spread(v):
                center = np.nanmedian(v)
                return float(center), float(1.4826 * np.nanmedian(np.abs(v - center)))
            before_median, before_mad = spread(before - ref)
            after_median, after_mad = spread(after - ref)
            rows.append(dict(catalog=cat, magnitude_type=typ, n=int(len(group)),
                             median_before=before_median, mad_before=before_mad,
                             median_after=after_median, mad_after=after_mad))
        return rows

    validation = scale_report()

    # Distance-binned and per-station structure of the anchor residuals after correction.
    bins = [10, 20, 40, 70, 100, 150]
    corrected = m.residual + m.new_correction_delta
    distance_bins = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        sel = (m.hypocentral_km >= lo) & (m.hypocentral_km < hi)
        if sel.sum() < 5:
            continue
        v = corrected[sel]
        distance_bins.append(dict(range_km=[lo, hi], n=int(sel.sum()),
                                  median=float(v.median()), mad=float(1.4826*(v - v.median()).abs().median())))
    station_terms = []
    for instrument, group in m.groupby('instrument_id'):
        v = corrected[group.index]
        station_terms.append(dict(instrument=instrument, n=int(len(group)),
                                  median=float(v.median()), mad=float(1.4826*(v - v.median()).abs().median())))
    station_terms.sort(key=lambda row: row['median'])
    edges = np.array([pd.Timestamp('2000-01-01T00:00:00Z').value, t1.value,
                      (t1 + pd.Timedelta(hours=48)).value, pd.Timestamp('2100-01-01T00:00:00Z').value])
    codes = np.searchsorted(edges, origin.reindex(m.event_id).astype('int64').to_numpy(), side='right') - 1
    period = np.array(['pre_mainshock', 'first_48h', 'later'])[codes]
    periods = [dict(period=str(p), n=int((period == p).sum()),
                    median=float(corrected[period == p].median()))
               for p in ('pre_mainshock', 'first_48h', 'later') if (period == p).sum()]

    # Convert the centered delta basis (log10(r/100), c) to the absolute form
    # A*log10(r) + B*r + C that stage 09 applies: the -2*a term is the
    # log10(100) part of the basis change.
    absolute = dict(a_log10r=HB_A + delta.get('a_log10_r100', 0.),
                    b_r_km=HB_B + delta.get('b_r_minus_100_km', 0.),
                    c=HB_C + delta['c'] - 2. * delta.get('a_log10_r100', 0.))
    report = dict(round=args.round,
                  anchor=dict(catalog=args.anchor_catalog, magnitude_type=args.anchor_type.upper(),
                              events=int(m.event_id.nunique()), measurements=len(m),
                              clipped_measurements=fits[selected]['clipped']),
                  residual_structure_fits={name: dict(beta=fit['beta'], se=fit['se'], t=fit['t'],
                                                      clipped=fit['clipped'], measurements=fit['measurements'],
                                                      events=fit['events']) for name, fit in fits.items()},
                  selected_model=selected, selected_delta=delta,
                  absolute_coefficients=absolute,
                  corrected_anchor_residual_by_distance=distance_bins,
                  corrected_anchor_residual_by_station=station_terms,
                  corrected_anchor_residual_by_period=periods,
                  scale_validation=validation,
                  hb87_reference=dict(a_log10r=HB_A, b_r_km=HB_B, c=HB_C),
                  inputs={str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [Path(__file__), exp / '05_match_references/reference_matches.csv',
                           exp / '09_estimate_magnitude/station_magnitudes.csv',
                           exp / '09_estimate_magnitude/catalog.csv']})
    (out / 'fit.yaml').write_text(yaml.safe_dump(native(report), sort_keys=False))

    # Figures: residual vs distance, anchor before/after, station terms, scale validation.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'pdf.fonttype': 42, 'axes.spines.top': False,
                         'axes.spines.right': False})
    fig, axes = plt.subplots(1, 4, figsize=(13, 3), constrained_layout=True)
    axes[0].scatter(m.hypocentral_km, m.residual, s=3, alpha=.15, color='#34638b')
    axes[0].scatter(m.hypocentral_km, corrected, s=3, alpha=.15, color='#c26135')
    grid = np.linspace(10, max(150, m.hypocentral_km.max()), 200)
    curve = (delta.get('a_log10_r100', 0.) * np.log10(grid / 100.)
             + delta.get('b_r_minus_100_km', 0.) * (grid - 100.) + delta['c'])
    axes[0].plot(grid, curve, color='black', lw=1, label=f'fitted: {selected}')
    axes[0].axhline(0, color='black', lw=.7, ls=':')
    axes[0].set(xlabel='Hypocentral distance (km)', ylabel='Station $M_L$ − UUSS $M_L$')
    axes[0].legend(fontsize=7)
    axes[1].hist(m.residual, bins=60, histtype='step', color='#34638b', label='HB87 (r1)')
    axes[1].hist(corrected, bins=60, histtype='step', color='#c26135', label='recalibrated')
    axes[1].axvline(0, color='black', lw=.7, ls=':')
    axes[1].set(xlabel='Station residual to UUSS $M_L$', ylabel='Measurements')
    axes[1].legend(fontsize=7)
    st = [row for row in station_terms if row['n'] >= 20]
    axes[2].barh([row['instrument'] for row in st], [row['median'] for row in st], color='#34638b')
    axes[2].axvline(0, color='black', lw=.7, ls=':')
    axes[2].set(xlabel='Corrected station median residual', title='station terms (n≥20)')
    axes[2].tick_params(labelsize=6)
    labels = [f"{row['catalog']} {row['magnitude_type']} (n={row['n']})" for row in validation]
    x = np.arange(len(validation))
    axes[3].plot(x, [row['median_before'] for row in validation], 'o', color='#34638b', label='HB87 (r1)')
    axes[3].plot(x, [row['median_after'] for row in validation], 'o', color='#c26135', label='recalibrated')
    for row, xi in zip(validation, x):
        axes[3].plot([xi, xi], [row['median_before'] - row['mad_before'], row['median_before'] + row['mad_before']],
                     color='#34638b', lw=.8)
        axes[3].plot([xi, xi], [row['median_after'] - row['mad_after'], row['median_after'] + row['mad_after']],
                     color='#c26135', lw=.8)
    axes[3].axhline(0, color='black', lw=.7, ls=':')
    axes[3].set_xticks(x, labels, rotation=30, ha='right', fontsize=6)
    axes[3].set(ylabel='Event $M_L$ − reference median')
    axes[3].legend(fontsize=7)
    for i, ax in enumerate(axes):
        old = ax.get_title().strip()
        ax.set_title(f'{chr(97 + i)}  {old}'.rstrip(), loc='left', fontweight='bold')
    fig.savefig(out / 'ml_calibration_fit.png', dpi=220)
    fig.savefig(out / 'ml_calibration_fit.pdf')
    plt.close(fig)

    print(json.dumps(native(dict(selected_model=selected, delta=delta, absolute=absolute,
                                 anchor_events=int(m.event_id.nunique()), measurements=len(m),
                                 clipped=fits[selected]['clipped'],
                                 scale_validation=validation)), indent=2))

if __name__ == '__main__':
    main()
