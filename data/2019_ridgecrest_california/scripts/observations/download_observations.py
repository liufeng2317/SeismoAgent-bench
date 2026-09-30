#!/usr/bin/env python3
"""Plan or download Ridgecrest observations using exact channel epochs and local coverage."""
import argparse
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import math
import re
import sys
import traceback
import hashlib
import json
from pathlib import Path
import tempfile
import time

import numpy as np
from obspy import read, Stream, UTCDateTime
import requests
import yaml

CASE = Path(__file__).resolve().parents[2]
PROVIDERS = {'SCEDC_CLOUD': 'https://scedc-pds.s3.us-west-2.amazonaws.com',
             'SCEDC': 'https://service.scedc.caltech.edu',
             'EARTHSCOPE': 'https://service.earthscope.org'}


def stream_sha256(handle):
    """Streaming SHA-256 compatible with Python 3.9 and later."""
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def error_details(exc, phase):
    message = re.sub(r'(https?://)[^/\s@]+@', r'\1[redacted]@', str(exc))
    result = dict(error=type(exc).__name__, message=message[:1200], phase=phase)
    if isinstance(exc, requests.RequestException) and exc.response is not None:
        result['http_status'] = exc.response.status_code
    frames = traceback.extract_tb(exc.__traceback__)
    if frames:
        frame = frames[-1]
        result['location'] = f'{Path(frame.filename).name}:{frame.lineno} ({frame.name})'
    return result


def union(intervals):
    out = []
    for a, b in sorted(intervals):
        if b <= a:
            continue
        if out and a <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(b, out[-1][1]))
        else:
            out.append((a, b))
    return out


def missing(start, end, intervals, minimum):
    cursor, out = start, []
    for a, b in union(intervals):
        if b <= cursor:
            continue
        if a >= end:
            break
        if a > cursor and a - cursor >= minimum and a - cursor > 1e-6:
            out.append((cursor, a))
        cursor = max(cursor, b)
    if end - cursor >= minimum and end - cursor > 1e-6:
        out.append((cursor, end))
    return out


def day_chunks(a, b):
    while a < b:
        next_day = float(UTCDateTime(UTCDateTime(a).strftime('%Y-%m-%d'))) + 86400
        stop = min(b, next_day)
        yield a, stop
        a = stop


def atomic_json(path, value):
    with tempfile.NamedTemporaryFile('w', dir=path.parent, suffix='.tmp', delete=False) as f:
        tmp = Path(f.name)
        json.dump(value, f, indent=2)
        f.write('\n')
    tmp.replace(path)


@contextmanager
def download_lock(root):
    # Lock the directory inode: no extra lock or state file is required.
    with open_directory(root) as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another downloader is using this waveform directory') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def open_directory(path):
    import os
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def station_ids(root, inventory, scope, explicit, families=None):
    if explicit:
        names = set(explicit.split(','))
        if any(len(n.split('.')) != 2 or any(not v.isalnum() for v in n.split('.')) for n in names):
            raise ValueError('--stations must contain exact NET.STA identifiers')
        return names
    if scope == 'existing':
        return {s['network']+'.'+s['station'] for r in inventory['files']
                for s in r['streams'] if s['candidate_npts']
                and (families is None or s['channel'][:2] in families)}
    if scope == 'ross':
        prep = json.loads((CASE/'analysis/station_preparation.json').read_text())
        return set(prep['ross_rule_candidates']['station_ids'])
    catalog = {'liu': 'LIU2020_GL086189', 'shelly': 'SHELLY2020_0220190309'}[scope]
    selection = json.loads((root/'stations/station_inventory.json').read_text())['catalogs'][catalog]
    return set(selection['metadata_present_station_ids'])


def load_epochs(root):
    epochs = json.loads((root/'stations/station_inventory.json').read_text())['channel_epochs']
    # Newly acquired response snapshots participate without replacing original evidence.
    from prepare_station_metadata import parse
    for p in sorted((root/'stations/downloads').glob('*.stationxml')):
        epochs.extend(parse(p, p.name.split('_')[0]))
    return epochs


def targets(epochs, stations, families, locations, start, end):
    selected = defaultdict(list)
    for e in epochs:
        if e['network']+'.'+e['station'] not in stations or e['channel'][:2] not in families:
            continue
        if locations is not None and e['location'] not in locations:
            continue
        if not e.get('sample_rate_hz') or e['sample_rate_hz'] <= 0:
            continue
        a = max(start, float(UTCDateTime(e['effective_start'])) if e['effective_start'] else start)
        b = min(end, float(UTCDateTime(e['effective_end'])) if e['effective_end'] else end)
        if b > a:
            seed = '.'.join(e[k] for k in ('network', 'station', 'location', 'channel'))
            selected[(seed, float(e['sample_rate_hz']))].append((a, b))
    # Conflicting simultaneous rates require a metadata decision, not a silent choice.
    for (seed, rate), spans in selected.items():
        for (other, other_rate), other_spans in selected.items():
            if seed == other and rate != other_rate and any(max(a,c)<min(b,d) for a,b in spans for c,d in other_spans):
                raise ValueError(f'Conflicting rates for {seed}: {rate}, {other_rate}')
    return {k: union(v) for k, v in selected.items()}


def local_coverage(root, stations, start, end):
    coverage = defaultdict(list)
    count = 0
    for name in sorted(stations):
        for path in sorted((root/'data'/name).rglob('*.mseed')):
            for tr in read(str(path), format='MSEED', headonly=True):
                s = tr.stats
                a = max(start, float(s.starttime))
                b = min(end, float(s.starttime) + s.npts / s.sampling_rate)
                if b > a:
                    coverage[(tr.id, float(s.sampling_rate))].append((a, b))
            count += 1
            if count % 500 == 0:
                print(f'Checked {count} local waveform headers', flush=True)
    return coverage


def waveform_plan(selected, coverage, minimum):
    rows = []
    for (seed, rate), epochs in sorted(selected.items()):
        for a, b in epochs:
            for lo, hi in missing(a, b, coverage.get((seed, rate), []), minimum):
                for left, right in day_chunks(lo, hi):
                    if right - left < max(minimum, 1 / rate) - 1e-6:
                        continue
                    rows.append(dict(seed_id=seed, sample_rate_hz=rate,
                                     start_utc=str(UTCDateTime(left)), end_utc=str(UTCDateTime(right))))
    return rows


def station_plan(selected):
    rows = []
    for (seed, rate), spans in sorted(selected.items()):
        for a, b in spans:
            rows.append(dict(seed_id=seed, sample_rate_hz=rate,
                             start_utc=str(UTCDateTime(a)), end_utc=str(UTCDateTime(b))))
    return rows


def download_response(session, url, params, path, retries, timeout):
    for attempt in range(retries):
        print(f'    Connecting: attempt {attempt+1}/{retries}, timeout={timeout}s', flush=True)
        try:
            with session.get(url, params=params, timeout=(10, timeout), stream=True) as response:
                print(f'    HTTP {response.status_code}', flush=True)
                if response.status_code in (204, 404):
                    return False
                response.raise_for_status()
                received, started, last = 0, time.monotonic(), time.monotonic()
                with path.open('wb') as out:
                    for block in response.iter_content(1024 * 1024):
                        out.write(block)
                        received += len(block)
                        now = time.monotonic()
                        if now-last >= 5:
                            print(f'    Received {received/1e6:.2f} MB ({received/1e6/max(now-started, .001):.2f} MB/s)', flush=True)
                            last = now
                print(f'    Received {received/1e6:.2f} MB; validating response', flush=True)
            if path.stat().st_size == 0:
                raise ValueError('Empty response with success status')
            return True
        except requests.RequestException as exc:
            status = exc.response.status_code if exc.response is not None else None
            if attempt + 1 == retries or (status is not None and status < 500 and status != 429):
                raise
            print(f'    Retry after {type(exc).__name__}', flush=True)
            time.sleep(min(2 ** attempt, 10))
    return False


def validate_waveform(path, row):
    # Decode to catch corrupt records before admitting any new payload.
    stream = read(str(path), format='MSEED')
    a, b = UTCDateTime(row['start_utc']), UTCDateTime(row['end_utc'])
    valid = []
    for tr in stream:
        s = tr.stats
        if tr.id != row['seed_id'] or s.sampling_rate != row['sample_rate_hz']:
            raise ValueError('Returned channel or sampling rate differs from request')
        # FDSN endpoints can include the final sample and round to sample boundaries.
        if s.starttime < a - s.delta or s.endtime > b + s.delta:
            raise ValueError('Returned waveform extends outside requested bounds')
        lo, hi = max(float(a), float(s.starttime)), min(float(b), float(s.starttime)+s.npts/s.sampling_rate)
        if hi > lo:
            valid.append((lo, hi))
    if not valid:
        raise ValueError('Response contains no samples in requested interval')
    return sum(y-x for x,y in union(valid))


def validate_station(path, row):
    from prepare_station_metadata import parse
    a, b = float(UTCDateTime(row['start_utc'])), float(UTCDateTime(row['end_utc']))
    spans = []
    for e in parse(path, 'download'):
        seed = '.'.join(e[k] for k in ('network', 'station', 'location', 'channel'))
        if seed == row['seed_id'] and e['sample_rate_hz'] == row['sample_rate_hz'] and e['response_stages']:
            lo = max(a, float(UTCDateTime(e['effective_start'])) if e['effective_start'] else a)
            hi = min(b, float(UTCDateTime(e['effective_end'])) if e['effective_end'] else b)
            if hi > lo:
                spans.append((lo, hi))
    if not spans:
        raise ValueError('No matching response/channel epoch in StationXML')
    return sum(y-x for x,y in union(spans))


class WaveformConflict(ValueError):
    """Do not replace a daily file when overlapping observations disagree."""


def add_samples(existing, incoming):
    """Retain existing segments and append only previously absent samples."""
    combined = existing.copy()
    added = 0
    for trace in incoming:
        covered = []
        for old in combined:
            if old.id != trace.id:
                raise WaveformConflict('Unexpected channel in daily file')
            if max(old.stats.starttime, trace.stats.starttime) > min(old.stats.endtime, trace.stats.endtime):
                continue
            if old.stats.sampling_rate != trace.stats.sampling_rate:
                raise WaveformConflict('Overlapping segments have different rates')
            offset = (old.stats.starttime - trace.stats.starttime) * trace.stats.sampling_rate
            shift = round(offset)
            if abs(offset - shift) > 1e-4:
                raise WaveformConflict('Overlapping samples have incompatible time grids')
            lo, hi = max(0, shift), min(trace.stats.npts, shift + old.stats.npts)
            if hi > lo:
                if not np.array_equal(trace.data[lo:hi], old.data[lo-shift:hi-shift]):
                    raise WaveformConflict('Overlapping samples have different values')
                covered.append((lo, hi))
        cursor = 0
        for lo, hi in union(covered) + [(trace.stats.npts, trace.stats.npts)]:
            if lo > cursor:
                part = trace.copy()
                part.data = trace.data[cursor:lo].copy()
                part.stats.starttime = trace.stats.starttime + cursor / trace.stats.sampling_rate
                combined.append(part)
                added += lo - cursor
            cursor = max(cursor, hi)
    return combined, added


def save_daily(path, row, outdir):
    """Atomically extend one canonical UTC-day file; never fill gaps or resolve conflicts silently."""
    day = UTCDateTime(UTCDateTime(row['start_utc']).strftime('%Y-%m-%d'))
    end = day + 86400
    if UTCDateTime(row['end_utc']) > end:
        raise ValueError('A waveform request must fit within one UTC day')
    stamp = lambda t: t.strftime('%Y%m%dT%H%M%SZ')
    dest = outdir / f"{row['seed_id']}__{stamp(day)}__{stamp(end)}.mseed"
    incoming = Stream()
    for trace in read(str(path), format='MSEED'):
        # Keep only sample timestamps within the nominal day, including fractional offsets.
        rate = trace.stats.sampling_rate
        lo = max(0, min(trace.stats.npts, math.ceil((day-trace.stats.starttime)*rate-1e-7)))
        hi = max(0, min(trace.stats.npts, math.ceil((end-trace.stats.starttime)*rate-1e-7)))
        if hi > lo:
            part = trace.copy()
            part.data = trace.data[lo:hi].copy()
            part.stats.starttime = trace.stats.starttime + lo/rate
            incoming.append(part)
    if not incoming:
        raise ValueError('No samples within the requested day')
    existed = dest.exists()
    previous_digest = None
    if existed:
        with dest.open('rb') as f:
            previous_digest = stream_sha256(f)
    existing = read(str(dest), format='MSEED') if existed else Stream()
    combined, added = add_samples(existing, incoming)
    if not added:
        return dest, 'already_saved', previous_digest, 0
    with tempfile.NamedTemporaryFile(dir=outdir, suffix='.part', delete=False) as f:
        stage = Path(f.name)
    try:
        combined.sort().write(str(stage), format='MSEED')
        decoded = read(str(stage), format='MSEED')
        if sum(t.stats.npts for t in decoded) != sum(t.stats.npts for t in combined):
            raise ValueError('Sample count changed during MiniSEED serialization')
        _, missing_samples = add_samples(decoded, combined)
        if missing_samples:
            raise ValueError('Samples changed during MiniSEED serialization')
        stage.replace(dest)
    finally:
        stage.unlink(missing_ok=True)
    return dest, 'updated' if existed else 'downloaded', previous_digest, added


def acquire(row, kind, root, session, providers, retries, timeout):
    net, sta, loc, channel = row['seed_id'].split('.')
    params = dict(network=net, station=sta, location=loc or '--', channel=channel,
                  starttime=row['start_utc'], endtime=row['end_utc'], nodata=204)
    service = 'dataselect' if kind == 'waveforms' else 'station'
    if kind == 'stations':
        params.update(level='response', format='xml')
    outdir = root/'data'/f'{net}.{sta}' if kind == 'waveforms' else root/'stations/downloads'
    outdir.mkdir(parents=True, exist_ok=True)
    failures = []
    for provider in providers:
        phase = 'request'
        print(f'  Provider {provider}: {row["seed_id"]}', flush=True)
        request_params = params
        if provider == 'SCEDC_CLOUD':
            day = UTCDateTime(UTCDateTime(row['start_utc']).strftime('%Y-%m-%d'))
            if (kind != 'waveforms' or net != 'CI' or loc != '' or
                    UTCDateTime(row['start_utc']) != day or UTCDateTime(row['end_utc']) != day + 86400):
                failures.append(dict(provider=provider, status='unsupported', reason='Cloud adapter supports blank-location CI full UTC-day waveforms only'))
                continue
            key = f"continuous_waveforms/{day.year}/{day.strftime('%Y_%j')}/CI{sta:_<5}{channel}___{day.strftime('%Y%j')}.ms"
            url = PROVIDERS[provider] + '/' + key
            request_params = {}
        else:
            url = PROVIDERS[provider] + f'/fdsnws/{service}/1/query'
        with tempfile.NamedTemporaryFile(dir=outdir, suffix='.part', delete=False) as f:
            temp = Path(f.name)
        try:
            if not download_response(session, url, request_params, temp, retries, timeout):
                print(f'  {provider}: no data for requested interval', flush=True)
                failures.append(dict(provider=provider, status='no_data'))
                continue
            phase = 'response_validation'
            coverage = (validate_waveform if kind == 'waveforms' else validate_station)(temp, row)
            phase = 'response_checksum'
            with temp.open('rb') as f:
                digest = stream_sha256(f)
            phase = 'save_payload'
            if kind == 'waveforms':
                dest, status, previous_digest, added = save_daily(temp, row, outdir)
            else:
                stamp = lambda v: UTCDateTime(v).strftime('%Y%m%dT%H%M%SZ')
                name = f"{provider.lower()}_{row['seed_id']}__{stamp(row['start_utc'])}__{stamp(row['end_utc'])}__{digest[:12]}.stationxml"
                dest = outdir/name
                previous_digest, added = None, None
                status = 'already_saved' if dest.exists() else 'downloaded'
                if not dest.exists():
                    temp.replace(dest)
            with dest.open('rb') as f:
                stored_digest = stream_sha256(f)
            total = UTCDateTime(row['end_utc']) - UTCDateTime(row['start_utc'])
            return dict(status=status, provider=provider, source_url=url, path=str(dest.relative_to(root)),
                        bytes=dest.stat().st_size, sha256=stored_digest, response_sha256=digest,
                        previous_sha256=previous_digest, added_npts=added, coverage_seconds=coverage,
                        incomplete=coverage < total-1/row['sample_rate_hz'], attempts=failures)
        except WaveformConflict as exc:
            details = error_details(exc, phase)
            print(f'  {provider}: {details}', flush=True)
            return dict(status='failed', **details, attempts=failures)
        except Exception as exc:
            details = error_details(exc, phase)
            print(f'  {provider}: {details}', flush=True)
            failures.append(dict(provider=provider, status='failed', **details))
        finally:
            temp.unlink(missing_ok=True)
    return dict(status='failed' if any(x['status'] in ('failed','unsupported') for x in failures) else 'no_data', attempts=failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=['plan', 'download'], default='plan')
    parser.add_argument('--kind', choices=['waveforms', 'stations'], default='waveforms')
    parser.add_argument('--root', type=Path, default=CASE/'data/waveforms')
    parser.add_argument('--scope', choices=['existing', 'liu', 'shelly', 'ross'], default='existing')
    parser.add_argument('--stations', help='Exact comma-separated NET.STA list; overrides scope')
    parser.add_argument('--channels', default='EH,HH', help='Exact two-character families, e.g. HH,HN')
    parser.add_argument('--locations', help='Comma-separated location codes; -- means blank; default uses metadata locations')
    parser.add_argument('--min-gap-seconds', type=float, default=1.0)
    parser.add_argument('--providers', default='SCEDC,EARTHSCOPE')
    parser.add_argument('--direct', action='store_true', help='Bypass environment proxies')
    parser.add_argument('--use-proxy', dest='direct', action='store_false', help='Use environment proxy settings (override shell default)')
    parser.set_defaults(direct=False)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--retries', type=int, default=3)
    parser.add_argument('--max-requests', type=int, help='Limit execution, not the generated plan')
    # Older argparse versions turn the literal -- value into an empty list.
    argv = ['--locations=' if value == '--locations=--' else value for value in sys.argv[1:]]
    args = parser.parse_args(argv)
    families = set(args.channels.split(','))
    if not families <= {'EH', 'HH', 'HN', 'BH'} or not families:
        parser.error('Supported families: EH,HH,HN,BH')
    providers = args.providers.split(',')
    if not set(providers) <= PROVIDERS.keys():
        parser.error('Supported providers: SCEDC_CLOUD,SCEDC,EARTHSCOPE')
    if args.min_gap_seconds < 0 or args.timeout <= 0 or args.retries < 1 or (args.max_requests is not None and args.max_requests < 1):
        parser.error('Invalid gap, timeout, retries or request limit')
    root = args.root.resolve(strict=True)
    with download_lock(root):
        path = root/'waveform_inventory.json'
        inventory = json.loads(path.read_text())
        cfg = yaml.safe_load((CASE/'analysis/processing.yaml').read_text())
        window = cfg['scientific_design']['candidate_window']
        a, b = float(UTCDateTime(window['start_utc'])), float(UTCDateTime(window['end_utc']))
        if b <= a:
            raise ValueError('Empty candidate window')
        if args.scope == 'existing' and not args.stations:
            if (UTCDateTime(inventory['candidate']['start_utc']) != UTCDateTime(a) or
                    UTCDateTime(inventory['candidate']['end_utc']) != UTCDateTime(b)):
                raise ValueError('Refresh inventory for the current case window first')
        names = station_ids(root, inventory, args.scope, args.stations, families)
        locations = None if args.locations is None else {'' if x=='--' else x for x in args.locations.split(',')}
        selected = targets(load_epochs(root), names, families, locations, a, b)
        coverage = local_coverage(root, names, a, b) if args.kind == 'waveforms' else {}
        rows = waveform_plan(selected, coverage, args.min_gap_seconds) if args.kind == 'waveforms' else station_plan(selected)
        unmatched = sorted(names - {seed.split('.')[0]+'.'+seed.split('.')[1] for seed, rate in selected})
        plan = dict(kind=args.kind, scope=args.scope, station_ids=sorted(names), channels=sorted(families),
                    locations=None if locations is None else sorted(locations), window=window,
                    min_gap_seconds=args.min_gap_seconds, providers=providers,
                    unmatched_station_ids=unmatched, request_count=len(rows), requests=rows,
                    semantics='Metadata-supported local gaps; remote availability not presumed. Plan mode makes no network calls.')
        inventory['download_plan'] = plan
        atomic_json(path, inventory)
        print(json.dumps({k:v for k,v in plan.items() if k not in ('requests','window')}, indent=2), flush=True)
        print(f'Mode: {args.action}; Python {sys.version.split()[0]}', flush=True)
        if args.action == 'plan':
            print('Plan saved. No downloads performed. Use --action download to execute.', flush=True)
            return
        session = requests.Session()
        session.trust_env = not args.direct
        run = dict(started_utc=datetime.now(timezone.utc).isoformat(), kind=args.kind,
                   requested=len(rows), limited_to=args.max_requests, python_version=sys.version.split()[0], results=[])
        inventory.setdefault('download_runs', []).append(run)
        atomic_json(path, inventory)
        active = rows[:args.max_requests]
        for index, row in enumerate(active, 1):
            run['active_request'] = dict(index=index, total=len(active), request=row)
            atomic_json(path, inventory)
            print(f'[{index}/{len(active)}] Starting {row["seed_id"]} {row["start_utc"]} -> {row["end_utc"]}', flush=True)
            result = acquire(row, args.kind, root, session, providers, args.retries, args.timeout)
            run['results'].append(dict(request=row, **result))
            run.pop('active_request', None)
            inventory['download_assessment_stale'] = True
            inventory['header_inventory_stale'] = args.kind == 'waveforms' or inventory.get('header_inventory_stale', False)
            atomic_json(path, inventory)
            print(row['seed_id'], row['start_utc'], result['status'], flush=True)
        run['finished_utc'] = datetime.now(timezone.utc).isoformat()
        atomic_json(path, inventory)
        if unmatched or any(r['status'] in ('failed', 'no_data') or r.get('incomplete') for r in run['results']):
            raise SystemExit(2)


if __name__ == '__main__':
    main()
