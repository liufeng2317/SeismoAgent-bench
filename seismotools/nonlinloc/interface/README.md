# Standard NonLinLoc interface

`run.py` is the stable project entry point for a prepared 1-D NonLinLoc case. It
keeps inputs separate from the writable run directory and stops on the first
failed native stage.

```bash
python seismotools/nonlinloc/interface/run.py \
  --input-dir seismotools/nonlinloc/examples/smoke/inputs \
  --output-dir /tmp/nonlinloc-smoke \
  --bin-dir seismotools/nonlinloc/runtime/bin
```

Pass standard settings with `--config config.json`; command-line flags such as
`--date`, `--native-obs` and `--prepare-only` override the JSON values.

The input files and generated outputs are defined in
[input_schema.json](input_schema.json) and [output_schema.json](output_schema.json).
Optional standard settings are listed in [config_schema.json](config_schema.json).
The adapter is intentionally narrow: case workflows may use `Nonlinlocpy`
directly for advanced controls, but should preserve the same separation of
read-only inputs and writable run products.

The adapter refuses to use a non-empty output directory unless `--overwrite` is
provided. A successful run records the generated model, travel-time, observation
and location directories in `run_result.json`; a failed run records the error
when the output directory is available.
