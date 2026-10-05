# Standard hypoDD interface

`run.py` runs a prepared native hypoDD relocation while keeping source inputs
read-only and copying them into a writable run directory.

```bash
python seismotools/hypodd/interface/run.py \
  --input-dir /path/to/hypodd-inputs \
  --output-dir /path/to/writable-run \
  --mode ct \
  --bin-dir /path/to/seismotools/hypodd/runtime/bin
```

Use `--mode ct_cc` when `dt.cc` is present. Use `--run-ph2dt` only when the
input folder also contains a valid `ph2dt.inp`. Input and output contracts are
in [input_schema.json](input_schema.json) and [output_schema.json](output_schema.json).

The adapter checks native exit status, records a combined log and requires
`hypoDD.loc` before reporting success. The richer Python API under
`runtime/python/HypoDDpy` remains available for input conversion, FDTCC and
parallel workflows.
