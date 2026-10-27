#!/usr/bin/env python3
"""Compare the Magna expert catalog, published reference catalogs, and agent runs.

Populations, all inside the evaluation window [2020-03-18T00:00Z, 2020-03-26T00:00Z)
and gated by the expert cohort mask (``expert/00_config/validation.yaml``;
masked counts are hard asserts, as in expert stage 05):

  pang   Pang et al. (2020) GL089798 relocated catalog
  baker  Baker & Whidden (2021) pick set collapsed to events
  uuss   UUSS/ComCat operational benchmark
  expert this repository's expert workflow, round catalog r7 (r6 + Match&Locate)
  agent_* completed agent runs (``AGENT_RUNS``; extend as arms complete)

Outputs (evaluation/):
  figures/01_reproduction_spatial_comparison      maps + population bar
  figures/02_reproduction_population_diagnostics  magnitude CCDF, depth CDF,
                                                  hourly rates
  figures/03_agent_reference_correspondence       matched-pair diagnostics
                                                  (per-run, via evaluate_run.py)
  match_statistics.json                           populations, provenance,
                                                  matcher criteria, pair stats

The reference readers are ports of the expert stage-05 readers
(``expert/04_comparison/05_match_references.py``, pandas-based there) so the
evaluation layer stays stdlib+numpy+matplotlib; any reader fix must be made
in both places. Event correspondence: greedy one-to-one pairing by
(distance, dt) within |dt| <= 4 s and epicentral separation <= 15 km —
the same gates as the expert primary matcher and the Ridgecrest evaluation.
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
CASE = TASK.parents[2] / 'data' / '2020_magna_utah'
STYLE = CASE / 'scripts' / 'figures' / 'figure_style.py'

spec = importlib.util.spec_from_file_location('magna_figure_style', STYLE)
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)

# Colors: the references keep the case's stage-05 colors; the expert and
# agent slots reuse the Ridgecrest evaluation palette so cross-case figures
# read the same way (Okabe-Ito; see evaluation/README.md).
COLORS = {'pang': '#0072B2', 'baker': '#D55E00', 'uuss': '#009E73'}
EXPERT_COLOR = '#E69F00'
AGENT_TOOLS_COLOR = '#56B4E9'
AGENT_MIN_COLOR = '#F0E442'
SHORT_LABELS = {
    'pang': 'Pang et al. 2020', 'baker': 'Baker et al. 2021', 'uuss': 'UUSS / ComCat',
    'expert': 'Expert', 'agent_min': 'Agent min', 'agent_tools': 'Agent tools',
}
# Depth datums: only sea-level pairs enter depth-difference statistics.
DATUMS = {'pang': 'sea_level', 'baker': 'unspecified_relocated',
          'uuss': 'sea_level', 'expert': 'sea_level'}

# Expert population = a complete round catalog (all rows). r6 is the stage-10
# NLL catalog (DD a separate layer); r7 = r6 with DD positions where relocated
# plus the Match&Locate events of stage 60 (export/r7/60_match_locate/full/
# catalog). r8 = r7 rebuilt on the stage-45 depth prior (weak NLL events
# re-weighted toward the sequence depth, DD rerun, M&L events shifted with
# their templates; export/r8/60_catalog). Rounds are explicit so that stage 60
# can keep scoring against r6.
EXPERT_ROUNDS = {
    'r6': (TASK / 'expert/export/r6/10_validate_catalog/events.csv', 'origin_time', 'depth_below_sea_level_km'),
    'r7': (TASK / 'expert/export/r7/60_match_locate/full/catalog/r6_plus_ml_events.csv', 'origin_time_utc',
           'depth_bsl_km'),
    'r8': (TASK / 'expert/export/r8/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),
    'r11': (TASK / 'expert/export/r11/60_catalog/catalog_events.csv', 'origin_time_utc', 'depth_bsl_km'),  # stages 65/67 (2026-10-28)
}
EXPERT_ROUND = 'r11'
SHORT_LABELS['expert'] = f'Expert ({EXPERT_ROUND})'
EXPERT_CATALOG = EXPERT_ROUNDS[EXPERT_ROUND][0]

AGENT_RUNS = {
    # 'agent_tools': {
    #     'label': 'Agent tools', 'color': AGENT_TOOLS_COLOR,
    #     'catalog': TASK / 'runs/tools/claude/glm-5.3/<RUN_ID>/work/catalog.csv',
    #     'run_id': 'runs/tools/claude/glm-5.3/<RUN_ID>',
    # },
}
FOCUS_AGENT = 'agent_tools'

DT_MAX_S = 4.0
D_MAX_KM = 15.0

MASK = yaml.safe_load((TASK / 'expert' / '00_config' / 'validation.yaml').read_text())
W0 = datetime.fromisoformat(MASK['window']['start_utc'].replace('Z', '+00:00'))
W1 = datetime.fromisoformat(MASK['window']['end_utc'].replace('Z', '+00:00'))
ANCHOR = json.loads((CASE / 'analysis' / 'mainshock_anchor.json').read_text())['anchor']


def parse_time(text):
    text = text.strip().replace('Z', '').replace(' ', 'T')
    # Python 3.9 fromisoformat rejects >6-digit fractional seconds; clamp them.
    text = re.sub(r'\.(\d{6})\d+', r'.\g<1>', text)
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mask_row(r):
    return (W0 <= r['time'] < W1
            and MASK['region']['latitude_bounds'][0] <= r['latitude'] <= MASK['region']['latitude_bounds'][1]
            and MASK['region']['longitude_bounds'][0] <= r['longitude'] <= MASK['region']['longitude_bounds'][1]
            and r['depth_km'] is not None
            and MASK['depth_bounds_sea_level_km'][0] <= r['depth_km'] <= MASK['depth_bounds_sea_level_km'][1])


# --- reference readers (ports of expert stage 05; see module docstring) ---

def read_pang(path):
    """Whitespace rows: date time lat lon dep Mc eid [type]; seconds may be non-canonical."""
    rows = []
    noncanonical = 0
    row_re = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\S+)\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+(\S+)')
    canonical = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{1,3}$')
    for line in path.read_text().splitlines():
        m = row_re.match(line.strip())
        if not m:
            continue
        date, hh, mm, ss, lat, lon, dep, mag, eid = m.groups()
        if not canonical.fullmatch(f'{hh}:{mm}:{ss}'):
            noncanonical += 1
        t = datetime.fromisoformat(f'{date}T{hh}:{mm}').replace(tzinfo=timezone.utc) \
            + timedelta(seconds=float(ss))
        magnitude = float(mag)
        rows.append({'time': t, 'latitude': float(lat), 'longitude': float(lon),
                     'depth_km': float(dep),
                     'magnitude': None if magnitude <= -4 else magnitude,  # sentinels
                     'reference_id': str(int(float(eid)))})
    return rows, noncanonical


def read_baker(path):
    """Pick-level CSV collapsed to one row per event (first row per event_number)."""
    rows, seen = [], set()
    with open(path, newline='') as fh:
        for r in _csv.DictReader(fh):
            n = r['event_number']
            if n in seen:
                continue
            seen.add(n)
            rows.append({'time': parse_time(r['origin_time']),
                         'latitude': _f(r['event_latitude']),
                         'longitude': _f(r['event_longitude']),
                         'depth_km': _f(r['event_depth']),
                         'magnitude': _f(r['magnitude']), 'reference_id': f'bak_{n}'})
    return rows


def read_uuss(path):
    rows = []
    with open(path, newline='') as fh:
        for r in _csv.DictReader(fh):
            if r['type'] != 'earthquake':
                continue
            rows.append({'time': parse_time(r['time']), 'latitude': _f(r['latitude']),
                         'longitude': _f(r['longitude']), 'depth_km': _f(r['depth']),
                         'magnitude': _f(r['mag']), 'reference_id': r['id']})
    return rows


READERS = {'pang': read_pang, 'baker': read_baker, 'uuss': read_uuss}


def read_catalog(path, time_col, depth_col='depth_km', keep=None):
    """Generic catalog reader (expert events.csv, agent catalog.csv)."""
    rows = []
    with open(path, newline='') as fh:
        for r in _csv.DictReader(fh):
            if keep is not None and not keep(r):
                continue
            rows.append({'time': parse_time(r[time_col]), 'latitude': _f(r.get('latitude')),
                         'longitude': _f(r.get('longitude')), 'depth_km': _f(r.get(depth_col)),
                         'magnitude': _f(r.get('magnitude'))})
    rows = [r for r in rows if W0 <= r['time'] < W1]
    rows.sort(key=lambda r: r['time'])
    return rows


def as_record(key, label, color, rows, datum=None, linestyle='-'):
    rec = {'key': key, 'label': label, 'color': color, 'rows': rows,
           'linestyle': linestyle, 'datum': datum or DATUMS.get(key)}
    for field in ('latitude', 'longitude', 'depth_km', 'magnitude'):
        rec[field] = np.array([r[field] if r[field] is not None else np.nan for r in rows])
    rec['hour'] = np.array([(r['time'] - W0).total_seconds() / 3600 for r in rows])
    return rec


def load_references():
    """Masked reference cohorts; counts are hard asserts (validation.yaml)."""
    populations, inputs = [], {}
    for name, spec_ in MASK['references'].items():
        path = (CASE / spec_['path']).resolve()
        if name == 'pang':
            rows, noncanonical = read_pang(path)
        else:
            rows, noncanonical = READERS[name](path), 0
        rows = [r for r in rows if _mask_row(r)]
        # Chronological order is required by the bisect-based matcher; the
        # source files are mostly but not reliably sorted (UUSS/ComCat rows
        # follow ComCat update order, Baker follows event_number).
        rows.sort(key=lambda r: r['time'])
        expected = MASK['expected_reference_counts'][name]
        assert len(rows) == expected, f'{name}: {len(rows)} masked rows != gate {expected}'
        populations.append(as_record(name, spec_['label'], COLORS[name], rows))
        inputs[name] = {'path': spec_['path'], 'plotted_records': len(rows)}
        if name == 'pang':
            inputs[name]['noncanonical_seconds_rows_absorbed'] = noncanonical
    return populations, inputs


def load_expert(round_=EXPERT_ROUND):
    # Complete round catalog (all rows, quality flags intact) — the same
    # convention as stage 05's headline matched fractions and symmetric with
    # an agent catalog, which also carries uncertain rows. The curated v1
    # subset lives in the round reports (expert/export/r*/05_match_references).
    path, time_col, depth_col = EXPERT_ROUNDS[round_]
    rows = read_catalog(path, time_col, depth_col=depth_col)
    if not rows:
        raise ValueError(f'No expert rows in window: {path}')
    rec = as_record('expert', f'Expert reproduction ({round_})', EXPERT_COLOR, rows)
    return rec, {'path': str(path.relative_to(TASK)), 'round': round_, 'plotted_records': len(rows),
                 'selection': 'complete round catalog (all rows)'}


def agent_run_style(key):
    color = AGENT_RUNS.get(key, {}).get('color', AGENT_TOOLS_COLOR)
    if key == 'agent_min':
        # Yellow is the only free Okabe-Ito slot but sits next to the expert
        # orange on the deutan confusion axis; disambiguate lines.
        return color, (0, (4, 2, 1, 2))
    return color, '-'


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
        rec = as_record(key, meta['label'], color, rows, datum=None, linestyle=linestyle)
        populations.append(rec)
        inputs[key] = {'path': str(meta['catalog'].relative_to(TASK)),
                       'plotted_records': len(rows), 'run_id': meta['run_id']}
    return populations, inputs


# --- correspondence ---

def km(dla, dlo, lat):
    return math.hypot(dla * 111.195, dlo * 111.195 * math.cos(math.radians(lat)))


def match(rec_a, rec_b):
    """Greedy one-to-one pairing by (distance, dt) within the criteria."""
    times = [r['time'] for r in rec_b['rows']]
    cand = []
    for i, ra in enumerate(rec_a['rows']):
        lo = bisect.bisect_left(times, ra['time'] - timedelta(seconds=DT_MAX_S))
        hi = bisect.bisect_right(times, ra['time'] + timedelta(seconds=DT_MAX_S))
        for jj in range(lo, hi):
            rb = rec_b['rows'][jj]
            if ra['latitude'] is None or ra['longitude'] is None or \
                    rb['latitude'] is None or rb['longitude'] is None:
                continue  # unlocated rows never enter correspondence
            dt = abs((rb['time'] - ra['time']).total_seconds())
            d = km(ra['latitude'] - rb['latitude'], ra['longitude'] - rb['longitude'], ra['latitude'])
            if dt <= DT_MAX_S and d <= D_MAX_KM:
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
    return float(np.nanpercentile(np.asarray(arr, dtype=float), p)) if len(arr) else None


def compute_stats(pops, focus_agent=None):
    refs = {'pang', 'baker', 'uuss'}
    stats = {}
    for p in pops:
        if p['key'] in refs:
            continue
        versus = {}
        for other in pops:
            if other['key'] == p['key']:
                continue
            pairs = match(p, other)
            entry = {
                'matched': len(pairs),
                'precision': len(pairs) / len(p['rows']) if p['rows'] else None,
                'recall': len(pairs) / len(other['rows']) if other['rows'] else None,
                'median_abs_dt_s': q([dt for _, _, _, dt in pairs], 50),
                'median_epicentral_km': q([d for _, _, d, _ in pairs], 50),
            }
            if p['datum'] == 'sea_level' and other['datum'] == 'sea_level':
                dz = [p['rows'][i]['depth_km'] - other['rows'][j]['depth_km']
                      for i, j, _, _ in pairs]
                entry['median_depth_difference_km'] = q(dz, 50)
                entry['mad_depth_difference_km'] = q(
                    [abs(v - entry['median_depth_difference_km']) for v in dz], 50)
            versus[other['key']] = entry
        stats[p['key']] = {'records': len(p['rows']), 'versus': versus}
    return stats


# --- figures ---
# Spatial figures work in km about the mainshock (east, north, along strike,
# depth below sea level). Each catalog gets its own column (small multiples on
# shared axes and one shared colour scale) and is drawn as a 2-D event-count
# density: thousands of overlapping dots hide structure, a density does not.
# Events outside the shared view are counted in the column header.

LON0, LAT0 = ANCHOR['longitude'], ANCHOR['latitude']
VIEW = {'east': (-6.0, 10.0), 'north': (-6.0, 6.0), 'along': (-10.0, 6.0), 'depth': (-2.0, 14.0)}
BIN_KM = 0.25
DENSITY_CMAP = LinearSegmentedColormap.from_list('density', ['#d4e3f2', '#6a9fd1', '#1f5a99', '#08254d'])
DENSITY_CMAP.set_bad(alpha=0)
SECTION_LABELS = {'baker': 'depth datum differs (not comparable)'}
MAG_SENTINEL = -3.0   # Baker carries -10 for events without magnitude


def panel_label(ax, letter, title):
    ax.set_title(title, loc='left', fontsize=7.5, pad=3)
    ax.text(-0.02, 1.0, letter, transform=ax.transAxes, fontsize=9, fontweight='bold',
            va='bottom', ha='right')


def horiz_km(rec):
    return ((rec['longitude'] - LON0) * 111.195 * math.cos(math.radians(LAT0)),
            (rec['latitude'] - LAT0) * 111.195)


def strike_angle(rec):
    """Sequence axis = major axis of the reference's horizontal distribution."""
    x, y = horiz_km(rec)
    ok = np.isfinite(x) & np.isfinite(y)
    evals, evecs = np.linalg.eigh(np.cov(np.stack([x[ok], y[ok]])))
    v = evecs[:, np.argmax(evals)]
    if v[0] > 0:            # point the axis westward so the label reads N..W
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


def spatial_grid(pops, stem, title):
    """Row 1: map density; row 2: along-strike depth section; one column per catalog."""
    theta = strike_angle(next(p for p in pops if p['key'] == 'pang'))
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
    mappable = None
    for k, (p, (m, sec)) in enumerate(zip(pops, grids)):
        name = SHORT_LABELS.get(p['key'], p['label'])
        for row, (ub, vb, h, outside) in enumerate((m, sec)):
            ax = fig.add_subplot(gs[row, k])
            mappable = ax.pcolormesh(ub, vb, h, cmap=DENSITY_CMAP, norm=norm, rasterized=True)
            ax.set_facecolor('#fbfbfb')
            if row == 0:
                ax.set_xlim(*VIEW['east']); ax.set_ylim(*VIEW['north']); ax.set_aspect('equal')
                ax.yaxis.set_major_locator(MultipleLocator(2)); ax.xaxis.set_major_locator(MultipleLocator(5))
                _star(ax, 0, 0)
                note = f'n = {len(p["rows"]):,}' + (f'\n{outside:,} outside view' if outside else '')
                ax.text(.97, .96, note, transform=ax.transAxes, ha='right', va='top', fontsize=5.8,
                        color='#333333', linespacing=1.15,
                        bbox={'fc': 'white', 'ec': 'none', 'alpha': .85, 'pad': 1.0})
                ax.set_xlabel('east (km)', labelpad=1.5)
                ylabel = 'north (km)'
                panel_label(ax, 'abcdefgh'[k], name)
            else:
                ax.set_xlim(*VIEW['along']); ax.set_ylim(VIEW['depth'][1], VIEW['depth'][0])
                ax.xaxis.set_major_locator(MultipleLocator(5)); ax.yaxis.set_major_locator(MultipleLocator(5))
                ax.axhline(0, color='#9a9a9a', lw=.5, zorder=0)
                _star(ax, 0, ANCHOR['depth_km'])
                if p['key'] in SECTION_LABELS:
                    ax.text(.5, .95, SECTION_LABELS[p['key']], transform=ax.transAxes, ha='center',
                            va='top', fontsize=5.6, color='#7a3b00')
                ax.set_xlabel('along strike (km)', labelpad=1.5)
                ylabel = 'depth bsl (km)'
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
    spatial_grid(pops, out / '01_reproduction_spatial_comparison',
                 '2020 Magna, Utah — where each catalog places the sequence')


def _ccdf(ax, values, color, label, linestyle='-'):
    v = np.sort(np.asarray([x for x in values if x is not None and np.isfinite(x) and x > MAG_SENTINEL],
                           dtype=float))
    if not len(v):
        return
    ax.step(v, np.arange(len(v), 0, -1), where='post', color=color, label=label,
            linestyle=linestyle, linewidth=1.3)


def fig_diagnostics(out, pops):
    """(a) magnitude-frequency, (b) depth CDF, (c) cumulative events with time."""
    fig, axes = plt.subplots(1, 3, figsize=(style.WIDTH_INCHES, 2.55),
                             gridspec_kw={'wspace': 0.32, 'left': 0.07, 'right': 0.99,
                                          'top': 0.80, 'bottom': 0.18})
    t_main = (parse_time(ANCHOR['time_utc']) - W0).total_seconds() / 3600
    for rec in pops:
        name = SHORT_LABELS.get(rec['key'], rec['label'])
        kw = dict(color=rec['color'], linestyle=rec.get('linestyle', '-'))
        _ccdf(axes[0], rec['magnitude'], label=name, **kw)
        v = np.sort(rec['depth_km'][np.isfinite(rec['depth_km'])])
        if len(v):
            axes[1].plot(v, np.linspace(0, 1, len(v)), lw=1.3, **kw)
        hours = np.sort(rec['hour'][np.isfinite(rec['hour'])])
        axes[2].step(hours, np.arange(1, len(hours) + 1), where='post', lw=1.3, **kw)
    axes[0].set_yscale('log')
    axes[0].set_xlim(-1.5, 5.8)
    axes[0].set_xlabel('magnitude m')
    axes[0].set_ylabel('events with magnitude ≥ m')
    panel_label(axes[0], 'a', 'Magnitude–frequency')
    axes[1].set_xlim(-2, 15)
    axes[1].set_ylim(0, 1)
    axes[1].set_xlabel('depth below sea level (km)')
    axes[1].set_ylabel('fraction of events ≤ depth')
    panel_label(axes[1], 'b', 'Depth distribution')
    axes[1].text(.03, .95, 'Baker: depth datum differs', transform=axes[1].transAxes, fontsize=5.8,
                 va='top', color='#7a3b00')
    axes[2].axvline(t_main, color='#555555', lw=.6, ls=':')
    axes[2].text(t_main + 3, 0.97, 'M 5.7 mainshock', transform=axes[2].get_xaxis_transform(),
                 fontsize=5.8, color='#555555', va='top')
    axes[2].set_xlim(0, (W1 - W0).total_seconds() / 3600)
    axes[2].set_xlabel('hours since 2020-03-18 00:00 UTC')
    axes[2].set_ylabel('cumulative events')
    axes[2].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    panel_label(axes[2], 'c', 'Cumulative detections')
    for ax in axes:
        ax.grid(True, color='#e6e6e6', lw=.5, zorder=0)
        ax.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=len(labels), frameon=False, fontsize=6.8,
               bbox_to_anchor=(0.5, 0.995), handlelength=1.8, columnspacing=1.6)
    style.save_figure(fig, out / '02_reproduction_population_diagnostics')
    plt.close(fig)


def fig_correspondence(out, pops, focus_agent=FOCUS_AGENT,
                       stem='03_agent_reference_correspondence'):
    """Matched-pair diagnostics for the focus agent population."""
    focus = next((p for p in pops if p['key'] == focus_agent), None)
    if focus is None:
        return False
    expert = next(p for p in pops if p['key'] == 'expert')
    pang = next(p for p in pops if p['key'] == 'pang')
    uuss = next(p for p in pops if p['key'] == 'uuss')
    fig, axes = plt.subplots(1, 4, figsize=(style.WIDTH_INCHES, 2.6))

    pairs_e = match(focus, expert)
    axes[0].hist([dt for _, _, _, dt in pairs_e], bins=np.linspace(0, DT_MAX_S, 21),
                 color=focus['color'], edgecolor='black', linewidth=.4)
    axes[0].set_xlabel('|Δ origin time| vs expert (s)')
    axes[0].set_ylabel('pairs')
    panel_label(axes[0], 'a', f'|Δt| ({SHORT_LABELS.get(focus_agent, focus_agent)} vs expert)')

    groups = [match(focus, other) for other in (expert, pang, uuss)]
    labels = ['expert', 'pang', 'uuss']
    p50 = [q([d for _, _, d, _ in g], 50) for g in groups]
    p90 = [q([d for _, _, d, _ in g], 90) for g in groups]
    x = np.arange(3)
    axes[1].bar(x - .18, p50, .34, label='p50', color=focus['color'],
                edgecolor='black', linewidth=.4)
    axes[1].bar(x + .18, p90, .34, label='p90', color='#999999',
                edgecolor='black', linewidth=.4)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)
    axes[1].set_ylabel('epicentral difference (km)')
    axes[1].legend(fontsize=6)
    panel_label(axes[1], 'b', 'Epicentral difference')

    em = np.array([expert['rows'][j]['magnitude'] for _, j, _, _ in pairs_e], dtype=float)
    am = np.array([focus['rows'][i]['magnitude'] for i, _, _, _ in pairs_e], dtype=float)
    ok = np.isfinite(em) & np.isfinite(am)
    axes[2].plot(em[ok], am[ok] - em[ok], '.', ms=1.5, color=focus['color'],
                 rasterized=True)
    order = np.argsort(em[ok])
    xs, ys = em[ok][order], (am[ok] - em[ok])[order]
    run, runx = [], []
    for xv in np.arange(1.0, 4.01, .25):
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

    pairs_p = match(focus, pang)
    ad = np.array([focus['rows'][i]['depth_km'] for i, _, _, _ in pairs_p], dtype=float)
    rd = np.array([pang['rows'][j]['depth_km'] for _, j, _, _ in pairs_p], dtype=float)
    ok = np.isfinite(ad) & np.isfinite(rd)
    lim = (-4, 16)
    axes[3].plot(rd[ok], ad[ok], '.', ms=1.5, color=focus['color'], rasterized=True)
    axes[3].plot(lim, lim, color='black', lw=.8)
    axes[3].set_xlim(*lim)
    axes[3].set_ylim(*lim)
    axes[3].set_xlabel('pang depth (km bsl)')
    axes[3].set_ylabel(f'{SHORT_LABELS.get(focus_agent, focus_agent)} depth (km)')
    panel_label(axes[3], 'd', 'Depth vs depth (pang)')
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
    figures = out / 'figures'
    figures.mkdir(parents=True, exist_ok=True)

    populations, inputs = load_populations()
    stats = compute_stats(populations, focus_agent=FOCUS_AGENT)
    with style.publication_style():
        fig_spatial(figures, populations)
        fig_diagnostics(figures, populations)
        wrote = fig_correspondence(figures, populations)

    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'evaluation_window': {'start_utc': MASK['window']['start_utc'],
                              'end_utc': MASK['window']['end_utc']},
        'matching': {'dt_max_s': DT_MAX_S, 'd_max_km': D_MAX_KM,
                     'method': 'greedy one-to-one by (distance, dt)'},
        'populations': {p['key']: {'label': p['label'], 'records': len(p['rows']),
                                   'color': p['color'], 'depth_datum': p['datum']}
                        for p in populations},
        'inputs': inputs,
        'statistics': stats,
    }
    (out / 'match_statistics.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for p in populations:
        if p['key'] in stats:
            v = stats[p['key']]['versus']
            print(f"{p['key']}: {len(p['rows']):,} events; " + '; '.join(
                f"vs {k} {e['matched']:,} (R {e['recall']:.1%})" for k, e in v.items()))
    if not wrote:
        print('correspondence figure skipped (no focus agent run registered)')


if __name__ == '__main__':
    main()
