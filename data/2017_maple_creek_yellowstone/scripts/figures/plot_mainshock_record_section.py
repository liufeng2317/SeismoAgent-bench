#!/usr/bin/env python3
"""Distance-ordered Maple Creek mainshock record sections; never modify raw waveforms.

Adapted from the Ridgecrest record-section script: one native vertical channel
per station (HHZ preferred, then EHZ, then BHZ), ordered by WGS84
epicentral distance. Raw-counts and response-corrected velocity panels are
independently normalized per channel. Gaps stay blank; the anchor comes from
`analysis/mainshock_anchor.json`.
"""
import csv
import hashlib
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from obspy import read, read_inventory, UTCDateTime
from obspy.geodetics import gps2dist_azimuth

from figure_style import publication_style, save_figure

CASE = Path(__file__).resolve().parents[2]
ROOT = CASE / 'data/waveforms'
OUT = CASE / 'analysis/figures/waveform_examples'
FAMILY_COLORS = {'HH': '#0072B2', 'EH': '#009E73', 'BH': '#8B4C9D'}
FAMILY_ORDER = {'HH': 0, 'EH': 1, 'BH': 2}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pre_filt(sample_rate):
    # Water-level corners stay clear of the Nyquist frequency for low-rate channels.
    return (.5, 1., 15., 20.) if sample_rate >= 80 else (.4, .8, 10., 14.)


def main():
    anchor_doc = json.loads((CASE / 'analysis/mainshock_anchor.json').read_text())
    anchor = anchor_doc['anchor']
    origin = UTCDateTime(anchor['time_utc'])
    label = f'M {anchor["magnitude"]:.1f}'
    stem = 'mainshock_record_section'
    sources_doc = anchor_doc['sources']
    if len(sources_doc) > 1:
        crosscheck = sources_doc[1]['provider']
    elif 'wei2022' in anchor_doc.get('cross_check', {}):
        crosscheck = 'the staged Wei et al. (2022) catalog row'
    else:
        crosscheck = 'staged paper statements'
    responses = read_inventory(str(sorted((ROOT / 'stations').glob('*.stationxml'))[0]))
    inventory = json.loads((ROOT / 'waveform_inventory.json').read_text())
    candidates = {}
    for row in inventory['files']:
        for s in row['streams']:
            if (s['channel'].endswith('Z') and s['candidate_npts'] and
                    UTCDateTime(s['start_utc']) <= origin <= UTCDateTime(s['last_sample_utc'])):
                candidates.setdefault(s['network'] + '.' + s['station'], []).append(
                    (s['seed_id'], row['path']))
    records = []
    for station, options in sorted(candidates.items()):
        # Native vertical velocity preferred; retain HN/EN when no HH/EH is present.
        seed, path = sorted(options,
                            key=lambda x: (FAMILY_ORDER.get(x[0].split('.')[-1][:2], 9), x[0]))[0]
        net, sta, loc, cha = seed.split('.')
        chosen = responses.select(network=net, station=sta, location=loc, channel=cha, time=origin)
        channels = [ch for network in chosen for st in network for ch in st]
        if len(channels) != 1:
            raise ValueError(f'Ambiguous metadata: {seed}')
        ch = channels[0]
        if ch.dip is None or abs(ch.dip + 90) > 1:
            raise ValueError(f'Unexpected vertical orientation: {seed}')
        distance = gps2dist_azimuth(anchor['latitude'], anchor['longitude'],
                                    ch.latitude, ch.longitude)[0] / 1000
        st = read(str(ROOT / path), starttime=origin - 720, endtime=origin + 720).select(id=seed)
        st.merge(method=-1)  # No padding or interpolation across gaps.
        intervals, segments = [], []
        caught_messages = []
        for raw in st:
            if ((ch.start_date is not None and raw.stats.starttime < ch.start_date) or
                    (ch.end_date is not None and raw.stats.endtime > ch.end_date) or
                    raw.stats.sampling_rate != ch.sample_rate):
                raise ValueError(f'Response epoch/rate mismatch: {seed}')
            if not np.isfinite(raw.data).all():
                raise ValueError(f'Nonfinite raw samples: {seed}')
            corrected = raw.copy().detrend('linear')
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                corrected.remove_response(inventory=chosen, output='VEL', pre_filt=pre_filt(raw.stats.sampling_rate),
                                          water_level=None, zero_mean=True, taper=True,
                                          taper_fraction=.05)
            caught_messages.extend(str(w.message) for w in caught)
            if not np.isfinite(corrected.data).all():
                raise ValueError(f'Nonfinite corrected samples: {seed}')
            t = raw.times(reftime=origin)
            mask = (t >= -600) & (t < 600)
            if not mask.any():
                continue
            times = t[mask]
            intervals.append((float(times[0]), float(times[-1] + raw.stats.delta)))
            values = raw.data[mask].astype(float)
            segments.append((times / 60, values, corrected.data[mask]))
        if not segments:
            raise ValueError(f'No samples: {seed}')
        raw_mean = sum(x[1].sum() for x in segments) / sum(len(x[1]) for x in segments)
        segments = [(t, x - raw_mean, v) for t, x, v in segments]
        raw_scale = max(float(np.max(np.abs(x))) for t, x, v in segments)
        vel_scale = max(float(np.max(np.abs(v))) for t, x, v in segments)
        cursor = -600.; missing = 0.; overlap = 0.
        for a, b in sorted(intervals):
            missing += max(0, a - cursor)
            overlap += max(0, min(cursor, b) - a)
            cursor = max(cursor, b)
        missing += max(0, 600 - cursor)
        records.append(dict(seed_id=seed, station=station, distance_km=distance, source_path=path,
                            latitude=ch.latitude, longitude=ch.longitude,
                            sample_rate_hz=ch.sample_rate,
                            response_input_units=(ch.response.instrument_sensitivity.input_units
                                                  if ch.response is not None else None),
                            start_utc=str(origin - 600), end_utc_exclusive=str(origin + 600),
                            samples=sum(len(x) for t, x, v in segments),
                            segment_count=len(segments),
                            missing_seconds=missing, overlap_seconds=overlap,
                            raw_mean_counts=raw_mean, raw_normalization_counts=raw_scale,
                            velocity_normalization_m_s=vel_scale,
                            warnings=' | '.join(caught_messages), segments=segments))
        print(f'Read and corrected {len(records)}/{len(candidates)}: {seed}', flush=True)
    records.sort(key=lambda r: (r['distance_km'], r['seed_id']))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / f'{stem}.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, lineterminator='\n',
                                fieldnames=[k for k in records[0] if k != 'segments'])
        writer.writeheader()
        writer.writerows({k: v for k, v in r.items() if k != 'segments'} for r in records)
    with publication_style():
        for kind, column, scale_name in [('raw', 1, 'raw_normalization_counts'),
                                         ('velocity', 2, 'velocity_normalization_m_s')]:
            fig, ax = plt.subplots(figsize=(7.09, 10.5), layout='constrained')
            for i, r in enumerate(records):
                scale = r[scale_name] or 1
                for segment in r['segments']:
                    ax.plot(segment[0], i - .42 * segment[column] / scale,
                            color=FAMILY_COLORS.get(r['seed_id'].split('.')[-1][:2], '#555555'),
                            lw=.4, rasterized=True)
            ax.axvline(0, color='black', lw=.6, ls='--')
            ax.set_yticks(range(len(records)),
                          [f'{r["seed_id"]}  {r["distance_km"]:.1f}' for r in records])
            ax.tick_params(axis='y', labelsize=6)
            ax.set(xlim=(-10, 10), ylim=(len(records) - .5, -.8),
                   xlabel=f'Time since {label} origin (min)',
                   ylabel='Channel · epicentral distance (km)')
            ax.set_xticks(np.arange(-10, 11, 2))
            ax.legend(handles=[Line2D([], [], color=c, label=k)
                               for k, c in FAMILY_COLORS.items()],
                      loc='upper right', ncol=4, frameon=False)
            save_figure(fig, OUT / f'{stem}_{kind}')
            plt.close(fig)
    families_used = sorted({r['seed_id'].split('.')[-1][:2] for r in records})
    (OUT / f'{stem}.md').write_text(f'''# {label} record sections

[Response-corrected velocity]({stem}_velocity.png) ([PDF]({stem}_velocity.pdf)) · [Raw counts]({stem}_raw.png) ([PDF]({stem}_raw.pdf)).

Event `{anchor['event_id']}`: {origin}, latitude {anchor['latitude']}, longitude {anchor['longitude']}, depth {anchor['depth_km']} km; source: `analysis/mainshock_anchor.json` ({anchor_doc['sources'][0]['provider']}), cross-checked against {crosscheck}. Window: [origin −600 s, origin +600 s). The dashed line is origin time, not a phase arrival.

{len(records)} observed stations, each represented by one native vertical channel (HHZ preferred, then EHZ, then BHZ). Stations are ordered by WGS84 epicentral surface distance, nearest at the top. Rows are equally spaced ranks, not a linear distance axis; right-hand values within the channel labels give distances in km. Channel metadata, samples, source paths, per-trace normalization factors and coverage are in [the CSV table]({stem}.csv).

Each channel is independently normalized by its maximum absolute amplitude over the displayed 20 minutes, with the same factor for all its segments. Thus waveform heights do not represent relative ground-motion amplitudes between stations; weaker pre-event signals may be visually small at mainshock scale. Positive excursions point upward. Native samples are plotted without temporal decimation; rasterized trace artists keep PDFs compact.

The raw panel only subtracts each channel's displayed-window mean, retaining native counts before normalization. The velocity panel reads 120 s of additional padding on each side, merges only adjacent compatible segments, linearly detrends each contiguous segment and uses ObsPy `remove_response(output='VEL', pre_filt=(0.5,1,15,20), water_level=None, zero_mean=True, taper=True, taper_fraction=0.05)` for channels at ≥80 Hz (corners scaled down to (0.4,0.8,10,14) below 80 Hz). The displayed interval is cropped afterwards. No further filter, resampling, rotation, gap interpolation or full-day processed archive is generated. StationXML epoch/rate and vertical orientation must match; corrected samples must be finite. This is an offline diagnostic and the frequency band is not a frozen preprocessing choice.

Gaps remain blank rather than being filled. Summed missing channel-seconds in the displayed interval: {sum(r['missing_seconds'] for r in records):.6f}; summed overlap channel-seconds: {sum(r['overlap_seconds'] for r in records):.6f}. Unmarked traces have not been individually cleared of saturation; response removal does not repair distorted input. These plots are for waveform timing and morphology, not validated peak-ground-motion measurements. Channel families present: {', '.join(families_used)}.

Reproduce from the case directory with `python -B scripts/figures/plot_mainshock_record_section.py` in the inversionagent environment. Raw waveform files and StationXML are read-only.
''')
    print(f'Wrote two record sections for {len(records)} stations; '
          f'distance range {records[0]["distance_km"]:.1f}–{records[-1]["distance_km"]:.1f} km',
          flush=True)


if __name__ == '__main__':
    main()
