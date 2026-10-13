#!/usr/bin/env python3
"""Read-only sample QC and exploratory preprocessing for the Magna candidate window.

Adapted from the Ridgecrest `analyze_waveform_quality.py`; conventions are the
same (union-of-segments coverage, hourly station matrix, plateau screening,
exploratory bandpass around the mainshock). Per-case changes: window comes from
`processing.yaml`, the mainshock anchor from `analysis/mainshock_anchor.json`,
channel families are EN/EH/HH/HN, and preprocessing stations are the three
nearest 100 Hz verticals to the anchor. Raw files are never modified.
"""
import csv
import json
import math
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from obspy import read, UTCDateTime
from scipy.signal import welch
import yaml

from figure_style import publication_style, save_figure

CASE = Path(__file__).resolve().parents[2]
ROOT = CASE / 'data/waveforms'
OUT = CASE / 'analysis/figures/waveform_quality'
FAMILY_COLORS = [('EN', '#8B4C9D'), ('EH', '#009E73'), ('HH', '#0072B2'), ('HN', '#D55E00')]
PREPROCESS_BAND = (2., 12.)
PREPROCESS_COUNT = 3


def union(intervals):
    result = []
    for a, b in sorted(intervals):
        if b <= a:
            continue
        if result and a <= result[-1][1] + 1e-6:
            result[-1][1] = max(b, result[-1][1])
        else:
            result.append([a, b])
    return result


def longest_run(x):
    if not len(x):
        return 0, 0
    edges = np.r_[0, np.flatnonzero(x[1:] != x[:-1]) + 1, len(x)]
    lengths = np.diff(edges)
    values = x[edges[:-1]]
    extreme = (values == np.min(x)) | (values == np.max(x))
    return int(lengths.max()), int(lengths[extreme].max(initial=0))


def table(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, lineterminator='\n', fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def preprocess_seeds(origin, anchor):
    """Nearest 100 Hz vertical channels to the anchor with anchor-day coverage."""
    inventory = json.loads((ROOT / 'waveform_inventory.json').read_text())
    from obspy.geodetics import gps2dist_azimuth
    candidates = []
    for row in inventory['files']:
        for s in row['streams']:
            if (s['component'] == 'Z' and s['sample_rates_hz'] and
                    min(s['sample_rates_hz']) >= 100.0 and s['candidate_npts'] and
                    UTCDateTime(s['start_utc']) <= origin <= UTCDateTime(s['last_sample_utc'])):
                candidates.append(s)
    inventory_path = ROOT / 'stations/station_inventory.json'
    coords = {}
    for e in json.loads(inventory_path.read_text())['channel_epochs']:
        if e['latitude'] is not None:
            coords.setdefault(e['network'] + '.' + e['station'], (e['longitude'], e['latitude']))
    preferred = {'HH': 0, 'EH': 1, 'HN': 2, 'EN': 3}
    ranked = []
    for s in candidates:
        station = s['network'] + '.' + s['station']
        lon, lat = coords[station]
        distance = gps2dist_azimuth(anchor['latitude'], anchor['longitude'], lat, lon)[0] / 1000
        ranked.append((distance, preferred.get(s['channel'][:2], 9), s['seed_id'],
                       s['network'] + '.' + s['station']))
    ranked.sort()
    return ranked[:PREPROCESS_COUNT]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((CASE / 'analysis/processing.yaml').read_text())
    window = cfg['scientific_design']['candidate_window']
    start, end = (UTCDateTime(window[k]) for k in ('start_utc', 'end_utc'))
    duration = end - start
    anchor = json.loads((CASE / 'analysis/mainshock_anchor.json').read_text())['anchor']
    origin = UTCDateTime(anchor['time_utc'])
    inventory = json.loads((ROOT / 'waveform_inventory.json').read_text())
    files = [r for r in inventory['files'] if r['in_candidate_window']]
    rows, errors = [], []
    spans = defaultdict(list)
    hours = defaultdict(lambda: [0, 0., 0.])
    file_states = []
    for index, record in enumerate(files, 1):
        path = ROOT / record['path']
        before = path.stat()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                st = read(str(path), format='MSEED')
            for seed in sorted({tr.id for tr in st}):
                n = bad = zeros = 0
                total = square = 0.
                peak = flat = plateau = 0.
                rates = set()
                count = 0
                for tr in st.select(id=seed):
                    rate = tr.stats.sampling_rate
                    lo = max(0, min(len(tr), math.ceil((start - tr.stats.starttime) * rate - 1e-7)))
                    hi = max(0, min(len(tr), math.ceil((end - tr.stats.starttime) * rate - 1e-7)))
                    if hi <= lo:
                        continue
                    x = tr.data[lo:hi]
                    a = float(tr.stats.starttime + lo / rate) - float(start)
                    b = a + len(x) / rate
                    spans[seed].append((a, b))
                    rates.add(rate)
                    count += 1
                    finite = np.isfinite(x)
                    bad += int((~finite).sum())
                    zeros += int((x == 0).sum())
                    run, extreme_run = longest_run(x)
                    flat = max(flat, run / rate)
                    plateau = max(plateau, extreme_run / rate)
                    # Double precision avoids integer overflow in energy statistics.
                    y = x[finite].astype(np.float64)
                    n += len(y)
                    total += y.sum()
                    square += np.dot(y, y)
                    peak = max(peak, float(np.max(np.abs(y), initial=0)))
                    for hour in range(max(0, int(a // 3600)), min(int(math.ceil(duration / 3600)), int(b // 3600) + 1)):
                        i = max(0, math.ceil((hour * 3600 - a) * rate - 1e-7))
                        j = min(len(x), math.ceil(((hour + 1) * 3600 - a) * rate - 1e-7))
                        v = x[i:j].astype(np.float64)
                        v = v[np.isfinite(v)]
                        h = hours[seed, hour]
                        h[0] += len(v)
                        h[1] += v.sum()
                        h[2] += np.dot(v, v)
                if n or bad:
                    rows.append(dict(path=record['path'], bytes=before.st_size, seed_id=seed,
                                     rates_hz=';'.join(map(str, sorted(rates))), segments=count,
                                     finite_samples=n, nonfinite_samples=bad, zero_samples=zeros,
                                     mean_counts=total / n if n else 0,
                                     std_counts=np.sqrt(max(0, square / n - (total / n) ** 2)) if n else 0,
                                     peak_abs_counts=peak, longest_constant_s=flat,
                                     longest_segment_extreme_plateau_s=plateau,
                                     decode_warnings=' | '.join(sorted({str(w.message) for w in caught}))))
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError('File changed during scan')
            file_states.append((record['path'], before.st_size, before.st_mtime_ns))
        except Exception as exc:
            errors.append({'path': record['path'], 'error': str(exc)})
        if index % 50 == 0 or index == len(files):
            print(f'QC decoded {index}/{len(files)} files', flush=True)
    # Detect concurrent changes, including changes after an earlier file was read.
    for name, size, mtime in file_states:
        stat = (ROOT / name).stat()
        if (stat.st_size, stat.st_mtime_ns) != (size, mtime):
            errors.append({'path': name, 'error': 'File changed during QC run'})
    table(OUT / 'channel_day_quality.csv', rows)
    channel_rows, gap_rows, hourly_rows = [], [], []
    for seed, intervals in sorted(spans.items()):
        merged = union(intervals)
        coverage = sum(b - a for a, b in merged)
        cursor = 0.
        for a, b in merged + [[duration, duration]]:
            if a - cursor > 1e-5:
                gap_rows.append(dict(seed_id=seed, start_utc=str(start + cursor),
                                     end_utc=str(start + a), seconds=a - cursor))
            cursor = max(cursor, b)
        channel_rows.append(dict(seed_id=seed, coverage_percent=100 * coverage / duration,
                                 missing_seconds=duration - coverage,
                                 overlap_seconds=max(0, sum(b - a for a, b in intervals) - coverage)))
        for hour in range(int(math.ceil(duration / 3600))):
            a, b = hour * 3600, min((hour + 1) * 3600, duration)
            covered = sum(max(0, min(y, b) - max(x, a)) for x, y in merged)
            n, s, q = hours[seed, hour]
            hourly_rows.append(dict(seed_id=seed, hour_utc=str(start + a), hour_index=hour,
                                    coverage_percent=100 * covered / (b - a),
                                    std_counts=np.sqrt(max(0, q / n - (s / n) ** 2)) if n else 0))
    table(OUT / 'channel_coverage.csv', channel_rows)
    if gap_rows:
        table(OUT / 'gaps.csv', gap_rows)
    table(OUT / 'hourly_quality.csv', hourly_rows)
    with publication_style():
        stations = sorted({'.'.join(s.split('.')[:2]) for s in spans})
        matrix = np.ones((len(stations), int(math.ceil(duration / 3600)))) * 100
        for r in hourly_rows:
            i = stations.index('.'.join(r['seed_id'].split('.')[:2]))
            matrix[i, r['hour_index']] = min(matrix[i, r['hour_index']], r['coverage_percent'])
        fig, ax = plt.subplots(figsize=(7.09, 8.4), layout='constrained')
        im = ax.imshow(matrix, aspect='auto', origin='lower',
                       extent=[0, duration / 3600, -.5, len(stations) - .5],
                       vmin=99, vmax=100, cmap='viridis')
        ax.set_yticks(range(len(stations)), stations)
        ticks = np.linspace(0, duration / 3600, 5).astype(int)
        ax.set_xticks(ticks)
        ax.set(xlabel=f'Hours since {start.strftime("%d %B %Y")}, 00:00 UTC', ylabel='Station')
        fig.colorbar(im, ax=ax, pad=.02, label='Minimum channel coverage per hour (%)',
                     shrink=.5, extend='min')
        save_figure(fig, OUT / '01_coverage')
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(7.09, 3), layout='constrained')
        ordered = sorted(channel_rows, key=lambda x: x['missing_seconds'], reverse=True)[:12]
        axes[0].barh([r['seed_id'] for r in ordered][::-1],
                     [r['missing_seconds'] for r in ordered][::-1], color='#0072B2')
        axes[0].set(xlabel='Missing duration (s)', title='a  Largest coverage deficits')
        for family, color in FAMILY_COLORS:
            selected = [r for r in rows if r['seed_id'].split('.')[-1].startswith(family)]
            if selected:
                axes[1].scatter([r['std_counts'] for r in selected],
                                [r['peak_abs_counts'] for r in selected],
                                s=9, alpha=.6, label=family, color=color)
        axes[1].set(xscale='log', yscale='log', xlabel='Window standard deviation (counts)',
                    ylabel='Window absolute peak (counts)', title='b  Recorded amplitudes')
        axes[1].legend(frameon=False)
        save_figure(fig, OUT / '02_quality')
        plt.close(fig)
        preprocessing(origin, anchor)
        peak_detail(origin)
    report(rows, channel_rows, gap_rows, errors, start, end, len(files), anchor, origin)
    if errors:
        raise RuntimeError(f'{len(errors)} QC errors; see report')


def _day_file(seed, station, origin):
    stem = origin.strftime('%Y%m%d')
    return ROOT / 'data' / station / f'{seed}__{stem}T000000Z__{(origin + 86400).strftime("%Y%m%d")}T000000Z.mseed'


def preprocessing(origin, anchor):
    specs = preprocess_seeds(origin, anchor)
    fig, axes = plt.subplots(len(specs), 2, figsize=(7.09, 2 * len(specs)),
                             layout='constrained', squeeze=False)
    for i, (distance, _pref, seed, station) in enumerate(specs):
        st = read(str(_day_file(seed, station, origin)),
                  starttime=origin - 90, endtime=origin + 150).select(id=seed)
        # Merge only exactly adjacent segments; gaps stay separate, no padding.
        st.merge(method=-1)
        for j, tr in enumerate(st.select(id=seed)):
            if len(tr) < 1000:
                continue
            processed = tr.copy().detrend('linear').detrend('demean')
            processed.taper(max_percentage=.05, type='cosine')
            processed.filter('bandpass', freqmin=PREPROCESS_BAND[0], freqmax=PREPROCESS_BAND[1],
                             corners=4, zerophase=True)
            t = tr.times(reftime=origin)
            mask = (t >= -30) & (t <= 120)
            # Plot all samples; export vector lines rasterized to keep PDFs small.
            axes[i][0].plot(t[mask], tr.data[mask], color='#777777', lw=.4,
                            label='Raw' if j == 0 else None, rasterized=True)
            axes[i][0].plot(t[mask], processed.data[mask], color='#0072B2', lw=.4,
                            label=f'{PREPROCESS_BAND[0]:g}–{PREPROCESS_BAND[1]:g} Hz' if j == 0 else None,
                            rasterized=True)
            for data, color, label in [(tr.data, '#777777', 'Raw'),
                                       (processed.data, '#0072B2', 'Filtered')]:
                f, p = welch(data[mask].astype(float), fs=tr.stats.sampling_rate,
                             nperseg=min(4096, int(mask.sum())))
                axes[i][1].loglog(f[1:], p[1:], color=color, lw=.8)
        axes[i][0].set(title=f'{seed} · {distance:.1f} km', ylabel='Counts', xlim=(-30, 120))
        axes[i][1].set(xlim=(.1, 50), ylabel='PSD (counts²/Hz)')
    axes[0][0].legend(frameon=False, ncol=2)
    axes[-1][0].set_xlabel(f'Time since M {anchor["magnitude"]:.1f} origin (s)')
    axes[-1][1].set_xlabel('Frequency (Hz)')
    save_figure(fig, OUT / '03_preprocessing')
    plt.close(fig)


def peak_detail(origin):
    anchor = json.loads((CASE / 'analysis/mainshock_anchor.json').read_text())['anchor']
    specs = preprocess_seeds(origin, anchor)[:2]
    fig, axes = plt.subplots(2, 1, figsize=(7.09, 3.6), layout='constrained')
    for ax, (distance, _pref, seed, station) in zip(axes, specs):
        st = read(str(_day_file(seed, station, origin)),
                  starttime=origin + 10, endtime=origin + 30).select(id=seed)
        for tr in st.select(id=seed):
            ax.plot(tr.times(reftime=origin), tr.data, color='#0072B2', lw=.6)
        ax.set(title=seed, ylabel='Counts', xlim=(10, 30))
    axes[-1].set_xlabel(f'Time since M {anchor["magnitude"]:.1f} origin (s)')
    save_figure(fig, OUT / '04_mainshock_detail')
    plt.close(fig)


def report(rows, channels, gaps, errors, start, end, file_count, anchor, origin):
    flagged = [r for r in rows if r['longest_constant_s'] >= 1 or
               r['longest_segment_extreme_plateau_s'] >= .1]
    label = f'M {anchor["magnitude"]:.1f}'
    lines = ['# Magna waveform quality review', '',
             f'Generated: {datetime.now(timezone.utc).isoformat()}',
             '',
             f'Window: [{start}, {end}). Candidate window, not a frozen benchmark input.',
             '',
             f'Fully decoded {file_count} MiniSEED files; {len(channels)} NSLCs at '
             f'{len({".".join(r["seed_id"].split(".")[:2]) for r in channels})} stations.',
             f'Finite samples: {sum(r["finite_samples"] for r in rows):,}; '
             f'nonfinite samples: {sum(r["nonfinite_samples"] for r in rows):,}; '
             f'exact-zero samples: {sum(r["zero_samples"] for r in rows):,}.',
             f'Decode/concurrent-change errors: {len(errors)}. '
             f'Files with decoding warnings: {sum(bool(r["decode_warnings"]) for r in rows)}.',
             f'Minimum channel coverage: {min(r["coverage_percent"] for r in channels):.6f}%. '
             f'Summed missing channel-seconds: {sum(r["missing_seconds"] for r in channels):.6f}. '
             f'Summed overlap channel-seconds: {sum(r["overlap_seconds"] for r in channels):.6f}.',
             '',
             '## Coverage and sample checks', '',
             'Coverage is the union of actual decoded segment intervals, clipped to the '
             'candidate window, with each last sample representing one sample interval. '
             'Deficits include day/window edges and internal gaps. Small offsets are '
             'reported without rounding them into entire missing samples. Hourly station '
             'coverage is the minimum over its observed NSLCs; it does not assert that '
             'absent components exist.',
             '', 'Gaps longer than 1 s:', '']
    long_gaps = [r for r in gaps if r['seconds'] > 1]
    bullet = '- `{r[seed_id]}`: {r[start_utc]} to {r[end_utc]}, {r[seconds]:.6f} s.'
    if not long_gaps:
        lines += ['- None.']
    elif len(long_gaps) <= 200:
        lines += [bullet.format(r=r) for r in long_gaps]
    else:
        # Full table lives in gaps.csv; the report only aggregates.
        lines += [f'{len(long_gaps)} gaps exceed 1 s; per-channel totals follow, the '
                  f'{min(len(long_gaps), 20)} longest are listed individually and every '
                  'interval, including sub-second deficits, is in `gaps.csv`.']
        by_seed = {}
        for r in long_gaps:
            count, total, longest = by_seed.setdefault(r['seed_id'], [0, 0.0, 0.0])
            by_seed[r['seed_id']] = [count + 1, total + r['seconds'],
                                     max(longest, r['seconds'])]
        lines += ['', 'Channel | Gaps >1 s | Total missing s | Longest s',
                  '|---|---:|---:|---:|']
        lines += [f'| `{seed}` | {n} | {t:.3f} | {x:.3f} |'
                  for seed, (n, t, x) in sorted(by_seed.items(), key=lambda kv: -kv[1][1])]
        lines += ['', f'{min(len(long_gaps), 20)} longest individual gaps:']
        lines += [bullet.format(r=r)
                  for r in sorted(long_gaps, key=lambda r: -r['seconds'])[:20]]
    lines += ['', f'Constant-run screening flags: {len(flagged)} channel-days. Thresholds: '
                  'identical samples for ≥1 s, or identical values at a segment minimum/maximum '
                  'for ≥0.1 s. These are screening flags, not proven ADC clipping; extrema are '
                  'segment-local and runs are measured within decoded segments (not across '
                  'boundaries). Exact zeros alone are not evidence of zero filling. Nonfinite '
                  'values are excluded from amplitude statistics.', '']
    lines += [f'- `{r["seed_id"]}` ({Path(r["path"]).name}): constant {r["longest_constant_s"]:.3f} s; '
              f'extreme plateau {r["longest_segment_extreme_plateau_s"]:.3f} s.' for r in flagged]
    seeds = ', '.join(s[2] for s in preprocess_seeds(origin, anchor))
    lines += ['', '## Exploratory preprocessing', '',
              f'The {label} comparison uses {seeds} (the nearest 100 Hz vertical channels to '
              f'the anchor, in distance order). Read −90 to +150 s around {origin}; show '
              '−30 to +120 s. Merge exactly adjacent segments only, then process each '
              'contiguous segment separately: linear detrend, demean, 5% cosine taper, '
              'fourth-order 2–12 Hz Butterworth bandpass applied forward/backward. Welch PSD '
              'uses the displayed interval, up to 4096 samples per segment and SciPy defaults '
              '(Hann window, 50% overlap, constant detrending).',
              '',
              'This zero-phase trial is an offline diagnostic, not a causal picker '
              'configuration. Filtering can alter arrival shape and amplitude. The frequency '
              'band is exploratory and must be validated against the later task. No resampling, '
              'gap interpolation, response removal, rotation or normalization is applied. All '
              'amplitudes remain digital counts; different channel families have different '
              'native physical inputs and must not be compared as ground-motion amplitudes. '
              'Raw files are opened read-only and are not rewritten.',
              '',
              '## Outputs and next decisions', '',
              '- [Hourly coverage](01_coverage.png): minimum observed-channel coverage at each '
              'station; color scale 99–100%, lower values clipped at the lower bound.',
              '- [Coverage deficits and amplitudes](02_quality.png): raw-count amplitudes are '
              'screening statistics, not calibrated station comparisons.',
              f'- [Mainshock detail](04_mainshock_detail.png): unfiltered vertical traces, '
              f'10–30 s after the {label} origin.',
              '- [Waveforms and spectra](03_preprocessing.png): raw versus trial filtering; '
              'PDF versions accompany all figures.',
              '- `channel_day_quality.csv`: path, bytes, rate, segment/sample counts, zeros, '
              'nonfinite samples, amplitude and plateau screening, decode warnings.',
              '- `channel_coverage.csv`, `gaps.csv`, `hourly_quality.csv`: compact derived '
              'tables supporting the plots; the external inventory remains the file inventory.',
              '',
              'This scan does not prove phase-picking readiness, timing accuracy, response '
              'correctness or absence of clipping. Processing parameters and station policy '
              'remain provisional.']
    if errors:
        lines += ['', '## Errors', '', *[f'- {r}' for r in errors]]
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
