#!/usr/bin/env python3
"""Retrieve Ridgecrest station metadata and audit epochs; never request waveforms."""
import argparse
import hashlib
import json
import signal
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import pandas as pd
import requests

CASE = Path(__file__).resolve().parents[1]
OUT = CASE / 'data/waveforms/stations'
NS = {'s': 'http://www.fdsn.org/xml/station/1'}
START = datetime(2019, 7, 4, tzinfo=timezone.utc)
END = datetime(2019, 7, 7, tzinfo=timezone.utc)
PARAMS = dict(starttime='2019-07-04T00:00:00', endtime='2019-07-10T00:00:00',
              latitude=35.7695, longitude=-117.5993333, maxradius=1.5,
              level='response', format='xml', nodata=204)
SERVICES = {'scedc': 'https://service.scedc.caltech.edu/fdsnws/station/1/query',
            'earthscope': 'https://service.earthscope.org/fdsnws/station/1/query'}
# Manually read from the original local DOCX, Fig. S1, including its inset.
LIU = sorted(['CI.' + s for s in 'CGO CWC FUR SPG2 DAW WMF WRV2 WCS2 JRC2 WVP2 WRC2 MPM SLA WNM TOW2 CLC SRT WAS2 WHF WOR ISA WBS WBM LRL CCC DTP CCA TEH LDR EDW2 LMR2 HYS HAR APL GSC'.split()]
             + ['GS.CA01', 'GS.CA02', 'GS.CA03', 'GS.CA04', 'PB.B916', 'PB.B917', 'PB.B918', 'PB.B921', 'NN.GWY', 'NN.QSM'])


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def utc(value):
    if not value:
        return None
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)


def fetch(direct):
    path = OUT / 'requests.json'
    history = json.loads(path.read_text()) if path.exists() else []
    session = requests.Session()
    session.trust_env = not direct
    for provider, endpoint in SERVICES.items():
        params = dict(PARAMS)
        if provider == 'scedc':
            params.update(net='CI,GS,PB,NN', sta=','.join(sorted({n.split('.')[1] for n in LIU})))
        row = dict(provider=provider, endpoint=endpoint, parameters=params,
                   retrieved_utc=datetime.now(timezone.utc).isoformat(),
                   transport='direct' if direct else 'environment_proxy',
                   url=endpoint + '?' + urlencode(params))
        def deadline(_signum, _frame):
            raise TimeoutError('Station request exceeded 90 seconds')
        previous_handler = signal.signal(signal.SIGALRM, deadline)
        signal.alarm(90)
        try:
            response = session.get(endpoint, params=params, timeout=(10, 50))
            row['http_status'] = response.status_code
            response.raise_for_status()
            if response.status_code == 204:
                row['status'] = 'no_data'
            else:
                root = ET.fromstring(response.content)
                if root.tag != '{http://www.fdsn.org/xml/station/1}FDSNStationXML':
                    raise ValueError('Expected StationXML')
                # Content-addressed snapshots preserve earlier retrievals.
                checksum = hashlib.sha256(response.content).hexdigest()
                target = OUT / f'{provider}_{checksum[:12]}.stationxml'
                target.write_bytes(response.content)
                row.update(status='downloaded', path=target.name,
                           bytes=target.stat().st_size, sha256=checksum)
        except (requests.RequestException, ET.ParseError, ValueError, TimeoutError) as error:
            row.update(status='failed', error=type(error).__name__)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
        history.append(row)
        write(path, history)


def parse(path, provider):
    root = ET.parse(path).getroot()
    for net in root.findall('s:Network', NS):
        for sta in net.findall('s:Station', NS):
            for cha in sta.findall('s:Channel', NS):
                starts = [utc(e.get('startDate')) for e in (net, sta, cha) if e.get('startDate')]
                ends = [utc(e.get('endDate')) for e in (net, sta, cha) if e.get('endDate')]
                start = max(starts) if starts else None
                end = min(ends) if ends else None
                a = max(START, start) if start else START
                b = min(END, end) if end else END
                def value(name):
                    t = cha.findtext('s:' + name, namespaces=NS)
                    return float(t) if t is not None else None
                yield dict(network=net.get('code'), station=sta.get('code'),
                           location=cha.get('locationCode', ''), channel=cha.get('code'),
                           network_start=net.get('startDate'), station_start=sta.get('startDate'),
                           start=cha.get('startDate'), end=cha.get('endDate'),
                           effective_start=start.isoformat() if start else None,
                           effective_end=end.isoformat() if end else None,
                           latitude=value('Latitude'), longitude=value('Longitude'),
                           elevation_m=value('Elevation'), depth_m=value('Depth'),
                           azimuth_deg=value('Azimuth'), dip_deg=value('Dip'), sample_rate_hz=value('SampleRate'),
                           restricted_status=cha.get('restrictedStatus', sta.get('restrictedStatus', net.get('restrictedStatus'))),
                           response_present=cha.find('s:Response', NS) is not None,
                           response_stages=len(cha.findall('s:Response/s:Stage', NS)),
                           candidate_overlap_seconds=max(0, (b-a).total_seconds()), provider=provider)



def export_catalog_views(rows, latest, all_shelly, selected_shelly):
    """Keep paper/auxiliary selection distinct from the shared discovery inventory."""
    active = {r['network'] + '.' + r['station'] for r in rows if r['candidate_overlap_seconds'] > 0}
    specs = {
        'LIU2020_GL086189': (set(LIU), set(LIU), 'paper_station_labels',
                            'Original DOCX Fig. S1: 45 station labels; channel choices are not specified by this station list.'),
        'SHELLY2020_0220190309': (all_shelly, selected_shelly, 'auxiliary_phase_arrival_station_subset',
                                'Auxiliary phase release: station IDs selected by arrival time, not the original paper station inventory.'),
        'AWR2025_CALTECHDATA': (None, None, 'unresolved', 'Exact paper station list not verified; regional discovery inventory is not assigned to this catalog.'),
        'ROSS2019_SCIENCE': (None, None, 'unresolved', 'Exact paper station list requires missing method evidence; no automatic station assignment.'),
        'USGS_SCSN_COMCAT_2019': (None, None, 'unresolved', 'Operational event snapshot does not identify its complete waveform station inputs.'),
    }
    outputs = {}
    for catalog, (source_ids, requested, status, evidence) in specs.items():
        folder = OUT/'by_catalog'/catalog
        selected = requested & active if requested is not None else set()
        manifest = dict(catalog_id=catalog, status=status, evidence=evidence,
                        candidate_window=[START.isoformat(), END.isoformat()],
                        source_station_ids=sorted(source_ids) if source_ids is not None else None,
                        requested_candidate_station_ids=sorted(requested) if requested is not None else None,
                        metadata_present_station_ids=sorted(selected) if requested is not None else None,
                        missing_candidate_metadata=sorted(requested-active) if requested is not None else None,
                        channel_policy='All returned channels at selected stations with epoch overlap; not a reconstruction of the paper channel selection. Metadata overlap does not establish waveform availability.',
                        files={})
        if requested is not None:
            wanted = {(r['network'],r['station'],r['location'],r['channel'],r['start'],r['end'])
                      for r in rows if r['candidate_overlap_seconds']>0 and r['network']+'.'+r['station'] in selected}
            for provider, request in latest.items():
                root = ET.parse(OUT/request['path']).getroot()
                kept = 0
                for net in list(root.findall('s:Network', NS)):
                    for sta in list(net.findall('s:Station', NS)):
                        for cha in list(sta.findall('s:Channel', NS)):
                            identity = (net.get('code'),sta.get('code'),cha.get('locationCode',''),cha.get('code'),cha.get('startDate'),cha.get('endDate'))
                            if identity not in wanted:
                                sta.remove(cha)
                            else:
                                kept += 1
                        if not sta.findall('s:Channel', NS):
                            net.remove(sta)
                        for tag in ('TotalNumberChannels','SelectedNumberChannels'):
                            for child in list(sta.findall('s:'+tag, NS)):
                                sta.remove(child)
                    if not net.findall('s:Station', NS):
                        root.remove(net)
                    for tag in ('TotalNumberStations','SelectedNumberStations'):
                        for child in list(net.findall('s:'+tag, NS)):
                            net.remove(child)
                if kept:
                    folder.mkdir(parents=True, exist_ok=True)
                    target = folder/(provider+'.stationxml')
                    ET.register_namespace('', NS['s'])
                    ET.ElementTree(root).write(target, encoding='utf-8', xml_declaration=True)
                    manifest['files'][target.name] = dict(channel_epochs=kept,bytes=target.stat().st_size,sha256=digest(target),
                                                         shared_source=request['path'],shared_source_sha256=request['sha256'])
        write(folder/'selection.json', manifest)
        outputs[catalog] = dict(status=status, station_count=len(selected) if requested is not None else None,
                                selection_path=str((folder/'selection.json').relative_to(CASE)),
                                selection_sha256=digest(folder/'selection.json'), files=manifest['files'])
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--direct', action='store_true', help='Use direct HTTPS instead of environment proxy')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.download:
        fetch(args.direct)
    requests_log = json.loads((OUT/'requests.json').read_text())
    latest = {}
    for request in requests_log:
        if request['status'] == 'downloaded':
            latest[request['provider']] = request
    if not latest:
        raise SystemExit('No successful metadata snapshot; requests.json records failures')
    merged = {}
    for provider, request in latest.items():
        path = OUT/request['path']
        if digest(path) != request['sha256']:
            raise ValueError(f'Checksum mismatch: {path.name}')
        for row in parse(path, provider):
            row.pop('provider')
            # Merge identical descriptive metadata, not response transfer functions.
            # Original provider XMLs remain authoritative for response selection.
            key = json.dumps(row, sort_keys=True)
            if key not in merged:
                merged[key] = dict(row, providers=[])
            merged[key]['providers'].append(provider)
    rows = sorted(merged.values(), key=lambda r: (r['network'], r['station'], r['location'], r['channel'], r['start'] or ''))
    write(OUT/'channel_epochs.json', rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row['network'] + '.' + row['station']].append(row)
    active = {k for k,v in groups.items() if any(r['candidate_overlap_seconds'] > 0 for r in v)}
    same_epoch = defaultdict(list)
    for r in rows:
        same_epoch[(r['network'],r['station'],r['location'],r['channel'],r['start'],r['end'])].append(r)
    conflicts = [dict(identity=list(k), variants=v) for k,v in same_epoch.items() if len(v)>1]
    write(OUT/'metadata_conflicts.json', conflicts)
    phase = CASE/'data/catalogs/SHELLY2020_0220190309/raw/Ridgecrest_2019_correlation_phase_arrivals.csv'
    all_stations, selected_stations = set(), set()
    for chunk in pd.read_csv(phase, usecols=['network','station','arrival'], chunksize=500000):
        names = chunk['network'] + '.' + chunk['station']
        all_stations.update(names.unique())
        selected_stations.update(names[(chunk.arrival>=START.timestamp()) & (chunk.arrival<END.timestamp())].unique())
    stations = []
    for name, variants in sorted(groups.items()):
        valid = [r for r in variants if r['candidate_overlap_seconds']>0]
        stations.append(dict(id=name, liu_fig_s1=name in LIU,
                             shelly_auxiliary_arrival_window=name in selected_stations,
                             candidate_channel_epoch_present=bool(valid),
                             channels=sorted({r['location']+'.'+r['channel'] for r in valid}),
                             coordinate_variants=sorted({(r['latitude'],r['longitude'],r['elevation_m']) for r in variants}),
                             earliest_effective_start=min((r['effective_start'] for r in variants if r['effective_start']), default=None),
                             providers=sorted({p for r in variants for p in r['providers']})))
    write(OUT/'station_inventory.json', stations)
    catalog_views = export_catalog_views(rows, latest, all_stations, selected_stations)
    report = dict(catalog_views=catalog_views, candidate_window=['2019-07-04T00:00:00Z','2019-07-07T00:00:00Z'],
                  discovery_query=PARAMS,
                  query_reason='1.5 degree radius contains the paper 120-km circle and approximate 200-km square; extended through July 9 to detect later temporary-station deployment. Not a paper station-list reconstruction.',
                  semantics='Metadata epoch overlap only; not waveform availability. Identical descriptive channel epochs merged with providers retained; conflicting metadata retained. Responses remain in provider XML and are not assumed equivalent.',
                  requests=requests_log, inputs={str(phase.relative_to(CASE)):digest(phase)},
                  script_sha256=digest(Path(__file__)),
                  liu=dict(source='references/LIU2020_GL086189/supplement/Liu2020_Ridgecrest_SI.docx',
                           locator='Fig. S1, word/media/image2.jpeg, manually read labels including inset',
                           source_sha256=digest(CASE/'references/LIU2020_GL086189/supplement/Liu2020_Ridgecrest_SI.docx'),
                           station_epoch_summary=[r for r in stations if r['id'] in LIU],
                           paper_stations=LIU, metadata_present_in_candidate=sorted(set(LIU)&active),
                           missing_in_candidate=sorted(set(LIU)-active),
                           present_only_in_extended_query=sorted(set(LIU)&(set(groups)-active))),
                  shelly_auxiliary=dict(all_station_ids=sorted(all_stations),arrival_window_station_ids=sorted(selected_stations),
                                        missing_in_candidate=sorted(selected_stations-active),
                                        shared_with_liu=sorted(selected_stations & set(LIU))),
                  counts=dict(provider_snapshots=len(latest),station_ids=len(groups),candidate_station_ids=len(active),
                              channel_epoch_variants=len(rows),candidate_channel_epoch_variants=sum(r['candidate_overlap_seconds']>0 for r in rows),
                              conflicting_epoch_identities=len(conflicts)),
                  artifacts={str(p.relative_to(CASE)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in [OUT/'channel_epochs.json',OUT/'station_inventory.json',OUT/'metadata_conflicts.json']})
    write(CASE/'analysis/station_preparation.json',report)
    print(json.dumps(report['counts']))
    print('Liu missing in candidate:',report['liu']['missing_in_candidate'])
    print('Liu/Shelly auxiliary shared:',len(report['shelly_auxiliary']['shared_with_liu']))


if __name__ == '__main__':
    main()
