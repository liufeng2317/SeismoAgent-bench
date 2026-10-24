# Match&Locate (MatchLocate2)

Match&Locate (Zhang & Wen 2015, GJI 200, 1523–1537) detects small earthquakes
in continuous data with template waveforms and locates each detection at the
same time. Each channel-phase of a template is correlated once with the
continuous trace; the correlograms are then shifted by the relative travel
time predicted for every node of a 3-D grid around the template, stacked,
and thresholded by CC and by N×MAD of the stack. The node with the highest
stack gives the detection's location, and the median peak-amplitude ratio to
the template gives a relative magnitude. With a zero-size grid the method is
the classic matched filter. Curated method notes are in
[docs/README.md](docs/README.md).

## Directory layout

```text
match_and_locate/
├── source/
│   ├── upstream/            # MatchLocate2-master snapshot (C source, examples, reference outputs; PDFs local only)
│   └── patches/             # local patches 0001-0007 + README with evidence
├── runtime/
│   ├── bin/                 # MatchLocate2, SelectFinal, SHIFT, lsac (built, not committed)
│   ├── build/, build.log    # rebuild cache and log (not committed)
│   ├── python/MatchLocatepy/# matchlocate_runner package: preparation, travel times, jobs, merge
│   └── example_data/        # extracted example archive and generated datasets (not committed)
├── interface/               # standard entry point and JSON contracts
├── examples/{smoke,workflow}/
├── docs/{core}/
├── metadata.json
└── README.md
```

Build (patches are applied to a copy; `source/` is never modified):

```bash
python seismotools/support/build_native.py --tool match_and_locate
```

The upstream distribution's binaries are macOS x86-64 and are not used.
Version 2.0 (`MatchLocate2.c`) is built; 2.1 and `ccsacc` need SAC's libsac
and are kept as source only — filtering happens during data preparation.

## Standard interface

Two steps ([interface/README.md](interface/README.md)):

```bash
# 1. MiniSEED + stations/templates/picks tables + velocity model -> prepared dataset
python seismotools/match_and_locate/interface/prepare.py --waveforms DIR --stations stations.csv \
  --templates templates.csv [--picks picks.csv] --velocity-model model.csv \
  --config prepare_config.json --output-dir DATASET --workers 16
# 2. prepared dataset -> detections.csv
python seismotools/match_and_locate/interface/run.py \
  --input-dir DATASET --output-dir RUN --jobs 16 --threads 4
```

`prepare.py` ([prepare_schema.json](interface/prepare_schema.json)) filters the
data, cuts templates from the processed continuous data, computes marks
(picks or model) and slownesses with the station elevations and depth
datum, gates rows by SNR and writes a per-row report.

The prepared dataset holds `templates.csv`, `channels.csv`,
`templates/<id>/<channel>.sac` and `continuous/<segment>/<channel>.sac` (a segment is
normally one UTC day; `prepare.py` writes it, or build it with the Python package)
([input_schema.json](interface/input_schema.json)); parameters come from
`config.json` ([config_schema.json](interface/config_schema.json)). The run
writes `detections.csv` (merged catalog), `template_detections.csv`,
`jobs.csv`, per-job native records and `run_result.json`
([output_schema.json](interface/output_schema.json)). See
[interface/README.md](interface/README.md).

## Python package

`runtime/python/MatchLocatepy/matchlocate_runner` prepares datasets (ObsPy
processing onto the day grid, continuous SAC, templates cut from the
processed data, layered-model travel times and the slownesses the native
moveout needs), validates them, runs the jobs and merges. Contract and
recommended sequence:
[MATCHLOCATEPY_CARD.md](runtime/python/MatchLocatepy/docs/MATCHLOCATEPY_CARD.md).

## Native command-line usage

```bash
BIN=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/match_and_locate/runtime/bin
cd /path/to/job        # INPUT.in paths are relative to the working directory
OMP_NUM_THREADS=8 "$BIN/MatchLocate2" -F40.751/-112.078/11.5 -R0.009/0.012/1.0 -I0.00225/0.003/0.5 \
  -T2.0/0.3/1.7 -H0.0/9.0 -D4.0 -O0 INPUT.in      # writes EventCase.out
"$BIN/SelectFinal" -H0.3/9.0 -D4.0 Allevents      # writes Allevents.final
```

`-F` grid center (template lat/lon/depth), `-R` half-widths (deg/deg/km),
`-I` steps (all > 0), `-T` window/before/after the phase mark (s), `-H`
CC/N×MAD thresholds, `-D` de-duplication window (s), `-O` diagnostic output.
`INPUT.in` format and units are documented in
`runtime/python/MatchLocatepy/matchlocate_runner/native.py`.

## Examples and validation

```bash
bash seismotools/match_and_locate/examples/smoke/run.sh            # synthetic MiniSEED -> prepare -> run, known answers, ~75 s
bash seismotools/match_and_locate/examples/workflow/run.sh \
  /liufeng1afs/software/Download/MatchLocate2-master.zip            # upstream Hi-net example, ~35 s
bash seismotools/match_and_locate/examples/ccdistribution/run.sh \
  /liufeng1afs/software/Download/MatchLocate2-master.zip            # upstream CC-distribution example, ~40 s
python seismotools/support/tools_usage_validation/validate_match_and_locate.py
```

The synthetic example recovers five injected events exactly in time, the
two offset events within 6 m and 0 km depth, and relative magnitudes within
0.08 except a low-SNR event (+0.22, the expected high bias of a peak-amplitude
ratio). The Hi-net replay matches the upstream outputs field for field on
1,179 detections; its remaining differences are explained by a thread race in
the upstream build ([examples/workflow/README.md](examples/workflow/README.md)). The
CC-distribution replay (40,401 nodes, `-O3`) has identical CC on all 390,107
rows common with upstream and reports the same event
([examples/ccdistribution/README.md](examples/ccdistribution/README.md)).
These checks show that the tool runs and behaves as designed; they do not
qualify detection thresholds or parameters for a case.
