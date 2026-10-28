#!/usr/bin/env python3
"""Compare the Prague expert catalog, the case references, and agent runs.

Populations, all inside the evaluation window [2011-11-11T00:00Z, 2011-11-19T00:00Z)
(the stable-network interval after the 2011-11-06 Mw 5.7, which precedes it):

  cochran  Cochran et al. (2020) template-enhanced relocated catalog (primary)
  mcmahon  McMahon et al. (2017) subspace-detection release (E records)
  isken    Isken & Mooney (2017) Table S3, M>3 manual relocations; origin times
           to the minute, so matched at 60 s / 5 km — a location anchor
  comcat   ComCat operational (11 events)
  expert   this repository's expert workflow, round catalog r3 (r2 + Match&Locate)
  <run>    every Agent run under runs/ (``discover_runs``); a run without
           work/catalog.csv is drawn from its recovered outputs, labelled
           'rescue' (reference only, not a formal result)

References are read and masked by the expert stage-05 module itself
(``expert/04_comparison/05_match_references.py``: readers, cohort mask) —
one implementation, so figures and round feedback cannot drift apart; masked
counts are hard asserts (``expert/00_config/validation.yaml``).
Correspondence: greedy one-to-one pairing by (distance, dt) within
|dt| <= 4 s and 15 km (a reference's own validation.yaml ``gates`` override:
Isken 60 s / 5 km). Reference depth datums are unstated (local surface
~0.28 km ASL); expert depths are converted from sea level with the model datum.

Outputs (evaluation/): expert/figures/{01,02} (references + expert);
agents/<run>/figures/{01,02,03} (references + expert + that run; 03 = matched-
pair correspondence); comparison/figures/{01,02} (references + expert + all runs).
Benchmark scores come from metrics v1 (SeismoAgentBench/scoring/catalog_metrics); these are figures only.
"""
import argparse
import bisect
import csv as _csv
import importlib.util
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.ticker import FuncFormatter, MultipleLocator, NullLocator
import numpy as np
import yaml

TASK = Path(__file__).resolve().parents[2]
EXPERT = TASK / 'expert'
CONFIG = yaml.safe_load((EXPERT / '00_config' / 'config.yaml').read_text())
CASE = (EXPERT / CONFIG['case_root']).resolve()
STYLE = CASE / 'scripts' / 'figures' / 'figure_style.py'


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


style = _load_module('prague_figure_style', STYLE)
REVIEW = _load_module('prague_stage05', EXPERT / '04_comparison' / '05_match_references.py')

# ------------------------------------------------------------- case settings
TITLE = '2011 Prague, Oklahoma'
PRIMARY = 'cochran'                       # depth panel / section axis reference
SECONDARY = ['cochran', 'mcmahon']        # epicentral panel references
COLORS = {'cochran': '#0072B2', 'mcmahon': '#D55E00', 'isken': '#7B5EA7', 'comcat': '#009E73'}
SHORT_LABELS = {'cochran': 'Cochran et al. 2020', 'mcmahon': 'McMahon et al. 2017', 'isken': 'Isken 2017 (M>3)',
                'comcat': 'ComCat'}
# Figures centre on the Mw 5.7 (Cochran location, expert config); it precedes
# the window, so it has no time marker.
CENTER = (CONFIG['mainshock']['longitude'], CONFIG['mainshock']['latitude'])
STAR = (CONFIG['mainshock']['longitude'], CONFIG['mainshock']['latitude'], CONFIG['mainshock']['depth_km'])
VIEW = {'east': (-10.0, 6.0), 'north': (-8.0, 4.0), 'along': (-10.0, 6.0), 'depth': (-1.0, 12.0)}
BIN_KM = 0.25
MAG_XLIM = (-2.0, 5.0)
DEPTH_LABEL = 'depth below surface (km)'
TIME_MARK = None
SPATIAL_EXCLUDE = ['isken']               # references too sparse for a density panel
EXPERT_ROUNDS = {
    'r2': (EXPERT / 'export/r2/10_validate_catalog/events.csv', 'origin_time', 'depth_below_sea_level_km'),
    'r3': (EXPERT / 'export/r3/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),
    'r4': (EXPERT / 'export/r4/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),
    'r5': (EXPERT / 'export/r5/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),
    'r7': (EXPERT / 'export/r7/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),  # stages 65/67 (2026-10-28)
}
EXPERT_ROUND = 'r7'
# ----------------------------------------------------------------------------

EXPERT_COLOR = '#E69F00'
AGENT_TOOLS_COLOR = '#56B4E9'
AGENT_MIN_COLOR = '#F0E442'
SHORT_LABELS.update({'expert': f'Expert ({EXPERT_ROUND})'})
MODEL_DATUM_KM = float(yaml.safe_load((EXPERT / '00_config' / 'association.yaml').read_text())
                       ['reference_elevation_km'])

RUN_COLORS = {'min': AGENT_MIN_COLOR, 'tools': AGENT_TOOLS_COLOR}
# Recovered outputs of a run whose work/ holds none (late or misplaced; reference only).
RESCUE_SOURCES = ('record/late_outputs', 'record/agent_home_work_mirror', 'record/runtime_home/work/out',
                  'record/runtime_home/work')


def discover_runs():
    """Every Agent run under runs/<variant>/<harness>/<model>/<run_id>, keyed by its agents/ folder name."""
    runs = {}
    for run in sorted((TASK / 'runs').glob('*/*/*/*')):
        if not (run / 'control').is_dir():
            continue
        variant, harness, model, run_id = run.relative_to(TASK / 'runs').parts
        catalog, rescue = run / 'work' / 'catalog.csv', False
        if not catalog.is_file():
            found = [run / d / 'catalog.csv' for d in RESCUE_SOURCES if (run / d / 'catalog.csv').is_file()]
            if not found:
                continue
            catalog, rescue = found[0], True
        key = f'{variant}__{harness}__{model}__{run_id}'
        runs[key] = {'label': f'Agent {variant}' + (' (rescue)' if rescue else ''), 'variant': variant,
                     'color': RUN_COLORS.get(variant, AGENT_TOOLS_COLOR), 'catalog': catalog, 'rescue': rescue,
                     'run_id': str(run.relative_to(TASK))}
    return runs


AGENT_RUNS = discover_runs()

DT_MAX_S = 4.0
D_MAX_KM = 15.0

MASK = yaml.safe_load((EXPERT / '00_config' / 'validation.yaml').read_text())
REFS = list(MASK['references'])
W0 = datetime.fromisoformat(MASK['window']['start_utc'].replace('Z', '+00:00'))
W1 = datetime.fromisoformat(MASK['window']['end_utc'].replace('Z', '+00:00'))


def parse_time(text):
    text = text.strip().replace('Z', '').replace(' ', 'T')
    text = re.sub(r'\+00:00$', '', text)
    # Python 3.9 fromisoformat rejects >6-digit fractional seconds; clamp them.
    text = re.sub(r'\.(\d{6})\d+', r'.\g<1>', text)
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def _f(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def read_catalog(path, time_col, depth_col='depth_km', keep=None, depth_offset=0.0):
    """Generic catalog reader (expert events.csv, agent catalog.csv); depth_offset shifts the datum."""
    rows = []
    with open(path, newline='') as fh:
        for r in _csv.DictReader(fh):
            if keep is not None and not keep(r):
                continue
            rows.append({'time': parse_time(r[time_col]), 'latitude': _f(r.get('latitude')),
                         'longitude': _f(r.get('longitude')),
                         'depth_km': None if _f(r.get(depth_col)) is None else _f(r.get(depth_col)) + depth_offset,
                         'magnitude': _f(r.get('magnitude'))})
    rows = [r for r in rows if W0 <= r['time'] < W1]
    rows.sort(key=lambda r: r['time'])
    return rows


def as_record(key, label, color, rows, linestyle='-', gates=None):
    rec = {'key': key, 'label': label, 'color': color, 'rows': rows, 'linestyle': linestyle, 'gates': gates}
    for field in ('latitude', 'longitude', 'depth_km', 'magnitude'):
        rec[field] = np.array([r[field] if r[field] is not None else np.nan for r in rows])
    rec['hour'] = np.array([(r['time'] - W0).total_seconds() / 3600 for r in rows])
    return rec


def load_references():
    """Masked reference cohorts via the stage-05 readers; counts are hard asserts."""
    frames, _ = REVIEW.read_references(CASE, MASK['references'])
    populations, inputs = [], {}
    for name in REFS:
        f = frames[name][REVIEW.reference_mask(frames[name], MASK)]
        mags = f['magnitude'] if 'magnitude' in f else [None] * len(f)
        rows = sorted(({'time': t.to_pydatetime(warn=False), 'latitude': _f(la), 'longitude': _f(lo),
                        'depth_km': _f(z), 'magnitude': _f(m)}
                       for t, la, lo, z, m in zip(f.time, f.latitude, f.longitude, f.depth_km, mags)),
                      key=lambda r: r['time'])
        expected = MASK['expected_reference_counts'][name]
        assert len(rows) == expected, f'{name}: {len(rows)} masked rows != gate {expected}'
        gates = (MASK['references'][name].get('gates') or {}).get('primary')
        populations.append(as_record(name, MASK['references'][name]['label'], COLORS[name], rows, gates=gates))
        inputs[name] = {'path': MASK['references'][name]['path'], 'plotted_records': len(rows)}
        if gates:
            inputs[name]['gates'] = gates
    return populations, inputs


def load_expert(round_=EXPERT_ROUND):
    # Complete round catalog (all rows), symmetric with an agent catalog; the
    # curated v1 subset lives in the round reports.
    path, time_col, depth_col = EXPERT_ROUNDS[round_]
    rows = read_catalog(path, time_col, depth_col=depth_col, depth_offset=MODEL_DATUM_KM)
    if not rows:
        raise ValueError(f'No expert rows in window: {path}')
    rec = as_record('expert', f'Expert reproduction ({round_})', EXPERT_COLOR, rows)
    return rec, {'path': str(path.relative_to(TASK)), 'round': round_, 'plotted_records': len(rows),
                 'selection': 'complete round catalog (all rows)'}


def agent_run_style(key):
    meta = AGENT_RUNS.get(key, {})
    return meta.get('color', AGENT_TOOLS_COLOR), ((0, (4, 2, 1, 2)) if meta.get('rescue') else '-')


def load_populations():
    populations, inputs = load_references()
    expert, expert_input = load_expert()
    populations.append(expert)
    inputs['expert'] = expert_input
    for key, meta in AGENT_RUNS.items():
        if not meta['catalog'].is_file():
            print(f'skipping {key}: no catalog at {meta["catalog"]}')
            continue
        rows = read_catalog(meta['catalog'], 'origin_time_utc')
        if not rows:
            print(f'skipping {key}: no rows in window')
            continue
        color, linestyle = agent_run_style(key)
        populations.append(as_record(key, meta['label'], color, rows, linestyle=linestyle))
        inputs[key] = {'path': str(meta['catalog'].relative_to(TASK)),
                       'plotted_records': len(rows), 'run_id': meta['run_id']}
    return populations, inputs


# --- correspondence ---

def km(dla, dlo, lat):
    return math.hypot(dla * 111.195, dlo * 111.195 * math.cos(math.radians(lat)))


def match(rec_a, rec_b):
    """Greedy one-to-one pairing by (distance, dt) within the criteria (rec_b gates override)."""
    dt_max, d_max = rec_b.get('gates') or (DT_MAX_S, D_MAX_KM)
    times = [r['time'] for r in rec_b['rows']]
    cand = []
    for i, ra in enumerate(rec_a['rows']):
        if ra['latitude'] is None or ra['longitude'] is None:
            continue  # unlocated rows never enter correspondence
        lo = bisect.bisect_left(times, ra['time'] - timedelta(seconds=dt_max))
        hi = bisect.bisect_right(times, ra['time'] + timedelta(seconds=dt_max))
        for jj in range(lo, hi):
            rb = rec_b['rows'][jj]
            if rb['latitude'] is None or rb['longitude'] is None:
                continue
            dt = abs((rb['time'] - ra['time']).total_seconds())
            d = km(ra['latitude'] - rb['latitude'], ra['longitude'] - rb['longitude'], ra['latitude'])
            if d <= d_max:
                cand.append((d, dt, i, jj))
    cand.sort()
    used_a, used_b, pairs = set(), set(), []
    for d, dt, i, jj in cand:
        if i not in used_a and jj not in used_b:
            used_a.add(i)
            used_b.add(jj)
            pairs.append((i, jj, d, dt))
    return pairs


def q(arr, p):
    arr = np.asarray(arr, dtype=float)
    return float(np.nanpercentile(arr, p)) if np.isfinite(arr).any() else None


def compute_stats(pops, focus_agent=None):
    stats = {}
    for p in pops:
        if p['key'] in REFS:
            continue
        versus = {}
        for other in pops:
            if other['key'] == p['key']:
                continue
            pairs = match(p, other)
            dz = [p['rows'][i]['depth_km'] - other['rows'][j]['depth_km'] for i, j, _, _ in pairs
                  if p['rows'][i]['depth_km'] is not None and other['rows'][j]['depth_km'] is not None]
            med = q(dz, 50)
            versus[other['key']] = {
                'matched': len(pairs),
                'precision': len(pairs) / len(p['rows']) if p['rows'] else None,
                'recall': len(pairs) / len(other['rows']) if other['rows'] else None,
                'median_abs_dt_s': q([dt for _, _, _, dt in pairs], 50),
                'median_epicentral_km': q([d for _, _, d, _ in pairs], 50),
                'median_depth_difference_km': med,
                'mad_depth_difference_km': None if med is None else q([abs(v - med) for v in dz], 50),
            }
        stats[p['key']] = {'records': len(p['rows']), 'versus': versus}
    return stats


# --- figures ---
# Spatial figures work in km about CENTER. Each catalog gets its own column
# (small multiples, shared axes, one shared colour scale), drawn as a 2-D
# event-count density; events outside the shared view are counted per column.

LON0, LAT0 = CENTER
DENSITY_CMAP = LinearSegmentedColormap.from_list('density', ['#d4e3f2', '#6a9fd1', '#1f5a99', '#08254d'])
DENSITY_CMAP.set_bad(alpha=0)


def panel_label(ax, letter, title):
    ax.set_title(title, loc='left', fontsize=7.5, pad=3)
    ax.text(-0.02, 1.0, letter, transform=ax.transAxes, fontsize=9, fontweight='bold',
            va='bottom', ha='right')


def horiz_km(rec):
    return ((rec['longitude'] - LON0) * 111.195 * math.cos(math.radians(LAT0)),
            (rec['latitude'] - LAT0) * 111.195)


def strike_angle(rec):
    """Section axis = major axis of the reference's horizontal distribution."""
    x, y = horiz_km(rec)
    ok = np.isfinite(x) & np.isfinite(y)
    evals, evecs = np.linalg.eigh(np.cov(np.stack([x[ok], y[ok]])))
    v = evecs[:, np.argmax(evals)]
    if v[0] < 0:            # point the axis eastward
        v = -v
    return math.atan2(v[1], v[0])


def _counts(u, v, ulim, vlim):
    ub = np.arange(ulim[0], ulim[1] + 1e-9, BIN_KM)
    vb = np.arange(vlim[0], vlim[1] + 1e-9, BIN_KM)
    ok = np.isfinite(u) & np.isfinite(v)
    h, _, _ = np.histogram2d(u[ok], v[ok], bins=[ub, vb])
    inside = int(np.sum((u[ok] >= ulim[0]) & (u[ok] <= ulim[1]) & (v[ok] >= vlim[0]) & (v[ok] <= vlim[1])))
    return ub, vb, np.ma.masked_equal(h.T, 0), int(ok.sum()) - inside


def _star(ax, x, y):
    ax.plot(x, y, marker='*', ms=8, mfc='white', mec='black', mew=.6, ls='none', zorder=5)


def _tick(span):
    return next(t for t in (1, 2, 5, 10, 20, 50, 100) if span / t <= 5)


def spatial_grid(pops, stem, title):
    """Row 1: map density; row 2: depth section along the reference's major axis."""
    theta = strike_angle(next(p for p in pops if p['key'] == PRIMARY))
    grids = []
    for p in pops:
        x, y = horiz_km(p)
        along = x * math.cos(theta) + y * math.sin(theta)
        grids.append((_counts(x, y, VIEW['east'], VIEW['north']),
                      _counts(along, p['depth_km'], VIEW['along'], VIEW['depth'])))
    vmax = max(float(g.max()) for pair in grids for (_, _, g, _) in pair)
    norm = LogNorm(1, vmax)
    ncol = len(pops)
    map_h = (VIEW['north'][1] - VIEW['north'][0]) / (VIEW['east'][1] - VIEW['east'][0])
    sec_h = 0.68
    width = style.WIDTH_INCHES
    col_w = (width - 0.8) / ncol
    height = col_w * (map_h + sec_h) + 1.55
    fig = plt.figure(figsize=(width, height))
    gs = fig.add_gridspec(2, ncol, height_ratios=[map_h, sec_h], hspace=0.42, wspace=0.10,
                          left=0.075, right=0.99, top=1 - 0.42 / height, bottom=0.95 / height)
    hx, hy = _tick(VIEW['east'][1] - VIEW['east'][0]), _tick(VIEW['north'][1] - VIEW['north'][0])
    hz = _tick(VIEW['depth'][1] - VIEW['depth'][0])
    star = None
    if STAR:
        sx, sy = horiz_km({'longitude': np.array(STAR[0]), 'latitude': np.array(STAR[1])})
        star = (float(sx), float(sy), float(sx * math.cos(theta) + sy * math.sin(theta)), STAR[2])
    mappable = None
    for k, (p, (m, sec)) in enumerate(zip(pops, grids)):
        name = SHORT_LABELS.get(p['key'], p['label'])
        for row, (ub, vb, h, outside) in enumerate((m, sec)):
            ax = fig.add_subplot(gs[row, k])
            mappable = ax.pcolormesh(ub, vb, h, cmap=DENSITY_CMAP, norm=norm, rasterized=True)
            ax.set_facecolor('#fbfbfb')
            if row == 0:
                ax.set_xlim(*VIEW['east']); ax.set_ylim(*VIEW['north']); ax.set_aspect('equal')
                ax.xaxis.set_major_locator(MultipleLocator(hx)); ax.yaxis.set_major_locator(MultipleLocator(hy))
                if star:
                    _star(ax, star[0], star[1])
                note = f'n = {len(p["rows"]):,}' + (f'\n{outside:,} outside view' if outside else '')
                ax.text(.97, .96, note, transform=ax.transAxes, ha='right', va='top', fontsize=5.8,
                        color='#333333', linespacing=1.15,
                        bbox={'fc': 'white', 'ec': 'none', 'alpha': .85, 'pad': 1.0})
                ax.set_xlabel('east (km)', labelpad=1.5)
                ylabel = 'north (km)'
                panel_label(ax, 'abcdefgh'[k], name)
            else:
                ax.set_xlim(*VIEW['along']); ax.set_ylim(VIEW['depth'][1], VIEW['depth'][0])
                ax.xaxis.set_major_locator(MultipleLocator(hx)); ax.yaxis.set_major_locator(MultipleLocator(hz))
                ax.axhline(0, color='#9a9a9a', lw=.5, zorder=0)
                if star:
                    _star(ax, star[2], star[3])
                ax.set_xlabel('along major axis (km)', labelpad=1.5)
                ylabel = DEPTH_LABEL
                panel_label(ax, 'abcdefghijklmnop'[ncol + k], '')
            if k == 0:
                ax.set_ylabel(ylabel)
            else:
                ax.tick_params(labelleft=False)
    cax = fig.add_axes([0.32, 0.30 / height, 0.36, 0.09 / height])
    cb = fig.colorbar(mappable, cax=cax, orientation='horizontal')
    cb.set_label(f'events per {BIN_KM:g} × {BIN_KM:g} km cell', fontsize=6.3, labelpad=1.5)
    cb.outline.set_linewidth(.4)
    cb.set_ticks([t for t in (1, 3, 10, 30, 100, 300, 1000) if t <= vmax])
    cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
    cb.ax.xaxis.set_minor_locator(NullLocator())
    cax.tick_params(labelsize=6, length=2)
    fig.text(0.5, 1 - 0.14 / height, title, ha='center', va='top', fontsize=8.5)
    style.save_figure(fig, stem)
    plt.close(fig)


def fig_spatial(out, pops):
    spatial_grid([p for p in pops if p['key'] not in SPATIAL_EXCLUDE], out / '01_reproduction_spatial_comparison',
                 f'{TITLE} — where each catalog places the sequence')


def _ccdf(ax, values, color, label, linestyle='-'):
    v = np.sort(np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float))
    if not len(v):
        return
    ax.step(v, np.arange(len(v), 0, -1), where='post', color=color, label=label,
            linestyle=linestyle, linewidth=1.3)


def fig_diagnostics(out, pops):
    """(a) magnitude-frequency, (b) depth CDF, (c) cumulative events with time."""
    fig, axes = plt.subplots(1, 3, figsize=(style.WIDTH_INCHES, 2.55),
                             gridspec_kw={'wspace': 0.32, 'left': 0.07, 'right': 0.99,
                                          'top': 0.80, 'bottom': 0.18})
    for rec in pops:
        name = SHORT_LABELS.get(rec['key'], rec['label'])
        kw = dict(color=rec['color'], linestyle=rec.get('linestyle', '-'))
        _ccdf(axes[0], rec['magnitude'], label=None, **kw)
        v = np.sort(rec['depth_km'][np.isfinite(rec['depth_km'])])
        if len(v):
            axes[1].plot(v, np.linspace(0, 1, len(v)), lw=1.3, **kw)
        hours = np.sort(rec['hour'][np.isfinite(rec['hour'])])
        axes[2].step(hours, np.arange(1, len(hours) + 1), where='post', lw=1.3, label=name, **kw)
    axes[0].set_yscale('log')
    axes[0].set_xlim(*MAG_XLIM)
    axes[0].set_xlabel('magnitude m')
    axes[0].set_ylabel('events with magnitude ≥ m')
    panel_label(axes[0], 'a', 'Magnitude–frequency')
    axes[1].set_xlim(*VIEW['depth'])
    axes[1].set_ylim(0, 1)
    axes[1].set_xlabel(DEPTH_LABEL)
    axes[1].set_ylabel('fraction of events ≤ depth')
    panel_label(axes[1], 'b', 'Depth distribution')
    axes[2].set_xlim(0, (W1 - W0).total_seconds() / 3600)
    if TIME_MARK:
        h = (parse_time(TIME_MARK[1]) - W0).total_seconds() / 3600
        axes[2].axvline(h, color='#555555', lw=.7, ls=':')
        axes[2].text(h, .97, f' {TIME_MARK[0]}', transform=axes[2].get_xaxis_transform(), fontsize=6,
                     va='top', ha='left', color='#333333')
    axes[2].set_xlabel(f'hours since {W0:%Y-%m-%d %H:%M} UTC')
    axes[2].set_ylabel('cumulative events')
    axes[2].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    panel_label(axes[2], 'c', 'Cumulative detections')
    for ax in axes:
        ax.grid(True, color='#e6e6e6', lw=.5, zorder=0)
        ax.set_axisbelow(True)
    # every population has times; not all carry magnitudes
    handles, labels = axes[2].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=len(labels), frameon=False, fontsize=6.8,
               bbox_to_anchor=(0.5, 0.995), handlelength=1.8, columnspacing=1.6)
    style.save_figure(fig, out / '02_reproduction_population_diagnostics')
    plt.close(fig)


def fig_correspondence(out, pops, focus_agent, stem='03_agent_reference_correspondence'):
    """Matched-pair diagnostics for the focus agent population."""
    focus = next((p for p in pops if p['key'] == focus_agent), None)
    if focus is None:
        return False
    by_key = {p['key']: p for p in pops}
    expert = by_key['expert']
    fig, axes = plt.subplots(1, 4, figsize=(style.WIDTH_INCHES, 2.6))
    name = SHORT_LABELS.get(focus_agent, focus['label'])

    pairs_e = match(focus, expert)
    axes[0].hist([dt for _, _, _, dt in pairs_e], bins=np.linspace(0, DT_MAX_S, 21),
                 color=focus['color'], edgecolor='black', linewidth=.4)
    axes[0].set_xlabel('|Δ origin time| vs expert (s)')
    axes[0].set_ylabel('pairs')
    panel_label(axes[0], 'a', f'|Δt| ({name} vs expert)')

    others = ['expert'] + SECONDARY
    groups = [match(focus, by_key[k]) for k in others]
    x = np.arange(len(others))
    axes[1].bar(x - .18, [q([d for _, _, d, _ in g], 50) or 0 for g in groups], .34, label='p50',
                color=focus['color'], edgecolor='black', linewidth=.4)
    axes[1].bar(x + .18, [q([d for _, _, d, _ in g], 90) or 0 for g in groups], .34, label='p90',
                color='#999999', edgecolor='black', linewidth=.4)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(others)
    axes[1].set_ylabel('epicentral difference (km)')
    axes[1].legend(fontsize=6)
    panel_label(axes[1], 'b', 'Epicentral difference')

    em = np.array([expert['rows'][j]['magnitude'] for _, j, _, _ in pairs_e], dtype=float)
    am = np.array([focus['rows'][i]['magnitude'] for i, _, _, _ in pairs_e], dtype=float)
    ok = np.isfinite(em) & np.isfinite(am)
    axes[2].plot(em[ok], am[ok] - em[ok], '.', ms=1.5, color=focus['color'], rasterized=True)
    order = np.argsort(em[ok])
    xs, ys = em[ok][order], (am[ok] - em[ok])[order]
    run, runx = [], []
    for xv in np.arange(MAG_XLIM[0], MAG_XLIM[1] + .01, .25):
        sel = np.abs(xs - xv) <= .5
        if sel.sum() >= 10:
            run.append(np.median(ys[sel]))
            runx.append(xv)
    axes[2].plot(runx, run, color='black', lw=1.2, label='running median')
    axes[2].axhline(0, color='#555555', lw=.6, ls=':')
    axes[2].set_xlabel('expert magnitude')
    axes[2].set_ylabel('Δ magnitude')
    axes[2].legend(fontsize=6)
    panel_label(axes[2], 'c', 'Magnitude bias')

    primary = by_key[PRIMARY]
    pairs_p = match(focus, primary)
    ad = np.array([focus['rows'][i]['depth_km'] for i, _, _, _ in pairs_p], dtype=float)
    rd = np.array([primary['rows'][j]['depth_km'] for _, j, _, _ in pairs_p], dtype=float)
    ok = np.isfinite(ad) & np.isfinite(rd)
    lim = VIEW['depth']
    axes[3].plot(rd[ok], ad[ok], '.', ms=1.5, color=focus['color'], rasterized=True)
    axes[3].plot(lim, lim, color='black', lw=.8)
    axes[3].set_xlim(*lim)
    axes[3].set_ylim(*lim)
    axes[3].set_xlabel(f'{SHORT_LABELS[PRIMARY]} depth (km)')
    axes[3].set_ylabel(f'{name} depth (km)')
    panel_label(axes[3], 'd', f'Depth vs depth ({PRIMARY})')
    fig.tight_layout()
    style.save_figure(fig, out / stem)
    plt.close(fig)
    return True


# --- entry point ---

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=TASK / 'evaluation')
    args = parser.parse_args()
    out = args.out_dir

    populations, inputs = load_populations()
    base = [p for p in populations if p['key'] in REFS or p['key'] == 'expert']
    runs = [p for p in populations if p['key'] in AGENT_RUNS]
    stats = compute_stats(populations)
    with style.publication_style():
        expert_figures = out / 'expert' / 'figures'
        expert_figures.mkdir(parents=True, exist_ok=True)
        fig_spatial(expert_figures, base)
        fig_diagnostics(expert_figures, base)
        for run in runs:
            figures = out / 'agents' / run['key'] / 'figures'
            figures.mkdir(parents=True, exist_ok=True)
            fig_spatial(figures, base + [run])
            fig_diagnostics(figures, base + [run])
            fig_correspondence(figures, base + [run], run['key'])
        if runs:
            comparison = out / 'comparison' / 'figures'
            comparison.mkdir(parents=True, exist_ok=True)
            fig_spatial(comparison, populations)
            fig_diagnostics(comparison, populations)

    for p in populations:
        if p['key'] in stats:
            v = stats[p['key']]['versus']
            print(f"{p['key']}: {len(p['rows']):,} events; " + '; '.join(
                f"vs {k} {e['matched']:,} (R {e['recall']:.1%}, epi {e['median_epicentral_km'] or 0:.2f} km)"
                for k, e in v.items()))


if __name__ == '__main__':
    main()
