# Package card: matchlocate_runner

Compact contract for building a Match&Locate run from case data. The
standard boundary is a prepared dataset (layout in
`interface/input_schema.json`) run by `interface/run.py` or
`matchlocate_runner.run_dataset`.

## Recommended sequence

Prefer `interface/prepare.py` (or `matchlocate_runner.build.build_dataset`,
which it wraps): it implements the sequence below for MiniSEED and table
inputs, including station elevations, the depth datum, P/S window overlap,
SNR gates and a per-row report. Write the steps by hand only for inputs it
cannot express. Template choice: `select_templates(catalog, candidates,
radius_km)` returns a greedy spatial cover of the catalog by quality-filtered
candidates.

```python
from obspy import UTCDateTime
from matchlocate_runner import (LayeredModel, first_arrival, epicentral_km, Template, ChannelPhase,
                                write_templates, write_channels)
from matchlocate_runner.prepare import Processing, process_continuous, write_continuous_sac, cut_template, window_snr

model = LayeredModel.from_rows(velocity_rows)          # rows with top_of_layer_km, vp_km_s, vs_km_s
proc = Processing(sampling_rate=50.0, freqmin=2.0, freqmax=10.0)

# 1. continuous: one processed trace per channel-day, reference = day start, o = 0
day = UTCDateTime("2020-03-20")
tr = process_continuous(raw_stream_for_channel_day, proc, start=day)        # 86,400 s on the day grid
write_continuous_sac(tr, f"{ds}/continuous/20200320/{channel}.sac", reference=day,
                     station_lat=slat, station_lon=slon, station_elev_m=selev)

# 2. templates: cut from the SAME processed trace of the template's day
ray_p = first_arrival(model, "P", epicentral_km(slat, slon, elat, elon), edepth_model, receiver_depth)
ray_s = first_arrival(model, "S", ...)
cut_template(tr, origin, pre_s=2.0, post_s=20.0, marks={1: tt_p, 2: tt_s},
             event_lat=elat, event_lon=elon, event_depth_km=edepth_model, magnitude=mag,
             station_lat=slat, station_lon=slon, path=f"{ds}/templates/{tid}/{channel}.sac")

# 3. tables: one row per correlated channel-phase (e.g. P on Z with mark 1, S on N/E with mark 2)
write_templates(f"{ds}/templates.csv", [Template(tid, str(origin), elat, elon, edepth_model, mag)])
write_channels(f"{ds}/channels.csv", [ChannelPhase(tid, channel, "S", 2,
                                       ray_s.slowness_h_s_per_deg, ray_s.dtdz_s_per_km), ...])
```

Then `python interface/run.py --input-dir ds --output-dir run --jobs J --threads T`.

## Rules that the native program does not check for you

- Templates and continuous data must share filter and sampling rate. Cut
  templates from the processed continuous data (`cut_template` on the output
  of `process_continuous`); a template's self-detection must then come out at
  CC = 1.0 — use that as the first sanity check of a new dataset.
- Template t-marks are travel times relative to the template origin
  (reference = origin, `o = 0`); `cut_template` snaps the origin to the
  sample grid and rounds marks to whole samples. Observed picks may replace
  model travel times as marks (better window alignment); slownesses still
  come from the model.
- Depth convention: `traveltime` depths are km below the model datum (the
  layer-top origin). `templates.csv` `depth_km`, the template SAC `evdp` and
  the grid all use that same depth; convert to/from below-sea-level depth in
  the calling workflow and record the datum.
- `dtdz_s_per_km` is `dT/dz_source`: positive for the usual upgoing direct
  ray, negative for a head wave (deeper source is closer to the refractor).
- The moveout about the template is linear in epicentral distance and depth.
  Keep the search half-width where the linearisation error stays well below
  a quarter period; `linearisation_error_s(model, phase, station, template,
  offset)` computes it for a geometry. Cover a large volume with several
  templates rather than one wide grid.
- N(*MAD) is computed per grid node over the whole continuous segment; more
  nodes = more independent tests = more noise detections at a fixed threshold.
  Choose `mad_threshold` with the grid fixed, and eye-check the weakest
  detections (upstream guidance).
- Magnitudes are `template magnitude + median log10(peak amplitude ratio)`:
  relative, inheriting the template magnitude scale, and biased high when the
  detected signal is only a few times the noise.
- Sampling: a uniform `delta` per segment is required. Gaps are zero-filled by
  `process_continuous` (zeros correlate to 0 and only dilute the stack).

## Scale

Per (segment, template) job, cost grows with rows x samples x (window length for
the single correlation pass + grid nodes for shift-and-stack); memory with
rows x samples (8 bytes per correlogram sample plus 4 per waveform sample).
Measured numbers for this host are in `docs/core/METHOD_NOTES.md` of the
tool. Use `--resume` for long runs and subsets (`--segments`, `--templates`) to
pilot parameters before a full run.
