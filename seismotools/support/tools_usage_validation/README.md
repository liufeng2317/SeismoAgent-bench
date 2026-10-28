# Tool usage validation

This directory contains environment checks for the locally bundled
seismological tools: synthetic known-answer tests and, where the upstream
project ships one, its example reproduced by the local build. Native-tool
checks use temporary directories. Checks on real case data are kept with the
benchmark, outside this library.

Run all checks with:

```bash
bash run_all.sh
```

Set `PYTHON` when a different compatible environment is intended:

```bash
PYTHON=/path/to/python bash run_all.sh
```

`synthetic_events.py` is the shared known-answer generator for the association
and location validations (uniform half-space, analytic travel times; optional
pick noise, false picks, dropped picks, one outlier).

The checks are deliberately small:

| Script | Validation |
| --- | --- |
| `validate_phasenet.py` | Synthetic CPU forward pass with the bundled weights. |
| `validate_gamma.py` | Synthetic P/S association. |
| `validate_pyocto.py` | Travel-time table built by PyOcto against analytic half-space times (first-order fast marching: never faster, ≤ 0.1 s P at 0.25 km); the shared synthetic case with 0.05-s noise, 3 false picks per station and 10 % dropped picks (≥ 95 % events within 1 s / 3 km, ≥ 95 % true picks on the right event, 1 vs 4 threads same events; false-pick absorption < 5 % at `pick_match_tolerance` 0.5). |
| `validate_real.py` | REAL's travel-time table (fast marching) against analytic half-space times and slopes; the shared synthetic case (noise, false and dropped picks) on one day and across midnight (two chunks, no duplicate events; ≥ 95 % events, ≥ 95 % true picks correct, < 5 % false picks absorbed). |
| `validate_nonlinloc.py` | Bundled `Nonlinlocpy` import, default sibling-binary resolution and template resource, tiny synthetic grids; the v2 adapter's smoke solution under all three `location_method`s (default unchanged); the v3 catalog locator `locate.py` on the shared synthetic half-space case (`synthetic_events.py`: 40 known hypocentres within 0.1 km / 0.15 km depth / 0.02 s for every method; one 2-s outlier pick: EDT less affected than GAU_ANALYTIC). |
| `validate_hypoinverse.py` | The gfortran build reproduces the upstream `testone` summary and archive exactly (path via `HYPOINVERSE_TESTONE`, skipped when absent); the interface on the shared synthetic case in both hemispheres (40 known hypocentres within 0.1 km / 0.2 km depth / 0.03 s; all arrivals parsed back). |
| `validate_hypodd.py` | Bundled `hypodd_runner` import, public configuration API and template, synthetic native relocation. |
| `validate_match_and_locate.py` | `matchlocate_runner` travel times against analytic solutions, SAC header reader against ObsPy, `select_templates` on two clusters, a synthetic end-to-end run of both interface steps (raw MiniSEED and tables → `prepare.py` → `run.py`) with known answers (detection times, offset locations, depths through the sea-level/datum conversion, relative magnitudes), and both upstream examples through the interface: Hi-net (1 vs 8 threads identical, Python merge equal to native `SelectFinal`, comparison with the upstream outputs) and CC distribution (per-node CC identical to upstream on all common rows, same detected event). Its real-data check is the upstream example (archive path via `MATCHLOCATE_ARCHIVE`, skipped when absent). |
| `validate_cross_correlation.py` | `ccdt` kernels against a brute-force Pearson loop and an analytic parabola; the synthetic known-answer dataset (`examples/smoke`: fractional-sample arrivals, midnight file boundary, 1/2 and E-only horizontals, 200 Hz, polarity reversal, overlapping events, exact/erroneous/predicted arrivals; 1 vs 4 workers identical). |
| `validate_growclust.py` | The local build reproduces the upstream Spanish Springs example catalog exactly (archive path via `GROWCLUST_EXAMPLE`, skipped when absent); the interface on a synthetic 60-event cluster perturbed by 0.5 km with exact `dt.cc` (relative error < 50 m horizontal, < 100 m 3-D, ≥ 5× better than the input). |

The native locator examples are intentionally underdetermined (one station) so
that they test executable startup, control-file parsing and file generation,
not location accuracy. A `pass` result means the local interface ran and
produced the expected smoke-test artifacts. It does not qualify scientific
parameters, model accuracy, full-data performance or reproducibility of a
case-level catalog.

Results are written to the ignored `outputs/` directory. Each
`validate_*.json` file is a single machine-readable JSON document; native
program stdout/stderr is kept separately in a matching `.native.log` file
when needed. The existing
`seismotools/support/check_tools.py --imports` remains the integrity and model-loading
check; these scripts additionally exercise actual tool execution and, for
NonLinLoc, the bundled Python interface.

For NonLinLoc, the validation deliberately covers both layers of the package:
the `runtime/bin/` executables and the copied `runtime/python/Nonlinlocpy/` Python package.
The default binary check temporarily removes executable paths from `PATH`, so
it verifies that the package resolves the repository-local sibling `bin/`
directory rather than accidentally using an unrelated system installation.
