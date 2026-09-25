# Ridgecrest waveform quality review

Generated: 2026-09-24T23:54:37.908695+00:00

Window: [2019-07-04T00:00:00.000000Z, 2019-07-07T00:00:00.000000Z). Candidate window, not a frozen benchmark input.

Fully decoded 351 MiniSEED files; 117 NSLCs at 41 stations.
Finite samples: 3,032,636,544; nonfinite samples: 0; exact-zero samples: 1,565,376.
Decode/concurrent-change errors: 0. Files with decoding warnings: 0.
Minimum channel coverage: 99.988870%. Summed missing channel-seconds: 34.560901. Summed overlap channel-seconds: 0.000901.

## Coverage and sample checks

Coverage is the union of actual decoded segment intervals, clipped to the candidate window, with each last sample representing one sample interval. Deficits include day/window edges and internal gaps. Small offsets are reported without rounding them into entire missing samples. Hourly station coverage is the minimum over its observed NSLCs; it does not assert that absent components exist.

Gaps longer than 1 s:

- `CI.WRC2..HHZ`: 2019-07-06T05:15:39.578300Z to 2019-07-06T05:16:06.968300Z, 27.390000 s.

Constant-run screening flags: 0 channel-days. Thresholds: identical samples for ≥1 s, or identical values at a segment minimum/maximum for ≥0.1 s. These are screening flags, not proven ADC clipping; extrema are segment-local and runs are measured within decoded segments (not across boundaries). Exact zeros alone are not evidence of zero filling. Nonfinite values are excluded from amplitude statistics.


## Exploratory preprocessing

The Mw 7.1 comparison uses CI.CCC..HHZ, CI.APL..HNZ and CI.WRC2..HHZ. Read −90 to +150 s around 2019-07-06 03:19:53.040 UTC; show −30 to +120 s. Merge exactly adjacent segments only, then process each contiguous segment separately: linear detrend, demean, 5% cosine taper, fourth-order 2–12 Hz Butterworth bandpass applied forward/backward. Welch PSD uses the displayed interval, up to 4096 samples per segment and SciPy defaults (Hann window, 50% overlap, constant detrending, density scaling).

This zero-phase trial is an offline diagnostic, not a causal picker configuration. Filtering can alter arrival shape and amplitude. The frequency band is exploratory and must be validated against the later task. No resampling, gap interpolation, response removal, rotation or normalization is applied. All amplitudes remain digital counts; HH/EH and HN have different native physical inputs and must not be compared as ground-motion amplitudes. CI.APL HN requires explicit response correction before physical-unit comparisons. Raw files are opened read-only and are not rewritten.

Visual inspection shows flattened large excursions on some HH traces during the mainshock. This may reflect sensor/digitizer limitations, but counts alone do not establish the cause. Exact-value plateau screening cannot rule out analog clipping or soft saturation. Check instrument sensitivity, operating range and calibrated nearby acceleration records before accepting these intervals for amplitude-based tasks.

## Outputs and next decisions

- [Hourly coverage](01_coverage.png): minimum observed-channel coverage at each station; color scale 99–100%, lower values clipped at the lower bound.
- [Coverage deficits and amplitudes](02_quality.png): raw-count amplitudes are screening statistics, not calibrated station comparisons.
- [Mainshock detail](04_mainshock_detail.png): unfiltered HHZ traces, 10–30 s after origin; flattened excursions warrant saturation review despite no exact-extrema plateau flags.
- [Waveforms and spectra](03_preprocessing.png): raw versus trial filtering; PDF versions accompany all figures.
- `channel_day_quality.csv`: path, bytes, rate, segment/sample counts, zeros, nonfinite samples, amplitude and plateau screening, decode warnings.
- `channel_coverage.csv`, `gaps.csv`, `hourly_quality.csv`: compact derived tables supporting the plots; the external inventory remains the file inventory.

Before freezing inputs: inspect flagged plateaus in raw time series and instrument limits; validate response epochs, sensitivity and orientation (especially 1/2 components); compare physically calibrated noise/event spectra; decide whether to retain single-component stations and how to mask the known unavailable gap. This scan does not prove phase-picking readiness, timing accuracy, response correctness or absence of clipping. Processing parameters and station policy remain provisional.
