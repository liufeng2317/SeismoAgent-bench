# Cross-correlation differential times (ccdt)

Measures waveform cross-correlation differential travel times between
earthquake pairs and writes them as `dt.cc`, the input format of both hypoDD
(`getdata.f`) and GrowClust (`xcordata`). It is the measurement step of
cross-correlation double-difference relocation. Events need no picks: the
arrival that positions each window may be a pick or a prediction (for
template-matching detections, the template's arrival shifted by the
detection's origin time), because the measured dt does not depend on it.

## Method

For a pair (a, b) at one station and phase:

1. **Windows.** Each channel is read file by file with `pad_s` of the
   neighbouring files (so windows across UTC midnight are complete), split at
   gaps, demeaned, detrended, tapered and band-pass filtered (Butterworth,
   zero phase) as a long trace; only then are windows cut. The search window
   `[t − before − max_lag, t + after + max_lag]` is stored with the exact UTC
   epoch of its first sample (float64).
2. **Correlation.** The central `[t_a − before, t_a + after]` of a's window
   (first sample `s_a`) slides over b's search window (first sample `u_b`);
   at each lag the Pearson coefficient of the two equal-length segments is
   computed (each demeaned and normalized over the overlap itself). S uses
   every horizontal present for both events (N/E or 1/2), averaging the
   per-component curves; P uses Z.
3. **Peak.** Integer peak plus a parabola through its neighbours gives the
   fractional lag. A measurement is accepted only when the peak is positive,
   not on the first or last lag, ≥ `min_cc`, larger than the magnitude of the
   most negative value (`anticorrelated` otherwise — a polarity-reversed pair
   has positive side lobes half a period from its true lag), not rivalled by a
   second local maximum ≥ `ambiguity_ratio` × peak at least
   `ambiguity_guard_s` away (`ambiguous`: a second event in the window), when
   the two windows do not overlap in absolute time (`self_overlap`: the
   template would find its own signal), and when both windows have
   SNR ≥ `snr.min` (RMS of the template part over the `noise_s` before it).
4. **dt.** The template's first sample aligns with
   `s'_b = u_b + (L + p)·δ` in b, so
   `dt = (s_a − o_a) − (s'_b − o_b)` = tt(a) − tt(b), the hypoDD/GrowClust
   convention. Picks or predictions cancel; only the waveforms and the two
   origin times enter.

Pairs: every event with its `max_neighbors` nearest events within
`max_distance_km` (hypocentral), or an explicit pair list. Station codes go to
`dt.cc` without the network, so a code repeated across networks is an error.

## Interface

```bash
python interface/run.py --events events.csv --arrivals arrivals.csv \
    --waveforms <MiniSEED root> --output-dir <run> [--pairs pairs.csv] \
    [--config overrides.json] [--workers N]
```

Input/output contract and configuration: [interface/README.md](interface/README.md).
Defaults: `runtime/python/ccdt/pipeline.py` `DEFAULT_CONFIG`.

## Validation

`support/tools_usage_validation/validate_cross_correlation.py` (2026-10-25: pass):

| Check | Result |
|---|---|
| Kernels | Pearson curves identical to a brute-force loop (3e-16); parabola recovers a 0.3-sample offset to 4e-4 |
| Synthetic known answers (`examples/smoke`): 40 events, 12 stations, fractional-sample arrivals, a midnight file boundary, a 1/2-component station, an E-only station, a 200 Hz station, a polarity-reversed station, an overlapping pair, picks exact / ±0.1 s / +0.15 s predicted | dt error median 0.005 samples, p95 0.023 (100 Hz), 0.014 (200 Hz); no bias from arrival errors (median ≤ 5e-4 samples per class); no polarity-reversed or overlapping pair accepted with a wrong dt; 1 and 4 workers give identical `dt.cc` |
| Real data: 76 well-picked events of a dense aftershock sequence (two hours), PhaseNet picks as arrivals | 1,496 accepted; CC dt − pick dt median 0.8 ms, MAD 18 ms, robust slope 0.989, 8.5 % beyond 0.1 s (pick errors included) |

## Relation to FDTCC

The hypoDD package bundles FDTCC (LOC-FLOW). A source audit (2026-10-25)
found its dt sign correct but: integer-sample lags and rounded window starts
(±1.5 samples), float32 seconds-of-day times, |CC| peaks (anti-correlation
accepted), no edge-peak rejection, no per-window demeaning, filtering of the
short windows, E/N-only horizontals, a crash on a missing N file, a file
descriptor leak, fixed array limits (30,000 events), and a travel-time table
indexed from distance 0 while the bundled `build_ttdb.py` starts at one step.
This tool replaces it for cross-correlation measurement; FDTCC is kept in the
hypoDD package unchanged.

## Layout

```text
cross_correlation/
├── interface/run.py, README.md     # standard entry point and contract
├── runtime/python/ccdt/            # windows.py, correlate.py, pipeline.py
├── examples/smoke/                 # synthetic known-answer dataset and checker
└── metadata.json
```
