#!/usr/bin/env python3
"""Stage the Magna M5.7 mainshock anchor from already-staged catalogs.

The 2020-03-18 13:09:31.530 UTC M5.7 mainshock is present in both staged
sources: the USGS/UUSS ComCat operational baseline (event uu60363602) and the
Pang et al. (2020) relocated primary catalog (first row, magnitude 5.67). This
script cross-checks the two rows and writes `analysis/mainshock_anchor.json`
so the figure scripts never hard-code event parameters. No network access.
"""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CASE = Path(__file__).resolve().parents[2]
COMCAT = CASE / ('data/catalogs/USGS_UUSS_COMCAT_2020/'
                 'USGS_UUSS_COMCAT_2020__catalog_operational_full.csv')
PANG = CASE / 'data/catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_primary.txt'
OUT = CASE / 'analysis/mainshock_anchor.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    row = next(r for r in csv.DictReader(COMCAT.open()) if r['id'] == 'uu60363602')
    comcat = dict(event_id=row['id'], time_utc=row['time'],
                  magnitude=float(row['mag']), magnitude_type=row['magType'],
                  latitude=float(row['latitude']), longitude=float(row['longitude']),
                  depth_km=float(row['depth']), status=row['status'])

    lines = PANG.read_text().splitlines()
    header = next(i for i, l in enumerate(lines) if l.lower().startswith('date'))
    cols = [c.lower() for c in lines[header].split()]
    cells = lines[header + 1].split()
    pang = dict(zip(cols, cells))

    # Pang writes 'YYYY-MM-DD HH:MM:SS.sss'; ComCat writes ISO-8601 with T/Z.
    pang_time = pang['date'] + ' ' + pang['time']
    comcat_time = comcat['time_utc'].replace('T', ' ').rstrip('Z')
    checks = dict(
        pang_origin_time_utc=pang_time,
        time_matches=pang_time == comcat_time,
        latitude_delta_deg=abs(float(pang['lat']) - comcat['latitude']),
        longitude_delta_deg=abs(float(pang['lon']) - comcat['longitude']),
        depth_delta_km=abs(float(pang['dep']) - comcat['depth_km']),
        pang_magnitude=float(pang['mag']),
    )
    assert checks['time_matches'], 'Anchor time differs between staged sources'
    assert checks['latitude_delta_deg'] < 2e-3 and checks['longitude_delta_deg'] < 2e-3
    assert checks['depth_delta_km'] < 0.5, checks['depth_delta_km']

    anchor = dict(
        schema_version=1,
        case_id=CASE.name,
        key='mainshock',
        anchor=comcat,
        label=f"M {comcat['magnitude']:.1f}",
        sources=[
            dict(role='primary', path=str(COMCAT.relative_to(CASE)),
                 sha256=sha(COMCAT), provider='USGS ANSS ComCat / UUSS operational baseline'),
            dict(role='cross_check', path=str(PANG.relative_to(CASE)),
                 sha256=sha(PANG), provider='Pang et al. (2020) relocated primary catalog'),
        ],
        cross_check=checks,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        note='Anchor parameters for figure scripts; both staged rows refer to the '
             'same event (ComCat id uu60363602). The relocated catalog magnitude '
             '5.67 is its own solution and is not substituted for the operational M 5.7.',
    )
    OUT.write_text(json.dumps(anchor, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(anchor['anchor'], indent=2))
    print('Cross-check:', checks)
    print(f'Wrote {OUT.relative_to(CASE)}')


if __name__ == '__main__':
    main()
