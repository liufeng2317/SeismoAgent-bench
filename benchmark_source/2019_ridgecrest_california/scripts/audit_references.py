#!/usr/bin/env python3
"""Read-only source audit and conservative reference-overlap diagnostics.

Writes one JSON artifact; never changes source catalogs or declares a freeze.
Requires PyYAML to read the existing case configuration.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile

import yaml

CASE = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def origin(columns):
    seconds = float(columns[5])
    if not math.isfinite(seconds) or not 0 <= seconds < 60:
        raise ValueError('seconds outside [0, 60)')
    return datetime(*map(int, columns[:5]), tzinfo=UTC) + timedelta(seconds=seconds)


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('non-finite number')
    return number


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def event(time, lat, lon, depth, magnitude, native_id, line, **extra):
    lat, lon, depth = map(finite, (lat, lon, depth))
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('invalid geographical coordinates')
    return dict(time=time, timestamp=time.timestamp(), latitude=lat, longitude=lon,
                depth_km=depth, magnitude=finite(magnitude) if magnitude not in ('', None) else None,
                native_id=native_id, source_row=line, **extra)


def read_events(path, kind):
    rows, errors = [], []
    archive = None
    if kind == 'ross':
        archive = tarfile.open(path, 'r:gz')
        stream = io.TextIOWrapper(archive.extractfile('ridgecrest_qtm.cat'), encoding='utf-8')
    else:
        stream = path.open(encoding='utf-8-sig', newline='')
    try:
        iterator = csv.DictReader(stream) if kind in ('awr_hypo', 'awr_mt', 'official') else stream
        for line, raw in enumerate(iterator, 2 if kind in ('awr_hypo', 'awr_mt', 'official') else 1):
            try:
                if isinstance(raw, str):
                    fields = raw.split()
                    if not fields or raw.lstrip().startswith('#') or fields[0] == 'yr':
                        continue
                    expected = {'shelly': 11, 'liu': 10, 'ross': 25}[kind]
                    if len(fields) != expected:
                        raise ValueError(f'expected {expected} columns, got {len(fields)}')
                    if kind == 'ross':
                        row = event(origin(fields), *fields[7:11], fields[6], line,
                                    nbranch=int(fields[13]), cluster_id=fields[12],
                                    horizontal_error_km=finite(fields[19]),
                                    vertical_error_km=finite(fields[20]))
                    else:
                        row = event(origin(fields), *fields[6:10], fields[10] if kind == 'shelly' else None, line)
                elif kind == 'official':
                    row = event(utc(raw['time']), raw['latitude'], raw['longitude'], raw['depth'],
                                raw['mag'], raw['id'], line, event_type=raw['type'],
                                magnitude_type=raw['magType'], updated=raw['updated'],
                                depth_error_km=finite(raw['depthError']) if raw['depthError'] else None)
                else:
                    mag = raw['magnitude_gamma'] if kind == 'awr_hypo' else raw['magnitude']
                    row = event(utc(raw['time']), raw['latitude'], raw['longitude'], raw['depth_km'],
                                mag, raw['evid'], line)
                rows.append(row)
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                errors.append({'source_row': line, 'error': str(exc)})
    finally:
        stream.close()
        if archive is not None:
            archive.close()
    return rows, errors


def within(row, start, end, bounds=None):
    if not start <= row['time'] < end:
        return False
    return bounds is None or all(bounds[key][0] <= row[key] <= bounds[key][1]
                                 for key in ('latitude', 'longitude', 'depth_km'))


def quantiles(values):
    values = sorted(values)
    if not values:
        return None
    def q(p):
        i = (len(values) - 1) * p
        lo = int(i)
        return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (i - lo)
    return {'min': values[0], 'p50': q(.5), 'p90': q(.9), 'max': values[-1]}


def horizontal_km(a, b):
    lat1, lat2 = math.radians(a['latitude']), math.radians(b['latitude'])
    dlat = lat2 - lat1
    dlon = math.radians(b['longitude'] - a['longitude'])
    v = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(min(1.0, max(0.0, v))))


def overlap(left, right, time_seconds, distance_km):
    """Accept only reciprocal degree-one edges; ambiguous components stay unresolved."""
    right = sorted(right, key=lambda r: r['timestamp'])
    times = [r['timestamp'] for r in right]
    candidates = []
    degrees = Counter()
    for a in left:
        js = []
        for j in range(bisect_left(times, a['timestamp'] - time_seconds),
                       bisect_right(times, a['timestamp'] + time_seconds)):
            if horizontal_km(a, right[j]) <= distance_km:
                js.append(j)
                degrees[j] += 1
        candidates.append(js)
    pairs = [(a, right[js[0]]) for a, js in zip(left, candidates)
             if len(js) == 1 and degrees[js[0]] == 1]
    return {
        'time_tolerance_s': time_seconds, 'horizontal_tolerance_km': distance_km,
        'left_rows': len(left), 'right_rows': len(right), 'candidate_edges': sum(map(len, candidates)),
        'reciprocal_unique_pairs': len(pairs),
        'left_without_candidate': sum(not js for js in candidates),
        'right_without_candidate': len(right) - len(degrees),
        'left_multiple_candidates': sum(len(js) > 1 for js in candidates),
        'right_multiple_candidates': sum(n > 1 for n in degrees.values()),
        'left_with_candidate_but_unresolved': sum(bool(js) for js in candidates) - len(pairs),
        'right_with_candidate_but_unresolved': len(degrees) - len(pairs),
        'absolute_origin_time_difference_s': quantiles([abs(a['timestamp']-b['timestamp']) for a,b in pairs]),
        'horizontal_difference_km': quantiles([horizontal_km(a,b) for a,b in pairs]),
        'native_depth_difference_left_minus_right_km': quantiles([a['depth_km']-b['depth_km'] for a,b in pairs]),
        'interpretation': 'Reference overlap diagnostic, not precision/recall or truth error; native depth datums are not harmonized.',
    }


def summary(rows):
    ids = [r['native_id'] for r in rows if r['native_id'] is not None]
    times = [r['time'].isoformat() for r in rows]
    tuples = [(r['timestamp'], r['latitude'], r['longitude'], r['depth_km'], r['magnitude']) for r in rows]
    return {
        'row_count': len(rows), 'rows_without_native_id': len(rows)-len(ids),
        'duplicate_native_id_rows': len(ids)-len(set(ids)),
        'duplicate_origin_time_rows': len(times)-len(set(times)),
        'duplicate_time_location_magnitude_rows': len(tuples)-len(set(tuples)),
        'observed_time_range_utc': [min(times), max(times)] if times else None,
        'ranges': {key: [min(v),max(v)] if v else None
                   for key in ('latitude','longitude','depth_km','magnitude')
                   for v in [[r[key] for r in rows if r[key] is not None]]},
        'event_types': dict(sorted(Counter(r.get('event_type','not_supplied') for r in rows).items())),
    }


def phase_summary(path, start, end):
    total = selected = 0
    counts = Counter(); stations = Counter(); ids = set(); matched = set(); minimum = maximum = None
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            # The USGS correlation release stores arrival as Unix seconds, not ISO text.
            t=datetime.fromtimestamp(finite(row['arrival']),UTC);total+=1;counts[row['phase']]+=1
            station=row['network']+'.'+row['station'];stations[station]+=1
            ids.add(row['template_id']);matched.add(row['match_id'])
            minimum=t if minimum is None else min(minimum,t);maximum=t if maximum is None else max(maximum,t)
            if start<=t<end:selected+=1
    return {'row_count':total, 'unit':'phase_pick', 'arrival_encoding':'unix_seconds', 'arrival_time_only_rows':selected,
            'origin_time_not_supplied':True, 'event_catalog_crosswalk_verified':False,
            'phase_counts':dict(counts), 'network_station_pairs':len(stations),
            'template_ids':len(ids), 'match_ids':len(matched),
            'observed_arrival_time_range_utc':[minimum.isoformat(),maximum.isoformat()],
            'interpretation':'Station occurrences do not establish station-day waveform availability; match IDs are not validated event IDs.'}


def run(case):
    config_path=case/'analysis/processing.yaml';cfg=yaml.safe_load(config_path.read_text())
    design=cfg['scientific_design'];window=design['candidate_window'];bounds=window['native_comparison_bounds']
    start,end=utc(window['start_utc']),utc(window['end_utc'])
    sources=cfg['reference_audit']['sources'];outputs={};data={}
    for key,spec in sources.items():
        path=case/spec['path'];actual=sha256(path)
        if spec.get('expected_sha256') and actual!=spec['expected_sha256']:
            raise ValueError(f'Source checksum mismatch: {key}')
        rows,errors=read_events(path,spec['parser'])
        if errors:
            raise ValueError(f'{key}: {len(errors)} parse errors; first entries: {errors[:5]}')
        data[key]=rows
        time_only=[r for r in rows if within(r,start,end)]
        spatial=[r for r in time_only if within(r,start,end,bounds)]
        outputs[key]={'path':spec['path'],'sha256':actual,'parse_errors':errors,
                      'full':summary(rows),'candidate_time_only':summary(time_only),
                      'candidate_native_mask':summary(spatial)}
        outputs[key]['native_mask_exclusions']={k:sum(not limits[0]<=r[k]<=limits[1] for r in time_only)
                                              for k,limits in bounds.items()}
        outputs[key]['depth_outliers_above_100km']=[{k:r[k] for k in ('native_id','source_row','depth_km')} for r in rows if r['depth_km']>100]
        if key=='ross':
            outputs[key]['relocated']={'rule':'nbranch > 1','full_rows':sum(r['nbranch']>1 for r in rows),
                'candidate_time_only_rows':sum(r['nbranch']>1 for r in time_only),
                'candidate_native_mask_rows':sum(r['nbranch']>1 for r in spatial)}
    anchors={}
    for name,eid in design['anchor_event_ids'].items():
        matches=[r for r in data['official_snapshot'] if r['native_id']==eid]
        if len(matches)!=1:raise ValueError(f'Anchor {eid}: {len(matches)} rows')
        anchors[name]=matches[0]
    t64=anchors['mw6_4']['time'];t71=anchors['mw7_1']['time']
    stages=[('before_mw6_4',start,t64),('first_hour_after_mw6_4',t64,t64+timedelta(hours=1)),
            ('later_between_large_events',t64+timedelta(hours=1),t71),
            ('first_hour_after_mw7_1',t71,t71+timedelta(hours=1)),('later_after_mw7_1',t71+timedelta(hours=1),end)]
    if not start<t64<t64+timedelta(hours=1)<t71<t71+timedelta(hours=1)<end:
        raise ValueError('Candidate window does not contain the five proposed stages')
    stages_out=[]
    for label,a,b in stages:
        counts={key:sum(within(r,a,b,bounds) for r in rows) for key,rows in data.items()}
        counts['ross_relocated']=sum(within(r,a,b,bounds) and r['nbranch']>1 for r in data['ross'])
        counts['official_earthquake']=sum(within(r,a,b,bounds) and r['event_type']=='earthquake' for r in data['official_snapshot'])
        stages_out.append({'stage':label,'start_utc':a.isoformat(),'end_utc':b.isoformat(),'hours':(b-a).total_seconds()/3600,'native_mask_rows':counts})
    selected={key:[r for r in rows if within(r,start,end,bounds)] for key,rows in data.items()}
    selected['ross_relocated']=[r for r in selected['ross'] if r['nbranch']>1]
    selected['official_earthquake']=[r for r in selected['official_snapshot'] if r['event_type']=='earthquake']
    diagnostic=cfg['reference_audit']['overlap_diagnostic'];comparisons=[]
    for left,right in diagnostic['pairs']:
        for dt in diagnostic['time_tolerances_s']:
            for dist in diagnostic['horizontal_tolerances_km']:
                comparisons.append({'left':left,'right':right,**overlap(selected[left],selected[right],dt,dist)})
    full_ids={r['native_id']:r for r in data['official_full']}
    snapshot_ids={r['native_id']:r for r in data['official_snapshot']}
    missing_ids=sorted(snapshot_ids.keys()-full_ids.keys())
    time_counts=Counter(r['time'] for r in data['official_snapshot'])
    duplicate_time_groups=[{
        'origin_time_utc':t,
        'records':[{k:r[k] for k in ('native_id','latitude','longitude','depth_km','magnitude','updated')}
                   for r in data['official_snapshot'] if r['time']==t],
        'identity_resolution':'unresolved; equal origin times alone do not establish duplicate events',
    } for t,n in sorted(time_counts.items()) if n>1]
    phase_path=case/cfg['reference_audit']['phase_source']['path']
    phase_sha=sha256(phase_path)
    if phase_sha!=cfg['reference_audit']['phase_source']['expected_sha256']:
        raise ValueError('Phase source checksum mismatch')
    phase=phase_summary(phase_path,start,end)
    phase.update(path=str(phase_path.relative_to(case)),sha256=phase_sha)
    result={'audit_version':1,'case_id':cfg['case_id'],'window_status':cfg['window_status'],
            'config_sha256':sha256(config_path),'candidate_window':window,
            'sources':outputs,'anchors':anchors,'stages':stages_out,'phase_auxiliary':phase,
            'official_snapshot_not_in_full_ids':missing_ids,'reference_overlap_diagnostics':comparisons,
            'official_duplicate_time_groups':duplicate_time_groups,
            'limitations':['Observed first/last events do not establish data availability or completeness.',
                           'Native numerical depth masks are not physically harmonized across datums.',
                           'No waveform access, published method reproduction, or evaluation freeze is asserted.',
                           'Overlap uses reciprocal-unique candidates and leaves ambiguity unresolved.']}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir',type=Path,default=CASE)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();case=args.case_dir.resolve()
    result=run(case)
    output=args.output or case/'analysis/reference_audit.json'
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,default=lambda v:v.isoformat())+'\n')
    print(f'Audited {len(result["sources"])} event products and one phase auxiliary -> {output}')


if __name__=='__main__':
    main()
