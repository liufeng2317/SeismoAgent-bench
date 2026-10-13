#!/usr/bin/env python3
"""Stage the Kaikoura in-window anchor from already-staged catalogs.

The v1 benchmark window (2016-12-01 to 12-09) sits in the early aftershock
period of the 2016-11-13 M7.8 Kaikoura mainshock, so the in-window anchor is
the largest aftershock inside the window, not the mainshock itself; the
mainshock is documented in `analysis/KAIKOURA2016_analysis.md` and the
station-availability window rationale. Both staged sources independently rank
GeoNet event 2016p913880 first in the window: the GeoNet operational baseline
gives M 5.5 and the Lanza et al. (2019) QuakeML relocation M 5.8. This script
re-derives that ranking from both files, cross-checks the shared EventID, and
writes `analysis/mainshock_anchor.json` so the figure scripts never hard-code
event parameters. The operational solution is kept as the anchor and the
relocation is recorded for provenance, matching the Magna/Kilauea anchor
convention. No network access; parsing the 135 MB QuakeML takes a few minutes.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from obspy import read_events, UTCDateTime

CASE = Path(__file__).resolve().parents[2]
GEONET = CASE / ('data/catalogs/GEONET_2016_KAIKOURA/'
                 'GEONET_2016_KAIKOURA__catalog_operational_full.txt')
LANZA = CASE / 'data/catalogs/LANZA2019_GL082780/raw/grl59060-sup-0003-ds01.xml'
WINDOW = (UTCDateTime('2016-12-01T00:00:00Z'), UTCDateTime('2016-12-09T00:00:00Z'))
MIN_SEPARATION = 0.5  # magnitude gap required between the anchor and the runner-up


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geonet_in_window(path):
    with path.open() as f:
        header = f.readline().lstrip('#').strip().split(' | ')
        for line in f:
            row = dict(zip(header, line.rstrip('\n').split('|')))
            if WINDOW[0] <= UTCDateTime(row['Time']) < WINDOW[1]:
                yield row


def lanza_origin(event):
    origin = event.preferred_origin()
    if origin is None and event.origins:
        origin = event.origins[0]
    return origin


def lanza_magnitude(event):
    magnitude = event.preferred_magnitude()
    if magnitude is None and event.magnitudes:
        magnitude = event.magnitudes[0]
    return magnitude


def main():
    operational = sorted(geonet_in_window(GEONET),
                         key=lambda r: -float(r['Magnitude']))
    assert len(operational) > 1, 'operational catalog has no in-window events'
    gap = float(operational[0]['Magnitude']) - float(operational[1]['Magnitude'])
    assert gap >= MIN_SEPARATION, f'ambiguous operational ranking, gap {gap}'
    row = operational[0]

    print(f'Parsing {LANZA.name} ({LANZA.stat().st_size / 1e6:.0f} MB)...', flush=True)
    catalog = read_events(str(LANZA))
    relocated = []
    for event in catalog:
        origin = lanza_origin(event)
        if origin is not None and WINDOW[0] <= origin.time < WINDOW[1]:
            relocated.append(event)
    relocated.sort(key=lambda ev: -(lanza_magnitude(ev).mag if lanza_magnitude(ev) else -9))
    assert len(relocated) > 1, 'Lanza catalog has no in-window events'
    lanza = relocated[0]
    lanza_id = lanza.resource_id.id.split('/')[-1]
    lanza_gap = (lanza_magnitude(lanza).mag
                 - (lanza_magnitude(relocated[1]).mag if lanza_magnitude(relocated[1])
                    else -9))
    assert lanza_gap >= MIN_SEPARATION, f'ambiguous Lanza ranking, gap {lanza_gap}'
    assert lanza_id == row['EventID'], f'catalogs disagree on the anchor: {lanza_id} vs {row["EventID"]}'

    origin = lanza_origin(lanza)
    magnitude = lanza_magnitude(lanza)
    delta_seconds = float(origin.time - UTCDateTime(row['Time']))
    cross_check = dict(
        lanza_event_id=lanza_id,
        lanza_origin_time_utc=str(origin.time),
        origin_time_delta_seconds=delta_seconds,
        latitude_delta_deg=round(origin.latitude - float(row['Latitude']), 6),
        longitude_delta_deg=round(origin.longitude - float(row['Longitude']), 6),
        depth_delta_km=round((origin.depth or 0) / 1000 - float(row['Depth/km']), 3),
        lanza_magnitude=float(magnitude.mag),
        lanza_magnitude_type=str(magnitude.magnitude_type),
        in_window_events=dict(operational_full=len(operational),
                              lanza_quakeml=len(relocated)),
    )

    doc = dict(
        schema_version=1,
        case_id=CASE.name,
        key='anchor',
        anchor=dict(event_id=row['EventID'], time_utc=row['Time'] + 'Z',
                    magnitude=float(row['Magnitude']), magnitude_type=row['MagType'],
                    latitude=float(row['Latitude']), longitude=float(row['Longitude']),
                    depth_km=float(row['Depth/km'])),
        label=f'M {float(row["Magnitude"]):.1f}',
        sources=[
            dict(role='primary', path=str(GEONET.relative_to(CASE)),
                 sha256=sha(GEONET),
                 provider='GeoNet operational catalogue (GNS), in-window ranking'),
            dict(role='cross_check', path=str(LANZA.relative_to(CASE)),
                 sha256=sha(LANZA),
                 provider='Lanza et al. (2019) relocated QuakeML, in-window ranking'),
        ],
        cross_check=cross_check,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        note=('Anchor parameters for figure scripts. The v1 window deliberately '
              'excludes the 2016-11-13 M7.8 mainshock, so the anchor is the largest '
              'in-window event (an aftershock near Seddon/Cape Campbell). Both staged '
              'sources rank the same EventID first; the operational M 5.5 is kept as '
              'the anchor and the relocated M 5.8 is recorded but not substituted.'),
    )
    out = CASE / 'analysis/mainshock_anchor.json'
    out.write_text(json.dumps(doc, indent=2) + '\n')
    print(f'Anchor {doc["anchor"]["event_id"]} M {doc["anchor"]["magnitude"]} '
          f'{doc["anchor"]["time_utc"]}; wrote {out}')
    print(f'In-window events: operational {len(operational)}, Lanza {len(relocated)}; '
          f'origin-time delta {delta_seconds:.3f} s')


if __name__ == '__main__':
    main()
