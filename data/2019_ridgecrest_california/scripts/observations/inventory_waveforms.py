#!/usr/bin/env python3
"""Build the Ridgecrest waveform inventory from MiniSEED headers, without editing data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import warnings

from obspy import read, UTCDateTime
import yaml

CASE = Path(__file__).resolve().parents[2]


def union_seconds(intervals):
    total = 0.0
    end = None
    for a, b in sorted(intervals):
        if b <= a:
            continue
        total += max(0.0, b - max(a, end if end is not None else a))
        end = max(b, end if end is not None else b)
    return round(total, 6)


def describe(stream, start, end):
    results = []
    for seed_id in sorted({tr.id for tr in stream}):
        traces = stream.select(id=seed_id).sort()
        intervals, candidate_intervals = [], []
        candidate_npts = 0
        for tr in traces:
            t, rate, n = tr.stats.starttime, tr.stats.sampling_rate, tr.stats.npts
            a, b = float(t), float(t) + n / rate
            intervals.append((a, b))
            candidate_intervals.append((max(a, float(start)), min(b, float(end))))
            lo = max(0, min(n, math.ceil((start - t) * rate - 1e-7)))
            hi = max(0, min(n, math.ceil((end - t) * rate - 1e-7)))
            candidate_npts += max(0, hi - lo)
        gap_count = overlap_count = 0
        gap_seconds = overlap_seconds = 0.0
        covered_end = None
        for a, b in sorted(intervals):
            if covered_end is not None:
                if a > covered_end + 1e-6:
                    gap_count += 1
                    gap_seconds += a - covered_end
                elif a < covered_end - 1e-6:
                    overlap_count += 1
                    overlap_seconds += max(0.0, min(b, covered_end) - a)
            covered_end = max(b, covered_end if covered_end is not None else b)
        first = traces[0].stats
        results.append(dict(
            seed_id=seed_id, network=first.network, station=first.station,
            location=first.location, channel=first.channel, component=first.channel[-1:],
            sample_rates_hz=sorted({tr.stats.sampling_rate for tr in traces}),
            segment_count=len(traces), npts=sum(tr.stats.npts for tr in traces),
            start_utc=str(min(tr.stats.starttime for tr in traces)),
            last_sample_utc=str(max(tr.stats.endtime for tr in traces)),
            coverage_seconds=union_seconds(intervals),
            gap_count=gap_count,
            gap_seconds=round(gap_seconds, 6),
            overlap_count=overlap_count,
            overlap_seconds=round(overlap_seconds, 6),
            candidate_npts=candidate_npts,
            candidate_coverage_seconds=union_seconds(candidate_intervals),
        ))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=CASE / 'data/waveforms')
    args = parser.parse_args()
    root = args.root.resolve()
    cfg = yaml.safe_load((CASE / 'analysis/processing.yaml').read_text())
    window = cfg['scientific_design']['candidate_window']
    start, end = UTCDateTime(window['start_utc']), UTCDateTime(window['end_utc'])
    previous = root / 'waveform_inventory.json'
    if previous.exists():
        old = json.loads(previous.read_text())
        provenance = old['provenance']
        hashes = {r['path']: r.get('copy_sha256') for r in old['files']}
    else:
        old = json.loads((root / 'copy_manifest.json').read_text())
        provenance = {k: v for k, v in old.items() if k != 'entries'}
        hashes = {'data/' + r['path']: r['sha256'] for r in old['entries']}
    rows = []
    files = sorted((root / 'data').rglob('*.mseed'))
    for i, path in enumerate(files, 1):
        row = dict(path=str(path.relative_to(root)), bytes=path.stat().st_size)
        if hashes.get(row['path']):
            row['copy_sha256'] = hashes[row['path']]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            st = read(str(path), format='MSEED', headonly=True)
        if not st:
            raise ValueError(f'No traces in {path}')
        row.update(format='MSEED', streams=describe(st, start, end))
        row['npts'] = sum(s['npts'] for s in row['streams'])
        row['candidate_npts'] = sum(s['candidate_npts'] for s in row['streams'])
        row['in_candidate_window'] = row['candidate_npts'] > 0
        if caught:
            row['read_warnings'] = sorted({str(w.message) for w in caught})
        rows.append(row)
        if i % 200 == 0:
            print(f'{i}/{len(files)} headers read', flush=True)
    selected = [r for r in rows if r['in_candidate_window']]
    summary = dict(files=len(rows), bytes=sum(r['bytes'] for r in rows),
                   stations=len({s['network']+'.'+s['station'] for r in rows for s in r['streams']}),
                   stored_npts=sum(r['npts'] for r in rows),
                   components=dict(sorted(Counter(s['component'] for r in rows for s in r['streams']).items())),
                   candidate_files=len(selected), candidate_file_bytes=sum(r['bytes'] for r in selected),
                   candidate_stations=len({s['network']+'.'+s['station'] for r in selected for s in r['streams'] if s['candidate_npts']}),
                   candidate_npts=sum(r['candidate_npts'] for r in rows))
    report = dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
                  path_base='Directory containing this inventory; file paths include data/.',
                  inspection='MiniSEED headers only; no sample decoding, filtering, merging or trimming.',
                  provenance=provenance,
                  candidate=dict(start_utc=str(start), end_utc=str(end), interval='half_open',
                                 status=cfg['window_status'], config='analysis/processing.yaml',
                                 station_channel_filter='not_defined_not_applied', buffer='not_defined',
                                 selection='At least one header-derived sample timestamp in the window.'),
                  field_notes=dict(npts='Stored sample count including overlaps; headers do not establish sample quality.',
                                   streams='One entry per distinct network.station.location.channel in each file.',
                                   coverage_seconds='Union of segment intervals [start, last sample + 1/rate); not a quality metric. Candidate coverage clips these intervals to the window.',
                                   gaps='Internal same-NSLC segment-interval gaps and redundant coverage within each file, using a sorted union sweep (1 microsecond tolerance); excludes cross-file and leading/trailing missing data. Overlap count counts segments intersecting preceding coverage.',
                                   component='Last character of channel code; 1/2 are not automatically N/E. Orientation and response matching remain unverified.',
                                   candidate_file_bytes='Whole-file sizes, not bytes of a trimmed candidate subset.',
                                   components='Counts of file/NSLC entries by component, not independent instruments.',
                                   copy_sha256='Historical copy verification digest, retained for provenance; not recomputed by this header scan.',
                                   units='Native digital counts assumed from source; physical units, amplitudes, clipping and zero fractions not checked.'),
                  summary=summary, files=rows)
    if old.get('download_runs'):
        report['download_runs'] = old['download_runs']
    temp = previous.with_suffix('.json.tmp')
    temp.write_text(json.dumps(report, indent=2) + '\n')
    temp.replace(previous)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
