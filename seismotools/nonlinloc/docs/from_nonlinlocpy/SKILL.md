---
name: nonlinlocpy
description: Use when working with NonLinLoc earthquake location workflows in this repo, including preparing control files, building 1-D or 3-D velocity grids, generating station travel-time tables, writing NLLOC_OBS picks, running NLLoc or related tools, and explaining when to use NLLoc, SSST, or NLDiffLoc.
---

# NonLinLoc

Use this skill when the task involves the NonLinLoc toolchain rather than a single executable. In this repo, the local Python wrapper and templates live under `seismoagent/library/basic_fun/Nonlinlocpy/`.

## What NonLinLoc Is

NonLinLoc is a modular earthquake-location toolkit built around this flow:

1. Build a velocity model grid.
2. Compute station travel-time grids.
3. Run nonlinear probabilistic location.
4. Optionally apply station corrections, relocation, or differential location.

The key programs are:

- `Vel2Grid` / `Vel2Grid3D`: convert 1-D layered or 3-D models into NonLinLoc grid files.
- `Grid2Time`: compute P/S travel-time tables from each station to all grid points.
- `NLLoc`: run nonlinear probabilistic absolute location.
- `Loc2ssst`: estimate source-specific station terms from a catalog of NLL results.
- `NLDiffLoc`: run differential-event global-search relocation.
- `LocSum`, `Grid2GMT`, and converters: summarize, convert, or visualize outputs.

## When To Use Which Method

- Use `NLLoc` for standard absolute event location with uncertainty.
- Use `NLLoc + SSST` when catalog-scale residual patterns suggest station or source-region bias.
- Use `NLDiffLoc` for clustered events with usable differential times or waveform-correlation picks.
- Use `Vel2Grid3D` only when a credible 3-D velocity model already exists and has been resampled to a regular grid format that NonLinLoc can use.

## Repo Entry Points

- `workflows.py`: user-facing `NLLocConfig` / `run_nlloc` facade for prepared inputs.
- `models.py`, `control.py`, `velocity.py`, `stations.py`, `observations.py`, `runner.py`, `hyp.py`: focused implementation modules.
- `run_nlloc_cli.py`: optional thin CLI wrapper that delegates to `run_nlloc`.
- `template/nlloc.in`: control-file skeleton.
- `template/velocity_model_1d.example.txt`: editable 1-D depth/Vp/Vs template.
- `template/stations_native.example.txt`: station table example.
- `template/picks_simple.example.txt`: simple pick table for automatic conversion to `NLLOC_OBS`.
- `template/event.obs.example`: arrival example.

## Required Inputs

Prepare or verify these before running location:

- A control directory containing `nlloc.in`.
- A velocity-model definition:
  either `LAYER` lines for 1-D models, or a prepared 3-D grid workflow.
- Station metadata with `station_id lon lat elev_m`.
- Observed arrivals in `NLLOC_OBS` layout or in a simple table that will be converted.
- A valid NonLinLoc binary directory on `PATH`, or passed explicitly to the wrapper.

## Standard 1-D Workflow

Use this as the default path unless the user explicitly needs 3-D relocation.

1. Copy `template/nlloc.in` into a run directory.
2. Set or patch `VGGRID`, `LOCGRID`, `LOCFILES`, and other control lines.
3. Start from `template/velocity_model_1d.example.txt`, then build `LAYER` lines from depth, `Vp`, and `Vs`, and write them into the Vel2Grid section.
4. Run `Vel2Grid` to generate model grids after the velocity model changes.
5. Inject `GTSRCE` station lines and run `Grid2Time` for both P and S.
6. Write the event picks as `obs/All.obs`.
7. Run `NLLoc`.
8. Parse `.hyp` outputs and prefer `GEOGRAPHIC` solutions when present.

## Standard 3-D Workflow

Use this only when the task explicitly requires lateral heterogeneity.

1. Convert the external 3-D model to the coordinate system and grid spacing expected by NonLinLoc.
2. Generate NonLinLoc-compatible 3-D velocity grids with `Vel2Grid3D` or a preprocessing conversion script.
3. Run `Grid2Time` for each station and phase.
4. Run `NLLoc` with the same observation and search-grid logic as in the 1-D workflow.

## Python Wrapper Guidance

Prefer `workflows.py` for normal usage and the focused implementation modules when you need lower-level automation:

- `velocity.py`: create and patch `LAYER` lines for 1-D models.
- `control.py`: patch `VGGRID` / `LOCGRID` and preserve template station sections.
- `stations.py`: write `GTSRCE` entries and run `Grid2Time` for P and S.
- `observations.py`: build `NLLOC_OBS` arrivals from pick tables.
- `runner.py`: clear run directories and run `NLLoc`.
- `hyp.py`: read location outputs from `loc/*.hyp`.

## Control-File Mindset

Do not treat NonLinLoc as a command-line-flag-first tool. Most work happens through the control file. These keywords are usually the ones to inspect first:

- `TRANS`: coordinate transform.
- `VGGRID`: velocity-grid geometry.
- `LAYER`: 1-D layered model.
- `GTFILES`: travel-time grid configuration.
- `GTSRCE`: station/source definitions for travel-time generation.
- `LOCFILES`: observation, travel-time, and output paths.
- `LOCMETH`: misfit and error settings.
- `LOCSEARCH`: search mode such as grid, Metropolis, or oct-tree.
- `LOCGRID`: search-space extent and spacing.

## Practical Interpretation

- `NLLoc` is the default absolute-location engine.
- `SSST` is an iterative residual-based correction workflow, not a magic accuracy switch.
- `NLDiffLoc` is best for dense clusters with strong event-pair constraints.
- Better 3-D structure can improve results, but a poor 3-D model can also introduce systematic bias.

## Output Expectations

After a successful run, expect outputs mainly under `loc/`:

- event `.hyp` files
- summary or auxiliary location products
- optional geographic or projected coordinates depending on output content

When parsing results in code, prefer:

1. `GEOGRAPHIC` lines in `.hyp`
2. fallback conversion from `HYPOCENTER x/y/z` with saved UTM zone metadata

## Working Rules

- Prefer the local Python wrapper over handwritten shell snippets when automating repeated runs.
- Keep station IDs and phase codes compatible with NonLinLoc formatting expectations.
- Regenerate travel-time grids whenever the station set or velocity model changes.
- If the task is only explanatory, answer in terms of the full toolchain, not just `NLLoc`.
- If a user asks for “NonLinLoc location,” confirm whether they mean standard absolute location, SSST relocation, or differential relocation.
