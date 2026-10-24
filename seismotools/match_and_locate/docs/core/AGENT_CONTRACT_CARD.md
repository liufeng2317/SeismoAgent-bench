# Tool contract card: Match&Locate

This card has priority over examples. It states what the tool does, what it
needs, and the decisions that remain with the calling workflow.

## What it produces

For each continuous day and each template: detections whose stacked
correlation over the template's channel-phases exceeds the thresholds, each
with origin time, the best grid node (lat, lon, depth), mean CC, N×MAD and a
relative magnitude. Across templates, detections within a separation window
are merged to one event (highest N×MAD; self-detections kept). Locations are
**relative to the template** and inherit its absolute position error;
magnitudes inherit the template magnitude scale.

## Entry points

- `interface/prepare.py` — MiniSEED + station/template/pick tables + velocity
  model → prepared dataset, with `prepare_report.json` (every row kept or
  dropped and why). Start here.
- `interface/run.py --input-dir DATASET --output-dir RUN [--jobs J --threads T]`
  — detection, location and merge; writes `detections.csv` and `run_result.json`.
- `matchlocate_runner` (Python) — the same steps as functions, plus
  `select_templates` (spatial-cover helper) for choosing templates.
- Native `runtime/bin/MatchLocate2` / `SelectFinal` — only for diagnostics
  (`-O1/2/3` outputs) or when the dataset contract cannot express a need.

## Required decisions (case-level; record them with the results)

1. **Templates.** Which events (well-located, adequate SNR on enough
   stations), and how many. Coverage, not count, matters: the search grid
   covers about ±1 km per template on a local network (below), so templates
   must sample the active volume at about that spacing.
2. **Processing.** One band and one sampling rate for templates and
   continuous data. Cut templates from the processed continuous data;
   confirm CC = 1.0 self-detections on the template days.
3. **Channel-phases.** Which components carry which phase (commonly P on
   vertical, S on horizontals), window `before/after` around the mark, a
   per-channel template SNR gate, and the minimum number of rows per job.
4. **Marks.** Observed picks or model travel times for the t-marks
   (picks align windows better); slownesses from a layered model.
5. **Grid.** Half-width and step per axis. Check the linearisation error
   (`linearisation_error_s`) for the network geometry; keep it well below a
   quarter period of the band's dominant frequency.
6. **Thresholds.** Per-template `cc_threshold`/`mad_threshold`/`min_separation_s`
   and the merge thresholds. Set them on a pilot subset with the final grid
   (false detections grow with node count), then inspect the weakest kept
   detections.

## Validity checks before claiming results

- `run_result.json` status `success`, no failed jobs; skipped jobs explained
  by `min_channels`.
- Template self-detections at CC = 1.0 on their own days, at the template
  location (node 0, 0, 0).
- Detection count vs threshold curve on the pilot is smooth; the weakest
  accepted detections show coherent waveforms on several stations.
- Known catalog events in the window are recovered (as matches, not
  necessarily as self-detections).
- Do not report M&L magnitudes below the template scale's calibration range
  without a check: the peak-amplitude ratio reads high near the noise.

## Failure meanings

- Validation error: dataset violates the layout or SAC header rules; nothing
  ran. Fix the preparation, not the thresholds.
- Native exit 3: more samples exceeded the thresholds at one node than the
  buffer (2 × duration) holds — thresholds too low for the data.
- Large memory: about `rows × samples × 12` bytes per job (correlograms in
  double precision plus waveforms); 90 rows × one day at 50 Hz ≈ 4.4 GB.

## Do not

- Use another case's reference catalogs to choose templates or thresholds in
  a benchmark run.
- Mix sampling rates or filters between templates and continuous data, or
  between days.
- Widen the grid to compensate for missing templates on a local network.
