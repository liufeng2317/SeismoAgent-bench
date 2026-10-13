#!/usr/bin/env python3
"""Stage the Kilauea M6.9 mainshock anchor from USGS ComCat.

The 2018-05-04 22:32:54.650 UTC Mw 6.9 caldera-flank event (hv70116556) is
absent from the staged HVO operational baseline snapshot, which tops out at
M 5.4 despite covering 2018-04-29 through 2018-08-07 (40,095 rows). This
script fetches the single ComCat event, cross-checks it against the staged
Wei et al. (2022) catalog S1 row for the same origin time, and writes
`analysis/mainshock_anchor.json` with full provenance. Requires network access
to earthquake.usgs.gov only.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests

CASE = Path(__file__).resolve().parents[2]
WEI = CASE / 'data/catalogs/WEI2022_EA001979/WEI2022_EA001979__catalog_S1.txt'
BASELINE = CASE / ('data/catalogs/USGS_HVO_COMCAT_2018/'
                   'USGS_HVO_COMCAT_2018__catalog_operational_full.csv')
OUT = CASE / 'analysis/mainshock_anchor.json'
QUERY = dict(format='geojson', starttime='2018-05-04T22:00:00',
             endtime='2018-05-04T23:00:00', minmagnitude=6.0, maxmagnitude=7.5,
             minlatitude=19.0, maxlatitude=20.0, minlongitude=-156.0,
             maxlongitude=-154.0)
EXPECTED_ID = 'hv70116556'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wei_cross_check(anchor_time):
    """Same-event row in the staged Wei et al. (2022) detection catalog."""
    best = None
    for line in WEI.read_text().splitlines():
        if line.startswith('SourceTime') or not line.strip():
            continue
        c = line.split()
        when = dt.datetime.fromisoformat(c[0]).replace(tzinfo=dt.timezone.utc)
        delta = abs((when - anchor_time).total_seconds())
        if delta <= 5 and (best is None or delta < best['time_delta_s']):
            best = dict(source=str(WEI.relative_to(CASE)), sha256=sha(WEI),
                        time_utc=c[0], time_delta_s=delta,
                        latitude=float(c[1]), longitude=float(c[2]),
                        depth_km=float(c[3]), magnitude=float(c[11]),
                        magnitude_type=c[12])
    return best


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
    anchor = dict(
        schema_version=1,
        case_id=CASE.name,
        key='mainshock',
        anchor=dict(event_id=features[0]['id'],
                    time_utc=time_utc.isoformat().replace('+00:00', 'Z'),
                    magnitude=props['mag'], magnitude_type=props['magType'],
                    latitude=lat, longitude=lon, depth_km=depth, status=props['status']),
        label=f"M {props['mag']:.1f}",
        sources=[dict(role='primary', provider='USGS ComCat / HVO (single-event query)',
                      url='https://earthquake.usgs.gov/fdsnws/event/1/query',
                      parameters={k: str(v) for k, v in QUERY.items()},
                      retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat())],
        cross_check=dict(
            wei2022=wei_cross_check(time_utc),
            baseline_snapshot=dict(path=str(BASELINE.relative_to(CASE)), sha256=sha(BASELINE),
                                   note='The Mw 6.9 event is absent from the staged '
                                        'operational baseline snapshot (max magnitude 5.4).')),
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        note='Anchor parameters for figure scripts. The staged Wei et al. (2022) '
             'detection catalog contains the same origin time; its location and '
             'local magnitude (5.31 l) are that catalog\'s own solution and are '
             'recorded as a cross-check only.',
    )
    assert anchor['cross_check']['wei2022'], 'No Wei (2022) row within 5 s of the anchor'
    OUT.write_text(json.dumps(anchor, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(anchor['anchor'], indent=2))
    print('Wei cross-check:', json.dumps(anchor['cross_check']['wei2022'], indent=2))
    print(f'Wrote {OUT.relative_to(CASE)}')


if __name__ == '__main__':
    main()
