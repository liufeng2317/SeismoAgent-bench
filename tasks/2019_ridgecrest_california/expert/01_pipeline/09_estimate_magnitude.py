#!/usr/bin/env python3
"""Provisional ordinary-event ML; frozen picks/locations and read-only raw archive."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import concurrent.futures as cf
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import yaml
from threadpoolctl import threadpool_limits
from obspy import read, read_inventory, Stream, Trace, UTCDateTime
from obspy.signal.invsim import WOODANDERSON

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
EXP = HERE / 'export'
OUT = EXP / '09_estimate_magnitude'
ROOT = (HERE / '../../../benchmark_source/2019_ridgecrest_california/data/waveforms').resolve()
MAIN = {'gamma_0000046': 'M6.4', 'gamma_0005482': 'M7.1'}
INV = None
SETTINGS = dict(prefilter_hz=[0.1, 0.2, 20., 25.], block_seconds=3600,
                padding_seconds=60, minimum_snr=3., minimum_stations=3,
                maximum_epicentral_km=100., minimum_hypocentral_km=10.,
                maximum_station_mad=0.5, data_start_utc='2019-07-04T00:00:00Z',
                data_end_utc='2019-07-07T00:00:00Z', window='P-0.5 to P-0.5+2*(S-P)',
                wood_anderson_magnification=2080, simulate_pitsasim=False, workers_default=6)

def correction(r):
    return 1.11 * np.log10(r / 100.) + 0.00189 * (r - 100.) + 3.

def init():
    global INV
    threadpool_limits(limits=1)
    INV = read_inventory(str(ROOT / 'stations/earthscope.stationxml'))

def measure(job):
    instrument, rows, all_s = job
    net, sta, loc, fam = instrument.split('.')
    inv = INV.select(network=net, station=sta, location=loc, channel=fam+'?')
    files = sorted((ROOT / 'data' / f'{net}.{sta}').glob(f'{instrument}?__*.mseed'))
    # Read each daily horizontal record once per station. Never interpolate gaps.
    raw = Stream()
    used = []
    earliest = min(r['p_epoch'] for r in rows) // 3600 * 3600 - 60
    latest = (max(r['p_epoch'] for r in rows) // 3600 + 1) * 3600 + 120
    earliest = max(earliest, float(UTCDateTime(SETTINGS['data_start_utc'])))
    latest = min(latest, float(UTCDateTime(SETTINGS['data_end_utc']))-0.000001)
    for path in files:
        _, file_start, file_end = path.stem.split('__')
        if float(UTCDateTime(file_end)) <= earliest or float(UTCDateTime(file_start)) >= latest:
            continue
        channel = path.name.split('__')[0].split('.')[-1]
        if channel[-1] == 'Z':
            continue
        raw += read(str(path), starttime=UTCDateTime(earliest), endtime=UTCDateTime(latest))
        used.append(str(path.relative_to(ROOT)))
    raw.merge(method=0, fill_value=None)
    raw.trim(UTCDateTime(SETTINGS['data_start_utc']),
             UTCDateTime(SETTINGS['data_end_utc'])-0.000001, nearest_sample=False)
    results = []
    blocks = {}
    for row in rows:
        blocks.setdefault(int(row['p_epoch'] // 3600), []).append(row)
    for hour, batch in sorted(blocks.items()):
        begin, end = hour*3600-60, (hour+1)*3600+120
        block = raw.slice(UTCDateTime(begin), UTCDateTime(end)).copy().split()
        processed = []
        errors = []
        for tr in block:
            try:
                epochs = inv.select(channel=tr.stats.channel, starttime=tr.stats.starttime,
                                    endtime=tr.stats.endtime)
                channels = [c for n in epochs for s in n for c in s
                            if c.start_date <= tr.stats.starttime and
                            (c.end_date is None or c.end_date >= tr.stats.endtime)]
                if len(channels) != 1 or not channels[0].response:
                    raise ValueError('response_epoch_not_unique_or_incomplete')
                ch = channels[0]
                if abs(ch.dip) > 1 or tr.stats.sampling_rate <= 50:
                    raise ValueError('unsupported_orientation_or_rate')
                if tr.stats.npts < 12000:
                    continue
                tr.remove_response(inventory=epochs, output='VEL', pre_filt=SETTINGS['prefilter_hz'],
                                   water_level=None, zero_mean=True, taper=True, taper_fraction=0.01)
                tr.simulate(paz_simulate=WOODANDERSON, zero_mean=False, taper=False, pitsasim=False)
                if not np.isfinite(tr.data).all():
                    raise ValueError('nonfinite_response_output')
                processed.append((tr, float(ch.azimuth)))
            except Exception as exc:
                errors.append(f'{tr.id}: {type(exc).__name__}: {exc}')
        for row0 in batch:
            row = dict(row0)
            flags = []
            a, b, p = row['window_start_epoch'], row['window_end_epoch'], row['p_epoch']
            noise_a, noise_b = p-12, p-2
            others = all_s[(all_s[:, 0] != row['event_number'])]
            if ((others[:, 1] >= a) & (others[:, 1] <= b)).any():
                flags.append('overlapping_associated_S')
            if ((others[:, 1] >= noise_a) & (others[:, 1] <= noise_b)).any():
                flags.append('noise_contains_associated_S')
            candidates = [(tr, az) for tr, az in processed
                          if float(tr.stats.starttime)+30 <= noise_a and
                          float(tr.stats.endtime)-30 >= b]
            try:
                if len(candidates) != 2:
                    raise ValueError('horizontal_pair_or_padded_coverage_missing')
                arrays, raw_arrays, azimuths = [], [], []
                starts, rates = [], []
                for tr, az in candidates:
                    cut = tr.slice(UTCDateTime(noise_a), UTCDateTime(b))
                    arrays.append(cut.data)
                    starts.append(float(cut.stats.starttime)); rates.append(cut.stats.sampling_rate)
                    azimuths.append(az)
                    raw_cut = raw.select(id=tr.id).slice(UTCDateTime(a), UTCDateTime(b))
                    if len(raw_cut) != 1 or np.ma.is_masked(raw_cut[0].data):
                        raise ValueError('raw_gap_or_overlap')
                    raw_arrays.append(np.asarray(raw_cut[0].data))
                if len(set(map(len, arrays))) != 1 or max(starts)-min(starts) > 0.001 or len(set(rates)) != 1:
                    raise ValueError('horizontal_sample_alignment')
                angles = np.deg2rad(azimuths)
                matrix = np.column_stack([np.cos(angles), np.sin(angles)])
                if abs(np.linalg.det(matrix)) < 0.9:
                    raise ValueError('horizontal_orientation_geometry')
                ne = np.linalg.solve(matrix, np.asarray(arrays)) * 1000.  # WA trace metres -> mm
                fs, t0 = rates[0], starts[0]
                sig = ne[:, int(round((a-t0)*fs)):int(round((b-t0)*fs))+1]
                noise = ne[:, :int(round((noise_b-t0)*fs))+1]
                amplitudes = np.max(np.abs(sig), axis=1)
                noise_peak = np.max(np.abs(noise), axis=1)
                snr = amplitudes / np.maximum(noise_peak, np.finfo(float).tiny)
                if not np.isfinite(amplitudes).all() or min(amplitudes) <= 0:
                    raise ValueError('invalid_amplitude')
                # A conservative digitizer-plateau indicator, not a saturation diagnosis.
                plateau = False
                for x in raw_arrays:
                    extreme = (x == x.min()) | (x == x.max())
                    plateau |= bool(np.any(extreme[:-2] & extreme[1:-1] & extreme[2:] &
                                           (x[:-2] == x[1:-1]) & (x[1:-1] == x[2:])))
                if plateau: flags.append('raw_extreme_plateau')
                if snr.min() < SETTINGS['minimum_snr']: flags.append('low_snr')
                ml = float(np.mean(np.log10(amplitudes)) + correction(row['hypocentral_km']))
                row.update(amplitude_n_mm=amplitudes[0], amplitude_e_mm=amplitudes[1],
                           noise_n_mm=noise_peak[0], noise_e_mm=noise_peak[1], snr_min=snr.min(),
                           ml_station=ml, ml_gamma_geometry=ml-correction(row['hypocentral_km'])+
                           correction(row['gamma_hypocentral_km']), source_channels=';'.join(tr.id for tr, _ in candidates))
            except Exception as exc:
                flags.append(str(exc))
                row['processing_error'] = '; '.join(errors)
            row['flags'] = ';'.join(flags)
            row['accepted'] = not flags and 'ml_station' in row
            results.append(row)
    frame = pd.DataFrame(results)
    frame.to_csv(OUT / 'stations' / (instrument + '.csv'), index=False)
    return instrument, len(frame), int(frame.accepted.sum()), used

def prepare(limit):
    catalog = pd.read_csv(EXP / '05_review_catalog/event_quality.csv')
    catalog['mainshock_uncertainty'] = catalog.event_id.map(MAIN).fillna('').map(
        lambda x: 'depth_unresolved;arrival_and_waveform_limitations' if x else '')
    catalog['magnitude_status'] = np.where(catalog.provisional_quality.eq('provisionally_usable'),
                                           'pending', 'deferred_location_or_association_review')
    catalog.loc[catalog.event_id.isin(MAIN), 'magnitude_status'] = 'deferred_mainshock'
    eligible = catalog[catalog.magnitude_status.eq('pending')]
    if limit:
        eligible = eligible.iloc[np.linspace(0, len(eligible)-1, min(limit,len(eligible))).astype(int)]
        catalog.loc[catalog.magnitude_status.eq('pending') & ~catalog.event_id.isin(eligible.event_id),
                    'magnitude_status'] = 'not_in_pilot'
    picks = pd.read_csv(EXP / '03_associate_gamma/full/picks.csv')
    picks = picks[picks.event_id.notna()].copy()
    picks['epoch'] = pd.to_datetime(picks.time_utc, format='ISO8601', utc=True).astype('int64') / 1e9
    nll = pd.read_csv(EXP / '04_locate_nonlinloc/full/picks.csv')
    picks = picks.drop(columns='residual_s').merge(nll[['pick_id','residual_s']], on='pick_id', validate='one_to_one')
    stations = pd.read_csv(EXP / '03_associate_gamma/full/stations.csv').set_index('id')
    event_map = eligible.set_index('event_id').to_dict('index')
    jobs = []
    plan = []
    for instrument, group in picks.groupby('instrument_id'):
        station = stations.loc[instrument]
        all_s = group[group.phase.eq('S')][['event_id','epoch']].copy()
        all_s.event_id = all_s.event_id.str.split('_').str[-1].astype(int)
        rows = []
        for event_id, pair in group[group.event_id.isin(event_map)].groupby('event_id'):
            rec = dict(event_id=event_id, instrument_id=instrument)
            if set(pair.phase) != {'P','S'} or len(pair) != 2:
                rec['reason'] = 'requires_unique_associated_P_and_S'; plan.append(rec); continue
            pair = pair.set_index('phase')
            p, s = float(pair.loc['P','epoch']), float(pair.loc['S','epoch'])
            ev = event_map[event_id]
            epi = np.hypot(ev['x_km']-station['x(km)'], ev['y_km']-station['y(km)'])
            r = np.hypot(epi, ev['depth_km']-station['z(km)'])
            gr = np.linalg.norm([ev['gamma_x_km']-station['x(km)'], ev['gamma_y_km']-station['y(km)'],
                                 ev['gamma_depth_km']-station['z(km)']])
            if not (0.5 <= s-p <= 30 and epi <= 100 and r >= 10 and pair.residual_s.abs().max() <= 0.5):
                rec['reason'] = 'distance_SP_or_residual_gate'; plan.append(rec); continue
            rec['reason'] = 'scheduled'; plan.append(rec)
            rows.append(dict(event_id=event_id, instrument_id=instrument, event_number=int(event_id.split('_')[-1]),
                             p_pick_id=pair.loc['P','pick_id'], s_pick_id=pair.loc['S','pick_id'],
                             p_epoch=p, s_epoch=s, window_start_epoch=p-.5, window_end_epoch=p-.5+2*(s-p),
                             epicentral_km=epi, hypocentral_km=r, gamma_hypocentral_km=gr))
        if rows: jobs.append((instrument, rows, all_s.to_numpy(dtype=float)))
    pd.DataFrame(plan).to_csv(OUT/'measurement_plan.csv',index=False)
    return catalog, jobs

def report(catalog, records):
    station = pd.concat([pd.read_csv(OUT/'stations'/f'{r[0]}.csv') for r in records], ignore_index=True)
    station.to_csv(OUT/'station_magnitudes.csv',index=False)
    for event_id, group in station[station.accepted].groupby('event_id'):
        m = group.ml_station.median()
        mad = (group.ml_station-m).abs().median()
        index = catalog.index[catalog.event_id.eq(event_id)]
        catalog.loc[index,'ml_station_count'] = len(group)
        catalog.loc[index,'ml_station_mad'] = mad
        catalog.loc[index,'ml_provisional'] = m
        catalog.loc[index,'ml_gamma_geometry'] = group.ml_gamma_geometry.median()
        catalog.loc[index,'magnitude_status'] = ('provisional' if len(group)>=3 and mad<=0.5 else
                                                'review_station_support_or_dispersion')
    catalog.loc[catalog.magnitude_status.eq('pending'),'magnitude_status'] = 'no_accepted_amplitude'
    catalog['location_product'] = 'stage04_NLL_linear_model_not_final'
    catalog['model_uncertainty'] = 'layer_interpretation_not_resolved_for_catalog'
    catalog.to_csv(OUT/'catalog.csv',index=False)
    ordinary = catalog[catalog.provisional_quality.eq('provisionally_usable') &
                       ~catalog.event_id.isin(MAIN)].copy()
    ordinary.to_csv(OUT/'ordinary_events.csv',index=False)
    matches = pd.read_csv(EXP/'05_review_catalog/reference_matches.csv')
    pairs = matches[matches.matched & ~matches.ambiguous].merge(catalog[['event_id','ml_provisional','magnitude_status']],on='event_id')
    pairs = pairs[pairs.magnitude_status.eq('provisional')].copy()
    pairs['ml_difference'] = pairs.ml_provisional-pairs.reference_magnitude
    pairs.to_csv(OUT/'reference_comparison.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(1,3,figsize=(10,3),constrained_layout=True)
    good = catalog[catalog.magnitude_status.eq('provisional')]
    axes[0].hist(good.ml_provisional,bins=35,color='#34638b'); axes[0].set(xlabel='Provisional $M_L$',ylabel='Events')
    axes[1].scatter(good.ml_station_count,good.ml_station_mad,s=3,alpha=.2,color='#34638b')
    axes[1].set(xlabel='Accepted stations',ylabel='Station magnitude MAD')
    for name, group in pairs.groupby('catalog'):
        axes[2].scatter(group.reference_magnitude,group.ml_provisional,s=3,alpha=.25,label=name)
    axes[2].plot([-1,5],[-1,5],color='black',lw=.7)
    axes[2].set(xlabel='Reference magnitude (mixed scales)',ylabel='Provisional $M_L$'); axes[2].legend(markerscale=3,fontsize=7)
    for i, ax in enumerate(axes): ax.set_title(chr(97+i),loc='left',fontweight='bold')
    fig.savefig(OUT/'magnitude_overview.png',dpi=220); fig.savefig(OUT/'magnitude_overview.pdf'); plt.close(fig)
    counts = catalog.magnitude_status.value_counts().to_dict()
    summary = dict(event_count=len(catalog),status_counts={k:int(v) for k,v in counts.items()},
                   station_measurements=len(station),accepted_station_measurements=int(station.accepted.sum()),
                   provisional_median_ml=float(good.ml_provisional.median()),
                   reference_differences={k:dict(n=len(g),median=float(g.ml_difference.median())) for k,g in pairs.groupby('catalog')})
    (OUT/'summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False))
    return summary

def numerical_checks():
    """Forward a known velocity sine through a real response, then recover WA."""
    inv = read_inventory(str(ROOT/'stations/earthscope.stationxml')).select(
        network='CI', station='CCA', channel='HHN', time=UTCDateTime('2019-07-05'))
    response = inv.get_response('CI.CCA..HHN', UTCDateTime('2019-07-05'))
    results = []
    for frequency in (1., 5.):
        t = np.arange(24000)/100.
        h = response.get_evalresp_response_for_frequencies([frequency], output='VEL')[0]
        trace = Trace(np.real(1e-6*h*np.exp(2j*np.pi*frequency*t)), header=dict(
            network='CI', station='CCA', location='', channel='HHN', sampling_rate=100.,
            starttime=UTCDateTime('2019-07-05')))
        trace.remove_response(inventory=inv, output='VEL', pre_filt=SETTINGS['prefilter_hz'],
                              water_level=None, taper_fraction=.01)
        trace.simulate(paz_simulate=WOODANDERSON, zero_mean=False, taper=False, pitsasim=False)
        w = 2j*np.pi*frequency
        expected = 1e-6*2080*abs(w/np.prod([w-p for p in WOODANDERSON['poles']]))*1000
        measured = np.max(abs(trace.data[6000:18000]))*1000
        error = abs(measured/expected-1)
        assert error < .015, (frequency, error)
        results.append(dict(frequency_hz=frequency, expected_wa_mm=float(expected),
                            measured_wa_mm=float(measured), relative_error=float(error)))
    (OUT/'numerical_validation.yaml').write_text(yaml.safe_dump(dict(real_response_sine_recovery=results)))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workers',type=int,default=6); ap.add_argument('--limit',type=int,default=0)
    args=ap.parse_args()
    if args.workers < 1 or args.limit < 0: ap.error('workers must be positive; limit nonnegative')
    global OUT
    if args.limit: OUT=OUT/'pilot'
    (OUT/'stations').mkdir(parents=True,exist_ok=True)
    started=time.time()
    threadpool_limits(limits=1)
    assert abs(correction(100)-3)<1e-12
    assert abs((np.log10(10*2.)+correction(20))-(np.log10(2.)+correction(20))-1)<1e-12
    numerical_checks()
    print('Response/amplitude synthetic checks passed', flush=True)
    catalog,jobs=prepare(args.limit)
    print(f'{len(jobs)} instruments; {sum(len(j[1]) for j in jobs)} station measurements; {args.workers} CPU workers',flush=True)
    records=[]
    with cf.ProcessPoolExecutor(max_workers=args.workers,initializer=init) as pool:
        futures=[pool.submit(measure,j) for j in jobs]
        for future in cf.as_completed(futures):
            result=future.result(); records.append(result)
            print(f'[{len(records)}/{len(jobs)}] {result[0]}: {result[2]}/{result[1]} accepted',flush=True)
    summary=report(catalog,records)
    run=dict(settings=SETTINGS,workers=args.workers,pilot_event_limit=args.limit,elapsed_seconds=time.time()-started,
             input_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
             [Path(__file__),EXP/'05_review_catalog/event_quality.csv',EXP/'03_associate_gamma/full/picks.csv',
              EXP/'04_locate_nonlinloc/full/picks.csv',ROOT/'stations/earthscope.stationxml'] if p.is_relative_to(HERE)},
             stationxml_path=str(ROOT/'stations/earthscope.stationxml'),
             stationxml_sha256=hashlib.sha256((ROOT/'stations/earthscope.stationxml').read_bytes()).hexdigest(),
             waveform_files=sorted(set(p for record in records for p in record[3])),summary=summary)
    (OUT/'run.yaml').write_text(yaml.safe_dump(run,sort_keys=False))
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__': main()
