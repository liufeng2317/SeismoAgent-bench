### Task objective

Construct a reproducible earthquake-catalog candidate for the 2019 Ridgecrest
sequence from the read-only waveform and station-metadata directory provided to
this run. Discover the available files before processing, state the temporal
scope actually used, and distinguish observed results from assumptions or
unresolved data-quality limitations. Do not claim completeness beyond the
available data and documented processing scope.

### Input data

The input directory is available under `input/waveforms/` after the run-local
input mapping. Explore its contents as needed:

- waveform files are under `input/waveforms/data/`;
- station metadata are under `input/waveforms/stations/`.

Treat the entire `input/` directory as read-only. Do not modify, rename,
delete, or replace any source file.

The current task input exposes waveform and station metadata only. Fault traces
and remote-sensing DEM are not included in this run; do not assume or silently
substitute those resources.

### Task procedure

First write a concise task plan describing file discovery, time coverage,
preprocessing, phase-picking and event-association choices, location method,
quality checks, and known limitations. Then save complete reusable processing
code based on that plan under the assigned output directory and run the saved
code to produce the catalog and supporting results. Record the methods,
parameters, assumptions, provenance and unresolved results so another user can
reproduce the run from the declared inputs and runtime environment.

The agent may choose the internal layout and supporting file names. Keep all
created files below the assigned output directory.

### Required output

Produce a machine-readable `catalog.json` containing a versioned list of
candidate events. Each event should include, when available, an identifier,
origin time with timezone, latitude, longitude, depth, magnitude information,
location method, picks or phase evidence, and uncertainty or status fields.
Missing or uncertain values must be represented explicitly rather than silently
removed.

Also provide concise human-readable documentation and any diagnostic figures or
tables needed to inspect the workflow, data coverage, event quality and major
limitations. The catalog is the required scored artifact; supporting artifacts
are part of the reproducibility record.
