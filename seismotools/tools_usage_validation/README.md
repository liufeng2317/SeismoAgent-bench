# Tool usage validation

This directory contains environment checks for the locally bundled
seismological tools. Each tool check runs both a synthetic smoke test and a
bounded Ridgecrest data check. Native-tool checks use temporary directories and
do not modify the stored case products.

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
| `validate_phasenet.py` | Synthetic CPU forward pass and one real Ridgecrest three-component window. |
| `validate_gamma.py` | Synthetic P/S association and one real stored Ridgecrest event's picks. |
| `validate_nonlinloc.py` | Tiny synthetic grids plus one stored Ridgecrest event and grid. |
| `validate_hypodd.py` | Synthetic input parsing plus two real Ridgecrest CT event-pair blocks. |

The native locator examples are intentionally underdetermined (one station) so
that they test executable startup, control-file parsing and file generation,
not location accuracy. A `pass` result means the local interface ran and
produced the expected smoke-test artifacts. It does not qualify scientific
parameters, model accuracy, full-data performance or reproducibility of a
case-level catalog.

Results are written to the ignored `outputs/` directory. The existing
`seismotools/check_tools.py --imports` remains the integrity and model-loading
check; these scripts additionally exercise actual tool execution. The
Ridgecrest checks are bounded and are not a full-data catalog rerun.
