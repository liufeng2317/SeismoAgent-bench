#!/usr/bin/env python3
"""Stage 52 -- double-difference relocation of the round catalog.

Self-contained CC kernel + native hypoDD driven directly. (The TRACE
hypodd_runner/FDTCC adapter assumes one mseed per net-station-day and cannot
read this case's per-component daily files, so the adapter path is not used.)

 1. Events/picks from the frozen round export (03 association, 05 NLL catalog).
 2. k-nearest-neighbor event pairs on NLL locations.
 3. Pick-aligned waveform windows cached per component and band from the
    daily mseed archive (one file per station-component-day).
 4. Scalar-P / vector-S correlation with two-band quality gates (kernel
    conventions cribbed from the Ridgecrest production stage 52).
 5. event.dat / station.dat / dt.ct / dt.cc / hypoDD.inp; iteration control
    copied verbatim from the Ridgecrest tuned run cc3_d1 (CT+CC, damp 80/40).
 6. hypoDD built from the TRACE hypodd_source (array capacities changed only).
 7. Relocated catalog + paired reference comparison against the NLL baseline.

Sign conventions (nailed by the synthetic self-checks written to checks.json):
  curve(a, b) peaks at +lag when b's waveform sits later inside its
  pick-aligned window -- the windows are aligned at picks, so the lag is the
  differential PICK RESIDUAL and
      cc_arrival_difference_s = (t_pick_a - t_pick_b) - lag_s
  recovers the absolute arrival difference (arrival_a - arrival_b); then
      dt.cc row = cc_arrival_difference_s - (origin_a - origin_b)   (OTC=0)
  while dt.ct rows carry raw (travel_a, travel_b) against the same origins.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linear_sum_assignment
from scipy.signal import butter, sosfiltfilt
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent          # 01_pipeline
ROOT = HERE.parent                               # expert/
CFG = yaml.safe_load((ROOT / '00_config/config.yaml').read_text())
DD = yaml.safe_load((ROOT / '00_config/double_difference.yaml').read_text())
ASSOC = yaml.safe_load((ROOT / '00_config/association.yaml').read_text())
DATUM = float(ASSOC['reference_elevation_km'])
EXPORT = ROOT / CFG['export_root']
OUT = EXPORT / '52_double_difference'
EARTH_KM = 6371.0088


# ------------------------------------------------------------------ kernel ---
def curve(a, b, limit=40):
    """Full-window-normalized dot product over shifted windows (RC verbatim)."""
    a = np.asarray(a, float).copy(); b = np.asarray(b, float).copy()
    assert a.shape == b.shape and a.ndim == 2
    a -= a.mean(axis=1, keepdims=True); b -= b.mean(axis=1, keepdims=True)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if min(na, nb) < 1e-20:
        raise ValueError('Zero vector signal')
    a /= na; b /= nb
    n = a.shape[1]; lags = np.arange(-limit, limit + 1); values = []
    for lag in lags:
        aa, bb = (a[:, -lag:], b[:, :n + lag]) if lag < 0 else ((a[:, :n - lag], b[:, lag:]) if lag > 0 else (a, b))
        values.append(float(np.sum(aa * bb)))
    return lags, np.array(values)


def whiten(signal, snr):
    """Normalize each component so its RMS equals its SNR (RC verbatim)."""
    rms = np.sqrt(np.mean(signal ** 2, axis=1)); snr = np.asarray(snr, float)
    if not np.all(np.isfinite(snr)) or np.any(snr <= 0) or np.any(rms <= 0):
        raise ValueError('Invalid noise estimate')
    return signal / (rms / snr)[:, None]


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return float(2 * EARTH_KM * np.arcsin(np.sqrt(a)))


def synthetic_checks():
    """End-to-end sign check on pick-aligned windows + the RC kernel unit checks.

    Two events at one station: each trace carries the same waveform with its
    own pulse position (arrival), each window is cut around its own pick
    (arrival minus pick error), so the correlation lag isolates the
    differential pick error and cc_arrival_difference recovers the true
    arrival difference regardless of it.
    """
    fs = 100.0
    t = np.arange(220) / fs

    def trace(pulse_center, rng):
        u = t - pulse_center
        return (np.exp(-(u / .05) ** 2) * np.cos(2 * np.pi * 9 * u)
                + .5 * np.exp(-((u - .4) / .07) ** 2) * np.cos(2 * np.pi * 5 * (u - .4))
                + rng.normal(0, .01, t.shape))

    rng = np.random.default_rng(7)
    e_a, e_b = .021, -.017          # pick errors; expected measured lag = e_b - e_a
    results = {}
    for true_diff in (-.13, -.05, 0., .05, .13):      # arrival_a - arrival_b
        arr_a, arr_b = .550, .550 - true_diff          # pulse positions in the two traces
        ta = trace(arr_a, rng); tb = trace(arr_b, rng)
        pick_a, pick_b = arr_a - e_a, arr_b - e_b      # picks (arrival - error)
        ia, ib = int(round(pick_a * fs)), int(round(pick_b * fs))
        av, bv = ta[ia:ia + 120][None, :], tb[ib:ib + 120][None, :]   # windows aligned at the picks
        sa = np.array([(np.max(av) - np.min(av)) / .06]); sb = np.array([(np.max(bv) - np.min(bv)) / .06])
        _, c = curve(whiten(av, sa), whiten(bv, sb))
        lag = np.arange(-40, 41)[np.argmax(c)] / fs
        observed_dt = pick_a - pick_b
        cc_ad = observed_dt - lag
        results[f'true_{true_diff:+.2f}s'] = {'lag_s': float(lag), 'expected_lag_s': e_b - e_a,
                                              'cc_arrival_difference_s': float(cc_ad),
                                              'true_arrival_difference_s': float(true_diff),
                                              'error_s': float(cc_ad - true_diff)}
    assert max(abs(v['error_s']) for v in results.values()) <= .01, results
    s = np.arange(181) / 100
    a = np.exp(-((s - .6) / .06) ** 2) * np.cos(2 * np.pi * 6 * (s - .6))
    b = np.exp(-((s - .67) / .06) ** 2) * np.cos(2 * np.pi * 6 * (s - .67))
    ls, c = curve(np.vstack([a, .1 * a]), np.vstack([b, .1 * b]))
    assert abs(ls[np.argmax(c)] / 100 - .07) < 1e-12
    assert ls[np.argmax(curve(np.vstack([b, .1 * b]), np.vstack([a, .1 * a]))[1])] == -7
    aa = np.vstack([a, .1 * a])
    assert np.allclose(whiten(aa, [10, 1]), whiten(aa * np.array([3., .2])[:, None], [10, 1]), atol=1e-13)
    return {'pick_aligned_arrival_recovery': results,
            'max_abs_error_s': max(abs(v['error_s']) for v in results.values()),
            'rc_kernel_checks': 'passed'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


# ------------------------------------------------------------------ inputs ---
def load_round():
    q = pd.read_csv(EXPORT / '05_match_references/event_quality.csv')
    events = q[q.status.eq('LOCATED')].copy()
    events['origin'] = pd.to_datetime(events.origin_time, utc=True, format='ISO8601').dt.round('10ms')
    events = events.sort_values('origin').reset_index(drop=True)
    events['native_id'] = np.arange(1, len(events) + 1)
    picks = pd.read_csv(EXPORT / '03_associate_gamma/full/picks.csv')
    picks = picks[picks.association_status.eq('associated') & picks.event_id.isin(set(events.event_id))].copy()
    picks['t'] = pd.to_datetime(picks.time_utc, utc=True, format='ISO8601').astype('int64') / 1e9
    dupes = int(picks.duplicated(['event_id', 'instrument_id', 'phase']).sum())
    if dupes:
        print(f'note: {dupes} duplicate event-instrument-phase picks; keeping highest probability', flush=True)
        picks = picks.sort_values('probability', ascending=False).drop_duplicates(
            ['event_id', 'instrument_id', 'phase'], keep='first')
    stations = pd.read_csv(EXPORT / '03_associate_gamma/full/stations.csv')
    stations['code'] = stations.station_id.str.split('.').str[-1]
    assert stations.code.is_unique and stations.code.str.len().max() <= 5
    model = json.loads((EXPORT / '03_associate_gamma/full/inputs.json').read_text())['model_source']['rows']
    return events, picks, stations, model


def seeds_for(pick):
    chans = pick.source_channels.split(';')
    if pick.phase == 'P':
        return [s for s in chans if s.endswith('Z')]
    return sorted(s for s in chans if not s.endswith('Z'))


def select_pairs(events):
    xy = events[['x_km', 'y_km', 'depth_km']].to_numpy()
    tree = cKDTree(xy)
    k = int(DD['pair_k_neighbors']); maxsep = float(DD['pair_max_separation_km'])
    pairs = set()
    for i in range(len(xy)):
        near = tree.query_ball_point(xy[i], maxsep)
        near = sorted(near, key=lambda j: float(np.linalg.norm(xy[j] - xy[i])))
        for j in near[1:k + 1]:
            a, b = sorted((i, j))
            pairs.add((a, b))
    return np.array(sorted(pairs), dtype=int)


# ----------------------------------------------------------------- windows ---
def _inventory_index(data_root):
    inv = json.loads((data_root / 'waveform_inventory.json').read_text())
    by_seed = {}
    for f in inv['files']:
        for s in f['streams']:
            by_seed.setdefault(s['seed_id'], []).append(
                (pd.Timestamp(s['start_utc']), pd.Timestamp(s['last_sample_utc']), data_root / f['path']))
    for v in by_seed.values():
        v.sort()
    return by_seed


def _windows_for_file(job):
    """Pick-aligned band windows for every pick whose padded window fits one file."""
    path, items, bands, order, pwin, swin, nwin, pad = job
    from obspy import read as obsread
    out = []
    try:
        tr = obsread(str(path), format='MSEED')[0]
        sr = float(tr.stats.sampling_rate)
        assert abs(sr - 100.) < .1, sr
        data = tr.data.astype(np.float64)
        t0 = tr.stats.starttime.timestamp
        n = len(data)
        sos = [butter(order, [lo, hi], btype='band', fs=sr, output='sos') for lo, hi in bands]
        for pick_id, seed, t, phase in items:
            ana0, ana1 = (pwin if phase == 'P' else swin)
            pre = min(nwin[0], ana0) - pad; post = max(nwin[1], ana1) + pad
            i0 = int(round((t + pre - t0) * sr)); i1 = int(round((t + post - t0) * sr))
            if i0 < 0 or i1 > n or i1 - i0 < int((post - pre) * sr) - 1:
                out.append((pick_id, seed, 'outside_window_or_missing_file', None, None)); continue
            raw = data[i0:i1]
            a0 = int(round((t + ana0 - t0) * sr)) - i0; a1 = int(round((t + ana1 - t0) * sr)) - i0
            n0 = int(round((t + nwin[0] - t0) * sr)) - i0; n1 = int(round((t + nwin[1] - t0) * sr)) - i0
            arr = np.empty((len(bands), a1 - a0), np.float32); snrs = []
            ok = True
            for bi, s in enumerate(sos):
                f = sosfiltfilt(s, raw)
                sig, noise = f[a0:a1], f[n0:n1]
                nr = float(np.sqrt(np.mean(noise ** 2)))
                if nr <= 0:
                    ok = False; break
                snrs.append(float(np.sqrt(np.mean(sig ** 2)) / nr))
                arr[bi] = sig
            if not ok:
                out.append((pick_id, seed, 'invalid_noise_estimate', None, None)); continue
            out.append((pick_id, seed, 'ok', arr, snrs))
    except Exception as exc:   # unreadable file: fail every item, keep going
        out = [(p, s, f'read_error:{type(exc).__name__}', None, None) for p, s, _, _ in items]
    return out


def cache_windows(picks):
    """Cache one analysis window per (pick, component) per band + SNR metadata."""
    import obspy   # parent imports once; forked workers inherit it
    data_root = ROOT / CFG['data_root']
    inv = _inventory_index(data_root)
    bands = [tuple(b) for b in DD['bands_hz']]
    pwin, swin, nwin = tuple(DD['p_window_s']), tuple(DD['s_window_s']), tuple(DD['noise_window_s'])
    pad = float(DD['edge_pad_s'])
    pre = min(nwin[0], min(pwin[0], swin[0])) - pad; post = max(nwin[1], max(pwin[1], swin[1])) + pad
    jobs, records = {}, []
    for r in picks.itertuples():
        seeds = seeds_for(r)
        if len(seeds) != (1 if r.phase == 'P' else 2):
            records.append((r.pick_id, '', 'wrong_channel_count', np.nan, np.nan, 0)); continue
        for s in seeds:
            hit = None
            for start, last, path in inv.get(s, []):
                if start.timestamp() <= r.t + pre and last.timestamp() >= r.t + post:
                    hit = path; break
            if hit is None:
                records.append((r.pick_id, s, 'outside_window_or_missing_file', np.nan, np.nan, 0)); continue
            jobs.setdefault((hit, s), []).append((r.pick_id, s, r.t, r.phase))
    joblist = [(path, items, bands, int(DD['butterworth_order']), pwin, swin, nwin, pad)
               for (path, s), items in jobs.items()]
    print(f'window jobs: {len(joblist)} files, {sum(map(len, jobs.values()))} pick-windows', flush=True)
    windows = {}
    t_start = time.time()
    with ProcessPoolExecutor(int(DD['workers'])) as pool:
        futures = [pool.submit(_windows_for_file, j) for j in joblist]
        for done, future in enumerate(as_completed(futures), 1):
            for pick_id, seed, status, arr, snrs in future.result():
                if status == 'ok':
                    windows[f'{pick_id}|{seed}'] = arr
                    records.append((pick_id, seed, 'ok', snrs[0], snrs[1], arr.shape[1]))
                else:
                    records.append((pick_id, seed, status, np.nan, np.nan, 0))
            if done % 100 == 0:
                print(f'  {done}/{len(joblist)} files, {len(windows)} windows, {time.time()-t_start:.0f}s', flush=True)
    cache = OUT / 'cache'; cache.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache / 'cc_windows.npz', **windows)
    meta = pd.DataFrame(records, columns=['pick_id', 'seed_id', 'status', 'snr_primary', 'snr_check', 'n_samples'])
    meta = meta.drop_duplicates(['pick_id', 'seed_id'], keep='last')
    meta.to_csv(cache / 'waveform_windows.csv', index=False)
    print(dict(meta.status.value_counts()), flush=True)
    return windows, meta.set_index(['pick_id', 'seed_id'])


# --------------------------------------------------------------- correlate ---
def correlate(events, picks, pairs, windows, meta):
    """CC differential times for every common pick of every selected pair."""
    boundary = int(round(float(DD['boundary_lag_s']) * 100))
    excl = int(round(float(DD['peak_exclusion_s']) * 100))
    min_snr, min_cc, min_margin = float(DD['min_snr']), float(DD['min_cc']), float(DD['min_peak_margin'])
    band_tol = float(DD['band_lag_tolerance_s'])
    ev_picks = {}
    for r in picks.itertuples():
        ev_picks.setdefault(r.event_id, {})[(r.instrument_id, r.phase)] = r
    oid = events.set_index('event_id')['native_id']
    rows, reasons = [], []
    for n_done, (ia, ib) in enumerate(pairs, 1):
        ea, eb = events.event_id.iloc[ia], events.event_id.iloc[ib]
        common = set(ev_picks.get(ea, {})) & set(ev_picks.get(eb, {}))
        for key in sorted(common):
            pa, pb = ev_picks[ea][key], ev_picks[eb][key]
            obs_dt = pa.t - pb.t
            seeds = seeds_for(pa)
            try:
                lags, peaks, margins, snrs = [], [], [], []
                hit_boundary = False
                for band, col in ((0, 'snr_primary'), (1, 'snr_check')):
                    av = np.stack([windows[f'{pa.pick_id}|{s}'][band] for s in seeds]).astype(float)
                    bv = np.stack([windows[f'{pb.pick_id}|{s}'][band] for s in seeds]).astype(float)
                    sa = np.array([meta.loc[(pa.pick_id, s), col] for s in seeds], float)
                    sb = np.array([meta.loc[(pb.pick_id, s), col] for s in seeds], float)
                    snrs.extend([float(np.sqrt(np.mean(sa ** 2))), float(np.sqrt(np.mean(sb ** 2)))])
                    ls, c = curve(whiten(av, sa), whiten(bv, sb))
                    best = int(np.argmax(abs(c)))
                    lags.append(float(ls[best] / 100)); peaks.append(float(c[best]))
                    margins.append(float(c[best] - np.max(abs(c[abs(ls - ls[best]) > excl]))))
                    hit_boundary |= abs(ls[best]) >= boundary
                bad = []
                if min(snrs) < min_snr: bad.append('low_snr')
                if min(peaks) < min_cc: bad.append('low_or_negative_cc')
                if min(margins) < min_margin: bad.append('ambiguous_peak')
                if hit_boundary: bad.append('lag_boundary')
                if abs(lags[0] - lags[1]) > band_tol: bad.append('band_instability')
            except (KeyError, ValueError):
                bad = ['missing_or_invalid_windows']
            if bad != []:
                reasons.append(';'.join(bad)); continue
            reasons.append('accepted')
            rows.append(dict(event_id_a=ea, event_id_b=eb, native_a=int(oid[ea]), native_b=int(oid[eb]),
                             instrument_id=pa.instrument_id, phase=pa.phase,
                             observed_dt_s=obs_dt, lag_s=lags[0], cc=peaks[0],
                             cc_arrival_difference_s=obs_dt - lags[0]))
        if n_done % 2000 == 0:
            print(f'  pairs {n_done}/{len(pairs)}, obs accepted {reasons.count("accepted")}', flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / 'cache/cc_measurements.csv', index=False)
    pd.Series(reasons).value_counts().to_csv(OUT / 'cache/cc_reasons.csv')
    return frame


# ----------------------------------------------------------------- hypoDD ----
def write_inputs(events, picks, stations, cc, pairs):
    inputs = OUT / 'inputs'; inputs.mkdir(parents=True, exist_ok=True)
    origin = events.set_index('event_id')['origin']
    code = stations.set_index('id')['code'].to_dict()
    ev_picks = {}
    for r in picks.itertuples():
        ev_picks.setdefault(r.event_id, {})[(r.instrument_id, r.phase)] = r
    oid = events.set_index('event_id')['native_id']
    min_ct, min_cc = int(DD['min_obs_ct_pair']), int(DD['min_obs_cc_pair'])
    cc_by_pair = {k: g for k, g in cc.groupby(['event_id_a', 'event_id_b'])} if len(cc) else {}
    pair_ids = sorted({(events.event_id.iloc[a], events.event_id.iloc[b]) for a, b in pairs}
                      | set(cc_by_pair))
    ct_rows = cc_rows = 0
    with (inputs / 'event.dat').open('w') as f:
        for r in events.itertuples():
            t = r.origin
            stamp = t.strftime('%H%M%S') + f'{t.microsecond // 10000:02d}'
            f.write(f'{t:%Y%m%d} {stamp} {r.latitude:.7f} {r.longitude:.7f} {r.depth_km:.5f} 0 0 0 0 {r.native_id}\n')
    with (inputs / 'station.dat').open('w') as f:
        for r in stations.itertuples():
            f.write(f'{r.code} {r.latitude:.7f} {r.longitude:.7f}\n')
    with (inputs / 'dt.ct').open('w') as fct, (inputs / 'dt.cc').open('w') as fcc:
        for (ea, eb) in pair_ids:
            common = set(ev_picks.get(ea, {})) & set(ev_picks.get(eb, {}))
            ct = []
            for key in sorted(common):
                pa, pb = ev_picks[ea][key], ev_picks[eb][key]
                ct.append((code[pa.instrument_id], pa.t - origin[ea].timestamp(),
                           pb.t - origin[eb].timestamp(), pa.phase))
            if len(ct) >= min_ct:
                fct.write(f'# {oid[ea]} {oid[eb]}\n')
                for s, ta, tb, ph in ct:
                    fct.write(f'{s} {ta:.6f} {tb:.6f} 1 {ph}\n')
                ct_rows += len(ct)
            g = cc_by_pair.get((ea, eb))
            if g is not None and len(g) >= min_cc:
                od = (origin[ea] - origin[eb]).total_seconds()
                fcc.write(f'# {oid[ea]} {oid[eb]} 0\n')
                for r in g.itertuples():
                    fcc.write(f'{code[r.instrument_id]} {r.cc_arrival_difference_s - od:.6f} '
                              f'{r.cc * r.cc:.6f} {r.phase}\n')
                cc_rows += len(g)
    print(f'dt.ct rows {ct_rows} across pairs, dt.cc rows {cc_rows}', flush=True)
    return ct_rows, cc_rows


def build_native(capacity, n_events):
    lib = Path(CFG['tools']['trace_library']) / 'basic_fun/HypoDD/hypodd_source'
    dest = OUT / 'native'; dest.mkdir(parents=True, exist_ok=True)
    for part in ['include', 'src/hypoDD']:
        shutil.copytree(lib / part, dest / part, dirs_exist_ok=True)
    maxeve = int(n_events * 1.05) + 10
    (dest / 'include/hypoDD.inc').write_text(
        '      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,\n'
        '     & MAXDATA0, MAXCL\n'
        f'      parameter(MAXEVE={maxeve}, MAXLAY=15, MAXDATA={capacity},\n'
        f'     & MAXSTA=100, MAXEVE0=2, MAXDATA0=1, MAXCL={maxeve})\n')
    cwd = dest / 'src/hypoDD'
    with (dest / 'build.log').open('w') as log:
        subprocess.run(['make', 'clean'], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(['make', '-j4', 'FC=gfortran',
                        'FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch'],
                       cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
    (dest / 'build.json').write_text(json.dumps(
        {'max_events': maxeve, 'max_data': capacity, 'maxsta': 100,
         'scientific_changes': 'None; array capacities only.',
         'binary_sha256': sha(cwd / 'hypoDD')}, indent=2) + '\n')
    return cwd / 'hypoDD', maxeve


def relocate(events, model, ct_rows, cc_rows):
    binary, maxeve = build_native(int(ct_rows + cc_rows + 1000), len(events))
    tops = [r['top_of_layer_km'] for r in model]; vps = [r['vp_km_s'] for r in model]
    # Iteration control verbatim from Ridgecrest 14_tune_hypodd run cc3_d1 (CT+CC, damp 80/40).
    (OUT / 'inputs/hypoDD.inp').write_text('\n'.join([
        'dt.cc', 'dt.ct', 'event.dat', 'station.dat',
        'hypoDD.loc', 'hypoDD.reloc', 'hypoDD.sta', 'hypoDD.res', 'hypoDD.src',
        f'3 3 {maxeve}', '0 0', '2 2 2',
        '4 3 1.5 -9 -9 1 .5 -9 -9 80',
        '8 3 1.5 -9 -9 1 .5 -9 -9 40',
        f'{len(tops)} 1.73', ' '.join(f'{v:.4f}' for v in tops), ' '.join(f'{v:.4f}' for v in vps), '0', '']))
    with (OUT / 'console.log').open('w') as log:
        subprocess.run([str(binary), 'hypoDD.inp'], cwd=OUT / 'inputs', stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=7200)
    console = (OUT / 'console.log').read_text(errors='replace')
    assert 'writing out results' in console, console[-2000:]
    columns = ['native_id', 'latitude', 'longitude', 'depth_km', 'x_m', 'y_m', 'z_m', 'ex_m', 'ey_m', 'ez_m',
               'year', 'month', 'day', 'hour', 'minute', 'second', 'magnitude_placeholder',
               'nccp', 'nccs', 'nctp', 'ncts', 'rmscc', 'rmsct', 'cluster']
    f = pd.read_csv(OUT / 'inputs/hypoDD.reloc', sep=r'\s+', header=None, names=columns)
    f['origin_time_dd'] = [(pd.Timestamp(year=int(r.year), month=int(r.month), day=int(r.day), hour=int(r.hour),
                                         minute=int(r.minute), tz='UTC') + pd.Timedelta(seconds=float(r.second))).isoformat()
                           for r in f.itertuples()]
    f = f.merge(events[['event_id', 'native_id', 'origin_time', 'longitude', 'latitude', 'depth_km',
                        'depth_below_sea_level_km', 'in_v1_working_catalog']],
                on='native_id', validate='one_to_one', suffixes=('_dd', '_nll'))
    f = f.rename(columns={'origin_time': 'origin_time_nll'})   # only events' column is unsuffixed
    # Flat-station/layer-tracer datum correction (see double_difference.yaml).
    f['dd_depth_below_sea_level_km'] = f.depth_km_dd - DATUM + float(DD.get('depth_datum_offset_km', 0.))
    f['dd_origin_shift_s'] = (pd.to_datetime(f.origin_time_dd, utc=True, format='ISO8601')
                              - pd.to_datetime(f.origin_time_nll, utc=True, format='ISO8601')).dt.total_seconds()
    f['dd_shift_km'] = [haversine(r.latitude_dd, r.longitude_dd, r.latitude_nll, r.longitude_nll)
                        for r in f.itertuples()]
    f.to_csv(OUT / 'relocated_events.csv', index=False)
    print(f'hypoDD retained {len(f)} of {len(events)} events; '
          f'median shift {f.dd_shift_km.median():.2f} km, origin shift {f.dd_origin_shift_s.median():+.3f} s', flush=True)
    return f


# --------------------------------------------------------------- compare -----
def match_one_to_one(events, ref, tlim, dlim):
    """Hungarian one-to-one matching on (time, epicentral distance) gates."""
    et = events.time.astype('int64').to_numpy() / 1e9
    ref = ref.sort_values('time').reset_index(drop=True)
    rt = ref.time.astype('int64').to_numpy() / 1e9
    penalty = 4 * min(len(events), len(ref)) + 1
    cost = np.full((len(events), len(ref) + len(events)), float(penalty))
    for i, e in enumerate(events.to_dict('records')):
        lo, hi = np.searchsorted(rt, et[i] - tlim), np.searchsorted(rt, et[i] + tlim, side='right')
        for j in range(lo, hi):
            r = ref.iloc[j]
            dt = et[i] - rt[j]
            dist = haversine(e['latitude_dd'], e['longitude_dd'], r.latitude, r.longitude)
            if abs(dt) <= tlim and dist <= dlim:
                cost[i, j] = np.hypot(dt / tlim, dist / dlim)
    rows, cols = linear_sum_assignment(cost)
    picked = {int(i): int(j) for i, j in zip(rows, cols) if j < len(ref) and cost[i, j] < penalty}
    out = []
    for i, e in enumerate(events.to_dict('records')):
        row = dict(event_id=e['event_id'], reference_id='', matched=False)
        if i in picked:
            r = ref.iloc[picked[i]]
            row.update(reference_id=r.reference_id, matched=True,
                       dt_s=et[i] - rt[picked[i]],
                       horizontal_km=haversine(e['latitude_dd'], e['longitude_dd'], r.latitude, r.longitude),
                       depth_difference_km=(e['dd_depth_below_sea_level_km'] - r.depth_km)
                       if np.isfinite(r.depth_km) else np.nan,
                       reference_depth_km=r.depth_km, reference_magnitude=r.magnitude)
        out.append(row)
    return pd.DataFrame(out)


def compare(f):
    tlim = float(DD['match_gates']['time_s']); dlim = float(DD['match_gates']['distance_km'])
    refs = pd.read_csv(EXPORT / '05_match_references/reference_events.csv')
    refs['time'] = pd.to_datetime(refs.time.str.replace(' ', 'T', regex=False), utc=True, format='ISO8601')
    nll_matches = pd.read_csv(EXPORT / '05_match_references/matches.csv')
    ev = f.copy()
    ev['time'] = pd.to_datetime(ev.origin_time_dd, utc=True, format='ISO8601')
    report = {'gates': {'time_s': tlim, 'distance_km': dlim}, 'references': {}}
    all_dd_matches = []
    for cat in ('pang', 'baker', 'uuss'):
        ref = refs[refs.catalog.eq(cat)].reset_index(drop=True)
        dd_m = match_one_to_one(ev, ref, tlim, dlim)
        dd_m['catalog'] = cat
        all_dd_matches.append(dd_m)
        entry = {'masked_reference_events': len(ref),
                 'nll_matched': int((nll_matches.catalog.eq(cat) & nll_matches.matched).sum()),
                 'dd_matched': int(dd_m.matched.sum()),
                 'dd_matched_fraction': float(dd_m.matched.mean())}
        # Paired comparison: identical event-reference pairs (the round's NLL matches) scored for both locators.
        nm = nll_matches[nll_matches.catalog.eq(cat) & nll_matches.matched].copy()
        paired = nm.merge(ev[['event_id', 'time', 'latitude_dd', 'longitude_dd', 'dd_depth_below_sea_level_km']],
                          on='event_id')
        paired = paired.merge(ref[['reference_id', 'latitude', 'longitude', 'depth_km', 'time']],
                              on='reference_id', suffixes=('', '_ref'))
        paired['dd_dt_s'] = (paired.time - paired.time_ref).dt.total_seconds()
        paired['dd_horizontal_km'] = [haversine(a, b, c, d) for a, b, c, d in
                                      zip(paired.latitude_dd, paired.longitude_dd, paired.latitude, paired.longitude)]
        paired['dd_depth_difference_km'] = paired.dd_depth_below_sea_level_km - paired.depth_km
        paired.to_csv(OUT / f'paired_{cat}.csv', index=False)
        entry['paired_events'] = len(paired)
        for col in ('nll_dt_s', 'nll_horizontal_km', 'nll_depth_difference_km',
                    'dd_dt_s', 'dd_horizontal_km', 'dd_depth_difference_km'):
            v = paired[col].dropna()
            if len(v):
                entry[f'{col}_median'] = float(v.median())
                entry[f'{col}_mad'] = float(np.median(np.abs(v - v.median())))
        report['references'][cat] = entry
    pd.concat(all_dd_matches).to_csv(OUT / 'dd_matches.csv', index=False)
    return report


# ------------------------------------------------------------------- main ----
def main():
    assert ASSOC['velocity_model'].endswith('basinfill2km'), 'stage 52 expects the r4 round model'
    OUT.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument('steps', nargs='+', choices=['all', 'windows', 'correlate', 'inputs', 'relocate', 'report'])
    args = ap.parse_args()
    todo = set(args.steps) | ({'windows', 'correlate', 'inputs', 'relocate', 'report'} if 'all' in args.steps else set())
    t0 = time.time()
    events, picks, stations, model = load_round()
    print(f'{len(events)} located events, {len(picks)} associated picks, {len(stations)} stations', flush=True)
    checks = synthetic_checks()
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(f"synthetic checks passed (max abs error {checks['max_abs_error_s']:.4f} s)", flush=True)
    cc = None
    if (OUT / 'cache/cc_measurements.csv').exists() and 'correlate' not in todo:
        cc = pd.read_csv(OUT / 'cache/cc_measurements.csv')
    ct_rows = cc_rows = None
    if (OUT / 'inputs/dt.ct').exists() and 'inputs' not in todo:
        ct_rows = sum(1 for line in (OUT / 'inputs/dt.ct').read_text().splitlines() if not line.startswith('#'))
        cc_rows = sum(1 for line in (OUT / 'inputs/dt.cc').read_text().splitlines() if not line.startswith('#'))
    if {'windows', 'correlate', 'inputs'} & todo:
        pairs = select_pairs(events)
        print(f'{len(pairs)} event pairs (k={DD["pair_k_neighbors"]}, maxsep={DD["pair_max_separation_km"]} km)', flush=True)
        if 'windows' in todo or not (OUT / 'cache/cc_windows.npz').exists():
            windows, meta = cache_windows(picks)
        else:
            archive = np.load(OUT / 'cache/cc_windows.npz')
            windows = {k: archive[k] for k in archive.files}; archive.close()
            meta = pd.read_csv(OUT / 'cache/waveform_windows.csv').set_index(['pick_id', 'seed_id'])
        if cc is None:
            cc = correlate(events, picks, pairs, windows, meta)
        print(f'{len(cc)} accepted CC observations, median CC {cc.cc.median():.3f}' if len(cc)
              else 'NO accepted CC observations', flush=True)
        del windows
        if 'inputs' in todo or not (OUT / 'inputs/dt.ct').exists():
            ct_rows, cc_rows = write_inputs(events, picks, stations, cc, pairs)
    if 'relocate' in todo or not (OUT / 'relocated_events.csv').exists():
        f = relocate(events, model, ct_rows, cc_rows)
    else:
        f = pd.read_csv(OUT / 'relocated_events.csv')
    report = compare(f)
    report.update({'round': CFG['round'], 'events_in': len(events), 'events_relocated': len(f),
                   'ct_rows': ct_rows, 'cc_rows': cc_rows,
                   'checks_max_abs_error_s': checks['max_abs_error_s'],
                   'seconds': round(time.time() - t0, 1),
                   'kernel': 'scalar-P / vector-S, bands ' + str(DD['bands_hz']),
                   'control': 'Ridgecrest 14_tune_hypodd cc3_d1 verbatim (CT+CC, damp 80/40)'})
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = [f'# Stage 52 double-difference report ({CFG["round"]})', '',
             '| reference | masked | NLL matched | DD matched | dZ NLL | dZ DD | MAD NLL | MAD DD | dEpi NLL | dEpi DD | dt NLL | dt DD |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for cat in ('pang', 'baker', 'uuss'):
        r = report['references'][cat]
        fmt = lambda k, f='{:+.2f}': f.format(r[k]) if k in r else '--'
        lines.append(f'| {cat} | {r["masked_reference_events"]} | {r["nll_matched"]} | {r["dd_matched"]} '
                     f'| {fmt("nll_depth_difference_km_median")} | {fmt("dd_depth_difference_km_median")} '
                     f'| {fmt("nll_depth_difference_km_mad")} | {fmt("dd_depth_difference_km_mad")} '
                     f'| {fmt("nll_horizontal_km_median", "{:.2f}")} | {fmt("dd_horizontal_km_median", "{:.2f}")} '
                     f'| {fmt("nll_dt_s_median", "{:+.3f}")} | {fmt("dd_dt_s_median", "{:+.3f}")} |')
    (OUT / 'summary.md').write_text('\n'.join(lines) + '\n')
    print((OUT / 'summary.md').read_text(), flush=True)
    (OUT / 'run.yaml').write_text(yaml.safe_dump(
        {'round': CFG['round'], 'export_root': CFG['export_root'], 'stage': '52_double_difference',
         'config_sha256': {str(p): sha(p) for p in
                           [ROOT / '00_config/config.yaml', ROOT / '00_config/double_difference.yaml']},
         'seconds': round(time.time() - t0, 1)}, sort_keys=False))
    print(f'stage 52 done in {time.time() - t0:.0f}s -> {OUT}', flush=True)


if __name__ == '__main__':
    main()
