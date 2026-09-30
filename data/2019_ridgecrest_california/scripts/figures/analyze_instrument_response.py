#!/usr/bin/env python3
"""Audit stored candidate-channel responses and demonstrate ObsPy restitution."""
from pathlib import Path
import csv
import json
import warnings
from datetime import datetime, timezone

import numpy as np
from obspy import read, read_inventory, UTCDateTime, __version__ as obspy_version
from scipy.signal import welch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_catalog_comparison import publication_style, save_figure

CASE = Path(__file__).resolve().parents[2]
ROOT = CASE / 'data/waveforms'
OUT = CASE / 'analysis/figures/instrument_response'
PRE_FILT = (.5, 1., 15., 20.)
SEEDS = ['CI.CCC..HHZ', 'CI.APL..HNZ', 'CI.WRC2..HHZ']
EVENT = UTCDateTime('2019-07-06T03:19:53.040Z')


def audit(inv, index):
    observed = {}
    for row in index['files']:
        if not row['in_candidate_window']:
            continue
        for s in row['streams']:
            seed = s['seed_id']
            a = max(UTCDateTime(s['start_utc']), UTCDateTime(index['candidate']['start_utc']))
            b = min(UTCDateTime(s['last_sample_utc']), UTCDateTime(index['candidate']['end_utc']))
            item = observed.setdefault(seed, [a, b, set()])
            item[0], item[1] = min(item[0], a), max(item[1], b)
            item[2].update(s['sample_rates_hz'])
    rows = []
    for seed, (start, end, rates) in sorted(observed.items()):
        net, sta, loc, cha = seed.split('.')
        matches = [ch for network in inv.select(network=net, station=sta, location=loc, channel=cha)
                   for station in network for ch in station
                   if (ch.start_date is None or ch.start_date <= start)
                   and (ch.end_date is None or ch.end_date >= end)
                   and rates == {float(ch.sample_rate)}]
        row = dict(seed_id=seed, start_utc=str(start), last_sample_utc=str(end),
                   sample_rates_hz=';'.join(map(str, sorted(rates))), matching_epochs=len(matches),
                   status='failed', response_stages=0, input_units='', output_units='',
                   sensitivity='', sensitivity_frequency_hz='', azimuth_deg='', dip_deg='',
                   epoch_start='', epoch_end='', warning='')
        try:
            if len(matches) != 1:
                raise ValueError('Expected one unambiguous response epoch covering observed bounds')
            ch = matches[0]
            response = ch.response
            sensitivity = response.instrument_sensitivity
            if not response.response_stages or not np.isfinite(sensitivity.value) or sensitivity.value <= 0:
                raise ValueError('Missing stages or invalid sensitivity')
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                values = response.get_evalresp_response_for_frequencies(np.geomspace(.5, 20, 100), output='VEL')
            if not np.all(np.isfinite(values)) or np.any(np.abs(values) == 0):
                raise ValueError('Nonfinite or zero response inside trial frequency band')
            row.update(status='passed', response_stages=len(response.response_stages),
                       input_units=sensitivity.input_units, output_units=sensitivity.output_units,
                       sensitivity=sensitivity.value, sensitivity_frequency_hz=sensitivity.frequency,
                       azimuth_deg=ch.azimuth, dip_deg=ch.dip,
                       epoch_start=str(ch.start_date), epoch_end=str(ch.end_date),
                       warning=' | '.join(str(w.message) for w in caught))
        except Exception as exc:
            row['warning'] = str(exc)
        rows.append(row)
    with (OUT/'response_audit.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, lineterminator='\n', fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return rows


def examples(inv):
    arrays, notes = {}, []
    fig, axes = plt.subplots(3, 3, figsize=(7.09, 6.2), layout='constrained')
    for i, seed in enumerate(SEEDS):
        station = '.'.join(seed.split('.')[:2])
        source = ROOT/'data'/station/f'{seed}__20190706T000000Z__20190707T000000Z.mseed'
        st = read(str(source), starttime=EVENT-120, endtime=EVENT+240).select(id=seed)
        st.merge(method=-1)
        if len(st) != 1:
            raise ValueError(f'{seed}: example contains a gap; do not interpolate')
        raw = st[0]
        response = inv.get_response(seed, raw.stats.starttime)
        velocity = raw.copy().detrend('linear')
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            velocity.remove_response(inventory=inv, output='VEL', pre_filt=PRE_FILT,
                                     water_level=None, zero_mean=True, taper=True, taper_fraction=.05)
        if not np.all(np.isfinite(velocity.data)):
            raise ValueError(f'{seed}: nonfinite corrected output')
        if len(raw) != len(velocity) or raw.stats.starttime != velocity.stats.starttime:
            raise ValueError('Response removal changed sample grid')
        t = raw.times(reftime=EVENT)
        mask = (t >= -30) & (t <= 120)
        axes[i,0].plot(t[mask], raw.data[mask], color='#444444', lw=.45, rasterized=True)
        axes[i,1].plot(t[mask], velocity.data[mask], color='#0072B2', lw=.45, rasterized=True)
        f, psd = welch(velocity.data[mask], fs=raw.stats.sampling_rate, nperseg=4096)
        axes[i,2].loglog(f[1:], psd[1:], color='#0072B2', lw=.8)
        axes[i,0].set(title=seed, ylabel='Counts', xlim=(-30,120))
        axes[i,1].set(ylabel='Velocity (m/s)', xlim=(-30,120))
        axes[i,2].set(ylabel='PSD ((m/s)²/Hz)', xlim=(.1,50))
        for j in [0,1]:
            axes[i,j].ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
        prefix = f'trace_{i}'
        arrays.update({prefix+'_seed_id':seed, prefix+'_time_since_origin_s':t,
                       prefix+'_raw_counts':raw.data, prefix+'_velocity_m_s':velocity.data,
                       prefix+'_source_path':str(source.relative_to(CASE))})
        notes.append(dict(seed_id=seed, peak_velocity_m_s=float(np.max(np.abs(velocity.data[mask]))),
                          warnings=[str(w.message) for w in caught]))
    for ax in axes[-1,:2]: ax.set_xlabel('Time since Mw 7.1 (s)')
    axes[-1,2].set_xlabel('Frequency (Hz)')
    save_figure(fig, OUT/'01_response_removed'); plt.close(fig)
    arrays.update(origin_utc=str(EVENT),pre_filt_hz=np.array(PRE_FILT),output_units='m/s',
                  water_level='None', obspy_version=obspy_version,
                  processing='linear detrend; remove_response zero_mean=True taper=True taper_fraction=0.05',
                  response_source='data/waveforms/stations/earthscope.stationxml')
    np.savez_compressed(OUT/'response_examples.npz', **arrays)
    fig, ax = plt.subplots(figsize=(7.09,2.7), layout='constrained')
    frequency = np.geomspace(.1,49,400)
    for seed in SEEDS:
        resp = inv.get_response(seed, EVENT).get_evalresp_response_for_frequencies(frequency,output='VEL')
        ax.loglog(frequency,np.abs(resp),label=seed)
    ax.set(xlabel='Frequency (Hz)',ylabel='Response amplitude (counts / (m/s))')
    ax.legend(frameon=False)
    save_figure(fig,OUT/'02_response_curves'); plt.close(fig)
    return notes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads((ROOT/'waveform_inventory.json').read_text())
    inv = read_inventory(str(ROOT/'stations/earthscope.stationxml'))
    rows = audit(inv,index)
    passed = sum(r['status']=='passed' for r in rows)
    print(f'Response audit: {passed}/{len(rows)} passed',flush=True)
    if passed != len(rows):
        raise RuntimeError('Missing/ambiguous/unusable responses: see response_audit.csv; refresh exact channels using download_observations.py --kind stations')
    with publication_style():
        notes = examples(inv)
    text = f'''# Ridgecrest instrument response audit and trial removal

Generated: {datetime.now(timezone.utc).isoformat()}; ObsPy {obspy_version}.

## Availability

The previously downloaded `data/waveforms/stations/earthscope.stationxml` already contains usable response stages for **{passed}/{len(rows)} observed candidate channels**. No additional download was needed. This file is in the shared external archive through the case waveform symlink; it is not a second local copy. This result is restricted to the current candidate inventory, not every regional station or every published catalog input.

`response_audit.csv` records exact NSLC, observed time bounds, sample rate, matching epoch count, stage count, sensitivity and units, orientation, warnings and status. Each response epoch must cover the observed bounds and match the rate unambiguously. A 100-point logarithmic frequency grid from 0.5 to 20 Hz must evaluate to finite, nonzero velocity responses. This is a numerical/metadata usability check, not an independent calibration or sensor operating-range certification. Multiple epochs across an observed span are deliberately rejected for explicit review instead of silently selecting one.

## Removal trial

[Raw counts, corrected velocity and corrected spectra](01_response_removed.png) ([PDF](01_response_removed.pdf)); [response curves](02_response_curves.png) ([PDF](02_response_curves.pdf)).

Three vertical channels around the Mw 7.1 origin (2019-07-06 03:19:53.040 UTC) are processed over −120 to +240 s; plots show −30 to +120 s. Adjacent segments may merge, but a gap aborts this example. Original samples are read-only. Linear detrending precedes ObsPy `Trace.remove_response(inventory=inv, output="VEL", pre_filt=(0.5, 1, 15, 20), water_level=None, zero_mean=True, taper=True, taper_fraction=0.05)`. Output is m/s for both native HH velocity and HN acceleration inputs. No extra bandpass, resampling, normalization or rotation is applied. The frequency taper passes 1–15 Hz and tapers to zero at 0.5 and 20 Hz; these exploratory settings are not frozen processing parameters. Welch PSD uses the displayed corrected data, Hann windows of 4096 samples, 50% overlap, constant detrending and density scaling.

We use `water_level=None` with an explicit frequency taper because requesting velocity from an accelerometer can otherwise suppress wanted frequencies with a water-level cutoff; see the [ObsPy remove_response documentation](https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html). This does not validate the frequency band for every instrument or eliminate edge effects. The earlier 2–12 Hz counts-filtering figure uses different processing and is not a controlled response-only comparison.

`response_examples.npz` is one small derived demonstration bundle with numeric raw/corrected arrays, sample times, source paths, units and processing settings (load with `numpy.load(..., allow_pickle=False)`). It is outside the raw archive. No full-day processed waveform files or duplicate response JSON files are generated.

## Interpretation

Response removal ran successfully on all three examples, preserving sample counts and start times with finite outputs. It does not restore saturation-distorted signal. CI.CCC and CI.WRC2 mainshock intervals remain suspected saturation cases from the prior raw-waveform review; calibrated values there must not be accepted as reliable peak ground velocity. Different stations also record different propagation/site effects; matching units does not make them identical inputs. Next, validate operating ranges and select reliable intervals before amplitude analysis or freezing preprocessing.

'''
    text += 'Trial diagnostics (displayed-window maxima; not validated PGV):\n\n'
    text += '\n'.join(f'- `{n["seed_id"]}`: max |velocity| {n["peak_velocity_m_s"]:.6g} m/s; warnings: {n["warnings"] or "none"}.' for n in notes)+'\n'
    (OUT/'README.md').write_text(text)
    print('Response examples and figures written to analysis/figures/instrument_response',flush=True)


if __name__=='__main__':
    main()
