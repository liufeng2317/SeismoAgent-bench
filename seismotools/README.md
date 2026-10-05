# Seismology tools

Local, reusable tool snapshots for controlled catalog-building experiments. These are **real copies**, not symlinks to TRACE or the expert exports. The Ridgecrest expert pipeline still uses its recorded original paths; this addition does not change historical results or automatically migrate callers.

| Tool | Purpose | Saved implementation / configuration | Documentation |
| --- | --- | --- | --- |
| PhaseNet | P/S picking | TRACE model package; `original` v2 weights | [Phase picking](phase_picking/README.md) |
| DPPPicker P | Conditional vertical P refinement | Same model package; SCEDC weights | [Phase picking](phase_picking/README.md) |
| EQTransformer | Alternative picking; retained S additions | Same model package; `original_nonconservative` v1 | [Phase picking](phase_picking/README.md) |
| GaMMA | Arrival association | Local source; setup reports GMMA 1.2.17 | [GaMMA](gamma/README.md) |
| NonLinLoc | Absolute location and travel-time grids | Actual local NLL7.00 source | [NonLinLoc](nonlinloc/README.md) |
| hypoDD | Differential relocation, CT or CT+CC | Local native source and executed full-cohort array capacities | [hypoDD](hypodd/README.md) |

`hypoDD CT` and `hypoDD CT+CC` are configurations of **one program**, not separate tool copies. PhaseNet/DPP/EQTransformer share model infrastructure, so their common code is stored once under `phase_picking/source/`. Extra model modules there preserve the original package imports; they are not additional validated tools.

## Layout and use

```text
seismotools/
  README.md
  registry.json                 # one source/weight inventory, identities and provenance
  environment.txt               # observed Python dependency versions, not a portable lockfile
  check_tools.py                # integrity, offline imports and strict CPU weight loading
  build_native.py               # builds native tools outside immutable source snapshots
  phase_picking/{source,weights,docs,README.md}
  gamma/{source,docs,README.md}   # tutorials, DeepWiki and retrieval text
  nonlinloc/{source,runtime,interface,examples,README.md}
  hypodd/{source,README.md}
```

From the project root, using the existing `seismoagent` environment:

```bash
conda run -n seismoagent python seismotools/check_tools.py
conda run -n seismoagent python seismotools/check_tools.py --imports
conda run -n seismoagent python seismotools/build_native.py --tool all --jobs 4
```

The first check uses only the standard library. `--imports` also imports local GaMMA and loads all three model state dictionaries strictly on CPU, without downloading weights. Building needs `make`, `gcc` and `gfortran`; binaries and logs stay inside each tool folder. Passing these checks establishes integrity/loadability/buildability, **not scientific equivalence of a new experiment**.

For a new Python process, add `seismotools/phase_picking/source` and/or `seismotools/gamma/source` to `sys.path` before importing `phase_picking` or `gamma`. Read weights directly from `phase_picking/weights`; avoid automatic pretrained downloads. New native callers can use `nonlinloc/runtime/bin/{NLLoc,Vel2Grid,Grid2Time}` and `hypodd/native/bin/hypoDD` after building. Existing Ridgecrest launchers are not yet wired to these paths.

## Scope and controlled comparisons

Tool folders contain reusable implementations and manuals. Waveforms, station metadata, velocity grids, case thresholds, event catalogs and evaluation references stay in their existing case/data directories. The custom **Joint DD** solver remains in the expert case because its current imports and assumptions are case-specific; it is not copied and advertised as a generic tool. ObsPy, SeisBench, PyTorch and SciPy are environment dependencies recorded in `environment.txt`, not duplicated installed environments.

For each future benchmark, record the tool/source identity, model weights, parameters, allowed input files, CPU/thread limits and outputs. Change one tool/configuration at a time while fixing the observation cohort, velocity model and evaluation matches where scientifically possible. Reference catalogs and expert outcomes are evaluator inputs, not automatic tool inputs. This folder organizes implementations; it does not itself enforce an isolated agent environment.

Add a future tool as `<tool>/{source,README.md}`, optionally with `weights/` and `docs/`. Document inputs/outputs, dependencies, source identity and one small validation command; extend the shared registry and check only when the tool is actually used. Preserve third-party notices. No new license is assigned to copied code; local folders without a standalone license are identified in the registry.

Weights are copied locally but ignored by Git, together with manual PDFs, builds and binaries. Source, metadata and Markdown documentation remain reviewable. A Git-only checkout therefore needs the registered local weights restored before model checks can pass; no fetcher or automatic installer is implied.

## Initial validation

The initial 197-file runtime snapshot passed byte-identity checks; the expanded documentation inventory is recorded in `registry.json`. Unmodified copies retain source bytes; notebooks have an explicitly recorded output-stripping transformation. The three model state dictionaries loaded strictly on CPU from the copied package, local GaMMA imported, and NLLoc/Vel2Grid/Grid2Time/hypoDD compiled successfully. Compiler identities and local binary hashes are recorded in `registry.json`. No earthquake catalog was recomputed, and no old tool paths were switched.

## Documentation coverage and exclusions

The first transfer was a runnable-source subset, not a complete documentation archive. The subsequent audit added GaMMA's 30 DeepWiki pages, five docs notebooks and their available image assets, original example/test code, and text from its retrieval index. It also added available NonLinLoc control/program manuals stored under Nonlinlocpy, plus original phase-picking inference examples. Follow each tool README for the reading order.

Source-distributed manuals, secondary generated descriptions and runnable implementations are distinguished. Examples retain original assumptions and may reference data not copied here; copied documentation is not a claim that every tutorial has been executed. Example datasets, old results, backups, embedding vectors, agent-service code and unused model weights remain excluded. Available source documents are preserved; missing pages in the original local library remain missing. `registry.json` records the scope and any transformations rather than asserting a complete copy of all TRACE tools or all documents historically read by an agent.
