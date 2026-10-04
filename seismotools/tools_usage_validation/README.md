# Tool usage validation

This directory contains minimal environment checks for the locally bundled
seismological tools. The checks use synthetic inputs and temporary directories;
they do not read or modify the large Ridgecrest waveform collection.

Run all checks with:

```bash
bash run_all.sh
```

Set `PYTHON` when a different compatible environment is intended:

```bash
PYTHON=/path/to/python bash run_all.sh
```

The checks are deliberately small:

| Script | Validation |
| --- | --- |
| `validate_phasenet.py` | Loads the bundled CPU weights and runs one three-component forward pass. |
| `validate_gamma.py` | Associates a deterministic synthetic P/S pick set into an event. |
| `validate_nonlinloc.py` | Builds a tiny velocity grid, computes one travel-time grid and starts NLLoc. |
| `validate_hypodd.py` | Parses a two-event catalog differential-time example and starts hypoDD. |

The native locator examples are intentionally underdetermined (one station) so
that they test executable startup, control-file parsing and file generation,
not location accuracy. A `pass` result means the local interface ran and
produced the expected smoke-test artifacts. It does not qualify scientific
parameters, model accuracy, full-data performance or reproducibility of a
case-level catalog.

Results are written to the ignored `outputs/` directory. The existing
`seismotools/check_tools.py --imports` remains the integrity and model-loading
check; this directory adds actual minimal execution checks.
