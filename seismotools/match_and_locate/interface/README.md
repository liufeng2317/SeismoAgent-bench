# Standard Match&Locate interface

Two steps, each with its own JSON contract:

| Step | Entry point | Input | Output |
| --- | --- | --- | --- |
| 1. prepare | `prepare.py` | MiniSEED + station / template / pick tables + velocity model ([prepare_schema.json](prepare_schema.json)) | prepared dataset ([input_schema.json](input_schema.json)) + `dataset.json`, `prepare_report.json` |
| 2. run | `run.py` | prepared dataset + parameters ([config_schema.json](config_schema.json)) | `detections.csv` and job records ([output_schema.json](output_schema.json)) |

Preparation is done once; detection parameters can then be piloted and
re-run on the same dataset. A dataset can also be built directly with the
Python package (`matchlocate_runner`) when a case needs something
`prepare.py` does not express; `run.py` accepts any dataset that follows
`input_schema.json`.

## 1. Prepare

```bash
PY=/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python
$PY seismotools/match_and_locate/interface/prepare.py \
  --waveforms /path/to/miniseed \
  --stations stations.csv \
  --templates templates.csv \
  --picks picks.csv \
  --velocity-model velocity_models.json --model-key <model> \
  --config prepare_config.json \
  --output-dir /path/to/dataset --workers 16
```

Tables: `stations.csv` — `station_id` (NET.STA), `latitude`, `longitude`,
`elevation_m`; `templates.csv` — `event_id`, `origin_time_utc`, `latitude`,
`longitude`, `depth_km`, `magnitude` (optional); `picks.csv` (optional) —
`event_id`, `station_id`, `phase`, `time_utc`.

`prepare_config.json` (every key optional except the segments; defaults in
`prepare_schema.json`):

```json
{
  "processing": {"sampling_rate": 50.0, "freqmin": 2.0, "freqmax": 10.0},
  "segments": {"days": ["2020-03-18", "2020-03-19"]},
  "channels": {"families": ["EN", "EH"], "P": ["Z"], "S": ["N", "E"]},
  "window": {"length_s": 2.0, "before_s": 0.3, "after_s": 1.7},
  "selection": {"max_distance_km": 60.0, "min_snr": 3.0, "min_rows": 12},
  "marks": {"source": "picks_then_model"},
  "depth": {"input_reference": "sea_level", "model_datum_elevation_km": 1.48},
  "run": {"search": {"units": "km", "half_width_km": 1.0, "step_km": 0.25,
                     "half_depth_km": 1.0, "step_depth_km": 0.5},
          "window": {"length_s": 2.0, "before_s": 0.3, "after_s": 1.7},
          "detection": {"cc_threshold": 0.0, "mad_threshold": 10.0, "min_separation_s": 4.0},
          "merge": {"cc_threshold": 0.2, "mad_threshold": 10.0, "min_separation_s": 4.0},
          "min_channels": 12}
}
```

What it does: indexes the MiniSEED headers; picks one channel family per
station; for every template and station within `max_distance_km` computes
model travel times and slownesses (station elevation and the depth datum
included) and takes picks as marks where available; then, per (channel,
day) task, filters and resamples the raw day onto the day's sample grid,
writes the continuous file of scanned days and cuts every template of that
day from the same processed trace (so a template's self-detection reaches
CC = 1). Rows below `min_snr`, P windows that would reach S, templates whose
window leaves the day, and templates with fewer than `min_rows` rows are
dropped; `prepare_report.json` lists each with the reason. Templates are the
caller's choice; `matchlocate_runner.select_templates` offers a spatial-cover
helper.

## 2. Run

```bash
$PY seismotools/match_and_locate/interface/run.py \
  --input-dir /path/to/dataset --output-dir /path/to/run --jobs 16 --threads 4
```

Options: `--config` (parameters; default `<dataset>/config.json`, written by
prepare from its `run` block), `--segments a,b` and `--templates id1,id2`
(subsets, e.g. a one-day pilot), `--bin-dir` (default `../runtime/bin`),
`--resume` (keep jobs whose `job.json` reports success), `--overwrite`,
`--quiet`.

One native job per (segment, template) runs concurrently (`jobs × threads`
cores); detections are merged across templates (and across overlapping
segments) with the SelectFinal rule. `detections.csv` reports origin time,
the best grid node, `depth_km` in the depth reference of the templates table
(`depth_model_km` below the model datum), relative magnitude, CC, N×MAD and
the detecting template. Before any native job the dataset headers are
validated (one SAC reference time per segment, `o = 0`, uniform sampling
and begin time, little-endian, template marks covering the window); failures
stop the run with `status=failed`. A native exit 3 means more samples passed
the thresholds at one node than the buffer holds — raise the thresholds.

## Checking a new setup

1. Prepare one template day plus one scanned day; read `prepare_report.json`
   (rows kept per template, SNR, pick vs model marks).
2. Run on that day: every template whose origin is in the scanned day must
   appear as a `self_detection` at its own location.
3. Pilot thresholds on a subset (`--segments`, `--templates`) with the final
   grid, inspect the weakest kept detections, then run everything with
   `--resume`.

Worked examples: `../examples/smoke` (synthetic, full two-step path with
known answers), `../examples/workflow` and `../examples/ccdistribution`
(upstream examples through `run.py`).
