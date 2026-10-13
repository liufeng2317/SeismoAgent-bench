#!/usr/bin/env python3
"""Plot the Kaikoura station set and the in-window anchor.

Station positions are the median of in-window channel-epoch coordinates in
`station_inventory.json` (same policy as the Ridgecrest station figure); the
selection is the 53 full-window stations of the availability probe, drawn from
the Lanza et al. (2019) Table S1 manifest. Panel a is a regional overview
auto-fitted to the stations, panel b zooms on the Cape Campbell area hosting
the STREWN deployment and most of the aftershocks. Local geographical
approximation, no basemap.
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import numpy as np

from figure_style import WIDTH_INCHES, publication_style, save_figure

CASE = Path(__file__).resolve().parents[2]
ROOT = CASE / 'data/waveforms'
OUT = CASE / 'analysis/figures/station_information'
ZOOM = (173.30, 174.85, -42.10, -41.20)
COLORS = {'NZ': '#0072B2', 'Z1': '#D55E00'}
LABELS = {'NZ': 'NZ permanent (44)', 'Z1': 'STREWN temporary (9)'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_points(ax, items, fontsize=5.2):
    """Greedy collision-free label placement in display coordinates."""
    offsets = [(4, 3), (4, -10), (-4, 3), (-4, -10), (6, -3), (-6, -3),
               (0, 6), (0, -12), (8, 2), (-8, 2), (8, -7), (-8, -7), (10, 4), (-10, 4)]
    placed = []
    skipped = []
    for x, y, text in items:
        chosen = None
        for dx, dy in offsets:
            ann = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords='offset points',
                              fontsize=fontsize, ha='left' if dx >= 0 else 'right', zorder=4)
            box = ann.get_window_extent()
            if not any(box.overlaps(other) for other in placed):
                placed.append(box)
                chosen = ann
                break
            ann.remove()
        if chosen is None:
            ann = ax.annotate(text, (x, y), xytext=offsets[0], textcoords='offset points',
                              fontsize=fontsize, zorder=4)
            placed.append(ann.get_window_extent())
            skipped.append(text)
    return skipped


def load_stations():
    manifest = json.loads(
        (ROOT / 'stations/lanza2019_table_s1_station_manifest.json').read_text())
    probe = json.loads((CASE / 'analysis/station_availability_probe.json').read_text())
    full = {s for s, v in probe['stations'].items()
            if not v['missing_days'] and not v['partial_days']}
    epochs = json.loads((ROOT / 'stations/station_inventory.json').read_text())['channel_epochs']
    by_station = {}
    for e in epochs:
        if e['candidate_overlap_seconds'] > 0 and e['latitude'] is not None:
            by_station.setdefault(e['network'] + '.' + e['station'], []).append(
                (e['longitude'], e['latitude']))
    stations = []
    for entry in manifest['stations']:
        if entry['station'] not in full:
            continue
        positions = sorted(set(by_station.get(entry['network_code'] + '.' + entry['station'], [])))
        if not positions:
            raise ValueError(f'No in-window coordinate evidence: {entry["station_id"]}')
        xy = np.median(np.array(positions), axis=0)
        stations.append(dict(id=entry['network_code'] + '.' + entry['station'],
                             longitude=float(xy[0]), latitude=float(xy[1]),
                             category=entry['network_code'],
                             coordinate_variants=positions))
    return manifest, stations


def main():
    manifest, stations = load_stations()
    anchor = json.loads((CASE / 'analysis/mainshock_anchor.json').read_text())
    a = anchor['anchor']
    counts = {k: sum(s['category'] == k for s in stations) for k in COLORS}
    assert counts == {'NZ': 44, 'Z1': 9}, counts

    lons = [s['longitude'] for s in stations] + [a['longitude']]
    lats = [s['latitude'] for s in stations] + [a['latitude']]
    pad_x, pad_y = 0.35, 0.25
    region = (min(lons) - pad_x, max(lons) + pad_x, min(lats) - pad_y, max(lats) + pad_y)

    with publication_style():
        fig, axes = plt.subplots(1, 2, figsize=(WIDTH_INCHES, 4.7),
                                 gridspec_kw={'left': .085, 'right': .98, 'bottom': .22,
                                              'top': .92, 'wspace': .27})
        for i, ax in enumerate(axes):
            box = region if i == 0 else ZOOM
            ax.set_xlim(box[:2]); ax.set_ylim(box[2:])
            ax.set_aspect(1 / np.cos(np.deg2rad(np.mean(box[2:]))))
            dec = lambda bb: 1 if (bb[1] - bb[0]) > 0.5 else 2
            ax.xaxis.set_major_formatter(FuncFormatter(
                lambda x, _: f'{abs(x):.{dec(ax.get_xlim())}f}'))
            ax.yaxis.set_major_formatter(FuncFormatter(
                lambda y, _: f'{abs(y):.{dec(ax.get_ylim())}f}'))
            ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°S)')
            ax.grid(color='#e8e8e8', lw=.45, zorder=0)
            for edge in ('top', 'right'):
                ax.spines[edge].set_visible(True)
            ax.set_title(('a  Downloaded stations', 'b  Cape Campbell / STREWN area')[i],
                         loc='left', pad=10, fontsize=9)
            for station in stations:
                x, y = station['longitude'], station['latitude']
                if not (box[0] <= x <= box[1] and box[2] <= y <= box[3]):
                    continue
                ax.scatter(x, y, s=26 if i else 20, marker='^',
                           facecolors='white' if i else COLORS[station['category']],
                           edgecolors=COLORS[station['category']], linewidths=.85, zorder=3)
            ax.scatter(a['longitude'], a['latitude'], marker='*', s=78, c='#F0C94E',
                       edgecolors='#222222', lw=.7, zorder=5)
            if i:
                ax.annotate(f'M {a["magnitude"]:.1f}', (a['longitude'], a['latitude']),
                            xytext=(-8, -10), textcoords='offset points', ha='right',
                            fontsize=6, zorder=6)
        fig.canvas.draw()
        skipped = label_points(
            axes[1], [(s['longitude'], s['latitude'], s['id'].split('.')[1])
                      for s in stations if ZOOM[0] <= s['longitude'] <= ZOOM[1]
                      and ZOOM[2] <= s['latitude'] <= ZOOM[3]])
        if skipped:
            print(f'Labels placed without collision check: {skipped}')
        axes[0].add_patch(Rectangle((ZOOM[0], ZOOM[2]), ZOOM[1] - ZOOM[0],
                                    ZOOM[3] - ZOOM[2], fill=False, ec='#444444',
                                    lw=.8, ls='--'))
        for ax, km in zip(axes, [100, 20]):
            x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
            x = x0 + .07 * (x1 - x0); y = y0 + .055 * (y1 - y0)
            length = km / (111.195 * np.cos(np.deg2rad(y)))
            ax.plot([x, x + length], [y, y], color='black', lw=1.5)
            ax.text(x + length / 2, y + .025 * (y1 - y0), f'{km} km', ha='center', fontsize=6)
        handles = [Line2D([], [], marker='^', color=COLORS[k], ls='', label=LABELS[k])
                   for k in COLORS]
        handles.append(Line2D([], [], marker='*', mfc='#F0C94E', mec='#222222', ls='',
                              markersize=9,
                              label=f'M {a["magnitude"]:.1f} anchor (largest in window)'))
        fig.legend(handles=handles, ncol=3, loc='lower center', bbox_to_anchor=(.52, .025),
                   frameon=False, fontsize=7, columnspacing=1.6, labelspacing=.9)
        out = OUT / 'station_distribution'
        save_figure(fig, out)
        plt.close(fig)

    manifest_out = dict(
        inputs={str(p.relative_to(CASE)): sha(p) for p in
                [ROOT / 'stations/lanza2019_table_s1_station_manifest.json',
                 CASE / 'analysis/station_availability_probe.json',
                 ROOT / 'stations/station_inventory.json',
                 CASE / 'analysis/mainshock_anchor.json']},
        script_sha256=sha(Path(__file__)),
        counts=counts,
        stations=[{k: s[k] for k in ('id', 'longitude', 'latitude', 'category')}
                  for s in stations],
        semantics='Downloaded-station selection: the 53 full-window stations of the '
                  'availability probe, drawn from the Lanza et al. (2019) Table S1 '
                  'manifest; not waveform coverage itself. Colors give the network of '
                  'origin (NZ permanent, Z1 STREWN temporary). Coordinates are medians '
                  'of in-window channel-epoch positions. The star marks the largest '
                  'in-window event, not the 2016-11-13 M7.8 mainshock, which precedes '
                  'the window.',
        anchor=anchor['anchor'],
        zoom_box=dict(longitude=list(ZOOM[:2]), latitude=list(ZOOM[2:])),
        outputs={p.name: dict(bytes=p.stat().st_size, sha256=sha(p))
                 for p in [out.with_suffix('.png'), out.with_suffix('.pdf')]},
    )
    out.with_suffix('.json').write_text(json.dumps(manifest_out, indent=2) + '\n')
    print(counts)


if __name__ == '__main__':
    main()
