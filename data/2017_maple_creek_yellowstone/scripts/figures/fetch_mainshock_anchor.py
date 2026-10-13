#!/usr/bin/env python3
"""Stage the Maple Creek Mw 4.4 mainshock anchor from USGS ComCat.

The largest event of the 2017 Maple Creek swarm (Shelly & Hardebeck 2019 and
Pang et al. 2019 report Mw 4.4 on 2017-06-16 from the UUSS moment tensor) is
NOT contained in the staged USGS/UUSS operational baseline: that snapshot's
query mask (44.45–44.75°N, 110.55–110.15°W) does not cover the swarm area near
44.78°N, 111.03°W, so the staged CSV never rises above ML 1.86. This script
fetches the single ComCat event (uu60203137), cross-checks it against the
staged paper statements, and writes `analysis/mainshock_anchor.json` with full
provenance. Requires network access to earthquake.usgs.gov only.
"""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests

CASE = Path(__file__).resolve().parents[2]
BASELINE = CASE / ('data/catalogs/USGS_UUSS_COMCAT_2017/'
                   'USGS_UUSS_COMCAT_2017__catalog_operational_full.csv')
PAPER = CASE / ('references/SHELLY2019_GL081607/parsed/paper/'
                'SHELLY2019_GL081607__paper_reading.md')
OUT = CASE / 'analysis/mainshock_anchor.json'
QUERY = dict(format='geojson', starttime='2017-06-16T00:00:00',
             endtime='2017-06-17T00:00:00', minmagnitude=4.0, maxmagnitude=5.0,
             minlatitude=44.3, maxlatitude=45.0, minlongitude=-111.3,
             maxlongitude=-110.8)
EXPECTED_ID = 'uu60203137'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    session = requests.Session()
    session.trust_env = False
    response = session.get('https://earthquake.usgs.gov/fdsnws/event/1/query',
                           params=QUERY, timeout=(10, 60))
    response.raise_for_status()
    features = response.json()['features']
    assert len(features) == 1 and features[0]['id'] == EXPECTED_ID, \
        f'Expected exactly {EXPECTED_ID}, got {[f["id"] for f in features]}'
    props = features[0]['properties']
    lon, lat, depth = features[0]['geometry']['coordinates']
    time_utc = dt.datetime.fromtimestamp(props['time'] / 1000, dt.timezone.utc)
    row = dict(event_id=features[0]['id'], time_utc=time_utc.isoformat().replace('+00:00', 'Z'),
               latitude=lat, longitude=lon, depth_km=depth,
               comcat_magnitude=props['mag'], comcat_magnitude_type=props['magType'],
               status=props['status'])

    paper = PAPER.read_text()
    statements = [l.strip() for l in paper.splitlines()
                  if '4.4' in l and '2017-06-16' in l]
    assert statements, 'Staged paper statement not found'

    baseline_rows = list(csv.DictReader(BASELINE.open()))
    baseline_max = max(float(r['mag']) for r in baseline_rows)
    lats = [float(r['latitude']) for r in baseline_rows]
    lons = [float(r['longitude']) for r in baseline_rows]
    anchor = dict(
        schema_version=1,
        case_id=CASE.name,
        key='mainshock',
        anchor=dict(event_id=row['event_id'], time_utc=row['time_utc'],
                    magnitude=4.4, magnitude_type='mw',
                    latitude=row['latitude'], longitude=row['longitude'],
                    depth_km=row['depth_km'], status=row['status']),
        label='Mw 4.4',
        sources=[dict(role='primary', provider='USGS ANSS ComCat (single-event query)',
                      url='https://earthquake.usgs.gov/fdsnws/event/1/query',
                      parameters={k: str(v) for k, v in QUERY.items()},
                      retrieved_utc=time_utc.isoformat(), event=row)],
        cross_check=dict(
            moment_tensor_magnitude='UUSS Mw 4.4 (Shelly & Hardebeck 2019 fig. 2; '
                                    'Pang et al. 2019 fig. 1), used as the anchor magnitude',
            comcat_magnitude_ml=row['comcat_magnitude'],
            staged_paper_statement_found=True,
            staged_paper=str(PAPER.relative_to(CASE)),
            staged_paper_statement=statements[0][:300],
            baseline_snapshot=dict(path=str(BASELINE.relative_to(CASE)), sha256=sha(BASELINE),
                                   rows=len(baseline_rows), max_magnitude=baseline_max,
                                   latitude_range=[min(lats), max(lats)],
                                   longitude_range=[min(lons), max(lons)],
                                   note='Baseline query mask (44.45–44.75°N, 110.55–110.15°W) '
                                        'does not cover the swarm area; the Mw 4.4 event is '
                                        'absent from the staged snapshot.')),
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        note='Anchor parameters for figure scripts. The plotted magnitude is the UUSS '
             'moment magnitude; ComCat lists the same event as ML 4.36.',
    )
    OUT.write_text(json.dumps(anchor, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(anchor['anchor'], indent=2))
    print(f'Wrote {OUT.relative_to(CASE)}')


if __name__ == '__main__':
    main()
