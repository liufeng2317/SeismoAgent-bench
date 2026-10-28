#!/usr/bin/env python3
"""Compare human-expert reproduction, published reference catalogs, and agent runs.

Extends the audited five-source catalog-comparison figure family
(data/2019_ridgecrest_california/scripts/figures/plot_catalog_comparison.py)
with the populations produced inside this repository: the expert
workflow's stage-52 candidate, and the completed Claude x GLM agent runs
across task arms (min, tools, legacy). Everything reuses the
published-figure style, gating and anchors.

Outputs (evaluation/figures):
  01_reproduction_spatial_comparison  3x3 maps + population bar
  02_reproduction_population_diagnostics  magnitude CCDF, depth CDF,
     stage-rate heatmap, recall-by-magnitude
  03_agent_reference_correspondence   matched-pair diagnostics
  04_reproduction_hourly_rates        events-per-hour timeline
Benchmark scores come from metrics v1 (SeismoAgentBench/scoring/catalog_metrics); these are figures only.
"""
import argparse
import bisect
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

TASK = Path(__file__).resolve().parents[2]
CASE = TASK.parents[2] / 'data' / '2019_ridgecrest_california'
HOUSE = CASE / 'scripts' / 'figures' / 'plot_catalog_comparison.py'

spec = importlib.util.spec_from_file_location('house_figures', HOUSE)
house = importlib.util.module_from_spec(spec)
spec.loader.exec_module(house)

# Fixed categorical order (validated Okabe-Ito adjacency; see evaluation/README.md).
# 1-5 are the audited published sources, colors unchanged from the house figures.
EXPERT_COLOR = '#E69F00'
AGENT_TOOLS_COLOR = '#56B4E9'
AGENT_MIN_COLOR = '#F0E442'
AGENT_LEGACY_COLOR = '#000000'
# Agent arm featured in the recall and matched-pair diagnostics panels.
FOCUS_AGENT = 'agent_tools'

# Stage-60 union with the location-quality rule (round 08: picked events and
# templates need >= 1 stage-52 CC link, gap <= 150 deg, NLL sigma_x <= 0.8 km;
# the plain union put 5.2 % of events > 1 km off the faults), close events
# with >= 3 templates (round 09), moved into the published layered Shelly
# Table-1 frame by stage 63 (round 10), then rebuilt with 0.5 km templates from
# quality-passing events and close events needing >= 6 templates (round
# 12_dense_layered, 2026-10-25). Its depths
# are below sea level; +0.7 km puts them on the working catalog's convention
# (below the nominal 0.7-km-ASL surface, association.yaml reference_elevation_km).
# 2026-10-28: round 57_coda_duplicates = 12_dense_layered + stage-65 direct ML, the depth-bound large
# events restored by stage 66 (M7.1, M6.4, M5.4; depth empty) and stage-67 coda ghosts removed.
EXPERT_CATALOG = TASK / 'expert/export/57_coda_duplicates/60_catalog/catalog_events.csv'
EXPERT_DEPTH = ('depth_bsl_km', 0.7)
AGENT_RUNS = {
    'agent_min': {
        'label': 'Agent min',
        'color': AGENT_MIN_COLOR,
        'catalog': TASK / 'runs_pilot/min/claude/glm-5.3/20261013T215003Z/work/catalog.csv',
        'run_id': 'runs_pilot/min/claude/glm-5.3/20261013T215003Z',
    },
    'agent_tools': {
        'label': 'Agent tools',
        'color': AGENT_TOOLS_COLOR,
        'catalog': TASK / 'runs_pilot/tools/claude/glm-5.3/20261015T020300Z/work/catalog.csv',
        'run_id': 'runs_pilot/tools/claude/glm-5.3/20261015T020300Z',
    },
    'agent_legacy': {
        'label': 'Agent legacy',
        'color': AGENT_LEGACY_COLOR,
        'catalog': TASK / 'runs_pilot/base/claude/glm-5.3/20261013T043225Z/work/catalog.csv',
        'run_id': 'runs_pilot/base/claude/glm-5.3/20261013T043225Z',
    },
}

SHORT_LABELS = {
    'shelly': 'Shelly', 'liu': 'Liu', 'ross_relocated': 'Ross rel.',
    'awr_hypocenters': 'AWR v2', 'official_earthquake': 'Official',
    'expert': 'Expert', 'agent_min': 'Agent min', 'agent_tools': 'Agent tools',
    'agent_legacy': 'Agent legacy',
}

# Event correspondence criteria (documented in evaluation/README.md).
DT_MAX_S = 4.0
D_MAX_KM = 15.0

W0 = datetime(2019, 7, 4, tzinfo=timezone.utc)
W1 = datetime(2019, 7, 7, tzinfo=timezone.utc)


def parse_time(text):
    import re
    text = text.strip().replace('Z', '').replace(' ', 'T')
    # Python 3.9 fromisoformat rejects >6-digit fractional seconds; clamp them.
    text = re.sub(r'\.(\d{6})\d+', r'.\g<1>', text)
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def read_ours(path, time_col, depth_col='depth_km', depth_offset=0.0):
    rows = []
    with open(path, newline='') as fh:
        for r in csv_dict(fh):
            t = parse_time(r[time_col])
            if not W0 <= t < W1:
                continue
            rows.append({
                'time': t,
                'latitude': _f(r.get('latitude')),
                'longitude': _f(r.get('longitude')),
                'depth_km': None if _f(r.get(depth_col)) is None else _f(r.get(depth_col)) + depth_offset,
                'magnitude': _f(r.get('magnitude')),
            })
    rows.sort(key=lambda r: r['time'])
    return rows


def csv_dict(fh):
    import csv as _csv
    return _csv.DictReader(fh)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def as_record(key, label, color, rows):
    rec = {'key': key, 'label': label, 'color': color, 'rows': rows, 'linestyle': '-'}
    for field in ('latitude', 'longitude', 'depth_km', 'magnitude'):
        rec[field] = np.array([r[field] if r[field] is not None else np.nan for r in rows])
    rec['hour'] = np.array([(r['time'] - W0).total_seconds() / 3600 for r in rows])
    return rec


def load_references():
    """Published reference catalogs plus the expert reproduction."""
    cfg, audit, published, inputs = house.load_data(CASE)
    populations = list(published)
    inputs = dict(inputs)
    expert_rows = read_ours(EXPERT_CATALOG, 'origin_time_utc', *EXPERT_DEPTH)
    if not expert_rows:
        raise ValueError(f'No expert rows in window: {EXPERT_CATALOG}')
    populations.append(as_record('expert', 'Expert reproduction', EXPERT_COLOR, expert_rows))
    inputs['expert'] = {'path': str(EXPERT_CATALOG.relative_to(TASK)), 'plotted_records': len(expert_rows)}
    return cfg, audit, populations, inputs


def agent_run_style(key):
    """Color and linestyle for an agent population (see README palette notes)."""
    color = AGENT_RUNS.get(key, {}).get('color', AGENT_TOOLS_COLOR)
    if key == 'agent_legacy':
        return color, (0, (4, 2))
    if key == 'agent_min':
        # Yellow is the only free Okabe-Ito slot but sits next to the
        # expert orange on the deutan confusion axis; disambiguate lines.
        return color, (0, (4, 2, 1, 2))
    return color, '-'


def load_populations():
    cfg, audit, populations, inputs = load_references()
    for key, meta in AGENT_RUNS.items():
        rows = read_ours(meta['catalog'], 'origin_time_utc')
        if not rows:
            raise ValueError(f'No agent rows in window: {meta["catalog"]}')
        color, linestyle = agent_run_style(key)
        rec = as_record(key, meta['label'], color, rows)
        rec['linestyle'] = linestyle
        populations.append(rec)
        inputs[key] = {'path': str(meta['catalog'].relative_to(TASK)),
                       'plotted_records': len(rows), 'run_id': meta['run_id']}
    return cfg, audit, populations, inputs


def km(dla, dlo, lat):
    return math.hypot(dla * 111.195, dlo * 111.195 * math.cos(math.radians(lat)))


def match(rec_a, rec_b):
    """Greedy one-to-one pairing by (distance, dt) within the criteria."""
    times = [r['time'] for r in rec_b['rows']]
    cand = []
    for i, ra in enumerate(rec_a['rows']):
        j = bisect.bisect_left(times, ra['time'])
        for jj in range(max(0, j - 2), min(len(times), j + 3)):
            dt = abs((rec_b['rows'][jj]['time'] - ra['time']).total_seconds())
            if dt <= DT_MAX_S:
                d = km(ra['latitude'] - rec_b['rows'][jj]['latitude'],
                       ra['longitude'] - rec_b['rows'][jj]['longitude'], ra['latitude'])
                if d <= D_MAX_KM:
                    cand.append((d, dt, i, jj))
    cand.sort()
    used_a, used_b, pairs = set(), set(), []
    for d, dt, i, jj in cand:
        if i not in used_a and jj not in used_b:
            used_a.add(i)
            used_b.add(jj)
            pairs.append((i, jj, d, dt))
    return pairs


def map_panel(ax, rec, bounds, audit, letter, title, extent=None):
    """Depth-colored map; auto extent (with bounds rectangle) when data overflow."""
    lat, lon = rec['latitude'], rec['longitude']
    if extent is None:
        extent = (bounds['longitude'][0], bounds['longitude'][1],
                  bounds['latitude'][0], bounds['latitude'][1])
    beyond_bounds = int(np.sum((lon < bounds['longitude'][0]) | (lon > bounds['longitude'][1]) |
                               (lat < bounds['latitude'][0]) | (lat > bounds['latitude'][1]) |
                               ~np.isfinite(lon)))
    ax.scatter(lon, lat, c=rec['depth_km'], norm=Normalize(0, 20), cmap='viridis_r',
               s=1.0, linewidths=0, rasterized=True)
    house.map_axes(ax, {'longitude': [extent[0], extent[1]], 'latitude': [extent[2], extent[3]]})
    if (extent[0], extent[2]) != (bounds['longitude'][0], bounds['latitude'][0]):
        # Widened panel: replace the house fixed ticks (which cluster around the
        # reference box) with adaptive ticks spanning the actual extent.
        from matplotlib.ticker import MaxNLocator
        from matplotlib.ticker import FuncFormatter as _FF
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.xaxis.set_major_formatter(_FF(lambda x, _: f'{abs(x):.2f}'))
        ax.yaxis.set_major_formatter(_FF(lambda y, _: f'{y:.2f}'))
        ax.add_patch(Rectangle((bounds['longitude'][0], bounds['latitude'][0]),
                               bounds['longitude'][1] - bounds['longitude'][0],
                               bounds['latitude'][1] - bounds['latitude'][0],
                               fill=False, ec='#666666', lw=.8, ls='--', zorder=4))
    house.stars(ax, audit)
    house.panel_label(ax, letter, title)
    ax.text(.96, .04, f'n = {len(rec["rows"]):,}', transform=ax.transAxes, ha='right',
            fontsize=7, bbox={'fc': 'white', 'ec': 'none', 'alpha': .9, 'pad': 1.2})
    if beyond_bounds:
        # Clipped-at-bounds panels only annotate the overflow; widened panels
        # (atlas figure) also show where those events land.
        ax.text(.04, .04, f'{beyond_bounds:,} outside reference box', transform=ax.transAxes,
                ha='left', fontsize=6, color='#8a1c1c',
                bbox={'fc': 'white', 'ec': 'none', 'alpha': .9, 'pad': 1.2})


def fig_spatial(out, cfg, audit, pops):
    bounds = cfg['scientific_design']['candidate_window']['native_comparison_bounds']
    fig = plt.figure(figsize=(house.WIDTH_INCHES, 10.2))
    grid = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, .62], left=.085, right=.975,
                            bottom=.115, top=.965, wspace=.30, hspace=.38)
    for i, rec in enumerate(pops):
        ax = fig.add_subplot(grid[i // 3, i % 3])
        extent = None
        if rec['key'].startswith('agent_'):
            lat, lon = rec['latitude'], rec['longitude']
            ok = np.isfinite(lat) & np.isfinite(lon)
            overflow = np.sum((lon < bounds['longitude'][0]) | (lon > bounds['longitude'][1]) |
                              (lat < bounds['latitude'][0]) | (lat > bounds['latitude'][1]))
            if overflow:
                extent = (np.percentile(lon[ok], .5), np.percentile(lon[ok], 99.5),
                          np.percentile(lat[ok], .5), np.percentile(lat[ok], 99.5))
                pad_x = .04 * (extent[1] - extent[0])
                pad_y = .04 * (extent[3] - extent[2])
                extent = (extent[0] - pad_x, extent[1] + pad_x, extent[2] - pad_y, extent[3] + pad_y)
        map_panel(ax, rec, bounds, audit, chr(97 + i), rec['label'], extent=extent)
        if i % 3:
            ax.set_ylabel('')
        if i // 3 < 2:
            ax.set_xlabel('')
    ax = fig.add_subplot(grid[3, :])
    y = np.arange(len(pops))
    ax.barh(y, [len(r['rows']) for r in pops], color=[r['color'] for r in pops], height=.58)
    ax.set_yticks(y, labels=[SHORT_LABELS[r['key']] for r in pops], fontsize=6)
    ax.invert_yaxis()
    top = max(len(r['rows']) for r in pops)
    step = 2500 if top <= 15000 else 5000
    ax.set_xlim(0, (top // step + 1) * step)
    from matplotlib.ticker import FuncFormatter, MultipleLocator
    ax.xaxis.set_major_locator(MultipleLocator(step))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    ax.set_xlabel('Catalog records in window')
    for i, rec in enumerate(pops):
        ax.text(len(rec['rows']) + top * .012, i, f'{len(rec["rows"]):,}', va='center', fontsize=6)
    house.panel_label(ax, 'j', 'Population size')
    cax = fig.add_axes([.09, .028, .45, .012])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 20), cmap='viridis_r'),
                       cax=cax, orientation='horizontal', ticks=[0, 5, 10, 15, 20])
    bar.set_label('Native depth (km)', labelpad=3)
    house.save_figure(fig, out / '01_reproduction_spatial_comparison')
    plt.close(fig)


def stage_bounds(audit):
    t64 = parse_time(audit['anchors']['mw6_4']['time'])
    t71 = parse_time(audit['anchors']['mw7_1']['time'])
    from datetime import timedelta
    h = timedelta(hours=1)
    return [('Before Mw 6.4', W0, t64), ('Mw 6.4 first hour', t64, t64 + h),
            ('Between, later', t64 + h, t71), ('Mw 7.1 first hour', t71, t71 + h),
            ('After 7.1, later', t71 + h, W1)]


def fig_diagnostics(out, cfg, audit, pops, stats):
    fig = plt.figure(figsize=(house.WIDTH_INCHES, 8.8))
    grid = fig.add_gridspec(3, 2, height_ratios=[1, .78, 1], left=.085, right=.965,
                            bottom=.105, top=.955, wspace=.30, hspace=.55)
    amag = fig.add_subplot(grid[0, 0])
    adepth = fig.add_subplot(grid[0, 1])
    arate = fig.add_subplot(grid[1, :])
    arec = fig.add_subplot(grid[2, 0])
    atime = fig.add_subplot(grid[2, 1])
    ours = ('expert', 'agent_min', 'agent_tools', 'agent_legacy')
    # Focus-and-context: published references thin and translucent, one proxy
    # legend entry; reproductions bold.
    for r in pops:
        focus = r['key'] in ours or r['key'] == 'shelly'
        lw = 1.6 if r['key'] in ours else (1.1 if r['key'] == 'shelly' else .85)
        alpha = 1.0 if focus else .45
        label = None
        if r['key'] in ours:
            label = r['label']
        elif r['key'] == 'shelly':
            label = 'Shelly (reference)'
        mag = np.sort(r['magnitude'][np.isfinite(r['magnitude'])])
        values, first = np.unique(mag, return_index=True)
        amag.step(values, (len(mag) - first) / len(mag), where='pre', color=r['color'],
                  lw=lw, ls=r.get('linestyle', '-'), alpha=alpha, label=label)
        depths = np.sort(r['depth_km'][np.isfinite(r['depth_km'])])
        adepth.step(depths, np.arange(1, len(depths) + 1) / len(depths), where='post',
                    color=r['color'], lw=lw, ls=r.get('linestyle', '-'), alpha=alpha)
    handles = [Line2D([], [], color='#8a8f98', lw=.9, label='Published references')]
    handles += [ln for ln in amag.get_lines() if ln.get_label()]
    amag.set_yscale('log')
    amag.set_ylim(1e-4, 1.6)
    amag.set_xlim(-2, 7.4)
    amag.set_xlabel('Native magnitude')
    amag.set_ylabel('Fraction with magnitude ≥ M')
    amag.legend(handles=handles, frameon=False, fontsize=6, loc='lower left',
                handlelength=1.7, labelspacing=.32)
    house.panel_label(amag, 'a', 'Magnitude populations')
    adepth.set_xlim(0, 20)
    adepth.set_ylim(0, 1)
    adepth.set_xlabel('Native depth (km)')
    adepth.set_ylabel('Cumulative fraction')
    house.panel_label(adepth, 'b', 'Depth distributions')
    # Stage-rate heatmap, full width: stages x catalogs.
    stages = stage_bounds(audit)
    rates = np.zeros((len(stages), len(pops)))
    for si, (_, s, e) in enumerate(stages):
        for pi, r in enumerate(pops):
            inside = (r['hour'] >= (s - W0).total_seconds() / 3600) & \
                     (r['hour'] < (e - W0).total_seconds() / 3600)
            rates[si, pi] = inside.sum() / ((e - s).total_seconds() / 3600)
    im = arate.imshow(rates, cmap='YlGnBu', norm=LogNorm(vmin=.5, vmax=400), aspect='auto')
    arate.set_xticks(range(len(pops)), labels=[SHORT_LABELS[r['key']] for r in pops],
                     fontsize=6.4)
    arate.set_yticks(range(len(stages)),
                     labels=['Before Mw 6.4', 'Mw 6.4 +1 h', 'Between', 'Mw 7.1 +1 h',
                             'After Mw 7.1'], fontsize=6.4)
    arate.tick_params(length=0)
    for i in range(len(stages)):
        for j in range(len(pops)):
            arate.text(j, i, f'{rates[i, j]:.0f}', ha='center', va='center', fontsize=6.2,
                       color='white' if rates[i, j] > 60 else '#1c2e41')
    house.panel_label(arate, 'c', 'Stage-specific rate (events h⁻¹)')
    pos = arate.get_position()
    cax = fig.add_axes([pos.x0, pos.y0 - .075, pos.width * .55, .012])
    bar = fig.colorbar(im, cax=cax, orientation='horizontal', ticks=[1, 10, 100, 400])
    bar.ax.set_xticklabels(['1', '10', '100', '400'])
    bar.ax.minorticks_off()
    # Recall of reference events by magnitude band (focus agent arm).
    bands = [(0, 1), (1, 2), (2, 3), (3, 8)]
    width = .38
    for k, (ref_key, label) in enumerate((('expert', 'vs Expert'), ('shelly', 'vs Shelly'))):
        ref = next(r for r in pops if r['key'] == ref_key)
        m = stats[FOCUS_AGENT]['versus'][ref_key]
        xs, ys, ns = [], [], []
        for b, (lo, hi) in enumerate(bands):
            idx = [j for j, r in enumerate(ref['rows'])
                   if r['magnitude'] is not None and lo <= r['magnitude'] < hi]
            hit = sum(1 for j in idx if j in set(m['matched_reference_indices']))
            xs.append(b + (width / 2 if k else -width / 2))
            ys.append(hit / len(idx) if idx else np.nan)
            ns.append(len(idx))
        arec.bar(xs, ys, width=width, color=(AGENT_TOOLS_COLOR if k else EXPERT_COLOR), label=label)
        for x, y, n in zip(xs, ys, ns):
            if n:
                arec.text(x, y + .02, f'{y:.0%}', ha='center', fontsize=5.8)
    arec.set_xticks(range(len(bands)), labels=[f'M {lo}–{hi}' for lo, hi in bands], fontsize=6.5)
    arec.set_ylim(0, 1.12)
    arec.set_yticks([0, .25, .5, .75, 1], labels=['0', '25', '50', '75', '100%'])
    arec.set_xlabel('Reference magnitude band')
    arec.set_ylabel('Reference events detected')
    arec.legend(frameon=False, fontsize=6, loc='lower left')
    house.panel_label(arec, 'd', f'{SHORT_LABELS[FOCUS_AGENT]} recall by magnitude')
    # Hourly rates, published-figure conventions.
    for r in pops:
        if r['key'] not in ('shelly', 'expert', 'agent_min', 'agent_tools', 'agent_legacy'):
            continue
        counts, edges = np.histogram(r['hour'], bins=np.arange(73))
        atime.stairs(counts, edges, color=r['color'], lw=1.3 if r['key'] != 'shelly' else .9,
                     ls=r.get('linestyle', '-'), label=SHORT_LABELS[r['key']])
    for key in ('mw6_4', 'mw7_1'):
        hour = (parse_time(audit['anchors'][key]['time']) - W0).total_seconds() / 3600
        atime.axvline(hour, color='#999999', lw=.7, ls='--', zorder=0)
        atime.text(hour + .7, .97, f'Mw {audit["anchors"][key]["magnitude"]:.1f}',
                   transform=atime.get_xaxis_transform(), fontsize=6, va='top')
    atime.set_xlim(0, 72)
    atime.set_yscale('symlog', linthresh=1)
    atime.set_ylim(0, 2000)
    atime.set_yticks([0, 10, 100, 1000], labels=['0', '10', '100', '1,000'])
    atime.set_xticks([0, 24, 48, 72], labels=['4 Jul', '5 Jul', '6 Jul', '7 Jul'])
    atime.set_ylabel('Events per hour')
    atime.set_xlabel('2019 (UTC)')
    atime.legend(frameon=True, framealpha=.9, edgecolor='none', fontsize=5.8,
                 loc='lower right', ncol=2, columnspacing=.9, handlelength=1.6)
    house.panel_label(atime, 'e', 'Recorded event rate')
    house.save_figure(fig, out / '02_reproduction_population_diagnostics')
    plt.close(fig)


def fig_correspondence(out, cfg, audit, pops, stats, focus_agent=FOCUS_AGENT,
                       stem='03_agent_reference_correspondence'):
    fig = plt.figure(figsize=(house.WIDTH_INCHES, 6.4))
    grid = fig.add_gridspec(2, 2, left=.17, right=.965, bottom=.145, top=.93,
                            wspace=.40, hspace=.46)
    adt = fig.add_subplot(grid[0, 0])
    adist = fig.add_subplot(grid[0, 1])
    amg = fig.add_subplot(grid[1, 0])
    adep = fig.add_subplot(grid[1, 1])
    refs = [('expert', 'Expert'), ('shelly', 'Shelly')]
    # (a) origin-time differences of matched pairs.
    bins = np.linspace(0, DT_MAX_S, 33)
    for key, label in refs:
        dts = np.array(stats[focus_agent]['versus'][key]['dt_samples_s'])
        adt.hist(dts, bins=bins, histtype='stepfilled', alpha=.28, lw=1.2,
                 color=EXPERT_COLOR if key == 'expert' else '#0072B2', label=label)
    adt.set_yscale('log')
    adt.set_ylim(.5, 2e3)
    adt.set_xlabel('|Δ origin time| (s, agent − reference)')
    adt.set_ylabel('Matched pairs')
    adt.legend(frameon=False, fontsize=6.5)
    house.panel_label(adt, 'a', 'Origin-time agreement')
    # (b) horizontal difference, house dot/diamond convention.
    for i, (key, label) in enumerate(refs):
        q = stats[focus_agent]['versus'][key]
        adist.plot([q['horizontal_km']['p50'], q['horizontal_km']['p90']], [i, i],
                   color='#8996a3', lw=1.3)
        adist.plot(q['horizontal_km']['p50'], i, 'o', color='#245775', ms=4)
        adist.plot(q['horizontal_km']['p90'], i, 'D', mfc='white', mec='#245775', ms=4)
    adist.set_yticks(range(2), labels=[f'{l}\nn = {stats[focus_agent]["versus"][k]["matched"]:,}'
                                       for (k, l) in refs], fontsize=6.4)
    adist.set_ylim(1.6, -.8)
    adist.set_xlim(0, D_MAX_KM)
    adist.set_xlabel('Horizontal difference (km)')
    adist.legend(handles=[Line2D([], [], marker='o', color='#245775', ls='', ms=4, label='Median'),
                          Line2D([], [], marker='D', mfc='white', mec='#245775', ls='', ms=4,
                                 label='90th percentile')],
                 frameon=False, fontsize=6, loc='lower right')
    house.panel_label(adist, 'b', 'Epicentral agreement')
    # (c) magnitude difference vs reference magnitude.
    pairs = [p for p in stats[focus_agent]['versus']['expert']['pairs']
             if p['ref_magnitude'] is not None and p['magnitude_difference'] is not None]
    em = np.array([p['ref_magnitude'] for p in pairs])
    dm = np.array([p['magnitude_difference'] for p in pairs])
    amg.scatter(em, dm, s=2, alpha=.2,
                color=next(r for r in pops if r['key'] == focus_agent)['color'],
                linewidths=0, rasterized=True)
    edges = np.arange(0, 6.5, .5)
    centers, med = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = dm[(em >= lo) & (em < hi)]
        if len(sel) >= 12:
            centers.append((lo + hi) / 2)
            med.append(np.median(sel))
    amg.plot(centers, med, color='#222222', lw=1.3)
    amg.axhline(0, color='#999999', lw=.6)
    amg.set_xlim(0, 6.5)
    amg.set_ylim(-3, 1.5)
    amg.set_xlabel('Expert magnitude')
    amg.set_ylabel('Δ magnitude (agent − expert)')
    house.panel_label(amg, 'c', f'Magnitude bias (n = {len(dm):,})')
    # (d) depth comparison of matched pairs.
    dpairs = [p for p in stats[focus_agent]['versus']['expert']['pairs']
              if p['ref_depth_km'] is not None and p['agent_depth_km'] is not None]
    ed = np.array([p['ref_depth_km'] for p in dpairs])
    ad = np.array([p['agent_depth_km'] for p in dpairs])
    adep.scatter(ed, ad, s=2, alpha=.2,
                 color=next(r for r in pops if r['key'] == focus_agent)['color'],
                 linewidths=0, rasterized=True)
    adep.plot([0, 20], [0, 20], color='#999999', lw=.7)
    adep.set_xlim(0, 20)
    adep.set_ylim(0, 25)
    adep.set_xlabel('Expert depth (km)')
    adep.set_ylabel('Agent depth (km)')
    house.panel_label(adep, 'd', 'Depth comparison')
    house.save_figure(fig, out / stem)
    plt.close(fig)


def fig_rates(out, cfg, audit, pops):
    fig = plt.figure(figsize=(house.WIDTH_INCHES, 3.1))
    ax = fig.add_axes([.09, .17, .88, .74])
    for r in pops:
        if r['key'] not in ('shelly', 'liu', 'ross_relocated', 'awr_hypocenters',
                            'official_earthquake', 'expert', 'agent_min', 'agent_tools',
                            'agent_legacy'):
            continue
        counts, edges = np.histogram(r['hour'], bins=np.arange(73))
        ax.stairs(counts, edges, color=r['color'], lw=1.2, ls=r.get('linestyle', '-'),
                  label=SHORT_LABELS[r['key']])
    for key in ('mw6_4', 'mw7_1'):
        hour = (parse_time(audit['anchors'][key]['time']) - W0).total_seconds() / 3600
        ax.axvline(hour, color='#999999', lw=.7, ls='--', zorder=0)
        ax.text(hour + .7, .97, f'Mw {audit["anchors"][key]["magnitude"]:.1f}',
                transform=ax.get_xaxis_transform(), fontsize=6, va='top')
    ax.set_xlim(0, 72)
    ax.set_yscale('symlog', linthresh=1)
    ax.set_ylim(0, 2500)
    ax.set_yticks([0, 10, 100, 1000], labels=['0', '10', '100', '1,000'])
    ax.set_xticks([0, 24, 48, 72], labels=['4 Jul', '5 Jul', '6 Jul', '7 Jul'])
    ax.set_ylabel('Events per hour')
    ax.set_xlabel('2019 (UTC)')
    ax.legend(frameon=True, framealpha=.9, edgecolor='none', fontsize=6, loc='lower right',
              ncol=2, columnspacing=.9, handlelength=1.6)
    house.panel_label(ax, 'a', 'Hourly event rate, all populations')
    house.save_figure(fig, out / '04_reproduction_hourly_rates')
    plt.close(fig)


def q(arr, p):
    arr = np.sort(arr)
    return float(arr[min(int(len(arr) * p), len(arr) - 1)])


def compute_stats(pops, focus_agent=FOCUS_AGENT):
    agents = [(r['key'], r) for r in pops if r['key'].startswith('agent_')]
    stats = {'window': {'start_utc': '2019-07-04T00:00:00Z', 'end_utc': '2019-07-07T00:00:00Z'},
             'matching': {'dt_max_s': DT_MAX_S, 'd_max_km': D_MAX_KM,
                          'method': 'greedy one-to-one by (distance, dt)'}}
    for agent_key, arec in agents:
        stats[agent_key] = {'events': len(arec['rows']), 'versus': {}}
        for ref_key in ('expert', 'shelly', 'official_earthquake'):
            ref = next(r for r in pops if r['key'] == ref_key)
            pairs = match(arec, ref)
            dts = np.array([p[3] for p in pairs])
            ds = np.array([p[2] for p in pairs])
            entry = {'matched': len(pairs),
                     'precision': len(pairs) / len(arec['rows']),
                     'recall': len(pairs) / len(ref['rows'])}
            if len(pairs):
                entry['dt_s'] = {'p50': q(dts, .5), 'p90': q(dts, .9)}
                entry['horizontal_km'] = {'p50': q(ds, .5), 'p90': q(ds, .9)}
                entry['matched_reference_indices'] = sorted(p[1] for p in pairs)
                if agent_key == focus_agent and ref_key in ('expert', 'shelly'):
                    entry['dt_samples_s'] = dts.tolist()
                if agent_key == focus_agent and ref_key == 'expert':
                    entry['pairs'] = [{
                        'agent_depth_km': arec['rows'][i]['depth_km'],
                        'ref_depth_km': ref['rows'][j]['depth_km'],
                        'ref_magnitude': ref['rows'][j]['magnitude'],
                        'magnitude_difference': (arec['rows'][i]['magnitude'] - ref['rows'][j]['magnitude']
                                                 if arec['rows'][i]['magnitude'] is not None
                                                 and ref['rows'][j]['magnitude'] is not None else None),
                    } for i, j, d, dt in pairs]
            stats[agent_key]['versus'][ref_key] = entry
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-dir', type=Path, default=TASK)
    args = parser.parse_args()
    out = args.task_dir / 'evaluation' / 'agents' / 'pilot' / 'figures'  # pilot runs vs expert and references
    out.mkdir(parents=True, exist_ok=True)
    cfg, audit, pops, inputs = load_populations()
    stats = compute_stats(pops)
    with house.publication_style():
        fig_spatial(out, cfg, audit, pops)
        fig_diagnostics(out, cfg, audit, pops, stats)
        fig_correspondence(out, cfg, audit, pops, stats)
        fig_rates(out, cfg, audit, pops)
    print(json.dumps({r['key']: len(r['rows']) for r in pops}, ensure_ascii=False))
    print('Figures:', out)


if __name__ == '__main__':
    main()
