## Task objective

Construct a reproducible candidate earthquake catalog for the 2019 Ridgecrest sequence from the waveform and station-metadata directory provided to this run. The task covers the complete usable waveform collection in the declared input. Discover and inventory the files first, determine their actual UTC coverage, stations and channels, and process all files in the selected coverage. If the data must be processed in partitions, define the partitions before processing and include their results in one consistent catalog. Do not silently select a small example subset.

## Input data

The run-local input is available under `input/waveforms/`. Waveforms are under `input/waveforms/data/`, and station metadata are under `input/waveforms/stations/`. Explore the directory structure and file metadata before analysis. Treat the entire `input/` directory as read-only: do not modify, rename, delete or replace any source file. The task provides waveform and station metadata only; do not assume that other data sources are available.

## Required workflow

First write a concise task plan describing the discovered data coverage, processing scope, preprocessing, event detection, P- and S-phase picking, phase association, location method, quality checks and selected parameters. Then save complete reusable processing code under the assigned output directory and execute that saved code to produce the results. The workflow must proceed from waveform inspection and preprocessing to phase picks, event association and earthquake location. Use the station metadata for station coordinates and any response or channel information needed by the selected method. Record the methods, parameters, assumptions, provenance, data-coverage decisions, missing results and unresolved quality issues so another user can reproduce the run from the declared inputs and runtime environment. The Agent may choose the internal output layout and supporting file names; all created files must remain below the assigned output directory.

## Required output

Produce a machine-readable `catalog.json` containing a versioned list of candidate events. Each event should include, when available, an identifier, origin time with timezone, latitude, longitude, depth, magnitude information, the location method, associated picks or phase evidence, and uncertainty or quality fields. Preserve missing or uncertain values explicitly. Also provide human-readable workflow documentation, a summary of discovered data coverage, and diagnostic figures or tables that allow inspection of waveform preprocessing, phase picks, event association, location results and major data-quality findings. The catalog is the scored artifact; the other files provide the reproducibility and inspection record.
