#!/usr/bin/env python3
"""Prepare expert input tables from existing verified metadata; no preprocessing."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path
from obspy import UTCDateTime
import yaml

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.


GEOMETRY=('latitude','longitude','elevation_m','depth_m','azimuth_deg','dip_deg','sample_rate_hz')


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=HERE/'00_config/config.yaml')
    parser.add_argument('--scope',choices=['pilot','full'],default='pilot')
    args=parser.parse_args()
    config_path=args.config.resolve();cfg=yaml.safe_load(config_path.read_text())
    root=(HERE/cfg['data_root']).resolve()
    out=(HERE/cfg['export_root'])/'01_prepare_inputs'
    if args.scope=='full':out=out/'full'
    out.mkdir(parents=True,exist_ok=True)
    a,b=(UTCDateTime(cfg['candidate_window' if args.scope=='full' else 'pilot_window'][k]) for k in ['start_utc','end_utc'])
    c,d=(UTCDateTime(cfg['candidate_window'][k]) for k in ['start_utc','end_utc'])
    if not c<=a<b<=d:raise ValueError('Pilot must lie within the candidate window')
    inventory_path=root/'waveform_inventory.json';metadata_path=root/'stations/station_inventory.json'
    inv=json.loads(inventory_path.read_text());metadata=json.loads(metadata_path.read_text())
    epochs=defaultdict(list)
    for e in metadata['channel_epochs']:
        epochs['.'.join(e[k] for k in ['network','station','location','channel'])].append(e)
    rows=[];groups=defaultdict(set)
    excluded=set(cfg['channel_policy'].get('exclude_stations',[]))  # e.g. unverifiable coordinates
    for f in inv['files']:
        for s in f['streams']:
            if UTCDateTime(s['start_utc'])>=b or UTCDateTime(s['last_sample_utc'])<a:continue
            if '.'.join(s['seed_id'].split('.')[:2]) in excluded:continue
            source=root/f['path']
            if not source.is_file() or source.stat().st_size!=f['bytes']:raise ValueError(f'Stale file inventory: {f["path"]}')
            # Epochs overlapping the window. Several are accepted only when they
            # describe the same instrument geometry and rate and join without a
            # gap (GeoNet re-issued four Kaikoura epochs at 2016-12-08T00:00:00).
            matched=[e for e in epochs[s['seed_id']] if (not e['effective_start'] or UTCDateTime(e['effective_start'])<b)
                     and (not e['effective_end'] or UTCDateTime(e['effective_end'])>a)
                     and s['sample_rates_hz']==[e['sample_rate_hz']]]
            matched.sort(key=lambda e:e['effective_start'] or '')
            geometry={tuple(e[k] for k in GEOMETRY) for e in matched}
            joined=all(UTCDateTime(x['effective_end'])+1.5>=UTCDateTime(y['effective_start']) for x,y in zip(matched,matched[1:]))
            covered=matched and (not matched[0]['effective_start'] or UTCDateTime(matched[0]['effective_start'])<=a) \
                and (not matched[-1]['effective_end'] or UTCDateTime(matched[-1]['effective_end'])>=b)
            if not matched or len(geometry)!=1 or not joined or not covered:raise ValueError(f'Ambiguous epoch/rate: {s["seed_id"]}')
            e=matched[0]
            if not e['response_present'] or not e['response_stages']:raise ValueError('Response metadata missing')
            station=e['network']+'.'+e['station'];family=e['channel'][:2]
            groups[station,e['location'],family].add(e['channel'][-1])
            rows.append(dict(path=f['path'],bytes=f['bytes'],seed_id=s['seed_id'],station_id=station,
                location=e['location'],family=family,component=e['channel'][-1],sample_rate_hz=e['sample_rate_hz'],
                latitude=e['latitude'],longitude=e['longitude'],elevation_m=e['elevation_m'],
                # Verticals carry no azimuth in this inventory; IRIS convention is 0.
                azimuth_deg=e['azimuth_deg'] if e['azimuth_deg'] not in ('', None)
                             else (0.0 if float(e['dip_deg'])==-90.0 else None),
                dip_deg=e['dip_deg'],start_utc=str(a),end_utc=str(b)))
    instruments=[]
    for (sta,loc,family),components in sorted(groups.items()):
        three={'E','N','Z'}<=components or {'1','2','Z'}<=components
        # r3+: vertical-only instruments of the listed families are a separate,
        # explicit input condition (P picks only; stage 02).
        vertical=components=={'Z'} and family in cfg['channel_policy'].get('vertical_only_families',[])
        selected=family in cfg['channel_policy']['primary_families'] and (three or vertical or not cfg['channel_policy']['require_three_components_for_first_pilot'])
        condition='three_component' if three else ('vertical_only' if vertical else 'incomplete')
        instruments.append(dict(station_id=sta,location=loc,family=family,components=','.join(sorted(components)),
            pilot_candidate=selected,input_condition=condition,
            orientation_action='rotate_12_from_metadata' if {'1','2'}<=components else 'verify_ENZ_orientation',
            reason=('three_real_components' if three else 'vertical_only_P_picks') if selected else 'deferred_HN_or_incomplete_components'))
    # One primary instrument per site (config channel_policy.site_family_preference).
    preference=cfg['channel_policy'].get('site_family_preference',[])
    by_site={}
    for r in instruments:
        if r['pilot_candidate']:by_site.setdefault((r['station_id'],r['location']),[]).append(r)
    for candidates in by_site.values():
        if len(candidates)>1:
            # A three-component instrument outranks a vertical-only one at the same site.
            keep=min(candidates,key=lambda r:(r['input_condition']!='three_component',
                                              preference.index(r['family']) if r['family'] in preference else len(preference)))
            for r in candidates:
                if r is not keep:r['pilot_candidate']=False;r['reason']='duplicate_site_family'
    chosen={(r['station_id'],r['location'],r['family']) for r in instruments if r['pilot_candidate']}
    condition={(r['station_id'],r['location'],r['family']):r['input_condition'] for r in instruments}
    for r in rows:
        key=(r['station_id'],r['location'],r['family'])
        r['pilot_candidate']=key in chosen;r['input_condition']=condition[key]
    write_csv(out/'waveform_inputs.csv',rows);write_csv(out/'station_inputs.csv',instruments)
    (out/'config.yaml').write_text(config_path.read_text())
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [config_path,inventory_path,metadata_path]}
    text=f'''# Step 01: expert input preparation

Scope: {args.scope}; window: [{a}, {b}). Indexed {len(rows)} channel-file entries at {len({r['station_id'] for r in rows})} stations; {len(chosen)} instruments are primary primary HH/EH pilot candidates (three-component or vertical-only input condition) (one per site after the family-preference rule).

The tables reuse existing header coverage and StationXML-derived metadata. File existence/size, response presence, and epoch/rate matching were checked; this step does not decode or preprocess waveforms, prove gap-free coverage, or freeze a final benchmark input. Channel orientation and simultaneous three-component coverage must be handled during picking. No reference event catalog or diagnostic labels were read.

HN and vertical-only instruments remain visible in the tables and are deferred for a separate input condition; they are not bad-data labels. Numbered horizontal channels require metadata-based rotation, not relabeling or copying. Stage 02 must explicitly decide how it handles any missing observations. Original files remain read-only.

`path` is relative to the configured external waveform root. Input-record hashes (not a new per-waveform hash pass):
'''
    text+='\n'.join(f'- `{name}`: `{digest}`' for name,digest in hashes.items())+'\n'
    (out/'README.md').write_text(text)
    print(f'{len(rows)} channel-file entries; {len(groups)} instruments; {len(chosen)} primary HH/EH pilot candidates (three-component or vertical-only input condition)')
    print('Deferred:',', '.join(r['station_id']+'.'+r['family'] for r in instruments if not r['pilot_candidate']))


if __name__=='__main__':main()
