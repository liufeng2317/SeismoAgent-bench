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
    for f in inv['files']:
        for s in f['streams']:
            if UTCDateTime(s['start_utc'])>=b or UTCDateTime(s['last_sample_utc'])<a:continue
            source=root/f['path']
            if not source.is_file() or source.stat().st_size!=f['bytes']:raise ValueError(f'Stale file inventory: {f["path"]}')
            matched=[e for e in epochs[s['seed_id']] if (not e['effective_start'] or UTCDateTime(e['effective_start'])<=a)
                     and (not e['effective_end'] or UTCDateTime(e['effective_end'])>=b)
                     and s['sample_rates_hz']==[e['sample_rate_hz']]]
            if len(matched)!=1:raise ValueError(f'Ambiguous epoch/rate: {s["seed_id"]}')
            e=matched[0]
            if not e['response_present'] or not e['response_stages']:raise ValueError('Response metadata missing')
            station=e['network']+'.'+e['station'];family=e['channel'][:2]
            groups[station,e['location'],family].add(e['channel'][-1])
            rows.append(dict(path=f['path'],bytes=f['bytes'],seed_id=s['seed_id'],station_id=station,
                location=e['location'],family=family,component=e['channel'][-1],sample_rate_hz=e['sample_rate_hz'],
                latitude=e['latitude'],longitude=e['longitude'],elevation_m=e['elevation_m'],
                azimuth_deg=e['azimuth_deg'],dip_deg=e['dip_deg'],start_utc=str(a),end_utc=str(b)))
    instruments=[]
    for (sta,loc,family),components in sorted(groups.items()):
        three={'E','N','Z'}<=components or {'1','2','Z'}<=components
        selected=family in cfg['channel_policy']['primary_families'] and (three or not cfg['channel_policy']['require_three_components_for_first_pilot'])
        instruments.append(dict(station_id=sta,location=loc,family=family,components=','.join(sorted(components)),
            pilot_candidate=selected,orientation_action='rotate_12_from_metadata' if {'1','2'}<=components else 'verify_ENZ_orientation',
            reason='three_real_components' if selected else 'deferred_HN_or_incomplete_components'))
    chosen={(r['station_id'],r['location'],r['family']) for r in instruments if r['pilot_candidate']}
    for r in rows:r['pilot_candidate']=(r['station_id'],r['location'],r['family']) in chosen
    write_csv(out/'waveform_inputs.csv',rows);write_csv(out/'station_inputs.csv',instruments)
    (out/'config.yaml').write_text(config_path.read_text())
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [config_path,inventory_path,metadata_path]}
    text=f'''# Step 01: expert input preparation

Scope: {args.scope}; window: [{a}, {b}). Indexed {len(rows)} channel-file entries at {len({r['station_id'] for r in rows})} stations; {len(chosen)} instruments are primary three-component HH/EH pilot candidates.

The tables reuse existing header coverage and StationXML-derived metadata. File existence/size, response presence, and epoch/rate matching were checked; this step does not decode or preprocess waveforms, prove gap-free coverage, or freeze a final benchmark input. Channel orientation and simultaneous three-component coverage must be handled during picking. No reference event catalog or diagnostic labels were read.

HN and vertical-only instruments remain visible in the tables and are deferred for a separate input condition; they are not bad-data labels. Numbered horizontal channels require metadata-based rotation, not relabeling or copying. Stage 02 must explicitly decide how it handles any missing observations. Original files remain read-only.

`path` is relative to the configured external waveform root. Input-record hashes (not a new per-waveform hash pass):
'''
    text+='\n'.join(f'- `{name}`: `{digest}`' for name,digest in hashes.items())+'\n'
    (out/'README.md').write_text(text)
    print(f'{len(rows)} channel-file entries; {len(groups)} instruments; {len(chosen)} three-component HH/EH pilot candidates')
    print('Deferred:',', '.join(r['station_id']+'.'+r['family'] for r in instruments if not r['pilot_candidate']))


if __name__=='__main__':main()
