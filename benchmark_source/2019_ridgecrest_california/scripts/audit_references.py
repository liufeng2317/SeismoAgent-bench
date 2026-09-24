#!/usr/bin/env python3
"""Read-only source audit and conservative reference-overlap diagnostics.

Writes one JSON artifact; never changes source catalogs or declares a freeze.
Requires PyYAML to read the existing case configuration.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tarfile

import sys

# Keep the case-local command usable without an installation step.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from seismoagentbench.catalog import (utc, origin, finite, sha256, event, within,
                                     quantiles, horizontal_km, overlap, summary)
from seismoagentbench.sources import load_case, resolve_stages, select_subset, case_path

CASE = Path(__file__).resolve().parents[1]
UTC = timezone.utc


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
    config_path=case/'analysis/processing.yaml';cfg=load_case(case)
    design=cfg['scientific_design'];window=design['candidate_window'];bounds=window['native_comparison_bounds']
    start,end=utc(window['start_utc']),utc(window['end_utc'])
    audit=cfg['reference_audit']
    sources={key:cfg['sources'][key] for key in audit['event_sources']};outputs={};data={}
    for key,spec in sources.items():
        path=case_path(case,spec['path']);actual=sha256(path)
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
        matches=[r for r in data[audit['anchor_source']] if r['native_id']==eid]
        if len(matches)!=1:raise ValueError(f'Anchor {eid}: {len(matches)} rows')
        anchors[name]=matches[0]
    stages=resolve_stages(design, audit, {key: row['time'] for key,row in anchors.items()})
    subsets={key:select_subset(data[spec['source']],spec) for key,spec in audit['subsets'].items()}
    stages_out=[]
    for label,a,b in stages:
        counts={key:sum(within(r,a,b,bounds) for r in rows) for key,rows in data.items()}
        counts.update({key:sum(within(r,a,b,bounds) for r in rows) for key,rows in subsets.items()})
        stages_out.append({'stage':label,'start_utc':a.isoformat(),'end_utc':b.isoformat(),'hours':(b-a).total_seconds()/3600,'native_mask_rows':counts})
    selected={key:[r for r in rows if within(r,start,end,bounds)] for key,rows in data.items()}
    selected.update({key:[r for r in rows if within(r,start,end,bounds)] for key,rows in subsets.items()})
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
    phase_spec=cfg['sources'][audit['phase_source']]
    phase_path=case_path(case,phase_spec['path'])
    phase_sha=sha256(phase_path)
    if phase_sha!=phase_spec['expected_sha256']:
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
    print(f'Audited {len(result["sources"])} catalog products and one phase auxiliary -> {output}')


if __name__=='__main__':
    main()
